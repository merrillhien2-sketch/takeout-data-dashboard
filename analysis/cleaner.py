"""数据清洗模块。

使用 pandas 对原始外卖订单数据进行清洗：
1. 缺失值处理（填充 / 删除）
2. 异常值处理（金额 <= 0 或过大使用分位裁剪）
3. 重复值处理（按订单号去重）
4. 类型转换（时间解析、数值类型规范）

输出清洗后的 processed CSV，供指标计算与入库使用。
"""

from __future__ import annotations

from pathlib import Path

import pandas as pd
from loguru import logger

from config.settings import settings

# 标准列定义
COLUMNS = [
    "order_id",
    "user_id",
    "merchant",
    "category",
    "amount",
    "order_time",
    "city",
    "region",
    "delivery_duration",
    "rating",
]


def _to_numeric(series: pd.Series) -> pd.Series:
    """将序列安全转为数值类型，无法转换的置为 NaN。"""
    return pd.to_numeric(series, errors="coerce")


def clean_orders(
    raw_csv: Path | None = None,
    output_csv: Path | None = None,
) -> pd.DataFrame:
    """清洗外卖订单数据。

    Args:
        raw_csv: 原始 CSV 路径，默认使用配置中的 raw_csv_path。
        output_csv: 清洗后输出 CSV 路径，默认使用配置中的 processed_csv_path。

    Returns:
        清洗后的 pandas DataFrame。
    """
    raw_csv = raw_csv or settings.raw_csv_path
    output_csv = output_csv or settings.processed_csv_path

    logger.info("开始清洗数据 | 源文件={}", raw_csv)

    # ---- 1. 读取原始数据 ----
    if not raw_csv.exists():
        raise FileNotFoundError(f"原始数据文件不存在：{raw_csv}，请先运行 `python main.py data` 生成样例数据。")

    df = pd.read_csv(raw_csv, dtype=str)
    initial_count = len(df)
    logger.info("读取原始数据 | 行数={} | 列={}", initial_count, list(df.columns))

    # 统一列名为小写
    df.columns = [c.strip().lower() for c in df.columns]

    # ---- 2. 重复值处理：按订单号去重，保留最后一条 ----
    if "order_id" in df.columns:
        before = len(df)
        df = df.drop_duplicates(subset=["order_id"], keep="last").reset_index(drop=True)
        logger.info("去重（order_id）| 移除 {} 条重复记录", before - len(df))

    # ---- 3. 类型转换 ----
    # 金额
    df["amount"] = _to_numeric(df["amount"])
    # 配送时长
    df["delivery_duration"] = _to_numeric(df["delivery_duration"])
    # 评分
    df["rating"] = _to_numeric(df["rating"])
    # 下单时间解析
    df["order_time"] = pd.to_datetime(df["order_time"], errors="coerce")

    # ---- 4. 缺失值处理 ----
    # 关键字段缺失直接删除整行
    key_cols = ["order_id", "user_id", "amount", "order_time"]
    before = len(df)
    df = df.dropna(subset=key_cols).reset_index(drop=True)
    logger.info("删除关键字段缺失行 | 移除 {} 条", before - len(df))

    # 文本字段填充默认值
    text_defaults = {
        "merchant": "未知商家",
        "category": "其他",
        "city": "未知城市",
        "region": "未知区域",
    }
    for col, default in text_defaults.items():
        if col in df.columns:
            df[col] = df[col].fillna(default).astype(str).str.strip()
            df.loc[df[col] == "", col] = default

    # 数值字段填充默认值
    df["delivery_duration"] = df["delivery_duration"].fillna(df["delivery_duration"].median())
    df["rating"] = df["rating"].fillna(df["rating"].median() if df["rating"].notna().any() else 5.0)

    # ---- 5. 异常值处理：金额 <= 0 或过大，使用分位裁剪 ----
    df = _clip_amount_outliers(df)

    # 配送时长异常裁剪（0 ~ 120 分钟合理区间，超出按分位裁剪）
    df = _clip_duration_outliers(df)

    # 评分范围约束到 [1, 5]
    df["rating"] = df["rating"].clip(lower=1.0, upper=5.0)

    # ---- 6. 衍生字段：方便后续指标计算 ----
    df["order_date"] = df["order_time"].dt.date
    df["order_hour"] = df["order_time"].dt.hour
    df["weekday"] = df["order_time"].dt.weekday  # 0=周一 ... 6=周日

    # 列顺序整理
    final_cols = COLUMNS + ["order_date", "order_hour", "weekday"]
    df = df[[c for c in final_cols if c in df.columns]]

    # ---- 7. 输出清洗后 CSV ----
    output_csv.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(output_csv, index=False, encoding="utf-8-sig")
    logger.info(
        "清洗完成 | 原始 {} 条 -> 清洗后 {} 条 | 输出={}",
        initial_count, len(df), output_csv,
    )
    return df


def _clip_amount_outliers(df: pd.DataFrame) -> pd.DataFrame:
    """金额异常值处理：删除 <= 0 的记录，对过大值按 1%/99% 分位裁剪。"""
    before = len(df)
    # 金额必须 > 0
    df = df[df["amount"] > 0].reset_index(drop=True)
    logger.info("金额异常（<=0）移除 {} 条", before - len(df))

    # 分位裁剪：上下 1%
    lo = df["amount"].quantile(0.01)
    hi = df["amount"].quantile(0.99)
    df["amount"] = df["amount"].clip(lower=lo, upper=hi)
    logger.info("金额分位裁剪 | 范围=[{:.2f}, {:.2f}]", lo, hi)
    return df


def _clip_duration_outliers(df: pd.DataFrame) -> pd.DataFrame:
    """配送时长异常值处理：负值置为中位数，过大值按分位裁剪。"""
    median_dur = df["delivery_duration"].median()
    # 负值或 0 视为异常
    mask = df["delivery_duration"] <= 0
    if mask.any():
        logger.info("配送时长异常（<=0）修正 {} 条为中位数", mask.sum())
        df.loc[mask, "delivery_duration"] = median_dur

    # 分位裁剪
    hi = df["delivery_duration"].quantile(0.99)
    df["delivery_duration"] = df["delivery_duration"].clip(upper=hi)
    return df
