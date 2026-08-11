"""模拟外卖订单数据生成脚本。

使用 Faker 与随机数生成约 5000 条模拟外卖订单 CSV。
字段包括：订单号、用户ID、商家、品类、金额、下单时间、城市、区域、配送时长、评分。
城市与品类均使用中文名称，城市与 pyecharts 中国地图匹配。
"""

from __future__ import annotations

import random
from datetime import datetime, timedelta
from pathlib import Path

import pandas as pd
from faker import Faker
from loguru import logger

from config.logging_conf import setup_logging
from config.settings import settings

# Faker 中文配置
fake = Faker("zh_CN")

# 城市与其区域映射（城市名与 pyecharts 中国地图一致）
CITY_REGIONS: dict[str, list[str]] = {
    "北京": ["朝阳区", "海淀区", "东城区", "西城区", "丰台区", "通州区"],
    "上海": ["浦东新区", "黄浦区", "徐汇区", "长宁区", "静安区", "闵行区"],
    "广州": ["天河区", "越秀区", "海珠区", "荔湾区", "白云区", "番禺区"],
    "深圳": ["南山区", "福田区", "罗湖区", "宝安区", "龙岗区", "龙华区"],
    "成都": ["锦江区", "青羊区", "金牛区", "武侯区", "成华区", "高新区"],
    "杭州": ["西湖区", "上城区", "下城区", "拱墅区", "滨江区", "余杭区"],
    "武汉": ["江汉区", "武昌区", "洪山区", "汉阳区", "硚口区", "江岸区"],
    "南京": ["鼓楼区", "玄武区", "建邺区", "秦淮区", "雨花台区", "江宁区"],
    "重庆": ["渝中区", "江北区", "南岸区", "九龙坡区", "沙坪坝区", "渝北区"],
    "西安": ["雁塔区", "碑林区", "莲湖区", "未央区", "新城区", "长安区"],
    "苏州": ["姑苏区", "吴中区", "相城区", "工业园区", "高新区", "吴江区"],
    "天津": ["和平区", "南开区", "河西区", "河北区", "河东区", "北辰区"],
    "长沙": ["岳麓区", "芙蓉区", "天心区", "开福区", "雨花区", "望城区"],
    "郑州": ["金水区", "二七区", "中原区", "管城区", "惠济区", "郑东新区"],
    "青岛": ["市南区", "市北区", "李沧区", "崂山区", "城阳区", "黄岛区"],
    "厦门": ["思明区", "湖里区", "集美区", "海沧区", "同安区", "翔安区"],
    "大连": ["中山区", "西岗区", "沙河口区", "甘井子区", "高新园区", "开发区"],
    "沈阳": ["和平区", "沈河区", "大东区", "皇姑区", "铁西区", "浑南区"],
}

# 品类列表（中文）
CATEGORIES: list[str] = [
    "快餐便当", "汉堡薯条", "麻辣烫", "奶茶果汁", "烧烤",
    "火锅", "日料寿司", "西餐", "面食小吃", "甜品蛋糕",
    "川湘菜", "粤菜", "饺子馄饨", "披萨意面", "轻食沙拉",
]

# 商家名称模板
MERCHANT_PREFIX: list[str] = [
    "老", "小", "大", "正", "真", "香", "好", "优", "鲜", "味",
    "御", "皇", "金", "银", "百", "万", "千", "亿", "豪", "鼎",
]
MERCHANT_SUFFIX: list[str] = [
    "记餐厅", "厨快餐", "食府", "味道", "厨房", "食堂",
    "小馆", "大饭店", "美食", "餐厅", "外卖", "私房菜",
]


def _gen_merchant() -> str:
    """随机生成商家名称。"""
    prefix = random.choice(MERCHANT_PREFIX)
    suffix = random.choice(MERCHANT_SUFFIX)
    # 偶尔加个品类关键词
    if random.random() < 0.4:
        cat = random.choice(CATEGORIES)[:2]
        return f"{prefix}{cat}{suffix}"
    return f"{prefix}{suffix}"


def _gen_order_time(start: datetime, end: datetime) -> datetime:
    """在时间范围内随机生成下单时间（午餐/晚餐高峰权重更高）。"""
    delta = (end - start).total_seconds()
    base = start + timedelta(seconds=random.uniform(0, delta))
    # 调整小时：集中在 11-13 点（午餐）和 17-21 点（晚餐）
    hour_weights = [
        0.5, 0.3, 0.2, 0.1, 0.1, 0.2, 0.4, 0.8, 1.2, 1.5, 2.0, 4.0,  # 0-11
        5.0, 3.0, 1.8, 1.5, 1.5, 3.5, 5.0, 4.5, 3.5, 2.5, 1.5, 0.8,  # 12-23
    ]
    hour = random.choices(range(24), weights=hour_weights, k=1)[0]
    minute = random.randint(0, 59)
    second = random.randint(0, 59)
    return base.replace(hour=hour, minute=minute, second=second)


def generate_sample_data(
    rows: int | None = None,
    output_csv: Path | None = None,
    seed: int | None = None,
) -> Path:
    """生成模拟外卖订单 CSV。

    Args:
        rows: 生成条数，默认使用配置中的 sample_data_rows。
        output_csv: 输出路径，默认使用配置中的 raw_csv_path。
        seed: 随机种子，默认使用配置中的 random_seed。

    Returns:
        输出 CSV 文件路径。
    """
    rows = rows if rows is not None else settings.sample_data_rows
    output_csv = output_csv or settings.raw_csv_path
    seed = seed if seed is not None else settings.random_seed

    random.seed(seed)
    Faker.seed(seed)

    logger.info("开始生成模拟数据 | 条数={} | 种子={}", rows, seed)

    # 城市列表与权重（一线城市订单量更大）
    cities = list(CITY_REGIONS.keys())
    city_weights = [5, 5, 4, 4, 3, 3, 2, 2, 3, 2, 2, 2, 1.5, 1.5, 1.5, 1, 1, 1]

    # 预生成用户池（模拟复购）
    user_pool_size = rows // 3 + 100
    user_ids = [f"U{10000 + i}" for i in range(user_pool_size)]

    # 预生成商家池
    merchant_pool = list({_gen_merchant() for _ in range(80)})
    if len(merchant_pool) < 20:
        merchant_pool.extend([_gen_merchant() for _ in range(20)])

    # 时间范围：最近 30 天
    end_time = datetime.now().replace(microsecond=0)
    start_time = end_time - timedelta(days=30)

    records: list[dict] = []
    for i in range(rows):
        city = random.choices(cities, weights=city_weights, k=1)[0]
        region = random.choice(CITY_REGIONS[city])
        order_time = _gen_order_time(start_time, end_time)

        # 金额：正态分布，均值 35，标准差 18，下限 8
        amount = max(8.0, round(random.gauss(35, 18), 2))
        # 偶尔出现大额订单
        if random.random() < 0.05:
            amount = round(random.uniform(80, 200), 2)

        # 配送时长：15-60 分钟为主
        delivery_duration = round(random.gauss(35, 12), 1)
        delivery_duration = max(10.0, min(90.0, delivery_duration))

        # 评分：4-5 分为主，偶尔低分
        rating = round(random.choices(
            [5.0, 4.5, 4.0, 3.5, 3.0, 2.0, 1.0],
            weights=[40, 25, 18, 8, 5, 3, 1],
        )[0], 1)

        records.append({
            "order_id": f"TO{202401010000 + i}",
            "user_id": random.choice(user_ids),
            "merchant": random.choice(merchant_pool),
            "category": random.choice(CATEGORIES),
            "amount": amount,
            "order_time": order_time.strftime("%Y-%m-%d %H:%M:%S"),
            "city": city,
            "region": region,
            "delivery_duration": delivery_duration,
            "rating": rating,
        })

    # 故意注入少量脏数据以演示清洗能力
    _inject_dirty_data(records, count=rows // 50)

    df = pd.DataFrame(records)
    output_csv.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(output_csv, index=False, encoding="utf-8-sig")

    logger.info(
        "模拟数据生成完成 | 行数={} | 文件={} | 列={}",
        len(df), output_csv, list(df.columns),
    )
    return output_csv


def _inject_dirty_data(records: list[dict], count: int) -> None:
    """注入少量脏数据以演示清洗能力。

    包括：缺失值、负金额、过大金额、重复订单号。
    """
    if count < 5:
        count = 5
    n = len(records)
    for _ in range(count):
        idx = random.randint(0, n - 1)
        r = records[idx]
        op = random.choice(["null", "negative", "huge", "duplicate"])
        if op == "null":
            r["amount"] = ""  # 空值
        elif op == "negative":
            r["amount"] = -round(random.uniform(5, 50), 2)  # 负值
        elif op == "huge":
            r["amount"] = round(random.uniform(5000, 99999), 2)  # 异常大
        elif op == "duplicate":
            # 复制一条记录的订单号到另一条
            other = random.randint(0, n - 1)
            if other != idx:
                records[other]["order_id"] = r["order_id"]
    logger.info("注入脏数据 | 条数≈{}", count)


if __name__ == "__main__":
    setup_logging()
    generate_sample_data()
