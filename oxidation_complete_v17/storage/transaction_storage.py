"""
Transaction storage implementation

This module provides storage for transaction records (income, expense, orders).
"""

from datetime import date, datetime
from decimal import Decimal
from typing import List, Optional
import logging

from ..models.core_models import TransactionRecord, TransactionType, TransactionStatus
from .base_storage import BaseStorage

logger = logging.getLogger(__name__)


class TransactionStorage(BaseStorage):
    """
    Storage for transaction records
    
    Provides CRUD operations for:
    - Income transactions
    - Expense transactions
    - Order transactions
    """
    
    def __init__(self, storage_dir: str = "data"):
        """
        Initialize transaction storage
        
        Args:
            storage_dir: Directory to store transaction data
        """
        super().__init__(storage_dir, "transactions.json")
    
    def add(self, transaction: TransactionRecord) -> None:
        """
        Add a new transaction
        
        Args:
            transaction: Transaction record to add
        
        Raises:
            ValueError: If transaction with same ID already exists
        """
        items = self._get_all_items()
        
        if transaction.id in items:
            raise ValueError(f"交易记录ID已存在: {transaction.id}")
        
        items[transaction.id] = transaction.to_dict()
        self._save_all_items(items)
        logger.info(f"添加交易记录: {transaction.id}")
    
    def get(self, transaction_id: str) -> Optional[TransactionRecord]:
        """
        Get a transaction by ID
        
        Args:
            transaction_id: Transaction ID
        
        Returns:
            Transaction record or None if not found
        """
        items = self._get_all_items()
        data = items.get(transaction_id)
        
        if data:
            return TransactionRecord.from_dict(data)
        return None
    
    def update(self, transaction: TransactionRecord) -> None:
        """
        Update an existing transaction
        
        Args:
            transaction: Transaction record to update
        
        Raises:
            ValueError: If transaction doesn't exist
        """
        items = self._get_all_items()
        
        if transaction.id not in items:
            raise ValueError(f"交易记录不存在: {transaction.id}")
        
        # Update the updated_at timestamp
        transaction.updated_at = datetime.now()
        items[transaction.id] = transaction.to_dict()
        self._save_all_items(items)
        logger.info(f"更新交易记录: {transaction.id}")
    
    def delete(self, transaction_id: str) -> None:
        """
        Delete a transaction
        
        Args:
            transaction_id: Transaction ID to delete
        
        Raises:
            ValueError: If transaction doesn't exist
        """
        items = self._get_all_items()
        
        if transaction_id not in items:
            raise ValueError(f"交易记录不存在: {transaction_id}")
        
        del items[transaction_id]
        self._save_all_items(items)
        logger.info(f"删除交易记录: {transaction_id}")
    
    def get_all(self) -> List[TransactionRecord]:
        """
        Get all transactions
        
        Returns:
            List of all transaction records
        """
        items = self._get_all_items()
        return [TransactionRecord.from_dict(data) for data in items.values()]
    
    def get_by_date_range(
        self, 
        start_date: date, 
        end_date: date
    ) -> List[TransactionRecord]:
        """
        Get transactions within a date range
        
        Args:
            start_date: Start date (inclusive)
            end_date: End date (inclusive)
        
        Returns:
            List of transactions within the date range
        """
        all_transactions = self.get_all()
        return [
            t for t in all_transactions
            if start_date <= t.date <= end_date
        ]
    
    def get_by_type(self, transaction_type: TransactionType) -> List[TransactionRecord]:
        """
        Get transactions by type
        
        Args:
            transaction_type: Type of transaction (INCOME, EXPENSE, ORDER)
        
        Returns:
            List of transactions of the specified type
        """
        all_transactions = self.get_all()
        return [t for t in all_transactions if t.type == transaction_type]
    
    def get_by_counterparty(self, counterparty_id: str) -> List[TransactionRecord]:
        """
        Get transactions for a specific counterparty
        
        Args:
            counterparty_id: Counterparty ID
        
        Returns:
            List of transactions for the counterparty
        """
        all_transactions = self.get_all()
        return [
            t for t in all_transactions 
            if t.counterparty_id == counterparty_id
        ]
    
    def get_by_status(self, status: TransactionStatus) -> List[TransactionRecord]:
        """
        Get transactions by status
        
        Args:
            status: Transaction status
        
        Returns:
            List of transactions with the specified status
        """
        all_transactions = self.get_all()
        return [t for t in all_transactions if t.status == status]
    
    def get_by_category(self, category: str) -> List[TransactionRecord]:
        """
        Get transactions by category
        
        Args:
            category: Transaction category
        
        Returns:
            List of transactions in the category
        """
        all_transactions = self.get_all()
        return [t for t in all_transactions if t.category == category]
    
    def get_total_amount_by_type(
        self, 
        transaction_type: TransactionType,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None
    ) -> Decimal:
        """
        Calculate total amount for a transaction type
        
        Args:
            transaction_type: Type of transaction
            start_date: Optional start date filter
            end_date: Optional end date filter
        
        Returns:
            Total amount
        """
        transactions = self.get_by_type(transaction_type)
        
        if start_date and end_date:
            transactions = [
                t for t in transactions
                if start_date <= t.date <= end_date
            ]
        
        return sum((t.amount for t in transactions), Decimal('0'))
    
    def get_by_id(self, transaction_id: str) -> Optional[TransactionRecord]:
        """
        Get a transaction by ID (alias for get method)
        
        Args:
            transaction_id: Transaction ID
        
        Returns:
            Transaction record or None if not found
        """
        return self.get(transaction_id)
    
    def count(self) -> int:
        """
        Count total number of transactions
        
        Returns:
            Number of transactions
        """
        return len(self._get_all_items())
