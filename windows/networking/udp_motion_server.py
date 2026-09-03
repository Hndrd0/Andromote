"""
UDP Motion Streaming Server:
Ultra-low latency UDP receiver for high-rate (100-200 Hz) motion frames.
Supports both compact binary protocol ('WMO1') and JSON fallback.
Feeds into MotionProcessor, Windows SendInput, and Dolphin DSU server,
with watchdog timer for input safety.
"""

import socket
import struct
import json
import math
import logging
import threading
import time
from typing import Optional, Callable

from ..motion.processor import MotionProcessor
from ..input.win_input import WindowsInputController
from ..config.settings_manager import SettingsManager

logger = logging.getLogger("udp_motion_server")

# Binary format: Magic(4s) + Seq(H) + Timestamp(Q) + Quat(4f) + Gyro(3f) + Accel(3f)
# Total size: 4 + 2 + 8 + 16 + 12 + 12 = 54 bytes
BINARY_PACKET_FORMAT = "!4sHQ4f3f3f"
BINARY_PACKET_SIZE = struct.calcsize(BINARY_PACKET_FORMAT)
BINARY_MAGIC = b"WMO1"


class UDPMotionServer:
    """
    High-performance UDP motion stream receiver.
    """

    def __init__(self,
                 port: int,
                 motion_processor: MotionProcessor,
                 input_controller: WindowsInputController,
                 settings_manager: SettingsManager,
                 dsu_server=None,
                 gesture_engine=None):
        self.port = int(port)
        self.motion_processor = motion_processor
        self.input_controller = input_controller
        self.settings_manager = settings_manager
        self.dsu_server = dsu_server
        self.gesture_engine = gesture_engine

        self._running = False
        self._socket: Optional[socket.socket] = None
        self._thread: Optional[threading.Thread] = None
        self._watchdog_thread: Optional[threading.Thread] = None

        # Packet and rate metrics
        self._last_packet_time: float = 0.0
        self._packet_count: int = 0
        self._current_hz: float = 0.0
        self._last_hz_calc_time: float = time.time()
        self._last_hz_packet_count: int = 0
        self._last_sequence: int = -1

        # State callback
        self.on_rate_update: Optional[Callable[[float], None]] = None

    def start(self):
        if self._running:
            return

        self._running = True
        self._socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self._socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self._socket.bind(('', self.port))
        self._socket.settimeout(0.5)

        self._thread = threading.Thread(target=self._receive_loop, daemon=True, name="UDPMotion")
        self._thread.start()

        self._watchdog_thread = threading.Thread(target=self._watchdog_loop, daemon=True, name="MotionWatchdog")
        self._watchdog_thread.start()

        logger.info(f"UDP Motion Server listening on port {self.port}")

    def stop(self):
        self._running = False
        if self.gesture_engine:
            self.gesture_engine.release_all(self.input_controller)
        if self._socket:
            try:
                self._socket.close()
            except Exception:
                pass
            self._socket = None

    def _receive_loop(self):
        while self._running:
            try:
                data, addr = self._socket.recvfrom(2048)
                self._handle_packet(data)
            except socket.timeout:
                continue
            except Exception as e:
                if self._running:
                    logger.debug(f"UDP recv error: {e}")
                break

    def _handle_packet(self, data: bytes):
        now = time.time()
        self._last_packet_time = now
        self._packet_count += 1

        # Rate calculation every 0.5s
        elapsed = now - self._last_hz_calc_time
        if elapsed >= 0.5:
            delta_pkts = self._packet_count - self._last_hz_packet_count
            self._current_hz = delta_pkts / elapsed
            self._last_hz_calc_time = now
            self._last_hz_packet_count = self._packet_count
            if self.on_rate_update:
                try:
                    self.on_rate_update(self._current_hz)
                except Exception:
                    pass

        # Try parsing as binary packet first
        if len(data) == BINARY_PACKET_SIZE and data[:4] == BINARY_MAGIC:
            try:
                magic, seq, ts, qx, qy, qz, qw, gx, gy, gz, ax, ay, az = struct.unpack(BINARY_PACKET_FORMAT, data)
                self._process_sensors(seq, ts, qx, qy, qz, qw, gx, gy, gz, ax, ay, az)
                return
            except Exception as e:
                logger.debug(f"Failed to unpack binary packet: {e}")
                return

        # Fallback to JSON packet
        try:
            msg = json.loads(data.decode("utf-8"))
            if isinstance(msg, dict) and msg.get("type") == "motion":
                seq = int(msg.get("sequence", 0))
                ts = int(msg.get("timestamp", 0))
                qx = float(msg.get("qx", 0.0))
                qy = float(msg.get("qy", 0.0))
                qz = float(msg.get("qz", 0.0))
                qw = float(msg.get("qw", 1.0))
                gx = float(msg.get("gx", 0.0))
                gy = float(msg.get("gy", 0.0))
                gz = float(msg.get("gz", 0.0))
                ax = float(msg.get("ax", 0.0))
                ay = float(msg.get("ay", 0.0))
                az = float(msg.get("az", 9.81))
                self._process_sensors(seq, ts, qx, qy, qz, qw, gx, gy, gz, ax, ay, az)
        except Exception:
            pass

    def _process_sensors(self, seq: int, ts: int,
                         qx: float, qy: float, qz: float, qw: float,
                         gx: float, gy: float, gz: float,
                         ax: float, ay: float, az: float):
        # Validate finite values
        for val in (qx, qy, qz, qw, gx, gy, gz, ax, ay, az):
            if not math.isfinite(val):
                return

        # Validate reasonable ranges
        if abs(gx) > 50.0 or abs(gy) > 50.0 or abs(gz) > 50.0:
            return
        if abs(ax) > 200.0 or abs(ay) > 200.0 or abs(az) > 200.0:
            return

        self._last_sequence = seq

        # Feed to Motion Processor
        dx, dy = self.motion_processor.process_frame(
            qx, qy, qz, qw,
            gx, gy, gz,
            ax, ay, az,
            timestamp_ms=ts
        )

        # Feed to Gesture Engine
        is_off_screen = False
        if self.gesture_engine:
            telem = self.motion_processor.get_telemetry()
            yaw_deg = telem.get("yaw_deg", 0.0)
            pitch_deg = telem.get("pitch_deg", 0.0)
            is_off_screen = self.gesture_engine.process_frame(
                qx, qy, qz, qw,
                gx, gy, gz,
                ax, ay, az,
                timestamp_ms=ts,
                input_controller=self.input_controller,
                euler_yaw_deg=yaw_deg,
                euler_pitch_deg=pitch_deg
            )

        # Inject relative mouse motion
        if self.input_controller.enabled and (dx != 0 or dy != 0):
            self.input_controller.move_cursor_relative(dx, dy)

        # Feed DSU server if available
        if self.dsu_server:
            self.dsu_server.update_motion(ax, ay, az, gx, gy, gz, ts)

    def _watchdog_loop(self):
        """
        Input safety watchdog:
        If motion stream stops while inputs are held, automatically releases all inputs.
        """
        while self._running:
            time.sleep(0.1)
            timeout = float(self.settings_manager.get("watchdog_timeout", 0.5))
            if self._last_packet_time > 0 and (time.time() - self._last_packet_time) > timeout:
                if self.gesture_engine:
                    self.gesture_engine.release_all(self.input_controller)
                held_mouse, held_keys = self.input_controller.get_held_inputs()
                if held_mouse or held_keys:
                    logger.warning("Watchdog triggered: Motion stream stalled with held inputs. Releasing all inputs.")
                    self.input_controller.release_all_inputs()
