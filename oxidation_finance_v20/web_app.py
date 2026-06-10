#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
氧化加工厂财务系统 V2.2 - Web版（模块化架构）
会计科目体系 | 凭证管理 | 账簿查询 | 自动化凭证生成
"""

import time
import sys
import logging
from pathlib import Path
from datetime import date, datetime
from flask import Flask, request, session, g, render_template, redirect, url_for

from routes.helpers import DB_PATH, get_db, request_stats
from routes import register_all_blueprints

# 配置日志
logging.basicConfig(level=logging.INFO,
                    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

# 创建Flask应用
app = Flask(__name__)
app.config["TEMPLATES_AUTO_RELOAD"] = True
app.secret_key = "oxidation_finance_v30_secret_2024"

# 注册所有路由蓝图
register_all_blueprints(app)


# ========== 中间件 ==========

# 不需要登录的公开路由
PUBLIC_ROUTES = {"main.login", "main.logout", "static"}


@app.before_request
def before_request():
    """请求前认证检查和性能计时"""
    g.start_time = time.time()
    g.conn = get_db()

    # 登录认证检查
    if request.endpoint and request.endpoint not in PUBLIC_ROUTES:
        if "user" not in session:
            return redirect(url_for("main.login", next=request.url))


@app.after_request
def after_request(response):
    """请求后记录性能"""
    if hasattr(g, "start_time"):
        elapsed = (time.time() - g.start_time) * 1000
        endpoint = request.endpoint or "unknown"
        request_stats[endpoint].append(elapsed)
        logger.info(f"📊 请求完成: {endpoint} - {elapsed:.2f}ms")
    return response


@app.teardown_request
def teardown_request(exception=None):
    """请求结束后关闭数据库连接"""
    conn = g.pop("conn", None)
    if conn is not None:
        conn.close()


# ========== 错误处理 ==========

@app.errorhandler(404)
def not_found(e):
    return render_template("error.html", error="页面不存在"), 404


@app.errorhandler(500)
def server_error(e):
    return render_template("error.html", error="服务器内部错误"), 500


# ========== 模板文件创建 ==========

def create_templates():
    """动态创建模板文件"""
    template_dir = Path(__file__).parent / "templates"
    template_dir.mkdir(exist_ok=True)

    # ------ 基础模板 ------
    base_html = """<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{% block title %}氧化加工厂财务系统{% endblock %}</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body { font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; background: #f5f5f5; }
        .container { max-width: 1200px; margin: 0 auto; padding: 20px; }
        .header { background: #1890ff; color: white; padding: 20px; margin-bottom: 20px; }
        .header h1 { font-size: 24px; }
        .nav { background: white; padding: 10px 20px; margin-bottom: 20px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }
        .nav a { color: #333; text-decoration: none; margin-right: 20px; padding: 5px 10px; }
        .nav a:hover { color: #1890ff; }
        .card { background: white; padding: 20px; margin-bottom: 20px; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }
        .card h2 { font-size: 18px; margin-bottom: 15px; color: #333; }
        .stats-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 15px; }
        .stat-item { background: #f8f9fa; padding: 15px; border-radius: 6px; text-align: center; }
        .stat-value { font-size: 24px; font-weight: bold; color: #1890ff; }
        .stat-label { font-size: 14px; color: #666; margin-top: 5px; }
        .btn { display: inline-block; padding: 10px 20px; background: #1890ff; color: white; text-decoration: none; border-radius: 4px; border: none; cursor: pointer; }
        .btn:hover { background: #40a9ff; }
        .btn-success { background: #52c41a; }
        .btn-warning { background: #faad14; }
        table { width: 100%; border-collapse: collapse; }
        th, td { padding: 12px; text-align: left; border-bottom: 1px solid #eee; }
        th { background: #fafafa; font-weight: 600; }
        tr:hover { background: #f5f5f5; }
        .form-group { margin-bottom: 15px; }
        .form-group label { display: block; margin-bottom: 5px; font-weight: 500; }
        .form-group input, .form-group select { width: 100%; padding: 10px; border: 1px solid #d9d9d9; border-radius: 4px; }
        .status-badge { padding: 4px 8px; border-radius: 4px; font-size: 12px; }
        .status-待加工 { background: #fff7e6; color: #fa8c16; }
        .status-加工中 { background: #e6f7ff; color: #1890ff; }
        .status-已完工 { background: #f6ffed; color: #52c41a; }
        .status-已交付 { background: #f9f0ff; color: #722ed1; }
        .quick-actions { display: grid; grid-template-columns: repeat(auto-fit, minmax(150px, 1fr)); gap: 10px; margin-top: 20px; }
        .table-wrap { overflow-x: auto; -webkit-overflow-scrolling: touch; }
        /* ===== 移动端响应式 ===== */
        @media (max-width: 768px) {
            .container { padding: 10px; }
            .header { padding: 12px; }
            .header h1 { font-size: 18px; }
            .nav { padding: 5px 10px; overflow-x: auto; white-space: nowrap; }
            .nav .container { flex-direction: column; gap: 8px; }
            .nav a { padding: 8px 12px; font-size: 13px; margin-right: 0; display: inline-block; }
            .card { padding: 12px; margin-bottom: 12px; }
            .stats-grid { grid-template-columns: repeat(2, 1fr); gap: 8px; }
            .stat-item { padding: 10px; }
            .stat-value { font-size: 18px; }
            .stat-label { font-size: 12px; }
            .kpi-row { grid-template-columns: repeat(2, 1fr); }
            .kpi .val { font-size: 18px; }
            .grid2, .grid3 { grid-template-columns: 1fr; }
            .kpi-list { grid-template-columns: repeat(2, 1fr); }
            table { font-size: 12px; }
            th, td { padding: 6px 8px; }
            .btn { padding: 8px 14px; font-size: 13px; }
            .form-group input, .form-group select { font-size: 16px; padding: 10px 12px; }
            .quick-actions { grid-template-columns: repeat(2, 1fr); gap: 6px; }
            .summary-row { grid-template-columns: repeat(2, 1fr) !important; }
            .filter-bar { flex-direction: column; }
            .modal { width: 95% !important; padding: 16px !important; }
        }
        @media (max-width: 480px) {
            .stats-grid { grid-template-columns: 1fr 1fr; gap: 6px; }
            .kpi-row { grid-template-columns: 1fr; }
            .kpi-list { grid-template-columns: 1fr 1fr; }
        }
    </style>
</head>
<body>
    <div class="header">
        <div class="container">
            <h1>氧化加工厂财务系统 V3.0</h1>
        </div>
    </div>
    <div class="nav">
        <div class="container" style="display:flex; justify-content:space-between; align-items:center;">
            <div>
                <a href="/">首页</a>
                <a href="/orders">订单</a>
                <a href="/customers">客户</a>
                <a href="/reports">报表</a>
                <a href="/chart-of-accounts">会计科目</a>
                <a href="/vouchers">会计凭证</a>
                <a href="/accounting-books">会计账簿</a>
            </div>
            <div style="display:flex; align-items:center; gap:15px;">
                {% if session.user %}
                <span style="color:#666; font-size:14px;">
                    当前用户: <strong>{{ session.user.display_name }}</strong>
                    <span style="background:#e6f7ff; color:#1890ff; padding:2px 8px; border-radius:10px; font-size:12px; margin-left:4px;">{{ session.user.role }}</span>
                </span>
                <a href="/logout" style="color:#f5222d; font-size:14px;">退出登录</a>
                {% endif %}
            </div>
        </div>
    </div>
    <div class="container">
        {% block content %}{% endblock %}
    </div>
</body>
</html>"""

    # ------ 首页模板 ------
    index_html = """{% extends "base.html" %}

{% block content %}
<div class="stats-grid">
    <div class="stat-item">
        <div class="stat-value">{{ "%.2f"|format(today_income) }}</div>
        <div class="stat-label">今日收入</div>
    </div>
    <div class="stat-item">
        <div class="stat-value">{{ "%.2f"|format(today_expense) }}</div>
        <div class="stat-label">今日支出</div>
    </div>
    <div class="stat-item">
        <div class="stat-value">{{ "%.2f"|format(today_profit) }}</div>
        <div class="stat-label">今日利润</div>
    </div>
    <div class="stat-item">
        <div class="stat-value">{{ pending_orders }}</div>
        <div class="stat-label">待加工订单</div>
    </div>
    <div class="stat-item">
        <div class="stat-value">{{ unpaid_orders }}</div>
        <div class="stat-label">未收款订单</div>
    </div>
    <div class="stat-item">
        <div class="stat-value">{{ "%.2f"|format(month_profit) }}</div>
        <div class="stat-label">本月利润</div>
    </div>
</div>

<div class="card">
    <h2>会计统计</h2>
    <div class="stats-grid">
        <div class="stat-item" style="border-left: 4px solid #1890ff;">
            <div class="stat-value">{{ account_count }}</div>
            <div class="stat-label">会计科目数</div>
        </div>
        <div class="stat-item" style="border-left: 4px solid #faad14;">
            <div class="stat-value">{{ draft_count }}</div>
            <div class="stat-label">待审核凭证</div>
        </div>
        <div class="stat-item" style="border-left: 4px solid #1890ff;">
            <div class="stat-value">{{ reviewed_count }}</div>
            <div class="stat-label">已审核凭证</div>
        </div>
        <div class="stat-item" style="border-left: 4px solid #52c41a;">
            <div class="stat-value">{{ posted_count }}</div>
            <div class="stat-label">已记账凭证</div>
        </div>
    </div>
</div>

<div class="quick-actions">
    <a href="/order/new" class="btn">+ 新建订单</a>
    <a href="/income/new" class="btn btn-success">+ 录入收入</a>
    <a href="/expense/new" class="btn btn-warning">+ 录入支出</a>
    <a href="/vouchers" class="btn">+ 制作凭证</a>
    <a href="/accounting-books" class="btn btn-success">查账簿</a>
</div>

<div class="card">
    <h2>最近订单</h2>
    <table>
        <thead>
            <tr>
                <th>订单号</th>
                <th>客户</th>
                <th>金额</th>
                <th>状态</th>
                <th>日期</th>
            </tr>
        </thead>
        <tbody>
            {% for order in recent_orders %}
            <tr>
                <td>{{ order.order_no }}</td>
                <td>{{ order.customer_name }}</td>
                <td>{{ "%.2f"|format(order.total_amount) }}</td>
                <td><span class="status-badge status-{{ order.status }}">{{ order.status }}</span></td>
                <td>{{ order.order_date }}</td>
            </tr>
            {% endfor %}
        </tbody>
    </table>
</div>
{% endblock %}"""

    # ------ 订单列表模板 ------
    orders_html = """{% extends "base.html" %}
{% block title %}订单管理 - 氧化加工厂财务系统{% endblock %}
{% block content %}
<div class="card">
    <h2>订单列表</h2>
    <div style="margin-bottom: 20px;">
        <a href="/orders" class="btn">全部</a>
        {% for s in statuses %}
        <a href="/orders?status={{ s.status }}" class="btn">{{ s.status }}</a>
        {% endfor %}
        <a href="/order/new" class="btn" style="float: right;">+ 新建订单</a>
    </div>
    <table>
        <thead>
            <tr>
                <th>订单号</th>
                <th>客户</th>
                <th>物品</th>
                <th>金额</th>
                <th>状态</th>
                <th>日期</th>
            </tr>
        </thead>
        <tbody>
            {% for order in orders %}
            <tr>
                <td><a href="/order/edit/{{ order.id }}">{{ order.order_no }}</a></td>
                <td>{{ order.customer_name }}</td>
                <td>{{ order.item_description }}</td>
                <td>{{ "%.2f"|format(order.total_amount) }}</td>
                <td><span class="status-badge status-{{ order.status }}">{{ order.status }}</span></td>
                <td>{{ order.order_date }}</td>
            </tr>
            {% endfor %}
        </tbody>
    </table>
</div>
{% endblock %}"""

    # ------ 订单表单模板 ------
    order_form_html = """{% extends "base.html" %}
{% block title %}新建订单 - 氧化加工厂财务系统{% endblock %}
{% block content %}
<div class="card">
    <h2>{% if edit_mode %}编辑订单{% else %}新建订单{% endif %}</h2>
    <form method="POST">
        <div class="form-group">
            <label>客户名称</label>
            <input type="text" name="customer_name" list="customers" value="{{ order.customer_name if order else '' }}" required>
            <datalist id="customers">
                {% for c in customers %}<option value="{{ c.name }}">{% endfor %}
            </datalist>
        </div>
        <div class="form-group"><label>物品描述</label><input type="text" name="item_description" value="{{ order.item_description if order else '' }}" required></div>
        <div class="form-group"><label>计价单位</label><select name="pricing_unit">
            <option value="件">件</option><option value="公斤">公斤</option><option value="米" selected>米</option><option value="平方米">平方米</option>
        </select></div>
        <div class="form-group"><label>数量</label><input type="number" name="quantity" step="0.01" value="{{ order.quantity if order else '' }}" required></div>
        <div class="form-group"><label>单价</label><input type="number" name="unit_price" step="0.01" value="{{ order.unit_price if order else '' }}" required></div>
        <div class="form-group"><label>加工工序</label><input type="text" name="processes" value="{{ order.processes if order else '氧化' }}"></div>
        {% if edit_mode %}
        <div class="form-group"><label>状态</label><select name="status">
            <option>待加工</option><option>加工中</option><option>已完工</option><option>已交付</option>
        </select></div>
        {% endif %}
        <button type="submit" class="btn">保存订单</button>
        <a href="/orders" class="btn" style="background: #999;">取消</a>
    </form>
</div>
{% endblock %}"""

    # ------ 收入表单模板 ------
    income_form_html = """{% extends "base.html" %}
{% block title %}录入收入 - 氧化加工厂财务系统{% endblock %}
{% block content %}
<div class="card">
    <h2>{% if edit_mode %}编辑收入{% else %}录入收入{% endif %}</h2>
    <form method="POST">
        <div class="form-group"><label>客户名称</label><input type="text" name="customer_name" list="customers" value="{{ income.customer_name if income else '' }}" required>
            <datalist id="customers">{% for c in customers %}<option value="{{ c.name }}">{% endfor %}</datalist></div>
        <div class="form-group"><label>金额</label><input type="number" name="amount" step="0.01" value="{{ income.amount if income else '' }}" required></div>
        <div class="form-group"><label>银行账户</label><select name="bank_type"><option value="G银行">G银行</option><option value="N银行">N银行</option></select></div>
        <div class="form-group"><label>日期</label><input type="date" name="income_date" value="{{ income.income_date if income else today }}"></div>
        <div class="form-group"><label>备注</label><input type="text" name="notes" value="{{ income.notes if income else '' }}"></div>
        <button type="submit" class="btn btn-success">保存收入</button>
        <a href="/" class="btn" style="background: #999;">取消</a>
    </form>
</div>
{% endblock %}"""

    # ------ 支出表单模板 ------
    expense_form_html = """{% extends "base.html" %}
{% block title %}录入支出 - 氧化加工厂财务系统{% endblock %}
{% block content %}
<div class="card">
    <h2>{% if edit_mode %}编辑支出{% else %}录入支出{% endif %}</h2>
    <form method="POST">
        <div class="form-group"><label>支出类型</label><select name="expense_type">
            {% for t in expense_types %}<option value="{{ t }}">{{ t }}</option>{% endfor %}
        </select></div>
        <div class="form-group"><label>供应商</label><input type="text" name="supplier_name" value="{{ expense.supplier_name if expense else '' }}"></div>
        <div class="form-group"><label>金额</label><input type="number" name="amount" step="0.01" value="{{ expense.amount if expense else '' }}" required></div>
        <div class="form-group"><label>银行账户</label><select name="bank_type"><option value="G银行">G银行</option><option value="N银行">N银行</option></select></div>
        <div class="form-group"><label>日期</label><input type="date" name="expense_date" value="{{ expense.expense_date if expense else today }}"></div>
        <div class="form-group"><label>备注</label><input type="text" name="description" value="{{ expense.description if expense else '' }}"></div>
        <button type="submit" class="btn btn-warning">保存支出</button>
        <a href="/" class="btn" style="background: #999;">取消</a>
    </form>
</div>
{% endblock %}"""

    # ------ 客户列表模板 ------
    customers_html = """{% extends "base.html" %}
{% block title %}客户管理 - 氧化加工厂财务系统{% endblock %}
{% block content %}
<div class="card">
    <h2>客户列表</h2>
    <table>
        <thead><tr><th>客户名称</th><th>联系人</th><th>电话</th><th>订单数</th><th>累计金额</th></tr></thead>
        <tbody>
            {% for c in customers %}
            <tr>
                <td>{{ c.name }}</td>
                <td>{{ c.contact or '-' }}</td>
                <td>{{ c.phone or '-' }}</td>
                <td>{{ c.order_count }}</td>
                <td>{{ "%.2f"|format(c.total_amount or 0) }}</td>
            </tr>
            {% endfor %}
        </tbody>
    </table>
</div>
{% endblock %}"""

    # ------ 报表模板 ------
    reports_html = """{% extends "base.html" %}
{% block title %}报表中心 - 氧化加工厂财务系统{% endblock %}
{% block content %}

<div class="stats-grid">
    <div class="stat-item" style="border-left:4px solid #1890ff;">
        <div class="stat-value">{{ "%.2f"|format(total_income) }}</div>
        <div class="stat-label">累计收入</div>
    </div>
    <div class="stat-item" style="border-left:4px solid #f5222d;">
        <div class="stat-value">{{ "%.2f"|format(total_expense) }}</div>
        <div class="stat-label">累计支出</div>
    </div>
    <div class="stat-item" style="border-left:4px solid #52c41a;">
        <div class="stat-value">{{ "%.2f"|format(total_income - total_expense) }}</div>
        <div class="stat-label">累计盈余</div>
    </div>
    <div class="stat-item" style="border-left:4px solid #722ed1;">
        <div class="stat-value">{{ voucher_stats.total }}</div>
        <div class="stat-label">会计凭证总数</div>
    </div>
    <div class="stat-item" style="border-left:4px solid #52c41a;">
        <div class="stat-value">{{ voucher_stats.posted }}</div>
        <div class="stat-label">已记账凭证</div>
    </div>
    <div class="stat-item" style="border-left:4px solid #faad14;">
        <div class="stat-value">{{ order_count }}</div>
        <div class="stat-label">订单总数</div>
    </div>
</div>

{% if monthly_stats %}
<div class="card">
    <h2>月度收支统计</h2>
    <table>
        <thead><tr><th>月份</th><th class="num">收入</th><th class="num">支出</th><th class="num">利润</th></tr></thead>
        <tbody>
            {% for m in monthly_stats %}
            <tr>
                <td>{{ m.month }}</td>
                <td class="num">{{ "%.2f"|format(m.income) }}</td>
                <td class="num">{{ "%.2f"|format(m.expense) }}</td>
                <td class="num" style="color: {% if m.profit >= 0 %}#52c41a{% else %}#f5222d{% endif %}; font-weight:600;">
                    {{ "%.2f"|format(m.profit) }}
                </td>
            </tr>
            {% endfor %}
        </tbody>
    </table>
</div>
{% endif %}

{% if expense_by_type %}
<div class="card">
    <h2>支出分类统计</h2>
    <table>
        <thead><tr><th>支出类型</th><th class="num">金额</th></tr></thead>
        <tbody>
            {% for e in expense_by_type %}
            <tr><td>{{ e.expense_type }}</td><td class="num">{{ "%.2f"|format(e.total) }}</td></tr>
            {% endfor %}
        </tbody>
    </table>
</div>
{% endif %}

{% if top_customers %}
<div class="card">
    <h2>客户排名</h2>
    <table>
        <thead><tr><th>客户</th><th class="num">订单数</th><th class="num">累计金额</th></tr></thead>
        <tbody>
            {% for c in top_customers %}
            <tr><td>{{ c.name }}</td><td class="num">{{ c.order_count }}</td><td class="num">{{ "%.2f"|format(c.total) }}</td></tr>
            {% endfor %}
        </tbody>
    </table>
</div>
{% endif %}
{% endblock %}"""

    # ------ 错误页面模板 ------
    error_html = """{% extends "base.html" %}
{% block title %}错误 - 氧化加工厂财务系统{% endblock %}
{% block content %}
<div class="card" style="text-align: center; padding: 50px;">
    <h2 style="color: #f5222d;">出错了</h2>
    <p style="color: #666; margin: 20px 0;">{{ error }}</p>
    <a href="/" class="btn">返回首页</a>
</div>
{% endblock %}"""

    # 写入模板文件（注意：不覆盖已存在的独立模板文件如 chart_of_accounts.html 等）
    embedded_templates = {
        "base.html": base_html,
        "index.html": index_html,
        "orders.html": orders_html,
        "order_form.html": order_form_html,
        "income_form.html": income_form_html,
        "expense_form.html": expense_form_html,
        "customers.html": customers_html,
        "reports.html": reports_html,
        "error.html": error_html,
    }

    for filename, content in embedded_templates.items():
        target = template_dir / filename
        if not target.exists():
            target.write_text(content, encoding="utf-8")

    # API文档模板 - 始终覆盖以确保最新
    api_docs_html = """{% extends "base.html" %}
{% block title %}API文档{% endblock %}
{% block content %}
<div class="card">
    <h2>API文档</h2>
    <table>
        <thead><tr><th>接口</th><th>方法</th></tr></thead>
        <tbody>
            {% for r in routes %}
            <tr><td>{{ r.endpoint }}</td><td>{{ r.methods }}</td></tr>
            {% endfor %}
        </tbody>
    </table>
</div>
<div class="card">
    <h2>快速入口</h2>
    <p><a href="/api/search?q=氧化">GET /api/search?q=氧化</a> - 全局搜索</p>
    <p><a href="/api/stats">GET /api/stats</a> - 统计数据</p>
    <p><a href="/vouchers">会计凭证管理</a></p>
    <p><a href="/accounting-books">会计账簿查询</a></p>
</div>
{% endblock %}"""
    (template_dir / "api_docs.html").write_text(api_docs_html, encoding="utf-8")

    print(f"✅ 模板文件已生成到: {template_dir}")


# ========== 主程序 ==========

if __name__ == "__main__":
    print("=" * 70)
    print("🏭 氧化加工厂财务系统 V2.2 - Web版（模块化架构 + 会计科目体系）")
    print("=" * 70)
    print(f"\n数据库: {DB_PATH}")

    if not DB_PATH.exists():
        print(f"[ERROR] 数据库不存在: {DB_PATH}")
        print("请先运行: python examples/generate_comprehensive_demo.py")
        sys.exit(1)

    # 创建模板文件
    create_templates()

    print("\n✅ 启动成功！")
    print(f"\n请打开浏览器访问:\n  http://localhost:5000")
    print(f"\n📚 会计模块:")
    print(f"  会计科目: http://localhost:5000/chart-of-accounts")
    print(f"  会计凭证: http://localhost:5000/vouchers")
    print(f"  会计账簿: http://localhost:5000/accounting-books")
    print(f"\n按 Ctrl+C 停止服务")
    print("=" * 70)

    app.run(host="0.0.0.0", port=5000, debug=False)