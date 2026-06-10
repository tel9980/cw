#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""会计路由：科目管理、凭证管理、账簿查询"""

import csv
import io
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

    banks = [dict(b) for b in conn.execute(
        "SELECT DISTINCT bank_type FROM bank_accounts UNION SELECT DISTINCT bank_type FROM bank_transactions"
    ).fetchall()]

    conn.close()
    return render_template("system_settings.html", settings=settings,
                           banks=banks, message=message, error=error,
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
        cursor.execute(
            "SELECT COUNT(*) FROM accounting_vouchers WHERE accounting_period=?",
            (period,))
        seq = cursor.fetchone()[0] + 1
        voucher_no = f"{period}-{seq:03d}"
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
    seq = cursor.execute(
        "SELECT COUNT(*) FROM accounting_vouchers WHERE accounting_period=?", (period,)
    ).fetchone()[0] + 1
    voucher_no = f"{period}-ZJ{seq:03d}"
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
    seq = conn.execute("SELECT COUNT(*) FROM accounting_vouchers WHERE accounting_period=?",
                       (orig["accounting_period"],)).fetchone()[0] + 1
    voucher_no = f"{orig['accounting_period']}-{seq:03d}"

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