"""API 数据模型（Pydantic schemas）。

定义请求参数校验与响应数据结构。
"""

from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


# ---- 请求参数 ----

class PaginationParams(BaseModel):
    """分页查询参数。"""

    page: int = Field(default=1, ge=1, description="页码，从 1 开始")
    page_size: int = Field(default=20, ge=1, le=100, description="每页条数，1-100")
    city: str | None = Field(default=None, description="按城市过滤")
    category: str | None = Field(default=None, description="按品类过滤")
    merchant: str | None = Field(default=None, description="按商家过滤")


# ---- 响应模型 ----

class OrderItem(BaseModel):
    """单条订单响应。"""

    order_id: str
    user_id: str
    merchant: str
    category: str
    amount: float
    order_time: datetime
    city: str
    region: str
    delivery_duration: float
    rating: float


class OrderListResponse(BaseModel):
    """订单分页列表响应。"""

    total: int
    page: int
    page_size: int
    items: list[OrderItem]


class MetricsResponse(BaseModel):
    """指标汇总响应。"""

    overview: dict[str, Any]
    peak_hours: dict[str, Any]
    average_order_value: dict[str, Any]
    repurchase_rate: dict[str, Any]
    merchant_ranking: dict[str, Any]
    category_ranking: dict[str, Any]
    city_distribution: dict[str, Any]
    region_distribution: dict[str, Any]
    delivery_duration_distribution: dict[str, Any]
    rating_distribution: dict[str, Any]
    weekday_hour_heatmap: dict[str, Any]


class HealthResponse(BaseModel):
    """健康检查响应。"""

    status: str
    app_name: str
    version: str


class ErrorResponse(BaseModel):
    """统一错误响应。"""

    detail: str
    error_type: str
