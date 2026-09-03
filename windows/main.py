"""
Andromote Windows Receiver Entrypoint:
Initializes settings, input controller, motion processor, networking servers,
Dolphin DSU server, and PySide6 user interface.
"""

import sys
import os
import argparse
import logging
import signal

# Ensure project root is in sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from windows.config.settings_manager import get_settings_manager
from windows.input.win_input import get_input_controller
from windows.motion.processor import MotionProcessor
from windows.networking.pairing import PairingManager
from windows.networking.discovery_server import DiscoveryServer
from windows.networking.tcp_server import TCPServer
from windows.networking.udp_motion_server import UDPMotionServer
from windows.networking.dsu_server import DSUServer


def main():
    parser = argparse.ArgumentParser(description="Andromote Windows Receiver")
    parser.add_argument("--mock-mode", action="store_true", help="Run with mock input (no real cursor/key actions)")
    parser.add_argument("--no-gui", action="store_true", help="Run headless in background without Qt window")
    parser.add_argument("--debug", action="store_true", help="Enable verbose debug logging")
    args = parser.parse_args()

    # Configure Logging
    log_level = logging.DEBUG if args.debug else logging.INFO
    logging.basicConfig(
        level=log_level,
        format="%(asctime)s [%(levelname)s] [%(name)s]: %(message)s",
        datefmt="%H:%M:%S"
    )
    logger = logging.getLogger("AndromoteMain")

    # Load Settings
    settings = get_settings_manager()
    if settings.get("verbose_logging", False) or args.debug:
        logging.getLogger().setLevel(logging.DEBUG)

    # Attach in-app log ring buffer for GUI terminal viewer
    from windows.ui.console_utils import InAppLogHandler, set_console_visible
    InAppLogHandler.get_instance()

    # Hide OS terminal window on startup if running GUI and not requested
    show_terminal = settings.get("show_debug_terminal", False) or args.debug
    if not args.no_gui and not show_terminal:
        set_console_visible(False)

    logger.info("Starting Andromote Windows Receiver...")

    # Input Controller & Safety
    input_ctrl = get_input_controller(mock_mode=args.mock_mode)
    if args.mock_mode:
        logger.info("Running in MOCK INPUT MODE: Real mouse/keyboard inputs will NOT be generated.")

    # Motion Processor
    motion_proc = MotionProcessor(
        sensitivity_x=settings.get("sensitivity_x", 18.0),
        sensitivity_y=settings.get("sensitivity_y", 18.0),
        deadzone=settings.get("deadzone", 0.04),
        smoothing=settings.get("smoothing", 0.30),
        acceleration=settings.get("acceleration", 0.50),
        invert_x=settings.get("invert_x", False),
        invert_y=settings.get("invert_y", False),
        cursor_max_delta=settings.get("cursor_max_delta", 120.0)
    )

    # Pairing & Security Manager
    pairing_mgr = PairingManager()

    # Dolphin DSU Server
    dsu_port = settings.get("dsu_port", 26760)
    dsu_srv = DSUServer(port=dsu_port)
    if settings.get("dsu_enabled", True):
        dsu_srv.start()

    # Networking Servers
    tcp_port = settings.get("tcp_port", 42425)
    motion_port = settings.get("motion_port", 42426)
    discovery_port = settings.get("discovery_port", 42424)

    tcp_srv = TCPServer(
        port=tcp_port,
        pairing_manager=pairing_mgr,
        input_controller=input_ctrl,
        motion_processor=motion_proc,
        settings_manager=settings,
        dsu_server=dsu_srv
    )

    # Gesture Recognition Engine
    from windows.motion.gestures import GestureEngine
    gesture_eng = GestureEngine(settings_manager=settings)

    udp_srv = UDPMotionServer(
        port=motion_port,
        motion_processor=motion_proc,
        input_controller=input_ctrl,
        settings_manager=settings,
        dsu_server=dsu_srv,
        gesture_engine=gesture_eng
    )

    discovery_srv = DiscoveryServer(
        discovery_port=discovery_port,
        tcp_port=tcp_port,
        motion_port=motion_port,
        dsu_port=dsu_port
    )

    # Start Servers
    tcp_srv.start()
    udp_srv.start()
    discovery_srv.start()

    def shutdown():
        logger.info("Shutting down Andromote receiver...")
        input_ctrl.release_all_inputs()
        tcp_srv.stop()
        udp_srv.stop()
        discovery_srv.stop()
        dsu_srv.stop()

    if args.no_gui:
        logger.info("Receiver running in headless mode. Press Ctrl+C to terminate.")
        try:
            signal.signal(signal.SIGINT, lambda sig, frame: shutdown() or sys.exit(0))
            while True:
                import time
                time.sleep(1.0)
        except (KeyboardInterrupt, SystemExit):
            shutdown()
            return

    # Start PySide6 GUI
    from PySide6.QtWidgets import QApplication
    from windows.ui.main_window import MainWindow

    app = QApplication(sys.argv)
    app.setApplicationName("Andromote")
    app.setQuitOnLastWindowClosed(False)

    window = MainWindow(
        settings=settings,
        input_ctrl=input_ctrl,
        motion_proc=motion_proc,
        pairing_mgr=pairing_mgr,
        tcp_srv=tcp_srv,
        udp_srv=udp_srv,
        discovery_srv=discovery_srv,
        dsu_srv=dsu_srv,
        gesture_eng=gesture_eng
    )
    window.show()

    try:
        ret = app.exec()
    finally:
        shutdown()
    sys.exit(ret)


if __name__ == "__main__":
    main()
