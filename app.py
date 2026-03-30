"""
蛋蛋模拟交易系统 - Flask后端
"""
import os
import json
import random
from datetime import datetime, date
from flask import Flask, render_template, jsonify, request

import akshare as ak
from trading.strategies import StrategyManager

strategy_mgr = StrategyManager()

app = Flask(__name__)
DATA_DIR = os.path.join(os.path.dirname(__file__), 'data')

# 初始化数据文件
os.makedirs(DATA_DIR, exist_ok=True)
PORTFOLIO_FILE = os.path.join(DATA_DIR, 'portfolio.json')
TRADES_FILE = os.path.join(DATA_DIR, 'trades.json')
DAILY_FILE = os.path.join(DATA_DIR, 'daily_review.json')

def load_json(path, default):
    if os.path.exists(path):
        with open(path, 'r', encoding='utf-8') as f:
            return json.load(f)
    return default

def save_json(path, data):
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

# ========== 模拟账户初始化 ==========
def init_account():
    return {
        "cash": 1000000.0,  # 初始本金100万
        "total_value": 1000000.0,
        "total_profit": 0.0,
        "positions": {},   # {stock_code: {shares, avg_cost, name}}
        "created_at": datetime.now().isoformat()
    }

# ========== 路由 ==========

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/portfolio')
def get_portfolio():
    """获取当前持仓"""
    portfolio = load_json(PORTFOLIO_FILE, init_account())
    return jsonify(portfolio)

@app.route('/api/trades')
def get_trades():
    """获取历史交易记录"""
    trades = load_json(TRADES_FILE, [])
    return jsonify(trades)

@app.route('/api/daily')
def get_daily():
    """获取每日复盘"""
    daily = load_json(DAILY_FILE, [])
    return jsonify(daily)

@app.route('/api/quote/<stock_code>')
def get_quote(stock_code):
    """获取实时行情"""
    try:
        df = ak.stock_zh_a_spot_em()
        row = df[df['代码'] == stock_code]
        if row.empty:
            return jsonify({"error": "股票代码不存在"}), 404
        row = row.iloc[0]
        return jsonify({
            "code": stock_code,
            "name": row['名称'],
            "price": float(row['最新价']),
            "change": float(row['涨跌额']),
            "change_pct": float(row['涨跌幅']),
            "volume": float(row['成交量']),
            "amount": float(row['成交额']),
            "high": float(row['最高']),
            "low": float(row['最低']),
            "open": float(row['今开']),
            "close": float(row['昨收']),
            "time": datetime.now().strftime("%H:%M:%S")
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/quotes/batch')
def get_quotes_batch():
    """批量获取行情"""
    portfolio = load_json(PORTFOLIO_FILE, init_account())
    codes = list(portfolio.get('positions', {}).keys())
    codes_str = ','.join(codes)
    
    if not codes_str:
        return jsonify([])
    
    try:
        df = ak.stock_zh_a_spot_em()
        rows = df[df['代码'].isin(codes)]
        result = []
        for _, row in rows.iterrows():
            result.append({
                "code": row['代码'],
                "name": row['名称'],
                "price": float(row['最新价']),
                "change": float(row['涨跌额']),
                "change_pct": float(row['涨跌幅']),
                "volume": float(row['成交量']),
                "high": float(row['最高']),
                "low": float(row['最低']),
                "time": datetime.now().strftime("%H:%M:%S")
            })
        return jsonify(result)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/market/top')
def get_market_top():
    """获取市场涨跌榜"""
    try:
        df = ak.stock_zh_a_spot_em()
        df = df.head(20)  # 取前20只
        result = []
        for _, row in df.iterrows():
            result.append({
                "code": row['代码'],
                "name": row['名称'],
                "price": float(row['最新价']),
                "change_pct": float(row['涨跌幅']),
                "volume": float(row['成交额']),
            })
        return jsonify(result)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/trade', methods=['POST'])
def execute_trade():
    """执行交易"""
    data = request.json
    action = data.get('action')  # buy or sell
    stock_code = data.get('stock_code')
    shares = int(data.get('shares', 100))  # 默认100股
    
    portfolio = load_json(PORTFOLIO_FILE, init_account())
    trades = load_json(TRADES_FILE, [])
    
    # 获取当前价
    try:
        df = ak.stock_zh_a_spot_em()
        row = df[df['代码'] == stock_code]
        if row.empty:
            return jsonify({"error": "股票不存在"}), 400
        price = float(row.iloc[0]['最新价'])
        name = row.iloc[0]['名称']
    except Exception as e:
        return jsonify({"error": f"获取行情失败: {str(e)}"}), 500
    
    trade_record = {
        "id": len(trades) + 1,
        "timestamp": datetime.now().isoformat(),
        "action": action,
        "stock_code": stock_code,
        "stock_name": name,
        "price": price,
        "shares": shares,
        "amount": price * shares,
        "reason": data.get('reason', '')
    }
    
    if action == 'buy':
        cost = price * shares * 1.0003  # 手续费+印花税
        if cost > portfolio['cash']:
            return jsonify({"error": "资金不足"}), 400
        portfolio['cash'] -= cost
        if stock_code in portfolio['positions']:
            old = portfolio['positions'][stock_code]
            total_shares = old['shares'] + shares
            total_cost = old['avg_cost'] * old['shares'] + price * shares
            old['avg_cost'] = total_cost / total_shares
            old['shares'] = total_shares
        else:
            portfolio['positions'][stock_code] = {
                "name": name,
                "shares": shares,
                "avg_cost": price,
                "buy_date": date.today().isoformat()
            }
        trade_record['commission'] = cost - price * shares
        portfolio['cash'] -= trade_record['commission']
        
    elif action == 'sell':
        if stock_code not in portfolio['positions']:
            return jsonify({"error": "没有持仓"}), 400
        pos = portfolio['positions'][stock_code]
        if pos['shares'] < shares:
            return jsonify({"error": "持仓不足"}), 400
        revenue = price * shares * 0.9997  # 手续费+印花税
        profit = (price - pos['avg_cost']) * shares * 0.9997
        portfolio['cash'] += revenue
        pos['shares'] -= shares
        if pos['shares'] == 0:
            del portfolio['positions'][stock_code]
        trade_record['profit'] = profit
        trade_record['commission'] = price * shares - revenue
    
    # 更新总市值
    total_value = portfolio['cash']
    for code, pos in portfolio['positions'].items():
        try:
            qdf = ak.stock_zh_a_spot_em()
            curr_price = float(qdf[qdf['代码'] == code].iloc[0]['最新价'])
            total_value += curr_price * pos['shares']
        except:
            total_value += pos['avg_cost'] * pos['shares']
    portfolio['total_value'] = total_value
    portfolio['total_profit'] = total_value - 1000000.0
    
    trades.append(trade_record)
    save_json(PORTFOLIO_FILE, portfolio)
    save_json(TRADES_FILE, trades)
    
    return jsonify({
        "success": True,
        "trade": trade_record,
        "portfolio": portfolio
    })

@app.route('/api/analyze/<stock_code>')
def analyze_stock(stock_code):
    """AI策略分析单只股票"""
    portfolio = load_json(PORTFOLIO_FILE, init_account())
    position = portfolio.get('positions', {}).get(stock_code)
    signal = strategy_mgr.get_best_signal(stock_code, position)
    return jsonify({
        "code": stock_code,
        "signal": signal,
        "strategies": strategy_mgr.analyze_all(stock_code, position)
    })

@app.route('/api/review', methods=['POST'])
def add_review():
    """添加复盘记录"""
    data = request.json
    daily = load_json(DAILY_FILE, [])
    
    review = {
        "id": len(daily) + 1,
        "date": date.today().isoformat(),
        "timestamp": datetime.now().isoformat(),
        "content": data.get('content', ''),
        "strategies": data.get('strategies', []),
        "profit": data.get('profit', 0),
        "tags": data.get('tags', [])
    }
    daily.append(review)
    save_json(DAILY_FILE, daily)
    return jsonify({"success": True, "review": review})

@app.route('/api/init', methods=['POST'])
def init_portfolio():
    """初始化/重置账户"""
    portfolio = init_account()
    # 默认放入几只候选股
    default_stocks = ['300750', '002475', '688525']  # 宁德时代、立讯精密、佰维存储
    save_json(PORTFOLIO_FILE, portfolio)
    save_json(TRADES_FILE, [])
    save_json(DAILY_FILE, [])
    return jsonify({"success": True, "portfolio": portfolio})

if __name__ == '__main__':
    with app.app_context():
        # 初始化账户
        if not os.path.exists(PORTFOLIO_FILE):
            save_json(PORTFOLIO_FILE, init_account())
    app.run(host='0.0.0.0', port=5000, debug=True)
