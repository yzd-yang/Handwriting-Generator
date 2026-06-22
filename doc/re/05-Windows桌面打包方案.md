# 05 · Windows 桌面打包方案(文件夹版 exe)

> 目标:把「Vue 前端 + FastAPI 后端」的 Web 项目,打包成 Windows 上**双击 exe 即用**的桌面应用。
> 形态:**PyInstaller --onedir**(一个主 exe + 隐藏子文件夹),用户双击主 exe → 自动启动后端 + 打开浏览器。
> 日期:2026-06-21
> 配套:`00-总览.md` ~ `04-验证方案.md`

---

## 一、方案选型与结论

### 1.1 最终选型

| 维度 | 选择 | 理由 |
|------|------|------|
| 打包工具 | **PyInstaller --onedir** | 启动快(~2s)、出错可看日志、不污染 temp |
| 安装形态 | 文件夹版(免安装,绿色) | 「点开即用」核心诉求;不需要 MSI 安装向导 |
| 前端形态 | FastAPI 内嵌静态文件挂载 | 不需要 nginx,后端直接 serve 前端 dist |
| 浏览器入口 | 启动器自动打开默认浏览器 | 用户不需要手动输地址 |
| 端口 | 固定 5005(冲突时动态顺延) | 兼顾简单与健壮 |
| Pandoc | PyInstaller `--add-data` 内嵌 | 避免运行时下载,离线可用 |
| 图片识别 | **保留** | opencv/numpy/sklearn 一并打包(体积代价 ~120MB) |
| 退出方式 | 关浏览器 + 系统托盘图标右键退出 | 友好的关闭体验 |

### 1.2 产物预期

**用户拿到的文件夹**(可整体压缩成 zip 分发):

```
手写生成器/
├── 手写生成器.exe          ← 用户双击这个(主入口,~20MB 启动器)
├── _internal/              ← PyInstaller 运行时(可对用户隐藏)
│   ├── python312.dll
│   ├── uvicorn/ fastapi/ PIL/ cv2/ ...   (所有依赖)
│   └── ...
├── frontend/               ← 前端构建产物(FastAPI 挂载)
│   ├── index.html
│   └── assets/
├── font_assets/            ← 字体文件(22MB)
├── pandoc/                 ← Pandoc 可执行文件(~40MB,内嵌)
│   └── pandoc.exe
└── runtime/                ← 运行时生成的数据(首次启动创建)
    ├── logs/app.log
    ├── temp/
    └── tasks.db
```

**体积估算**:

| 部分 | 大小 |
|------|------|
| PyInstaller 后端(Python + 依赖,含 cv2/numpy/sklearn) | ~280MB |
| 前端 dist | ~5MB |
| 字体文件 | ~22MB |
| Pandoc 二进制 | ~40MB |
| 启动器 exe | ~20MB |
| **总计(未压缩)** | **~370MB** |
| **zip 压缩后** | **~170MB** |

---

## 二、整体架构

```
用户双击「手写生成器.exe」
        │
        ▼
┌─────────────────────────────────────┐
│  启动器 launcher.exe (PyInstaller)   │
│  1. 选端口(5005 被占则 5006...)      │
│  2. 后台拉起 backend.exe(uvicorn)   │
│  3. 等待 /api/health 200(就绪探针)   │
│  4. 自动打开浏览器 http://localhost:port│
│  5. 系统托盘显示图标(右键可退出)      │
│  6. 监听 backend 进程,崩了弹错提示   │
└─────────────────────────────────────┘
        │ 子进程
        ▼
┌─────────────────────────────────────┐
│  backend.exe (PyInstaller --onedir)  │
│  - FastAPI + uvicorn                 │
│  - 挂载 frontend/ 为静态根           │
│  - 挂载 /api/* 路由                  │
│  - 字体/Pandoc/temp 都用相对路径     │
└─────────────────────────────────────┘
        ▲ HTTP
        │
┌─────────────────────────────────────┐
│  浏览器 (用户的 Chrome/Edge)         │
│  访问 http://localhost:5005          │
└─────────────────────────────────────┘
```

**关键设计**:前端和后端在**同一个端口**(5005),FastAPI 同时 serve 前端静态文件和后端 API,避免跨域和双端口复杂度。

---

## 三、前置改造(代码改动)

打包前,后端代码需要做 3 处小改造,让它能感知「桌面模式」。这些改造**不影响现有 Docker/开发模式**(通过环境变量切换)。

### 3.1 后端挂载前端静态文件

当前后端只服务 `/api/*`,桌面模式下需要同时 serve 前端。新增挂载逻辑:

```python
# backend/app.py 末尾、路由注册之后加入
import os
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

DESKTOP_MODE = os.getenv("DESKTOP_MODE", "false").lower() == "true"
FRONTEND_DIST = os.getenv("FRONTEND_DIST", "./frontend")

if DESKTOP_MODE and os.path.isdir(FRONTEND_DIST):
    # 挂载静态资源目录(JS/CSS/图片)
    app.mount("/assets", StaticFiles(directory=os.path.join(FRONTEND_DIST, "assets")), name="assets")

    @app.get("/")
    async def desktop_index():
        return FileResponse(os.path.join(FRONTEND_DIST, "index.html"))

    # SPA history 模式回退:除 /api 外的路径都返回 index.html
    @app.get("/{full_path:path}")
    async def desktop_spa_fallback(full_path: str):
        if full_path.startswith("api/"):
            return JSONResponse({"status": "error", "message": "Not found"}, status_code=404)
        candidate = os.path.join(FRONTEND_DIST, full_path)
        if os.path.isfile(candidate):
            return FileResponse(candidate)
        return FileResponse(os.path.join(FRONTEND_DIST, "index.html"))
```

> 这段逻辑只在 `DESKTOP_MODE=true` 时生效,开发/Docker 不受影响。`routes/__init__.py` 和 API 路由要在此代码**之前**注册,否则 catch-all 会吞掉 `/api`。

### 3.2 后端使用资源相对路径(Pydantic settings 路径调整)

PyInstaller 打包后,工作目录(cwd)和 exe 所在目录可能不同。需要让 `font_assets_dir`、`temp/`、`logs/` 等路径基于 **exe 所在目录**而非 cwd。

新增一个工具函数解析「应用根目录」:

```python
# backend/config.py 顶部补充
import sys
import os

def get_app_root() -> str:
    """返回应用根目录。
    - PyInstaller 打包后:exe 所在目录
    - 开发模式:backend/ 目录
    """
    if getattr(sys, "frozen", False):
        # PyInstaller:sys.executable 是 exe 路径
        return os.path.dirname(sys.executable)
    return os.path.dirname(os.path.abspath(__file__))


APP_ROOT = get_app_root()
```

然后 `Settings` 里的路径默认值改为基于 `APP_ROOT`:

```python
# backend/config.py
@dataclass(frozen=True)
class Settings:
    # ... 其他不变 ...

    # 应用根目录(exe 所在目录或 backend/)
    app_root: str = APP_ROOT

    # 字体资源路径(优先环境变量,否则用 app_root 下的 font_assets)
    font_assets_dir: str = os.getenv("FONT_ASSETS_DIR") or os.path.join(APP_ROOT, "font_assets")
    font_assets_bundled_dir: str = os.getenv("FONT_ASSETS_BUNDLED_DIR") or os.path.join(APP_ROOT, "font_assets")

    # 日志/临时目录(桌面模式写到 app_root 下的 runtime/,避免权限问题)
    log_dir: str = os.getenv("LOG_DIR") or os.path.join(APP_ROOT, "runtime", "logs")
    temp_dir: str = os.getenv("TEMP_DIR") or os.path.join(APP_ROOT, "runtime", "temp")
```

**注意**:现有代码里 `safe_remove_*`、`generate_pdf`、`textfileprocess` 等用了大量硬编码相对路径(`"./temp"`、`"./textfileprocess"`、`"logs/app.log"`)。桌面打包前需要把这些相对路径**全部改为读 `settings.temp_dir` / `settings.log_dir`**,否则 PyInstaller 运行时 cwd 可能是任意位置(如 `C:\Windows\System32`),会导致写文件失败。

> ⚠️ 这是工作量最大的一项改造,对应 `01-问题分析.md` 的「2.7 临时文件清理过度复杂」的根治。改造完成后不仅利于打包,也能修掉现有相对路径缺陷。

### 3.3 Pandoc 离线可用

当前 `app.py` 在启动时会尝试 `pypandoc.download_pandoc()`(联网下载)。桌面模式必须离线。两种做法:

**做法 A(🟢 推荐)**:用 `pypandoc.download_pandoc(targetfolder=...)` 在**打包阶段**就把 pandoc 下到 `backend/pandoc/`,然后 PyInstaller `--add-data` 带进去,运行时设环境变量 `PYPANDOC_PANDOC` 指向它。

```python
# backend/config.py
# 桌面模式:pandoc 放在 app_root/pandoc/pandoc.exe
pandoc_path: str = os.path.join(APP_ROOT, "pandoc", "pandoc.exe")
if getattr(sys, "frozen", False) and os.path.isfile(pandoc_path):
    os.environ["PYPANDOC_PANDOC"] = pandoc_path
```

并把 `app.py` 顶层的 `pypandoc.download_pandoc()` 改为「**只在 pandoc 真的不存在且非桌面模式时**才下载」:

```python
# 改造 app.py 里的 pandoc 初始化
import pypandoc
def ensure_pandoc():
    try:
        pypandoc.get_pandoc_version()
    except OSError:
        if os.getenv("DESKTOP_MODE", "false").lower() == "true":
            # 桌面模式绝不下网,缺了就报错
            logger.error("桌面模式缺少 pandoc,请检查打包")
            raise
        logger.info("Pandoc not found. Downloading...")
        pypandoc.download_pandoc()
```

**做法 B(🟡 简单但稍重)**:直接把项目里已有的 `backend/pandoc-3.10-windows-x86_64.msi` 用 lessmsi 解压出 `pandoc.exe`,塞进打包目录。

---

## 四、打包配置(PyInstaller)

打包分两个产物:**backend.exe**(后端服务)和 **launcher.exe**(启动器)。

### 4.1 目录结构

在仓库新增 `packaging/` 目录:

```
packaging/
├── backend.spec              # 后端 PyInstaller 配置
├── launcher.spec             # 启动器 PyInstaller 配置
├── launcher.py               # 启动器源码
├── build.bat                 # Windows 一键构建脚本
├── icon.ico                  # 应用图标
├── README.md                 # 打包说明
└── tests/
    └── smoke_test.py         # 打包后冒烟测试
```

### 4.2 后端 spec(`packaging/backend.spec`)

```python
# -*- mode: python ; coding: utf-8 -*-
# PyInstaller spec for handwriting backend
# 构建:pyinstaller packaging/backend.spec --noconfirm

import os
from PyInstaller.utils.hooks import collect_all, collect_data_files

block_cipher = None

# ── 收集隐式依赖(这些包 PyInstaller 静态分析发现不了)──
datas = []
binaries = []
hiddenimports = []

# uvicorn / fastapi 子模块
for pkg in ['uvicorn', 'fastapi', 'starlette', 'pydantic']:
    d, b, h = collect_all(pkg)
    datas += d; binaries += b; hiddenimports += h

# cv2 / numpy(sklearn 也依赖)
for pkg in ['cv2', 'numpy', 'sklearn', 'scipy', 'PIL', 'fitz']:
    d, b, h = collect_all(pkg)
    datas += d; binaries += b; hiddenimports += h

# handright / pypandoc
datas += collect_data_files('handright')
datas += collect_data_files('pypandoc')

# ── 额外资源 ──
REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(SPECPATH), '..'))

# 字体文件 → app_root/font_assets/
datas += [(os.path.join(REPO_ROOT, 'ttf_files'), 'font_assets')]

# 前端构建产物 → app_root/frontend/(需先 npm run build)
FE_DIST = os.path.join(REPO_ROOT, 'frontendVite', 'dist')
if os.path.isdir(FE_DIST):
    datas += [(FE_DIST, 'frontend')]
else:
    print("⚠️ 前端 dist 不存在,请先在 frontendVite/ 执行 npm run build")
    raise SystemExit(1)

# Pandoc 二进制 → app_root/pandoc/
PANDOC_DIR = os.path.join(REPO_ROOT, 'packaging', 'pandoc')
if os.path.isdir(PANDOC_DIR):
    datas += [(PANDOC_DIR, 'pandoc')]
else:
    print("⚠️ 缺少 pandoc/,请先运行 packaging/fetch_pandoc.py")
    raise SystemExit(1)

a = Analysis(
    ['../backend/app.py'],
    pathex=[os.path.join(REPO_ROOT, 'backend')],
    binaries=binaries,
    datas=datas,
    hiddenimports=hiddenimports + [
        'uvicorn.logging', 'uvicorn.loops', 'uvicorn.loops.auto',
        'uvicorn.protocols', 'uvicorn.protocols.http.auto',
        'uvicorn.protocols.websockets.auto',
        'identify', 'pdf', 'task_store', 'task_types', 'config',
        'services.cleanup', 'services.file_processing', 'services.fonts',
        'services.generation', 'services.image_utils', 'services.task_manager',
        'utils.logging_setup',
    ],
    hookspath=[],
    runtime_hooks=[],
    excludes=['pytest', 'tests', 'mysql.connector', 'pymysql'],  # 排除不需要的
    cipher=block_cipher,
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
    upx=True,                       # UPX 压缩,体积再降 ~30%
    console=True,                   # 保留控制台窗口便于调试;发布版改 False
    icon=os.path.join(SPECPATH, 'icon.ico'),
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='手写生成器',               # 输出目录名
)
```

### 4.3 启动器(`packaging/launcher.py`)

启动器职责:选端口、拉起后端、探活、开浏览器、托盘、退出。用纯标准库 + `webview` 可选(不引第三方)。

```python
# packaging/launcher.py
"""
手写生成器启动器。
- 启动同目录下的 backend.exe
- 等待健康检查通过
- 打开默认浏览器
- 系统托盘图标(右键退出)
"""
import os
import sys
import time
import socket
import subprocess
import threading
import urllib.request
import webbrowser
from pathlib import Path

# 托盘图标用 pystray(需打包进去)
import pystray
from PIL import Image as PILImage

APP_ROOT = Path(sys.executable).parent if getattr(sys, "frozen", False) else Path(__file__).parent
BACKEND_EXE = APP_ROOT / "backend.exe"
LOG_FILE = APP_ROOT / "runtime" / "logs" / "launcher.log"
START_PORT = 5005
END_PORT = 5020  # 端口冲突时顺延的上限


def log(msg: str):
    LOG_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] {msg}\n")


def find_free_port() -> int:
    """从 START_PORT 开始找可用端口。"""
    for port in range(START_PORT, END_PORT + 1):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            try:
                s.bind(("127.0.0.1", port))
                return port
            except OSError:
                continue
    raise RuntimeError(f"端口 {START_PORT}-{END_PORT} 都被占用,无法启动")


def wait_for_health(port: int, timeout: float = 30) -> bool:
    """轮询 /api/fonts_info 直到 200 或超时。"""
    url = f"http://127.0.0.1:{port}/api/fonts_info"
    deadline = time.time() + timeout
    while time.time() < deadline:
        try:
            with urllib.request.urlopen(url, timeout=2) as r:
                if r.status == 200:
                    return True
        except Exception:
            time.sleep(0.5)
    return False


def main():
    log("启动器启动")
    port = find_free_port()
    log(f"使用端口 {port}")

    env = os.environ.copy()
    env["DESKTOP_MODE"] = "true"
    env["LOG_DIR"] = str(APP_ROOT / "runtime" / "logs")
    env["TEMP_DIR"] = str(APP_ROOT / "runtime" / "temp")
    env["SENTRY_DSN"] = ""  # 桌面版关闭 Sentry 上报(避免泄漏 + 离线)

    # 拉起后端(无窗口)
    creationflags = subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0
    proc = subprocess.Popen(
        [str(BACKEND_EXE)],
        cwd=str(APP_ROOT),
        env=env,
        stdout=open(APP_ROOT / "runtime" / "logs" / "backend.stdout.log", "w", encoding="utf-8"),
        stderr=subprocess.STDOUT,
        creationflags=creationflags,
    )
    log(f"backend.exe PID={proc.pid}")

    # 探活
    if not wait_for_health(port):
        log("后端启动失败")
        # 这里应弹原生消息框提示用户去看日志
        try:
            import ctypes
            ctypes.windll.user32.MessageBoxW(
                0, "后端启动失败,请查看 runtime/logs/backend.stdout.log", "手写生成器", 0x10
            )
        except Exception:
            pass
        return

    url = f"http://127.0.0.1:{port}"
    log(f"打开浏览器 {url}")
    webbrowser.open(url)

    # 系统托盘
    icon_image = PILImage.new("RGB", (64, 64), "green")  # 占位图,换成 icon.ico
    tray = pystray.Icon(
        "handwriting",
        icon_image,
        "手写生成器(运行中)",
        menu=pystray.Menu(
            pystray.MenuItem("打开网页", lambda: webbrowser.open(url)),
            pystray.MenuItem("退出", lambda: exit_app(proc, tray)),
        ),
    )

    # 后台监控后端进程,崩了提示
    def watch():
        proc.wait()
        log(f"backend 退出,code={proc.returncode}")
        tray.stop()

    threading.Thread(target=watch, daemon=True).start()
    tray.run()


def exit_app(proc, tray):
    proc.terminate()
    try:
        proc.wait(timeout=5)
    except subprocess.TimeoutExpired:
        proc.kill()
    tray.stop()


if __name__ == "__main__":
    main()
```

启动器 spec(`packaging/launcher.spec`)类似,`console=False`(无窗口),`hiddenimports=['pystray', 'PIL']`。

---

## 五、构建流程(一键脚本)

### 5.1 准备 Pandoc(一次性)

新建 `packaging/fetch_pandoc.py`,把仓库里已有的 `backend/pandoc-3.10-windows-x86_64.msi` 解压出 `pandoc.exe`:

```python
# packaging/fetch_pandoc.py
"""
从仓库自带的 pandoc msi 解压出 pandoc.exe,放到 packaging/pandoc/。
依赖:pip install lessmsi (或 lesscli)
"""
import os
import subprocess
import shutil
from pathlib import Path

MSI = Path("../backend/pandoc-3.10-windows-x86_64.msi")
OUT = Path("pandoc")

def main():
    OUT.mkdir(exist_ok=True)
    tmp = Path("_msi_extract")
    subprocess.run(["lessmsi", "x", str(MSI.resolve()), str(tmp.resolve())], check=True)
    # lessmsi 解压后在 tmp/<msi名>/SourceDir/... 找 pandoc.exe
    for p in tmp.rglob("pandoc.exe"):
        shutil.copy2(p, OUT / "pandoc.exe")
        print(f"已复制 {p} → {OUT / 'pandoc.exe'}")
        break
    shutil.rmtree(tmp, ignore_errors=True)

if __name__ == "__main__":
    main()
```

### 5.2 构建脚本(`packaging/build.bat`)

```bat
@echo off
chcp 65001 >nul
setlocal

echo ========================================
echo  手写生成器 - Windows 桌面打包
echo ========================================

set ROOT=%~dp0..
cd /d %ROOT%

REM ── 1. 前端构建 ──
echo [1/6] 构建前端...
cd frontendVite
call npm ci || goto :error
call npm run build || goto :error
cd /d %ROOT%

REM ── 2. 后端依赖(打包用独立 venv)──
echo [2/6] 准备后端打包环境...
python -m venv packaging\build_venv
call packaging\build_venv\Scripts\activate.bat
pip install --upgrade pip
pip install -r backend\requirements.txt
pip install pyinstaller pystray lessmsi
cd /d %ROOT%

REM ── 3. 准备 Pandoc ──
echo [3/6] 解压 Pandoc...
if not exist packaging\pandoc\pandoc.exe (
    cd packaging
    python fetch_pandoc.py || goto :error
    cd /d %ROOT%
)

REM ── 4. 清理旧产物 ──
echo [4/6] 清理旧构建...
rmdir /s /q packaging\build 2>nul
rmdir /s /q packaging\dist 2>nul

REM ── 5. PyInstaller 打包后端 ──
echo [5/6] 打包后端 backend.exe...
cd packaging
pyinstaller backend.spec --noconfirm --distpath dist --workpath build || goto :error

REM ── 6. 打包启动器 ──
echo [6/6] 打包启动器 launcher.exe...
pyinstaller launcher.spec --noconfirm --distpath dist --workpath build || goto :error

REM ── 收尾:把 launcher.exe 放进后端目录,重命名 ──
move /Y dist\launcher.exe "dist\手写生成器\手写生成器.exe" || goto :error

echo.
echo ========================================
echo  打包成功!
echo  产物:packaging\dist\手写生成器\
echo  双击「手写生成器.exe」即可使用
echo ========================================
goto :eof

:error
echo.
echo 打包失败,请检查上方日志
exit /b 1
```

### 5.3 压缩分发(可选)

```bat
REM packaging/zip_release.bat
@echo off
cd /d %~dp0
set VER=%1
if "%VER%"=="" set VER=dev
powershell Compress-Archive -Path "dist\手写生成器\*" -DestinationPath "dist\手写生成器-v%VER%.zip" -Force
echo 生成:dist\手写生成器-v%VER%.zip
```

---

## 六、关键工程问题与对策

| 问题 | 对策 |
|------|------|
| **相对路径失效**(cwd 问题) | 所有 `./temp`、`logs/` 改读 `settings.temp_dir`/`settings.log_dir`(见 3.2)。这是打包前**必须完成**的改造。 |
| **PyInstaller 漏依赖** | 用 `collect_all` 收集 uvicorn/fastapi/cv2/numpy;`hiddenimports` 显式声明 services/routes/utils 各模块。 |
| **Pandoc 运行时下载** | 离线内嵌(见 3.3),桌面模式禁用下载。 |
| **端口冲突** | 启动器从 5005 顺延到 5020,找到可用端口再用。 |
| **用户关闭后端进程残留** | 启动器托盘「退出」时 `terminate` + 5 秒超时 `kill`;backend 退出时 `lifespan` 清理 temp。 |
| **首次启动慢** | onedir 模式不压缩,启动 ~2s(对比 onefile 首次 5-10s)。 |
| **Sentry 泄漏/离线** | 桌面模式 `SENTRY_DSN=""`,不上报。 |
| **Windows Defender 误报** | 用 UPX 压缩可能触发误报,权衡后可关闭 UPX(spec 里 `upx=False`);或做代码签名(见第八节)。 |
| **字体路径** | spec 里把 `ttf_files` 作为 `font_assets` 打进去,`config.py` 的 `font_assets_dir` 默认指向 `APP_ROOT/font_assets`。 |
| **前端 API baseURL** | 桌面模式前后端同源(都是 5005),前端 `axios` 的 `baseURL` 应为空字符串。检查 `frontendVite/src/utils/http.js`,确认 `VITE_API_BASE_URL` 在桌面构建时为空。 |

---

## 七、分阶段执行计划

> 工时估算:单人全职约 **4-6 人日**。

### 阶段 A:后端路径改造(1.5-2 人日,**前置必需**)

对应 `02-修改方案.md` 的 2.7 子项,是打包的硬前提。

- [ ] `config.py` 增加 `APP_ROOT` / `log_dir` / `temp_dir`
- [ ] 全仓库把 `./temp`、`logs/`、`./textfileprocess`、`imagefileprocess`、`./output` 改为读 `settings`
- [ ] `safe_remove_*`、`generate_pdf`、`/api/textfileprocess`、`/api/imagefileprocess` 路径统一
- [ ] 验证:Docker 模式 + `python app.py` 模式都仍正常(回归)
- [ ] 验证:`cd C:\ && python E:\...\backend\app.py` 也能正常工作(模拟 cwd 不在 backend)

### 阶段 B:桌面模式适配(1 人日)

- [ ] `app.py` 加 `DESKTOP_MODE` 静态文件挂载(3.1)
- [ ] Pandoc 离线化(3.3)
- [ ] 前端 `http.js` 确认同源 baseURL
- [ ] 验证:`DESKTOP_MODE=true python app.py` + 把 `frontendVite/dist` 拷到 `./frontend`,浏览器访问根路径能打开页面

### 阶段 C:打包流水线(1.5-2 人日)

- [ ] 写 `packaging/backend.spec`、`launcher.spec`、`launcher.py`
- [ ] 写 `build.bat`、`fetch_pandoc.py`、`zip_release.bat`
- [ ] 准备 `icon.ico`
- [ ] 首次打包,逐个解决依赖缺失/import 报错
- [ ] 验证:双击 exe → 浏览器打开 → 全功能跑通

### 阶段 D:打磨与验证(1 人日)

- [ ] 托盘图标、退出逻辑、崩溃提示
- [ ] 体积优化(见第九节)
- [ ] 冒烟测试清单(见第十节)
- [ ] 写 `packaging/README.md` 用户文档

---

## 八、代码签名(可选,发布时做)

未签名的 exe 会触发 Windows SmartScreen 警告(用户体验差)。商业发布建议签名:

- 购买代码签名证书(EV 证书 ~$300/年,普通 ~$100/年)。
- 用 `signtool.exe`(Windows SDK 自带)签名:
  ```bat
  signtool sign /tr http://timestamp.digicert.com /td sha256 /fd sha256 /a /f cert.pfx /p <password> "dist\手写生成器\手写生成器.exe"
  signtool sign ... "dist\手写生成器\backend.exe"
  ```
- EV 证书可立即消除 SmartScreen 警告;普通证书需要积累声誉。

无预算时可跳过,但要在文档里提示用户「SmartScreen 点仍要运行」。

---

## 九、体积优化清单

打包完成后如果体积超标,按顺序尝试:

| 优化 | 预估省 | 副作用 |
|------|--------|--------|
| UPX 压缩 DLL/exe(spec `upx=True`) | ~80MB | ⚠️ 可能被杀软误报 |
| 排除 `scipy` 的测试数据 `scipy/tests` | ~10MB | 无 |
| 排除 `sklearn` 的 `datasets` | ~20MB | 无(我们不跑内置数据集) |
| 排除 `matplotlib`(若被间接引入) | ~30MB | 无 |
| numpy 用 `numpy-headless`(无 MKL) | ~15MB | 部分 numpy 运算变慢,本项目不受影响 |
| opencv 用 `opencv-python-headless`(无 GUI) | ~10MB | 无(后端不弹窗) |
| 字体文件剔除非必需的大字体 | 视情况 | 字体选项减少 |
| 前端 dist 移除 sourcemap(已 `sourcemap:false`) | ~2MB | 无 |

在 spec 的 `excludes` 加:
```python
excludes=['pytest', 'tests', 'mysql.connector', 'pymysql',
          'matplotlib', 'tkinter', 'PyQt5', 'PySide6',
          'IPython', 'notebook', 'jupyter']
```

目标:从 ~370MB 压到 **~250MB(未压缩)/ ~120MB(zip)** 是现实的。

---

## 十、验证清单(打包后冒烟测试)

在**干净 Windows 机器**(没装 Python、没装 Node)上验证:

### 10.1 基础启动
- [ ] 双击 `手写生成器.exe`,2-5 秒内浏览器自动打开 `http://localhost:5005`
- [ ] 页面正常显示首页(前端加载 OK)
- [ ] 任务栏右下角出现托盘图标
- [ ] 右键托盘 → 「打开网页」能再次打开
- [ ] 右键托盘 → 「退出」,进程完全消失(任务管理器无残留 backend.exe)

### 10.2 核心功能(回归矩阵,对齐 `04-验证方案.md` 第三节)
- [ ] 字体列表加载(`/api/fonts_info` 返回非空)
- [ ] 默认参数生成图片(空白纸 + 黑字)
- [ ] 单线/方格/点阵/空白四种纸张
- [ ] 生成 PDF
- [ ] 预览功能
- [ ] docx 导入(验证 Pandoc 离线可用)
- [ ] PDF 导入
- [ ] txt 导入
- [ ] 图片边距识别(验证 opencv 可用)
- [ ] 上传自定义字体生成

### 10.3 异常路径
- [ ] 5005 端口被占(先手动起一个)→ 启动器自动用 5006
- [ ] 删除 `font_assets` 目录后启动 → 友好报错,不崩溃
- [ ] 删除 `pandoc/pandoc.exe` 后启动 → docx 导入失败但有错误提示
- [ ] 杀掉 backend.exe → 启动器检测到并退出(或提示)

### 10.4 性能
- [ ] 冷启动(首次双击)到浏览器打开 < 10 秒
- [ ] 热启动(再次双击)< 5 秒
- [ ] 单页生成 < 10 秒
- [ ] 连续生成 10 次,`runtime/temp/` 不无限增长

### 10.5 体积确认
- [ ] 未压缩文件夹 < 400MB(优化后 < 280MB)
- [ ] zip 分发包 < 180MB(优化后 < 130MB)

---

## 十一、与既有文档的关系

本方案是新增维度——「桌面化分发」,与既有优化文档的关系:

| 关联 | 说明 |
|------|------|
| `02-修改方案.md` 2.7 | 本方案的**阶段 A**(路径改造)就是 2.7 的根治版,完成后同时解决打包和现有相对路径缺陷 |
| `02-修改方案.md` 2.1 | 敏感信息已移到环境变量(已完成),桌面模式 `SENTRY_DSN=""` 复用同一机制 |
| `04-验证方案.md` 第三节 | 本方案第十节的回归矩阵与之对齐,桌面版只多不少 |

---

## 十二、风险与决策点

| 风险/决策 | 说明 |
|-----------|------|
| **PyInstaller 对 opencv/sklearn 兼容性** | cv2 和 sklearn 有时有隐式 DLL 加载问题,首次打包大概率要调 `hiddenimports`。预留半天调试。 |
| **杀软误报** | UPX 压缩 + 无签名 → Defender 可能隔离。权衡:关 UPX(体积大)或买签名(花钱)。 |
| **字体许可证** | `ttf_files/` 里的字体如果打包进 exe 分发,需确认字体的许可证允许再分发(部分商业字体禁止)。 |
| **Pandoc 许可证** | Pandoc 是 GPL,内嵌进闭源分发需注意 GPL 传染性(本项目 MIT,作为独立可执行文件分发通常 OK,但建议法务确认)。 |
| **多用户同机** | 装在 Program Files 需要管理员权限,`runtime/` 写不进去;建议装在用户目录或让安装到任意位置。当前「文件夹版」天然规避(用户解压哪都行)。 |
| **是否需要自动更新** | 当前方案不含自动更新。需要的话加 `pyupdater` 或自检版本号提示下载。 |

---

*下一步:确认阶段 A(路径改造)是否要先做。这是打包的硬前提,也是 `02-修改方案.md` 2.7 的根治项,做了能一举两得。*
