"""外卖订单数据分析与可视化大屏系统 - 统一入口。

CLI 命令：
  python main.py data      生成模拟外卖订单数据（约 5000 条 CSV）
  python main.py analyze   清洗数据 + 计算指标 + 写入数据库
  python main.py dashboard 生成可视化大屏 HTML
  python main.py serve     启动 FastAPI 服务（托管大屏 + 数据接口）
  python main.py all       一键执行 data -> analyze -> dashboard -> serve

使用 argparse 实现命令行解析，兼容 Python 3.10+。
"""

from __future__ import annotations

import argparse
import sys

from config.logging_conf import setup_logging
from config.settings import settings
from loguru import logger


def cmd_data(args: argparse.Namespace) -> None:
    """生成模拟数据。"""
    from scripts.generate_sample_data import generate_sample_data

    generate_sample_data(rows=args.rows, seed=args.seed)
    logger.info("数据生成完毕，可执行 `python main.py analyze` 进行分析")


def cmd_analyze(args: argparse.Namespace) -> None:
    """清洗 + 计算指标。"""
    from scripts.run_analysis import run_analysis

    run_analysis(store_db=not args.no_db)


def cmd_dashboard(args: argparse.Namespace) -> None:
    """生成大屏 HTML。"""
    from scripts.build_dashboard import build_dashboard_script

    build_dashboard_script()


def cmd_serve(args: argparse.Namespace) -> None:
    """启动 FastAPI 服务。"""
    import uvicorn

    host = args.host or settings.api_host
    port = args.port or settings.api_port

    logger.info("启动 FastAPI 服务 | host={} port={}", host, port)
    logger.info("大屏地址: http://{}:{}/", host, port)
    logger.info("API 文档: http://{}:{}/docs", host, port)

    uvicorn.run(
        "api.main:app",
        host=host,
        port=port,
        reload=args.reload,
        log_level="info",
    )


def cmd_all(args: argparse.Namespace) -> None:
    """一键执行完整流程。"""
    logger.info("执行完整流程: data -> analyze -> dashboard")
    from scripts.generate_sample_data import generate_sample_data
    from scripts.run_analysis import run_analysis
    from scripts.build_dashboard import build_dashboard_script

    generate_sample_data()
    run_analysis(store_db=True)
    build_dashboard_script()
    logger.info("数据与分析流程完成，即将启动服务...")

    import uvicorn

    uvicorn.run(
        "api.main:app",
        host=args.host or settings.api_host,
        port=args.port or settings.api_port,
        log_level="info",
    )


def build_parser() -> argparse.ArgumentParser:
    """构建命令行参数解析器。"""
    parser = argparse.ArgumentParser(
        prog="takeout-dashboard",
        description="外卖订单数据分析与可视化大屏系统",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  python main.py data          生成模拟数据
  python main.py analyze       清洗与分析
  python main.py dashboard     生成大屏
  python main.py serve         启动 API 服务
  python main.py all           一键全流程
        """,
    )
    subparsers = parser.add_subparsers(dest="command", help="可用命令")

    # data
    p_data = subparsers.add_parser("data", help="生成模拟外卖订单数据")
    p_data.add_argument("--rows", type=int, default=None, help="生成条数（默认 5000）")
    p_data.add_argument("--seed", type=int, default=None, help="随机种子")
    p_data.set_defaults(func=cmd_data)

    # analyze
    p_analyze = subparsers.add_parser("analyze", help="清洗数据 + 计算指标")
    p_analyze.add_argument("--no-db", action="store_true", help="跳过写入 SQLite 数据库")
    p_analyze.set_defaults(func=cmd_analyze)

    # dashboard
    p_dash = subparsers.add_parser("dashboard", help="生成可视化大屏 HTML")
    p_dash.set_defaults(func=cmd_dashboard)

    # serve
    p_serve = subparsers.add_parser("serve", help="启动 FastAPI 服务")
    p_serve.add_argument("--host", type=str, default=None, help="监听地址")
    p_serve.add_argument("--port", type=int, default=None, help="监听端口")
    p_serve.add_argument("--reload", action="store_true", help="热重载（开发模式）")
    p_serve.set_defaults(func=cmd_serve)

    # all
    p_all = subparsers.add_parser("all", help="一键执行全流程并启动服务")
    p_all.add_argument("--host", type=str, default=None, help="监听地址")
    p_all.add_argument("--port", type=int, default=None, help="监听端口")
    p_all.set_defaults(func=cmd_all)

    return parser


def main() -> None:
    """主入口函数。"""
    setup_logging()

    parser = build_parser()
    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        sys.exit(0)

    logger.info("执行命令: {}", args.command)
    args.func(args)


if __name__ == "__main__":
    main()
