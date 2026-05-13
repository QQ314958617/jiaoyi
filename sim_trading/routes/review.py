"""
复盘路由: /api/daily, /api/review
"""
import json
import logging
from datetime import date
from flask import Blueprint, jsonify, request

import database as db

logger = logging.getLogger(__name__)

review_bp = Blueprint('review', __name__)


@review_bp.route('/api/daily')
def get_daily():
    """获取每日复盘（支持分页）"""
    page = int(request.args.get('page', 1))
    page_size = int(request.args.get('page_size', 10))
    offset = (page - 1) * page_size

    total, reviews = db.get_reviews_paged(offset=offset, limit=page_size)

    for r in reviews:
        if r.get('strategies'):
            try:
                r['strategies'] = json.loads(r['strategies'])
            except Exception:
                pass
        if r.get('tags'):
            try:
                r['tags'] = json.loads(r['tags'])
            except Exception:
                r['tags'] = r['tags'].split(',') if r['tags'] else []

    return jsonify({
        "total": total,
        "page": page,
        "page_size": page_size,
        "total_pages": (total + page_size - 1) // page_size if total > 0 else 0,
        "reviews": reviews
    })


@review_bp.route('/api/review', methods=['POST'])
def add_review():
    """添加复盘记录"""
    data = request.json
    content = data.get('content', '')
    tags = data.get('tags', [])
    strategies = data.get('strategies', [])

    account = db.get_account()

    review_id = db.add_review(
        date=date.today().isoformat(),
        content=content,
        strategies=json.dumps(strategies, ensure_ascii=False),
        profit=account.get('total_profit', 0),
        tags=json.dumps(tags, ensure_ascii=False)
    )

    return jsonify({
        "success": True,
        "review_id": review_id
    })
