"""
Motion Processing Package
"""
from .math_utils import Quaternion, EMAFilter, apply_deadzone, apply_acceleration
from .processor import MotionProcessor

__all__ = ["Quaternion", "EMAFilter", "apply_deadzone", "apply_acceleration", "MotionProcessor"]
