"""
Settings Manager:
Thread-safe JSON configuration persistence with automatic schema migrations,
corrupt configuration recovery, and sensible default values.
"""

import os
import json
import logging
import threading
from typing import Dict, Any, Optional

from ..input.keycodes import DEFAULT_BUTTON_MAPPINGS

logger = logging.getLogger("settings_manager")

DEFAULT_SETTINGS: Dict[str, Any] = {
    # Motion Tuning
    "sensitivity_x": 18.0,
    "sensitivity_y": 18.0,
    "deadzone": 0.04,
    "smoothing": 0.30,
    "acceleration": 0.50,
    "invert_x": False,
    "invert_y": False,
    "cursor_max_delta": 120.0,

    # Safety & Watchdog
    "watchdog_timeout": 0.5,  # Seconds before releasing inputs after data ceases
    "controller_enabled": True,

    # Network Ports
    "discovery_port": 42424,
    "tcp_port": 42425,
    "motion_port": 42426,

    # Dolphin DSU
    "dsu_enabled": True,
    "dsu_port": 26760,

    # Button Mappings
    "button_mappings": dict(DEFAULT_BUTTON_MAPPINGS),
}


class SettingsManager:
    """
    Manages persistent user settings in JSON format.
    """

    def __init__(self, config_path: Optional[str] = None):
        self._lock = threading.RLock()
        if config_path:
            self.config_path = config_path
        else:
            base_dir = os.path.join(os.path.expanduser("~"), ".andromote")
            os.makedirs(base_dir, exist_ok=True)
            self.config_path = os.path.join(base_dir, "settings.json")

        self._settings: Dict[str, Any] = dict(DEFAULT_SETTINGS)
        self.load()

    def get(self, key: str, default: Any = None) -> Any:
        with self._lock:
            return self._settings.get(key, default)

    def set(self, key: str, value: Any, auto_save: bool = True):
        with self._lock:
            self._settings[key] = value
            if auto_save:
                self.save()

    def update(self, updates: Dict[str, Any], auto_save: bool = True):
        with self._lock:
            self._settings.update(updates)
            if auto_save:
                self.save()

    def get_all(self) -> Dict[str, Any]:
        with self._lock:
            return dict(self._settings)

    def reset_to_defaults(self):
        with self._lock:
            self._settings = dict(DEFAULT_SETTINGS)
            self.save()

    def load(self):
        with self._lock:
            if not os.path.exists(self.config_path):
                logger.info(f"No settings file found at {self.config_path}. Initializing defaults.")
                self.save()
                return

            try:
                with open(self.config_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    if isinstance(data, dict):
                        # Merge loaded data on top of defaults
                        for k, v in data.items():
                            if k in DEFAULT_SETTINGS:
                                self._settings[k] = v
                        logger.info(f"Settings loaded successfully from {self.config_path}")
                    else:
                        logger.warning("Settings file corrupted (not a dict). Resetting defaults.")
                        self.save()
            except Exception as e:
                logger.error(f"Error reading settings {self.config_path}: {e}. Falling back to defaults.")
                self.save()

    def save(self):
        with self._lock:
            try:
                os.makedirs(os.path.dirname(self.config_path), exist_ok=True)
                temp_path = self.config_path + ".tmp"
                with open(temp_path, "w", encoding="utf-8") as f:
                    json.dump(self._settings, f, indent=2)
                # Atomic replace
                if os.path.exists(self.config_path):
                    os.replace(temp_path, self.config_path)
                else:
                    os.rename(temp_path, self.config_path)
            except Exception as e:
                logger.error(f"Failed to save settings to {self.config_path}: {e}")


_settings_instance: Optional[SettingsManager] = None

def get_settings_manager(config_path: Optional[str] = None) -> SettingsManager:
    global _settings_instance
    if _settings_instance is None:
        _settings_instance = SettingsManager(config_path)
    return _settings_instance
