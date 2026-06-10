#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""辅助路由：AI助手、API接口"""

import re
from datetime import date
from flask import Blueprint, render_template, request, jsonify

from routes.helpers import get_db, to_float

assistant_bp = Blueprint('assistant', __name__)


@assistant_bp.route("/assistant", methods=["GET", "POST"])
def assistant():
    """AI助手页面"""
    conn = get_db()
    question = request.args.get("q", "")
    answer = ""

    if request.method == "POST":
        question = request.form.get("question", "")
        answer = process_question(conn, question)

    conn.close()
    return render_template("assistant.html", question=question, answer=answer)


def process_question(conn, question):
    """AI助手 - 处理自然语言查询"""
    q = question.lower()

    # 收入查询
    if any(kw in q for kw in ["收入", "收款", "进账"]):
        if "月" in q:
            m = re.search(r"(\d{4})-?(\d{1,2})", q)
            if m:
                year, month = m.group(1), m.group(2).zfill(2)
                total = conn.execute(
                    "SELECT SUM(CAST(amount AS REAL)) FROM incomes WHERE income_date LIKE ?",
                    (f"{year}-{month}%",)).fetchone()[0] or 0
                return f"{year}年{month}月总收入：{to_float(total):,.2f} 元"
        total = conn.execute("SELECT SUM(CAST(amount AS REAL)) FROM incomes WHERE income_date = ?",
                             (date.today().isoformat(),)).fetchone()[0] or 0
        return f"今日收入：{to_float(total):,.2f} 元"

    # 支出查询
    if any(kw in q for kw in ["支出", "付款", "花费", "费用"]):
        if "月" in q:
            m = re.search(r"(\d{4})-?(\d{1,2})", q)
            if m:
                year, month = m.group(1), m.group(2).zfill(2)
                total = conn.execute(
                    "SELECT SUM(CAST(amount AS REAL)) FROM expenses WHERE expense_date LIKE ?",
                    (f"{year}-{month}%",)).fetchone()[0] or 0
                return f"{year}年{month}月总支出：{to_float(total):,.2f} 元"
        total = conn.execute("SELECT SUM(CAST(amount AS REAL)) FROM expenses WHERE expense_date = ?",
                             (date.today().isoformat(),)).fetchone()[0] or 0
        return f"今日支出：{to_float(total):,.2f} 元"

    # 订单查询
    if any(kw in q for kw in ["订单", "生产"]):
        pending = conn.execute(
            "SELECT COUNT(*) FROM processing_orders WHERE status IN ('待加工','加工中')").fetchone()[0] or 0
        return f"当前待处理订单：{pending} 个"

    # 利润查询
    if any(kw in q for kw in ["利润", "赚", "盈利"]):
        month_start = date.today().replace(day=1).isoformat()
        income = to_float(conn.execute(
            "SELECT SUM(CAST(amount AS REAL)) FROM incomes WHERE income_date >= ?",
            (month_start,)).fetchone()[0])
        expense = to_float(conn.execute(
            "SELECT SUM(CAST(amount AS REAL)) FROM expenses WHERE expense_date >= ?",
            (month_start,)).fetchone()[0])
        return f"本月利润：{income - expense:,.2f} 元（收入 {income:,.2f} - 支出 {expense:,.2f}）"

    return "您好！我是财务助手。请问关于收入、支出、订单或利润的问题。"


@assistant_bp.route("/api/search")
def api_search():
    """全局搜索API"""
    conn = get_db()
    query = request.args.get("q", "").strip()
    if not query or len(query) < 2:
        conn.close()
        return jsonify({"results": []})

    results = []
    param = f"%{query}%"

    # 搜索订单
    orders = conn.execute(
        "SELECT id, order_no, customer_name, CAST(total_amount AS REAL) as total_amount, status FROM processing_orders WHERE order_no LIKE ? OR customer_name LIKE ? LIMIT 10",
        (param, param)).fetchall()
    for o in orders:
        results.append({"type": "订单", "id": o["id"], "title": f"{o['order_no']} ({o['customer_name']})",
                        "subtitle": f"{to_float(o['total_amount']):,.2f} 元 | {o['status']}", "url": "/orders"})

    # 搜索客户
    customers = conn.execute(
        "SELECT id, name FROM customers WHERE name LIKE ? LIMIT 5", (param,)).fetchall()
    for c in customers:
        results.append({"type": "客户", "id": c["id"], "title": c["name"], "subtitle": "", "url": "/customers"})

    # 搜索科目
    accounts = conn.execute(
        "SELECT id, code, name, account_type FROM chart_of_accounts WHERE code LIKE ? OR name LIKE ? LIMIT 10",
        (param, param)).fetchall()
    for a in accounts:
        results.append({"type": "会计科目", "id": a["id"], "title": f"{a['code']} - {a['name']}",
                        "subtitle": a["account_type"], "url": "/chart-of-accounts"})

    # 搜索凭证
    vouchers = conn.execute(
        "SELECT id, voucher_no, summary, status FROM accounting_vouchers WHERE voucher_no LIKE ? OR summary LIKE ? LIMIT 5",
        (param, param)).fetchall()
    for v in vouchers:
        results.append({"type": "会计凭证", "id": v["id"], "title": v["voucher_no"],
                        "subtitle": f"{v.get('summary','')} | {v['status']}", "url": f"/vouchers/{v['id']}"})

    conn.close()
    return jsonify({"results": results[:20]})


@assistant_bp.route("/api/stats")
def api_stats():
    """数据统计API"""
    conn = get_db()
    today = date.today().isoformat()
    month_start = date.today().replace(day=1).isoformat()

    stats = {
        "today": {
            "income": to_float(conn.execute("SELECT SUM(CAST(amount AS REAL)) FROM incomes WHERE income_date = ?", (today,)).fetchone()[0]),
            "expense": to_float(conn.execute("SELECT SUM(CAST(amount AS REAL)) FROM expenses WHERE expense_date = ?", (today,)).fetchone()[0]),
        },
        "month": {
            "income": to_float(conn.execute("SELECT SUM(CAST(amount AS REAL)) FROM incomes WHERE income_date >= ?", (month_start,)).fetchone()[0]),
            "expense": to_float(conn.execute("SELECT SUM(CAST(amount AS REAL)) FROM expenses WHERE expense_date >= ?", (month_start,)).fetchone()[0]),
        },
        "orders": {
            "total": conn.execute("SELECT COUNT(*) FROM processing_orders").fetchone()[0] or 0,
            "pending": conn.execute("SELECT COUNT(*) FROM processing_orders WHERE status IN ('待加工','加工中')").fetchone()[0] or 0,
        },
        "accounting": {
            "voucher_total": conn.execute("SELECT COUNT(*) FROM accounting_vouchers").fetchone()[0] or 0,
            "voucher_posted": conn.execute("SELECT COUNT(*) FROM accounting_vouchers WHERE status='已记账'").fetchone()[0] or 0,
            "account_count": conn.execute("SELECT COUNT(*) FROM chart_of_accounts WHERE is_active=1").fetchone()[0] or 0,
        },
    }
    conn.close()
    return jsonify(stats)


@assistant_bp.route("/api-docs")
def api_docs():
    """API文档页面"""
    import flask
    routes = []
    for rule in sorted(flask.current_app.url_map.iter_rules(), key=lambda r: r.rule):
        if rule.rule.startswith("/api"):
            routes.append({
                "endpoint": rule.rule,
                "methods": ",".join(sorted(rule.methods - {"HEAD", "OPTIONS"})),
            })
    return render_template("api_docs.html", routes=routes)