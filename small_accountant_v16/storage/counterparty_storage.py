"""
Counterparty storage implementation

This module provides storage for counterparty records (customers and suppliers).
"""

from datetime import datetime
from typing import List, Optional
import logging

from ..models.core_models import Counterparty, CounterpartyType
from .base_storage import BaseStorage

logger = logging.getLogger(__name__)


class CounterpartyStorage(BaseStorage):
    """
    Storage for counterparty records (customers and suppliers)
    
    Provides CRUD operations for:
    - Customer records
    - Supplier records
    """
    
    def __init__(self, storage_dir: str = "data"):
        """
        Initialize counterparty storage
        
        Args:
            storage_dir: Directory to store counterparty data
        """
        super().__init__(storage_dir, "counterparties.json")
    
    def add(self, counterparty: Counterparty) -> None:
        """
        Add a new counterparty
        
        Args:
            counterparty: Counterparty record to add
        
        Raises:
            ValueError: If counterparty with same ID already exists
        """
        items = self._get_all_items()
        
        if counterparty.id in items:
            raise ValueError(f"往来单位ID已存在: {counterparty.id}")
        
        items[counterparty.id] = counterparty.to_dict()
        self._save_all_items(items)
        logger.info(f"添加往来单位: {counterparty.id} - {counterparty.name}")
    
    def get(self, counterparty_id: str) -> Optional[Counterparty]:
        """
        Get a counterparty by ID
        
        Args:
            counterparty_id: Counterparty ID
        
        Returns:
            Counterparty record or None if not found
        """
        items = self._get_all_items()
        data = items.get(counterparty_id)
        
        if data:
            return Counterparty.from_dict(data)
        return None
    
    def update(self, counterparty: Counterparty) -> None:
        """
        Update an existing counterparty
        
        Args:
            counterparty: Counterparty record to update
        
        Raises:
            ValueError: If counterparty doesn't exist
        """
        items = self._get_all_items()
        
        if counterparty.id not in items:
            raise ValueError(f"往来单位不存在: {counterparty.id}")
        
        # Update the updated_at timestamp
        counterparty.updated_at = datetime.now()
        items[counterparty.id] = counterparty.to_dict()
        self._save_all_items(items)
        logger.info(f"更新往来单位: {counterparty.id} - {counterparty.name}")
    
    def delete(self, counterparty_id: str) -> None:
        """
        Delete a counterparty
        
        Args:
            counterparty_id: Counterparty ID to delete
        
        Raises:
            ValueError: If counterparty doesn't exist
        """
        items = self._get_all_items()
        
        if counterparty_id not in items:
            raise ValueError(f"往来单位不存在: {counterparty_id}")
        
        del items[counterparty_id]
        self._save_all_items(items)
        logger.info(f"删除往来单位: {counterparty_id}")
    
    def get_all(self) -> List[Counterparty]:
        """
        Get all counterparties
        
        Returns:
            List of all counterparty records
        """
        items = self._get_all_items()
        return [Counterparty.from_dict(data) for data in items.values()]
    
    def get_by_type(self, counterparty_type: CounterpartyType) -> List[Counterparty]:
        """
        Get counterparties by type
        
        Args:
            counterparty_type: Type of counterparty (CUSTOMER or SUPPLIER)
        
        Returns:
            List of counterparties of the specified type
        """
        all_counterparties = self.get_all()
        return [c for c in all_counterparties if c.type == counterparty_type]
    
    def get_customers(self) -> List[Counterparty]:
        """
        Get all customers
        
        Returns:
            List of customer records
        """
        return self.get_by_type(CounterpartyType.CUSTOMER)
    
    def get_suppliers(self) -> List[Counterparty]:
        """
        Get all suppliers
        
        Returns:
            List of supplier records
        """
        return self.get_by_type(CounterpartyType.SUPPLIER)
    
    def search_by_name(self, name: str) -> List[Counterparty]:
        """
        Search counterparties by name (case-insensitive partial match)
        
        Args:
            name: Name to search for
        
        Returns:
            List of matching counterparties
        """
        all_counterparties = self.get_all()
        name_lower = name.lower()
        return [
            c for c in all_counterparties 
            if name_lower in c.name.lower()
        ]
    
    def get_by_tax_id(self, tax_id: str) -> Optional[Counterparty]:
        """
        Get counterparty by tax ID
        
        Args:
            tax_id: Tax identification number
        
        Returns:
            Counterparty record or None if not found
        """
        all_counterparties = self.get_all()
        for counterparty in all_counterparties:
            if counterparty.tax_id == tax_id:
                return counterparty
        return None
    
    def get_by_id(self, counterparty_id: str) -> Optional[Counterparty]:
        """
        Get a counterparty by ID (alias for get method)
        
        Args:
            counterparty_id: Counterparty ID
        
        Returns:
            Counterparty record or None if not found
        """
        return self.get(counterparty_id)
    
    def exists(self, counterparty_id: str) -> bool:
        """
        Check if a counterparty exists
        
        Args:
            counterparty_id: Counterparty ID
        
        Returns:
            True if counterparty exists, False otherwise
        """
        items = self._get_all_items()
        return counterparty_id in items
    
    def count(self) -> int:
        """
        Count total number of counterparties
        
        Returns:
            Number of counterparties
        """
        return len(self._get_all_items())
    
    def count_by_type(self, counterparty_type: CounterpartyType) -> int:
        """
        Count counterparties by type
        
        Args:
            counterparty_type: Type of counterparty
        
        Returns:
            Number of counterparties of the specified type
        """
        return len(self.get_by_type(counterparty_type))
