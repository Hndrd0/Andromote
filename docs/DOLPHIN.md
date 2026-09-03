# Dolphin Emulator Motion Integration Guide

Andromote features a built-in **Cemuhook / DSU Protocol Server** running on UDP port `26760`.
This allows Dolphin Emulator to use your Android phone as a high-fidelity, real motion-sensing Wii Remote.

---

## How it Works

Unlike basic keyboard/mouse remappers that convert tilt to digital keys, the DSU server sends raw, calibrated **3-axis Gyroscope (degrees/second)** and **3-axis Accelerometer (g)** values directly into Dolphin's internal Wii Remote motion pipeline.

* **Pointer Aiming:** Smooth, authentic Wii Remote pointer behavior driven by phone gyroscopes.
* **Wii MotionPlus Support:** 1:1 motion tracking in games like *Wii Sports Resort*, *The Legend of Zelda: Skyward Sword*, and *Red Steel 2*.
* **Shake & Gestures:** Natural flick/shake detection in games like *Super Mario Galaxy* and *New Super Mario Bros. Wii*.
* **Full Button Mappings:** D-Pad, A, B, 1, 2, Plus, Minus, and Home.

---

## Step-by-Step Configuration

### Step 1: Enable DSU in Dolphin
1. Launch **Dolphin Emulator**.
2. Click **Controllers** on the top toolbar.
3. Under the **Alternate Input Sources** section:
   * Check **Enable**.
   * Server Address: `127.0.0.1`
   * Port: `26760`
   * Click **Description / Test** to verify connection.

---

### Step 2: Configure the Emulated Wii Remote
1. In the Dolphin Controllers window, look under **Wii Remotes**.
2. Set **Wii Remote 1** to **Emulated Wii Remote**.
3. Click **Configure**.
4. In the top-left **Device** dropdown, select:
   ```text
   DSUClient/0/Virtual Android Wiimote
   ```
   *(or `DSUClient/0/DualShock 4` depending on your Dolphin version)*

---

### Step 3: Load the Included Profile (Quickest Setup)
1. Copy the profile file:
   ```text
   dolphin_profiles/WiimoteNew.ini
   ```
   to your Dolphin User Profiles folder:
   ```text
   %APPDATA%\Dolphin Emulator\Config\Profiles\Wiimote\
   ```
   *(or `Documents\Dolphin Emulator\Config\Profiles\Wiimote\`)*
2. In Dolphin's Wii Remote configuration window, under **Profile**, select `WiimoteNew` and click **Load**.

---

### Step 4: Manual Button & Motion Mapping (Alternative)

If mapping manually:
* **Buttons:**
  * **A:** Click on A, tap 'A' on phone.
  * **B:** Click on B, tap 'B' (or volume down) on phone.
  * **1 / 2:** Map to 1 and 2 buttons.
  * **+ / - / Home:** Map to Plus, Minus, Home.
* **Motion Input Tab:**
  * Under **Point:** Map to IR Axis 0 and 1.
  * Under **Shake:** Map to Axis X, Y, Z.
  * Under **Motion Plus / IMU:**
    * Accelerometer: Map Accel Up, Down, Left, Right, Forward, Backward.
    * Gyroscope: Map Gyro Pitch Up/Down, Gyro Roll Left/Right, Gyro Yaw Left/Right.

---

## Tips for Best Dolphin Gameplay

1. **Recenter Before Playing:** Tap the **Home** button or on-screen **Recenter** button while holding the phone comfortably pointing at your monitor.
2. **Volume Buttons as Trigger:** By default, pressing the physical **Volume Down** or **Volume Up** button on your Android phone triggers the **B button**, giving you a tactile rear trigger grip!
