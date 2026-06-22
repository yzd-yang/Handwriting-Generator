"""
文件安全删除与临时目录清理工具。

从 app.py 中拆分出来（P1 2.4 重构），使 app.py 变薄，
工具函数可独立单测。
"""

import gc
import os
import shutil
import time
from pathlib import Path

from config import settings
from utils.logging_setup import get_logger

logger = get_logger(__name__)


def safe_remove_directory(directory_path, max_retries=5):
    """删除目录，失败仅记日志。残留由定时清理兜底。

    根因已修复（PIL 句柄正确释放），无需复杂重试。
    """
    if not os.path.exists(directory_path):
        return True
    try:
        shutil.rmtree(directory_path, ignore_errors=True)
        gc.collect()
        logger.info("Successfully deleted temp directory: %s", directory_path)
        return True
    except Exception as e:
        logger.warning("safe_remove_directory failed %s: %s", directory_path, e)
        return False


def safe_remove_single_file(file_path, max_retries=3):
    """安全删除单个文件，去掉 os.chmod(0o777) 安全反模式。"""
    try:
        Path(file_path).unlink(missing_ok=True)
        return True
    except Exception as e:
        logger.warning("Failed to delete file %s: %s", file_path, e)
        return False


def safe_remove_file(file_path, max_retries=3):
    """安全删除文件，带重试机制"""
    result = safe_remove_single_file(file_path, max_retries)
    if result:
        logger.info("Successfully deleted file: %s", file_path)
    else:
        logger.error("Failed to delete file after %s attempts: %s", max_retries, file_path)
    return result


def safe_save_and_close_image(image, image_path):
    """安全保存并关闭图片，确保文件句柄被释放。"""
    try:
        image.save(image_path)
        # 释放 PIL 句柄，避免 Windows 下文件锁定
        if hasattr(image, "close"):
            image.close()
        gc.collect()
        return True
    except Exception as e:
        logger.error("Failed to save image %s: %s", image_path, e)
        return False


def cleanup_marked_directories():
    """清理项目内标记为稍后清理的目录"""
    project_temp_base = settings.temp_dir

    # 确保项目临时目录存在
    os.makedirs(project_temp_base, exist_ok=True)

    try:
        for item in os.listdir(project_temp_base):
            item_path = os.path.join(project_temp_base, item)
            if os.path.isdir(item_path) and item.startswith("tmp"):
                cleanup_marker = os.path.join(item_path, ".cleanup_later")
                if os.path.exists(cleanup_marker):
                    try:
                        # 检查标记时间，如果超过1小时则尝试清理
                        with open(cleanup_marker, "r") as f:
                            content = f.read()
                            if "Failed to delete at" in content:
                                timestamp = float(content.split("Failed to delete at ")[1])
                                if time.time() - timestamp > 3600:  # 1小时后
                                    logger.info(
                                        "Attempting to cleanup marked directory: %s",
                                        item_path,
                                    )
                                    if safe_remove_directory(item_path, max_retries=2):
                                        logger.info(
                                            "Successfully cleaned up marked directory: %s",
                                            item_path,
                                        )
                    except Exception as e:
                        logger.warning("Failed to cleanup marked directory %s: %s", item_path, e)
    except Exception as e:
        logger.warning("Error during cleanup of marked directories: %s", e)
