"""FastAPI 应用工厂。

创建 FastAPI 应用实例，注册路由、全局异常处理与日志中间件。
"""

from __future__ import annotations

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from loguru import logger

from api.routes import APP_VERSION, router
from config.logging_conf import setup_logging
from config.settings import settings


def create_app() -> FastAPI:
    """创建并配置 FastAPI 应用。"""
    # 初始化日志
    setup_logging()

    app = FastAPI(
        title=settings.app_name,
        description="外卖订单数据分析与可视化大屏系统 API",
        version=APP_VERSION,
        docs_url="/docs",
        redoc_url="/redoc",
    )

    # CORS 中间件（开发环境允许跨域）
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # ---- 请求日志中间件 ----
    @app.middleware("http")
    async def log_requests(request: Request, call_next):
        """记录每个请求的方法、路径与耗时。"""
        logger.info("请求 | {} {}", request.method, request.url.path)
        response = await call_next(request)
        logger.info(
            "响应 | {} {} | status={}",
            request.method, request.url.path, response.status_code,
        )
        return response

    # ---- 全局异常处理 ----
    @app.exception_handler(Exception)
    async def global_exception_handler(request: Request, exc: Exception):
        """捕获未处理异常，返回 500 与友好错误信息，并记录日志。"""
        logger.exception(
            "未处理异常 | {} {} | 错误={}",
            request.method, request.url.path, exc,
        )
        return JSONResponse(
            status_code=500,
            content={
                "detail": "服务器内部错误，请稍后重试",
                "error_type": type(exc).__name__,
            },
        )

    @app.exception_handler(FileNotFoundError)
    async def file_not_found_handler(request: Request, exc: FileNotFoundError):
        """文件不存在异常处理。"""
        logger.warning("文件不存在 | {} | {}", request.url.path, exc)
        return JSONResponse(
            status_code=404,
            content={"detail": str(exc), "error_type": "FileNotFoundError"},
        )

    # 注册路由
    app.include_router(router)

    logger.info("FastAPI 应用创建完成 | 版本={}", APP_VERSION)
    return app


# 模块级应用实例（供 uvicorn 直接引用）
app: FastAPI = create_app()
