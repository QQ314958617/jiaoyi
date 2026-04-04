"""
AWS Utilities - AWS工具函数
基于 Claude Code aws.ts 设计

AWS凭证和STS相关工具。
"""
from dataclasses import dataclass
from typing import Optional


@dataclass
class AwsCredentials:
    """AWS短期凭证"""
    access_key_id: str
    secret_access_key: str
    session_token: str
    expiration: Optional[str] = None


@dataclass
class AwsStsOutput:
    """AWS STS输出"""
    credentials: AwsCredentials


def is_valid_aws_sts_output(obj: dict) -> bool:
    """
    验证AWS STS输出格式
    
    Args:
        obj: 对象
        
    Returns:
        是否有效
    """
    if not obj or not isinstance(obj, dict):
        return False
    
    creds = obj.get('Credentials')
    if not creds or not isinstance(creds, dict):
        return False
    
    return (
        isinstance(creds.get('AccessKeyId'), str) and
        isinstance(creds.get('SecretAccessKey'), str) and
        isinstance(creds.get('SessionToken'), str) and
        bool(creds.get('AccessKeyId')) and
        bool(creds.get('SecretAccessKey')) and
        bool(creds.get('SessionToken'))
    )


def parse_aws_credentials(data: dict) -> Optional[AwsCredentials]:
    """
    解析AWS凭证
    
    Args:
        data: 原始数据
        
    Returns:
        AwsCredentials或None
    """
    if not is_valid_aws_sts_output(data):
        return None
    
    creds = data['Credentials']
    return AwsCredentials(
        access_key_id=creds['AccessKeyId'],
        secret_access_key=creds['SecretAccessKey'],
        session_token=creds['SessionToken'],
        expiration=creds.get('Expiration'),
    )


# 导出
__all__ = [
    "AwsCredentials",
    "AwsStsOutput",
    "is_valid_aws_sts_output",
    "parse_aws_credentials",
]
