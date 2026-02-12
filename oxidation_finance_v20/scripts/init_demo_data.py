#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
初始化演示数据到数据库
"""

import sys
import json
from pathlib import Path
from datetime import date, datetime
from decimal import Decimal

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from oxidation_finance_v20.database import DatabaseManager
from oxidation_finance_v20.models import (
    Customer, Supplier, ProcessingOrder, Income, Expense,
    BankAccount, BankTransaction,
    PricingUnit, ProcessType, OrderStatus, ExpenseType, BankType
)


def load_demo_data():
    """从JSON文件加载演示数据"""
    demo_file = project_root / "demo_data_v20" / "oxidation_factory_demo_data.json"
    
    if not demo_file.exists():
        print(f"❌ 演示数据文件不存在: {demo_file}")
        print("请先运行: python 生成氧化加工厂示例数据_V2.0.py")
        return None
    
    with open(demo_file, 'r', encoding='utf-8') as f:
        return json.load(f)


def import_customers(db: DatabaseManager, customers_data):
    """导入客户数据"""
    print("\n📋 导入客户数据...")
    count = 0
    for data in customers_data:
        customer = Customer(
            id=data['id'],
            name=data['name'],
            contact=data['contact'],
            phone=data['phone'],
            address=data['address'],
            credit_limit=Decimal(str(data['credit_limit'])),
            notes=data['notes'],
            created_at=datetime.fromisoformat(data['created_at'])
        )
        db.save_customer(customer)
        count += 1
    print(f"✅ 已导入 {count} 个客户")


def import_suppliers(db: DatabaseManager, suppliers_data):
    """导入供应商数据"""
    print("\n📋 导入供应商数据...")
    count = 0
    for data in suppliers_data:
        supplier = Supplier(
            id=data['id'],
            name=data['name'],
            contact=data['contact'],
            phone=data['phone'],
            address=data['address'],
            business_type=data['business_type'],
            notes=data['notes'],
            created_at=datetime.fromisoformat(data['created_at'])
        )
        db.save_supplier(supplier)
        count += 1
    print(f"✅ 已导入 {count} 个供应商")


def import_orders(db: DatabaseManager, orders_data):
    """导入订单数据"""
    print("\n📋 导入订单数据...")
    count = 0
    for data in orders_data:
        order = ProcessingOrder(
            id=data['id'],
            order_no=data['order_no'],
            customer_id=data['customer_id'],
            customer_name=data['customer_name'],
            item_description=data['item_description'],
            quantity=Decimal(str(data['quantity'])),
            pricing_unit=PricingUnit(data['pricing_unit']),
            unit_price=Decimal(str(data['unit_price'])),
            processes=[ProcessType(p) for p in data['processes']],
            outsourced_processes=data['outsourced_processes'],
            total_amount=Decimal(str(data['total_amount'])),
            outsourcing_cost=Decimal(str(data['outsourcing_cost'])),
            status=OrderStatus(data['status']),
            order_date=date.fromisoformat(data['order_date']),
            completion_date=date.fromisoformat(data['completion_date']) if data['completion_date'] else None,
            delivery_date=date.fromisoformat(data['delivery_date']) if data['delivery_date'] else None,
            received_amount=Decimal(str(data['received_amount'])),
            notes=data['notes'],
            created_at=datetime.fromisoformat(data['created_at']),
            updated_at=datetime.fromisoformat(data['updated_at'])
        )
        db.save_order(order)
        count += 1
    print(f"✅ 已导入 {count} 个订单")


def import_incomes(db: DatabaseManager, incomes_data):
    """导入收入数据"""
    print("\n📋 导入收入数据...")
    count = 0
    for data in incomes_data:
        income = Income(
            id=data['id'],
            customer_id=data['customer_id'],
            customer_name=data['customer_name'],
            amount=Decimal(str(data['amount'])),
            bank_type=BankType(data['bank_type']),
            has_invoice=data['has_invoice'],
            related_orders=data['related_orders'],
            allocation={k: Decimal(str(v)) for k, v in data['allocation'].items()},
            income_date=date.fromisoformat(data['income_date']),
            notes=data['notes'],
            created_at=datetime.fromisoformat(data['created_at'])
        )
        db.save_income(income)
        count += 1
    print(f"✅ 已导入 {count} 条收入记录")


def import_expenses(db: DatabaseManager, expenses_data):
    """导入支出数据"""
    print("\n📋 导入支出数据...")
    count = 0
    for data in expenses_data:
        expense = Expense(
            id=data['id'],
            expense_type=ExpenseType(data['expense_type']),
            supplier_id=data['supplier_id'],
            supplier_name=data['supplier_name'],
            amount=Decimal(str(data['amount'])),
            bank_type=BankType(data['bank_type']),
            has_invoice=data['has_invoice'],
            related_order_id=data['related_order_id'],
            expense_date=date.fromisoformat(data['expense_date']),
            description=data['description'],
            notes=data['notes'],
            created_at=datetime.fromisoformat(data['created_at'])
        )
        db.save_expense(expense)
        count += 1
    print(f"✅ 已导入 {count} 条支出记录")


def import_bank_accounts(db: DatabaseManager, accounts_data):
    """导入银行账户数据"""
    print("\n📋 导入银行账户...")
    count = 0
    for data in accounts_data:
        account = BankAccount(
            id=data['id'],
            bank_type=BankType(data['bank_type']),
            account_name=data['account_name'],
            account_number=data['account_number'],
            balance=Decimal(str(data['balance'])),
            notes=data['notes']
        )
        db.save_bank_account(account)
        count += 1
    print(f"✅ 已导入 {count} 个银行账户")


def import_bank_transactions(db: DatabaseManager, transactions_data):
    """导入银行交易数据"""
    print("\n📋 导入银行交易记录...")
    count = 0
    for data in transactions_data:
        transaction = BankTransaction(
            id=data['id'],
            bank_type=BankType(data['bank_type']),
            transaction_date=date.fromisoformat(data['transaction_date']),
            amount=Decimal(str(data['amount'])),
            counterparty=data['counterparty'],
            description=data['description'],
            matched=data['matched'],
            matched_income_id=data['matched_income_id'],
            matched_expense_id=data['matched_expense_id'],
            notes=data['notes'],
            created_at=datetime.fromisoformat(data['created_at'])
        )
        db.save_bank_transaction(transaction)
        count += 1
    print(f"✅ 已导入 {count} 条银行交易")


def main():
    """主函数"""
    print("=" * 60)
    print("🎨 氧化加工厂财务系统 - 初始化演示数据")
    print("=" * 60)
    
    # 加载演示数据
    demo_data = load_demo_data()
    if not demo_data:
        return
    
    # 数据库文件路径
    db_path = project_root / "oxidation_finance_v20" / "oxidation_finance_demo.db"
    
    print(f"\n📁 数据库文件: {db_path}")
    
    # 如果数据库已存在，询问是否覆盖
    if db_path.exists():
        response = input("\n⚠️  数据库文件已存在，是否覆盖? (y/n): ")
        if response.lower() != 'y':
            print("❌ 操作已取消")
            return
        db_path.unlink()
        print("✅ 已删除旧数据库")
    
    # 创建数据库并导入数据
    try:
        with DatabaseManager(str(db_path)) as db:
            import_customers(db, demo_data['customers'])
            import_suppliers(db, demo_data['suppliers'])
            import_orders(db, demo_data['orders'])
            import_incomes(db, demo_data['incomes'])
            import_expenses(db, demo_data['expenses'])
            import_bank_accounts(db, demo_data['bank_accounts'])
            import_bank_transactions(db, demo_data['bank_transactions'])
        
        print("\n" + "=" * 60)
        print("🎉 演示数据初始化完成！")
        print(f"\n📊 数据库文件: {db_path}")
        print("\n💡 提示: 现在可以使用系统查看和管理这些演示数据了")
        print("=" * 60)
        
    except Exception as e:
        print(f"\n❌ 导入数据时出错: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
