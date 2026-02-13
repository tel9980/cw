"""
Unit tests for Bank Account Manager

Tests bank account management functionality including:
- Account CRUD operations
- Account type classification
- Invoice marking
- Balance management
- Transaction statistics
"""

import pytest
from datetime import datetime, date
from decimal import Decimal
from pathlib import Path
import tempfile
import shutil

from oxidation_complete_v17.models.core_models import (
    BankAccount,
    AccountType,
    TransactionRecord,
    TransactionType,
    TransactionStatus,
)
from oxidation_complete_v17.storage.bank_account_manager import BankAccountManager


@pytest.fixture
def temp_storage_dir():
    """Create a temporary storage directory"""
    temp_dir = tempfile.mkdtemp()
    yield temp_dir
    shutil.rmtree(temp_dir)


@pytest.fixture
def bank_account_manager(temp_storage_dir):
    """Create a BankAccountManager instance"""
    return BankAccountManager(storage_dir=temp_storage_dir)


@pytest.fixture
def sample_account():
    """Create a sample bank account"""
    return BankAccount(
        id="test_bank",
        name="测试银行",
        account_number="1234567890",
        account_type=AccountType.BUSINESS,
        has_invoice=True,
        balance=Decimal("10000.00"),
        description="测试账户",
        created_at=datetime.now(),
        updated_at=datetime.now(),
    )


@pytest.fixture
def sample_transactions():
    """Create sample transactions"""
    now = datetime.now()
    return [
        TransactionRecord(
            id="t1",
            date=date.today(),
            type=TransactionType.INCOME,
            amount=Decimal("5000.00"),
            counterparty_id="c1",
            description="收入1",
            category="加工费收入",
            status=TransactionStatus.COMPLETED,
            created_at=now,
            updated_at=now,
            bank_account_id="g_bank",
        ),
        TransactionRecord(
            id="t2",
            date=date.today(),
            type=TransactionType.EXPENSE,
            amount=Decimal("2000.00"),
            counterparty_id="c2",
            description="支出1",
            category="原材料",
            status=TransactionStatus.COMPLETED,
            created_at=now,
            updated_at=now,
            bank_account_id="g_bank",
        ),
        TransactionRecord(
            id="t3",
            date=date.today(),
            type=TransactionType.INCOME,
            amount=Decimal("3000.00"),
            counterparty_id="c3",
            description="收入2",
            category="加工费收入",
            status=TransactionStatus.COMPLETED,
            created_at=now,
            updated_at=now,
            bank_account_id="n_bank",
        ),
    ]


class TestBankAccountManager:
    """Test BankAccountManager functionality"""
    
    def test_initialization_creates_default_accounts(self, bank_account_manager):
        """Test that initialization creates default accounts"""
        accounts = bank_account_manager.get_all()
        
        assert len(accounts) == 3
        
        # Check G银行
        g_bank = bank_account_manager.get("g_bank")
        assert g_bank is not None
        assert g_bank.name == "G银行"
        assert g_bank.account_type == AccountType.BUSINESS
        assert g_bank.has_invoice is True
        
        # Check N银行
        n_bank = bank_account_manager.get("n_bank")
        assert n_bank is not None
        assert n_bank.name == "N银行"
        assert n_bank.account_type == AccountType.CASH
        assert n_bank.has_invoice is False
        
        # Check 微信
        wechat = bank_account_manager.get("wechat")
        assert wechat is not None
        assert wechat.name == "微信"
        assert wechat.account_type == AccountType.CASH
        assert wechat.has_invoice is False
    
    def test_add_account(self, bank_account_manager, sample_account):
        """Test adding a new bank account"""
        bank_account_manager.add(sample_account)
        
        retrieved = bank_account_manager.get(sample_account.id)
        assert retrieved is not None
        assert retrieved.id == sample_account.id
        assert retrieved.name == sample_account.name
        assert retrieved.account_type == sample_account.account_type
        assert retrieved.has_invoice == sample_account.has_invoice
    
    def test_add_duplicate_account(self, bank_account_manager, sample_account):
        """Test adding a duplicate account raises error"""
        bank_account_manager.add(sample_account)
        
        with pytest.raises(ValueError, match="银行账户ID已存在"):
            bank_account_manager.add(sample_account)
    
    def test_get_account(self, bank_account_manager, sample_account):
        """Test getting an account by ID"""
        bank_account_manager.add(sample_account)
        
        retrieved = bank_account_manager.get(sample_account.id)
        assert retrieved is not None
        assert retrieved.id == sample_account.id
    
    def test_get_nonexistent_account(self, bank_account_manager):
        """Test getting a nonexistent account returns None"""
        result = bank_account_manager.get("nonexistent")
        assert result is None
    
    def test_update_account(self, bank_account_manager, sample_account):
        """Test updating an account"""
        bank_account_manager.add(sample_account)
        
        sample_account.balance = Decimal("20000.00")
        sample_account.description = "更新后的描述"
        bank_account_manager.update(sample_account)
        
        retrieved = bank_account_manager.get(sample_account.id)
        assert retrieved.balance == Decimal("20000.00")
        assert retrieved.description == "更新后的描述"
    
    def test_update_nonexistent_account(self, bank_account_manager, sample_account):
        """Test updating a nonexistent account raises error"""
        with pytest.raises(ValueError, match="银行账户不存在"):
            bank_account_manager.update(sample_account)
    
    def test_delete_account(self, bank_account_manager, sample_account):
        """Test deleting an account"""
        bank_account_manager.add(sample_account)
        bank_account_manager.delete(sample_account.id)
        
        retrieved = bank_account_manager.get(sample_account.id)
        assert retrieved is None
    
    def test_delete_nonexistent_account(self, bank_account_manager):
        """Test deleting a nonexistent account raises error"""
        with pytest.raises(ValueError, match="银行账户不存在"):
            bank_account_manager.delete("nonexistent")
    
    def test_get_all_accounts(self, bank_account_manager, sample_account):
        """Test getting all accounts"""
        # Should have 3 default accounts
        accounts = bank_account_manager.get_all()
        assert len(accounts) == 3
        
        # Add one more
        bank_account_manager.add(sample_account)
        accounts = bank_account_manager.get_all()
        assert len(accounts) == 4
    
    def test_get_by_type(self, bank_account_manager):
        """Test getting accounts by type"""
        business_accounts = bank_account_manager.get_by_type(AccountType.BUSINESS)
        assert len(business_accounts) == 1
        assert business_accounts[0].name == "G银行"
        
        cash_accounts = bank_account_manager.get_by_type(AccountType.CASH)
        assert len(cash_accounts) == 2
        assert any(a.name == "N银行" for a in cash_accounts)
        assert any(a.name == "微信" for a in cash_accounts)
    
    def test_get_business_accounts(self, bank_account_manager):
        """Test getting business accounts"""
        accounts = bank_account_manager.get_business_accounts()
        assert len(accounts) == 1
        assert accounts[0].name == "G银行"
        assert accounts[0].account_type == AccountType.BUSINESS
    
    def test_get_cash_accounts(self, bank_account_manager):
        """Test getting cash accounts"""
        accounts = bank_account_manager.get_cash_accounts()
        assert len(accounts) == 2
        assert all(a.account_type == AccountType.CASH for a in accounts)
    
    def test_get_accounts_with_invoice(self, bank_account_manager):
        """Test getting accounts with invoice capability"""
        accounts = bank_account_manager.get_accounts_with_invoice()
        assert len(accounts) == 1
        assert accounts[0].name == "G银行"
        assert accounts[0].has_invoice is True
    
    def test_get_accounts_without_invoice(self, bank_account_manager):
        """Test getting accounts without invoice capability"""
        accounts = bank_account_manager.get_accounts_without_invoice()
        assert len(accounts) == 2
        assert all(not a.has_invoice for a in accounts)
    
    def test_update_balance_income(self, bank_account_manager):
        """Test updating balance with income"""
        g_bank = bank_account_manager.get("g_bank")
        initial_balance = g_bank.balance
        
        bank_account_manager.update_balance("g_bank", Decimal("1000.00"), is_income=True)
        
        updated = bank_account_manager.get("g_bank")
        assert updated.balance == initial_balance + Decimal("1000.00")
    
    def test_update_balance_expense(self, bank_account_manager):
        """Test updating balance with expense"""
        g_bank = bank_account_manager.get("g_bank")
        initial_balance = g_bank.balance
        
        bank_account_manager.update_balance("g_bank", Decimal("500.00"), is_income=False)
        
        updated = bank_account_manager.get("g_bank")
        assert updated.balance == initial_balance - Decimal("500.00")
    
    def test_update_balance_nonexistent_account(self, bank_account_manager):
        """Test updating balance for nonexistent account raises error"""
        with pytest.raises(ValueError, match="银行账户不存在"):
            bank_account_manager.update_balance("nonexistent", Decimal("100.00"), is_income=True)
    
    def test_get_account_statistics(self, bank_account_manager, sample_transactions):
        """Test getting statistics for a specific account"""
        stats = bank_account_manager.get_account_statistics("g_bank", sample_transactions)
        
        assert stats["total_income"] == Decimal("5000.00")
        assert stats["total_expense"] == Decimal("2000.00")
        assert stats["net_amount"] == Decimal("3000.00")
        assert stats["transaction_count"] == 2
    
    def test_get_account_statistics_no_transactions(self, bank_account_manager):
        """Test getting statistics for account with no transactions"""
        stats = bank_account_manager.get_account_statistics("g_bank", [])
        
        assert stats["total_income"] == 0
        assert stats["total_expense"] == 0
        assert stats["net_amount"] == 0
        assert stats["transaction_count"] == 0
    
    def test_get_all_account_statistics(self, bank_account_manager, sample_transactions):
        """Test getting statistics for all accounts"""
        all_stats = bank_account_manager.get_all_account_statistics(sample_transactions)
        
        assert "g_bank" in all_stats
        assert "n_bank" in all_stats
        assert "wechat" in all_stats
        
        # G银行 statistics
        assert all_stats["g_bank"]["total_income"] == Decimal("5000.00")
        assert all_stats["g_bank"]["total_expense"] == Decimal("2000.00")
        assert all_stats["g_bank"]["net_amount"] == Decimal("3000.00")
        
        # N银行 statistics
        assert all_stats["n_bank"]["total_income"] == Decimal("3000.00")
        assert all_stats["n_bank"]["total_expense"] == 0
        assert all_stats["n_bank"]["net_amount"] == Decimal("3000.00")
        
        # 微信 statistics (no transactions)
        assert all_stats["wechat"]["total_income"] == 0
        assert all_stats["wechat"]["total_expense"] == 0
    
    def test_search_by_name(self, bank_account_manager):
        """Test searching accounts by name"""
        results = bank_account_manager.search_by_name("银行")
        assert len(results) == 2
        assert any(a.name == "G银行" for a in results)
        assert any(a.name == "N银行" for a in results)
        
        results = bank_account_manager.search_by_name("微信")
        assert len(results) == 1
        assert results[0].name == "微信"
    
    def test_search_by_name_case_insensitive(self, bank_account_manager):
        """Test searching accounts by name is case-insensitive"""
        results = bank_account_manager.search_by_name("g银行")
        assert len(results) == 1
        assert results[0].name == "G银行"
    
    def test_exists(self, bank_account_manager, sample_account):
        """Test checking if account exists"""
        assert bank_account_manager.exists("g_bank") is True
        assert bank_account_manager.exists("nonexistent") is False
        
        bank_account_manager.add(sample_account)
        assert bank_account_manager.exists(sample_account.id) is True
    
    def test_count(self, bank_account_manager, sample_account):
        """Test counting accounts"""
        assert bank_account_manager.count() == 3
        
        bank_account_manager.add(sample_account)
        assert bank_account_manager.count() == 4
    
    def test_count_by_type(self, bank_account_manager):
        """Test counting accounts by type"""
        assert bank_account_manager.count_by_type(AccountType.BUSINESS) == 1
        assert bank_account_manager.count_by_type(AccountType.CASH) == 2
    
    def test_persistence(self, temp_storage_dir):
        """Test data persistence across instances"""
        # Create first instance and add account
        manager1 = BankAccountManager(storage_dir=temp_storage_dir)
        sample = BankAccount(
            id="persist_test",
            name="持久化测试",
            account_number="9999",
            account_type=AccountType.BUSINESS,
            has_invoice=True,
            balance=Decimal("5000.00"),
            description="测试持久化",
            created_at=datetime.now(),
            updated_at=datetime.now(),
        )
        manager1.add(sample)
        
        # Create second instance and verify data persisted
        manager2 = BankAccountManager(storage_dir=temp_storage_dir)
        retrieved = manager2.get("persist_test")
        
        assert retrieved is not None
        assert retrieved.id == "persist_test"
        assert retrieved.name == "持久化测试"
        assert retrieved.balance == Decimal("5000.00")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
