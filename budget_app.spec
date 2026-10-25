# -*- mode: python ; coding: utf-8 -*-
from pathlib import Path

block_cipher = None

a = Analysis(
    ['app/main.py'],
    pathex=['.'],
    binaries=[],
    datas=[
        ('app/ui.html', 'app'),
        ('app/css', 'app/css'),
        ('app/js', 'app/js'),
    ],
    hiddenimports=[
        'pycparser.lextab',
        'pycparser.yacctab',
        'clr_loader',
        'pythonnet',
        'webview',
        'openpyxl',
        'openpyxl.worksheet._reader',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=['tkinter', 'matplotlib', 'scipy'],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='Budgeting App',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    version='app/file_version_info.txt',
)
