"""
Automated unit tests for GestureEngine.
"""

import unittest
import time
import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

from windows.motion.gestures import GestureEngine
from windows.input.win_input import WindowsInputController
from windows.config.settings_manager import SettingsManager


class TestGestureEngine(unittest.TestCase):
    def setUp(self):
        self.input_ctrl = WindowsInputController(mock_mode=True)
        self.settings = SettingsManager()
        self.engine = GestureEngine(settings_manager=self.settings)
        self.triggered_gestures = []
        self.engine.on_gesture = lambda name, act: self.triggered_gestures.append((name, act))

    def tearDown(self):
        self.engine.release_all(self.input_ctrl)

    def test_shake_detection(self):
        # Simulate alternating rapid shaking cycles (50 Hz, 10 samples)
        for i in range(15):
            sign = 1 if (i % 2 == 0) else -1
            az = 9.81 + sign * 18.0
            self.engine.process_frame(
                0, 0, 0, 1,
                0, 0, 0,
                0, 0, az,
                timestamp_ms=1000 + i * 20,
                input_controller=self.input_ctrl
            )
            time.sleep(0.02)

        shake_events = [g for g in self.triggered_gestures if g[0] == "shake"]
        self.assertGreater(len(shake_events), 0, "Shake gesture should be triggered by rapid oscillations")

    def test_wrist_snap_detection(self):
        # Frame 1: Resting
        self.engine.process_frame(
            0, 0, 0, 1,
            0.0, 0, 0,
            0, 0, 9.81,
            timestamp_ms=1000,
            input_controller=self.input_ctrl
        )
        # Frame 2: Sharp upward pitch velocity (jerk > 32 rad/s^2)
        self.engine.process_frame(
            0, 0, 0, 1,
            2.5, 0, 0,
            0, 0, 9.81,
            timestamp_ms=1010,
            input_controller=self.input_ctrl
        )

        flick_events = [g for g in self.triggered_gestures if g[0] == "wrist_snap"]
        self.assertGreater(len(flick_events), 0, "Wrist snap should trigger on upward pitch jerk")

    def test_straight_thrust_detection(self):
        # Forward surge along phone axis (ay > 15 m/s^2) with low angular rotation
        self.engine.process_frame(
            0, 0, 0, 1,
            0.2, 0.1, 0.0,
            0, 18.0, 9.81,
            timestamp_ms=1000,
            input_controller=self.input_ctrl
        )

        thrust_events = [g for g in self.triggered_gestures if g[0] == "thrust"]
        self.assertGreater(len(thrust_events), 0, "Straight thrust should trigger on forward acceleration")

    def test_tilt_steering(self):
        # Phone held horizontally (ax = 8.5 m/s^2) and tilted left by 25 deg (ay = -4.0 m/s^2)
        self.engine.process_frame(
            0, 0, 0, 1,
            0, 0, 0,
            8.5, -4.0, 3.0,
            timestamp_ms=1000,
            input_controller=self.input_ctrl
        )
        steer_left_events = [g for g in self.triggered_gestures if g[0] == "steer_left"]
        self.assertGreater(len(steer_left_events), 0, "Tilt left should trigger steer_left")

        # Now center (within deadzone: ay = 0.2 m/s^2)
        self.engine.process_frame(
            0, 0, 0, 1,
            0, 0, 0,
            9.2, 0.2, 2.0,
            timestamp_ms=1050,
            input_controller=self.input_ctrl
        )
        self.assertFalse(self.engine._steer_left_active, "Steer left should deactivate when centered")

    def test_off_screen_detection(self):
        # Pointing at screen: cone angle 10 degrees -> returns False
        off1 = self.engine.process_frame(
            0, 0, 0, 1,
            0, 0, 0,
            0, 0, 9.81,
            timestamp_ms=1000,
            input_controller=self.input_ctrl,
            euler_yaw_deg=8.0,
            euler_pitch_deg=6.0
        )
        self.assertFalse(off1, "Should be on-screen when pointing at monitor")

        # Aiming away from screen: cone angle 40 degrees (> 32 threshold) -> returns True
        off2 = self.engine.process_frame(
            0, 0, 0, 1,
            0, 0, 0,
            0, 0, 9.81,
            timestamp_ms=1050,
            input_controller=self.input_ctrl,
            euler_yaw_deg=35.0,
            euler_pitch_deg=20.0
        )
        self.assertTrue(off2, "Should be off-screen when aiming away from monitor")
        off_events = [g for g in self.triggered_gestures if g[0] == "off_screen"]
        self.assertGreater(len(off_events), 0, "Off-screen gesture should trigger reload action")

    def test_key_twisting(self):
        # Fast wrist roll: gy = 4.5 rad/s
        self.engine.process_frame(
            0, 0, 0, 1,
            0, 4.5, 0,
            0, 0, 9.81,
            timestamp_ms=1000,
            input_controller=self.input_ctrl
        )
        twist_events = [g for g in self.triggered_gestures if g[0] == "twist_right"]
        self.assertGreater(len(twist_events), 0, "Wrist roll right should trigger twist_right")


if __name__ == "__main__":
    unittest.main()
