"""
价值投资策略模块
================
基于巴菲特价值投资分析，中线持仓
选股：PE<15, ROE>15%, 负债率<50%, 护城河评级高
买入后持有到合理估值，目标持有1-3个月
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from strategies import BaseStrategy, StrategyRegistry
from datetime import time as t_time

import buffett_analyzer as ba


class ValueInvestingStrategy(BaseStrategy):
    """价值投资策略 - 中线价值持有"""
    
    name = "价值投资"
    strategy_type = "value"
    description = "巴菲特价值投资理念，PE<15、ROE>15%，中线持有到合理估值"
    
    def __init__(self, strategy_id: int, config: dict = None):
        super().__init__(strategy_id, config)
        self.config = {
            'pe_max': 15,             # PE上限（巴菲特标准）
            'roe_min': 15.0,          # ROE下限%
            'debt_ratio_max': 50.0,   # 负债率上限%
            'stop_loss': -8.0,        # 中线止损%（更宽松）
            'target_pe': 25,          # 目标PE（止盈触发）
            'monthly_check_day': 1,   # 每月第几天检查
            ** (config or {})
        }
    
    def is_trading_time(self) -> bool:
        """日内可交易时间"""
        bj = self.get_bj_time()
        now = bj.time()
        return t_time(9, 30) <= now <= t_time(15, 0)
    
    def analyze_stock(self, stock_code: str) -> dict:
        """使用巴菲特分析器分析个股"""
        try:
            return ba.build_report(stock_code)
        except Exception as e:
            return {'error': str(e)}
    
    def meets_buy_criteria(self, report: dict) -> tuple:
        """
        检查是否满足买入条件
        返回: (through, reason)
        """
        cfg = self.config
        
        # 检查PE
        pe_val = report.get('indicators', {}).get('PE', {}).get('value', 999)
        if pe_val > cfg['pe_max']:
            return False, f"PE={pe_val:.1f} > {cfg['pe_max']}，估值偏高"
        
        # 检查ROE
        roe_val = report.get('indicators', {}).get('ROE', {}).get('value', 0)
        if roe_val < cfg['roe_min']:
            return False, f"ROE={roe_val:.1f}% < {cfg['roe_min']}%，盈利能力不足"
        
        # 检查负债率
        debt_ratio = 999
        for key, val in report.get('indicators', {}).items():
            if '负债' in key or '资产负债' in key:
                debt_ratio = val.get('value', 999)
                break
        if debt_ratio != 999 and debt_ratio > cfg['debt_ratio_max']:
            return False, f"负债率={debt_ratio:.1f}% > {cfg['debt_ratio_max']}%，财务风险较高"
        
        # 检查行动建议
        action = report.get('action', '')
        if '买入' not in action and '持有' not in action:
            return False, f"价值分析建议：{action}，不建议买入"
        
        # 当前价格 vs 目标价
        current_price = report.get('current_price', 0)
        target_price = report.get('target_price', 0)
        if target_price and current_price and target_price <= current_price:
            return False, f"现价{current_price} >= 目标价{target_price}，无安全边际"
        
        return True, (
            f"PE={pe_val:.1f}符合标准, "
            f"ROE={roe_val:.1f}%达标"
        )
    
    def should_sell(self, report: dict, cost_price: float, current_price: float, highest_since_buy: float) -> tuple:
        """
        判断是否该卖出
        返回: (should_sell, reason)
        """
        cfg = self.config
        
        # 止损
        loss_pct = (current_price - cost_price) / cost_price * 100
        if loss_pct <= cfg['stop_loss']:
            return True, f"止损触发：亏损{loss_pct:.1f}%（≤{cfg['stop_loss']}%）"
        
        # 按目标PE止盈
        pe_val = report.get('indicators', {}).get('PE', {}).get('value', 999)
        if pe_val >= cfg['target_pe']:
            return True, f"止盈触发：PE={pe_val:.1f} ≥ {cfg['target_pe']}，达到目标估值"
        
        # 估值偏高离场信号
        if loss_pct > 0 and loss_pct >= 15:
            return True, f"盈利{loss_pct:.1f}%达成，锁定利润"
        
        return False, ""


# 注册策略
StrategyRegistry.register(ValueInvestingStrategy)
