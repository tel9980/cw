"""
Unit tests for storage layer

Tests CRUD operations and data persistence for:
- TransactionStorage
- CounterpartyStorage
- ReminderStorage
- ImportHistory
"""

import pytest
import os
from datetime import date, datetime
from decimal import Decimal
from pathlib import Path

from small_accountant_v16.models import (
    TransactionRecord,
    Counterparty,
    Reminder,
    ImportResult,
    ImportError,
    TransactionType,
    CounterpartyType,
    ReminderType,
    TransactionStatus,
    ReminderStatus,
    Priority,
    NotificationChannel,
)
from small_accountant_v16.storage import (
    TransactionStorage,
    CounterpartyStorage,
    ReminderStorage,
    ImportHistory,
    ImportRecord,
)


class TestTransactionStorage:
    """测试交易记录存储"""
    
    @pytest.fixture
    def storage(self, temp_dir):
        """创建交易存储实例"""
        return TransactionStorage(storage_dir=temp_dir)
    
    def test_add_transaction(self, storage, sample_transaction):
        """测试添加交易记录"""
        storage.add(sample_transaction)
        retrieved = storage.get(sample_transaction.id)
        
        assert retrieved is not None
        assert retrieved.id == sample_transaction.id
        assert retrieved.amount == sample_transaction.amount
        assert retrieved.description == sample_transaction.description
    
    def test_add_duplicate_transaction_raises_error(self, storage, sample_transaction):
        """测试添加重复ID的交易记录应该抛出错误"""
        storage.add(sample_transaction)
        
        with pytest.raises(ValueError, match="交易记录ID已存在"):
            storage.add(sample_transaction)
    
    def test_get_nonexistent_transaction(self, storage):
        """测试获取不存在的交易记录"""
        result = storage.get("NONEXISTENT")
        assert result is None
    
    def test_update_transaction(self, storage, sample_transaction):
        """测试更新交易记录"""
        storage.add(sample_transaction)
        
        # 修改金额
        sample_transaction.amount = Decimal("20000.00")
        storage.update(sample_transaction)
        
        retrieved = storage.get(sample_transaction.id)
        assert retrieved.amount == Decimal("20000.00")
    
    def test_update_nonexistent_transaction_raises_error(self, storage, sample_transaction):
        """测试更新不存在的交易记录应该抛出错误"""
        with pytest.raises(ValueError, match="交易记录不存在"):
            storage.update(sample_transaction)
    
    def test_delete_transaction(self, storage, sample_transaction):
        """测试删除交易记录"""
        storage.add(sample_transaction)
        storage.delete(sample_transaction.id)
        
        result = storage.get(sample_transaction.id)
        assert result is None
    
    def test_delete_nonexistent_transaction_raises_error(self, storage):
        """测试删除不存在的交易记录应该抛出错误"""
        with pytest.raises(ValueError, match="交易记录不存在"):
            storage.delete("NONEXISTENT")
    
    def test_get_all_transactions(self, storage):
        """测试获取所有交易记录"""
        # 添加多个交易
        transactions = [
            TransactionRecord(
                id=f"T{i:03d}",
                date=date(2024, 1, i+1),
                type=TransactionType.INCOME,
                amount=Decimal(f"{1000 * (i+1)}.00"),
                counterparty_id="C001",
                description=f"交易{i+1}",
                category="销售",
                status=TransactionStatus.COMPLETED,
                created_at=datetime.now(),
                updated_at=datetime.now(),
            )
            for i in range(5)
        ]
        
        for t in transactions:
            storage.add(t)
        
        all_transactions = storage.get_all()
        assert len(all_transactions) == 5
    
    def test_get_by_date_range(self, storage):
        """测试按日期范围查询"""
        # 添加不同日期的交易
        transactions = [
            TransactionRecord(
                id=f"T{i:03d}",
                date=date(2024, 1, i+1),
                type=TransactionType.INCOME,
                amount=Decimal("1000.00"),
                counterparty_id="C001",
                description=f"交易{i+1}",
                category="销售",
                status=TransactionStatus.COMPLETED,
                created_at=datetime.now(),
                updated_at=datetime.now(),
            )
            for i in range(10)
        ]
        
        for t in transactions:
            storage.add(t)
        
        # 查询1月5日到1月8日的交易
        results = storage.get_by_date_range(date(2024, 1, 5), date(2024, 1, 8))
        assert len(results) == 4  # 5, 6, 7, 8
    
    def test_get_by_type(self, storage):
        """测试按类型查询"""
        # 添加不同类型的交易
        income = TransactionRecord(
            id="T001",
            date=date(2024, 1, 1),
            type=TransactionType.INCOME,
            amount=Decimal("1000.00"),
            counterparty_id="C001",
            description="收入",
            category="销售",
            status=TransactionStatus.COMPLETED,
            created_at=datetime.now(),
            updated_at=datetime.now(),
        )
        expense = TransactionRecord(
            id="T002",
            date=date(2024, 1, 2),
            type=TransactionType.EXPENSE,
            amount=Decimal("500.00"),
            counterparty_id="S001",
            description="支出",
            category="采购",
            status=TransactionStatus.COMPLETED,
            created_at=datetime.now(),
            updated_at=datetime.now(),
        )
        
        storage.add(income)
        storage.add(expense)
        
        incomes = storage.get_by_type(TransactionType.INCOME)
        expenses = storage.get_by_type(TransactionType.EXPENSE)
        
        assert len(incomes) == 1
        assert len(expenses) == 1
        assert incomes[0].id == "T001"
        assert expenses[0].id == "T002"
    
    def test_get_by_counterparty(self, storage):
        """测试按往来单位查询"""
        # 添加不同往来单位的交易
        for i in range(3):
            storage.add(TransactionRecord(
                id=f"T{i:03d}",
                date=date(2024, 1, i+1),
                type=TransactionType.INCOME,
                amount=Decimal("1000.00"),
                counterparty_id="C001",
                description=f"交易{i+1}",
                category="销售",
                status=TransactionStatus.COMPLETED,
                created_at=datetime.now(),
                updated_at=datetime.now(),
            ))
        
        storage.add(TransactionRecord(
            id="T999",
            date=date(2024, 1, 10),
            type=TransactionType.INCOME,
            amount=Decimal("2000.00"),
            counterparty_id="C002",
            description="其他客户",
            category="销售",
            status=TransactionStatus.COMPLETED,
            created_at=datetime.now(),
            updated_at=datetime.now(),
        ))
        
        results = storage.get_by_counterparty("C001")
        assert len(results) == 3
    
    def test_get_total_amount_by_type(self, storage):
        """测试计算总金额"""
        # 添加多个收入交易
        for i in range(5):
            storage.add(TransactionRecord(
                id=f"T{i:03d}",
                date=date(2024, 1, i+1),
                type=TransactionType.INCOME,
                amount=Decimal("1000.00"),
                counterparty_id="C001",
                description=f"交易{i+1}",
                category="销售",
                status=TransactionStatus.COMPLETED,
                created_at=datetime.now(),
                updated_at=datetime.now(),
            ))
        
        total = storage.get_total_amount_by_type(TransactionType.INCOME)
        assert total == Decimal("5000.00")
    
    def test_count(self, storage):
        """测试计数"""
        assert storage.count() == 0
        
        storage.add(TransactionRecord(
            id="T001",
            date=date(2024, 1, 1),
            type=TransactionType.INCOME,
            amount=Decimal("1000.00"),
            counterparty_id="C001",
            description="交易",
            category="销售",
            status=TransactionStatus.COMPLETED,
            created_at=datetime.now(),
            updated_at=datetime.now(),
        ))
        
        assert storage.count() == 1
    
    def test_persistence(self, temp_dir):
        """测试数据持久化"""
        # 创建存储并添加数据
        storage1 = TransactionStorage(storage_dir=temp_dir)
        transaction = TransactionRecord(
            id="T001",
            date=date(2024, 1, 1),
            type=TransactionType.INCOME,
            amount=Decimal("1000.00"),
            counterparty_id="C001",
            description="测试持久化",
            category="销售",
            status=TransactionStatus.COMPLETED,
            created_at=datetime.now(),
            updated_at=datetime.now(),
        )
        storage1.add(transaction)
        
        # 创建新的存储实例，应该能读取到数据
        storage2 = TransactionStorage(storage_dir=temp_dir)
        retrieved = storage2.get("T001")
        
        assert retrieved is not None
        assert retrieved.description == "测试持久化"


class TestCounterpartyStorage:
    """测试往来单位存储"""
    
    @pytest.fixture
    def storage(self, temp_dir):
        """创建往来单位存储实例"""
        return CounterpartyStorage(storage_dir=temp_dir)
    
    def test_add_counterparty(self, storage, sample_counterparty):
        """测试添加往来单位"""
        storage.add(sample_counterparty)
        retrieved = storage.get(sample_counterparty.id)
        
        assert retrieved is not None
        assert retrieved.name == sample_counterparty.name
        assert retrieved.type == sample_counterparty.type
    
    def test_add_duplicate_counterparty_raises_error(self, storage, sample_counterparty):
        """测试添加重复ID的往来单位应该抛出错误"""
        storage.add(sample_counterparty)
        
        with pytest.raises(ValueError, match="往来单位ID已存在"):
            storage.add(sample_counterparty)
    
    def test_update_counterparty(self, storage, sample_counterparty):
        """测试更新往来单位"""
        storage.add(sample_counterparty)
        
        sample_counterparty.phone = "13900139000"
        storage.update(sample_counterparty)
        
        retrieved = storage.get(sample_counterparty.id)
        assert retrieved.phone == "13900139000"
    
    def test_delete_counterparty(self, storage, sample_counterparty):
        """测试删除往来单位"""
        storage.add(sample_counterparty)
        storage.delete(sample_counterparty.id)
        
        result = storage.get(sample_counterparty.id)
        assert result is None
    
    def test_get_by_type(self, storage):
        """测试按类型查询"""
        customer = Counterparty(
            id="C001",
            name="客户公司",
            type=CounterpartyType.CUSTOMER,
            contact_person="张三",
            phone="13800138000",
            email="test@example.com",
            address="地址",
            tax_id="123456789012345678",
            created_at=datetime.now(),
            updated_at=datetime.now(),
        )
        supplier = Counterparty(
            id="S001",
            name="供应商公司",
            type=CounterpartyType.SUPPLIER,
            contact_person="李四",
            phone="13900139000",
            email="test2@example.com",
            address="地址2",
            tax_id="987654321098765432",
            created_at=datetime.now(),
            updated_at=datetime.now(),
        )
        
        storage.add(customer)
        storage.add(supplier)
        
        customers = storage.get_customers()
        suppliers = storage.get_suppliers()
        
        assert len(customers) == 1
        assert len(suppliers) == 1
        assert customers[0].id == "C001"
        assert suppliers[0].id == "S001"
    
    def test_search_by_name(self, storage):
        """测试按名称搜索"""
        storage.add(Counterparty(
            id="C001",
            name="北京测试公司",
            type=CounterpartyType.CUSTOMER,
            contact_person="张三",
            phone="13800138000",
            email="test@example.com",
            address="地址",
            tax_id="123456789012345678",
            created_at=datetime.now(),
            updated_at=datetime.now(),
        ))
        storage.add(Counterparty(
            id="C002",
            name="上海测试公司",
            type=CounterpartyType.CUSTOMER,
            contact_person="李四",
            phone="13900139000",
            email="test2@example.com",
            address="地址2",
            tax_id="987654321098765432",
            created_at=datetime.now(),
            updated_at=datetime.now(),
        ))
        
        results = storage.search_by_name("测试")
        assert len(results) == 2
        
        results = storage.search_by_name("北京")
        assert len(results) == 1
        assert results[0].id == "C001"
    
    def test_get_by_tax_id(self, storage, sample_counterparty):
        """测试按税号查询"""
        storage.add(sample_counterparty)
        
        result = storage.get_by_tax_id(sample_counterparty.tax_id)
        assert result is not None
        assert result.id == sample_counterparty.id
    
    def test_exists(self, storage, sample_counterparty):
        """测试检查存在性"""
        assert not storage.exists(sample_counterparty.id)
        
        storage.add(sample_counterparty)
        assert storage.exists(sample_counterparty.id)
    
    def test_count_by_type(self, storage):
        """测试按类型计数"""
        for i in range(3):
            storage.add(Counterparty(
                id=f"C{i:03d}",
                name=f"客户{i}",
                type=CounterpartyType.CUSTOMER,
                contact_person="张三",
                phone="13800138000",
                email=f"test{i}@example.com",
                address="地址",
                tax_id=f"12345678901234567{i}",
                created_at=datetime.now(),
                updated_at=datetime.now(),
            ))
        
        for i in range(2):
            storage.add(Counterparty(
                id=f"S{i:03d}",
                name=f"供应商{i}",
                type=CounterpartyType.SUPPLIER,
                contact_person="李四",
                phone="13900139000",
                email=f"supplier{i}@example.com",
                address="地址",
                tax_id=f"98765432109876543{i}",
                created_at=datetime.now(),
                updated_at=datetime.now(),
            ))
        
        assert storage.count_by_type(CounterpartyType.CUSTOMER) == 3
        assert storage.count_by_type(CounterpartyType.SUPPLIER) == 2


class TestReminderStorage:
    """测试提醒存储"""
    
    @pytest.fixture
    def storage(self, temp_dir):
        """创建提醒存储实例"""
        return ReminderStorage(storage_dir=temp_dir)
    
    def test_add_reminder(self, storage, sample_reminder):
        """测试添加提醒"""
        storage.add(sample_reminder)
        retrieved = storage.get(sample_reminder.id)
        
        assert retrieved is not None
        assert retrieved.title == sample_reminder.title
        assert retrieved.type == sample_reminder.type
    
    def test_update_reminder(self, storage, sample_reminder):
        """测试更新提醒"""
        storage.add(sample_reminder)
        
        sample_reminder.status = ReminderStatus.SENT
        storage.update(sample_reminder)
        
        retrieved = storage.get(sample_reminder.id)
        assert retrieved.status == ReminderStatus.SENT
    
    def test_delete_reminder(self, storage, sample_reminder):
        """测试删除提醒"""
        storage.add(sample_reminder)
        storage.delete(sample_reminder.id)
        
        result = storage.get(sample_reminder.id)
        assert result is None
    
    def test_get_by_type(self, storage):
        """测试按类型查询"""
        tax_reminder = Reminder(
            id="R001",
            type=ReminderType.TAX,
            title="税务提醒",
            description="描述",
            due_date=date(2024, 1, 15),
            priority=Priority.HIGH,
            status=ReminderStatus.PENDING,
            notification_channels=[NotificationChannel.DESKTOP],
            created_at=datetime.now(),
        )
        payable_reminder = Reminder(
            id="R002",
            type=ReminderType.PAYABLE,
            title="应付账款提醒",
            description="描述",
            due_date=date(2024, 1, 20),
            priority=Priority.MEDIUM,
            status=ReminderStatus.PENDING,
            notification_channels=[NotificationChannel.DESKTOP],
            created_at=datetime.now(),
        )
        
        storage.add(tax_reminder)
        storage.add(payable_reminder)
        
        tax_reminders = storage.get_by_type(ReminderType.TAX)
        assert len(tax_reminders) == 1
        assert tax_reminders[0].id == "R001"
    
    def test_get_pending(self, storage):
        """测试获取待处理提醒"""
        pending = Reminder(
            id="R001",
            type=ReminderType.TAX,
            title="待处理",
            description="描述",
            due_date=date(2024, 1, 15),
            priority=Priority.HIGH,
            status=ReminderStatus.PENDING,
            notification_channels=[NotificationChannel.DESKTOP],
            created_at=datetime.now(),
        )
        sent = Reminder(
            id="R002",
            type=ReminderType.TAX,
            title="已发送",
            description="描述",
            due_date=date(2024, 1, 20),
            priority=Priority.HIGH,
            status=ReminderStatus.SENT,
            notification_channels=[NotificationChannel.DESKTOP],
            created_at=datetime.now(),
        )
        
        storage.add(pending)
        storage.add(sent)
        
        pending_reminders = storage.get_pending()
        assert len(pending_reminders) == 1
        assert pending_reminders[0].id == "R001"
    
    def test_get_due_reminders(self, storage):
        """测试获取到期提醒"""
        today = date.today()
        from datetime import timedelta
        
        due_today = Reminder(
            id="R001",
            type=ReminderType.TAX,
            title="今天到期",
            description="描述",
            due_date=today,
            priority=Priority.HIGH,
            status=ReminderStatus.PENDING,
            notification_channels=[NotificationChannel.DESKTOP],
            created_at=datetime.now(),
        )
        due_tomorrow = Reminder(
            id="R002",
            type=ReminderType.TAX,
            title="明天到期",
            description="描述",
            due_date=today + timedelta(days=1),
            priority=Priority.HIGH,
            status=ReminderStatus.PENDING,
            notification_channels=[NotificationChannel.DESKTOP],
            created_at=datetime.now(),
        )
        
        storage.add(due_today)
        storage.add(due_tomorrow)
        
        due_reminders = storage.get_due_reminders(today)
        assert len(due_reminders) == 1
        assert due_reminders[0].id == "R001"
    
    def test_get_upcoming_reminders(self, storage):
        """测试获取即将到期的提醒"""
        today = date.today()
        from datetime import timedelta
        
        for i in range(10):
            storage.add(Reminder(
                id=f"R{i:03d}",
                type=ReminderType.TAX,
                title=f"提醒{i}",
                description="描述",
                due_date=today + timedelta(days=i),
                priority=Priority.HIGH,
                status=ReminderStatus.PENDING,
                notification_channels=[NotificationChannel.DESKTOP],
                created_at=datetime.now(),
            ))
        
        upcoming = storage.get_upcoming_reminders(days=7)
        assert len(upcoming) == 8  # 0-7天，包含今天
    
    def test_mark_as_sent(self, storage, sample_reminder):
        """测试标记为已发送"""
        storage.add(sample_reminder)
        storage.mark_as_sent(sample_reminder.id)
        
        retrieved = storage.get(sample_reminder.id)
        assert retrieved.status == ReminderStatus.SENT
    
    def test_mark_as_completed(self, storage, sample_reminder):
        """测试标记为已完成"""
        storage.add(sample_reminder)
        storage.mark_as_completed(sample_reminder.id)
        
        retrieved = storage.get(sample_reminder.id)
        assert retrieved.status == ReminderStatus.COMPLETED


class TestImportHistory:
    """测试导入历史管理"""
    
    @pytest.fixture
    def storage(self, temp_dir):
        """创建导入历史存储实例"""
        return ImportHistory(storage_dir=temp_dir)
    
    @pytest.fixture
    def sample_import_result(self):
        """创建示例导入结果"""
        return ImportResult(
            import_id="IMP001",
            total_rows=100,
            successful_rows=95,
            failed_rows=5,
            errors=[
                ImportError(row_number=10, field="amount", error_message="金额格式错误"),
                ImportError(row_number=25, field="date", error_message="日期格式错误"),
            ],
            import_date=datetime.now(),
            can_undo=True,
        )
    
    def test_record_import(self, storage, sample_import_result):
        """测试记录导入操作"""
        imported_ids = [f"T{i:03d}" for i in range(95)]
        
        storage.record_import(
            import_id="IMP001",
            import_type="transactions",
            imported_ids=imported_ids,
            import_result=sample_import_result,
        )
        
        record = storage.get_import_record("IMP001")
        assert record is not None
        assert record.import_type == "transactions"
        assert len(record.imported_ids) == 95
    
    def test_get_all_imports(self, storage, sample_import_result):
        """测试获取所有导入记录"""
        # 记录多个导入
        for i in range(5):
            storage.record_import(
                import_id=f"IMP{i:03d}",
                import_type="transactions",
                imported_ids=[f"T{j:03d}" for j in range(10)],
                import_result=sample_import_result,
            )
        
        all_imports = storage.get_all_imports()
        assert len(all_imports) == 5
    
    def test_get_imports_by_type(self, storage, sample_import_result):
        """测试按类型获取导入记录"""
        storage.record_import(
            import_id="IMP001",
            import_type="transactions",
            imported_ids=["T001", "T002"],
            import_result=sample_import_result,
        )
        storage.record_import(
            import_id="IMP002",
            import_type="counterparties",
            imported_ids=["C001", "C002"],
            import_result=sample_import_result,
        )
        
        transaction_imports = storage.get_imports_by_type("transactions")
        counterparty_imports = storage.get_imports_by_type("counterparties")
        
        assert len(transaction_imports) == 1
        assert len(counterparty_imports) == 1
    
    def test_mark_as_undone(self, storage, sample_import_result):
        """测试标记为已撤销"""
        storage.record_import(
            import_id="IMP001",
            import_type="transactions",
            imported_ids=["T001"],
            import_result=sample_import_result,
        )
        
        assert storage.can_undo_import("IMP001")
        
        storage.mark_as_undone("IMP001")
        assert not storage.can_undo_import("IMP001")
    
    def test_get_imported_ids(self, storage, sample_import_result):
        """测试获取导入的ID列表"""
        imported_ids = ["T001", "T002", "T003"]
        
        storage.record_import(
            import_id="IMP001",
            import_type="transactions",
            imported_ids=imported_ids,
            import_result=sample_import_result,
        )
        
        retrieved_ids = storage.get_imported_ids("IMP001")
        assert retrieved_ids == imported_ids
    
    def test_get_statistics(self, storage, sample_import_result):
        """测试获取统计信息"""
        # 记录多个导入
        storage.record_import(
            import_id="IMP001",
            import_type="transactions",
            imported_ids=["T001", "T002"],
            import_result=sample_import_result,
        )
        storage.record_import(
            import_id="IMP002",
            import_type="counterparties",
            imported_ids=["C001"],
            import_result=sample_import_result,
        )
        
        stats = storage.get_statistics()
        
        assert stats["total_imports"] == 2
        assert stats["transaction_imports"] == 1
        assert stats["counterparty_imports"] == 1
        assert stats["total_records_imported"] == 95 * 2  # 每个导入95条成功记录
    
    def test_delete_import_record(self, storage, sample_import_result):
        """测试删除导入记录"""
        storage.record_import(
            import_id="IMP001",
            import_type="transactions",
            imported_ids=["T001"],
            import_result=sample_import_result,
        )
        
        storage.delete_import_record("IMP001")
        
        record = storage.get_import_record("IMP001")
        assert record is None


class TestBaseStorage:
    """测试基础存储功能"""
    
    def test_backup_and_restore(self, temp_dir, sample_transaction):
        """测试备份和恢复"""
        storage = TransactionStorage(storage_dir=temp_dir)
        storage.add(sample_transaction)
        
        # 备份
        backup_path = os.path.join(temp_dir, "backup.json")
        storage.backup(backup_path)
        
        # 清空数据
        storage.clear()
        assert storage.count() == 0
        
        # 恢复
        storage.restore(backup_path)
        assert storage.count() == 1
        
        retrieved = storage.get(sample_transaction.id)
        assert retrieved is not None
        assert retrieved.id == sample_transaction.id
    
    def test_clear(self, temp_dir, sample_transaction):
        """测试清空数据"""
        storage = TransactionStorage(storage_dir=temp_dir)
        storage.add(sample_transaction)
        
        assert storage.count() == 1
        
        storage.clear()
        assert storage.count() == 0
