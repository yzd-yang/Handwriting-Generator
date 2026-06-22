"""
手写生成器启动器（Launcher）。

职责：
1. 选择可用端口（5005 起，冲突则顺延）
2. 后台拉起 backend.exe
3. 等待健康检查通过（轮询 /api/fonts_info）
4. 自动打开默认浏览器
5. 系统托盘图标（右键退出）
6. 监控 backend 进程，崩了弹提示

用法：
- 开发模式：python launcher.py
- 打包后：双击 手写生成器.exe
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

# 条件导入托盘图标（打包时会一并打进去）
try:
    import pystray
    from PIL import Image as PILImage

    HAS_TRAY = True
except ImportError:
    HAS_TRAY = False

# ── 配置 ──
APP_ROOT = Path(sys.executable).parent if getattr(sys, "frozen", False) else Path(__file__).parent
BACKEND_EXE = APP_ROOT / "backend.exe"
LOG_DIR = APP_ROOT / "runtime" / "logs"
START_PORT = 5005
END_PORT = 5020  # 端口冲突时顺延上限


def log(msg: str):
    """写日志到 runtime/logs/launcher.log"""
    try:
        LOG_DIR.mkdir(parents=True, exist_ok=True)
        with open(LOG_DIR / "launcher.log", "a", encoding="utf-8") as f:
            f.write(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] {msg}\n")
    except Exception:
        pass


def find_free_port() -> int:
    """从 START_PORT 开始找可用端口。"""
    for port in range(START_PORT, END_PORT + 1):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            try:
                s.bind(("127.0.0.1", port))
                return port
            except OSError:
                continue
    raise RuntimeError(f"端口 {START_PORT}-{END_PORT} 都被占用，无法启动")


def wait_for_health(port: int, timeout: float = 60) -> bool:
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


def show_error_box(title: str, message: str):
    """弹窗提示错误（Windows 原生对话框）。"""
    try:
        import ctypes

        ctypes.windll.user32.MessageBoxW(0, message, title, 0x10)  # MB_ICONERROR=0x10
    except Exception:
        print(f"ERROR: {title}: {message}")


def main():
    log("=" * 60)
    log("启动器启动")
    log(f"APP_ROOT: {APP_ROOT}")
    log(f"BACKEND_EXE exists: {BACKEND_EXE.is_file()}")

    if not BACKEND_EXE.is_file():
        msg = f"未找到 backend.exe，请确保它在以下路径：\n{BACKEND_EXE}"
        log(msg)
        show_error_box("手写生成器 - 启动失败", msg)
        return

    # 找可用端口
    try:
        port = find_free_port()
    except RuntimeError as e:
        msg = str(e)
        log(msg)
        show_error_box("手写生成器 - 端口冲突", msg)
        return

    log(f"使用端口：{port}")
    url = f"http://127.0.0.1:{port}"

    # 准备环境变量
    env = os.environ.copy()
    env["DESKTOP_MODE"] = "true"
    env["LOG_DIR"] = str(LOG_DIR)
    env["TEMP_DIR"] = str(APP_ROOT / "runtime" / "temp")
    env["SENTRY_DSN"] = ""  # 桌面版关闭 Sentry 上报

    # 拉起后端（无窗口）
    backend_log = LOG_DIR / "backend.stdout.log"
    backend_log.parent.mkdir(parents=True, exist_ok=True)

    creationflags = 0
    if os.name == "nt":
        # Windows：CREATE_NO_WINDOW 避免弹出黑窗口
        creationflags = getattr(subprocess, "CREATE_NO_WINDOW", 0x08000000)

    log(f"启动 backend.exe，日志：{backend_log}")
    try:
        proc = subprocess.Popen(
            [str(BACKEND_EXE)],
            cwd=str(APP_ROOT),
            env=env,
            stdout=open(backend_log, "w", encoding="utf-8", errors="ignore"),
            stderr=subprocess.STDOUT,
            creationflags=creationflags,
        )
    except Exception as e:
        msg = f"启动 backend.exe 失败：{e}"
        log(msg)
        show_error_box("手写生成器 - 启动失败", msg)
        return

    log(f"backend.exe PID={proc.pid}")

    # 探活
    log("等待后端就绪...")
    if not wait_for_health(port):
        msg = f"后端启动失败（{port} 端口探活超时）\n请查看日志：{backend_log}"
        log(msg)
        show_error_box("手写生成器 - 启动失败", msg)
        try:
            proc.terminate()
        except Exception:
            pass
        return

    log("后端就绪，打开浏览器")
    webbrowser.open(url)

    # ── 系统托盘 ──
    if HAS_TRAY:
        log("启动系统托盘")
        try:
            # 创建简单图标（绿色方块）
            icon_img = PILImage.new("RGBA", (64, 64), (76, 175, 80, 255))

            def exit_app(icon, item):
                log("用户通过托盘退出")
                proc.terminate()
                try:
                    proc.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    proc.kill()
                icon.stop()

            def open_browser(icon, item):
                webbrowser.open(url)

            tray = pystray.Icon(
                "handwriting_launcher",
                icon_img,
                "手写生成器（运行中）",
                menu=pystray.Menu(
                    pystray.MenuItem("打开网页", open_browser),
                    pystray.MenuItem("退出", exit_app),
                ),
            )

            # 后台监控后端进程
            def watch_backend():
                proc.wait()
                log(f"backend.exe 已退出，code={proc.returncode}")
                tray.stop()

            threading.Thread(target=watch_backend, daemon=True).start()

            tray.run()
        except Exception as e:
            log(f"托盘图标启动失败：{e}")
            # 托盘失败不阻碍主流程，等待 backend 进程
            proc.wait()
    else:
        # 无托盘支持，直接等待进程
        log("无托盘支持，等待 backend 进程...")
        proc.wait()

    log("启动器退出")


if __name__ == "__main__":
    main()
