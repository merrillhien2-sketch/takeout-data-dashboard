"""大屏组合模块。

将 charts.py 生成的各单项图表组合成一个可视化大屏 HTML。
对每个图表单独调用 render_embed() 获取其 div + 初始化脚本，
再用自定义 HTML/CSS 包裹，引入共享的 echarts.min.js，
实现 KPI 卡片 + 网格图表的深色科技风大屏布局。
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from loguru import logger

from analysis.metrics import compute_all_metrics, load_clean_data
from config.settings import settings
from visualization.charts import build_all_charts

# echarts JS 依赖（pyecharts v5 对应 echarts 5.x）
ECHARTS_CDN = "https://assets.pyecharts.org/assets/v5/echarts.min.js"
# 中国地图 JS 依赖
CHINA_MAP_CDN = "https://assets.pyecharts.org/assets/v5/maps/china.js"

# 大屏自定义 CSS 样式（深色科技风 + 网格布局）
DASHBOARD_CSS = """
    * { box-sizing: border-box; }
    body { margin: 0; padding: 0; background: #0d1b2a; color: #e0e6ed;
           font-family: "Microsoft YaHei", "PingFang SC", "Helvetica Neue", sans-serif; }
    .page-container { padding: 16px; max-width: 1920px; margin: 0 auto; }

    /* 标题区 */
    .dashboard-header { text-align: center; padding: 16px 0; margin-bottom: 14px;
                        background: linear-gradient(90deg, #1b263b, #415a77, #1b263b);
                        border-radius: 8px; border: 1px solid #415a77; }
    .dashboard-header h1 { margin: 0; font-size: 28px; color: #7ec8e3;
                           letter-spacing: 4px; text-shadow: 0 0 12px rgba(126,200,227,0.5); }
    .dashboard-header p { margin: 8px 0 0; color: #9fb3c8; font-size: 13px; }

    /* KPI 卡片行 */
    .kpi-row { display: flex; flex-wrap: wrap; justify-content: space-between;
               margin-bottom: 14px; gap: 10px; }
    .kpi-card { flex: 1 1 13%; min-width: 130px; background: #1b263b;
                border: 1px solid #415a77; border-radius: 8px; padding: 14px 10px;
                text-align: center; }
    .kpi-card .kpi-value { font-size: 26px; font-weight: bold; color: #7ec8e3; }
    .kpi-card .kpi-label { font-size: 12px; color: #9fb3c8; margin-top: 6px; }

    /* 图表网格 */
    .chart-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 14px; margin-bottom: 14px; }
    .chart-cell.chart-full { grid-column: 1 / -1; }
    .chart-cell { min-width: 0; background: #1b263b; border: 1px solid #415a77;
                  border-radius: 8px; padding: 6px; }
    .chart-cell .chart-container { width: 100% !important; height: 320px !important; }
    .chart-cell.chart-full .chart-container { height: 280px !important; }
    @media (max-width: 900px) { .chart-grid { grid-template-columns: 1fr; } }
"""


def _build_kpi_html(overview: dict[str, Any]) -> str:
    """构建顶部 KPI 卡片 HTML。"""
    cards = [
        ("总订单数", f"{overview['total_orders']:,}"),
        ("总金额", f"¥{overview['total_amount']:,.0f}"),
        ("用户数", f"{overview['total_users']:,}"),
        ("客单价", f"¥{overview['aov']:.2f}"),
        ("复购率", f"{overview['repurchase_rate']*100:.1f}%"),
        ("平均评分", f"{overview['avg_rating']:.2f}"),
        ("平均配送", f"{overview['avg_delivery_duration']:.0f}分钟"),
    ]
    items = "".join(
        f'<div class="kpi-card"><div class="kpi-value">{val}</div>'
        f'<div class="kpi-label">{label}</div></div>'
        for label, val in cards
    )
    return f'<div class="kpi-row">{items}</div>'


def _build_header_html() -> str:
    """构建大屏标题区 HTML。"""
    return (
        '<div class="dashboard-header">'
        f'<h1>{settings.app_name}</h1>'
        '<p>外卖订单数据清洗 · 指标分析 · 可视化大屏</p>'
        "</div>"
    )


def build_dashboard(
    output_html: Path | None = None,
    metrics: dict[str, Any] | None = None,
) -> Path:
    """生成完整大屏 HTML。

    对每个图表单独调用 render_embed() 获取嵌入 HTML，
    再用自定义布局组装为科技风大屏。

    Args:
        output_html: 输出 HTML 路径，默认使用配置中的 dashboard_html_path。
        metrics: 预计算的指标字典；为 None 时自动从清洗数据计算。

    Returns:
        生成的大屏 HTML 文件路径。
    """
    output_html = output_html or settings.dashboard_html_path

    if metrics is None:
        df = load_clean_data()
        metrics = compute_all_metrics(df)

    logger.info("开始组合大屏 HTML | 输出={}", output_html)

    charts = build_all_charts(metrics)

    # 逐个图表获取嵌入 HTML（div + 初始化 script，不含外部依赖）
    chart_embeds: list[str] = []
    for name, chart in charts.items():
        embed = chart.render_embed()
        chart_embeds.append(embed)
        logger.debug("图表 {} embed 长度={}", name, len(embed))

    # 布局：折线图全宽 -> 热力图+地图并排 -> 柱状图+饼图并排
    layout_map = [
        ("chart-full", [0]),   # 折线图（24小时趋势）全宽
        (None, [1, 2]),        # 热力图 + 地图 并排
        (None, [3, 4]),        # 柱状图 + 饼图 并排
    ]
    rows_html = ""
    for extra_class, indices in layout_map:
        cells = ""
        for i in indices:
            if i < len(chart_embeds):
                cls = "chart-cell"
                if extra_class:
                    cls += f" {extra_class}"
                cells += f'<div class="{cls}">{chart_embeds[i]}</div>'
        rows_html += f'<div class="chart-grid">{cells}</div>'

    header = _build_header_html()
    kpi = _build_kpi_html(metrics["overview"])

    final_html = f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{settings.app_name}</title>
    <script src="{ECHARTS_CDN}"></script>
    <script src="{CHINA_MAP_CDN}"></script>
    <style>
{DASHBOARD_CSS}
    </style>
</head>
<body>
    <div class="page-container">
        {header}
        {kpi}
        {rows_html}
    </div>
</body>
</html>"""

    output_html.parent.mkdir(parents=True, exist_ok=True)
    output_html.write_text(final_html, encoding="utf-8")
    logger.info(
        "大屏 HTML 生成成功 | 文件={} | 大小={}KB",
        output_html,
        output_html.stat().st_size // 1024,
    )
    return output_html
