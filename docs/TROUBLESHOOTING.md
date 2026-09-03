# Andromote Troubleshooting Guide

Solutions for common networking, motion, and input issues.

---

## 1. Network Discovery & Connection Issues

### Phone cannot find the Windows PC automatically
* **Windows Network Profile:** Windows defaults to "Public Network" which blocks UDP discovery broadcasts.
  * Open Windows **Settings** → **Network & Internet** → **Wi-Fi** (or Ethernet) → click your network.
  * Change Network Profile type from **Public** to **Private**.
* **Router "AP Isolation" / Guest Network:**
  * Guest networks prevent devices from communicating with each other. Ensure both PC and phone are connected to the main Wi-Fi network.
* **Manual IP Fallback:**
  * Look at the Windows Receiver header bar to find your PC's IP address (e.g., `192.168.1.100`).
  * On the phone app, navigate to **Connection** → **Manual IP Entry** → enter the IP and tap **Connect Directly**.

---

## 2. Motion Aiming & Cursor Drift

### The cursor slowly drifts when the phone is held still
* Microscopic sensor noise can accumulate. Increase the **Deadzone** slider in the receiver's **Motion Tuning** tab (e.g., from `0.04` to `0.06` or `0.08`).
* Tap the **Recenter** (Home) button while holding the phone pointing at the screen to calibrate the neutral center point.

### Motion feels too fast or too slow
* Open the **Motion Tuning** tab in the Windows Receiver or the **Calibration** screen on the Android app.
* Adjust **X Sensitivity** (horizontal) and **Y Sensitivity** (vertical).
* Adjust the **Acceleration** slider to tune how fast flicks amplify cursor leaps.

---

## 3. Latency & Jitter Optimization

### Motion feels sluggish or choppy
* **Use 5 GHz Wi-Fi:** 2.4 GHz Wi-Fi networks are prone to microwave and Bluetooth interference. Switching your phone and PC to 5 GHz reduces network jitter to under 4 ms.
* **Disable Android Battery Saver:** Android Battery Saver mode throttles background sensor sampling rates from 200 Hz down to 20 Hz. Ensure standard performance mode is active while gaming.
* **Adjust Smoothing:** Lower the **Smoothing** slider in Motion Tuning from `0.30` down to `0.15` for snappier, raw response.

---

## 4. Input Safety & Stuck Buttons

### What happens if the phone battery dies while holding down the mouse button?
* Andromote features an automated **watchdog timer** (default: 0.5s) and a **disconnect failsafe**.
* As soon as network communication is interrupted, the receiver's `release_all_inputs()` immediately releases all held mouse buttons and keyboard keys, preventing stuck clicks.

### Emergency Input Stop
* If you ever need to immediately disable all inputs:
  1. Click **Emergency Release Inputs** on the receiver Dashboard.
  2. Or right-click the Andromote tray icon and click **Toggle Controller** to disable control globally.
