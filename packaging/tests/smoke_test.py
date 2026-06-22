"""
打包后冒烟测试。

在干净 Windows 机器上运行，验证桌面版基本功能。

使用方法：
    python packaging/tests/smoke_test.py
"""

import os
import sys
import time
import subprocess
import urllib.request
import shutil
from pathlib import Path

APP_ROOT = Path(__file__).resolve().parent.parent.parent / "packaging" / "dist" / "手写生成器"


def log(msg):
    print(f"[TEST] {msg}")


def test_1_backend_exe_exists():
    """测试 1：backend.exe 存在"""
    exe = APP_ROOT / "backend.exe"
    if exe.is_file():
        log("✓ backend.exe 存在")
        return True
    else:
        log("✗ backend.exe 不存在")
        return False


def test_2_launcher_exe_exists():
    """测试 2：手写生成器.exe 存在"""
    exe = APP_ROOT / "手写生成器.exe"
    if exe.is_file():
        log("✓ 手写生成器.exe 存在")
        return True
    else:
        log("✗ 手写生成器.exe 不存在")
        return False


def test_3_font_assets_exists():
    """测试 3：font_assets 目录存在且有字体文件"""
    d = APP_ROOT / "font_assets"
    if d.is_dir() and list(d.glob("*.ttf")):
        log(f"✓ font_assets 存在，有 {len(list(d.glob('*.ttf')))} 个字体文件")
        return True
    else:
        log("✗ font_assets 不存在或为空")
        return False


def test_4_frontend_exists():
    """测试 4：frontend 目录存在"""
    d = APP_ROOT / "frontend"
    if d.is_dir() and (d / "index.html").is_file():
        log("✓ frontend 目录存在")
        return True
    else:
        log("✗ frontend 目录不存在")
        return False


def test_5_backend_starts():
    """测试 5：后端能启动"""
    log("  启动后端（10 秒超时）...")
    env = os.environ.copy()
    env["DESKTOP_MODE"] = "true"
    env["LOG_DIR"] = str(APP_ROOT / "runtime" / "logs")
    env["TEMP_DIR"] = str(APP_ROOT / "runtime" / "temp")

    try:
        proc = subprocess.Popen(
            [str(APP_ROOT / "backend.exe")],
            cwd=str(APP_ROOT),
            env=env,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0x08000000),
        )
    except Exception as e:
        log(f"✗ 启动后端失败: {e}")
        return False

    # 等待就绪
    port = 5005
    url = f"http://127.0.0.1:{port}/api/fonts_info"
    deadline = time.time() + 10
    while time.time() < deadline:
        try:
            with urllib.request.urlopen(url, timeout=1) as r:
                if r.status == 200:
                    log("✓ 后端启动成功")
                    proc.terminate()
                    return True
        except Exception:
            time.sleep(0.5)

    log("✗ 后端启动超时")
    proc.terminate()
    return False


def main():
    log("=" * 60)
    log("手写生成器桌面版 - 冒烟测试")
    log("=" * 60)

    if not APP_ROOT.is_dir():
        log(f"❌ 未找到产物目录: {APP_ROOT}")
        log("   请先运行 packaging/build.bat")
        sys.exit(1)

    results = []
    results.append(("backend.exe 存在", test_1_backend_exe_exists()))
    results.append(("手写生成器.exe 存在", test_2_launcher_exe_exists()))
    results.append(("font_assets 存在", test_3_font_assets_exists()))
    results.append(("frontend 存在", test_4_frontend_exists()))
    results.append(("后端能启动", test_5_backend_starts()))

    log("=" * 60)
    log("测试结果：")
    for name, passed in results:
        status = "✓ 通过" if passed else "✗ 失败"
        log(f"  {name}: {status}")

    passed = sum(1 for _, r in results if r)
    total = len(results)
    log(f"\n总计: {passed}/{total} 通过")

    if passed == total:
        log("🎉 所有测试通过！")
        sys.exit(0)
    else:
        log("⚠️  有测试失败，请检查")
        sys.exit(1)


if __name__ == "__main__":
    main()
