"""指标计算模块测试。

验证 metrics.py 的各项指标计算逻辑正确性。
"""

from __future__ import annotations

from pathlib import Path

import pandas as pd
import pytest

from analysis.metrics import (
    average_order_value,
    city_distribution,
    compute_all_metrics,
    delivery_duration_distribution,
    peak_hours,
    rating_distribution,
    repurchase_rate,
    sales_ranking,
    weekday_hour_heatmap,
)


class TestPeakHours:
    """高峰时段测试。"""

    def test_returns_24_hours(self, clean_df: pd.DataFrame) -> None:
        """测试返回完整 24 小时序列。"""
        result = peak_hours(clean_df)
        assert len(result["hours"]) == 24
        assert len(result["counts"]) == 24

    def test_peak_hour_in_range(self, clean_df: pd.DataFrame) -> None:
        """测试高峰小时在 0-23 范围内。"""
        result = peak_hours(clean_df)
        assert 0 <= result["peak_hour"] <= 23

    def test_counts_non_negative(self, clean_df: pd.DataFrame) -> None:
        """测试订单量非负。"""
        result = peak_hours(clean_df)
        assert all(c >= 0 for c in result["counts"])


class TestAverageOrderValue:
    """客单价测试。"""

    def test_aov_positive(self, clean_df: pd.DataFrame) -> None:
        """测试客单价为正数。"""
        result = average_order_value(clean_df)
        assert result["aov"] > 0

    def test_total_orders_match(self, clean_df: pd.DataFrame) -> None:
        """测试总订单数与数据行数一致。"""
        result = average_order_value(clean_df)
        assert result["total_orders"] == len(clean_df)

    def test_amount_calculation(self, clean_df: pd.DataFrame) -> None:
        """测试总金额计算正确。"""
        result = average_order_value(clean_df)
        expected = float(clean_df["amount"].sum())
        assert abs(result["total_amount"] - expected) < 0.01


class TestRepurchaseRate:
    """复购率测试。"""

    def test_rate_in_range(self, clean_df: pd.DataFrame) -> None:
        """测试复购率在 [0, 1] 范围内。"""
        result = repurchase_rate(clean_df)
        assert 0 <= result["repurchase_rate"] <= 1

    def test_repurchase_user_detection(self, clean_df: pd.DataFrame) -> None:
        """测试能正确识别复购用户（U01 出现多次）。"""
        result = repurchase_rate(clean_df)
        assert result["repurchase_users"] >= 1

    def test_total_users_positive(self, clean_df: pd.DataFrame) -> None:
        """测试总用户数为正。"""
        result = repurchase_rate(clean_df)
        assert result["total_users"] > 0


class TestSalesRanking:
    """销量排行测试。"""

    def test_merchant_ranking(self, clean_df: pd.DataFrame) -> None:
        """测试商家排行返回正确结构。"""
        result = sales_ranking(clean_df, by="merchant", top=5)
        assert "names" in result
        assert "order_counts" in result
        assert len(result["names"]) == len(result["order_counts"])

    def test_ranking_sorted_desc(self, clean_df: pd.DataFrame) -> None:
        """测试排行按订单量降序排列。"""
        result = sales_ranking(clean_df, by="merchant", top=10)
        counts = result["order_counts"]
        assert counts == sorted(counts, reverse=True)

    def test_category_ranking(self, clean_df: pd.DataFrame) -> None:
        """测试品类排行。"""
        result = sales_ranking(clean_df, by="category", top=10)
        assert len(result["names"]) > 0

    def test_invalid_by_param(self, clean_df: pd.DataFrame) -> None:
        """测试无效 by 参数抛出异常。"""
        with pytest.raises(ValueError):
            sales_ranking(clean_df, by="invalid_field", top=5)


class TestCityDistribution:
    """城市分布测试。"""

    def test_returns_cities(self, clean_df: pd.DataFrame) -> None:
        """测试返回城市列表。"""
        result = city_distribution(clean_df)
        assert len(result["cities"]) > 0
        assert len(result["cities"]) == len(result["order_counts"])

    def test_counts_match(self, clean_df: pd.DataFrame) -> None:
        """测试城市订单数之和等于总订单数。"""
        result = city_distribution(clean_df)
        assert sum(result["order_counts"]) == len(clean_df)


class TestDeliveryDuration:
    """配送时长分布测试。"""

    def test_returns_bins(self, clean_df: pd.DataFrame) -> None:
        """测试返回分箱标签与计数。"""
        result = delivery_duration_distribution(clean_df)
        assert len(result["labels"]) == 6
        assert len(result["counts"]) == 6

    def test_avg_duration_positive(self, clean_df: pd.DataFrame) -> None:
        """测试平均配送时长为正。"""
        result = delivery_duration_distribution(clean_df)
        assert result["avg_duration"] > 0


class TestRatingDistribution:
    """评分分布测试。"""

    def test_returns_5_levels(self, clean_df: pd.DataFrame) -> None:
        """测试返回 5 个评分等级。"""
        result = rating_distribution(clean_df)
        assert len(result["labels"]) == 5
        assert len(result["counts"]) == 5

    def test_avg_rating_in_range(self, clean_df: pd.DataFrame) -> None:
        """测试平均评分在 [1, 5] 范围内。"""
        result = rating_distribution(clean_df)
        assert 1 <= result["avg_rating"] <= 5


class TestWeekdayHourHeatmap:
    """星期×小时热力图测试。"""

    def test_returns_7_weekdays(self, clean_df: pd.DataFrame) -> None:
        """测试返回 7 个星期标签。"""
        result = weekday_hour_heatmap(clean_df)
        assert len(result["weekdays"]) == 7

    def test_returns_24_hours(self, clean_df: pd.DataFrame) -> None:
        """测试返回 24 个小时标签。"""
        result = weekday_hour_heatmap(clean_df)
        assert len(result["hours"]) == 24

    def test_data_format(self, clean_df: pd.DataFrame) -> None:
        """测试热力图数据格式为 [x, y, value]。"""
        result = weekday_hour_heatmap(clean_df)
        assert len(result["data"]) == 24 * 7  # 168 个点
        for point in result["data"]:
            assert len(point) == 3


class TestComputeAllMetrics:
    """全量指标计算测试。"""

    def test_returns_all_keys(self, clean_df: pd.DataFrame) -> None:
        """测试返回所有指标项。"""
        result = compute_all_metrics(clean_df)
        expected_keys = {
            "overview", "peak_hours", "average_order_value", "repurchase_rate",
            "merchant_ranking", "category_ranking", "city_distribution",
            "region_distribution", "delivery_duration_distribution",
            "rating_distribution", "weekday_hour_heatmap",
        }
        assert set(result.keys()) == expected_keys

    def test_overview_has_required_fields(self, clean_df: pd.DataFrame) -> None:
        """测试总览包含必要字段。"""
        result = compute_all_metrics(clean_df)
        ov = result["overview"]
        for key in ("total_orders", "total_amount", "total_users",
                     "aov", "repurchase_rate", "avg_rating"):
            assert key in ov

    def test_overview_values_consistent(self, clean_df: pd.DataFrame) -> None:
        """测试总览数值一致性。"""
        result = compute_all_metrics(clean_df)
        ov = result["overview"]
        assert ov["total_orders"] == len(clean_df)
        assert ov["total_users"] == clean_df["user_id"].nunique()
        assert ov["total_merchants"] == clean_df["merchant"].nunique()
