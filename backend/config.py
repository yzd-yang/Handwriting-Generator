"""
配置管理：从环境变量读取配置，提供默认值。
所有敏感信息（DSN、密钥）必须通过环境变量注入，不得硬编码。
"""

import os
from dataclasses import dataclass


@dataclass(frozen=True)
class Settings:
    # Sentry 错误监控
    sentry_dsn: str = os.getenv("SENTRY_DSN", "")
    sentry_traces_sample_rate: float = float(os.getenv("SENTRY_TRACES_SAMPLE_RATE", "0.1"))

    # 安全密钥（当前未启用，留空）
    secret_key: str = os.getenv("SECRET_KEY", "")

    # 字体资源路径
    font_assets_dir: str = os.getenv("FONT_ASSETS_DIR", "./font_assets")
    font_assets_bundled_dir: str = os.getenv("FONT_ASSETS_BUNDLED_DIR", "./font_assets")

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


settings = Settings()
