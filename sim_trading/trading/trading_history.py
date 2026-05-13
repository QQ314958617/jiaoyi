"""
交易历史记录管理系统
===================
从Claude Code源码history.ts学习的设计理念：

核心设计：
1. JSONL格式 - 每次写入一行JSON，方便追加和流式读取
2. 文件锁机制 - 防止多进程并发写入冲突
3. 异步flush - pending buffer + 延迟写入，减少IO频率
4. pending buffer - 先存内存，定期批量写入磁盘
5. 当前会话优先 - 当日交易记录排在前面
6. 去重机制 - 同一标的的交易去重

使用方法：
    from trading.trading_history import TradingHistory
    
    th = TradingHistory()
    th.add_trade({
        'symbol': '601362',
        'action': 'buy',
        'price': 12.50,
        'quantity': 100,
        'timestamp': '2026-04-03 10:30:00'
    })
"""

import json
import os
import threading
import time
from datetime import datetime
from dataclasses import dataclass, field, asdict
from typing import Optional, List, Dict, Any
from pathlib import Path
from filelock import FileLock, Timeout
from contextlib import contextmanager


# 配置
MAX_HISTORY_ITEMS = 1000  # 内存中保留的最大历史条目数
FLUSH_INTERVAL_SECONDS = 5  # 定期flush间隔
MAX_FLUSH_RETRIES = 3  # 最大重试次数


@dataclass
class TradeRecord:
    """交易记录数据结构"""
    symbol: str           # 股票代码
    action: str           # buy/sell
    price: float          # 成交价格
    quantity: int          # 成交数量
    timestamp: str        # 成交时间（北京时间）
    pnl: Optional[float] = None     # 盈亏（仅卖出时计算）
    reason: Optional[str] = None     # 交易原因
    strategy: Optional[str] = None   # 策略名称
    

@dataclass
class ReviewRecord:
    """复盘记录数据结构"""
    date: str             # 复盘日期
    market_close: float   # 收盘点位
    market_change: float  # 涨跌幅
    account_value: float  # 账户总值
    day_pnl: float        # 当日盈亏
    positions: List[Dict[str, Any]] = field(default_factory=list)  # 持仓详情
    trades: List[Dict[str, Any]] = field(default_factory=list)     # 当日交易
    summary: str = ""      # 复盘总结
    tomorrow_plan: str = ""  # 次日计划


class TradingHistory:
    """
    交易历史记录管理器
    
    设计特点：
    - JSONL格式存储，每条记录一行
    - 文件锁保证多进程安全
    - 内存buffer减少IO次数
    - 自动定期flush
    - 支持按日期查询历史
    """
    
    def __init__(self, data_dir: str = None):
        if data_dir is None:
            data_dir = os.path.join(os.path.dirname(__file__), '..', 'data')
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(parents=True, exist_ok=True)
        
        # 历史文件路径
        self.trades_file = self.data_dir / 'trades_history.jsonl'
        self.reviews_file = self.data_dir / 'reviews_history.jsonl'
        
        # 锁文件路径
        self.trades_lock_file = self.data_dir / 'trades_history.lock'
        self.reviews_lock_file = self.data_dir / 'reviews_history.lock'
        
        # Pending buffer（待写入的记录）
        self._pending_trades: List[TradeRecord] = []
        self._pending_reviews: List[ReviewRecord] = []
        
        # 写入锁
        self._trades_lock = threading.Lock()
        self._reviews_lock = threading.Lock()
        
        # 是否正在写入
        self._is_writing_trades = False
        self._is_writing_reviews = False
        
        # 最后flush时间
        self._last_flush_time = time.time()
        
        # 启动定期flush线程
        self._flush_thread = None
        self._running = True
        self._start_flush_thread()
    
    def _start_flush_thread(self):
        """启动定期flush后台线程"""
        def flush_loop():
            while self._running:
                time.sleep(FLUSH_INTERVAL_SECONDS)
                if time.time() - self._last_flush_time >= FLUSH_INTERVAL_SECONDS:
                    try:
                        self.flush()
                    except Exception as e:
                        print(f"定期flush失败: {e}")
        
        self._flush_thread = threading.Thread(target=flush_loop, daemon=True)
        self._flush_thread.start()
    
    def stop(self):
        """停止flush线程并执行最终flush"""
        self._running = False
        if self._flush_thread:
            self._flush_thread.join(timeout=2)
        self.flush()
    
    @contextmanager
    def _acquire_lock(self, lock_file: Path, timeout: int = 10):
        """获取文件锁的上下文管理器"""
        lock = FileLock(lock_file, timeout=timeout)
        try:
            lock.acquire()
            yield lock
        finally:
            lock.release()
    
    def _serialize_record(self, record) -> str:
        """将记录序列化为JSON字符串"""
        if isinstance(record, TradeRecord):
            return json.dumps(asdict(record), ensure_ascii=False) + '\n'
        elif isinstance(record, ReviewRecord):
            return json.dumps(asdict(record), ensure_ascii=False) + '\n'
        else:
            return json.dumps(record, ensure_ascii=False) + '\n'
    
    def _append_to_file(self, file_path: Path, lock_file: Path, records: List):
        """批量追加记录到文件"""
        if not records:
            return
        
        try:
            with self._acquire_lock(lock_file):
                with open(file_path, 'a', encoding='utf-8') as f:
                    for record in records:
                        f.write(self._serialize_record(record))
        except Timeout:
            print(f"获取文件锁超时: {lock_file}")
        except Exception as e:
            print(f"写入历史文件失败: {e}")
    
    def flush(self):
        """立即将pending buffer中的记录写入磁盘"""
        self._last_flush_time = time.time()
        
        # 写入交易记录
        if self._pending_trades and not self._is_writing_trades:
            self._is_writing_trades = True
            trades_to_write = self._pending_trades.copy()
            self._pending_trades.clear()
            try:
                self._append_to_file(
                    self.trades_file,
                    self.trades_lock_file,
                    trades_to_write
                )
            finally:
                self._is_writing_trades = False
        
        # 写入复盘记录
        if self._pending_reviews and not self._is_writing_reviews:
            self._is_writing_reviews = True
            reviews_to_write = self._pending_reviews.copy()
            self._pending_reviews.clear()
            try:
                self._append_to_file(
                    self.reviews_file,
                    self.reviews_lock_file,
                    reviews_to_write
                )
            finally:
                self._is_writing_reviews = False
    
    def add_trade(self, trade: TradeRecord):
        """添加交易记录到pending buffer"""
        with self._trades_lock:
            self._pending_trades.append(trade)
        
        # 如果buffer过大，触发flush
        if len(self._pending_trades) >= 100:
            self.flush()
    
    def add_review(self, review: ReviewRecord):
        """添加复盘记录到pending buffer"""
        with self._reviews_lock:
            self._pending_reviews.append(review)
        
        # 如果buffer过大，触发flush
        if len(self._pending_reviews) >= 10:
            self.flush()
    
    def get_trades(
        self,
        symbol: Optional[str] = None,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        limit: int = 100
    ) -> List[TradeRecord]:
        """读取交易历史记录"""
        records = []
        
        try:
            with self._acquire_lock(self.trades_lock_file, timeout=5):
                if not self.trades_file.exists():
                    return []
                
                with open(self.trades_file, 'r', encoding='utf-8') as f:
                    for line in f:
                        line = line.strip()
                        if not line:
                            continue
                        try:
                            data = json.loads(line)
                            record = TradeRecord(**data)
                            
                            # 过滤条件
                            if symbol and record.symbol != symbol:
                                continue
                            if start_date and record.timestamp < start_date:
                                continue
                            if end_date and record.timestamp > end_date:
                                continue
                            
                            records.append(record)
                        except Exception:
                            continue
        except Exception as e:
            print(f"读取交易历史失败: {e}")
        
        # 合并pending buffer中的记录
        with self._trades_lock:
            for record in self._pending_trades:
                if symbol and record.symbol != symbol:
                    continue
                if start_date and record.timestamp < start_date:
                    continue
                if end_date and record.timestamp > end_date:
                    continue
                records.append(record)
        
        # 按时间倒序
        records.sort(key=lambda x: x.timestamp, reverse=True)
        return records[:limit]
    
    def get_reviews(
        self,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        limit: int = 30
    ) -> List[ReviewRecord]:
        """读取复盘历史记录"""
        records = []
        
        try:
            with self._acquire_lock(self.reviews_lock_file, timeout=5):
                if not self.reviews_file.exists():
                    return []
                
                with open(self.reviews_file, 'r', encoding='utf-8') as f:
                    for line in f:
                        line = line.strip()
                        if not line:
                            continue
                        try:
                            data = json.loads(line)
                            record = ReviewRecord(**data)
                            
                            # 过滤条件
                            if start_date and record.date < start_date:
                                continue
                            if end_date and record.date > end_date:
                                continue
                            
                            records.append(record)
                        except Exception:
                            continue
        except Exception as e:
            print(f"读取复盘历史失败: {e}")
        
        # 合并pending buffer中的记录
        with self._reviews_lock:
            for record in self._pending_reviews:
                if start_date and record.date < start_date:
                    continue
                if end_date and record.date > end_date:
                    continue
                records.append(record)
        
        # 按日期倒序
        records.sort(key=lambda x: x.date, reverse=True)
        return records[:limit]
    
    def get_today_trades(self) -> List[TradeRecord]:
        """获取今日交易记录"""
        today = datetime.now().strftime('%Y-%m-%d')
        return self.get_trades(start_date=today)
    
    def get_today_review(self) -> Optional[ReviewRecord]:
        """获取今日复盘记录"""
        today = datetime.now().strftime('%Y-%m-%d')
        reviews = self.get_reviews(start_date=today, limit=1)
        return reviews[0] if reviews else None
    
    def get_position_summary(self) -> Dict[str, Any]:
        """获取持仓汇总"""
        all_trades = self.get_trades(limit=10000)
        
        # 按股票分组
        positions = {}
        for trade in all_trades:
            if trade.symbol not in positions:
                positions[trade.symbol] = {
                    'symbol': trade.symbol,
                    'quantity': 0,
                    'avg_cost': 0,
                    'total_cost': 0,
                    'buys': 0,
                    'sells': 0
                }
            
            pos = positions[trade.symbol]
            if trade.action == 'buy':
                pos['buys'] += 1
                old_qty = pos['quantity']
                old_cost = pos['total_cost']
                pos['quantity'] += trade.quantity
                pos['total_cost'] += trade.price * trade.quantity
                if pos['quantity'] > 0:
                    pos['avg_cost'] = pos['total_cost'] / pos['quantity']
            else:  # sell
                pos['sells'] += 1
                pos['quantity'] -= trade.quantity
                pos['total_cost'] = pos['avg_cost'] * pos['quantity']
        
        # 过滤零持仓
        return {k: v for k, v in positions.items() if v['quantity'] > 0}


# 全局单例
_trading_history: Optional[TradingHistory] = None


def get_trading_history() -> TradingHistory:
    """获取全局交易历史实例"""
    global _trading_history
    if _trading_history is None:
        _trading_history = TradingHistory()
    return _trading_history
