#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""主页面路由：首页、订单、客户"""

import uuid
from datetime import date, datetime
from flask import Blueprint, render_template, request, redirect, url_for

from routes.helpers import get_db, to_float, convert_rows_to_dicts

main_bp = Blueprint('main', __name__)


@main_bp.route("/")
def index():
    """首页 - 仪表盘"""
    conn = get_db()
    today = date.today().isoformat()

    # 今日统计
    today_income_row = conn.execute(
        "SELECT SUM(CAST(amount AS REAL)) FROM incomes WHERE income_date = ?", (today,)
    ).fetchone()[0]
    today_income = to_float(today_income_row)

    today_expense_row = conn.execute(
        "SELECT SUM(CAST(amount AS REAL)) FROM expenses WHERE expense_date = ?", (today,)
    ).fetchone()[0]
    today_expense = to_float(today_expense_row)

    pending_orders = (
        conn.execute(
            "SELECT COUNT(*) FROM processing_orders WHERE status IN ('待加工', '加工中')"
        ).fetchone()[0]
        or 0
    )
    unpaid_orders = (
        conn.execute(
            "SELECT COUNT(*) FROM processing_orders WHERE CAST(received_amount AS REAL) < CAST(total_amount AS REAL)"
        ).fetchone()[0]
        or 0
    )

    month_start = date.today().replace(day=1).isoformat()
    month_income = to_float(conn.execute(
        "SELECT SUM(CAST(amount AS REAL)) FROM incomes WHERE income_date >= ?", (month_start,)
    ).fetchone()[0])
    month_expense = to_float(conn.execute(
        "SELECT SUM(CAST(amount AS REAL)) FROM expenses WHERE expense_date >= ?", (month_start,)
    ).fetchone()[0])

    # 最近订单
    recent_orders_raw = conn.execute("""
        SELECT order_no, customer_name, total_amount, status, order_date
        FROM processing_orders ORDER BY order_date DESC LIMIT 5
    """).fetchall()
    recent_orders = [{'order_no': r[0], 'customer_name': r[1],
                       'total_amount': to_float(r[2]), 'status': r[3],
                       'order_date': r[4]} for r in recent_orders_raw]

    # 最近收支
    recent_incomes_raw = conn.execute(
        "SELECT customer_name, amount, bank_type, income_date FROM incomes ORDER BY income_date DESC LIMIT 5"
    ).fetchall()
    recent_incomes = [{'customer_name': r[0], 'amount': to_float(r[1]),
                        'bank_type': r[2], 'income_date': r[3]} for r in recent_incomes_raw]

    recent_expenses_raw = conn.execute(
        "SELECT expense_type, supplier_name, amount, bank_type, expense_date FROM expenses ORDER BY expense_date DESC LIMIT 5"
    ).fetchall()
    recent_expenses = [{'expense_type': r[0], 'supplier_name': r[1],
                         'amount': to_float(r[2]), 'bank_type': r[3],
                         'expense_date': r[4]} for r in recent_expenses_raw]

    # 会计统计
    account_count = conn.execute(
        "SELECT COUNT(*) FROM chart_of_accounts WHERE is_active=1"
    ).fetchone()[0] or 0
    draft_count = conn.execute(
        "SELECT COUNT(*) FROM accounting_vouchers WHERE status='草稿'"
    ).fetchone()[0] or 0
    reviewed_count = conn.execute(
        "SELECT COUNT(*) FROM accounting_vouchers WHERE status='已审核'"
    ).fetchone()[0] or 0
    posted_count = conn.execute(
        "SELECT COUNT(*) FROM accounting_vouchers WHERE status='已记账'"
    ).fetchone()[0] or 0

    conn.close()

    return render_template(
        "index.html",
        today_income=today_income, today_expense=today_expense,
        today_profit=today_income - today_expense,
        pending_orders=pending_orders, unpaid_orders=unpaid_orders,
        month_income=month_income, month_expense=month_expense,
        month_profit=month_income - month_expense,
        recent_orders=recent_orders, recent_incomes=recent_incomes,
        recent_expenses=recent_expenses,
        account_count=account_count, draft_count=draft_count,
        reviewed_count=reviewed_count, posted_count=posted_count,
    )


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