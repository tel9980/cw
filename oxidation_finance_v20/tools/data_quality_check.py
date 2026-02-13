#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
数据质量检查工具

功能：
- 检测重复数据
- 检测异常数据
- 修复常见问题
- 数据统计报告
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
from decimal import Decimal
import sqlite3
import json


class DataQualityChecker:
    """数据质量检查器"""

    def __init__(self):
        # 查找数据库文件
        base_dir = Path(__file__).resolve().parent.parent
        self.db_path = base_dir / "oxidation_finance_demo_ready.db"

        # 如果主数据库不存在，尝试其他位置
        if not self.db_path.exists():
            alt_db = Path(__file__).parent / "oxidation_finance_demo_ready.db"
            if alt_db.exists():
                self.db_path = alt_db

        self.issues = []
        self.warnings = []

    def get_connection(self):
        """获取数据库连接"""
        conn = sqlite3.connect(str(self.db_path))
        conn.row_factory = sqlite3.Row
        return conn

    def check_duplicate_customers(self):
        """检查重复客户"""
        conn = self.get_connection()

        # 按名称查找重复
        duplicates = conn.execute("""
            SELECT name, COUNT(*) as cnt
            FROM customers
            WHERE name IS NOT NULL AND name != ''
            GROUP BY name
            HAVING COUNT(*) > 1
        """).fetchall()

        if duplicates:
            for d in duplicates:
                self.warnings.append(f"重复客户名称: {d['name']} ({d['cnt']}次)")
                # 获取重复的客户ID
                customers = conn.execute(
                    "SELECT id, name, contact FROM customers WHERE name = ?",
                    (d["name"],),
                ).fetchall()
                for c in customers:
                    print(f"  - {c['id'][:8]}... {c['name']} ({c['contact']})")

        conn.close()
        return len(duplicates)

    def check_duplicate_orders(self):
        """检查重复订单"""
        conn = self.get_connection()

        # 按订单号查找重复
        duplicates = conn.execute("""
            SELECT order_no, COUNT(*) as cnt
            FROM processing_orders
            WHERE order_no IS NOT NULL AND order_no != ''
            GROUP BY order_no
            HAVING COUNT(*) > 1
        """).fetchall()

        if duplicates:
            for d in duplicates:
                self.warnings.append(f"重复订单号: {d['order_no']} ({d['cnt']}次)")

        conn.close()
        return len(duplicates)

    def check_orders_without_customer(self):
        """检查无客户的订单"""
        conn = self.get_connection()

        orders = conn.execute("""
            SELECT id, order_no, customer_name, total_amount
            FROM processing_orders
            WHERE customer_id IS NULL OR customer_id = ''
        """).fetchall()

        if orders:
            self.warnings.append(f"无客户订单: {len(orders)}个")
            for o in orders[:5]:
                print(
                    f"  - [{o['order_no']}] {o['customer_name']} ¥{o['total_amount']:,.2f}"
                )

        conn.close()
        return len(orders)

    def check_unbalanced_orders(self):
        """检查订单金额异常"""
        conn = self.get_connection()

        # 金额为0的订单
        zero_orders = conn.execute("""
            SELECT id, order_no, customer_name, total_amount
            FROM processing_orders
            WHERE total_amount <= 0
        """).fetchall()

        if zero_orders:
            self.warnings.append(f"金额为0的订单: {len(zero_orders)}个")

        # 金额异常的订单（>100万）
        large_orders = conn.execute("""
            SELECT id, order_no, customer_name, total_amount
            FROM processing_orders
            WHERE total_amount > 1000000
        """).fetchall()

        if large_orders:
            self.warnings.append(f"大额订单(>100万): {len(large_orders)}个")
            for o in large_orders[:5]:
                print(
                    f"  - [{o['order_no']}] {o['customer_name']} ¥{o['total_amount']:,.2f}"
                )

        conn.close()
        return len(zero_orders) + len(large_orders)

    def check_unpaid_orders(self):
        """检查未收款订单"""
        conn = self.get_connection()

        orders = conn.execute("""
            SELECT order_no, customer_name, total_amount, received_amount,
                   (total_amount - received_amount) as unpaid
            FROM processing_orders
            WHERE received_amount < total_amount
            ORDER BY unpaid DESC
        """).fetchall()

        conn.close()

        total_unpaid = sum(o["unpaid"] for o in orders)
        print(f"\n未收款订单统计:")
        print(f"  总数: {len(orders)}个")
        print(f"  总金额: ¥{total_unpaid:,.2f}")

        return len(orders)

    def check_income_allocation(self):
        """检查收入分配"""
        conn = self.get_connection()

        # 有分配但无关联订单的收入
        incomes = conn.execute("""
            SELECT id, customer_name, amount, allocation
            FROM incomes
            WHERE allocation != '' AND allocation != '{}'
            AND (related_orders = '' OR related_orders = '[]')
        """).fetchall()

        if incomes:
            self.warnings.append(f"分配但无关联的收入: {len(incomes)}笔")

        conn.close()
        return len(incomes)

    def check_bank_transactions(self):
        """检查银行交易"""
        conn = self.get_connection()

        # 未匹配的交易
        unmatched = conn.execute("""
            SELECT id, transaction_date, amount, counterparty, description
            FROM bank_transactions
            WHERE matched = 0
        """).fetchall()

        if unmatched:
            self.warnings.append(f"未匹配银行交易: {len(unmatched)}条")
            for t in unmatched[:5]:
                print(
                    f"  - [{t['transaction_date']}] ¥{t['amount']:,.2f} {t['counterparty']}"
                )

        conn.close()
        return len(unmatched)

    def generate_report(self):
        """生成完整报告"""
        print("\n" + "=" * 70)
        print("           氧化加工厂财务系统 V2.0 - 数据质量报告")
        print("=" * 70)
        print(f"\n检查时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"数据库: {self.db_path.name}")

        if not self.db_path.exists():
            print("\n[ERROR] 数据库不存在!")
            return

        # 连接数据库
        conn = sqlite3.connect(str(self.db_path))

        # 基本统计
        print("\n" + "-" * 70)
        print("数据统计:")
        print("-" * 70)

        stats = {
            "客户": "SELECT COUNT(*) FROM customers",
            "供应商": "SELECT COUNT(*) FROM suppliers",
            "订单": "SELECT COUNT(*) FROM processing_orders",
            "收入": "SELECT COUNT(*) FROM incomes",
            "支出": "SELECT COUNT(*) FROM expenses",
            "银行账户": "SELECT COUNT(*) FROM bank_accounts",
            "银行交易": "SELECT COUNT(*) FROM bank_transactions",
        }

        total_records = 0
        for name, sql in stats.items():
            try:
                count = conn.execute(sql).fetchone()[0]
                print(f"  {name}: {count:,}")
                total_records += count
            except sqlite3.Error:
                print(f"  {name}: N/A")

        print(f"\n  总记录数: {total_records:,}")

        conn.close()

        # 检查项目
        print("\n" + "-" * 70)
        print("质量检查:")
        print("-" * 70)

        self.check_duplicate_customers()
        self.check_duplicate_orders()
        self.check_orders_without_customer()
        self.check_unbalanced_orders()
        self.check_income_allocation()
        self.check_bank_transactions()

        # 汇总
        print("\n" + "-" * 70)
        print("汇总:")
        print("-" * 70)

        if self.warnings:
            print(f"\n发现 {len(self.warnings)} 个问题:")
            for i, w in enumerate(self.warnings, 1):
                print(f"  {i}. {w}")
        else:
            print("\n✓ 未发现明显问题!")

        # 特殊统计
        print("\n" + "-" * 70)
        print("特殊统计:")
        print("-" * 70)

        self.check_unpaid_orders()

        print("\n" + "=" * 70)
        print("                        报告结束")
        print("=" * 70)

    def quick_check(self):
        """快速检查"""
        print("\n" + "=" * 70)
        print("                    数据质量快速检查")
        print("=" * 70)

        conn = self.get_connection()

        # 关键指标
        today = date.today().isoformat()

        # 今日数据
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

        # 待处理
        pending_orders = (
            conn.execute(
                "SELECT COUNT(*) FROM processing_orders WHERE status IN ('待加工', '加工中')"
            ).fetchone()[0]
            or 0
        )

        # 未收款
        unpaid_count = (
            conn.execute(
                "SELECT COUNT(*) FROM processing_orders WHERE received_amount < total_amount"
            ).fetchone()[0]
            or 0
        )

        # 未匹配银行交易
        unmatched = (
            conn.execute(
                "SELECT COUNT(*) FROM bank_transactions WHERE matched = 0"
            ).fetchone()[0]
            or 0
        )

        conn.close()

        print(
            f"\n  今日收支:  ¥{today_income:>12,.2f} 收入  |  ¥{today_expense:>12,.2f} 支出"
        )
        print(
            f"  待处理订单: {pending_orders:>12}个  |  未收款订单: {unpaid_count:>8}个"
        )
        print(f"  未匹配银行交易: {unmatched:>8}条")

        # 健康评分
        health_score = 100
        if pending_orders > 20:
            health_score -= 10
        if unpaid_count > 30:
            health_score -= 10
        if unmatched > 10:
            health_score -= 10

        health = (
            "优秀" if health_score >= 90 else "良好" if health_score >= 70 else "需注意"
        )

        print(f"\n  数据健康度: {health} ({health_score}分)")
        print("\n" + "=" * 70)

    def run(self, full_check=False):
        """运行检查"""
        if full_check:
            self.generate_report()
        else:
            self.quick_check()


def main():
    """主函数"""
    checker = DataQualityChecker()

    # 检查参数
    full = "--full" in sys.argv or "--详细" in sys.argv

    if full:
        checker.run(full_check=True)
    else:
        checker.run(full_check=False)


if __name__ == "__main__":
    main()
