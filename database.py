"""
数据库层 - SQLite
"""
import sqlite3
import os
from datetime import datetime, timezone, timedelta
from contextlib import contextmanager

DATABASE_FILE = os.path.join(os.path.dirname(__file__), 'data', 'trading.db')

def get_db_path():
    os.makedirs(os.path.dirname(DATABASE_FILE), exist_ok=True)
    return DATABASE_FILE

@contextmanager
def get_connection():
    """数据库连接上下文管理器"""
    conn = sqlite3.connect(get_db_path())
    conn.row_factory = sqlite3.Row
    try:
        yield conn
        conn.commit()
    except Exception as e:
        conn.rollback()
        raise e
    finally:
        conn.close()

def init_database():
    """初始化数据库表"""
    with get_connection() as conn:
        c = conn.cursor()
        
        # 账户表
        c.execute('''
            CREATE TABLE IF NOT EXISTS account (
                id INTEGER PRIMARY KEY,
                cash REAL DEFAULT 50000.0,
                total_value REAL DEFAULT 50000.0,
                total_profit REAL DEFAULT 0.0,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                updated_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # 持仓表
        c.execute('''
            CREATE TABLE IF NOT EXISTS positions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                stock_code TEXT NOT NULL,
                stock_name TEXT,
                shares INTEGER,
                avg_cost REAL,
                buy_date TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(stock_code)
            )
        ''')
        
        # 交易记录表
        c.execute('''
            CREATE TABLE IF NOT EXISTS trades (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT DEFAULT CURRENT_TIMESTAMP,
                action TEXT NOT NULL,
                stock_code TEXT NOT NULL,
                stock_name TEXT,
                price REAL,
                shares INTEGER,
                amount REAL,
                commission REAL DEFAULT 0,
                profit REAL DEFAULT 0,
                reason TEXT
            )
        ''')
        
        # 每日复盘表
        c.execute('''
            CREATE TABLE IF NOT EXISTS daily_reviews (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                date TEXT NOT NULL,
                timestamp TEXT DEFAULT CURRENT_TIMESTAMP,
                content TEXT,
                strategies TEXT,
                profit REAL DEFAULT 0,
                tags TEXT
            )
        ''')
        
        # 账户净值历史（用于画曲线）
        c.execute('''
            CREATE TABLE IF NOT EXISTS equity_curve (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                date TEXT NOT NULL,
                total_value REAL,
                cash REAL,
                position_value REAL,
                timestamp TEXT DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # 初始化账户（如果不存在）
        bj_tz = timezone(timedelta(hours=8))
        now_bj = datetime.now(bj_tz).strftime('%Y-%m-%d %H:%M:%S')
        c.execute('SELECT COUNT(*) FROM account')
        if c.fetchone()[0] == 0:
            c.execute('INSERT INTO account (id, cash, total_value, created_at, updated_at) VALUES (1, 50000.0, 50000.0, ?, ?)',
                      (now_bj, now_bj))
        
        conn.commit()

# ========== 账户操作 ==========

def get_account():
    """获取账户信息"""
    with get_connection() as conn:
        c = conn.cursor()
        c.execute('SELECT * FROM account WHERE id = 1')
        row = c.fetchone()
        if row:
            return dict(row)
        return {'cash': 50000.0, 'total_value': 50000.0, 'total_profit': 0.0}

def update_account(cash, total_value, total_profit):
    """更新账户"""
    bj_tz = timezone(timedelta(hours=8))
    now_bj = datetime.now(bj_tz).strftime('%Y-%m-%d %H:%M:%S')
    
    with get_connection() as conn:
        c = conn.cursor()
        c.execute('''
            UPDATE account 
            SET cash = ?, total_value = ?, total_profit = ?, updated_at = ?
            WHERE id = 1
        ''', (cash, total_value, total_profit, now_bj))
        conn.commit()

# ========== 持仓操作 ==========

def get_positions():
    """获取所有持仓"""
    with get_connection() as conn:
        c = conn.cursor()
        c.execute('SELECT * FROM positions')
        return [dict(row) for row in c.fetchall()]

def get_position(stock_code):
    """获取单只股票持仓"""
    with get_connection() as conn:
        c = conn.cursor()
        c.execute('SELECT * FROM positions WHERE stock_code = ?', (stock_code,))
        row = c.fetchone()
        return dict(row) if row else None

def upsert_position(stock_code, stock_name, shares, avg_cost, buy_date=None):
    """更新持仓（插入或更新）"""
    bj_tz = timezone(timedelta(hours=8))
    now_bj = datetime.now(bj_tz).strftime('%Y-%m-%d %H:%M:%S')
    
    with get_connection() as conn:
        c = conn.cursor()
        c.execute('''
            INSERT INTO positions (stock_code, stock_name, shares, avg_cost, buy_date, created_at)
            VALUES (?, ?, ?, ?, ?, ?)
            ON CONFLICT(stock_code) DO UPDATE SET
                stock_name = excluded.stock_name,
                shares = excluded.shares,
                avg_cost = excluded.avg_cost
        ''', (stock_code, stock_name, shares, avg_cost, buy_date or now_bj, now_bj))
        conn.commit()

def delete_position(stock_code):
    """删除持仓"""
    with get_connection() as conn:
        c = conn.cursor()
        c.execute('DELETE FROM positions WHERE stock_code = ?', (stock_code,))
        conn.commit()

# ========== 交易记录 ==========

def add_trade(action, stock_code, stock_name, price, shares, amount, commission=0, profit=0, reason=''):
    """添加交易记录"""
    bj_tz = timezone(timedelta(hours=8))
    bj_time = datetime.now(bj_tz).strftime('%Y-%m-%d %H:%M:%S')
    
    with get_connection() as conn:
        c = conn.cursor()
        c.execute('''
            INSERT INTO trades (action, stock_code, stock_name, price, shares, amount, commission, profit, reason, timestamp)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (action, stock_code, stock_name, price, shares, amount, commission, profit, reason, bj_time))
        conn.commit()
        return c.lastrowid

def get_trades(limit=100):
    """获取交易记录"""
    with get_connection() as conn:
        c = conn.cursor()
        c.execute('SELECT * FROM trades ORDER BY timestamp DESC LIMIT ?', (limit,))
        return [dict(row) for row in c.fetchall()]

# ========== 复盘记录 ==========

def add_review(date, content, strategies='', profit=0, tags=''):
    """添加复盘"""
    # 使用北京时间（SQLite的CURRENT_TIMESTAMP是UTC，需要显式传入）
    bj_tz = timezone(timedelta(hours=8))
    bj_time = datetime.now(bj_tz).strftime('%Y-%m-%d %H:%M:%S')
    
    with get_connection() as conn:
        c = conn.cursor()
        c.execute('''
            INSERT INTO daily_reviews (date, content, strategies, profit, tags, timestamp)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (date, content, strategies, profit, tags, bj_time))
        conn.commit()
        return c.lastrowid

def get_reviews(limit=50):
    """获取复盘记录"""
    with get_connection() as conn:
        c = conn.cursor()
        c.execute('SELECT * FROM daily_reviews ORDER BY timestamp DESC LIMIT ?', (limit,))
        return [dict(row) for row in c.fetchall()]

def get_reviews_paged(offset=0, limit=10):
    """获取复盘记录（分页）"""
    with get_connection() as conn:
        c = conn.cursor()
        c.execute('SELECT COUNT(*) FROM daily_reviews')
        total = c.fetchone()[0]
        c.execute('SELECT * FROM daily_reviews ORDER BY timestamp DESC LIMIT ? OFFSET ?', (limit, offset))
        return total, [dict(row) for row in c.fetchall()]

# ========== 净值曲线 ==========

def add_equity_record(date, total_value, cash, position_value):
    """记录净值"""
    bj_tz = timezone(timedelta(hours=8))
    bj_time = datetime.now(bj_tz).strftime('%Y-%m-%d %H:%M:%S')
    
    with get_connection() as conn:
        c = conn.cursor()
        c.execute('''
            INSERT INTO equity_curve (date, total_value, cash, position_value, timestamp)
            VALUES (?, ?, ?, ?, ?)
        ''', (date, total_value, cash, position_value, bj_time))
        conn.commit()

def get_equity_curve(days=30):
    """获取净值曲线数据"""
    with get_connection() as conn:
        c = conn.cursor()
        c.execute('''
            SELECT * FROM equity_curve 
            ORDER BY date DESC 
            LIMIT ?
        ''', (days,))
        return [dict(row) for row in c.fetchall()]

# ========== 统计分析 ==========

def get_trade_stats():
    """获取交易统计"""
    with get_connection() as conn:
        c = conn.cursor()
        # 总交易次数
        c.execute('SELECT COUNT(*) FROM trades')
        total_trades = c.fetchone()[0]
        # 盈利次数
        c.execute("SELECT COUNT(*) FROM trades WHERE profit > 0")
        win_trades = c.fetchone()[0]
        # 总盈利
        c.execute('SELECT SUM(profit) FROM trades WHERE profit > 0')
        total_profit = c.fetchone()[0] or 0
        # 总亏损
        c.execute('SELECT SUM(ABS(profit)) FROM trades WHERE profit < 0')
        total_loss = c.fetchone()[0] or 0
        
        return {
            'total_trades': total_trades,
            'win_trades': win_trades,
            'win_rate': round(win_trades / total_trades * 100, 2) if total_trades > 0 else 0,
            'total_profit': total_profit,
            'total_loss': total_loss,
            'net_profit': total_profit - total_loss
        }
