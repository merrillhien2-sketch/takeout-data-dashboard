"""配置模块包。

统一管理应用配置（pydantic-settings）与日志（loguru）。
"""

from config.settings import settings
from config.logging_conf import setup_logging

__all__ = ["settings", "setup_logging"]
