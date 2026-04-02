"""
蛋蛋模拟交易系统 - Flask后端 + SQLite数据库
"""
import os
import json
import re
import requests
from datetime import datetime, date
from flask import Flask, render_template, jsonify, request

import akshare as ak
import database as db
from trading.strategies import StrategyManager

# ========== 腾讯行情API (备用) ==========
def get_tencent_quote(code):
    """
    通过腾讯行情API获取股票实时数据
    code: 如 'sz300274', 'sh600362'
    返回: dict 或 None
    """
    try:
        import urllib.request
        url = f'https://qt.gtimg.cn/q={code}'
        req = urllib.request.Request(url, headers={
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Referer': 'https://finance.qq.com/'
        })
        with urllib.request.urlopen(req, timeout=8) as resp:
            data = resp.read().decode('gbk')
        # 解析: v_sz300274="51~阳光电源~300274~131.47~134.45~0.00~..."
        m = re.search(r'v_\w+="([^"]+)"', data)
        if not m:
            return None
        fields = m.group(1).split('~')
        if len(fields) < 35:
            return None
        name = fields[1]
        price = float(fields[3])   # 当前价格
        close = float(fields[4])   # 昨收/今开
        open_ = float(fields[5])   # 开盘价
        high = float(fields[33]) if fields[33] else 0  # 最高
        low = float(fields[34]) if fields[34] else 0   # 最低
        vol = float(fields[38]) if fields[38] else 0  # 成交量(手)
        amount = float(fields[39]) if fields[39] else 0  # 成交额
        change = float(fields[31])  # 涨跌额
        change_pct = float(fields[32])  # 涨跌幅%
        time_str = fields[30] if len(fields) > 30 else ''
        # 格式化时间
        if len(time_str) == 14:
            time_fmt = f"{time_str[8:10]}:{time_str[10:12]}:{time_str[12:14]}"
        else:
            time_fmt = time_str
        return {
            "code": code,
            "name": name,
            "price": price,
            "open": open_,
            "high": high,
            "low": low,
            "close": close,
            "change": change,
            "change_pct": change_pct,
            "volume": vol,
            "amount": amount,
            "time": time_fmt
        }
    except Exception as e:
        return None

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
    """获取实时行情 (优先akshare，失败用腾讯API)"""
    # 标准化代码前缀
    code = stock_code.strip()
    if not code.startswith(('sh', 'sz')):
        # 默认加前缀
        if code.startswith('6'):
            code = 'sh' + code
        elif code.startswith(('0', '3')):
            code = 'sz' + code
    
    # 1. 先尝试腾讯API (快速备用)
    tencent_data = get_tencent_quote(code)
    
    try:
        df = ak.stock_zh_a_spot_em()
        row = df[df['代码'] == stock_code]
        if not row.empty:
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
    except Exception:
        pass
    
    # 2. akshare失败，尝试腾讯API
    if tencent_data:
        return jsonify(tencent_data)
    
    return jsonify({"error": "查不到该股票行情"}), 404

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
    """获取大盘指数及均线数据 (腾讯API实时 + akshare历史均线)"""
    try:
        # 1. 腾讯API获取上证指数实时数据
        import urllib.request
        url = 'https://qt.gtimg.cn/q=sh000001'
        req = urllib.request.Request(url, headers={
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Referer': 'https://finance.qq.com/'
        })
        with urllib.request.urlopen(req, timeout=8) as resp:
            data = resp.read().decode('gbk')
        m = re.search(r'v_sh000001="([^"]+)"', data)
        if not m:
            raise Exception("腾讯指数接口返回格式错误")
        fields = m.group(1).split('~')
        current_price = float(fields[3])
        change_pct = float(fields[32])
        
        # 2. akshare获取历史数据计算MA (备用: 也用腾讯历史)
        try:
            end_date = date.today().strftime('%Y%m%d')
            start_date = (date.today().replace(day=1)).strftime('%Y%m%d')
            df = ak.stock_zh_index_daily( symbol="sh000001")
            df = df.tail(20)
            closes = df['close'].tolist()
            ma5 = sum(closes[-5:]) / 5
            ma10 = sum(closes[-10:]) / 10
        except Exception:
            # 备用：用腾讯历史K线
            kline_url = f'https://web.ifzq.gtimg.cn/appstock/app/fqkline/get?_var=kline_dayqfq&param=sh000001,day,,,20,qfq&r=0.1'
            kreq = urllib.request.Request(kline_url, headers={'User-Agent': 'Mozilla/5.0'})
            with urllib.request.urlopen(kreq, timeout=8) as kresp:
                kdata = kresp.read().decode('utf-8')
            kdata = kdata.replace('var kline_dayqfq=', '')
            kjson = json.loads(kdata)
            klines = kjson['data']['sh000001']['day']
            closes = [float(k[1]) for k in klines]
            ma5 = sum(closes[-5:]) / 5
            ma10 = sum(closes[-10:]) / 10
        
        return jsonify({
            "index": "上证指数",
            "code": "000001",
            "price": current_price,
            "change_pct": change_pct,
            "ma5": round(ma5, 2),
            "ma10": round(ma10, 2),
            "above_ma5": current_price > ma5,
            "above_ma10": current_price > ma10,
            "ma5_above_ma10": ma5 > ma10,
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
