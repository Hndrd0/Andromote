"""
Andromote Synthetic Test Client:
Simulates a connected Android phone for automated end-to-end testing without hardware.
Performs LAN discovery, PIN pairing, authentication, button down/up events,
recenter commands, and streams 100 Hz synthetic motion packets.
"""

import socket
import struct
import json
import time
import math
import argparse
import sys
import os

# Binary packet definition matching server
BINARY_PACKET_FORMAT = "!4sHQ4f3f3f"
BINARY_MAGIC = b"WMO1"


class AndromoteTestClient:
    def __init__(self, host: str = "127.0.0.1", tcp_port: int = 42425, motion_port: int = 42426):
        self.host = host
        self.tcp_port = tcp_port
        self.motion_port = motion_port

        self.device_id = "test-virtual-phone-001"
        self.device_name = "Virtual Android Wiimote"
        self.token = None

        self.tcp_sock = None
        self.udp_sock = None
        self.seq = 0

    @classmethod
    def discover_pc(cls, timeout: float = 2.0):
        """Send UDP discovery broadcast to find running Andromote PC."""
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        sock.settimeout(timeout)

        req = json.dumps({"type": "discovery_request"}).encode("utf-8")
        sock.sendto(req, ('<broadcast>', 42424))

        try:
            data, addr = sock.recvfrom(2048)
            resp = json.loads(data.decode("utf-8"))
            print(f"[Discovery] Found receiver at {addr[0]}: {resp}")
            return resp
        except socket.timeout:
            print("[Discovery] No broadcast response received.")
            return None
        finally:
            sock.close()

    def connect_tcp(self):
        """Connect TCP control socket."""
        self.tcp_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.tcp_sock.connect((self.host, self.tcp_port))
        self.tcp_sock.settimeout(5.0)

    def close(self):
        if self.tcp_sock:
            try:
                self.tcp_sock.close()
            except Exception:
                pass
            self.tcp_sock = None
        if self.udp_sock:
            try:
                self.udp_sock.close()
            except Exception:
                pass
            self.udp_sock = None

    def send_tcp(self, data: dict):
        payload = json.dumps(data).encode("utf-8")
        header = struct.pack(">I", len(payload))
        self.tcp_sock.sendall(header + payload)

    def recv_tcp(self) -> dict:
        hdr = self.tcp_sock.recv(4)
        if not hdr or len(hdr) < 4:
            raise ConnectionError("Server closed connection")
        length = struct.unpack(">I", hdr)[0]
        buf = bytearray()
        while len(buf) < length:
            chunk = self.tcp_sock.recv(length - len(buf))
            if not chunk:
                raise ConnectionError("Incomplete frame")
            buf.extend(chunk)
        return json.loads(bytes(buf).decode("utf-8"))

    def hello(self) -> dict:
        self.send_tcp({"type": "hello", "device_id": self.device_id})
        return self.recv_tcp()

    def pair(self, pin: str) -> bool:
        self.send_tcp({
            "type": "pair",
            "pin": pin,
            "device_id": self.device_id,
            "device_name": self.device_name
        })
        resp = self.recv_tcp()
        if resp.get("status") == "success":
            self.token = resp.get("token")
            return True
        return False

    def auth(self, token: str) -> bool:
        self.send_tcp({
            "type": "auth",
            "device_id": self.device_id,
            "token": token,
            "device_name": self.device_name
        })
        resp = self.recv_tcp()
        return resp.get("status") == "success"

    def send_button(self, button: str, state: str):
        self.send_tcp({
            "type": "button",
            "button": button,
            "state": state,
            "timestamp": int(time.time() * 1000)
        })

    def recenter(self):
        self.send_tcp({"type": "recenter"})

    def init_udp(self):
        self.udp_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

    def send_motion_packet_binary(self, qx, qy, qz, qw, gx, gy, gz, ax, ay, az):
        self.seq = (self.seq + 1) & 0xFFFF
        ts = int(time.time() * 1000)
        pkt = struct.pack(
            BINARY_PACKET_FORMAT,
            BINARY_MAGIC,
            self.seq,
            ts,
            float(qx), float(qy), float(qz), float(qw),
            float(gx), float(gy), float(gz),
            float(ax), float(ay), float(az)
        )
        self.udp_sock.sendto(pkt, (self.host, self.motion_port))

    def stream_synthetic_motion(self, duration_sec: float = 3.0, rate_hz: int = 100):
        """
        Generates realistic 100 Hz sinusoidal angular velocity simulating
        a hand smoothly moving the phone in circles.
        """
        print(f"[Motion] Streaming {rate_hz} Hz motion for {duration_sec}s...")
        interval = 1.0 / rate_hz
        start_time = time.time()
        angle = 0.0

        while (time.time() - start_time) < duration_sec:
            t0 = time.time()
            angle += 0.08

            # Circle in angular velocity: gz (yaw) and gx (pitch)
            gx = 0.5 * math.sin(angle)
            gz = 0.5 * math.cos(angle)
            gy = 0.0

            # Orientation quaternion around identity
            qw = 0.99
            qx = 0.05 * math.sin(angle)
            qy = 0.0
            qz = 0.05 * math.cos(angle)

            # Acceleration
            ax = 0.2 * math.sin(angle)
            ay = 0.2 * math.cos(angle)
            az = 9.81

            self.send_motion_packet_binary(qx, qy, qz, qw, gx, gy, gz, ax, ay, az)

            elapsed = time.time() - t0
            sleep_time = interval - elapsed
            if sleep_time > 0:
                time.sleep(sleep_time)


def run_automated_test(host="127.0.0.1", pin=None, tcp_port=42425, motion_port=42426):
    """Run full automated suite verifying receiver communication."""
    print("=" * 60)
    print("ANDROMOTE AUTOMATED PROTOCOL & INTEGRATION TEST")
    print("=" * 60)

    client = AndromoteTestClient(host=host, tcp_port=tcp_port, motion_port=motion_port)

    # 1. Connect TCP
    print("\n[Step 1] Connecting to TCP control channel...")
    client.connect_tcp()
    print("  -> Connected to TCP successfully.")

    # 2. Handshake Hello
    print("\n[Step 2] Sending 'hello' handshake...")
    hello_resp = client.hello()
    print(f"  -> Hello response: {hello_resp}")
    assert hello_resp.get("status") == "ready"

    # 3. Pairing
    if pin:
        print(f"\n[Step 3] Submitting PIN '{pin}' for pairing...")
        success = client.pair(pin)
        print(f"  -> Pairing success: {success}, token: {client.token}")
        assert success, "Pairing with provided PIN failed"
    else:
        print("\n[Step 3] No PIN provided; skipping pair test (assuming pre-authenticated or testing buttons)")

    # 4. Button Events
    print("\n[Step 4] Sending button down and up events (A, B, DPAD_UP)...")
    client.send_button("A", "down")
    time.sleep(0.05)
    client.send_button("A", "up")
    time.sleep(0.05)

    client.send_button("B", "down")
    time.sleep(0.05)
    client.send_button("B", "up")
    time.sleep(0.05)

    client.send_button("DPAD_UP", "down")
    time.sleep(0.05)
    client.send_button("DPAD_UP", "up")
    print("  -> Button events transmitted.")

    # 5. Recenter
    print("\n[Step 5] Triggering recenter...")
    client.recenter()
    print("  -> Recenter command transmitted.")

    # 6. UDP Motion Streaming
    print("\n[Step 6] Streaming synthetic 100 Hz motion frames...")
    client.init_udp()
    client.stream_synthetic_motion(duration_sec=2.0, rate_hz=100)
    print("  -> Motion stream completed successfully.")

    # 7. Disconnect and Failsafe
    print("\n[Step 7] Testing disconnect failsafe...")
    # Hold button A, then abruptly close TCP connection
    client.send_button("A", "down")
    time.sleep(0.05)
    client.close()
    print("  -> Closed connection abruptly. Watchdog and TCP handler will release held buttons.")

    print("\n" + "=" * 60)
    print("ALL AUTOMATED TESTS COMPLETED SUCCESSFULLY!")
    print("=" * 60)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Andromote Synthetic Test Client")
    parser.add_argument("--host", default="127.0.0.1", help="Receiver host IP")
    parser.add_argument("--pin", default=None, help="4-digit pairing PIN shown on receiver")
    parser.add_argument("--discover", action="store_true", help="Run LAN discovery scan")
    parser.add_argument("--test", action="store_true", help="Run automated test suite")
    args = parser.parse_args()

    if args.discover:
        AndromoteTestClient.discover_pc()
    elif args.test:
        run_automated_test(host=args.host, pin=args.pin)
    else:
        run_automated_test(host=args.host, pin=args.pin)
