"""
Modern dark theme stylesheet for PySide6 UI.
Matches the AndroMote website design language:
Deep obsidian backdrop, Electric Cyan accents, sleek 1px glass borders,
and glowing indicators.
"""

DARK_STYLESHEET = """
QMainWindow, QWidget#CentralWidget {
    background-color: #08080C;
    color: #F5F5F7;
    font-family: 'Inter', -apple-system, 'Segoe UI', sans-serif;
    font-size: 13px;
}

QTabWidget::pane {
    border: 1px solid rgba(255, 255, 255, 0.08);
    background-color: #0E0E14;
    border-radius: 12px;
    padding: 14px;
}

QTabBar::tab {
    background-color: #14141C;
    color: #A0A0AA;
    padding: 10px 20px;
    border-top-left-radius: 8px;
    border-top-right-radius: 8px;
    margin-right: 4px;
    font-weight: 600;
    border: 1px solid rgba(255, 255, 255, 0.06);
    border-bottom: none;
}

QTabBar::tab:selected {
    background-color: #1A1A24;
    color: #5AE7FF;
    border-bottom: 2px solid #5AE7FF;
    font-weight: 700;
}

QTabBar::tab:hover:!selected {
    background-color: #181824;
    color: #F5F5F7;
}

QGroupBox {
    border: 1px solid rgba(255, 255, 255, 0.08);
    border-radius: 12px;
    margin-top: 14px;
    padding-top: 20px;
    padding-left: 12px;
    padding-right: 12px;
    padding-bottom: 12px;
    font-weight: 700;
    color: #5AE7FF;
    background-color: #14141C;
}

QGroupBox::title {
    subcontrol-origin: margin;
    subcontrol-position: top left;
    left: 14px;
    padding: 0 8px;
    background-color: #14141C;
    border-radius: 4px;
}

QPushButton {
    background-color: #1A1A24;
    color: #F5F5F7;
    border: 1px solid rgba(255, 255, 255, 0.12);
    border-radius: 8px;
    padding: 8px 16px;
    font-weight: 600;
}

QPushButton:hover {
    background-color: #222232;
    border-color: #5AE7FF;
    color: #5AE7FF;
}

QPushButton:pressed {
    background-color: #2A2A3E;
}

QPushButton:disabled {
    background-color: #14141C;
    color: #60606A;
    border-color: rgba(255, 255, 255, 0.04);
}

QPushButton#EmergencyButton {
    background-color: #FF6B6B;
    color: #08080C;
    font-weight: 700;
    border: none;
}

QPushButton#EmergencyButton:hover {
    background-color: #FA5252;
}

QPushButton#RecenterButton {
    background-color: #4ADE80;
    color: #08080C;
    font-weight: 700;
    border: none;
}

QPushButton#RecenterButton:hover {
    background-color: #22C55E;
}

QLabel {
    color: #A0A0AA;
}

QLabel#HeaderTitle {
    font-size: 22px;
    font-weight: 800;
    letter-spacing: -0.02em;
    color: #5AE7FF;
}

QLabel#PINDisplay {
    font-family: 'JetBrains Mono', 'Consolas', monospace;
    font-size: 38px;
    font-weight: 900;
    letter-spacing: 8px;
    color: #5AE7FF;
    background-color: #08080C;
    border: 1px solid rgba(90, 231, 255, 0.4);
    border-radius: 12px;
    padding: 12px 28px;
}

QLabel#StatusBadge {
    padding: 6px 14px;
    border-radius: 100px;
    font-weight: 700;
    font-size: 11px;
    font-family: 'JetBrains Mono', 'Consolas', monospace;
}

QSlider::groove:horizontal {
    height: 6px;
    background: #1A1A24;
    border: 1px solid rgba(255, 255, 255, 0.06);
    border-radius: 3px;
}

QSlider::sub-page:horizontal {
    background: #5AE7FF;
    border-radius: 3px;
}

QSlider::handle:horizontal {
    background: #08080C;
    border: 2px solid #5AE7FF;
    width: 16px;
    margin-top: -5px;
    margin-bottom: -5px;
    border-radius: 8px;
}

QSlider::handle:horizontal:hover {
    background: #5AE7FF;
}

QComboBox {
    background-color: #14141C;
    color: #F5F5F7;
    border: 1px solid rgba(255, 255, 255, 0.1);
    border-radius: 6px;
    padding: 6px 12px;
    min-width: 140px;
}

QComboBox:hover {
    border-color: #5AE7FF;
}

QComboBox QAbstractItemView {
    background-color: #14141C;
    color: #F5F5F7;
    selection-background-color: #1A1A24;
    selection-color: #5AE7FF;
    border: 1px solid rgba(255, 255, 255, 0.1);
}

QCheckBox {
    color: #F5F5F7;
    spacing: 8px;
}

QCheckBox::indicator {
    width: 18px;
    height: 18px;
    border-radius: 4px;
    border: 1px solid rgba(255, 255, 255, 0.15);
    background-color: #14141C;
}

QCheckBox::indicator:checked {
    background-color: #5AE7FF;
    border-color: #5AE7FF;
}

QTableWidget {
    background-color: #14141C;
    border: 1px solid rgba(255, 255, 255, 0.08);
    border-radius: 8px;
    gridline-color: rgba(255, 255, 255, 0.05);
    color: #F5F5F7;
}

QHeaderView::section {
    background-color: #0E0E14;
    color: #A0A0AA;
    padding: 8px;
    font-weight: 700;
    border: none;
    border-bottom: 1px solid rgba(255, 255, 255, 0.08);
}
"""
