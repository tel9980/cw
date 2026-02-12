#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
实际发生制记账功能测试
"""

import pytest
from decimal import Decimal
from datetime import date, timedelta
from ..business.finance_manager import FinanceManager
from ..models.business_models import BankType, ExpenseType
from ..database.db_manager import DatabaseManager


@pytest.fixture
def finance_manager(tmp_path):
    """创建测试用的财务管理器"""
    db_path = tmp_path / "test_accrual.db"
    db_manager = DatabaseManager(str(db_path))
    return FinanceManager(db_manager)


class TestAccrualIncome:
    """测试实际发生制收入记录"""
    
    def test_record_income_with_occurrence_date(self, finance_manager):
        """测试按实际发生日期记录收入"""
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
        
        assert income.income_date == occurrence_date
        assert income.amount == Decimal("10000")
        assert income.customer_name == "客户A"
        assert income.bank_type == BankType.G_BANK
    
    def test_record_advance_receipt(self, finance_manager):
        """测试记录预收款（付款日期早于发生日期）"""
        occurrence_date = date(2024, 1, 20)
        payment_date = date(2024, 1, 10)  # 提前10天收款
        
        income = finance_manager.record_accrual_income(
            customer_id="C002",
            customer_name="客户B",
            amount=Decimal("5000"),
            bank_type=BankType.N_BANK,
            occurrence_date=occurrence_date,
            payment_date=payment_date,
            notes="预收款"
        )
        
        # 应该使用实际发生日期
        assert income.income_date == occurrence_date
        # 备注中应该记录预收款信息
        assert "预收款" in income.notes
        assert "提前10天" in income.notes
        assert payment_date.isoformat() in income.notes
    
    def test_record_delayed_receipt(self, finance_manager):
        """测试记录延迟收款（付款日期晚于发生日期）"""
        occurrence_date = date(2024, 1, 10)
        payment_date = date(2024, 1, 25)  # 延后15天收款
        
        income = finance_manager.record_accrual_income(
            customer_id="C003",
            customer_name="客户C",
            amount=Decimal("8000"),
            bank_type=BankType.G_BANK,
            occurrence_date=occurrence_date,
            payment_date=payment_date
        )
        
        assert income.income_date == occurrence_date
        assert "延迟收款" in income.notes
        assert "延后15天" in income.notes


class TestAccrualExpense:
    """测试实际发生制支出记录"""
    
    def test_record_expense_with_occurrence_date(self, finance_manager):
        """测试按实际发生日期记录支出"""
        occurrence_date = date(2024, 1, 15)
        
        expense = finance_manager.record_accrual_expense(
            expense_type=ExpenseType.ACID_THREE,
            amount=Decimal("3000"),
            bank_type=BankType.G_BANK,
            occurrence_date=occurrence_date,
            supplier_name="供应商A",
            description="采购硫酸"
        )
        
        assert expense.expense_date == occurrence_date
        assert expense.amount == Decimal("3000")
        assert expense.expense_type == ExpenseType.ACID_THREE
    
    def test_record_advance_payment(self, finance_manager):
        """测试记录预付款（付款日期早于发生日期）"""
        occurrence_date = date(2024, 1, 20)
        payment_date = date(2024, 1, 5)  # 提前15天付款
        
        expense = finance_manager.record_accrual_expense(
            expense_type=ExpenseType.RENT,
            amount=Decimal("5000"),
            bank_type=BankType.G_BANK,
            occurrence_date=occurrence_date,
            payment_date=payment_date,
            description="厂房租金"
        )
        
        # 应该使用实际发生日期
        assert expense.expense_date == occurrence_date
        # 备注中应该记录预付款信息
        assert "预付款" in expense.notes
        assert "提前15天" in expense.notes
        assert payment_date.isoformat() in expense.notes
    
    def test_record_delayed_payment(self, finance_manager):
        """测试记录延迟付款（付款日期晚于发生日期）"""
        occurrence_date = date(2024, 1, 10)
        payment_date = date(2024, 1, 30)  # 延后20天付款
        
        expense = finance_manager.record_accrual_expense(
            expense_type=ExpenseType.UTILITIES,
            amount=Decimal("2000"),
            bank_type=BankType.N_BANK,
            occurrence_date=occurrence_date,
            payment_date=payment_date,
            description="水电费"
        )
        
        assert expense.expense_date == occurrence_date
        assert "延迟付款" in expense.notes
        assert "延后20天" in expense.notes


class TestFlexibleMatching:
    """测试收支灵活匹配"""
    
    def test_match_income_to_multiple_expenses(self, finance_manager):
        """测试将一笔收入匹配到多笔支出"""
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
        
        assert success is True
        assert "成功匹配" in message
        
        # 验证匹配信息已记录
        updated_income = finance_manager.get_income_by_id(income.id)
        assert "匹配到2笔支出" in updated_income.notes
    
    def test_match_expense_to_multiple_incomes(self, finance_manager):
        """测试将一笔支出匹配到多笔收入"""
        # 记录多笔收入
        income1 = finance_manager.record_accrual_income(
            customer_id="C001",
            customer_name="客户A",
            amount=Decimal("5000"),
            bank_type=BankType.G_BANK,
            occurrence_date=date(2024, 1, 10)
        )
        
        income2 = finance_manager.record_accrual_income(
            customer_id="C002",
            customer_name="客户B",
            amount=Decimal("3000"),
            bank_type=BankType.G_BANK,
            occurrence_date=date(2024, 1, 12)
        )
        
        # 记录一笔支出
        expense = finance_manager.record_accrual_expense(
            expense_type=ExpenseType.OUTSOURCING,
            amount=Decimal("7000"),
            bank_type=BankType.G_BANK,
            occurrence_date=date(2024, 1, 15),
            supplier_name="委外供应商"
        )
        
        # 将支出匹配到多笔收入
        success, message = finance_manager.match_expense_to_incomes(
            expense.id,
            {
                income1.id: Decimal("4000"),
                income2.id: Decimal("2500")
            }
        )
        
        assert success is True
        assert "成功匹配" in message
        
        # 验证匹配信息已记录
        updated_expense = finance_manager.db.get_expense(expense.id)
        assert "匹配到2笔收入" in updated_expense.notes
    
    def test_match_validation_amount_exceeds(self, finance_manager):
        """测试匹配验证：分配金额超过总额"""
        income = finance_manager.record_accrual_income(
            customer_id="C001",
            customer_name="客户A",
            amount=Decimal("5000"),
            bank_type=BankType.G_BANK,
            occurrence_date=date(2024, 1, 15)
        )
        
        expense = finance_manager.record_accrual_expense(
            expense_type=ExpenseType.RENT,
            amount=Decimal("6000"),
            bank_type=BankType.G_BANK,
            occurrence_date=date(2024, 1, 10),
            supplier_name="房东"
        )
        
        # 尝试分配超过收入总额的金额
        success, message = finance_manager.match_income_to_expenses(
            income.id,
            {expense.id: Decimal("6000")}
        )
        
        assert success is False
        assert "超过收入金额" in message
    
    def test_match_validation_nonexistent_record(self, finance_manager):
        """测试匹配验证：记录不存在"""
        income = finance_manager.record_accrual_income(
            customer_id="C001",
            customer_name="客户A",
            amount=Decimal("5000"),
            bank_type=BankType.G_BANK,
            occurrence_date=date(2024, 1, 15)
        )
        
        # 尝试匹配到不存在的支出
        success, message = finance_manager.match_income_to_expenses(
            income.id,
            {"nonexistent_id": Decimal("1000")}
        )
        
        assert success is False
        assert "不存在" in message


class TestPrepaymentAnalysis:
    """测试预收预付款分析"""
    
    def test_analyze_advance_receipts_and_payments(self, finance_manager):
        """测试分析预收预付款"""
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
        
        assert analysis["advance_receipts"]["count"] == 2
        assert analysis["advance_receipts"]["total_amount"] == Decimal("8000")
        assert analysis["advance_payments"]["count"] == 1
        assert analysis["advance_payments"]["total_amount"] == Decimal("4000")
        assert analysis["net_advance"] == Decimal("4000")
    
    def test_analyze_with_date_range(self, finance_manager):
        """测试按日期范围分析预收预付款"""
        # 记录不同日期的预收款
        finance_manager.record_accrual_income(
            customer_id="C001",
            customer_name="客户A",
            amount=Decimal("5000"),
            bank_type=BankType.G_BANK,
            occurrence_date=date(2024, 1, 15),
            payment_date=date(2024, 1, 10)
        )
        
        finance_manager.record_accrual_income(
            customer_id="C002",
            customer_name="客户B",
            amount=Decimal("3000"),
            bank_type=BankType.G_BANK,
            occurrence_date=date(2024, 2, 15),
            payment_date=date(2024, 2, 10)
        )
        
        # 只分析1月份的
        analysis = finance_manager.get_prepayment_analysis(
            start_date=date(2024, 1, 1),
            end_date=date(2024, 1, 31)
        )
        
        assert analysis["advance_receipts"]["count"] == 1
        assert analysis["advance_receipts"]["total_amount"] == Decimal("5000")


class TestAccrualPeriodSummary:
    """测试会计期间汇总"""
    
    def test_period_summary_basic(self, finance_manager):
        """测试基本的会计期间汇总"""
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
        
        assert summary["income"]["total"] == Decimal("15000")
        assert summary["income"]["count"] == 2
        assert summary["income"]["g_bank"] == Decimal("10000")
        assert summary["income"]["n_bank"] == Decimal("5000")
        
        assert summary["expense"]["total"] == Decimal("5000")
        assert summary["expense"]["count"] == 2
        
        assert summary["net_profit"] == Decimal("10000")
    
    def test_period_summary_excludes_outside_dates(self, finance_manager):
        """测试期间汇总排除期间外的数据"""
        # 期间内的收入
        finance_manager.record_accrual_income(
            customer_id="C001",
            customer_name="客户A",
            amount=Decimal("10000"),
            bank_type=BankType.G_BANK,
            occurrence_date=date(2024, 1, 15)
        )
        
        # 期间外的收入（应该被排除）
        finance_manager.record_accrual_income(
            customer_id="C002",
            customer_name="客户B",
            amount=Decimal("5000"),
            bank_type=BankType.G_BANK,
            occurrence_date=date(2024, 2, 15)
        )
        
        # 获取1月份的汇总
        summary = finance_manager.get_accrual_period_summary(
            start_date=date(2024, 1, 1),
            end_date=date(2024, 1, 31)
        )
        
        # 只应该包含1月份的收入
        assert summary["income"]["total"] == Decimal("10000")
        assert summary["income"]["count"] == 1
    
    def test_period_summary_by_expense_type(self, finance_manager):
        """测试按支出类型分类的期间汇总"""
        # 记录不同类型的支出
        finance_manager.record_accrual_expense(
            expense_type=ExpenseType.RENT,
            amount=Decimal("5000"),
            bank_type=BankType.G_BANK,
            occurrence_date=date(2024, 1, 10),
            supplier_name="房东"
        )
        
        finance_manager.record_accrual_expense(
            expense_type=ExpenseType.RENT,
            amount=Decimal("5000"),
            bank_type=BankType.G_BANK,
            occurrence_date=date(2024, 1, 15),
            supplier_name="房东"
        )
        
        finance_manager.record_accrual_expense(
            expense_type=ExpenseType.ACID_THREE,
            amount=Decimal("3000"),
            bank_type=BankType.G_BANK,
            occurrence_date=date(2024, 1, 20),
            supplier_name="供应商A"
        )
        
        # 获取期间汇总
        summary = finance_manager.get_accrual_period_summary(
            start_date=date(2024, 1, 1),
            end_date=date(2024, 1, 31)
        )
        
        # 验证按类型分类
        assert summary["expense"]["by_type"]["房租"] == Decimal("10000")
        assert summary["expense"]["by_type"]["三酸"] == Decimal("3000")
    
    def test_period_summary_profit_margin(self, finance_manager):
        """测试利润率计算"""
        # 记录收入和支出
        finance_manager.record_accrual_income(
            customer_id="C001",
            customer_name="客户A",
            amount=Decimal("10000"),
            bank_type=BankType.G_BANK,
            occurrence_date=date(2024, 1, 15)
        )
        
        finance_manager.record_accrual_expense(
            expense_type=ExpenseType.RENT,
            amount=Decimal("3000"),
            bank_type=BankType.G_BANK,
            occurrence_date=date(2024, 1, 10),
            supplier_name="房东"
        )
        
        # 获取期间汇总
        summary = finance_manager.get_accrual_period_summary(
            start_date=date(2024, 1, 1),
            end_date=date(2024, 1, 31)
        )
        
        # 净利润 = 10000 - 3000 = 7000
        # 利润率 = 7000 / 10000 * 100 = 70%
        assert summary["net_profit"] == Decimal("7000")
        assert summary["profit_margin"] == Decimal("70")


class TestEdgeCases:
    """测试边界情况"""
    
    def test_same_occurrence_and_payment_date(self, finance_manager):
        """测试发生日期和付款日期相同的情况"""
        same_date = date(2024, 1, 15)
        
        income = finance_manager.record_accrual_income(
            customer_id="C001",
            customer_name="客户A",
            amount=Decimal("5000"),
            bank_type=BankType.G_BANK,
            occurrence_date=same_date,
            payment_date=same_date
        )
        
        # 不应该有预收款或延迟收款的标记
        assert "预收款" not in income.notes
        assert "延迟收款" not in income.notes
    
    def test_zero_amount_matching(self, finance_manager):
        """测试零金额匹配的验证"""
        income = finance_manager.record_accrual_income(
            customer_id="C001",
            customer_name="客户A",
            amount=Decimal("5000"),
            bank_type=BankType.G_BANK,
            occurrence_date=date(2024, 1, 15)
        )
        
        expense = finance_manager.record_accrual_expense(
            expense_type=ExpenseType.RENT,
            amount=Decimal("3000"),
            bank_type=BankType.G_BANK,
            occurrence_date=date(2024, 1, 10),
            supplier_name="房东"
        )
        
        # 尝试分配零金额
        success, message = finance_manager.match_income_to_expenses(
            income.id,
            {expense.id: Decimal("0")}
        )
        
        assert success is False
        assert "必须大于0" in message
    
    def test_empty_period_summary(self, finance_manager):
        """测试空期间的汇总"""
        summary = finance_manager.get_accrual_period_summary(
            start_date=date(2024, 1, 1),
            end_date=date(2024, 1, 31)
        )
        
        assert summary["income"]["total"] == Decimal("0")
        assert summary["expense"]["total"] == Decimal("0")
        assert summary["net_profit"] == Decimal("0")
        assert summary["profit_margin"] == Decimal("0")
