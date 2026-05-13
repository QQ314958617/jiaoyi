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
└── templates/           — Dashboard（Three.js 入场动画 + Alpine.js）
```

## 核心功能

| 模块 | 说明 |
|------|------|
| 📊 多策略并行 | 一夜持股法 / 价值投资 / 趋势跟踪，各独立资金池 |
| 🤖 全自动交易 | 尾盘选股(14:50) → 买入 → 次日早盘卖出(09:30-10:30) |
| 🎯 AI 校准 | 基于历史交易自动优化策略参数（胜率/盈亏比分析） |
| 📸 策略快照 | 每次参数变更保存版本，支持对比回溯 |
| 🔄 自动反思 | 每周分析执行质量，检测止损及时性/T+1违规 |
| 📈 实时行情 | 腾讯行情API + TTL缓存，支持大盘指数/个股/批量查询 |
| 📝 复盘系统 | 每日自动复盘 + 手动记录，分页浏览 |
| 🛡️ 风控 | 止损-2% / 止盈+5%~8% / 回撤-2% / T+1检查 |

## 交易策略

### 一夜持股法 v2.3（主力策略）
- **买入条件**：涨幅3%-5%、换手率3%-10%、RSI<65、量比>1.5x、流通市值50-200亿
- **买入时间**：14:50-14:55 尾盘
- **卖出时间**：次日 09:30-10:30 冲高即走
- **止损**：-2% 无条件

### 价值投资
- PE<15、ROE>15%、资产负债率<50%
- 持有周期 1-3 个月

### 趋势跟踪
- MA20 上穿 MA60、量比>1.5x、近5日涨幅3%-10%
- 持有周期 1-2 周

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
| `/api/portfolio` | GET | 账户 + 持仓 |
| `/api/trades` | GET | 交易记录（分页） |
| `/api/trade` | POST | 执行买卖 |
| `/api/stats` | GET | 交易统计 |
| `/api/equity` | GET | 净值曲线 |
| `/api/daily` | GET | 复盘日志（分页） |
| `/api/review` | POST | 添加复盘 |
| `/api/index` | GET | 大盘指数 + MA |
| `/api/quote/<code>` | GET | 个股行情 |
| `/api/strategies` | GET | 策略列表 |
| `/api/strategies/<id>/calibrate` | POST | 运行策略校准 |
| `/api/strategies/<id>/snapshots` | GET | 策略参数快照 |
| `/api/reflection` | POST | 运行交易反思 |
| `/api/market/top` | GET | 热门股票 |
| `/api/analyze/<code>` | GET | AI 策略分析 |

## 技术栈

- **后端**: Flask 3.x + Gunicorn + Blueprint 模块化
- **数据库**: SQLite（7张表 + 5个索引）
- **行情**: 腾讯行情API（GBK编码）
- **前端**: Alpine.js + ECharts + Three.js（粒子入场动画）
- **样式**: Tailwind CSS + 深色主题
- **定时任务**: OpenClaw Cron（6个任务）
- **部署**: 腾讯云 VPS

## 项目结构

```
sim_trading/
├── app.py              # 入口（56行）
├── config.py           # 配置
├── database.py         # 数据库层
├── requirements.txt    # 依赖
├── routes/             # 8个 Blueprint 路由模块
├── services/           # 服务层（缓存/行情/校准/快照/反思）
├── strategies/         # 策略模块
├── openclaw/           # 工具模块（指标/预警/状态）
├── templates/          # 前端模板
├── trading/            # 策略管理
└── data/               # SQLite 数据库
```

## 自动化任务

| 任务 | 时间 | 说明 |
|------|------|------|
| 尾盘选股扫描 | 14:25 周一至周五 | 扫描符合条件的个股 |
| 尾盘买入执行 | 14:45 周一至周五 | 对扫描结果执行买入 |
| 早盘卖出扫描 | 09:30-10:30 每5分钟 | 持仓时冲高卖出 |
| 每日复盘 | 15:30 周一至周五 | 当日交易分析 |
| 每周反思+校准 | 16:00 周五 | 策略参数自动优化 |

## 运营数据

- **初始资金**: ¥300,000（三策略各¥100,000）
- **累计交易**: 27笔
- **胜率**: 53.85%
- **净利润**: ¥3,786

---

*由蛋蛋（AI）全权运营，自主决策、自主进化。*
