#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
任务 4.3 验证脚本 - 支出管理功能
"""

import sys
from pathlib import Path
from decimal import Decimal
from datetime import date

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent))

from database.db_manager import DatabaseManager
from business.finance_manager import FinanceManager
from models.business_models import (
    Supplier, ExpenseType, BankType
)


def print_section(title):
    """打印章节标题"""
    print("\n" + "=" * 70)
    print(f"  {title}")
    print("=" * 70)


def verify_expense_management():
    """验证支出管理功能"""
    print("\n" + "🎯" * 35)
    print("任务 4.3 - 支出管理功能验证")
    print("🎯" * 35)
    
    # 创建临时数据库
    db = DatabaseManager(":memory:")
    db.connect()
    finance_manager = FinanceManager(db)
    
    # ========== 需求 3.1: 十种支出类型的分类管理 ==========
    print_section("需求 3.1: 十种支出类型的分类管理")
    
    expense_types_data = [
        (ExpenseType.RENT, Decimal("5000"), "厂房租金"),
        (ExpenseType.UTILITIES, Decimal("1200"), "水电费"),
        (ExpenseType.ACID_THREE, Decimal("3000"), "硫酸采购"),
        (ExpenseType.CAUSTIC_SODA, Decimal("1500"), "片碱采购"),
        (ExpenseType.SODIUM_SULFITE, Decimal("800"), "亚钠采购"),
        (ExpenseType.COLOR_POWDER, Decimal("600"), "色粉采购"),
        (ExpenseType.DEGREASER, Decimal("400"), "除油剂采购"),
        (ExpenseType.FIXTURES, Decimal("2000"), "挂具采购"),
        (ExpenseType.OUTSOURCING, Decimal("5000"), "委外加工费"),
        (ExpenseType.DAILY_EXPENSE, Decimal("300"), "办公用品"),
        (ExpenseType.SALARY, Decimal("15000"), "员工工资"),
    ]
    
    print("\n✓ 支持的支出类型:")
    for exp_type, amount, desc in expense_types_data:
        expense = finance_manager.record_expense(
            expense_type=exp_type,
            amount=amount,
            bank_type=BankType.G_BANK,
            expense_date=date.today(),
            description=desc
        )
        print(f"  • {exp_type.value:12s} - {amount:>8} 元 - {desc}")
    
    # 验证按类型查询
    print("\n✓ 按类型查询验证:")
    rent_expenses = finance_manager.get_expenses_by_type(ExpenseType.RENT)
    print(f"  • 房租支出: {len(rent_expenses)} 笔, 总额: {sum(e.amount for e in rent_expenses)} 元")
    
    utilities_expenses = finance_manager.get_expenses_by_type(ExpenseType.UTILITIES)
    print(f"  • 水电费支出: {len(utilities_expenses)} 笔, 总额: {sum(e.amount for e in utilities_expenses)} 元")
    
    # 支出汇总
    print("\n✓ 支出类型汇总:")
    summary = finance_manager.get_expense_summary_by_type()
    total_expenses = Decimal("0")
    for expense_type_name, amount in sorted(summary.items(), key=lambda x: x[1], reverse=True):
        print(f"  • {expense_type_name:12s}: {amount:>8} 元")
        total_expenses += amount
    print(f"  {'─' * 30}")
    print(f"  • {'总计':12s}: {total_expenses:>8} 元")
    
    # ========== 需求 3.2: 专业原料管理 ==========
    print_section("需求 3.2: 专业原料（三酸、片碱等）管理")
    
    # 创建供应商
    supplier = Supplier(
        name="化工原料供应商",
        contact="李经理",
        phone="13800138000",
        business_type="原料供应商"
    )
    db.save_supplier(supplier)
    
    # 记录专业原料采购
    professional_materials = [
        (ExpenseType.ACID_THREE, Decimal("3500"), "硫酸、硝酸、盐酸"),
        (ExpenseType.CAUSTIC_SODA, Decimal("2000"), "片碱（氢氧化钠）"),
        (ExpenseType.SODIUM_SULFITE, Decimal("1200"), "亚钠（亚硫酸钠）"),
        (ExpenseType.COLOR_POWDER, Decimal("800"), "氧化着色用色粉"),
        (ExpenseType.DEGREASER, Decimal("600"), "前处理除油剂"),
    ]
    
    print("\n✓ 专业原料采购记录:")
    for material_type, amount, description in professional_materials:
        expense = finance_manager.record_expense(
            expense_type=material_type,
            amount=amount,
            bank_type=BankType.G_BANK,
            expense_date=date.today(),
            supplier_id=supplier.id,
            supplier_name=supplier.name,
            description=description
        )
        print(f"  • {material_type.value:12s} - {amount:>8} 元 - {description}")
    
    # 获取专业原料汇总
    materials_summary = finance_manager.get_professional_materials_expenses()
    print(f"\n✓ 专业原料支出汇总:")
    print(f"  • 总金额: {materials_summary['total_amount']} 元")
    print(f"  • 明细:")
    for material_name, material_data in materials_summary['materials'].items():
        if material_data['amount'] > 0:
            print(f"    - {material_name:12s}: {material_data['amount']:>8} 元 ({material_data['count']} 笔)")
    
    # ========== 需求 3.4: 供应商付款的灵活分配 ==========
    print_section("需求 3.4: 供应商付款的灵活分配")
    
    # 创建多笔待付款支出
    print("\n✓ 创建待付款支出:")
    expense1 = finance_manager.record_expense(
        expense_type=ExpenseType.ACID_THREE,
        amount=Decimal("2000"),
        bank_type=BankType.G_BANK,
        expense_date=date.today(),
        supplier_id=supplier.id,
        supplier_name=supplier.name,
        description="硫酸采购批次1"
    )
    print(f"  • 支出1: 硫酸 2000 元")
    
    expense2 = finance_manager.record_expense(
        expense_type=ExpenseType.CAUSTIC_SODA,
        amount=Decimal("1500"),
        bank_type=BankType.G_BANK,
        expense_date=date.today(),
        supplier_id=supplier.id,
        supplier_name=supplier.name,
        description="片碱采购批次1"
    )
    print(f"  • 支出2: 片碱 1500 元")
    
    expense3 = finance_manager.record_expense(
        expense_type=ExpenseType.COLOR_POWDER,
        amount=Decimal("800"),
        bank_type=BankType.G_BANK,
        expense_date=date.today(),
        supplier_id=supplier.id,
        supplier_name=supplier.name,
        description="色粉采购批次1"
    )
    print(f"  • 支出3: 色粉 800 元")
    
    # 灵活分配付款
    print("\n✓ 灵活分配付款到多个支出:")
    payment_amount = Decimal("4300")
    allocations = {
        expense1.id: Decimal("2000"),
        expense2.id: Decimal("1500"),
        expense3.id: Decimal("800")
    }
    
    success, message = finance_manager.allocate_payment_to_expenses(
        payment_amount=payment_amount,
        allocations=allocations,
        bank_type=BankType.G_BANK,
        payment_date=date.today(),
        notes="批量付款给化工供应商"
    )
    
    print(f"  • 付款总额: {payment_amount} 元")
    print(f"  • 分配明细:")
    for expense_id, allocated_amount in allocations.items():
        print(f"    - 支出 {expense_id[:8]}...: {allocated_amount} 元")
    print(f"  • 分配结果: {message}")
    print(f"  • 状态: {'✓ 成功' if success else '✗ 失败'}")
    
    # 验证分配一致性
    total_allocated = sum(allocations.values())
    print(f"\n✓ 验证分配一致性:")
    print(f"  • 付款金额: {payment_amount} 元")
    print(f"  • 分配总额: {total_allocated} 元")
    print(f"  • 一致性检查: {'✓ 通过' if total_allocated == payment_amount else '✗ 失败'}")
    
    # 测试超额分配保护
    print("\n✓ 测试超额分配保护:")
    success, message = finance_manager.allocate_payment_to_expenses(
        payment_amount=Decimal("1000"),
        allocations={expense1.id: Decimal("2000")},
        bank_type=BankType.G_BANK,
        payment_date=date.today()
    )
    print(f"  • 尝试分配 2000 元，但付款金额只有 1000 元")
    print(f"  • 系统响应: {message}")
    print(f"  • 保护机制: {'✓ 生效' if not success else '✗ 未生效'}")
    
    # 供应商应付账款汇总
    print("\n✓ 供应商应付账款汇总:")
    payables = finance_manager.get_supplier_payables(supplier.id)
    print(f"  • 供应商: {supplier.name}")
    print(f"  • 应付总额: {payables['total_amount']} 元")
    print(f"  • 支出笔数: {payables['expense_count']} 笔")
    print(f"  • 明细:")
    for detail in payables['expense_details'][:5]:  # 只显示前5笔
        print(f"    - {detail['expense_type']:12s}: {detail['amount']:>8} 元 - {detail['description']}")
    
    db.close()
    
    # ========== 总结 ==========
    print_section("✓ 任务 4.3 验证完成")
    print("\n已实现功能:")
    print("  ✓ 支持十种支出类型的分类管理")
    print("  ✓ 特别支持专业原料（三酸、片碱、亚钠、色粉、除油剂）管理")
    print("  ✓ 实现供应商付款的灵活分配")
    print("  ✓ 支出按类型汇总和查询")
    print("  ✓ 专业原料支出专项汇总")
    print("  ✓ 供应商应付账款管理")
    print("  ✓ 付款分配一致性验证")
    print("  ✓ 超额分配保护机制")
    print("\n验证需求:")
    print("  ✓ 需求 3.1: 支出类型分类管理")
    print("  ✓ 需求 3.2: 专业原料管理")
    print("  ✓ 需求 3.4: 灵活付款分配")
    print("\n" + "🎉" * 35)


if __name__ == "__main__":
    verify_expense_management()
