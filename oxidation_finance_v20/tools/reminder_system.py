#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
智能提醒系统 - 自动生成催款通知和待办提醒
"""

import sys
import io

# Windows编码支持
if sys.platform == "win32":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")

from pathlib import Path
from datetime import date, datetime, timedelta
import sqlite3


class ReminderSystem:
    def __init__(self):
        base_dir = Path(__file__).resolve().parent.parent
        self.db_path = base_dir / "oxidation_finance_demo_ready.db"
        if not self.db_path.exists():
            self.db_path = base_dir / "oxidation_finance_demo.db"

    def get_connection(self):
        conn = sqlite3.connect(str(self.db_path))
        conn.row_factory = sqlite3.Row
        return conn

    def get_daily_summary(self):
        conn = self.get_connection()
        today = date.today().isoformat()
        yesterday = (date.today() - timedelta(days=1)).isoformat()

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
        pending = (
            conn.execute(
                "SELECT COUNT(*) FROM processing_orders WHERE status IN ('待加工', '加工中')"
            ).fetchone()[0]
            or 0
        )
        unpaid = (
            conn.execute(
                "SELECT COUNT(*) FROM processing_orders WHERE received_amount < total_amount"
            ).fetchone()[0]
            or 0
        )

        conn.close()

        print("\n" + "=" * 70)
        print("每日汇总")
        print("=" * 70)
        print(f"\n日期: {date.today().strftime('%Y-%m-%d')}")
        print(f"今日收入: {today_income:,.2f}")
        print(f"今日支出: {today_expense:,.2f}")
        print(f"今日利润: {today_income - today_expense:,.2f}")
        print(f"\n待加工订单: {pending}个")
        print(f"未收款订单: {unpaid}个")

    def get_pending_reminders(self):
        conn = self.get_connection()
        today = date.today().isoformat()

        # 超期订单
        pending = conn.execute(
            """
            SELECT order_no, customer_name, total_amount, status,
                   JULIANDAY(?) - JULIANDAY(order_date) as days
            FROM processing_orders
            WHERE status IN ('待加工', '加工中')
            AND JULIANDAY(?) - JULIANDAY(order_date) > 3
            ORDER BY days DESC
            LIMIT 10
        """,
            (today, today),
        ).fetchall()

        if pending:
            print("\n[!] 待处理订单提醒")
            print("-" * 70)
            for o in pending:
                print(
                    f"  {o['order_no']} {o['customer_name'][:10]} {o['total_amount']:>8,.0f} {o['status']} 已{int(o['days'])}天"
                )

        conn.close()
        return len(pending)

    def get_unpaid_reminders(self):
        conn = self.get_connection()

        unpaid = conn.execute("""
            SELECT order_no, customer_name, (total_amount - received_amount) as unpaid,
                   delivery_date
            FROM processing_orders
            WHERE received_amount < total_amount
            ORDER BY unpaid DESC
            LIMIT 10
        """).fetchall()

        if unpaid:
            print("\n[!] 未收款提醒")
            print("-" * 70)
            total = 0
            for o in unpaid:
                print(
                    f"  {o['order_no']} {o['customer_name'][:10]} {o['unpaid']:>8,.0f}"
                )
                total += o["unpaid"]
            print(f"\n  未收款总额: {total:,.2f}")

        conn.close()
        return len(unpaid)

    def generate_collection_letters(self):
        conn = self.get_connection()

        overdue = conn.execute("""
            SELECT c.name, c.contact, SUM(o.total_amount - o.received_amount) as total,
                   COUNT(o.id) as count
            FROM customers c
            JOIN processing_orders o ON c.id = o.customer_id
            WHERE o.status = '已交付' AND o.received_amount < o.total_amount
            GROUP BY c.id
            HAVING total > 5000
            ORDER BY total DESC
        """).fetchall()

        if overdue:
            print("\n[!] 催款通知")
            print("=" * 70)
            for c in overdue[:3]:
                print(f"\n致: {c['name']} {c['contact']}")
                print(f"  贵司尚有 {c['total']:,.2f} 未结清（{c['count']}笔订单）")
                print(f"  请于7日内安排付款。")

        conn.close()

    def run(self):
        print("\n" + "=" * 70)
        print("智能提醒系统")
        print("=" * 70)

        self.get_daily_summary()
        self.get_pending_reminders()
        self.get_unpaid_reminders()
        self.generate_collection_letters()

        print("\n" + "=" * 70)
        print("提醒完成")
        print("=" * 70)


def main():
    r = ReminderSystem()
    if not r.db_path.exists():
        print("数据库不存在")
        return
    r.run()


if __name__ == "__main__":
    main()
