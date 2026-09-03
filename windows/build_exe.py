"""
PyInstaller Build Script:
Compiles Andromote Windows Receiver into a standalone, single-file executable.
"""

import os
import sys
import subprocess


def build():
    script_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.abspath(os.path.join(script_dir, ".."))
    main_py = os.path.join(script_dir, "main.py")
    dist_dir = os.path.join(project_root, "dist")
    build_dir = os.path.join(project_root, "build")

    print(f"Building Andromote executable from {main_py}...")

    cmd = [
        sys.executable, "-m", "PyInstaller",
        "--name", "Andromote",
        "--onefile",
        "--noconfirm",
        "--clean",
        "--distpath", dist_dir,
        "--workpath", build_dir,
        "--paths", project_root,
        "--hidden-import", "PySide6",
        "--hidden-import", "PySide6.QtCore",
        "--hidden-import", "PySide6.QtGui",
        "--hidden-import", "PySide6.QtWidgets",
        "--hidden-import", "windows",
        "--hidden-import", "windows.input",
        "--hidden-import", "windows.motion",
        "--hidden-import", "windows.networking",
        "--hidden-import", "windows.ui",
        "--hidden-import", "windows.config",
        main_py
    ]

    print("Running command: " + " ".join(cmd))
    res = subprocess.run(cmd, cwd=project_root)
    if res.returncode == 0:
        exe_path = os.path.join(dist_dir, "Andromote.exe")
        print(f"\n[SUCCESS] Standalone executable created at: {exe_path}")
    else:
        print(f"\n[ERROR] PyInstaller build failed with return code {res.returncode}")
        sys.exit(res.returncode)


if __name__ == "__main__":
    build()
