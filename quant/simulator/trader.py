"""
AI量化交易执行系统 v1.0
======================
负责：
1. 买入/卖出执行
2. 持仓管理
3. 交易记录
4. 止损/止盈管理
"""

import json
import os
from datetime import datetime
from pathlib import Path

ACCOUNT_FILE = '/root/.openclaw/workspace/quant/simulator/account.json'
TRADE_LOG_FILE = '/root/.openclaw/workspace/quant/simulator/logs/trades.json'
POSITIONS_FILE = '/root/.openclaw/workspace/quant/simulator/positions/positions.json'

def load_account():
    """加载账户信息"""
    with open(ACCOUNT_FILE, 'r') as f:
        return json.load(f)

def save_account(account):
    """保存账户信息"""
    with open(ACCOUNT_FILE, 'w') as f:
        json.dump(account, f, indent=2, ensure_ascii=False)

def load_trades():
    """加载交易记录"""
    if os.path.exists(TRADE_LOG_FILE):
        with open(TRADE_LOG_FILE, 'r') as f:
            return json.load(f)
    return []

def save_trades(trades):
    """保存交易记录"""
    os.makedirs(os.path.dirname(TRADE_LOG_FILE), exist_ok=True)
    with open(TRADE_LOG_FILE, 'w') as f:
        json.dump(trades, f, indent=2, ensure_ascii=False)

def load_positions():
    """加载持仓"""
    if os.path.exists(POSITIONS_FILE):
        with open(POSITIONS_FILE, 'r') as f:
            return json.load(f)
    return {}

def save_positions(positions):
    """保存持仓"""
    os.makedirs(os.path.dirname(POSITIONS_FILE), exist_ok=True)
    with open(POSITIONS_FILE, 'w') as f:
        json.dump(positions, f, indent=2, ensure_ascii=False)

def update_total_value(stock_prices):
    """更新账户总市值"""
    account = load_account()
    positions = load_positions()
    
    total_value = account['cash']
    for code, pos in positions.items():
        price = stock_prices.get(code, pos['cost'])
        pos_value = price * pos['shares']
        total_value += pos_value
    
    account['total_value'] = round(total_value, 2)
    account['total_profit'] = round(total_value - account['init_cash'], 2)
    account['total_profit_rate'] = round((total_value / account['init_cash'] - 1) * 100, 2)
    
    save_account(account)
    return account

def buy_stock(code, name, price, shares, reason=""):
    """买入股票"""
    account = load_account()
    positions = load_positions()
    trades = load_trades()
    
    cost = price * shares
    commission = cost * 0.0003  # 万三佣金
    stamp_tax = cost * 0.001  # 千一印花税（卖时收取）
    total_cost = cost + commission
    
    if total_cost > account['cash']:
        print(f"❌ 资金不足！需要 {total_cost:.2f}，可用 {account['cash']:.2f}")
        return False
    
    # 扣除资金
    account['cash'] = round(account['cash'] - total_cost, 2)
    
    # 添加持仓
    if code in positions:
        # 补仓：计算新的平均成本
        old_shares = positions[code]['shares']
        old_cost = positions[code]['cost'] * old_shares
        new_cost = price * shares
        new_avg_cost = (old_cost + new_cost) / (old_shares + shares)
        positions[code]['shares'] = old_shares + shares
        positions[code]['cost'] = round(new_avg_cost, 3)
        positions[code]['times'] += 1
    else:
        positions[code] = {
            'name': name,
            'shares': shares,
            'cost': round(price, 3),
            'buy_price': round(price, 2),
            'times': 1,
            'first_buy_date': datetime.now().strftime('%Y-%m-%d')
        }
    
    # 记录交易
    trade = {
        'id': len(trades) + 1,
        'date': datetime.now().strftime('%Y-%m-%d %H:%M'),
        'action': 'BUY',
        'code': code,
        'name': name,
        'price': price,
        'shares': shares,
        'cost': round(cost, 2),
        'commission': round(commission, 2),
        'reason': reason,
        'profit': 0
    }
    trades.append(trade)
    
    # 保存
    save_account(account)
    save_positions(positions)
    save_trades(trades)
    
    print(f"\n✅ 买入成功！")
    print(f"   股票: {name}({code})")
    print(f"   价格: {price}")
    print(f"   数量: {shares}股")
    print(f"   成本: {cost:.2f}")
    print(f"   佣金: {commission:.2f}")
    print(f"   买入理由: {reason}")
    print(f"   剩余资金: {account['cash']:.2f}")
    
    return True

def sell_stock(code, reason="技术信号"):
    """卖出股票"""
    account = load_account()
    positions = load_positions()
    trades = load_trades()
    
    if code not in positions:
        print(f"❌ 你没有持有 {code}")
        return False
    
    import akshare as ak
    # 获取最新价格
    try:
        if code.startswith('6'):
            symbol = f"sh{code}"
        else:
            symbol = f"sz{code}"
        df = ak.stock_zh_a_hist(symbol=code, period="daily", 
                                 start_date=(datetime.now()-timedelta(days=7)).strftime('%Y%m%d'),
                                 end_date=datetime.now().strftime('%Y%m%d'))
        price = float(df.iloc[-1]['收盘'])
    except:
        price = positions[code]['cost']  # 如果获取失败，用成本价
    
    pos = positions[code]
    shares = pos['shares']
    cost = pos['cost'] * shares
    sell_value = price * shares
    commission = sell_value * 0.0003
    stamp_tax = sell_value * 0.001
    net_value = sell_value - commission - stamp_tax
    
    profit = net_value - cost
    profit_rate = (price / pos['cost'] - 1) * 100
    
    # 更新资金
    account['cash'] = round(account['cash'] + net_value, 2)
    
    # 记录交易
    trade = {
        'id': len(trades) + 1,
        'date': datetime.now().strftime('%Y-%m-%d %H:%M'),
        'action': 'SELL',
        'code': code,
        'name': pos['name'],
        'price': price,
        'shares': shares,
        'cost': round(cost, 2),
        'sell_value': round(sell_value, 2),
        'commission': round(commission, 2),
        'stamp_tax': round(stamp_tax, 2),
        'profit': round(profit, 2),
        'profit_rate': round(profit_rate, 2),
        'reason': reason,
        'hold_days': (datetime.now() - datetime.strptime(pos['first_buy_date'], '%Y-%m-%d')).days
    }
    trades.append(trade)
    
    # 删除持仓
    del positions[code]
    
    # 保存
    save_account(account)
    save_positions(positions)
    save_trades(trades)
    
    emoji = "🎉" if profit > 0 else "😢"
    print(f"\n{emoji} 卖出完成！")
    print(f"   股票: {pos['name']}({code})")
    print(f"   卖出价格: {price}")
    print(f"   持有天数: {trade['hold_days']}天")
    print(f"   收益率: {profit_rate:+.2f}%")
    print(f"   盈利金额: {profit:+.2f}")
    print(f"   卖出理由: {reason}")
    print(f"   剩余资金: {account['cash']:.2f}")
    
    return True

def show_positions(stock_prices=None):
    """显示当前持仓"""
    positions = load_positions()
    account = load_account()
    
    print("\n" + "="*70)
    print("📊 当前持仓".center(50))
    print("="*70)
    
    if not positions:
        print("  空仓中...")
    else:
        print(f"{'代码':<8}{'名称':<10}{'持仓':<6}{'成本':<10}{'现价':<10}{'盈亏%':<10}{'盈亏额':<10}")
        print("-"*70)
        
        total_profit = 0
        for code, pos in positions.items():
            price = stock_prices.get(code, pos['cost']) if stock_prices else pos['cost']
            profit = (price - pos['cost']) * pos['shares']
            profit_rate = (price / pos['cost'] - 1) * 100
            total_profit += profit
            
            emoji = "🟢" if profit > 0 else "🔴" if profit < 0 else "⚪"
            print(f"{code:<8}{pos['name']:<10}{pos['shares']:<6}{pos['cost']:<10.2f}{price:<10.2f}{profit_rate:>+7.2f}%  {profit:>+10.2f}")
    
    print("-"*70)
    print(f"  持仓盈亏: {total_profit:+.2f}")
    print(f"  可用资金: {account['cash']:.2f}")
    print(f"  总市值: {account['total_value']:.2f}")
    print(f"  总收益率: {account['total_profit_rate']:+.2f}%")
    print(f"  初始资金: {account['init_cash']:.2f}")
    print("="*70)
    
    return positions

def show_trades():
    """显示交易记录"""
    trades = load_trades()
    
    print("\n" + "="*70)
    print("📜 交易记录".center(50))
    print("="*70)
    
    if not trades:
        print("  暂无交易记录")
    else:
        for trade in trades[-10:]:  # 显示最近10条
            if trade['action'] == 'BUY':
                print(f"  📅 {trade['date']} | 买入 | {trade['name']}({trade['code']}) | {trade['price']} x {trade['shares']} | 原因: {trade['reason']}")
            else:
                print(f"  📅 {trade['date']} | 卖出 | {trade['name']}({trade['code']}) | {trade['price']} x {trade['shares']} | 盈亏: {trade['profit']:+.2f}({trade['profit_rate']:+.2f}%) | 持有{trade.get('hold_days', '?')}天")
    
    # 统计
    buy_count = len([t for t in trades if t['action'] == 'BUY'])
    sell_count = len([t for t in trades if t['action'] == 'SELL'])
    total_profit = sum([t.get('profit', 0) for t in trades if t['action'] == 'SELL'])
    
    print(f"\n  总交易次数: {len(trades)} | 买入: {buy_count} | 卖出: {sell_count}")
    print(f"  已实现盈亏: {total_profit:+.2f}")
    print("="*70)
    
    return trades

def check_stop_loss():
    """检查止损信号"""
    positions = load_positions()
    signals = []
    
    import akshare as ak
    from datetime import timedelta
    
    for code, pos in positions.items():
        try:
            if code.startswith('6'):
                symbol = f"sh{code}"
            else:
                symbol = f"sz{code}"
            
            df = ak.stock_zh_a_hist(symbol=code, period="daily", 
                                     start_date=(datetime.now()-timedelta(days=30)).strftime('%Y%m%d'),
                                     end_date=datetime.now().strftime('%Y%m%d'))
            
            prices = df['收盘'].astype(float)
            current_price = prices.iloc[-1]
            
            # 止损条件1：亏损超过8%
            if current_price < pos['cost'] * 0.92:
                signals.append({
                    'code': code,
                    'name': pos['name'],
                    'type': '止损',
                    'reason': f"亏损超过8% ({((current_price/pos['cost']-1)*100):.1f}%)",
                    'action': 'SELL'
                })
            
            # 止盈条件：盈利超过20%
            elif current_price > pos['cost'] * 1.20:
                signals.append({
                    'code': code,
                    'name': pos['name'],
                    'type': '止盈',
                    'reason': f"盈利超过20% ({((current_price/pos['cost']-1)*100):.1f}%)",
                    'action': 'SELL'
                })
            
            # RSI超买信号
            from selector import calc_rsi
            rsi = calc_rsi(prices, 14).iloc[-1]
            if rsi > 85:
                signals.append({
                    'code': code,
                    'name': pos['name'],
                    'type': '风险提醒',
                    'reason': f"RSI严重超买({rsi:.0f})",
                    'action': 'CONSIDER_SELL'
                })
                
        except Exception as e:
            print(f"检查 {code} 失败: {e}")
    
    return signals

if __name__ == "__main__":
    print("="*70)
    print("🤖 AI量化交易系统 | 交易时间: {}".format(datetime.now().strftime('%Y-%m-%d %H:%M')))
    print("="*70)
    
    show_positions()
    show_trades()
