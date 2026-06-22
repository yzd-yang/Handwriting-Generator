# -*- mode: python ; coding: utf-8 -*-
# PyInstaller spec for launcher (启动器)
# 构建: pyinstaller launcher.spec --noconfirm

import os
from PyInstaller.utils.hooks import collect_all

block_cipher = None

# 收集 pystray / PIL 依赖
datas = []
binaries = []
hiddenimports = []

for pkg in ['PIL', 'pystray']:
    try:
        d, b, h = collect_all(pkg)
        datas += d
        binaries += b
        hiddenimports += h
    except Exception as e:
        print(f"Warning: collect_all({pkg}) failed: {e}")

# 补充 pystray 的平台特定子模块
hiddenimports += [
    'pystray._appindicator',
    'pystray._darwin',
    'pystray._win32',
]

a = Analysis(
    [os.path.join(SPECPATH, 'launcher.py')],
    pathex=[],
    binaries=binaries,
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        'matplotlib',
        'tkinter',
        'PyQt5',
        'PySide6',
    ],
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
    a.datas,
    [],
    name='手写生成器',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_shell=False,
    icon=os.path.join(SPECPATH, 'icon.ico') if os.path.isfile(os.path.join(SPECPATH, 'icon.ico')) else None,
)
