"""大屏构建脚本。

执行可视化大屏 HTML 生成流程：
1. 加载清洗后数据
2. 计算全部指标
3. 调用 dashboard 模块组合生成大屏 HTML
"""

from __future__ import annotations

from pathlib import Path

from loguru import logger

from config.logging_conf import setup_logging
from config.settings import settings
from visualization.dashboard import build_dashboard


def build_dashboard_script(
    output_html: Path | None = None,
) -> Path:
    """构建可视化大屏 HTML。

    Args:
        output_html: 输出 HTML 路径，默认使用配置中的 dashboard_html_path。

    Returns:
        生成的大屏 HTML 文件路径。
    """
    setup_logging()
    logger.info("=" * 60)
    logger.info("开始构建可视化大屏")
    logger.info("=" * 60)

    html_path = build_dashboard(output_html=output_html)

    logger.info("大屏构建完成 | 文件={}", html_path)
    logger.info("可在浏览器打开查看，或运行 `python main.py serve` 通过 FastAPI 访问")
    return html_path


if __name__ == "__main__":
    build_dashboard_script()
