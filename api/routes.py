"""FastAPI 路由模块。

提供以下接口：
- GET /            返回大屏 HTML
- GET /api/metrics 返回全部指标 JSON
- GET /api/orders  分页查询订单
- GET /api/health  健康检查
"""

from __future__ import annotations

from pathlib import Path

import pandas as pd
from fastapi import APIRouter, Depends, HTTPException, Query, Request
from fastapi.responses import HTMLResponse, JSONResponse
from loguru import logger

from analysis.metrics import compute_all_metrics, load_clean_data
from api.schemas import HealthResponse, MetricsResponse, OrderItem, OrderListResponse
from config.settings import settings

router = APIRouter()

# 应用版本
APP_VERSION = "1.0.0"


@router.get("/", response_class=HTMLResponse, summary="可视化大屏")
async def dashboard_page() -> HTMLResponse:
    """返回可视化大屏 HTML 页面。"""
    html_path = settings.dashboard_html_path
    if not html_path.exists():
        logger.warning("大屏 HTML 不存在，提示先生成 | path={}", html_path)
        return HTMLResponse(
            content="<html><body><h2>大屏尚未生成</h2>"
                    "<p>请先运行 <code>python main.py dashboard</code> 生成大屏 HTML。</p>"
                    "<p>或访问 <a href='/api/metrics'>/api/metrics</a> 查看指标 JSON。</p>"
                    "</body></html>",
            status_code=200,
        )
    logger.info("返回大屏 HTML | path={}", html_path)
    return HTMLResponse(content=html_path.read_text(encoding="utf-8"))


@router.get("/api/health", response_model=HealthResponse, summary="健康检查")
async def health() -> HealthResponse:
    """健康检查接口。"""
    return HealthResponse(status="ok", app_name=settings.app_name, version=APP_VERSION)


@router.get("/api/metrics", response_model=MetricsResponse, summary="全部指标")
async def get_metrics() -> dict:
    """返回全部计算指标 JSON。"""
    try:
        df = load_clean_data()
        metrics = compute_all_metrics(df)
        logger.info("返回指标数据 | 指标项数={}", len(metrics))
        return metrics
    except FileNotFoundError as e:
        logger.error("指标查询失败 | 错误={}", e)
        raise HTTPException(status_code=404, detail=str(e))


@router.get("/api/orders", response_model=OrderListResponse, summary="订单分页查询")
async def get_orders(
    page: int = Query(default=1, ge=1, description="页码，从 1 开始"),
    page_size: int = Query(default=20, ge=1, le=100, description="每页条数 1-100"),
    city: str | None = Query(default=None, description="按城市过滤"),
    category: str | None = Query(default=None, description="按品类过滤"),
    merchant: str | None = Query(default=None, description="按商家过滤"),
) -> dict:
    """分页查询订单列表，支持按城市/品类/商家过滤。"""
    try:
        df = load_clean_data()
    except FileNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))

    # 过滤
    if city:
        df = df[df["city"] == city]
    if category:
        df = df[df["category"] == category]
    if merchant:
        df = df[df["merchant"] == merchant]

    total = len(df)
    start = (page - 1) * page_size
    end = start + page_size
    page_df = df.iloc[start:end]

    items = [
        OrderItem(
            order_id=str(row["order_id"]),
            user_id=str(row["user_id"]),
            merchant=str(row["merchant"]),
            category=str(row["category"]),
            amount=float(row["amount"]),
            order_time=pd.to_datetime(row["order_time"]).to_pydatetime(),
            city=str(row["city"]),
            region=str(row["region"]),
            delivery_duration=float(row["delivery_duration"]),
            rating=float(row["rating"]),
        )
        for _, row in page_df.iterrows()
    ]

    logger.info("订单分页查询 | page={} size={} total={}", page, page_size, total)
    return {
        "total": total,
        "page": page,
        "page_size": page_size,
        "items": items,
    }


@router.get("/api/cities", summary="城市列表")
async def get_cities() -> dict:
    """返回所有城市及订单数，供前端筛选下拉使用。"""
    df = load_clean_data()
    cities = df.groupby("city").size().sort_values(ascending=False)
    return {
        "cities": [
            {"name": name, "order_count": int(count)}
            for name, count in cities.items()
        ]
    }


@router.get("/api/categories", summary="品类列表")
async def get_categories() -> dict:
    """返回所有品类及订单数。"""
    df = load_clean_data()
    cats = df.groupby("category").size().sort_values(ascending=False)
    return {
        "categories": [
            {"name": name, "order_count": int(count)}
            for name, count in cats.items()
        ]
    }
