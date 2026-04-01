#!/usr/bin/env python3
"""
AI量化交易系统 - 主入口
======================
功能：
1. 每日选股扫描
2. 执行交易
3. 检查持仓状态
4. 生成复盘报告

使用方法：
    python3 main.py [command]

Commands:
    scan    - 扫描市场选股
    trade   - 执行交易
    status  - 查看持仓状态
    review  - 生成复盘报告
    all     - 执行全部流程
"""

import sys
import os

# 添加当前目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from selector import scan_market, print_analysis
from trader import show_positions, show_trades, buy_stock, sell_stock, check_stop_loss, update_total_value, load_positions, load_account
from reviewer import generate_daily_report, generate_weekly_summary
from datetime import datetime
import akshare as ak
import warnings
warnings.filterwarnings('ignore')

def get_realtime_prices(codes):
    """获取多个股票实时价格"""
    prices = {}
    for code in codes:
        try:
            if code.startswith('6'):
                symbol = f"sh{code}"
            else:
                symbol = f"sz{code}"
            df = ak.stock_zh_a_hist(symbol=code, period="daily", 
                                     start_date=(datetime.now()-timedelta(days=5)).strftime('%Y%m%d'),
                                     end_date=datetime.now().strftime('%Y%m%d'))
            prices[code] = float(df.iloc[-1]['收盘'])
        except:
            pass
    return prices

def auto_trade():
    """自动交易逻辑"""
    print("\n" + "="*70)
    print("🤖 AI自动交易执行".center(50))
    print("="*70)
    
    # 1. 检查持仓止损/止盈信号
    print("\n📋 检查持仓信号...")
    signals = check_stop_loss()
    
    if signals:
        print("\n⚠️ 发现以下信号:")
        for sig in signals:
            print(f"  {sig['type']}: {sig['name']}({sig['code']}) - {sig['reason']}")
        
        # 自动执行止损/止盈
        for sig in signals:
            if sig['action'] == 'SELL':
                print(f"\n🔴 自动卖出: {sig['name']} ({sig['reason']})")
                sell_stock(sig['code'], reason=f"{sig['type']}:{sig['reason']}")
    else:
        print("  持仓暂无止损/止盈信号")
    
    # 2. 更新账户市值
    positions = load_positions()
    if positions:
        prices = get_realtime_prices(list(positions.keys()))
        account = update_total_value(prices)
        print(f"\n💰 当前总市值: {account['total_value']:.2f} ({account['total_profit_rate']:+.2f}%)")
        show_positions(prices)
    
    # 3. 选股扫描
    print("\n" + "="*70)
    input("\n按回车继续扫描市场选股（Ctrl+C退出）...")
    
    print("\n" + "="*70)
    print("🔍 开始市场扫描选股...".center(50))
    print("="*70)
    
    results = scan_market(top_n=30)
    strong_buys, consider_buys = print_analysis(results)
    
    # 4. 根据评分执行买入
    account = load_account()
    available_cash = account['cash']
    
    print(f"\n💵 当前可用资金: {available_cash:.2f}")
    
    # 优先买入80分以上的
    if strong_buys and available_cash >= 10000:
        for stock in strong_buys[:2]:  # 最多买2只
            if available_cash < 10000:
                break
            
            # 检查是否已持仓
            positions = load_positions()
            if stock['code'] in positions:
                print(f"\n⚠️ {stock['name']} 已在持仓中，跳过")
                continue
            
            price = stock['price']
            # 每次买入1/3仓位
            shares = int(available_cash * 0.3 / price / 100) * 100  # 按手买
            
            if shares >= 100:
                reason = "; ".join(stock['reasons'][:3])
                print(f"\n🟢 买入: {stock['name']}({stock['code']})")
                print(f"   价格: {price} x {shares}股 = {price*shares:.2f}")
                buy_stock(stock['code'], stock['name'], price, shares, reason=reason)
                available_cash -= price * shares
            else:
                print(f"\n⚠️ 资金不足，无法买入 {stock['name']}")
    
    print("\n" + "="*70)
    print("✅ 今日交易完成！")
    print("="*70)
    
    # 5. 生成复盘
    generate_daily_report()

def show_status():
    """显示状态"""
    positions = load_positions()
    if positions:
        prices = get_realtime_prices(list(positions.keys()))
        update_total_value(prices)
        show_positions(prices)
    else:
        show_positions()
    show_trades()
    
    # 检查信号
    signals = check_stop_loss()
    if signals:
        print("\n⚠️ 持仓提醒:")
        for sig in signals:
            print(f"  {sig['type']}: {sig['name']} - {sig['reason']}")

def main():
    if len(sys.argv) < 2:
        # 默认执行全部流程
        cmd = 'all'
    else:
        cmd = sys.argv[1].lower()
    
    print("="*70)
    print(f"🤖 AI量化交易系统 | {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*70)
    
    if cmd == 'scan':
        results = scan_market(top_n=30)
        print_analysis(results)
    
    elif cmd == 'trade':
        auto_trade()
    
    elif cmd == 'status':
        show_status()
    
    elif cmd == 'review':
        generate_daily_report()
        print("\n" + generate_weekly_summary())
    
    elif cmd == 'all':
        show_status()
        auto_trade()
    
    else:
        print(f"未知命令: {cmd}")
        print(__doc__)

if __name__ == "__main__":
    main()
