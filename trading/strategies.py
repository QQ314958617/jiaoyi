"""
蛋蛋的交易策略库
"""
import random
import pandas as pd
import akshare as ak
from datetime import datetime, date

class Strategy:
    """策略基类"""
    def __init__(self, name, description):
        self.name = name
        self.description = description
    
    def analyze(self, stock_code):
        """分析返回买入/卖出/持有信号"""
        raise NotImplementedError

# ========== 策略1: 均线金叉死叉 ==========
class MAcrossStrategy(Strategy):
    """均线金叉死叉策略"""
    def __init__(self):
        super().__init__("均线交叉", "MA5上穿MA20买入，下穿卖出")
    
    def analyze(self, stock_code):
        try:
            df = ak.stock_zh_a_hist(symbol=stock_code, period="daily", adjust="qfq", count=30)
            df = df.tail(20).copy()
            
            ma5 = df['收盘'].rolling(5).mean().iloc[-1]
            ma20 = df['收盘'].rolling(20).mean().iloc[-1]
            ma5_prev = df['收盘'].rolling(5).mean().iloc[-2]
            ma20_prev = df['收盘'].rolling(20).mean().iloc[-2]
            
            # 金叉: MA5从下方穿越MA20
            if ma5_prev < ma20_prev and ma5 > ma20:
                return {'signal': 'buy', 'reason': f'MA5({ma5:.2f})上穿MA20({ma20:.2f})金叉', 'score': 75}
            # 死叉: MA5从上方穿越MA20
            elif ma5_prev > ma20_prev and ma5 < ma20:
                return {'signal': 'sell', 'reason': f'MA5({ma5:.2f})下穿MA20({ma20:.2f})死叉', 'score': 70}
            else:
                return {'signal': 'hold', 'reason': f'MA5={ma5:.2f}, MA20={ma20:.2f}', 'score': 50}
        except Exception as e:
            return {'signal': 'hold', 'reason': f'分析失败: {str(e)}', 'score': 50}

# ========== 策略2: RSI超买超卖 ==========
class RSIStrategy(Strategy):
    """RSI均值回归策略"""
    def __init__(self):
        super().__init__("RSI超买超卖", "RSI<30超卖买入，RSI>70超买卖出")
    
    def analyze(self, stock_code):
        try:
            df = ak.stock_zh_a_hist(symbol=stock_code, period="daily", adjust="qfq", count=14)
            delta = df['收盘'].diff()
            gain = (delta.where(delta > 0, 0)).rolling(14).mean()
            loss = (-delta.where(delta < 0, 0)).rolling(14).mean()
            rs = gain / loss
            rsi = 100 - (100 / (1 + rs))
            rsi_value = rsi.iloc[-1]
            
            if rsi_value < 30:
                return {'signal': 'buy', 'reason': f'RSI({rsi_value:.2f})超卖', 'score': 80}
            elif rsi_value > 70:
                return {'signal': 'sell', 'reason': f'RSI({rsi_value:.2f})超买', 'score': 80}
            else:
                return {'signal': 'hold', 'reason': f'RSI={rsi_value:.2f}', 'score': 50}
        except Exception as e:
            return {'signal': 'hold', 'reason': f'分析失败: {str(e)}', 'score': 50}

# ========== 策略3: 成交量异动 ==========
class VolumeStrategy(Strategy):
    """成交量异动策略"""
    def __init__(self):
        super().__init__("成交量异动", "成交量突增3倍且股价上涨买入")
    
    def analyze(self, stock_code):
        try:
            df = ak.stock_zh_a_hist(symbol=stock_code, period="daily", adjust="qfq", count=10)
            avg_volume = df['成交量'].tail(5).mean()
            today_volume = df['成交量'].iloc[-1]
            today_change = df['收盘'].iloc[-1] / df['收盘'].iloc[-2] - 1
            
            if today_volume > avg_volume * 3 and today_change > 0.02:
                return {'signal': 'buy', 'reason': f'成交量突增{(today_volume/avg_volume):.1f}倍, 涨幅{today_change*100:.2f}%', 'score': 75}
            elif today_volume > avg_volume * 2 and today_change < -0.02:
                return {'signal': 'sell', 'reason': f'成交量突增{(today_volume/avg_volume):.1f}倍, 跌幅{today_change*100:.2f}%', 'score': 70}
            else:
                return {'signal': 'hold', 'reason': f'成交量正常', 'score': 50}
        except Exception as e:
            return {'signal': 'hold', 'reason': f'分析失败: {str(e)}', 'score': 50}

# ========== 策略4: 网格交易 ==========
class GridStrategy(Strategy):
    """网格交易策略"""
    def __init__(self, grid_pct=0.02):
        super().__init__("网格交易", f"涨{grid_pct*100:.0f}%卖，跌{grid_pct*100:.0f}%买")
        self.grid_pct = grid_pct
    
    def analyze(self, stock_code, position):
        """position包含成本价和持仓"""
        try:
            df = ak.stock_zh_a_hist(symbol=stock_code, period="daily", adjust="qfq", count=5)
            current_price = df['收盘'].iloc[-1]
            cost = position.get('avg_cost', current_price)
            change = current_price / cost - 1
            
            if change >= self.grid_pct:
                return {'signal': 'sell', 'reason': f'上涨{change*100:.2f}%, 触及网格卖出线', 'score': 70}
            elif change <= -self.grid_pct:
                return {'signal': 'buy', 'reason': f'下跌{abs(change)*100:.2f}%, 触及网格买入线', 'score': 70}
            else:
                return {'signal': 'hold', 'reason': f'偏离成本{change*100:.2f}%', 'score': 50}
        except Exception as e:
            return {'signal': 'hold', 'reason': f'分析失败: {str(e)}', 'score': 50}

# ========== 策略5: 趋势跟随 ==========
class TrendStrategy(Strategy):
    """趋势跟随策略"""
    def __init__(self):
        super().__init__("趋势跟随", "股价站上20日线且20日线上倾买入")
    
    def analyze(self, stock_code):
        try:
            df = ak.stock_zh_a_hist(symbol=stock_code, period="daily", adjust="qfq", count=25)
            ma20 = df['收盘'].rolling(20).mean()
            ma20_current = ma20.iloc[-1]
            ma20_prev = ma20.iloc[-5]  # 5天前的MA20
            current_price = df['收盘'].iloc[-1]
            
            if current_price > ma20_current and ma20_current > ma20_prev:
                return {'signal': 'buy', 'reason': f'股价({current_price})站上20日线({ma20_current:.2f}), 趋势向上', 'score': 75}
            elif current_price < ma20_current:
                return {'signal': 'sell', 'reason': f'股价({current_price})跌破20日线({ma20_current:.2f})', 'score': 70}
            else:
                return {'signal': 'hold', 'reason': f'价格在20日线附近震荡', 'score': 50}
        except Exception as e:
            return {'signal': 'hold', 'reason': f'分析失败: {str(e)}', 'score': 50}

# ========== 策略管理器 ==========
class StrategyManager:
    """策略管理器"""
    def __init__(self):
        self.strategies = [
            MAcrossStrategy(),
            RSIStrategy(),
            VolumeStrategy(),
            TrendStrategy(),
            GridStrategy()
        ]
    
    def get_strategy(self, name):
        for s in self.strategies:
            if s.name == name:
                return s
        return None
    
    def analyze_all(self, stock_code, position=None):
        """综合所有策略分析"""
        results = []
        for s in self.strategies:
            if isinstance(s, GridStrategy) and position:
                result = s.analyze(stock_code, position)
            else:
                result = s.analyze(stock_code)
            result['strategy'] = s.name
            results.append(result)
        return results
    
    def get_best_signal(self, stock_code, position=None):
        """获取最佳信号"""
        results = self.analyze_all(stock_code, position)
        
        buy_signals = [r for r in results if r['signal'] == 'buy']
        sell_signals = [r for r in results if r['signal'] == 'sell']
        
        if buy_signals:
            best = max(buy_signals, key=lambda x: x['score'])
            return {'action': 'buy', 'strategy': best['strategy'], 'reason': best['reason'], 'score': best['score']}
        elif sell_signals:
            best = max(sell_signals, key=lambda x: x['score'])
            return {'action': 'sell', 'strategy': best['strategy'], 'reason': best['reason'], 'score': best['score']}
        else:
            return {'action': 'hold', 'strategy': '-', 'reason': '无策略触发', 'score': 50}
