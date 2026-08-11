"""应用配置模块。

基于 pydantic-settings 从环境变量 / .env 文件读取配置，
禁止在代码中硬编码密钥，所有可配置项集中于此。
"""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


# 项目根目录：config/ 的上一级
BASE_DIR: Path = Path(__file__).resolve().parent.parent
# 数据目录
DATA_DIR: Path = BASE_DIR / "data"
RAW_DIR: Path = DATA_DIR / "raw"
PROCESSED_DIR: Path = DATA_DIR / "processed"
# 日志目录
LOG_DIR: Path = BASE_DIR / "logs"


class Settings(BaseSettings):
    """全局配置项。

    所有字段均可通过环境变量或 .env 文件覆盖，字段名不区分大小写。
    """

    model_config = SettingsConfigDict(
        env_file=str(BASE_DIR / ".env"),
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # ---- 应用基础 ----
    app_env: str = "development"
    app_name: str = "外卖订单数据分析大屏"
    debug: bool = True

    # ---- API 服务 ----
    api_host: str = "127.0.0.1"
    api_port: int = 8000

    # ---- 数据 ----
    sample_data_rows: int = 5000
    random_seed: int = 42

    # ---- 数据库 ----
    database_url: str = "sqlite:///data/takeout.db"

    # ---- 日志 ----
    log_level: str = "INFO"
    log_file: str = "logs/app.log"

    # ---- 密钥占位（本项目实际不使用真实外部服务）----
    secret_key: str = "please-replace-with-your-own-secret-key-placeholder"

    @property
    def base_dir(self) -> Path:
        """项目根目录。"""
        return BASE_DIR

    @property
    def raw_csv_path(self) -> Path:
        """原始样例数据 CSV 路径。"""
        return RAW_DIR / "takeout_orders_raw.csv"

    @property
    def processed_csv_path(self) -> Path:
        """清洗后数据 CSV 路径。"""
        return PROCESSED_DIR / "takeout_orders_clean.csv"

    @property
    def dashboard_html_path(self) -> Path:
        """生成的大屏 HTML 路径。"""
        return DATA_DIR / "dashboard.html"

    @property
    def db_path(self) -> Path:
        """SQLite 数据库文件路径。"""
        return DATA_DIR / "takeout.db"

    def ensure_dirs(self) -> None:
        """确保运行所需的目录存在。"""
        for d in (DATA_DIR, RAW_DIR, PROCESSED_DIR, LOG_DIR):
            d.mkdir(parents=True, exist_ok=True)


@lru_cache
def get_settings() -> Settings:
    """获取单例配置（带缓存）。"""
    s = Settings()
    s.ensure_dirs()
    return s


# 默认单例，供模块导入直接使用
settings: Settings = get_settings()
