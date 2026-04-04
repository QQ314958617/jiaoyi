"""
CA Certificates - CA证书管理
基于 Claude Code caCerts.ts 设计

加载TLS连接的CA证书。
"""
import os
import ssl
from functools import lru_cache
from typing import List, Optional


def _has_node_option(option: str) -> bool:
    """
    检查NODE_OPTIONS中是否有指定选项
    
    Args:
        option: 选项名称
        
    Returns:
        是否存在
    """
    node_options = os.environ.get('NODE_OPTIONS', '')
    if not node_options:
        return False
    return option in node_options.split()


@lru_cache(maxsize=1)
def get_ca_certificates() -> Optional[List[str]]:
    """
    获取CA证书
    
    Returns:
        证书列表或None（使用运行时默认）
    """
    use_system_ca = (
        _has_node_option('--use-system-ca') or
        _has_node_option('--use-openssl-ca')
    )
    
    extra_certs_path = os.environ.get('NODE_EXTRA_CA_CERTS')
    
    # 两者都未设置，返回None使用运行时默认
    if not use_system_ca and not extra_certs_path:
        return None
    
    certs = []
    
    # 添加系统CA
    if use_system_ca:
        try:
            # Python的默认CA证书
            import certifi
            with open(certifi.where(), 'r') as f:
                cert_content = f.read()
            certs.append(cert_content)
        except Exception:
            pass
    
    # 添加额外的CA证书
    if extra_certs_path:
        try:
            if os.path.isfile(extra_certs_path):
                with open(extra_certs_path, 'r') as f:
                    certs.append(f.read())
        except Exception:
            pass
    
    return certs if certs else None


def get_ssl_context() -> Optional[ssl.SSLContext]:
    """
    获取SSL上下文
    
    Returns:
        配置好的SSL上下文或None
    """
    certs = get_ca_certificates()
    if not certs:
        return None
    
    context = ssl.create_default_context()
    for cert in certs:
        context.load_verify_locations(cadata=cert)
    
    return context


def clear_ca_certs_cache() -> None:
    """清除CA证书缓存"""
    get_ca_certificates.cache_clear()


# 导出
__all__ = [
    "get_ca_certificates",
    "get_ssl_context",
    "clear_ca_certs_cache",
]
