#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
验证数据库数据
"""

import sys
from pathlib import Path
from decimal import Decimal

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from oxidation_finance_v20.database import DatabaseManager


def verify_database(db_path: str):
    """验证数据库数据"""
    print("=" * 60)
    print("🔍 验证数据库数据")
    print("=" * 60)
    print(f"\n📁 数据库文件: {db_path}\n")
    
    with DatabaseManager(db_path) as db:
        # 统计数据
        customers = db.list_customers()
        suppliers = db.list_suppliers()
        orders = db.list_orders()
        incomes = db.list_incomes()
        expenses = db.list_expenses()
        accounts = db.list_bank_accounts()
        transactions = db.list_bank_transactions()
        
        print("📊 数据统计:")
        print(f"   客户数量: {len(customers)}")
        print(f"   供应商数量: {len(suppliers)}")
        print(f"   订单数量: {len(orders)}")
        print(f"   收入记录: {len(incomes)}")
        print(f"   支出记录: {len(expenses)}")
        print(f"   银行账户: {len(accounts)}")
        print(f"   银行交易: {len(transactions)}")
        
        # 财务汇总
        total_income = sum(i.amount for i in incomes)
        total_expense = sum(e.amount for e in expenses)
        profit = total_income - total_expense
        
        print(f"\n💰 财务汇总:")
        print(f"   总收入: ¥{total_income:,.2f}")
        print(f"   总支出: ¥{total_expense:,.2f}")
        print(f"   利润: ¥{profit:,.2f}")
        
        # 订单状态统计
        from oxidation_finance_v20.models import OrderStatus
        status_counts = {}
        for order in orders:
            status = order.status.value
            status_counts[status] = status_counts.get(status, 0) + 1
        
        print(f"\n📋 订单状态:")
        for status, count in status_counts.items():
            print(f"   {status}: {count}")
        
        # 银行账户余额
        print(f"\n🏦 银行账户:")
        for account in accounts:
            print(f"   {account.account_name}: ¥{account.balance:,.2f}")
        
        # 示例客户
        if customers:
            print(f"\n👥 示例客户:")
            for customer in customers[:3]:
                print(f"   {customer.name} - {customer.contact} - 信用额度: ¥{customer.credit_limit:,.2f}")
        
        # 示例订单
        if orders:
            print(f"\n📦 示例订单:")
            for order in orders[:3]:
                print(f"   {order.order_no} - {order.customer_name} - {order.item_description}")
                print(f"      数量: {order.quantity} {order.pricing_unit.value}, 金额: ¥{order.total_amount:,.2f}, 状态: {order.status.value}")
        
        print("\n" + "=" * 60)
        print("✅ 数据库验证完成！")
        print("=" * 60)


def main():
    """主函数"""
    db_path = project_root / "oxidation_finance_v20" / "oxidation_finance_demo.db"
    
    if not db_path.exists():
        print(f"❌ 数据库文件不存在: {db_path}")
        print("请先运行: python oxidation_finance_v20/scripts/init_demo_data.py")
        return
    
    verify_database(str(db_path))


if __name__ == "__main__":
    main()
