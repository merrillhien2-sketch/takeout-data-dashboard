"""pytest 共享夹具。

提供测试用的脏数据 DataFrame 与临时 CSV 路径，
供 test_cleaner 与 test_metrics 复用。
"""

from __future__ import annotations

import sys
from pathlib import Path
from tempfile import TemporaryDirectory

import pandas as pd
import pytest

# 确保项目根目录在 sys.path 中（pytest 从根目录运行时自动处理，此处兜底）
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


@pytest.fixture
def dirty_df() -> pd.DataFrame:
    """构造含脏数据的测试 DataFrame。

    包含：缺失值、负金额、过大金额、重复订单号、空文本字段。
    """
    data = [
        # 正常记录
        {"order_id": "T001", "user_id": "U01", "merchant": "老记餐厅", "category": "快餐便当",
         "amount": "35.5", "order_time": "2024-06-01 12:30:00", "city": "北京", "region": "朝阳区",
         "delivery_duration": "30", "rating": "5"},
        {"order_id": "T002", "user_id": "U02", "merchant": "小厨快餐", "category": "麻辣烫",
         "amount": "28.0", "order_time": "2024-06-01 18:45:00", "city": "上海", "region": "浦东新区",
         "delivery_duration": "25", "rating": "4.5"},
        {"order_id": "T003", "user_id": "U01", "merchant": "老记餐厅", "category": "快餐便当",
         "amount": "42.0", "order_time": "2024-06-02 12:15:00", "city": "北京", "region": "海淀区",
         "delivery_duration": "35", "rating": "4"},
        # 负金额（异常）
        {"order_id": "T004", "user_id": "U03", "merchant": "大食府", "category": "火锅",
         "amount": "-10.0", "order_time": "2024-06-02 19:00:00", "city": "广州", "region": "天河区",
         "delivery_duration": "40", "rating": "3"},
        # 过大金额（异常）
        {"order_id": "T005", "user_id": "U04", "merchant": "味厨房", "category": "西餐",
         "amount": "99999.0", "order_time": "2024-06-03 13:00:00", "city": "深圳", "region": "南山区",
         "delivery_duration": "50", "rating": "5"},
        # 缺失金额
        {"order_id": "T006", "user_id": "U05", "merchant": "好味道", "category": "烧烤",
         "amount": "", "order_time": "2024-06-03 20:30:00", "city": "成都", "region": "锦江区",
         "delivery_duration": "45", "rating": "4"},
        # 缺失关键字段（order_time 为空）
        {"order_id": "T007", "user_id": "U06", "merchant": "优美食", "category": "面食小吃",
         "amount": "20.0", "order_time": "", "city": "杭州", "region": "西湖区",
         "delivery_duration": "20", "rating": "4.5"},
        # 重复订单号（与 T001 相同）
        {"order_id": "T001", "user_id": "U07", "merchant": "鲜食堂", "category": "川湘菜",
         "amount": "33.0", "order_time": "2024-06-04 12:00:00", "city": "北京", "region": "东城区",
         "delivery_duration": "28", "rating": "5"},
        # 空文本字段
        {"order_id": "T008", "user_id": "U08", "merchant": "", "category": "",
         "amount": "15.0", "order_time": "2024-06-04 18:00:00", "city": "", "region": "",
         "delivery_duration": "22", "rating": "3.5"},
        # U01 的第三笔订单（确保清洗后 U01 仍有 >= 2 笔，验证复购率）
        {"order_id": "T009", "user_id": "U01", "merchant": "好味道", "category": "川湘菜",
         "amount": "38.0", "order_time": "2024-06-05 19:30:00", "city": "北京", "region": "朝阳区",
         "delivery_duration": "32", "rating": "4.5"},
    ]
    return pd.DataFrame(data)


@pytest.fixture
def dirty_csv(tmp_path: Path, dirty_df: pd.DataFrame) -> Path:
    """将脏数据写入临时 CSV。"""
    csv_path = tmp_path / "test_dirty.csv"
    dirty_df.to_csv(csv_path, index=False, encoding="utf-8-sig")
    return csv_path


@pytest.fixture
def clean_df(dirty_csv: Path) -> pd.DataFrame:
    """清洗脏数据并返回结果 DataFrame。"""
    from analysis.cleaner import clean_orders

    output = dirty_csv.parent / "test_clean.csv"
    df = clean_orders(raw_csv=dirty_csv, output_csv=output)
    return df


@pytest.fixture
def tmp_output_dir(tmp_path: Path) -> Path:
    """临时输出目录。"""
    return tmp_path
