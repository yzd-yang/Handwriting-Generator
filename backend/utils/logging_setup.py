"""
日志配置工具。

提供 setup_logging()，集中配置 root logger：
- StreamHandler（控制台）+ RotatingFileHandler（轮转文件，10MB × 5 份）
- 日志级别由 config.settings.log_level 控制（默认 INFO）
- 格式统一为 %(asctime)s - %(name)s - %(levelname)s - %(message)s
- 全项目禁用第三方库的冗余 INFO 日志（httpcore、httpx、urllib3 等）
"""

import logging
import os
from logging.handlers import RotatingFileHandler

from config import settings


def setup_logging(level: str = "INFO") -> logging.Logger:
    """
    配置 root logger，返回本项目使用的 logger 实例。

    Args:
        level: 日志级别字符串，如 "INFO"、"DEBUG"。默认从 settings.log_level 取。

    Returns:
        logging.Logger: 以当前模块名命名的 logger。
    """
    log_level = getattr(logging, level.upper(), logging.INFO)
    fmt = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")

    root = logging.getLogger()
    # 避免重复添加 handler（reload 或测试时）
    if root.handlers:
        root.handlers.clear()

    root.setLevel(log_level)

    # 控制台 handler
    ch = logging.StreamHandler()
    ch.setLevel(log_level)
    ch.setFormatter(fmt)
    root.addHandler(ch)

    # 轮转文件 handler（10MB，保留最近 5 份）
    # 使用 settings.log_dir 确保路径基于 app_root，而非 cwd
    os.makedirs(settings.log_dir, exist_ok=True)
    fh = RotatingFileHandler(
        os.path.join(settings.log_dir, "app.log"),
        maxBytes=10 * 1024 * 1024,
        backupCount=5,
        encoding="utf-8",
    )
    fh.setLevel(log_level)
    fh.setFormatter(fmt)
    root.addHandler(fh)

    # 禁用第三方库的无用 INFO 日志
    for _noisy in ("httpcore", "httpx", "urllib3", "pypandoc"):
        logging.getLogger(_noisy).setLevel(logging.WARNING)

    logger = logging.getLogger(__name__)
    logger.info(
        "logging configured: level=%s, log_file=%s (10MB x 5)",
        logging.getLevelName(log_level),
        os.path.join(settings.log_dir, "app.log"),
    )
    return logger


def get_logger(name: str) -> logging.Logger:
    """
    获取指定名称的 logger，自动继承 root 配置。

    Usage:
        from utils.logging_setup import get_logger
        logger = get_logger(__name__)
    """
    return logging.getLogger(name)
