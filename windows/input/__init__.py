"""
Windows Input Package
"""
from .win_input import WindowsInputController, get_input_controller
from .keycodes import FRIENDLY_ACTIONS, DEFAULT_BUTTON_MAPPINGS

__all__ = ["WindowsInputController", "get_input_controller", "FRIENDLY_ACTIONS", "DEFAULT_BUTTON_MAPPINGS"]
