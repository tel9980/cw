#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""会计路由：科目管理、凭证管理、账簿查询"""

import uuid
from datetime import date, datetime
from flask import Blueprint, render_template, request, redirect

from routes.helpers import get_db, to_float

accounting_bp = Blueprint('accounting', __name__)


# ========== 会计科目管理 ==========

@accounting_bp.route("/chart-of-accounts", methods=["GET", "POST"])
def chart_of_accounts():
    """会计科目管理页面"""
    conn = get_db()
    message = None
    error = None

    if request.method == "POST":
        code = request.form.get("code", "").strip()
        name = request.form.get("name", "").strip()
        account_type = request.form.get("account_type", "资产类")
        balance_direction = request.form.get("balance_direction", "借")
        aux_customer = request.form.get("aux_customer") == "1"
        aux_supplier = request.form.get("aux_supplier") == "1"
        aux_department = request.form.get("aux_department") == "1"
        aux_project = request.form.get("aux_project") == "1"
        aux_employee = request.form.get("aux_employee") == "1"
        notes = request.form.get("notes", "")

        if not code or not name:
            error = "科目编码和名称不能为空"
        else:
            try:
                from business.account_manager import AccountManager
                am = AccountManager(conn=conn)
                success, msg, _ = am.create_account(
                    code=code, name=name, account_type=account_type,
                    balance_direction=balance_direction,
                    aux_customer=aux_customer, aux_supplier=aux_supplier,
                    aux_department=aux_department, aux_project=aux_project,
                    aux_employee=aux_employee, notes=notes
                )
                if success:
                    message = msg
                else:
                    error = msg
            except Exception as e:
                error = f"保存失败: {e}"

    accounts = [dict(a) for a in conn.execute(
        "SELECT * FROM chart_of_accounts ORDER BY code"
    ).fetchall()]

    stats = {"total_accounts": len(accounts), "by_type": {}, "controlled_accounts": 0}
    for acc in accounts:
        t = acc["account_type"]
        stats["by_type"][t] = stats["by_type"].get(t, 0) + 1
        if acc.get("is_controlled"):
            stats["controlled_accounts"] += 1

    departments = [dict(d) for d in conn.execute(
        "SELECT * FROM departments ORDER BY code").fetchall()]
    projects = [dict(p) for p in conn.execute(
        "SELECT * FROM projects ORDER BY code").fetchall()]

    conn.close()

    return render_template(
        "chart_of_accounts.html",
        accounts=accounts, stats=stats,
        departments=departments, projects=projects,
        department_count=len(departments), project_count=len(projects),
        message=message, error=error,
    )


@accounting_bp.route("/chart-of-accounts/delete", methods=["POST"])
def delete_account_route():
    """删除会计科目"""
    account_id = request.form.get("account_id", "")
    conn = get_db()
    try:
        from business.account_manager import AccountManager
        am = AccountManager(conn=conn)
        success, msg = am.delete_account(account_id)
        if success:
            conn.commit()
    except Exception as e:
        pass
    conn.close()
    return redirect("/chart-of-accounts")


@accounting_bp.route("/chart-of-accounts/department", methods=["POST"])
def add_department():
    """新增部门"""
    code = request.form.get("code", "").strip()
    name = request.form.get("name", "").strip()
    manager = request.form.get("manager", "")
    notes = request.form.get("notes", "")
    conn = get_db()
    try:
        from business.account_manager import AccountManager
        am = AccountManager(conn=conn)
        success, msg, _ = am.create_department(code=code, name=name, manager=manager, notes=notes)
        if success:
            conn.commit()
    except Exception:
        pass
    conn.close()
    return redirect("/chart-of-accounts")


@accounting_bp.route("/chart-of-accounts/project", methods=["POST"])
def add_project():
    """新增项目"""
    code = request.form.get("code", "").strip()
    name = request.form.get("name", "").strip()
    status = request.form.get("status", "进行中")
    manager = request.form.get("manager", "")
    budget = float(request.form.get("budget", "0") or 0)
    notes = request.form.get("notes", "")
    conn = get_db()
    try:
        from business.account_manager import AccountManager
        am = AccountManager(conn=conn)
        success, msg, _ = am.create_project(
            code=code, name=name, status=status, manager=manager, budget=budget, notes=notes)
        if success:
            conn.commit()
    except Exception:
        pass
    conn.close()
    return redirect("/chart-of-accounts")


# ========== 会计凭证管理 ==========

@accounting_bp.route("/vouchers", methods=["GET", "POST"])
def vouchers_page():
    """会计凭证管理页面"""
    conn = get_db()
    message = None
    error = None

    if request.method == "POST":
        voucher_id = request.form.get("voucher_id")
        action = request.form.get("action", "")
        operator = request.form.get("operator", "管理员")
        now = datetime.now().isoformat()

        if action == "review" and voucher_id:
            conn.execute(
                "UPDATE accounting_vouchers SET status='已审核', reviewed_by=?, reviewed_at=? WHERE id=?",
                (operator, now, voucher_id))
            conn.commit()
            message = "凭证审核成功"
        elif action == "post" and voucher_id:
            conn.execute(
                "UPDATE accounting_vouchers SET status='已记账', posted_by=?, posted_at=? WHERE id=?",
                (operator, now, voucher_id))
            conn.commit()
            message = "凭证记账成功"
        elif action == "create":
            try:
                voucher_date = request.form.get("voucher_date", date.today().isoformat())
                accounting_period = request.form.get("accounting_period", voucher_date[:7])
                summary = request.form.get("summary", "")
                created_by = request.form.get("created_by", "系统")
                accounts = request.form.getlist("line_account[]")
                debits = request.form.getlist("line_debit[]")
                credits = request.form.getlist("line_credit[]")

                total_debit = sum(float(d or 0) for d in debits)
                total_credit = sum(float(c or 0) for c in credits)

                if abs(total_debit - total_credit) > 0.001:
                    error = f"借贷不平衡：借方 {total_debit:.2f} != 贷方 {total_credit:.2f}"
                elif not accounts:
                    error = "至少需要一条分录"
                else:
                    cursor = conn.cursor()
                    cursor.execute(
                        "SELECT COUNT(*) FROM accounting_vouchers WHERE accounting_period=?",
                        (accounting_period,))
                    seq = cursor.fetchone()[0] + 1
                    voucher_no = f"{accounting_period}-{seq:03d}"
                    vid = str(uuid.uuid4())

                    cursor.execute(
                        """INSERT INTO accounting_vouchers
                           (id, voucher_no, voucher_date, accounting_period, summary,
                            total_debit, total_credit, created_by, status, created_at, updated_at)
                           VALUES (?, ?, ?, ?, ?, ?, ?, ?, '草稿', ?, ?)""",
                        (vid, voucher_no, voucher_date, accounting_period, summary,
                         f"{total_debit:.2f}", f"{total_credit:.2f}", created_by, now, now))

                    for i in range(len(accounts)):
                        account_code = accounts[i]
                        debit = float(debits[i] or 0)
                        credit = float(credits[i] or 0)
                        if debit > 0 or credit > 0:
                            acc = conn.execute(
                                "SELECT name FROM chart_of_accounts WHERE code=?", (account_code,)
                            ).fetchone()
                            acc_name = acc["name"] if acc else account_code
                            cursor.execute(
                                """INSERT INTO voucher_lines
                                   (id, voucher_id, account_code, account_name, debit, credit, summary)
                                   VALUES (?, ?, ?, ?, ?, ?, ?)""",
                                (str(uuid.uuid4()), vid, account_code, acc_name,
                                 f"{debit:.2f}", f"{credit:.2f}", summary))
                    conn.commit()
                    message = f"凭证 {voucher_no} 创建成功"
            except Exception as e:
                error = f"创建凭证失败: {e}"

    vouchers = [dict(v) for v in conn.execute("""
        SELECT v.*, (SELECT COUNT(*) FROM voucher_lines WHERE voucher_id=v.id) as line_count
        FROM accounting_vouchers v ORDER BY v.voucher_date DESC, v.voucher_no DESC LIMIT 100
    """).fetchall()]

    accounts_list = [dict(a) for a in conn.execute(
        "SELECT code, name, account_type FROM chart_of_accounts WHERE is_active=1 ORDER BY code"
    ).fetchall()]

    stats = {
        "total": len(vouchers),
        "draft": sum(1 for v in vouchers if v.get("status") == "草稿"),
        "reviewed": sum(1 for v in vouchers if v.get("status") == "已审核"),
        "posted": sum(1 for v in vouchers if v.get("status") == "已记账"),
    }
    periods = [dict(p) for p in conn.execute(
        "SELECT DISTINCT accounting_period FROM accounting_vouchers ORDER BY accounting_period DESC"
    ).fetchall()]

    conn.close()
    return render_template("vouchers.html", vouchers=vouchers, accounts_list=accounts_list,
                           stats=stats, periods=periods, message=message, error=error,
                           today=date.today().isoformat())


@accounting_bp.route("/vouchers/<voucher_id>")
def voucher_detail(voucher_id):
    """凭证详情页"""
    conn = get_db()
    voucher = conn.execute("SELECT * FROM accounting_vouchers WHERE id=?", (voucher_id,)).fetchone()
    if not voucher:
        return render_template("error.html", error="凭证不存在")
    voucher = dict(voucher)
    lines = [dict(l) for l in conn.execute(
        "SELECT * FROM voucher_lines WHERE voucher_id=? ORDER BY id", (voucher_id,)).fetchall()]
    conn.close()
    return render_template("voucher_detail.html", voucher=voucher, lines=lines)


# ========== 会计账簿查询 ==========

@accounting_bp.route("/accounting-books")
def accounting_books():
    """会计账簿查询页面（余额表/明细账/财务报表/期间管理）"""
    conn = get_db()
    period = request.args.get("period", "")
    account_code = request.args.get("account_code", "")
    book_type = request.args.get("type", "balance")

    periods = [dict(p) for p in conn.execute(
        "SELECT DISTINCT accounting_period FROM accounting_vouchers ORDER BY accounting_period DESC"
    ).fetchall()]

    accounts_list = [dict(a) for a in conn.execute(
        "SELECT code, name, account_type, balance_direction FROM chart_of_accounts WHERE is_active=1 ORDER BY code"
    ).fetchall()]

    # 会计期间管理数据
    period_records = [dict(p) for p in conn.execute(
        "SELECT * FROM accounting_periods ORDER BY period_name DESC"
    ).fetchall()]

    if not period and periods:
        period = periods[0]["accounting_period"]

    balance_data = []
    detail_data = []
    acc_info = None
    statement_data = {}

    if period and book_type == "balance":
        rows = conn.execute("""
            SELECT a.code, a.name, a.account_type, a.balance_direction,
                COALESCE(SUM(CASE WHEN v.status='已记账' AND CAST(l.debit AS REAL) > 0
                    THEN CAST(l.debit AS REAL) ELSE 0 END), 0) as debit_sum,
                COALESCE(SUM(CASE WHEN v.status='已记账' AND CAST(l.credit AS REAL) > 0
                    THEN CAST(l.credit AS REAL) ELSE 0 END), 0) as credit_sum
            FROM chart_of_accounts a
            LEFT JOIN voucher_lines l ON l.account_code = a.code
            LEFT JOIN accounting_vouchers v ON v.id = l.voucher_id AND v.accounting_period = ?
            WHERE a.is_active = 1
            GROUP BY a.code, a.name, a.account_type, a.balance_direction
            ORDER BY a.code
        """, (period,)).fetchall()

        balance_data = []
        for r in rows:
            r = dict(r)
            direction = r["balance_direction"] or "借"
            closing = (r["debit_sum"] - r["credit_sum"]) if direction == "借" else (r["credit_sum"] - r["debit_sum"])
            r["closing_balance"] = closing
            balance_data.append(r)

    elif period and account_code and book_type == "detail":
        detail_rows = conn.execute("""
            SELECT v.voucher_no, v.voucher_date, v.summary,
                l.account_code, l.account_name,
                CAST(l.debit AS REAL) as debit, CAST(l.credit AS REAL) as credit, v.status
            FROM voucher_lines l
            JOIN accounting_vouchers v ON v.id = l.voucher_id
            WHERE l.account_code = ? AND v.accounting_period = ?
            ORDER BY v.voucher_date, v.voucher_no
        """, (account_code, period)).fetchall()
        detail_data = [dict(d) for d in detail_rows]
        acc_info_row = conn.execute(
            "SELECT code, name, account_type, balance_direction FROM chart_of_accounts WHERE code=?",
            (account_code,)).fetchone()
        acc_info = dict(acc_info_row) if acc_info_row else None

    elif book_type == "statement" and period:
        # 计算科目余额用于财务报表
        rows = conn.execute("""
            SELECT a.code, a.name, a.account_type, a.balance_direction,
                COALESCE(SUM(CASE WHEN v.status='已记账' AND CAST(l.debit AS REAL) > 0
                    THEN CAST(l.debit AS REAL) ELSE 0 END), 0) as debit_sum,
                COALESCE(SUM(CASE WHEN v.status='已记账' AND CAST(l.credit AS REAL) > 0
                    THEN CAST(l.credit AS REAL) ELSE 0 END), 0) as credit_sum
            FROM chart_of_accounts a
            LEFT JOIN voucher_lines l ON l.account_code = a.code
            LEFT JOIN accounting_vouchers v ON v.id = l.voucher_id AND v.accounting_period = ?
            WHERE a.is_active = 1
            GROUP BY a.code, a.name, a.account_type, a.balance_direction
            ORDER BY a.code
        """, (period,)).fetchall()

        # 资产负债表
        bs_assets = []
        bs_liabilities = []
        bs_equity = []
        total_assets = 0.0
        total_liabilities = 0.0
        total_equity = 0.0

        # 利润表
        is_revenue = []
        is_costs = []
        total_revenue = 0.0
        total_costs = 0.0

        for r in rows:
            r = dict(r)
            direction = r["balance_direction"] or "借"
            if direction == "借":
                balance = r["debit_sum"] - r["credit_sum"]
            else:
                balance = r["credit_sum"] - r["debit_sum"]

            entry = {"code": r["code"], "name": r["name"], "balance": balance}

            if r["account_type"] == "资产类":
                bs_assets.append(entry)
                total_assets += balance
            elif r["account_type"] == "负债类":
                bs_liabilities.append(entry)
                total_liabilities += balance
            elif r["account_type"] == "权益类":
                bs_equity.append(entry)
                total_equity += balance
            elif r["account_type"] == "成本类":
                is_costs.append(entry)
                total_costs += r["debit_sum"]
            elif r["account_type"] == "损益类":
                if r["code"].startswith("5"):  # 收入类
                    is_revenue.append(entry)
                    total_revenue += r["credit_sum"]
                else:  # 费用类
                    is_costs.append(entry)
                    total_costs += r["debit_sum"]

        statement_data = {
            "bs": {"assets": bs_assets, "liabilities": bs_liabilities, "equity": bs_equity,
                   "total_assets": total_assets, "total_liabilities": total_liabilities,
                   "total_equity": total_equity, "balanced": abs(total_assets - total_liabilities - total_equity) < 0.01},
            "is": {"revenue": is_revenue, "costs": is_costs,
                   "total_revenue": total_revenue, "total_costs": total_costs,
                   "net_profit": total_revenue - total_costs},
        }

    conn.close()

    return render_template("accounting_books.html",
                           periods=periods, current_period=period,
                           accounts_list=accounts_list, current_account=account_code,
                           book_type=book_type, balance_data=balance_data,
                           detail_data=detail_data, acc_info=acc_info,
                           period_records=period_records, statement_data=statement_data)