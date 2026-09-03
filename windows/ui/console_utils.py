"""
Console & Logging Utilities for Andromote Windows Receiver:
- Dynamic show/hide of the Windows OS console (terminal) window.
- In-memory thread-safe log buffer with Qt signal dispatching.
- Modern Live Log Viewer dialog.
- Settings Dialog with terminal toggle and configuration options.
"""

import sys
import ctypes
import logging
import collections
from datetime import datetime
from typing import Optional, Deque

from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QCheckBox, QGroupBox, QGridLayout, QPlainTextEdit, QLineEdit,
    QComboBox, QFrame, QMessageBox
)
from PySide6.QtCore import Qt, Signal, QObject
from PySide6.QtGui import QFont, QTextCursor, QColor

logger = logging.getLogger("console_utils")

SW_HIDE = 0
SW_SHOW = 5


def get_console_hwnd():
    """Retrieve the HWND of the attached Windows console window."""
    if sys.platform == "win32":
        try:
            return ctypes.windll.kernel32.GetConsoleWindow()
        except Exception:
            return 0
    return 0


def set_console_visible(visible: bool) -> bool:
    """
    Shows or hides the Windows console (terminal) window.
    Returns True if an operation was successfully performed.
    """
    if sys.platform != "win32":
        return False

    try:
        kernel32 = ctypes.windll.kernel32
        user32 = ctypes.windll.user32
        hwnd = kernel32.GetConsoleWindow()

        if not hwnd and visible:
            kernel32.AllocConsole()
            hwnd = kernel32.GetConsoleWindow()

        if hwnd:
            cmd = SW_SHOW if visible else SW_HIDE
            user32.ShowWindow(hwnd, cmd)
            return True
    except Exception as e:
        logger.debug(f"Failed to toggle console visibility: {e}")
    return False


def is_console_visible() -> bool:
    """Check if the attached Windows console window is currently visible."""
    if sys.platform != "win32":
        return False
    try:
        hwnd = ctypes.windll.kernel32.GetConsoleWindow()
        if hwnd:
            return bool(ctypes.windll.user32.IsWindowVisible(hwnd))
    except Exception:
        pass
    return False


class LogSignalEmitter(QObject):
    sig_log = Signal(str, str, str)  # (timestamp, level, message)


class InAppLogHandler(logging.Handler):
    """
    Custom logging handler storing recent log messages and dispatching Qt signals.
    """
    _instance: Optional["InAppLogHandler"] = None

    def __init__(self, capacity: int = 1000):
        super().__init__()
        self.capacity = capacity
        self.buffer: Deque[dict] = collections.deque(maxlen=capacity)
        self.emitter = LogSignalEmitter()

    def emit(self, record: logging.LogRecord):
        try:
            msg = self.format(record)
            time_str = datetime.fromtimestamp(record.created).strftime("%H:%M:%S")
            entry = {
                "time": time_str,
                "level": record.levelname,
                "name": record.name,
                "message": msg
            }
            self.buffer.append(entry)
            self.emitter.sig_log.emit(time_str, record.levelname, msg)
        except Exception:
            self.handleError(record)

    @classmethod
    def get_instance(cls) -> "InAppLogHandler":
        if cls._instance is None:
            cls._instance = InAppLogHandler()
            formatter = logging.Formatter("[%(asctime)s] [%(levelname)s] [%(name)s]: %(message)s", datefmt="%H:%M:%S")
            cls._instance.setFormatter(formatter)
            logging.getLogger().addHandler(cls._instance)
        return cls._instance


class LogViewerDialog(QDialog):
    """
    Sleek, dark-mode terminal log viewer dialog matching the website aesthetic.
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Andromote — Live Debug Terminal")
        self.resize(740, 480)
        self.setMinimumSize(600, 360)

        self.handler = InAppLogHandler.get_instance()
        self.handler.emitter.sig_log.connect(self._on_new_log)

        self._init_ui()
        self._load_existing_logs()

    def _init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(10)

        # Header bar
        header = QHBoxLayout()
        title = QLabel("Debug Log Terminal")
        title.setStyleSheet("color: #5AE7FF; font-size: 16px; font-weight: 800; font-family: 'JetBrains Mono', monospace;")
        header.addWidget(title)

        badge = QLabel("● LIVE")
        badge.setStyleSheet("color: #4ADE80; font-size: 11px; font-weight: bold; background: rgba(74,222,128,0.12); padding: 3px 8px; border-radius: 100px;")
        header.addWidget(badge)
        header.addStretch()

        # Search & Filter
        self.search_box = QLineEdit()
        self.search_box.setPlaceholderText("Filter logs...")
        self.search_box.setStyleSheet("background-color: #14141C; color: #F5F5F7; border: 1px solid rgba(255,255,255,0.1); border-radius: 6px; padding: 4px 10px;")
        self.search_box.textChanged.connect(self._reload_logs)
        header.addWidget(self.search_box)

        self.combo_level = QComboBox()
        self.combo_level.addItems(["ALL", "INFO", "WARNING", "ERROR", "DEBUG"])
        self.combo_level.currentTextChanged.connect(self._reload_logs)
        header.addWidget(self.combo_level)

        layout.addLayout(header)

        # Log output text view
        self.txt_logs = QPlainTextEdit()
        self.txt_logs.setReadOnly(True)
        self.txt_logs.setFont(QFont("Consolas", 10))
        self.txt_logs.setStyleSheet("""
            QPlainTextEdit {
                background-color: #08080C;
                color: #A0A0AA;
                border: 1px solid rgba(255, 255, 255, 0.08);
                border-radius: 8px;
                padding: 10px;
                font-family: 'JetBrains Mono', 'Consolas', monospace;
                font-size: 12px;
                line-height: 1.4;
            }
        """)
        layout.addWidget(self.txt_logs)

        # Bottom Bar
        bottom = QHBoxLayout()
        self.chk_autoscroll = QCheckBox("Auto-scroll")
        self.chk_autoscroll.setChecked(True)
        bottom.addWidget(self.chk_autoscroll)

        bottom.addStretch()

        btn_copy = QPushButton("Copy All")
        btn_copy.clicked.connect(self._copy_logs)
        bottom.addWidget(btn_copy)

        btn_clear = QPushButton("Clear")
        btn_clear.clicked.connect(self._clear_logs)
        bottom.addWidget(btn_clear)

        btn_close = QPushButton("Close")
        btn_close.clicked.connect(self.accept)
        bottom.addWidget(btn_close)

        layout.addLayout(bottom)

    def _append_formatted(self, level: str, text: str):
        color_map = {
            "ERROR": "#FF6B6B",
            "WARNING": "#FBBF24",
            "INFO": "#F5F5F7",
            "DEBUG": "#60606A"
        }
        color = color_map.get(level, "#A0A0AA")
        html = f'<span style="color: {color};">{text}</span>'
        self.txt_logs.appendHtml(html)

        if self.chk_autoscroll.isChecked():
            self.txt_logs.moveCursor(QTextCursor.End)

    def _matches_filter(self, entry: dict) -> bool:
        sel_level = self.combo_level.currentText()
        if sel_level != "ALL" and entry["level"] != sel_level:
            return False
        q = self.search_box.text().strip().lower()
        if q and q not in entry["message"].lower():
            return False
        return True

    def _reload_logs(self):
        self.txt_logs.clear()
        for entry in self.handler.buffer:
            if self._matches_filter(entry):
                self._append_formatted(entry["level"], entry["message"])

    def _load_existing_logs(self):
        self._reload_logs()

    def _on_new_log(self, time_str: str, level: str, msg: str):
        entry = {"time": time_str, "level": level, "message": msg}
        if self._matches_filter(entry):
            self._append_formatted(level, msg)

    def _copy_logs(self):
        from PySide6.QtWidgets import QApplication
        QApplication.clipboard().setText(self.txt_logs.toPlainText())

    def _clear_logs(self):
        self.handler.buffer.clear()
        self.txt_logs.clear()


class SettingsDialog(QDialog):
    """
    Settings dialog containing:
    - Debug Terminal toggle (Show/Hide OS console window)
    - Live Log Viewer launcher
    - Verbose Logging toggle
    - Network ports and general behavior
    """

    def __init__(self, settings_manager, parent=None):
        super().__init__(parent)
        self.settings = settings_manager
        self.setWindowTitle("Andromote Settings")
        self.resize(520, 420)
        self.setMinimumSize(460, 380)

        self._init_ui()

    def _init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(18, 18, 18, 18)
        layout.setSpacing(14)

        # Header Title
        title = QLabel("Application Settings")
        title.setStyleSheet("font-size: 18px; font-weight: 800; color: #5AE7FF; letter-spacing: -0.02em;")
        layout.addWidget(title)

        # 1. Debug Terminal & Logging Group
        grp_term = QGroupBox("Terminal & Logging")
        vbox_term = QVBoxLayout(grp_term)
        vbox_term.setSpacing(8)

        self.chk_terminal = QCheckBox("Show Debug Terminal (Console Window)")
        self.chk_terminal.setChecked(self.settings.get("show_debug_terminal", False))
        self.chk_terminal.toggled.connect(self._on_terminal_toggled)
        vbox_term.addWidget(self.chk_terminal)

        lbl_term_desc = QLabel("Displays the command prompt terminal. Keep hidden for a quiet background experience, or toggle on to inspect low-level stream logs.")
        lbl_term_desc.setStyleSheet("color: #A0A0AA; font-size: 11px; margin-left: 26px; line-height: 1.4;")
        lbl_term_desc.setWordWrap(True)
        vbox_term.addWidget(lbl_term_desc)

        self.chk_verbose = QCheckBox("Enable Verbose Debug Logging (High Frequency)")
        self.chk_verbose.setChecked(self.settings.get("verbose_logging", False))
        self.chk_verbose.toggled.connect(self._on_verbose_toggled)
        vbox_term.addWidget(self.chk_verbose)

        btn_open_viewer = QPushButton("Open Live Log Terminal")
        btn_open_viewer.setStyleSheet("background-color: #1A1A24; color: #5AE7FF; border: 1px solid rgba(90, 231, 255, 0.3); padding: 6px 14px; font-weight: 600; border-radius: 6px;")
        btn_open_viewer.clicked.connect(self._open_log_viewer)
        vbox_term.addWidget(btn_open_viewer)

        layout.addWidget(grp_term)

        # 2. General Preferences Group
        grp_gen = QGroupBox("General Preferences")
        grid_gen = QGridLayout(grp_gen)

        self.chk_dsu = QCheckBox("Enable Dolphin DSU Server (Port 26760)")
        self.chk_dsu.setChecked(self.settings.get("dsu_enabled", True))
        self.chk_dsu.toggled.connect(lambda v: self.settings.set("dsu_enabled", v))
        grid_gen.addWidget(self.chk_dsu, 0, 0, 1, 2)

        self.chk_tray = QCheckBox("Minimize to System Tray on Close")
        self.chk_tray.setChecked(self.settings.get("minimize_to_tray", True))
        self.chk_tray.toggled.connect(lambda v: self.settings.set("minimize_to_tray", v))
        grid_gen.addWidget(self.chk_tray, 1, 0, 1, 2)

        layout.addWidget(grp_gen)

        layout.addStretch()

        # Bottom Action Bar
        bottom = QHBoxLayout()
        btn_reset = QPushButton("Reset Defaults")
        btn_reset.setStyleSheet("background-color: transparent; color: #FF6B6B; border: 1px solid rgba(255, 107, 107, 0.3);")
        btn_reset.clicked.connect(self._on_reset_defaults)
        bottom.addWidget(btn_reset)

        bottom.addStretch()

        btn_done = QPushButton("Done")
        btn_done.setStyleSheet("background-color: #5AE7FF; color: #08080C; font-weight: bold; padding: 8px 22px; border-radius: 6px;")
        btn_done.clicked.connect(self.accept)
        bottom.addWidget(btn_done)

        layout.addLayout(bottom)

    def _on_terminal_toggled(self, checked: bool):
        self.settings.set("show_debug_terminal", checked)
        success = set_console_visible(checked)
        if not success and checked:
            QMessageBox.information(
                self,
                "Terminal Notification",
                "Console window could not be attached directly in this environment. You can use the built-in 'Open Live Log Terminal' to inspect all live logs."
            )

    def _on_verbose_toggled(self, checked: bool):
        self.settings.set("verbose_logging", checked)
        new_level = logging.DEBUG if checked else logging.INFO
        logging.getLogger().setLevel(new_level)

    def _open_log_viewer(self):
        viewer = LogViewerDialog(self)
        viewer.exec()

    def _on_reset_defaults(self):
        reply = QMessageBox.question(
            self,
            "Reset Settings",
            "Are you sure you want to reset preferences to default values?",
            QMessageBox.Yes | QMessageBox.No
        )
        if reply == QMessageBox.Yes:
            self.settings.set("show_debug_terminal", False)
            self.settings.set("verbose_logging", False)
            self.settings.set("dsu_enabled", True)
            self.settings.set("minimize_to_tray", True)
            self.chk_terminal.setChecked(False)
            self.chk_verbose.setChecked(False)
            self.chk_dsu.setChecked(True)
            self.chk_tray.setChecked(True)
            set_console_visible(False)
