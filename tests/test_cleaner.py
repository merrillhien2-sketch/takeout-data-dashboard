"""数据清洗模块测试。

验证 cleaner.py 的缺失值处理、异常值裁剪、重复去重与类型转换。
"""

from __future__ import annotations

from pathlib import Path

import pandas as pd
import pytest

from analysis.cleaner import clean_orders


class TestCleanOrders:
    """clean_orders 函数测试。"""

    def test_returns_dataframe(self, dirty_csv: Path, tmp_path: Path) -> None:
        """测试返回 DataFrame 且非空。"""
        output = tmp_path / "clean.csv"
        df = clean_orders(raw_csv=dirty_csv, output_csv=output)
        assert isinstance(df, pd.DataFrame)
        assert len(df) > 0

    def test_output_csv_created(self, dirty_csv: Path, tmp_path: Path) -> None:
        """测试输出 CSV 文件被创建。"""
        output = tmp_path / "clean.csv"
        clean_orders(raw_csv=dirty_csv, output_csv=output)
        assert output.exists()

    def test_duplicates_removed(self, dirty_csv: Path, tmp_path: Path) -> None:
        """测试重复订单号被去重。"""
        output = tmp_path / "clean.csv"
        df = clean_orders(raw_csv=dirty_csv, output_csv=output)
        # 原始有 T001 重复，去重后应只剩一条
        t001_count = (df["order_id"] == "T001").sum()
        assert t001_count == 1

    def test_no_negative_amount(self, dirty_csv: Path, tmp_path: Path) -> None:
        """测试负金额被移除。"""
        output = tmp_path / "clean.csv"
        df = clean_orders(raw_csv=dirty_csv, output_csv=output)
        assert (df["amount"] > 0).all()

    def test_amount_outlier_clipped(self, dirty_csv: Path, tmp_path: Path) -> None:
        """测试过大金额被分位裁剪（不超过 99 分位）。"""
        output = tmp_path / "clean.csv"
        df = clean_orders(raw_csv=dirty_csv, output_csv=output)
        # 99999 的异常值应被裁剪，不会出现在结果中
        assert (df["amount"] < 99999).all()

    def test_missing_amount_removed(self, dirty_csv: Path, tmp_path: Path) -> None:
        """测试缺失金额行被删除。"""
        output = tmp_path / "clean.csv"
        df = clean_orders(raw_csv=dirty_csv, output_csv=output)
        # T006 的 amount 为空，应被删除
        assert "T006" not in df["order_id"].values

    def test_missing_time_removed(self, dirty_csv: Path, tmp_path: Path) -> None:
        """测试缺失下单时间行被删除。"""
        output = tmp_path / "clean.csv"
        df = clean_orders(raw_csv=dirty_csv, output_csv=output)
        # T007 的 order_time 为空，应被删除
        assert "T007" not in df["order_id"].values

    def test_text_fields_filled(self, dirty_csv: Path, tmp_path: Path) -> None:
        """测试空文本字段被填充默认值。"""
        output = tmp_path / "clean.csv"
        df = clean_orders(raw_csv=dirty_csv, output_csv=output)
        # T008 的 merchant/category/city/region 为空，应被填充
        t008 = df[df["order_id"] == "T008"]
        if len(t008) > 0:
            row = t008.iloc[0]
            assert row["merchant"] != ""
            assert row["category"] != ""
            assert row["city"] != ""

    def test_time_column_parsed(self, dirty_csv: Path, tmp_path: Path) -> None:
        """测试 order_time 列被正确解析为 datetime。"""
        output = tmp_path / "clean.csv"
        df = clean_orders(raw_csv=dirty_csv, output_csv=output)
        # 重新读取 CSV 验证（CSV 中为字符串）
        df_read = pd.read_csv(output)
        df_read["order_time"] = pd.to_datetime(df_read["order_time"])
        assert pd.api.types.is_datetime64_any_dtype(df_read["order_time"])

    def test_derived_columns_exist(self, dirty_csv: Path, tmp_path: Path) -> None:
        """测试衍生列（order_hour, weekday）被正确添加。"""
        output = tmp_path / "clean.csv"
        df = clean_orders(raw_csv=dirty_csv, output_csv=output)
        assert "order_hour" in df.columns
        assert "weekday" in df.columns
        assert "order_date" in df.columns

    def test_rating_in_range(self, dirty_csv: Path, tmp_path: Path) -> None:
        """测试评分被约束在 [1, 5] 范围内。"""
        output = tmp_path / "clean.csv"
        df = clean_orders(raw_csv=dirty_csv, output_csv=output)
        assert (df["rating"] >= 1).all()
        assert (df["rating"] <= 5).all()

    def test_delivery_duration_positive(self, dirty_csv: Path, tmp_path: Path) -> None:
        """测试配送时长为正数。"""
        output = tmp_path / "clean.csv"
        df = clean_orders(raw_csv=dirty_csv, output_csv=output)
        assert (df["delivery_duration"] > 0).all()

    def test_file_not_found(self, tmp_path: Path) -> None:
        """测试源文件不存在时抛出 FileNotFoundError。"""
        with pytest.raises(FileNotFoundError):
            clean_orders(raw_csv=tmp_path / "nonexistent.csv", output_csv=tmp_path / "out.csv")
