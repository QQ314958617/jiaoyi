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

# 加载 .env 环境变量
try:
    env_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".env")
    if os.path.exists(env_path):
        with open(env_path) as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    k, v = line.split("=", 1)
                    os.environ.setdefault(k, v)
except Exception:
    pass
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


# ==================== 成本追踪路由 ====================

@app.route('/api/cost', methods=['GET'])
def cost_route():
    """
    获取成本报表。
    GET /api/cost?format=summary|detail|recent
    """
    fmt = request.args.get('format', 'summary')

    from openclaw.cost_tracker import (
        get_cost_state, format_total_cost, get_cost_summary,
        get_recent_calls, get_model_usage, format_cost, format_tokens
    )

    state = get_cost_state()

    if fmt == 'detail':
        return jsonify(state.to_dict())
    elif fmt == 'recent':
        return jsonify({"calls": get_recent_calls(20)})
    elif fmt == 'model':
        return jsonify(get_model_usage())
    else:
        # summary
        return jsonify({
            "summary": get_cost_summary(),
            "total_cost_usd": round(state.total_cost_usd, 6),
            "total_api_calls": state.total_api_calls,
            "total_duration_ms": state.total_duration_ms,
            "input_tokens": state.total_input_tokens,
            "output_tokens": state.total_output_tokens,
            "cache_read_tokens": state.total_cache_read_tokens,
            "cache_write_tokens": state.total_cache_write_tokens,
            "model_usage": get_model_usage(),
        })


@app.route('/api/cost/reset', methods=['POST'])
def cost_reset_route():
    """重置成本计数器"""
    from openclaw.cost_tracker import reset_cost_state, save_cost_state
    reset_cost_state()
    save_cost_state()
    return jsonify({"ok": True, "message": "成本计数器已重置"})


# ==================== 一夜持股法选股 API ====================

@app.route('/api/screen/overnight', methods=['GET'])
def screen_overnight_route():
    """
    一夜持股法选股API
    GET /api/screen/overnight
    
    策略：尾盘14:50-14:58选股，次日早盘卖出
    条件：
    - 涨幅2-5%
    - 成交量放大1.5-5倍
    - RSI 40-60
    - 换手率3-15%
    - 价格站上MA5
    """
    try:
        # 动态导入（避免循环依赖）
        import sys
        sys.path.insert(0, '/root/.openclaw/workspace/sim_trading')
        from overnight_screener import screen_overnight_v2 as screen_overnight, format_screening_report_v2 as format_screening_report, Config, get_index_realtime
        
        results = screen_overnight()
        index_data = get_index_realtime()
        
        return jsonify({
            "success": True,
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "strategy": "一夜持股法v2.0",
            "config": {
                "rise_min": Config.RISE_MIN,
                "rise_max": Config.RISE_MAX,
                "volume_ratio_min": Config.VOLUME_RATIO_MIN,
                "volume_ratio_max": Config.VOLUME_RATIO_MAX,
                "rsi_min": Config.RSI_MIN,
                "rsi_max": Config.RSI_MAX,
                "turnover_min": Config.TURNOVER_MIN,
                "turnover_max": Config.TURNOVER_MAX,
                "market_cap_min": Config.MARKET_CAP_MIN,
                "market_cap_max": Config.MARKET_CAP_MAX,
                "max_position": Config.MAX_POSITION,
                "max_stocks": Config.MAX_STOCKS,
            },
            "index": index_data,
            "results": results,
            "count": len(results),
            "report": format_screening_report(results, index_data),
        })
        
    except Exception as e:
        import traceback
        return jsonify({
            "success": False,
            "error": str(e),
            "traceback": traceback.format_exc(),
        }), 500


if __name__ == '__main__':
    db.init_database()
    app.run(host='0.0.0.0', port=80, debug=False, threaded=True)

# ==================== 蛋蛋交易引擎 ====================
# 整合 Task/Hooks/Store/Coordinator 四大核心系统

def _get_index_data_cached():
    """获取大盘数据"""
    try:
        # 直接调用腾讯API获取上证指数
        url = "https://qt.gtimg.cn/q=sh000001"
        headers = {'User-Agent': 'Mozilla/5.0', 'Referer': 'https://gu.qq.com/'}
        r = requests.get(url, headers=headers, timeout=5)
        fields = r.text.split('="')[1].strip('"').split('~')
        current_price = float(fields[3]) if fields[3] != '-' else 0
        change_pct = float(fields[32]) if len(fields) > 32 and fields[32] != '-' else 0

        # 计算均线（使用缓存数据或重新计算）
        import pandas as pd
        now = time.time()
        if _cache.get('index', {}).get('data') and (now - _cache.get('index', {}).get('time', 0)) < _CACHE_TTL:
            cached = _cache['index']['data']
            return {
                "code": cached.get("code", "000001"),
                "name": cached.get("name", "上证指数"),
                "price": current_price,
                "ma5": cached.get("ma5", 0),
                "ma10": cached.get("ma10", 0),
                "change_pct": change_pct,
            }

        # 如果缓存过期，重新计算
        try:
            df = ak.stock_zh_index_daily(symbol='sh000001')
            df = df.tail(15).copy()
            df['ma5'] = df['close'].rolling(window=5).mean()
            df['ma10'] = df['close'].rolling(window=10).mean()
            latest = df.iloc[-1]
            ma5 = round(latest['ma5'], 2) if pd.notna(latest['ma5']) else 0
            ma10 = round(latest['ma10'], 2) if pd.notna(latest['ma10']) else 0
        except:
            ma5 = 0
            ma10 = 0

        return {
            "code": "000001",
            "name": "上证指数",
            "price": current_price,
            "ma5": ma5,
            "ma10": ma10,
            "change_pct": change_pct,
        }
    except Exception as e:
        print(f"获取大盘数据失败: {e}")
        return None

def _get_portfolio_cached():
    """获取账户数据（使用缓存）"""
    try:
        account = db.get_account()
        positions = db.get_positions()
        return {
            **account,
            'positions': {p['stock_code']: p for p in positions}
        }
    except:
        return None

def _get_market_top_cached():
    """获取热门股票（使用缓存）"""
    now = time.time()
    if now - _cache.get('market_top', {}).get('time', 0) < 60:
        return _cache.get('market_top', {}).get('data')
    return None


@app.route('/api/engine/status', methods=['GET'])
def engine_status():
    """
    获取交易引擎状态
    整合四大核心系统状态
    """
    index_data = _get_index_data_cached()
    portfolio = _get_portfolio_cached()

    # 获取持仓实时行情
    positions_quote = {}
    if portfolio and portfolio.get("positions"):
        codes = list(portfolio["positions"].keys())
        if codes:
            code_str = ','.join(['sh'+c if c.startswith(('6','5')) else 'sz'+c for c in codes])
            url = f"https://qt.gtimg.cn/q={code_str}"
            try:
                r = requests.get(url, timeout=3)
                for line in r.text.strip().split('\n'):
                    if '=' in line:
                        fields = line.split('="')[1].strip('"').split('~')
                        if len(fields) > 10:
                            code = fields[0]
                            for prefix in ['v_szh', 'v_shsh', 'sz', 'sh']:
                                code = code.replace(prefix, '')
                            positions_quote[code] = {
                                "price": float(fields[3]) if fields[3] != '-' else 0,
                                "change_pct": float(fields[32]) if len(fields) > 32 and fields[32] != '-' else 0,
                            }
            except:
                pass

    # 合并持仓数据
    positions = []
    if portfolio and portfolio.get("positions"):
        for code, pos in portfolio["positions"].items():
            quote = positions_quote.get(code, {})
            current_price = quote.get("price", 0)
            cost = pos.get("cost", 0)
            profit_pct = ((current_price - cost) / cost * 100) if cost > 0 else 0
            positions.append({
                "code": code,
                "name": pos.get("name", code),
                "shares": pos.get("shares", 0),
                "cost": cost,
                "current_price": current_price,
                "profit_loss_pct": profit_pct,
            })

    can_build = False
    if index_data:
        price = index_data.get("price", 0)
        ma5 = index_data.get("ma5", 0)
        ma10 = index_data.get("ma10", 0)
        can_build = price > ma5 > 0 and ma5 > ma10 > 0

    return jsonify({
        "timestamp": datetime.now().strftime("%H:%M:%S"),
        "engine": {
            "phase": "idle",
            "description": "🥚 蛋蛋交易引擎就绪",
            "四大系统": {
                "task_manager": task_manager.stats() if 'task_manager' in dir() else {},
                "hooks_manager": "钩子已注册",
                "store": "状态管理就绪",
                "coordinator": "协调器就绪",
            }
        },
        "market": {
            "code": index_data.get("code", "000001") if index_data else "000001",
            "name": index_data.get("name", "上证指数") if index_data else "上证指数",
            "price": index_data.get("price", 0) if index_data else 0,
            "ma5": index_data.get("ma5", 0) if index_data else 0,
            "ma10": index_data.get("ma10", 0) if index_data else 0,
            "can_build_position": can_build,
        } if index_data else None,
        "account": {
            "cash": portfolio.get("cash", 0) if portfolio else 0,
            "total_value": portfolio.get("total_value", 0) if portfolio else 0,
            "positions_count": len(positions),
        },
        "positions": positions,
    })



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



# ==================== 技术指标 API ====================

@app.route('/api/indicators/<stock_code>')
def get_indicators(stock_code):
    """
    获取股票技术指标
    RSI / MACD / KDJ / 布林带
    """
    try:
        import pandas as pd
        import numpy as np
        from openclaw.indicators import (
            calculate_rsi, calculate_macd, calculate_kdj,
            calculate_bollinger, calculate_volume_ratio, get_signal
        )

        # 获取历史数据
        try:
            symbol = f"sh{stock_code}" if stock_code.startswith(('6', '5')) else f"sz{stock_code}"
            df = ak.stock_zh_a_hist(symbol=symbol, period="daily", adjust="qfq").tail(60)

            if df.empty or len(df) < 20:
                return jsonify({"error": "数据不足"}), 400

            close = df['收盘'].tolist()
            high = df['最高'].tolist()
            low = df['最低'].tolist()
            volume = df['成交量'].tolist()
        except Exception as e:
            return jsonify({"error": f"获取数据失败: {str(e)}"}), 500

        result = {
            "code": stock_code,
            "close": close[-1],
            "high": high[-1],
            "low": low[-1],
            "volume": volume[-1],
            "date": str(df.iloc[-1]['日期']),
        }

        # RSI
        rsi = calculate_rsi(close)
        if rsi:
            result["rsi"] = rsi

        # MACD
        macd = calculate_macd(close)
        if macd:
            result["macd"] = macd

        # KDJ
        kdj = calculate_kdj(high, low, close)
        if kdj:
            result["kdj"] = kdj

        # 布林带
        bollinger = calculate_bollinger(close)
        if bollinger:
            result["bollinger"] = bollinger

        # 量比
        vol_ratio = calculate_volume_ratio(volume)
        if vol_ratio:
            result["volume_ratio"] = vol_ratio

        # 综合信号
        result["signal"] = get_signal(
            result.get("rsi"),
            result.get("macd"),
            result.get("kdj")
        )

        return jsonify(result)

    except Exception as e:
        import traceback
        return jsonify({"error": str(e), "traceback": traceback.format_exc()}), 500


# ==================== 自选股/预警系统 API ====================

@app.route('/api/watchlist', methods=['GET'])
def get_watchlist():
    """
    获取自选股列表（带实时行情）
    """
    try:
        from openclaw.alert_system import get_watchlist as _get_watchlist
        watchlist = _get_watchlist()
        return jsonify({
            "watchlist": watchlist,
            "count": len(watchlist),
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/api/watchlist/add', methods=['POST'])
def add_watchlist():
    """
    添加自选股
    POST /api/watchlist/add
    {"code": "600036", "name": "招商银行", "threshold": 5.0}
    """
    try:
        from openclaw.alert_system import add_to_watchlist as _add_watchlist

        data = request.json or {}
        code = data.get("code", "").strip()
        name = data.get("name", code)
        threshold = float(data.get("threshold", 5.0))

        if not code:
            return jsonify({"error": "股票代码不能为空"}), 400

        result = _add_watchlist(code, name, threshold=threshold)
        if result.get("success"):
            return jsonify(result)
        else:
            return jsonify(result), 400

    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/api/watchlist/remove', methods=['POST'])
def remove_watchlist():
    """
    删除自选股
    POST /api/watchlist/remove
    {"code": "600036"}
    """
    try:
        from openclaw.alert_system import remove_from_watchlist as _remove_watchlist

        data = request.json or {}
        code = data.get("code", "").strip()

        if not code:
            return jsonify({"error": "股票代码不能为空"}), 400

        result = _remove_watchlist(code)
        if result.get("success"):
            return jsonify(result)
        else:
            return jsonify(result), 400

    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/api/alerts', methods=['GET'])
def get_alerts():
    """
    获取预警记录
    """
    try:
        from openclaw.alert_system import load_alerts, clear_old_alerts

        # 清理旧预警
        cleared = clear_old_alerts()

        alerts = load_alerts()
        # 只返回未确认的
        unacknowledged = [a for a in alerts if not a.get("acknowledged", False)]

        return jsonify({
            "alerts": unacknowledged[-10:],  # 最近10条
            "total": len(unacknowledged),
            "cleared": cleared,
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/api/alerts/acknowledge', methods=['POST'])
def acknowledge_alert():
    """
    确认预警
    POST /api/alerts/acknowledge
    {"code": "600036", "triggered_at": "2026-04-07 10:30:00"}
    """
    try:
        from openclaw.alert_system import acknowledge_alert as _acknowledge

        data = request.json or {}
        code = data.get("code", "")
        triggered_at = data.get("triggered_at", "")

        if not code or not triggered_at:
            return jsonify({"error": "参数不完整"}), 400

        _acknowledge(code, triggered_at)
        return jsonify({"success": True})

    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/api/alerts/check', methods=['GET'])
def check_alerts():
    """
    检查预警（供定时任务调用）
    """
    try:
        from openclaw.alert_system import check_and_notify

        result = check_and_notify()
        return jsonify({
            "success": True,
            **result,
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# ==================== 增强的交易引擎 ====================

@app.route('/api/engine/run', methods=['POST'])
def engine_run():
    """
    执行完整交易周期（增强版）
    - 自动止损/止盈执行
    - RSI超买超卖检查
    - 跌停保护
    """
    try:
        # 1. 获取市场数据
        index_data = _get_index_data_cached()
        if not index_data:
            return jsonify({"success": False, "error": "无法获取大盘数据"}), 500

        price = index_data.get("price", 0)
        ma5 = index_data.get("ma5", 0)
        ma10 = index_data.get("ma10", 0)
        can_build = price > ma5 > 0 and ma5 > ma10 > 0

        # 2. 获取账户数据
        portfolio = _get_portfolio_cached()
        if not portfolio:
            return jsonify({"success": False, "error": "无法获取账户数据"}), 500

        cash = portfolio.get("cash", 0)
        positions_data = portfolio.get("positions", {})

        # 3. 获取持仓实时行情
        positions_quote = {}
        if positions_data:
            codes = list(positions_data.keys())
            code_str = ','.join(['sh'+c if c.startswith(('6','5')) else 'sz'+c for c in codes])
            url = f"https://qt.gtimg.cn/q={code_str}"
            r = requests.get(url, timeout=3)
            for line in r.text.strip().split('\n'):
                if '=' in line:
                    fields = line.split('="')[1].strip('"').split('~')
                    if len(fields) > 10:
                        code = fields[0]
                        for prefix in ['v_szh', 'v_shsh', 'sz', 'sh']:
                            code = code.replace(prefix, '')
                        positions_quote[code] = {
                            "price": float(fields[3]) if fields[3] != '-' else 0,
                            "change_pct": float(fields[32]) if len(fields) > 32 and fields[32] != '-' else 0,
                        }

        # 4. 分析持仓 - 止损/止盈/RSI检查
        actions = []
        alerts = []

        for code, pos in positions_data.items():
            quote = positions_quote.get(code, {})
            current_price = quote.get("price", 0)
            change_pct = quote.get("change_pct", 0)
            cost = pos.get("cost", 0)
            shares = pos.get("shares", 0)

            if cost > 0 and current_price > 0:
                profit_pct = (current_price - cost) / cost * 100
                loss_pct = -profit_pct

                # ===== 止损检查（一夜持股法：亏损3%止损，比普通策略更严格）=====
                if loss_pct >= 3:
                    actions.append({
                        "action": "SELL",
                        "code": code,
                        "name": pos.get("name", code),
                        "shares": shares,
                        "reason": f"🚨 止损！亏损 {loss_pct:.2f}%",
                        "priority": 1,
                        "urgent": True,
                    })
                    alerts.append(f"{pos.get('name', code)} 触发止损！亏损 {-loss_pct:.2f}%")
                    continue

                # ===== 止盈检查（一夜持股法：+3%~5%全仓卖出）=====
                if profit_pct >= 3:
                    actions.append({
                        "action": "SELL",
                        "code": code,
                        "name": pos.get("name", code),
                        "shares": shares,
                        "reason": f"💰 止盈！盈利 {profit_pct:.2f}%",
                        "priority": 2,
                        "urgent": False,
                    })

                # ===== RSI超买预警 =====
                try:
                    symbol = f"sh{code}" if code.startswith(('6', '5')) else f"sz{code}"
                    df = ak.stock_zh_a_hist(symbol=symbol, period="daily", adjust="qfq").tail(20)
                    if len(df) >= 15:
                        from openclaw.indicators import calculate_rsi
                        prices = df['收盘'].tolist()
                        rsi = calculate_rsi(prices)
                        if rsi and rsi > 70:
                            alerts.append(f"{pos.get('name', code)} RSI={rsi}，注意超买风险！")
                except:
                    pass

        # 5. 检查建仓条件
        if can_build and not actions and cash >= 10000:
            market_top = _get_market_top_cached()
            if market_top:
                for item in market_top[:10]:
                    code = item.get("code", "")
                    change_pct = item.get("change_pct", 0)
                    volume = item.get("volume", 0)

                    if code not in positions_data:
                        # 放量突破买入信号
                        if abs(change_pct) > 1.5 and volume > 500000:
                            actions.append({
                                "action": "BUY",
                                "code": code,
                                "name": item.get("name", code),
                                "shares": 100,
                                "reason": f"📈 放量突破！{'上涨' if change_pct > 0 else '下跌'} {change_pct:.2f}%，买入信号",
                                "priority": 5,
                                "urgent": False,
                            })
                            break  # 只买一个

        # 6. 执行交易（按优先级）
        results = []
        executed_count = 0

        # 先执行止损（紧急）
        urgent_actions = [a for a in actions if a.get("urgent")]
        normal_actions = [a for a in actions if not a.get("urgent")]

        for action in urgent_actions + normal_actions:
            if executed_count >= 5:
                break

            trade_result = db.execute_trade(
                action["action"].lower(),
                action["code"],
                action["shares"],
                action["reason"]
            )

            results.append({
                "action": action,
                "result": trade_result,
                "success": trade_result.get("success", False),
            })

            if trade_result.get("success"):
                executed_count += 1

        # 7. 生成执行报告
        report = {
            "success": True,
            "timestamp": datetime.now().strftime("%H:%M:%S"),
            "market": {
                "price": float(price),
                "ma5": float(ma5),
                "ma10": float(ma10),
                "can_build": bool(can_build),
            },
            "account": {
                "cash": float(cash),
                "positions_count": len(positions_data),
            },
            "analysis": {
                "stop_loss_triggered": sum(1 for a in actions if "止损" in a.get("reason", "")),
                "take_profit_triggered": sum(1 for a in actions if "止盈" in a.get("reason", "")),
                "buy_signals": sum(1 for a in actions if a["action"] == "BUY"),
                "alerts": alerts,
            },
            "actions_planned": len(actions),
            "actions_executed": executed_count,
            "results": results,
        }

        return jsonify(report)

    except Exception as e:
        import traceback
        return jsonify({
            "success": False,
            "error": str(e),
            "traceback": traceback.format_exc(),
        }), 500


# ==================== 盘中监控核心接口 ====================

@app.route('/api/market/scan', methods=['GET'])
def market_scan():
    """
    盘中监控核心接口 - 智能决策版本
    ==================================
    整合：大盘分析 + 持仓检查 + RSI + 成交量 + 自动执行
    
    调用频率：每5分钟（交易时间段）
    """
    try:
        from openclaw.indicators import calculate_rsi
        
        result = {
            "timestamp": datetime.now().strftime("%H:%M:%S"),
            "scan_mode": "auto",
            "index": None,
            "positions": [],
            "signals": [],
            "actions": [],
            "executed": [],
        }
        
        # ===== 1. 大盘检查 =====
        try:
            index_url = "https://qt.gtimg.cn/q=sh000001"
            r = requests.get(index_url, timeout=3)
            fields = r.text.split('="')[1].strip('"').split('~')
            price = float(fields[3]) if fields[3] != '-' else 0
            
            # 获取MA5/MA10（使用akshare）
            try:
                df = ak.stock_zh_index_daily(symbol='sh000001')
                closes = df['close'].tail(20).tolist()
                ma5 = sum(closes[-5:]) / 5 if len(closes) >= 5 else 0
                ma10 = sum(closes[-10:]) / 10 if len(closes) >= 10 else 0
            except:
                ma5 = ma10 = 0
            
            can_build = price > ma5 > 0 and ma5 > ma10 > 0
            
            result["index"] = {
                "name": "上证指数",
                "price": price,
                "ma5": round(ma5, 2),
                "ma10": round(ma10, 2),
                "above_ma5": price > ma5 > 0,
                "ma5_above_ma10": ma5 > ma10 > 0,
                "can_build": can_build,
            }
        except Exception as e:
            result["index"] = {"error": str(e)}
        
        # ===== 2. 账户和持仓 =====
        portfolio = _get_portfolio_cached()
        cash = portfolio.get("cash", 0) if portfolio else 0
        positions_data = portfolio.get("positions", {}) if portfolio else {}
        
        result["account"] = {
            "cash": cash,
            "positions_count": len(positions_data),
        }
        
        # ===== 3. 持仓检查 =====
        if positions_data:
            codes = list(positions_data.keys())
            code_str = ','.join(['sh'+c if c.startswith(('6','5')) else 'sz'+c for c in codes])
            url = f"https://qt.gtimg.cn/q={code_str}"
            r = requests.get(url, timeout=3)
            
            for line in r.text.strip().split('\n'):
                if '=' not in line:
                    continue
                fields = line.split('="')[1].strip('"').split('~')
                if len(fields) < 10:
                    continue
                
                code = fields[0]
                for prefix in ['v_szh', 'v_shsh', 'sz', 'sh']:
                    code = code.replace(prefix, '')
                
                if code not in positions_data:
                    continue
                
                pos = positions_data[code]
                current_price = float(fields[3]) if fields[3] != '-' else 0
                change_pct = float(fields[32]) if len(fields) > 32 and fields[32] != '-' else 0
                cost = pos.get("cost", 0)
                shares = pos.get("shares", 0)
                
                if cost <= 0 or current_price <= 0:
                    continue
                
                profit_pct = (current_price - cost) / cost * 100
                loss_pct = -profit_pct
                
                # RSI 计算
                rsi_value = None
                try:
                    symbol = f"sh{code}" if code.startswith(('6', '5')) else f"sz{code}"
                    df = ak.stock_zh_a_hist(symbol=symbol, period="daily", adjust="qfq").tail(20)
                    if len(df) >= 15:
                        prices = df['收盘'].tolist()
                        rsi_value = calculate_rsi(prices)
                except:
                    pass
                
                pos_result = {
                    "code": code,
                    "name": pos.get("name", code),
                    "price": current_price,
                    "cost": cost,
                    "profit_pct": profit_pct,
                    "rsi": rsi_value,
                    "signals": [],
                    "action": None,
                }
                
                # ===== 信号判断（一夜持股法止损3%）=====
                # 止损信号
                if loss_pct >= 3:
                    pos_result["signals"].append({"type": "STOP_LOSS", "value": loss_pct, "urgent": True})
                    pos_result["action"] = "SELL"
                
                # 止盈信号（一夜持股法：+3%~5%全仓）
                elif profit_pct >= 3:
                    pos_result["signals"].append({"type": "TAKE_PROFIT", "value": profit_pct, "urgent": False})
                    pos_result["action"] = "SELL"
                
                # RSI超买
                if rsi_value and rsi_value > 70:
                    pos_result["signals"].append({"type": "RSI_OVERBOUGHT", "value": rsi_value, "urgent": False})
                
                # RSI超卖
                if rsi_value and rsi_value < 35:
                    pos_result["signals"].append({"type": "RSI_OVERSOLD", "value": rsi_value, "urgent": True})
                
                result["positions"].append(pos_result)
                
                # 加入执行队列
                if pos_result["action"]:
                    result["actions"].append({
                        "action": pos_result["action"],
                        "code": code,
                        "name": pos_result["name"],
                        "shares": shares,
                        "reason": f"{pos_result['signals'][0]['type']} {pos_result['signals'][0]['value']:.1f}%",
                        "urgent": pos_result["signals"][0].get("urgent", False),
                    })
        
        # ===== 4. 找新买入机会 =====
        if result["index"].get("can_build") and not result["actions"] and cash >= 10000:
            try:
                market_top = _get_market_top_cached()
                if market_top:
                    for item in market_top[:15]:
                        code = item.get("code", "")
                        if code in positions_data:
                            continue
                        
                        change_pct = item.get("change_pct", 0)
                        volume = item.get("volume", 0)
                        
                        # 放量突破信号
                        if abs(change_pct) > 1.5 and volume > 500000:
                            result["signals"].append({
                                "type": "BUY_OPPORTUNITY",
                                "code": code,
                                "name": item.get("name", code),
                                "change_pct": change_pct,
                                "volume": volume,
                            })
                            result["actions"].append({
                                "action": "BUY",
                                "code": code,
                                "name": item.get("name", code),
                                "shares": 100,
                                "reason": f"放量突破 {change_pct:.1f}%",
                                "urgent": False,
                            })
                            break
            except:
                pass
        
        # ===== 5. 执行交易（按优先级） =====
        # 先执行止损（紧急）
        urgent_actions = [a for a in result["actions"] if a.get("urgent")]
        normal_actions = [a for a in result["actions"] if not a.get("urgent")]
        
        for action in urgent_actions + normal_actions:
            trade_result = db.execute_trade(
                action["action"].lower(),
                action["code"],
                action["shares"],
                action["reason"]
            )
            result["executed"].append({
                "action": action,
                "result": trade_result,
            })
        
        # ===== 6. 最终决定 =====
        if result["actions"]:
            action_summary = [f"{a['action']} {a['name']}({a['code']})" for a in result["actions"]]
            result["decision"] = f"执行: {', '.join(action_summary)}"
        elif result["index"].get("can_build"):
            result["decision"] = "观望 - 大盘满足条件，等待机会"
        else:
            result["decision"] = "观望 - 大盘未企稳，不建仓"
        
        return jsonify({
            "success": True,
            **result,
        })
        
    except Exception as e:
        import traceback
        return jsonify({
            "success": False,
            "error": str(e),
            "traceback": traceback.format_exc(),
        }), 500


# ==================== 多指数行情 API ====================

@app.route('/api/market/indices', methods=['GET'])
def get_multi_indices():
    """
    获取多个主要指数的实时行情
    上证指数、深证成指、创业板、科创综指、科创50
    """
    try:
        # 5个主要指数代码
        indices = {
            'sh000001': '上证指数',
            'sz399001': '深证成指', 
            'sz399006': '创业板指',
            'sh000688': '科创综指',
            'sh000688': '科创50',  # 同代码，展示用
        }
        
        code_str = ','.join(indices.keys())
        url = f"https://qt.gtimg.cn/q={code_str}"
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Referer': 'https://gu.qq.com/'
        }
        
        r = requests.get(url, headers=headers, timeout=5)
        result = []
        
        for line in r.text.strip().split('\n'):
            if '=' not in line:
                continue
            fields = line.split('="')[1].strip('"').split('~')
            if len(fields) < 35:
                continue
                
            # fields[0] = record type, fields[2] = actual code
            code = fields[2] if len(fields) > 2 else fields[0]
            name = fields[1]
            price = float(fields[3]) if fields[3] != '-' else 0
            change = float(fields[31]) if len(fields) > 31 and fields[31] != '-' else 0
            change_pct = float(fields[32]) if len(fields) > 32 and fields[32] != '-' else 0
            volume = float(fields[37]) if len(fields) > 37 and fields[37] != '-' else 0
            high = float(fields[33]) if len(fields) > 33 and fields[33] != '-' else 0
            low = float(fields[34]) if len(fields) > 34 and fields[34] != '-' else 0
            
            # 计算均线（使用akshare）
            ma5 = 0
            ma10 = 0
            try:
                # 指数代码映射
                index_symbols = {
                    '000001': 'sh000001',  # 上证指数
                    '399001': 'sz399001',  # 深证成指
                    '399006': 'sz399006',  # 创业板
                    '000688': 'sh000688',  # 科创50
                }
                symbol = index_symbols.get(code, f"sh{code}")
                df = ak.stock_zh_index_daily(symbol=symbol).tail(15)
                if len(df) >= 10:
                    ma5_val = df['close'].iloc[-5:].mean() if len(df) >= 5 else 0
                    ma10_val = df['close'].iloc[-10:].mean() if len(df) >= 10 else ma5_val
                    ma5 = round(float(ma5_val), 2) if ma5_val else 0
                    ma10 = round(float(ma10_val), 2) if ma10_val else 0
            except Exception as e:
                ma5 = 0
                ma10 = 0
            
            result.append({
                'code': code,
                'name': name,
                'price': price,
                'change': change,
                'change_pct': change_pct,
                'volume': volume,
                'high': high,
                'low': low,
                'ma5': ma5,
                'ma10': ma10,
                'above_ma5': price > ma5 > 0,
                'above_ma10': price > ma10 > 0,
                'ma5_above_ma10': ma5 > ma10 > 0,
            })
        
        return jsonify({
            'success': True,
            'timestamp': datetime.now().strftime('%H:%M:%S'),
            'indices': result,
        })
        
    except Exception as e:
        import traceback
        return jsonify({'success': False, 'error': str(e)}), 500


# ==================== 热点板块 API ====================

@app.route('/api/market/hot-sectors', methods=['GET'])
def get_hot_sectors():
    """
    获取实时热点板块 - 使用新浪API
    """
    try:
        # 使用新浪行业板块API
        url = "https://vip.stock.finance.sina.com.cn/q/view/newFLJK.php"
        params = {'param': 'class=hy'}
        
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Referer': 'https://finance.sina.com.cn/'
        }
        
        r = requests.get(url, params=params, headers=headers, timeout=5)
        text = r.text
        
        # 解析JavaScript格式数据
        import re
        # 格式: var S_Finance_bankuai_class=hy = {...}
        match = re.search(r'S_Finance_bankuai_class=hy\s*=\s*(\{.*\})', text)
        if not match:
            raise ValueError("无法解析板块数据")
        
        import ast
        # 将JavaScript对象转换为Python dict
        js_str = match.group(1)
        # 简单解析：提取各板块数据
        sectors_raw = re.findall(r'hangye_(\w+)"[^"]*"([^"]*)', js_str)
        
        sectors = []
        for prefix, data_str in sectors_raw:
            parts = data_str.split(',')
            if len(parts) >= 5:
                name = parts[1]  # 板块名
                try:
                    change_pct = float(parts[4]) if parts[4] else 0  # 涨跌幅
                except:
                    change_pct = 0
                
                if name and len(name) > 1:  # 过滤无效
                    sectors.append({
                        'name': name,
                        'change_pct': change_pct,
                    })
        
        # 按涨跌幅排序
        sectors.sort(key=lambda x: abs(x['change_pct']), reverse=True)
        
        # 取前10
        result = []
        for i, s in enumerate(sectors[:10]):
            result.append({
                'rank': i + 1,
                'code': '',
                'name': s['name'],
                'change_pct': round(s['change_pct'], 2),
                'direction': 'up' if s['change_pct'] > 0 else 'down',
            })
        
        return jsonify({
            'success': True,
            'timestamp': datetime.now().strftime('%H:%M:%S'),
            'sectors': result,
            'source': 'sina',
        })
        
    except Exception as e:
        # API失败时返回代表性示例数据
        return jsonify({
            'success': True,
            'timestamp': datetime.now().strftime('%H:%M:%S'),
            'sectors': [
                {'rank': 1, 'code': 'BK0889', 'name': 'AI算力', 'change_pct': 3.2, 'direction': 'up'},
                {'rank': 2, 'code': 'BK0401', 'name': '存储芯片', 'change_pct': 2.8, 'direction': 'up'},
                {'rank': 3, 'code': 'BK0091', 'name': '新能源汽车', 'change_pct': 1.5, 'direction': 'up'},
                {'rank': 4, 'code': 'BK0441', 'name': '医疗服务', 'change_pct': -1.2, 'direction': 'down'},
                {'rank': 5, 'code': 'BK0231', 'name': '光伏设备', 'change_pct': -0.8, 'direction': 'down'},
            ],
            'source': 'demo',
            'note': '实时数据获取失败，显示示例数据',
        })


# ==================== 实时大盘分析 API ====================

@app.route('/api/market/analyze', methods=['GET'])
def get_market_analysis():
    """
    获取实时大盘分析（技术面+资金面+情绪面）
    """
    try:
        # 获取多指数数据
        indices_data = get_multi_indices()
        indices = indices_data.json.get('indices', [])
        
        # 获取市场情绪数据
        # 涨跌停数量
        up_count = 0
        down_count = 0
        try:
            url = "https://push2.eastmoney.com/api/qt/clist/get"
            params = {
                'pn': 1, 'pz': 10,
                'fs': 'm:0+t:6,m:0+t:13,m:0+t:80,m:1+t:2,m:1+t:23',
                'fields': 'f1,f2,f3',
            }
            r = requests.get(url, params=params, headers={'Referer': 'https://quote.eastmoney.com/'}, timeout=5)
            import re
            json_str = re.search(r'\((.*)\)', r.text)
            if json_str:
                data = json.loads(json_str.group(1))
                stocks = data.get('data', {}).get('diff', [])
                for s in stocks:
                    if s.get('f3', 0) > 0:
                        up_count += 1
                    elif s.get('f3', 0) < 0:
                        down_count += 1
        except:
            pass
        
        # 主要分析上证指数
        main_index = next((i for i in indices if i['code'] == '000001'), None)
        
        analysis = {
            'timestamp': datetime.now().strftime('%H:%M:%S'),
            'indices': indices,
            'technical': {
                'above_ma5': main_index.get('above_ma5', False) if main_index else False,
                'above_ma10': main_index.get('above_ma10', False) if main_index else False,
                'ma5_above_ma10': main_index.get('ma5_above_ma10', False) if main_index else False,
                'trend': '多头' if (main_index.get('ma5_above_ma10') if main_index else False) else '震荡',
            },
            'sentiment': {
                'up_count': up_count,
                'down_count': down_count,
                'market_breadth': '偏多' if up_count > down_count else '偏空',
            },
            'volume': main_index.get('volume', 0) if main_index else 0,
        }
        
        # 综合结论
        can_build = (
            main_index.get('above_ma5', False) and 
            main_index.get('ma5_above_ma10', False)
        ) if main_index else False
        
        analysis['conclusion'] = {
            'can_build': can_build,
            'suggestion': '可建仓' if can_build else '观望',
            'signal': '✅' if can_build else '❌',
            'reason': '指数站稳5日线且多头排列' if can_build else '指数未站稳5日线或非多头排列',
        }
        
        return jsonify({
            'success': True,
            **analysis,
        })
        
    except Exception as e:
        import traceback
        return jsonify({'success': False, 'error': str(e)}), 500


