"""
行情服务 - 腾讯实时行情API封装
统一缓存，避免重复请求
"""
import time
import threading
import logging
import requests

from services.cache import cache

logger = logging.getLogger(__name__)

# 腾讯行情API headers
_HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
    'Referer': 'https://gu.qq.com/'
}


def get_tencent_quote(codes):
    """从腾讯获取实时行情"""
    if not codes:
        return {}

    code_str = ','.join([f"sh{c}" if c.startswith(('6', '5')) else f"sz{c}" for c in codes])
    url = f"https://qt.gtimg.cn/q={code_str}"

    try:
        r = requests.get(url, headers=_HEADERS, timeout=5)
        r.encoding = 'gbk'
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
        logger.warning(f"腾讯行情错误: {e}")
        return {}


def get_quote_cached(stock_code):
    """获取单只股票行情（带缓存）"""
    cache_key = f'quote_{stock_code}'
    cached = cache.get(cache_key)
    if cached is not None:
        return cached

    quotes = get_tencent_quote([stock_code])
    if stock_code in quotes:
        data = quotes[stock_code]
        cache.set(cache_key, data)
        return data
    return None


def get_quotes_batch_cached(codes):
    """批量获取行情（带缓存）"""
    if not codes:
        return {}

    result = {}
    uncached = []

    for code in codes:
        cache_key = f'quote_{code}'
        cached = cache.get(cache_key)
        if cached is not None:
            result[code] = cached
        else:
            uncached.append(code)

    if uncached:
        try:
            quotes = get_tencent_quote(uncached)
            for code, data in quotes.items():
                cache.set(f'quote_{code}', data)
                result[code] = data
        except Exception as e:
            logger.warning(f"批量行情获取失败: {e}")

    return result


# 热门股票列表
HOT_CODES = [
    '600036', '000001', '601318', '600519', '000858',
    '300750', '002475', '688525', '002428', '600276',
    '601888', '600009', '000333', '002594', '300059',
    '300274', '002466', '600900', '601012', '300015',
    '688041', '300033', '002352', '601166', '600030',
]


def get_market_top_cached():
    """获取市场热门股票（带缓存+后台刷新）"""
    cache_key = 'market_top'
    data, expired = cache.get_or_none(cache_key)

    if data and expired:
        # 后台刷新
        def _refresh():
            try:
                quotes = get_tencent_quote(HOT_CODES)
                result = []
                for code, d in quotes.items():
                    if d.get('price', 0) > 0:
                        result.append({
                            "code": code,
                            "name": d['name'],
                            "price": d['price'],
                            "change_pct": d['change_pct'],
                            "volume": d.get('amount', 0),
                        })
                result.sort(key=lambda x: x['volume'], reverse=True)
                cache.set(cache_key, result[:20])
            except Exception as e:
                logger.warning(f"刷新热门股票失败: {e}")
        threading.Thread(target=_refresh, daemon=True).start()
        return data

    if data:
        return data

    # 完全没有缓存，同步获取
    try:
        quotes = get_tencent_quote(HOT_CODES)
        result = []
        for code, d in quotes.items():
            if d.get('price', 0) > 0:
                result.append({
                    "code": code,
                    "name": d['name'],
                    "price": d['price'],
                    "change_pct": d['change_pct'],
                    "volume": d.get('amount', 0),
                })
        result.sort(key=lambda x: x['volume'], reverse=True)
        cache.set(cache_key, result[:20])
        return result[:20]
    except Exception as e:
        logger.warning(f"获取热门股票失败: {e}")
        return []


def preload_market_data():
    """后台预加载市场数据"""
    def _load():
        logger.info("🔄 预加载市场数据...")
        try:
            result = get_market_top_cached()
            logger.info(f"✅ 市场数据加载完成: {len(result)} 只股票")
        except Exception as e:
            logger.warning(f"❌ 市场数据加载失败: {e}")

    t = threading.Thread(target=_load, daemon=True)
    t.start()
