"""
Bank Account Manager for V1.7 Oxidation Factory Complete Financial Assistant

This module provides management for bank accounts with support for:
- Account type classification (business/cash)
- Invoice marking (有票据/无票据)
- Account-based transaction statistics
- G银行(有票), N银行(现金), 微信(现金)
"""

from datetime import datetime
from typing import List, Optional, Dict
from decimal import Decimal
import logging

from ..models.core_models import BankAccount, AccountType, TransactionRecord, TransactionType
from .base_storage import BaseStorage

logger = logging.getLogger(__name__)


class BankAccountManager(BaseStorage):
    """
    Bank Account Manager
    
    Manages bank accounts with support for:
    - Account configuration (name, type, invoice marking)
    - G银行 marked as "有票据" (business account)
    - N银行 and 微信 marked as "现金账户" (cash accounts)
    - Transaction statistics by account
    """
    
    def __init__(self, storage_dir: str = "data"):
        """
        Initialize bank account manager
        
        Args:
            storage_dir: Directory to store bank account data
        """
        super().__init__(storage_dir, "bank_accounts.json")
        self._initialize_default_accounts()
    
    def _initialize_default_accounts(self) -> None:
        """
        Initialize default bank accounts from config if they don't exist
        
        Creates:
        - G银行 (business account, has invoice)
        - N银行 (cash account, no invoice)
        - 微信 (cash account, no invoice)
        """
        items = self._get_all_items()
        
        # Only initialize if no accounts exist
        if len(items) == 0:
            default_accounts = [
                {
                    "id": "g_bank",
                    "name": "G银行",
                    "account_number": "",
                    "account_type": AccountType.BUSINESS.value,
                    "has_invoice": True,
                    "balance": "0",
                    "description": "对公账户,有票据",
                    "created_at": datetime.now().isoformat(),
                    "updated_at": datetime.now().isoformat(),
                },
                {
                    "id": "n_bank",
                    "name": "N银行",
                    "account_number": "",
                    "account_type": AccountType.CASH.value,
                    "has_invoice": False,
                    "balance": "0",
                    "description": "现金账户,无票据",
                    "created_at": datetime.now().isoformat(),
                    "updated_at": datetime.now().isoformat(),
                },
                {
                    "id": "wechat",
                    "name": "微信",
                    "account_number": "",
                    "account_type": AccountType.CASH.value,
                    "has_invoice": False,
                    "balance": "0",
                    "description": "微信支付,现金账户",
                    "created_at": datetime.now().isoformat(),
                    "updated_at": datetime.now().isoformat(),
                },
            ]
            
            for account_data in default_accounts:
                items[account_data["id"]] = account_data
            
            self._save_all_items(items)
            logger.info("初始化默认银行账户: G银行, N银行, 微信")
    
    def add(self, account: BankAccount) -> None:
        """
        Add a new bank account
        
        Args:
            account: Bank account to add
        
        Raises:
            ValueError: If account with same ID already exists
        """
        items = self._get_all_items()
        
        if account.id in items:
            raise ValueError(f"银行账户ID已存在: {account.id}")
        
        items[account.id] = account.to_dict()
        self._save_all_items(items)
        logger.info(f"添加银行账户: {account.id} - {account.name}")
    
    def get(self, account_id: str) -> Optional[BankAccount]:
        """
        Get a bank account by ID
        
        Args:
            account_id: Bank account ID
        
        Returns:
            Bank account or None if not found
        """
        items = self._get_all_items()
        data = items.get(account_id)
        
        if data:
            return BankAccount.from_dict(data)
        return None
    
    def update(self, account: BankAccount) -> None:
        """
        Update an existing bank account
        
        Args:
            account: Bank account to update
        
        Raises:
            ValueError: If account doesn't exist
        """
        items = self._get_all_items()
        
        if account.id not in items:
            raise ValueError(f"银行账户不存在: {account.id}")
        
        # Update the updated_at timestamp
        account.updated_at = datetime.now()
        items[account.id] = account.to_dict()
        self._save_all_items(items)
        logger.info(f"更新银行账户: {account.id} - {account.name}")
    
    def delete(self, account_id: str) -> None:
        """
        Delete a bank account
        
        Args:
            account_id: Bank account ID to delete
        
        Raises:
            ValueError: If account doesn't exist
        """
        items = self._get_all_items()
        
        if account_id not in items:
            raise ValueError(f"银行账户不存在: {account_id}")
        
        del items[account_id]
        self._save_all_items(items)
        logger.info(f"删除银行账户: {account_id}")
    
    def get_all(self) -> List[BankAccount]:
        """
        Get all bank accounts
        
        Returns:
            List of all bank accounts
        """
        items = self._get_all_items()
        return [BankAccount.from_dict(data) for data in items.values()]
    
    def get_by_type(self, account_type: AccountType) -> List[BankAccount]:
        """
        Get bank accounts by type
        
        Args:
            account_type: Account type (BUSINESS or CASH)
        
        Returns:
            List of bank accounts of the specified type
        """
        all_accounts = self.get_all()
        return [a for a in all_accounts if a.account_type == account_type]
    
    def get_business_accounts(self) -> List[BankAccount]:
        """
        Get all business accounts (对公账户)
        
        Returns:
            List of business accounts
        """
        return self.get_by_type(AccountType.BUSINESS)
    
    def get_cash_accounts(self) -> List[BankAccount]:
        """
        Get all cash accounts (现金账户)
        
        Returns:
            List of cash accounts
        """
        return self.get_by_type(AccountType.CASH)
    
    def get_accounts_with_invoice(self) -> List[BankAccount]:
        """
        Get all accounts with invoice capability (有票据)
        
        Returns:
            List of accounts that can issue invoices
        """
        all_accounts = self.get_all()
        return [a for a in all_accounts if a.has_invoice]
    
    def get_accounts_without_invoice(self) -> List[BankAccount]:
        """
        Get all accounts without invoice capability (无票据)
        
        Returns:
            List of accounts that cannot issue invoices
        """
        all_accounts = self.get_all()
        return [a for a in all_accounts if not a.has_invoice]
    
    def update_balance(self, account_id: str, amount: Decimal, is_income: bool) -> None:
        """
        Update account balance
        
        Args:
            account_id: Bank account ID
            amount: Transaction amount
            is_income: True for income (increase balance), False for expense (decrease balance)
        
        Raises:
            ValueError: If account doesn't exist
        """
        account = self.get(account_id)
        if not account:
            raise ValueError(f"银行账户不存在: {account_id}")
        
        if is_income:
            account.balance += amount
        else:
            account.balance -= amount
        
        self.update(account)
        logger.info(f"更新账户余额: {account_id}, 金额: {amount}, 收入: {is_income}, 新余额: {account.balance}")
    
    def get_account_statistics(
        self, 
        account_id: str, 
        transactions: List[TransactionRecord]
    ) -> Dict[str, Decimal]:
        """
        Calculate statistics for a specific account
        
        Args:
            account_id: Bank account ID
            transactions: List of all transactions
        
        Returns:
            Dictionary with statistics:
            - total_income: Total income amount
            - total_expense: Total expense amount
            - net_amount: Net amount (income - expense)
            - transaction_count: Number of transactions
        """
        account_transactions = [
            t for t in transactions 
            if t.bank_account_id == account_id
        ]
        
        total_income = sum(
            t.amount for t in account_transactions 
            if t.type == TransactionType.INCOME
        )
        
        total_expense = sum(
            t.amount for t in account_transactions 
            if t.type == TransactionType.EXPENSE
        )
        
        return {
            "total_income": total_income,
            "total_expense": total_expense,
            "net_amount": total_income - total_expense,
            "transaction_count": len(account_transactions),
        }
    
    def get_all_account_statistics(
        self, 
        transactions: List[TransactionRecord]
    ) -> Dict[str, Dict[str, Decimal]]:
        """
        Calculate statistics for all accounts
        
        Args:
            transactions: List of all transactions
        
        Returns:
            Dictionary mapping account_id to statistics
        """
        all_accounts = self.get_all()
        result = {}
        
        for account in all_accounts:
            result[account.id] = self.get_account_statistics(account.id, transactions)
        
        return result
    
    def search_by_name(self, name: str) -> List[BankAccount]:
        """
        Search bank accounts by name (case-insensitive partial match)
        
        Args:
            name: Name to search for
        
        Returns:
            List of matching bank accounts
        """
        all_accounts = self.get_all()
        name_lower = name.lower()
        return [
            a for a in all_accounts 
            if name_lower in a.name.lower()
        ]
    
    def exists(self, account_id: str) -> bool:
        """
        Check if a bank account exists
        
        Args:
            account_id: Bank account ID
        
        Returns:
            True if account exists, False otherwise
        """
        items = self._get_all_items()
        return account_id in items
    
    def count(self) -> int:
        """
        Count total number of bank accounts
        
        Returns:
            Number of bank accounts
        """
        return len(self._get_all_items())
    
    def count_by_type(self, account_type: AccountType) -> int:
        """
        Count bank accounts by type
        
        Args:
            account_type: Account type
        
        Returns:
            Number of accounts of the specified type
        """
        return len(self.get_by_type(account_type))
