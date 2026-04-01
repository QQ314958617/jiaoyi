"""
蛋蛋模拟交易系统 - Flask后端 + SQLite数据库
"""
import os
import json
import requests
from datetime import datetime, date
from flask import Flask, render_template, jsonify, request

import akshare as ak
import database as db
from trading.strategies import StrategyManager

app = Flask(__name__)
app.config['JSON_AS_ASCII'] = False

strategy_mgr = StrategyManager()

# ========== 初始化 ==========

@app.before_request
def before_first_request():
    """首次请求前初始化数据库"""
    if not hasattr(app, '_db_initialized'):
        db.init_database()
        app._db_initialized = True

# ========== 路由 ==========

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/portfolio')
def get_portfolio():
    """获取当前持仓"""
    account = db.get_account()
    positions = db.get_positions()
    return jsonify({
        **account,
        'positions': {p['stock_code']: p for p in positions}
    })

@app.route('/api/trades')
def get_trades():
    """获取历史交易记录"""
    trades = db.get_trades(limit=100)
    return jsonify(trades)

@app.route('/api/daily')
def get_daily():
    """获取每日复盘"""
    reviews = db.get_reviews(limit=50)
    # 解析 JSON 字段
    for r in reviews:
        if r.get('strategies'):
            try:
                r['strategies'] = json.loads(r['strategies'])
            except:
                pass
        if r.get('tags'):
            try:
                r['tags'] = json.loads(r['tags'])
            except:
                r['tags'] = r['tags'].split(',') if r['tags'] else []
    return jsonify(reviews)

@app.route('/api/stats')
def get_stats():
    """获取交易统计"""
    return jsonify(db.get_trade_stats())

@app.route('/api/equity')
def get_equity():
    """获取净值曲线"""
    curve = db.get_equity_curve(days=60)
    return jsonify(curve)

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
    """批量获取持仓股行情"""
    positions = db.get_positions()
    codes = [p['stock_code'] for p in positions]
    
    if not codes:
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
    """获取市场热门股票"""
    try:
        df = ak.stock_zh_a_spot_em()
        df = df.head(20)
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

@app.route('/api/index')
def get_index():
    """获取大盘指数及均线数据"""
    try:
        # 获取上证指数和创业板指数实时数据
        url = 'https://push2.eastmoney.com/api/qt/stock/get?secid=1.000001&fields=f43,f169,f170,f57,f58'
        r = requests.get(url, timeout=5)
        data = r.json()['data']
        
        # 获取历史数据计算均线
        hist_url = 'https://push2his.eastmoney.com/api/qt/stock/kline/get?secid=1.000001&fields1=f1,f2,f3,f4,f5,f6&fields2=f51,f52,f53,f54,f55,f56&klt=101&fqt=0&beg=20260320&end=20260401'
        hr = requests.get(hist_url, timeout=5)
        hist_data = hr.json()['data']['klines']
        
        # 计算MA5和MA10
        closes = [float(d.split(',')[2]) for d in hist_data]
        ma5 = sum(closes[-5:]) / 5
        ma10 = sum(closes[-10:]) / 10
        
        current_price = data['f43'] / 100
        
        return jsonify({
            "index": "上证指数",
            "code": "000001",
            "price": current_price,
            "change_pct": data['f170'] / 100,
            "ma5": round(ma5, 2),
            "ma10": round(ma10, 2),
            "above_ma5": current_price > ma5,
            "above_ma10": current_price > ma10,
            "ma5_above_ma10": ma5 > ma10,  # 多头排列
            "time": datetime.now().strftime("%H:%M:%S")
        })
    except Exception as e:
        return jsonify({"error": f"获取指数失败: {str(e)}"}), 500

@app.route('/api/trade', methods=['POST'])
def execute_trade():
    """执行交易"""
    data = request.json
    action = data.get('action')
    stock_code = data.get('stock_code')
    shares = int(data.get('shares', 100))
    
    account = db.get_account()
    
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
    
    commission = 0
    profit = 0
    
    if action == 'buy':
        # 买入：券商佣金约0.03%（最低5元，但模拟账户忽略最低限制）
        commission = price * shares * 0.0003
        cost = price * shares + commission
        if cost > account['cash']:
            return jsonify({"error": "资金不足"}), 400
        
        new_cash = account['cash'] - cost
        position = db.get_position(stock_code)
        
        if position:
            # 追加买入
            total_shares = position['shares'] + shares
            total_cost = position['avg_cost'] * position['shares'] + price * shares
            new_avg_cost = total_cost / total_shares
            db.upsert_position(stock_code, name, total_shares, new_avg_cost)
        else:
            # 新买入
            db.upsert_position(stock_code, name, shares, price)
        
        # 记录今日买入（用于T+1校验）
        db.record_today_buy(stock_code, shares)
        
    elif action == 'sell':
        # T+1检查：今天买的不能卖
        if not db.can_sell_today(stock_code):
            return jsonify({"error": "T+1制度：今日买入的股票不能当日卖出"}), 400
        
        position = db.get_position(stock_code)
        if not position:
            return jsonify({"error": "没有持仓"}), 400
        if position['shares'] < shares:
            return jsonify({"error": "持仓不足"}), 400
        
        # 卖出：券商佣金0.03% + 印花税0.05% = 0.08%
        commission = price * shares * 0.0008
        revenue = price * shares - commission
        profit = (price - position['avg_cost']) * shares - commission
        new_cash = account['cash'] + revenue
        
        remaining = position['shares'] - shares
        if remaining == 0:
            db.delete_position(stock_code)
        else:
            db.upsert_position(stock_code, name, remaining, position['avg_cost'])
    
    # 更新账户
    positions = db.get_positions()
    total_value = new_cash
    for pos in positions:
        try:
            qdf = ak.stock_zh_a_spot_em()
            curr_price = float(qdf[qdf['代码'] == pos['stock_code']].iloc[0]['最新价'])
            total_value += curr_price * pos['shares']
        except:
            total_value += pos['avg_cost'] * pos['shares']
    
    total_profit = total_value - 1000000.0
    db.update_account(new_cash, total_value, total_profit)
    
    # 记录交易
    trade_id = db.add_trade(
        action, stock_code, name, price, shares,
        price * shares, commission, profit, data.get('reason', '')
    )
    
    # 记录净值
    position_value = total_value - new_cash
    db.add_equity_record(date.today().isoformat(), total_value, new_cash, position_value)
    
    return jsonify({
        "success": True,
        "trade_id": trade_id,
        "trade": {
            "id": trade_id,
            "timestamp": datetime.now().isoformat(),
            "action": action,
            "stock_code": stock_code,
            "stock_name": name,
            "price": price,
            "shares": shares,
            "amount": price * shares,
            "commission": commission,
            "profit": profit
        },
        "portfolio": {
            "cash": new_cash,
            "total_value": total_value,
            "total_profit": total_profit
        }
    })

@app.route('/api/review', methods=['POST'])
def add_review():
    """添加复盘记录"""
    data = request.json
    content = data.get('content', '')
    tags = data.get('tags', [])
    strategies = data.get('strategies', [])
    
    # 获取今日收益
    account = db.get_account()
    
    review_id = db.add_review(
        date=date.today().isoformat(),
        content=content,
        strategies=json.dumps(strategies, ensure_ascii=False),
        profit=account.get('total_profit', 0),
        tags=json.dumps(tags, ensure_ascii=False)
    )
    
    return jsonify({
        "success": True,
        "review_id": review_id
    })

@app.route('/api/analyze/<stock_code>')
def analyze_stock(stock_code):
    """AI策略分析单只股票"""
    position = db.get_position(stock_code)
    signal = strategy_mgr.get_best_signal(stock_code, position)
    return jsonify({
        "code": stock_code,
        "signal": signal,
        "strategies": strategy_mgr.analyze_all(stock_code, position)
    })

@app.route('/api/init', methods=['POST'])
def reset_account():
    """重置账户"""
    import shutil
    db_path = db.get_db_path()
    if os.path.exists(db_path):
        os.remove(db_path)
    db.init_database()
    return jsonify({"success": True})

if __name__ == '__main__':
    db.init_database()
    app.run(host='0.0.0.0', port=5000, debug=True)
