#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""财务路由：收入、支出、报表"""

import uuid
from datetime import date, datetime, timedelta
from decimal import Decimal
from flask import Blueprint, render_template, request, redirect, url_for

from routes.helpers import get_db, to_float, auto_gen_voucher

finance_bp = Blueprint('finance', __name__)

# 支出类型
EXPENSE_TYPES = ["房租", "水电费", "三酸", "片碱", "亚钠", "色粉", "除油剂", "挂具", "外发加工费", "日常费用", "工资", "其他"]


@finance_bp.route("/income/new", methods=["GET", "POST"])
def new_income():
    """录入收入"""
    if request.method == "POST":
        conn = get_db()

        customer_name = request.form["customer_name"]
        customer = conn.execute("SELECT id FROM customers WHERE name = ?", (customer_name,)).fetchone()
        if not customer:
            customer_id = str(uuid.uuid4())
            conn.execute("INSERT INTO customers (id, name, created_at) VALUES (?, ?, ?)",
                         (customer_id, customer_name, datetime.now().isoformat()))
        else:
            customer_id = customer["id"]

        has_invoice = request.form.get("has_invoice") == "on"
        amount = Decimal(request.form["amount"])
        income_date = request.form.get("income_date", date.today().isoformat())

        conn.execute(
            """INSERT INTO incomes (id, customer_id, customer_name, amount, bank_type,
               has_invoice, income_date, notes, created_at)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (str(uuid.uuid4()), customer_id, customer_name, str(amount),
             request.form["bank_type"], 1 if has_invoice else 0,
             income_date, request.form.get("notes", ""), datetime.now().isoformat()),
        )

        # 自动生成会计凭证
        period = income_date[:7]
        auto_gen_voucher(conn, "INCOME", str(uuid.uuid4()), [
            {'code': '1002', 'debit': float(amount), 'credit': 0},
            {'code': '5001', 'debit': 0, 'credit': float(amount)},
        ], period, f"收{customer_name}货款")

        conn.commit()
        conn.close()
        return redirect(url_for("main.index"))

    conn = get_db()
    customers = conn.execute("SELECT name FROM customers ORDER BY name").fetchall()
    conn.close()
    return render_template("income_form.html", customers=customers)


@finance_bp.route("/expense/new", methods=["GET", "POST"])
def new_expense():
    """录入支出"""
    if request.method == "POST":
        conn = get_db()

        has_invoice = request.form.get("has_invoice") == "on"
        expense_type = request.form["expense_type"]
        amount = Decimal(request.form["amount"])
        expense_date = request.form.get("expense_date", date.today().isoformat())

        conn.execute(
            """INSERT INTO expenses (id, expense_type, supplier_name, amount, bank_type,
               has_invoice, expense_date, description, created_at)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (str(uuid.uuid4()), expense_type, request.form.get("supplier_name", ""),
             str(amount), request.form["bank_type"], 1 if has_invoice else 0,
             expense_date, request.form.get("description", ""), datetime.now().isoformat()),
        )

        # 自动生成会计凭证：根据支出类型选科目
        if expense_type in ["三酸", "片碱", "亚钠", "色粉", "除油剂", "挂具", "外发加工费"]:
            debit_code = '5401'  # 主营业务成本
        elif expense_type in ["房租", "水电费"]:
            debit_code = '4101'  # 制造费用
        elif expense_type == "工资":
            debit_code = '5602'  # 管理费用
        else:
            debit_code = '5602'  # 管理费用

        period = expense_date[:7]
        auto_gen_voucher(conn, "EXPENSE", str(uuid.uuid4()), [
            {'code': debit_code, 'debit': float(amount), 'credit': 0},
            {'code': '1002', 'debit': 0, 'credit': float(amount)},
        ], period, f"付{request.form.get('supplier_name', expense_type)}款")

        conn.commit()
        conn.close()
        return redirect(url_for("main.index"))

    return render_template("expense_form.html", expense_types=EXPENSE_TYPES)


@finance_bp.route("/income/edit/<income_id>", methods=["GET", "POST"])
def edit_income(income_id):
    """编辑收入"""
    conn = get_db()
    if request.method == "POST":
        conn.execute(
            """UPDATE incomes SET customer_name=?, amount=?, bank_type=?,
               income_date=?, notes=?, updated_at=? WHERE id=?""",
            (request.form["customer_name"], float(request.form["amount"]),
             request.form["bank_type"], request.form.get("income_date", date.today().isoformat()),
             request.form.get("notes", ""), datetime.now().isoformat(), income_id),
        )
        conn.commit()
        conn.close()
        return redirect(url_for("main.index"))

    income = conn.execute("SELECT * FROM incomes WHERE id = ?", (income_id,)).fetchone()
    if not income:
        conn.close()
        return redirect(url_for("main.index"))
    customers = conn.execute("SELECT name FROM customers ORDER BY name").fetchall()
    conn.close()
    return render_template("income_form.html", customers=customers, income=income, edit_mode=True)


@finance_bp.route("/expense/edit/<expense_id>", methods=["GET", "POST"])
def edit_expense(expense_id):
    """编辑支出"""
    conn = get_db()
    if request.method == "POST":
        conn.execute(
            """UPDATE expenses SET expense_type=?, supplier_name=?, amount=?, bank_type=?,
               expense_date=?, description=?, updated_at=? WHERE id=?""",
            (request.form["expense_type"], request.form.get("supplier_name", ""),
             float(request.form["amount"]), request.form["bank_type"],
             request.form.get("expense_date", date.today().isoformat()),
             request.form.get("description", ""), datetime.now().isoformat(), expense_id),
        )
        conn.commit()
        conn.close()
        return redirect(url_for("main.index"))

    expense = conn.execute("SELECT * FROM expenses WHERE id = ?", (expense_id,)).fetchone()
    if not expense:
        conn.close()
        return redirect(url_for("main.index"))
    conn.close()
    return render_template("expense_form.html", expense_types=EXPENSE_TYPES, expense=expense, edit_mode=True)


@finance_bp.route("/quick-income", methods=["GET", "POST"])
def quick_income():
    """快速记录收入"""
    import time
    if request.method == "POST":
        customer_name = request.form["customer_name"]
        amount = Decimal(request.form["amount"])
        has_invoice = request.form.get("has_invoice") == "on"
        is_n_bank = request.form.get("is_n_bank") == "on"
        notes = request.form.get("notes", "")

        conn = get_db()
        bank_type = "N银行" if is_n_bank else "G银行"

        customer = conn.execute("SELECT * FROM customers WHERE name = ?", (customer_name,)).fetchone()
        if not customer:
            conn.execute(
                """INSERT INTO customers (id, name, contact, phone, credit_limit, notes, created_at)
                   VALUES (?, ?, ?, ?, ?, ?, ?)""",
                (f"cust_{int(time.time())}", customer_name, "", "", "0", "", datetime.now().isoformat()))
            conn.commit()
        customer = conn.execute("SELECT * FROM customers WHERE name = ?", (customer_name,)).fetchone()

        income_id = f"income_{int(time.time())}"
        conn.execute(
            """INSERT INTO incomes (id, customer_id, customer_name, amount, bank_type,
               has_invoice, related_orders, allocation, income_date, notes, created_at)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (income_id, customer["id"], customer_name, str(amount), bank_type,
             has_invoice, "[]", "{}", date.today().isoformat(), notes, datetime.now().isoformat()))

        # 自动生成会计凭证
        period = date.today().isoformat()[:7]
        auto_gen_voucher(conn, "INCOME", income_id, [
            {'code': '1002', 'debit': float(amount), 'credit': 0},
            {'code': '5001', 'debit': 0, 'credit': float(amount)},
        ], period, f"快速收入-{customer_name}")

        conn.commit()
        conn.close()
        return redirect(url_for("assistant.assistant"))

    return render_template("quick_income.html")


@finance_bp.route("/quick-expense", methods=["GET", "POST"])
def quick_expense():
    """快速记录支出"""
    import time
    if request.method == "POST":
        expense_type = request.form["expense_type"]
        supplier_name = request.form.get("supplier_name", "")
        amount = Decimal(request.form["amount"])
        has_invoice = request.form.get("has_invoice") == "on"
        is_n_bank = request.form.get("is_n_bank") == "on"
        description = request.form.get("description", "")

        conn = get_db()
        bank_type = "N银行" if is_n_bank else "G银行"

        expense_id = f"expense_{int(time.time())}"
        conn.execute(
            """INSERT INTO expenses (id, expense_type, supplier_id, supplier_name, amount,
               bank_type, has_invoice, related_order_id, expense_date, description, notes, created_at)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (expense_id, expense_type, None, supplier_name, str(amount), bank_type,
             has_invoice, None, date.today().isoformat(), description, "", datetime.now().isoformat()))

        # 自动生成凭证
        period = date.today().isoformat()[:7]
        if expense_type in ["三酸", "片碱", "亚钠", "色粉", "除油剂", "挂具", "外发加工费"]:
            debit_code = '5401'
        elif expense_type in ["房租", "水电费"]:
            debit_code = '4101'
        else:
            debit_code = '5602'

        auto_gen_voucher(conn, "EXPENSE", expense_id, [
            {'code': debit_code, 'debit': float(amount), 'credit': 0},
            {'code': '1002', 'debit': 0, 'credit': float(amount)},
        ], period, f"快速支出-{supplier_name or expense_type}")

        conn.commit()
        conn.close()
        return redirect(url_for("assistant.assistant"))

    return render_template("quick_expense.html")


@finance_bp.route("/reports")
def reports():
    """报表中心"""
    conn = get_db()

    total_income = to_float(conn.execute("SELECT SUM(CAST(amount AS REAL)) FROM incomes").fetchone()[0])
    total_expense = to_float(conn.execute("SELECT SUM(CAST(amount AS REAL)) FROM expenses").fetchone()[0])
    order_count = conn.execute("SELECT COUNT(*) FROM processing_orders").fetchone()[0] or 0

    # 月度统计
    monthly_rows = conn.execute("""
        SELECT strftime('%Y-%m', income_date) as month,
               COALESCE(SUM(CAST(i.amount AS REAL)), 0) as income, 0 as expense
        FROM incomes i GROUP BY month
        UNION ALL
        SELECT strftime('%Y-%m', expense_date) as month,
               0 as income, COALESCE(SUM(CAST(e.amount AS REAL)), 0) as expense
        FROM expenses e GROUP BY month
        ORDER BY month
    """).fetchall()

    monthly_data = {}
    for row in monthly_rows:
        m = row["month"]
        if m not in monthly_data:
            monthly_data[m] = {"income": 0, "expense": 0}
        monthly_data[m]["income"] += row["income"]
        monthly_data[m]["expense"] += row["expense"]

    monthly_stats = sorted(
        [{"month": k, "income": v["income"], "expense": v["expense"],
          "profit": v["income"] - v["expense"]} for k, v in monthly_data.items()],
        key=lambda x: x["month"], reverse=True
    )[:12]

    # 客户排名
    top_customers = conn.execute("""
        SELECT c.name, COUNT(o.id) as order_count, COALESCE(SUM(CAST(o.total_amount AS REAL)), 0) as total
        FROM customers c LEFT JOIN processing_orders o ON c.id = o.customer_id
        GROUP BY c.id ORDER BY total DESC LIMIT 10
    """).fetchall()

    # 支出分类
    expense_by_type = conn.execute("""
        SELECT expense_type, SUM(CAST(amount AS REAL)) as total
        FROM expenses GROUP BY expense_type ORDER BY total DESC
    """).fetchall()

    # 会计凭证统计
    voucher_stats = {
        "total": conn.execute("SELECT COUNT(*) FROM accounting_vouchers").fetchone()[0] or 0,
        "posted": conn.execute("SELECT COUNT(*) FROM accounting_vouchers WHERE status='已记账'").fetchone()[0] or 0,
    }

    conn.close()

    return render_template("reports.html",
                           total_income=total_income, total_expense=total_expense,
                           order_count=order_count, monthly_stats=monthly_stats,
                           top_customers=top_customers, expense_by_type=expense_by_type,
                           voucher_stats=voucher_stats)