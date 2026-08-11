"""指标计算模块。

基于清洗后的外卖订单数据，计算以下核心指标：
1. 高峰时段（按小时订单量）
2. 客单价（平均每单金额）
3. 复购率（多次下单用户占比）
4. 销量排行（商家 / 品类）
5. 城市 / 区域分布
6. 配送时长分布
7. 评分分布

所有计算结果以可 JSON 序列化的字典返回，供 API 与大屏复用。
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import pandas as pd
from loguru import logger

from config.settings import settings


def load_clean_data(csv_path: Path | None = None) -> pd.DataFrame:
    """加载清洗后的订单数据。

    优先使用传入路径，其次使用配置中的 processed_csv_path。
    若文件不存在则抛出友好异常。
    """
    csv_path = csv_path or settings.processed_csv_path
    if not csv_path.exists():
        raise FileNotFoundError(
            f"清洗后数据不存在：{csv_path}，请先运行 `python main.py analyze`。"
        )
    df = pd.read_csv(csv_path)
    # 重新解析时间列
    if "order_time" in df.columns:
        df["order_time"] = pd.to_datetime(df["order_time"], errors="coerce")
    logger.info("加载清洗数据 | 行数={} | 文件={}", len(df), csv_path)
    return df


# ------------------------------------------------------------------ #
#  单项指标计算函数
# ------------------------------------------------------------------ #

def peak_hours(df: pd.DataFrame) -> dict[str, Any]:
    """高峰时段：按小时统计订单量（0-23 点完整序列）。"""
    if "order_hour" not in df.columns:
        df = df.copy()
        df["order_hour"] = df["order_time"].dt.hour
    # 保证 0-23 小时都有值
    counts = df.groupby("order_hour").size().reindex(range(24), fill_value=0)
    hours = [f"{h:02d}:00" for h in range(24)]
    return {
        "title": "24小时订单趋势",
        "hours": hours,
        "counts": counts.astype(int).tolist(),
        "peak_hour": int(counts.idxmax()),
        "peak_count": int(counts.max()),
    }


def average_order_value(df: pd.DataFrame) -> dict[str, Any]:
    """客单价：平均每单金额。"""
    total_amount = float(df["amount"].sum())
    total_orders = int(len(df))
    aov = total_amount / total_orders if total_orders else 0.0
    return {
        "total_amount": round(total_amount, 2),
        "total_orders": total_orders,
        "aov": round(aov, 2),
    }


def repurchase_rate(df: pd.DataFrame) -> dict[str, Any]:
    """复购率：下单次数 >= 2 的用户占总用户比例。"""
    user_orders = df.groupby("user_id").size()
    total_users = int(len(user_orders))
    repurchase_users = int((user_orders >= 2).sum())
    rate = repurchase_users / total_users if total_users else 0.0
    return {
        "total_users": total_users,
        "repurchase_users": repurchase_users,
        "repurchase_rate": round(rate, 4),
    }


def sales_ranking(df: pd.DataFrame, by: str = "merchant", top: int = 10) -> dict[str, Any]:
    """销量排行：按商家或品类统计订单数与金额，取 Top N。"""
    valid = {"merchant", "category"}
    if by not in valid:
        raise ValueError(f"by 参数必须是 {valid} 之一，当前：{by}")

    grouped = (
        df.groupby(by)
        .agg(order_count=("order_id", "count"), total_amount=("amount", "sum"))
        .sort_values("order_count", ascending=False)
        .head(top)
        .reset_index()
    )
    return {
        "title": f"销量排行 - {by}",
        "names": grouped[by].astype(str).tolist(),
        "order_counts": grouped["order_count"].astype(int).tolist(),
        "total_amounts": grouped["total_amount"].round(2).tolist(),
    }


def city_distribution(df: pd.DataFrame) -> dict[str, Any]:
    """城市分布：各城市订单量。"""
    grouped = (
        df.groupby("city")
        .agg(order_count=("order_id", "count"), total_amount=("amount", "sum"))
        .sort_values("order_count", ascending=False)
        .reset_index()
    )
    return {
        "title": "城市订单分布",
        "cities": grouped["city"].astype(str).tolist(),
        "order_counts": grouped["order_count"].astype(int).tolist(),
        "total_amounts": grouped["total_amount"].round(2).tolist(),
    }


def region_distribution(df: pd.DataFrame, city: str | None = None) -> dict[str, Any]:
    """区域分布：各区域订单量，可按城市过滤。"""
    sub = df if city is None else df[df["city"] == city]
    grouped = (
        sub.groupby("region")
        .agg(order_count=("order_id", "count"))
        .sort_values("order_count", ascending=False)
        .reset_index()
    )
    return {
        "title": f"区域订单分布{f' - {city}' if city else ''}",
        "regions": grouped["region"].astype(str).tolist(),
        "order_counts": grouped["order_count"].astype(int).tolist(),
    }


def delivery_duration_distribution(df: pd.DataFrame) -> dict[str, Any]:
    """配送时长分布：按时长分箱统计。"""
    bins = [0, 15, 30, 45, 60, 90, 120]
    labels = ["0-15", "15-30", "30-45", "45-60", "60-90", "90+"]
    binned = pd.cut(df["delivery_duration"], bins=bins, labels=labels, right=True)
    counts = binned.value_counts().reindex(labels, fill_value=0)
    avg_dur = float(df["delivery_duration"].mean())
    return {
        "title": "配送时长分布",
        "labels": labels,
        "counts": counts.astype(int).tolist(),
        "avg_duration": round(avg_dur, 2),
    }


def rating_distribution(df: pd.DataFrame) -> dict[str, Any]:
    """评分分布：按评分取整统计。"""
    if "rating" not in df.columns:
        return {"title": "评分分布", "labels": [], "counts": [], "avg_rating": 0.0}
    rounded = df["rating"].round().clip(1, 5).astype(int)
    counts = rounded.value_counts().reindex(range(1, 6), fill_value=0).sort_index()
    labels = [f"{i}星" for i in range(1, 6)]
    avg_rating = float(df["rating"].mean())
    return {
        "title": "评分分布",
        "labels": labels,
        "counts": counts.astype(int).tolist(),
        "avg_rating": round(avg_rating, 2),
    }


def weekday_hour_heatmap(df: pd.DataFrame) -> dict[str, Any]:
    """热力图数据：星期 × 小时 的订单量矩阵。"""
    if "weekday" not in df.columns:
        df = df.copy()
        df["weekday"] = df["order_time"].dt.weekday
    if "order_hour" not in df.columns:
        df = df.copy()
        df["order_hour"] = df["order_time"].dt.hour

    weekdays = ["周一", "周二", "周三", "周四", "周五", "周六", "周日"]
    pivot = (
        df.pivot_table(
            index="weekday", columns="order_hour", values="order_id", aggfunc="count",
            fill_value=0,
        )
        .reindex(index=range(7), columns=range(24), fill_value=0)
    )
    # 转为 [[x(小时), y(星期), value], ...] 格式供 pyecharts 热力图使用
    data: list[list[int]] = []
    for h in range(24):
        for w in range(7):
            data.append([h, w, int(pivot.iloc[w, h])])
    return {
        "title": "星期×小时 订单热力图",
        "weekdays": weekdays,
        "hours": [f"{h:02d}:00" for h in range(24)],
        "data": data,
        "max_value": int(pivot.values.max()),
    }


def overview(df: pd.DataFrame) -> dict[str, Any]:
    """总览指标：订单数、总金额、用户数、商家数、客单价、复购率、平均评分、平均配送时长。"""
    aov = average_order_value(df)
    rep = repurchase_rate(df)
    return {
        "total_orders": aov["total_orders"],
        "total_amount": aov["total_amount"],
        "total_users": rep["total_users"],
        "total_merchants": int(df["merchant"].nunique()),
        "total_cities": int(df["city"].nunique()),
        "aov": aov["aov"],
        "repurchase_rate": rep["repurchase_rate"],
        "avg_rating": round(float(df["rating"].mean()), 2),
        "avg_delivery_duration": round(float(df["delivery_duration"].mean()), 2),
    }


def compute_all_metrics(df: pd.DataFrame | None = None) -> dict[str, Any]:
    """计算全部指标，返回统一字典结构。

    Args:
        df: 清洗后的 DataFrame；为 None 时自动从 processed CSV 加载。

    Returns:
        包含所有指标的大字典，可直接 JSON 序列化。
    """
    if df is None:
        df = load_clean_data()

    logger.info("开始计算全部指标 | 数据量={}", len(df))

    result: dict[str, Any] = {
        "overview": overview(df),
        "peak_hours": peak_hours(df),
        "average_order_value": average_order_value(df),
        "repurchase_rate": repurchase_rate(df),
        "merchant_ranking": sales_ranking(df, by="merchant", top=10),
        "category_ranking": sales_ranking(df, by="category", top=10),
        "city_distribution": city_distribution(df),
        "region_distribution": region_distribution(df),
        "delivery_duration_distribution": delivery_duration_distribution(df),
        "rating_distribution": rating_distribution(df),
        "weekday_hour_heatmap": weekday_hour_heatmap(df),
    }

    logger.info("指标计算完成 | 指标项数={}", len(result))
    return result
