# -*- mode: python ; coding: utf-8 -*-
# Build Windows / Linux (GitHub Actions). Pas de BUNDLE macOS — voir Mnemos.spec.
# Nom d’exécutable ASCII pour éviter les soucis de chemins sous Windows.

import re

block_cipher = None

with open("mnemos/config.py", encoding="utf-8") as f:
    _v = re.search(r'^VERSION\s*=\s*"([^"]+)"', f.read(), re.M)
    APP_VERSION = _v.group(1) if _v else "0.0.0"

a = Analysis(
    ["quiz_rappel_gui.py"],
    pathex=[],
    binaries=[],
    datas=[
        ("Mnemos_icon.png", "."),
        ("Plan_hebdomadaire_Mnemos.pdf", "."),
    ],
    hiddenimports=[
        "PIL", "PIL._tkinter_finder", "certifi",
        "mnemos", "mnemos.bootstrap_env", "mnemos.config", "mnemos.theme",
        "mnemos.paths", "mnemos.domain.table", "mnemos.storage",
        "mnemos.ui", "mnemos.ui._quiz_shared", "mnemos.ui.widgets", "mnemos.ui.assets",
        "mnemos.ui.screens", "mnemos.ui.screens.drawing", "mnemos.ui.screens.flashcard",
        "mnemos.ui.screens.home", "mnemos.ui.screens.preferences", "mnemos.ui.screens.quiz",
        "mnemos.ui.screens.stats", "mnemos.ui.screens.table_browse",
        "mnemos.ui.screens.table_edit", "mnemos.updater", "mnemos.updater.check",
        "mnemos.updater.install", "mnemos.updater.http", "mnemos.updater.releases",
    ],
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
