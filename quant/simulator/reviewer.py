"""
AI量化每日复盘系统 v1.0
=======================
负责：
1. 每日操作复盘
2. 个股操作复盘
3. 选股复盘
4. 生成复盘报告
"""

import json
import os
from datetime import datetime, timedelta
from pathlib import Path

REPORTS_DIR = '/root/.openclaw/workspace/quant/simulator/reports'
TRADE_LOG_FILE = '/root/.openclaw/workspace/quant/simulator/logs/trades.json'
ACCOUNT_FILE = '/root/.openclaw/workspace/quant/simulator/account.json'
POSITIONS_FILE = '/root/.openclaw/workspace/quant/simulator/positions/positions.json'
DAILY_SCAN_FILE = '/root/.openclaw/workspace/quant/simulator/data/daily_scan.json'

def load_trades():
    with open(TRADE_LOG_FILE, 'r') as f:
        return json.load(f)

def load_account():
    with open(ACCOUNT_FILE, 'r') as f:
        return json.load(f)

def load_positions():
    if os.path.exists(POSITIONS_FILE):
        with open(POSITIONS_FILE, 'r') as f:
            return json.load(f)
    return {}

def load_daily_scan():
    if os.path.exists(DAILY_SCAN_FILE):
        with open(DAILY_SCAN_FILE, 'r') as f:
            return json.load(f)
    return {}

def generate_daily_report():
    """生成每日操作复盘报告"""
    trades = load_trades()
    account = load_account()
    positions = load_positions()
    scan_data = load_daily_scan()
    
    today = datetime.now().strftime('%Y-%m-%d')
    
    # 今日交易
    today_trades = [t for t in trades if t['date'].startswith(today)]
    today_buys = [t for t in today_trades if t['action'] == 'BUY']
    today_sells = [t for t in today_trades if t['action'] == 'SELL']
    
    # 最近7日交易
    week_ago = (datetime.now() - timedelta(days=7)).strftime('%Y-%m-%d')
    week_trades = [t for t in trades if t['date'] >= week_ago]
    
    # 所有卖出及盈亏
    all_sells = [t for t in trades if t['action'] == 'SELL']
    total_profit = sum([t.get('profit', 0) for t in all_sells])
    winning_trades = [t for t in all_sells if t.get('profit', 0) > 0]
    losing_trades = [t for t in all_sells if t.get('profit', 0) < 0]
    win_rate = len(winning_trades) / len(all_sells) * 100 if all_sells else 0
    
    report = f"""
{'='*70}
📊 AI量化每日复盘报告
📅 日期: {today} {datetime.now().strftime('%A')}
{'='*70}

{'='*70}
💰 账户概览
{'='*70}
初始资金:     {account['init_cash']:.2f}
当前总市值:   {account['total_value']:.2f}
总盈亏:       {account['total_profit']:+.2f} ({account['total_profit_rate']:+.2f}%)
可用资金:     {account['cash']:.2f}
持仓数量:     {len(positions)}只

{'='*70}
📈 交易统计
{'='*70}
总交易次数:   {len(trades)}次 (买入{len([t for t in trades if t['action']=='BUY'])}次, 卖出{len(all_sells)}次)
本周交易:    {len(week_trades)}次
今日交易:    {len(today_trades)}次 (买入{len(today_buys)}, 卖出{len(today_sells)})

卖出统计:
  - 盈利次数:  {len(winning_trades)}次
  - 亏损次数:  {len(losing_trades)}次
  - 胜率:      {win_rate:.1f}%
  - 已实现盈亏: {total_profit:+.2f}

{'='*70}
📋 今日操作
{'='*70}
"""
    
    if today_trades:
        for t in today_trades:
            if t['action'] == 'BUY':
                report += f"""
🟢 买入: {t['name']}({t['code']})
   价格: {t['price']} x {t['shares']}股 = {t['cost']:.2f}
   原因: {t['reason']}
"""
            else:
                report += f"""
🔴 卖出: {t['name']}({t['code']})
   价格: {t['price']} x {t['shares']}股
   盈亏: {t['profit']:+.2f} ({t['profit_rate']:+.2f}%)
   持有: {t.get('hold_days', '?')}天
   原因: {t['reason']}
"""
    else:
        report += "\n今日无操作\n"
    
    report += f"""
{'='*70}
📊 当前持仓
{'='*70}
"""
    
    if positions:
        for code, pos in positions.items():
            report += f"""
{pos['name']}({code})
  持仓: {pos['shares']}股 | 成本: {pos['cost']:.2f} | 现价: --
  买入时间: {pos['first_buy_date']} | 买入次数: {pos['times']}次
"""
    else:
        report += "\n空仓\n"
    
    report += f"""
{'='*70}
🎯 选股复盘
{'='*70}
"""
    
    if scan_data:
        report += f"""
今日扫描: {scan_data.get('date', 'N/A')}
扫描股票数: {scan_data.get('total_scanned', 0)}只

🏆 强烈买入候选:
"""
        for stock in scan_data.get('strong_buys', [])[:3]:
            report += f"  • {stock['name']}({stock['code']}) 评分:{stock['score']} RSI:{stock['rsi']}\n"
        
        report += "\n💡 考虑买入候选:\n"
        for stock in scan_data.get('consider_buys', [])[:3]:
            report += f"  • {stock['name']}({stock['code']}) 评分:{stock['score']}\n"
    else:
        report += "\n今日未进行选股扫描\n"
    
    report += f"""
{'='*70}
📝 操作反思
{'='*70}
"""
    
    # 自动生成反思
    reflections = []
    
    if account['total_profit_rate'] > 5:
        reflections.append("✅ 本周盈利不错，控制回撤很重要")
    elif account['total_profit_rate'] < -3:
        reflections.append("⚠️ 回撤较大，注意风险控制，减少单笔仓位")
    
    if len(winning_trades) > len(losing_trades):
        reflections.append("✅ 胜率不错，保持当前策略")
    elif win_rate < 40:
        reflections.append("⚠️ 胜率偏低，考虑优化选股条件")
    
    if positions:
        if len(positions) > 5:
            reflections.append("⚠️ 持仓过于分散，建议集中到3-5只")
        reflections.append("📌 定期检查持仓，关注RSI是否超买")
    
    if not reflections:
        reflections.append("📌 正常运营，继续观察")
    
    for r in reflections:
        report += f"  {r}\n"
    
    report += f"""
{'='*70}
🎯 明日计划
{'='*70}
  1. 关注持仓股动态，检查止损信号
  2. 每日扫描市场，寻找新的买入机会
  3. 如有盈利超过15%的个股，考虑分批止盈
  4. 亏损个股设置8%止损线

{'='*70}
🤖 AI量化交易系统 v1.0 | 每日自动复盘
{'='*70}
"""
    
    # 保存报告
    os.makedirs(REPORTS_DIR, exist_ok=True)
    report_file = os.path.join(REPORTS_DIR, f"复盘_{today}.txt")
    with open(report_file, 'w', encoding='utf-8') as f:
        f.write(report)
    
    # 同时保存JSON版本
    report_json = {
        'date': today,
        'account': account,
        'today_trades': today_trades,
        'total_trades': len(trades),
        'win_rate': win_rate,
        'total_profit': total_profit,
        'positions_count': len(positions),
        'reflections': reflections
    }
    json_file = os.path.join(REPORTS_DIR, f"复盘_{today}.json")
    with open(json_file, 'w', encoding='utf-8') as f:
        json.dump(report_json, f, indent=2, ensure_ascii=False)
    
    print(report)
    print(f"\n✅ 复盘报告已保存到: {report_file}")
    
    return report

def analyze_trade_detail(trade_id):
    """分析单笔交易详情"""
    trades = load_trades()
    
    trade = None
    for t in trades:
        if t['id'] == trade_id:
            trade = t
            break
    
    if not trade:
        return f"未找到交易 #{trade_id}"
    
    report = f"""
{'='*70}
🔍 单笔交易复盘 #{trade_id}
{'='*70}

{'='*70}
交易基本信息
{'='*70}
操作:     {'买入' if trade['action'] == 'BUY' else '卖出'}
股票:     {trade['name']}({trade['code']})
时间:     {trade['date']}
价格:     {trade['price']}
数量:     {trade['shares']}股
金额:     {trade['cost']:.2f}
"""
    
    if trade['action'] == 'SELL':
        report += f"""
盈亏:     {trade['profit']:+.2f}
收益率:   {trade['profit_rate']:+.2f}%
持有天数: {trade.get('hold_days', 'N/A')}天
卖出理由: {trade['reason']}
"""
    
        # 绩效评估
        profit = trade.get('profit', 0)
        profit_rate = trade.get('profit_rate', 0)
        
        report += f"""
{'='*70}
绩效评估
{'='*70}
"""
        if profit_rate > 15:
            report += "🌟 优秀！盈利超过15%，成功止盈\n"
        elif profit_rate > 5:
            report += "✅ 良好，盈利在5-15%区间\n"
        elif profit_rate > 0:
            report += "🟡 勉强盈利，建议反思卖出时机\n"
        else:
            report += "❌ 亏损，需要反思买入时机和选股逻辑\n"
        
        # 持有时间分析
        hold_days = trade.get('hold_days', 0)
        if hold_days > 30 and profit_rate < 5:
            report += "⚠️ 持有超过30天但盈利不足5%，仓位效率低\n"
        elif hold_days <= 3 and profit_rate > 5:
            report += "🌟 短线操作成功！快速获利了结\n"
    
    else:
        report += f"\n买入理由: {trade['reason']}\n"
    
    report += f"""
{'='*70}
经验总结
{'='*70}
"""
    
    # 根据交易类型生成总结
    if trade['action'] == 'BUY':
        report += f"""
• 买入信号: {trade['reason']}
• 建议: 持续跟踪该股表现，设置8%止损线
"""
    else:
        profit = trade.get('profit', 0)
        if profit > 0:
            report += f"""
• 这次盈利说明策略有效
• 反思: 能否更早买入/卖出？
"""
        else:
            report += f"""
• 这次亏损是正常的交易成本
• 反思: 买入前是否充分分析？
• 教训: 做好止损纪律
"""
    
    report += "="*70 + "\n"
    
    return report

def generate_weekly_summary():
    """生成周报"""
    trades = load_trades()
    account = load_account()
    
    week_ago = (datetime.now() - timedelta(days=7)).strftime('%Y-%m-%d')
    week_trades = [t for t in trades if t['date'] >= week_ago]
    week_sells = [t for t in week_trades if t['action'] == 'SELL']
    
    week_profit = sum([t.get('profit', 0) for t in week_sells])
    
    summary = f"""
{'='*70}
📊 本周交易周报
📅 {datetime.now().strftime('%Y-%m-%d')} (过去7天)
{'='*70}

本周交易次数:   {len(week_trades)}
本周买入:       {len([t for t in week_trades if t['action']=='BUY'])}次
本周卖出:       {len(week_sells)}次
本周盈亏:       {week_profit:+.2f}
账户总收益率:   {account['total_profit_rate']:+.2f}%

"""
    
    if week_sells:
        summary += "本周卖出明细:\n"
        for t in week_sells:
            emoji = "🟢" if t['profit'] > 0 else "🔴"
            summary += f"  {emoji} {t['name']} | {t['profit_rate']:+.2f}% | {t['profit']:+.2f}元\n"
    
    summary += "="*70 + "\n"
    
    return summary

if __name__ == "__main__":
    print("🤖 AI量化每日复盘系统")
    print("="*70)
    
    # 生成每日报告
    generate_daily_report()
    
    # 生成周报
    print("\n" + generate_weekly_summary())
