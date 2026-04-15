# 蛋蛋交易系统升级方案 v3.0

> 目标：从"能用的一夜持股法"升级为"专业级个人量化交易系统"
> 设计时间：2026-04-15
> 实施周期：预估4-6周（边用边迭代）

---

## 一、系统架构总览

```
┌─────────────────────────────────────────────────┐
│                  AI工作室（前端）                   │
│          状态推送 / 净值曲线 / 交易日志              │
└──────────────────────┬──────────────────────────┘
                       │
┌──────────────────────▼──────────────────────────┐
│              Flask API 层 (app.py)                │
│  /api/portfolio  /api/trade  /api/screen         │
│  /api/backtest   /api/sentiment  /api/fundflow   │
└──────────────────────┬──────────────────────────┘
                       │
┌──────────────────────▼──────────────────────────┐
│                  核心引擎层                        │
│                                                   │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐         │
│  │ 选股引擎  │ │ 回测引擎  │ │ 风控引擎  │         │
│  │ screener │ │backtester│ │ risk_mgr │         │
│  └──────────┘ └──────────┘ └──────────┘         │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐         │
│  │ 行情引擎  │ │ 资金流引擎│ │ 情绪引擎  │         │
│  │  quotes  │ │ fundflow │ │sentiment │         │
│  └──────────┘ └──────────┘ └──────────┘         │
└──────────────────────┬──────────────────────────┘
                       │
┌──────────────────────▼──────────────────────────┐
│              数据层 (SQLite + 缓存)                │
│  trades / positions / equity_curve / backtest     │
│  fund_flow / sector_data / sentiment_data         │
└─────────────────────────────────────────────────┘
```

---

## 二、模块详细设计

### 模块1：回测引擎（P0 🔴 最高优先级）

**为什么要做**：不知道策略胜率就是在碰运气。回测用历史数据验证，能量化策略到底行不行。

#### 1.1 核心功能
- 读取历史行情数据（akshare日K线）
- 模拟一夜持股法在历史上的每次交易
- 输出：胜率、盈亏比、最大回撤、夏普比率、年化收益

#### 1.2 回测参数
```python
class BacktestConfig:
    # 回测时间范围
    start_date: str = "2024-01-01"
    end_date: str = "2026-04-15"

    # 策略参数（复用overnight_screener.py的Config）
    rise_min: float = 3.0
    rise_max: float = 5.0
    rsi_min: int = 40
    rsi_max: int = 65
    turnover_min: float = 3.0
    turnover_max: float = 10.0
    volume_ratio_min: float = 1.5

    # 交易参数
    initial_capital: float = 50000
    commission_rate: float = 0.0003  # 佣金0.03%
    stamp_tax_rate: float = 0.0005   # 印花税0.05%（仅卖出）
    slippage: float = 0.001          # 滑点0.1%

    # 卖出参数
    stop_loss: float = -3.0          # 止损-3%
    take_profit: float = 3.0         # 止盈+3%（冲高即走）
```

#### 1.3 回测流程
```
for 每个交易日 in 历史日期:
    1. 获取当日全市场行情快照
    2. 用选股条件筛选（涨幅/换手率/RSI/成交量/市值）
    3. 如果有符合条件的股票：
       - 模拟买入（扣手续费）
       - 记录买入价格
    4. 如果有持仓：
       - 检查是否触发止损/止盈
       - 检查次日是否应该卖出
       - 模拟卖出（扣手续费+印花税）
    5. 记录当日净值
```

#### 1.4 输出报告
```
📊 一夜持股法回测报告
━━━━━━━━━━━━━━━━━━━
回测区间：2024-01-01 ~ 2026-04-15（525个交易日）
初始资金：¥50,000
最终资金：¥XX,XXX

📈 绩效指标
├─ 总收益率：+XX.XX%
├─ 年化收益：+XX.XX%
├─ 最大回撤：-XX.XX%
├─ 夏普比率：X.XX
├─ 胜率：XX.X%（XX胜/XX负）
├─ 盈亏比：X.XX:1
├─ 平均盈利：+¥XXX
├─ 平均亏损：-¥XXX
└─ 最长连胜：X次 | 最长连亏：X次

📊 月度收益分布
├─ 1月：+X.X%  2月：-X.X%  ...
└─ 最佳月：YYYY-MM (+XX%)
    最差月：YYYY-MM (-XX%)

🔍 参数敏感性
├─ 涨幅3%-4% vs 4%-5%：胜率 XX% vs XX%
├─ RSI 40-55 vs 55-65：胜率 XX% vs XX%
└─ 换手率3%-6% vs 6%-10%：胜率 XX% vs XX%
```

#### 1.5 API接口
```
GET  /api/backtest/run         运行回测
GET  /api/backtest/result      获取上次回测结果
GET  /api/backtest/optimize    参数优化（网格搜索）
```

#### 1.6 文件结构
```
sim_trading/
├── backtester.py          # 回测引擎主模块
├── backtest_report.py     # 报告生成
├── backtest_optimizer.py  # 参数优化
└── backtest_data.py       # 历史数据加载
```

#### 1.7 实现要点
- **数据源**：用akshare `stock_zh_a_hist` 获取历史日K线
- **速度优化**：预加载全市场数据到内存，避免逐只查询
- **防未来函数**：严格按日期顺序回测，不能看到"明天"的数据
- **参数优化**：网格搜索各参数组合，找到最优区间

---

### 模块2：资金流向引擎（P0 🔴）

**为什么要做**：主力资金流入的股票次日溢价概率高，资金流出的容易被砸盘。

#### 2.1 数据来源
- akshare `stock_individual_fund_flow` — 个股资金流向
- akshare `stock_market_fund_flow` — 大盘资金流向
- 北向资金（沪深港通）

#### 2.2 筛选条件（加入选股流程）
```python
class FundFlowFilter:
    # 主力净流入
    main_net_inflow_min: float = 0  # 主力净流入>0（正值）

    # 超大单+大单占比
    big_order_ratio_min: float = 0.3  # 超大单+大单占成交量>30%

    # 北向资金
    northbound_flow: bool = True  # 北向净买入加分
```

#### 2.3 API接口
```
GET /api/fundflow/<code>       个股资金流向
GET /api/fundflow/market       大盘资金流向
GET /api/fundflow/northbound   北向资金
```

---

### 模块3：板块联动引擎（P0 🔴）

**为什么要做**：热点板块内的个股成功率远高于冷门板块。板块效应是一夜持股法最大的alpha来源之一。

#### 3.1 数据来源
- akshare `stock_board_industry_name_em` — 行业板块行情
- akshare `stock_board_concept_name_em` — 概念板块行情

#### 3.2 功能
```python
class SectorEngine:
    def get_hot_sectors(self, top_n=5):
        """获取当日涨幅前N的热门板块"""

    def get_sector_stocks(self, sector_name):
        """获取板块内个股"""

    def is_stock_in_hot_sector(self, code):
        """判断股票是否在热门板块内"""
```

#### 3.3 选股加分机制
- 股票在当日涨幅前3的板块内 → 评分+20
- 股票是板块龙头（涨幅最高）→ 评分+30
- 股票不在任何热门板块内 → 评分-10

---

### 模块4：市场情绪引擎（P1 🟡）

**为什么要做**：市场情绪差时（百股跌停），即使个股信号再好也可能被拖下水。

#### 4.1 情绪指标
```python
class SentimentEngine:
    def calculate(self):
        return {
            "limit_up_count": 涨停数,
            "limit_down_count": 跌停数,
            "up_down_ratio": 上涨数/下跌数,
            "continuous_limit_up": 最高连板数,
            "active_stocks": 活跃股数,
            "sentiment_score": 0-100综合评分,
        }
```

#### 4.2 情绪决策规则
| 情绪评分 | 状态 | 操作建议 |
|---------|------|---------|
| 80-100 | 极度亢奋 | 可以加仓 |
| 60-80 | 偏强 | 正常操作 |
| 40-60 | 中性 | 正常操作 |
| 20-40 | 偏弱 | 减仓/观望 |
| 0-20 | 极度悲观 | 禁止买入 |

#### 4.3 API接口
```
GET /api/sentiment           当前市场情绪
GET /api/sentiment/history   情绪历史曲线
```

---

### 模块5：ATR动态止损（P1 🟡）

**为什么要做**：不同股票波动率差异大，固定-3%止损对高波动股太紧（频繁触发），对低波动股太宽（亏损大）。

#### 5.1 计算方法
```python
def calculate_atr_stop_loss(code, period=14):
    """基于ATR计算动态止损位"""
    hist = get_history(code, period + 5)
    atr = calculate_atr(hist, period)  # 14日ATR
    current_price = hist['close'][-1]

    # 止损 = 当前价格 - 2倍ATR
    stop_loss_price = current_price - 2 * atr
    stop_loss_pct = (stop_loss_price - current_price) / current_price * 100

    return stop_loss_pct  # 如 -2.5% 或 -4.2%
```

#### 5.2 与固定止损结合
```python
# 取两者中较宽松的（给波动大的股票更多空间）
atr_stop = calculate_atr_stop_loss(code)
fixed_stop = -3.0
final_stop = max(atr_stop, fixed_stop)  # 如 -3% vs -4.2% → 取-3%
```

---

### 模块6：净值曲线可视化（P1 🟡）

**为什么要做**：数字不如图表直观，一张净值曲线图胜过千言万语。

#### 6.1 API接口
```
GET /api/equity/chart         净值曲线数据（JSON）
GET /api/equity/drawdown      回撤曲线数据
GET /api/equity/monthly       月度收益热力图数据
```

#### 6.2 前端展示
- 每日净值折线图
- 回撤曲线（填充色）
- 月度收益热力图
- 胜率/盈亏比趋势

---

### 模块7：多策略管理（P2 🟢）

**为什么要做**：单一策略在不同市场环境下表现差异大，多策略平滑收益曲线。

#### 7.1 策略池
```python
STRATEGIES = {
    "overnight": 一夜持股法,          # 现有
    "opening_rush": 开盘强势股策略,    # 新增
    "trend_follow": 趋势跟踪策略,      # 新增
}
```

#### 7.2 开盘强势股策略（新增）
- 买入时间：09:30-09:45（开盘15分钟）
- 条件：开盘涨幅>5%、成交量>3倍、非一字板
- 卖出：当日尾盘14:50或次日

#### 7.3 策略权重分配
- 根据最近30天回测表现动态调整权重
- 表现好的策略多分配资金

---

## 三、数据库扩展

### 新增表
```sql
-- 回测结果表
CREATE TABLE backtest_results (
    id INTEGER PRIMARY KEY,
    strategy_name TEXT,
    start_date TEXT,
    end_date TEXT,
    total_return REAL,
    annual_return REAL,
    max_drawdown REAL,
    sharpe_ratio REAL,
    win_rate REAL,
    profit_loss_ratio REAL,
    total_trades INTEGER,
    params TEXT,  -- JSON: 策略参数
    created_at TEXT
);

-- 回测详细交易记录
CREATE TABLE backtest_trades (
    id INTEGER PRIMARY KEY,
    backtest_id INTEGER,
    stock_code TEXT,
    stock_name TEXT,
    buy_date TEXT,
    buy_price REAL,
    sell_date TEXT,
    sell_price REAL,
    shares INTEGER,
    profit_pct REAL,
    profit_amount REAL,
    hold_days INTEGER,
    reason TEXT
);

-- 资金流向记录
CREATE TABLE fund_flow (
    id INTEGER PRIMARY KEY,
    stock_code TEXT,
    date TEXT,
    main_net_inflow REAL,     -- 主力净流入
    super_big_net REAL,       -- 超大单净额
    big_net REAL,             -- 大单净额
    mid_net REAL,             -- 中单净额
    small_net REAL            -- 小单净额
);

-- 板块数据
CREATE TABLE sector_data (
    id INTEGER PRIMARY KEY,
    sector_name TEXT,
    date TEXT,
    change_pct REAL,
    volume REAL,
    stock_count INTEGER,
    top_stock_code TEXT,
    top_stock_change REAL
);

-- 情绪数据
CREATE TABLE sentiment_data (
    id INTEGER PRIMARY KEY,
    date TEXT,
    limit_up_count INTEGER,
    limit_down_count INTEGER,
    up_count INTEGER,
    down_count INTEGER,
    active_stocks INTEGER,
    sentiment_score REAL
);
```

---

## 四、实施路线图

### 第1周：回测引擎
- [ ] Day 1-2: 数据加载模块（akshare历史数据批量获取）
- [ ] Day 3-4: 回测核心引擎（模拟买卖、净值计算）
- [ ] Day 5: 报告生成（胜率/盈亏比/回撤/夏普）
- [ ] Day 6-7: 参数优化（网格搜索各参数组合）

### 第2周：资金流 + 板块
- [ ] Day 1-2: 资金流向数据获取和存储
- [ ] Day 3-4: 板块联动引擎（热门板块/龙头识别）
- [ ] Day 5-7: 集成到选股流程（加分机制）

### 第3周：情绪 + ATR
- [ ] Day 1-3: 市场情绪引擎（涨跌比/涨停数/连板数）
- [ ] Day 4-5: ATR动态止损模块
- [ ] Day 6-7: 集成测试

### 第4周：可视化 + 多策略
- [ ] Day 1-3: 净值曲线/回撤图/热力图API
- [ ] Day 4-5: 前端图表展示
- [ ] Day 6-7: 开盘强势股策略（第二个策略）

### 第5-6周：优化 + 上线
- [ ] 全链路压力测试
- [ ] 回测验证所有策略的历史表现
- [ ] 调参定稿
- [ ] 正式上线运行

---

## 五、技术选型

| 组件 | 选型 | 原因 |
|------|------|------|
| 数据源 | akshare | 免费、稳定、覆盖A股全量 |
| 数据库 | SQLite | 现有，够用，无需迁移 |
| 回测框架 | 自研 | 轻量，完全匹配我们的策略 |
| 图表 | ECharts / 纯API | AI工作室已有前端 |
| 任务调度 | cron定时任务 | 现有方案 |

---

## 六、预期效果

| 指标 | 现在 | 升级后 |
|------|------|--------|
| 策略数量 | 1个 | 2-3个 |
| 选股维度 | 7个 | 12+个 |
| 回测能力 | 无 | 完整回测+参数优化 |
| 风控维度 | 固定止损 | ATR动态+情绪过滤 |
| 可视化 | 无 | 净值曲线+回撤+热力图 |
| 数据覆盖 | 免费行情 | 行情+资金流+板块+情绪 |

---

## 七、风险与注意事项

1. **回测过拟合**：参数优化时要防止过度拟合历史数据，用样本外测试验证
2. **API限流**：akshare有请求频率限制，批量获取时注意间隔
3. **数据质量**：历史数据可能有缺失/异常，需要清洗
4. **实时性**：资金流/情绪数据延迟5-15分钟，对尾盘选股影响有限
5. **工程复杂度**：6个模块互相依赖，需要合理安排依赖顺序

---

*方案由蛋蛋设计，老板确认后开始实施*
