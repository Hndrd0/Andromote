# Andromote 🎮📱

[![Platform](https://img.shields.io/badge/Platform-Windows%20%7C%20Android-0078D6.svg?logo=windows&logoColor=white)](#)
[![Python](https://img.shields.io/badge/Python-3.10%2B-3776AB.svg?logo=python&logoColor=white)](https://www.python.org/)
[![Kotlin](https://img.shields.io/badge/Kotlin-Jetpack%20Compose-7F52FF.svg?logo=kotlin&logoColor=white)](https://kotlinlang.org/)
[![Dolphin](https://img.shields.io/badge/Dolphin-DSU%20%2F%20Cemuhook-009688.svg?logo=dolphin&logoColor=white)](https://dolphin-emu.org/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

> **Turn any Android smartphone into an authentic, ultra-low-latency Nintendo Wii Remote and motion air-mouse for Windows PCs and the Dolphin Emulator.**

---

## 🌟 Highlights

* 🎮 **Authentic Virtual Wii Remote UI:** Beautiful, tactile Jetpack Compose interface with D-Pad, oversized A button, underside B trigger, `—` (Minus), `+` (Plus), `🏠` (Home), `1`, `2`, and player LED indicators.
* 🕹️ **Auto-Rotating NES Gamepad Mode:** Rotate your phone 90° sideways to instantly switch to a horizontal retro NES gamepad layout. Features **hardware-gravity orientation detection** that works even if your Android system auto-rotate lock is enabled!
* 🎯 **Butter-Smooth 1€ Motion Pointing:** Fused 3D quaternion raycasting paired with an adaptive **One-Euro (1€) filter** and gravity EMA vector smoothing eliminates trembling hands without adding lag during fast flicks.
* ⚡ **Wii Physical Gesture Recognition:** Recognizes rapid shaking, wrist flicks, straight thrusts, Wii Wheel tilt steering, off-screen aiming, and key twisting in real time.
* 🐬 **Native Dolphin Emulator Support:** Embedded Cemuhook / DSU motion server (UDP `26760`) formatted to Dolphin's strict 100-byte `PadDataResponse` specification. Streams calibrated 6-DOF motion ($g$ and $^\circ/\text{s}$) and full controller button states directly into Dolphin.
* 💥 **Off-Screen Aim & Reload:** 3D angular cone tracking detects when you point away from the monitor ($\theta_{cone} > 32^\circ$), freezing the cursor at the screen edge and triggering weapon reload (`KEY_R` / Right-Click), just like classic arcade light-gun rail shooters.
* 🔒 **Zero-Config LAN Discovery & PIN Pairing:** Connects automatically over local Wi-Fi via UDP broadcast discovery (`42424`) and authenticates with a 4-digit PIN and HMAC SHA-256 session token (`42425`).
* 🛡️ **Fail-Safe Watchdog:** Native Windows `SendInput` dispatcher with an automatic watchdog timer that releases held buttons if connection drops.
* 📦 **Standalone Windows Executable:** Runs out-of-the-box as a single standalone binary (`Andromote.exe`) without needing Python or external drivers.

---

## 🏗️ System Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                 Android Smartphone (Andromote App)           │
│  • Jetpack Compose Tactile UI (Wii Remote + NES Gamepad)    │
│  • Force Gravity Auto-Rotate (Bypasses OS auto-rotate lock) │
│  • 100 Hz Fusion (Rotation Vector + Gyro + Accelerometer)   │
└──────────────┬───────────────────────────────┬──────────────┘
               │ UDP Broadcast (Port 42424)    │
               │ (ZeroConf Auto-Discovery)     │
               ▼                               │
┌──────────────────────────────────────────────▼──────────────┐
│                  Dual-Channel Networking                     │
│  • TCP Port 42425: Auth (PIN/HMAC), Buttons, Recenter, Ping │
│  • UDP Port 42426: 100 Hz Binary Motion Frames (44 bytes)   │
└──────────────┬───────────────────────────────┬──────────────┘
               ▼                               ▼
┌─────────────────────────────────────────────────────────────┐
│                 Windows Receiver (PySide6 GUI)               │
│  • One-Euro Adaptive Filter & Gravity EMA Motion Smoothing   │
│  • Wii Gesture Engine (Shake, Flick, Thrust, Steer, Twist)   │
│  • 3D Cone Off-Screen Aim & Reload Detection                │
│  • Customizable Windows Mouse & Keyboard Input Dispatcher   │
│  • Background System Tray Support                           │
└──────────────────────────────┬──────────────────────────────┘
                               │ UDP Port 26760
                               ▼
┌─────────────────────────────────────────────────────────────┐
│            Dolphin Emulator (Cemuhook / DSU Server)         │
│  • Exact 100-byte PadDataResponse packet structure          │
│  • Full Gyroscope & Accelerometer 6-DOF Motion Input        │
│  • Complete Button Mapping (Home/PS, Cross, Square, etc.)    │
└─────────────────────────────────────────────────────────────┘
```

---

## 🚀 Quick Start

### 1. Launch the Windows Receiver
Download and double-click `Andromote.exe` from the latest release (or build from source):
```cmd
python windows/main.py
```
Note the **4-digit PIN** displayed on the receiver screen.

### 2. Install & Open the Android App
Download `Andromote.apk` to your phone and install:
```cmd
adb install -r Andromote.apk
```

### 3. Connect & Play
1. The app will auto-discover your PC via Wi-Fi. Tap your PC in the discovered list.
2. Enter the 4-digit PIN when prompted.
3. Aim your phone at your monitor and move it like a Wii Remote to control your cursor!
4. Tap **A** to left-click, **B** to right-click, or tap **🎯 Recenter** at any time to re-zero the reference angle.

---

## 🐬 Dolphin Emulator Setup

Andromote features an integrated DSU / Cemuhook server compatible with Dolphin, Cemu, and PCSX2.

### Step-by-Step Configuration:
1. Open **Dolphin Emulator** → click **Controllers**.
2. Under **Wii Remotes**, set **Wii Remote 1** to **Emulated Wii Remote** → click **Configure**.
3. Under **Motion Input**, check **Alternate Input Sources** (DSU Client):
   * Server Address: `127.0.0.1`
   * Port: `26760`
4. At the top of the Configure dialog, set **Device** to: `DSUClient/0/...`
5. **Mapping Dolphin Buttons:**
   Click each button field and press the button on your phone (or right-click and type the identifier):

| Wii Remote Function | Phone Button | Dolphin Detected ID | Direct String |
| :--- | :--- | :--- | :--- |
| **Home** | 🏠 Home | **`PS`** | `PS` |
| **A** | A Button | **`Cross`** | `Cross` |
| **B (Trigger)** | B Trigger | **`R2`** | `R2` |
| **1** | 1 Button | **`Square`** | `Square` |
| **2** | 2 Button | **`Circle`** | `Circle` |
| **+ (Plus)** | + Button | **`Options`** | `Options` |
| **— (Minus)** | — Button | **`Share`** | `Share` |
| **D-Pad Up** | ▲ Up | **`Pad N`** | `Pad N` |
| **D-Pad Down** | ▼ Down | **`Pad S`** | `Pad S` |
| **D-Pad Left** | ◀ Left | **`Pad W`** | `Pad W` |
| **D-Pad Right** | ▶ Right | **`Pad E`** | `Pad E` |

---

## ⚡ Wii Motion Gestures

In the Windows receiver, navigate to the **Wii Gestures** tab to toggle gestures, customize key bindings, and view live glowing HUD indicator badges:

| Gesture | Real-World Motion | In-Game Action / Default Key |
| :--- | :--- | :--- |
| **⚡ Rapid Shaking** | Shake phone quickly back and forth | Spin attack / Shake off (`KEY_SPACE`) |
| **🎣 Wrist Snapping** | Sharp upward flick of the wrist | Cast fishing line / Jump (`KEY_UP`) |
| **🥊 Straight Thrust** | Punch / thrust phone straight forward | Jab / Sword lunge (`KEY_F`) |
| **🏎️ Tilt Steering** | Lean horizontal phone like a steering wheel | Steer Left / Right (`KEY_A` / `KEY_D`) |
| **💥 Off-Screen Reload** | Aim phone away from the monitor ($>32^\circ$) | Reload weapon (`KEY_R`) |
| **🔑 Key Twisting** | Fast wrist roll / tilt | Peek / Roll sideways (`KEY_Q` / `KEY_E`) |

---

## 🛠️ Building from Source

### Windows Receiver
* Requires **Python 3.10+**.
```cmd
git clone https://github.com/your-username/Andromote.git
cd Andromote
pip install -r requirements.txt
python windows/main.py
```

To build a standalone `.exe`:
```cmd
python windows/build_exe.py
# Output generated in dist/Andromote.exe
```

### Android App
* Requires **Android Studio Ladybug+** and **JDK 21**.
```bash
cd android
./gradlew assembleDebug
# Output generated in android/app/build/outputs/apk/debug/app-debug.apk
```

---

## 🧪 Automated Tests

Andromote comes with 22 automated unit and end-to-end integration tests:
```bash
python windows/tests/test_phase1.py   # Math, Quaternion, 1€ Filter, WinInput, Settings
python windows/tests/test_phase2.py   # Pairing PIN, Handshake, UDP Motion Framing
python windows/tests/test_dsu.py      # Dolphin Cemuhook 100-byte & PS Button
python windows/tests/test_e2e.py      # Full client-server synthetic stream
python windows/tests/test_gestures.py # Shake, Flick, Thrust, Steer, Off-Screen, Twist
```

---

## 📄 License

Distributed under the **MIT License**. See [`LICENSE`](LICENSE) for more information.

---

## 🤝 Contributing

Contributions, feature requests, and bug reports are welcome! Check out [`CONTRIBUTING.md`](CONTRIBUTING.md) to get started.
