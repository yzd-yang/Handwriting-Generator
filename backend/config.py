"""
配置管理：从环境变量读取配置，提供默认值。
所有敏感信息（DSN、密钥）必须通过环境变量注入，不得硬编码。

路径策略：
- 开发模式：backend/ 为工作目录，相对路径基于 backend/
- PyInstaller 桌面模式：exe 所在目录为 APP_ROOT，所有路径基于此
- 环境变量优先：所有路径均可通过环境变量覆盖
"""

import os
import sys
from dataclasses import dataclass


def get_app_root() -> str:
    """返回应用根目录（exe 所在目录，用于可写运行时数据）。

    - PyInstaller 打包后：exe 所在目录（sys.executable 的 dirname）
    - 开发模式：backend/ 目录（本文件所在目录）
    """
    if getattr(sys, "frozen", False):
        return os.path.dirname(sys.executable)
    return os.path.dirname(os.path.abspath(__file__))


def get_data_root() -> str:
    """返回数据资源根目录（只读的打包资源）。

    - PyInstaller 打包后：sys._MEIPASS（_internal 目录）
    - 开发模式：同 APP_ROOT（backend/ 目录）
    """
    if getattr(sys, "frozen", False):
        # PyInstaller 把所有 datas 解压到 _MEIPASS
        return sys._MEIPASS
    return get_app_root()


APP_ROOT = get_app_root()
DATA_ROOT = get_data_root()


@dataclass(frozen=True)
class Settings:
    # Sentry 错误监控
    sentry_dsn: str = os.getenv("SENTRY_DSN", "")
    sentry_traces_sample_rate: float = float(os.getenv("SENTRY_TRACES_SAMPLE_RATE", "0.1"))

    # 安全密钥（当前未启用，留空）
    secret_key: str = os.getenv("SECRET_KEY", "")

    # 应用根目录（exe 所在目录或 backend/）
    app_root: str = APP_ROOT

    # 字体资源路径（从 DATA_ROOT 读取，优先环境变量）
    font_assets_dir: str = os.getenv("FONT_ASSETS_DIR") or os.path.join(DATA_ROOT, "font_assets")
    font_assets_bundled_dir: str = os.getenv("FONT_ASSETS_BUNDLED_DIR") or os.path.join(DATA_ROOT, "font_assets")

    # 日志/临时目录（桌面模式写到 app_root 下的 runtime/，避免权限问题）
    log_dir: str = os.getenv("LOG_DIR") or os.path.join(APP_ROOT, "runtime", "logs")
    temp_dir: str = os.getenv("TEMP_DIR") or os.path.join(APP_ROOT, "runtime", "temp")
    # 上传文件临时目录（textfileprocess/imagefileprocess 等）
    upload_dir: str = os.getenv("UPLOAD_DIR") or os.path.join(APP_ROOT, "runtime", "uploads")
    # 桌面模式前端 dist 目录（DESKTOP_MODE=true 时挂载，从 DATA_ROOT 读取）
    frontend_dist: str = os.getenv("FRONTEND_DIST") or os.path.join(DATA_ROOT, "frontend")

    # 用户认证（已禁用）
    enable_user_auth: str = os.getenv("ENABLE_USER_AUTH", "false")

    # MySQL（已禁用）
    mysql_host: str = os.getenv("MYSQL_HOST", "db")

    # 日志级别
    log_level: str = os.getenv("LOG_LEVEL", "INFO")

    # 上传大小限制（MB）
    max_upload_mb: int = int(os.getenv("MAX_UPLOAD_MB", "20"))

    # CORS 允许的域名（逗号分隔）
    cors_origins: str = os.getenv("CORS_ORIGINS", "http://localhost:5173,http://localhost:2345")

    # 桌面模式（PyInstaller 打包后设为 true）
    desktop_mode: str = os.getenv("DESKTOP_MODE", "false")


settings = Settings()
