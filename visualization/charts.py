"""图表生成模块。

使用 pyecharts 生成各单项图表：
1. 折线图：24 小时订单趋势
2. 热力图：星期 × 小时
3. 地图：城市订单量（中国地图）
4. 柱状图：商家排行 Top10
5. 饼图：品类占比

所有图表返回 pyecharts Chart 对象，供 dashboard 组合使用。
"""

from __future__ import annotations

from typing import Any

from loguru import logger
from pyecharts import options as opts
from pyecharts.charts import Bar, HeatMap, Line, Map, Pie
from pyecharts.globals import ThemeType

# 大屏统一主题色与尺寸
DARK_THEME = ThemeType.DARK
CHART_WIDTH = "100%"
CHART_HEIGHT = "320px"


def _line_chart(metrics: dict[str, Any]) -> Line:
    """折线图：24 小时订单趋势。"""
    pk = metrics["peak_hours"]
    chart = (
        Line(init_opts=opts.InitOpts(width=CHART_WIDTH, height=CHART_HEIGHT, theme=DARK_THEME))
        .add_xaxis(pk["hours"])
        .add_yaxis(
            "订单量",
            pk["counts"],
            is_smooth=True,
            symbol="circle",
            symbol_size=6,
            linestyle_opts=opts.LineStyleOpts(width=2),
            areastyle_opts=opts.AreaStyleOpts(opacity=0.25),
            label_opts=opts.LabelOpts(is_show=False),
        )
        .set_global_opts(
            title_opts=opts.TitleOpts(title="24小时订单趋势", subtitle=f"高峰时段 {pk['peak_hour']:02d}:00"),
            tooltip_opts=opts.TooltipOpts(trigger="axis"),
            xaxis_opts=opts.AxisOpts(name="时间", axislabel_opts=opts.LabelOpts(rotate=0)),
            yaxis_opts=opts.AxisOpts(name="订单量"),
            legend_opts=opts.LegendOpts(pos_top="3%"),
        )
    )
    return chart


def _heatmap_chart(metrics: dict[str, Any]) -> HeatMap:
    """热力图：星期 × 小时 订单分布。"""
    hm = metrics["weekday_hour_heatmap"]
    chart = (
        HeatMap(init_opts=opts.InitOpts(width=CHART_WIDTH, height=CHART_HEIGHT, theme=DARK_THEME))
        .add_xaxis(hm["hours"])
        .add_yaxis(
            "订单量",
            hm["weekdays"],
            hm["data"],
            label_opts=opts.LabelOpts(is_show=False),
        )
        .set_global_opts(
            title_opts=opts.TitleOpts(title="星期×小时 订单热力图"),
            visualmap_opts=opts.VisualMapOpts(
                min_=0,
                max_=hm["max_value"] if hm["max_value"] > 0 else 1,
                orient="horizontal",
                pos_left="center",
                pos_bottom="2%",
            ),
            xaxis_opts=opts.AxisOpts(name="小时", axislabel_opts=opts.LabelOpts(rotate=0)),
            yaxis_opts=opts.AxisOpts(name="星期"),
        )
    )
    return chart


def _map_chart(metrics: dict[str, Any]) -> Map:
    """地图：城市订单量（中国地图）。"""
    cd = metrics["city_distribution"]
    data_pairs = list(zip(cd["cities"], cd["order_counts"]))
    max_val = max(cd["order_counts"]) if cd["order_counts"] else 1
    chart = (
        Map(init_opts=opts.InitOpts(width=CHART_WIDTH, height=CHART_HEIGHT, theme=DARK_THEME))
        .add("订单量", data_pairs, maptype="china")
        .set_global_opts(
            title_opts=opts.TitleOpts(title="城市订单分布", subtitle="全国主要城市"),
            visualmap_opts=opts.VisualMapOpts(
                min_=0,
                max_=max_val,
                is_piecewise=True,
                pieces=_make_pieces(max_val),
                pos_left="2%",
                pos_bottom="5%",
            ),
            legend_opts=opts.LegendOpts(is_show=False),
        )
    )
    return chart


def _make_pieces(max_val: int) -> list[dict[str, Any]]:
    """生成地图分段配置。"""
    if max_val <= 0:
        max_val = 1
    step = max(1, max_val // 5)
    return [
        {"min": step * 4, "label": f"≥{step * 4}", "color": "#7f1800"},
        {"min": step * 3, "max": step * 4 - 1, "label": f"{step*3}-{step*4-1}", "color": "#b30000"},
        {"min": step * 2, "max": step * 3 - 1, "label": f"{step*2}-{step*3-1}", "color": "#e34a33"},
        {"min": step, "max": step * 2 - 1, "label": f"{step}-{step*2-1}", "color": "#fc8d59"},
        {"min": 0, "max": step - 1, "label": f"0-{step-1}", "color": "#fdbb84"},
    ]


def _bar_chart(metrics: dict[str, Any]) -> Bar:
    """柱状图：商家销量排行 Top10。"""
    mr = metrics["merchant_ranking"]
    chart = (
        Bar(init_opts=opts.InitOpts(width=CHART_WIDTH, height=CHART_HEIGHT, theme=DARK_THEME))
        .add_xaxis(mr["names"])
        .add_yaxis("订单量", mr["order_counts"], label_opts=opts.LabelOpts(position="right"))
        .reversal_axis()
        .set_global_opts(
            title_opts=opts.TitleOpts(title="商家销量排行 Top10"),
            tooltip_opts=opts.TooltipOpts(trigger="axis", axis_pointer_type="shadow"),
            xaxis_opts=opts.AxisOpts(name="订单量"),
            yaxis_opts=opts.AxisOpts(name="商家"),
            legend_opts=opts.LegendOpts(pos_top="3%"),
        )
    )
    return chart


def _pie_chart(metrics: dict[str, Any]) -> Pie:
    """饼图：品类占比。"""
    cr = metrics["category_ranking"]
    data_pairs = list(zip(cr["names"], cr["order_counts"]))
    chart = (
        Pie(init_opts=opts.InitOpts(width=CHART_WIDTH, height=CHART_HEIGHT, theme=DARK_THEME))
        .add(
            "品类占比",
            data_pairs,
            radius=["30%", "65%"],
            rosetype="radius",
            label_opts=opts.LabelOpts(formatter="{b}: {d}%"),
        )
        .set_global_opts(
            title_opts=opts.TitleOpts(title="品类销量占比"),
            legend_opts=opts.LegendOpts(orient="vertical", pos_left="2%", pos_top="15%"),
            tooltip_opts=opts.TooltipOpts(trigger="item", formatter="{a}<br/>{b}: {c} ({d}%)"),
        )
    )
    return chart


def build_all_charts(metrics: dict[str, Any]) -> dict[str, Any]:
    """构建全部图表，返回图表名 -> Chart 对象的字典。"""
    logger.info("开始生成 pyecharts 图表")
    charts = {
        "line": _line_chart(metrics),
        "heatmap": _heatmap_chart(metrics),
        "map": _map_chart(metrics),
        "bar": _bar_chart(metrics),
        "pie": _pie_chart(metrics),
    }
    logger.info("图表生成完成 | 数量={}", len(charts))
    return charts
