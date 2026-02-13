"""
Data storage layer for V1.7 Oxidation Factory Complete Financial Assistant

This package provides JSON-based local storage for:
- Transaction records
- Counterparty (customer/supplier) records
- Reminder records
- Import history
- Bank accounts (NEW in V1.7)
"""

from .base_storage import BaseStorage
from .transaction_storage import TransactionStorage
from .counterparty_storage import CounterpartyStorage
from .reminder_storage import ReminderStorage
from .import_history import ImportHistory, ImportRecord
from .bank_account_manager import BankAccountManager

__all__ = [
    "BaseStorage",
    "TransactionStorage",
    "CounterpartyStorage",
    "ReminderStorage",
    "ImportHistory",
    "ImportRecord",
    "BankAccountManager",
]
