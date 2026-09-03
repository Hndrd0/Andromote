# Andromote Setup & Installation Guide

Complete guide to building, configuring, and running the Andromote system.

---

## System Requirements

* **Windows PC:** Windows 10 or Windows 11 (64-bit).
* **Android Phone:** Android 7.0 (API 24) or newer with physical **gyroscope** and **accelerometer**.
* **Network:** Both the PC and Phone must be connected to the **same local Wi-Fi network** (or phone connected via Wi-Fi hotspot to PC).

---

## 1. Running the Windows Receiver

### Option A: Standalone Executable (No Python Required)
1. Navigate to the `dist/` directory:
   ```cmd
   cd C:\Users\sushi\downloads\Andromote\dist
   ```
2. Double-click `Andromote.exe` or run from terminal:
   ```cmd
   Andromote.exe
   ```
3. The modern dark-themed receiver dashboard will open, displaying your machine IP and a 4-digit Pairing PIN.

### Option B: Running from Source
If running with Python 3.10+:
1. Install dependencies:
   ```cmd
   pip install PySide6
   ```
2. Launch the receiver:
   ```cmd
   python windows/main.py
   ```
3. Optional flags:
   * `--mock-mode`: Runs without injecting real cursor or keystrokes (ideal for testing).
   * `--no-gui`: Runs headless in the console background.
   * `--debug`: Enables detailed network and sensor debugging logs.

---

## 2. Building the Android Application

### Option A: Building with Android Studio
1. Launch **Android Studio**.
2. Select **Open** and select the folder:
   `C:\Users\sushi\downloads\Andromote\android`
3. Wait for Gradle sync to complete.
4. Connect your phone via USB with USB Debugging enabled, or select an emulator.
5. Click the green **Run** button (or `Shift + F10`) to build and launch on your phone.

### Option B: Building via Gradle CLI
From the `android/` directory:
```bash
./gradlew assembleDebug
```
The compiled APK will be located at:
```text
android/app/build/outputs/apk/debug/app-debug.apk
```
Install directly to your connected Android phone using ADB:
```cmd
adb install -r app/build/outputs/apk/debug/app-debug.apk
```

---

## 3. Windows Firewall Configuration

When running Andromote for the first time, Windows Defender Firewall may prompt you to allow network access.
Ensure **Private Networks** is checked.

If you need to manually open the firewall ports in Windows PowerShell (Administrator):
```powershell
# Discovery UDP
New-NetFirewallRule -DisplayName "Andromote Discovery" -Direction Inbound -Protocol UDP -LocalPort 42424 -Action Allow

# Control TCP
New-NetFirewallRule -DisplayName "Andromote Control" -Direction Inbound -Protocol TCP -LocalPort 42425 -Action Allow

# Motion Stream UDP
New-NetFirewallRule -DisplayName "Andromote Motion" -Direction Inbound -Protocol UDP -LocalPort 42426 -Action Allow

# Dolphin DSU UDP
New-NetFirewallRule -DisplayName "Andromote DSU" -Direction Inbound -Protocol UDP -LocalPort 26760 -Action Allow
```

> [!CAUTION]
> Do NOT forward these ports on your internet router. Andromote is designed strictly for secure, low-latency LAN operation.

---

## 4. Connecting and Pairing

1. **Start the Windows Receiver:**
   The dashboard will show a 4-digit PIN (e.g. `8492`) and indicate `LISTENING`.
2. **Open Andromote on Android:**
   The phone app will automatically scan for your PC.
3. **Select Your PC:**
   Tap your PC's name in the discovered list (or enter the PC IP manually).
4. **Enter PIN:**
   When prompted on the phone, enter the 4-digit PIN shown on your PC monitor.
5. **Ready!**
   The connection status turns green (`CONNECTED`). Move the phone to control the PC mouse cursor!

---

## 5. Compiling Standalone Executable (Packaging)

To rebuild the single-file executable using PyInstaller:
```cmd
python windows/build_exe.py
```
The executable is generated at `dist/Andromote.exe`.
