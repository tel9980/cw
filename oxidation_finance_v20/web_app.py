#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Web版财务系统 V2.1 - 使用业务层重构

功能：
- 今日概览仪表盘
- 快速录入（订单/收入/支出）
- 数据查看与搜索
- 一键报表导出
- 自动备份

优化：
- 使用业务层（OrderManager, FinanceManager）
- 更好的错误处理
- 结构化日志记录

使用方法：
    python web_app.py
    然后打开浏览器访问: http://localhost:5000
"""

import sys
import logging
from pathlib import Path
from datetime import date, datetime
from decimal import Decimal

try:
    from flask import Flask, render_template, request, jsonify, redirect, url_for, abort
except ImportError:
    print("[ERROR] 需要先安装Flask:")
    print("  pip install flask")
    sys.exit(1)

# 设置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

app = Flask(__name__, template_folder=Path(__file__).resolve().parent / "templates")
app.jinja_env.auto_reload = True
app.config["TEMPLATES_AUTO_RELOAD"] = True
app.config["SEND_FILE_MAX_AGE_DEFAULT"] = 0

# 数据库路径
DB_PATH = Path(__file__).resolve().parent / "oxidation_finance_demo_ready.db"
if not DB_PATH.exists():
    DB_PATH = Path(__file__).resolve().parent / "oxidation_finance_demo.db"

# 业务层组件
try:
    import oxidation_finance_v20 as package
    from oxidation_finance_v20.database.db_manager import DatabaseManager
    from oxidation_finance_v20.business.order_manager import OrderManager
    from oxidation_finance_v20.business.finance_manager import FinanceManager
    from oxidation_finance_v20.models.business_models import (
        Customer, ProcessingOrder, Income, Expense, BankAccount, BankTransaction,
        PricingUnit, ProcessType, OrderStatus, ExpenseType, BankType
    )
    logger.info("✅ 业务层组件加载成功")
except ImportError as e:
    logger.error(f"❌ 无法导入业务层组件: {e}")
    print("[ERROR] 无法导入业务层组件:")
    print("  请确保项目结构正确")
    print("  提示: 请在项目根目录 /workspace 运行此脚本")
    sys.exit(1)


def get_db():
    """获取数据库连接"""
    try:
        db = DatabaseManager(str(DB_PATH))
        db.connect()
        return db
    except Exception as e:
        logger.error(f"数据库连接失败: {e}")
        raise


def init_business_managers():
    """初始化业务管理器"""
    db = get_db()
    order_mgr = OrderManager(db)
    finance_mgr = FinanceManager(db)
    return db, order_mgr, finance_mgr


# ========== 页面路由 ==========


@app.route("/")
def index():
    """首页 - 仪表盘"""
    logger.info("访问首页仪表盘")

    try:
        db, order_mgr, finance_mgr = init_business_managers()
        today = date.today().isoformat()

        # 今日统计
        today_income = finance_mgr.get_today_income(today)
        today_expense = finance_mgr.get_today_expense(today)

        # 待处理订单
        pending_orders = order_mgr.count_pending_orders()
        unpaid_orders = order_mgr.count_unpaid_orders()

        # 本月统计
        month_start = date.today().replace(day=1).isoformat()
        month_income = finance_mgr.get_income_by_period(month_start)
        month_expense = finance_mgr.get_expense_by_period(month_start)

        # 最近记录
        recent_orders = order_mgr.list_orders(limit=5)
        recent_incomes = finance_mgr.list_incomes(limit=5)
        recent_expenses = finance_mgr.list_expenses(limit=5)

        db.close()

        return render_template(
            "index.html",
            today_income=today_income,
            today_expense=today_expense,
            today_profit=today_income - today_expense,
            pending_orders=pending_orders,
            unpaid_orders=unpaid_orders,
            month_income=month_income,
            month_expense=month_expense,
            month_profit=month_income - month_expense,
            recent_orders=recent_orders,
            recent_incomes=recent_incomes,
            recent_expenses=recent_expenses,
        )
    except Exception as e:
        logger.error(f"首页加载失败: {e}")
        return render_template("error.html", error=str(e)), 500


@app.route("/orders")
def orders():
    """订单列表"""
    logger.info("访问订单列表")

    try:
        db, order_mgr, _ = init_business_managers()
        status_filter = request.args.get("status", "")

        if status_filter:
            orders = order_mgr.list_orders(status=OrderStatus(status_filter))
        else:
            orders = order_mgr.list_orders(limit=50)

        statuses = [s.value for s in OrderStatus]
        db.close()

        return render_template(
            "orders.html",
            orders=orders,
            statuses=[{'status': s} for s in statuses],
            current_status=status_filter
        )
    except Exception as e:
        logger.error(f"订单列表加载失败: {e}")
        return render_template("error.html", error=str(e)), 500


@app.route("/order/new", methods=["GET", "POST"])
def new_order():
    """新建订单"""
    logger.info("访问新建订单页面")

    try:
        db, order_mgr, _ = init_business_managers()

        if request.method == "POST":
            # 从表单获取数据
            customer_name = request.form["customer_name"]
            quantity = Decimal(request.form["quantity"])
            unit_price = Decimal(request.form["unit_price"])
            total_amount = quantity * unit_price

            # 获取或创建客户
            customers = db.list_customers()
            customer = next((c for c in customers if c.name == customer_name), None)

            if not customer:
                customer = Customer(name=customer_name)
                db.save_customer(customer)

            # 创建订单
            order = ProcessingOrder(
                order_no=order_mgr.generate_order_no(),
                customer_id=customer.id,
                customer_name=customer_name,
                item_description=request.form["item_description"],
                quantity=quantity,
                pricing_unit=PricingUnit(request.form["pricing_unit"]),
                unit_price=unit_price,
                total_amount=total_amount,
                processes=[ProcessType.OXIDATION],
                status=OrderStatus.PENDING,
                order_date=date.today(),
            )

            order_mgr.save_order(order)
            db.close()

            logger.info(f"✅ 新建订单成功: {order.order_no}")
            return redirect(url_for("orders"))

        # GET请求
        customers = db.list_customers()
        db.close()

        return render_template("order_form.html", customers=[{'name': c.name} for c in customers])

    except Exception as e:
        logger.error(f"新建订单失败: {e}")
        return render_template("error.html", error=str(e)), 500


@app.route("/income/new", methods=["GET", "POST"])
def new_income():
    """录入收入"""
    logger.info("访问录入收入页面")

    try:
        db, _, finance_mgr = init_business_managers()

        if request.method == "POST":
            income = Income(
                customer_name=request.form["customer_name"],
                amount=Decimal(request.form["amount"]),
                bank_type=BankType(request.form["bank_type"]),
                income_date=date.fromisoformat(request.form.get("income_date", date.today().isoformat())),
                notes=request.form.get("notes", ""),
            )

            finance_mgr.record_income(income)
            db.close()

            logger.info(f"✅ 录入收入成功: ¥{income.amount}")
            return redirect(url_for("index"))

        # GET请求
        customers = db.list_customers()
        db.close()

        return render_template("income_form.html", customers=[{'name': c.name} for c in customers])

    except Exception as e:
        logger.error(f"录入收入失败: {e}")
        return render_template("error.html", error=str(e)), 500


@app.route("/expense/new", methods=["GET", "POST"])
def new_expense():
    """录入支出"""
    logger.info("访问录入支出页面")

    try:
        db, _, finance_mgr = init_business_managers()

        if request.method == "POST":
            expense = Expense(
                expense_type=ExpenseType(request.form["expense_type"]),
                supplier_name=request.form.get("supplier_name", ""),
                amount=Decimal(request.form["amount"]),
                bank_type=BankType(request.form["bank_type"]),
                expense_date=date.fromisoformat(request.form.get("expense_date", date.today().isoformat())),
                description=request.form.get("description", ""),
            )

            finance_mgr.record_expense(expense)
            db.close()

            logger.info(f"✅ 录入支出成功: ¥{expense.amount}")
            return redirect(url_for("index"))

        # GET请求
        db.close()
        expense_types = [et.value for et in ExpenseType]

        return render_template("expense_form.html", expense_types=expense_types)

    except Exception as e:
        logger.error(f"录入支出失败: {e}")
        return render_template("error.html", error=str(e)), 500


@app.route("/customers")
def customers():
    """客户列表"""
    logger.info("访问客户列表")

    try:
        db, _, _ = init_business_managers()
        customers_list = db.list_customers()
        db.close()

        # 增强客户信息（添加订单统计）
        customers_data = []
        for c in customers_list:
            customers_data.append({
                'name': c.name,
                'contact': c.contact,
                'phone': c.phone,
                'order_count': 0,
                'total_amount': 0
            })

        return render_template("customers.html", customers=customers_data)

    except Exception as e:
        logger.error(f"客户列表加载失败: {e}")
        return render_template("error.html", error=str(e)), 500


@app.route("/reports")
def reports():
    """报表中心"""
    logger.info("访问报表中心")

    try:
        db, _, finance_mgr = init_business_managers()

        # 获取财务统计
        stats = finance_mgr.get_financial_summary()
        monthly_stats = finance_mgr.get_monthly_stats(limit=12)
        top_customers = finance_mgr.get_top_customers(limit=10)
        expense_by_type = finance_mgr.get_expense_by_type()

        db.close()

        return render_template(
            "reports.html",
            total_income=stats.get('total_income', 0),
            total_expense=stats.get('total_expense', 0),
            order_count=stats.get('order_count', 0),
            monthly_stats=monthly_stats,
            top_customers=top_customers,
            expense_by_type=expense_by_type,
        )
    except Exception as e:
        logger.error(f"报表中心加载失败: {e}")
        return render_template("error.html", error=str(e)), 500


# ========== API 路由 ==========


@app.route("/api/search")
def api_search():
    """搜索API"""
    keyword = request.args.get("q", "")
    if not keyword:
        return jsonify({"results": []})

    logger.info(f"搜索: {keyword}")

    try:
        db, order_mgr, _ = init_business_managers()

        # 搜索客户
        customers = db.list_customers()
        matched_customers = [
            {"name": c.name, "contact": c.contact}
            for c in customers
            if keyword.lower() in c.name.lower()
        ][:5]

        # 搜索订单
        orders = order_mgr.list_orders(limit=10)
        matched_orders = [
            {
                "order_no": o.order_no,
                "customer": o.customer_name,
                "amount": float(o.total_amount),
            }
            for o in orders
            if keyword.lower() in o.order_no.lower() or keyword.lower() in o.customer_name.lower()
        ][:5]

        db.close()

        return jsonify({
            "customers": matched_customers,
            "orders": matched_orders,
        })
    except Exception as e:
        logger.error(f"搜索失败: {e}")
        return jsonify({"error": str(e)}), 500


@app.route("/api/stats")
def api_stats():
    """统计数据API"""
    try:
        db, order_mgr, finance_mgr = init_business_managers()
        today = date.today().isoformat()

        stats = {
            "today_income": float(finance_mgr.get_today_income(today)),
            "today_expense": float(finance_mgr.get_today_expense(today)),
            "pending_orders": order_mgr.count_pending_orders(),
            "unpaid_orders": order_mgr.count_unpaid_orders(),
        }

        db.close()
        return jsonify(stats)
    except Exception as e:
        logger.error(f"统计API失败: {e}")
        return jsonify({"error": str(e)}), 500


# ========== 错误处理 ==========


@app.errorhandler(404)
def not_found(error):
    """404错误"""
    logger.warning(f"404错误: {request.url}")
    return render_template("error.html", error="页面未找到"), 404


@app.errorhandler(500)
def internal_error(error):
    """500错误"""
    logger.error(f"服务器错误: {error}")
    return render_template("error.html", error="服务器内部错误"), 500


# ========== 模板 ==========


@app.route("/templates/<path:filename>")
def serve_template(filename):
    """提供模板文件"""
    from flask import send_from_directory
    return send_from_directory("templates", filename)


def create_templates():
    """创建HTML模板"""
    template_dir = Path(__file__).parent / "templates"
    template_dir.mkdir(exist_ok=True)

    # 错误页面模板
    error_html = """<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <title>错误 - 氧化加工厂财务系统</title>
    <style>
        body { font-family: Arial, sans-serif; background: #f5f5f5; padding: 40px; text-align: center; }
        .error-container { background: white; padding: 40px; border-radius: 8px; max-width: 600px; margin: 0 auto; }
        h1 { color: #ff4d4f; }
        p { color: #666; }
        a { color: #1890ff; }
    </style>
</head>
<body>
    <div class="error-container">
        <h1>出错了</h1>
        <p>{{ error }}</p>
        <p><a href="/">返回首页</a></p>
    </div>
</body>
</html>"""

    (template_dir / "error.html").write_text(error_html, encoding="utf-8")

    # 基础模板（复用原有内容）
    base_html = """<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{% block title %}氧化加工厂财务系统 V2.1{% endblock %}</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body { font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; background: #f5f5f5; }
        .container { max-width: 1200px; margin: 0 auto; padding: 20px; }
        .header { background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 20px; margin-bottom: 20px; }
        .header h1 { font-size: 24px; }
        .nav { background: white; padding: 10px 20px; margin-bottom: 20px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }
        .nav a { color: #333; text-decoration: none; margin-right: 20px; padding: 5px 10px; border-radius: 4px; }
        .nav a:hover { background: #667eea; color: white; }
        .card { background: white; padding: 20px; margin-bottom: 20px; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }
        .card h2 { font-size: 18px; margin-bottom: 15px; color: #333; }
        .stats-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 15px; }
        .stat-item { background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 20px; border-radius: 8px; text-align: center; }
        .stat-value { font-size: 28px; font-weight: bold; }
        .stat-label { font-size: 14px; margin-top: 8px; opacity: 0.9; }
        .btn { display: inline-block; padding: 10px 20px; background: #667eea; color: white; text-decoration: none; border-radius: 4px; border: none; cursor: pointer; transition: all 0.3s; }
        .btn:hover { background: #764ba2; transform: translateY(-2px); }
        .btn-success { background: #52c41a; }
        .btn-warning { background: #faad14; }
        table { width: 100%; border-collapse: collapse; }
        th, td { padding: 12px; text-align: left; border-bottom: 1px solid #eee; }
        th { background: #f8f9fa; font-weight: 600; }
        tr:hover { background: #f5f5f5; }
        .form-group { margin-bottom: 15px; }
        .form-group label { display: block; margin-bottom: 5px; font-weight: 500; }
        .form-group input, .form-group select { width: 100%; padding: 10px; border: 1px solid #d9d9d9; border-radius: 4px; }
        .status-badge { padding: 4px 8px; border-radius: 4px; font-size: 12px; }
        .status-待加工 { background: #fff7e6; color: #fa8c16; }
        .status-加工中 { background: #e6f7ff; color: #1890ff; }
        .status-已完工 { background: #f6ffed; color: #52c41a; }
        .quick-actions { display: grid; grid-template-columns: repeat(auto-fit, minmax(150px, 1fr)); gap: 10px; margin-top: 20px; }
    </style>
</head>
<body>
    <div class="header">
        <div class="container">
            <h1>🏭 氧化加工厂财务系统 V2.1</h1>
        </div>
    </div>
    <div class="nav">
        <div class="container">
            <a href="/">📊 首页</a>
            <a href="/orders">📋 订单</a>
            <a href="/customers">👥 客户</a>
            <a href="/reports">📈 报表</a>
        </div>
    </div>
    <div class="container">
        {% block content %}{% endblock %}
    </div>
</body>
</html>"""

    # 首页模板
    index_html = """{% extends "base.html" %}

{% block content %}
<div class="stats-grid">
    <div class="stat-item">
        <div class="stat-value">¥{{ "%.2f"|format(today_income) }}</div>
        <div class="stat-label">📈 今日收入</div>
    </div>
    <div class="stat-item">
        <div class="stat-value">¥{{ "%.2f"|format(today_expense) }}</div>
        <div class="stat-label">📉 今日支出</div>
    </div>
    <div class="stat-item">
        <div class="stat-value">¥{{ "%.2f"|format(today_profit) }}</div>
        <div class="stat-label">💰 今日利润</div>
    </div>
    <div class="stat-item">
        <div class="stat-value">{{ pending_orders }}</div>
        <div class="stat-label">⏳ 待加工订单</div>
    </div>
    <div class="stat-item">
        <div class="stat-value">{{ unpaid_orders }}</div>
        <div class="stat-label">💵 未收款订单</div>
    </div>
    <div class="stat-item">
        <div class="stat-value">¥{{ "%.2f"|format(month_profit) }}</div>
        <div class="stat-label">📅 本月利润</div>
    </div>
</div>

<div class="quick-actions">
    <a href="/order/new" class="btn">➕ 新建订单</a>
    <a href="/income/new" class="btn btn-success">💵 录入收入</a>
    <a href="/expense/new" class="btn btn-warning">💸 录入支出</a>
</div>

<div class="card">
    <h2>📋 最近订单</h2>
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
                <td>¥{{ "%.2f"|format(order.total_amount) }}</td>
                <td><span class="status-badge status-{{ order.status.value }}">{{ order.status.value }}</span></td>
                <td>{{ order.order_date }}</td>
            </tr>
            {% endfor %}
        </tbody>
    </table>
</div>
{% endblock %}"""

    # 订单列表模板
    orders_html = """{% extends "base.html" %}

{% block title %}订单管理 - 氧化加工厂财务系统{% endblock %}

{% block content %}
<div class="card">
    <h2>📋 订单列表</h2>
    <div style="margin-bottom: 20px;">
        <a href="/orders" class="btn">全部</a>
        {% for status in statuses %}
        <a href="/orders?status={{ status.status }}" class="btn">{{ status.status }}</a>
        {% endfor %}
        <a href="/order/new" class="btn" style="float: right;">➕ 新建订单</a>
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
                <td>{{ order.order_no }}</td>
                <td>{{ order.customer_name }}</td>
                <td>{{ order.item_description }}</td>
                <td>¥{{ "%.2f"|format(order.total_amount) }}</td>
                <td><span class="status-badge status-{{ order.status.value }}">{{ order.status.value }}</span></td>
                <td>{{ order.order_date }}</td>
            </tr>
            {% endfor %}
        </tbody>
    </table>
</div>
{% endblock %}"""

    # 订单表单模板
    order_form_html = """{% extends "base.html" %}

{% block title %}新建订单 - 氧化加工厂财务系统{% endblock %}

{% block content %}
<div class="card">
    <h2>➕ 新建订单</h2>
    <form method="POST">
        <div class="form-group">
            <label>客户名称</label>
            <input type="text" name="customer_name" list="customers" placeholder="输入或选择客户" required>
            <datalist id="customers">
                {% for customer in customers %}
                <option value="{{ customer.name }}">
                {% endfor %}
            </datalist>
        </div>
        <div class="form-group">
            <label>物品描述</label>
            <input type="text" name="item_description" placeholder="如：铝型材6063氧化" required>
        </div>
        <div class="form-group">
            <label>计价单位</label>
            <select name="pricing_unit">
                <option value="件">件</option>
                <option value="条">条</option>
                <option value="只">只</option>
                <option value="个">个</option>
                <option value="米" selected>米</option>
                <option value="公斤">公斤</option>
                <option value="平方米">平方米</option>
            </select>
        </div>
        <div class="form-group">
            <label>数量</label>
            <input type="number" name="quantity" step="0.01" required>
        </div>
        <div class="form-group">
            <label>单价</label>
            <input type="number" name="unit_price" step="0.01" required>
        </div>
        <button type="submit" class="btn">保存订单</button>
        <a href="/orders" class="btn" style="background: #999;">取消</a>
    </form>
</div>
{% endblock %}"""

    # 收入表单模板
    income_form_html = """{% extends "base.html" %}

{% block title %}录入收入 - 氧化加工厂财务系统{% endblock %}

{% block content %}
<div class="card">
    <h2>💵 录入收入</h2>
    <form method="POST">
        <div class="form-group">
            <label>客户名称</label>
            <input type="text" name="customer_name" list="customers" required>
            <datalist id="customers">
                {% for customer in customers %}
                <option value="{{ customer.name }}">
                {% endfor %}
            </datalist>
        </div>
        <div class="form-group">
            <label>金额</label>
            <input type="number" name="amount" step="0.01" required>
        </div>
        <div class="form-group">
            <label>银行账户</label>
            <select name="bank_type">
                <option value="G银行">G银行（有发票）</option>
                <option value="N银行">N银行（现金/微信）</option>
            </select>
        </div>
        <div class="form-group">
            <label>日期</label>
            <input type="date" name="income_date" value="{{ today }}" required>
        </div>
        <div class="form-group">
            <label>备注</label>
            <input type="text" name="notes" placeholder="如：订单收款">
        </div>
        <button type="submit" class="btn btn-success">保存收入</button>
        <a href="/" class="btn" style="background: #999;">取消</a>
    </form>
</div>
{% endblock %}"""

    # 支出表单模板
    expense_form_html = """{% extends "base.html" %}

{% block title %}录入支出 - 氧化加工厂财务系统{% endblock %}

{% block content %}
<div class="card">
    <h2>💸 录入支出</h2>
    <form method="POST">
        <div class="form-group">
            <label>支出类型</label>
            <select name="expense_type">
                {% for type in expense_types %}
                <option value="{{ type }}">{{ type }}</option>
                {% endfor %}
            </select>
        </div>
        <div class="form-group">
            <label>供应商/说明</label>
            <input type="text" name="supplier_name" placeholder="如：化工原料公司">
        </div>
        <div class="form-group">
            <label>金额</label>
            <input type="number" name="amount" step="0.01" required>
        </div>
        <div class="form-group">
            <label>银行账户</label>
            <select name="bank_type">
                <option value="G银行">G银行（有发票）</option>
                <option value="N银行">N银行（现金/微信）</option>
            </select>
        </div>
        <div class="form-group">
            <label>日期</label>
            <input type="date" name="expense_date" value="{{ today }}" required>
        </div>
        <div class="form-group">
            <label>备注</label>
            <input type="text" name="description" placeholder="如：三酸采购">
        </div>
        <button type="submit" class="btn btn-warning">保存支出</button>
        <a href="/" class="btn" style="background: #999;">取消</a>
    </form>
</div>
{% endblock %}"""

    # 客户列表模板
    customers_html = """{% extends "base.html" %}

{% block title %}客户管理 - 氧化加工厂财务系统{% endblock %}

{% block content %}
<div class="card">
    <h2>👥 客户列表</h2>
    <table>
        <thead>
            <tr>
                <th>客户名称</th>
                <th>联系人</th>
                <th>电话</th>
                <th>订单数</th>
                <th>累计金额</th>
            </tr>
        </thead>
        <tbody>
            {% for customer in customers %}
            <tr>
                <td>{{ customer.name }}</td>
                <td>{{ customer.contact or '-' }}</td>
                <td>{{ customer.phone or '-' }}</td>
                <td>{{ customer.order_count }}</td>
                <td>¥{{ "%.2f"|format(customer.total_amount or 0) }}</td>
            </tr>
            {% endfor %}
        </tbody>
    </table>
</div>
{% endblock %}"""

    # 报表中心模板
    reports_html = """{% extends "base.html" %}

{% block title %}报表中心 - 氧化加工厂财务系统{% endblock %}

{% block content %}
<div class="stats-grid">
    <div class="stat-item">
        <div class="stat-value">¥{{ "%.2f"|format(total_income) }}</div>
        <div class="stat-label">💰 总收入</div>
    </div>
    <div class="stat-item">
        <div class="stat-value">¥{{ "%.2f"|format(total_expense) }}</div>
        <div class="stat-label">💸 总支出</div>
    </div>
    <div class="stat-item">
        <div class="stat-value">{{ order_count }}</div>
        <div class="stat-label">📋 订单总数</div>
    </div>
</div>

<div class="card">
    <h2>📅 月度统计</h2>
    <table>
        <thead>
            <tr>
                <th>月份</th>
                <th>收入</th>
                <th>支出</th>
                <th>利润</th>
            </tr>
        </thead>
        <tbody>
            {% for stat in monthly_stats %}
            <tr>
                <td>{{ stat.month }}</td>
                <td>¥{{ "%.2f"|format(stat.income) }}</td>
                <td>¥{{ "%.2f"|format(stat.expense) }}</td>
                <td>¥{{ "%.2f"|format(stat.profit) }}</td>
            </tr>
            {% endfor %}
        </tbody>
    </table>
</div>
{% endblock %}"""

    # 写入模板文件
    (template_dir / "base.html").write_text(base_html, encoding="utf-8")
    (template_dir / "index.html").write_text(index_html, encoding="utf-8")
    (template_dir / "orders.html").write_text(orders_html, encoding="utf-8")
    (template_dir / "order_form.html").write_text(order_form_html, encoding="utf-8")
    (template_dir / "income_form.html").write_text(income_form_html, encoding="utf-8")
    (template_dir / "expense_form.html").write_text(expense_form_html, encoding="utf-8")
    (template_dir / "customers.html").write_text(customers_html, encoding="utf-8")
    (template_dir / "reports.html").write_text(reports_html, encoding="utf-8")


# ========== 主程序 ==========


if __name__ == "__main__":
    # 检查数据库
    if not DB_PATH.exists():
        print(f"[ERROR] 数据库不存在: {DB_PATH}")
        print("请先运行: python oxidation_finance_v20/examples/generate_comprehensive_demo.py")
        sys.exit(1)

    # 创建模板
    create_templates()

    print("\n" + "=" * 70)
    print("🏭 氧化加工厂财务系统 V2.1 - Web版（业务层重构版）")
    print("=" * 70)
    print(f"\n数据库: {DB_PATH}")
    print("\n✅ 启动成功！")
    print("\n请打开浏览器访问:")
    print("  http://localhost:5000")
    print("\n按 Ctrl+C 停止服务")
    print("=" * 70 + "\n")

    # 启动服务
    app.run(host="0.0.0.0", port=5000, debug=False)
