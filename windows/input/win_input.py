"""
Windows SendInput implementation for mouse and keyboard control.
Includes tracking of held inputs, thread safety, scan code translation,
failsafe release, and dry-run/mock mode for testing.
"""

import ctypes
from ctypes import wintypes
import logging
import threading
from typing import Set, Tuple, Optional

from .keycodes import (
    INPUT_MOUSE, INPUT_KEYBOARD,
    MOUSEEVENTF_MOVE, MOUSEEVENTF_LEFTDOWN, MOUSEEVENTF_LEFTUP,
    MOUSEEVENTF_RIGHTDOWN, MOUSEEVENTF_RIGHTUP,
    MOUSEEVENTF_MIDDLEDOWN, MOUSEEVENTF_MIDDLEUP,
    MOUSEEVENTF_WHEEL,
    KEYEVENTF_EXTENDEDKEY, KEYEVENTF_KEYUP, KEYEVENTF_SCANCODE,
    EXTENDED_KEYS
)

logger = logging.getLogger("win_input")

# Windows API Structures
ULONG_PTR = ctypes.c_ulonglong if ctypes.sizeof(ctypes.c_void_p) == 8 else ctypes.c_ulong

class MOUSEINPUT(ctypes.Structure):
    _fields_ = [
        ("dx", ctypes.c_long),
        ("dy", ctypes.c_long),
        ("mouseData", ctypes.c_ulong),
        ("dwFlags", ctypes.c_ulong),
        ("time", ctypes.c_ulong),
        ("dwExtraInfo", ULONG_PTR)
    ]

class KEYBDINPUT(ctypes.Structure):
    _fields_ = [
        ("wVk", ctypes.c_ushort),
        ("wScan", ctypes.c_ushort),
        ("dwFlags", ctypes.c_ulong),
        ("time", ctypes.c_ulong),
        ("dwExtraInfo", ULONG_PTR)
    ]

class HARDWAREINPUT(ctypes.Structure):
    _fields_ = [
        ("uMsg", ctypes.c_ulong),
        ("wParamL", ctypes.c_ushort),
        ("wParamH", ctypes.c_ushort)
    ]

class _INPUTunion(ctypes.Union):
    _fields_ = [
        ("mi", MOUSEINPUT),
        ("ki", KEYBDINPUT),
        ("hi", HARDWAREINPUT)
    ]

class INPUT(ctypes.Structure):
    _fields_ = [
        ("type", ctypes.c_ulong),
        ("union", _INPUTunion)
    ]


class WindowsInputController:
    """
    Direct Windows input injection controller wrapping user32.dll SendInput.
    """

    MAPVK_VK_TO_VSC = 0

    def __init__(self, mock_mode: bool = False):
        self.mock_mode = mock_mode
        self._lock = threading.RLock()
        self._held_mouse_buttons: Set[str] = set()
        self._held_keys: Set[int] = set()
        self._action_log = []  # For verification in mock_mode
        self._enabled = True

        if not self.mock_mode:
            try:
                self._user32 = ctypes.WinDLL('user32', use_last_error=True)
                self._send_input = self._user32.SendInput
                self._send_input.argtypes = [ctypes.c_uint, ctypes.POINTER(INPUT), ctypes.c_int]
                self._send_input.restype = ctypes.c_uint
                self._map_virtual_key = self._user32.MapVirtualKeyW
                self._map_virtual_key.argtypes = [ctypes.c_uint, ctypes.c_uint]
                self._map_virtual_key.restype = ctypes.c_uint
            except Exception as e:
                logger.error(f"Failed to load user32.dll: {e}. Falling back to mock mode.")
                self.mock_mode = True

    @property
    def enabled(self) -> bool:
        with self._lock:
            return self._enabled

    @enabled.setter
    def enabled(self, value: bool):
        with self._lock:
            if not value and self._enabled:
                self.release_all_inputs()
            self._enabled = bool(value)

    def _send(self, input_struct: INPUT) -> bool:
        """Internal helper to send a single INPUT struct."""
        if not self._enabled:
            return False

        if self.mock_mode:
            return True

        n = self._send_input(1, ctypes.byref(input_struct), ctypes.sizeof(INPUT))
        if n != 1:
            err = ctypes.get_last_error()
            logger.warning(f"SendInput returned {n}, error code {err}")
            return False
        return True

    def move_cursor_relative(self, dx: int, dy: int) -> bool:
        """
        Move Windows mouse cursor relatively by dx, dy.
        """
        if dx == 0 and dy == 0:
            return True

        with self._lock:
            if not self._enabled:
                return False

            if self.mock_mode:
                self._action_log.append(("move", dx, dy))
                return True

            inp = INPUT(type=INPUT_MOUSE)
            inp.union.mi = MOUSEINPUT(
                dx=int(dx),
                dy=int(dy),
                mouseData=0,
                dwFlags=MOUSEEVENTF_MOVE,
                time=0,
                dwExtraInfo=0
            )
            ok = self._send(inp)
            if not ok and hasattr(self, '_user32'):
                try:
                    self._user32.mouse_event(MOUSEEVENTF_MOVE, int(dx), int(dy), 0, 0)
                    return True
                except Exception as e:
                    logger.debug(f"mouse_event fallback failed: {e}")
            return ok

    def mouse_down(self, button: str) -> bool:
        """
        Press mouse button ('left', 'right', 'middle').
        """
        button = button.lower()
        flag_map = {
            "left": MOUSEEVENTF_LEFTDOWN,
            "right": MOUSEEVENTF_RIGHTDOWN,
            "middle": MOUSEEVENTF_MIDDLEDOWN
        }
        flag = flag_map.get(button)
        if not flag:
            logger.warning(f"Unsupported mouse button: {button}")
            return False

        with self._lock:
            if not self._enabled:
                return False

            self._held_mouse_buttons.add(button)
            if self.mock_mode:
                self._action_log.append(("mouse_down", button))
                return True

            inp = INPUT(type=INPUT_MOUSE)
            inp.union.mi = MOUSEINPUT(
                dx=0, dy=0, mouseData=0,
                dwFlags=flag,
                time=0, dwExtraInfo=0
            )
            ok = self._send(inp)
            if not ok and hasattr(self, '_user32'):
                try:
                    self._user32.mouse_event(flag, 0, 0, 0, 0)
                    return True
                except Exception:
                    pass
            return ok

    def mouse_up(self, button: str) -> bool:
        """
        Release mouse button ('left', 'right', 'middle').
        """
        button = button.lower()
        flag_map = {
            "left": MOUSEEVENTF_LEFTUP,
            "right": MOUSEEVENTF_RIGHTUP,
            "middle": MOUSEEVENTF_MIDDLEUP
        }
        flag = flag_map.get(button)
        if not flag:
            return False

        with self._lock:
            self._held_mouse_buttons.discard(button)
            if not self._enabled:
                return False

            if self.mock_mode:
                self._action_log.append(("mouse_up", button))
                return True

            inp = INPUT(type=INPUT_MOUSE)
            inp.union.mi = MOUSEINPUT(
                dx=0, dy=0, mouseData=0,
                dwFlags=flag,
                time=0, dwExtraInfo=0
            )
            ok = self._send(inp)
            if not ok and hasattr(self, '_user32'):
                try:
                    self._user32.mouse_event(flag, 0, 0, 0, 0)
                    return True
                except Exception:
                    pass
            return ok

    def mouse_wheel(self, delta: int) -> bool:
        """Scroll mouse wheel vertically by delta (120 = 1 tick up, -120 = 1 tick down)."""
        with self._lock:
            if not self._enabled:
                return False

            if self.mock_mode:
                self._action_log.append(("mouse_wheel", delta))
                return True

            inp = INPUT(type=INPUT_MOUSE)
            inp.union.mi = MOUSEINPUT(
                dx=0, dy=0,
                mouseData=delta & 0xFFFFFFFF,
                dwFlags=MOUSEEVENTF_WHEEL,
                time=0, dwExtraInfo=0
            )
            ok = self._send(inp)
            if not ok and hasattr(self, '_user32'):
                try:
                    self._user32.mouse_event(MOUSEEVENTF_WHEEL, 0, 0, delta & 0xFFFFFFFF, 0)
                    return True
                except Exception:
                    pass
            return ok

    def key_down(self, vk_code: int) -> bool:
        """
        Press a keyboard key given its Virtual-Key code.
        """
        with self._lock:
            if not self._enabled:
                return False

            self._held_keys.add(vk_code)
            if self.mock_mode:
                self._action_log.append(("key_down", vk_code))
                return True

            scan_code = self._map_virtual_key(vk_code, self.MAPVK_VK_TO_VSC)
            flags = 0
            if vk_code in EXTENDED_KEYS:
                flags |= KEYEVENTF_EXTENDEDKEY

            inp = INPUT(type=INPUT_KEYBOARD)
            inp.union.ki = KEYBDINPUT(
                wVk=vk_code,
                wScan=scan_code,
                dwFlags=flags,
                time=0,
                dwExtraInfo=0
            )
            return self._send(inp)

    def key_up(self, vk_code: int) -> bool:
        """
        Release a keyboard key given its Virtual-Key code.
        """
        with self._lock:
            self._held_keys.discard(vk_code)
            if not self._enabled:
                return False

            if self.mock_mode:
                self._action_log.append(("key_up", vk_code))
                return True

            scan_code = self._map_virtual_key(vk_code, self.MAPVK_VK_TO_VSC)
            flags = KEYEVENTF_KEYUP
            if vk_code in EXTENDED_KEYS:
                flags |= KEYEVENTF_EXTENDEDKEY

            inp = INPUT(type=INPUT_KEYBOARD)
            inp.union.ki = KEYBDINPUT(
                wVk=vk_code,
                wScan=scan_code,
                dwFlags=flags,
                time=0,
                dwExtraInfo=0
            )
            return self._send(inp)

    def release_all_inputs(self):
        """
        CRITICAL FAILSAFE:
        Releases every currently-held mouse button and keyboard key.
        Guarantees that no keys or mouse buttons remain stuck down if
        the connection drops or the controller is disabled.
        """
        with self._lock:
            # Release all held mouse buttons
            for btn in list(self._held_mouse_buttons):
                logger.info(f"Failsafe: Releasing stuck mouse button '{btn}'")
                self.mouse_up(btn)
            self._held_mouse_buttons.clear()

            # Release all held keyboard keys
            for vk in list(self._held_keys):
                logger.info(f"Failsafe: Releasing stuck keyboard key 0x{vk:02X}")
                self.key_up(vk)
            self._held_keys.clear()

    def get_held_inputs(self) -> Tuple[Set[str], Set[int]]:
        """Return a snapshot of currently held (mouse_buttons, keyboard_keys)."""
        with self._lock:
            return set(self._held_mouse_buttons), set(self._held_keys)


# Global singleton instance
_controller_instance: Optional[WindowsInputController] = None

def get_input_controller(mock_mode: bool = False) -> WindowsInputController:
    global _controller_instance
    if _controller_instance is None:
        _controller_instance = WindowsInputController(mock_mode=mock_mode)
    return _controller_instance
