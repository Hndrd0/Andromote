"""
Unit tests for Phase 1: Math, Input Controller, Processor, Settings
"""

import unittest
import math
import sys
import os

# Ensure windows package is in sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

from windows.motion.math_utils import (
    Quaternion, EMAFilter, apply_deadzone, apply_acceleration
)
from windows.motion.processor import MotionProcessor
from windows.input.win_input import WindowsInputController
from windows.input.keycodes import VK_UP, VK_DOWN, FRIENDLY_ACTIONS
from windows.config.settings_manager import SettingsManager


class TestMathUtils(unittest.TestCase):
    def test_quaternion_identity(self):
        q = Quaternion.identity()
        self.assertEqual(q.x, 0.0)
        self.assertEqual(q.y, 0.0)
        self.assertEqual(q.z, 0.0)
        self.assertEqual(q.w, 1.0)
        self.assertAlmostEqual(q.norm(), 1.0)

    def test_quaternion_multiplication(self):
        # 90-degree rotation around Z axis: q_z = [0, 0, sin(45), cos(45)]
        angle = math.radians(90)
        qz = Quaternion(0, 0, math.sin(angle/2), math.cos(angle/2))
        inv_qz = qz.conjugate()
        prod = qz * inv_qz
        self.assertAlmostEqual(prod.w, 1.0, places=5)
        self.assertAlmostEqual(prod.x, 0.0, places=5)
        self.assertAlmostEqual(prod.y, 0.0, places=5)
        self.assertAlmostEqual(prod.z, 0.0, places=5)

    def test_quaternion_relative_and_recenter(self):
        # If neutral == current, relative rotation must be identity
        q1 = Quaternion(0.1, 0.2, 0.3, 0.9).normalized()
        rel = q1.relative_to(q1)
        self.assertAlmostEqual(rel.w, 1.0, places=5)
        self.assertAlmostEqual(rel.x, 0.0, places=5)
        self.assertAlmostEqual(rel.y, 0.0, places=5)
        self.assertAlmostEqual(rel.z, 0.0, places=5)
        yaw, pitch, roll = rel.to_euler_degrees()
        self.assertAlmostEqual(yaw, 0.0, places=4)
        self.assertAlmostEqual(pitch, 0.0, places=4)
        self.assertAlmostEqual(roll, 0.0, places=4)

    def test_deadzone(self):
        self.assertEqual(apply_deadzone(0.02, 0.05), 0.0)
        self.assertEqual(apply_deadzone(-0.03, 0.05), 0.0)
        self.assertGreater(apply_deadzone(0.10, 0.05), 0.0)
        self.assertLess(apply_deadzone(-0.10, 0.05), 0.0)

    def test_ema_filter(self):
        ema = EMAFilter(smoothing_factor=0.5)
        # First sample returns raw value
        x1, y1 = ema.filter(10.0, 10.0)
        self.assertEqual((x1, y1), (10.0, 10.0))
        # Second sample blends: 0.5 * 0 + 0.5 * 10 = 5.0
        x2, y2 = ema.filter(0.0, 0.0)
        self.assertAlmostEqual(x2, 5.0)
        self.assertAlmostEqual(y2, 5.0)


class TestInputController(unittest.TestCase):
    def test_mock_input_and_failsafe(self):
        controller = WindowsInputController(mock_mode=True)
        # Press mouse buttons
        controller.mouse_down("left")
        controller.mouse_down("right")
        held_mouse, held_keys = controller.get_held_inputs()
        self.assertIn("left", held_mouse)
        self.assertIn("right", held_mouse)

        # Press keys
        controller.key_down(VK_UP)
        held_mouse, held_keys = controller.get_held_inputs()
        self.assertIn(VK_UP, held_keys)

        # Move
        controller.move_cursor_relative(5, -10)
        self.assertIn(("move", 5, -10), controller._action_log)

        # Failsafe release_all_inputs()
        controller.release_all_inputs()
        held_mouse, held_keys = controller.get_held_inputs()
        self.assertEqual(len(held_mouse), 0)
        self.assertEqual(len(held_keys), 0)
        self.assertIn(("mouse_up", "left"), controller._action_log)
        self.assertIn(("mouse_up", "right"), controller._action_log)
        self.assertIn(("key_up", VK_UP), controller._action_log)


class TestMotionProcessor(unittest.TestCase):
    def test_processor_first_frame_recenter(self):
        proc = MotionProcessor(deadzone=0.01)
        # First frame should establish neutral orientation and return (0, 0)
        dx, dy = proc.process_frame(0, 0, 0, 1, 0, 0, 0, 0, 0, 9.81, timestamp_ms=1000)
        self.assertEqual((dx, dy), (0, 0))

    def test_processor_gyro_motion(self):
        proc = MotionProcessor(deadzone=0.01, smoothing=0.0, acceleration=0.0)
        # Init neutral
        proc.process_frame(0, 0, 0, 1, 0, 0, 0, 0, 0, 9.81, timestamp_ms=1000)

        # Rotate phone left (positive/negative gz angular velocity)
        dx, dy = proc.process_frame(0, 0, 0, 1, 0.0, 0.0, -1.0, 0, 0, 9.81, timestamp_ms=1010)
        self.assertGreater(dx, 0)


class TestSettingsManager(unittest.TestCase):
    def test_settings_load_save(self):
        import tempfile
        tmp_file = os.path.join(tempfile.gettempdir(), "andromote_test_settings.json")
        if os.path.exists(tmp_file):
            os.remove(tmp_file)

        mgr = SettingsManager(tmp_file)
        self.assertEqual(mgr.get("sensitivity_x"), 18.0)

        mgr.set("sensitivity_x", 25.5)
        self.assertEqual(mgr.get("sensitivity_x"), 25.5)

        # Reload from disk
        mgr2 = SettingsManager(tmp_file)
        self.assertEqual(mgr2.get("sensitivity_x"), 25.5)

        if os.path.exists(tmp_file):
            os.remove(tmp_file)


if __name__ == "__main__":
    unittest.main()
