"""
LAN Discovery Server:
Listens on UDP 42424 for phone discovery requests and periodically broadcasts
availability beacons on the local network.
"""

import socket
import json
import time
import logging
import threading
from typing import Optional

logger = logging.getLogger("discovery_server")


def get_local_ip() -> str:
    """
    Find best local LAN IP address by creating a dummy UDP connection.
    Falls back to '127.0.0.1' if disconnected.
    """
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        # Does not actually transmit packets, just routes to find default interface IP
        s.connect(('10.255.255.255', 1))
        ip = s.getsockname()[0]
    except Exception:
        try:
            ip = socket.gethostbyname(socket.gethostname())
        except Exception:
            ip = '127.0.0.1'
    finally:
        s.close()
    return ip


class DiscoveryServer:
    """
    UDP broadcast responder and beacon broadcaster.
    """

    PROTOCOL_VERSION = 1

    def __init__(self,
                 discovery_port: int = 42424,
                 tcp_port: int = 42425,
                 motion_port: int = 42426,
                 dsu_port: int = 26760):
        self.discovery_port = int(discovery_port)
        self.tcp_port = int(tcp_port)
        self.motion_port = int(motion_port)
        self.dsu_port = int(dsu_port)

        self._running = False
        self._thread: Optional[threading.Thread] = None
        self._beacon_thread: Optional[threading.Thread] = None
        self._socket: Optional[socket.socket] = None

    def start(self):
        """Start discovery listening and periodic beacon threads."""
        if self._running:
            return

        self._running = True
        self._thread = threading.Thread(target=self._listen_loop, daemon=True, name="DiscoveryListener")
        self._thread.start()

        self._beacon_thread = threading.Thread(target=self._beacon_loop, daemon=True, name="DiscoveryBeacon")
        self._beacon_thread.start()
        logger.info(f"Discovery server started on UDP {self.discovery_port}")

    def stop(self):
        """Stop discovery server and release socket."""
        self._running = False
        if self._socket:
            try:
                self._socket.close()
            except Exception:
                pass
            self._socket = None

    def _get_discovery_payload(self) -> bytes:
        payload = {
            "type": "discovery_response",
            "protocol_version": self.PROTOCOL_VERSION,
            "hostname": socket.gethostname(),
            "ip": get_local_ip(),
            "tcp_port": self.tcp_port,
            "motion_port": self.motion_port,
            "dsu_port": self.dsu_port
        }
        return json.dumps(payload).encode("utf-8")

    def _listen_loop(self):
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
            sock.bind(('', self.discovery_port))
            sock.settimeout(1.0)
            self._socket = sock
        except Exception as e:
            logger.error(f"Failed to bind discovery socket on port {self.discovery_port}: {e}")
            self._running = False
            return

        while self._running:
            try:
                data, addr = sock.recvfrom(2048)
                try:
                    msg = json.loads(data.decode("utf-8"))
                except Exception:
                    continue

                if isinstance(msg, dict) and msg.get("type") in ("discovery_request", "discover"):
                    response = self._get_discovery_payload()
                    sock.sendto(response, addr)
                    logger.debug(f"Replied to discovery request from {addr}")
            except socket.timeout:
                continue
            except Exception as e:
                if self._running:
                    logger.debug(f"Discovery listen error: {e}")
                break

    def _beacon_loop(self):
        """Broadcast beacon every 3 seconds to facilitate instant discovery."""
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)

        while self._running:
            try:
                data = self._get_discovery_payload()
                sock.sendto(data, ('<broadcast>', self.discovery_port))
            except Exception as e:
                logger.debug(f"Beacon broadcast error: {e}")

            # Sleep in small increments to respond quickly to shutdown
            for _ in range(30):
                if not self._running:
                    break
                time.sleep(0.1)

        sock.close()
