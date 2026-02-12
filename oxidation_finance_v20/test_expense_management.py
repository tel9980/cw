#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试支出管理功能
"""

import sys
from pathlib import Path
from decimal import Decimal
from datetime import date, timedelta

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent))

from database.db_manager import DatabaseManager
from business.finance_manager import FinanceManager
from models.business_models import (
    Supplier, ExpenseType, BankType
)


def test_expense_management():
    """测试支出管理功能"""
    print("=" * 60)
    print("测试支出管理功能")
    print("=" * 60)
    
    # 创建临时数据库
    db = DatabaseManager(":memory:")
    db.connect()
    
    finance_manager = FinanceManager(db)
    
    # 1. 测试记录基本支出
    print("\n1. 测试记录基本支出...")
    supplier = Supplier(
        name="化工供应商",
        contact="张三",
        phone="13800138000",
        business_type="原料供应商"
    )
    db.save_supplier(supplier)
    
    expense1 = finance_manager.record_expense(
        expense_type=ExpenseType.ACID_THREE,
        amount=Decimal("3000"),
        bank_type=BankType.G_BANK,
        expense_date=date.today(),
        supplier_id=supplier.id,
        supplier_name=supplier.name,
        has_invoice=True,
        description="采购硫酸"
    )
    print(f"✓ 记录支出成功: {expense1.expense_type.value}, 金额: {expense1.amount}")
    
    # 2. 测试十种支出类型
    print("\n2. 测试十种支出类型...")
    expense_types = [
        (ExpenseType.RENT, Decimal("5000"), "厂房租金"),
        (ExpenseType.UTILITIES, Decimal("1200"), "水电费"),
        (ExpenseType.CAUSTIC_SODA, Decimal("1500"), "片碱采购"),
        (ExpenseType.SODIUM_SULFITE, Decimal("800"), "亚钠采购"),
        (ExpenseType.COLOR_POWDER, Decimal("600"), "色粉采购"),
        (ExpenseType.DEGREASER, Decimal("400"), "除油剂采购"),
        (ExpenseType.FIXTURES, Decimal("2000"), "挂具采购"),
        (ExpenseType.OUTSOURCING, Decimal("5000"), "委外加工费"),
        (ExpenseType.DAILY_EXPENSE, Decimal("300"), "办公用品"),
        (ExpenseType.SALARY, Decimal("15000"), "员工工资"),
    ]
    
    for exp_type, amount, desc in expense_types:
        expense = finance_manager.record_expense(
            expense_type=exp_type,
            amount=amount,
            bank_type=BankType.G_BANK,
            expense_date=date.today(),
            supplier_id=supplier.id if exp_type not in [ExpenseType.RENT, ExpenseType.SALARY] else None,
            supplier_name=supplier.name if exp_type not in [ExpenseType.RENT, ExpenseType.SALARY] else "",
            description=desc
        )
        print(f"✓ {exp_type.value}: {amount} 元")
    
    # 3. 测试专业原料管理
    print("\n3. 测试专业原料支出汇总...")
    materials = finance_manager.get_professional_materials_expenses()
    print(f"✓ 专业原料总支出: {materials['total_amount']} 元")
    for material_name, material_data in materials['materials'].items():
        if material_data['amount'] > 0:
            print(f"  - {material_name}: {material_data['amount']} 元 ({material_data['count']} 笔)")
    
    # 4. 测试供应商付款分配
    print("\n4. 测试供应商付款灵活分配...")
    expense2 = finance_manager.record_expense(
        expense_type=ExpenseType.CAUSTIC_SODA,
        amount=Decimal("2000"),
        bank_type=BankType.G_BANK,
        expense_date=date.today(),
        supplier_id=supplier.id,
        supplier_name=supplier.name,
        description="片碱采购2"
    )
    
    expense3 = finance_manager.record_expense(
        expense_type=ExpenseType.COLOR_POWDER,
        amount=Decimal("1000"),
        bank_type=BankType.G_BANK,
        expense_date=date.today(),
        supplier_id=supplier.id,
        supplier_name=supplier.name,
        description="色粉采购2"
    )
    
    success, message = finance_manager.allocate_payment_to_expenses(
        payment_amount=Decimal("3000"),
        allocations={
            expense2.id: Decimal("2000"),
            expense3.id: Decimal("1000")
        },
        bank_type=BankType.G_BANK,
        payment_date=date.today(),
        notes="批量付款"
    )
    print(f"✓ 付款分配: {message}")
    assert success is True
    
    # 5. 测试供应商应付账款
    print("\n5. 测试供应商应付账款汇总...")
    payables = finance_manager.get_supplier_payables(supplier.id)
    print(f"✓ 供应商应付账款总额: {payables['total_amount']} 元")
    print(f"✓ 支出记录数: {payables['expense_count']} 笔")
    
    # 6. 测试按类型汇总支出
    print("\n6. 测试按类型汇总支出...")
    summary = finance_manager.get_expense_summary_by_type()
    print("✓ 支出类型汇总:")
    for expense_type_name, amount in sorted(summary.items(), key=lambda x: x[1], reverse=True):
        print(f"  - {expense_type_name}: {amount} 元")
    
    # 7. 测试按类型查询
    print("\n7. 测试按类型查询支出...")
    acid_expenses = finance_manager.get_expenses_by_type(ExpenseType.ACID_THREE)
    print(f"✓ 三酸支出记录: {len(acid_expenses)} 笔")
    for exp in acid_expenses:
        print(f"  - {exp.expense_date}: {exp.amount} 元 - {exp.description}")
    
    # 8. 测试日期过滤
    print("\n8. 测试日期过滤...")
    today = date.today()
    yesterday = today - timedelta(days=1)
    
    # 添加昨天的支出
    finance_manager.record_expense(
        expense_type=ExpenseType.RENT,
        amount=Decimal("5000"),
        bank_type=BankType.G_BANK,
        expense_date=yesterday,
        description="上月租金"
    )
    
    summary_today = finance_manager.get_expense_summary_by_type(
        start_date=today,
        end_date=today
    )
    print(f"✓ 今日支出汇总: {sum(summary_today.values())} 元")
    
    # 9. 测试错误处理
    print("\n9. 测试错误处理...")
    success, message = finance_manager.allocate_payment_to_expenses(
        payment_amount=Decimal("1000"),
        allocations={
            expense2.id: Decimal("2000")  # 超过付款金额
        },
        bank_type=BankType.G_BANK,
        payment_date=date.today()
    )
    print(f"✓ 超额分配检测: {message}")
    assert success is False
    assert "超过付款金额" in message
    
    db.close()
    
    print("\n" + "=" * 60)
    print("✓ 所有测试通过！")
    print("=" * 60)


if __name__ == "__main__":
    test_expense_management()
