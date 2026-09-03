"""
TCP Control Channel Server:
Implements length-prefixed framed JSON protocol for authentication, PIN pairing,
reliable button press/release events, recenter triggers, and latency pings.
Includes failsafe button release on disconnect.
"""

import socket
import struct
import json
import logging
import threading
import time
from typing import Optional, Callable, Dict, Any

from .pairing import PairingManager
from ..input.win_input import WindowsInputController
from ..input.keycodes import FRIENDLY_ACTIONS
from ..config.settings_manager import SettingsManager
from ..motion.processor import MotionProcessor

logger = logging.getLogger("tcp_server")


class TCPServer:
    """
    TCP server for reliable control, pairing, and button event stream.
    """

    PROTOCOL_VERSION = 1

    def __init__(self,
                 port: int,
                 pairing_manager: PairingManager,
                 input_controller: WindowsInputController,
                 motion_processor: MotionProcessor,
                 settings_manager: SettingsManager,
                 dsu_server=None):
        self.port = int(port)
        self.pairing_manager = pairing_manager
        self.input_controller = input_controller
        self.motion_processor = motion_processor
        self.settings_manager = settings_manager
        self.dsu_server = dsu_server

        self._running = False
        self._server_socket: Optional[socket.socket] = None
        self._listen_thread: Optional[threading.Thread] = None
        self._active_client_sock: Optional[socket.socket] = None
        self._lock = threading.RLock()

        # Connection state
        self.connected_device_id: Optional[str] = None
        self.connected_device_name: Optional[str] = None
        self.is_authenticated: bool = False
        self.client_ip: Optional[str] = None
        self.last_latency_ms: float = 0.0

        # UI Callbacks
        self.on_state_change: Optional[Callable[[str, Optional[str]], None]] = None
        self.on_latency_update: Optional[Callable[[float], None]] = None

        # Touchpad sub-pixel accumulator
        self._touch_subpixel_x: float = 0.0
        self._touch_subpixel_y: float = 0.0

    def start(self):
        if self._running:
            return

        self._running = True
        self._server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self._server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self._server_socket.bind(('', self.port))
        self._server_socket.listen(2)
        self._server_socket.settimeout(1.0)

        self._listen_thread = threading.Thread(target=self._accept_loop, daemon=True, name="TCPAccept")
        self._listen_thread.start()
        logger.info(f"TCP control server listening on port {self.port}")

    def stop(self):
        self._running = False
        with self._lock:
            if self._active_client_sock:
                try:
                    self._active_client_sock.close()
                except Exception:
                    pass
                self._active_client_sock = None
        if self._server_socket:
            try:
                self._server_socket.close()
            except Exception:
                pass
            self._server_socket = None

        # Guarantee all inputs are released on stop
        self.input_controller.release_all_inputs()

    def _accept_loop(self):
        while self._running:
            try:
                client_sock, addr = self._server_socket.accept()
                logger.info(f"Accepted TCP connection from {addr}")

                with self._lock:
                    if self._active_client_sock:
                        # Close previous connection if active
                        try:
                            self._active_client_sock.close()
                        except Exception:
                            pass
                    self._active_client_sock = client_sock
                    self.client_ip = addr[0]
                    self.is_authenticated = False
                    self.connected_device_id = None
                    self.connected_device_name = None

                client_thread = threading.Thread(
                    target=self._handle_client,
                    args=(client_sock, addr),
                    daemon=True,
                    name=f"TCPClient-{addr[0]}"
                )
                client_thread.start()

            except socket.timeout:
                continue
            except Exception as e:
                if self._running:
                    logger.error(f"TCP accept error: {e}")
                break

    @staticmethod
    def _read_exact(sock: socket.socket, num_bytes: int) -> Optional[bytes]:
        """Read exactly num_bytes from stream, handling partial TCP chunks."""
        buf = bytearray()
        while len(buf) < num_bytes:
            try:
                chunk = sock.recv(num_bytes - len(buf))
                if not chunk:
                    return None
                buf.extend(chunk)
            except Exception:
                return None
        return bytes(buf)

    @classmethod
    def send_frame(cls, sock: socket.socket, data: Dict[str, Any]) -> bool:
        """Send length-prefixed JSON frame."""
        try:
            payload = json.dumps(data).encode("utf-8")
            header = struct.pack(">I", len(payload))
            sock.sendall(header + payload)
            return True
        except Exception as e:
            logger.debug(f"TCP send_frame error: {e}")
            return False

    def _handle_client(self, sock: socket.socket, addr):
        sock.settimeout(15.0)  # Keepalive ping will refresh
        self._notify_state("connecting", f"Connected from {addr[0]}")

        try:
            while self._running:
                # Read 4-byte big-endian frame length
                header = self._read_exact(sock, 4)
                if not header:
                    break
                length = struct.unpack(">I", header)[0]
                if length > 65536:  # Max 64KB sanity limit
                    logger.warning(f"Frame length too large: {length} bytes. Terminating connection.")
                    break

                body = self._read_exact(sock, length)
                if not body:
                    break

                try:
                    msg = json.loads(body.decode("utf-8"))
                except Exception as e:
                    logger.warning(f"Malformed JSON frame: {e}")
                    continue

                self._process_message(sock, msg)

        except Exception as e:
            logger.info(f"TCP client {addr} disconnected: {e}")
        finally:
            logger.info(f"TCP connection closed for {addr}")
            with self._lock:
                if self._active_client_sock == sock:
                    self._active_client_sock = None
                    self.is_authenticated = False
                    self.connected_device_id = None
                    self.connected_device_name = None
            try:
                sock.close()
            except Exception:
                pass

            # CRITICAL: Always release all held inputs when connection drops!
            self.input_controller.release_all_inputs()
            self._notify_state("disconnected", None)

    def _notify_state(self, status: str, details: Optional[str]):
        if self.on_state_change:
            try:
                self.on_state_change(status, details)
            except Exception:
                pass

    def _process_message(self, sock: socket.socket, msg: Dict[str, Any]):
        msg_type = msg.get("type")

        if msg_type == "hello":
            dev_id = msg.get("device_id", "")
            trusted = dev_id in self.pairing_manager.get_trusted_devices()
            self.send_frame(sock, {
                "type": "hello_reply",
                "protocol_version": self.PROTOCOL_VERSION,
                "needs_pairing": not trusted,
                "status": "ready"
            })

        elif msg_type == "pair":
            pin = str(msg.get("pin", "")).strip()
            dev_id = str(msg.get("device_id", "")).strip()
            dev_name = str(msg.get("device_name", "Android Phone")).strip()

            success, token, reason = self.pairing_manager.pair_device(pin, dev_id, dev_name)
            if success:
                self.is_authenticated = True
                self.connected_device_id = dev_id
                self.connected_device_name = dev_name
                self.send_frame(sock, {
                    "type": "pair_reply",
                    "status": "success",
                    "token": token,
                    "message": reason
                })
                self._notify_state("connected", dev_name)
            else:
                self.send_frame(sock, {
                    "type": "pair_reply",
                    "status": "error",
                    "message": reason
                })

        elif msg_type == "auth":
            dev_id = str(msg.get("device_id", "")).strip()
            token = str(msg.get("token", "")).strip()
            dev_name = str(msg.get("device_name", "Android Phone")).strip()

            valid, reason = self.pairing_manager.validate_token(dev_id, token)
            if valid:
                self.is_authenticated = True
                self.connected_device_id = dev_id
                self.connected_device_name = dev_name
                self.send_frame(sock, {
                    "type": "auth_reply",
                    "status": "success",
                    "message": reason
                })
                self._notify_state("connected", dev_name)
            else:
                self.send_frame(sock, {
                    "type": "auth_reply",
                    "status": "error",
                    "message": reason
                })

        elif msg_type == "ping":
            client_ts = msg.get("timestamp", 0)
            now_ms = int(time.time() * 1000)
            self.send_frame(sock, {
                "type": "pong",
                "client_timestamp": client_ts,
                "server_timestamp": now_ms
            })
            if "last_rtt" in msg:
                self.last_latency_ms = float(msg["last_rtt"])
                if self.on_latency_update:
                    self.on_latency_update(self.last_latency_ms)

        elif msg_type == "button":
            if not self.is_authenticated:
                return

            btn = msg.get("button", "").upper()
            state = msg.get("state", "").lower()
            self._handle_button(btn, state)

        elif msg_type == "scroll":
            if not self.is_authenticated:
                return
            dy = int(msg.get("delta_y", 0))
            if dy != 0:
                self.input_controller.mouse_wheel(dy)

        elif msg_type == "double_click":
            if not self.is_authenticated:
                return
            self.input_controller.mouse_down("left")
            self.input_controller.mouse_up("left")
            self.input_controller.mouse_down("left")
            self.input_controller.mouse_up("left")

        elif msg_type == "touchpad_move":
            if not self.is_authenticated:
                return
            raw_dx = float(msg.get("dx", 0.0))
            raw_dy = float(msg.get("dy", 0.0))
            self._touch_subpixel_x += raw_dx
            self._touch_subpixel_y += raw_dy
            out_dx = int(self._touch_subpixel_x)
            out_dy = int(self._touch_subpixel_y)
            self._touch_subpixel_x -= out_dx
            self._touch_subpixel_y -= out_dy
            if out_dx != 0 or out_dy != 0:
                self.input_controller.move_cursor_relative(out_dx, out_dy)

        elif msg_type == "touchpad_tap":
            if not self.is_authenticated:
                return
            fingers = int(msg.get("fingers", 1))
            btn = "right" if fingers == 2 else "left"
            self.input_controller.mouse_down(btn)
            self.input_controller.mouse_up(btn)

        elif msg_type == "recenter":
            if not self.is_authenticated:
                return
            self.motion_processor.recenter()

    def _handle_button(self, btn_name: str, state: str):
        """Dispatch button down/up to mouse or keyboard."""
        is_down = (state == "down")

        # Forward to Dolphin DSU server immediately so Dolphin detects the press regardless of PC mappings
        if self.dsu_server:
            self.dsu_server.set_button_state(btn_name, is_down)

        mappings = self.settings_manager.get("button_mappings", {})
        action_key = mappings.get(btn_name)
        if not action_key:
            if btn_name in FRIENDLY_ACTIONS:
                action_key = btn_name
            else:
                return

        action = FRIENDLY_ACTIONS.get(action_key)
        if not action:
            return

        category, target = action

        if category == "mouse":
            if is_down:
                self.input_controller.mouse_down(target)
            else:
                self.input_controller.mouse_up(target)

        elif category == "mouse_wheel" and is_down:
            self.input_controller.mouse_wheel(target)

        elif category == "keyboard":
            if is_down:
                self.input_controller.key_down(target)
            else:
                self.input_controller.key_up(target)

        elif category == "system" and target == "recenter" and is_down:
            self.motion_processor.recenter()
