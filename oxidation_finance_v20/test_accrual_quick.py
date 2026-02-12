#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
快速验证实际发生制记账功能
"""

import sys
from pathlib import Path
from decimal import Decimal
from datetime import date

# 添加项目根目录到路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from business.finance_manager import FinanceManager
from models.business_models import BankType, ExpenseType
from database.db_manager import DatabaseManager


def test_accrual_income():
    """测试实际发生制收入记录"""
    print("\n测试1: 实际发生制收入记录")
    print("-" * 50)
    
    db_path = project_root / "test_accrual_quick.db"
    if db_path.exists():
        db_path.unlink()
    
    db_manager = DatabaseManager(str(db_path))
    finance_manager = FinanceManager(db_manager)
    
    # 测试按实际发生日期记录收入
    occurrence_date = date(2024, 1, 15)
    income = finance_manager.record_accrual_income(
        customer_id="C001",
        customer_name="客户A",
        amount=Decimal("10000"),
        bank_type=BankType.G_BANK,
        occurrence_date=occurrence_date,
        has_invoice=True,
        notes="订单001收款"
    )
    
    assert income.income_date == occurrence_date, "收入日期应该是实际发生日期"
    assert income.amount == Decimal("10000"), "收入金额应该正确"
    print(f"✓ 收入记录创建成功: {income.customer_name}, {income.amount}元, 日期: {income.income_date}")
    
    # 测试预收款
    occurrence_date2 = date(2024, 1, 20)
    payment_date2 = date(2024, 1, 10)
    income2 = finance_manager.record_accrual_income(
        customer_id="C002",
        customer_name="客户B",
        amount=Decimal("5000"),
        bank_type=BankType.N_BANK,
        occurrence_date=occurrence_date2,
        payment_date=payment_date2,
        notes="预收款"
    )
    
    assert income2.income_date == occurrence_date2, "应该使用实际发生日期"
    assert "预收款" in income2.notes, "应该标记为预收款"
    assert "提前10天" in income2.notes, "应该记录提前天数"
    print(f"✓ 预收款记录成功: {income2.customer_name}, 提前10天收款")
    
    db_path.unlink()
    print("✓ 测试1通过\n")


def test_accrual_expense():
    """测试实际发生制支出记录"""
    print("测试2: 实际发生制支出记录")
    print("-" * 50)
    
    db_path = project_root / "test_accrual_quick.db"
    if db_path.exists():
        db_path.unlink()
    
    db_manager = DatabaseManager(str(db_path))
    finance_manager = FinanceManager(db_manager)
    
    # 测试按实际发生日期记录支出
    occurrence_date = date(2024, 1, 15)
    expense = finance_manager.record_accrual_expense(
        expense_type=ExpenseType.ACID_THREE,
        amount=Decimal("3000"),
        bank_type=BankType.G_BANK,
        occurrence_date=occurrence_date,
        supplier_name="供应商A",
        description="采购硫酸"
    )
    
    assert expense.expense_date == occurrence_date, "支出日期应该是实际发生日期"
    assert expense.amount == Decimal("3000"), "支出金额应该正确"
    print(f"✓ 支出记录创建成功: {expense.expense_type.value}, {expense.amount}元, 日期: {expense.expense_date}")
    
    # 测试预付款
    occurrence_date2 = date(2024, 1, 20)
    payment_date2 = date(2024, 1, 5)
    expense2 = finance_manager.record_accrual_expense(
        expense_type=ExpenseType.RENT,
        amount=Decimal("5000"),
        bank_type=BankType.G_BANK,
        occurrence_date=occurrence_date2,
        payment_date=payment_date2,
        description="厂房租金"
    )
    
    assert expense2.expense_date == occurrence_date2, "应该使用实际发生日期"
    assert "预付款" in expense2.notes, "应该标记为预付款"
    assert "提前15天" in expense2.notes, "应该记录提前天数"
    print(f"✓ 预付款记录成功: {expense2.expense_type.value}, 提前15天付款")
    
    db_path.unlink()
    print("✓ 测试2通过\n")


def test_flexible_matching():
    """测试收支灵活匹配"""
    print("测试3: 收支灵活匹配")
    print("-" * 50)
    
    db_path = project_root / "test_accrual_quick.db"
    if db_path.exists():
        db_path.unlink()
    
    db_manager = DatabaseManager(str(db_path))
    finance_manager = FinanceManager(db_manager)
    
    # 记录一笔收入
    income = finance_manager.record_accrual_income(
        customer_id="C001",
        customer_name="客户A",
        amount=Decimal("10000"),
        bank_type=BankType.G_BANK,
        occurrence_date=date(2024, 1, 15)
    )
    
    # 记录多笔支出
    expense1 = finance_manager.record_accrual_expense(
        expense_type=ExpenseType.ACID_THREE,
        amount=Decimal("3000"),
        bank_type=BankType.G_BANK,
        occurrence_date=date(2024, 1, 10),
        supplier_name="供应商A"
    )
    
    expense2 = finance_manager.record_accrual_expense(
        expense_type=ExpenseType.RENT,
        amount=Decimal("5000"),
        bank_type=BankType.G_BANK,
        occurrence_date=date(2024, 1, 12),
        supplier_name="房东"
    )
    
    # 将收入匹配到多笔支出
    success, message = finance_manager.match_income_to_expenses(
        income.id,
        {
            expense1.id: Decimal("3000"),
            expense2.id: Decimal("5000")
        }
    )
    
    assert success is True, f"匹配应该成功: {message}"
    assert "成功匹配" in message, "应该返回成功消息"
    print(f"✓ 收入匹配到多笔支出成功: {message}")
    
    # 验证匹配信息已记录
    updated_income = finance_manager.get_income_by_id(income.id)
    assert "匹配到2笔支出" in updated_income.notes, "应该记录匹配信息"
    print(f"✓ 匹配信息已记录: {updated_income.notes[:50]}...")
    
    db_path.unlink()
    print("✓ 测试3通过\n")


def test_prepayment_analysis():
    """测试预收预付款分析"""
    print("测试4: 预收预付款分析")
    print("-" * 50)
    
    db_path = project_root / "test_accrual_quick.db"
    if db_path.exists():
        db_path.unlink()
    
    db_manager = DatabaseManager(str(db_path))
    finance_manager = FinanceManager(db_manager)
    
    # 记录预收款
    finance_manager.record_accrual_income(
        customer_id="C001",
        customer_name="客户A",
        amount=Decimal("5000"),
        bank_type=BankType.G_BANK,
        occurrence_date=date(2024, 1, 20),
        payment_date=date(2024, 1, 10)
    )
    
    finance_manager.record_accrual_income(
        customer_id="C002",
        customer_name="客户B",
        amount=Decimal("3000"),
        bank_type=BankType.N_BANK,
        occurrence_date=date(2024, 1, 25),
        payment_date=date(2024, 1, 15)
    )
    
    # 记录预付款
    finance_manager.record_accrual_expense(
        expense_type=ExpenseType.RENT,
        amount=Decimal("4000"),
        bank_type=BankType.G_BANK,
        occurrence_date=date(2024, 1, 30),
        payment_date=date(2024, 1, 5)
    )
    
    # 分析预收预付款
    analysis = finance_manager.get_prepayment_analysis()
    
    assert analysis["advance_receipts"]["count"] == 2, "应该有2笔预收款"
    assert analysis["advance_receipts"]["total_amount"] == Decimal("8000"), "预收款总额应该是8000"
    assert analysis["advance_payments"]["count"] == 1, "应该有1笔预付款"
    assert analysis["advance_payments"]["total_amount"] == Decimal("4000"), "预付款总额应该是4000"
    assert analysis["net_advance"] == Decimal("4000"), "净预收应该是4000"
    
    print(f"✓ 预收款: {analysis['advance_receipts']['count']}笔, 总额: {analysis['advance_receipts']['total_amount']}元")
    print(f"✓ 预付款: {analysis['advance_payments']['count']}笔, 总额: {analysis['advance_payments']['total_amount']}元")
    print(f"✓ 净预收: {analysis['net_advance']}元")
    
    db_path.unlink()
    print("✓ 测试4通过\n")


def test_period_summary():
    """测试会计期间汇总"""
    print("测试5: 会计期间汇总")
    print("-" * 50)
    
    db_path = project_root / "test_accrual_quick.db"
    if db_path.exists():
        db_path.unlink()
    
    db_manager = DatabaseManager(str(db_path))
    finance_manager = FinanceManager(db_manager)
    
    # 记录期间内的收入
    finance_manager.record_accrual_income(
        customer_id="C001",
        customer_name="客户A",
        amount=Decimal("10000"),
        bank_type=BankType.G_BANK,
        occurrence_date=date(2024, 1, 15)
    )
    
    finance_manager.record_accrual_income(
        customer_id="C002",
        customer_name="客户B",
        amount=Decimal("5000"),
        bank_type=BankType.N_BANK,
        occurrence_date=date(2024, 1, 20)
    )
    
    # 记录期间内的支出
    finance_manager.record_accrual_expense(
        expense_type=ExpenseType.RENT,
        amount=Decimal("3000"),
        bank_type=BankType.G_BANK,
        occurrence_date=date(2024, 1, 10),
        supplier_name="房东"
    )
    
    finance_manager.record_accrual_expense(
        expense_type=ExpenseType.ACID_THREE,
        amount=Decimal("2000"),
        bank_type=BankType.G_BANK,
        occurrence_date=date(2024, 1, 18),
        supplier_name="供应商A"
    )
    
    # 获取期间汇总
    summary = finance_manager.get_accrual_period_summary(
        start_date=date(2024, 1, 1),
        end_date=date(2024, 1, 31)
    )
    
    assert summary["income"]["total"] == Decimal("15000"), "收入总额应该是15000"
    assert summary["income"]["count"] == 2, "应该有2笔收入"
    assert summary["expense"]["total"] == Decimal("5000"), "支出总额应该是5000"
    assert summary["expense"]["count"] == 2, "应该有2笔支出"
    assert summary["net_profit"] == Decimal("10000"), "净利润应该是10000"
    
    print(f"✓ 收入总额: {summary['income']['total']}元 ({summary['income']['count']}笔)")
    print(f"✓ 支出总额: {summary['expense']['total']}元 ({summary['expense']['count']}笔)")
    print(f"✓ 净利润: {summary['net_profit']}元")
    print(f"✓ 利润率: {summary['profit_margin']}%")
    
    db_path.unlink()
    print("✓ 测试5通过\n")


def main():
    """运行所有测试"""
    print("\n" + "=" * 60)
    print("实际发生制记账功能快速验证")
    print("=" * 60)
    
    try:
        test_accrual_income()
        test_accrual_expense()
        test_flexible_matching()
        test_prepayment_analysis()
        test_period_summary()
        
        print("=" * 60)
        print("✓ 所有测试通过!")
        print("=" * 60)
        return 0
    except AssertionError as e:
        print(f"\n✗ 测试失败: {e}")
        return 1
    except Exception as e:
        print(f"\n✗ 错误: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
