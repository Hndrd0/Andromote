"""
DSU / Cemuhook Protocol Server:
Standard UDP motion server compatible with Dolphin Emulator, Cemu, and PCSX2.
Implements CRC32 calculation, controller info negotiation, client subscriptions,
and motion state reporting (accelerometer in g, gyroscope in deg/s, button flags).
"""

import socket
import struct
import zlib
import time
import math
import logging
import threading
from typing import Dict, Tuple, Optional

logger = logging.getLogger("dsu_server")

# Protocol Constants
MAGIC_SERVER = b"DSUS"
MAGIC_CLIENT = b"DSUC"
PROTOCOL_VERSION = 1001

# Message Types
MSG_PROTOCOL_VERSION = 0x00100000
MSG_CONTROLLER_INFO = 0x00100001
MSG_CONTROLLER_DATA = 0x00100002

# Controller States
STATE_DISCONNECTED = 0x00
STATE_CONNECTED = 0x02

# Connection Types
CONN_NOT_APPLICABLE = 0x00
CONN_USB = 0x01
CONN_BLUETOOTH = 0x02

# Models
MODEL_NONE = 0x00
MODEL_PARTIAL_GYRO = 0x01
MODEL_FULL_GYRO = 0x02

# Battery
BATTERY_FULL = 0x05


class DSUServer:
    """
    Cemuhook / DSU Protocol Server running on UDP port 26760.
    """

    def __init__(self, port: int = 26760):
        self.port = int(port)
        self._server_id = 0x12345678
        self._running = False
        self._socket: Optional[socket.socket] = None
        self._thread: Optional[threading.Thread] = None
        self._lock = threading.RLock()

        # Controller state for Slot 0
        self._connected = True
        self._packet_counter = 0

        # Motion measurements
        self._accel_g = (0.0, 0.0, 1.0)        # in g
        self._gyro_deg = (0.0, 0.0, 0.0)       # in deg/s
        self._timestamp_us = 0

        # Buttons state
        self._btn_a = False
        self._btn_b = False
        self._btn_1 = False
        self._btn_2 = False
        self._btn_plus = False
        self._btn_minus = False
        self._btn_home = False
        self._dpad_up = False
        self._dpad_down = False
        self._dpad_left = False
        self._dpad_right = False

        # Subscribed clients: { (ip, port): last_request_time }
        self._subscribers: Dict[Tuple[str, int], float] = {}

    def start(self):
        if self._running:
            return

        self._running = True
        self._socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self._socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self._socket.bind(('', self.port))
        self._socket.settimeout(0.5)

        self._thread = threading.Thread(target=self._server_loop, daemon=True, name="DSUServer")
        self._thread.start()
        logger.info(f"Dolphin DSU Server active on UDP port {self.port}")

    def stop(self):
        self._running = False
        if self._socket:
            try:
                self._socket.close()
            except Exception:
                pass
            self._socket = None

    def get_subscriber_count(self) -> int:
        with self._lock:
            # Clean up subscribers older than 5 seconds
            now = time.time()
            self._subscribers = {k: v for k, v in self._subscribers.items() if (now - v) < 5.0}
            return len(self._subscribers)

    def set_button_state(self, button_name: str, is_down: bool):
        """Update Wii Remote button states for Dolphin mapping."""
        with self._lock:
            b = button_name.upper()
            if b == "A":
                self._btn_a = is_down
            elif b == "B":
                self._btn_b = is_down
            elif b == "1":
                self._btn_1 = is_down
            elif b == "2":
                self._btn_2 = is_down
            elif b in ("PLUS", "+"):
                self._btn_plus = is_down
            elif b in ("MINUS", "-"):
                self._btn_minus = is_down
            elif b == "HOME":
                self._btn_home = is_down
            elif b == "DPAD_UP":
                self._dpad_up = is_down
            elif b == "DPAD_DOWN":
                self._dpad_down = is_down
            elif b == "DPAD_LEFT":
                self._dpad_left = is_down
            elif b == "DPAD_RIGHT":
                self._dpad_right = is_down

            # Immediately broadcast to Dolphin subscribers so button detection is instantaneous
            if self._subscribers and self._socket:
                self._send_controller_data_report()

    def update_motion(self, ax: float, ay: float, az: float,
                      gx: float, gy: float, gz: float,
                      timestamp_ms: int = 0):
        """
        Ingest accelerometer (m/s²) and gyro (rad/s) and stream to subscribed clients.
        Converts m/s² -> g (divide by 9.80665) and rad/s -> deg/s.
        """
        with self._lock:
            # 1 g = 9.80665 m/s²
            self._accel_g = (ax / 9.80665, ay / 9.80665, az / 9.80665)
            # rad/s to deg/s
            self._gyro_deg = (math.degrees(gx), math.degrees(gy), math.degrees(gz))
            self._timestamp_us = (timestamp_ms * 1000) if timestamp_ms > 0 else int(time.time() * 1000000)

            # Broadcast to active subscribers
            if self._subscribers and self._socket:
                self._send_controller_data_report()

    def _create_header(self, msg_type: int, payload_len: int) -> bytearray:
        """
        Build 16-byte header:
        magic (4s), version (H), length (H), crc32 (I), server_id (I)
        """
        # Length in header = payload length + 4 (for msg_type field)
        full_length = payload_len + 4
        # We start with CRC = 0
        header = bytearray(struct.pack(
            "<4sHHII",
            MAGIC_SERVER,
            PROTOCOL_VERSION,
            full_length,
            0,
            self._server_id
        ))
        return header

    @staticmethod
    def _finalize_packet(header: bytearray, body: bytes) -> bytes:
        """Calculate CRC32 over the entire packet and inject into header."""
        packet = header + body
        # Calculate CRC32 of full packet with crc field set to 0
        computed_crc = zlib.crc32(packet) & 0xFFFFFFFF
        # Inject CRC into header at offset 8 (bytes 8..12)
        packet[8:12] = struct.pack("<I", computed_crc)
        return bytes(packet)

    def _server_loop(self):
        while self._running:
            try:
                data, addr = self._socket.recvfrom(1024)
                self._handle_client_packet(data, addr)
            except socket.timeout:
                continue
            except Exception as e:
                if self._running:
                    logger.debug(f"DSU recv error: {e}")
                break

    def _handle_client_packet(self, data: bytes, addr: Tuple[str, int]):
        if len(data) < 16:
            return

        magic = data[:4]
        if magic != MAGIC_CLIENT:
            return

        # Check CRC
        received_crc = struct.unpack_from("<I", data, 8)[0]
        zero_crc_data = bytearray(data)
        zero_crc_data[8:12] = b"\x00\x00\x00\x00"
        if (zlib.crc32(zero_crc_data) & 0xFFFFFFFF) != received_crc:
            return

        msg_type = struct.unpack_from("<I", data, 16)[0]

        if msg_type == MSG_PROTOCOL_VERSION:
            # Reply with protocol version
            body = struct.pack("<IH", MSG_PROTOCOL_VERSION, PROTOCOL_VERSION)
            hdr = self._create_header(MSG_PROTOCOL_VERSION, len(body) - 4)
            pkt = self._finalize_packet(hdr, body)
            self._socket.sendto(pkt, addr)

        elif msg_type == MSG_CONTROLLER_INFO:
            # Slot info request
            body = self._build_controller_info_body(slot=0)
            hdr = self._create_header(MSG_CONTROLLER_INFO, len(body) - 4)
            pkt = self._finalize_packet(hdr, body)
            self._socket.sendto(pkt, addr)

        elif msg_type == MSG_CONTROLLER_DATA:
            # Subscription request
            with self._lock:
                self._subscribers[addr] = time.time()

            # Immediate response with current state
            body = self._build_controller_data_body(slot=0)
            hdr = self._create_header(MSG_CONTROLLER_DATA, len(body) - 4)
            pkt = self._finalize_packet(hdr, body)
            self._socket.sendto(pkt, addr)

    def _build_controller_info_body(self, slot: int = 0) -> bytes:
        # Slot (B), State (B), Model (B), Connection (B), MAC (6B), Battery (B)
        mac = b"\xAA\xBB\xCC\xDD\xEE\x01"
        return struct.pack(
            "<IBBBB6sBB",
            MSG_CONTROLLER_INFO,
            slot,
            STATE_CONNECTED if self._connected else STATE_DISCONNECTED,
            MODEL_FULL_GYRO,
            CONN_BLUETOOTH,
            mac,
            BATTERY_FULL,
            0  # zero terminator
        )

    def _build_controller_data_body(self, slot: int = 0) -> bytes:
        self._packet_counter = (self._packet_counter + 1) & 0xFFFFFFFF
        mac = b"\xAA\xBB\xCC\xDD\xEE\x01"

        # Digital button 1: D-pad Left, Down, Right, Up, Options (+), R3, L3, Share (-)
        btn1 = 0
        if self._dpad_left:  btn1 |= 0x80
        if self._dpad_down:  btn1 |= 0x40
        if self._dpad_right: btn1 |= 0x20
        if self._dpad_up:    btn1 |= 0x10
        if self._btn_plus:   btn1 |= 0x08
        if self._btn_minus:  btn1 |= 0x01

        # Digital button 2: Square (1), Cross (A), Circle (2), Triangle, R1, L1, R2 (B), L2
        btn2 = 0
        if self._btn_1:      btn2 |= 0x80  # Square / 1
        if self._btn_a:      btn2 |= 0x40  # Cross / A
        if self._btn_2:      btn2 |= 0x20  # Circle / 2
        if self._btn_b:      btn2 |= 0x02  # R2 Trigger / B

        # PS / Home button (bit 0 = 1 when pressed)
        ps_btn = 1 if self._btn_home else 0

        # Analog Sticks (centered at 128)
        lx, ly = 128, 128
        rx, ry = 128, 128

        # 12 Analog Buttons (0 or 255) as expected by Dolphin ControllerInterface
        a_dpad_left  = 255 if self._dpad_left else 0
        a_dpad_down  = 255 if self._dpad_down else 0
        a_dpad_right = 255 if self._dpad_right else 0
        a_dpad_up    = 255 if self._dpad_up else 0
        a_square     = 255 if self._btn_1 else 0
        a_cross      = 255 if self._btn_a else 0
        a_circle     = 255 if self._btn_2 else 0
        a_triangle   = 0
        a_r1         = 0
        a_l1         = 0
        a_r2         = 255 if self._btn_b else 0
        a_l2         = 0

        # Motion Data
        pitch_deg, yaw_deg, roll_deg = self._gyro_deg
        acc_x, acc_y, acc_z = self._accel_g

        # Exact 84-byte payload (total 100 bytes with 16-byte header)
        body = struct.pack(
            "<IBBBB6sBB"    # msg_type (4), slot(1), state(1), model(1), conn(1), mac(6), battery(1), active(1) = 16B
            "IBBBB"         # hid_packet_counter (4), btn1 (1), btn2 (1), ps_btn (1), touch_btn (1) = 8B
            "BBBB"          # lx, ly, rx, ry = 4B
            "12B"           # 12 analog buttons = 12B
            "BBhh"          # touch1: active(1), id(1), x(2), y(2) = 6B
            "BBhh"          # touch2: active(1), id(1), x(2), y(2) = 6B
            "Q"             # timestamp us = 8B
            "fff"           # accel x, y, z = 12B
            "fff",          # gyro pitch, yaw, roll = 12B
            MSG_CONTROLLER_DATA,
            slot,
            STATE_CONNECTED,
            MODEL_FULL_GYRO,
            CONN_BLUETOOTH,
            mac,
            BATTERY_FULL,
            1,              # is connected
            self._packet_counter,
            btn1,
            btn2,
            ps_btn,
            0,              # touch btn
            lx, ly, rx, ry,
            a_dpad_left, a_dpad_down, a_dpad_right, a_dpad_up,
            a_square, a_cross, a_circle, a_triangle,
            a_r1, a_l1, a_r2, a_l2,
            0, 0, 0, 0,     # touch1 (inactive)
            0, 0, 0, 0,     # touch2 (inactive)
            self._timestamp_us,
            float(acc_x), float(acc_y), float(acc_z),
            float(pitch_deg), float(yaw_deg), float(roll_deg)
        )
        return body

    def _send_controller_data_report(self):
        body = self._build_controller_data_body(slot=0)
        hdr = self._create_header(MSG_CONTROLLER_DATA, len(body) - 4)
        pkt = self._finalize_packet(hdr, body)

        now = time.time()
        for addr, last_time in list(self._subscribers.items()):
            if (now - last_time) < 5.0:
                try:
                    self._socket.sendto(pkt, addr)
                except Exception:
                    pass
