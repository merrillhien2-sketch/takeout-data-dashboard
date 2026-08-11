"""数据分析模块包。

包含数据清洗（cleaner）与指标计算（metrics）两个子模块。
"""

from analysis.cleaner import clean_orders
from analysis.metrics import compute_all_metrics

__all__ = ["clean_orders", "compute_all_metrics"]
