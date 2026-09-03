"""
PySide6 Main Window:
Complete graphical interface with real-time motion diagnostics HUD,
pairing PIN display, motion curve tuning sliders, button mapping matrix,
Dolphin DSU status, and Windows system tray integration.
"""

import sys
import os
import time
import socket
from typing import Optional

from PySide6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QTabWidget, QGroupBox, QSlider, QDoubleSpinBox,
    QCheckBox, QComboBox, QTableWidget, QTableWidgetItem, QHeaderView,
    QSystemTrayIcon, QMenu, QMessageBox, QGridLayout, QFrame
)
from PySide6.QtCore import Qt, QTimer, Signal, Slot
from PySide6.QtGui import QIcon, QAction, QColor, QFont

from .styles import DARK_STYLESHEET
from ..config.settings_manager import SettingsManager
from ..input.win_input import WindowsInputController
from ..input.keycodes import FRIENDLY_ACTIONS
from ..motion.processor import MotionProcessor
from ..networking.pairing import PairingManager
from ..networking.tcp_server import TCPServer
from ..networking.udp_motion_server import UDPMotionServer
from ..networking.discovery_server import DiscoveryServer, get_local_ip


class MainWindow(QMainWindow):
    """
    Main desktop window for Andromote receiver.
    """

    sig_state_change = Signal(str, str)
    sig_latency_update = Signal(float)
    sig_rate_update = Signal(float)
    sig_gesture_trigger = Signal(str, bool)

    def __init__(self,
                 settings: SettingsManager,
                 input_ctrl: WindowsInputController,
                 motion_proc: MotionProcessor,
                 pairing_mgr: PairingManager,
                 tcp_srv: TCPServer,
                 udp_srv: UDPMotionServer,
                 discovery_srv: DiscoveryServer,
                 dsu_srv=None,
                 gesture_eng=None):
        super().__init__()
        self.settings = settings
        self.input_ctrl = input_ctrl
        self.motion_proc = motion_proc
        self.pairing_mgr = pairing_mgr
        self.tcp_srv = tcp_srv
        self.udp_srv = udp_srv
        self.discovery_srv = discovery_srv
        self.dsu_srv = dsu_srv
        self.gesture_eng = gesture_eng
        self._gesture_badges = {}

        self.setWindowTitle("Andromote — Wii Remote PC Receiver")
        self.resize(780, 640)
        self.setMinimumSize(700, 560)
        self.setStyleSheet(DARK_STYLESHEET)

        # Wire network signals to Qt main thread
        self.sig_state_change.connect(self._on_connection_state_changed)
        self.sig_latency_update.connect(self._on_latency_updated)
        self.sig_rate_update.connect(self._on_rate_updated)
        self.sig_gesture_trigger.connect(self._on_gesture_triggered)

        self.tcp_srv.on_state_change = lambda s, d: self.sig_state_change.emit(s, d or "")
        self.tcp_srv.on_latency_update = lambda lat: self.sig_latency_update.emit(lat)
        self.udp_srv.on_rate_update = lambda hz: self.sig_rate_update.emit(hz)
        if self.gesture_eng:
            self.gesture_eng.on_gesture = lambda name, act: self.sig_gesture_trigger.emit(name, act)

        self._init_ui()
        self._init_tray()

        # Telemetry refresh timer (20 Hz)
        self._telemetry_timer = QTimer(self)
        self._telemetry_timer.timeout.connect(self._refresh_telemetry)
        self._telemetry_timer.start(50)

    def _init_ui(self):
        central = QWidget(self)
        central.setObjectName("CentralWidget")
        self.setCentralWidget(central)
        root_layout = QVBoxLayout(central)
        root_layout.setContentsMargins(16, 16, 16, 16)
        root_layout.setSpacing(12)

        # --- Top Header Bar ---
        header_frame = QFrame()
        header_layout = QHBoxLayout(header_frame)
        header_layout.setContentsMargins(0, 0, 0, 0)

        title_box = QVBoxLayout()
        title = QLabel("Andromote")
        title.setObjectName("HeaderTitle")
        subtitle = QLabel(f"IP: {get_local_ip()}  |  TCP: {self.tcp_srv.port}  |  Motion UDP: {self.udp_srv.port}")
        subtitle.setStyleSheet("color: #60606A; font-size: 11px; font-family: 'JetBrains Mono', 'Consolas', monospace;")
        title_box.addWidget(title)
        title_box.addWidget(subtitle)
        header_layout.addLayout(title_box)

        header_layout.addStretch()

        # Master Controller Switch
        self.btn_master_toggle = QPushButton("Controller: ENABLED")
        self.btn_master_toggle.setCheckable(True)
        self.btn_master_toggle.setChecked(self.input_ctrl.enabled)
        self.btn_master_toggle.setStyleSheet("background-color: #5AE7FF; color: #08080C; font-weight: bold; border-radius: 6px;")
        self.btn_master_toggle.clicked.connect(self._toggle_master_controller)
        header_layout.addWidget(self.btn_master_toggle)

        # Connection Status Badge
        self.lbl_status_badge = QLabel("LISTENING")
        self.lbl_status_badge.setObjectName("StatusBadge")
        self.lbl_status_badge.setStyleSheet("background-color: #14141C; color: #A0A0AA; border: 1px solid rgba(255, 255, 255, 0.1); border-radius: 100px; padding: 4px 12px;")
        header_layout.addWidget(self.lbl_status_badge)

        # Settings Button
        self.btn_settings = QPushButton("Settings")
        self.btn_settings.setStyleSheet("background-color: #1A1A24; color: #F5F5F7; border: 1px solid rgba(255, 255, 255, 0.12); border-radius: 6px; padding: 6px 14px; font-weight: 600;")
        self.btn_settings.clicked.connect(self._open_settings_dialog)
        header_layout.addWidget(self.btn_settings)

        root_layout.addWidget(header_frame)

        # --- Tabs ---
        self.tabs = QTabWidget()
        root_layout.addWidget(self.tabs)

        self.tab_dashboard = QWidget()
        self.tab_pairing = QWidget()
        self.tab_motion = QWidget()
        self.tab_mappings = QWidget()
        self.tab_gestures = QWidget()
        self.tab_dolphin = QWidget()

        self.tabs.addTab(self.tab_dashboard, "Dashboard")
        self.tabs.addTab(self.tab_pairing, "Pairing & Security")
        self.tabs.addTab(self.tab_motion, "Motion Tuning")
        self.tabs.addTab(self.tab_mappings, "Button Mappings")
        self.tabs.addTab(self.tab_gestures, "Wii Gestures")
        self.tabs.addTab(self.tab_dolphin, "Dolphin DSU")

        self._build_dashboard_tab()
        self._build_pairing_tab()
        self._build_motion_tab()
        self._build_mappings_tab()
        self._build_gestures_tab()
        self._build_dolphin_tab()

    # --- Dashboard Tab ---
    def _build_dashboard_tab(self):
        layout = QVBoxLayout(self.tab_dashboard)

        # Connection Card
        conn_group = QGroupBox("Connection Status")
        conn_layout = QGridLayout(conn_group)

        self.lbl_conn_device = QLabel("None (Waiting for connection)")
        self.lbl_conn_device.setStyleSheet("color: #F5F5F7; font-weight: 600;")
        self.lbl_conn_ip = QLabel("—")
        self.lbl_conn_ip.setStyleSheet("color: #F5F5F7; font-family: 'JetBrains Mono', monospace;")
        self.lbl_conn_latency = QLabel("0 ms")
        self.lbl_conn_latency.setStyleSheet("color: #4ADE80; font-family: 'JetBrains Mono', monospace; font-weight: 600;")
        self.lbl_conn_rate = QLabel("0 Hz")
        self.lbl_conn_rate.setStyleSheet("color: #5AE7FF; font-family: 'JetBrains Mono', monospace; font-weight: 600;")

        conn_layout.addWidget(QLabel("Connected Device:"), 0, 0)
        conn_layout.addWidget(self.lbl_conn_device, 0, 1)
        conn_layout.addWidget(QLabel("Device IP:"), 0, 2)
        conn_layout.addWidget(self.lbl_conn_ip, 0, 3)

        conn_layout.addWidget(QLabel("Network Latency:"), 1, 0)
        conn_layout.addWidget(self.lbl_conn_latency, 1, 1)
        conn_layout.addWidget(QLabel("Motion Packet Rate:"), 1, 2)
        conn_layout.addWidget(self.lbl_conn_rate, 1, 3)

        layout.addWidget(conn_group)

        # Live Sensor Diagnostics HUD
        telem_group = QGroupBox("Live Motion Diagnostics (Relative to Neutral)")
        telem_layout = QGridLayout(telem_group)

        self.lbl_yaw = QLabel("0.0°")
        self.lbl_yaw.setStyleSheet("color: #5AE7FF; font-family: 'JetBrains Mono', monospace; font-weight: 600;")
        self.lbl_pitch = QLabel("0.0°")
        self.lbl_pitch.setStyleSheet("color: #5AE7FF; font-family: 'JetBrains Mono', monospace; font-weight: 600;")
        self.lbl_roll = QLabel("0.0°")
        self.lbl_roll.setStyleSheet("color: #5AE7FF; font-family: 'JetBrains Mono', monospace; font-weight: 600;")
        self.lbl_gyro = QLabel("X: 0.00 | Y: 0.00 | Z: 0.00 rad/s")
        self.lbl_gyro.setStyleSheet("color: #A0A0AA; font-family: 'JetBrains Mono', monospace;")
        self.lbl_accel = QLabel("X: 0.00 | Y: 0.00 | Z: 0.00 m/s²")
        self.lbl_accel.setStyleSheet("color: #A0A0AA; font-family: 'JetBrains Mono', monospace;")
        self.lbl_packets = QLabel("0")
        self.lbl_packets.setStyleSheet("color: #5AE7FF; font-family: 'JetBrains Mono', monospace; font-weight: 600;")

        telem_layout.addWidget(QLabel("Yaw (Azimuth):"), 0, 0)
        telem_layout.addWidget(self.lbl_yaw, 0, 1)
        telem_layout.addWidget(QLabel("Pitch (Elevation):"), 0, 2)
        telem_layout.addWidget(self.lbl_pitch, 0, 3)
        telem_layout.addWidget(QLabel("Roll (Twist):"), 0, 4)
        telem_layout.addWidget(self.lbl_roll, 0, 5)

        telem_layout.addWidget(QLabel("Angular Velocity:"), 1, 0)
        telem_layout.addWidget(self.lbl_gyro, 1, 1, 1, 2)
        telem_layout.addWidget(QLabel("Acceleration:"), 1, 3)
        telem_layout.addWidget(self.lbl_accel, 1, 4, 1, 2)

        telem_layout.addWidget(QLabel("Total Motion Frames:"), 2, 0)
        telem_layout.addWidget(self.lbl_packets, 2, 1)

        layout.addWidget(telem_group)

        # Quick Control Actions
        action_layout = QHBoxLayout()

        btn_recenter = QPushButton("Recenter Neutral Orientation (Home)")
        btn_recenter.setObjectName("RecenterButton")
        btn_recenter.clicked.connect(self._on_recenter_clicked)
        action_layout.addWidget(btn_recenter)

        btn_emergency = QPushButton("Emergency Release Inputs")
        btn_emergency.setObjectName("EmergencyButton")
        btn_emergency.clicked.connect(self._on_emergency_release)
        action_layout.addWidget(btn_emergency)

        layout.addLayout(action_layout)
        layout.addStretch()

    # --- Pairing & Security Tab ---
    def _build_pairing_tab(self):
        layout = QVBoxLayout(self.tab_pairing)

        pin_group = QGroupBox("Pairing Code")
        pin_layout = QVBoxLayout(pin_group)
        pin_layout.setAlignment(Qt.AlignCenter)

        desc = QLabel("Enter this 4-digit PIN on your phone to authorize controller access:")
        desc.setStyleSheet("color: #94A3B8; font-size: 13px;")
        desc.setAlignment(Qt.AlignCenter)
        pin_layout.addWidget(desc)

        self.lbl_pin_display = QLabel(self.pairing_mgr.get_current_pin())
        self.lbl_pin_display.setObjectName("PINDisplay")
        self.lbl_pin_display.setAlignment(Qt.AlignCenter)
        pin_layout.addWidget(self.lbl_pin_display)

        btn_refresh_pin = QPushButton("Generate New PIN")
        btn_refresh_pin.clicked.connect(self._on_refresh_pin)
        pin_layout.addWidget(btn_refresh_pin, alignment=Qt.AlignCenter)

        layout.addWidget(pin_group)

        # Trusted Devices Table
        dev_group = QGroupBox("Trusted Devices")
        dev_layout = QVBoxLayout(dev_group)

        self.table_devices = QTableWidget(0, 3)
        self.table_devices.setHorizontalHeaderLabels(["Device Name", "Device ID", "Last Seen"])
        self.table_devices.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        dev_layout.addWidget(self.table_devices)

        tbl_actions = QHBoxLayout()
        btn_forget_selected = QPushButton("Forget Selected Device")
        btn_forget_selected.clicked.connect(self._on_forget_selected_device)
        tbl_actions.addWidget(btn_forget_selected)

        btn_forget_all = QPushButton("Forget All Devices")
        btn_forget_all.setObjectName("EmergencyButton")
        btn_forget_all.clicked.connect(self._on_forget_all_devices)
        tbl_actions.addWidget(btn_forget_all)

        dev_layout.addLayout(tbl_actions)
        layout.addWidget(dev_group)

        self._refresh_trusted_devices_table()

    # --- Motion Tuning Tab ---
    def _build_motion_tab(self):
        layout = QVBoxLayout(self.tab_motion)

        # Quick Tuning Profiles
        preset_box = QHBoxLayout()
        lbl_preset = QLabel("Mode Profiles:")
        lbl_preset.setStyleSheet("font-weight: bold; color: #5AE7FF;")
        preset_box.addWidget(lbl_preset)

        btn_preset_wii = QPushButton("Wii Remote")
        btn_preset_wii.clicked.connect(lambda: self._apply_tuning_preset(18.0, 18.0, 0.04, 0.30, 0.50))
        preset_box.addWidget(btn_preset_wii)

        btn_preset_mouse = QPushButton("Air Mouse")
        btn_preset_mouse.clicked.connect(lambda: self._apply_tuning_preset(24.0, 24.0, 0.02, 0.35, 0.65))
        preset_box.addWidget(btn_preset_mouse)

        btn_preset_pres = QPushButton("Presentation")
        btn_preset_pres.clicked.connect(lambda: self._apply_tuning_preset(15.0, 15.0, 0.05, 0.55, 0.30))
        preset_box.addWidget(btn_preset_pres)

        preset_box.addStretch()
        layout.addLayout(preset_box)

        form_layout = QGridLayout()

        # Sensitivity X
        form_layout.addWidget(QLabel("X Sensitivity (Yaw):"), 0, 0)
        self.spin_sens_x = QDoubleSpinBox()
        self.spin_sens_x.setRange(1.0, 80.0)
        self.spin_sens_x.setValue(float(self.settings.get("sensitivity_x", 18.0)))
        self.spin_sens_x.valueChanged.connect(self._on_motion_settings_changed)
        form_layout.addWidget(self.spin_sens_x, 0, 1)

        # Sensitivity Y
        form_layout.addWidget(QLabel("Y Sensitivity (Pitch):"), 1, 0)
        self.spin_sens_y = QDoubleSpinBox()
        self.spin_sens_y.setRange(1.0, 80.0)
        self.spin_sens_y.setValue(float(self.settings.get("sensitivity_y", 18.0)))
        self.spin_sens_y.valueChanged.connect(self._on_motion_settings_changed)
        form_layout.addWidget(self.spin_sens_y, 1, 1)

        # Deadzone
        form_layout.addWidget(QLabel("Deadzone:"), 2, 0)
        self.spin_deadzone = QDoubleSpinBox()
        self.spin_deadzone.setRange(0.0, 0.20)
        self.spin_deadzone.setSingleStep(0.01)
        self.spin_deadzone.setValue(float(self.settings.get("deadzone", 0.04)))
        self.spin_deadzone.valueChanged.connect(self._on_motion_settings_changed)
        form_layout.addWidget(self.spin_deadzone, 2, 1)

        # Smoothing
        form_layout.addWidget(QLabel("Smoothing Factor (EMA):"), 3, 0)
        self.spin_smoothing = QDoubleSpinBox()
        self.spin_smoothing.setRange(0.0, 0.90)
        self.spin_smoothing.setSingleStep(0.05)
        self.spin_smoothing.setValue(float(self.settings.get("smoothing", 0.30)))
        self.spin_smoothing.valueChanged.connect(self._on_motion_settings_changed)
        form_layout.addWidget(self.spin_smoothing, 3, 1)

        # Acceleration
        form_layout.addWidget(QLabel("Acceleration Curve:"), 4, 0)
        self.spin_accel = QDoubleSpinBox()
        self.spin_accel.setRange(0.0, 2.0)
        self.spin_accel.setSingleStep(0.1)
        self.spin_accel.setValue(float(self.settings.get("acceleration", 0.50)))
        self.spin_accel.valueChanged.connect(self._on_motion_settings_changed)
        form_layout.addWidget(self.spin_accel, 4, 1)

        # Invert Checkboxes
        self.chk_invert_x = QCheckBox("Invert Horizontal Axis (X)")
        self.chk_invert_x.setChecked(bool(self.settings.get("invert_x", False)))
        self.chk_invert_x.toggled.connect(self._on_motion_settings_changed)
        form_layout.addWidget(self.chk_invert_x, 5, 0)

        self.chk_invert_y = QCheckBox("Invert Vertical Axis (Y)")
        self.chk_invert_y.setChecked(bool(self.settings.get("invert_y", False)))
        self.chk_invert_y.toggled.connect(self._on_motion_settings_changed)
        form_layout.addWidget(self.chk_invert_y, 5, 1)

        layout.addLayout(form_layout)

        # Button row
        btn_row = QHBoxLayout()
        btn_reset = QPushButton("Reset Defaults")
        btn_reset.clicked.connect(self._on_reset_motion_defaults)
        btn_row.addWidget(btn_reset)
        btn_row.addStretch()

        layout.addLayout(btn_row)
        layout.addStretch()

    # --- Button Mappings Tab ---
    def _build_mappings_tab(self):
        layout = QVBoxLayout(self.tab_mappings)
        desc = QLabel("Configure how virtual Wii Remote buttons are translated on Windows:")
        desc.setStyleSheet("color: #94A3B8; margin-bottom: 8px;")
        layout.addWidget(desc)

        grid = QGridLayout()
        buttons = [
            ("DPAD_UP", "D-Pad Up"),
            ("DPAD_DOWN", "D-Pad Down"),
            ("DPAD_LEFT", "D-Pad Left"),
            ("DPAD_RIGHT", "D-Pad Right"),
            ("A", "A Button"),
            ("B", "B Button (Trigger)"),
            ("1", "1 Button"),
            ("2", "2 Button"),
            ("PLUS", "+ (Plus)"),
            ("MINUS", "- (Minus)"),
            ("HOME", "Home Button"),
        ]

        current_mappings = self.settings.get("button_mappings", {})
        self._mapping_combos = {}

        for idx, (btn_key, label_str) in enumerate(buttons):
            lbl = QLabel(label_str + ":")
            combo = QComboBox()
            for action_key in FRIENDLY_ACTIONS.keys():
                combo.addItem(action_key)

            curr_val = current_mappings.get(btn_key, "NONE")
            index = combo.findText(curr_val)
            if index >= 0:
                combo.setCurrentIndex(index)

            combo.currentTextChanged.connect(lambda val, k=btn_key: self._on_mapping_changed(k, val))
            self._mapping_combos[btn_key] = combo

            row = idx // 2
            col = (idx % 2) * 2
            grid.addWidget(lbl, row, col)
            grid.addWidget(combo, row, col + 1)

        layout.addLayout(grid)
        layout.addStretch()

    # --- Gestures Tab ---
    def _build_gestures_tab(self):
        layout = QVBoxLayout(self.tab_gestures)
        layout.setSpacing(10)

        # 1. Direct Motion Gestures
        grp_direct = QGroupBox("Direct Motion Gestures (Wii Physical Actions)")
        grid_d = QGridLayout(grp_direct)

        # Shake
        self.chk_shake = QCheckBox("Rapid Shaking (Spin Attack / Shake Off)")
        self.chk_shake.setChecked(self.settings.get("gesture_shake_enabled", True))
        self.chk_shake.toggled.connect(lambda v: self.settings.set("gesture_shake_enabled", v))
        self.combo_shake = self._create_action_combo("gesture_shake_action", "KEY_SPACE")
        badge_shake = QLabel(" SHAKE ")
        badge_shake.setStyleSheet("background-color: #1A1A24; color: #A0A0AA; padding: 3px 8px; border-radius: 6px; font-weight: bold; border: 1px solid rgba(255, 255, 255, 0.08);")
        self._gesture_badges["shake"] = badge_shake
        grid_d.addWidget(self.chk_shake, 0, 0)
        grid_d.addWidget(QLabel("Action:"), 0, 1)
        grid_d.addWidget(self.combo_shake, 0, 2)
        grid_d.addWidget(badge_shake, 0, 3)

        # Wrist Snap / Flick
        self.chk_flick = QCheckBox("Wrist Snapping (Cast Fishing Line / Jump)")
        self.chk_flick.setChecked(self.settings.get("gesture_flick_enabled", True))
        self.chk_flick.toggled.connect(lambda v: self.settings.set("gesture_flick_enabled", v))
        self.combo_flick = self._create_action_combo("gesture_flick_action", "KEY_UP")
        badge_flick = QLabel(" FLICK ")
        badge_flick.setStyleSheet("background-color: #1A1A24; color: #A0A0AA; padding: 3px 8px; border-radius: 6px; font-weight: bold; border: 1px solid rgba(255, 255, 255, 0.08);")
        self._gesture_badges["wrist_snap"] = badge_flick
        grid_d.addWidget(self.chk_flick, 1, 0)
        grid_d.addWidget(QLabel("Action:"), 1, 1)
        grid_d.addWidget(self.combo_flick, 1, 2)
        grid_d.addWidget(badge_flick, 1, 3)

        # Straight Thrust
        self.chk_thrust = QCheckBox("Straight Thrusts (Punch / Sword Jab)")
        self.chk_thrust.setChecked(self.settings.get("gesture_thrust_enabled", True))
        self.chk_thrust.toggled.connect(lambda v: self.settings.set("gesture_thrust_enabled", v))
        self.combo_thrust = self._create_action_combo("gesture_thrust_action", "KEY_F")
        badge_thrust = QLabel(" THRUST ")
        badge_thrust.setStyleSheet("background-color: #1A1A24; color: #A0A0AA; padding: 3px 8px; border-radius: 6px; font-weight: bold; border: 1px solid rgba(255, 255, 255, 0.08);")
        self._gesture_badges["thrust"] = badge_thrust
        grid_d.addWidget(self.chk_thrust, 2, 0)
        grid_d.addWidget(QLabel("Action:"), 2, 1)
        grid_d.addWidget(self.combo_thrust, 2, 2)
        grid_d.addWidget(badge_thrust, 2, 3)

        layout.addWidget(grp_direct)

        # 2. Screen-Based Pointer Gestures
        grp_pointer = QGroupBox("Screen-Based Pointer Gestures")
        grid_p = QGridLayout(grp_pointer)

        # Off-Screen Reload
        self.chk_offscreen = QCheckBox("Off-Screen Aim & Reload (Aim away from monitor)")
        self.chk_offscreen.setChecked(self.settings.get("gesture_offscreen_enabled", True))
        self.chk_offscreen.toggled.connect(lambda v: self.settings.set("gesture_offscreen_enabled", v))
        self.combo_offscreen = self._create_action_combo("gesture_offscreen_action", "KEY_R")
        badge_offscreen = QLabel(" OFF-SCREEN ")
        badge_offscreen.setStyleSheet("background-color: #1A1A24; color: #A0A0AA; padding: 3px 8px; border-radius: 6px; font-weight: bold; border: 1px solid rgba(255, 255, 255, 0.08);")
        self._gesture_badges["off_screen"] = badge_offscreen
        grid_p.addWidget(self.chk_offscreen, 0, 0)
        grid_p.addWidget(QLabel("Action:"), 0, 1)
        grid_p.addWidget(self.combo_offscreen, 0, 2)
        grid_p.addWidget(badge_offscreen, 0, 3)

        layout.addWidget(grp_pointer)

        # 3. Physical Orientation Gestures
        grp_orient = QGroupBox("Physical Orientation & Steering Gestures")
        grid_o = QGridLayout(grp_orient)

        # Tilt Steering
        self.chk_steering = QCheckBox("Tilt Steering (Wii Wheel in Landscape)")
        self.chk_steering.setChecked(self.settings.get("gesture_steering_enabled", True))
        self.chk_steering.toggled.connect(lambda v: self.settings.set("gesture_steering_enabled", v))
        self.combo_steer_l = self._create_action_combo("gesture_steer_left_action", "KEY_A")
        self.combo_steer_r = self._create_action_combo("gesture_steer_right_action", "KEY_D")
        badge_steer_l = QLabel(" STEER L ")
        badge_steer_l.setStyleSheet("background-color: #1A1A24; color: #A0A0AA; padding: 3px 8px; border-radius: 6px; font-weight: bold; border: 1px solid rgba(255, 255, 255, 0.08);")
        badge_steer_r = QLabel(" STEER R ")
        badge_steer_r.setStyleSheet("background-color: #1A1A24; color: #A0A0AA; padding: 3px 8px; border-radius: 6px; font-weight: bold; border: 1px solid rgba(255, 255, 255, 0.08);")
        self._gesture_badges["steer_left"] = badge_steer_l
        self._gesture_badges["steer_right"] = badge_steer_r
        grid_o.addWidget(self.chk_steering, 0, 0)
        grid_o.addWidget(QLabel("Left:"), 0, 1)
        grid_o.addWidget(self.combo_steer_l, 0, 2)
        grid_o.addWidget(badge_steer_l, 0, 3)
        grid_o.addWidget(QLabel("Right:"), 1, 1)
        grid_o.addWidget(self.combo_steer_r, 1, 2)
        grid_o.addWidget(badge_steer_r, 1, 3)

        # Key Twisting
        self.chk_twist = QCheckBox("Key Twisting (Wrist Roll / Tilt)")
        self.chk_twist.setChecked(self.settings.get("gesture_twist_enabled", True))
        self.chk_twist.toggled.connect(lambda v: self.settings.set("gesture_twist_enabled", v))
        self.combo_twist_l = self._create_action_combo("gesture_twist_left_action", "KEY_Q")
        self.combo_twist_r = self._create_action_combo("gesture_twist_right_action", "KEY_E")
        badge_twist_l = QLabel(" TWIST L ")
        badge_twist_l.setStyleSheet("background-color: #1A1A24; color: #A0A0AA; padding: 3px 8px; border-radius: 6px; font-weight: bold; border: 1px solid rgba(255, 255, 255, 0.08);")
        badge_twist_r = QLabel(" TWIST R ")
        badge_twist_r.setStyleSheet("background-color: #1A1A24; color: #A0A0AA; padding: 3px 8px; border-radius: 6px; font-weight: bold; border: 1px solid rgba(255, 255, 255, 0.08);")
        self._gesture_badges["twist_left"] = badge_twist_l
        self._gesture_badges["twist_right"] = badge_twist_r
        grid_o.addWidget(self.chk_twist, 2, 0)
        grid_o.addWidget(QLabel("Twist L:"), 2, 1)
        grid_o.addWidget(self.combo_twist_l, 2, 2)
        grid_o.addWidget(badge_twist_l, 2, 3)
        grid_o.addWidget(QLabel("Twist R:"), 3, 1)
        grid_o.addWidget(self.combo_twist_r, 3, 2)
        grid_o.addWidget(badge_twist_r, 3, 3)

        layout.addWidget(grp_orient)
        layout.addStretch()

    def _create_action_combo(self, setting_key: str, default_val: str) -> QComboBox:
        combo = QComboBox()
        for action_key in FRIENDLY_ACTIONS.keys():
            combo.addItem(action_key)
        val = self.settings.get(setting_key, default_val)
        idx = combo.findText(val)
        if idx >= 0:
            combo.setCurrentIndex(idx)
        combo.currentTextChanged.connect(lambda txt, k=setting_key: self.settings.set(k, txt))
        return combo

    @Slot(str, bool)
    def _on_gesture_triggered(self, name: str, active: bool):
        badge = self._gesture_badges.get(name)
        if badge:
            if active:
                badge.setStyleSheet("background-color: #5AE7FF; color: #08080C; padding: 3px 8px; border-radius: 6px; font-weight: bold; border: 1px solid #5AE7FF;")
                if name not in ("steer_left", "steer_right", "off_screen"):
                    QTimer.singleShot(250, lambda: badge.setStyleSheet("background-color: #1A1A24; color: #A0A0AA; padding: 3px 8px; border-radius: 6px; font-weight: bold; border: 1px solid rgba(255, 255, 255, 0.08);"))
            else:
                badge.setStyleSheet("background-color: #1A1A24; color: #A0A0AA; padding: 3px 8px; border-radius: 6px; font-weight: bold; border: 1px solid rgba(255, 255, 255, 0.08);")

    # --- Dolphin Tab ---
    def _build_dolphin_tab(self):
        layout = QVBoxLayout(self.tab_dolphin)

        group = QGroupBox("Dolphin DSU / Cemuhook Motion Server")
        vbox = QVBoxLayout(group)

        dsu_port = self.settings.get("dsu_port", 26760)
        lbl_status = QLabel(f"Status: Active on UDP Port {dsu_port}")
        lbl_status.setStyleSheet("color: #4ADE80; font-weight: 700; font-size: 14px; font-family: 'JetBrains Mono', monospace;")
        vbox.addWidget(lbl_status)

        guide = QLabel(
            "<b>How to use with Dolphin Emulator:</b><br><br>"
            "1. Open Dolphin → <i>Controllers</i><br>"
            "2. Under <b>Wii Remotes</b>, set Wii Remote 1 to <b>Emulated Wii Remote</b> and click <b>Configure</b>.<br>"
            "3. Under <b>Motion Input</b>, select <b>Alternate Input Sources</b> (DSU Client).<br>"
            "4. Check <i>Enable</i> and set Server Address to: <code>127.0.0.1</code> Port: <code>26760</code>.<br>"
            "5. At top of Configure window, set <b>Device</b> to: <code>DSUClient/0/...</code><br>"
            "6. <b>Mapping Dolphin Buttons:</b><br>"
            "&nbsp;&nbsp;• <b>Home:</b> Detects as <code>PS</code> (or right-click and enter <code>PS</code>)<br>"
            "&nbsp;&nbsp;• <b>A:</b> Detects as <code>Cross</code><br>"
            "&nbsp;&nbsp;• <b>B:</b> Detects as <code>R2</code><br>"
            "&nbsp;&nbsp;• <b>1:</b> Detects as <code>Square</code><br>"
            "&nbsp;&nbsp;• <b>2:</b> Detects as <code>Circle</code><br>"
            "&nbsp;&nbsp;• <b>+:</b> Detects as <code>Options</code><br>"
            "&nbsp;&nbsp;• <b>-:</b> Detects as <code>Share</code><br>"
            "&nbsp;&nbsp;• <b>D-Pad:</b> Detects as <code>Pad N / Pad S / Pad W / Pad E</code>"
        )
        guide.setStyleSheet("color: #CBD5E1; line-height: 1.5; font-size: 13px;")
        vbox.addWidget(guide)

        layout.addWidget(group)
        layout.addStretch()

    # --- System Tray ---
    def _init_tray(self):
        self.tray_icon = QSystemTrayIcon(self)
        # Fallback icon from standard pixmap
        icon = self.style().standardIcon(self.style().StandardPixmap.SP_ComputerIcon)
        self.tray_icon.setIcon(icon)
        self.setWindowIcon(icon)

        tray_menu = QMenu()
        act_open = QAction("Open Andromote", self)
        act_open.triggered.connect(self.showNormal)
        tray_menu.addAction(act_open)

        act_recenter = QAction("Recenter Motion", self)
        act_recenter.triggered.connect(self._on_recenter_clicked)
        tray_menu.addAction(act_recenter)

        act_toggle = QAction("Toggle Controller", self)
        act_toggle.triggered.connect(self._toggle_master_controller)
        tray_menu.addAction(act_toggle)

        act_settings = QAction("Settings", self)
        act_settings.triggered.connect(self._open_settings_dialog)
        tray_menu.addAction(act_settings)

        tray_menu.addSeparator()

        act_exit = QAction("Exit", self)
        act_exit.triggered.connect(self._on_app_exit)
        tray_menu.addAction(act_exit)

        self.tray_icon.setContextMenu(tray_menu)
        self.tray_icon.activated.connect(self._on_tray_activated)
        self.tray_icon.show()

    def _open_settings_dialog(self):
        from .console_utils import SettingsDialog
        dlg = SettingsDialog(self.settings, self)
        dlg.exec()

    def _on_tray_activated(self, reason):
        if reason == QSystemTrayIcon.ActivationReason.Trigger:
            if self.isVisible():
                self.hide()
            else:
                self.showNormal()
                self.activateWindow()

    def closeEvent(self, event):
        """Minimize to tray instead of abrupt exit."""
        if self.tray_icon.isVisible():
            self.hide()
            self.tray_icon.showMessage(
                "Andromote Running",
                "Receiver is running in the background. Access via system tray.",
                QSystemTrayIcon.MessageIcon.Information,
                2000
            )
            event.ignore()
        else:
            self._on_app_exit()
            event.accept()

    def _on_app_exit(self):
        # CRITICAL: Always release all held inputs before exiting!
        self.input_ctrl.release_all_inputs()
        self.tcp_srv.stop()
        self.udp_srv.stop()
        self.discovery_srv.stop()
        if self.dsu_srv:
            self.dsu_srv.stop()
        sys.exit(0)

    # --- Slot Handlers ---
    @Slot(str, str)
    def _on_connection_state_changed(self, status: str, details: str):
        if status == "connected":
            self.lbl_status_badge.setText("CONNECTED")
            self.lbl_status_badge.setStyleSheet("background-color: rgba(74, 222, 128, 0.15); color: #4ADE80; border: 1px solid #4ADE80; border-radius: 100px; padding: 4px 14px;")
            self.lbl_conn_device.setText(details or "Authenticated Phone")
            self.lbl_conn_ip.setText(self.tcp_srv.client_ip or "—")
        elif status == "connecting":
            self.lbl_status_badge.setText("CONNECTING")
            self.lbl_status_badge.setStyleSheet("background-color: rgba(90, 231, 255, 0.15); color: #5AE7FF; border: 1px solid #5AE7FF; border-radius: 100px; padding: 4px 14px;")
        else:
            self.lbl_status_badge.setText("LISTENING")
            self.lbl_status_badge.setStyleSheet("background-color: #14141C; color: #A0A0AA; border: 1px solid rgba(255, 255, 255, 0.1); border-radius: 100px; padding: 4px 14px;")
            self.lbl_conn_device.setText("None (Waiting for connection)")
            self.lbl_conn_ip.setText("—")
            self.lbl_conn_latency.setText("0 ms")
            self.lbl_conn_rate.setText("0 Hz")

        self._refresh_trusted_devices_table()

    @Slot(float)
    def _on_latency_updated(self, ms: float):
        self.lbl_conn_latency.setText(f"{ms:.1f} ms")

    @Slot(float)
    def _on_rate_updated(self, hz: float):
        self.lbl_conn_rate.setText(f"{hz:.0f} Hz")

    def _refresh_telemetry(self):
        telem = self.motion_proc.get_telemetry()
        self.lbl_yaw.setText(f"{telem['yaw_deg']:.1f}°")
        self.lbl_pitch.setText(f"{telem['pitch_deg']:.1f}°")
        self.lbl_roll.setText(f"{telem['roll_deg']:.1f}°")
        self.lbl_gyro.setText(f"X: {telem['gyro_x']:.2f} | Y: {telem['gyro_y']:.2f} | Z: {telem['gyro_z']:.2f} rad/s")
        self.lbl_accel.setText(f"X: {telem['accel_x']:.2f} | Y: {telem['accel_y']:.2f} | Z: {telem['accel_z']:.2f} m/s²")
        self.lbl_packets.setText(str(telem["packets"]))

    def _on_recenter_clicked(self):
        self.motion_proc.recenter()

    def _on_emergency_release(self):
        self.input_ctrl.release_all_inputs()
        QMessageBox.information(self, "Inputs Released", "All held mouse and keyboard inputs have been released.")

    def _toggle_master_controller(self):
        enabled = not self.input_ctrl.enabled
        self.input_ctrl.enabled = enabled
        self.btn_master_toggle.setChecked(enabled)
        if enabled:
            self.btn_master_toggle.setText("Controller: ENABLED")
            self.btn_master_toggle.setStyleSheet("background-color: #5AE7FF; color: #08080C; font-weight: bold; border-radius: 6px;")
        else:
            self.btn_master_toggle.setText("Controller: DISABLED")
            self.btn_master_toggle.setStyleSheet("background-color: #1A1A24; color: #A0A0AA; border: 1px solid rgba(255, 255, 255, 0.12); border-radius: 6px;")

    def _on_refresh_pin(self):
        new_pin = self.pairing_mgr.refresh_pin()
        self.lbl_pin_display.setText(new_pin)

    def _refresh_trusted_devices_table(self):
        devices = self.pairing_mgr.get_trusted_devices()
        self.table_devices.setRowCount(len(devices))
        for row, (dev_id, info) in enumerate(devices.items()):
            self.table_devices.setItem(row, 0, QTableWidgetItem(info.get("name", "Unknown")))
            self.table_devices.setItem(row, 1, QTableWidgetItem(dev_id))
            last_seen = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(info.get("last_seen", 0)))
            self.table_devices.setItem(row, 2, QTableWidgetItem(last_seen))

    def _on_forget_selected_device(self):
        row = self.table_devices.currentRow()
        if row >= 0:
            dev_id_item = self.table_devices.item(row, 1)
            if dev_id_item:
                dev_id = dev_id_item.text()
                self.pairing_mgr.forget_device(dev_id)
                self._refresh_trusted_devices_table()

    def _on_forget_all_devices(self):
        confirm = QMessageBox.question(
            self, "Forget All Devices",
            "Are you sure you want to forget all trusted devices? All phones will need to re-pair with PIN.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        if confirm == QMessageBox.StandardButton.Yes:
            self.pairing_mgr.forget_all()
            self._refresh_trusted_devices_table()

    def _on_motion_settings_changed(self):
        updates = {
            "sensitivity_x": self.spin_sens_x.value(),
            "sensitivity_y": self.spin_sens_y.value(),
            "deadzone": self.spin_deadzone.value(),
            "smoothing": self.spin_smoothing.value(),
            "acceleration": self.spin_accel.value(),
            "invert_x": self.chk_invert_x.isChecked(),
            "invert_y": self.chk_invert_y.isChecked(),
        }
        self.settings.update(updates)
        self.motion_proc.update_settings(**updates)

    def _apply_tuning_preset(self, sx: float, sy: float, dz: float, sm: float, ac: float):
        self.spin_sens_x.setValue(sx)
        self.spin_sens_y.setValue(sy)
        self.spin_deadzone.setValue(dz)
        self.spin_smoothing.setValue(sm)
        self.spin_accel.setValue(ac)
        self._on_motion_settings_changed()

    def _on_reset_motion_defaults(self):
        self._apply_tuning_preset(18.0, 18.0, 0.04, 0.30, 0.50)
        self.chk_invert_x.setChecked(False)
        self.chk_invert_y.setChecked(False)

    def _on_mapping_changed(self, btn_key: str, action_val: str):
        mappings = self.settings.get("button_mappings", {})
        mappings[btn_key] = action_val
        self.settings.set("button_mappings", mappings)
