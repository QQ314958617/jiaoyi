"""
反向代理路由 - 合并5个重复代理为1个通用函数
"""
import logging
from flask import Blueprint, request, make_response, render_template, redirect

import requests

from config import STAR_OFFICE_BACKEND

logger = logging.getLogger(__name__)

proxy_bp = Blueprint('proxy', __name__)


def _proxy_request(target_url, rewrite_content=False, rewrite_rules=None):
    """通用反向代理函数"""
    try:
        headers = {'Origin': request.headers.get('Origin', '*')}

        if request.method == 'GET':
            resp = requests.get(target_url, params=request.args, headers=headers, timeout=10)
        elif request.method == 'POST':
            resp = requests.post(target_url, json=request.json, headers=headers, timeout=10)
        elif request.method == 'PUT':
            resp = requests.put(target_url, json=request.json, headers=headers, timeout=10)
        elif request.method == 'DELETE':
            resp = requests.delete(target_url, headers=headers, timeout=10)
        else:
            return make_response('Method not allowed', 405)

        if rewrite_content and rewrite_rules:
            content = resp.content.decode('utf-8')
            for old, new in rewrite_rules:
                content = content.replace(old, new)
            response = make_response(content, resp.status_code)
        else:
            response = make_response(resp.content, resp.status_code)

        content_type = resp.headers.get('Content-Type', 'application/octet-stream')
        response.content_type = content_type
        for key, value in resp.headers.items():
            if key not in ('Content-Length', 'Content-Encoding', 'Transfer-Encoding', 'Host', 'Content-Type'):
                response.headers[key] = value
        response.headers['Access-Control-Allow-Origin'] = '*'
        return response
    except Exception as e:
        logger.warning(f"Proxy error ({target_url}): {e}")
        return make_response(f'Proxy error: {e}', 502)


# ========== Studio UI 代理 ==========

@proxy_bp.route('/studio')
def studio_page():
    return render_template('studio.html')


@proxy_bp.route('/studio-ui')
@proxy_bp.route('/studio-ui/')
def studio_ui_index():
    """反向代理 Star Office UI 首页"""
    return _proxy_request(
        f'{STAR_OFFICE_BACKEND}/',
        rewrite_content=True,
        rewrite_rules=[
            ('href="/', 'href="/studio-ui/'),
            ('src="/', 'src="/studio-ui/'),
        ]
    )


@proxy_bp.route('/studio-ui/<path:path>')
def studio_ui_proxy(path):
    """反向代理 Star Office UI 静态资源"""
    return _proxy_request(f'{STAR_OFFICE_BACKEND}/{path}')


@proxy_bp.route('/studio-api/<path:path>', methods=['GET', 'POST', 'PUT', 'DELETE'])
def studio_api_proxy(path):
    """反向代理 Star Office UI API"""
    return _proxy_request(f'{STAR_OFFICE_BACKEND}/{path}')


# ========== Star Office 代理 ==========

@proxy_bp.route('/star-api/<path:path>', methods=['GET', 'POST', 'PUT', 'DELETE'])
def star_api_proxy(path):
    """反向代理 Star Office UI 所有请求"""
    return _proxy_request(f'{STAR_OFFICE_BACKEND}/{path}')


@proxy_bp.route('/static/<path:filename>')
def star_static_catchall(filename):
    """反向代理静态文件"""
    return _proxy_request(f'{STAR_OFFICE_BACKEND}/static/{filename}')


@proxy_bp.route('/star-assets/<path:filename>')
def star_assets_proxy(filename):
    """反向代理 Star Office UI 静态文件"""
    return _proxy_request(f'{STAR_OFFICE_BACKEND}/static/{filename}')


@proxy_bp.route('/star-static/<path:filename>')
def star_static_proxy(filename):
    """反向代理 Star Office UI 静态文件"""
    return _proxy_request(f'{STAR_OFFICE_BACKEND}/static/{filename}')


@proxy_bp.route('/star-index')
def star_index():
    """获取 Star Office UI 首页并重写静态资源路径"""
    return _proxy_request(
        f'{STAR_OFFICE_BACKEND}/',
        rewrite_content=True,
        rewrite_rules=[
            ('href="/static/', 'href="/static/'),
            ('src="/static/', 'src="/static/'),
            ("fetch('/", "fetch('/star-api/"),
            ('fetch("/', 'fetch("/star-api/'),
        ]
    )


@proxy_bp.route('/star/')
@proxy_bp.route('/star')
def star_home():
    """重定向到重写后的首页"""
    return redirect('/star-index')
