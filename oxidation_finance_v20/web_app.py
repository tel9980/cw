#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Web版财务系统 - 极简高效

功能：
- 今日概览仪表盘
- 快速录入（订单/收入/支出）
- 数据查看与搜索
- 一键报表导出
- 自动备份

使用方法：
    python web_app.py
    然后打开浏览器访问: http://localhost:5000
"""

import sys
from pathlib import Path
from datetime import date, datetime, timedelta
from decimal import Decimal
import sqlite3
import json
from functools import wraps
from oxidation_finance_v20.database.db_manager import DatabaseManager
from oxidation_finance_v20.reports import ReportManager
from oxidation_finance_v20.utils.config import get_db_path

# 尝试导入Flask
try:
    from flask import Flask, render_template, request, jsonify, redirect, url_for
except ImportError:
    print("[ERROR] 需要先安装Flask:")
    print("  pip install flask")
    sys.exit(1)

app = Flask(__name__, template_folder=Path(__file__).resolve().parent / "templates")
# 禁用Jinja模板缓存
app.jinja_env.auto_reload = True
app.config["TEMPLATES_AUTO_RELOAD"] = True
app.config["SEND_FILE_MAX_AGE_DEFAULT"] = 0

# 数据库路径 - 使用统一配置路径获取（支持自定义环境变量 CWZS_DB_PATH）
DB_PATH = Path(get_db_path())  # type: ignore
if not DB_PATH.exists():
    # 回退到旧的演示数据库路径，以确保开发环境可用
    DB_PATH = Path(__file__).resolve().parent / "oxidation_finance_demo_ready.db"
    if not DB_PATH.exists():
        DB_PATH = Path(__file__).resolve().parent / "oxidation_finance_demo.db"


def get_db():
    """获取数据库连接"""
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    return conn


# ---------------------- 简易报表 API ----------------------
@app.route("/api/reports/summary")
def api_reports_summary():
    """简易报表摘要 API（聚合性数据，便于前端展示或对接）"""
    conn = get_db()
    today = date.today().isoformat()
    total_income = conn.execute("SELECT SUM(amount) FROM incomes").fetchone()[0] or 0
    total_expense = conn.execute("SELECT SUM(amount) FROM expenses").fetchone()[0] or 0
    order_count = (
        conn.execute("SELECT COUNT(*) FROM processing_orders").fetchone()[0] or 0
    )

    # 本月汇总利润
    month_start = date.today().replace(day=1).isoformat()
    month_income = (
        conn.execute(
            "SELECT SUM(amount) FROM incomes WHERE income_date >= ?", (month_start,)
        ).fetchone()[0]
        or 0
    )
    month_expense = (
        conn.execute(
            "SELECT SUM(amount) FROM expenses WHERE expense_date >= ?", (month_start,)
        ).fetchone()[0]
        or 0
    )
    month_profit = float(month_income - month_expense)

    # 月度统计列表
    monthly_rows = conn.execute("""
        SELECT strftime('%Y-%m', income_date) AS month, SUM(amount) AS income
        FROM incomes
        GROUP BY month
        ORDER BY month DESC
    """).fetchall()
    exp_rows = conn.execute("""
        SELECT strftime('%Y-%m', expense_date) AS month, SUM(amount) AS expense
        FROM expenses
        GROUP BY month
        ORDER BY month DESC
    """).fetchall()
    data = {}
    for r in monthly_rows:
        data[str(r["month"])] = float(r["income"])
    for er in exp_rows:
        key = str(er["month"])
        data[key] = data.get(key, 0.0) - float(er["expense"])
    monthly_stats_list = [{"month": k, "profit": float(v)} for k, v in data.items()]
    monthly_stats_list = sorted(
        monthly_stats_list, key=lambda x: x["month"], reverse=True
    )[:12]

    # 顾客排名
    top_customers = conn.execute("""
        SELECT c.name, COUNT(o.id) AS order_count, COALESCE(SUM(o.total_amount), 0) AS total
        FROM customers c
        LEFT JOIN processing_orders o ON c.id = o.customer_id
        GROUP BY c.id
        ORDER BY total DESC
        LIMIT 10
    """).fetchall()
    top_customers_list = [
        {
            "name": t["name"],
            "order_count": int(t["order_count"]),
            "total": float(t["total"]),
        }
        for t in top_customers
    ]

    # 支出类型聚合
    expense_by_type = conn.execute("""
        SELECT expense_type, SUM(amount) AS total
        FROM expenses
        GROUP BY expense_type
        ORDER BY total DESC
    """).fetchall()
    expense_by_type_list = [
        {"expense_type": e["expense_type"], "total": float(e["total"])}
        for e in expense_by_type
    ]

    conn.close()
    return jsonify(
        {
            "summary": {
                "total_income": float(total_income),
                "total_expense": float(total_expense),
                "order_count": int(order_count),
                "profit": float(total_income - total_expense),
            },
            "monthly": monthly_stats_list,
            "top_customers": top_customers_list,
            "expense_by_type": expense_by_type_list,
            "today": today,
            "month_profit": month_profit,
        }
    )


@app.route("/api/reports/monthly")
def api_reports_monthly():
    """分月报表数据（月度利润等）"""
    try:
        with DatabaseManager(str(DB_PATH)) as db:
            rm = ReportManager(db)
            data = rm.get_monthly_stats()
        return jsonify({"monthly": data})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/reports/top-customers")
def api_reports_top_customers():
    """前10客户贡献报表"""
    try:
        with DatabaseManager(str(DB_PATH)) as db:
            rm = ReportManager(db)
            data = rm.get_top_customers()
        return jsonify({"top_customers": data})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/reports/expense-by-type")
def api_reports_expense_by_type():
    """支出类型聚合报表"""
    try:
        with DatabaseManager(str(DB_PATH)) as db:
            rm = ReportManager(db)
            data = rm.get_expense_by_type()
        return jsonify({"expense_by_type": data})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/reports/dashboard")
def reports_dashboard():
    """简易看板：聚合报表的前端视图入口"""
    with DatabaseManager(str(DB_PATH)) as db:
        rm = ReportManager(db)
        data = rm.generate_all_reports()
    return render_template(
        "reports_dashboard.html", data=data, today=date.today().isoformat()
    )


# ========== 页面路由 ==========


@app.route("/")
def index():
    """首页 - 仪表盘"""
    conn = get_db()
    today = date.today().isoformat()

    # 今日统计
    today_income = (
        conn.execute(
            "SELECT SUM(amount) FROM incomes WHERE income_date = ?", (today,)
        ).fetchone()[0]
        or 0
    )
    today_expense = (
        conn.execute(
            "SELECT SUM(amount) FROM expenses WHERE expense_date = ?", (today,)
        ).fetchone()[0]
        or 0
    )

    # 待处理
    pending_orders = (
        conn.execute(
            "SELECT COUNT(*) FROM processing_orders WHERE status IN ('待加工', '加工中')"
        ).fetchone()[0]
        or 0
    )
    unpaid_orders = (
        conn.execute(
            "SELECT COUNT(*) FROM processing_orders WHERE received_amount < total_amount"
        ).fetchone()[0]
        or 0
    )

    # 本月统计
    month_start = date.today().replace(day=1).isoformat()
    month_income = (
        conn.execute(
            "SELECT SUM(amount) FROM incomes WHERE income_date >= ?", (month_start,)
        ).fetchone()[0]
        or 0
    )
    month_expense = (
        conn.execute(
            "SELECT SUM(amount) FROM expenses WHERE expense_date >= ?", (month_start,)
        ).fetchone()[0]
        or 0
    )

    # 最近订单
    recent_orders = conn.execute("""
        SELECT order_no, customer_name, total_amount, status, order_date
        FROM processing_orders
        ORDER BY order_date DESC
        LIMIT 5
    """).fetchall()

    # 最近收入
    recent_incomes = conn.execute("""
        SELECT customer_name, amount, bank_type, income_date
        FROM incomes
        ORDER BY income_date DESC
        LIMIT 5
    """).fetchall()

    # 最近支出
    recent_expenses = conn.execute("""
        SELECT expense_type, supplier_name, amount, bank_type, expense_date
        FROM expenses
        ORDER BY expense_date DESC
        LIMIT 5
    """).fetchall()

    conn.close()

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


@app.route("/orders")
def orders():
    """订单列表"""
    conn = get_db()
    status_filter = request.args.get("status", "")

    if status_filter:
        orders = conn.execute(
            """
            SELECT * FROM processing_orders
            WHERE status = ?
            ORDER BY order_date DESC
        """,
            (status_filter,),
        ).fetchall()
    else:
        orders = conn.execute("""
            SELECT * FROM processing_orders
            ORDER BY order_date DESC
            LIMIT 50
        """).fetchall()

    # 获取所有状态
    statuses = conn.execute("SELECT DISTINCT status FROM processing_orders").fetchall()
    conn.close()

    return render_template(
        "orders.html", orders=orders, statuses=statuses, current_status=status_filter
    )


@app.route("/order/new", methods=["GET", "POST"])
def new_order():
    """新建订单"""
    if request.method == "POST":
        conn = get_db()

        # 生成订单号
        order_no = f"OX{date.today().strftime('%Y%m')}{conn.execute('SELECT COUNT(*) FROM processing_orders').fetchone()[0] + 1:03d}"

        # 获取客户信息
        customer_name = request.form["customer_name"]
        customer = conn.execute(
            "SELECT id FROM customers WHERE name = ?", (customer_name,)
        ).fetchone()

        if not customer:
            # 自动创建客户
            import uuid

            customer_id = str(uuid.uuid4())
            conn.execute(
                """
                INSERT INTO customers (id, name, created_at)
                VALUES (?, ?, ?)
            """,
                (customer_id, customer_name, datetime.now().isoformat()),
            )
        else:
            customer_id = customer["id"]

        # 计算金额
        quantity = float(request.form["quantity"])
        unit_price = float(request.form["unit_price"])
        total_amount = quantity * unit_price

        # 插入订单
        import uuid

        conn.execute(
            """
            INSERT INTO processing_orders 
            (id, order_no, customer_id, customer_name, item_description, quantity,
             pricing_unit, unit_price, total_amount, processes, status, order_date, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
            (
                str(uuid.uuid4()),
                order_no,
                customer_id,
                customer_name,
                request.form["item_description"],
                quantity,
                request.form["pricing_unit"],
                unit_price,
                total_amount,
                request.form.get("processes", "氧化"),
                "待加工",
                date.today().isoformat(),
                datetime.now().isoformat(),
                datetime.now().isoformat(),
            ),
        )

        conn.commit()
        conn.close()

        return redirect(url_for("orders"))

    # GET请求
    conn = get_db()
    customers = conn.execute("SELECT name FROM customers ORDER BY name").fetchall()
    conn.close()

    return render_template("order_form.html", customers=customers)


@app.route("/income/new", methods=["GET", "POST"])
def new_income():
    """录入收入"""
    if request.method == "POST":
        conn = get_db()
        import uuid

        conn.execute(
            """
            INSERT INTO incomes (id, customer_name, amount, bank_type, income_date, notes, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """,
            (
                str(uuid.uuid4()),
                request.form["customer_name"],
                float(request.form["amount"]),
                request.form["bank_type"],
                request.form.get("income_date", date.today().isoformat()),
                request.form.get("notes", ""),
                datetime.now().isoformat(),
            ),
        )

        conn.commit()
        conn.close()
        return redirect(url_for("index"))

    conn = get_db()
    customers = conn.execute("SELECT name FROM customers ORDER BY name").fetchall()
    conn.close()
    return render_template("income_form.html", customers=customers)


@app.route("/expense/new", methods=["GET", "POST"])
def new_expense():
    """录入支出"""
    if request.method == "POST":
        conn = get_db()
        import uuid

        conn.execute(
            """
            INSERT INTO expenses (id, expense_type, supplier_name, amount, bank_type, 
                                expense_date, description, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """,
            (
                str(uuid.uuid4()),
                request.form["expense_type"],
                request.form.get("supplier_name", ""),
                float(request.form["amount"]),
                request.form["bank_type"],
                request.form.get("expense_date", date.today().isoformat()),
                request.form.get("description", ""),
                datetime.now().isoformat(),
            ),
        )

        conn.commit()
        conn.close()
        return redirect(url_for("index"))

    expense_types = [
        "房租",
        "水电费",
        "三酸",
        "片碱",
        "亚钠",
        "色粉",
        "除油剂",
        "挂具",
        "外发加工费",
        "日常费用",
        "工资",
        "其他",
    ]
    return render_template("expense_form.html", expense_types=expense_types)


@app.route("/order/edit/<order_id>", methods=["GET", "POST"])
def edit_order(order_id):
    """编辑订单"""
    conn = get_db()

    if request.method == "POST":
        quantity = float(request.form["quantity"])
        unit_price = float(request.form["unit_price"])
        total_amount = quantity * unit_price

        conn.execute(
            """
            UPDATE processing_orders SET
            customer_name = ?, item_description = ?, quantity = ?,
            pricing_unit = ?, unit_price = ?, total_amount = ?,
            processes = ?, status = ?, updated_at = ?
            WHERE id = ?
        """,
            (
                request.form["customer_name"],
                request.form["item_description"],
                quantity,
                request.form["pricing_unit"],
                unit_price,
                total_amount,
                request.form.get("processes", "氧化"),
                request.form.get("status", "待加工"),
                datetime.now().isoformat(),
                order_id,
            ),
        )

        conn.commit()
        conn.close()
        return redirect(url_for("orders"))

    # GET请求
    order = conn.execute(
        "SELECT * FROM processing_orders WHERE id = ?", (order_id,)
    ).fetchone()

    if not order:
        conn.close()
        return redirect(url_for("orders"))

    customers = conn.execute("SELECT name FROM customers ORDER BY name").fetchall()
    conn.close()

    return render_template(
        "order_form.html", customers=customers, order=order, edit_mode=True
    )


@app.route("/order/delete/<order_id>")
def delete_order(order_id):
    """删除订单"""
    conn = get_db()
    conn.execute("DELETE FROM processing_orders WHERE id = ?", (order_id,))
    conn.commit()
    conn.close()
    return redirect(url_for("orders"))


@app.route("/income/edit/<income_id>", methods=["GET", "POST"])
def edit_income(income_id):
    """编辑收入"""
    conn = get_db()

    if request.method == "POST":
        conn.execute(
            """
            UPDATE incomes SET
            customer_name = ?, amount = ?, bank_type = ?,
            income_date = ?, notes = ?, updated_at = ?
            WHERE id = ?
        """,
            (
                request.form["customer_name"],
                float(request.form["amount"]),
                request.form["bank_type"],
                request.form.get("income_date", date.today().isoformat()),
                request.form.get("notes", ""),
                datetime.now().isoformat(),
                income_id,
            ),
        )

        conn.commit()
        conn.close()
        return redirect(url_for("index"))

    # GET请求
    income = conn.execute("SELECT * FROM incomes WHERE id = ?", (income_id,)).fetchone()

    if not income:
        conn.close()
        return redirect(url_for("index"))

    customers = conn.execute("SELECT name FROM customers ORDER BY name").fetchall()
    conn.close()

    return render_template(
        "income_form.html", customers=customers, income=income, edit_mode=True
    )


@app.route("/expense/edit/<expense_id>", methods=["GET", "POST"])
def edit_expense(expense_id):
    """编辑支出"""
    conn = get_db()

    if request.method == "POST":
        conn.execute(
            """
            UPDATE expenses SET
            expense_type = ?, supplier_name = ?, amount = ?, bank_type = ?,
            expense_date = ?, description = ?, updated_at = ?
            WHERE id = ?
        """,
            (
                request.form["expense_type"],
                request.form.get("supplier_name", ""),
                float(request.form["amount"]),
                request.form["bank_type"],
                request.form.get("expense_date", date.today().isoformat()),
                request.form.get("description", ""),
                datetime.now().isoformat(),
                expense_id,
            ),
        )

        conn.commit()
        conn.close()
        return redirect(url_for("index"))

    # GET请求
    expense = conn.execute(
        "SELECT * FROM expenses WHERE id = ?", (expense_id,)
    ).fetchone()

    if not expense:
        conn.close()
        return redirect(url_for("index"))

    expense_types = [
        "房租",
        "水电费",
        "三酸",
        "片碱",
        "亚钠",
        "色粉",
        "除油剂",
        "挂具",
        "外发加工费",
        "日常费用",
        "工资",
        "其他",
    ]
    conn.close()

    return render_template(
        "expense_form.html",
        expense_types=expense_types,
        expense=expense,
        edit_mode=True,
    )


@app.route("/customers")
def customers():
    """客户列表"""
    conn = get_db()
    customers = conn.execute("""
        SELECT c.*, COUNT(o.id) as order_count, SUM(o.total_amount) as total_amount
        FROM customers c
        LEFT JOIN processing_orders o ON c.id = o.customer_id
        GROUP BY c.id
        ORDER BY total_amount DESC
    """).fetchall()
    conn.close()
    return render_template("customers.html", customers=customers)


@app.route("/reports")
def reports():
    """报表中心"""
    conn = get_db()

    # 总收入/支出
    total_income = conn.execute("SELECT SUM(amount) FROM incomes").fetchone()[0] or 0
    total_expense = conn.execute("SELECT SUM(amount) FROM expenses").fetchone()[0] or 0

    # 订单总数
    order_count = (
        conn.execute("SELECT COUNT(*) FROM processing_orders").fetchone()[0] or 0
    )

    # 月度统计
    monthly_stats = conn.execute("""
        SELECT 
            strftime('%Y-%m', income_date) as month,
            COALESCE(SUM(i.amount), 0) as income,
            0 as expense
        FROM incomes i
        GROUP BY month
        UNION ALL
        SELECT 
            strftime('%Y-%m', expense_date) as month,
            0 as income,
            COALESCE(SUM(e.amount), 0) as expense
        FROM expenses e
        GROUP BY month
        ORDER BY month
    """).fetchall()

    # 聚合月度数据
    monthly_data = {}
    for row in monthly_stats:
        month = row["month"]
        if month not in monthly_data:
            monthly_data[month] = {"income": 0, "expense": 0}
        monthly_data[month]["income"] += row["income"]
        monthly_data[month]["expense"] += row["expense"]

    monthly_stats = [
        {
            "month": k,
            "income": v["income"],
            "expense": v["expense"],
            "profit": v["income"] - v["expense"],
        }
        for k, v in monthly_data.items()
    ]
    monthly_stats = sorted(monthly_stats, key=lambda x: x["month"], reverse=True)[:12]

    # 客户排名
    top_customers = conn.execute("""
        SELECT c.name, COUNT(o.id) as order_count, COALESCE(SUM(o.total_amount), 0) as total
        FROM customers c
        LEFT JOIN processing_orders o ON c.id = o.customer_id
        GROUP BY c.id
        ORDER BY total DESC
        LIMIT 10
    """).fetchall()

    # 支出分类
    expense_by_type = conn.execute("""
        SELECT expense_type, SUM(amount) as total
        FROM expenses
        GROUP BY expense_type
        ORDER BY total DESC
    """).fetchall()

    conn.close()

    return render_template(
        "reports.html",
        total_income=total_income,
        total_expense=total_expense,
        order_count=order_count,
        monthly_stats=monthly_stats,
        top_customers=top_customers,
        expense_by_type=expense_by_type,
    )


@app.route("/api/search")
def api_search():
    """搜索API"""
    keyword = request.args.get("q", "")
    if not keyword:
        return jsonify({"results": []})

    conn = get_db()
    kw = f"%{keyword}%"

    # 搜索客户
    customers = conn.execute(
        "SELECT name, contact FROM customers WHERE name LIKE ? LIMIT 5", (kw,)
    ).fetchall()

    # 搜索订单
    orders = conn.execute(
        "SELECT order_no, customer_name, total_amount FROM processing_orders WHERE order_no LIKE ? OR customer_name LIKE ? LIMIT 5",
        (kw, kw),
    ).fetchall()

    conn.close()

    return jsonify(
        {
            "customers": [
                {"name": c["name"], "contact": c["contact"]} for c in customers
            ],
            "orders": [
                {
                    "order_no": o["order_no"],
                    "customer": o["customer_name"],
                    "amount": float(o["total_amount"]),
                }
                for o in orders
            ],
        }
    )


@app.route("/api/stats")
def api_stats():
    """统计数据API"""
    conn = get_db()
    today = date.today().isoformat()

    stats = {
        "today_income": conn.execute(
            "SELECT SUM(amount) FROM incomes WHERE income_date = ?", (today,)
        ).fetchone()[0]
        or 0,
        "today_expense": conn.execute(
            "SELECT SUM(amount) FROM expenses WHERE expense_date = ?", (today,)
        ).fetchone()[0]
        or 0,
        "pending_orders": conn.execute(
            "SELECT COUNT(*) FROM processing_orders WHERE status IN ('待加工', '加工中')"
        ).fetchone()[0]
        or 0,
        "unpaid_orders": conn.execute(
            "SELECT COUNT(*) FROM processing_orders WHERE received_amount < total_amount"
        ).fetchone()[0]
        or 0,
    }

    conn.close()
    return jsonify(stats)


# ========== HTML模板 ==========


@app.route("/templates/<path:filename>")
def serve_template(filename):
    """提供模板文件"""
    from flask import send_from_directory

    return send_from_directory("templates", filename)


# 创建模板目录和文件
def create_templates():
    """创建HTML模板"""
    template_dir = Path(__file__).parent / "templates"
    template_dir.mkdir(exist_ok=True)

    # 基础模板
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
    </style>
</head>
<body>
    <div class="header">
        <div class="container">
            <h1>氧化加工厂财务系统 V2.0</h1>
        </div>
    </div>
    <div class="nav">
        <div class="container">
            <a href="/">首页</a>
            <a href="/orders">订单</a>
            <a href="/customers">客户</a>
            <a href="/reports">报表</a>
            <a href="/reports/dashboard">看板</a>
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

<div class="quick-actions">
    <a href="/order/new" class="btn">+ 新建订单</a>
    <a href="/income/new" class="btn btn-success">+ 录入收入</a>
    <a href="/expense/new" class="btn btn-warning">+ 录入支出</a>
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

    # 订单列表模板
    orders_html = """{% extends "base.html" %}

{% block title %}订单管理 - 氧化加工厂财务系统{% endblock %}

{% block content %}
<div class="card">
    <h2>订单列表</h2>
    <div style="margin-bottom: 20px;">
        <a href="/orders" class="btn {% if not current_status %}btn-primary{% endif %}">全部</a>
        {% for status in statuses %}
        <a href="/orders?status={{ status.status }}" class="btn {% if current_status == status.status %}btn-primary{% endif %}">{{ status.status }}</a>
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
                <td>{{ order.order_no }}</td>
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

    # 订单表单模板
    order_form_html = """{% extends "base.html" %}

{% block title %}新建订单 - 氧化加工厂财务系统{% endblock %}

{% block content %}
<div class="card">
    <h2>新建订单</h2>
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
        <div class="form-group">
            <label>加工工序</label>
            <input type="text" name="processes" value="氧化" placeholder="如：喷砂,氧化">
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
    <h2>录入收入</h2>
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
            <input type="text" name="notes" placeholder="如：订单OX202401001收款">
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
    <h2>录入支出</h2>
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
    <h2>客户列表</h2>
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
                <td>{{ "%.2f"|format(customer.total_amount or 0) }}</td>
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
<div class="card">
    <h2>报表中心</h2>
    <p>请使用命令行工具生成详细报表：</p>
    <div style="background: #f5f5f5; padding: 15px; border-radius: 4px; margin: 20px 0;">
        <code>python oxidation_finance_v20/tools/report_exporter.py --all</code>
    </div>
    <p>或在浏览器控制台运行：</p>
    <div style="background: #f5f5f5; padding: 15px; border-radius: 4px; margin: 20px 0;">
        <code>python oxidation_finance_v20/tools/quick_panel.py</code><br>
        <code>python oxidation_finance_v20/tools/reminder_system.py</code>
    </div>
    <p>报表将生成在 <code>reports/</code> 目录下</p>
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
    # 新增看板模板
    dashboard_html = """{% extends "base.html" %}

{% block title %}报表看板 - 氧化加工厂财务系统{% endblock %}

{% block content %}
<div class="card">
  <h2>报表看板</h2>
  <h3>汇总</h3>
  <table>
    <tr><th>总收入</th><td>{{ data.summary.total_income }}</td></tr>
    <tr><th>总支出</th><td>{{ data.summary.total_expense }}</td></tr>
    <tr><th>订单数量</th><td>{{ data.summary.order_count }}</td></tr>
    <tr><th>利润</th><td>{{ data.summary.profit }}</td></tr>
  </table>
  <h3>月度利润</h3>
  <table>
    <tr><th>月份</th><th>利润</th></tr>
    {% for m in data.monthly %}
    <tr><td>{{ m.month }}</td><td>{{ m.profit }}</td></tr>
    {% endfor %}
  </table>
  <h3>Top 客户</h3>
  <table>
    <tr><th>名称</th><th>订单数</th><th>总额</th></tr>
    {% for c in data.top_customers %}
    <tr><td>{{ c.name }}</td><td>{{ c.order_count }}</td><td>{{ c.total }}</td></tr>
    {% endfor %}
  </table>
  <h3>支出类型</h3>
  <table>
    <tr><th>类型</th><th>总额</th></tr>
    {% for e in data.expense_by_type %}
    <tr><td>{{ e.expense_type }}</td><td>{{ e.total }}</td></tr>
    {% endfor %}
  </table>
</div>
{% endblock %}"""
    (template_dir / "reports_dashboard.html").write_text(
        dashboard_html, encoding="utf-8"
    )


# ========== 主程序 ==========

if __name__ == "__main__":
    # 检查数据库
    if not DB_PATH.exists():
        print(f"[ERROR] 数据库不存在: {DB_PATH}")
        print(
            "请先运行: python oxidation_finance_v20/examples/generate_comprehensive_demo.py"
        )
        sys.exit(1)

    # 创建模板
    create_templates()

    print("\n" + "=" * 70)
    print("氧化加工厂财务系统 V2.0 - Web版")
    print("=" * 70)
    print(f"\n数据库: {DB_PATH}")
    print("\n启动成功！")
    print("\n请打开浏览器访问:")
    print("  http://localhost:5000")
    print("\n按 Ctrl+C 停止服务")
    print("=" * 70 + "\n")

    # 启动服务
    app.run(host="0.0.0.0", port=5000, debug=False)
