"""
GhPrStatus - GitHub PR状态
基于 Claude Code gh_pr_status.ts 设计

GitHub PR状态工具。
"""
import os
import urllib.request
import urllib.parse
import json
from typing import Optional, Dict, Any


def get_pr_status(repo: str, pr_number: int, token: str = None) -> Optional[Dict]:
    """
    获取PR状态
    
    Args:
        repo: 仓库 (owner/repo)
        pr_number: PR编号
        token: GitHub Token
    """
    url = f"https://api.github.com/repos/{repo}/pulls/{pr_number}"
    
    headers = {
        "Accept": "application/vnd.github.v3+json",
        "User-Agent": "Python/3"
    }
    
    if token:
        headers["Authorization"] = f"token {token}"
    elif os.getenv("GITHUB_TOKEN"):
        headers["Authorization"] = f"token {os.getenv('GITHUB_TOKEN')}"
    
    try:
        req = urllib.request.Request(url)
        for key, value in headers.items():
            req.add_header(key, value)
        
        with urllib.request.urlopen(req) as resp:
            return json.loads(resp.read().decode())
    except Exception as e:
        return None


def get_pr_reviews(repo: str, pr_number: int, token: str = None) -> list:
    """获取PR审查"""
    url = f"https://api.github.com/repos/{repo}/pulls/{pr_number}/reviews"
    
    headers = {
        "Accept": "application/vnd.github.v3+json",
        "User-Agent": "Python/3"
    }
    
    if token:
        headers["Authorization"] = f"token {token}"
    elif os.getenv("GITHUB_TOKEN"):
        headers["Authorization"] = f"token {os.getenv('GITHUB_TOKEN')}"
    
    try:
        req = urllib.request.Request(url)
        for key, value in headers.items():
            req.add_header(key, value)
        
        with urllib.request.urlopen(req) as resp:
            return json.loads(resp.read().decode())
    except Exception:
        return []


def get_pr_checks(repo: str, pr_number: int, token: str = None) -> Dict:
    """获取PR的CI检查状态"""
    url = f"https://api.github.com/repos/{repo}/commits?per_page=1"
    
    headers = {
        "Accept": "application/vnd.github.v3+json",
        "User-Agent": "Python/3"
    }
    
    if token:
        headers["Authorization"] = f"token {token}"
    elif os.getenv("GITHUB_TOKEN"):
        headers["Authorization"] = f"token {os.getenv('GITHUB_TOKEN')}"
    
    try:
        req = urllib.request.Request(url)
        for key, value in headers.items():
            req.add_header(key, value)
        
        with urllib.request.urlopen(req) as resp:
            commits = json.loads(resp.read().decode())
            if commits:
                sha = commits[0]["sha"]
                # 获取status
                status_url = f"https://api.github.com/repos/{repo}/commits/{sha}/status"
                status_req = urllib.request.Request(status_url)
                for key, value in headers.items():
                    status_req.add_header(key, value)
                with urllib.request.urlopen(status_req) as status_resp:
                    return json.loads(status_resp.read().decode())
    except Exception:
        return {}


def is_pr_merged(repo: str, pr_number: int, token: str = None) -> bool:
    """检查PR是否已合并"""
    pr = get_pr_status(repo, pr_number, token)
    if pr:
        return pr.get("merged", False)
    return False


def get_pr_state(repo: str, pr_number: int, token: str = None) -> str:
    """获取PR状态 (open/closed/merged)"""
    pr = get_pr_status(repo, pr_number, token)
    if pr:
        if pr.get("merged"):
            return "merged"
        elif pr.get("state") == "closed":
            return "closed"
        return "open"
    return "unknown"


# 导出
__all__ = [
    "get_pr_status",
    "get_pr_reviews",
    "get_pr_checks",
    "is_pr_merged",
    "get_pr_state",
]
