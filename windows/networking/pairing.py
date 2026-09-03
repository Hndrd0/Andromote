"""
Device Pairing and Security Manager:
Generates a random 4-digit PIN for initial setup, securely hashes authentication
tokens with SHA-256, maintains trusted devices list, and validates client access.
"""

import os
import json
import random
import secrets
import hashlib
import logging
import threading
import time
from typing import Dict, Any, Optional, Tuple

logger = logging.getLogger("pairing_manager")


class PairingManager:
    """
    Manages local LAN pairing and token-based device authentication.
    """

    def __init__(self, storage_path: Optional[str] = None):
        self._lock = threading.RLock()
        if storage_path:
            self.storage_path = storage_path
        else:
            base_dir = os.path.join(os.path.expanduser("~"), ".andromote")
            os.makedirs(base_dir, exist_ok=True)
            self.storage_path = os.path.join(base_dir, "trusted_devices.json")

        self._current_pin: str = self._generate_pin()
        self._trusted_devices: Dict[str, Dict[str, Any]] = {}
        self.load()

    def _generate_pin(self) -> str:
        """Generate a random 4-digit numeric PIN (e.g. '7429')."""
        return f"{random.randint(1000, 9999)}"

    def get_current_pin(self) -> str:
        """Get the active 4-digit pairing PIN."""
        with self._lock:
            return self._current_pin

    def refresh_pin(self) -> str:
        """Generate a new pairing PIN."""
        with self._lock:
            self._current_pin = self._generate_pin()
            logger.info(f"Generated new pairing PIN: {self._current_pin}")
            return self._current_pin

    @staticmethod
    def _hash_token(token: str) -> str:
        """Hash token using SHA-256 before persisting."""
        return hashlib.sha256(token.encode("utf-8")).hexdigest()

    def pair_device(self, pin: str, device_id: str, device_name: str) -> Tuple[bool, Optional[str], str]:
        """
        Validate PIN and pair device.
        Returns: (success: bool, token: Optional[str], message: str)
        """
        with self._lock:
            if not pin or not device_id:
                return False, None, "Invalid PIN or Device ID."

            if pin.strip() != self._current_pin:
                logger.warning(f"Failed pairing attempt from {device_name} ({device_id}): Incorrect PIN.")
                return False, None, "Incorrect pairing PIN."

            # Generate high-entropy 256-bit token
            token = secrets.token_hex(32)
            token_hash = self._hash_token(token)

            now_ts = int(time.time())
            self._trusted_devices[device_id] = {
                "name": device_name or "Android Phone",
                "token_hash": token_hash,
                "paired_at": now_ts,
                "last_seen": now_ts
            }
            self.save()
            # Rotate PIN after successful pair
            self.refresh_pin()
            logger.info(f"Successfully paired device: {device_name} ({device_id})")
            return True, token, "Paired successfully."

    def validate_token(self, device_id: str, token: str) -> Tuple[bool, str]:
        """
        Authenticate an already-paired device by its auth token.
        """
        with self._lock:
            if not device_id or not token:
                return False, "Missing credentials."

            device = self._trusted_devices.get(device_id)
            if not device:
                return False, "Device not recognized. Please pair first."

            token_hash = self._hash_token(token)
            if secrets.compare_digest(device.get("token_hash", ""), token_hash):
                device["last_seen"] = int(time.time())
                self.save()
                return True, "Authenticated."
            else:
                logger.warning(f"Authentication failed for device {device_id}: Token mismatch.")
                return False, "Invalid authentication token."

    def forget_device(self, device_id: str) -> bool:
        """Remove a trusted device."""
        with self._lock:
            if device_id in self._trusted_devices:
                del self._trusted_devices[device_id]
                self.save()
                logger.info(f"Removed trusted device: {device_id}")
                return True
            return False

    def forget_all(self):
        """Remove all trusted devices."""
        with self._lock:
            self._trusted_devices.clear()
            self.save()
            logger.info("Cleared all trusted devices.")

    def get_trusted_devices(self) -> Dict[str, Dict[str, Any]]:
        """Return shallow copy of all trusted devices."""
        with self._lock:
            return {k: dict(v) for k, v in self._trusted_devices.items()}

    def load(self):
        with self._lock:
            if not os.path.exists(self.storage_path):
                self.save()
                return
            try:
                with open(self.storage_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    if isinstance(data, dict):
                        self._trusted_devices = data
            except Exception as e:
                logger.error(f"Failed to load trusted devices from {self.storage_path}: {e}")
                self._trusted_devices = {}

    def save(self):
        with self._lock:
            try:
                os.makedirs(os.path.dirname(self.storage_path), exist_ok=True)
                temp_path = self.storage_path + ".tmp"
                with open(temp_path, "w", encoding="utf-8") as f:
                    json.dump(self._trusted_devices, f, indent=2)
                if os.path.exists(self.storage_path):
                    os.replace(temp_path, self.storage_path)
                else:
                    os.rename(temp_path, self.storage_path)
            except Exception as e:
                logger.error(f"Failed to save trusted devices to {self.storage_path}: {e}")
