#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
银行账户管理属性测试 - 验证银行账户管理的核心正确性属性
"""

import pytest
from hypothesis import given, strategies as st, settings, assume
from decimal import Decimal
from datetime import date, timedelta
import tempfile
import os

from oxidation_finance_v20.models.business_models import (
    Customer, Supplier, BankType, ExpenseType
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
def supplier_strategy(draw):
    """生成供应商数据的策略"""
    return Supplier(
        name=draw(st.text(min_size=1, max_size=50, alphabet=st.characters(whitelist_categories=('L', 'N')))),
        contact=draw(st.text(min_size=1, max_size=30, alphabet=st.characters(whitelist_categories=('L', 'N')))),
        phone=draw(st.text(min_size=8, max_size=15, alphabet=st.characters(whitelist_categories=('N',)))),
        address=draw(st.text(min_size=1, max_size=100, alphabet=st.characters(whitelist_categories=('L', 'N')))),
        business_type=draw(st.text(min_size=1, max_size=50, alphabet=st.characters(whitelist_categories=('L', 'N')))),
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


# ==================== 属性测试 ====================

class TestProperty8_BankAccountTypeIdentificationAccuracy:
    """
    **属性 8: 银行账户类型识别准确性**
    **Validates: Requirements 2.3, 4.2, 4.3**
    
    对于任何收入记录，G银行交易应该正确标记票据信息，N银行交易应该被标记为现金等价物
    """
    
    @given(
        customer=customer_strategy(),
        amount=amount_strategy(),
        has_invoice=st.booleans()
    )
    @settings(max_examples=100, deadline=None)
    def test_g_bank_invoice_marking_accuracy(self, customer, amount, has_invoice):
        """测试G银行交易的票据标记准确性"""
        fd, path = tempfile.mkstemp(suffix='.db')
        os.close(fd)
        
        try:
            with DatabaseManager(path) as db:
                db.save_customer(customer)
                finance_manager = FinanceManager(db)
                
                # 记录G银行收入
                income = finance_manager.record_income(
                    customer_id=customer.id,
                    customer_name=customer.name,
                    amount=amount,
                    bank_type=BankType.G_BANK,
                    income_date=date.today(),
                    has_invoice=has_invoice,
                    notes="G银行交易"
                )
                
                # 验证银行类型识别
                assert income.bank_type == BankType.G_BANK, "应该正确识别为G银行"
                assert income.has_invoice == has_invoice, f"票据标记应该为 {has_invoice}"
                
                # 从数据库查询验证
                retrieved = finance_manager.get_income_by_id(income.id)
                assert retrieved.bank_type == BankType.G_BANK, "查询的银行类型应该是G银行"
                assert retrieved.has_invoice == has_invoice, f"查询的票据标记应该为 {has_invoice}"
                
                # 验证G银行特性在汇总中体现
                summary = finance_manager.get_bank_account_summary(BankType.G_BANK)
                assert "票据" in summary["special_notes"][0], "G银行汇总应该标注票据特性"
        
        finally:
            if os.path.exists(path):
                os.unlink(path)

    @given(
        customer=customer_strategy(),
        amount=amount_strategy()
    )
    @settings(max_examples=100, deadline=None)
    def test_n_bank_cash_equivalent_identification(self, customer, amount):
        """测试N银行交易作为现金等价物的识别"""
        fd, path = tempfile.mkstemp(suffix='.db')
        os.close(fd)
        
        try:
            with DatabaseManager(path) as db:
                db.save_customer(customer)
                finance_manager = FinanceManager(db)
                
                # 记录N银行收入（现金等价物）
                income = finance_manager.record_income(
                    customer_id=customer.id,
                    customer_name=customer.name,
                    amount=amount,
                    bank_type=BankType.N_BANK,
                    income_date=date.today(),
                    has_invoice=False,
                    notes="微信收款"
                )
                
                # 验证银行类型识别
                assert income.bank_type == BankType.N_BANK, "应该正确识别为N银行"
                
                # 从数据库查询验证
                retrieved = finance_manager.get_income_by_id(income.id)
                assert retrieved.bank_type == BankType.N_BANK, "查询的银行类型应该是N银行"
                
                # 验证N银行特性在汇总中体现
                summary = finance_manager.get_bank_account_summary(BankType.N_BANK)
                assert "现金等价物" in summary["special_notes"][0], "N银行汇总应该标注现金等价物特性"
        
        finally:
            if os.path.exists(path):
                os.unlink(path)
    
    @given(
        supplier=supplier_strategy(),
        amount=amount_strategy(),
        has_invoice=st.booleans()
    )
    @settings(max_examples=100, deadline=None)
    def test_g_bank_expense_invoice_marking(self, supplier, amount, has_invoice):
        """测试G银行支出的票据标记准确性"""
        fd, path = tempfile.mkstemp(suffix='.db')
        os.close(fd)
        
        try:
            with DatabaseManager(path) as db:
                db.save_supplier(supplier)
                finance_manager = FinanceManager(db)
                
                # 记录G银行支出
                expense = finance_manager.record_expense(
                    expense_type=ExpenseType.ACID_THREE,
                    amount=amount,
                    bank_type=BankType.G_BANK,
                    expense_date=date.today(),
                    supplier_id=supplier.id,
                    supplier_name=supplier.name,
                    has_invoice=has_invoice,
                    description="原料采购"
                )
                
                # 验证银行类型和票据标记
                assert expense.bank_type == BankType.G_BANK, "应该正确识别为G银行"
                assert expense.has_invoice == has_invoice, f"票据标记应该为 {has_invoice}"
        
        finally:
            if os.path.exists(path):
                os.unlink(path)

    @given(
        supplier=supplier_strategy(),
        amount=amount_strategy()
    )
    @settings(max_examples=100, deadline=None)
    def test_n_bank_expense_cash_equivalent(self, supplier, amount):
        """测试N银行支出作为现金等价物处理"""
        fd, path = tempfile.mkstemp(suffix='.db')
        os.close(fd)
        
        try:
            with DatabaseManager(path) as db:
                db.save_supplier(supplier)
                finance_manager = FinanceManager(db)
                
                # 记录N银行支出（现金等价物）
                expense = finance_manager.record_expense(
                    expense_type=ExpenseType.DAILY_EXPENSES,
                    amount=amount,
                    bank_type=BankType.N_BANK,
                    expense_date=date.today(),
                    supplier_id=supplier.id,
                    supplier_name=supplier.name,
                    has_invoice=False,
                    description="日常支出"
                )
                
                # 验证银行类型识别
                assert expense.bank_type == BankType.N_BANK, "应该正确识别为N银行"
        
        finally:
            if os.path.exists(path):
                os.unlink(path)
    
    @given(
        customer=customer_strategy(),
        amount=amount_strategy(),
        bank_type=st.sampled_from(list(BankType))
    )
    @settings(max_examples=100, deadline=None)
    def test_bank_type_consistency_across_operations(self, customer, amount, bank_type):
        """测试银行类型在各种操作中保持一致"""
        fd, path = tempfile.mkstemp(suffix='.db')
        os.close(fd)
        
        try:
            with DatabaseManager(path) as db:
                db.save_customer(customer)
                finance_manager = FinanceManager(db)
                
                # 创建银行账户
                account = finance_manager.create_bank_account(
                    bank_type=bank_type,
                    account_name=f"{bank_type.value}账户",
                    initial_balance=Decimal("50000")
                )
                
                # 记录收入
                income = finance_manager.record_income(
                    customer_id=customer.id,
                    customer_name=customer.name,
                    amount=amount,
                    bank_type=bank_type,
                    income_date=date.today()
                )
                
                # 记录银行交易
                transaction = finance_manager.record_bank_transaction(
                    bank_type=bank_type,
                    amount=amount,
                    transaction_date=date.today(),
                    counterparty=customer.name,
                    is_income=True
                )
                
                # 验证所有记录的银行类型一致
                assert account.bank_type == bank_type, "账户银行类型应该一致"
                assert income.bank_type == bank_type, "收入银行类型应该一致"
                assert transaction.bank_type == bank_type, "交易银行类型应该一致"
                
                # 验证查询时银行类型保持一致
                retrieved_account = finance_manager.get_bank_account(account.id)
                retrieved_income = finance_manager.get_income_by_id(income.id)
                
                assert retrieved_account.bank_type == bank_type, "查询的账户银行类型应该一致"
                assert retrieved_income.bank_type == bank_type, "查询的收入银行类型应该一致"
        
        finally:
            if os.path.exists(path):
                os.unlink(path)


class TestProperty12_BankAccountIndependentManagement:
    """
    **属性 12: 银行账户独立管理**
    **Validates: Requirements 4.1**
    
    对于任何银行交易，G银行和N银行的账户余额和交易记录应该完全独立，
    一个账户的操作不应影响另一个账户
    """
    
    @given(
        initial_g_balance=st.decimals(min_value=Decimal("10000"), max_value=Decimal("100000"), places=2),
        initial_n_balance=st.decimals(min_value=Decimal("5000"), max_value=Decimal("50000"), places=2),
        g_transaction_amount=st.decimals(min_value=Decimal("100"), max_value=Decimal("10000"), places=2),
        is_income=st.booleans()
    )
    @settings(max_examples=100, deadline=None)
    def test_g_bank_operations_do_not_affect_n_bank(self, initial_g_balance, initial_n_balance, 
                                                     g_transaction_amount, is_income):
        """测试G银行操作不影响N银行"""
        fd, path = tempfile.mkstemp(suffix='.db')
        os.close(fd)
        
        try:
            with DatabaseManager(path) as db:
                finance_manager = FinanceManager(db)
                
                # 创建两个银行账户
                finance_manager.create_bank_account(
                    bank_type=BankType.G_BANK,
                    account_name="G银行账户",
                    initial_balance=initial_g_balance
                )
                
                finance_manager.create_bank_account(
                    bank_type=BankType.N_BANK,
                    account_name="N银行账户",
                    initial_balance=initial_n_balance
                )
                
                # 记录N银行初始余额
                n_balance_before = finance_manager.get_account_balance(BankType.N_BANK)
                assert n_balance_before == initial_n_balance, "N银行初始余额应该正确"
                
                # 在G银行进行交易
                finance_manager.record_bank_transaction(
                    bank_type=BankType.G_BANK,
                    amount=g_transaction_amount,
                    transaction_date=date.today(),
                    counterparty="测试对手",
                    is_income=is_income
                )
                
                # 验证G银行余额变化
                g_balance_after = finance_manager.get_account_balance(BankType.G_BANK)
                if is_income:
                    expected_g_balance = initial_g_balance + g_transaction_amount
                else:
                    expected_g_balance = initial_g_balance - g_transaction_amount
                
                assert abs(g_balance_after - expected_g_balance) < Decimal("0.01"), \
                    f"G银行余额应该变化为 {expected_g_balance}"
                
                # 验证N银行余额不变
                n_balance_after = finance_manager.get_account_balance(BankType.N_BANK)
                assert n_balance_after == initial_n_balance, \
                    f"N银行余额应该保持不变 {initial_n_balance}，实际为 {n_balance_after}"
        
        finally:
            if os.path.exists(path):
                os.unlink(path)

    @given(
        initial_g_balance=st.decimals(min_value=Decimal("10000"), max_value=Decimal("100000"), places=2),
        initial_n_balance=st.decimals(min_value=Decimal("5000"), max_value=Decimal("50000"), places=2),
        n_transaction_amount=st.decimals(min_value=Decimal("100"), max_value=Decimal("10000"), places=2),
        is_income=st.booleans()
    )
    @settings(max_examples=100, deadline=None)
    def test_n_bank_operations_do_not_affect_g_bank(self, initial_g_balance, initial_n_balance,
                                                     n_transaction_amount, is_income):
        """测试N银行操作不影响G银行"""
        fd, path = tempfile.mkstemp(suffix='.db')
        os.close(fd)
        
        try:
            with DatabaseManager(path) as db:
                finance_manager = FinanceManager(db)
                
                # 创建两个银行账户
                finance_manager.create_bank_account(
                    bank_type=BankType.G_BANK,
                    account_name="G银行账户",
                    initial_balance=initial_g_balance
                )
                
                finance_manager.create_bank_account(
                    bank_type=BankType.N_BANK,
                    account_name="N银行账户",
                    initial_balance=initial_n_balance
                )
                
                # 记录G银行初始余额
                g_balance_before = finance_manager.get_account_balance(BankType.G_BANK)
                assert g_balance_before == initial_g_balance, "G银行初始余额应该正确"
                
                # 在N银行进行交易
                finance_manager.record_bank_transaction(
                    bank_type=BankType.N_BANK,
                    amount=n_transaction_amount,
                    transaction_date=date.today(),
                    counterparty="测试对手",
                    is_income=is_income
                )
                
                # 验证N银行余额变化
                n_balance_after = finance_manager.get_account_balance(BankType.N_BANK)
                if is_income:
                    expected_n_balance = initial_n_balance + n_transaction_amount
                else:
                    expected_n_balance = initial_n_balance - n_transaction_amount
                
                assert abs(n_balance_after - expected_n_balance) < Decimal("0.01"), \
                    f"N银行余额应该变化为 {expected_n_balance}"
                
                # 验证G银行余额不变
                g_balance_after = finance_manager.get_account_balance(BankType.G_BANK)
                assert g_balance_after == initial_g_balance, \
                    f"G银行余额应该保持不变 {initial_g_balance}，实际为 {g_balance_after}"
        
        finally:
            if os.path.exists(path):
                os.unlink(path)

    @given(
        num_g_transactions=st.integers(min_value=1, max_value=5),
        num_n_transactions=st.integers(min_value=1, max_value=5)
    )
    @settings(max_examples=100, deadline=None)
    def test_transaction_records_are_independent(self, num_g_transactions, num_n_transactions):
        """测试交易记录完全独立"""
        fd, path = tempfile.mkstemp(suffix='.db')
        os.close(fd)
        
        try:
            with DatabaseManager(path) as db:
                finance_manager = FinanceManager(db)
                
                # 创建两个银行账户
                finance_manager.create_bank_account(
                    bank_type=BankType.G_BANK,
                    account_name="G银行账户",
                    initial_balance=Decimal("100000")
                )
                
                finance_manager.create_bank_account(
                    bank_type=BankType.N_BANK,
                    account_name="N银行账户",
                    initial_balance=Decimal("50000")
                )
                
                # 记录G银行交易
                for i in range(num_g_transactions):
                    finance_manager.record_bank_transaction(
                        bank_type=BankType.G_BANK,
                        amount=Decimal("1000"),
                        transaction_date=date.today(),
                        counterparty=f"G客户{i+1}",
                        is_income=True
                    )
                
                # 记录N银行交易
                for i in range(num_n_transactions):
                    finance_manager.record_bank_transaction(
                        bank_type=BankType.N_BANK,
                        amount=Decimal("500"),
                        transaction_date=date.today(),
                        counterparty=f"N客户{i+1}",
                        is_income=True
                    )
                
                # 验证交易记录独立
                g_transactions = finance_manager.get_bank_transactions(BankType.G_BANK)
                n_transactions = finance_manager.get_bank_transactions(BankType.N_BANK)
                
                assert len(g_transactions) == num_g_transactions, \
                    f"G银行应该有 {num_g_transactions} 笔交易"
                assert len(n_transactions) == num_n_transactions, \
                    f"N银行应该有 {num_n_transactions} 笔交易"
                
                # 验证所有G银行交易都是G银行类型
                for transaction in g_transactions:
                    assert transaction.bank_type == BankType.G_BANK, \
                        "G银行交易记录应该都是G银行类型"
                
                # 验证所有N银行交易都是N银行类型
                for transaction in n_transactions:
                    assert transaction.bank_type == BankType.N_BANK, \
                        "N银行交易记录应该都是N银行类型"
        
        finally:
            if os.path.exists(path):
                os.unlink(path)

    @given(
        initial_g_balance=st.decimals(min_value=Decimal("10000"), max_value=Decimal("100000"), places=2),
        initial_n_balance=st.decimals(min_value=Decimal("5000"), max_value=Decimal("50000"), places=2),
        num_operations=st.integers(min_value=3, max_value=10)
    )
    @settings(max_examples=100, deadline=None)
    def test_mixed_operations_maintain_independence(self, initial_g_balance, initial_n_balance, num_operations):
        """测试混合操作时账户保持独立"""
        fd, path = tempfile.mkstemp(suffix='.db')
        os.close(fd)
        
        try:
            with DatabaseManager(path) as db:
                finance_manager = FinanceManager(db)
                
                # 创建两个银行账户
                finance_manager.create_bank_account(
                    bank_type=BankType.G_BANK,
                    account_name="G银行账户",
                    initial_balance=initial_g_balance
                )
                
                finance_manager.create_bank_account(
                    bank_type=BankType.N_BANK,
                    account_name="N银行账户",
                    initial_balance=initial_n_balance
                )
                
                # 跟踪预期余额
                expected_g_balance = initial_g_balance
                expected_n_balance = initial_n_balance
                
                # 执行混合操作
                for i in range(num_operations):
                    # 交替在两个银行进行操作
                    if i % 2 == 0:
                        # G银行操作
                        amount = Decimal("500")
                        is_income = (i % 4 == 0)
                        
                        finance_manager.record_bank_transaction(
                            bank_type=BankType.G_BANK,
                            amount=amount,
                            transaction_date=date.today(),
                            counterparty=f"对手{i+1}",
                            is_income=is_income
                        )
                        
                        if is_income:
                            expected_g_balance += amount
                        else:
                            expected_g_balance -= amount
                    else:
                        # N银行操作
                        amount = Decimal("300")
                        is_income = (i % 4 == 1)
                        
                        finance_manager.record_bank_transaction(
                            bank_type=BankType.N_BANK,
                            amount=amount,
                            transaction_date=date.today(),
                            counterparty=f"对手{i+1}",
                            is_income=is_income
                        )
                        
                        if is_income:
                            expected_n_balance += amount
                        else:
                            expected_n_balance -= amount
                
                # 验证最终余额
                g_balance_final = finance_manager.get_account_balance(BankType.G_BANK)
                n_balance_final = finance_manager.get_account_balance(BankType.N_BANK)
                
                assert abs(g_balance_final - expected_g_balance) < Decimal("0.01"), \
                    f"G银行最终余额应该是 {expected_g_balance}，实际为 {g_balance_final}"
                assert abs(n_balance_final - expected_n_balance) < Decimal("0.01"), \
                    f"N银行最终余额应该是 {expected_n_balance}，实际为 {n_balance_final}"
        
        finally:
            if os.path.exists(path):
                os.unlink(path)

    @given(
        customer=customer_strategy(),
        g_income_amount=st.decimals(min_value=Decimal("100"), max_value=Decimal("10000"), places=2),
        n_income_amount=st.decimals(min_value=Decimal("100"), max_value=Decimal("10000"), places=2)
    )
    @settings(max_examples=100, deadline=None)
    def test_income_records_are_independent_by_bank(self, customer, g_income_amount, n_income_amount):
        """测试收入记录按银行独立管理"""
        fd, path = tempfile.mkstemp(suffix='.db')
        os.close(fd)
        
        try:
            with DatabaseManager(path) as db:
                db.save_customer(customer)
                finance_manager = FinanceManager(db)
                
                # 创建两个银行账户
                finance_manager.create_bank_account(
                    bank_type=BankType.G_BANK,
                    account_name="G银行账户",
                    initial_balance=Decimal("50000")
                )
                
                finance_manager.create_bank_account(
                    bank_type=BankType.N_BANK,
                    account_name="N银行账户",
                    initial_balance=Decimal("20000")
                )
                
                # 记录G银行收入
                g_income = finance_manager.record_income(
                    customer_id=customer.id,
                    customer_name=customer.name,
                    amount=g_income_amount,
                    bank_type=BankType.G_BANK,
                    income_date=date.today(),
                    has_invoice=True
                )
                
                # 记录N银行收入
                n_income = finance_manager.record_income(
                    customer_id=customer.id,
                    customer_name=customer.name,
                    amount=n_income_amount,
                    bank_type=BankType.N_BANK,
                    income_date=date.today(),
                    has_invoice=False
                )
                
                # 验证收入记录的银行类型独立
                assert g_income.bank_type == BankType.G_BANK, "G银行收入应该标记为G银行"
                assert n_income.bank_type == BankType.N_BANK, "N银行收入应该标记为N银行"
                
                # 验证账户余额独立变化
                g_summary = finance_manager.get_bank_account_summary(BankType.G_BANK)
                n_summary = finance_manager.get_bank_account_summary(BankType.N_BANK)
                
                # G银行汇总应该只包含G银行的收入
                assert g_summary["total_income"] == g_income_amount, \
                    f"G银行总收入应该是 {g_income_amount}"
                
                # N银行汇总应该只包含N银行的收入
                assert n_summary["total_income"] == n_income_amount, \
                    f"N银行总收入应该是 {n_income_amount}"
        
        finally:
            if os.path.exists(path):
                os.unlink(path)

    @given(
        supplier=supplier_strategy(),
        g_expense_amount=st.decimals(min_value=Decimal("100"), max_value=Decimal("10000"), places=2),
        n_expense_amount=st.decimals(min_value=Decimal("100"), max_value=Decimal("10000"), places=2)
    )
    @settings(max_examples=100, deadline=None)
    def test_expense_records_are_independent_by_bank(self, supplier, g_expense_amount, n_expense_amount):
        """测试支出记录按银行独立管理"""
        fd, path = tempfile.mkstemp(suffix='.db')
        os.close(fd)
        
        try:
            with DatabaseManager(path) as db:
                db.save_supplier(supplier)
                finance_manager = FinanceManager(db)
                
                # 创建两个银行账户
                finance_manager.create_bank_account(
                    bank_type=BankType.G_BANK,
                    account_name="G银行账户",
                    initial_balance=Decimal("50000")
                )
                
                finance_manager.create_bank_account(
                    bank_type=BankType.N_BANK,
                    account_name="N银行账户",
                    initial_balance=Decimal("20000")
                )
                
                # 记录G银行支出
                g_expense = finance_manager.record_expense(
                    expense_type=ExpenseType.ACID_THREE,
                    amount=g_expense_amount,
                    bank_type=BankType.G_BANK,
                    expense_date=date.today(),
                    supplier_id=supplier.id,
                    supplier_name=supplier.name,
                    has_invoice=True
                )
                
                # 记录N银行支出
                n_expense = finance_manager.record_expense(
                    expense_type=ExpenseType.DAILY_EXPENSES,
                    amount=n_expense_amount,
                    bank_type=BankType.N_BANK,
                    expense_date=date.today(),
                    supplier_id=supplier.id,
                    supplier_name=supplier.name,
                    has_invoice=False
                )
                
                # 验证支出记录的银行类型独立
                assert g_expense.bank_type == BankType.G_BANK, "G银行支出应该标记为G银行"
                assert n_expense.bank_type == BankType.N_BANK, "N银行支出应该标记为N银行"
                
                # 验证账户余额独立变化
                g_summary = finance_manager.get_bank_account_summary(BankType.G_BANK)
                n_summary = finance_manager.get_bank_account_summary(BankType.N_BANK)
                
                # G银行汇总应该只包含G银行的支出
                assert g_summary["total_expense"] == g_expense_amount, \
                    f"G银行总支出应该是 {g_expense_amount}"
                
                # N银行汇总应该只包含N银行的支出
                assert n_summary["total_expense"] == n_expense_amount, \
                    f"N银行总支出应该是 {n_expense_amount}"
        
        finally:
            if os.path.exists(path):
                os.unlink(path)
    
    @given(
        initial_g_balance=st.decimals(min_value=Decimal("10000"), max_value=Decimal("100000"), places=2),
        initial_n_balance=st.decimals(min_value=Decimal("5000"), max_value=Decimal("50000"), places=2)
    )
    @settings(max_examples=100, deadline=None)
    def test_account_summaries_are_independent(self, initial_g_balance, initial_n_balance):
        """测试账户汇总信息完全独立"""
        fd, path = tempfile.mkstemp(suffix='.db')
        os.close(fd)
        
        try:
            with DatabaseManager(path) as db:
                finance_manager = FinanceManager(db)
                
                # 创建两个银行账户
                finance_manager.create_bank_account(
                    bank_type=BankType.G_BANK,
                    account_name="G银行账户",
                    initial_balance=initial_g_balance
                )
                
                finance_manager.create_bank_account(
                    bank_type=BankType.N_BANK,
                    account_name="N银行账户",
                    initial_balance=initial_n_balance
                )
                
                # 获取对账汇总
                reconciliation = finance_manager.reconcile_bank_accounts()
                
                # 验证汇总信息独立
                assert reconciliation["g_bank"]["balance"] == initial_g_balance, \
                    "G银行余额应该正确"
                assert reconciliation["n_bank"]["balance"] == initial_n_balance, \
                    "N银行余额应该正确"
                
                # 验证总余额是两个账户的和
                expected_total = initial_g_balance + initial_n_balance
                assert abs(reconciliation["total_balance"] - expected_total) < Decimal("0.01"), \
                    f"总余额应该是 {expected_total}"
                
                # 验证特殊标记独立
                assert "票据" in reconciliation["g_bank"]["special_notes"][0], \
                    "G银行应该有票据标记"
                assert "现金等价物" in reconciliation["n_bank"]["special_notes"][0], \
                    "N银行应该有现金等价物标记"
        
        finally:
            if os.path.exists(path):
                os.unlink(path)
