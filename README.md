# 🥚 蛋蛋交易系统

AI 驱动的 A 股模拟量化交易系统，全自动选股、交易、复盘、策略进化。

## 系统架构

```
Flask API (Blueprint 模块化)
├── routes/trading.py    — 交易执行（买入/卖出/T+1检查）
├── routes/market.py     — 行情数据（腾讯API + TTL缓存）
├── routes/strategy.py   — 策略管理 + 校准 + 快照 + 反思
├── routes/analysis.py   — AI 策略分析
├── routes/engine.py     — 选股引擎（尾盘扫描/早盘卖出）
├── routes/review.py     — 复盘日志
├── routes/system.py     — 系统状态 + 预警
├── routes/proxy.py      — 外部API代理
├── services/            — 缓存/行情/校准/快照/反思
├── strategies/          — 多策略模块（一夜持股法/价值投资/趋势跟踪）
├── buffett_analyzer.py  — 巴菲特价值分析（TTM年化ROE）
├── value_screener.py    — 价值投资全市场扫描器
├── trend_screener.py    — 趋势跟踪全市场扫描器
└── templates/           — Dashboard（Three.js 入场动画 + Alpine.js）
```

## 核心功能

| 模块 | 说明 |
|------|------|
| 📊 多策略并行 | 一夜持股法 / 价值投资 / 趋势跟踪，各独立¥100,000资金池 |
| 🔍 全市场扫盘 | 三策略均具备5000+只全市场扫描能力（两步筛选法） |
| 🤖 全自动交易 | 选股→买入→持仓管理→卖出，全流程无人干预 |
| 🎯 AI 校准 | 基于历史交易自动优化策略参数（胜率/盈亏比分析） |
| 📸 策略快照 | 每次参数变更保存版本，支持对比回溯 |
| 🔄 自动反思 | 每周分析执行质量，检测止损及时性/T+1违规 |
| 📈 实时行情 | 腾讯行情API + TTL缓存，支持大盘指数/个股/批量查询 |
| 📝 复盘系统 | 每日自动复盘 + 手动记录，分页浏览 |
| 🛡️ 风控 | 多级止损止盈 / T+1检查 / 策略资金隔离 |

## 交易策略

### 一夜持股法 v2.3（短线主力）
- **全市场扫描**：腾讯API实时行情扫描5000+只，7条件全满足才买
- **买入条件**：涨幅3%-5%、换手率3%-10%、RSI<65、量比>1.5x、流通市值50-200亿、站上分时均价线、强于大盘
- **买入时间**：14:50-14:55 尾盘
- **卖出时间**：次日 09:30-10:30 冲高即走
- **止损**：-2% 无条件 / 回撤-2% / 低开15分钟无反弹

### 价值投资 v2.0（中线）
- **全市场扫描**：两步筛选法（腾讯PE≤20快筛→深度财务分析），21分钟扫完全市场
- **选股条件**：PE≤20、PEG≤1.5（PE≤10免检）、ROE≥12%(TTM年化)、营收利润双增长、负债率≤65%、评分≥50/80
- **持仓规则**：最多同时持有3只，每只1/3资金（~¥33,000）
- **止盈**：目标PE=28
- **止损**：-8% 无条件
- **持有周期**：最长90天

### 趋势跟踪 v2.0（波段）
- **全市场扫描**：两步筛选法（腾讯强势股快筛→多因子趋势评分），10-15分钟
- **选股条件**：多因子评分≥55/100（动量30%+成交量20%+均线20%+MACD15%+RSI15%）
- **买入确认**：K线形态确认 + RSI不过热 + 涨停冷却期
- **止盈**：+12%
- **止损**：-6%（ATR动态）/ 高位回撤-4%
- **持有周期**：最长14天

## 全市场扫描器

三策略均采用**两步筛选法**，兼顾速度与精度：

| 扫描器 | Step1 快筛 | Step2 深度分析 | 总耗时 |
|--------|-----------|---------------|--------|
| `value_screener.py` | 腾讯API筛PE≤20（5252→596只） | akshare财务数据+巴菲特评分 | ~21分钟 |
| `trend_screener.py` | 腾讯API筛强势股（5252→200-400只） | 多因子趋势评分（K线+均线+MACD） | ~10-15分钟 |
| 一夜持股法(内置) | 腾讯API全市场行情 | 7条件实时筛选 | ~15秒 |

## 快速启动

```bash
cd sim_trading

# 创建虚拟环境
python3 -m venv venv
source venv/bin/activate

# 安装依赖
pip install -r requirements.txt

# 启动服务
gunicorn -w 1 -b 0.0.0.0:80 app:app --timeout 300
```

访问 http://your-server/

## API 接口

| 接口 | 方法 | 说明 |
|------|------|------|
| `/api/portfolio` | GET | 账户 + 持仓（支持 ?strategy_id= 过滤） |
| `/api/trades` | GET | 交易记录（分页） |
| `/api/trade` | POST | 执行买卖 |
| `/api/stats` | GET | 交易统计 |
| `/api/equity` | GET | 净值曲线 |
| `/api/daily` | GET | 复盘日志（分页） |
| `/api/review` | POST | 添加复盘 |
| `/api/index` | GET | 大盘指数 + MA5/MA10 |
| `/api/quote/<code>` | GET | 个股行情 |
| `/api/quotes/batch` | GET | 批量持仓股行情 |
| `/api/market/top` | GET | 热门股票 |
| `/api/market/fullscan` | GET | 全市场扫盘（?mode=overnight） |
| `/api/strategies` | GET | 策略列表 |
| `/api/strategies/<id>` | GET | 策略详情 |
| `/api/strategies/<id>/calibrate` | POST | 运行策略校准 |
| `/api/strategies/<id>/snapshots` | GET | 策略参数快照 |
| `/api/reflection` | POST | 运行交易反思 |
| `/api/analyze/<code>` | GET | AI 策略分析 |

## 技术栈

- **后端**: Flask 3.x + Gunicorn + Blueprint 模块化（8个路由模块）
- **数据库**: SQLite（7张表 + 索引）
- **行情**: 腾讯行情API（GBK编码 + TTL缓存）
- **财务数据**: AKShare（财报/ROE/PEG/负债率）
- **前端**: Alpine.js + ECharts + Three.js（粒子入场动画）
- **样式**: Tailwind CSS + 深色主题（移动端响应式）
- **定时任务**: OpenClaw Cron（7个任务）
- **部署**: 腾讯云 VPS + systemd 守护

## 项目结构

```
sim_trading/
├── app.py                # 入口（56行）
├── config.py             # 集中配置管理
├── database.py           # 数据库层
├── buffett_analyzer.py   # 巴菲特价值分析（TTM年化ROE）
├── value_screener.py     # 价值投资全市场扫描器
├── trend_screener.py     # 趋势跟踪全市场扫描器
├── requirements.txt      # 依赖
├── routes/               # 8个 Blueprint 路由模块
│   ├── trading.py        # 交易执行
│   ├── market.py         # 行情数据
│   ├── strategy.py       # 策略管理
│   ├── analysis.py       # AI分析
│   ├── engine.py         # 选股引擎
│   ├── review.py         # 复盘日志
│   ├── system.py         # 系统状态
│   └── proxy.py          # 外部代理
├── services/             # 服务层
│   ├── cache_service.py  # TTL缓存
│   ├── quote_service.py  # 腾讯行情
│   ├── calibration.py    # 策略校准
│   ├── snapshot.py       # 参数快照
│   └── reflection.py     # 交易反思
├── strategies/           # 策略模块
│   ├── __init__.py       # BaseStrategy + Registry
│   ├── overnight_strategy.py   # 一夜持股法
│   ├── overnight_v2.py         # 一夜持股法v2（AKShare版）
│   ├── value_strategy.py       # 价值投资
│   └── trend_strategy.py       # 趋势跟踪
├── openclaw/             # 工具模块
├── trading/              # 策略管理器
├── templates/            # 前端模板
└── data/                 # SQLite 数据库
```

## 自动化任务（7个 Cron）

| 任务 | 时间 | 说明 |
|------|------|------|
| 尾盘选股扫描 | 14:50 周一至周五 | 一夜持股法全市场扫盘 |
| 尾盘买入执行 | 14:55 周一至周五 | 对扫描结果执行买入 |
| 早盘卖出扫描 | 09:30-10:30 每5分钟 | 一夜持股法持仓冲高卖出 |
| 趋势跟踪扫描 | 10:00 周一至周五 | 全市场趋势扫描+买卖决策 |
| 价值投资扫描 | 09:30 每周一 | 全市场价值扫描+持仓管理 |
| 每日复盘 | 15:30 周一至周五 | 多策略当日交易分析 |
| 每周反思+校准 | 16:00 周五 | 策略参数自动优化 |

## 运营数据

- **初始资金**: ¥300,000（三策略各¥100,000）
- **累计交易**: 29笔
- **胜率**: 53.85%
- **净利润**: ¥3,786
- **总资产**: ¥303,132

---

*由蛋蛋（AI）全权运营，自主决策、自主进化。* 🥚
