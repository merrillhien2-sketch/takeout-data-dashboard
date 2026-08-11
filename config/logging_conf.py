"""日志配置模块。

使用 loguru 统一管理日志，支持控制台彩色输出与文件落盘（按大小/时间轮转）。
"""

from __future__ import annotations

import sys
from typing import Any

from loguru import logger

from config.settings import settings


def setup_logging() -> Any:
    """初始化 loguru 日志配置。

    - 控制台输出：彩色、简洁格式。
    - 文件落盘：按 10MB 轮转，保留 7 份，UTF-8 编码。
    - 日志级别由配置项 LOG_LEVEL 控制。

    Returns:
        配置后的 logger 实例。
    """
    # 移除默认 handler
    logger.remove()

    # 日志格式
    fmt_console = (
        "<green>{time:YYYY-MM-DD HH:mm:ss}</green> | "
        "<level>{level: <8}</level> | "
        "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - "
        "<level>{message}</level>"
    )
    fmt_file = (
        "{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | "
        "{name}:{function}:{line} - {message}"
    )

    level = settings.log_level.upper()

    # 控制台输出
    logger.add(
        sys.stderr,
        format=fmt_console,
        level=level,
        colorize=True,
        backtrace=settings.debug,
        diagnose=settings.debug,
    )

    # 文件落盘
    logger.add(
        settings.log_file,
        format=fmt_file,
        level=level,
        rotation="10 MB",
        retention="7 days",
        compression="zip",
        encoding="utf-8",
        backtrace=True,
        diagnose=False,
    )

    logger.info("日志初始化完成 | 级别={} | 文件={}", level, settings.log_file)
    return logger
