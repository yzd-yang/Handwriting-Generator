# -*- mode: python ; coding: utf-8 -*-
# PyInstaller spec for handwriting backend
# 使用方法：pyinstaller backend.spec --noconfirm

import os
import sys

# 仓库根目录（spec 文件在 packaging/ 下，所以 .. 就是仓库根）
REPO_ROOT = os.path.abspath(os.path.join(SPECPATH, '..'))

# 调试信息
print(f"[SPEC] REPO_ROOT: {REPO_ROOT}")
print(f"[SPEC] app.py: {os.path.join(REPO_ROOT, 'backend', 'app.py')}")

block_cipher = None

# ── 收集隐式依赖 ──
datas = []
binaries = []
hiddenimports = []

# 添加后端目录到 sys.path（确保能找到所有模块）
sys.path.insert(0, os.path.join(REPO_ROOT, 'backend'))

# uvicorn / fastapi 子模块
for pkg in ['uvicorn', 'fastapi', 'starlette', 'pydantic', 'anyio']:
    try:
        from PyInstaller.utils.hooks import collect_all
        d, b, h = collect_all(pkg)
        datas += d
        binaries += b
        hiddenimports += h
    except Exception as e:
        print(f"Warning: collect_all({pkg}) failed: {e}")

# cv2 / numpy / PIL / sklearn / scipy
for pkg in ['cv2', 'numpy', 'sklearn', 'scipy', 'PIL', 'fitz', 'pypandoc']:
    try:
        d, b, h = collect_all(pkg)
        datas += d
        binaries += b
        hiddenimports += h
    except Exception as e:
        print(f"Warning: collect_all({pkg}) failed: {e}")

# handright 数据文件
try:
    from PyInstaller.utils.hooks import collect_data_files
    datas += collect_data_files('handright')
except Exception as e:
    print(f"Warning: collect_data_files(handright) failed: {e}")

# ── 额外资源 ──
# 字体文件 → app_root/font_assets/
ttf_files_dir = os.path.join(REPO_ROOT, 'ttf_files')
if os.path.isdir(ttf_files_dir):
    datas.append((ttf_files_dir, 'font_assets'))
    print(f"[OK] Fonts: {ttf_files_dir}")
else:
    print(f"[WARN] ttf_files/ not found at {ttf_files_dir}")

# 前端构建产物 → app_root/frontend/
FE_DIST = os.path.join(REPO_ROOT, 'frontendVite', 'dist')
if os.path.isdir(FE_DIST):
    datas.append((FE_DIST, 'frontend'))
    print(f"[OK] Frontend: {FE_DIST}")
else:
    print(f"[WARN] frontend dist not found at {FE_DIST}")

# Pandoc 二进制
PANDOC_DIR = os.path.join(REPO_ROOT, 'packaging', 'pandoc')
if os.path.isdir(PANDOC_DIR):
    datas.append((PANDOC_DIR, 'pandoc'))
    print(f"[OK] Pandoc: {PANDOC_DIR}")
else:
    print(f"[WARN] pandoc/ not found at {PANDOC_DIR}")

a = Analysis(
    [os.path.join(REPO_ROOT, 'backend', 'app.py')],
    pathex=[
        os.path.join(REPO_ROOT, 'backend'),
        REPO_ROOT,
    ],
    binaries=binaries,
    datas=datas,
    hiddenimports=hiddenimports + [
        'uvicorn.logging',
        'uvicorn.loops',
        'uvicorn.loops.auto',
        'uvicorn.protocols',
        'uvicorn.protocols.http.auto',
        'uvicorn.protocols.websockets.auto',
        'identify',
        'pdf',
        'task_store',
        'task_types',
        'config',
        'services.cleanup',
        'services.file_processing',
        'services.fonts',
        'services.generation',
        'services.image_utils',
        'services.task_manager',
        'utils.logging_setup',
        'schedule_clean',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        'pytest',
        'tests',
        'mysql.connector',
        'pymysql',
        'matplotlib',
        'tkinter',
        'PyQt5',
        'PySide6',
        'IPython',
        'notebook',
        'jupyter',
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
    [],
    exclude_binaries=True,
    name='backend',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_shell=False,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='手写生成器',
)
