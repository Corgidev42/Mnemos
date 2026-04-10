# -*- mode: python ; coding: utf-8 -*-
# Build Windows / Linux (GitHub Actions). Pas de BUNDLE macOS — voir Mnemos.spec.
# Nom d’exécutable ASCII pour éviter les soucis de chemins sous Windows.

import re

block_cipher = None

with open("quiz_rappel_gui.py", encoding="utf-8") as f:
    _v = re.search(r'VERSION\s*=\s*"([^"]+)"', f.read())
    APP_VERSION = _v.group(1) if _v else "0.0.0"

a = Analysis(
    ["quiz_rappel_gui.py"],
    pathex=[],
    binaries=[],
    datas=[("Mnemos_icon.png", ".")],
    hiddenimports=["PIL", "PIL._tkinter_finder"],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name="Mnemos",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=False,
    upx_exclude=[],
    name="Mnemos",
)
