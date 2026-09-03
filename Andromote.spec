# -*- mode: python ; coding: utf-8 -*-


a = Analysis(
    ['C:\\Users\\sushi\\Downloads\\Andromote\\windows\\main.py'],
    pathex=['C:\\Users\\sushi\\Downloads\\Andromote'],
    binaries=[],
    datas=[],
    hiddenimports=['PySide6', 'PySide6.QtCore', 'PySide6.QtGui', 'PySide6.QtWidgets', 'windows', 'windows.input', 'windows.motion', 'windows.networking', 'windows.ui', 'windows.config'],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
    optimize=0,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name='Andromote',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
