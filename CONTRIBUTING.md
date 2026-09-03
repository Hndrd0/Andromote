# Contributing to Andromote

Thank you for your interest in contributing to Andromote! Whether you're reporting a bug, proposing a feature, or writing code, we welcome your contributions.

---

## 🛠️ Development Setup

### 1. Windows Receiver (Python)
- **Prerequisites:** Python 3.10+ (Python 3.12 recommended).
- **Clone & Install Dependencies:**
  ```bash
  git clone https://github.com/your-username/Andromote.git
  cd Andromote
  pip install -r requirements.txt  # Or: pip install PySide6 numpy
  ```
- **Running from Source:**
  ```bash
  python windows/main.py
  ```
- **Running Tests:**
  ```bash
  python windows/tests/test_phase1.py
  python windows/tests/test_phase2.py
  python windows/tests/test_dsu.py
  python windows/tests/test_e2e.py
  python windows/tests/test_gestures.py
  ```
- **Building Standalone Binary:**
  ```bash
  pip install pyinstaller
  python windows/build_exe.py
  ```

### 2. Android App (Kotlin / Compose)
- **Prerequisites:** Android Studio Ladybug (or newer), JDK 21, Android SDK 34+.
- **Building Debug APK:**
  ```bash
  cd android
  ./gradlew assembleDebug
  ```
- **Installing to Device:**
  ```bash
  adb install -r app/build/outputs/apk/debug/app-debug.apk
  ```

---

## 🧪 Pull Request Guidelines

1. **Keep Commits Clean & Focused:** Write descriptive commit messages.
2. **Ensure All Automated Tests Pass:** Verify all unit and integration tests run with 0 errors before submitting.
3. **Follow Idiomatic Code Style:**
   - Python: PEP 8 guidelines, type hints where appropriate.
   - Kotlin: Kotlin coding conventions with Jetpack Compose idioms.
4. **Update Documentation:** If you add new gestures, network protocol commands, or UI options, update `README.md` and `docs/` accordingly.

---

## 💬 Community & Questions

Feel free to open an Issue or Discussion for feature requests, emulator compatibility questions, or bug reports.
