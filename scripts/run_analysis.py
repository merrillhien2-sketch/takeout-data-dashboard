"""数据分析脚本。

执行完整的数据清洗与指标计算流程：
1. 调用 cleaner 清洗原始数据
2. 调用 metrics 计算全部指标
3. 可选：将清洗后数据写入 SQLite 数据库
4. 输出指标摘要到控制台
"""

from __future__ import annotations

from pathlib import Path

from loguru import logger

from analysis.cleaner import clean_orders
from analysis.metrics import compute_all_metrics
from api.database import store_orders_from_csv
from config.logging_conf import setup_logging
from config.settings import settings


def run_analysis(
    raw_csv: Path | None = None,
    output_csv: Path | None = None,
    store_db: bool = True,
) -> dict:
    """执行清洗 + 指标计算流程。

    Args:
        raw_csv: 原始数据路径。
        output_csv: 清洗后输出路径。
        store_db: 是否写入 SQLite 数据库。

    Returns:
        计算的指标字典。
    """
    setup_logging()
    logger.info("=" * 60)
    logger.info("开始执行数据分析流程")
    logger.info("=" * 60)

    # 1. 清洗数据
    df = clean_orders(raw_csv=raw_csv, output_csv=output_csv)

    # 2. 计算指标
    metrics = compute_all_metrics(df)

    # 3. 打印关键指标摘要
    _print_summary(metrics)

    # 4. 可选：写入数据库
    if store_db:
        try:
            count = store_orders_from_csv(output_csv or settings.processed_csv_path)
            logger.info("清洗数据已写入 SQLite | 记录数={}", count)
        except Exception as e:
            logger.warning("写入数据库失败（不影响主流程）| 错误={}", e)

    logger.info("数据分析流程完成")
    return metrics


def _print_summary(metrics: dict) -> None:
    """打印关键指标摘要。"""
    ov = metrics["overview"]
    rep = metrics["repurchase_rate"]
    pk = metrics["peak_hours"]

    logger.info("-" * 40)
    logger.info("【指标摘要】")
    logger.info("  总订单数:     {}", ov["total_orders"])
    logger.info("  总金额:       ¥{:,.2f}", ov["total_amount"])
    logger.info("  用户数:       {}", ov["total_users"])
    logger.info("  商家数:       {}", ov["total_merchants"])
    logger.info("  城市数:       {}", ov["total_cities"])
    logger.info("  客单价:       ¥{:.2f}", ov["aov"])
    logger.info("  复购率:       {:.1f}%", rep["repurchase_rate"] * 100)
    logger.info("  平均评分:     {:.2f}", ov["avg_rating"])
    logger.info("  平均配送时长: {:.1f} 分钟", ov["avg_delivery_duration"])
    logger.info("  高峰时段:     {:02d}:00 ({} 单)", pk["peak_hour"], pk["peak_count"])
    logger.info("-" * 40)


if __name__ == "__main__":
    run_analysis()
