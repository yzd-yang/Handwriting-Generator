"""
utils 包入口。

用法：
    from utils import get_logger
    logger = get_logger(__name__)
"""

from utils.logging_setup import setup_logging, get_logger

__all__ = ["setup_logging", "get_logger"]
