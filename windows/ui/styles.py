"""
Modern dark theme stylesheet for PySide6 UI.
Clean typography, rounded corners, responsive accents, and distinct status badges.
"""

DARK_STYLESHEET = """
QMainWindow, QWidget#CentralWidget {
    background-color: #121418;
    color: #E2E8F0;
    font-family: 'Segoe UI', 'Helvetica Neue', Arial, sans-serif;
    font-size: 13px;
}

QTabWidget::pane {
    border: 1px solid #23272F;
    background-color: #161920;
    border-radius: 8px;
    padding: 12px;
}

QTabBar::tab {
    background-color: #1A1D24;
    color: #94A3B8;
    padding: 10px 18px;
    border-top-left-radius: 6px;
    border-top-right-radius: 6px;
    margin-right: 4px;
    font-weight: 600;
}

QTabBar::tab:selected {
    background-color: #2563EB;
    color: #FFFFFF;
}

QTabBar::tab:hover:!selected {
    background-color: #23272F;
    color: #F8FAFC;
}

QGroupBox {
    border: 1px solid #262B35;
    border-radius: 8px;
    margin-top: 14px;
    padding-top: 18px;
    font-weight: 700;
    color: #38BDF8;
}

QGroupBox::title {
    subcontrol-origin: margin;
    subcontrol-position: top left;
    left: 12px;
    padding: 0 6px;
}

QPushButton {
    background-color: #2563EB;
    color: #FFFFFF;
    border: none;
    border-radius: 6px;
    padding: 8px 16px;
    font-weight: 600;
}

QPushButton:hover {
    background-color: #1D4ED8;
}

QPushButton:pressed {
    background-color: #1E40AF;
}

QPushButton:disabled {
    background-color: #334155;
    color: #64748B;
}

QPushButton#EmergencyButton {
    background-color: #DC2626;
}

QPushButton#EmergencyButton:hover {
    background-color: #B91C1C;
}

QPushButton#RecenterButton {
    background-color: #059669;
}

QPushButton#RecenterButton:hover {
    background-color: #047857;
}

QLabel {
    color: #CBD5E1;
}

QLabel#HeaderTitle {
    font-size: 20px;
    font-weight: 800;
    color: #38BDF8;
}

QLabel#PINDisplay {
    font-size: 38px;
    font-weight: 900;
    letter-spacing: 8px;
    color: #F59E0B;
    background-color: #0F172A;
    border: 2px dashed #3B82F6;
    border-radius: 12px;
    padding: 12px 24px;
}

QLabel#StatusBadge {
    padding: 6px 14px;
    border-radius: 12px;
    font-weight: 700;
    font-size: 12px;
}

QSlider::groove:horizontal {
    height: 6px;
    background: #334155;
    border-radius: 3px;
}

QSlider::sub-page:horizontal {
    background: #38BDF8;
    border-radius: 3px;
}

QSlider::handle:horizontal {
    background: #FFFFFF;
    border: 2px solid #38BDF8;
    width: 16px;
    margin-top: -5px;
    margin-bottom: -5px;
    border-radius: 8px;
}

QSlider::handle:horizontal:hover {
    background: #E0F2FE;
}

QComboBox {
    background-color: #1E293B;
    color: #F8FAFC;
    border: 1px solid #475569;
    border-radius: 6px;
    padding: 6px 12px;
    min-width: 140px;
}

QComboBox:hover {
    border-color: #38BDF8;
}

QComboBox QAbstractItemView {
    background-color: #1E293B;
    color: #F8FAFC;
    selection-background-color: #2563EB;
    border: 1px solid #475569;
}

QCheckBox {
    color: #CBD5E1;
    spacing: 8px;
}

QCheckBox::indicator {
    width: 18px;
    height: 18px;
    border-radius: 4px;
    border: 1px solid #475569;
    background-color: #1E293B;
}

QCheckBox::indicator:checked {
    background-color: #2563EB;
    border-color: #38BDF8;
}

QTableWidget {
    background-color: #1E293B;
    border: 1px solid #334155;
    border-radius: 6px;
    gridline-color: #334155;
    color: #F8FAFC;
}

QHeaderView::section {
    background-color: #0F172A;
    color: #94A3B8;
    padding: 8px;
    font-weight: 700;
    border: none;
    border-bottom: 1px solid #334155;
}
"""
