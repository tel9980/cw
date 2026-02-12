#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
银行账户管理单元测试
"""

import pytest
from decimal import Decimal
from datetime import date, timedelta
from ..models.business_models import (
    Customer, Supplier, Income, Expense,
    BankType, ExpenseType, BankAccount, BankTransaction
)
from ..business.finance_manager import FinanceManager
from ..database.db_manager import DatabaseManager


@pytest.fixture
def db_manager(tmp_path):
    """创建临时数据库管理器"""
    db_path = tmp_path / "test_bank.db"
    db = DatabaseManager(str(db_path))
    db.connect()
    yield db
    db.close()


@pytest.fixture
def finance_manager(db_manager):
    """创建财务管理器"""
    return FinanceManager(db_manager)


@pytest.fixture
def sample_customer(db_manager):
    """创建示例客户"""
    customer = Customer(
        name="测试客户",
        contact="张三",
        phone="13800138000"
    )
    db_manager.save_customer(customer)
    return customer


@pytest.fixture
def sample_supplier(db_manager):
    """创建示例供应商"""
    supplier = Supplier(
        name="测试供应商",
        contact="李四",
        business_type="原料供应商"
    )
    db_manager.save_supplier(supplier)
    return supplier


class TestBankAccountCreation:
    """银行账户创建测试"""
    
    def test_create_g_bank_account(self, finance_manager):
        """测试创建G银行账户"""
        account = finance_manager.create_bank_account(
            bank_type=BankType.G_BANK,
            account_name="G银行主账户",
            account_number="6222000012345678",
            initial_balance=Decimal("50000"),
            notes="用于有票据的正式交易"
        )
        
        assert account.bank_type == BankType.G_BANK
        assert account.account_name == "G银行主账户"
        assert account.balance == Decimal("50000")
        assert "票据" in account.notes
    
    def test_create_n_bank_account(self, finance_manager):
        """测试创建N银行账户"""
        account = finance_manager.create_bank_account(
            bank_type=BankType.N_BANK,
            account_name="N银行现金账户",
            account_number="6228000087654321",
            initial_balance=Decimal("10000"),
            notes="现金等价物，与微信结合使用"
        )
        
        assert account.bank_type == BankType.N_BANK
        assert account.account_name == "N银行现金账户"
        assert account.balance == Decimal("10000")
        assert "现金" in account.notes
    
    def test_get_bank_account(self, finance_manager):
        """测试获取银行账户"""
        account = finance_manager.create_bank_account(
            bank_type=BankType.G_BANK,
            account_name="测试账户",
            initial_balance=Decimal("30000")
        )
        
        retrieved = finance_manager.get_bank_account(account.id)
        assert retrieved is not None
        assert retrieved.id == account.id
        assert retrieved.balance == Decimal("30000")
    
    def test_list_bank_accounts(self, finance_manager):
        """测试列出所有银行账户"""
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
        
        accounts = finance_manager.list_bank_accounts()
        assert len(accounts) == 2
        
        g_accounts = [a for a in accounts if a.bank_type == BankType.G_BANK]
        n_accounts = [a for a in accounts if a.bank_type == BankType.N_BANK]
        assert len(g_accounts) == 1
        assert len(n_accounts) == 1


class TestBankAccountBalance:
    """银行账户余额管理测试"""
    
    def test_get_account_balance_g_bank(self, finance_manager):
        """测试获取G银行余额"""
        finance_manager.create_bank_account(
            bank_type=BankType.G_BANK,
            account_name="G银行账户1",
            initial_balance=Decimal("30000")
        )
        
        finance_manager.create_bank_account(
            bank_type=BankType.G_BANK,
            account_name="G银行账户2",
            initial_balance=Decimal("20000")
        )
        
        balance = finance_manager.get_account_balance(BankType.G_BANK)
        assert balance == Decimal("50000")
    
    def test_get_account_balance_n_bank(self, finance_manager):
        """测试获取N银行余额"""
        finance_manager.create_bank_account(
            bank_type=BankType.N_BANK,
            account_name="N银行账户",
            initial_balance=Decimal("15000")
        )
        
        balance = finance_manager.get_account_balance(BankType.N_BANK)
        assert balance == Decimal("15000")
    
    def test_update_account_balance_income(self, finance_manager):
        """测试更新账户余额（收入）"""
        finance_manager.create_bank_account(
            bank_type=BankType.G_BANK,
            account_name="G银行账户",
            initial_balance=Decimal("50000")
        )
        
        success, message = finance_manager.update_account_balance(
            bank_type=BankType.G_BANK,
            amount=Decimal("10000"),
            is_income=True
        )
        
        assert success is True
        assert "成功" in message
        
        balance = finance_manager.get_account_balance(BankType.G_BANK)
        assert balance == Decimal("60000")
    
    def test_update_account_balance_expense(self, finance_manager):
        """测试更新账户余额（支出）"""
        finance_manager.create_bank_account(
            bank_type=BankType.G_BANK,
            account_name="G银行账户",
            initial_balance=Decimal("50000")
        )
        
        success, message = finance_manager.update_account_balance(
            bank_type=BankType.G_BANK,
            amount=Decimal("8000"),
            is_income=False
        )
        
        assert success is True
        balance = finance_manager.get_account_balance(BankType.G_BANK)
        assert balance == Decimal("42000")
    
    def test_update_account_balance_insufficient_funds(self, finance_manager):
        """测试余额不足时的支出"""
        finance_manager.create_bank_account(
            bank_type=BankType.G_BANK,
            account_name="G银行账户",
            initial_balance=Decimal("5000")
        )
        
        success, message = finance_manager.update_account_balance(
            bank_type=BankType.G_BANK,
            amount=Decimal("10000"),
            is_income=False
        )
        
        assert success is False
        assert "余额不足" in message
    
    def test_update_account_balance_no_account(self, finance_manager):
        """测试更新不存在的账户"""
        success, message = finance_manager.update_account_balance(
            bank_type=BankType.G_BANK,
            amount=Decimal("1000"),
            is_income=True
        )
        
        assert success is False
        assert "未找到" in message


class TestBankTransactions:
    """银行交易记录测试"""
    
    def test_record_income_transaction(self, finance_manager):
        """测试记录收入交易"""
        # 先创建账户
        finance_manager.create_bank_account(
            bank_type=BankType.G_BANK,
            account_name="G银行账户",
            initial_balance=Decimal("50000")
        )
        
        transaction = finance_manager.record_bank_transaction(
            bank_type=BankType.G_BANK,
            amount=Decimal("10000"),
            transaction_date=date.today(),
            counterparty="客户A",
            description="加工费收入",
            is_income=True,
            notes="有票据"
        )
        
        assert transaction.bank_type == BankType.G_BANK
        assert transaction.amount == Decimal("10000")
        assert transaction.counterparty == "客户A"
        
        # 验证余额已更新
        balance = finance_manager.get_account_balance(BankType.G_BANK)
        assert balance == Decimal("60000")
    
    def test_record_expense_transaction(self, finance_manager):
        """测试记录支出交易"""
        finance_manager.create_bank_account(
            bank_type=BankType.G_BANK,
            account_name="G银行账户",
            initial_balance=Decimal("50000")
        )
        
        transaction = finance_manager.record_bank_transaction(
            bank_type=BankType.G_BANK,
            amount=Decimal("5000"),
            transaction_date=date.today(),
            counterparty="供应商B",
            description="原料采购",
            is_income=False,
            notes="已付款"
        )
        
        assert transaction.amount == Decimal("-5000")
        
        # 验证余额已更新
        balance = finance_manager.get_account_balance(BankType.G_BANK)
        assert balance == Decimal("45000")
    
    def test_record_n_bank_transaction(self, finance_manager):
        """测试记录N银行交易（现金等价物）"""
        finance_manager.create_bank_account(
            bank_type=BankType.N_BANK,
            account_name="N银行账户",
            initial_balance=Decimal("20000")
        )
        
        transaction = finance_manager.record_bank_transaction(
            bank_type=BankType.N_BANK,
            amount=Decimal("3000"),
            transaction_date=date.today(),
            counterparty="客户C",
            description="微信收款",
            is_income=True,
            notes="现金等价物"
        )
        
        assert transaction.bank_type == BankType.N_BANK
        balance = finance_manager.get_account_balance(BankType.N_BANK)
        assert balance == Decimal("23000")
    
    def test_get_bank_transactions(self, finance_manager):
        """测试获取银行交易记录"""
        finance_manager.create_bank_account(
            bank_type=BankType.G_BANK,
            account_name="G银行账户",
            initial_balance=Decimal("50000")
        )
        
        # 记录多笔交易
        finance_manager.record_bank_transaction(
            bank_type=BankType.G_BANK,
            amount=Decimal("10000"),
            transaction_date=date.today(),
            counterparty="客户A",
            is_income=True
        )
        
        finance_manager.record_bank_transaction(
            bank_type=BankType.G_BANK,
            amount=Decimal("5000"),
            transaction_date=date.today(),
            counterparty="供应商B",
            is_income=False
        )
        
        transactions = finance_manager.get_bank_transactions(BankType.G_BANK)
        assert len(transactions) == 2
    
    def test_get_bank_transactions_with_date_filter(self, finance_manager):
        """测试按日期过滤交易记录"""
        finance_manager.create_bank_account(
            bank_type=BankType.G_BANK,
            account_name="G银行账户",
            initial_balance=Decimal("50000")
        )
        
        today = date.today()
        yesterday = today - timedelta(days=1)
        
        # 记录不同日期的交易
        finance_manager.record_bank_transaction(
            bank_type=BankType.G_BANK,
            amount=Decimal("5000"),
            transaction_date=yesterday,
            counterparty="客户A",
            is_income=True
        )
        
        finance_manager.record_bank_transaction(
            bank_type=BankType.G_BANK,
            amount=Decimal("10000"),
            transaction_date=today,
            counterparty="客户B",
            is_income=True
        )
        
        # 只查询今天的交易
        transactions = finance_manager.get_bank_transactions(
            bank_type=BankType.G_BANK,
            start_date=today,
            end_date=today
        )
        
        assert len(transactions) == 1
        assert transactions[0].amount == Decimal("10000")


class TestTransactionMatching:
    """交易匹配测试"""
    
    def test_match_transaction_to_income(self, finance_manager, db_manager, sample_customer):
        """测试将交易匹配到收入记录"""
        # 创建账户
        finance_manager.create_bank_account(
            bank_type=BankType.G_BANK,
            account_name="G银行账户",
            initial_balance=Decimal("50000")
        )
        
        # 记录收入
        income = finance_manager.record_income(
            customer_id=sample_customer.id,
            customer_name=sample_customer.name,
            amount=Decimal("10000"),
            bank_type=BankType.G_BANK,
            income_date=date.today(),
            has_invoice=True
        )
        
        # 记录银行交易
        transaction = finance_manager.record_bank_transaction(
            bank_type=BankType.G_BANK,
            amount=Decimal("10000"),
            transaction_date=date.today(),
            counterparty=sample_customer.name,
            description="加工费收入",
            is_income=True
        )
        
        # 匹配交易到收入
        success, message = finance_manager.match_transaction_to_income(
            transaction_id=transaction.id,
            income_id=income.id
        )
        
        assert success is True
        assert "成功" in message
        
        # 验证匹配信息
        matched_transaction = db_manager.get_bank_transaction(transaction.id)
        assert matched_transaction.matched is True
        assert matched_transaction.matched_income_id == income.id
    
    def test_match_transaction_to_expense(self, finance_manager, db_manager, sample_supplier):
        """测试将交易匹配到支出记录"""
        finance_manager.create_bank_account(
            bank_type=BankType.G_BANK,
            account_name="G银行账户",
            initial_balance=Decimal("50000")
        )
        
        # 记录支出
        expense = finance_manager.record_expense(
            expense_type=ExpenseType.ACID_THREE,
            amount=Decimal("5000"),
            bank_type=BankType.G_BANK,
            expense_date=date.today(),
            supplier_id=sample_supplier.id,
            supplier_name=sample_supplier.name,
            has_invoice=True
        )
        
        # 记录银行交易
        transaction = finance_manager.record_bank_transaction(
            bank_type=BankType.G_BANK,
            amount=Decimal("5000"),
            transaction_date=date.today(),
            counterparty=sample_supplier.name,
            description="原料采购",
            is_income=False
        )
        
        # 匹配交易到支出
        success, message = finance_manager.match_transaction_to_expense(
            transaction_id=transaction.id,
            expense_id=expense.id
        )
        
        assert success is True
        
        # 验证匹配信息
        matched_transaction = db_manager.get_bank_transaction(transaction.id)
        assert matched_transaction.matched is True
        assert matched_transaction.matched_expense_id == expense.id
    
    def test_match_transaction_amount_mismatch(self, finance_manager, db_manager, sample_customer):
        """测试金额不匹配的情况"""
        finance_manager.create_bank_account(
            bank_type=BankType.G_BANK,
            account_name="G银行账户",
            initial_balance=Decimal("50000")
        )
        
        income = finance_manager.record_income(
            customer_id=sample_customer.id,
            customer_name=sample_customer.name,
            amount=Decimal("10000"),
            bank_type=BankType.G_BANK,
            income_date=date.today()
        )
        
        transaction = finance_manager.record_bank_transaction(
            bank_type=BankType.G_BANK,
            amount=Decimal("8000"),
            transaction_date=date.today(),
            counterparty=sample_customer.name,
            is_income=True
        )
        
        success, message = finance_manager.match_transaction_to_income(
            transaction_id=transaction.id,
            income_id=income.id
        )
        
        assert success is False
        assert "金额不匹配" in message
    
    def test_match_transaction_bank_type_mismatch(self, finance_manager, db_manager, sample_customer):
        """测试银行类型不匹配的情况"""
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
        
        income = finance_manager.record_income(
            customer_id=sample_customer.id,
            customer_name=sample_customer.name,
            amount=Decimal("10000"),
            bank_type=BankType.G_BANK,
            income_date=date.today()
        )
        
        transaction = finance_manager.record_bank_transaction(
            bank_type=BankType.N_BANK,
            amount=Decimal("10000"),
            transaction_date=date.today(),
            counterparty=sample_customer.name,
            is_income=True
        )
        
        success, message = finance_manager.match_transaction_to_income(
            transaction_id=transaction.id,
            income_id=income.id
        )
        
        assert success is False
        assert "银行类型不匹配" in message
    
    def test_get_unmatched_transactions(self, finance_manager, db_manager, sample_customer):
        """测试获取未匹配的交易"""
        finance_manager.create_bank_account(
            bank_type=BankType.G_BANK,
            account_name="G银行账户",
            initial_balance=Decimal("50000")
        )
        
        # 记录一笔匹配的交易
        income = finance_manager.record_income(
            customer_id=sample_customer.id,
            customer_name=sample_customer.name,
            amount=Decimal("10000"),
            bank_type=BankType.G_BANK,
            income_date=date.today()
        )
        
        matched_transaction = finance_manager.record_bank_transaction(
            bank_type=BankType.G_BANK,
            amount=Decimal("10000"),
            transaction_date=date.today(),
            counterparty=sample_customer.name,
            is_income=True
        )
        
        finance_manager.match_transaction_to_income(
            transaction_id=matched_transaction.id,
            income_id=income.id
        )
        
        # 记录一笔未匹配的交易
        finance_manager.record_bank_transaction(
            bank_type=BankType.G_BANK,
            amount=Decimal("5000"),
            transaction_date=date.today(),
            counterparty="未知客户",
            is_income=True
        )
        
        unmatched = finance_manager.get_unmatched_transactions(BankType.G_BANK)
        assert len(unmatched) == 1
        assert unmatched[0].counterparty == "未知客户"


class TestBankAccountSummary:
    """银行账户汇总测试"""
    
    def test_get_bank_account_summary_g_bank(self, finance_manager):
        """测试获取G银行账户汇总"""
        finance_manager.create_bank_account(
            bank_type=BankType.G_BANK,
            account_name="G银行账户",
            initial_balance=Decimal("50000")
        )
        
        # 记录收入和支出交易
        finance_manager.record_bank_transaction(
            bank_type=BankType.G_BANK,
            amount=Decimal("10000"),
            transaction_date=date.today(),
            counterparty="客户A",
            is_income=True
        )
        
        finance_manager.record_bank_transaction(
            bank_type=BankType.G_BANK,
            amount=Decimal("5000"),
            transaction_date=date.today(),
            counterparty="供应商B",
            is_income=False
        )
        
        summary = finance_manager.get_bank_account_summary(BankType.G_BANK)
        
        assert summary["bank_type"] == "G银行"
        assert summary["balance"] == Decimal("55000")
        assert summary["total_income"] == Decimal("10000")
        assert summary["total_expense"] == Decimal("5000")
        assert summary["net_flow"] == Decimal("5000")
        assert summary["transaction_count"] == 2
        assert "票据" in summary["special_notes"][0]
    
    def test_get_bank_account_summary_n_bank(self, finance_manager):
        """测试获取N银行账户汇总（现金等价物）"""
        finance_manager.create_bank_account(
            bank_type=BankType.N_BANK,
            account_name="N银行账户",
            initial_balance=Decimal("20000")
        )
        
        finance_manager.record_bank_transaction(
            bank_type=BankType.N_BANK,
            amount=Decimal("3000"),
            transaction_date=date.today(),
            counterparty="客户C",
            is_income=True
        )
        
        summary = finance_manager.get_bank_account_summary(BankType.N_BANK)
        
        assert summary["bank_type"] == "N银行"
        assert summary["balance"] == Decimal("23000")
        assert "现金等价物" in summary["special_notes"][0]
    
    def test_reconcile_bank_accounts(self, finance_manager, db_manager, sample_customer):
        """测试银行账户对账汇总"""
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
        
        # G银行交易
        finance_manager.record_bank_transaction(
            bank_type=BankType.G_BANK,
            amount=Decimal("10000"),
            transaction_date=date.today(),
            counterparty="客户A",
            is_income=True
        )
        
        # N银行交易
        finance_manager.record_bank_transaction(
            bank_type=BankType.N_BANK,
            amount=Decimal("3000"),
            transaction_date=date.today(),
            counterparty="客户B",
            is_income=True
        )
        
        reconciliation = finance_manager.reconcile_bank_accounts()
        
        assert reconciliation["total_balance"] == Decimal("83000")
        assert reconciliation["g_bank"]["balance"] == Decimal("60000")
        assert reconciliation["n_bank"]["balance"] == Decimal("23000")
        assert reconciliation["total_unmatched_transactions"] == 2
        assert reconciliation["reconciliation_status"] == "有未匹配交易"
    
    def test_reconcile_with_matched_transactions(self, finance_manager, db_manager, sample_customer):
        """测试有匹配交易的对账"""
        finance_manager.create_bank_account(
            bank_type=BankType.G_BANK,
            account_name="G银行账户",
            initial_balance=Decimal("50000")
        )
        
        # 记录收入
        income = finance_manager.record_income(
            customer_id=sample_customer.id,
            customer_name=sample_customer.name,
            amount=Decimal("10000"),
            bank_type=BankType.G_BANK,
            income_date=date.today()
        )
        
        # 记录交易并匹配
        transaction = finance_manager.record_bank_transaction(
            bank_type=BankType.G_BANK,
            amount=Decimal("10000"),
            transaction_date=date.today(),
            counterparty=sample_customer.name,
            is_income=True
        )
        
        finance_manager.match_transaction_to_income(
            transaction_id=transaction.id,
            income_id=income.id
        )
        
        reconciliation = finance_manager.reconcile_bank_accounts()
        
        assert reconciliation["total_unmatched_transactions"] == 0
        assert reconciliation["reconciliation_status"] == "完成"
        assert reconciliation["g_bank"]["matched_count"] == 1
        assert reconciliation["g_bank"]["unmatched_count"] == 0


class TestBankAccountIndependence:
    """银行账户独立性测试"""
    
    def test_g_bank_and_n_bank_independence(self, finance_manager):
        """测试G银行和N银行账户完全独立"""
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
        
        # G银行交易
        finance_manager.record_bank_transaction(
            bank_type=BankType.G_BANK,
            amount=Decimal("10000"),
            transaction_date=date.today(),
            counterparty="客户A",
            is_income=True
        )
        
        # 验证G银行余额变化，N银行不变
        g_balance = finance_manager.get_account_balance(BankType.G_BANK)
        n_balance = finance_manager.get_account_balance(BankType.N_BANK)
        
        assert g_balance == Decimal("60000")
        assert n_balance == Decimal("20000")
        
        # N银行交易
        finance_manager.record_bank_transaction(
            bank_type=BankType.N_BANK,
            amount=Decimal("5000"),
            transaction_date=date.today(),
            counterparty="供应商B",
            is_income=False
        )
        
        # 验证N银行余额变化，G银行不变
        g_balance = finance_manager.get_account_balance(BankType.G_BANK)
        n_balance = finance_manager.get_account_balance(BankType.N_BANK)
        
        assert g_balance == Decimal("60000")
        assert n_balance == Decimal("15000")
    
    def test_separate_transaction_records(self, finance_manager):
        """测试交易记录分别管理"""
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
        
        # 记录不同银行的交易
        finance_manager.record_bank_transaction(
            bank_type=BankType.G_BANK,
            amount=Decimal("10000"),
            transaction_date=date.today(),
            counterparty="客户A",
            is_income=True
        )
        
        finance_manager.record_bank_transaction(
            bank_type=BankType.N_BANK,
            amount=Decimal("3000"),
            transaction_date=date.today(),
            counterparty="客户B",
            is_income=True
        )
        
        # 分别查询交易记录
        g_transactions = finance_manager.get_bank_transactions(BankType.G_BANK)
        n_transactions = finance_manager.get_bank_transactions(BankType.N_BANK)
        
        assert len(g_transactions) == 1
        assert len(n_transactions) == 1
        assert g_transactions[0].bank_type == BankType.G_BANK
        assert n_transactions[0].bank_type == BankType.N_BANK
