# -*- mode: python ; coding: utf-8 -*-
from PyInstaller.utils.hooks import collect_data_files

import sys
import os

# Check for dev build flag
dev_build = os.environ.get('DEV_BUILD') == '1'

datas = []
if dev_build:
    datas.append(('dev_mode.txt', '.'))

datas_files = collect_data_files('litellm')

a = Analysis(
    ['src/main.py'],
    pathex=[],
    binaries=[],
    datas=datas_files,
    hiddenimports=['win32api', 'win32timezone', 'win32security', 'win32con', 'psutil', 'litellm', 'litellm.litellm_core_utils', 'litellm.litellm_core_utils.tokenizers'],
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
    name='urmom',
    debug=dev_build,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=dev_build,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
