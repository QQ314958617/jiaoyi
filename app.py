"""
蛋蛋模拟交易系统 - Flask后端 + SQLite数据库
==============================================
学习 Claude Code 源码后的改进：
1. 上下文缓存（context_cache.py）
2. Feature Flag 系统（feature_flags.py）
3. 启动计时点（startup profiler）
"""
import os
import json
import time
import threading
import requests
from datetime import datetime, date
from flask import Flask, render_template, jsonify, request, make_response

import akshare as ak
import database as db
from trading.strategies import StrategyManager

# OpenClaw 基础设施
from openclaw.feature_flags import feature, is_feature_enabled
from openclaw.context_cache import session_cache, heartbeat_cache

# ============================================================================
# 启动计时点（学习 Claude Code 的 profileCheckpoint）
# ============================================================================
_startup_markers = {}

def _profile_checkpoint(name: str) -> None:
    """记录启动计时点"""
    _startup_markers[name] = time.time()

_profile_checkpoint("module_import_done")

# ============================================================================
# Feature Flag: 各模块按需加载
# ============================================================================

# 行情数据缓存（默认启用，可通过 OPENCLAW_FEATURE_MARKET_CACHE=0 关闭）
_MARKET_CACHE_ENABLED = is_feature_enabled("MARKET_CACHE")

# 交易统计缓存（默认启用）
_STATS_CACHE_ENABLED = is_feature_enabled("STATS_CACHE")

# 股票监控功能
_STOCK_MONITOR_ENABLED = is_feature_enabled("STOCK_MONITOR")

# 启动时打印特性状态（仅调试）
if os.environ.get("OPENCLAW_DEBUG") == "1":
    from openclaw.feature_flags import list_features
    print("[DEBUG] Feature flags:", list_features())

# 腾讯实时行情API
def get_tencent_quote(codes):
    """从腾讯获取实时行情"""
    if not codes:
        return {}
    
    # 腾讯行情URL
    code_str = ','.join([f"sh{c}" if c.startswith(('6', '5')) else f"sz{c}" for c in codes])
    url = f"https://qt.gtimg.cn/q={code_str}"
    
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Referer': 'https://gu.qq.com/'
        }
        r = requests.get(url, headers=headers, timeout=5)
        result = {}
        for line in r.text.strip().split('\n'):
            if '=' in line:
                key = line.split('=')[0].replace('v_', '')
                fields = line.split('="')[1].strip('"').split('~')
                if len(fields) > 10:
                    result[key.upper().replace('SH', '').replace('SZ', '')] = {
                        'name': fields[1],
                        'price': float(fields[3]) if fields[3] != '-' else 0,
                        'close': float(fields[4]) if fields[4] != '-' else 0,
                        'open': float(fields[5]) if fields[5] != '-' else 0,
                        'volume': float(fields[6]) if fields[6] != '-' else 0,
                        'amount': float(fields[37]) if len(fields) > 37 and fields[37] != '-' else 0,
                        'high': float(fields[33]) if len(fields) > 33 and fields[33] != '-' else 0,
                        'low': float(fields[34]) if len(fields) > 34 and fields[34] != '-' else 0,
                        'change': float(fields[31]) if len(fields) > 31 and fields[31] != '-' else 0,
                        'change_pct': float(fields[32]) if len(fields) > 32 and fields[32] != '-' else 0,
                        'time': fields[30] if len(fields) > 30 else '',
                    }
        return result
    except Exception as e:
        print(f"腾讯行情错误: {e}")
        return {}

app = Flask(__name__, static_folder=None)  # Disable default static, we use custom routes
app.config['JSON_AS_ASCII'] = False

strategy_mgr = StrategyManager()

# 缓存 TTL 设置（秒）
_CACHE_TTL = 300  # 5分钟

# 使用 OpenClaw 统一缓存系统替代旧的手动缓存
_cache = {
    'market_top': {'data': None, 'time': 0},
    'quote': {},
    'index': {'data': None, 'time': 0},
}

# 后台预加载市场数据（参考 Claude Code 的并行预加载）
def preload_market_data():
    def _load():
        print("🔄 预加载市场数据...")
        try:
            hot_codes = [
                '600036', '000001', '601318', '600519', '000858',
                '300750', '002475', '688525', '002428', '600276',
                '601888', '600009', '000333', '002594', '300059',
                '300274', '002466', '600900', '601012', '300015',
            ]
            quotes = get_tencent_quote(hot_codes)
            result = []
            for code, data in quotes.items():
                if data.get('price', 0) > 0:
                    result.append({
                        "code": code,
                        "name": data['name'],
                        "price": data['price'],
                        "change_pct": data['change_pct'],
                        "volume": data.get('amount', 0),
                    })
            result.sort(key=lambda x: x['volume'], reverse=True)
            _cache['market_top'] = {'data': result[:20], 'time': time.time()}
            print(f"✅ 市场数据加载完成: {len(result)} 只股票")
        except Exception as e:
            print(f"❌ 市场数据加载失败: {e}")
    
    t = threading.Thread(target=_load, daemon=True)
    t.start()

preload_market_data()

# ========== 初始化 ==========

@app.before_request
def before_first_request():
    """首次请求前初始化数据库"""
    if not hasattr(app, '_db_initialized'):
        _profile_checkpoint("db_init_start")
        db.init_database()
        _profile_checkpoint("db_init_done")
        app._db_initialized = True
        if os.environ.get("OPENCLAW_DEBUG") == "1":
            elapsed = {k: round(v - list(_startup_markers.values())[0], 1)
                       for k, v in _startup_markers.items()}
            print(f"[DEBUG] Startup markers: {elapsed}")

# ========== 路由 ==========

@app.route('/')
def index():
    response = make_response(render_template('index.html'))
    response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
    return response

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
    """获取每日复盘（支持分页）
    参数: page=1, page_size=10
    """
    page = int(request.args.get('page', 1))
    page_size = int(request.args.get('page_size', 10))
    offset = (page - 1) * page_size
    
    total, reviews = db.get_reviews_paged(offset=offset, limit=page_size)
    
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
    
    return jsonify({
        "total": total,
        "page": page,
        "page_size": page_size,
        "total_pages": (total + page_size - 1) // page_size if total > 0 else 0,
        "reviews": reviews
    })

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
    """获取实时行情（腾讯API）"""
    now = time.time()
    cache_key = f'quote_{stock_code}'
    
    if cache_key in _cache['quote'] and (now - _cache['quote'][cache_key]['time']) < _CACHE_TTL:
        return jsonify(_cache['quote'][cache_key]['data'])
    
    try:
        quotes = get_tencent_quote([stock_code])
        if stock_code not in quotes:
            return jsonify({"error": "股票代码不存在"}), 404
        
        data = quotes[stock_code]
        result = {
            "code": stock_code,
            "name": data['name'],
            "price": data['price'],
            "change": data['change'],
            "change_pct": data['change_pct'],
            "volume": data['volume'],
            "amount": data.get('amount', 0),
            "high": data.get('high', 0),
            "low": data.get('low', 0),
            "open": data.get('open', 0),
            "close": data.get('close', 0),
            "time": data.get('time', datetime.now().strftime("%H:%M:%S"))
        }
        _cache['quote'][cache_key] = {'data': result, 'time': now}
        return jsonify(result)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/quotes/batch')
def get_quotes_batch():
    """批量获取持仓股行情（腾讯API）"""
    positions = db.get_positions()
    codes = [p['stock_code'] for p in positions]
    
    if not codes:
        return jsonify([])
    
    now = time.time()
    # 检查缓存
    cached = []
    uncached = []
    for code in codes:
        cache_key = f'quote_{code}'
        if cache_key in _cache['quote'] and (now - _cache['quote'][cache_key]['time']) < _CACHE_TTL:
            cached.append(_cache['quote'][cache_key]['data'])
        else:
            uncached.append(code)
    
    result = list(cached)
    
    if uncached:
        try:
            quotes = get_tencent_quote(uncached)
            for code, data in quotes.items():
                q = {
                    "code": code,
                    "name": data['name'],
                    "price": data['price'],
                    "change": data['change'],
                    "change_pct": data['change_pct'],
                    "volume": data['volume'],
                    "high": data.get('high', 0),
                    "low": data.get('low', 0),
                    "time": data.get('time', datetime.now().strftime("%H:%M:%S"))
                }
                _cache['quote'][f'quote_{code}'] = {'data': q, 'time': now}
                result.append(q)
        except:
            pass
    
    return jsonify(result)

@app.route('/api/market/top')
def get_market_top():
    """获取市场热门股票（使用腾讯API）"""
    now = time.time()
    
    # 常用热门股票列表
    hot_codes = [
        '600036', '000001', '601318', '600519', '000858',  # 银行保险白酒
        '300750', '002475', '688525', '002428', '600276',  # 宁德时代/立讯/佰维/云南锗业/恒瑞
        '601888', '600009', '000333', '002594', '300059',  # 中免/上海机场/美的/比亚迪/东方财富
        '300274', '002466', '600900', '601012', '300015',  # 阳光电源/天齐/长江电力/隆基/爱尔
        '688041', '300033', '002352', '601166', '600030',  # 海光/同花顺/顺丰/兴业/中信
    ]
    
    # 如果有缓存，直接返回（即使过期也先用旧数据）
    if _cache['market_top']['data']:
        if (now - _cache['market_top']['time']) >= _CACHE_TTL:
            def _refresh():
                try:
                    quotes = get_tencent_quote(hot_codes)
                    result = []
                    for code, data in quotes.items():
                        if data.get('price', 0) > 0:
                            result.append({
                                "code": code,
                                "name": data['name'],
                                "price": data['price'],
                                "change_pct": data['change_pct'],
                                "volume": data.get('amount', 0),
                            })
                    result.sort(key=lambda x: x['volume'], reverse=True)
                    _cache['market_top'] = {'data': result[:20], 'time': time.time()}
                except:
                    pass
            threading.Thread(target=_refresh, daemon=True).start()
        return jsonify(_cache['market_top']['data'])
    
    # 完全没有缓存
    try:
        quotes = get_tencent_quote(hot_codes)
        result = []
        for code, data in quotes.items():
            if data.get('price', 0) > 0:
                result.append({
                    "code": code,
                    "name": data['name'],
                    "price": data['price'],
                    "change_pct": data['change_pct'],
                    "volume": data.get('amount', 0),
                })
        result.sort(key=lambda x: x['volume'], reverse=True)
        _cache['market_top'] = {'data': result[:20], 'time': time.time()}
        return jsonify(result[:20])
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/index')
def get_index():
    """获取大盘指数及均线数据"""
    import pandas as pd
    
    # 从缓存获取当日指数数据
    now = time.time()
    if _cache['index']['data'] and (now - _cache['index']['time']) < _CACHE_TTL:
        return jsonify(_cache['index']['data'])
    
    try:
        # 1. 获取实时价格（腾讯API）
        url = "https://qt.gtimg.cn/q=sh000001"
        headers = {'User-Agent': 'Mozilla/5.0', 'Referer': 'https://gu.qq.com/'}
        r = requests.get(url, headers=headers, timeout=5)
        fields = r.text.split('="')[1].strip('"').split('~')
        current_price = float(fields[3]) if fields[3] != '-' else 0
        
        # 2. 获取历史数据计算MA（akshare）
        df = ak.stock_zh_index_daily(symbol='sh000001')
        df = df.tail(15).copy()
        df['ma5'] = df['close'].rolling(window=5).mean()
        df['ma10'] = df['close'].rolling(window=10).mean()
        
        latest = df.iloc[-1]
        ma5 = round(latest['ma5'], 2) if pd.notna(latest['ma5']) else 0
        ma10 = round(latest['ma10'], 2) if pd.notna(latest['ma10']) else 0
        
        result = {
            "code": "000001",
            "name": "上证指数",
            "price": current_price,
            "ma5": ma5,
            "ma10": ma10,
            "above_ma5": bool(current_price > ma5) if ma5 > 0 else False,
            "above_ma10": bool(current_price > ma10) if ma10 > 0 else False,
            "ma5_above_ma10": bool(ma5 > ma10),  # 多头排列
            "change_pct": float(fields[32]) if len(fields) > 32 and fields[32] != '-' else 0,
            "volume": float(fields[37]) if len(fields) > 37 and fields[37] != '-' else 0,
        }
        
        _cache['index'] = {'data': result, 'time': time.time()}
        return jsonify(result)
    except Exception as e:
        return jsonify({"error": f"获取指数数据失败: {str(e)}"}), 500

@app.route('/api/trade', methods=['POST'])
def execute_trade():
    """执行交易"""
    data = request.json
    action = data.get('action')
    stock_code = data.get('stock_code')
    shares = int(data.get('shares', 100))
    
    account = db.get_account()
    
    # 获取当前价（腾讯API）
    try:
        quotes = get_tencent_quote([stock_code])
        if stock_code not in quotes or quotes[stock_code]['price'] == 0:
            return jsonify({"error": "股票不存在或停牌"}), 400
        price = quotes[stock_code]['price']
        name = quotes[stock_code]['name']
    except Exception as e:
        return jsonify({"error": f"获取行情失败: {str(e)}"}), 500
    
    commission = 0
    profit = 0
    
    if action == 'buy':
        cost = price * shares * 1.0003  # 手续费+印花税
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
        
        commission = cost - price * shares
        new_cash -= commission
        
    elif action == 'sell':
        position = db.get_position(stock_code)
        if not position:
            return jsonify({"error": "没有持仓"}), 400
        if position['shares'] < shares:
            return jsonify({"error": "持仓不足"}), 400
        
        revenue = price * shares * 0.9997  # 扣除手续费
        profit = (price - position['avg_cost']) * shares * 0.9997
        new_cash = account['cash'] + revenue
        commission = price * shares - revenue
        
        remaining = position['shares'] - shares
        if remaining == 0:
            db.delete_position(stock_code)
        else:
            db.upsert_position(stock_code, name, remaining, position['avg_cost'])
    
    # 更新账户
    positions = db.get_positions()
    total_value = new_cash
    try:
        codes = [p['stock_code'] for p in positions]
        quotes = get_tencent_quote(codes) if codes else {}
        for pos in positions:
            code = pos['stock_code']
            if code in quotes and quotes[code]['price'] > 0:
                total_value += quotes[code]['price'] * pos['shares']
            else:
                total_value += pos['avg_cost'] * pos['shares']
    except:
        for pos in positions:
            total_value += pos['avg_cost'] * pos['shares']
    
    total_profit = total_value - 50000.0
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



# ========== 工作室页面 ==========

@app.route('/studio')
def studio_page():
    return render_template('studio.html')


@app.route('/trading-card')
def trading_card_page():
    """交易状态卡片 HTML 页面"""
    return render_template('trading_card.html')

@app.route('/studio-ui')
@app.route('/studio-ui/')
def studio_ui_index():
    """反向代理 Star Office UI 首页"""
    try:
        resp = requests.get(f'http://127.0.0.1:19000/', timeout=10)
        content = resp.content.decode('utf-8')
        # 重写静态资源路径
        content = content.replace('href="/', 'href="/studio-ui/')
        content = content.replace('src="/', 'src="/studio-ui/')
        return make_response(content, resp.status_code)
    except Exception as e:
        return make_response(f'Proxy error: {e}', 502)

@app.route('/studio-ui/<path:path>')
def studio_ui_proxy(path):
    """反向代理 Star Office UI 静态资源"""
    try:
        resp = requests.get(f'http://127.0.0.1:19000/{path}', timeout=10)
        response = make_response(resp.content, resp.status_code)
        # Pass through CORS headers
        response.headers['Access-Control-Allow-Origin'] = '*'
        return response
    except Exception as e:
        return make_response(f'Proxy error: {e}', 502)

@app.route('/studio-api/<path:path>', methods=['GET', 'POST', 'PUT', 'DELETE'])
def studio_api_proxy(path):
    """反向代理 Star Office UI API"""
    try:
        url = f'http://127.0.0.1:19000/{path}'
        if request.method == 'GET':
            resp = requests.get(url, params=request.args, timeout=10)
        elif request.method == 'POST':
            resp = requests.post(url, json=request.json, timeout=10)
        elif request.method == 'PUT':
            resp = requests.put(url, json=request.json, timeout=10)
        elif request.method == 'DELETE':
            resp = requests.delete(url, timeout=10)
        else:
            return make_response('Method not allowed', 405)
        
        response = make_response(resp.content, resp.status_code)
        for key, value in resp.headers.items():
            if key not in ('Content-Length', 'Content-Encoding', 'Transfer-Encoding'):
                response.headers[key] = value
        return response
    except Exception as e:
        return make_response(f'Proxy error: {e}', 502)

@app.route('/api/run_command', methods=['POST'])
def run_command():
    import subprocess
    data = request.json
    cmd = data.get('command', '')
    try:
        result = subprocess.run(
            cmd, shell=True, capture_output=True, text=True, timeout=120
        )
        output = result.stdout.strip() or result.stderr.strip() or '执行完成'
        return jsonify({'success': True, 'output': output[:500]})
    except subprocess.TimeoutExpired:
        return jsonify({'success': False, 'error': '执行超时'})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/start_tunnel', methods=['POST'])
def start_tunnel():
    import subprocess
    try:
        subprocess.run('pkill -f cloudflared', shell=True)
        subprocess.run('sleep 1')
        proc = subprocess.Popen(
            'cloudflared tunnel --url http://127.0.0.1:19000',
            shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True
        )
        import time
        url = None
        for _ in range(30):
            time.sleep(2)
            try:
                with open('/tmp/tunnel_url', 'r') as f:
                    url = f.read().strip()
                    if url:
                        break
            except:
                pass
            if proc.poll() is not None:
                break
        if url:
            return jsonify({'url': url})
        else:
            return jsonify({'error': '创建链接超时'})
    except Exception as e:
        return jsonify({'error': str(e)})


# ==================== Agent 状态路由 ====================

@app.route('/api/agent_status', methods=['GET', 'POST'])
def agent_status_route():
    """
    获取或设置 Agent 状态。

    GET: 返回当前状态 {"state": "idle", "detail": "..."}
    POST: 设置状态 {"state": "researching", "detail": "分析中..."}
    """
    from openclaw.state_manager import (
        set_agent_status, VALID_AGENT_STATES, get_global_store
    )
    import os

    if request.method == 'GET':
        # 从 state.json 读取（gunicorn 多 worker 共享文件）
        state_file = os.environ.get(
            "STAR_OFFICE_STATE_FILE",
            "/root/Star-Office-UI/state.json"
        )
        try:
            if os.path.exists(state_file):
                with open(state_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                return jsonify({
                    "state": data.get("state", "idle"),
                    "detail": data.get("detail", "")
                })
        except (json.JSONDecodeError, OSError):
            pass
        return jsonify({"state": "idle", "detail": ""})

    # POST: set status
    try:
        data = request.json or {}
        state = data.get('state', 'idle')
        detail = data.get('detail', '')

        if state not in VALID_AGENT_STATES:
            return jsonify({'error': f'Invalid state. Valid: {list(VALID_AGENT_STATES)}'}), 400

        set_agent_status(state, detail)
        return jsonify({'state': state, 'detail': detail})
    except Exception as e:
        return jsonify({'error': str(e)}), 500


if __name__ == '__main__':
    db.init_database()
    app.run(host='0.0.0.0', port=80, debug=False, threaded=True)

# ==================== Star Office UI 集成路由 ====================

@app.route('/star-api/<path:path>', methods=['GET', 'POST', 'PUT', 'DELETE'])
def star_api_proxy(path):
    """反向代理 Star Office UI 所有请求"""
    try:
        url = f'http://127.0.0.1:19000/{path}'
        headers = {'Origin': request.headers.get('Origin', '*')}
        
        if request.method == 'GET':
            resp = requests.get(url, params=request.args, headers=headers, timeout=10)
        elif request.method == 'POST':
            resp = requests.post(url, json=request.json, headers=headers, timeout=10)
        elif request.method == 'PUT':
            resp = requests.put(url, json=request.json, headers=headers, timeout=10)
        elif request.method == 'DELETE':
            resp = requests.delete(url, headers=headers, timeout=10)
        else:
            return make_response('Method not allowed', 405)
        
        response = make_response(resp.content)
        response.status_code = resp.status_code
        content_type = resp.headers.get('Content-Type', 'application/json')
        response.content_type = content_type
        for key, value in resp.headers.items():
            if key not in ('Content-Length', 'Content-Encoding', 'Transfer-Encoding', 'Host', 'Content-Type'):
                response.headers[key] = value
        response.headers['Access-Control-Allow-Origin'] = '*'
        return response
    except Exception as e:
        return make_response(f'Proxy error: {e}', 502)

@app.route('/static/<path:filename>')
def star_static_catchall(filename):
    """反向代理 Star Office UI 静态文件"""
    import sys
    print(f"DEBUG star_static_catchall called: filename={filename}", flush=True)
    try:
        resp = requests.get(f'http://127.0.0.1:19000/static/{filename}', timeout=10)
        response = make_response(resp.content)
        response.status_code = resp.status_code
        content_type = resp.headers.get('Content-Type', 'application/octet-stream')
        response.content_type = content_type
        response.headers['Access-Control-Allow-Origin'] = '*'
        return response
    except Exception as e:
        print(f"DEBUG star_static_catchall error: {e}", flush=True)
        return make_response(f'Proxy error: {e}', 502)

@app.route('/star-assets/<path:filename>')
def star_assets_proxy(filename):
    """反向代理 Star Office UI 静态文件"""
    try:
        resp = requests.get(f'http://127.0.0.1:19000/static/{filename}', timeout=10)
        response = make_response(resp.content)
        response.status_code = resp.status_code
        content_type = resp.headers.get('Content-Type', 'application/octet-stream')
        response.content_type = content_type
        response.headers['Access-Control-Allow-Origin'] = '*'
        return response
    except Exception as e:
        return make_response(f'Proxy error: {e}', 502)

@app.route('/star-static/<path:filename>')
def star_static_proxy(filename):
    """反向代理 Star Office UI 静态文件"""
    try:
        resp = requests.get(f'http://127.0.0.1:19000/static/{filename}', timeout=10)
        response = make_response(resp.content)
        response.status_code = resp.status_code
        content_type = resp.headers.get('Content-Type', 'application/octet-stream')
        response.content_type = content_type
        response.headers['Access-Control-Allow-Origin'] = '*'
        return response
    except Exception as e:
        return make_response(f'Proxy error: {e}', 502)

@app.route('/star-index')
def star_index():
    """获取 Star Office UI 首页并重写静态资源路径"""
    try:
        resp = requests.get(f'http://127.0.0.1:19000/', timeout=10)
        content = resp.content.decode('utf-8')
        # 重写静态资源路径
        content = content.replace('href="/static/', 'href="/static/')
        content = content.replace('src="/static/', 'src="/static/')
        # 重写API路径
        content = content.replace("fetch('/", "fetch('/star-api/")
        content = content.replace('fetch("/', 'fetch("/star-api/')
        return make_response(content, resp.status_code)
    except Exception as e:
        return make_response(f'Proxy error: {e}', 502)

@app.route('/star/')
@app.route('/star')
def star_home():
    """重定向到重写后的首页"""
    return redirect('/star-index')

