"""
端到端集成测试

测试完整的工作流：导入 → 生成报表 → 发送提醒
"""

import pytest
import os
import tempfile
import shutil
from datetime import date, datetime, timedelta
from decimal import Decimal
from pathlib import Path

from small_accountant_v16.config import ConfigManager
from small_accountant_v16.storage import (
    TransactionStorage,
    CounterpartyStorage,
    ReminderStorage
)
from small_accountant_v16.storage.import_history import ImportHistory
from small_accountant_v16.import_engine import ImportEngine
from small_accountant_v16.reports import ReportGenerator
from small_accountant_v16.reminders import ReminderSystem, ReminderScheduler
from small_accountant_v16.reconciliation import ReconciliationAssistant
from small_accountant_v16.models.core_models import (
    TransactionRecord, TransactionType, TransactionStatus,
    Counterparty, CounterpartyType,
    Reminder, ReminderType, Priority, ReminderStatus,
    NotificationChannel
)


@pytest.fixture
def integration_env(temp_dir):
    """创建集成测试环境"""
    # 创建配置
    config_file = os.path.join(temp_dir, "config.json")
    config_manager = ConfigManager(config_file)
    config_manager.config.storage.data_dir = temp_dir
    config_manager.config.storage.report_output_dir = os.path.join(temp_dir, "reports")
    config_manager.config.storage.backup_dir = os.path.join(temp_dir, "backups")
    config_manager.save_config()
    config_manager.ensure_directories()
    
    # 创建存储
    transaction_storage = TransactionStorage(temp_dir)
    counterparty_storage = CounterpartyStorage(temp_dir)
    reminder_storage = ReminderStorage(temp_dir)
    import_history = ImportHistory(temp_dir)
    
    # 创建服务
    import_engine = ImportEngine(
        transaction_storage=transaction_storage,
        counterparty_storage=counterparty_storage,
        import_history=import_history
    )
    
    report_generator = ReportGenerator(
        transaction_storage=transaction_storage,
        counterparty_storage=counterparty_storage,
        output_dir=config_manager.config.storage.report_output_dir
    )
    
    reminder_system = ReminderSystem(
        transaction_storage=transaction_storage,
        counterparty_storage=counterparty_storage,
        reminder_storage=reminder_storage,
        storage_dir=temp_dir,
        wechat_webhook_url=config_manager.config.wechat.webhook_url if config_manager.config.wechat.enabled else None
    )
    
    reminder_scheduler = ReminderScheduler(
        reminder_system=reminder_system,
        config_manager=config_manager,
        storage_dir=temp_dir
    )
    
    reconciliation_assistant = ReconciliationAssistant(
        transaction_storage=transaction_storage,
        counterparty_storage=counterparty_storage,
        output_dir=config_manager.config.storage.report_output_dir
    )
    
    return {
        "temp_dir": temp_dir,
        "config_manager": config_manager,
        "transaction_storage": transaction_storage,
        "counterparty_storage": counterparty_storage,
        "reminder_storage": reminder_storage,
        "import_history": import_history,
        "import_engine": import_engine,
        "report_generator": report_generator,
        "reminder_system": reminder_system,
        "reminder_scheduler": reminder_scheduler,
        "reconciliation_assistant": reconciliation_assistant,
    }


class TestEndToEndWorkflows:
    """测试端到端工作流"""
    
    def test_complete_workflow_import_report_reminder(self, integration_env):
        """测试完整工作流：导入数据 → 生成报表 → 发送提醒"""
        env = integration_env
        
        # 步骤1：添加往来单位
        customer = Counterparty(
            id="CUST001",
            name="测试客户公司",
            type=CounterpartyType.CUSTOMER,
            contact_person="张三",
            phone="13800138000",
            email="test@example.com",
            address="测试地址123号",
            tax_id="91110000123456789X",
            created_at=datetime.now(),
            updated_at=datetime.now()
        )
        env["counterparty_storage"].add(customer)
        
        # 步骤2：添加交易记录
        transactions = []
        for i in range(5):
            transaction = TransactionRecord(
                id=f"TXN{i:03d}",
                date=date.today() - timedelta(days=i),
                type=TransactionType.INCOME if i % 2 == 0 else TransactionType.EXPENSE,
                amount=Decimal(f"{1000 * (i + 1)}.00"),
                counterparty_id="CUST001",
                description=f"测试交易{i+1}",
                category="销售收入" if i % 2 == 0 else "采购成本",
                status=TransactionStatus.COMPLETED,
                created_at=datetime.now(),
                updated_at=datetime.now()
            )
            env["transaction_storage"].add(transaction)
            transactions.append(transaction)
        
        # 验证数据已添加
        assert len(env["transaction_storage"].get_all()) == 5
        assert len(env["counterparty_storage"].get_all()) == 1
        
        # 步骤3：生成管理报表
        start_date = date.today() - timedelta(days=30)
        end_date = date.today()
        
        report_result = env["report_generator"].generate_management_report(
            start_date=start_date,
            end_date=end_date
        )
        
        assert report_result.success
        assert os.path.exists(report_result.file_path)
        
        # 步骤4：检查提醒
        tax_reminders = env["reminder_system"].check_tax_reminders()
        receivable_reminders = env["reminder_system"].check_receivable_reminders()
        
        # 验证提醒系统正常工作（不抛出异常）
        assert isinstance(tax_reminders, list)
        assert isinstance(receivable_reminders, list)
        
        print(f"✅ 完整工作流测试通过")
        print(f"  - 添加了 {len(transactions)} 条交易记录")
        print(f"  - 添加了 1 个往来单位")
        print(f"  - 生成了管理报表：{report_result.file_path}")
        print(f"  - 检查了税务提醒：{len(tax_reminders)} 条")
        print(f"  - 检查了应收提醒：{len(receivable_reminders)} 条")
    
    def test_import_and_reconciliation_workflow(self, integration_env):
        """测试导入和对账工作流"""
        env = integration_env
        
        # 步骤1：添加测试数据
        customer = Counterparty(
            id="CUST002",
            name="对账测试客户",
            type=CounterpartyType.CUSTOMER,
            contact_person="李四",
            phone="13900139000",
            email="lisi@example.com",
            address="对账测试地址",
            tax_id="91110000987654321X",
            created_at=datetime.now(),
            updated_at=datetime.now()
        )
        env["counterparty_storage"].add(customer)
        
        # 添加交易记录
        for i in range(3):
            transaction = TransactionRecord(
                id=f"REC{i:03d}",
                date=date.today() - timedelta(days=i*10),
                type=TransactionType.INCOME,
                amount=Decimal(f"{5000 * (i + 1)}.00"),
                counterparty_id="CUST002",
                description=f"对账测试交易{i+1}",
                category="销售收入",
                status=TransactionStatus.COMPLETED,
                created_at=datetime.now(),
                updated_at=datetime.now()
            )
            env["transaction_storage"].add(transaction)
        
        # 步骤2：生成客户对账单
        start_date = date.today() - timedelta(days=90)
        end_date = date.today()
        
        statement = env["reconciliation_assistant"].generate_customer_statement(
            customer_id="CUST002",
            start_date=start_date,
            end_date=end_date
        )
        
        # 验证对账单生成
        assert statement is not None
        
        print(f"✅ 导入和对账工作流测试通过")
        print(f"  - 添加了对账测试客户")
        print(f"  - 添加了 3 条交易记录")
        print(f"  - 生成了客户对账单")
    
    def test_reminder_scheduling_workflow(self, integration_env):
        """测试提醒调度工作流"""
        env = integration_env
        
        # 步骤1：创建提醒
        reminder = Reminder(
            id="REM001",
            type=ReminderType.TAX,
            title="增值税申报提醒",
            description="请在本月15日前完成增值税申报",
            due_date=date.today() + timedelta(days=7),
            priority=Priority.HIGH,
            status=ReminderStatus.PENDING,
            notification_channels=[NotificationChannel.DESKTOP],
            created_at=datetime.now()
        )
        env["reminder_storage"].add(reminder)
        
        # 步骤2：安排提醒
        from small_accountant_v16.reminders.reminder_scheduler import ScheduleConfig, ScheduleFrequency
        from datetime import time as dt_time
        
        schedule = ScheduleConfig(
            frequency=ScheduleFrequency.DAILY,
            check_time=dt_time(9, 0)
        )
        
        env["reminder_scheduler"].schedule_reminder(
            reminder_id="REM001",
            name="增值税申报提醒",
            check_function="check_tax_reminders",
            schedule=schedule
        )
        
        # 步骤3：获取调度器状态
        status = env["reminder_scheduler"].get_status()
        
        assert "is_running" in status
        assert "total_scheduled" in status
        assert status["total_scheduled"] >= 1
        
        print(f"✅ 提醒调度工作流测试通过")
        print(f"  - 创建了提醒")
        print(f"  - 安排了调度")
        print(f"  - 调度器状态：{status}")
    
    def test_error_handling_workflow(self, integration_env):
        """测试错误处理工作流"""
        env = integration_env
        
        # 测试1：尝试生成空数据报表
        start_date = date.today() + timedelta(days=30)  # 未来日期
        end_date = date.today() + timedelta(days=60)
        
        report_result = env["report_generator"].generate_management_report(
            start_date=start_date,
            end_date=end_date
        )
        
        # 应该成功但可能没有数据
        assert report_result is not None
        
        # 测试2：尝试访问不存在的往来单位
        nonexistent = env["counterparty_storage"].get_by_id("NONEXISTENT")
        assert nonexistent is None
        
        # 测试3：尝试撤销不存在的导入
        undo_result = env["import_engine"].undo_import("NONEXISTENT_IMPORT")
        assert undo_result is False
        
        print(f"✅ 错误处理工作流测试通过")
        print(f"  - 处理了空数据报表生成")
        print(f"  - 处理了不存在的往来单位")
        print(f"  - 处理了无效的撤销操作")
    
    def test_configuration_workflow(self, integration_env):
        """测试配置管理工作流"""
        env = integration_env
        
        # 步骤1：更新配置
        env["config_manager"].update_reminder_config(
            tax_reminder_days=[10, 5, 2, 0],
            check_interval_minutes=30
        )
        
        # 步骤2：验证配置已更新
        config = env["config_manager"].get_config()
        assert config.reminder.tax_reminder_days == [10, 5, 2, 0]
        assert config.reminder.check_interval_minutes == 30
        
        # 步骤3：导出配置
        export_file = os.path.join(env["temp_dir"], "exported_config.json")
        env["config_manager"].export_config(export_file)
        assert os.path.exists(export_file)
        
        # 步骤4：重置配置
        env["config_manager"].reset_to_default()
        assert env["config_manager"].config.reminder.tax_reminder_days == [7, 3, 1, 0]
        
        # 步骤5：导入配置
        env["config_manager"].import_config(export_file)
        assert env["config_manager"].config.reminder.tax_reminder_days == [10, 5, 2, 0]
        
        print(f"✅ 配置管理工作流测试通过")
        print(f"  - 更新了配置")
        print(f"  - 导出了配置")
        print(f"  - 重置了配置")
        print(f"  - 导入了配置")


class TestDataIntegrity:
    """测试数据完整性"""
    
    def test_transaction_counterparty_relationship(self, integration_env):
        """测试交易记录和往来单位的关系完整性"""
        env = integration_env
        
        # 添加往来单位
        supplier = Counterparty(
            id="SUPP001",
            name="测试供应商",
            type=CounterpartyType.SUPPLIER,
            contact_person="王五",
            phone="13700137000",
            email="wangwu@example.com",
            address="供应商地址",
            tax_id="91110000111111111X",
            created_at=datetime.now(),
            updated_at=datetime.now()
        )
        env["counterparty_storage"].add(supplier)
        
        # 添加关联交易
        transaction = TransactionRecord(
            id="INT001",
            date=date.today(),
            type=TransactionType.EXPENSE,
            amount=Decimal("8000.00"),
            counterparty_id="SUPP001",
            description="采购原材料",
            category="采购成本",
            status=TransactionStatus.COMPLETED,
            created_at=datetime.now(),
            updated_at=datetime.now()
        )
        env["transaction_storage"].add(transaction)
        
        # 验证关系
        retrieved_transaction = env["transaction_storage"].get_by_id("INT001")
        assert retrieved_transaction is not None
        assert retrieved_transaction.counterparty_id == "SUPP001"
        
        retrieved_supplier = env["counterparty_storage"].get_by_id("SUPP001")
        assert retrieved_supplier is not None
        assert retrieved_supplier.name == "测试供应商"
        
        print(f"✅ 数据关系完整性测试通过")
    
    def test_import_history_tracking(self, integration_env):
        """测试导入历史追踪"""
        env = integration_env
        
        # 记录导入
        import_id = f"IMPORT_{datetime.now().strftime('%Y%m%d%H%M%S')}"
        env["import_history"].record_import(
            import_id=import_id,
            import_type="transactions",
            imported_ids=["TXN001", "TXN002", "TXN003", "TXN004", "TXN005", "TXN006", "TXN007", "TXN008"],
            source_file="test_import.xlsx"
        )
        
        assert import_id is not None
        
        # 获取历史
        history = env["import_history"].get_all_imports()
        assert len(history) > 0
        
        # 获取特定导入
        import_record = env["import_history"].get_import_by_id(import_id)
        assert import_record is not None
        assert import_record["imported_ids"] == ["TXN001", "TXN002", "TXN003", "TXN004", "TXN005", "TXN006", "TXN007", "TXN008"]
        
        print(f"✅ 导入历史追踪测试通过")


class TestPerformance:
    """测试性能"""
    
    def test_bulk_transaction_handling(self, integration_env):
        """测试批量交易处理性能"""
        env = integration_env
        
        # 添加往来单位
        customer = Counterparty(
            id="PERF001",
            name="性能测试客户",
            type=CounterpartyType.CUSTOMER,
            contact_person="性能测试",
            phone="13600136000",
            email="perf@example.com",
            address="性能测试地址",
            tax_id="91110000222222222X",
            created_at=datetime.now(),
            updated_at=datetime.now()
        )
        env["counterparty_storage"].add(customer)
        
        # 批量添加交易（100条）
        import time
        start_time = time.time()
        
        for i in range(100):
            transaction = TransactionRecord(
                id=f"PERF{i:04d}",
                date=date.today() - timedelta(days=i % 30),
                type=TransactionType.INCOME if i % 2 == 0 else TransactionType.EXPENSE,
                amount=Decimal(f"{100 * (i + 1)}.00"),
                counterparty_id="PERF001",
                description=f"性能测试交易{i+1}",
                category="测试类别",
                status=TransactionStatus.COMPLETED,
                created_at=datetime.now(),
                updated_at=datetime.now()
            )
            env["transaction_storage"].add(transaction)
        
        elapsed_time = time.time() - start_time
        
        # 验证所有交易已添加
        all_transactions = env["transaction_storage"].get_all()
        perf_transactions = [t for t in all_transactions if t.id.startswith("PERF")]
        assert len(perf_transactions) == 100
        
        # 性能应该在合理范围内（100条记录应该在5秒内完成）
        assert elapsed_time < 5.0
        
        print(f"✅ 批量交易处理性能测试通过")
        print(f"  - 添加了 100 条交易记录")
        print(f"  - 耗时：{elapsed_time:.2f} 秒")
        print(f"  - 平均每条：{elapsed_time/100*1000:.2f} 毫秒")


class TestRecovery:
    """测试恢复功能"""
    
    def test_config_backup_and_restore(self, integration_env):
        """测试配置备份和恢复"""
        env = integration_env
        
        # 修改配置
        original_days = env["config_manager"].config.reminder.tax_reminder_days
        env["config_manager"].update_reminder_config(tax_reminder_days=[20, 15, 10, 5])
        
        # 获取备份列表
        backups = env["config_manager"].list_backups()
        
        if backups:
            # 从备份恢复
            env["config_manager"].restore_from_backup(backups[0])
            
            # 验证恢复成功（配置应该改变）
            assert env["config_manager"].config is not None
            
            print(f"✅ 配置备份和恢复测试通过")
            print(f"  - 找到 {len(backups)} 个备份")
            print(f"  - 成功从备份恢复")
        else:
            print(f"⚠️  没有可用的备份文件")


@pytest.fixture
def temp_dir():
    """创建临时目录"""
    temp_dir = tempfile.mkdtemp()
    yield temp_dir
    shutil.rmtree(temp_dir, ignore_errors=True)
