"""可视化模块包。

包含图表生成（charts）与大屏组合（dashboard）两个子模块。
"""

from visualization.charts import build_all_charts
from visualization.dashboard import build_dashboard

__all__ = ["build_all_charts", "build_dashboard"]
