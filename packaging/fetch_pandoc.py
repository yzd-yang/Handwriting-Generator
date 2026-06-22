"""
从 pypandoc 下载 Pandoc 到 packaging/pandoc/ 目录。

使用方法（在 backend venv 中运行）：
    ../backend/venv/Scripts/python.exe fetch_pandoc.py
"""

import os
import sys
import shutil
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
TARGET_DIR = Path(__file__).resolve().parent / "pandoc"


def main():
    TARGET_DIR.mkdir(exist_ok=True)

    print(f"目标目录: {TARGET_DIR}")

    # 方法：用 pypandoc 下载（最可靠）
    try:
        import pypandoc

        print("使用 pypandoc.download_pandoc() 下载...")
        pypandoc.download_pandoc(targetfolder=str(TARGET_DIR))

        # 检查是否下载成功
        pandoc_exe = TARGET_DIR / "pandoc.exe"
        if not pandoc_exe.is_file():
            # 可能下载到了子目录
            for p in TARGET_DIR.rglob("pandoc.exe"):
                shutil.copy2(p, pandoc_exe)
                print(f"已复制 {p} -> {pandoc_exe}")
                break

        if pandoc_exe.is_file():
            print(f"✓ Pandoc 下载成功: {pandoc_exe}")
        else:
            print("⚠️  Pandoc 下载完成但未找到 pandoc.exe")

    except ImportError:
        print("❌ pypandoc 未安装，请先在 backend venv 中安装")
        sys.exit(1)
    except Exception as e:
        print(f"❌ 下载失败: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
