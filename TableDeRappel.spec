# -*- mode: python ; coding: utf-8 -*-
# PyInstaller spec pour Table de Rappel — génère un .app macOS

block_cipher = None

a = Analysis(
    ['quiz_rappel_gui.py'],
    pathex=[],
    binaries=[],
    datas=[
        ('table_rappel.csv', '.'),
        ('stats_rappel.csv', '.'),
    ],
    hiddenimports=[],
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
    name='Table de Rappel',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=True,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='Table de Rappel',
)

# Sur macOS, PyInstaller crée un .app quand on utilise --windowed
# Le spec est conçu pour --onedir (COLLECT) qui produit le .app
