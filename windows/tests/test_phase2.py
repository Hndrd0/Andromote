"""
Unit tests for Phase 2: Pairing, Discovery, TCP Control, UDP Motion Server
"""

import unittest
import socket
import struct
import json
import time
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

from windows.networking.pairing import PairingManager
from windows.networking.discovery_server import DiscoveryServer
from windows.networking.tcp_server import TCPServer
from windows.networking.udp_motion_server import UDPMotionServer, BINARY_MAGIC, BINARY_PACKET_FORMAT
from windows.input.win_input import WindowsInputController
from windows.motion.processor import MotionProcessor
from windows.config.settings_manager import SettingsManager


class TestPairingManager(unittest.TestCase):
    def setUp(self):
        import tempfile
        self.tmp = os.path.join(tempfile.gettempdir(), "andromote_test_pairing.json")
        if os.path.exists(self.tmp):
            os.remove(self.tmp)
        self.mgr = PairingManager(self.tmp)

    def tearDown(self):
        if os.path.exists(self.tmp):
            os.remove(self.tmp)

    def test_pin_and_pair_flow(self):
        pin = self.mgr.get_current_pin()
        self.assertEqual(len(pin), 4)

        # Pair with correct PIN
        success, token, msg = self.mgr.pair_device(pin, "device-123", "Pixel 8")
        self.assertTrue(success)
        self.assertIsNotNone(token)

        # Verify device is trusted
        valid, reason = self.mgr.validate_token("device-123", token)
        self.assertTrue(valid)

        # Invalid token rejection
        invalid, _ = self.mgr.validate_token("device-123", "bad_token")
        self.assertFalse(invalid)

        # Forget device
        self.mgr.forget_device("device-123")
        valid_after_forget, _ = self.mgr.validate_token("device-123", token)
        self.assertFalse(valid_after_forget)


class TestNetworkIntegration(unittest.TestCase):
    def setUp(self):
        self.input_ctrl = WindowsInputController(mock_mode=True)
        self.proc = MotionProcessor()
        self.settings = SettingsManager()
        import tempfile
        self.tmp_pair = os.path.join(tempfile.gettempdir(), "andromote_test_pair2.json")
        self.pairing = PairingManager(self.tmp_pair)

        # Start TCP server on port 42435 (test port)
        self.tcp_port = 42435
        self.tcp_server = TCPServer(
            port=self.tcp_port,
            pairing_manager=self.pairing,
            input_controller=self.input_ctrl,
            motion_processor=self.proc,
            settings_manager=self.settings
        )
        self.tcp_server.start()

        # Start UDP motion server on port 42436 (test port)
        self.motion_port = 42436
        self.udp_server = UDPMotionServer(
            port=self.motion_port,
            motion_processor=self.proc,
            input_controller=self.input_ctrl,
            settings_manager=self.settings
        )
        self.udp_server.start()
        time.sleep(0.1)

    def tearDown(self):
        self.tcp_server.stop()
        self.udp_server.stop()
        if os.path.exists(self.tmp_pair):
            os.remove(self.tmp_pair)

    def _send_tcp_frame(self, sock, data):
        payload = json.dumps(data).encode("utf-8")
        sock.sendall(struct.pack(">I", len(payload)) + payload)

    def _recv_tcp_frame(self, sock):
        hdr = sock.recv(4)
        if not hdr or len(hdr) < 4:
            return None
        length = struct.unpack(">I", hdr)[0]
        buf = bytearray()
        while len(buf) < length:
            buf.extend(sock.recv(length - len(buf)))
        return json.loads(bytes(buf).decode("utf-8"))

    def test_tcp_pairing_and_button_events(self):
        client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        client.connect(('127.0.0.1', self.tcp_port))

        # Send Hello
        self._send_tcp_frame(client, {"type": "hello", "device_id": "phone-1"})
        reply = self._recv_tcp_frame(client)
        self.assertEqual(reply.get("type"), "hello_reply")
        self.assertTrue(reply.get("needs_pairing"))

        # Pair with PIN
        pin = self.pairing.get_current_pin()
        self._send_tcp_frame(client, {
            "type": "pair",
            "pin": pin,
            "device_id": "phone-1",
            "device_name": "Test Phone"
        })
        pair_reply = self._recv_tcp_frame(client)
        self.assertEqual(pair_reply.get("status"), "success")
        token = pair_reply.get("token")
        self.assertIsNotNone(token)

        # Press Button A (mapped to MOUSE_LEFT by default)
        self._send_tcp_frame(client, {
            "type": "button",
            "button": "A",
            "state": "down"
        })
        time.sleep(0.05)
        held_mouse, _ = self.input_ctrl.get_held_inputs()
        self.assertIn("left", held_mouse)

        # Close client connection -> must trigger failsafe release
        client.close()
        time.sleep(0.1)
        held_mouse, _ = self.input_ctrl.get_held_inputs()
        self.assertEqual(len(held_mouse), 0, "Button A should be released on disconnect")

    def test_udp_binary_motion_packet(self):
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        # Pack binary frame: Magic, seq, ts, qx, qy, qz, qw, gx, gy, gz, ax, ay, az
        pkt = struct.pack(
            BINARY_PACKET_FORMAT,
            BINARY_MAGIC,
            1,          # seq
            1000,       # ts ms
            0.0, 0.0, 0.0, 1.0,  # q
            0.0, 0.0, -1.0,      # gyro (turning left)
            0.0, 0.0, 9.81       # accel
        )
        sock.sendto(pkt, ('127.0.0.1', self.motion_port))
        time.sleep(0.05)
        sock.close()

        # Check telemetry updated
        telem = self.proc.get_telemetry()
        self.assertGreaterEqual(telem["packets"], 1)

    def test_tcp_touchpad_move(self):
        client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        client.connect(('127.0.0.1', self.tcp_port))

        pin = self.pairing.get_current_pin()
        self._send_tcp_frame(client, {
            "type": "pair",
            "pin": pin,
            "device_id": "phone-touch",
            "device_name": "Test Phone"
        })
        self._recv_tcp_frame(client)

        # Clear action log
        self.input_ctrl._action_log.clear()

        # Send small subpixel movements: 0.6 + 0.6 -> accumulates to 1.2 -> outputs 1
        self._send_tcp_frame(client, {
            "type": "touchpad_move",
            "dx": 0.6,
            "dy": 0.4
        })
        time.sleep(0.05)
        self.assertEqual(len(self.input_ctrl._action_log), 0)

        # Second frame: dx=0.6, dy=0.8 -> accumulated dx=1.2, dy=1.2 -> outputs dx=1, dy=1!
        self._send_tcp_frame(client, {
            "type": "touchpad_move",
            "dx": 0.6,
            "dy": 0.8
        })
        time.sleep(0.05)
        self.assertEqual(len(self.input_ctrl._action_log), 1)
        self.assertEqual(self.input_ctrl._action_log[0], ("move", 1, 1))

        client.close()


if __name__ == "__main__":
    unittest.main()
