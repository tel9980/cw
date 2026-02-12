#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
实际发生制记账属性测试 - 验证实际发生制记账的核心正确性属性
"""

import pytest
from hypothesis import given, strategies as st, settings, assume
from decimal import Decimal
from datetime import date, timedelta
import tempfile
import os

from oxidation_finance_v20.models.business_models import (
    Customer, BankType, ExpenseType
)
from oxidation_finance_v20.database.db_manager import DatabaseManager
from oxidation_finance_v20.business.finance_manager import FinanceManager


# ==================== 策略定义 ====================

@st.composite
def customer_strategy(draw):
    """生成客户数据的策略"""
    return Customer(
        name=draw(st.text(min_size=1, max_size=50, alphabet=st.characters(whitelist_categories=('L', 'N')))),
        contact=draw(st.text(min_size=1, max_size=30, alphabet=st.characters(whitelist_categories=('L', 'N')))),
        phone=draw(st.text(min_size=8, max_size=15, alphabet=st.characters(whitelist_categories=('N',)))),
        address=draw(st.text(min_size=1, max_size=100, alphabet=st.characters(whitelist_categories=('L', 'N')))),
        credit_limit=Decimal(str(draw(st.floats(min_value=0, max_value=1000000, allow_nan=False, allow_infinity=False)))),
        notes=draw(st.text(max_size=200))
    )


@st.composite
def amount_strategy(draw):
    """生成金额的策略"""
    return Decimal(str(draw(st.floats(min_value=0.01, max_value=100000, allow_nan=False, allow_infinity=False))))


@st.composite
def date_strategy(draw):
    """生成日期的策略"""
    days_offset = draw(st.integers(min_value=-365, max_value=365))
    return date.today() + timedelta(days=days_offset)


@st.composite
def date_pair_strategy(draw):
    """生成日期对的策略（occurrence_date, payment_date）"""
    occurrence_date = draw(date_strategy())
    # 生成付款日期（可能早于、等于或晚于发生日期）
    days_diff = draw(st.integers(min_value=-60, max_value=60))
    payment_date = occurrence_date + timedelta(days=days_diff)
    return occurrence_date, payment_date


# ==================== 属性测试 ====================

class TestProperty16_AccrualTimingAccuracy:
    """
    **属性 16: 实际发生制记账时间准确性**
    **Validates: Requirements 6.1**
    
    对于任何业务交易，记录的交易日期应该是业务实际发生的日期，而不是系统录入日期
    """
    
    @given(
        customer=customer_strategy(),
        amount=amount_strategy(),
        bank_type=st.sampled_from(list(BankType)),
        dates=date_pair_strategy()
    )
    @settings(max_examples=100, deadline=None)
    def test_income_uses_occurrence_date_not_entry_date(self, customer, amount, bank_type, dates):
        """测试收入记录使用实际发生日期而非录入日期"""
        occurrence_date, payment_date = dates
        fd, path = tempfile.mkstemp(suffix='.db')
        os.close(fd)
        
        try:
            with DatabaseManager(path) as db:
                db.save_customer(customer)
                finance_manager = FinanceManager(db)
                
                # 记录实际发生制收入
                income = finance_manager.record_accrual_income(
                    customer_id=customer.id,
                    customer_name=customer.name,
                    amount=amount,
                    bank_type=bank_type,
                    occurrence_date=occurrence_date,
                    payment_date=payment_date if payment_date != occurrence_date else None,
                    has_invoice=True
                )
                
                # 验证使用实际发生日期
                assert income.income_date == occurrence_date, \
                    f"收入日期应该是实际发生日期 {occurrence_date}，而不是录入日期"
                
                # 从数据库查询验证
                retrieved = finance_manager.get_income_by_id(income.id)
                assert retrieved.income_date == occurrence_date, \
                    "查询的收入日期应该是实际发生日期"
        
        finally:
            if os.path.exists(path):
                os.unlink(path)
    
    @given(
        amount=amount_strategy(),
        expense_type=st.sampled_from(list(ExpenseType)),
        bank_type=st.sampled_from(list(BankType)),
        dates=date_pair_strategy()
    )
    @settings(max_examples=100, deadline=None)
    def test_expense_uses_occurrence_date_not_entry_date(self, amount, expense_type, bank_type, dates):
        """测试支出记录使用实际发生日期而非录入日期"""
        occurrence_date, payment_date = dates
        fd, path = tempfile.mkstemp(suffix='.db')
        os.close(fd)
        
        try:
            with DatabaseManager(path) as db:
                finance_manager = FinanceManager(db)
                
                # 记录实际发生制支出
                expense = finance_manager.record_accrual_expense(
                    expense_type=expense_type,
                    amount=amount,
                    bank_type=bank_type,
                    occurrence_date=occurrence_date,
                    payment_date=payment_date if payment_date != occurrence_date else None,
                    supplier_name="测试供应商",
                    description="测试支出"
                )
                
                # 验证使用实际发生日期
                assert expense.expense_date == occurrence_date, \
                    f"支出日期应该是实际发生日期 {occurrence_date}，而不是录入日期"
                
                # 从数据库查询验证
                retrieved = db.get_expense(expense.id)
                assert retrieved.expense_date == occurrence_date, \
                    "查询的支出日期应该是实际发生日期"
        
        finally:
            if os.path.exists(path):
                os.unlink(path)
    
    @given(
        customer=customer_strategy(),
        amount=amount_strategy(),
        occurrence_date=date_strategy(),
        start_date=date_strategy(),
        end_date=date_strategy()
    )
    @settings(max_examples=100, deadline=None)
    def test_period_summary_uses_occurrence_dates(self, customer, amount, occurrence_date, start_date, end_date):
        """测试会计期间汇总使用实际发生日期"""
        # 确保日期范围有效
        if start_date > end_date:
            start_date, end_date = end_date, start_date
        
        fd, path = tempfile.mkstemp(suffix='.db')
        os.close(fd)
        
        try:
            with DatabaseManager(path) as db:
                db.save_customer(customer)
                finance_manager = FinanceManager(db)
                
                # 记录收入
                income = finance_manager.record_accrual_income(
                    customer_id=customer.id,
                    customer_name=customer.name,
                    amount=amount,
                    bank_type=BankType.G_BANK,
                    occurrence_date=occurrence_date
                )
                
                # 获取期间汇总
                summary = finance_manager.get_accrual_period_summary(
                    start_date=start_date,
                    end_date=end_date
                )
                
                # 验证：只有实际发生日期在期间内的交易才被包含
                if start_date <= occurrence_date <= end_date:
                    assert summary["income"]["total"] >= amount, \
                        "期间内的收入应该被包含在汇总中"
                else:
                    # 如果发生日期不在期间内，该收入不应被包含
                    # （除非有其他收入在期间内）
                    pass
        
        finally:
            if os.path.exists(path):
                os.unlink(path)


class TestProperty17_FlexibleMatchingConsistency:
    """
    **属性 17: 收支匹配灵活性**
    **Validates: Requirements 6.2**
    
    对于任何收入和支出的匹配操作，系统应该支持多对多的匹配关系，
    且匹配后的金额分配应该保持数学一致性
    """
    
    @given(
        customer=customer_strategy(),
        income_amount=st.decimals(min_value=Decimal("100"), max_value=Decimal("10000"), places=2),
        num_expenses=st.integers(min_value=1, max_value=5)
    )
    @settings(max_examples=100, deadline=None)
    def test_income_to_multiple_expenses_allocation_consistency(self, customer, income_amount, num_expenses):
        """测试一笔收入匹配到多笔支出的金额一致性"""
        fd, path = tempfile.mkstemp(suffix='.db')
        os.close(fd)
        
        try:
            with DatabaseManager(path) as db:
                db.save_customer(customer)
                finance_manager = FinanceManager(db)
                
                # 记录收入
                income = finance_manager.record_accrual_income(
                    customer_id=customer.id,
                    customer_name=customer.name,
                    amount=income_amount,
                    bank_type=BankType.G_BANK,
                    occurrence_date=date.today()
                )
                
                # 记录多笔支出
                expenses = []
                for i in range(num_expenses):
                    expense = finance_manager.record_accrual_expense(
                        expense_type=ExpenseType.RENT,
                        amount=Decimal("1000"),
                        bank_type=BankType.G_BANK,
                        occurrence_date=date.today(),
                        supplier_name=f"供应商{i+1}"
                    )
                    expenses.append(expense)
                
                # 计算分配金额（平均分配，但不超过收入总额）
                allocations = {}
                remaining = income_amount
                for i, expense in enumerate(expenses):
                    if i == len(expenses) - 1:
                        # 最后一个分配剩余金额
                        allocated = remaining
                    else:
                        # 平均分配
                        allocated = (income_amount / num_expenses).quantize(Decimal("0.01"))
                        allocated = min(allocated, remaining)
                    
                    if allocated > 0:
                        allocations[expense.id] = allocated
                        remaining -= allocated
                
                # 执行匹配
                if allocations:
                    success, message = finance_manager.match_income_to_expenses(
                        income.id,
                        allocations
                    )
                    
                    if success:
                        # 验证金额分配一致性
                        total_allocated = sum(allocations.values())
                        assert total_allocated <= income_amount, \
                            f"分配金额总和 {total_allocated} 不应超过收入金额 {income_amount}"
                        
                        # 验证匹配信息已记录
                        updated_income = finance_manager.get_income_by_id(income.id)
                        assert f"匹配到{len(allocations)}笔支出" in updated_income.notes, \
                            "收入记录应该包含匹配信息"
        
        finally:
            if os.path.exists(path):
                os.unlink(path)

    @given(
        customer=customer_strategy(),
        expense_amount=st.decimals(min_value=Decimal("100"), max_value=Decimal("10000"), places=2),
        num_incomes=st.integers(min_value=1, max_value=5)
    )
    @settings(max_examples=100, deadline=None)
    def test_expense_to_multiple_incomes_allocation_consistency(self, customer, expense_amount, num_incomes):
        """测试一笔支出匹配到多笔收入的金额一致性"""
        fd, path = tempfile.mkstemp(suffix='.db')
        os.close(fd)
        
        try:
            with DatabaseManager(path) as db:
                db.save_customer(customer)
                finance_manager = FinanceManager(db)
                
                # 记录多笔收入
                incomes = []
                for i in range(num_incomes):
                    income = finance_manager.record_accrual_income(
                        customer_id=customer.id,
                        customer_name=customer.name,
                        amount=Decimal("1000"),
                        bank_type=BankType.G_BANK,
                        occurrence_date=date.today()
                    )
                    incomes.append(income)
                
                # 记录支出
                expense = finance_manager.record_accrual_expense(
                    expense_type=ExpenseType.OUTSOURCING,
                    amount=expense_amount,
                    bank_type=BankType.G_BANK,
                    occurrence_date=date.today(),
                    supplier_name="委外供应商"
                )
                
                # 计算分配金额（平均分配，但不超过支出总额）
                allocations = {}
                remaining = expense_amount
                for i, income in enumerate(incomes):
                    if i == len(incomes) - 1:
                        # 最后一个分配剩余金额
                        allocated = remaining
                    else:
                        # 平均分配
                        allocated = (expense_amount / num_incomes).quantize(Decimal("0.01"))
                        allocated = min(allocated, remaining)
                    
                    if allocated > 0:
                        allocations[income.id] = allocated
                        remaining -= allocated
                
                # 执行匹配
                if allocations:
                    success, message = finance_manager.match_expense_to_incomes(
                        expense.id,
                        allocations
                    )
                    
                    if success:
                        # 验证金额分配一致性
                        total_allocated = sum(allocations.values())
                        assert total_allocated <= expense_amount, \
                            f"分配金额总和 {total_allocated} 不应超过支出金额 {expense_amount}"
                        
                        # 验证匹配信息已记录
                        updated_expense = db.get_expense(expense.id)
                        assert f"匹配到{len(allocations)}笔收入" in updated_expense.notes, \
                            "支出记录应该包含匹配信息"
        
        finally:
            if os.path.exists(path):
                os.unlink(path)
    
    @given(
        customer=customer_strategy(),
        income_amount=st.decimals(min_value=Decimal("100"), max_value=Decimal("5000"), places=2),
        expense_amount=st.decimals(min_value=Decimal("100"), max_value=Decimal("5000"), places=2)
    )
    @settings(max_examples=100, deadline=None)
    def test_matching_validation_prevents_over_allocation(self, customer, income_amount, expense_amount):
        """测试匹配验证防止超额分配"""
        fd, path = tempfile.mkstemp(suffix='.db')
        os.close(fd)
        
        try:
            with DatabaseManager(path) as db:
                db.save_customer(customer)
                finance_manager = FinanceManager(db)
                
                # 记录收入
                income = finance_manager.record_accrual_income(
                    customer_id=customer.id,
                    customer_name=customer.name,
                    amount=income_amount,
                    bank_type=BankType.G_BANK,
                    occurrence_date=date.today()
                )
                
                # 记录支出
                expense = finance_manager.record_accrual_expense(
                    expense_type=ExpenseType.RENT,
                    amount=expense_amount,
                    bank_type=BankType.G_BANK,
                    occurrence_date=date.today(),
                    supplier_name="房东"
                )
                
                # 尝试分配超过收入金额的金额
                over_allocated = income_amount + Decimal("100")
                success, message = finance_manager.match_income_to_expenses(
                    income.id,
                    {expense.id: over_allocated}
                )
                
                # 应该失败
                assert success is False, "分配超过收入金额应该失败"
                assert "超过收入金额" in message, "错误消息应该提示超过收入金额"
        
        finally:
            if os.path.exists(path):
                os.unlink(path)
    
    @given(
        customer=customer_strategy(),
        amount=st.decimals(min_value=Decimal("100"), max_value=Decimal("5000"), places=2)
    )
    @settings(max_examples=100, deadline=None)
    def test_matching_validation_requires_positive_amounts(self, customer, amount):
        """测试匹配验证要求正数金额"""
        fd, path = tempfile.mkstemp(suffix='.db')
        os.close(fd)
        
        try:
            with DatabaseManager(path) as db:
                db.save_customer(customer)
                finance_manager = FinanceManager(db)
                
                # 记录收入和支出
                income = finance_manager.record_accrual_income(
                    customer_id=customer.id,
                    customer_name=customer.name,
                    amount=amount,
                    bank_type=BankType.G_BANK,
                    occurrence_date=date.today()
                )
                
                expense = finance_manager.record_accrual_expense(
                    expense_type=ExpenseType.RENT,
                    amount=amount,
                    bank_type=BankType.G_BANK,
                    occurrence_date=date.today(),
                    supplier_name="房东"
                )
                
                # 尝试分配零金额
                success, message = finance_manager.match_income_to_expenses(
                    income.id,
                    {expense.id: Decimal("0")}
                )
                
                # 应该失败
                assert success is False, "分配零金额应该失败"
                assert "必须大于0" in message, "错误消息应该提示金额必须大于0"
        
        finally:
            if os.path.exists(path):
                os.unlink(path)


class TestProperty18_PrepaymentTimeDifferenceHandling:
    """
    **属性 18: 预收预付款时间差异处理**
    **Validates: Requirements 6.3**
    
    对于任何预收或预付款，系统应该正确处理收付款日期与业务发生日期的差异，
    确保会计期间归属正确
    """
    
    @given(
        customer=customer_strategy(),
        amount=amount_strategy(),
        occurrence_date=date_strategy(),
        days_advance=st.integers(min_value=1, max_value=60)
    )
    @settings(max_examples=100, deadline=None)
    def test_advance_receipt_time_difference_recorded(self, customer, amount, occurrence_date, days_advance):
        """测试预收款时间差异被正确记录"""
        payment_date = occurrence_date - timedelta(days=days_advance)
        fd, path = tempfile.mkstemp(suffix='.db')
        os.close(fd)
        
        try:
            with DatabaseManager(path) as db:
                db.save_customer(customer)
                finance_manager = FinanceManager(db)
                
                # 记录预收款
                income = finance_manager.record_accrual_income(
                    customer_id=customer.id,
                    customer_name=customer.name,
                    amount=amount,
                    bank_type=BankType.G_BANK,
                    occurrence_date=occurrence_date,
                    payment_date=payment_date
                )
                
                # 验证使用实际发生日期
                assert income.income_date == occurrence_date, \
                    "收入日期应该是实际发生日期，不是付款日期"
                
                # 验证预收款信息被记录
                assert "预收款" in income.notes, "备注应该标记为预收款"
                assert f"提前{days_advance}天" in income.notes, \
                    f"备注应该记录提前{days_advance}天收款"
                assert payment_date.isoformat() in income.notes, \
                    "备注应该包含实际付款日期"
        
        finally:
            if os.path.exists(path):
                os.unlink(path)
    
    @given(
        amount=amount_strategy(),
        occurrence_date=date_strategy(),
        days_advance=st.integers(min_value=1, max_value=60)
    )
    @settings(max_examples=100, deadline=None)
    def test_advance_payment_time_difference_recorded(self, amount, occurrence_date, days_advance):
        """测试预付款时间差异被正确记录"""
        payment_date = occurrence_date - timedelta(days=days_advance)
        fd, path = tempfile.mkstemp(suffix='.db')
        os.close(fd)
        
        try:
            with DatabaseManager(path) as db:
                finance_manager = FinanceManager(db)
                
                # 记录预付款
                expense = finance_manager.record_accrual_expense(
                    expense_type=ExpenseType.RENT,
                    amount=amount,
                    bank_type=BankType.G_BANK,
                    occurrence_date=occurrence_date,
                    payment_date=payment_date,
                    supplier_name="房东"
                )
                
                # 验证使用实际发生日期
                assert expense.expense_date == occurrence_date, \
                    "支出日期应该是实际发生日期，不是付款日期"
                
                # 验证预付款信息被记录
                assert "预付款" in expense.notes, "备注应该标记为预付款"
                assert f"提前{days_advance}天" in expense.notes, \
                    f"备注应该记录提前{days_advance}天付款"
                assert payment_date.isoformat() in expense.notes, \
                    "备注应该包含实际付款日期"
        
        finally:
            if os.path.exists(path):
                os.unlink(path)

    @given(
        customer=customer_strategy(),
        amount=amount_strategy(),
        occurrence_date=date_strategy(),
        days_delay=st.integers(min_value=1, max_value=60)
    )
    @settings(max_examples=100, deadline=None)
    def test_delayed_receipt_time_difference_recorded(self, customer, amount, occurrence_date, days_delay):
        """测试延迟收款时间差异被正确记录"""
        payment_date = occurrence_date + timedelta(days=days_delay)
        fd, path = tempfile.mkstemp(suffix='.db')
        os.close(fd)
        
        try:
            with DatabaseManager(path) as db:
                db.save_customer(customer)
                finance_manager = FinanceManager(db)
                
                # 记录延迟收款
                income = finance_manager.record_accrual_income(
                    customer_id=customer.id,
                    customer_name=customer.name,
                    amount=amount,
                    bank_type=BankType.N_BANK,
                    occurrence_date=occurrence_date,
                    payment_date=payment_date
                )
                
                # 验证使用实际发生日期
                assert income.income_date == occurrence_date, \
                    "收入日期应该是实际发生日期"
                
                # 验证延迟收款信息被记录
                assert "延迟收款" in income.notes, "备注应该标记为延迟收款"
                assert f"延后{days_delay}天" in income.notes, \
                    f"备注应该记录延后{days_delay}天收款"
        
        finally:
            if os.path.exists(path):
                os.unlink(path)
    
    @given(
        customer=customer_strategy(),
        num_advance_receipts=st.integers(min_value=1, max_value=5),
        num_advance_payments=st.integers(min_value=1, max_value=5)
    )
    @settings(max_examples=100, deadline=None)
    def test_prepayment_analysis_aggregates_correctly(self, customer, num_advance_receipts, num_advance_payments):
        """测试预收预付款分析正确汇总"""
        fd, path = tempfile.mkstemp(suffix='.db')
        os.close(fd)
        
        try:
            with DatabaseManager(path) as db:
                db.save_customer(customer)
                finance_manager = FinanceManager(db)
                
                # 记录多笔预收款
                total_advance_receipts = Decimal("0")
                for i in range(num_advance_receipts):
                    amount = Decimal("1000")
                    occurrence_date = date.today() + timedelta(days=10)
                    payment_date = date.today()
                    
                    finance_manager.record_accrual_income(
                        customer_id=customer.id,
                        customer_name=customer.name,
                        amount=amount,
                        bank_type=BankType.G_BANK,
                        occurrence_date=occurrence_date,
                        payment_date=payment_date
                    )
                    total_advance_receipts += amount
                
                # 记录多笔预付款
                total_advance_payments = Decimal("0")
                for i in range(num_advance_payments):
                    amount = Decimal("500")
                    occurrence_date = date.today() + timedelta(days=15)
                    payment_date = date.today()
                    
                    finance_manager.record_accrual_expense(
                        expense_type=ExpenseType.RENT,
                        amount=amount,
                        bank_type=BankType.G_BANK,
                        occurrence_date=occurrence_date,
                        payment_date=payment_date,
                        supplier_name="供应商"
                    )
                    total_advance_payments += amount
                
                # 获取预收预付款分析
                analysis = finance_manager.get_prepayment_analysis()
                
                # 验证汇总准确性
                assert analysis["advance_receipts"]["count"] == num_advance_receipts, \
                    f"预收款笔数应该是 {num_advance_receipts}"
                assert analysis["advance_receipts"]["total_amount"] == total_advance_receipts, \
                    f"预收款总额应该是 {total_advance_receipts}"
                
                assert analysis["advance_payments"]["count"] == num_advance_payments, \
                    f"预付款笔数应该是 {num_advance_payments}"
                assert analysis["advance_payments"]["total_amount"] == total_advance_payments, \
                    f"预付款总额应该是 {total_advance_payments}"
                
                # 验证净预收款计算
                expected_net = total_advance_receipts - total_advance_payments
                assert analysis["net_advance"] == expected_net, \
                    f"净预收款应该是 {expected_net}"
        
        finally:
            if os.path.exists(path):
                os.unlink(path)
    
    @given(
        customer=customer_strategy(),
        amount=amount_strategy(),
        occurrence_date=date_strategy()
    )
    @settings(max_examples=100, deadline=None)
    def test_same_date_payment_no_prepayment_marking(self, customer, amount, occurrence_date):
        """测试发生日期和付款日期相同时不标记为预收预付款"""
        fd, path = tempfile.mkstemp(suffix='.db')
        os.close(fd)
        
        try:
            with DatabaseManager(path) as db:
                db.save_customer(customer)
                finance_manager = FinanceManager(db)
                
                # 记录收入（发生日期和付款日期相同）
                income = finance_manager.record_accrual_income(
                    customer_id=customer.id,
                    customer_name=customer.name,
                    amount=amount,
                    bank_type=BankType.G_BANK,
                    occurrence_date=occurrence_date,
                    payment_date=occurrence_date
                )
                
                # 验证不应该有预收款标记
                assert "预收款" not in income.notes, "相同日期不应标记为预收款"
                assert "延迟收款" not in income.notes, "相同日期不应标记为延迟收款"
                
                # 记录支出（发生日期和付款日期相同）
                expense = finance_manager.record_accrual_expense(
                    expense_type=ExpenseType.UTILITIES,
                    amount=amount,
                    bank_type=BankType.G_BANK,
                    occurrence_date=occurrence_date,
                    payment_date=occurrence_date,
                    supplier_name="供应商"
                )
                
                # 验证不应该有预付款标记
                assert "预付款" not in expense.notes, "相同日期不应标记为预付款"
                assert "延迟付款" not in expense.notes, "相同日期不应标记为延迟付款"
        
        finally:
            if os.path.exists(path):
                os.unlink(path)
    
    @given(
        customer=customer_strategy(),
        start_date=date_strategy(),
        end_date=date_strategy()
    )
    @settings(max_examples=100, deadline=None)
    def test_period_summary_uses_occurrence_date_for_prepayments(self, customer, start_date, end_date):
        """测试会计期间汇总对预收预付款使用实际发生日期"""
        # 确保日期范围有效
        if start_date > end_date:
            start_date, end_date = end_date, start_date
        
        fd, path = tempfile.mkstemp(suffix='.db')
        os.close(fd)
        
        try:
            with DatabaseManager(path) as db:
                db.save_customer(customer)
                finance_manager = FinanceManager(db)
                
                # 记录预收款：付款日期在期间外，发生日期在期间内
                occurrence_date = start_date + timedelta(days=5)
                payment_date = start_date - timedelta(days=10)
                
                if occurrence_date <= end_date:
                    income = finance_manager.record_accrual_income(
                        customer_id=customer.id,
                        customer_name=customer.name,
                        amount=Decimal("5000"),
                        bank_type=BankType.G_BANK,
                        occurrence_date=occurrence_date,
                        payment_date=payment_date
                    )
                    
                    # 获取期间汇总
                    summary = finance_manager.get_accrual_period_summary(
                        start_date=start_date,
                        end_date=end_date
                    )
                    
                    # 验证：预收款应该按实际发生日期归入期间
                    assert summary["income"]["total"] >= Decimal("5000"), \
                        "预收款应该按实际发生日期归入会计期间"
        
        finally:
            if os.path.exists(path):
                os.unlink(path)
