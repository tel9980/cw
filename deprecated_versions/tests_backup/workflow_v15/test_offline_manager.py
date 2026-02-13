"""
Unit tests for Offline Data Management System

Tests cover:
- Offline transaction creation and management
- Connection status handling
- Synchronization logic
- Conflict detection and resolution
- Data persistence

Author: V1.5 Development Team
Date: 2026-02-10
"""

import unittest
import tempfile
import shutil
import os
from datetime import datetime, timedelta
from workflow_v15.core.offline_manager import (
    OfflineDataManager,
    OfflineTransaction,
    SyncConflict,
    ConnectionStatus,
    SyncStatus,
    ConflictResolution
)


class TestOfflineDataManagerInit(unittest.TestCase):
    """Test offline data manager initialization"""
    
    def setUp(self):
        """Set up test environment"""
        self.temp_dir = tempfile.mkdtemp()
        self.storage_path = os.path.join(self.temp_dir, "offline_data")
    
    def tearDown(self):
        """Clean up test environment"""
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_initialization(self):
        """Test manager initialization"""
        manager = OfflineDataManager(self.storage_path)
        
        self.assertEqual(manager.connection_status, ConnectionStatus.ONLINE)
        self.assertEqual(len(manager.offline_transactions), 0)
        self.assertEqual(len(manager.sync_conflicts), 0)
        self.assertEqual(len(manager.pending_sync), 0)
        self.assertTrue(os.path.exists(self.storage_path))
    
    def test_default_online_status(self):
        """Test default connection status is online"""
        manager = OfflineDataManager(self.storage_path)
        
        self.assertTrue(manager.is_online())
        self.assertFalse(manager.is_offline())


class TestConnectionStatus(unittest.TestCase):
    """Test connection status management"""
    
    def setUp(self):
        """Set up test environment"""
        self.temp_dir = tempfile.mkdtemp()
        self.storage_path = os.path.join(self.temp_dir, "offline_data")
        self.manager = OfflineDataManager(self.storage_path)
    
    def tearDown(self):
        """Clean up test environment"""
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_set_offline_status(self):
        """Test setting offline status"""
        self.manager.set_connection_status(ConnectionStatus.OFFLINE)
        
        self.assertEqual(self.manager.connection_status, ConnectionStatus.OFFLINE)
        self.assertTrue(self.manager.is_offline())
        self.assertFalse(self.manager.is_online())
    
    def test_set_online_status(self):
        """Test setting online status"""
        self.manager.set_connection_status(ConnectionStatus.OFFLINE)
        self.manager.set_connection_status(ConnectionStatus.ONLINE)
        
        self.assertEqual(self.manager.connection_status, ConnectionStatus.ONLINE)
        self.assertTrue(self.manager.is_online())
        self.assertFalse(self.manager.is_offline())
    
    def test_auto_sync_on_reconnect(self):
        """Test synchronization is available when coming back online"""
        # Create transaction while offline
        self.manager.set_connection_status(ConnectionStatus.OFFLINE)
        transaction = self.manager.create_transaction(
            transaction_type="income",
            amount=1000.0,
            date=datetime.now(),
            partner="客户A",
            category="销售收入",
            description="测试交易"
        )
        
        self.assertEqual(len(self.manager.pending_sync), 1)
        self.assertEqual(transaction.sync_status, SyncStatus.PENDING)
        
        # Go back online
        self.manager.set_connection_status(ConnectionStatus.ONLINE)
        
        # Verify we're online and can sync
        self.assertEqual(self.manager.connection_status, ConnectionStatus.ONLINE)
        self.assertTrue(self.manager.is_online())
        
        # Manually trigger sync
        result = self.manager.synchronize()
        self.assertTrue(result.success)


class TestOfflineTransactionCreation(unittest.TestCase):
    """Test offline transaction creation"""
    
    def setUp(self):
        """Set up test environment"""
        self.temp_dir = tempfile.mkdtemp()
        self.storage_path = os.path.join(self.temp_dir, "offline_data")
        self.manager = OfflineDataManager(self.storage_path)
    
    def tearDown(self):
        """Clean up test environment"""
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_create_transaction_online(self):
        """Test creating transaction while online"""
        transaction = self.manager.create_transaction(
            transaction_type="income",
            amount=1000.0,
            date=datetime.now(),
            partner="客户A",
            category="销售收入",
            description="测试交易"
        )
        
        self.assertIsNotNone(transaction)
        self.assertEqual(transaction.transaction_type, "income")
        self.assertEqual(transaction.amount, 1000.0)
        self.assertEqual(transaction.partner, "客户A")
        self.assertEqual(transaction.sync_status, SyncStatus.SYNCED)
        self.assertEqual(len(self.manager.pending_sync), 0)
    
    def test_create_transaction_offline(self):
        """Test creating transaction while offline"""
        self.manager.set_connection_status(ConnectionStatus.OFFLINE)
        
        transaction = self.manager.create_transaction(
            transaction_type="expense",
            amount=500.0,
            date=datetime.now(),
            partner="供应商B",
            category="采购成本",
            description="离线交易"
        )
        
        self.assertIsNotNone(transaction)
        self.assertEqual(transaction.sync_status, SyncStatus.PENDING)
        self.assertEqual(len(self.manager.pending_sync), 1)
        self.assertIn(transaction.transaction_id, self.manager.pending_sync)
    
    def test_transaction_id_generation(self):
        """Test transaction ID is unique"""
        t1 = self.manager.create_transaction(
            "income", 100.0, datetime.now(), "A", "Cat", "Desc"
        )
        t2 = self.manager.create_transaction(
            "expense", 200.0, datetime.now(), "B", "Cat", "Desc"
        )
        
        self.assertNotEqual(t1.transaction_id, t2.transaction_id)
        self.assertTrue(t1.transaction_id.startswith("offline_"))
        self.assertTrue(t2.transaction_id.startswith("offline_"))


class TestTransactionRetrieval(unittest.TestCase):
    """Test transaction retrieval operations"""
    
    def setUp(self):
        """Set up test environment"""
        self.temp_dir = tempfile.mkdtemp()
        self.storage_path = os.path.join(self.temp_dir, "offline_data")
        self.manager = OfflineDataManager(self.storage_path)
        
        # Create test transactions
        self.t1 = self.manager.create_transaction(
            "income", 1000.0, datetime.now(), "客户A", "销售", "收入1"
        )
        self.t2 = self.manager.create_transaction(
            "expense", 500.0, datetime.now(), "供应商B", "采购", "支出1"
        )
    
    def tearDown(self):
        """Clean up test environment"""
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_get_transaction(self):
        """Test getting transaction by ID"""
        transaction = self.manager.get_transaction(self.t1.transaction_id)
        
        self.assertIsNotNone(transaction)
        self.assertEqual(transaction.transaction_id, self.t1.transaction_id)
        self.assertEqual(transaction.amount, 1000.0)
    
    def test_get_nonexistent_transaction(self):
        """Test getting non-existent transaction"""
        transaction = self.manager.get_transaction("nonexistent_id")
        
        self.assertIsNone(transaction)
    
    def test_list_all_transactions(self):
        """Test listing all transactions"""
        transactions = self.manager.list_transactions()
        
        self.assertEqual(len(transactions), 2)
    
    def test_list_transactions_by_type(self):
        """Test filtering transactions by type"""
        income_transactions = self.manager.list_transactions(transaction_type="income")
        expense_transactions = self.manager.list_transactions(transaction_type="expense")
        
        self.assertEqual(len(income_transactions), 1)
        self.assertEqual(len(expense_transactions), 1)
        self.assertEqual(income_transactions[0].transaction_type, "income")
        self.assertEqual(expense_transactions[0].transaction_type, "expense")
    
    def test_list_transactions_by_sync_status(self):
        """Test filtering transactions by sync status"""
        # Set one transaction to pending
        self.manager.set_connection_status(ConnectionStatus.OFFLINE)
        t3 = self.manager.create_transaction(
            "income", 300.0, datetime.now(), "客户C", "销售", "待同步"
        )
        
        pending = self.manager.list_transactions(sync_status=SyncStatus.PENDING)
        synced = self.manager.list_transactions(sync_status=SyncStatus.SYNCED)
        
        self.assertEqual(len(pending), 1)
        self.assertEqual(len(synced), 2)
    
    def test_transactions_sorted_by_date(self):
        """Test transactions are sorted by date descending"""
        # Create transactions with different dates
        yesterday = datetime.now() - timedelta(days=1)
        tomorrow = datetime.now() + timedelta(days=1)
        
        t_old = self.manager.create_transaction(
            "income", 100.0, yesterday, "A", "Cat", "Old"
        )
        t_new = self.manager.create_transaction(
            "income", 200.0, tomorrow, "B", "Cat", "New"
        )
        
        transactions = self.manager.list_transactions()
        
        # Most recent should be first
        self.assertEqual(transactions[0].transaction_id, t_new.transaction_id)


class TestTransactionUpdate(unittest.TestCase):
    """Test transaction update operations"""
    
    def setUp(self):
        """Set up test environment"""
        self.temp_dir = tempfile.mkdtemp()
        self.storage_path = os.path.join(self.temp_dir, "offline_data")
        self.manager = OfflineDataManager(self.storage_path)
        
        self.transaction = self.manager.create_transaction(
            "income", 1000.0, datetime.now(), "客户A", "销售", "原始描述"
        )
    
    def tearDown(self):
        """Clean up test environment"""
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_update_transaction(self):
        """Test updating transaction"""
        updated = self.manager.update_transaction(
            self.transaction.transaction_id,
            {"amount": 1500.0, "description": "更新后的描述"}
        )
        
        self.assertIsNotNone(updated)
        self.assertEqual(updated.amount, 1500.0)
        self.assertEqual(updated.description, "更新后的描述")
        self.assertEqual(updated.version, 2)
    
    def test_update_increments_version(self):
        """Test update increments version number"""
        original_version = self.transaction.version
        
        self.manager.update_transaction(
            self.transaction.transaction_id,
            {"amount": 2000.0}
        )
        
        updated = self.manager.get_transaction(self.transaction.transaction_id)
        self.assertEqual(updated.version, original_version + 1)
    
    def test_update_marks_for_sync_when_offline(self):
        """Test update marks transaction for sync when offline"""
        # Transaction starts as synced (created online)
        self.assertEqual(self.transaction.sync_status, SyncStatus.SYNCED)
        
        # Go offline and update
        self.manager.set_connection_status(ConnectionStatus.OFFLINE)
        updated = self.manager.update_transaction(
            self.transaction.transaction_id,
            {"amount": 1500.0}
        )
        
        self.assertEqual(updated.sync_status, SyncStatus.PENDING)
        self.assertIn(self.transaction.transaction_id, self.manager.pending_sync)
    
    def test_update_nonexistent_transaction(self):
        """Test updating non-existent transaction"""
        updated = self.manager.update_transaction(
            "nonexistent_id",
            {"amount": 1500.0}
        )
        
        self.assertIsNone(updated)
    
    def test_update_preserves_immutable_fields(self):
        """Test update doesn't change immutable fields"""
        original_id = self.transaction.transaction_id
        original_created = self.transaction.created_at
        
        self.manager.update_transaction(
            self.transaction.transaction_id,
            {"transaction_id": "new_id", "created_at": datetime.now()}
        )
        
        updated = self.manager.get_transaction(original_id)
        self.assertEqual(updated.transaction_id, original_id)
        self.assertEqual(updated.created_at, original_created)


class TestTransactionDeletion(unittest.TestCase):
    """Test transaction deletion"""
    
    def setUp(self):
        """Set up test environment"""
        self.temp_dir = tempfile.mkdtemp()
        self.storage_path = os.path.join(self.temp_dir, "offline_data")
        self.manager = OfflineDataManager(self.storage_path)
        
        self.transaction = self.manager.create_transaction(
            "income", 1000.0, datetime.now(), "客户A", "销售", "测试"
        )
    
    def tearDown(self):
        """Clean up test environment"""
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_delete_transaction(self):
        """Test deleting transaction"""
        result = self.manager.delete_transaction(self.transaction.transaction_id)
        
        self.assertTrue(result)
        self.assertIsNone(self.manager.get_transaction(self.transaction.transaction_id))
        self.assertEqual(len(self.manager.offline_transactions), 0)
    
    def test_delete_removes_from_pending_sync(self):
        """Test deletion removes from pending sync"""
        self.manager.set_connection_status(ConnectionStatus.OFFLINE)
        t = self.manager.create_transaction(
            "income", 500.0, datetime.now(), "A", "Cat", "Desc"
        )
        
        self.assertIn(t.transaction_id, self.manager.pending_sync)
        
        self.manager.delete_transaction(t.transaction_id)
        
        self.assertNotIn(t.transaction_id, self.manager.pending_sync)
    
    def test_delete_nonexistent_transaction(self):
        """Test deleting non-existent transaction"""
        result = self.manager.delete_transaction("nonexistent_id")
        
        self.assertFalse(result)


class TestSynchronization(unittest.TestCase):
    """Test synchronization operations"""
    
    def setUp(self):
        """Set up test environment"""
        self.temp_dir = tempfile.mkdtemp()
        self.storage_path = os.path.join(self.temp_dir, "offline_data")
        self.manager = OfflineDataManager(self.storage_path)
    
    def tearDown(self):
        """Clean up test environment"""
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_sync_while_offline_fails(self):
        """Test synchronization fails when offline"""
        self.manager.set_connection_status(ConnectionStatus.OFFLINE)
        
        result = self.manager.synchronize()
        
        self.assertFalse(result.success)
        self.assertEqual(result.synced_count, 0)
        self.assertIn("offline", result.errors[0].lower())
    
    def test_sync_pending_transactions(self):
        """Test synchronizing pending transactions"""
        # Create offline transactions
        self.manager.set_connection_status(ConnectionStatus.OFFLINE)
        t1 = self.manager.create_transaction(
            "income", 1000.0, datetime.now(), "A", "Cat", "Desc1"
        )
        t2 = self.manager.create_transaction(
            "expense", 500.0, datetime.now(), "B", "Cat", "Desc2"
        )
        
        self.assertEqual(len(self.manager.pending_sync), 2)
        
        # Go online and sync
        self.manager.set_connection_status(ConnectionStatus.ONLINE)
        
        # Manually trigger sync
        result = self.manager.synchronize()
        
        self.assertTrue(result.success)
        self.assertEqual(result.synced_count, 2)
        self.assertEqual(result.conflict_count, 0)
        self.assertEqual(len(self.manager.pending_sync), 0)
    
    def test_sync_updates_transaction_status(self):
        """Test sync updates transaction sync status"""
        self.manager.set_connection_status(ConnectionStatus.OFFLINE)
        t = self.manager.create_transaction(
            "income", 1000.0, datetime.now(), "A", "Cat", "Desc"
        )
        
        self.assertEqual(t.sync_status, SyncStatus.PENDING)
        
        self.manager.set_connection_status(ConnectionStatus.ONLINE)
        self.manager.synchronize()
        
        updated = self.manager.get_transaction(t.transaction_id)
        self.assertEqual(updated.sync_status, SyncStatus.SYNCED)
    
    def test_get_pending_sync_count(self):
        """Test getting pending sync count"""
        self.assertEqual(self.manager.get_pending_sync_count(), 0)
        
        self.manager.set_connection_status(ConnectionStatus.OFFLINE)
        self.manager.create_transaction(
            "income", 1000.0, datetime.now(), "A", "Cat", "Desc"
        )
        self.manager.create_transaction(
            "expense", 500.0, datetime.now(), "B", "Cat", "Desc"
        )
        
        self.assertEqual(self.manager.get_pending_sync_count(), 2)


class TestConflictResolution(unittest.TestCase):
    """Test conflict detection and resolution"""
    
    def setUp(self):
        """Set up test environment"""
        self.temp_dir = tempfile.mkdtemp()
        self.storage_path = os.path.join(self.temp_dir, "offline_data")
        self.manager = OfflineDataManager(self.storage_path)
    
    def tearDown(self):
        """Clean up test environment"""
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_create_conflict(self):
        """Test creating a conflict"""
        transaction = self.manager.create_transaction(
            "income", 1000.0, datetime.now(), "A", "Cat", "Desc"
        )
        
        remote_data = {
            'amount': 1500.0,
            'date': datetime.now().isoformat(),
            'partner': 'A',
            'category': 'Cat',
            'description': 'Remote Desc',
            'version': 2
        }
        
        conflict = self.manager._create_conflict(transaction, remote_data)
        
        self.assertIsNotNone(conflict)
        self.assertEqual(conflict.transaction_id, transaction.transaction_id)
        self.assertEqual(conflict.local_version, transaction.version)
        self.assertEqual(conflict.remote_version, 2)
        self.assertEqual(transaction.sync_status, SyncStatus.CONFLICT)
    
    def test_resolve_conflict_local_wins(self):
        """Test resolving conflict with local wins strategy"""
        transaction = self.manager.create_transaction(
            "income", 1000.0, datetime.now(), "A", "Cat", "Local"
        )
        
        remote_data = {
            'amount': 1500.0,
            'date': datetime.now().isoformat(),
            'partner': 'A',
            'category': 'Cat',
            'description': 'Remote',
            'version': 2
        }
        
        conflict = self.manager._create_conflict(transaction, remote_data)
        
        result = self.manager.resolve_conflict(
            conflict.conflict_id,
            ConflictResolution.LOCAL_WINS
        )
        
        self.assertTrue(result)
        self.assertEqual(transaction.sync_status, SyncStatus.SYNCED)
        self.assertEqual(transaction.description, "Local")  # Local data preserved
    
    def test_resolve_conflict_remote_wins(self):
        """Test resolving conflict with remote wins strategy"""
        transaction = self.manager.create_transaction(
            "income", 1000.0, datetime.now(), "A", "Cat", "Local"
        )
        
        remote_data = {
            'amount': 1500.0,
            'date': datetime.now().isoformat(),
            'partner': 'A',
            'category': 'Cat',
            'description': 'Remote',
            'version': 2
        }
        
        conflict = self.manager._create_conflict(transaction, remote_data)
        
        result = self.manager.resolve_conflict(
            conflict.conflict_id,
            ConflictResolution.REMOTE_WINS
        )
        
        self.assertTrue(result)
        self.assertEqual(transaction.sync_status, SyncStatus.SYNCED)
        self.assertEqual(transaction.amount, 1500.0)  # Remote data applied
        self.assertEqual(transaction.description, "Remote")
    
    def test_resolve_conflict_merge(self):
        """Test resolving conflict with merge strategy"""
        transaction = self.manager.create_transaction(
            "income", 1000.0, datetime.now(), "A", "Cat", "Local"
        )
        
        remote_data = {
            'amount': 1500.0,
            'date': datetime.now().isoformat(),
            'partner': 'A',
            'category': 'Cat',
            'description': 'Remote',
            'version': 2
        }
        
        conflict = self.manager._create_conflict(transaction, remote_data)
        
        merged_data = {
            'amount': 1250.0,  # Average
            'date': datetime.now().isoformat(),
            'partner': 'A',
            'category': 'Cat',
            'description': 'Merged',
            'version': 3
        }
        
        result = self.manager.resolve_conflict(
            conflict.conflict_id,
            ConflictResolution.MERGE,
            merged_data
        )
        
        self.assertTrue(result)
        self.assertEqual(transaction.sync_status, SyncStatus.SYNCED)
        self.assertEqual(transaction.amount, 1250.0)
        self.assertEqual(transaction.description, "Merged")
    
    def test_get_unresolved_conflicts(self):
        """Test getting unresolved conflicts"""
        t1 = self.manager.create_transaction(
            "income", 1000.0, datetime.now(), "A", "Cat", "Desc"
        )
        t2 = self.manager.create_transaction(
            "expense", 500.0, datetime.now(), "B", "Cat", "Desc"
        )
        
        remote_data = {
            'amount': 1500.0,
            'date': datetime.now().isoformat(),
            'partner': 'A',
            'category': 'Cat',
            'description': 'Remote',
            'version': 2
        }
        
        c1 = self.manager._create_conflict(t1, remote_data)
        c2 = self.manager._create_conflict(t2, remote_data)
        
        # Resolve one conflict
        self.manager.resolve_conflict(c1.conflict_id, ConflictResolution.LOCAL_WINS)
        
        unresolved = self.manager.get_conflicts()
        
        self.assertEqual(len(unresolved), 1)
        self.assertEqual(unresolved[0].conflict_id, c2.conflict_id)


class TestDataPersistence(unittest.TestCase):
    """Test data persistence across sessions"""
    
    def setUp(self):
        """Set up test environment"""
        self.temp_dir = tempfile.mkdtemp()
        self.storage_path = os.path.join(self.temp_dir, "offline_data")
    
    def tearDown(self):
        """Clean up test environment"""
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_transactions_persist_across_sessions(self):
        """Test transactions are saved and loaded"""
        # Create manager and add transactions
        manager1 = OfflineDataManager(self.storage_path)
        t1 = manager1.create_transaction(
            "income", 1000.0, datetime.now(), "A", "Cat", "Desc1"
        )
        t2 = manager1.create_transaction(
            "expense", 500.0, datetime.now(), "B", "Cat", "Desc2"
        )
        
        # Create new manager instance (simulates restart)
        manager2 = OfflineDataManager(self.storage_path)
        
        # Verify transactions were loaded
        self.assertEqual(len(manager2.offline_transactions), 2)
        self.assertIsNotNone(manager2.get_transaction(t1.transaction_id))
        self.assertIsNotNone(manager2.get_transaction(t2.transaction_id))
    
    def test_pending_sync_persists(self):
        """Test pending sync set is restored"""
        manager1 = OfflineDataManager(self.storage_path)
        manager1.set_connection_status(ConnectionStatus.OFFLINE)
        
        t1 = manager1.create_transaction(
            "income", 1000.0, datetime.now(), "A", "Cat", "Desc"
        )
        
        self.assertEqual(len(manager1.pending_sync), 1)
        
        # Create new manager instance
        manager2 = OfflineDataManager(self.storage_path)
        
        # Verify pending sync was restored
        self.assertEqual(len(manager2.pending_sync), 1)
        self.assertIn(t1.transaction_id, manager2.pending_sync)
    
    def test_conflicts_persist(self):
        """Test conflicts are saved and loaded"""
        manager1 = OfflineDataManager(self.storage_path)
        t = manager1.create_transaction(
            "income", 1000.0, datetime.now(), "A", "Cat", "Desc"
        )
        
        remote_data = {
            'amount': 1500.0,
            'date': datetime.now().isoformat(),
            'partner': 'A',
            'category': 'Cat',
            'description': 'Remote',
            'version': 2
        }
        
        conflict = manager1._create_conflict(t, remote_data)
        
        # Create new manager instance
        manager2 = OfflineDataManager(self.storage_path)
        
        # Verify conflict was loaded
        self.assertEqual(len(manager2.sync_conflicts), 1)
        self.assertIn(conflict.conflict_id, manager2.sync_conflicts)


if __name__ == '__main__':
    unittest.main()
