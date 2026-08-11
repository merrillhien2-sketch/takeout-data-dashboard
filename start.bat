@echo off
REM ===================================================================
REM 外卖订单数据分析与可视化大屏系统 - Windows 一键启动脚本
REM 流程：创建虚拟环境 -> 安装依赖 -> 生成数据 -> 清洗分析 -> 生成大屏 -> 启动服务
REM ===================================================================
setlocal

REM 切换到脚本所在目录（项目根目录）
cd /d "%~dp0"

echo ======================================================
echo   外卖订单数据分析与可视化大屏系统 - 一键启动
echo ======================================================

REM 1. 创建虚拟环境（使用 uv）
if not exist ".venv" (
    echo [1/6] 创建虚拟环境 (.venv) ...
    uv venv
) else (
    echo [1/6] 虚拟环境已存在，跳过创建
)

REM 激活虚拟环境
call .venv\Scripts\activate.bat

REM 2. 安装依赖
echo [2/6] 安装依赖 ...
uv pip install -r requirements.txt

REM 3. 生成模拟数据
echo [3/6] 生成模拟外卖订单数据 ...
python main.py data

REM 4. 清洗数据 + 计算指标
echo [4/6] 清洗数据与计算指标 ...
python main.py analyze

REM 5. 生成可视化大屏
echo [5/6] 生成可视化大屏 HTML ...
python main.py dashboard

REM 6. 启动 API 服务
echo [6/6] 启动 FastAPI 服务 ...
echo ======================================================
echo   大屏地址: http://127.0.0.1:8000/
echo   API 文档: http://127.0.0.1:8000/docs
echo   按 Ctrl+C 停止服务
echo ======================================================
python main.py serve

endlocal
