"""
Unit tests for Dolphin DSU / Cemuhook Protocol Server:
Validates CRC32 calculation, protocol version negotiation, controller info query,
client subscription, and real-time motion/button state serialization.
"""

import unittest
import socket
import struct
import zlib
import time
import sys
import os
from typing import Tuple

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

from windows.networking.dsu_server import (
    DSUServer, MAGIC_SERVER, MAGIC_CLIENT, PROTOCOL_VERSION,
    MSG_PROTOCOL_VERSION, MSG_CONTROLLER_INFO, MSG_CONTROLLER_DATA
)


class TestDSUServer(unittest.TestCase):
    def setUp(self):
        self.dsu_port = 26765
        self.server = DSUServer(port=self.dsu_port)
        self.server.start()
        time.sleep(0.1)

    def tearDown(self):
        self.server.stop()

    def _build_client_packet(self, msg_type: int, payload: bytes = b"") -> bytes:
        full_length = len(payload) + 4
        # Magic (4s), version (H), length (H), crc32 (I), client_id (I)
        header = bytearray(struct.pack(
            "<4sHHII",
            MAGIC_CLIENT,
            PROTOCOL_VERSION,
            full_length,
            0,
            0x87654321
        ))
        body = struct.pack("<I", msg_type) + payload
        packet = header + body
        crc = zlib.crc32(packet) & 0xFFFFFFFF
        packet[8:12] = struct.pack("<I", crc)
        return bytes(packet)

    def _verify_server_packet(self, data: bytes) -> Tuple[int, bytes]:
        self.assertGreaterEqual(len(data), 16)
        magic = data[:4]
        self.assertEqual(magic, MAGIC_SERVER)

        # Check CRC
        received_crc = struct.unpack_from("<I", data, 8)[0]
        zero_crc_data = bytearray(data)
        zero_crc_data[8:12] = b"\x00\x00\x00\x00"
        computed_crc = zlib.crc32(zero_crc_data) & 0xFFFFFFFF
        self.assertEqual(received_crc, computed_crc, "Server CRC32 must match")

        msg_type = struct.unpack_from("<I", data, 16)[0]
        return msg_type, data[16:]

    def test_dsu_version_request(self):
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.settimeout(1.0)
        req = self._build_client_packet(MSG_PROTOCOL_VERSION)
        sock.sendto(req, ('127.0.0.1', self.dsu_port))

        resp, _ = sock.recvfrom(1024)
        msg_type, body = self._verify_server_packet(resp)
        self.assertEqual(msg_type, MSG_PROTOCOL_VERSION)
        ver = struct.unpack_from("<H", body, 4)[0]
        self.assertEqual(ver, PROTOCOL_VERSION)
        sock.close()

    def test_dsu_controller_info_request(self):
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.settimeout(1.0)
        # Query slot 0
        req = self._build_client_packet(MSG_CONTROLLER_INFO, struct.pack("<B", 0))
        sock.sendto(req, ('127.0.0.1', self.dsu_port))

        resp, _ = sock.recvfrom(1024)
        msg_type, body = self._verify_server_packet(resp)
        self.assertEqual(msg_type, MSG_CONTROLLER_INFO)
        # slot is at offset 4
        slot = body[4]
        self.assertEqual(slot, 0)
        sock.close()

    def test_dsu_controller_data_subscription_and_motion(self):
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.settimeout(1.0)

        # Set button state and motion on server
        self.server.set_button_state("A", True)
        self.server.set_button_state("DPAD_UP", True)
        # Accel 9.80665 m/s² on Z = 1.0g
        self.server.update_motion(ax=0.0, ay=0.0, az=9.80665, gx=0.0, gy=0.0, gz=0.5, timestamp_ms=12345)

        # Subscribe
        req = self._build_client_packet(MSG_CONTROLLER_DATA, struct.pack("<BB", 1, 0))
        sock.sendto(req, ('127.0.0.1', self.dsu_port))

        resp, _ = sock.recvfrom(1024)
        msg_type, body = self._verify_server_packet(resp)
        # Check subscriber count
        self.assertGreaterEqual(self.server.get_subscriber_count(), 1)

        # Check total packet length is exactly 100 bytes as required by Dolphin / Cemuhook
        self.assertEqual(len(resp), 100)

        # Test HOME button (PS button in Cemuhook at offset 18 of payload, which is offset 22 in body after msg_type)
        self.server.set_button_state("HOME", True)
        resp_home, _ = sock.recvfrom(1024)
        self.assertEqual(len(resp_home), 100)
        # body offset 22 is button_ps
        ps_val = resp_home[16 + 4 + 1 + 1 + 1 + 1 + 6 + 1 + 1 + 4 + 1 + 1] # 16 header + 22 body offset
        self.assertEqual(ps_val, 1, "HOME button must set button_ps to 1 for Dolphin")

        sock.close()


if __name__ == "__main__":
    unittest.main()
