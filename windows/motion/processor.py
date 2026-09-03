"""
Motion Processor:
Converts 3D device orientation quaternions, gyroscope angular velocity, and
accelerometer measurements into smooth, responsive relative cursor movements.
"""

import math
import logging
import threading
from typing import Dict, Any, Tuple, Optional

from .math_utils import (
    Quaternion,
    EMAFilter,
    OneEuroFilter,
    apply_deadzone,
    apply_acceleration
)

logger = logging.getLogger("motion_processor")


class MotionProcessor:
    """
    Processes incoming sensor frames and produces relative Windows cursor movements.
    """

    def __init__(self,
                 sensitivity_x: float = 18.0,
                 sensitivity_y: float = 18.0,
                 deadzone: float = 0.04,
                 smoothing: float = 0.3,
                 acceleration: float = 0.5,
                 invert_x: bool = False,
                 invert_y: bool = False,
                 cursor_max_delta: float = 120.0):
        self._lock = threading.RLock()

        # Configuration parameters
        self.sensitivity_x = float(sensitivity_x)
        self.sensitivity_y = float(sensitivity_y)
        self.deadzone = float(deadzone)
        self.acceleration = float(acceleration)
        self.invert_x = bool(invert_x)
        self.invert_y = bool(invert_y)
        self.cursor_max_delta = float(cursor_max_delta)

        # Filters
        self._filter = EMAFilter(smoothing_factor=smoothing)
        self._filter_x = OneEuroFilter(min_cutoff=1.0, beta=0.015)
        self._filter_y = OneEuroFilter(min_cutoff=1.0, beta=0.015)
        self._gravity_ema = [0.0, 0.0, 9.81]
        self._dt_filtered = 0.01

        # Reference / Neutral orientation for recentering
        self._neutral_q: Quaternion = Quaternion.identity()
        self._current_q: Quaternion = Quaternion.identity()
        self._prev_q: Optional[Quaternion] = None
        self._has_neutral: bool = False

        # Sub-pixel accumulator to guarantee fine slow movements are not truncated to 0
        self._subpixel_x: float = 0.0
        self._subpixel_y: float = 0.0

        # Latest telemetry for UI and diagnostics
        self._latest_gyro = (0.0, 0.0, 0.0)
        self._latest_accel = (0.0, 0.0, 0.0)
        self._latest_euler_deg = (0.0, 0.0, 0.0)
        self._last_timestamp: int = 0
        self._packet_count: int = 0

    def update_settings(self, **kwargs):
        """Update motion parameters dynamically from GUI or settings."""
        with self._lock:
            if "sensitivity_x" in kwargs:
                self.sensitivity_x = float(kwargs["sensitivity_x"])
            if "sensitivity_y" in kwargs:
                self.sensitivity_y = float(kwargs["sensitivity_y"])
            if "deadzone" in kwargs:
                self.deadzone = max(0.0, float(kwargs["deadzone"]))
            if "smoothing" in kwargs:
                sm_val = float(kwargs["smoothing"])
                self._filter.set_smoothing(sm_val)
                cutoff = max(0.3, 2.5 - sm_val * 2.3)
                self._filter_x.min_cutoff = cutoff
                self._filter_y.min_cutoff = cutoff
            if "acceleration" in kwargs:
                self.acceleration = max(0.0, float(kwargs["acceleration"]))
            if "invert_x" in kwargs:
                self.invert_x = bool(kwargs["invert_x"])
            if "invert_y" in kwargs:
                self.invert_y = bool(kwargs["invert_y"])
            if "cursor_max_delta" in kwargs:
                self.cursor_max_delta = max(10.0, float(kwargs["cursor_max_delta"]))

    def recenter(self, current_q: Optional[Quaternion] = None):
        """
        Set the current phone orientation as the neutral reference.
        Subsequent relative rotation will be measured from this orientation.
        Immediate cursor jump is zero.
        """
        with self._lock:
            if current_q is not None:
                self._neutral_q = current_q.normalized()
            else:
                self._neutral_q = self._current_q.normalized()

            self._has_neutral = True
            self._prev_q = self._neutral_q
            self._subpixel_x = 0.0
            self._subpixel_y = 0.0
            self._filter.reset()
            self._filter_x.reset()
            self._filter_y.reset()
            self._gravity_ema = [0.0, 0.0, 9.81]
            self._dt_filtered = 0.01
            logger.info(f"Motion recentered to: {self._neutral_q}")

    def process_frame(self,
                      qx: float, qy: float, qz: float, qw: float,
                      gx: float, gy: float, gz: float,
                      ax: float, ay: float, az: float,
                      timestamp_ms: int = 0) -> Tuple[int, int]:
        """
        Process a single motion packet and compute integer cursor delta (dx, dy).
        Returns (dx, dy) for Windows SendInput.
        """
        with self._lock:
            curr_q = Quaternion(qx, qy, qz, qw).normalized()
            self._current_q = curr_q

            self._latest_gyro = (gx, gy, gz)
            self._latest_accel = (ax, ay, az)
            self._packet_count += 1

            if not self._has_neutral:
                self.recenter(curr_q)
                self._last_timestamp = timestamp_ms
                return 0, 0

            # Delta time in seconds (fallback to 1/100s if timestamp missing/zero)
            dt = 0.01
            if self._last_timestamp > 0 and timestamp_ms > self._last_timestamp:
                dt = min(0.05, (timestamp_ms - self._last_timestamp) / 1000.0)
            self._last_timestamp = timestamp_ms

            # Filter dt to eliminate Wi-Fi packet arrival timing jitter from cursor velocity
            self._dt_filtered = 0.15 * dt + 0.85 * self._dt_filtered
            dt_eff = self._dt_filtered

            # Compute relative rotation from neutral for diagnostics/HUD
            rel_q = curr_q.relative_to(self._neutral_q)
            self._latest_euler_deg = rel_q.to_euler_degrees()

            # --- Motion Calculation ---
            # Low-pass filter the gravity vector so rapid hand motion does not wobble the vertical axis
            alpha_g = 0.08
            self._gravity_ema[0] = alpha_g * ax + (1.0 - alpha_g) * self._gravity_ema[0]
            self._gravity_ema[1] = alpha_g * ay + (1.0 - alpha_g) * self._gravity_ema[1]
            self._gravity_ema[2] = alpha_g * az + (1.0 - alpha_g) * self._gravity_ema[2]

            gxe, gye, gze = self._gravity_ema
            g_norm = math.sqrt(gxe * gxe + gye * gye + gze * gze)
            if g_norm >= 1.0:
                ux, uy, uz = -gxe / g_norm, -gye / g_norm, -gze / g_norm
                # Yaw: rotation around true room vertical (gravity axis)
                omega_yaw = gx * ux + gy * uy + gz * uz
                # Pitch: rotation around lateral hand axis (perpendicular to up and forward)
                # Calibrated so phone UP -> cursor UP, phone DOWN -> cursor DOWN
                if abs(ux) < 0.707:
                    # Portrait / tilted mode: lateral axis is primarily phone X
                    omega_pitch = gx
                else:
                    # Landscape mode: lateral axis is phone Y
                    omega_pitch = gy if ux > 0 else -gy
            else:
                # Fallback to direct Wii Remote pointing axes if accelerometer data unavailable
                omega_yaw = -gz
                omega_pitch = gx

            # Fine deadzone on angular velocity (in rad/s) to silence hand tremor at rest
            dz_thresh = self.deadzone * 0.4
            dz_yaw = apply_deadzone(omega_yaw, dz_thresh)
            dz_pitch = apply_deadzone(omega_pitch, dz_thresh)

            raw_dx = dz_yaw * dt_eff * self.sensitivity_x * 80.0
            raw_dy = -dz_pitch * dt_eff * self.sensitivity_y * 80.0

            # Apply Invert toggles
            if self.invert_x:
                raw_dx = -raw_dx
            if self.invert_y:
                raw_dy = -raw_dy

            # Apply adaptive OneEuroFilter for silky-smooth cursor motion
            rate = 1.0 / dt_eff if dt_eff > 0 else 100.0
            sm_dx = self._filter_x.filter(raw_dx, rate=rate)
            sm_dy = self._filter_y.filter(raw_dy, rate=rate)

            # Apply non-linear acceleration curve
            acc_dx, acc_dy = apply_acceleration(sm_dx, sm_dy, self.acceleration)

            # Clamp maximum cursor step per frame to prevent wild jumps
            clamped_dx = max(-self.cursor_max_delta, min(self.cursor_max_delta, acc_dx))
            clamped_dy = max(-self.cursor_max_delta, min(self.cursor_max_delta, acc_dy))

            # Sub-pixel accumulator
            self._subpixel_x += clamped_dx
            self._subpixel_y += clamped_dy

            out_dx = int(self._subpixel_x)
            out_dy = int(self._subpixel_y)

            self._subpixel_x -= out_dx
            self._subpixel_y -= out_dy

            return out_dx, out_dy

    def get_telemetry(self) -> Dict[str, Any]:
        """Return snapshot of latest motion telemetry for UI HUD."""
        with self._lock:
            yaw, pitch, roll = self._latest_euler_deg
            gx, gy, gz = self._latest_gyro
            ax, ay, az = self._latest_accel
            return {
                "yaw_deg": yaw,
                "pitch_deg": pitch,
                "roll_deg": roll,
                "gyro_x": gx,
                "gyro_y": gy,
                "gyro_z": gz,
                "accel_x": ax,
                "accel_y": ay,
                "accel_z": az,
                "packets": self._packet_count,
            }
