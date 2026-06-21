"""
字体文件管理：字体列表获取、字体同步。

从 app.py 中拆分出来（P1 2.4 重构）。
"""

import os
import shutil

from config import settings
from utils.logging_setup import get_logger

logger = get_logger(__name__)


def sync_font_assets(source_dir, target_dir):
    """将打包内置字体同步到运行时字体目录。"""
    if os.path.abspath(source_dir) == os.path.abspath(target_dir):
        return
    if not os.path.isdir(source_dir) or not os.path.isdir(target_dir):
        return
    for filename in os.listdir(source_dir):
        if not filename.lower().endswith(".ttf"):
            continue
        source_path = os.path.join(source_dir, filename)
        target_path = os.path.join(target_dir, filename)
        if os.path.isfile(source_path) and not os.path.exists(target_path):
            shutil.copy2(source_path, target_path)


def get_font_file_names():
    """获取字体目录中所有 .ttf 文件名列表。"""
    font_assets_dir = settings.font_assets_dir
    if not os.path.isdir(font_assets_dir):
        return []
    return [
        f
        for f in os.listdir(font_assets_dir)
        if os.path.isfile(os.path.join(font_assets_dir, f)) and f.endswith(".ttf")
    ]


def get_font_path(font_name):
    """获取字体文件的完整路径。"""
    return os.path.join(settings.font_assets_dir, font_name)
