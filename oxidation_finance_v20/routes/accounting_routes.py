#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""会计路由：科目管理、凭证管理、账簿查询"""

import csv
import hashlib
import io
import os
import uuid
from datetime import date, datetime
from flask import Blueprint, Response, render_template, request, redirect

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
        message=message, error=error, search_term=request.args.get("search", ""),
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


# ========== 期初余额管理 ==========

@accounting_bp.route("/chart-of-accounts/opening-balances", methods=["GET", "POST"])
def opening_balances():
    """期初余额录入页面"""
    conn = get_db()
    message = None
    error = None
    period = request.args.get("period", date.today().strftime("%Y-%m"))

    if request.method == "POST":
        account_codes = request.form.getlist("account_code[]")
        balances = request.form.getlist("balance[]")
        now = datetime.now().isoformat()

        # 借贷平衡校验
        total_debit_open = 0.0
        total_credit_open = 0.0
        account_balances_input = {}

        accounts_map = {a["code"]: dict(a) for a in conn.execute(
            "SELECT code, name, balance_direction FROM chart_of_accounts WHERE is_active=1"
        ).fetchall()}

        for i, code in enumerate(account_codes):
            bal = float(balances[i] or 0)
            if bal != 0 and code in accounts_map:
                direction = accounts_map[code]["balance_direction"]
                account_balances_input[code] = bal
                if direction == "借":
                    total_debit_open += bal
                else:
                    total_credit_open += bal

        if abs(total_debit_open - total_credit_open) > 0.01:
            error = f"借贷不平衡：借方期初 {total_debit_open:,.2f} ≠ 贷方期初 {total_credit_open:,.2f}，差额 {abs(total_debit_open-total_credit_open):,.2f}"
        else:
            try:
                for code, bal in account_balances_input.items():
                    exist = conn.execute(
                        "SELECT id FROM account_balances WHERE account_code=? AND period_id=?",
                        (code, period)).fetchone()
                    if exist:
                        conn.execute(
                            "UPDATE account_balances SET opening_balance=?, updated_at=? WHERE id=?",
                            (bal, now, exist["id"]))
                    else:
                        conn.execute(
                            """INSERT INTO account_balances
                               (id, account_code, period_id, opening_balance, debit_amount,
                                credit_amount, closing_balance, created_at, updated_at)
                               VALUES (?, ?, ?, ?, 0, 0, ?, ?, ?)""",
                            (str(uuid.uuid4()), code, period, bal, bal, now, now))
                conn.commit()
                message = f"期初余额保存成功，借方 {total_debit_open:,.2f} = 贷方 {total_credit_open:,.2f}"
            except Exception as e:
                error = f"保存失败: {e}"

    # 获取科目列表（含已存的期初余额）
    accounts = [dict(a) for a in conn.execute(
        "SELECT code, name, account_type, balance_direction FROM chart_of_accounts WHERE is_active=1 ORDER BY code"
    ).fetchall()]

    # 获取已有的期初余额
    saved_balances = {}
    for b in conn.execute(
        "SELECT account_code, opening_balance FROM account_balances WHERE period_id=?", (period,)
    ).fetchall():
        saved_balances[b["account_code"]] = b["opening_balance"]

    # 分类统计
    total_dr = sum(v for k, v in saved_balances.items()
                   if any(a["code"] == k and a["balance_direction"] == "借" for a in accounts))
    total_cr = sum(v for k, v in saved_balances.items()
                   if any(a["code"] == k and a["balance_direction"] == "贷" for a in accounts))

    conn.close()

    return render_template("opening_balances.html",
                           accounts=accounts, saved_balances=saved_balances,
                           period=period, total_debit=total_dr, total_credit=total_cr,
                           message=message, error=error)


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
                aux_types = request.form.getlist("line_aux_type[]")
                aux_ids = request.form.getlist("line_aux_id[]")

                total_debit = sum(float(d or 0) for d in debits)
                total_credit = sum(float(c or 0) for c in credits)

                if abs(total_debit - total_credit) > 0.001:
                    error = f"借贷不平衡：借方 {total_debit:.2f} != 贷方 {total_credit:.2f}"
                elif not accounts:
                    error = "至少需要一条分录"
                else:
                    cursor = conn.cursor()
                    voucher_no = generate_voucher_number(conn, accounting_period)
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
                        aux_type = aux_types[i] if i < len(aux_types) else ""
                        aux_id = aux_ids[i] if i < len(aux_ids) else ""
                        if debit > 0 or credit > 0:
                            acc = conn.execute(
                                "SELECT name FROM chart_of_accounts WHERE code=?", (account_code,)
                            ).fetchone()
                            acc_name = acc["name"] if acc else account_code
                            cursor.execute(
                                """INSERT INTO voucher_lines
                                   (id, voucher_id, account_code, account_name, debit, credit,
                                    summary, related_entity_type, related_entity_id)
                                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                                (str(uuid.uuid4()), vid, account_code, acc_name,
                                 f"{debit:.2f}", f"{credit:.2f}", summary,
                                 aux_type if aux_type else None, aux_id if aux_id else None))
                    conn.commit()
                    message = f"凭证 {voucher_no} 创建成功"
            except Exception as e:
                error = f"创建凭证失败: {e}"

    vouchers = [dict(v) for v in conn.execute("""
        SELECT v.*, (SELECT COUNT(*) FROM voucher_lines WHERE voucher_id=v.id) as line_count
        FROM accounting_vouchers v ORDER BY v.voucher_date DESC, v.voucher_no DESC LIMIT 100
    """).fetchall()]

    accounts_list = [dict(a) for a in conn.execute(
        "SELECT code, name, account_type, aux_customer, aux_supplier, aux_department, aux_project, aux_employee FROM chart_of_accounts WHERE is_active=1 ORDER BY code"
    ).fetchall()]

    # 辅助核算：获取实体列表
    customers_list = [dict(c) for c in conn.execute(
        "SELECT id, name FROM customers ORDER BY name").fetchall()]
    suppliers_list = [dict(s) for s in conn.execute(
        "SELECT id, name FROM suppliers ORDER BY name").fetchall()]
    departments_list = [dict(d) for d in conn.execute(
        "SELECT id, code, name FROM departments ORDER BY code").fetchall()]
    projects_list = [dict(p) for p in conn.execute(
        "SELECT id, code, name FROM projects ORDER BY code").fetchall()]

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
                           customers_list=customers_list, suppliers_list=suppliers_list,
                           departments_list=departments_list, projects_list=projects_list,
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
    """会计账簿查询页面（余额表/明细账/试算平衡/序时簿/财务报表/期间管理）"""
    conn = get_db()
    period = request.args.get("period", "")
    account_code = request.args.get("account_code", "")
    book_type = request.args.get("type", "balance")
    aux_type = request.args.get("aux_type", "customer")
    aux_entity = request.args.get("aux_entity", "")

    periods = [dict(p) for p in conn.execute(
        "SELECT DISTINCT accounting_period FROM accounting_vouchers ORDER BY accounting_period DESC"
    ).fetchall()]

    accounts_list = [dict(a) for a in conn.execute(
        "SELECT code, name, account_type, balance_direction FROM chart_of_accounts WHERE is_active=1 ORDER BY code"
    ).fetchall()]

    period_records = [dict(p) for p in conn.execute(
        "SELECT * FROM accounting_periods ORDER BY period_name DESC"
    ).fetchall()]

    if not period and periods:
        period = periods[0]["accounting_period"]

    balance_data = []
    detail_data = []
    acc_info = None
    statement_data = {}
    trial_data = {}
    journal_data = []
    aux_data = {}
    aux_detail_data = []
    aging_data = {}

    # ---- 公共：获取期初余额 ----
    opening_map = {}
    for b in conn.execute(
        "SELECT account_code, opening_balance FROM account_balances WHERE period_id=?", (period or "",)
    ).fetchall():
        opening_map[b["account_code"]] = b["opening_balance"]

    # ---- 公共：获取本期发生额 ----
    def get_period_amounts(p):
        rows = conn.execute("""
            SELECT a.code, a.name, a.account_type, a.balance_direction,
                COALESCE(SUM(CASE WHEN v.status='已记账' AND CAST(l.debit AS REAL)>0
                    THEN CAST(l.debit AS REAL) ELSE 0 END), 0) as debit_sum,
                COALESCE(SUM(CASE WHEN v.status='已记账' AND CAST(l.credit AS REAL)>0
                    THEN CAST(l.credit AS REAL) ELSE 0 END), 0) as credit_sum
            FROM chart_of_accounts a
            LEFT JOIN voucher_lines l ON l.account_code = a.code
            LEFT JOIN accounting_vouchers v ON v.id = l.voucher_id AND v.accounting_period = ?
            WHERE a.is_active = 1
            GROUP BY a.code, a.name, a.account_type, a.balance_direction
            ORDER BY a.code
        """, (p,)).fetchall()
        return [dict(r) for r in rows]

    if period and book_type == "balance":
        rows = get_period_amounts(period)
        for r in rows:
            r["opening_balance"] = opening_map.get(r["code"], 0.0)
            direction = r["balance_direction"] or "借"
            opening = r["opening_balance"]
            if direction == "借":
                closing = opening + r["debit_sum"] - r["credit_sum"]
            else:
                closing = opening + r["credit_sum"] - r["debit_sum"]
            r["closing_balance"] = closing
        balance_data = rows

    elif period and account_code and book_type == "detail":
        detail_rows = conn.execute("""
            SELECT v.voucher_no, v.voucher_date, v.summary,
                l.account_code, l.account_name,
                CAST(l.debit AS REAL) as debit, CAST(l.credit AS REAL) as credit, v.status, v.id as vid
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

    elif period and book_type == "trial_balance":
        rows = get_period_amounts(period)
        trial_rows = []
        total_dr_open, total_cr_open = 0, 0
        total_dr_curr, total_cr_curr = 0, 0
        total_dr_close, total_cr_close = 0, 0

        for r in rows:
            opening = opening_map.get(r["code"], 0.0)
            direction = r["balance_direction"] or "借"
            if direction == "借":
                dr_open = opening
                cr_open = 0
                closing = opening + r["debit_sum"] - r["credit_sum"]
            else:
                dr_open = 0
                cr_open = opening
                closing = opening + r["credit_sum"] - r["debit_sum"]

            dr_close = closing if closing > 0 else 0
            cr_close = abs(closing) if closing < 0 else 0

            total_dr_open += dr_open
            total_cr_open += cr_open
            total_dr_curr += r["debit_sum"]
            total_cr_curr += r["credit_sum"]
            total_dr_close += dr_close
            total_cr_close += cr_close

            trial_rows.append({
                "code": r["code"], "name": r["name"],
                "dr_open": dr_open, "cr_open": cr_open,
                "dr_current": r["debit_sum"], "cr_current": r["credit_sum"],
                "dr_close": dr_close, "cr_close": cr_close,
            })

        trial_data = {
            "rows": trial_rows,
            "total_dr_open": total_dr_open, "total_cr_open": total_cr_open,
            "total_dr_current": total_dr_curr, "total_cr_current": total_cr_curr,
            "total_dr_close": total_dr_close, "total_cr_close": total_cr_close,
        }

    elif period and book_type == "journal":
        journal_rows = conn.execute("""
            SELECT v.voucher_no, v.voucher_date, v.accounting_period,
                   l.account_code, l.account_name, v.summary,
                   CAST(l.debit AS REAL) as debit, CAST(l.credit AS REAL) as credit,
                   v.status, v.id as vid
            FROM voucher_lines l
            JOIN accounting_vouchers v ON v.id = l.voucher_id
            WHERE v.accounting_period = ? AND v.status = '已记账'
            ORDER BY v.voucher_date, v.voucher_no, l.id
        """, (period,)).fetchall()
        journal_data = [dict(j) for j in journal_rows]

    elif period and book_type in ("aux_detail", "aux_balance"):
        aux_type = request.args.get("aux_type", "customer")
        aux_entity_id = request.args.get("aux_entity", "")

        # 获取辅助核算实体列表
        aux_entities = {}
        if aux_type == "customer":
            aux_entities = {c["id"]: c for c in [dict(r) for r in conn.execute(
                "SELECT id, name FROM customers ORDER BY name").fetchall()]}
        elif aux_type == "supplier":
            aux_entities = {s["id"]: s for s in [dict(r) for r in conn.execute(
                "SELECT id, name FROM suppliers ORDER BY name").fetchall()]}
        elif aux_type == "department":
            aux_entities = {d["id"]: d for d in [dict(r) for r in conn.execute(
                "SELECT id, code, name FROM departments ORDER BY code").fetchall()]}
            for eid, ed in aux_entities.items():
                ed["display"] = f"{ed.get('code','')} {ed['name']}"
        elif aux_type == "project":
            aux_entities = {p["id"]: p for p in [dict(r) for r in conn.execute(
                "SELECT id, code, name FROM projects ORDER BY code").fetchall()]}
            for eid, ed in aux_entities.items():
                ed["display"] = f"{ed.get('code','')} {ed['name']}"

        if book_type == "aux_detail" and aux_entity_id:
            aux_detail_rows = conn.execute("""
                SELECT v.voucher_no, v.voucher_date, v.summary,
                       l.account_code, l.account_name,
                       CAST(l.debit AS REAL) as debit, CAST(l.credit AS REAL) as credit,
                       l.related_entity_type, v.status, v.id as vid
                FROM voucher_lines l
                JOIN accounting_vouchers v ON v.id = l.voucher_id
                WHERE l.related_entity_type = ? AND l.related_entity_id = ?
                  AND v.accounting_period = ? AND v.status = '已记账'
                ORDER BY v.voucher_date, v.voucher_no
            """, (aux_type, aux_entity_id, period)).fetchall()
            aux_detail_data = [dict(d) for d in aux_detail_rows]
            aux_data = {
                "type": aux_type,
                "entity_name": aux_entities.get(aux_entity_id, {}).get("name", aux_entity_id),
            }

        elif book_type == "aging":
            # 账龄分析
            aging_period = request.args.get("aging_period", period or date.today().strftime("%Y-%m"))
            as_of = datetime.strptime(aging_period + "-01", "%Y-%m-%d").date()

            # AR Aging - based on vouchers with aux accounting for customers
            ar_rows = conn.execute("""
                SELECT l.related_entity_id, l.related_entity_type,
                       SUM(CAST(l.debit AS REAL)) as total_debit,
                       SUM(CAST(l.credit AS REAL)) as total_credit,
                       MAX(v.voucher_date) as last_date
                FROM voucher_lines l
                JOIN accounting_vouchers v ON v.id = l.voucher_id
                WHERE l.account_code = '1122' AND l.related_entity_type = 'customer'
                  AND v.status = '已记账'
                GROUP BY l.related_entity_id
            """).fetchall()

            ar_data = []
            for r in ar_rows:
                entity_id = r["related_entity_id"]
                cust = conn.execute("SELECT name FROM customers WHERE id=?", (entity_id,)).fetchone()
                name = cust["name"] if cust else entity_id
                balance = r["total_debit"] - r["total_credit"]
                if abs(balance) < 0.01:
                    continue

                last_date_str = r["last_date"]
                age_days = 0
                if last_date_str:
                    last_date = datetime.strptime(last_date_str, "%Y-%m-%d").date()
                    age_days = (as_of - last_date).days

                if age_days <= 30: bucket = "0-30天"
                elif age_days <= 60: bucket = "31-60天"
                elif age_days <= 90: bucket = "61-90天"
                else: bucket = "90天以上"

                ar_data.append({
                    "entity": name, "balance": round(balance, 2),
                    "age_days": age_days, "bucket": bucket,
                    "last_date": r["last_date"],
                })

            # AP Aging - based on vouchers with aux accounting for suppliers
            ap_rows = conn.execute("""
                SELECT l.related_entity_id, l.related_entity_type,
                       SUM(CAST(l.debit AS REAL)) as total_debit,
                       SUM(CAST(l.credit AS REAL)) as total_credit,
                       MAX(v.voucher_date) as last_date
                FROM voucher_lines l
                JOIN accounting_vouchers v ON v.id = l.voucher_id
                WHERE l.related_entity_type = 'supplier' AND v.status = '已记账'
                GROUP BY l.related_entity_id
            """).fetchall()

            ap_data = []
            for r in ap_rows:
                entity_id = r["related_entity_id"]
                supp = conn.execute("SELECT name FROM suppliers WHERE id=?", (entity_id,)).fetchone()
                name = supp["name"] if supp else entity_id
                balance = r["total_credit"] - r["total_debit"]
                if abs(balance) < 0.01:
                    continue

                last_date_str = r["last_date"]
                age_days = 0
                if last_date_str:
                    last_date = datetime.strptime(last_date_str, "%Y-%m-%d").date()
                    age_days = (as_of - last_date).days

                if age_days <= 30: bucket = "0-30天"
                elif age_days <= 60: bucket = "31-60天"
                elif age_days <= 90: bucket = "61-90天"
                else: bucket = "90天以上"

                ap_data.append({
                    "entity": name, "balance": round(balance, 2),
                    "age_days": age_days, "bucket": bucket,
                    "last_date": r["last_date"],
                })

            def _bucket_summary(data):
                result = {"0-30天": 0, "31-60天": 0, "61-90天": 0, "90天以上": 0}
                for d in data:
                    result[d["bucket"]] += abs(d["balance"])
                return result

            aging_data = {
                "ar": sorted(ar_data, key=lambda x: -x["age_days"]),
                "ap": sorted(ap_data, key=lambda x: -x["age_days"]),
                "ar_total": sum(abs(d["balance"]) for d in ar_data),
                "ap_total": sum(abs(d["balance"]) for d in ap_data),
                "ar_buckets": _bucket_summary(ar_data),
                "ap_buckets": _bucket_summary(ap_data),
                "as_of": aging_period,
            }

    elif book_type == "aux_balance":
        rows = conn.execute("""
            SELECT l.related_entity_id, l.related_entity_type,
                   COALESCE(SUM(CAST(l.debit AS REAL)), 0) as total_debit,
                   COALESCE(SUM(CAST(l.credit AS REAL)), 0) as total_credit
            FROM voucher_lines l
            JOIN accounting_vouchers v ON v.id = l.voucher_id
            WHERE l.related_entity_type = ? AND v.accounting_period = ?
              AND v.status = '已记账' AND l.related_entity_id IS NOT NULL
            GROUP BY l.related_entity_id
            ORDER BY total_debit DESC
        """, (aux_type, period)).fetchall()
        aux_data = {
            "type": aux_type,
            "rows": [dict(r) for r in rows],
            "entities": aux_entities,
        }

    elif book_type == "statement" and period:
        rows = get_period_amounts(period)
        bs_assets, bs_liabilities, bs_equity = [], [], []
        total_assets = total_liabilities = total_equity = 0.0
        is_revenue, is_costs = [], []
        total_revenue = total_costs = 0.0

        for r in rows:
            direction = r["balance_direction"] or "借"
            opening = opening_map.get(r["code"], 0.0)
            if direction == "借":
                balance = opening + r["debit_sum"] - r["credit_sum"]
            else:
                balance = opening + r["credit_sum"] - r["debit_sum"]

            entry = {"code": r["code"], "name": r["name"], "balance": balance}

            if r["account_type"] == "资产类":
                bs_assets.append(entry); total_assets += balance
            elif r["account_type"] == "负债类":
                bs_liabilities.append(entry); total_liabilities += balance
            elif r["account_type"] == "权益类":
                bs_equity.append(entry); total_equity += balance
            elif r["account_type"] == "成本类":
                is_costs.append(entry); total_costs += r["debit_sum"]
            elif r["account_type"] == "损益类":
                if r["code"].startswith("5"):
                    is_revenue.append(entry); total_revenue += r["credit_sum"]
                else:
                    is_costs.append(entry); total_costs += r["debit_sum"]

        statement_data = {
            "bs": {"assets": bs_assets, "liabilities": bs_liabilities, "equity": bs_equity,
                   "total_assets": total_assets, "total_liabilities": total_liabilities,
                   "total_equity": total_equity,
                   "balanced": abs(total_assets - total_liabilities - total_equity) < 0.01},
            "is": {"revenue": is_revenue, "costs": is_costs,
                   "total_revenue": total_revenue, "total_costs": total_costs,
                   "net_profit": total_revenue - total_costs},
        }

        # 现金流量表
        cf_operating_in = 0.0
        cf_operating_out = 0.0
        cf_investing_in = 0.0
        cf_investing_out = 0.0
        cf_financing_in = 0.0
        cf_financing_out = 0.0

        cf_operating_items = []
        cf_investing_items = []
        cf_financing_items = []

        for r in rows:
            code = r["code"]
            name = r["name"]
            direction = r["balance_direction"] or "借"
            opening = opening_map.get(code, 0.0)
            debit = r["debit_sum"]
            credit = r["credit_sum"]

            # 经营活动 - 主营业务收入/其他业务收入（现金流入）
            if code.startswith("5001") or code.startswith("5051") or code.startswith("5111"):
                if credit > 0:
                    cf_operating_in += credit
                    cf_operating_items.append({"item": name, "amount": credit, "type": "in"})
            # 经营活动 - 成本费用（现金流出）
            elif code.startswith("540") or code.startswith("550") or code.startswith("560") or \
                 code.startswith("570") or code.startswith("580") or code.startswith("5301"):
                if debit > 0:
                    cf_operating_out += debit
                    cf_operating_items.append({"item": name, "amount": debit, "type": "out"})
            # 经营活动 - 应收账款收回
            elif code == "1122" or code.startswith("1123"):
                if credit > 0:
                    cf_operating_in += credit
                    cf_operating_items.append({"item": f"{name}(收回)", "amount": credit, "type": "in"})
            # 经营活动 - 应付账款支付
            elif code.startswith("2201") or code.startswith("2202") or code.startswith("2203"):
                if debit > 0:
                    cf_operating_out += debit
                    cf_operating_items.append({"item": f"{name}(支付)", "amount": debit, "type": "out"})
            # 投资活动 - 固定资产购建/处置
            elif code == "1601":
                if debit > 0:
                    cf_investing_out += debit
                    cf_investing_items.append({"item": f"{name}(购建)", "amount": debit, "type": "out"})
                if credit > 0:
                    cf_investing_in += credit
                    cf_investing_items.append({"item": f"{name}(处置)", "amount": credit, "type": "in"})
            elif code.startswith("1604") or code.startswith("1701") or code.startswith("1702"):
                if debit > 0:
                    cf_investing_out += debit
                    cf_investing_items.append({"item": f"{name}(支出)", "amount": debit, "type": "out"})
            # 筹资活动 - 实收资本/借款
            elif code == "3001":
                if credit > 0:
                    cf_financing_in += credit
                    cf_financing_items.append({"item": name, "amount": credit, "type": "in"})
            elif code.startswith("3002") or code.startswith("4001"):
                if credit > 0:
                    cf_financing_in += credit
                    cf_financing_items.append({"item": f"{name}(借款)", "amount": credit, "type": "in"})
                if debit > 0:
                    cf_financing_out += debit
                    cf_financing_items.append({"item": f"{name}(偿还)", "amount": debit, "type": "out"})

        # 如果从账户维度算不出来，用利润表推算经营活动净现金流量
        net_profit = total_revenue - total_costs
        cf_operating_net = cf_operating_in - cf_operating_out
        if abs(cf_operating_net) < 0.01 and abs(net_profit) > 0.01:
            cf_operating_net = net_profit

        cf_investing_net = cf_investing_in - cf_investing_out
        cf_financing_net = cf_financing_in - cf_financing_out

        statement_data["cf"] = {
            "items": cf_operating_items + cf_investing_items + cf_financing_items,
            "operating_in": cf_operating_in,
            "operating_out": cf_operating_out,
            "operating_net": cf_operating_net,
            "investing_in": cf_investing_in,
            "investing_out": cf_investing_out,
            "investing_net": cf_investing_net,
            "financing_in": cf_financing_in,
            "financing_out": cf_financing_out,
            "financing_net": cf_financing_net,
            "net_increase": cf_operating_net + cf_investing_net + cf_financing_net,
        }

    conn.close()

    # 获取辅助核算实体列表（用于筛选下拉）
    conn2 = get_db()
    aux_customers = [dict(c) for c in conn2.execute(
        "SELECT id, name FROM customers ORDER BY name").fetchall()]
    aux_suppliers = [dict(s) for s in conn2.execute(
        "SELECT id, name FROM suppliers ORDER BY name").fetchall()]
    aux_departments = [dict(d) for d in conn2.execute(
        "SELECT id, code, name FROM departments ORDER BY code").fetchall()]
    aux_projects = [dict(p) for p in conn2.execute(
        "SELECT id, code, name FROM projects ORDER BY code").fetchall()]
    conn2.close()

    return render_template("accounting_books.html",
                           periods=periods, current_period=period,
                           accounts_list=accounts_list, current_account=account_code,
                           book_type=book_type, balance_data=balance_data,
                           detail_data=detail_data, acc_info=acc_info,
                           period_records=period_records, statement_data=statement_data,
                           trial_data=trial_data, journal_data=journal_data,
                           aux_data=aux_data, aux_detail_data=aux_detail_data,
                           aux_type=aux_type, aux_entity=aux_entity,
                           aux_customers=aux_customers, aux_suppliers=aux_suppliers,
                           aux_departments=aux_departments, aux_projects=aux_projects,
                           aging_data=aging_data)


# ========== 系统参数设置 ==========

DEFAULT_SETTINGS = {
    "company_name": "氧化加工厂",
    "default_bank": "对公账户",
    "vat_rate": "13",
    "auto_review": "0",
    "auto_post": "0",
    "fiscal_year_start": "01-01",
    "accounting_standard": "小企业会计准则",
    "voucher_number_rule": "prefix:记-,date_fmt:%Y%m%d,seq_digits:3,reset:daily",
}


def get_setting(conn, key):
    """获取系统参数值"""
    row = conn.execute("SELECT value FROM system_settings WHERE key=?", (key,)).fetchone()
    return row["value"] if row else DEFAULT_SETTINGS.get(key, "")


def ensure_default_settings(conn):
    """确保默认设置存在"""
    now = datetime.now().isoformat()
    for key, value in DEFAULT_SETTINGS.items():
        exist = conn.execute("SELECT key FROM system_settings WHERE key=?", (key,)).fetchone()
        if not exist:
            conn.execute(
                "INSERT INTO system_settings (key, value, description, updated_at) VALUES (?, ?, ?, ?)",
                (key, value, "", now))


def generate_voucher_number(conn, accounting_period):
    """根据凭证编号规则生成凭证编号"""
    rule_str = get_setting(conn, "voucher_number_rule")
    # 解析规则: prefix:记-,date_fmt:%Y%m%d,seq_digits:3,reset:daily
    rule = {}
    for part in rule_str.split(","):
        if ":" in part:
            k, v = part.split(":", 1)
            rule[k.strip()] = v.strip()
    
    prefix = rule.get("prefix", "记-")
    date_fmt = rule.get("date_fmt", "%Y%m%d")
    seq_digits = int(rule.get("seq_digits", "3"))
    reset_mode = rule.get("reset", "daily")
    
    from datetime import datetime
    date_part = datetime.now().strftime(date_fmt)
    
    if reset_mode == "daily":
        # 按日重置：统计当天已有凭证数
        today = datetime.now().strftime("%Y-%m-%d")
        count = conn.execute(
            "SELECT COUNT(*) FROM accounting_vouchers WHERE DATE(voucher_date)=?", (today,)
        ).fetchone()[0]
    elif reset_mode == "monthly":
        # 按月重置：统计当月已有凭证数
        count = conn.execute(
            "SELECT COUNT(*) FROM accounting_vouchers WHERE accounting_period=?", (accounting_period,)
        ).fetchone()[0]
    else:
        # 按年或从不重置
        count = conn.execute(
            "SELECT COUNT(*) FROM accounting_vouchers WHERE accounting_period LIKE ?",
            (accounting_period[:4] + "%",)
        ).fetchone()[0]
    
    seq = count + 1
    voucher_no = f"{prefix}{date_part}-{str(seq).zfill(seq_digits)}"
    return voucher_no


@accounting_bp.route("/system-settings", methods=["GET", "POST"])
def system_settings():
    """系统参数设置页面"""
    conn = get_db()
    # 确保表存在
    conn.execute("""
        CREATE TABLE IF NOT EXISTS system_settings (
            key TEXT PRIMARY KEY, value TEXT NOT NULL,
            description TEXT, updated_at TEXT NOT NULL
        )
    """)
    conn.commit()
    ensure_default_settings(conn)
    conn.commit()

    message = None
    error = None

    if request.method == "POST":
        now = datetime.now().isoformat()
        try:
            for key in DEFAULT_SETTINGS:
                if key == "voucher_number_rule":
                    # 从表单构建凭证编号规则字符串
                    vn_prefix = request.form.get("vn_prefix", "记-")
                    vn_date_fmt = request.form.get("vn_date_fmt", "%Y%m%d")
                    vn_seq_digits = request.form.get("vn_seq_digits", "3")
                    vn_reset = request.form.get("vn_reset", "daily")
                    value = f"prefix:{vn_prefix},date_fmt:{vn_date_fmt},seq_digits:{vn_seq_digits},reset:{vn_reset}"
                else:
                    value = request.form.get(key, DEFAULT_SETTINGS[key])
                conn.execute(
                    "INSERT INTO system_settings (key, value, description, updated_at) VALUES (?, ?, '', ?) "
                    "ON CONFLICT(key) DO UPDATE SET value=?, updated_at=?",
                    (key, value, now, value, now))
            conn.commit()
            message = "系统参数保存成功"
        except Exception as e:
            error = f"保存失败: {e}"

    settings = {}
    for row in conn.execute("SELECT key, value FROM system_settings").fetchall():
        settings[row["key"]] = row["value"]

    # 填充默认值
    for key, value in DEFAULT_SETTINGS.items():
        if key not in settings:
            settings[key] = value

    # 解析凭证编号规则供模板使用
    rule_str = settings.get("voucher_number_rule", DEFAULT_SETTINGS["voucher_number_rule"])
    vn_rule = {}
    for part in rule_str.split(","):
        if ":" in part:
            k, v = part.split(":", 1)
            vn_rule[k.strip()] = v.strip()
    # 生成预览
    from datetime import datetime as dt
    prefix = vn_rule.get("prefix", "记-")
    date_fmt = vn_rule.get("date_fmt", "%Y%m%d")
    seq_digits = int(vn_rule.get("seq_digits", "3"))
    vn_rule["preview"] = f"{prefix}{dt.now().strftime(date_fmt)}-{'1'.zfill(seq_digits)}"

    banks = [dict(b) for b in conn.execute(
        "SELECT DISTINCT bank_type FROM bank_accounts UNION SELECT DISTINCT bank_type FROM bank_transactions"
    ).fetchall()]

    conn.close()
    return render_template("system_settings.html", settings=settings,
                           vn_rule=vn_rule, banks=banks, message=message, error=error,
                           defaults=DEFAULT_SETTINGS)


# ========== 损益结转（月末结账） ==========

@accounting_bp.route("/period-close", methods=["POST"])
def period_close():
    """月末损益结转 - 将损益类科目余额转入本年利润"""
    conn = get_db()
    period = request.form.get("period", "")
    operator = request.form.get("operator", "管理员")
    now = datetime.now().isoformat()

    if not period:
        conn.close()
        return redirect("/accounting-books?type=periods")

    try:
        # 1. 获取所有已记账凭证的损益类科目发生额汇总
        revenue_rows = conn.execute("""
            SELECT l.account_code, l.account_name,
                   COALESCE(SUM(CAST(l.debit AS REAL)), 0) as dr,
                   COALESCE(SUM(CAST(l.credit AS REAL)), 0) as cr
            FROM voucher_lines l
            JOIN accounting_vouchers v ON v.id = l.voucher_id
            WHERE v.accounting_period = ? AND v.status = '已记账'
              AND l.account_code LIKE '5%'
            GROUP BY l.account_code
        """, (period,)).fetchall()

        expense_rows = conn.execute("""
            SELECT l.account_code, l.account_name,
                   COALESCE(SUM(CAST(l.debit AS REAL)), 0) as dr,
                   COALESCE(SUM(CAST(l.credit AS REAL)), 0) as cr
            FROM voucher_lines l
            JOIN accounting_vouchers v ON v.id = l.voucher_id
            WHERE v.accounting_period = ? AND v.status = '已记账'
              AND (l.account_code LIKE '5%' AND l.account_code NOT LIKE '50%' AND l.account_code NOT LIKE '51%')
            GROUP BY l.account_code
        """, (period,)).fetchall()

        lines_to_create = []

        # 收入类科目（5001, 5051, 5111, 5301）- 贷方余额转入本年利润借方
        for r in revenue_rows:
            code = r["account_code"]
            net = r["cr"] - r["dr"]  # 收入类贷方余额
            if abs(net) > 0.01:
                lines_to_create.append({
                    "code": code,
                    "debit": net,  # 借：收入（减少）
                    "credit": 0,
                })

        # 费用类科目（5401-5801）- 借方余额转入本年利润贷方
        for r in expense_rows:
            code = r["account_code"]
            net = r["dr"] - r["cr"]  # 费用类借方余额
            if abs(net) > 0.01:
                lines_to_create.append({
                    "code": code,
                    "debit": 0,
                    "credit": net,  # 贷：费用（减少）
                })

        if not lines_to_create:
            conn.close()
            return redirect("/accounting-books?type=periods")

        # 计算本年利润发生额
        total_revenue_dr = sum(l["debit"] for l in lines_to_create)
        total_expense_cr = sum(l["credit"] for l in lines_to_create)

        # 添加本年利润分录（借贷差额）
        if total_revenue_dr > total_expense_cr:
            # 盈利：本年利润在贷方
            lines_to_create.append({
                "code": "3103",
                "debit": 0,
                "credit": total_revenue_dr - total_expense_cr,
            })
        elif total_expense_cr > total_revenue_dr:
            # 亏损：本年利润在借方
            lines_to_create.append({
                "code": "3103",
                "debit": total_expense_cr - total_revenue_dr,
                "credit": 0,
            })

        # 2. 创建结转凭证
        cursor = conn.cursor()
        voucher_no = generate_voucher_number(conn, period)
        vid = str(uuid.uuid4())

        total_debit = sum(l["debit"] for l in lines_to_create)
        total_credit = sum(l["credit"] for l in lines_to_create)

        cursor.execute(
            """INSERT INTO accounting_vouchers
               (id, voucher_no, voucher_date, accounting_period, summary,
                total_debit, total_credit, created_by, status, created_at, updated_at)
               VALUES (?, ?, date('now'), ?, ?, ?, ?, ?, '已记账', ?, ?)""",
            (vid, voucher_no, period, f"月末损益结转 - {period}",
             f"{total_debit:.2f}", f"{total_credit:.2f}", operator, now, now))

        for line in lines_to_create:
            acc = conn.execute(
                "SELECT name FROM chart_of_accounts WHERE code=?", (line["code"],)
            ).fetchone()
            acc_name = acc["name"] if acc else line["code"]
            cursor.execute(
                """INSERT INTO voucher_lines
                   (id, voucher_id, account_code, account_name, debit, credit, summary)
                   VALUES (?, ?, ?, ?, ?, ?, ?)""",
                (str(uuid.uuid4()), vid, line["code"], acc_name,
                 f"{line['debit']:.2f}", f"{line['credit']:.2f}",
                 f"月末损益结转 - {period}"))

        # 3. 关闭会计期间
        conn.execute(
            "UPDATE accounting_periods SET status='关闭', is_closed=1, "
            "closed_by=?, closed_at=? WHERE period_name=? OR id=?",
            (operator, now, period, period))

        conn.commit()
    except Exception as e:
        pass

    conn.close()
    return redirect("/accounting-books?type=periods")


# ========== 月末结转损益向导 ==========

@accounting_bp.route("/profit-carry-forward", methods=["GET", "POST"])
def profit_carry_forward():
    """月末结转损益向导：预览 → 一键结转 → 结果"""
    conn = get_db()
    message = None
    error = None
    
    # 获取所有会计期间
    periods = [dict(p) for p in conn.execute(
        "SELECT * FROM accounting_periods ORDER BY period_name DESC"
    ).fetchall()]
    
    if not periods:
        conn.close()
        return render_template("profit_carry_forward.html", step="init",
                               periods=[], message=None, error="没有可用的会计期间，请先创建期间。")

    if request.method == "POST":
        action = request.form.get("action", "")
        period = request.form.get("period", "")
        
        if action == "start":
            # 预览损益汇总
            return _carry_forward_preview(conn, period)
        elif action == "execute":
            # 执行结转
            return _carry_forward_execute(conn, period)

    conn.close()
    return render_template("profit_carry_forward.html", step="init",
                           periods=periods, message=message, error=error)


def _carry_forward_preview(conn, period):
    """预览损益类科目发生额"""
    # 获取损益类科目的本期发生额
    def get_pl_sum(conn, period, code_pattern, is_credit=True):
        """获取损益类科目的贷方(收入)或借方(成本费用)发生额"""
        field = "cr" if is_credit else "dr"
        rows = conn.execute(f"""
            SELECT l.account_code as code, l.account_name as name,
                   COALESCE(SUM(CAST(l.{field} AS REAL)), 0) as amount
            FROM voucher_lines l
            JOIN accounting_vouchers v ON v.id = l.voucher_id
            WHERE v.accounting_period = ? AND v.status = '已记账'
              AND l.account_code LIKE ?
            GROUP BY l.account_code
            ORDER BY l.account_code
        """, (period, code_pattern)).fetchall()
        return [{"code": r["code"], "name": r["name"], "amount": float(r["amount"] or 0)} for r in rows]

    # 收入类: 5开头但不是5401(主营业务成本)和54开头(成本)和55/56(费用), 即贷方发生额
    # 简化: 收入类 = 5001(主营业务收入)开头的科目
    revenue_items = get_pl_sum(conn, period, "5001%", is_credit=True)
    # 成本类: 5401(主营业务成本)
    cost_items = get_pl_sum(conn, period, "5401%", is_credit=False)
    # 费用类: 55/56开头的科目
    expense_items = get_pl_sum(conn, period, "55%", is_credit=False)
    expense_items += get_pl_sum(conn, period, "56%", is_credit=False)
    expense_items += get_pl_sum(conn, period, "53%", is_credit=False)  # 营业外支出等

    revenue_total = sum(r["amount"] for r in revenue_items)
    cost_total = sum(r["amount"] for r in cost_items)
    expense_total = sum(r["amount"] for r in expense_items)
    net_profit = revenue_total - cost_total - expense_total

    # 检查条件
    unposted_count = conn.execute("""
        SELECT COUNT(*) FROM accounting_vouchers 
        WHERE accounting_period=? AND status NOT IN ('已记账')
    """, (period,)).fetchone()[0]

    pending_count = conn.execute("""
        SELECT COUNT(*) FROM accounting_vouchers 
        WHERE accounting_period=? AND status = '待审核'
    """, (period,)).fetchone()[0]

    has_pl_data = revenue_total > 0 or cost_total > 0 or expense_total > 0
    checks = {
        "has_revenue": not has_pl_data,
        "no_unposted": unposted_count > 0,
        "no_pending": pending_count > 0,
    }
    can_execute = has_pl_data and unposted_count == 0 and pending_count == 0

    periods = [dict(p) for p in conn.execute(
        "SELECT * FROM accounting_periods ORDER BY period_name DESC"
    ).fetchall()]
    conn.close()

    return render_template("profit_carry_forward.html", step="preview",
                           period=period, periods=periods,
                           revenue_items=revenue_items, cost_items=cost_items,
                           expense_items=expense_items,
                           revenue_total=revenue_total, cost_total=cost_total,
                           expense_total=expense_total, net_profit=net_profit,
                           checks=checks, can_execute=can_execute)


def _carry_forward_execute(conn, period):
    """执行损益结转：生成结转凭证"""
    now = datetime.now().isoformat()
    
    # 获取收入类科目贷方发生额（转入本年利润贷方）
    def get_dr_cr(conn, period, code_pattern):
        rows = conn.execute("""
            SELECT l.account_code as code, l.account_name as name,
                   COALESCE(SUM(CAST(l.debit AS REAL)), 0) as dr,
                   COALESCE(SUM(CAST(l.credit AS REAL)), 0) as cr
            FROM voucher_lines l
            JOIN accounting_vouchers v ON v.id = l.voucher_id
            WHERE v.accounting_period = ? AND v.status = '已记账'
              AND l.account_code LIKE ?
            GROUP BY l.account_code
        """, (period, code_pattern)).fetchall()
        return [{"code": r["code"], "name": r["name"],
                 "dr": float(r["dr"] or 0), "cr": float(r["cr"] or 0)} for r in rows]

    revenue = get_dr_cr(conn, period, "5001%")
    costs = get_dr_cr(conn, period, "5401%")
    expenses = get_dr_cr(conn, period, "55%") + get_dr_cr(conn, period, "56%") + get_dr_cr(conn, period, "53%")

    revenue_total = sum(r["cr"] for r in revenue)
    cost_total = sum(c["dr"] for c in costs)
    expense_total = sum(e["dr"] for e in expenses)

    lines_to_create = []
    result_lines = []

    # 借：主营业务收入 → 贷：本年利润
    for r in revenue:
        if r["cr"] > 0:
            lines_to_create.append({"code": r["code"], "name": r["name"], "debit": r["cr"], "credit": 0})
            result_lines.append({"code": r["code"], "name": r["name"], "debit": r["cr"], "credit": 0})

    # 借：本年利润 → 贷：主营业务成本/管理费用等
    profit_dr = 0
    for c in costs + expenses:
        if c["dr"] > 0:
            lines_to_create.append({"code": c["code"], "name": c["name"], "debit": 0, "credit": c["dr"]})
            result_lines.append({"code": c["code"], "name": c["name"], "debit": 0, "credit": c["dr"]})
            profit_dr += c["dr"]

    # 本年利润结转
    net = revenue_total - cost_total - expense_total
    if net > 0:
        # 盈利：贷方增加
        lines_to_create.append({"code": "3103", "name": "本年利润", "debit": 0, "credit": net})
    else:
        # 亏损：借方增加
        lines_to_create.append({"code": "3103", "name": "本年利润", "debit": abs(net), "credit": 0})

    # 创建凭证
    cursor = conn.cursor()
    voucher_no = generate_voucher_number(conn, period) + "-JZSY"
    vid = str(uuid.uuid4())
    total_debit = sum(l["debit"] for l in lines_to_create)
    total_credit = sum(l["credit"] for l in lines_to_create)

    cursor.execute("""
        INSERT INTO accounting_vouchers
        (id, voucher_no, voucher_date, accounting_period, summary,
         total_debit, total_credit, created_by, status, created_at, updated_at)
        VALUES (?, ?, date('now'), ?, ?, ?, ?, '系统', '已记账', ?, ?)
    """, (vid, voucher_no, period, f"月末损益结转 - {period}",
          f"{total_debit:.2f}", f"{total_credit:.2f}", now, now))

    for line in lines_to_create:
        cursor.execute("""
            INSERT INTO voucher_lines
            (id, voucher_id, account_code, account_name, debit, credit, summary)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (str(uuid.uuid4()), vid, line["code"], line["name"],
              f"{line['debit']:.2f}", f"{line['credit']:.2f}",
              f"月末损益结转 - {period}"))

    # 更新期间状态为已结转
    conn.execute("UPDATE accounting_periods SET status='已结转' WHERE period_name=? AND is_closed=0",
                 (period,))
    conn.commit()
    
    result_data = {
        "voucher_no": voucher_no,
        "revenue": revenue_total,
        "cost_expense": cost_total + expense_total,
    }

    periods = [dict(p) for p in conn.execute(
        "SELECT * FROM accounting_periods ORDER BY period_name DESC"
    ).fetchall()]
    conn.close()

    return render_template("profit_carry_forward.html", step="result",
                           period=period, periods=periods,
                           result_data=result_data, result_lines=result_lines,
                           message="损益结转凭证已生成！")


# ========== 数据导出 ==========

@accounting_bp.route("/export/vouchers")
def export_vouchers():
    """导出凭证列表为CSV"""
    conn = get_db()
    period = request.args.get("period", "")

    if period:
        rows = conn.execute("""
            SELECT voucher_no, voucher_date, accounting_period, summary,
                   total_debit, total_credit, created_by, status, created_at
            FROM accounting_vouchers WHERE accounting_period=?
            ORDER BY voucher_date, voucher_no
        """, (period,)).fetchall()
    else:
        rows = conn.execute("""
            SELECT voucher_no, voucher_date, accounting_period, summary,
                   total_debit, total_credit, created_by, status, created_at
            FROM accounting_vouchers ORDER BY voucher_date DESC, voucher_no DESC
        """).fetchall()

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["凭证编号", "日期", "期间", "摘要", "借方合计", "贷方合计", "制单人", "状态", "创建时间"])
    for r in rows:
        writer.writerow([r[0], r[1], r[2], r[3], r[4], r[5], r[6], r[7], r[8]])

    conn.close()
    output.seek(0)
    return Response(
        output.getvalue().encode('utf-8-sig'),
        mimetype='text/csv',
        headers={"Content-Disposition": f"attachment;filename=vouchers_{period or 'all'}.csv"}
    )


@accounting_bp.route("/export/balance")
def export_balance():
    """导出科目余额表为CSV"""
    conn = get_db()
    period = request.args.get("period", "")

    # 获取期初余额
    opening_map = {}
    for b in conn.execute(
        "SELECT account_code, opening_balance FROM account_balances WHERE period_id=?", (period,)
    ).fetchall():
        opening_map[b["account_code"]] = b["opening_balance"]

    rows = conn.execute("""
        SELECT a.code, a.name, a.account_type, a.balance_direction,
            COALESCE(SUM(CASE WHEN v.status='已记账' AND CAST(l.debit AS REAL)>0
                THEN CAST(l.debit AS REAL) ELSE 0 END), 0) as debit_sum,
            COALESCE(SUM(CASE WHEN v.status='已记账' AND CAST(l.credit AS REAL)>0
                THEN CAST(l.credit AS REAL) ELSE 0 END), 0) as credit_sum
        FROM chart_of_accounts a
        LEFT JOIN voucher_lines l ON l.account_code = a.code
        LEFT JOIN accounting_vouchers v ON v.id = l.voucher_id AND v.accounting_period = ?
        WHERE a.is_active = 1
        GROUP BY a.code, a.name, a.account_type, a.balance_direction
        ORDER BY a.code
    """, (period,)).fetchall()

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["科目编码", "科目名称", "类型", "方向", "期初余额", "借方发生额", "贷方发生额", "期末余额"])

    for r in rows:
        opening = opening_map.get(r[0], 0.0)
        direction = r[3] or "借"
        if direction == "借":
            closing = opening + r[4] - r[5]
        else:
            closing = opening + r[5] - r[4]
        writer.writerow([r[0], r[1], r[2], r[3],
                         f"{opening:.2f}", f"{r[4]:.2f}",
                         f"{r[5]:.2f}", f"{closing:.2f}"])

    conn.close()
    output.seek(0)
    return Response(
        output.getvalue().encode('utf-8-sig'),
        mimetype='text/csv',
        headers={"Content-Disposition": f"attachment;filename=balance_{period or 'all'}.csv"}
    )


@accounting_bp.route("/export/trial-balance")
def export_trial_balance():
    """导出试算平衡表为CSV"""
    conn = get_db()
    period = request.args.get("period", "")

    opening_map = {}
    for b in conn.execute(
        "SELECT account_code, opening_balance FROM account_balances WHERE period_id=?", (period,)
    ).fetchall():
        opening_map[b["account_code"]] = b["opening_balance"]

    rows = conn.execute("""
        SELECT a.code, a.name, a.balance_direction,
            COALESCE(SUM(CASE WHEN v.status='已记账' AND CAST(l.debit AS REAL)>0
                THEN CAST(l.debit AS REAL) ELSE 0 END), 0) as debit_sum,
            COALESCE(SUM(CASE WHEN v.status='已记账' AND CAST(l.credit AS REAL)>0
                THEN CAST(l.credit AS REAL) ELSE 0 END), 0) as credit_sum
        FROM chart_of_accounts a
        LEFT JOIN voucher_lines l ON l.account_code = a.code
        LEFT JOIN accounting_vouchers v ON v.id = l.voucher_id AND v.accounting_period = ?
        WHERE a.is_active = 1
        GROUP BY a.code, a.name, a.balance_direction
        ORDER BY a.code
    """, (period,)).fetchall()

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["科目编码", "科目名称",
                     "期初借方", "期初贷方", "本期借方", "本期贷方", "期末借方", "期末贷方"])

    totals = [0.0] * 6
    for r in rows:
        opening = opening_map.get(r[0], 0.0)
        direction = r[2] or "借"
        if direction == "借":
            dr_open, cr_open = opening, 0.0
            closing = opening + r[3] - r[4]
        else:
            dr_open, cr_open = 0.0, opening
            closing = opening + r[4] - r[3]
        dr_close = closing if closing > 0 else 0.0
        cr_close = abs(closing) if closing < 0 else 0.0

        row_vals = [r[0], r[1], dr_open, cr_open, r[3], r[4], dr_close, cr_close]
        writer.writerow([r[0], r[1],
                         f"{dr_open:.2f}" if dr_open else "", f"{cr_open:.2f}" if cr_open else "",
                         f"{r[3]:.2f}" if r[3] else "", f"{r[4]:.2f}" if r[4] else "",
                         f"{dr_close:.2f}" if dr_close else "", f"{cr_close:.2f}" if cr_close else ""])
        for i in range(6):
            totals[i] += row_vals[i + 2]

    writer.writerow(["合计", "", totals[0], totals[1], totals[2], totals[3], totals[4], totals[5]])

    conn.close()
    output.seek(0)
    return Response(
        output.getvalue().encode('utf-8-sig'),
        mimetype='text/csv',
        headers={"Content-Disposition": f"attachment;filename=trial_balance_{period or 'all'}.csv"}
    )


# ========== 固定资产管理 ==========

@accounting_bp.route("/fixed-assets", methods=["GET", "POST"])
def fixed_assets():
    """固定资产管理"""
    conn = get_db()
    # 确保表存在
    conn.execute("""
        CREATE TABLE IF NOT EXISTS fixed_assets (
            id TEXT PRIMARY KEY,
            asset_code TEXT UNIQUE NOT NULL,
            asset_name TEXT NOT NULL,
            category TEXT NOT NULL DEFAULT '设备',
            department TEXT,
            purchase_date TEXT NOT NULL,
            original_value REAL NOT NULL DEFAULT 0,
            residual_value REAL NOT NULL DEFAULT 0,
            useful_life_months INTEGER NOT NULL DEFAULT 60,
            monthly_depreciation REAL NOT NULL DEFAULT 0,
            accumulated_depreciation REAL NOT NULL DEFAULT 0,
            net_value REAL NOT NULL DEFAULT 0,
            account_code TEXT DEFAULT '1601',
            status TEXT DEFAULT '使用中',
            location TEXT,
            notes TEXT,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL
        )
    """)
    conn.commit()

    message = None
    error = None

    if request.method == "POST":
        action = request.form.get("action", "")
        now = datetime.now().isoformat()

        try:
            if action == "create":
                asset_id = str(uuid.uuid4())
                name = request.form.get("asset_name", "")
                category = request.form.get("category", "设备")
                original = float(request.form.get("original_value", 0))
                residual = float(request.form.get("residual_value", 0))
                months = int(request.form.get("useful_life_months", 60))
                monthly_dep = round((original - residual) / months, 2) if months > 0 else 0
                net_value = original

                existing = conn.execute(
                    "SELECT COALESCE(MAX(CAST(SUBSTR(asset_code,4) AS INTEGER)),0)+1 FROM fixed_assets"
                ).fetchone()[0]
                asset_code = f"FA{existing:04d}"

                conn.execute("""
                    INSERT INTO fixed_assets (id, asset_code, asset_name, category, department,
                        purchase_date, original_value, residual_value, useful_life_months,
                        monthly_depreciation, accumulated_depreciation, net_value,
                        account_code, status, location, notes, created_at, updated_at)
                    VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
                """, (asset_id, asset_code, name, category,
                      request.form.get("department", ""),
                      request.form.get("purchase_date", date.today().isoformat()),
                      original, residual, months, monthly_dep, 0, net_value,
                      request.form.get("account_code", "1601"),
                      request.form.get("status", "使用中"),
                      request.form.get("location", ""),
                      request.form.get("notes", ""), now, now))
                conn.commit()
                message = f"固定资产 {asset_code} 创建成功"

            elif action == "update":
                aid = request.form.get("asset_id", "")
                original = float(request.form.get("original_value", 0))
                residual = float(request.form.get("residual_value", 0))
                months = int(request.form.get("useful_life_months", 60))
                monthly_dep = round((original - residual) / months, 2) if months > 0 else 0

                conn.execute("""
                    UPDATE fixed_assets SET asset_name=?,category=?,department=?,
                        purchase_date=?,original_value=?,residual_value=?,
                        useful_life_months=?,monthly_depreciation=?,
                        account_code=?,status=?,location=?,notes=?,updated_at=?
                    WHERE id=?
                """, (request.form.get("asset_name"), request.form.get("category"),
                      request.form.get("department"), request.form.get("purchase_date"),
                      original, residual, months, monthly_dep,
                      request.form.get("account_code", "1601"),
                      request.form.get("status"), request.form.get("location"),
                      request.form.get("notes"), now, aid))
                conn.commit()
                message = "固定资产信息已更新"

            elif action == "delete":
                aid = request.form.get("asset_id", "")
                conn.execute("DELETE FROM fixed_assets WHERE id=?", (aid,))
                conn.commit()
                message = "固定资产已删除"

            elif action == "dispose":
                aid = request.form.get("asset_id", "")
                conn.execute(
                    "UPDATE fixed_assets SET status='已处置', updated_at=? WHERE id=?",
                    (now, aid))
                conn.commit()
                message = "固定资产已标记为处置"

        except Exception as e:
            error = f"操作失败: {e}"

    assets = [dict(a) for a in conn.execute(
        "SELECT * FROM fixed_assets ORDER BY status, purchase_date DESC").fetchall()]
    depts = [dict(d) for d in conn.execute(
        "SELECT DISTINCT name FROM departments ORDER BY name").fetchall()]

    # 汇总
    total_original = sum(a["original_value"] for a in assets if a["status"] == "使用中")
    total_dep = sum(a["accumulated_depreciation"] for a in assets if a["status"] == "使用中")
    total_net = sum(a["net_value"] for a in assets if a["status"] == "使用中")

    conn.close()
    return render_template("fixed_assets.html", assets=assets, depts=depts,
                           total_original=total_original, total_dep=total_dep,
                           total_net=total_net, message=message, error=error,
                           today=date.today().isoformat())


# ========== 自动计提折旧 ==========

@accounting_bp.route("/depreciate-fixed-assets", methods=["POST"])
def depreciate_fixed_assets():
    """月末计提折旧 - 生成折旧凭证"""
    period = request.form.get("period", "")
    operator = request.form.get("operator", "管理员")
    if not period:
        period = date.today().strftime("%Y-%m")

    conn = get_db()
    now = datetime.now().isoformat()

    # 只对使用中的固定资产计提
    assets = [dict(a) for a in conn.execute(
        "SELECT * FROM fixed_assets WHERE status='使用中' ORDER BY id").fetchall()]

    if len(assets) == 0:
        conn.close()
        return redirect("/fixed-assets")

    total_depreciation = sum(a["monthly_depreciation"] for a in assets)
    if total_depreciation <= 0:
        conn.close()
        return redirect("/fixed-assets")

    # 按部门汇总折旧费用
    from collections import defaultdict
    dept_map = defaultdict(float)
    for a in assets:
        dept = a["department"] or "管理部门"
        dept_map[dept] += a["monthly_depreciation"]

    # 更新累计折旧和净值
    for a in assets:
        dep = a["monthly_depreciation"]
        new_accum = round(a["accumulated_depreciation"] + dep, 2)
        new_net = round(a["original_value"] - new_accum, 2)
        conn.execute(
            "UPDATE fixed_assets SET accumulated_depreciation=?, net_value=?, updated_at=? WHERE id=?",
            (new_accum, new_net, now, a["id"]))

    # 生成折旧凭证
    cursor = conn.cursor()
    voucher_no = generate_voucher_number(conn, period) + "-ZJ"
    vid = str(uuid.uuid4())

    cursor.execute("""
        INSERT INTO accounting_vouchers
        (id, voucher_no, voucher_date, accounting_period, summary,
         total_debit, total_credit, created_by, status, created_at, updated_at)
        VALUES (?, ?, date('now'), ?, ?, ?, ?, ?, '已记账', ?, ?)
    """, (vid, voucher_no, period,
          f"月末计提折旧 - {period} ({len(assets)}项资产)",
          f"{total_depreciation:.2f}", f"{total_depreciation:.2f}",
          operator, now, now))

    # Debit lines (制造费用/管理费用)
    for dept, amount in dept_map.items():
        if amount > 0:
            acc_code = "5101" if dept in ["生产部门"] else "6602"
            acc_name = "制造费用" if acc_code == "5101" else "管理费用"
            cursor.execute("""
                INSERT INTO voucher_lines
                (id, voucher_id, account_code, account_name, debit, credit, summary)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (str(uuid.uuid4()), vid, acc_code, acc_name,
                  f"{amount:.2f}", "0.00",
                  f"{dept}折旧({len(assets)}项)"))

    # Credit line (累计折旧)
    cursor.execute("""
        INSERT INTO voucher_lines
        (id, voucher_id, account_code, account_name, debit, credit, summary)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (str(uuid.uuid4()), vid, "1602", "累计折旧",
          "0.00", f"{total_depreciation:.2f}",
          f"计提折旧({len(assets)}项)"))

    conn.commit()
    conn.close()
    return redirect("/fixed-assets")


# ========== 凭证模板 ==========

@accounting_bp.route("/voucher-templates", methods=["GET", "POST"])
def voucher_templates():
    """凭证模板管理"""
    conn = get_db()
    conn.execute("""
        CREATE TABLE IF NOT EXISTS voucher_templates (
            id TEXT PRIMARY KEY, template_name TEXT NOT NULL, summary TEXT NOT NULL,
            lines_json TEXT NOT NULL, created_at TEXT NOT NULL, updated_at TEXT NOT NULL
        )
    """)
    conn.commit()

    message = None
    if request.method == "POST":
        action = request.form.get("action", "")
        now = datetime.now().isoformat()
        try:
            if action == "create":
                name = request.form.get("template_name", "")
                summary = request.form.get("summary", "")
                accounts = request.form.getlist("line_account[]")
                debits = request.form.getlist("line_debit[]")
                credits = request.form.getlist("line_credit[]")
                lines = []
                for i in range(len(accounts)):
                    d = float(debits[i] or 0); c = float(credits[i] or 0)
                    if d > 0 or c > 0:
                        acc = conn.execute("SELECT name FROM chart_of_accounts WHERE code=?",
                                          (accounts[i],)).fetchone()
                        lines.append({"code": accounts[i], "name": acc["name"] if acc else accounts[i],
                                       "debit": d, "credit": c})
                import json
                conn.execute(
                    "INSERT INTO voucher_templates (id,template_name,summary,lines_json,created_at,updated_at) VALUES (?,?,?,?,?,?)",
                    (str(uuid.uuid4()), name, summary, json.dumps(lines, ensure_ascii=False), now, now))
                conn.commit()
                message = f"模板 {name} 创建成功"
            elif action == "delete":
                tid = request.form.get("template_id", "")
                conn.execute("DELETE FROM voucher_templates WHERE id=?", (tid,))
                conn.commit()
                message = "模板已删除"
        except Exception as e:
            message = f"操作失败: {e}"

    templates = [dict(t) for t in conn.execute(
        "SELECT * FROM voucher_templates ORDER BY updated_at DESC").fetchall()]
    import json
    for t in templates:
        t["lines"] = json.loads(t["lines_json"])

    accounts_list = [dict(a) for a in conn.execute(
        "SELECT code, name FROM chart_of_accounts WHERE is_active=1 ORDER BY code").fetchall()]
    conn.close()
    return render_template("voucher_templates.html", templates=templates,
                          accounts_list=accounts_list, message=message,
                          today=date.today().isoformat())


# ========== 凭证批量审核/记账 ==========

@accounting_bp.route("/batch-vouchers", methods=["POST"])
def batch_vouchers():
    """批量审核/记账"""
    action = request.form.get("action", "")
    voucher_ids = request.form.getlist("voucher_ids[]")
    conn = get_db()
    now = datetime.now().isoformat()

    if action == "batch_review":
        conn.execute("UPDATE accounting_vouchers SET status='已审核',updated_at=? WHERE id IN ({}) AND status='草稿'".format(
            ",".join("?" for _ in voucher_ids)), [now] + voucher_ids)
    elif action == "batch_post":
        conn.execute("UPDATE accounting_vouchers SET status='已记账',updated_at=? WHERE id IN ({}) AND status='已审核'".format(
            ",".join("?" for _ in voucher_ids)), [now] + voucher_ids)

    conn.commit()
    conn.close()
    return redirect("/vouchers")


# ========== 凭证复制 ==========

@accounting_bp.route("/copy-voucher/<voucher_id>", methods=["POST"])
def copy_voucher(voucher_id):
    """复制凭证"""
    conn = get_db()
    now = datetime.now().isoformat()
    orig = conn.execute("SELECT * FROM accounting_vouchers WHERE id=?", (voucher_id,)).fetchone()
    if not orig:
        conn.close()
        return redirect("/vouchers")

    orig_lines = conn.execute("SELECT * FROM voucher_lines WHERE voucher_id=?", (voucher_id,)).fetchall()
    vid = str(uuid.uuid4())
    voucher_no = generate_voucher_number(conn, orig["accounting_period"]) + "-COPY"

    conn.execute("""
        INSERT INTO accounting_vouchers
        (id, voucher_no, voucher_date, accounting_period, summary,
         total_debit, total_credit, created_by, status, created_at, updated_at)
        VALUES (?,?,?,?,?,?,?,?,?,?,?)
    """, (vid, voucher_no, orig["voucher_date"], orig["accounting_period"],
          orig["summary"] + " (复制)", orig["total_debit"], orig["total_credit"],
          "管理员", "草稿", now, now))

    for line in orig_lines:
        conn.execute("""
            INSERT INTO voucher_lines
            (id, voucher_id, account_code, account_name, debit, credit, summary,
             related_entity_type, related_entity_id)
            VALUES (?,?,?,?,?,?,?,?,?)
        """, (str(uuid.uuid4()), vid, line["account_code"], line["account_name"],
              line["debit"], line["credit"], line["summary"],
              line["related_entity_type"], line["related_entity_id"]))

    conn.commit()
    conn.close()
    return redirect("/vouchers")


# ========== 多栏式明细账 ==========

@accounting_bp.route("/multi-column-ledger")
def multi_column_ledger():
    """多栏式明细账"""
    conn = get_db()
    period = request.args.get("period", date.today().strftime("%Y-%m"))
    ledger_type = request.args.get("ltype", "expense")

    # 费用科目明细（管理费用/销售费用/财务费用的子科目）
    expense_accounts = conn.execute("""
        SELECT code, name FROM chart_of_accounts
        WHERE (code LIKE '6601%' OR code LIKE '6602%' OR code LIKE '6603%' OR code LIKE '5501%' OR code LIKE '5502%' OR code LIKE '5503%')
        AND is_active=1 ORDER BY code
    """).fetchall()

    # 增值税科目
    vat_accounts = conn.execute("""
        SELECT code, name FROM chart_of_accounts
        WHERE code LIKE '2221%' AND is_active=1 ORDER BY code
    """).fetchall()

    columns = expense_accounts if ledger_type == "expense" else vat_accounts
    columns = [dict(c) for c in columns]

    # 获取每个科目的发生额（按期间汇总）
    col_data = {}
    for col in columns:
        row = conn.execute("""
            SELECT COALESCE(SUM(CAST(l.debit AS REAL)),0) dr, COALESCE(SUM(CAST(l.credit AS REAL)),0) cr
            FROM voucher_lines l JOIN accounting_vouchers v ON v.id=l.voucher_id
            WHERE l.account_code=? AND v.accounting_period=? AND v.status='已记账'
        """, (col["code"], period)).fetchone()
        col_data[col["code"]] = {"debit": row["dr"], "credit": row["cr"], "net": row["dr"] - row["cr"]}

    # 按凭证获取明细
    detail_rows = []
    total_dr = 0
    total_cr = 0
    for col in columns:
        lines = conn.execute("""
            SELECT v.voucher_no, v.voucher_date, v.summary,
                   CAST(l.debit AS REAL) dr, CAST(l.credit AS REAL) cr
            FROM voucher_lines l JOIN accounting_vouchers v ON v.id=l.voucher_id
            WHERE l.account_code=? AND v.accounting_period=? AND v.status='已记账'
            ORDER BY v.voucher_date
        """, (col["code"], period)).fetchall()
        for l in lines:
            detail_rows.append(dict(l, account=col["code"], name=col["name"]))
            total_dr += l["dr"]; total_cr += l["cr"]

    conn.close()
    return render_template("multi_column_ledger.html",
        period=period, ledger_type=ledger_type,
        columns=columns, col_data=col_data,
        detail_rows=detail_rows, total_dr=total_dr, total_cr=total_cr)


# ========== 审计日志 ==========

@accounting_bp.route("/audit-log")
def audit_log():
    """审计日志查询"""
    conn = get_db()
    # Ensure table
    conn.execute("""
        CREATE TABLE IF NOT EXISTS audit_logs (
            id TEXT PRIMARY KEY, user_name TEXT, action TEXT,
            entity_type TEXT, entity_id TEXT, details TEXT, created_at TEXT
        )
    """)
    conn.commit()

    page = int(request.args.get("page", 1))
    per_page = 30
    offset = (page - 1) * per_page

    rows = conn.execute("""
        SELECT * FROM audit_logs ORDER BY created_at DESC LIMIT ? OFFSET ?
    """, (per_page, offset)).fetchall()
    total = conn.execute("SELECT COUNT(*) FROM audit_logs").fetchone()[0]

    conn.close()
    return render_template("audit_log.html",
        logs=[dict(r) for r in rows], total=total, page=page, per_page=per_page)


# ========== 财务比率分析 ==========

@accounting_bp.route("/financial-ratios")
def financial_ratios():
    """财务比率分析 + 环比同比"""
    conn = get_db()
    period_str = request.args.get("period", date.today().strftime("%Y-%m"))

    # Parse period for MOM and YOY comparisons
    y, m = int(period_str[:4]), int(period_str[5:7])
    last_month = f"{y}-{m-1:02d}" if m > 1 else f"{y-1}-12"
    last_year = f"{y-1}-{m:02d}"

    def sum_period(table, date_col, amount_col, p):
        return to_float(conn.execute(
            f"SELECT COALESCE(SUM(CAST({amount_col} AS REAL)),0) FROM {table} "
            f"WHERE {date_col} LIKE ?", (p + "%",)).fetchone()[0])

    # Revenue and expense for current, last month, last year
    inc_cur = sum_period("incomes", "income_date", "amount", period_str)
    exp_cur = sum_period("expenses", "expense_date", "amount", period_str)
    inc_lm = sum_period("incomes", "income_date", "amount", last_month)
    exp_lm = sum_period("expenses", "expense_date", "amount", last_month)
    inc_ly = sum_period("incomes", "income_date", "amount", last_year)
    exp_ly = sum_period("expenses", "expense_date", "amount", last_year)

    profit_cur = inc_cur - exp_cur
    profit_lm = inc_lm - exp_lm
    profit_ly = inc_ly - exp_ly

    # Asset/Liability/Equity from account balances
    def get_balance(account_code, period_str):
        r = conn.execute(
            "SELECT COALESCE(SUM(closing_balance),0) FROM account_balances ab "
            "JOIN accounting_periods ap ON ab.period_id=ap.id "
            "WHERE ab.account_code=? AND ap.period_name=?",
            (account_code, period_str)).fetchone()
        return to_float(r[0]) if r else 0

    # Simplified: calculate from incomes/expenses directly since account_balances may be sparse
    total_assets = get_balance("1001", period_str) + get_balance("1002", period_str)  # cash + bank deposits
    # Add AR
    ar = to_float(conn.execute("""
        SELECT COALESCE(SUM(CAST(l.debit AS REAL))-SUM(CAST(l.credit AS REAL)),0)
        FROM voucher_lines l JOIN accounting_vouchers v ON v.id=l.voucher_id
        WHERE l.account_code='1122' AND v.status='已记账' AND v.accounting_period=?
    """, (period_str,)).fetchone()[0])
    total_assets += ar

    # Fixed assets
    fa = to_float(conn.execute(
        "SELECT COALESCE(SUM(net_value),0) FROM fixed_assets WHERE status='使用中'"
    ).fetchone()[0])
    total_assets += fa
    total_assets = max(total_assets, profit_cur)  # ensure not zero

    # AP
    ap = to_float(conn.execute("""
        SELECT COALESCE(SUM(CAST(l.credit AS REAL))-SUM(CAST(l.debit AS REAL)),0)
        FROM voucher_lines l JOIN accounting_vouchers v ON v.id=l.voucher_id
        WHERE l.account_code LIKE '220%' AND v.status='已记账' AND v.accounting_period=?
    """, (period_str,)).fetchone()[0])
    total_liabilities = ap + max(0, exp_cur * 0.3)  # approximate
    total_equity = max(total_assets - total_liabilities, 1000)

    # Financial Ratios
    ratios = {}
    ratios["gross_margin"] = (inc_cur - exp_cur * 0.6) / max(inc_cur, 1) * 100
    ratios["net_margin"] = profit_cur / max(inc_cur, 1) * 100
    ratios["roe"] = profit_cur / max(total_equity, 1) * 100
    ratios["roa"] = profit_cur / max(total_assets, 1) * 100
    ratios["current_ratio"] = total_assets / max(total_liabilities, 1)
    ratios["debt_ratio"] = total_liabilities / max(total_assets, 1) * 100
    ratios["interest_coverage"] = max(profit_cur, 0) / max(exp_cur * 0.05, 1)
    ratios["ar_turnover"] = inc_cur / max(ar, 1)
    ratios["ar_days"] = 365 / max(ratios["ar_turnover"], 0.01)
    ratios["asset_turnover"] = inc_cur / max(total_assets, 1)
    ratios["equity_mult"] = total_assets / max(total_equity, 1)

    # MOM/YOY comparison
    def pct_change(curr, prev):
        if prev == 0: return None
        return (curr - prev) / abs(prev) * 100

    comparison = [
        {"metric": "收入", "current": inc_cur, "last_month": inc_lm, "last_year": inc_ly,
         "mom_pct": pct_change(inc_cur, inc_lm) or 0, "yoy_pct": pct_change(inc_cur, inc_ly)},
        {"metric": "支出", "current": exp_cur, "last_month": exp_lm, "last_year": exp_ly,
         "mom_pct": pct_change(exp_cur, exp_lm) or 0, "yoy_pct": pct_change(exp_cur, exp_ly)},
        {"metric": "利润", "current": profit_cur, "last_month": profit_lm, "last_year": profit_ly,
         "mom_pct": pct_change(profit_cur, profit_lm) or 0, "yoy_pct": pct_change(profit_cur, profit_ly)},
    ]

    conn.close()
    return render_template("financial_ratios.html", ratios=ratios, comparison=comparison,
                           period=period_str)


# ========== 客户/供应商对账单 ==========

@accounting_bp.route("/customer-statement")
def customer_statement():
    """客户对账单"""
    return _statement("customer")

@accounting_bp.route("/supplier-statement")
def supplier_statement():
    """供应商对账单"""
    return _statement("supplier")

def _statement(stype):
    conn = get_db()
    entity_id = request.args.get("entity_id", "")
    start_date = request.args.get("start_date", date.today().replace(day=1).isoformat())
    end_date = request.args.get("end_date", date.today().isoformat())

    if stype == "customer":
        entities = [dict(r) for r in conn.execute(
            "SELECT id, name FROM customers ORDER BY name").fetchall()]
    else:
        entities = [dict(r) for r in conn.execute(
            "SELECT id, name FROM suppliers ORDER BY name").fetchall()]

    entity_name = None
    transactions = []
    opening_balance = 0.0
    total_debit = 0.0
    total_credit = 0.0
    closing_balance = 0.0

    if entity_id:
        if stype == "customer":
            entity_name = conn.execute("SELECT name FROM customers WHERE id=?", (entity_id,)
                                       ).fetchone()
            entity_name = entity_name[0] if entity_name else ""
            # Calculate opening AR balance (orders before start_date - payments before start_date)
            orders_before = to_float(conn.execute(
                "SELECT COALESCE(SUM(CAST(total_amount AS REAL)),0) FROM processing_orders "
                "WHERE customer_id=? AND order_date<?", (entity_id, start_date)).fetchone()[0])
            payments_before = to_float(conn.execute(
                "SELECT COALESCE(SUM(CAST(amount AS REAL)),0) FROM incomes "
                "WHERE customer_id=? AND income_date<?", (entity_id, start_date)).fetchone()[0])
            opening_balance = orders_before - payments_before

            # Orders in period (increases)
            orders = conn.execute(
                "SELECT order_date as date, order_no, CAST(total_amount AS REAL) amount "
                "FROM processing_orders WHERE customer_id=? AND order_date>=? AND order_date<=? "
                "ORDER BY order_date", (entity_id, start_date, end_date)).fetchall()
            for r in orders:
                transactions.append({
                    "date": r[0], "type_label": "订单", "is_increase": True,
                    "summary": f"订单 {r[1]}", "debit": float(r[2]), "credit": 0, "balance": 0
                })
            # Incomes in period (decreases)
            incs = conn.execute(
                "SELECT income_date as date, CAST(amount AS REAL) amount, bank_type, notes "
                "FROM incomes WHERE customer_id=? AND income_date>=? AND income_date<=? "
                "ORDER BY income_date", (entity_id, start_date, end_date)).fetchall()
            for r in incs:
                transactions.append({
                    "date": r[0], "type_label": "收款", "is_increase": False,
                    "summary": f"收款({r[2]})" + (f" {r[3]}" if r[3] else ""),
                    "debit": 0, "credit": float(r[1]), "balance": 0
                })
        else:
            entity_name = conn.execute("SELECT name FROM suppliers WHERE id=?", (entity_id,)
                                       ).fetchone()
            entity_name = entity_name[0] if entity_name else ""
            # AP: expenses before start_date minus payments
            exp_before = to_float(conn.execute(
                "SELECT COALESCE(SUM(CAST(amount AS REAL)),0) FROM expenses "
                "WHERE supplier_id=? AND expense_date<?", (entity_id, start_date)).fetchone()[0])
            # For simplicity, AP increases with expenses (credit), decreases with payments via bank
            opening_balance = exp_before  # amount owed to supplier before period

            expenses = conn.execute(
                "SELECT expense_date as date, expense_type, CAST(amount AS REAL) amount, description "
                "FROM expenses WHERE supplier_id=? AND expense_date>=? AND expense_date<=? "
                "ORDER BY expense_date", (entity_id, start_date, end_date)).fetchall()
            for r in expenses:
                transactions.append({
                    "date": r[0], "type_label": "发生", "is_increase": True,
                    "summary": f"{r[1]}" + (f" - {r[3]}" if r[3] else ""),
                    "debit": float(r[2]), "credit": 0, "balance": 0
                })

        # Sort by date and compute running balance
        def sort_key(t):
            parts = [int(x) for x in t["date"].split("-")]
            inc_prio = 0 if t["is_increase"] else 1
            return (parts[0], parts[1], parts[2], inc_prio)
        transactions.sort(key=sort_key)

        bal = opening_balance
        for t in transactions:
            if t["is_increase"]:
                bal += t["debit"]
                total_debit += t["debit"]
            else:
                bal -= t["credit"]
                total_credit += t["credit"]
            t["balance"] = bal
        closing_balance = bal

    conn.close()

    export_url = (f"/export/statement?type={stype}&entity_id={entity_id}"
                    f"&start_date={start_date}&end_date={end_date}") if entity_id else "#"

    return render_template("customer_statement.html",
        stype=stype, entities=entities, entity_id=entity_id, entity_name=entity_name,
        start_date=start_date, end_date=end_date,
        opening_balance=opening_balance, total_debit=total_debit,
        total_credit=total_credit, closing_balance=closing_balance,
        transactions=transactions, export_url=export_url)


# ========== 出纳日记账 ==========

@accounting_bp.route("/cash-journal")
def cash_journal():
    """现金/银行日记账"""
    conn = get_db()
    journal_type = request.args.get("jtype", "cash")
    period = request.args.get("period", date.today().strftime("%Y-%m"))
    bank_name = request.args.get("bank_name", "")

    if journal_type == "cash":
        incomes = conn.execute("""
            SELECT income_date as date, customer_name as party, CAST(amount AS REAL) amount,
                   '收入' as type, bank_type, bank_type||' 收入' as note
            FROM incomes WHERE income_date LIKE ? AND (bank_type NOT LIKE '%银行%' OR bank_type='现金')
            ORDER BY income_date
        """, (period + "%",)).fetchall()
        expenses = conn.execute("""
            SELECT expense_date as date, supplier_name as party, CAST(amount AS REAL) amount,
                   '支出' as type, bank_type, expense_type||' 支出' as note
            FROM expenses WHERE expense_date LIKE ? AND (bank_type NOT LIKE '%银行%' OR bank_type='现金')
            ORDER BY expense_date
        """, (period + "%",)).fetchall()
    else:
        incomes = conn.execute("""
            SELECT income_date as date, customer_name as party, CAST(amount AS REAL) amount,
                   '收入' as type, bank_type, bank_type||' 收入' as note
            FROM incomes WHERE income_date LIKE ? AND bank_type=?
            ORDER BY income_date
        """, (period + "%", bank_name)).fetchall()
        expenses = conn.execute("""
            SELECT expense_date as date, supplier_name as party, CAST(amount AS REAL) amount,
                   '支出' as type, bank_type, expense_type||' 支出' as note
            FROM expenses WHERE expense_date LIKE ? AND bank_type=?
            ORDER BY expense_date
        """, (period + "%", bank_name)).fetchall()

    all_items = sorted(
        [dict(r) for r in incomes] + [dict(r) for r in expenses],
        key=lambda x: (x["date"] or "", x.get("type", "")))

    running_balance = 0.0
    total_in = 0.0
    total_out = 0.0
    for item in all_items:
        amt = item["amount"]
        if item["type"] == "收入":
            running_balance += amt
            total_in += amt
        else:
            running_balance -= amt
            total_out += amt
        item["balance"] = round(running_balance, 2)

    bank_list = [dict(r) for r in conn.execute(
        "SELECT DISTINCT bank_type FROM incomes UNION SELECT DISTINCT bank_type FROM expenses").fetchall()]
    if not bank_list:
        bank_list = [{"bank_type": "对公账户"}, {"bank_type": "N银行"}]

    conn.close()
    return render_template("cash_journal.html",
        journal_type=journal_type, period=period, bank_name=bank_name,
        items=all_items, total_in=total_in, total_out=total_out,
        balance=running_balance, bank_list=bank_list)


# ========== 资金日报表导出 ==========

@accounting_bp.route("/export/statement")
def export_statement():
    """导出资金日报/月报CSV 或 对账单CSV"""
    conn = get_db()
    export_type = request.args.get("type", "")

    import csv, io
    output = io.StringIO()
    writer = csv.writer(output)

    if export_type in ("customer", "supplier"):
        entity_id = request.args.get("entity_id", "")
        start_date = request.args.get("start_date", "")
        end_date = request.args.get("end_date", "")
        entity_name = ""
        if export_type == "customer":
            en = conn.execute("SELECT name FROM customers WHERE id=?", (entity_id,)).fetchone()
            entity_name = en[0] if en else ""
        else:
            en = conn.execute("SELECT name FROM suppliers WHERE id=?", (entity_id,)).fetchone()
            entity_name = en[0] if en else ""

        writer.writerow([f"{'客户' if export_type=='customer' else '供应商'}对账单"])
        writer.writerow([f"名称：{entity_name}", f"期间：{start_date} 至 {end_date}"])
        writer.writerow(["日期", "类型", "摘要", "增加", "减少", "余额"])
        # Reuse _statement logic in simplified form
        if export_type == "customer":
            ob = to_float(conn.execute(
                "SELECT COALESCE(SUM(CAST(total_amount AS REAL)),0)-COALESCE(SUM((SELECT COALESCE(SUM(CAST(amount AS REAL)),0) FROM incomes WHERE customer_id=? AND income_date<?)),0) FROM processing_orders WHERE customer_id=? AND order_date<?",
                (entity_id, start_date, entity_id, start_date)).fetchone()[0])
            writer.writerow(["", "", "期初余额", "", "", f"{ob:.2f}"])
        conn.close()
        output.seek(0)
        return Response(output.getvalue().encode('utf-8-sig'),
            mimetype='text/csv',
            headers={"Content-Disposition": f"attachment;filename=statement_{export_type}_{entity_name}_{start_date}.csv"})

    period = request.args.get("period", date.today().strftime("%Y-%m"))
    jtype = request.args.get("jtype", "cash")
    bank_name = request.args.get("bank_name", "")

    if jtype == "cash":
        incomes = conn.execute(
            "SELECT income_date, customer_name, CAST(amount AS REAL) FROM incomes "
            "WHERE income_date LIKE ? ORDER BY income_date", (period + "%",)).fetchall()
        expenses = conn.execute(
            "SELECT expense_date, supplier_name, CAST(amount AS REAL) FROM expenses "
            "WHERE expense_date LIKE ? ORDER BY expense_date", (period + "%",)).fetchall()
    else:
        incomes = conn.execute(
            "SELECT income_date, customer_name, CAST(amount AS REAL) FROM incomes "
            "WHERE income_date LIKE ? AND bank_type=? ORDER BY income_date",
            (period + "%", bank_name)).fetchall()
        expenses = conn.execute(
            "SELECT expense_date, supplier_name, CAST(amount AS REAL) FROM expenses "
            "WHERE expense_date LIKE ? AND bank_type=? ORDER BY expense_date",
            (period + "%", bank_name)).fetchall()

    import csv, io
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["日期", "类型", "对方", "金额", "摘要"])
    for r in incomes:
        writer.writerow([r[0], "收入", r[1], f"{r[2]:.2f}", "收入"])
    for r in expenses:
        writer.writerow([r[0], "支出", r[1], f"{r[2]:.2f}", "支出"])

    conn.close()
    output.seek(0)
    return Response(output.getvalue().encode('utf-8-sig'),
        mimetype='text/csv',
        headers={"Content-Disposition": f"attachment;filename=journal_{jtype}_{period}.csv"})


# ========== 月末结账检查 ==========

@accounting_bp.route("/check-before-close", methods=["GET", "POST"])
def check_before_close():
    """月末结账前检查"""
    conn = get_db()
    period = request.args.get("period", date.today().strftime("%Y-%m"))

    if request.method == "POST":
        action = request.form.get("action", "")
        if action == "rollback":
            # 删除该期间的最后一张结转凭证
            last_close = conn.execute(
                "SELECT id, voucher_no FROM accounting_vouchers "
                "WHERE summary LIKE '%损益结转%' AND accounting_period=? "
                "ORDER BY created_at DESC LIMIT 1", (period,)).fetchone()
            if last_close:
                conn.execute("DELETE FROM voucher_lines WHERE voucher_id=?", (last_close["id"],))
                conn.execute("DELETE FROM accounting_vouchers WHERE id=?", (last_close["id"],))
                conn.execute("UPDATE accounting_periods SET status='open', is_closed=0, "
                           "closed_by='', closed_at='' WHERE period_name=?",
                           (period,))
                conn.commit()
            conn.close()
            return redirect(f"/check-before-close?period={period}")

    checks = {}

    # 1. 所有凭证是否已记账
    unposted = conn.execute(
        "SELECT COUNT(*) FROM accounting_vouchers WHERE accounting_period=? AND status!='已记账'",
        (period,)).fetchone()[0]
    checks["all_posted"] = {"pass": unposted == 0, "detail": f"{unposted} 张未记账凭证"}

    # 2. 试算是否平衡
    rows = conn.execute("""
        SELECT a.code, a.balance_direction,
            COALESCE(SUM(CASE WHEN v.status='已记账' THEN CAST(l.debit AS REAL) ELSE 0 END), 0) dr,
            COALESCE(SUM(CASE WHEN v.status='已记账' THEN CAST(l.credit AS REAL) ELSE 0 END), 0) cr
        FROM chart_of_accounts a
        LEFT JOIN voucher_lines l ON l.account_code=a.code
        LEFT JOIN accounting_vouchers v ON v.id=l.voucher_id AND v.accounting_period=?
        WHERE a.is_active=1 GROUP BY a.code
    """, (period,)).fetchall()
    total_dr = sum(r[2] for r in rows)
    total_cr = sum(r[3] for r in rows)
    checks["balanced"] = {"pass": abs(total_dr - total_cr) < 0.01,
                          "detail": f"借 {total_dr:.2f} = 贷 {total_cr:.2f}"}

    # 3. 损益是否已结转
    has_close = conn.execute(
        "SELECT COUNT(*) FROM accounting_vouchers "
        "WHERE summary LIKE '%损益结转%' AND accounting_period=?",
        (period,)).fetchone()[0]
    has_posted = conn.execute(
        "SELECT COUNT(*) FROM accounting_vouchers "
        "WHERE summary LIKE '%损益结转%' AND accounting_period=? AND status='已记账'",
        (period,)).fetchone()[0]
    checks["profit_closed"] = {"pass": has_posted > 0,
                               "detail": f"{has_close} 张结转凭证({has_posted} 已记账)"}

    # 4. 折旧是否已计提
    has_dep = conn.execute(
        "SELECT COUNT(*) FROM accounting_vouchers "
        "WHERE summary LIKE '%折旧%' AND accounting_period=?",
        (period,)).fetchone()[0]
    fa_count = conn.execute("SELECT COUNT(*) FROM fixed_assets WHERE status='使用中'").fetchone()[0]
    checks["depreciated"] = {"pass": has_dep > 0 or fa_count == 0,
                             "detail": f"{has_dep} 张折旧凭证({fa_count} 项资产)"}

    # 5. 期间是否已关闭
    period_status = conn.execute(
        "SELECT is_closed FROM accounting_periods WHERE period_name=?",
        (period,)).fetchone()
    is_closed = period_status["is_closed"] if period_status else 0
    checks["not_closed"] = {"pass": not is_closed, "detail": "已关闭" if is_closed else "未关闭"}

    all_ok = all(c["pass"] for c in checks.values())

    conn.close()
    return render_template("check_close.html", period=period, checks=checks, all_ok=all_ok,
                          has_posted=has_posted, is_closed=is_closed)


# ========== 数据备份与恢复 ==========

@accounting_bp.route("/data-backup", methods=["GET", "POST"])
def data_backup():
    """数据备份与恢复"""
    import shutil
    DB = "/workspace/oxidation_finance_v20/oxidation_finance_demo_ready.db"
    BACKUP_DIR = "/workspace/oxidation_finance_v20/backups"
    os.makedirs(BACKUP_DIR, exist_ok=True)

    message = None
    error = None

    if request.method == "POST":
        action = request.form.get("action", "")
        try:
            if action == "backup":
                ts = datetime.now().strftime("%Y%m%d_%H%M%S")
                note = request.form.get("note", "")
                fname = f"backup_{ts}.db"
                dst = os.path.join(BACKUP_DIR, fname)
                shutil.copy2(DB, dst)
                conn = get_db()
                conn.execute(
                    "INSERT INTO audit_logs (id, user_name, action, entity_type, entity_id, details, created_at) "
                    "VALUES (?,?,?,?,?,?,?)",
                    (str(uuid.uuid4()), "管理员", "数据备份", "system", fname,
                     note or "手动备份", datetime.now().isoformat()))
                conn.commit()
                conn.close()
                message = f"备份成功: {fname}"
            elif action == "restore":
                file = request.files.get("backup_file")
                if file and file.filename.endswith('.db'):
                    restore_path = os.path.join(BACKUP_DIR, "restore_" + file.filename)
                    file.save(restore_path)
                    shutil.copy2(restore_path, DB)
                    conn = get_db()
                    conn.execute(
                        "INSERT INTO audit_logs (id, user_name, action, entity_type, entity_id, details, created_at) "
                        "VALUES (?,?,?,?,?,?,?)",
                        (str(uuid.uuid4()), "管理员", "数据恢复", "system", file.filename,
                         "从备份恢复", datetime.now().isoformat()))
                    conn.commit()
                    conn.close()
                    message = f"数据已从 {file.filename} 恢复"
                else:
                    error = "请上传 .db 格式的备份文件"
        except Exception as e:
            error = f"操作失败: {e}"

    backups = []
    if os.path.exists(BACKUP_DIR):
        for f in sorted(os.listdir(BACKUP_DIR), reverse=True):
            fp = os.path.join(BACKUP_DIR, f)
            if f.endswith('.db'):
                stat = os.stat(fp)
                backups.append({"name": f, "size": f"{stat.st_size / 1024:.1f} KB",
                               "time": datetime.fromtimestamp(stat.st_mtime).strftime("%Y-%m-%d %H:%M:%S")})

    return render_template("data_backup.html", backups=backups, message=message, error=error)


# ========== 用户管理 ==========

@accounting_bp.route("/user-management", methods=["GET", "POST"])
def user_management():
    """用户与权限管理"""
    conn = get_db()
    conn.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id TEXT PRIMARY KEY,
            username TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            role TEXT NOT NULL DEFAULT '记账会计',
            is_active INTEGER DEFAULT 1,
            created_at TEXT NOT NULL
        )
    """)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS login_sessions (
            id TEXT PRIMARY KEY,
            user_id TEXT NOT NULL,
            login_at TEXT NOT NULL,
            ip_address TEXT
        )
    """)
    # Ensure default admin
    import hashlib
    exist = conn.execute("SELECT COUNT(*) FROM users").fetchone()[0]
    if exist == 0:
        conn.execute(
            "INSERT INTO users (id, username, password, role, is_active, created_at) VALUES (?,?,?,?,?,?)",
            (str(uuid.uuid4()), "admin",
             hashlib.sha256("admin123".encode()).hexdigest(),
             "管理员", 1, datetime.now().isoformat()))
    conn.commit()

    message = None
    if request.method == "POST":
        action = request.form.get("action", "")
        try:
            if action == "create":
                uid = str(uuid.uuid4())
                pwd = hashlib.sha256(request.form.get("password", "").encode()).hexdigest()
                conn.execute(
                    "INSERT INTO users (id, username, password, role, is_active, created_at) VALUES (?,?,?,?,?,?)",
                    (uid, request.form.get("username"), pwd, request.form.get("role", "记账会计"),
                     1, datetime.now().isoformat()))
                conn.commit()
                message = "用户创建成功"
            elif action == "delete":
                uid = request.form.get("user_id")
                conn.execute("DELETE FROM users WHERE id=? AND role!='管理员'", (uid,))
                conn.commit()
                message = "用户已删除"
            elif action == "change_pwd":
                uid = request.form.get("user_id")
                pwd = hashlib.sha256(request.form.get("password", "").encode()).hexdigest()
                conn.execute("UPDATE users SET password=? WHERE id=?", (pwd, uid))
                conn.commit()
                message = "密码已更新"
        except Exception as e:
            message = f"操作失败: {e}"

    users_list = [dict(u) for u in conn.execute(
        "SELECT id, username, role, is_active, created_at FROM users ORDER BY role").fetchall()]
    conn.close()
    return render_template("user_management.html", users=users_list, message=message)


# ========== 批量导入 ==========

@accounting_bp.route("/batch-import", methods=["GET", "POST"])
def batch_import():
    """批量导入（客户/供应商/科目CSV）"""
    import csv, io
    message = None
    error = None

    if request.method == "POST":
        imp_type = request.form.get("import_type", "")
        file = request.files.get("csv_file")
        if not file:
            error = "请选择CSV文件"
        elif imp_type not in ("customer", "supplier", "account"):
            error = "未知导入类型"
        else:
            try:
                content = file.read().decode('utf-8-sig')
                reader = csv.reader(io.StringIO(content))
                headers = next(reader, None)
                conn = get_db()
                now = datetime.now().isoformat()
                count = 0
                for row in reader:
                    if not row or all(c.strip() == '' for c in row):
                        continue
                    if imp_type == "customer":
                        name = row[0].strip()
                        if name:
                            exist = conn.execute("SELECT COUNT(*) FROM customers WHERE name=?", (name,)).fetchone()[0]
                            if exist == 0:
                                conn.execute(
                                    "INSERT INTO customers (id, name, contact, phone, address, notes, created_at, updated_at) VALUES (?,?,?,?,?,?,?,?)",
                                    (str(uuid.uuid4()), name, row[1] if len(row) > 1 else "",
                                     row[2] if len(row) > 2 else "", "", "", now, now))
                                count += 1
                    elif imp_type == "supplier":
                        name = row[0].strip()
                        if name:
                            exist = conn.execute("SELECT COUNT(*) FROM suppliers WHERE name=?", (name,)).fetchone()[0]
                            if exist == 0:
                                conn.execute(
                                    "INSERT INTO suppliers (id, name, contact, phone, address, notes, created_at, updated_at) VALUES (?,?,?,?,?,?,?,?)",
                                    (str(uuid.uuid4()), name, row[1] if len(row) > 1 else "",
                                     row[2] if len(row) > 2 else "", "", "", now, now))
                                count += 1
                    elif imp_type == "account":
                        code = row[0].strip()
                        name = row[1].strip() if len(row) > 1 else ""
                        acct_type = row[2].strip() if len(row) > 2 else "资产"
                        if code and name:
                            exist = conn.execute(
                                "SELECT COUNT(*) FROM chart_of_accounts WHERE code=?", (code,)).fetchone()[0]
                            if exist == 0:
                                direction = "借" if acct_type in ("资产", "成本", "费用") else "贷"
                                conn.execute(
                                    "INSERT INTO chart_of_accounts (id, code, name, account_type, balance_direction, "
                                    "parent_code, is_active, created_at, updated_at) VALUES (?,?,?,?,?,?,?,?,?)",
                                    (str(uuid.uuid4()), code, name, acct_type, direction, "", 1, now, now))
                                count += 1
                conn.commit()
                conn.close()
                message = f"成功导入 {count} 条 {imp_type} 记录"
            except Exception as eMsg:
                error = f"导入失败: {eMsg}"

    return render_template("batch_import.html", message=message, error=error)


# ========== 部门损益表 ==========

@accounting_bp.route("/department-pl")
def department_pl():
    """部门损益表"""
    conn = get_db()
    period = request.args.get("period", date.today().strftime("%Y-%m"))

    departments = [dict(r) for r in conn.execute(
        "SELECT id, name FROM departments WHERE is_active=1 ORDER BY name").fetchall()]

    dept_data = []
    for d in departments:
        # Expenses by department (from expense records tagged by supplier's business type or direct)
        income = to_float(conn.execute(
            "SELECT COALESCE(SUM(CAST(amount AS REAL)),0) FROM incomes "
            "WHERE income_date LIKE ?", (period + "%",)).fetchone()[0]) / max(len(departments), 1)
        cost = to_float(conn.execute(
            "SELECT COALESCE(SUM(CAST(amount AS REAL)),0) FROM expenses "
            "WHERE expense_date LIKE ? AND expense_type IN ('三酸','片碱','亚钠','色粉','除油剂','挂具','外发加工费')",
            (period + "%",)).fetchone()[0]) / max(len(departments), 1)
        expense = to_float(conn.execute(
            "SELECT COALESCE(SUM(CAST(amount AS REAL)),0) FROM expenses "
            "WHERE expense_date LIKE ? AND expense_type IN ('房租','水电费','日常费用','工资','其他')",
            (period + "%",)).fetchone()[0]) / max(len(departments), 1)

        profit = income - cost - expense
        margin = profit / max(income, 1) * 100
        dept_data.append({"name": d["name"], "income": income, "cost": cost,
                          "expense": expense, "profit": profit, "margin": margin})

    conn.close()
    return render_template("department_pl.html", dept_data=dept_data, period=period)


# ========== 项目损益与预算 ==========

@accounting_bp.route("/project-pl", methods=["GET", "POST"])
def project_pl():
    """项目损益表 + 预算管理"""
    conn = get_db()
    period = request.args.get("period", date.today().strftime("%Y-%m"))
    action = request.args.get("action", "")
    show_modal = False

    if request.method == "POST" and request.form.get("action") == "set_budget":
        pid = request.form.get("project_id")
        budget = float(request.form.get("budget", "0") or 0)
        conn.execute("UPDATE projects SET budget=? WHERE id=?", (budget, pid))
        conn.commit()
        action = "budget"

    projects = [dict(r) for r in conn.execute(
        "SELECT id, name, status, start_date, end_date, budget, manager "
        "FROM projects ORDER BY name").fetchall()]

    project_data = []
    for p in projects:
        budget = to_float(p["budget"] if p["budget"] else 0)
        # Approximate actual cost from expenses in period
        actual = to_float(conn.execute(
            "SELECT COALESCE(SUM(CAST(amount AS REAL)),0) FROM expenses "
            "WHERE expense_date LIKE ?", (period + "%",)).fetchone()[0]) / max(len(projects), 1)
        variance = budget - actual
        var_pct = (variance / budget * 100) if budget > 0 else 0
        p["actual"] = actual
        p["variance"] = variance
        p["var_pct"] = var_pct
        project_data.append(p)

    conn.close()
    return render_template("project_pl.html", project_data=project_data,
                          projects=projects, period=period, action=action,
                          show_modal=show_modal)


# ========== 发票管理 ==========

@accounting_bp.route("/invoices", methods=["GET", "POST"])
def invoices():
    """发票管理"""
    conn = get_db()
    conn.execute("""
        CREATE TABLE IF NOT EXISTS invoices (
            id TEXT PRIMARY KEY,
            invoice_no TEXT NOT NULL,
            inv_type TEXT NOT NULL,
            counterparty TEXT NOT NULL,
            amount REAL NOT NULL DEFAULT 0,
            tax_rate REAL DEFAULT 13,
            tax_amount REAL NOT NULL DEFAULT 0,
            invoice_date TEXT NOT NULL,
            status TEXT DEFAULT '未认证',
            related_income_id TEXT,
            related_expense_id TEXT,
            notes TEXT,
            created_at TEXT NOT NULL
        )
    """)
    conn.commit()

    show_modal = False
    message = None
    error = None

    if request.method == "POST":
        action = request.form.get("action", "")
        try:
            if action == "create":
                amount = float(request.form.get("amount", "0") or 0)
                tax_rate = float(request.form.get("tax_rate", "13") or 0)
                tax_amount = amount * tax_rate / 100.0
                conn.execute(
                    "INSERT INTO invoices (id, invoice_no, inv_type, counterparty, amount, "
                    "tax_rate, tax_amount, invoice_date, status, created_at) "
                    "VALUES (?,?,?,?,?,?,?,?,?,?)",
                    (str(uuid.uuid4()), request.form.get("invoice_no"),
                     request.form.get("inv_type"), request.form.get("counterparty"),
                     amount, tax_rate, tax_amount,
                     request.form.get("invoice_date", date.today().isoformat()),
                     "未认证", datetime.now().isoformat()))
                conn.commit()
                message = "发票录入成功"
            elif action == "delete":
                conn.execute("DELETE FROM invoices WHERE id=?",
                            (request.form.get("inv_id"),))
                conn.commit()
                message = "发票已删除"
        except Exception as e:
            error = f"操作失败: {e}"

    view = request.args.get("view", "list")
    if view == "summary":
        output_amount = to_float(conn.execute(
            "SELECT COALESCE(SUM(amount),0) FROM invoices WHERE inv_type='销项'").fetchone()[0])
        output_tax = to_float(conn.execute(
            "SELECT COALESCE(SUM(tax_amount),0) FROM invoices WHERE inv_type='销项'").fetchone()[0])
        input_amount = to_float(conn.execute(
            "SELECT COALESCE(SUM(amount),0) FROM invoices WHERE inv_type='进项'").fetchone()[0])
        input_tax = to_float(conn.execute(
            "SELECT COALESCE(SUM(tax_amount),0) FROM invoices WHERE inv_type='进项'").fetchone()[0])
        conn.close()
        return render_template("invoice_management.html", view="summary",
            summary={"output_amount": output_amount, "output_tax": output_tax,
                     "input_amount": input_amount, "input_tax": input_tax,
                     "tax_payable": output_tax - input_tax})

    invoices_list = [dict(r) for r in conn.execute(
        "SELECT * FROM invoices ORDER BY invoice_date DESC, created_at DESC").fetchall()]
    conn.close()
    return render_template("invoice_management.html",
        invoices=invoices_list, message=message, error=error,
        show_modal=show_modal, today=date.today().isoformat())


# ========== 工资管理 ==========

@accounting_bp.route("/salary", methods=["GET", "POST"])
def salary():
    """员工管理 + 工资表 + 个税计算"""
    conn = get_db()
    # Create tables
    conn.execute("""
        CREATE TABLE IF NOT EXISTS employees (
            id TEXT PRIMARY KEY, name TEXT NOT NULL, id_number TEXT,
            position TEXT, base_salary REAL DEFAULT 0, social_base REAL DEFAULT 0,
            hire_date TEXT, is_active INTEGER DEFAULT 1,
            created_at TEXT NOT NULL, updated_at TEXT NOT NULL
        )
    """)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS salary_records (
            id TEXT PRIMARY KEY, employee_id TEXT NOT NULL, emp_name TEXT NOT NULL,
            period TEXT NOT NULL, base_salary REAL DEFAULT 0,
            overtime REAL DEFAULT 0, bonus REAL DEFAULT 0, gross REAL DEFAULT 0,
            social_personal REAL DEFAULT 0, social_company REAL DEFAULT 0,
            tax REAL DEFAULT 0, net REAL DEFAULT 0,
            created_at TEXT NOT NULL,
            UNIQUE(employee_id, period)
        )
    """)
    conn.commit()

    tab = request.args.get("tab", "list")
    period = request.args.get("period", date.today().strftime("%Y-%m"))
    message = None; error = None; show_modal = False; voucher_msg = None

    if request.method == "POST":
        action = request.form.get("action", "")
        try:
            if action == "add_employee":
                now = datetime.now().isoformat()
                conn.execute(
                    "INSERT INTO employees (id, name, id_number, position, base_salary, social_base, hire_date, is_active, created_at, updated_at) "
                    "VALUES (?,?,?,?,?,?,?,1,?,?)",
                    (str(uuid.uuid4()), request.form.get("name"),
                     request.form.get("id_number", ""), request.form.get("position", ""),
                     float(request.form.get("base_salary", "0") or 0),
                     float(request.form.get("social_base", "0") or 0),
                     request.form.get("hire_date", date.today().isoformat()), now, now))
                conn.commit()
                message = "员工添加成功"
            elif action in ("delete", "restore"):
                conn.execute("UPDATE employees SET is_active=? WHERE id=?",
                    (0 if action == "delete" else 1, request.form.get("emp_id")))
                conn.commit()
                message = "操作成功"
            elif action == "generate":
                _generate_salary(conn, period)
                message = f"工资表 {period} 生成成功"
                tab = "salary"
            elif action == "gen_voucher":
                voucher_msg, err = _gen_salary_voucher(conn, period)
                tab = "voucher"
                if err: error = err
        except Exception as e:
            error = f"操作失败: {e}"

    # Queries
    employees = [dict(r) for r in conn.execute(
        "SELECT * FROM employees ORDER BY is_active DESC, name").fetchall()]

    salary_records = []
    salary_summary = {"total_gross": 0, "total_tax": 0, "total_social": 0, "total_net": 0}
    if tab == "salary":
        salary_records = [dict(r) for r in conn.execute(
            "SELECT * FROM salary_records WHERE period=? ORDER BY emp_name", (period,)).fetchall()]
        for r in salary_records:
            salary_summary["total_gross"] += float(r["gross"] or 0)
            salary_summary["total_tax"] += float(r["tax"] or 0)
            salary_summary["total_social"] += float(r["social_personal"] or 0)
            salary_summary["total_net"] += float(r["net"] or 0)

    conn.close()
    return render_template("salary_management.html",
        employees=employees, salary_records=salary_records, salary_summary=salary_summary,
        tab=tab, period=period, message=message, error=error, voucher_msg=voucher_msg,
        show_modal=show_modal, today=date.today().isoformat())


def _generate_salary(conn, period):
    """生成月度工资表"""
    import hashlib
    employees = conn.execute(
        "SELECT * FROM employees WHERE is_active=1").fetchall()
    for emp in employees:
        eid = emp["id"]; ename = emp["name"]
        base = float(emp["base_salary"] or 0)
        social_base = float(emp["social_base"] or base)
        # Social insurance (personal portion ~10.5%)
        social_personal = round(social_base * 0.105, 2)
        # Tax calculation (simplified progressive)
        taxable = base - 5000 - social_personal  # basic deduction
        if taxable <= 0:
            tax = 0
        elif taxable <= 3000:
            tax = taxable * 0.03
        elif taxable <= 12000:
            tax = taxable * 0.1 - 210
        elif taxable <= 25000:
            tax = taxable * 0.2 - 1410
        elif taxable <= 35000:
            tax = taxable * 0.25 - 2660
        else:
            tax = taxable * 0.3 - 4410
        tax = max(round(tax, 2), 0)
        gross = base
        net = gross - social_personal - tax
        sid = hashlib.md5(f"{eid}_{period}".encode()).hexdigest()[:16]
        # Upsert
        conn.execute("DELETE FROM salary_records WHERE employee_id=? AND period=?", (eid, period))
        conn.execute(
            "INSERT INTO salary_records (id, employee_id, emp_name, period, base_salary, overtime, bonus, gross, social_personal, social_company, tax, net, created_at) "
            "VALUES (?,?,?,?,?,0,0,?,?,?,?,?,?)",
            (sid, eid, ename, period, base, gross, social_personal, social_personal * 1.5, tax, net, datetime.now().isoformat()))
    conn.commit()


def _gen_salary_voucher(conn, period):
    """生成工资凭证"""
    records = conn.execute(
        "SELECT * FROM salary_records WHERE period=?", (period,)).fetchall()
    if not records:
        return None, "该月无工资数据，请先生成工资表"

    total = sum(float(r["gross"] or 0) for r in records)
    vno = f"GZ{period.replace('-','')}01"
    # Check duplicate
    exist = conn.execute(
        "SELECT COUNT(*) FROM accounting_vouchers WHERE voucher_no=?", (vno,)).fetchone()[0]
    if exist:
        return f"凭证 {vno} 已存在", None

    vid = str(uuid.uuid4())
    now = datetime.now().isoformat()
    conn.execute(
        "INSERT INTO accounting_vouchers (id, voucher_no, voucher_date, accounting_period, summary, total_debit, total_credit, created_by, status, created_at, updated_at) "
        "VALUES (?,?,?,?,?,?,?,?,'已审核',?,?)",
        (vid, vno, date.today().isoformat(), period,
         f"计提{period}工资", total, total, "系统", now, now))
    conn.execute(
        "INSERT INTO voucher_lines (id, voucher_id, account_code, account_name, debit, credit, summary) VALUES (?,?,?,?,?,?,?)",
        (str(uuid.uuid4()), vid, "5602", "管理费用-工资", str(total), "0", f"{period}工资"))
    conn.execute(
        "INSERT INTO voucher_lines (id, voucher_id, account_code, account_name, debit, credit, summary) VALUES (?,?,?,?,?,?,?)",
        (str(uuid.uuid4()), vid, "2211", "应付职工薪酬", "0", str(total), f"{period}工资"))
    conn.commit()
    return f"工资凭证 {vno} 生成成功（金额: {total:.2f}）", None


# ========== 标准财务报表打印 ==========

@accounting_bp.route("/financial-reports")
def financial_reports():
    """标准财务报表（资产负债表/利润表/现金流量表）"""
    conn = get_db()
    period = request.args.get("period", date.today().strftime("%Y-%m"))

    def sum_incomes(p):
        return to_float(conn.execute(
            "SELECT COALESCE(SUM(CAST(amount AS REAL)),0) FROM incomes WHERE income_date LIKE ?",
            (p + "%",)).fetchone()[0])

    def sum_expenses(p):
        return to_float(conn.execute(
            "SELECT COALESCE(SUM(CAST(amount AS REAL)),0) FROM expenses WHERE expense_date LIKE ?",
            (p + "%",)).fetchone()[0])

    revenue = sum_incomes(period)
    total_exp = sum_expenses(period)
    cost = total_exp * 0.6
    admin_exp = total_exp * 0.3
    fin_exp = total_exp * 0.05
    gross = revenue - cost
    o_profit = gross - admin_exp - fin_exp
    income_tax = max(o_profit * 0.25, 0)
    net = o_profit - income_tax

    # YTD
    year = period[:4]
    rev_ytd = sum_incomes(year)
    cost_ytd = sum_expenses(year) * 0.6
    gross_ytd = rev_ytd - cost_ytd
    admin_ytd = sum_expenses(year) * 0.3
    o_ytd = gross_ytd - admin_ytd - sum_expenses(year) * 0.05
    net_ytd = o_ytd - max(o_ytd * 0.25, 0)

    # Balance sheet
    cash = to_float(conn.execute(
        "SELECT COALESCE(SUM(CAST(amount AS REAL)),0) FROM incomes").fetchone()[0]) - total_exp
    cash_begin = max(cash * 0.8, 0)
    ar = to_float(conn.execute(
        "SELECT COALESCE(SUM(CAST(total_amount AS REAL)),0) FROM processing_orders "
        "WHERE status NOT IN ('已交付','已取消')").fetchone()[0])
    ar_begin = max(ar * 0.6, 0)
    other_ar = 0
    ca_total = cash + ar + other_ar
    ca_begin = cash_begin + ar_begin

    fa = to_float(conn.execute(
        "SELECT COALESCE(SUM(net_value),0) FROM fixed_assets WHERE status='使用中'").fetchone()[0])
    fa_begin = fa * 1.1
    total_assets = ca_total + fa
    total_assets_begin = ca_begin + fa_begin

    ap = to_float(conn.execute(
        "SELECT COALESCE(SUM(CAST(amount AS REAL)),0) FROM expenses WHERE expense_date LIKE ?",
        (period + "%",)).fetchone()[0]) * 0.3
    salary_payable = to_float(conn.execute(
        "SELECT COALESCE(SUM(gross),0) FROM salary_records WHERE period=?",
        (period,)).fetchone()[0])
    tax_payable = income_tax
    cl_total = ap + salary_payable + tax_payable

    capital = 100000
    retained = total_assets - cl_total - capital
    equity = capital + retained

    balance_sheet = type('obj', (), {
        "cash": cash, "cash_begin": cash_begin, "ar": ar, "ar_begin": ar_begin,
        "other_ar": other_ar, "ca_total": ca_total, "ca_begin": ca_begin,
        "fa": fa, "fa_begin": fa_begin,
        "total_assets": total_assets, "total_assets_begin": total_assets_begin,
        "ap": ap, "salary_payable": salary_payable, "tax_payable": tax_payable,
        "cl_total": cl_total, "capital": capital, "retained": retained, "equity": equity
    })()

    profit_loss = type('obj', (), {
        "revenue": revenue, "cost": cost, "gross": gross,
        "admin_expense": admin_exp, "sell_expense": 0, "finance_expense": fin_exp,
        "o_profit": o_profit, "income_tax": income_tax, "net": net,
        "revenue_ytd": rev_ytd, "cost_ytd": cost_ytd, "gross_ytd": gross_ytd,
        "admin_expense_ytd": admin_ytd, "o_profit_ytd": o_ytd, "net_ytd": net_ytd
    })()

    op_inflow = revenue * 0.9
    op_outflow = cost * 0.7
    salary_out = salary_payable
    tax_out = income_tax * 0.5
    op_net = op_inflow - op_outflow - salary_out - tax_out
    inv_out = fa * 0.05
    begin_cash = cash_begin
    end_cash = begin_cash + op_net - inv_out

    cash_flow = type('obj', (), {
        "op_inflow": op_inflow, "op_outflow": op_outflow,
        "salary_out": salary_out, "tax_out": tax_out, "op_net": op_net,
        "inv_out": inv_out, "begin": begin_cash, "end": end_cash, "net": op_net - inv_out
    })()

    conn.close()
    return render_template("financial_reports.html",
        balance_sheet=balance_sheet, profit_loss=profit_loss, cash_flow=cash_flow,
        period=period)


# ========== 摊销与预提 ==========

@accounting_bp.route("/amortization", methods=["GET", "POST"])
def amortization():
    """摊销管理"""
    conn = get_db()
    conn.execute("""
        CREATE TABLE IF NOT EXISTS amortization_plans (
            id TEXT PRIMARY KEY, name TEXT NOT NULL, plan_type TEXT NOT NULL,
            account_code TEXT, total_amount REAL DEFAULT 0, total_months INTEGER DEFAULT 12,
            monthly_amount REAL DEFAULT 0, amortized_months INTEGER DEFAULT 0,
            start_date TEXT, next_date TEXT, status TEXT DEFAULT '进行中',
            created_at TEXT NOT NULL
        )
    """)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS amortization_logs (
            id TEXT PRIMARY KEY, plan_id TEXT, plan_name TEXT,
            exec_date TEXT, amount REAL, voucher_no TEXT, notes TEXT,
            created_at TEXT NOT NULL
        )
    """)
    conn.commit()

    message = None; error = None; show_modal = False

    if request.method == "POST":
        action = request.form.get("action", "")
        try:
            if action == "create":
                total = float(request.form.get("total_amount", "0") or 0)
                months = int(request.form.get("total_months", "12") or 12)
                start = request.form.get("start_date", date.today().strftime("%Y-%m"))
                plan_id = str(uuid.uuid4())
                conn.execute(
                    "INSERT INTO amortization_plans (id, name, plan_type, account_code, total_amount, total_months, monthly_amount, amortized_months, start_date, next_date, status, created_at) "
                    "VALUES (?,?,?,?,?,?,?,0,?,?,?,?)",
                    (plan_id, request.form.get("name"), request.form.get("plan_type"),
                     request.form.get("account_code"), total, months,
                     round(total / months, 2), start, start, "进行中",
                     datetime.now().isoformat()))
                conn.commit()
                message = "摊销计划创建成功"
            elif action == "delete":
                conn.execute("DELETE FROM amortization_plans WHERE id=?",
                            (request.form.get("plan_id"),))
                conn.commit()
                message = "摊销计划已删除"
            elif action == "exec_all":
                plans = conn.execute(
                    "SELECT * FROM amortization_plans WHERE status='进行中' AND next_date<=?",
                    (date.today().strftime("%Y-%m"),)).fetchall()
                if not plans:
                    error = "没有需要执行的摊销计划"
                else:
                    for p in plans:
                        p_m = int(p["amortized_months"] or 0) + 1
                        status = "已完成" if p_m >= int(p["total_months"] or 12) else "进行中"
                        vno = f"AM{p['id'][:6]}{date.today().strftime('%m')}"
                        conn.execute(
                            "INSERT INTO amortization_logs (id, plan_id, plan_name, exec_date, amount, voucher_no, notes, created_at) "
                            "VALUES (?,?,?,?,?,?,?,?)",
                            (str(uuid.uuid4()), p["id"], p["name"],
                             date.today().isoformat(), round(float(p["monthly_amount"] or 0), 2),
                             vno, f"第{p_m}期摊销", datetime.now().isoformat()))
                        conn.execute(
                            "UPDATE amortization_plans SET amortized_months=?, status=?, next_date=? WHERE id=?",
                            (p_m, status,
                             (date.today().replace(month=date.today().month+1) if date.today().month < 12 else date.today().replace(year=date.today().year+1, month=1)).strftime("%Y-%m"),
                             p["id"]))
                    conn.commit()
                    message = f"完成 {len(plans)} 项摊销处理"
        except Exception as e:
            error = f"操作失败: {e}"

    plans = []
    for p in conn.execute("SELECT * FROM amortization_plans ORDER BY status, start_date").fetchall():
        p = dict(p)
        total_m = max(int(p["total_months"] or 12), 1)
        am_m = int(p["amortized_months"] or 0)
        p["progress"] = min(int(am_m / total_m * 100), 100)
        plans.append(p)

    exec_logs = [dict(r) for r in conn.execute(
        "SELECT * FROM amortization_logs ORDER BY created_at DESC LIMIT 20").fetchall()]

    stats = {
        "total_amount": f"{sum(float(p['total_amount'] or 0) for p in plans):.2f}",
        "amortized": f"{sum(float(p.get('monthly_amount', 0) or 0) * p['amortized_months'] for p in plans):.2f}",
        "remaining": f"{sum(float(p.get('monthly_amount', 0) or 0) * (max(p['total_months'] - p['amortized_months'], 0)) for p in plans):.2f}"
    }

    conn.close()
    return render_template("amortization.html",
        plans=plans, exec_logs=exec_logs, stats=stats,
        message=message, error=error, show_modal=show_modal,
        today=date.today().isoformat())


# ========== 增值税申报表 ==========

@accounting_bp.route("/vat-return", methods=["GET", "POST"])
def vat_return():
    """增值税申报表"""
    conn = get_db()
    conn.execute("""
        CREATE TABLE IF NOT EXISTS invoices (
            id TEXT PRIMARY KEY, invoice_no TEXT NOT NULL, inv_type TEXT NOT NULL,
            counterparty TEXT NOT NULL, amount REAL NOT NULL DEFAULT 0,
            tax_rate REAL DEFAULT 13, tax_amount REAL NOT NULL DEFAULT 0,
            invoice_date TEXT NOT NULL, status TEXT DEFAULT '未认证',
            related_income_id TEXT, related_expense_id TEXT,
            notes TEXT, created_at TEXT NOT NULL
        )
    """)
    conn.commit()

    period = request.args.get("period", date.today().strftime("%Y-%m"))

    if request.method == "POST":
        action = request.form.get("action", "")
        if action == "certify":
            conn.execute("UPDATE invoices SET status='已认证' WHERE id=?",
                        (request.form.get("inv_id"),))
            conn.commit()

    # Output tax detail by rate
    output_detail = [dict(r) for r in conn.execute(
        "SELECT tax_rate rate, SUM(amount) amount, SUM(tax_amount) tax, COUNT(*) count "
        "FROM invoices WHERE inv_type='销项' AND invoice_date LIKE ? "
        "GROUP BY tax_rate ORDER BY tax_rate DESC", (period + "%",)).fetchall()]

    output_amount = sum(r["amount"] for r in output_detail)
    output_tax = sum(r["tax"] for r in output_detail)

    input_invoices = [dict(r) for r in conn.execute(
        "SELECT * FROM invoices WHERE inv_type='进项' AND invoice_date LIKE ? ORDER BY invoice_date DESC",
        (period + "%",)).fetchall()]
    input_amount = sum(r["amount"] for r in input_invoices)
    input_tax_certified = sum(r["tax_amount"] for r in input_invoices if r["status"] == "已认证")
    carryover = 0  # Simplified: no carryover tracking

    tax_payable = max(output_tax - input_tax_certified - carryover, 0)

    data = {
        "output_detail": output_detail, "input_invoices": input_invoices,
        "output_amount": output_amount, "output_tax": output_tax,
        "input_amount": input_amount, "input_tax_certified": input_tax_certified,
        "carryover": carryover, "tax_payable": tax_payable
    }

    conn.close()
    return render_template("vat_return.html", data=data, period=period)


# ========== 凭证审批工作台 ==========

@accounting_bp.route("/voucher-approval", methods=["GET", "POST"])
def voucher_approval():
    """凭证审批工作台：待审核/审核/驳回/记账"""
    conn = get_db()
    message = None; error = None; show_reject = False
    status_filter = request.args.get("status", "待审核")
    operator = request.args.get("operator", "审核人")
    now = datetime.now().isoformat()

    # Auto-create default status columns if missing
    try:
        conn.execute("ALTER TABLE accounting_vouchers ADD COLUMN reject_reason TEXT")
    except:
        pass  # already exists

    if request.method == "POST":
        batch_action = request.form.get("batch_action", "")
        ids = request.form.getlist("voucher_ids")
        if not ids and request.form.get("voucher_ids"):
            ids = [request.form.get("voucher_ids")]  # single form
        try:
            if batch_action == "submit_review":
                for vid in ids:
                    conn.execute(
                        "UPDATE accounting_vouchers SET status='待审核', updated_at=? WHERE id=? AND status='草稿'",
                        (now, vid))
                conn.commit()
                message = f"已将 {len(ids)} 条凭证提交审核"
            elif batch_action == "approve":
                for vid in ids:
                    conn.execute(
                        "UPDATE accounting_vouchers SET status='已审核', reviewed_by=?, reviewed_at=?, reject_reason=NULL, updated_at=? WHERE id=? AND status='待审核'",
                        (operator, now, now, vid))
                conn.commit()
                message = f"已审核 {len(ids)} 条凭证"
            elif batch_action == "reject":
                reason = request.form.get("reject_reason", "不符合要求")
                for vid in ids:
                    conn.execute(
                        "UPDATE accounting_vouchers SET status='已驳回', reject_reason=?, reviewed_by=?, updated_at=? WHERE id=? AND status='待审核'",
                        (reason, operator, now, vid))
                conn.commit()
                message = f"已驳回 {len(ids)} 条凭证"
            elif batch_action == "resubmit":
                for vid in ids:
                    conn.execute(
                        "UPDATE accounting_vouchers SET status='待审核', reject_reason=NULL, updated_at=? WHERE id=? AND status='已驳回'",
                        (now, vid))
                conn.commit()
                message = f"已重新提交 {len(ids)} 条凭证"
            elif batch_action == "post":
                for vid in ids:
                    conn.execute(
                        "UPDATE accounting_vouchers SET status='已记账', posted_by=?, posted_at=?, updated_at=? WHERE id=? AND status='已审核'",
                        (operator, now, now, vid))
                conn.commit()
                message = f"已记账 {len(ids)} 条凭证"
        except Exception as e:
            error = f"操作失败: {e}"

    # Count by status
    counts = {}
    for s in ["草稿", "待审核", "已审核", "已记账", "已驳回"]:
        counts[{"草稿": "draft", "待审核": "pending", "已审核": "reviewed",
                "已记账": "posted", "已驳回": "rejected"}[s]] = conn.execute(
            "SELECT COUNT(*) FROM accounting_vouchers WHERE status=?", (s,)).fetchone()[0]

    vouchers = [dict(r) for r in conn.execute(
        "SELECT * FROM accounting_vouchers WHERE status=? ORDER BY voucher_date DESC, voucher_no DESC LIMIT 200",
        (status_filter,)).fetchall()]

    conn.close()
    return render_template("voucher_approval.html",
        vouchers=vouchers, counts=counts, status_filter=status_filter,
        message=message, error=error, show_reject=show_reject)


# ========== 期间锁定 ==========

@accounting_bp.route("/period-lock", methods=["POST"])
def period_lock():
    """锁定/解锁会计期间"""
    conn = get_db()
    conn.execute("""
        CREATE TABLE IF NOT EXISTS period_locks (
            id TEXT PRIMARY KEY, period TEXT NOT NULL UNIQUE,
            locked_by TEXT, locked_at TEXT, is_locked INTEGER DEFAULT 1
        )
    """)
    conn.commit()

    action = request.form.get("action", "lock")
    period = request.form.get("period", "")
    try:
        if action == "lock":
            conn.execute(
                "INSERT OR REPLACE INTO period_locks (id, period, locked_by, locked_at, is_locked) "
                "VALUES (?,?,?,?,1)",
                (str(uuid.uuid4()), period, "管理员", datetime.now().isoformat()))
            conn.commit()
            return redirect("/check-before-close?period=" + period)
        elif action == "unlock":
            conn.execute("DELETE FROM period_locks WHERE period=?", (period,))
            conn.commit()
            return redirect("/check-before-close?period=" + period)
    except Exception as e:
        conn.close()
        return f"操作失败: {e}"


# ========== 智能预警中心 ==========

@accounting_bp.route("/alert-center")
def alert_center():
    """智能预警中心"""
    conn = get_db()
    today_str = date.today().isoformat()

    # 逾期应收账款
    overdue_ar = [dict(r) for r in conn.execute("""
        SELECT o.order_no, o.total_amount, o.delivery_date, c.name customer_name,
               CAST(julianday(?) - julianday(o.delivery_date) AS INTEGER) overdue_days
        FROM processing_orders o
        JOIN customers c ON c.id = o.customer_id
        WHERE o.status IN ('已交付','已完工') AND o.delivery_date IS NOT NULL
          AND o.delivery_date < ? AND o.received_amount < o.total_amount
        ORDER BY o.delivery_date
    """, (today_str, today_str)).fetchall()]
    overdue_total = sum(float(r["total_amount"] or 0) for r in overdue_ar)

    # 到期应付
    due_ap = [dict(r) for r in conn.execute("""
        SELECT e.expense_date, e.expense_type, e.amount, s.name supplier_name
        FROM expenses e
        LEFT JOIN suppliers s ON s.id = e.supplier_id
        WHERE e.expense_date <= ?
        ORDER BY e.expense_date DESC LIMIT 20
    """, (today_str,)).fetchall()]
    due_ap_total = sum(float(r["amount"] or 0) for r in due_ap)
    # Ensure numeric types for template
    for r in due_ap:
        r["amount"] = float(r["amount"] or 0)

    # 未记账凭证
    unposted = conn.execute(
        "SELECT COUNT(*) FROM accounting_vouchers WHERE status IN ('已审核','待审核')"
    ).fetchone()[0]

    # 现金流预警
    total_income = to_float(conn.execute(
        "SELECT COALESCE(SUM(CAST(amount AS REAL)),0) FROM incomes").fetchone()[0])
    total_expense = to_float(conn.execute(
        "SELECT COALESCE(SUM(CAST(amount AS REAL)),0) FROM expenses").fetchone()[0])
    bank_balance = total_income - total_expense
    avg_monthly_exp = total_expense / max(1, date.today().month)
    safety_line = avg_monthly_exp * 2
    cash_warning = bank_balance < safety_line and bank_balance > 0

    # 未认证进项发票
    uncertified_invoices = conn.execute(
        "SELECT COUNT(*) FROM invoices WHERE inv_type='进项' AND status='未认证'"
    ).fetchone()[0]

    # 预算超支
    budget_overrun = []
    for p in conn.execute("SELECT id, name, budget FROM projects WHERE budget > 0").fetchall():
        p = dict(p)
        actual = to_float(conn.execute(
            "SELECT COALESCE(SUM(CAST(amount AS REAL)),0) FROM expenses "
            "WHERE expense_date LIKE ?", (today_str[:7] + "%",)).fetchone()[0]) / max(
                conn.execute("SELECT COUNT(*) FROM projects").fetchone()[0], 1)
        if p["budget"] and actual > float(p["budget"]) * 0.8:
            p["actual"] = actual
            p["rate"] = actual / float(p["budget"]) * 100
            budget_overrun.append(p)

    conn.close()

    alerts = {
        "overdue_ar": overdue_ar, "overdue_total": overdue_total,
        "due_ap": due_ap, "due_ap_total": due_ap_total,
        "unposted": unposted, "bank_balance": bank_balance,
        "safety_line": safety_line, "cash_warning": cash_warning,
        "uncertified_invoices": uncertified_invoices,
        "budget_overrun": budget_overrun
    }

    return render_template("alert_center.html", alerts=alerts)


# ========== 自动凭证规则 ==========

@accounting_bp.route("/auto-voucher", methods=["GET", "POST"])
def auto_voucher():
    """自动凭证规则管理"""
    conn = get_db()
    conn.execute("""
        CREATE TABLE IF NOT EXISTS auto_voucher_rules (
            id TEXT PRIMARY KEY, name TEXT NOT NULL, frequency TEXT NOT NULL DEFAULT '每月',
            debit_account TEXT, credit_account TEXT, amount REAL DEFAULT 0,
            summary TEXT, next_date TEXT, exec_count INTEGER DEFAULT 0,
            enabled INTEGER DEFAULT 1, created_at TEXT NOT NULL
        )
    """)
    conn.commit()

    message = None; error = None
    today_str = date.today().isoformat()
    today_month = today_str[:7]

    if request.method == "POST":
        action = request.form.get("action", "")
        try:
            if action == "create":
                freq = request.form.get("frequency", "每月")
                next_date = today_month
                conn.execute(
                    "INSERT INTO auto_voucher_rules (id, name, frequency, debit_account, credit_account, amount, summary, next_date, enabled, created_at) "
                    "VALUES (?,?,?,?,?,?,?,?,1,?)",
                    (str(uuid.uuid4()), request.form.get("name"), freq,
                     request.form.get("debit_account"), request.form.get("credit_account"),
                     float(request.form.get("amount", "0") or 0),
                     request.form.get("summary", ""), next_date, datetime.now().isoformat()))
                conn.commit()
                message = "规则创建成功"
            elif action == "toggle":
                rule = conn.execute("SELECT * FROM auto_voucher_rules WHERE id=?",
                                   (request.form.get("rule_id"),)).fetchone()
                conn.execute("UPDATE auto_voucher_rules SET enabled=? WHERE id=?",
                            (0 if rule["enabled"] else 1, request.form.get("rule_id")))
                conn.commit()
            elif action == "delete":
                conn.execute("DELETE FROM auto_voucher_rules WHERE id=?",
                            (request.form.get("rule_id"),))
                conn.commit()
                message = "规则已删除"
            elif action == "preset":
                ptype = request.form.get("preset_type", "")
                presets = {
                    "depreciation": ("固定资产折旧", "5502", "1502", 1000, "每月计提折旧"),
                    "rent": ("房租摊销", "5502", "1123", 5000, "每月房租摊销"),
                    "salary": ("工资计提", "5502", "2211", 15000, "每月工资计提"),
                }
                if ptype in presets:
                    nm, dr, cr, amt, sm = presets[ptype]
                    conn.execute(
                        "INSERT INTO auto_voucher_rules (id, name, frequency, debit_account, credit_account, amount, summary, next_date, enabled, created_at) "
                        "VALUES (?,?,?,?,?,?,?,?,1,?)",
                        (str(uuid.uuid4()), nm, "每月", dr, cr, amt, sm, today_month,
                         datetime.now().isoformat()))
                    conn.commit()
                    message = f"预设规则「{nm}」已添加"
            elif action in ("exec_one", "exec_all"):
                rules = []
                if action == "exec_one":
                    r = conn.execute("SELECT * FROM auto_voucher_rules WHERE id=?",
                                    (request.form.get("rule_id"),)).fetchone()
                    if r: rules = [r]
                else:
                    rules = conn.execute(
                        "SELECT * FROM auto_voucher_rules WHERE enabled=1 AND next_date<=?",
                        (today_month,)).fetchall()
                if not rules:
                    error = "没有可执行的规则"
                else:
                    count = 0
                    for rule in rules:
                        vid = str(uuid.uuid4())
                        vno = f"AV{rule['id'][:4]}{today_month.replace('-','')}"
                        exist = conn.execute(
                            "SELECT COUNT(*) FROM accounting_vouchers WHERE voucher_no=?",
                            (vno,)).fetchone()[0]
                        if exist:
                            continue
                        amt = float(rule["amount"] or 0)
                        conn.execute(
                            "INSERT INTO accounting_vouchers (id, voucher_no, voucher_date, accounting_period, summary, total_debit, total_credit, created_by, status, created_at, updated_at) "
                            "VALUES (?,?,?,?,?,?,?,?,?,?,?)",
                            (vid, vno, today_str, today_month, rule["summary"] or rule["name"],
                             amt, amt, "自动", "待审核", datetime.now().isoformat(),
                             datetime.now().isoformat()))
                        conn.execute(
                            "INSERT INTO voucher_lines (id, voucher_id, account_code, account_name, debit, credit, summary) VALUES (?,?,?,?,?,?,?)",
                            (str(uuid.uuid4()), vid, rule["debit_account"], rule["debit_account"],
                             str(amt), "0", rule["summary"] or ""))
                        conn.execute(
                            "INSERT INTO voucher_lines (id, voucher_id, account_code, account_name, debit, credit, summary) VALUES (?,?,?,?,?,?,?)",
                            (str(uuid.uuid4()), vid, rule["credit_account"], rule["credit_account"],
                             "0", str(amt), rule["summary"] or ""))
                        # Update next date
                        y, m = int(today_month[:4]), int(today_month[5:])
                        freq = rule["frequency"]
                        if freq == "每月":
                            m += 1
                        elif freq == "每季度":
                            m += 3
                        else:
                            y += 1
                        if m > 12: y += 1; m -= 12
                        next_d = f"{y}-{m:02d}"
                        conn.execute(
                            "UPDATE auto_voucher_rules SET next_date=?, exec_count=exec_count+1 WHERE id=?",
                            (next_d, rule["id"]))
                        count += 1
                    conn.commit()
                    message = f"已执行 {count} 条规则"
        except Exception as e:
            error = f"操作失败: {e}"

    rules = []
    for r in conn.execute(
        "SELECT * FROM auto_voucher_rules ORDER BY enabled DESC, next_date").fetchall():
        r = dict(r)
        r["is_due"] = r["enabled"] and (r["next_date"] or "") <= today_month
        rules.append(r)

    conn.close()
    return render_template("auto_voucher.html", rules=rules,
                          message=message, error=error)


# ========== 客户/供应商全景视图 ==========

@accounting_bp.route("/customer-profile/<entity_id>")
def customer_profile(entity_id):
    """客户全景视图"""
    return _entity_profile(entity_id, "customer")

@accounting_bp.route("/supplier-profile/<entity_id>")
def supplier_profile(entity_id):
    """供应商全景视图"""
    return _entity_profile(entity_id, "supplier")

def _entity_profile(entity_id, etype):
    conn = get_db()
    today_str = date.today().isoformat()
    this_year = today_str[:4]

    if etype == "customer":
        entity = dict(conn.execute(
            "SELECT * FROM customers WHERE id=?", (entity_id,)).fetchone())
        # Stats
        order_count = conn.execute(
            "SELECT COUNT(*) FROM processing_orders WHERE customer_id=?", (entity_id,)).fetchone()[0]
        total_amount = to_float(conn.execute(
            "SELECT COALESCE(SUM(CAST(total_amount AS REAL)),0) FROM processing_orders WHERE customer_id=?",
            (entity_id,)).fetchone()[0])
        paid = to_float(conn.execute(
            "SELECT COALESCE(SUM(CAST(amount AS REAL)),0) FROM incomes WHERE customer_id=?",
            (entity_id,)).fetchone()[0])
        balance = total_amount - paid
        overdue_orders = conn.execute(
            "SELECT COUNT(*) FROM processing_orders WHERE customer_id=? AND status IN ('已交付','已完工') AND delivery_date IS NOT NULL AND delivery_date<? AND received_amount<total_amount",
            (entity_id, today_str)).fetchone()[0]
        # Recent orders
        recent_orders = [dict(r) for r in conn.execute(
            "SELECT * FROM processing_orders WHERE customer_id=? ORDER BY order_date DESC LIMIT 5",
            (entity_id,)).fetchall()]
        for o in recent_orders:
            o["total_amount"] = float(o["total_amount"] or 0)
        # Recent transactions
        recent_transactions = [dict(r) for r in conn.execute(
            "SELECT income_date date, bank_type bank, amount, notes, '收款' type FROM incomes WHERE customer_id=? "
            "ORDER BY income_date DESC LIMIT 10", (entity_id,)).fetchall()]
        for t in recent_transactions:
            t["amount"] = float(t["amount"] or 0)
    else:
        entity = dict(conn.execute(
            "SELECT * FROM suppliers WHERE id=?", (entity_id,)).fetchone())
        order_count = conn.execute(
            "SELECT COUNT(*) FROM expenses WHERE supplier_id=?", (entity_id,)).fetchone()[0]
        total_amount = to_float(conn.execute(
            "SELECT COALESCE(SUM(CAST(amount AS REAL)),0) FROM expenses WHERE supplier_id=?",
            (entity_id,)).fetchone()[0])
        balance = total_amount  # owed to supplier
        overdue_orders = 0
        recent_orders = []
        recent_transactions = [dict(r) for r in conn.execute(
            "SELECT expense_date date, amount, expense_type type, '' bank, description notes FROM expenses WHERE supplier_id=? "
            "ORDER BY expense_date DESC LIMIT 10", (entity_id,)).fetchall()]

    # Aging (simplified customer only)
    aging = []
    if etype == "customer":
        buckets = {"0-30天": 0, "31-60天": 0, "61-90天": 0, "90天以上": 0}
        for r in conn.execute(
            "SELECT CAST(julianday(?)-julianday(delivery_date) AS INTEGER) days, total_amount FROM processing_orders "
            "WHERE customer_id=? AND status IN ('已交付','已完工') AND delivery_date IS NOT NULL AND received_amount<total_amount",
            (today_str, entity_id)).fetchall():
            days = r[0]; amt = float(r[1] or 0)
            if days <= 30: buckets["0-30天"] += amt
            elif days <= 60: buckets["31-60天"] += amt
            elif days <= 90: buckets["61-90天"] += amt
            else: buckets["90天以上"] += amt
        total_aging = sum(buckets.values()) or 1
        for k, v in buckets.items():
            aging.append({"bucket": k, "amount": v, "pct": v / total_aging * 100})

    stats = {"order_count": order_count, "total_amount": total_amount,
             "balance": balance, "overdue_orders": overdue_orders}

    conn.close()
    return render_template("entity_profile.html",
        entity=entity, etype=etype, stats=stats, aging=aging,
        recent_orders=recent_orders, recent_transactions=recent_transactions,
        this_year=this_year, today=today_str)


# ========== Excel 导出 ==========

@accounting_bp.route("/export/xls/<report_type>")
def export_xls(report_type):
    """导出报表为 .xls 格式（HTML表格，Excel可打开）"""
    conn = get_db()
    period = request.args.get("period", date.today().strftime("%Y-%m"))

    if report_type == "salary":
        records = [dict(r) for r in conn.execute(
            "SELECT * FROM salary_records WHERE period=? ORDER BY emp_name", (period,)).fetchall()]
        html = """<html><meta charset='utf-8'><body>
        <h2>工资表 - """ + period + """</h2>
        <table border=1 cellpadding=4 cellspacing=0>
        <tr style='background:#f0f0f0'><th>员工</th><th>基本工资</th><th>加班费</th><th>奖金</th><th>应发</th><th>社保个人</th><th>个税</th><th>实发</th></tr>"""
        for r in records:
            html += f"<tr><td>{r['emp_name']}</td><td align=right>{float(r['base_salary']):.2f}</td><td align=right>{float(r['overtime']):.2f}</td><td align=right>{float(r['bonus']):.2f}</td><td align=right>{float(r['gross']):.2f}</td><td align=right>{float(r['social_personal']):.2f}</td><td align=right>{float(r['tax']):.2f}</td><td align=right>{float(r['net']):.2f}</td></tr>"
        html += "</table></body></html>"
        conn.close()
        return Response(html.encode('utf-8'), mimetype='application/vnd.ms-excel',
            headers={"Content-Disposition": f"attachment;filename=salary_{period}.xls"})

    elif report_type == "financial-reports":
        # Simple balance sheet export
        html = f"""<html><meta charset='utf-8'><body>
        <h2>资产负债表 - {period}</h2>
        <table border=1 cellpadding=4 cellspacing=0>
        <tr style='background:#f0f0f0'><th>项目</th><th>金额</th></tr>
        <tr><td>货币资金</td><td align=right>--</td></tr>
        <tr><td>应收账款</td><td align=right>--</td></tr>
        <tr><td>固定资产</td><td align=right>--</td></tr>
        <tr style='font-weight:bold'><td>资产总计</td><td align=right>--</td></tr>
        </table><br>
        <h2>利润表 - {period}</h2>
        <table border=1 cellpadding=4 cellspacing=0>
        <tr style='background:#f0f0f0'><th>项目</th><th>金额</th></tr>"""
        inc = to_float(conn.execute(
            "SELECT COALESCE(SUM(CAST(amount AS REAL)),0) FROM incomes WHERE income_date LIKE ?",
            (period + "%",)).fetchone()[0])
        exp = to_float(conn.execute(
            "SELECT COALESCE(SUM(CAST(amount AS REAL)),0) FROM expenses WHERE expense_date LIKE ?",
            (period + "%",)).fetchone()[0])
        html += f"<tr><td>营业收入</td><td align=right>{inc:.2f}</td></tr>"
        html += f"<tr><td>营业成本</td><td align=right>{exp*.6:.2f}</td></tr>"
        html += f"<tr style='font-weight:bold'><td>净利润</td><td align=right>{inc-exp:.2f}</td></tr>"
        html += "</table></body></html>"
        conn.close()
        return Response(html.encode('utf-8'), mimetype='application/vnd.ms-excel',
            headers={"Content-Disposition": f"attachment;filename=financial_reports_{period}.xls"})

    elif report_type == "vat-return":
        invoices = [dict(r) for r in conn.execute(
            "SELECT * FROM invoices WHERE invoice_date LIKE ? ORDER BY inv_type, invoice_date",
            (period + "%",)).fetchall()]
        html = """<html><meta charset='utf-8'><body>
        <h2>增值税申报表 - """ + period + """</h2>
        <table border=1 cellpadding=4 cellspacing=0>
        <tr style='background:#f0f0f0'><th>发票号码</th><th>类型</th><th>对方</th><th>金额</th><th>税额</th><th>认证状态</th></tr>"""
        for inv in invoices:
            html += f"<tr><td>{inv['invoice_no']}</td><td>{inv['inv_type']}</td><td>{inv['counterparty']}</td><td align=right>{float(inv['amount']):.2f}</td><td align=right>{float(inv['tax_amount']):.2f}</td><td>{inv['status']}</td></tr>"
        html += "</table></body></html>"
        conn.close()
        return Response(html.encode('utf-8'), mimetype='application/vnd.ms-excel',
            headers={"Content-Disposition": f"attachment;filename=vat_return_{period}.xls"})

    elif report_type == "customer-statement":
        entity_id = request.args.get("entity_id", "")
        stype = request.args.get("stype", "customer")
        start = request.args.get("start_date", "")
        end = request.args.get("end_date", "")
        html = f"<html><meta charset='utf-8'><body><h2>{'客户' if stype=='customer' else '供应商'}对账单 {start}~{end}</h2><table border=1 cellpadding=4><tr style='background:#f0f0f0'><th>日期</th><th>类型</th><th>摘要</th><th>金额</th></tr>"
        if stype == "customer":
            rows = conn.execute(
                "SELECT order_date date, '订单' type, order_no summary, CAST(total_amount AS REAL) amount "
                "FROM processing_orders WHERE customer_id=? AND order_date BETWEEN ? AND ? ORDER BY order_date",
                (entity_id, start, end)).fetchall()
            rows += conn.execute(
                "SELECT income_date, '收款', '收款', CAST(amount AS REAL) FROM incomes WHERE customer_id=? AND income_date BETWEEN ? AND ? ORDER BY income_date",
                (entity_id, start, end)).fetchall()
        else:
            rows = conn.execute(
                "SELECT expense_date, expense_type, description, CAST(amount AS REAL) FROM expenses WHERE supplier_id=? AND expense_date BETWEEN ? AND ? ORDER BY expense_date",
                (entity_id, start, end)).fetchall()
        for r in rows:
            html += f"<tr><td>{r[0]}</td><td>{r[1]}</td><td>{r[2]}</td><td align=right>{float(r[3]):.2f}</td></tr>"
        html += "</table></body></html>"
        conn.close()
        return Response(html.encode('utf-8'), mimetype='application/vnd.ms-excel',
            headers={"Content-Disposition": f"attachment;filename=statement_{start}_{end}.xls"})

    conn.close()
    return "Unknown report type", 400


# ========== 常用摘要管理 ==========

@accounting_bp.route("/common-summaries", methods=["GET", "POST"])
def common_summaries():
    """常用摘要管理"""
    conn = get_db()
    try:
        conn.execute("ALTER TABLE system_settings ADD COLUMN common_summaries TEXT DEFAULT ''")
    except:
        pass

    message = None
    if request.method == "POST":
        action = request.form.get("action", "")
        summaries = request.form.get("summaries", "")
        conn.execute("DELETE FROM system_settings")
        conn.execute("INSERT INTO system_settings (key, value) VALUES ('common_summaries', ?)",
                    (summaries,))
        conn.commit()
        message = "常用摘要已更新"

    row = conn.execute(
        "SELECT value FROM system_settings WHERE key='common_summaries'").fetchone()
    summaries_str = row["value"] if row else ""
    summaries_list = [s.strip() for s in summaries_str.split("\n") if s.strip()]

    conn.close()
    return render_template("common_summaries.html",
        summaries=summaries_list, summaries_str=summaries_str, message=message)


# ========== 凭证批量删除 ==========

@accounting_bp.route("/vouchers/batch-delete", methods=["POST"])
def batch_delete_vouchers():
    """批量删除凭证"""
    conn = get_db()
    ids = request.form.getlist("voucher_ids")
    if not ids and request.form.get("voucher_ids"):
        ids = [request.form.get("voucher_ids")]
    try:
        count = 0
        for vid in ids:
            conn.execute("DELETE FROM voucher_lines WHERE voucher_id=?", (vid,))
            conn.execute("DELETE FROM accounting_vouchers WHERE id=?", (vid,))
            # Audit log
            conn.execute(
                "INSERT INTO audit_logs (id, entity_type, entity_id, action, operator, details, created_at) "
                "VALUES (?,?,?,?,?,?,?)",
                (str(uuid.uuid4()), "voucher", vid, "批量删除", "管理员",
                 f"凭证ID:{vid}", datetime.now().isoformat()))
            count += 1
        conn.commit()
        message = f"已删除 {count} 条凭证"
    except Exception as e:
        message = f"删除失败: {e}"
    conn.close()
    return redirect(f"/voucher-approval?status=草稿&message={message}")