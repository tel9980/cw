#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""主页面路由：首页、订单、客户"""

import uuid
import hashlib
from datetime import date, datetime
from flask import Blueprint, render_template, request, redirect, url_for, session

from routes.helpers import get_db, to_float, convert_rows_to_dicts

main_bp = Blueprint('main', __name__)


@main_bp.route("/login", methods=["GET", "POST"])
def login():
    """用户登录"""
    error = None
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "").strip()
        if not username or not password:
            error = "请输入用户名和密码"
        else:
            conn = get_db()
            conn.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    id TEXT PRIMARY KEY, username TEXT UNIQUE NOT NULL,
                    password TEXT NOT NULL, role TEXT NOT NULL DEFAULT '记账会计',
                    is_active INTEGER DEFAULT 1, created_at TEXT NOT NULL
                )
            """)
            # Ensure default admin
            exist = conn.execute("SELECT COUNT(*) FROM users").fetchone()[0]
            if exist == 0:
                conn.execute(
                    "INSERT INTO users (id, username, password, role, is_active, created_at) VALUES (?,?,?,?,?,?)",
                    (str(uuid.uuid4()), "admin",
                     hashlib.sha256("admin123".encode()).hexdigest(),
                     "管理员", 1, datetime.now().isoformat()))
                conn.commit()

            pwd_hash = hashlib.sha256(password.encode()).hexdigest()
            user = conn.execute(
                "SELECT id, username, role FROM users WHERE username=? AND password=? AND is_active=1",
                (username, pwd_hash)
            ).fetchone()
            conn.close()

            if user:
                session["user"] = {"id": user[0], "username": user[1],
                                    "display_name": user[1], "role": user[2]}
                next_url = request.args.get("next", "/")
                return redirect(next_url)
            else:
                error = "用户名或密码错误，或账号已被禁用"

    return render_template("login.html", error=error)


@main_bp.route("/logout")
def logout():
    """退出登录"""
    session.pop("user", None)
    return redirect(url_for("main.login"))


@main_bp.route("/")
def index():
    """首页 - 仪表盘"""
    conn = get_db()
    today = date.today().isoformat()
    month_start = date.today().replace(day=1).isoformat()

    # 今日/本月统计
    today_income = to_float(conn.execute(
        "SELECT SUM(CAST(amount AS REAL)) FROM incomes WHERE income_date=?", (today,)
    ).fetchone()[0])
    today_expense = to_float(conn.execute(
        "SELECT SUM(CAST(amount AS REAL)) FROM expenses WHERE expense_date=?", (today,)
    ).fetchone()[0])
    month_income = to_float(conn.execute(
        "SELECT SUM(CAST(amount AS REAL)) FROM incomes WHERE income_date>=?", (month_start,)
    ).fetchone()[0])
    month_expense = to_float(conn.execute(
        "SELECT SUM(CAST(amount AS REAL)) FROM expenses WHERE expense_date>=?", (month_start,)
    ).fetchone()[0])
    total_income = to_float(conn.execute(
        "SELECT SUM(CAST(amount AS REAL)) FROM incomes").fetchone()[0])
    total_expense = to_float(conn.execute(
        "SELECT SUM(CAST(amount AS REAL)) FROM expenses").fetchone()[0])

    # 银行余额
    bank_total = to_float(conn.execute(
        "SELECT SUM(CAST(balance AS REAL)) FROM bank_accounts").fetchone()[0])

    # 应收账款
    ar_total = to_float(conn.execute("""
        SELECT COALESCE(SUM(CAST(l.debit AS REAL)) - SUM(CAST(l.credit AS REAL)), 0)
        FROM voucher_lines l JOIN accounting_vouchers v ON v.id=l.voucher_id
        WHERE l.account_code='1122' AND v.status='已记账'
    """).fetchone()[0])

    # 应付账款
    ap_total = to_float(conn.execute("""
        SELECT COALESCE(SUM(CAST(l.credit AS REAL)) - SUM(CAST(l.debit AS REAL)), 0)
        FROM voucher_lines l JOIN accounting_vouchers v ON v.id=l.voucher_id
        WHERE (l.account_code LIKE '220%') AND v.status='已记账'
    """).fetchone()[0])

    # 订单统计
    pending_orders = conn.execute(
        "SELECT COUNT(*) FROM processing_orders WHERE status IN ('待加工','加工中')"
    ).fetchone()[0] or 0
    unpaid_orders = conn.execute(
        "SELECT COUNT(*) FROM processing_orders WHERE CAST(received_amount AS REAL) < CAST(total_amount AS REAL)"
    ).fetchone()[0] or 0

    # 凭证状态
    draft_count = conn.execute("SELECT COUNT(*) FROM accounting_vouchers WHERE status='草稿'").fetchone()[0] or 0
    reviewed_count = conn.execute("SELECT COUNT(*) FROM accounting_vouchers WHERE status='已审核'").fetchone()[0] or 0
    posted_count = conn.execute("SELECT COUNT(*) FROM accounting_vouchers WHERE status='已记账'").fetchone()[0] or 0

    # 月度趋势(最近6个月)
    monthly_rows = conn.execute("""
        SELECT strftime('%Y-%m', income_date) m, SUM(CAST(amount AS REAL)) inc, 0 exp
        FROM incomes GROUP BY m UNION ALL
        SELECT strftime('%Y-%m', expense_date) m, 0 inc, SUM(CAST(amount AS REAL)) exp
        FROM expenses GROUP BY m ORDER BY m
    """).fetchall()
    month_map = {}
    for r in monthly_rows:
        m = r[0]; month_map.setdefault(m, {"inc":0,"exp":0})
        month_map[m]["inc"] += to_float(r[1]); month_map[m]["exp"] += to_float(r[2])
    monthly_data = sorted([{"m":k, "inc":v["inc"], "exp":v["exp"],
        "profit":v["inc"]-v["exp"]} for k,v in month_map.items()], key=lambda x:x["m"])[-6:]

    # 支出分类Top5
    expense_cats = [dict(r) for r in conn.execute(
        "SELECT expense_type, SUM(CAST(amount AS REAL)) total FROM expenses "
        "GROUP BY expense_type ORDER BY total DESC LIMIT 5").fetchall()]

    # 最近5笔收支
    recent_inc = [dict(r) for r in conn.execute(
        "SELECT customer_name, CAST(amount AS REAL) amount, bank_type, income_date "
        "FROM incomes ORDER BY income_date DESC LIMIT 5").fetchall()]
    recent_exp = [dict(r) for r in conn.execute(
        "SELECT expense_type, supplier_name, CAST(amount AS REAL) amount, bank_type, expense_date "
        "FROM expenses ORDER BY expense_date DESC LIMIT 5").fetchall()]

    # 最近订单
    recent_orders = [dict(r) for r in conn.execute("""
        SELECT order_no, customer_name, CAST(total_amount AS REAL) total_amount, status, order_date
        FROM processing_orders ORDER BY order_date DESC LIMIT 5
    """).fetchall()]

    # 固定资产
    fa_count = conn.execute("SELECT COUNT(*) FROM fixed_assets WHERE status='使用中'").fetchone()[0] or 0

    conn.close()

    import json
    return render_template("index.html",
        today_income=today_income, today_expense=today_expense,
        today_profit=today_income-today_expense,
        month_income=month_income, month_expense=month_expense,
        month_profit=month_income-month_expense,
        total_income=total_income, total_expense=total_expense,
        bank_total=bank_total, ar_total=ar_total, ap_total=ap_total,
        pending_orders=pending_orders, unpaid_orders=unpaid_orders,
        draft_count=draft_count, reviewed_count=reviewed_count,
        posted_count=posted_count, fa_count=fa_count,
        monthly_data=json.dumps(monthly_data),
        expense_cats=expense_cats,
        recent_inc=recent_inc, recent_exp=recent_exp,
        recent_orders=recent_orders)


@main_bp.route("/orders")
def orders():
    """订单列表"""
    conn = get_db()
    status_filter = request.args.get("status", "")

    if status_filter:
        orders = conn.execute(
            "SELECT * FROM processing_orders WHERE status = ? ORDER BY order_date DESC",
            (status_filter,),
        ).fetchall()
    else:
        orders = conn.execute(
            "SELECT * FROM processing_orders ORDER BY order_date DESC LIMIT 50"
        ).fetchall()

    orders = convert_rows_to_dicts(orders)
    statuses = conn.execute("SELECT DISTINCT status FROM processing_orders").fetchall()
    conn.close()

    return render_template("orders.html", orders=orders, statuses=statuses, current_status=status_filter)


@main_bp.route("/order/new", methods=["GET", "POST"])
def new_order():
    """新建订单"""
    if request.method == "POST":
        conn = get_db()

        order_no = f"OX{date.today().strftime('%Y%m')}{conn.execute('SELECT COUNT(*) FROM processing_orders').fetchone()[0] + 1:03d}"
        customer_name = request.form["customer_name"]
        customer = conn.execute("SELECT id FROM customers WHERE name = ?", (customer_name,)).fetchone()

        if not customer:
            customer_id = str(uuid.uuid4())
            conn.execute("INSERT INTO customers (id, name, created_at) VALUES (?, ?, ?)",
                         (customer_id, customer_name, datetime.now().isoformat()))
        else:
            customer_id = customer["id"]

        quantity = float(request.form["quantity"])
        unit_price = float(request.form["unit_price"])
        total_amount = quantity * unit_price

        conn.execute(
            """INSERT INTO processing_orders
               (id, order_no, customer_id, customer_name, item_description, quantity,
                pricing_unit, unit_price, processes, total_amount, status, order_date,
                created_at, updated_at)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, '待加工', ?, ?, ?)""",
            (str(uuid.uuid4()), order_no, customer_id, customer_name,
             request.form["item_description"], quantity, request.form["pricing_unit"],
             unit_price, request.form.get("processes", "氧化"), total_amount,
             request.form.get("order_date", date.today().isoformat()),
             datetime.now().isoformat(), datetime.now().isoformat()),
        )

        conn.commit()
        conn.close()
        return redirect(url_for("main.orders"))

    conn = get_db()
    customers = conn.execute("SELECT name FROM customers ORDER BY name").fetchall()
    conn.close()
    return render_template("order_form.html", customers=customers, order=None, edit_mode=False)


@main_bp.route("/order/edit/<order_id>", methods=["GET", "POST"])
def edit_order(order_id):
    """编辑订单"""
    conn = get_db()

    if request.method == "POST":
        quantity = float(request.form["quantity"])
        unit_price = float(request.form["unit_price"])
        total_amount = quantity * unit_price

        conn.execute(
            """UPDATE processing_orders SET
               customer_name=?, item_description=?, quantity=?, pricing_unit=?,
               unit_price=?, total_amount=?, processes=?, status=?, updated_at=?
               WHERE id=?""",
            (request.form["customer_name"], request.form["item_description"],
             quantity, request.form["pricing_unit"], unit_price, total_amount,
             request.form.get("processes", "氧化"), request.form.get("status", "待加工"),
             datetime.now().isoformat(), order_id),
        )
        conn.commit()
        conn.close()
        return redirect(url_for("main.orders"))

    order = conn.execute("SELECT * FROM processing_orders WHERE id = ?", (order_id,)).fetchone()
    if not order:
        conn.close()
        return redirect(url_for("main.orders"))

    customers = conn.execute("SELECT name FROM customers ORDER BY name").fetchall()
    conn.close()
    return render_template("order_form.html", customers=customers, order=order, edit_mode=True)


@main_bp.route("/order/delete/<order_id>")
def delete_order(order_id):
    """删除订单"""
    conn = get_db()
    conn.execute("DELETE FROM processing_orders WHERE id = ?", (order_id,))
    conn.commit()
    conn.close()
    return redirect(url_for("main.orders"))


@main_bp.route("/customers")
def customers():
    """客户列表"""
    conn = get_db()
    customers = conn.execute("""
        SELECT c.*, COUNT(o.id) as order_count, SUM(o.total_amount) as total_amount
        FROM customers c
        LEFT JOIN processing_orders o ON c.id = o.customer_id
        GROUP BY c.id ORDER BY total_amount DESC
    """).fetchall()
    conn.close()
    return render_template("customers.html", customers=customers)