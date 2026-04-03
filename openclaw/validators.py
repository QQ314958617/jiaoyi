"""
OpenClaw Validators
=================
Inspired by Claude Code's validation utilities.

数据验证器，支持：
1. 股票代码验证
2. 价格/数量验证
3. 交易参数验证
4. URL/邮箱验证
5. 范围验证
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any, Callable, Optional, Union

# ============================================================================
# 验证结果
# ============================================================================

@dataclass
class ValidationResult:
    """验证结果"""
    is_valid: bool
    error: Optional[str] = None
    value: Any = None

    @staticmethod
    def ok(value: Any = None) -> 'ValidationResult':
        return ValidationResult(is_valid=True, value=value)
    
    @staticmethod
    def error(msg: str) -> 'ValidationResult':
        return ValidationResult(is_valid=False, error=msg)

# ============================================================================
# 股票相关验证
# ============================================================================

STOCK_CODE_PATTERN = re.compile(r'^\d{6}$')
SHARE_MULTIPLE = 100  # A股最小交易单位

def validate_stock_code(code: str) -> ValidationResult:
    """
    验证股票代码
    
    6位数字，上交所/深交所
    """
    if not code:
        return ValidationResult.error("股票代码不能为空")
    
    code = code.strip()
    
    if not STOCK_CODE_PATTERN.match(code):
        return ValidationResult.error(f"股票代码必须是6位数字，当前: {code}")
    
    return ValidationResult.ok(code)

def validate_price(price: Union[int, float], min_price: float = 0.01, 
                  max_price: float = 10000.0) -> ValidationResult:
    """
    验证价格
    
    Args:
        price: 价格
        min_price: 最低价（默认为0.01）
        max_price: 最高价（默认为10000）
    """
    if price is None:
        return ValidationResult.error("价格不能为空")
    
    try:
        price = float(price)
    except (TypeError, ValueError):
        return ValidationResult.error(f"价格必须是数字，当前: {price}")
    
    if price <= 0:
        return ValidationResult.error(f"价格必须大于0，当前: {price}")
    
    if price < min_price:
        return ValidationResult.error(f"价格不能低于最小价格 {min_price}，当前: {price}")
    
    if price > max_price:
        return ValidationResult.error(f"价格不能超过最大价格 {max_price}，当前: {price}")
    
    # A股价格精度：小数点后2位
    price_str = f"{price:.3f}"
    if '.' in price_str:
        decimals = len(price_str.split('.')[1].rstrip('0'))
        if decimals > 2:
            return ValidationResult.error(f"价格最多2位小数，当前: {price}")
    
    return ValidationResult.ok(round(price, 2))

def validate_shares(shares: int, allow_zero: bool = False) -> ValidationResult:
    """
    验证交易数量
    
    A股必须是100的整数倍
    """
    if shares is None:
        return ValidationResult.error("数量不能为空")
    
    try:
        shares = int(shares)
    except (TypeError, ValueError):
        return ValidationResult.error(f"数量必须是整数，当前: {shares}")
    
    if shares == 0 and not allow_zero:
        return ValidationResult.error("数量不能为0")
    
    if shares < 0:
        return ValidationResult.error(f"数量不能为负数，当前: {shares}")
    
    if shares % SHARE_MULTIPLE != 0:
        return ValidationResult.error(f"数量必须是{SHARE_MULTIPLE}的整数倍，当前: {shares}")
    
    return ValidationResult.ok(shares)

def validate_amount(amount: Union[int, float], max_amount: float = 1000000.0) -> ValidationResult:
    """
    验证交易金额
    """
    if amount is None:
        return ValidationResult.error("金额不能为空")
    
    try:
        amount = float(amount)
    except (TypeError, ValueError):
        return ValidationResult.error(f"金额必须是数字，当前: {amount}")
    
    if amount <= 0:
        return ValidationResult.error(f"金额必须大于0，当前: {amount}")
    
    if amount > max_amount:
        return ValidationResult.error(f"金额不能超过{max_amount}，当前: {amount}")
    
    return ValidationResult.ok(round(amount, 2))

# ============================================================================
# 交易参数验证
# ============================================================================

def validate_trade_params(stock_code: str, shares: int, price: float,
                          max_position: float = 10000.0) -> ValidationResult:
    """
    验证完整交易参数
    
    Returns: ValidationResult(is_valid=True) 或 ValidationResult(is_valid=False, error=...)
    """
    # 验证股票代码
    result = validate_stock_code(stock_code)
    if not result.is_valid:
        return result
    
    # 验证数量
    result = validate_shares(shares)
    if not result.is_valid:
        return result
    
    # 验证价格
    result = validate_price(price)
    if not result.is_valid:
        return result
    
    # 验证金额
    amount = shares * price
    result = validate_amount(amount, max_position * 10)  # 单笔不超过10倍最大持仓
    if not result.is_valid:
        return result
    
    # 验证持仓上限
    if amount > max_position:
        return ValidationResult.error(
            f"单笔交易金额 {amount:.2f} 超过最大持仓 {max_position}，请减少数量"
        )
    
    return ValidationResult.ok({
        "stock_code": stock_code,
        "shares": shares,
        "price": round(price, 2),
        "amount": round(amount, 2)
    })

# ============================================================================
# 通用验证
# ============================================================================

def validate_range(value: Union[int, float], min_val: Optional[float] = None,
                 max_val: Optional[float] = None, name: str = "值") -> ValidationResult:
    """验证数值范围"""
    try:
        value = float(value)
    except (TypeError, ValueError):
        return ValidationResult.error(f"{name}必须是数字，当前: {value}")
    
    if min_val is not None and value < min_val:
        return ValidationResult.error(f"{name}不能小于{min_val}，当前: {value}")
    
    if max_val is not None and value > max_val:
        return ValidationResult.error(f"{name}不能大于{max_val}，当前: {value}")
    
    return ValidationResult.ok(value)

def validate_url(url: str) -> ValidationResult:
    """验证 URL"""
    if not url:
        return ValidationResult.error("URL不能为空")
    
    pattern = re.compile(
        r'^https?://'  # http:// 或 https://
        r'(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+[A-Z]{2,6}\.?|'  # 域名
        r'localhost|'  # localhost
        r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})'  # IP
        r'(?::\d+)?'  # 可选端口
        r'(?:/?|[/?]\S+)$', re.IGNORECASE)
    
    if not pattern.match(url):
        return ValidationResult.error(f"无效的URL格式: {url}")
    
    return ValidationResult.ok(url)

def validate_email(email: str) -> ValidationResult:
    """验证邮箱"""
    if not email:
        return ValidationResult.error("邮箱不能为空")
    
    pattern = re.compile(r'^[\w\.-]+@[\w\.-]+\.\w+$')
    if not pattern.match(email):
        return ValidationResult.error(f"无效的邮箱格式: {email}")
    
    return ValidationResult.ok(email)

def validate_phone(phone: str) -> ValidationResult:
    """验证手机号（中国大陆）"""
    if not phone:
        return ValidationResult.error("手机号不能为空")
    
    # 去掉非数字字符
    phone = re.sub(r'\D', '', phone)
    
    if len(phone) == 11:
        if phone[0] != '1':
            return ValidationResult.error("手机号必须以1开头")
        return ValidationResult.ok(phone)
    
    return ValidationResult.error(f"手机号必须是11位，当前: {phone}")

def validate_required(value: Any, field_name: str = "字段") -> ValidationResult:
    """验证必填字段"""
    if value is None:
        return ValidationResult.error(f"{field_name}不能为空")
    
    if isinstance(value, str) and not value.strip():
        return ValidationResult.error(f"{field_name}不能为空")
    
    return ValidationResult.ok(value)

def validate_string_length(value: str, min_len: int = 0, max_len: Optional[int] = None,
                          field_name: str = "字符串") -> ValidationResult:
    """验证字符串长度"""
    if not isinstance(value, str):
        return ValidationResult.error(f"{field_name}必须是字符串")
    
    length = len(value)
    
    if length < min_len:
        return ValidationResult.error(f"{field_name}长度不能小于{min_len}，当前: {length}")
    
    if max_len is not None and length > max_len:
        return ValidationResult.error(f"{field_name}长度不能大于{max_len}，当前: {length}")
    
    return ValidationResult.ok(value)

def validate_enum(value: Any, allowed: list, field_name: str = "值") -> ValidationResult:
    """验证枚举值"""
    if value not in allowed:
        return ValidationResult.error(
            f"{field_name}必须是{allowed}之一，当前: {value}"
        )
    return ValidationResult.ok(value)

# ============================================================================
# 组合验证器
# ============================================================================

class Validator:
    """
    组合验证器
    
    支持链式调用：
    ```python
    result = (Validator()
        .required("code", stock_code)
        .pattern("code", r"^\d{6}$")
        .range("price", price, min=0.01)
        .validate())
    ```
    """
    
    def __init__(self):
        self._errors: list[str] = []
        self._values: dict = {}
    
    def required(self, name: str, value: Any) -> 'Validator':
        if value is None or (isinstance(value, str) and not value.strip()):
            self._errors.append(f"{name}不能为空")
        else:
            self._values[name] = value
        return self
    
    def pattern(self, name: str, value: str, pattern: str, 
               error_msg: Optional[str] = None) -> 'Validator':
        if name not in self._errors:
            if not re.match(pattern, str(value)):
                self._errors.append(error_msg or f"{name}格式不正确")
        return self
    
    def range(self, name: str, value: Union[int, float], 
              min: Optional[float] = None, max: Optional[float] = None) -> 'Validator':
        if name in self._errors:
            return self
        
        try:
            value = float(value)
        except (TypeError, ValueError):
            self._errors.append(f"{name}必须是数字")
            return self
        
        if min is not None and value < min:
            self._errors.append(f"{name}不能小于{min}")
            return self
        
        if max is not None and value > max:
            self._errors.append(f"{name}不能大于{max}")
            return self
        
        self._values[name] = value
        return self
    
    def enum(self, name: str, value: Any, allowed: list) -> 'Validator':
        if name in self._errors:
            return self
        
        if value not in allowed:
            self._errors.append(f"{name}必须是{allowed}之一")
            return self
        
        self._values[name] = value
        return self
    
    def validate(self) -> ValidationResult:
        if self._errors:
            return ValidationResult.error("; ".join(self._errors))
        return ValidationResult.ok(dict(self._values))
