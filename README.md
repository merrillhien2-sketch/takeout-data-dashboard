# 外卖订单数据分析与可视化大屏系统

一个基于 Python 的外卖订单数据分析与可视化大屏项目，涵盖数据生成、清洗、指标分析、可视化大屏与 API 服务全流程。适合作为简历项目展示。

## 项目亮点

- **全流程贯通**：模拟数据生成 -> Pandas 清洗 -> 指标分析 -> pyecharts 大屏 -> FastAPI 服务
- **可视化大屏**：折线图、热力图、中国地图、柱状图、饼图，深色科技风网格布局
- **工程化规范**：分层架构、配置管理、日志落盘、参数校验、全局异常、ORM 封装、单元测试
- **一键启动**：`start.sh` / `start.bat` 自动完成环境搭建与全流程运行

## 技术栈

| 类别       | 技术                         |
|------------|------------------------------|
| 数据处理   | pandas >= 2.2                |
| 可视化     | pyecharts >= 2.0             |
| Web 框架   | FastAPI >= 0.110 + uvicorn   |
| ORM        | SQLAlchemy 2.0 + SQLite      |
| 配置管理   | pydantic-settings            |
| 日志       | loguru                       |
| 模拟数据   | Faker                        |
| 测试       | pytest + httpx               |

## 目录结构

```
takeout-data-dashboard/
├── config/                # 配置模块
│   ├── __init__.py
│   ├── settings.py        # pydantic-settings 配置（从 .env 读取）
│   └── logging_conf.py    # loguru 日志配置（控制台 + 文件落盘）
├── data/                  # 数据目录
│   ├── raw/               # 原始样例 CSV
│   ├── processed/         # 清洗后 CSV（.gitignore）
│   └── dashboard.html     # 生成的大屏 HTML（.gitignore）
├── analysis/              # 数据分析模块
│   ├── __init__.py
│   ├── cleaner.py         # Pandas 清洗（缺失值/异常值/重复值/类型转换）
│   └── metrics.py         # 指标计算（高峰时段/客单价/复购率/排行/分布）
├── visualization/         # 可视化模块
│   ├── __init__.py
│   ├── charts.py          # pyecharts 各图表生成
│   └── dashboard.py       # 大屏组合（KPI + 网格布局）
├── api/                   # FastAPI 接口模块
│   ├── __init__.py
│   ├── main.py            # FastAPI 应用工厂（异常处理 + 日志中间件）
│   ├── routes.py          # 路由（/ /api/metrics /api/orders ...）
│   ├── schemas.py         # Pydantic 请求/响应模型
│   └── database.py        # SQLAlchemy 2.0 ORM 封装
├── scripts/               # 脚本模块
│   ├── __init__.py
│   ├── generate_sample_data.py  # 生成模拟外卖订单 CSV
│   ├── run_analysis.py           # 清洗 + 指标计算
│   └── build_dashboard.py        # 生成大屏 HTML
├── tests/                 # 单元测试
│   ├── __init__.py
│   ├── conftest.py        # pytest 夹具（脏数据构造）
│   ├── test_cleaner.py    # 清洗模块测试
│   └── test_metrics.py    # 指标模块测试
├── main.py                # 统一 CLI 入口
├── requirements.txt       # 依赖清单
├── pytest.ini             # pytest 配置
├── .env.example           # 环境变量示例（占位符）
├── .gitignore
├── start.sh               # Linux/Mac 一键启动脚本
├── start.bat              # Windows 一键启动脚本
├── README.md              # 项目说明（本文件）
└── 接口文档.md            # API 接口文档
```

## 快速开始

### 环境要求

- Python 3.10+（本项目在 3.10.12 上测试通过）
- 推荐使用 [uv](https://github.com/astral-sh/uv) 管理虚拟环境

### 一键启动

**Linux / Mac：**

```bash
chmod +x start.sh
./start.sh
```

**Windows：**

```cmd
start.bat
```

脚本会自动完成：创建虚拟环境 -> 安装依赖 -> 生成数据 -> 清洗分析 -> 生成大屏 -> 启动服务。

### 手动步骤

```bash
# 1. 创建虚拟环境并安装依赖
uv venv
uv pip install -r requirements.txt

# 2. 生成模拟数据（约 5000 条）
python main.py data

# 3. 清洗数据 + 计算指标 + 写入 SQLite
python main.py analyze

# 4. 生成可视化大屏 HTML
python main.py dashboard

# 5. 启动 API 服务
python main.py serve
```

### 一键全流程

```bash
python main.py all
```

## CLI 命令说明

| 命令              | 说明                                   |
|-------------------|----------------------------------------|
| `python main.py data`      | 生成模拟外卖订单数据（约 5000 条 CSV） |
| `python main.py analyze`   | 清洗数据 + 计算指标 + 写入数据库        |
| `python main.py dashboard` | 生成可视化大屏 HTML                    |
| `python main.py serve`     | 启动 FastAPI 服务（托管大屏 + API）    |
| `python main.py all`       | 一键执行全流程并启动服务               |

可选参数：
- `data --rows 10000 --seed 42`：自定义数据条数与随机种子
- `analyze --no-db`：跳过写入 SQLite
- `serve --host 0.0.0.0 --port 9000 --reload`：自定义服务配置

## 访问地址

服务启动后：

| 地址                  | 说明                          |
|-----------------------|-------------------------------|
| http://127.0.0.1:8000/          | 可视化大屏 HTML      |
| http://127.0.0.1:8000/api/metrics | 全部指标 JSON        |
| http://127.0.0.1:8000/api/orders  | 订单分页查询         |
| http://127.0.0.1:8000/api/health  | 健康检查             |
| http://127.0.0.1:8000/docs        | Swagger API 文档    |

## 核心功能

### 1. 数据生成（generate_sample_data.py）

使用 Faker + 随机数生成约 5000 条模拟外卖订单，包含：
- 18 个中国主要城市及其区域
- 15 个外卖品类
- 午餐/晚餐高峰时段加权分布
- 模拟复购用户（用户池约为订单数的 1/3）
- 故意注入少量脏数据（缺失值/负金额/过大金额/重复订单号）以演示清洗能力

### 2. 数据清洗（cleaner.py）

Pandas 清洗流程：
- **重复值**：按订单号去重，保留最后一条
- **缺失值**：关键字段缺失删除整行；文本字段填充默认值；数值字段填充中位数
- **异常值**：金额 <= 0 删除；过大值按 1%/99% 分位裁剪；配送时长/评分范围约束
- **类型转换**：时间解析、数值类型规范
- **衍生字段**：order_hour、weekday、order_date

### 3. 指标计算（metrics.py）

| 指标             | 说明                            |
|------------------|---------------------------------|
| 高峰时段         | 按小时统计订单量（0-23 点）     |
| 客单价           | 总金额 / 总订单数               |
| 复购率           | 下单 >= 2 次的用户占比          |
| 销量排行         | 商家/品类 Top10（按订单量降序） |
| 城市分布         | 各城市订单量与金额              |
| 区域分布         | 各区域订单量                    |
| 配送时长分布     | 按时长分箱统计 + 平均时长       |
| 评分分布         | 1-5 星分布 + 平均评分           |
| 星期×小时热力图  | 7×24 订单量矩阵                 |

### 4. 可视化大屏（charts.py + dashboard.py）

pyecharts 生成 5 类图表，组合为深色科技风大屏：
- **折线图**（全宽）：24 小时订单趋势
- **热力图**：星期 × 小时订单分布
- **中国地图**：城市订单量地理分布
- **柱状图**：商家销量排行 Top10
- **饼图**：品类销量占比
- **KPI 卡片行**：7 个核心指标数字展示

### 5. FastAPI 服务（api/）

- `GET /`：返回大屏 HTML
- `GET /api/metrics`：返回全部指标 JSON
- `GET /api/orders`：分页查询订单（支持城市/品类/商家过滤）
- `GET /api/cities`：城市列表
- `GET /api/categories`：品类列表
- `GET /api/health`：健康检查
- 全局异常处理 + 请求日志中间件 + CORS 支持
- Swagger 文档自动生成（`/docs`）

## 配置说明

复制 `.env.example` 为 `.env` 并按需修改：

```env
APP_ENV=development
API_HOST=127.0.0.1
API_PORT=8000
SAMPLE_DATA_ROWS=5000
RANDOM_SEED=42
LOG_LEVEL=INFO
LOG_FILE=logs/app.log
```

所有配置通过 pydantic-settings 管理，禁止硬编码密钥。

## 运行测试

```bash
# 运行全部测试
pytest

# 运行指定测试文件
pytest tests/test_cleaner.py
pytest tests/test_metrics.py

# 查看详细输出
pytest -v
```

## 项目自检

```bash
# 编译检查
python -m compileall .

# 冒烟测试（生成数据 -> 清洗 -> 指标 -> 大屏 -> API 启动）
python main.py data
python main.py analyze --no-db
python main.py dashboard
python main.py serve  # 手动 Ctrl+C 关闭
```

## 已知限制

1. 模拟数据为随机生成，不反映真实业务规律
2. SQLite 单文件数据库，适合演示，不适合高并发生产场景
3. 大屏 HTML 依赖 CDN 加载 echarts.js，需联网才能渲染图表
4. 中国地图城市名称需与 pyecharts 内置地图匹配
5. 配置中的 SECRET_KEY 仅为占位符，本项目不使用真实外部服务

## 许可证

本项目仅用于学习与简历展示，无商业用途。
