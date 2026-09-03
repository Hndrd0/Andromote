"""
Virtual Key and Mouse Definitions for Windows Input Injection.
Provides friendly mappings, scan code resolution, and input classification.
"""

# Windows Mouse Event Flags
MOUSEEVENTF_MOVE = 0x0001
MOUSEEVENTF_LEFTDOWN = 0x0002
MOUSEEVENTF_LEFTUP = 0x0004
MOUSEEVENTF_RIGHTDOWN = 0x0008
MOUSEEVENTF_RIGHTUP = 0x0010
MOUSEEVENTF_MIDDLEDOWN = 0x0020
MOUSEEVENTF_MIDDLEUP = 0x0040
MOUSEEVENTF_XDOWN = 0x0080
MOUSEEVENTF_XUP = 0x0100
MOUSEEVENTF_WHEEL = 0x0800
MOUSEEVENTF_ABSOLUTE = 0x8000

# Input Types
INPUT_MOUSE = 0
INPUT_KEYBOARD = 1
INPUT_HARDWARE = 2

# Keyboard Flags
KEYEVENTF_EXTENDEDKEY = 0x0001
KEYEVENTF_KEYUP = 0x0002
KEYEVENTF_UNICODE = 0x0004
KEYEVENTF_SCANCODE = 0x0008

# Standard Windows Virtual-Key Codes
VK_LBUTTON = 0x01
VK_RBUTTON = 0x02
VK_CANCEL = 0x03
VK_MBUTTON = 0x04
VK_XBUTTON1 = 0x05
VK_XBUTTON2 = 0x06
VK_BACK = 0x08
VK_TAB = 0x09
VK_CLEAR = 0x0C
VK_RETURN = 0x0D
VK_SHIFT = 0x10
VK_CONTROL = 0x11
VK_MENU = 0x12       # ALT
VK_PAUSE = 0x13
VK_CAPITAL = 0x14
VK_ESCAPE = 0x1B
VK_SPACE = 0x20
VK_PRIOR = 0x21      # PAGE UP
VK_NEXT = 0x22       # PAGE DOWN
VK_END = 0x23
VK_HOME = 0x24
VK_LEFT = 0x25
VK_UP = 0x26
VK_RIGHT = 0x27
VK_DOWN = 0x28
VK_SELECT = 0x29
VK_PRINT = 0x2A
VK_EXECUTE = 0x2B
VK_SNAPSHOT = 0x2C   # PRINT SCREEN
VK_INSERT = 0x2D
VK_DELETE = 0x2E
VK_HELP = 0x2F

# Digits 0-9: 0x30 - 0x39
# Alphabet A-Z: 0x41 - 0x5A
VK_LWIN = 0x5B
VK_RWIN = 0x5C
VK_APPS = 0x5D
VK_NUMPAD0 = 0x60
VK_NUMPAD1 = 0x61
VK_NUMPAD2 = 0x62
VK_NUMPAD3 = 0x63
VK_NUMPAD4 = 0x64
VK_NUMPAD5 = 0x65
VK_NUMPAD6 = 0x66
VK_NUMPAD7 = 0x67
VK_NUMPAD8 = 0x68
VK_NUMPAD9 = 0x69
VK_MULTIPLY = 0x6A
VK_ADD = 0x6B
VK_SEPARATOR = 0x6C
VK_SUBTRACT = 0x6D
VK_DECIMAL = 0x6E
VK_DIVIDE = 0x6F
VK_F1 = 0x70
VK_F2 = 0x71
VK_F3 = 0x72
VK_F4 = 0x73
VK_F5 = 0x74
VK_F6 = 0x75
VK_F7 = 0x76
VK_F8 = 0x77
VK_F9 = 0x78
VK_F10 = 0x79
VK_F11 = 0x7A
VK_F12 = 0x7B

VK_OEM_1 = 0xBA      # ;:
VK_OEM_PLUS = 0xBB   # =+
VK_OEM_COMMA = 0xBC  # ,<
VK_OEM_MINUS = 0xBD  # -_
VK_OEM_PERIOD = 0xBE # .>
VK_OEM_2 = 0xBF      # /?
VK_OEM_3 = 0xC0      # `~
VK_OEM_4 = 0xDB      # [{
VK_OEM_5 = 0xDC      # \|
VK_OEM_6 = 0xDD      # ]}
VK_OEM_7 = 0xDE      # '"

# Extended keys that require KEYEVENTF_EXTENDEDKEY flag
EXTENDED_KEYS = {
    VK_UP, VK_DOWN, VK_LEFT, VK_RIGHT,
    VK_HOME, VK_END, VK_PRIOR, VK_NEXT,
    VK_INSERT, VK_DELETE,
    VK_LWIN, VK_RWIN, VK_APPS,
    VK_DIVIDE,
}

# Action Mapping Dictionary (Friendly String -> (Category, Identifier))
FRIENDLY_ACTIONS = {
    # Mouse Actions
    "MOUSE_LEFT": ("mouse", "left"),
    "MOUSE_RIGHT": ("mouse", "right"),
    "MOUSE_MIDDLE": ("mouse", "middle"),
    "MOUSE_WHEEL_UP": ("mouse_wheel", 120),
    "MOUSE_WHEEL_DOWN": ("mouse_wheel", -120),

    # Motion Recenter
    "RECENTER": ("system", "recenter"),
    "NONE": ("none", None),

    # Common Keyboard Keys
    "KEY_UP": ("keyboard", VK_UP),
    "KEY_DOWN": ("keyboard", VK_DOWN),
    "KEY_LEFT": ("keyboard", VK_LEFT),
    "KEY_RIGHT": ("keyboard", VK_RIGHT),
    "KEY_ENTER": ("keyboard", VK_RETURN),
    "KEY_SPACE": ("keyboard", VK_SPACE),
    "KEY_ESCAPE": ("keyboard", VK_ESCAPE),
    "KEY_TAB": ("keyboard", VK_TAB),
    "KEY_BACKSPACE": ("keyboard", VK_BACK),
    "KEY_SHIFT": ("keyboard", VK_SHIFT),
    "KEY_CTRL": ("keyboard", VK_CONTROL),
    "KEY_ALT": ("keyboard", VK_MENU),
    "KEY_PLUS": ("keyboard", VK_OEM_PLUS),
    "KEY_MINUS": ("keyboard", VK_OEM_MINUS),

    # Numbers
    "KEY_1": ("keyboard", ord('1')),
    "KEY_2": ("keyboard", ord('2')),
    "KEY_3": ("keyboard", ord('3')),
    "KEY_4": ("keyboard", ord('4')),
    "KEY_0": ("keyboard", ord('0')),

    # Letters commonly used in gaming
    "KEY_W": ("keyboard", ord('W')),
    "KEY_A": ("keyboard", ord('A')),
    "KEY_S": ("keyboard", ord('S')),
    "KEY_D": ("keyboard", ord('D')),
    "KEY_E": ("keyboard", ord('E')),
    "KEY_Q": ("keyboard", ord('Q')),
    "KEY_R": ("keyboard", ord('R')),
    "KEY_F": ("keyboard", ord('F')),
    "KEY_Z": ("keyboard", ord('Z')),
    "KEY_X": ("keyboard", ord('X')),
    "KEY_C": ("keyboard", ord('C')),
}

# Default Wii Remote Button Mappings
DEFAULT_BUTTON_MAPPINGS = {
    "DPAD_UP": "KEY_UP",
    "DPAD_DOWN": "KEY_DOWN",
    "DPAD_LEFT": "KEY_LEFT",
    "DPAD_RIGHT": "KEY_RIGHT",
    "A": "MOUSE_LEFT",
    "B": "MOUSE_RIGHT",
    "1": "KEY_1",
    "2": "KEY_2",
    "PLUS": "KEY_PLUS",
    "MINUS": "KEY_MINUS",
    "HOME": "RECENTER",
}
