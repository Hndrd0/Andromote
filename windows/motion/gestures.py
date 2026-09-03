"""
Gesture Recognition Engine:
Recognizes authentic Wii-style physical gestures from 6-DOF sensor telemetry:
- Rapid Shaking (continuous spin/attack actions)
- Wrist Snapping (flick up for jump/cast)
- Straight Thrusts (punch/lunge)
- Tilt Steering (Wii Wheel car steering)
- Off-Screen Aiming (aim away from monitor to reload weapon)
- Key Twisting (wrist roll for leaning/turning)
"""

import math
import time
import logging
from typing import Dict, Any, Optional, Callable
from collections import deque

from ..input.keycodes import FRIENDLY_ACTIONS

logger = logging.getLogger("gesture_engine")


class GestureEngine:
    def __init__(self, settings_manager=None):
        self.settings = settings_manager

        # Callback invoked when a gesture fires: callback(gesture_name: str, active: bool)
        self.on_gesture: Optional[Callable[[str, bool], None]] = None

        # Internal sensor state
        self._last_ts: int = 0
        self._last_gyro_pitch: float = 0.0
        self._accel_base = [0.0, 0.0, 9.81]
        self._prev_dyn_accel = [0.0, 0.0, 0.0]
        self._shake_crossings: deque = deque()

        # Off-screen state
        self.is_off_screen: bool = False

        # Tilt steering state
        self._steer_left_active: bool = False
        self._steer_right_active: bool = False

        # Gesture cooldown timestamps
        self._last_shake_time: float = 0.0
        self._last_flick_time: float = 0.0
        self._last_thrust_time: float = 0.0
        self._last_twist_time: float = 0.0
        self._last_offscreen_time: float = 0.0

        # Held keys triggered by gestures that need release
        self._held_gesture_actions = set()

    def get_setting(self, key: str, default: Any) -> Any:
        if self.settings:
            return self.settings.get(key, default)
        return default

    def _trigger_action(self, action_name: str, input_controller, duration: float = 0.08):
        """Execute a key or mouse click action for a momentary gesture."""
        if not action_name or action_name == "NONE" or not input_controller:
            return

        action = FRIENDLY_ACTIONS.get(action_name)
        if not action:
            return

        category, target = action
        if category == "mouse":
            input_controller.mouse_down(target)
            import threading
            def _rel():
                time.sleep(duration)
                try:
                    input_controller.mouse_up(target)
                except Exception:
                    pass
            threading.Thread(target=_rel, daemon=True).start()

        elif category == "keyboard":
            input_controller.key_down(target)
            import threading
            def _rel_k():
                time.sleep(duration)
                try:
                    input_controller.key_up(target)
                except Exception:
                    pass
            threading.Thread(target=_rel_k, daemon=True).start()

    def _set_hold_action(self, action_name: str, is_down: bool, input_controller):
        """Maintain persistent held/released state for continuous gestures like steering."""
        if not action_name or action_name == "NONE" or not input_controller:
            return

        action = FRIENDLY_ACTIONS.get(action_name)
        if not action:
            return

        category, target = action
        if category == "keyboard":
            if is_down:
                if target not in self._held_gesture_actions:
                    input_controller.key_down(target)
                    self._held_gesture_actions.add(target)
            else:
                if target in self._held_gesture_actions:
                    input_controller.key_up(target)
                    self._held_gesture_actions.discard(target)

    def release_all(self, input_controller):
        """Release any keys currently held by gestures."""
        if not input_controller:
            return
        for target in list(self._held_gesture_actions):
            try:
                input_controller.key_up(target)
            except Exception:
                pass
        self._held_gesture_actions.clear()
        self._steer_left_active = False
        self._steer_right_active = False

    def process_frame(self,
                      qx: float, qy: float, qz: float, qw: float,
                      gx: float, gy: float, gz: float,
                      ax: float, ay: float, az: float,
                      timestamp_ms: int,
                      input_controller,
                      euler_yaw_deg: float = 0.0,
                      euler_pitch_deg: float = 0.0) -> bool:
        """
        Processes a single sensor frame.
        Returns True if controller is pointing off-screen (suppressing pointer motion).
        """
        now = time.time()
        dt = 0.01
        if self._last_ts > 0 and timestamp_ms > self._last_ts:
            dt = min(0.05, (timestamp_ms - self._last_ts) / 1000.0)
        self._last_ts = timestamp_ms

        # ------------------------------------------------------------------
        # 1. Off-Screen Aiming / Reload Detection
        # ------------------------------------------------------------------
        offscreen_enabled = self.get_setting("gesture_offscreen_enabled", True)
        if offscreen_enabled:
            cone_angle = math.sqrt(euler_yaw_deg * euler_yaw_deg + euler_pitch_deg * euler_pitch_deg)
            threshold = float(self.get_setting("gesture_offscreen_angle", 32.0))
            hysteresis = threshold - 6.0

            if not self.is_off_screen and cone_angle > threshold:
                self.is_off_screen = True
                if (now - self._last_offscreen_time) > 0.4:
                    self._last_offscreen_time = now
                    action = self.get_setting("gesture_offscreen_action", "KEY_R")
                    self._trigger_action(action, input_controller)
                    if self.on_gesture:
                        self.on_gesture("off_screen", True)
            elif self.is_off_screen and cone_angle < hysteresis:
                self.is_off_screen = False
                if self.on_gesture:
                    self.on_gesture("off_screen", False)
        else:
            self.is_off_screen = False

        # ------------------------------------------------------------------
        # 2. Rapid Shaking Detection
        # ------------------------------------------------------------------
        shake_enabled = self.get_setting("gesture_shake_enabled", True)
        if shake_enabled:
            # Low-pass filter baseline gravity vector
            self._accel_base[0] = 0.05 * ax + 0.95 * self._accel_base[0]
            self._accel_base[1] = 0.05 * ay + 0.95 * self._accel_base[1]
            self._accel_base[2] = 0.05 * az + 0.95 * self._accel_base[2]

            dax = ax - self._accel_base[0]
            day = ay - self._accel_base[1]
            daz = az - self._accel_base[2]
            dyn_mag = math.sqrt(dax * dax + day * day + daz * daz)

            shake_thresh = float(self.get_setting("gesture_shake_threshold", 8.0))
            dot = dax * self._prev_dyn_accel[0] + day * self._prev_dyn_accel[1] + daz * self._prev_dyn_accel[2]
            self._prev_dyn_accel = [dax, day, daz]

            # Direction reversal under significant dynamic acceleration
            if dyn_mag > shake_thresh and dot < 0:
                self._shake_crossings.append(now)

            # Expire crossings older than 350ms
            while self._shake_crossings and (now - self._shake_crossings[0]) > 0.35:
                self._shake_crossings.popleft()

            # If at least 2 reversals occur within 350ms, trigger shake
            if len(self._shake_crossings) >= 2 and (now - self._last_shake_time) > 0.20:
                self._last_shake_time = now
                self._shake_crossings.clear()
                action = self.get_setting("gesture_shake_action", "KEY_SPACE")
                self._trigger_action(action, input_controller)
                if self.on_gesture:
                    self.on_gesture("shake", True)

        # ------------------------------------------------------------------
        # 3. Wrist Snapping / Flick Up Detection
        # ------------------------------------------------------------------
        flick_enabled = self.get_setting("gesture_flick_enabled", True)
        if flick_enabled:
            # Gyro pitch acceleration: derivative of gx
            pitch_rate = gx
            pitch_accel = (pitch_rate - self._last_gyro_pitch) / dt if dt > 0 else 0.0
            self._last_gyro_pitch = pitch_rate

            flick_thresh = float(self.get_setting("gesture_flick_threshold", 32.0))
            if pitch_accel > flick_thresh and (now - self._last_flick_time) > 0.4:
                self._last_flick_time = now
                action = self.get_setting("gesture_flick_action", "KEY_UP")
                self._trigger_action(action, input_controller)
                if self.on_gesture:
                    self.on_gesture("wrist_snap", True)
        else:
            self._last_gyro_pitch = gx

        # ------------------------------------------------------------------
        # 4. Straight Thrust (Punch / Lunge) Detection
        # ------------------------------------------------------------------
        thrust_enabled = self.get_setting("gesture_thrust_enabled", True)
        if thrust_enabled:
            # Forward linear surge along pointing axis (ay for phone holding, or -az)
            total_gyro = math.sqrt(gx * gx + gy * gy + gz * gz)
            # A punch has high forward acceleration but LOW rotational velocity
            thrust_thresh = float(self.get_setting("gesture_thrust_threshold", 14.0))
            if (ay > thrust_thresh or -az > thrust_thresh) and total_gyro < 2.5:
                if (now - self._last_thrust_time) > 0.45:
                    self._last_thrust_time = now
                    action = self.get_setting("gesture_thrust_action", "KEY_F")
                    self._trigger_action(action, input_controller)
                    if self.on_gesture:
                        self.on_gesture("thrust", True)

        # ------------------------------------------------------------------
        # 5. Tilt Steering (Wii Wheel Horizontal Grip)
        # ------------------------------------------------------------------
        steering_enabled = self.get_setting("gesture_steering_enabled", True)
        if steering_enabled:
            steer_thresh = float(self.get_setting("gesture_steering_angle", 14.0))
            steer_deadzone = steer_thresh * 0.5
            steer_left_key = self.get_setting("gesture_steer_left_action", "KEY_A")
            steer_right_key = self.get_setting("gesture_steer_right_action", "KEY_D")

            # Active when phone is held horizontally
            if abs(ax) > 3.5:
                # Tilt angle of phone wheel
                tilt_deg = math.atan2(ay, abs(ax)) * (180.0 / math.pi)

                # Leaning Left (either negative tilt or negative ax steering input)
                if ax < -steer_thresh or tilt_deg < -steer_thresh:
                    self._set_hold_action(steer_left_key, True, input_controller)
                    self._set_hold_action(steer_right_key, False, input_controller)
                    if not self._steer_left_active and self.on_gesture:
                        self.on_gesture("steer_left", True)
                    self._steer_left_active = True
                    self._steer_right_active = False

                # Leaning Right
                elif ax > steer_thresh or tilt_deg > steer_thresh:
                    self._set_hold_action(steer_right_key, True, input_controller)
                    self._set_hold_action(steer_left_key, False, input_controller)
                    if not self._steer_right_active and self.on_gesture:
                        self.on_gesture("steer_right", True)
                    self._steer_right_active = True
                    self._steer_left_active = False

                # Centered (within deadzone)
                elif abs(tilt_deg) < steer_deadzone:
                    if self._steer_left_active:
                        self._set_hold_action(steer_left_key, False, input_controller)
                        self._steer_left_active = False
                    if self._steer_right_active:
                        self._set_hold_action(steer_right_key, False, input_controller)
                        self._steer_right_active = False
            else:
                # Released when returned to vertical/portrait
                if self._steer_left_active:
                    self._set_hold_action(steer_left_key, False, input_controller)
                    self._steer_left_active = False
                if self._steer_right_active:
                    self._set_hold_action(steer_right_key, False, input_controller)
                    self._steer_right_active = False

        # ------------------------------------------------------------------
        # 6. Key Twisting (Wrist Roll)
        # ------------------------------------------------------------------
        twist_enabled = self.get_setting("gesture_twist_enabled", True)
        if twist_enabled:
            # Longitudinal angular velocity (gy in portrait)
            roll_gyro = gy
            twist_thresh = float(self.get_setting("gesture_twist_threshold", 3.2))
            if abs(roll_gyro) > twist_thresh and (now - self._last_twist_time) > 0.35:
                self._last_twist_time = now
                if roll_gyro < -twist_thresh:
                    action = self.get_setting("gesture_twist_left_action", "KEY_Q")
                    self._trigger_action(action, input_controller)
                    if self.on_gesture:
                        self.on_gesture("twist_left", True)
                elif roll_gyro > twist_thresh:
                    action = self.get_setting("gesture_twist_right_action", "KEY_E")
                    self._trigger_action(action, input_controller)
                    if self.on_gesture:
                        self.on_gesture("twist_right", True)

        return self.is_off_screen
