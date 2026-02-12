#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
打印优化工具

功能：
- 生成可直接打印的报表
- 格式优化，适合A4纸
- 支持打印机直接输出
"""

import sys
import io

# Windows编码支持
if sys.platform == "win32":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")

import sys
from pathlib import Path
from datetime import date, datetime
import sqlite3


class PrintOptimizer:
    """打印优化工具"""

    def __init__(self):
        base_dir = Path(__file__).resolve().parent.parent
        self.db_path = base_dir / "oxidation_finance_demo_ready.db"
        if not self.db_path.exists():
            self.db_path = base_dir / "oxidation_finance_demo.db"
        self.output_dir = Path("print_ready")
        self.output_dir.mkdir(exist_ok=True)

    def get_connection(self):
        conn = sqlite3.connect(str(self.db_path))
        conn.row_factory = sqlite3.Row
        return conn

    def generate_profit_statement_for_print(self):
        """生成可打印的利润表"""
        conn = self.get_connection()

        # 获取本月数据
        month_start = date.today().replace(day=1).isoformat()
        today = date.today().isoformat()

        total_income = (
            conn.execute(
                "SELECT SUM(amount) FROM incomes WHERE income_date >= ?", (month_start,)
            ).fetchone()[0]
            or 0
        )

        expenses = conn.execute(
            """
            SELECT expense_type, SUM(amount) as total
            FROM expenses
            WHERE expense_date >= ?
            GROUP BY expense_type
            ORDER BY total DESC
        """,
            (month_start,),
        ).fetchall()

        total_expense = sum(e["total"] for e in expenses)
        profit = total_income - total_expense

        conn.close()

        # 生成打印版本（纯文本，适合打印）
        output_file = (
            self.output_dir / f"利润表_打印版_{date.today().strftime('%Y%m')}.txt"
        )

        with open(output_file, "w", encoding="utf-8") as f:
            # 打印优化格式
            f.write("\n" + "=" * 72 + "\n")
            f.write(" " * 25 + "利 润 表\n")
            f.write("=" * 72 + "\n")
            f.write(
                f"\n期间：{date.today().replace(day=1).strftime('%Y年%m月%d日')} 至 {date.today().strftime('%Y年%m月%d日')}\n"
            )
            f.write(f"生成日期：{datetime.now().strftime('%Y年%m月%d日')}\n")
            f.write("\n" + "=" * 72 + "\n")

            f.write("\n一、收入\n")
            f.write("-" * 72 + "\n")
            f.write(
                f"加工收入                                          {total_income:>15,.2f}\n"
            )
            f.write("-" * 72 + "\n")
            f.write(
                f"收入合计                                          {total_income:>15,.2f}\n"
            )

            f.write("\n二、支出\n")
            f.write("-" * 72 + "\n")
            for e in expenses:
                f.write(
                    f"{e['expense_type']:<20}                              {e['total']:>15,.2f}\n"
                )
            f.write("-" * 72 + "\n")
            f.write(
                f"支出合计                                          {total_expense:>15,.2f}\n"
            )

            f.write("\n" + "=" * 72 + "\n")
            f.write(
                f"净利润                                            {profit:>15,.2f}\n"
            )
            f.write("=" * 72 + "\n")

            if total_income > 0:
                margin = (profit / total_income) * 100
                f.write(f"\n利润率：{margin:.2f}%\n")

            f.write("\n" + " " * 20 + "会计：__________    审核：__________\n")
            f.write("\n" + "=" * 72 + "\n")

        print(f"[OK] 打印版利润表已生成: {output_file}")
        print(f"\n打印建议:")
        print(f"  1. 使用A4纸纵向打印")
        print(f"  2. 使用等宽字体（如宋体、Consolas）")
        print(f"  3. 页边距: 上下2cm，左右2.5cm")

        return str(output_file)

    def generate_customer_statement_for_print(self, customer_name=None):
        """生成可打印的客户对账单"""
        conn = self.get_connection()

        if customer_name:
            customers = conn.execute(
                "SELECT * FROM customers WHERE name = ?", (customer_name,)
            ).fetchall()
        else:
            customers = conn.execute(
                "SELECT * FROM customers ORDER BY name LIMIT 1"
            ).fetchall()

        output_files = []

        for customer in customers:
            # 获取本期数据
            month_start = date.today().replace(day=1).isoformat()

            orders = conn.execute(
                """
                SELECT order_no, order_date, item_description, total_amount
                FROM processing_orders
                WHERE customer_id = ? AND order_date >= ?
                ORDER BY order_date
            """,
                (customer["id"], month_start),
            ).fetchall()

            total_amount = sum(o["total_amount"] for o in orders)

            # 生成对账单
            safe_name = "".join(
                c for c in customer["name"] if c.isalnum() or c in (" ", "-", "_")
            ).strip()
            output_file = (
                self.output_dir
                / f"对账单_{safe_name}_{date.today().strftime('%Y%m')}_打印版.txt"
            )

            with open(output_file, "w", encoding="utf-8") as f:
                f.write("\n" + "=" * 72 + "\n")
                f.write(" " * 25 + "客 户 对 账 单\n")
                f.write("=" * 72 + "\n\n")

                f.write(f"客户名称：{customer['name']}\n")
                f.write(f"联系人：{customer['contact'] or '__________'}\n")
                f.write(f"联系电话：{customer['phone'] or '__________'}\n")
                f.write(f"地址：{customer['address'] or '__________'}\n\n")

                f.write(
                    f"对账期间：{date.today().replace(day=1).strftime('%Y年%m月%d日')} 至 {date.today().strftime('%Y年%m月%d日')}\n"
                )
                f.write(f"生成日期：{datetime.now().strftime('%Y年%m月%d日')}\n\n")

                f.write("=" * 72 + "\n")
                f.write("订单明细\n")
                f.write("=" * 72 + "\n")
                f.write(f"{'订单号':<12} {'日期':<12} {'物品':<20} {'金额':>12}\n")
                f.write("-" * 72 + "\n")

                for o in orders:
                    item = o["item_description"][:18] if o["item_description"] else ""
                    f.write(
                        f"{o['order_no']:<12} {o['order_date']:<12} {item:<20} {o['total_amount']:>12,.2f}\n"
                    )

                f.write("-" * 72 + "\n")
                f.write(f"{'合计':<44} {total_amount:>12,.2f}\n")
                f.write("=" * 72 + "\n\n")

                f.write("说明：\n")
                f.write("1. 请核对以上数据，如有疑问请于3日内联系。\n")
                f.write("2. 如无异议，请签字盖章确认。\n\n")

                f.write(" " * 20 + "客户确认：__________    日期：__________\n\n")
                f.write("=" * 72 + "\n")

            print(f"[OK] 打印版对账单已生成: {output_file}")
            output_files.append(str(output_file))

        conn.close()
        return output_files

    def print_all(self):
        """生成所有打印文件"""
        print("\n" + "=" * 72)
        print("生成打印优化文件")
        print("=" * 72)

        print("\n[1/2] 生成利润表...")
        self.generate_profit_statement_for_print()

        print("\n[2/2] 生成客户对账单...")
        self.generate_customer_statement_for_print()

        print("\n" + "=" * 72)
        print(f"所有文件已保存到: {self.output_dir}")
        print("=" * 72 + "\n")

        print("打印提示:")
        print("  1. 打开生成的txt文件")
        print("  2. 使用记事本或Word打开")
        print("  3. 选择等宽字体（宋体12号）")
        print("  4. 页面设置：A4纵向，页边距2cm")
        print("  5. 打印预览确认格式正确后打印")
        print()


def main():
    optimizer = PrintOptimizer()
    if not optimizer.db_path.exists():
        print("[ERROR] 数据库不存在")
        return
    optimizer.print_all()


if __name__ == "__main__":
    main()
