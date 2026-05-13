"""
路由注册中心 - 所有 Blueprint 在此注册
"""
from routes.trading import trading_bp
from routes.market import market_bp
from routes.strategy import strategy_bp
from routes.analysis import analysis_bp
from routes.review import review_bp
from routes.engine import engine_bp
from routes.system import system_bp
from routes.proxy import proxy_bp


def register_blueprints(app):
    """注册所有 Blueprint"""
    app.register_blueprint(trading_bp)
    app.register_blueprint(market_bp)
    app.register_blueprint(strategy_bp)
    app.register_blueprint(analysis_bp)
    app.register_blueprint(review_bp)
    app.register_blueprint(engine_bp)
    app.register_blueprint(system_bp)
    app.register_blueprint(proxy_bp)
