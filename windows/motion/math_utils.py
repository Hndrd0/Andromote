"""
Mathematical utilities for motion processing:
Quaternion algebra, Euler angle extraction, Exponential Moving Average filters,
deadzone filtering, and non-linear acceleration curves.
"""

import math
from typing import Tuple


class Quaternion:
    """
    3D Quaternion representation: q = [x, y, z, w].
    Follows standard Hamilton quaternion conventions.
    """
    __slots__ = ('x', 'y', 'z', 'w')

    def __init__(self, x: float = 0.0, y: float = 0.0, z: float = 0.0, w: float = 1.0):
        self.x = float(x)
        self.y = float(y)
        self.z = float(z)
        self.w = float(w)

    @classmethod
    def identity(cls) -> 'Quaternion':
        return cls(0.0, 0.0, 0.0, 1.0)

    def norm(self) -> float:
        return math.sqrt(self.x * self.x + self.y * self.y + self.z * self.z + self.w * self.w)

    def normalized(self) -> 'Quaternion':
        n = self.norm()
        if n == 0.0 or math.isnan(n):
            return Quaternion.identity()
        inv_n = 1.0 / n
        return Quaternion(self.x * inv_n, self.y * inv_n, self.z * inv_n, self.w * inv_n)

    def conjugate(self) -> 'Quaternion':
        """For unit quaternions, conjugate equals inverse."""
        return Quaternion(-self.x, -self.y, -self.z, self.w)

    def __mul__(self, other: 'Quaternion') -> 'Quaternion':
        """Hamilton product self * other."""
        w1, x1, y1, z1 = self.w, self.x, self.y, self.z
        w2, x2, y2, z2 = other.w, other.x, other.y, other.z

        w = w1 * w2 - x1 * x2 - y1 * y2 - z1 * z2
        x = w1 * x2 + x1 * w2 + y1 * z2 - z1 * y2
        y = w1 * y2 - x1 * z2 + y1 * w2 + z1 * x2
        z = w1 * z2 + x1 * y2 - y1 * x2 + z1 * w2

        return Quaternion(x, y, z, w)

    def relative_to(self, reference: 'Quaternion') -> 'Quaternion':
        """
        Compute relative rotation delta Q from reference to self:
        Delta_Q = reference.conjugate() * self
        """
        ref_norm = reference.normalized()
        self_norm = self.normalized()
        return (ref_norm.conjugate() * self_norm).normalized()

    def to_euler_angles(self) -> Tuple[float, float, float]:
        """
        Convert to Tait-Bryan Euler angles: (yaw, pitch, roll) in radians.
        Yaw (Z-axis rotation, azimuth), Pitch (X-axis rotation), Roll (Y-axis rotation).
        Robust against gimbal lock.
        """
        x, y, z, w = self.x, self.y, self.z, self.w

        # Pitch (around X axis)
        sinp = 2.0 * (w * x - y * z)
        if abs(sinp) >= 1.0:
            pitch = math.copysign(math.pi / 2.0, sinp)  # Gimbal lock
        else:
            pitch = math.asin(sinp)

        # Yaw (around Z axis)
        siny_cosp = 2.0 * (w * z + x * y)
        cosy_cosp = 1.0 - 2.0 * (x * x + z * z)
        yaw = math.atan2(siny_cosp, cosy_cosp)

        # Roll (around Y axis)
        sinr_cosp = 2.0 * (w * y + z * x)
        cosr_cosp = 1.0 - 2.0 * (x * x + y * y)
        roll = math.atan2(sinr_cosp, cosr_cosp)

        return yaw, pitch, roll

    def to_euler_degrees(self) -> Tuple[float, float, float]:
        """Convert Euler angles to degrees: (yaw_deg, pitch_deg, roll_deg)."""
        yaw, pitch, roll = self.to_euler_angles()
        return math.degrees(yaw), math.degrees(pitch), math.degrees(roll)

    def __repr__(self) -> str:
        return f"Quaternion(x={self.x:.4f}, y={self.y:.4f}, z={self.z:.4f}, w={self.w:.4f})"


class EMAFilter:
    """
    Exponential Moving Average filter for 2D delta motion smoothing.
    smoothing_factor in [0.0, 1.0):
      0.0 = no smoothing (raw response)
      0.9 = heavy smoothing (reduced jitter, higher latency)
    """
    def __init__(self, smoothing_factor: float = 0.3):
        self.smoothing = max(0.0, min(0.95, float(smoothing_factor)))
        self._filtered_x: float = 0.0
        self._filtered_y: float = 0.0
        self._initialized: bool = False

    def reset(self):
        self._filtered_x = 0.0
        self._filtered_y = 0.0
        self._initialized = False

    def set_smoothing(self, factor: float):
        self.smoothing = max(0.0, min(0.95, float(factor)))

    def filter(self, dx: float, dy: float) -> Tuple[float, float]:
        if not self._initialized:
            self._filtered_x = dx
            self._filtered_y = dy
            self._initialized = True
            return dx, dy

        alpha = 1.0 - self.smoothing
        self._filtered_x = alpha * dx + (1.0 - alpha) * self._filtered_x
        self._filtered_y = alpha * dy + (1.0 - alpha) * self._filtered_y
        return self._filtered_x, self._filtered_y


class OneEuroFilter:
    """
    1€ (One Euro) Filter:
    Adaptive low-pass filter specifically designed for human-motion tracking.
    Provides heavy smoothing at low speeds to eliminate jitter and tremor,
    while automatically reducing lag to near-zero during fast hand flicks.
    """
    def __init__(self, min_cutoff: float = 1.2, beta: float = 0.015, d_cutoff: float = 1.0):
        self.min_cutoff = float(min_cutoff)
        self.beta = float(beta)
        self.d_cutoff = float(d_cutoff)
        self.x_prev = 0.0
        self.dx_prev = 0.0
        self.initialized = False

    def reset(self):
        self.x_prev = 0.0
        self.dx_prev = 0.0
        self.initialized = False

    def _alpha(self, rate: float, cutoff: float) -> float:
        tau = 1.0 / (2.0 * math.pi * cutoff)
        te = 1.0 / rate if rate > 0 else 0.01
        return 1.0 / (1.0 + tau / te)

    def filter(self, x: float, rate: float = 100.0) -> float:
        if not self.initialized:
            self.x_prev = x
            self.dx_prev = 0.0
            self.initialized = True
            return x

        rate = max(10.0, min(500.0, float(rate)))
        dx = (x - self.x_prev) * rate
        a_d = self._alpha(rate, self.d_cutoff)
        dx_hat = a_d * dx + (1.0 - a_d) * self.dx_prev

        cutoff = self.min_cutoff + self.beta * abs(dx_hat)
        a = self._alpha(rate, cutoff)
        x_hat = a * x + (1.0 - a) * self.x_prev

        self.x_prev = x_hat
        self.dx_prev = dx_hat
        return x_hat


def apply_deadzone(val: float, threshold: float) -> float:
    """
    Smooth deadzone: removes tremors below threshold while avoiding
    a sudden jerk when passing the threshold.
    """
    if abs(val) <= threshold:
        return 0.0
    sign = 1.0 if val > 0 else -1.0
    return sign * (abs(val) - threshold)


def apply_acceleration(dx: float, dy: float, factor: float, threshold: float = 3.0) -> Tuple[float, float]:
    """
    Non-linear cursor acceleration curve.
    Fast phone flicks produce accelerated cursor leaps, while slow movements
    remain pixel-precise.
    """
    if factor <= 0.0:
        return dx, dy

    mag = math.sqrt(dx * dx + dy * dy)
    if mag <= threshold:
        return dx, dy

    # Scale multiplier above threshold capped at 3.5x boost
    overage = mag - threshold
    boost = 1.0 + factor * min(overage / threshold, 3.5)
    return dx * boost, dy * boost
