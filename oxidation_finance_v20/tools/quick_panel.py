#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
快捷面板 - 日常工作效率提升工具

功能：
- 今日概览
- 快捷操作
- 快速统计
- 提醒事项
"""

import sys
import io

# Windows编码支持
if sys.platform == "win32":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")

from pathlib import Path
from datetime import date, datetime, timedelta
from decimal import Decimal
import sqlite3


class QuickPanel:
    def __init__(self):
        base_dir = Path(__file__).resolve().parent.parent
        self.db_path = base_dir / "oxidation_finance_demo_ready.db"
        if not self.db_path.exists():
            alt_db = Path(__file__).parent / "oxidation_finance_demo_ready.db"
            if alt_db.exists():
                self.db_path = alt_db
            else:
                demo_db = base_dir / "oxidation_finance_demo.db"
                if demo_db.exists():
                    self.db_path = demo_db

    def get_connection(self):
        conn = sqlite3.connect(str(self.db_path))
        conn.row_factory = sqlite3.Row
        return conn

    def get_today_stats(self):
        conn = self.get_connection()
        today = date.today().isoformat()
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
        today_orders = (
            conn.execute(
                "SELECT COUNT(*) FROM processing_orders WHERE order_date = ?", (today,)
            ).fetchone()[0]
            or 0
        )
        conn.close()
        return {
            "today_income": today_income,
            "today_expense": today_expense,
            "today_orders": today_orders,
            "today_profit": today_income - today_expense,
        }

    def get_week_stats(self):
        conn = self.get_connection()
        today = date.today()
        week_start = (today - timedelta(days=today.weekday())).isoformat()
        week_income = (
            conn.execute(
                "SELECT SUM(amount) FROM incomes WHERE income_date >= ?", (week_start,)
            ).fetchone()[0]
            or 0
        )
        week_expense = (
            conn.execute(
                "SELECT SUM(amount) FROM expenses WHERE expense_date >= ?",
                (week_start,),
            ).fetchone()[0]
            or 0
        )
        week_orders = (
            conn.execute(
                "SELECT COUNT(*) FROM processing_orders WHERE order_date >= ?",
                (week_start,),
            ).fetchone()[0]
            or 0
        )
        conn.close()
        return {
            "week_income": week_income,
            "week_expense": week_expense,
            "week_orders": week_orders,
            "week_profit": week_income - week_expense,
        }

    def get_month_stats(self):
        conn = self.get_connection()
        month_start = date.today().replace(day=1).isoformat()
        month_income = (
            conn.execute(
                "SELECT SUM(amount) FROM incomes WHERE income_date >= ?", (month_start,)
            ).fetchone()[0]
            or 0
        )
        month_expense = (
            conn.execute(
                "SELECT SUM(amount) FROM expenses WHERE expense_date >= ?",
                (month_start,),
            ).fetchone()[0]
            or 0
        )
        month_orders = (
            conn.execute(
                "SELECT COUNT(*) FROM processing_orders WHERE order_date >= ?",
                (month_start,),
            ).fetchone()[0]
            or 0
        )
        conn.close()
        return {
            "month_income": month_income,
            "month_expense": month_expense,
            "month_orders": month_orders,
            "month_profit": month_income - month_expense,
        }

    def get_pending_orders(self):
        conn = self.get_connection()
        orders = conn.execute(
            """SELECT order_no, customer_name, item_description, total_amount, order_date FROM processing_orders WHERE status IN ('待加工', '加工中', '委外中') ORDER BY order_date DESC LIMIT 10"""
        ).fetchall()
        conn.close()
        return [dict(o) for o in orders]

    def get_unpaid_orders(self):
        conn = self.get_connection()
        orders = conn.execute(
            """SELECT order_no, customer_name, total_amount, received_amount, (total_amount - received_amount) as unpaid FROM processing_orders WHERE received_amount < total_amount ORDER BY unpaid DESC LIMIT 10"""
        ).fetchall()
        conn.close()
        return [dict(o) for o in orders]

    def get_top_customers(self):
        conn = self.get_connection()
        customers = conn.execute(
            """SELECT c.name, SUM(o.total_amount) as total, COUNT(o.id) as order_count FROM customers c LEFT JOIN processing_orders o ON c.id = o.customer_id GROUP BY c.id ORDER BY total DESC LIMIT 5"""
        ).fetchall()
        conn.close()
        return [dict(c) for c in customers]

    def generate_dashboard(self):
        today = self.get_today_stats()
        week = self.get_week_stats()
        month = self.get_month_stats()
        pending = self.get_pending_orders()
        unpaid = self.get_unpaid_orders()
        top_customers = self.get_top_customers()

        today_str = date.today().strftime("%Y年%m月%d日")
        weekday = ["一", "二", "三", "四", "五", "六", "日"][date.today().weekday()]

        return (
            f"""
======================================================================
                氧化加工厂财务系统 V2.0 - 今日概览
======================================================================
日期: {today_str} 星期{weekday}
----------------------------------------------------------------------
                          今日数据
----------------------------------------------------------------------
  收入: ¥{today["today_income"]:>12,.2f}    支出: ¥{today["today_expense"]:>12,.2f}
  订单: {today["today_orders"]:>12}个    利润: ¥{today["today_profit"]:>12,.2f}
----------------------------------------------------------------------
----------------------+----------------------+----------------------
       本 周           |       本 月           |       待处理
----------------------+----------------------+----------------------
 收入: ¥{week["week_income"]:>10,.2f} | 收入: ¥{month["month_income"]:>10,.2f} | 加工中: {len(pending):>8}个
 支出: ¥{week["week_expense"]:>10,.2f} | 支出: ¥{month["month_expense"]:>10,.2f} | 未收款: {len(unpaid):>8}个
 利润: ¥{week["week_profit"]:>10,.2f} | 利润: ¥{month["month_profit"]:>10,.2f} |
 订单: {week["week_orders"]:>12}个 | 订单: {month["month_orders"]:>12}个 |
----------------------------------------------------------------------
待加工订单 (最近10个):
----------------------------------------------------------------------
"""
            + (
                "\n".join(
                    [
                        f"  {i}. [{o['order_no']}] {o['customer_name']} - ¥{o['total_amount']:,.2f}"
                        for i, o in enumerate(pending, 1)
                    ]
                )
                or "  无待加工订单"
            )
            + f"""

----------------------------------------------------------------------
未收款订单 (TOP 10):
----------------------------------------------------------------------
"""
            + (
                f"  未收款总额: ¥{sum(o['unpaid'] for o in unpaid):,.2f}\n"
                + "\n".join(
                    [
                        f"  {i}. [{o['order_no']}] {o['customer_name']} - ¥{o['unpaid']:,.2f}"
                        for i, o in enumerate(unpaid[:5], 1)
                    ]
                )
                if unpaid
                else "  所有订单已收款"
            )
            + f"""

----------------------------------------------------------------------
TOP客户 (按订单金额):
----------------------------------------------------------------------
"""
            + "\n".join(
                [
                    f"  {i}. {c['name']} - ¥{c['total']:,.2f} ({c['order_count']}单)"
                    for i, c in enumerate(top_customers, 1)
                ]
            )
            + f"""

======================================================================
                          快捷操作
======================================================================
  [1] 录入订单    [2] 录入收入    [3] 录入支出    [4] 订单列表
  [5] 客户管理   [6] 供应商管理  [7] 生成报表    [8] 数据备份
  [9] 搜索      [0] 退出
======================================================================
"""
        )

    def run(self):
        if not self.db_path.exists():
            print(f"\n[ERROR] 数据库不存在: {self.db_path}")
            print(
                "请先运行: python oxidation_finance_v20/examples/generate_comprehensive_demo.py"
            )
            return
        print(self.generate_dashboard())
        while True:
            try:
                choice = input("\n请选择: ").strip()
                if choice == "0":
                    break
                elif choice == "4":
                    self.show_list("orders")
                elif choice == "5":
                    self.show_list("customers")
                elif choice == "6":
                    self.show_list("suppliers")
                elif choice == "9":
                    kw = input("搜索: ").strip()
                    if kw:
                        self.show_search(kw)
            except KeyboardInterrupt:
                break
            except:
                pass

    def show_list(self, list_type):
        conn = self.get_connection()
        if list_type == "orders":
            data = conn.execute(
                "SELECT order_no, customer_name, total_amount, status FROM processing_orders ORDER BY order_date DESC LIMIT 20"
            ).fetchall()
            print(f"\n{'=' * 60}\n订单列表\n{'=' * 60}")
            print(f"{'订单号':<15} {'客户':<15} {'金额':>12} {'状态':<8}")
            for o in data:
                print(f"{o[0]:<15} {o[1][:12]:<15} ¥{o[2]:>10,.2f} {o[3]:<8}")
        elif list_type == "customers":
            data = conn.execute(
                "SELECT name, contact, phone FROM customers ORDER BY name"
            ).fetchall()
            print(f"\n{'=' * 60}\n客户列表\n{'=' * 60}")
            for c in data:
                print(f"  {c[0]} ({c[1]} {c[2]})")
        elif list_type == "suppliers":
            data = conn.execute(
                "SELECT name, business_type FROM suppliers ORDER BY name"
            ).fetchall()
            print(f"\n{'=' * 60}\n供应商列表\n{'=' * 60}")
            for s in data:
                print(f"  {s[0]} - {s[1]}")
        conn.close()

    def show_search(self, keyword):
        conn = self.get_connection()
        kw = f"%{keyword}%"
        print(f"\n搜索: {keyword}")
        print("-" * 60)
        for r in conn.execute(
            "SELECT name, contact FROM customers WHERE name LIKE ? LIMIT 3", (kw,)
        ).fetchall():
            print(f"客户: {r[0]} ({r[1]})")
        for r in conn.execute(
            "SELECT order_no, customer_name, total_amount FROM processing_orders WHERE order_no LIKE ? OR customer_name LIKE ? LIMIT 3",
            (kw, kw),
        ).fetchall():
            print(f"订单: [{r[0]}] {r[1]} ¥{r[2]:,.2f}")
        conn.close()


def main():
    panel = QuickPanel()
    if not panel.db_path.exists():
        print(f"\n[ERROR] 数据库不存在")
        return
    panel.run()


if __name__ == "__main__":
    main()
