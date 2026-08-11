"""数据库 ORM 模块。

使用 SQLAlchemy 2.0 风格定义订单数据模型与会话管理。
清洗后的订单数据可持久化到 SQLite，供 API 查询使用（可选）。
"""

from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import Generator

from loguru import logger
from sqlalchemy import (
    Column,
    DateTime,
    Float,
    Integer,
    String,
    create_engine,
)
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from config.settings import settings


class Base(DeclarativeBase):
    """SQLAlchemy 2.0 声明式基类。"""
    pass


class Order(Base):
    """外卖订单 ORM 模型。

    对应数据库 orders 表，存储清洗后的订单记录。
    """

    __tablename__ = "orders"

    id = Column("id", Integer, primary_key=True, autoincrement=True)
    order_id = Column("order_id", String(64), unique=True, index=True, comment="订单号")
    user_id = Column("user_id", String(64), index=True, comment="用户ID")
    merchant = Column("merchant", String(128), comment="商家")
    category = Column("category", String(64), index=True, comment="品类")
    amount = Column("amount", Float, comment="订单金额")
    order_time = Column("order_time", DateTime, index=True, comment="下单时间")
    city = Column("city", String(32), index=True, comment="城市")
    region = Column("region", String(64), comment="区域")
    delivery_duration = Column("delivery_duration", Float, comment="配送时长(分钟)")
    rating = Column("rating", Float, comment="评分")

    def __repr__(self) -> str:
        return f"<Order(order_id={self.order_id!r}, amount={self.amount})>"


# ---- 引擎与会话工厂 ----

def get_engine():
    """创建数据库引擎（SQLite，自动建目录）。"""
    db_path = settings.db_path
    db_path.parent.mkdir(parents=True, exist_ok=True)
    url = f"sqlite:///{db_path}"
    logger.info("创建数据库引擎 | url={}", url)
    return create_engine(url, echo=False, future=True)


def get_session_factory(engine=None) -> sessionmaker:
    """创建会话工厂。"""
    engine = engine or get_engine()
    return sessionmaker(bind=engine, class_=Session, expire_on_commit=False, future=True)


def init_db(engine=None) -> None:
    """初始化数据库：建表。"""
    engine = engine or get_engine()
    Base.metadata.create_all(engine)
    logger.info("数据库表已创建")


def store_orders_from_csv(csv_path: Path | None = None, engine=None) -> int:
    """将清洗后的 CSV 数据批量写入数据库。

    Args:
        csv_path: 清洗后 CSV 路径，默认使用配置中的 processed_csv_path。
        engine: 已有引擎，默认新建。

    Returns:
        写入的记录数。
    """
    import pandas as pd

    csv_path = csv_path or settings.processed_csv_path
    if not csv_path.exists():
        raise FileNotFoundError(f"清洗数据不存在：{csv_path}")

    engine = engine or get_engine()
    init_db(engine)

    df = pd.read_csv(csv_path)
    # 仅保留 ORM 模型定义的列
    orm_cols = [
        "order_id", "user_id", "merchant", "category", "amount",
        "order_time", "city", "region", "delivery_duration", "rating",
    ]
    df = df[[c for c in orm_cols if c in df.columns]].copy()
    df["order_time"] = pd.to_datetime(df["order_time"], errors="coerce")

    df.to_sql("orders", engine, if_exists="replace", index=False)
    count = len(df)
    logger.info("订单数据写入数据库 | 记录数={} | 表=orders", count)
    return count


def get_session() -> Generator[Session, None, None]:
    """FastAPI 依赖：获取数据库会话（请求级）。"""
    factory = get_session_factory()
    session = factory()
    try:
        yield session
    finally:
        session.close()
