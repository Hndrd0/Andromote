"""
End-to-end automated test executing test_client against live server in mock mode.
"""

import unittest
import threading
import time
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

from windows.config.settings_manager import SettingsManager
from windows.input.win_input import WindowsInputController
from windows.motion.processor import MotionProcessor
from windows.networking.pairing import PairingManager
from windows.networking.tcp_server import TCPServer
from windows.networking.udp_motion_server import UDPMotionServer
from windows.networking.discovery_server import DiscoveryServer
from windows.networking.dsu_server import DSUServer
from windows.test_client import AndromoteTestClient, run_automated_test


class TestEndToEndIntegration(unittest.TestCase):
    def setUp(self):
        self.settings = SettingsManager()
        self.input_ctrl = WindowsInputController(mock_mode=True)
        self.proc = MotionProcessor()
        import tempfile
        self.tmp_pair = os.path.join(tempfile.gettempdir(), "andromote_test_e2e_pairing.json")
        self.pairing = PairingManager(self.tmp_pair)

        self.tcp_port = 52425
        self.motion_port = 52426
        self.discovery_port = 52424
        self.dsu_port = 36760

        self.dsu_srv = DSUServer(port=self.dsu_port)
        self.dsu_srv.start()

        self.tcp_srv = TCPServer(
            port=self.tcp_port,
            pairing_manager=self.pairing,
            input_controller=self.input_ctrl,
            motion_processor=self.proc,
            settings_manager=self.settings,
            dsu_server=self.dsu_srv
        )
        self.tcp_srv.start()

        self.udp_srv = UDPMotionServer(
            port=self.motion_port,
            motion_processor=self.proc,
            input_controller=self.input_ctrl,
            settings_manager=self.settings,
            dsu_server=self.dsu_srv
        )
        self.udp_srv.start()

        self.disc_srv = DiscoveryServer(
            discovery_port=self.discovery_port,
            tcp_port=self.tcp_port,
            motion_port=self.motion_port,
            dsu_port=self.dsu_port
        )
        self.disc_srv.start()
        time.sleep(0.1)

    def tearDown(self):
        self.tcp_srv.stop()
        self.udp_srv.stop()
        self.disc_srv.stop()
        self.dsu_srv.stop()
        if os.path.exists(self.tmp_pair):
            os.remove(self.tmp_pair)

    def test_full_pipeline(self):
        pin = self.pairing.get_current_pin()
        # Run automated test with the current PIN on isolated test ports
        run_automated_test(host="127.0.0.1", pin=pin, tcp_port=self.tcp_port, motion_port=self.motion_port)

        # Verify failsafe: all inputs must be released
        time.sleep(0.2)
        held_m, held_k = self.input_ctrl.get_held_inputs()
        self.assertEqual(len(held_m), 0, "Mouse inputs should be released by failsafe")
        self.assertEqual(len(held_k), 0, "Keyboard inputs should be released by failsafe")


if __name__ == "__main__":
    unittest.main()
