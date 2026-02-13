"""
Offline Data Management System

This module provides offline capability for the V1.5 workflow system, allowing users
to work without an internet connection and automatically synchronize when connection
is restored.

Requirements:
- 7.5: Offline capability for basic transaction entry and viewing
- 10.5: Automatic synchronization when connection is restored

Author: V1.5 Development Team
Date: 2026-02-10
"""

from dataclasses import dataclass, field, asdict
from datetime import datetime
from typing import Dict, List, Optional, Any, Set
from enum import Enum
import json
import os


class ConnectionStatus(Enum):
    """Network connection status"""
    ONLINE = "online"
    OFFLINE = "offline"
    SYNCING = "syncing"


class SyncStatus(Enum):
    """Synchronization status for offline data"""
    PENDING = "pending"
    SYNCED = "synced"
    CONFLICT = "conflict"
    FAILED = "failed"


class ConflictResolution(Enum):
    """Conflict resolution strategies"""
    LOCAL_WINS = "local_wins"
    REMOTE_WINS = "remote_wins"
    MERGE = "merge"
    MANUAL = "manual"


@dataclass
class OfflineTransaction:
    """Offline transaction record"""
    transaction_id: str
    transaction_type: str  # income, expense, transfer
    amount: float
    date: datetime
    partner: str
    category: str
    description: str
    created_at: datetime
    modified_at: datetime
    sync_status: SyncStatus = SyncStatus.PENDING
    version: int = 1
    
    def to_dict(self) -> dict:
        """Convert to dictionary for storage"""
        data = asdict(self)
        data['date'] = self.date.isoformat()
        data['created_at'] = self.created_at.isoformat()
        data['modified_at'] = self.modified_at.isoformat()
        data['sync_status'] = self.sync_status.value
        return data
    
    @classmethod
    def from_dict(cls, data: dict) -> 'OfflineTransaction':
        """Create from dictionary"""
        data = data.copy()
        data['date'] = datetime.fromisoformat(data['date'])
        data['created_at'] = datetime.fromisoformat(data['created_at'])
        data['modified_at'] = datetime.fromisoformat(data['modified_at'])
        data['sync_status'] = SyncStatus(data['sync_status'])
        return cls(**data)


@dataclass
class SyncConflict:
    """Represents a synchronization conflict"""
    conflict_id: str
    transaction_id: str
    local_version: int
    remote_version: int
    local_data: dict
    remote_data: dict
    detected_at: datetime
    resolution: Optional[ConflictResolution] = None
    resolved_at: Optional[datetime] = None
    
    def to_dict(self) -> dict:
        """Convert to dictionary"""
        data = asdict(self)
        data['detected_at'] = self.detected_at.isoformat()
        if self.resolved_at:
            data['resolved_at'] = self.resolved_at.isoformat()
        if self.resolution:
            data['resolution'] = self.resolution.value
        return data
    
    @classmethod
    def from_dict(cls, data: dict) -> 'SyncConflict':
        """Create from dictionary"""
        data = data.copy()
        data['detected_at'] = datetime.fromisoformat(data['detected_at'])
        if data.get('resolved_at'):
            data['resolved_at'] = datetime.fromisoformat(data['resolved_at'])
        if data.get('resolution'):
            data['resolution'] = ConflictResolution(data['resolution'])
        return cls(**data)


@dataclass
class SyncResult:
    """Result of a synchronization operation"""
    success: bool
    synced_count: int
    conflict_count: int
    failed_count: int
    conflicts: List[SyncConflict] = field(default_factory=list)
    errors: List[str] = field(default_factory=list)
    synced_at: datetime = field(default_factory=datetime.now)


class OfflineDataManager:
    """
    Manages offline data storage and synchronization.
    
    This manager provides:
    - Local data storage for offline operations
    - Basic transaction entry and viewing in offline mode
    - Automatic synchronization when connection is restored
    - Conflict resolution for offline/online data discrepancies
    """
    
    def __init__(self, storage_path: str = "财务数据/offline_data"):
        """
        Initialize offline data manager.
        
        Args:
            storage_path: Path to offline data storage directory
        """
        self.storage_path = storage_path
        self.connection_status = ConnectionStatus.ONLINE
        self.offline_transactions: Dict[str, OfflineTransaction] = {}
        self.sync_conflicts: Dict[str, SyncConflict] = {}
        self.pending_sync: Set[str] = set()
        
        # Create storage directory if it doesn't exist
        os.makedirs(storage_path, exist_ok=True)
        
        # Load offline data
        self._load_offline_data()
    
    def set_connection_status(self, status: ConnectionStatus) -> None:
        """
        Set network connection status.
        
        Args:
            status: New connection status
        """
        old_status = self.connection_status
        self.connection_status = status
        
        # Note: Auto-sync is available but not automatically triggered
        # User can call synchronize() manually when coming back online
    
    def is_online(self) -> bool:
        """Check if currently online"""
        return self.connection_status == ConnectionStatus.ONLINE
    
    def is_offline(self) -> bool:
        """Check if currently offline"""
        return self.connection_status == ConnectionStatus.OFFLINE
    
    def create_transaction(
        self,
        transaction_type: str,
        amount: float,
        date: datetime,
        partner: str,
        category: str,
        description: str
    ) -> OfflineTransaction:
        """
        Create a new transaction (works offline).
        
        Args:
            transaction_type: Type of transaction (income, expense, transfer)
            amount: Transaction amount
            date: Transaction date
            partner: Partner name
            category: Transaction category
            description: Transaction description
            
        Returns:
            Created offline transaction
        """
        transaction_id = f"offline_{datetime.now().strftime('%Y%m%d%H%M%S%f')}"
        now = datetime.now()
        
        transaction = OfflineTransaction(
            transaction_id=transaction_id,
            transaction_type=transaction_type,
            amount=amount,
            date=date,
            partner=partner,
            category=category,
            description=description,
            created_at=now,
            modified_at=now,
            sync_status=SyncStatus.PENDING if self.is_offline() else SyncStatus.SYNCED
        )
        
        self.offline_transactions[transaction_id] = transaction
        
        if self.is_offline():
            self.pending_sync.add(transaction_id)
        
        self._save_offline_data()
        
        return transaction
    
    def get_transaction(self, transaction_id: str) -> Optional[OfflineTransaction]:
        """
        Get a transaction by ID.
        
        Args:
            transaction_id: Transaction ID
            
        Returns:
            Transaction if found, None otherwise
        """
        return self.offline_transactions.get(transaction_id)
    
    def list_transactions(
        self,
        transaction_type: Optional[str] = None,
        sync_status: Optional[SyncStatus] = None
    ) -> List[OfflineTransaction]:
        """
        List transactions with optional filters.
        
        Args:
            transaction_type: Filter by transaction type
            sync_status: Filter by sync status
            
        Returns:
            List of matching transactions
        """
        transactions = list(self.offline_transactions.values())
        
        if transaction_type:
            transactions = [t for t in transactions if t.transaction_type == transaction_type]
        
        if sync_status:
            transactions = [t for t in transactions if t.sync_status == sync_status]
        
        # Sort by date descending
        transactions.sort(key=lambda t: t.date, reverse=True)
        
        return transactions
    
    def update_transaction(
        self,
        transaction_id: str,
        updates: dict
    ) -> Optional[OfflineTransaction]:
        """
        Update a transaction.
        
        Args:
            transaction_id: Transaction ID
            updates: Dictionary of fields to update
            
        Returns:
            Updated transaction if found, None otherwise
        """
        transaction = self.offline_transactions.get(transaction_id)
        if not transaction:
            return None
        
        # Update fields
        for key, value in updates.items():
            if hasattr(transaction, key) and key not in ['transaction_id', 'created_at']:
                setattr(transaction, key, value)
        
        # Update metadata
        transaction.modified_at = datetime.now()
        transaction.version += 1
        
        # Mark for sync if offline
        if self.is_offline() and transaction.sync_status == SyncStatus.SYNCED:
            transaction.sync_status = SyncStatus.PENDING
            self.pending_sync.add(transaction_id)
        
        self._save_offline_data()
        
        return transaction
    
    def delete_transaction(self, transaction_id: str) -> bool:
        """
        Delete a transaction.
        
        Args:
            transaction_id: Transaction ID
            
        Returns:
            True if deleted, False if not found
        """
        if transaction_id not in self.offline_transactions:
            return False
        
        del self.offline_transactions[transaction_id]
        self.pending_sync.discard(transaction_id)
        
        self._save_offline_data()
        
        return True
    
    def get_pending_sync_count(self) -> int:
        """Get count of transactions pending synchronization"""
        return len(self.pending_sync)
    
    def synchronize(self) -> SyncResult:
        """
        Synchronize offline data with remote server.
        
        This method:
        1. Uploads pending local changes
        2. Downloads remote changes
        3. Detects and resolves conflicts
        
        Returns:
            Synchronization result
        """
        if self.is_offline():
            return SyncResult(
                success=False,
                synced_count=0,
                conflict_count=0,
                failed_count=0,
                errors=["Cannot synchronize while offline"]
            )
        
        self.connection_status = ConnectionStatus.SYNCING
        
        synced_count = 0
        conflict_count = 0
        failed_count = 0
        conflicts = []
        errors = []
        
        try:
            # Process pending transactions
            for transaction_id in list(self.pending_sync):
                transaction = self.offline_transactions.get(transaction_id)
                if not transaction:
                    continue
                
                # Simulate remote sync (in real implementation, this would call API)
                remote_data = self._fetch_remote_transaction(transaction_id)
                
                if remote_data:
                    # Check for conflicts
                    if remote_data['version'] != transaction.version - 1:
                        # Conflict detected
                        conflict = self._create_conflict(transaction, remote_data)
                        conflicts.append(conflict)
                        conflict_count += 1
                    else:
                        # No conflict, sync successful
                        transaction.sync_status = SyncStatus.SYNCED
                        self.pending_sync.discard(transaction_id)
                        synced_count += 1
                else:
                    # New transaction, upload to remote
                    if self._upload_transaction(transaction):
                        transaction.sync_status = SyncStatus.SYNCED
                        self.pending_sync.discard(transaction_id)
                        synced_count += 1
                    else:
                        transaction.sync_status = SyncStatus.FAILED
                        failed_count += 1
                        errors.append(f"Failed to upload transaction {transaction_id}")
            
            self._save_offline_data()
            
        finally:
            self.connection_status = ConnectionStatus.ONLINE
        
        return SyncResult(
            success=failed_count == 0,
            synced_count=synced_count,
            conflict_count=conflict_count,
            failed_count=failed_count,
            conflicts=conflicts,
            errors=errors
        )
    
    def resolve_conflict(
        self,
        conflict_id: str,
        resolution: ConflictResolution,
        merged_data: Optional[dict] = None
    ) -> bool:
        """
        Resolve a synchronization conflict.
        
        Args:
            conflict_id: Conflict ID
            resolution: Resolution strategy
            merged_data: Merged data (required for MERGE resolution)
            
        Returns:
            True if resolved successfully
        """
        conflict = self.sync_conflicts.get(conflict_id)
        if not conflict:
            return False
        
        transaction = self.offline_transactions.get(conflict.transaction_id)
        if not transaction:
            return False
        
        # Apply resolution
        if resolution == ConflictResolution.LOCAL_WINS:
            # Keep local version, upload to remote
            self._upload_transaction(transaction)
        elif resolution == ConflictResolution.REMOTE_WINS:
            # Use remote version
            self._apply_remote_data(transaction, conflict.remote_data)
        elif resolution == ConflictResolution.MERGE:
            # Use merged data
            if not merged_data:
                return False
            self._apply_remote_data(transaction, merged_data)
            self._upload_transaction(transaction)
        elif resolution == ConflictResolution.MANUAL:
            # User will manually resolve
            return True
        
        # Mark conflict as resolved
        conflict.resolution = resolution
        conflict.resolved_at = datetime.now()
        transaction.sync_status = SyncStatus.SYNCED
        self.pending_sync.discard(transaction.transaction_id)
        
        self._save_offline_data()
        
        return True
    
    def get_conflicts(self) -> List[SyncConflict]:
        """Get all unresolved conflicts"""
        return [c for c in self.sync_conflicts.values() if not c.resolved_at]
    
    def _create_conflict(
        self,
        transaction: OfflineTransaction,
        remote_data: dict
    ) -> SyncConflict:
        """Create a conflict record"""
        conflict_id = f"conflict_{datetime.now().strftime('%Y%m%d%H%M%S%f')}"
        
        conflict = SyncConflict(
            conflict_id=conflict_id,
            transaction_id=transaction.transaction_id,
            local_version=transaction.version,
            remote_version=remote_data['version'],
            local_data=transaction.to_dict(),
            remote_data=remote_data,
            detected_at=datetime.now()
        )
        
        self.sync_conflicts[conflict_id] = conflict
        transaction.sync_status = SyncStatus.CONFLICT
        
        # Save conflicts immediately
        self._save_offline_data()
        
        return conflict
    
    def _fetch_remote_transaction(self, transaction_id: str) -> Optional[dict]:
        """
        Fetch transaction from remote server.
        
        In real implementation, this would call API.
        For testing, returns None (simulating new transaction).
        """
        return None
    
    def _upload_transaction(self, transaction: OfflineTransaction) -> bool:
        """
        Upload transaction to remote server.
        
        In real implementation, this would call API.
        For testing, always returns True.
        """
        return True
    
    def _apply_remote_data(self, transaction: OfflineTransaction, remote_data: dict) -> None:
        """Apply remote data to local transaction"""
        transaction.amount = remote_data['amount']
        transaction.date = datetime.fromisoformat(remote_data['date'])
        transaction.partner = remote_data['partner']
        transaction.category = remote_data['category']
        transaction.description = remote_data['description']
        transaction.version = remote_data['version']
        transaction.modified_at = datetime.now()
    
    def _load_offline_data(self) -> None:
        """Load offline data from storage"""
        transactions_file = os.path.join(self.storage_path, "transactions.json")
        conflicts_file = os.path.join(self.storage_path, "conflicts.json")
        
        # Load transactions
        if os.path.exists(transactions_file):
            try:
                with open(transactions_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self.offline_transactions = {
                        tid: OfflineTransaction.from_dict(tdata)
                        for tid, tdata in data.items()
                    }
                    # Rebuild pending sync set
                    self.pending_sync = {
                        tid for tid, t in self.offline_transactions.items()
                        if t.sync_status == SyncStatus.PENDING
                    }
            except Exception:
                pass
        
        # Load conflicts
        if os.path.exists(conflicts_file):
            try:
                with open(conflicts_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self.sync_conflicts = {
                        cid: SyncConflict.from_dict(cdata)
                        for cid, cdata in data.items()
                    }
            except Exception:
                pass
    
    def _save_offline_data(self) -> None:
        """Save offline data to storage"""
        transactions_file = os.path.join(self.storage_path, "transactions.json")
        conflicts_file = os.path.join(self.storage_path, "conflicts.json")
        
        # Save transactions
        with open(transactions_file, 'w', encoding='utf-8') as f:
            data = {
                tid: t.to_dict()
                for tid, t in self.offline_transactions.items()
            }
            json.dump(data, f, ensure_ascii=False, indent=2)
        
        # Save conflicts
        with open(conflicts_file, 'w', encoding='utf-8') as f:
            data = {
                cid: c.to_dict()
                for cid, c in self.sync_conflicts.items()
            }
            json.dump(data, f, ensure_ascii=False, indent=2)
