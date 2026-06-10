#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""路由模块 - 注册所有Blueprint"""


def register_all_blueprints(app):
    """注册所有路由蓝图到Flask应用"""
    from routes.main_routes import main_bp
    from routes.finance_routes import finance_bp
    from routes.accounting_routes import accounting_bp
    from routes.assistant_routes import assistant_bp

    app.register_blueprint(main_bp)
    app.register_blueprint(finance_bp)
    app.register_blueprint(accounting_bp)
    app.register_blueprint(assistant_bp)