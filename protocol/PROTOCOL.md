# Andromote Network Protocol Specification

**Protocol Version:** `1`  
**Architecture:** Client (Android Phone) → Server (Windows PC Receiver)

Andromote uses a hybrid networking model optimized for high-frequency motion streaming and reliable, deterministic button events over local Wi-Fi:

* **UDP Port 42424:** LAN Device Discovery (Broadcast / Beacon)
* **TCP Port 42425:** Reliable Control, Pairing PIN Auth, Button Events, and Pings
* **UDP Port 42426:** Ultra-Low-Latency Motion Streaming (100–200 Hz)
* **UDP Port 26760:** Dolphin Emulator DSU / Cemuhook Protocol Server

---

## 1. LAN Device Discovery (UDP 42424)

### Discovery Request (Android → PC Broadcast)
Sent to `255.255.255.255:42424`:
```json
{
  "type": "discovery_request"
}
```

### Discovery Response (PC → Android)
Sent back to the requesting client's address and port:
```json
{
  "type": "discovery_response",
  "protocol_version": 1,
  "hostname": "DESKTOP-SUSHI",
  "ip": "192.168.1.100",
  "tcp_port": 42425,
  "motion_port": 42426,
  "dsu_port": 26760
}
```
*The Windows receiver also periodically broadcasts this beacon every 3 seconds to facilitate instant discovery when the phone app opens.*

---

## 2. TCP Control Channel (Port 42425)

The TCP connection is framed using 4-byte big-endian length prefixing:
```text
┌───────────────────────────┬──────────────────────────────────────────┐
│  Payload Length (4 bytes) │      JSON Message Body (UTF-8)           │
│       uint32 big-endian   │            N bytes                       │
└───────────────────────────┴──────────────────────────────────────────┘
```

### 2.1 Handshake: `hello`
```json
// Android -> PC
{
  "type": "hello",
  "device_id": "9f7b1c3e-...",
  "protocol_version": 1
}

// PC -> Android
{
  "type": "hello_reply",
  "protocol_version": 1,
  "needs_pairing": true,
  "status": "ready"
}
```

### 2.2 Pairing Flow: `pair`
```json
// Android -> PC
{
  "type": "pair",
  "pin": "7429",
  "device_id": "9f7b1c3e-...",
  "device_name": "Google Pixel 8"
}

// PC -> Android (Success)
{
  "type": "pair_reply",
  "status": "success",
  "token": "a1b2c3d4e5f6... (64 hex characters)",
  "message": "Paired successfully."
}

// PC -> Android (Failure)
{
  "type": "pair_reply",
  "status": "error",
  "message": "Incorrect pairing PIN."
}
```

### 2.3 Authentication with Saved Token: `auth`
```json
// Android -> PC
{
  "type": "auth",
  "token": "a1b2c3d4e5f6...",
  "device_id": "9f7b1c3e-...",
  "device_name": "Google Pixel 8"
}

// PC -> Android
{
  "type": "auth_reply",
  "status": "success",
  "message": "Authenticated."
}
```

### 2.4 Button Events: `button`
Button events strictly use `down` and `up` states to allow press-and-hold, dragging, and charging:
```json
{
  "type": "button",
  "button": "A",
  "state": "down",
  "timestamp": 1725300000123
}
```
Supported Button Identifiers:
`DPAD_UP`, `DPAD_DOWN`, `DPAD_LEFT`, `DPAD_RIGHT`, `A`, `B`, `1`, `2`, `PLUS`, `MINUS`, `HOME`.

### 2.5 Recenter Trigger: `recenter`
```json
{
  "type": "recenter"
}
```

### 2.6 Keepalive & Latency Measurement: `ping` / `pong`
```json
// Android -> PC
{
  "type": "ping",
  "timestamp": 1725300000500,
  "last_rtt": 12.5
}

// PC -> Android
{
  "type": "pong",
  "client_timestamp": 1725300000500,
  "server_timestamp": 1725300000506
}
```

---

## 3. High-Rate Motion Stream (UDP Port 42426)

Motion packets are streamed at 100–200 Hz.

### 3.1 Compact Binary Packet Format (`WMO1`, 54 Bytes)
Packed with standard C struct alignment (Big-Endian `!4s H Q 4f 3f 3f`):

| Offset | Type | Size | Field | Description |
|---|---|---|---|---|
| `0` | `char[4]` | 4 B | `magic` | Fixed ASCII `b"WMO1"` |
| `4` | `uint16` | 2 B | `seq` | Monotonically increasing sequence number (0–65535) |
| `6` | `uint64` | 8 B | `timestamp` | Monotonic or epoch timestamp in milliseconds |
| `14` | `float32` | 4 B | `qx` | Orientation quaternion X component |
| `18` | `float32` | 4 B | `qy` | Orientation quaternion Y component |
| `22` | `float32` | 4 B | `qz` | Orientation quaternion Z component |
| `26` | `float32` | 4 B | `qw` | Orientation quaternion W (scalar) component |
| `30` | `float32` | 4 B | `gx` | Gyroscope angular velocity around X in rad/s |
| `34` | `float32` | 4 B | `gy` | Gyroscope angular velocity around Y in rad/s |
| `38` | `float32` | 4 B | `gz` | Gyroscope angular velocity around Z in rad/s |
| `42` | `float32` | 4 B | `ax` | Accelerometer X in m/s² |
| `46` | `float32` | 4 B | `ay` | Accelerometer Y in m/s² |
| `50` | `float32` | 4 B | `az` | Accelerometer Z in m/s² |

### 3.2 JSON Motion Packet Fallback (Debug)
```json
{
  "type": "motion",
  "version": 1,
  "sequence": 1420,
  "timestamp": 1725300000123,
  "qx": 0.012, "qy": 0.124, "qz": -0.045, "qw": 0.991,
  "gx": 0.05, "gy": -0.12, "gz": 0.02,
  "ax": 0.1, "ay": -0.2, "az": 9.81
}
```

---

## 4. Dolphin DSU / Cemuhook Protocol (UDP Port 26760)

The receiver implements the standard Cemuhook DSU protocol specifications:
1. **Header (16 Bytes):**
   - Magic: `DSUS` (Server) / `DSUC` (Client)
   - Protocol Version: `1001`
   - Packet Length: uint16 little-endian
   - CRC32: IEEE 802.3 CRC32 of full packet with CRC field zeroed out
   - Server / Client ID: uint32
2. **Message Types:**
   - `0x00100000`: Version Information
   - `0x00100001`: Controller Info (Slot 0, Full Gyro, Bluetooth wireless, MAC)
   - `0x00100002`: Controller Data Stream (Accelerometer in g, Gyroscope in deg/s, digital buttons)
