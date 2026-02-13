"""
Reminder storage implementation

This module provides storage for reminder records.
"""

from datetime import date, datetime
from typing import List, Optional
import logging

from ..models.core_models import Reminder, ReminderType, ReminderStatus, Priority
from .base_storage import BaseStorage

logger = logging.getLogger(__name__)


class ReminderStorage(BaseStorage):
    """
    Storage for reminder records
    
    Provides CRUD operations for:
    - Tax reminders
    - Payable reminders
    - Receivable reminders
    - Cash flow warnings
    """
    
    def __init__(self, storage_dir: str = "data"):
        """
        Initialize reminder storage
        
        Args:
            storage_dir: Directory to store reminder data
        """
        super().__init__(storage_dir, "reminders.json")
    
    def add(self, reminder: Reminder) -> None:
        """
        Add a new reminder
        
        Args:
            reminder: Reminder record to add
        
        Raises:
            ValueError: If reminder with same ID already exists
        """
        items = self._get_all_items()
        
        if reminder.id in items:
            raise ValueError(f"提醒事项ID已存在: {reminder.id}")
        
        items[reminder.id] = reminder.to_dict()
        self._save_all_items(items)
        logger.info(f"添加提醒事项: {reminder.id} - {reminder.title}")
    
    def get(self, reminder_id: str) -> Optional[Reminder]:
        """
        Get a reminder by ID
        
        Args:
            reminder_id: Reminder ID
        
        Returns:
            Reminder record or None if not found
        """
        items = self._get_all_items()
        data = items.get(reminder_id)
        
        if data:
            return Reminder.from_dict(data)
        return None
    
    def update(self, reminder: Reminder) -> None:
        """
        Update an existing reminder
        
        Args:
            reminder: Reminder record to update
        
        Raises:
            ValueError: If reminder doesn't exist
        """
        items = self._get_all_items()
        
        if reminder.id not in items:
            raise ValueError(f"提醒事项不存在: {reminder.id}")
        
        items[reminder.id] = reminder.to_dict()
        self._save_all_items(items)
        logger.info(f"更新提醒事项: {reminder.id} - {reminder.title}")
    
    def delete(self, reminder_id: str) -> None:
        """
        Delete a reminder
        
        Args:
            reminder_id: Reminder ID to delete
        
        Raises:
            ValueError: If reminder doesn't exist
        """
        items = self._get_all_items()
        
        if reminder_id not in items:
            raise ValueError(f"提醒事项不存在: {reminder_id}")
        
        del items[reminder_id]
        self._save_all_items(items)
        logger.info(f"删除提醒事项: {reminder_id}")
    
    def get_all(self) -> List[Reminder]:
        """
        Get all reminders
        
        Returns:
            List of all reminder records
        """
        items = self._get_all_items()
        return [Reminder.from_dict(data) for data in items.values()]
    
    def get_by_type(self, reminder_type: ReminderType) -> List[Reminder]:
        """
        Get reminders by type
        
        Args:
            reminder_type: Type of reminder
        
        Returns:
            List of reminders of the specified type
        """
        all_reminders = self.get_all()
        return [r for r in all_reminders if r.type == reminder_type]
    
    def get_by_status(self, status: ReminderStatus) -> List[Reminder]:
        """
        Get reminders by status
        
        Args:
            status: Reminder status
        
        Returns:
            List of reminders with the specified status
        """
        all_reminders = self.get_all()
        return [r for r in all_reminders if r.status == status]
    
    def get_by_priority(self, priority: Priority) -> List[Reminder]:
        """
        Get reminders by priority
        
        Args:
            priority: Reminder priority
        
        Returns:
            List of reminders with the specified priority
        """
        all_reminders = self.get_all()
        return [r for r in all_reminders if r.priority == priority]
    
    def get_pending(self) -> List[Reminder]:
        """
        Get all pending reminders
        
        Returns:
            List of pending reminders
        """
        return self.get_by_status(ReminderStatus.PENDING)
    
    def get_due_reminders(self, check_date: Optional[date] = None) -> List[Reminder]:
        """
        Get reminders that are due on or before a specific date
        
        Args:
            check_date: Date to check (defaults to today)
        
        Returns:
            List of due reminders
        """
        if check_date is None:
            check_date = date.today()
        
        pending_reminders = self.get_pending()
        return [r for r in pending_reminders if r.due_date <= check_date]
    
    def get_upcoming_reminders(self, days: int = 7) -> List[Reminder]:
        """
        Get reminders due within the next N days
        
        Args:
            days: Number of days to look ahead
        
        Returns:
            List of upcoming reminders
        """
        today = date.today()
        from datetime import timedelta
        future_date = today + timedelta(days=days)
        
        pending_reminders = self.get_pending()
        return [
            r for r in pending_reminders 
            if today <= r.due_date <= future_date
        ]
    
    def get_overdue_reminders(self) -> List[Reminder]:
        """
        Get reminders that are overdue
        
        Returns:
            List of overdue reminders
        """
        today = date.today()
        pending_reminders = self.get_pending()
        return [r for r in pending_reminders if r.due_date < today]
    
    def mark_as_sent(self, reminder_id: str) -> None:
        """
        Mark a reminder as sent
        
        Args:
            reminder_id: Reminder ID
        
        Raises:
            ValueError: If reminder doesn't exist
        """
        reminder = self.get(reminder_id)
        if not reminder:
            raise ValueError(f"提醒事项不存在: {reminder_id}")
        
        reminder.status = ReminderStatus.SENT
        self.update(reminder)
    
    def mark_as_completed(self, reminder_id: str) -> None:
        """
        Mark a reminder as completed
        
        Args:
            reminder_id: Reminder ID
        
        Raises:
            ValueError: If reminder doesn't exist
        """
        reminder = self.get(reminder_id)
        if not reminder:
            raise ValueError(f"提醒事项不存在: {reminder_id}")
        
        reminder.status = ReminderStatus.COMPLETED
        self.update(reminder)
    
    def count(self) -> int:
        """
        Count total number of reminders
        
        Returns:
            Number of reminders
        """
        return len(self._get_all_items())
    
    def count_by_status(self, status: ReminderStatus) -> int:
        """
        Count reminders by status
        
        Args:
            status: Reminder status
        
        Returns:
            Number of reminders with the specified status
        """
        return len(self.get_by_status(status))
