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

    # 本月统计
    month_start = date.today().replace(day=1).isoformat()
    month_income = to_float(conn.execute(
        "SELECT SUM(CAST(amount AS REAL)) FROM incomes WHERE income_date >= ?", (month_start,)).fetchone()[0])
    month_expense = to_float(conn.execute(
        "SELECT SUM(CAST(amount AS REAL)) FROM expenses WHERE expense_date >= ?", (month_start,)).fetchone()[0])

    # 银行账户余额
    bank_balances = [dict(b) for b in conn.execute(
        "SELECT bank_type, CAST(balance AS REAL) as bal FROM bank_accounts ORDER BY bank_type").fetchall()]
    total_bank = sum(b["bal"] for b in bank_balances)

    # 未审核/未记账凭证数
    draft_vouchers = conn.execute("SELECT COUNT(*) FROM accounting_vouchers WHERE status='草稿'").fetchone()[0] or 0
    pending_review = conn.execute("SELECT COUNT(*) FROM accounting_vouchers WHERE status='已审核'").fetchone()[0] or 0

    # 月度统计（最近12个月用于图表）
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

    # 图表数据（按时间正序）
    chart_months = [m["month"] for m in monthly_stats][::-1]
    chart_income = [m["income"] for m in monthly_stats][::-1]
    chart_expense = [m["expense"] for m in monthly_stats][::-1]

    # 客户排名
    top_customers = conn.execute("""
        SELECT c.name, COUNT(o.id) as order_count, COALESCE(SUM(CAST(o.total_amount AS REAL)), 0) as total
        FROM customers c LEFT JOIN processing_orders o ON c.id = o.customer_id
        GROUP BY c.id ORDER BY total DESC LIMIT 10
    """).fetchall()

    # 收入按客户分类
    income_by_customer = conn.execute("""
        SELECT customer_name, SUM(CAST(amount AS REAL)) as total
        FROM incomes GROUP BY customer_name ORDER BY total DESC LIMIT 8
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

    # 订单状态分布
    order_status = [dict(r) for r in conn.execute("""
        SELECT status, COUNT(*) as cnt FROM processing_orders GROUP BY status ORDER BY cnt DESC
    """).fetchall()]

    # 最近订单
    recent_orders = [dict(r) for r in conn.execute("""
        SELECT order_no, customer_name, CAST(total_amount AS REAL) as total_amount, status, order_date
        FROM processing_orders ORDER BY order_date DESC LIMIT 5
    """).fetchall()]

    conn.close()

    import json
    return render_template("reports.html",
                           total_income=total_income, total_expense=total_expense,
                           total_bank=total_bank, order_count=order_count,
                           month_income=month_income, month_expense=month_expense,
                           monthly_stats=monthly_stats,
                           chart_data=json.dumps({"months": chart_months, "income": chart_income, "expense": chart_expense}),
                           top_customers=top_customers, income_by_customer=income_by_customer,
                           expense_by_type=expense_by_type, voucher_stats=voucher_stats,
                           draft_vouchers=draft_vouchers, pending_review=pending_review,
                           order_status=order_status, recent_orders=recent_orders,
                           bank_balances=bank_balances)


# ========== 银行对账 ==========

@finance_bp.route("/bank-reconciliation", methods=["GET", "POST"])
def bank_reconciliation():
    """银行对账页面"""
    conn = get_db()
    # Ensure table exists
    conn.execute("""
        CREATE TABLE IF NOT EXISTS bank_reconciliations (
            id TEXT PRIMARY KEY, bank_type TEXT NOT NULL, period TEXT NOT NULL,
            book_item_type TEXT NOT NULL, book_item_id TEXT NOT NULL,
            bank_item_id TEXT, amount REAL NOT NULL,
            reconciled_at TEXT NOT NULL, reconciled_by TEXT DEFAULT '', notes TEXT
        )
    """)
    conn.commit()

    bank_type = request.args.get("bank_type", "N银行")
    period = request.args.get("period", date.today().strftime("%Y-%m"))
    message = None
    error = None

    if request.method == "POST":
        action = request.form.get("action", "")
        now = datetime.now().isoformat()
        operator = request.form.get("operator", "管理员")

        try:
            if action == "import_bank_stmt":
                # Import bank statement items (or auto-generate from incomes/expenses)
                items_added = 0
                incomes = conn.execute(
                    "SELECT id, customer_name, CAST(amount AS REAL) amount, bank_type, income_date "
                    "FROM incomes WHERE bank_type=? AND income_date LIKE ?",
                    (bank_type, period + "%")).fetchall()
                expenses = conn.execute(
                    "SELECT id, expense_type, supplier_name, CAST(amount AS REAL) amount, bank_type, expense_date "
                    "FROM expenses WHERE bank_type=? AND expense_date LIKE ?",
                    (bank_type, period + "%")).fetchall()

                for inc in incomes:
                    exist = conn.execute(
                        "SELECT COUNT(*) FROM bank_transactions WHERE matched_income_id=?",
                        (inc[0],)).fetchone()[0]
                    if exist == 0:
                        conn.execute("""
                            INSERT INTO bank_transactions (id, bank_type, transaction_date, amount,
                                counterparty, description, matched, matched_income_id, created_at)
                            VALUES (?,?,?,?,?,?,0,?,?)
                        """, (str(uuid.uuid4()), bank_type, inc[4], f"{inc[2]:.2f}",
                              inc[1], f"收入-{inc[1]}", inc[0], now))
                        items_added += 1

                for exp in expenses:
                    exist = conn.execute(
                        "SELECT COUNT(*) FROM bank_transactions WHERE matched_expense_id=?",
                        (exp[0],)).fetchone()[0]
                    if exist == 0:
                        conn.execute("""
                            INSERT INTO bank_transactions (id, bank_type, transaction_date, amount,
                                counterparty, description, matched, matched_expense_id, created_at)
                            VALUES (?,?,?,?,?,?,0,?,?)
                        """, (str(uuid.uuid4()), bank_type, exp[4], f"{exp[2]:.2f}",
                              exp[2] or "供应商", f"支出-{exp[1]}", exp[0], now))
                        items_added += 1

                conn.commit()
                message = f"已导入 {items_added} 条银行对账单项目"

            elif action == "reconcile":
                # Manual reconciliation
                book_ids = request.form.getlist("book_id[]")
                book_types = request.form.getlist("book_type[]")
                bank_ids = request.form.getlist("bank_id[]")
                amounts = request.form.getlist("amount[]")

                reconciled = 0
                for i in range(len(book_ids)):
                    if i < len(bank_ids) and bank_ids[i]:
                        rid = str(uuid.uuid4())
                        conn.execute("""
                            INSERT INTO bank_reconciliations
                            (id, bank_type, period, book_item_type, book_item_id,
                             bank_item_id, amount, reconciled_at, reconciled_by)
                            VALUES (?,?,?,?,?,?,?,?,?)
                        """, (rid, bank_type, period, book_types[i], book_ids[i],
                              bank_ids[i], amounts[i], now, operator))

                        # Mark bank transaction as matched
                        conn.execute(
                            "UPDATE bank_transactions SET matched=1 WHERE id=?",
                            (bank_ids[i],))

                        # If income, set matched_income_id; if expense, set matched_expense_id
                        if book_types[i] == "income":
                            conn.execute(
                                "UPDATE bank_transactions SET matched_income_id=? WHERE id=?",
                                (book_ids[i], bank_ids[i]))
                        elif book_types[i] == "expense":
                            conn.execute(
                                "UPDATE bank_transactions SET matched_expense_id=? WHERE id=?",
                                (book_ids[i], bank_ids[i]))

                        reconciled += 1

                conn.commit()
                message = f"已对账 {reconciled} 笔"

            elif action == "auto_match":
                # Auto-match by exact amount + same date
                matched = 0
                bank_items = conn.execute(
                    "SELECT * FROM bank_transactions WHERE bank_type=? AND matched=0",
                    (bank_type,)).fetchall()
                incomes = conn.execute(
                    "SELECT * FROM incomes WHERE bank_type=? AND income_date LIKE ?",
                    (bank_type, period + "%")).fetchall()
                expenses = conn.execute(
                    "SELECT * FROM expenses WHERE bank_type=? AND expense_date LIKE ?",
                    (bank_type, period + "%")).fetchall()

                for bt in bank_items:
                    bank_amt = round(float(bt[3]), 2)
                    bank_date = bt[2]
                    bank_counter = (bt[4] or "").strip()
                    # Try match income
                    for inc in incomes:
                        if abs(round(float(inc[4]), 2) - bank_amt) < 0.01 and inc[5] == bank_date:
                            if inc[2] == bank_counter or True:
                                rid = str(uuid.uuid4())
                                conn.execute("""
                                    INSERT INTO bank_reconciliations VALUES (?,?,?,?,?,?,?,?,?,?)
                                """, (rid, bank_type, period, "income", inc[0], bt[0],
                                      bank_amt, now, operator, ""))
                                conn.execute(
                                    "UPDATE bank_transactions SET matched=1, matched_income_id=? WHERE id=?",
                                    (inc[0], bt[0]))
                                matched += 1
                                break
                    # Try match expense
                    if not conn.execute("SELECT matched FROM bank_transactions WHERE id=?",
                                       (bt[0],)).fetchone()[0]:
                        for exp in expenses:
                            if abs(round(float(exp[4]), 2) - bank_amt) < 0.01 and exp[6] == bank_date:
                                rid = str(uuid.uuid4())
                                conn.execute("""
                                    INSERT INTO bank_reconciliations VALUES (?,?,?,?,?,?,?,?,?,?)
                                """, (rid, bank_type, period, "expense", exp[0], bt[0],
                                      bank_amt, now, operator, ""))
                                conn.execute(
                                    "UPDATE bank_transactions SET matched=1, matched_expense_id=? WHERE id=?",
                                    (exp[0], bt[0]))
                                matched += 1
                                break

                conn.commit()
                message = f"自动匹配了 {matched} 笔"

        except Exception as e:
            error = f"操作失败: {e}"

    # Get bank statement items
    bank_stmt = [dict(b) for b in conn.execute(
        "SELECT * FROM bank_transactions WHERE bank_type=? ORDER BY transaction_date",
        (bank_type,)).fetchall()]

    # Get book items (incomes + expenses) not yet reconciled
    reconciled_book_ids = set()
    for r in conn.execute(
        "SELECT book_item_id FROM bank_reconciliations WHERE bank_type=? AND period=?",
        (bank_type, period)).fetchall():
        reconciled_book_ids.add(r[0])

    book_income = [dict(inc) for inc in conn.execute(
        "SELECT id, customer_name as name, CAST(amount AS REAL) amount, bank_type, income_date as date "
        "FROM incomes WHERE bank_type=? AND income_date LIKE ? ORDER BY income_date",
        (bank_type, period + "%")).fetchall()
        if inc["id"] not in reconciled_book_ids]

    book_expense = [dict(exp) for exp in conn.execute(
        "SELECT id, supplier_name as name, expense_type, CAST(amount AS REAL) amount, bank_type, expense_date as date "
        "FROM expenses WHERE bank_type=? AND expense_date LIKE ? ORDER BY expense_date",
        (bank_type, period + "%")).fetchall()
        if exp["id"] not in reconciled_book_ids]

    # Reconciled items for display
    recon_items = [dict(r) for r in conn.execute(
        "SELECT * FROM bank_reconciliations WHERE bank_type=? AND period=? ORDER BY reconciled_at",
        (bank_type, period)).fetchall()]

    # Reconciliation summary
    bank_stmt_total = sum(float(b["amount"]) for b in bank_stmt if not b["matched"])
    book_income_total = sum(i["amount"] for i in book_income)
    book_expense_total = sum(e["amount"] for e in book_expense)
    recon_total = sum(f["amount"] for f in recon_items)

    # Available bank types
    bank_types = [dict(r) for r in conn.execute(
        "SELECT DISTINCT bank_type FROM bank_accounts UNION "
        "SELECT DISTINCT bank_type FROM incomes UNION "
        "SELECT DISTINCT bank_type FROM expenses").fetchall()]

    conn.close()
    return render_template("bank_reconciliation.html",
        bank_type=bank_type, period=period, bank_types=bank_types,
        bank_stmt=bank_stmt, book_income=book_income, book_expense=book_expense,
        recon_items=recon_items, message=message, error=error,
        bank_stmt_total=bank_stmt_total,
        book_income_total=book_income_total,
        book_expense_total=book_expense_total,
        recon_total=recon_total)