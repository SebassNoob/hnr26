# -*- mode: python ; coding: utf-8 -*-
from PyInstaller.utils.hooks import collect_data_files

import sys
import os

# Check for dev build flag
dev_build = os.environ.get('DEV_BUILD') == '1'

# Initialize lists
datas = []
binaries = []
hiddenimports = ['_ssl', 'win32api', 'win32timezone', 'win32security', 'win32con', 'psutil', 'groq']


datas.append(('assets', 'assets')) 

if dev_build:
    datas.append(('dev_mode.txt', '.'))

datas.append(('.env', '.')) 

datas_files = collect_data_files('litellm')

a = Analysis(
    ['src/main.py'],  # Ensure this path points to your main.py correctly!
    pathex=['src'],
    binaries=binaries,       # Updated list
    datas=datas,             # Updated list
    hiddenimports=hiddenimports, # Updated list
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
    icon='assets/mom.ico'
)