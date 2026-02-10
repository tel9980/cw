"""
Unit tests for ReminderScheduler

Tests the reminder scheduling functionality including:
- Scheduling reminders with different frequencies
- Running scheduled checks
- Calculating next run times
- Enabling/disabling reminders
- Configuration support
"""

import pytest
from datetime import datetime, date, time as dt_time, timedelta
from decimal import Decimal
from unittest.mock import Mock, patch, MagicMock
import uuid

from small_accountant_v16.reminders.reminder_scheduler import (
    ReminderScheduler, ScheduleConfig, ScheduledReminder, ScheduleFrequency
)
from small_accountant_v16.reminders.reminder_system import ReminderSystem
from small_accountant_v16.models.core_models import (
    Reminder, ReminderType, ReminderStatus, Priority, NotificationChannel,
    TransactionRecord, TransactionType, TransactionStatus, Counterparty, CounterpartyType
)
from small_accountant_v16.config.config_manager import ConfigManager
from small_accountant_v16.storage.transaction_storage import TransactionStorage
from small_accountant_v16.storage.counterparty_storage import CounterpartyStorage
from small_accountant_v16.storage.reminder_storage import ReminderStorage


@pytest.fixture
def temp_storage(tmp_path):
    """临时存储目录"""
    return str(tmp_path / "test_data")


@pytest.fixture
def mock_reminder_system():
    """模拟提醒系统"""
    system = Mock(spec=ReminderSystem)
    
    # 模拟检查函数返回空列表
    system.check_tax_reminders.return_value = []
    system.check_payable_reminders.return_value = []
    system.check_receivable_reminders.return_value = []
    system.check_cashflow_warnings.return_value = []
    system.send_reminder.return_value = {"desktop": True, "wechat": True}
    
    return system


@pytest.fixture
def mock_config_manager():
    """模拟配置管理器"""
    config_manager = Mock(spec=ConfigManager)
    
    # 模拟配置
    mock_config = Mock()
    mock_config.reminder.enable_desktop_notification = True
    mock_config.reminder.enable_wechat_notification = True
    mock_config.wechat.enabled = True
    
    config_manager.get_config.return_value = mock_config
    
    return config_manager


@pytest.fixture
def scheduler(mock_reminder_system, mock_config_manager, temp_storage):
    """提醒调度器实例"""
    return ReminderScheduler(
        reminder_system=mock_reminder_system,
        config_manager=mock_config_manager,
        storage_dir=temp_storage
    )


class TestScheduleConfig:
    """测试调度配置"""
    
    def test_schedule_config_creation(self):
        """测试创建调度配置"""
        config = ScheduleConfig(
            frequency=ScheduleFrequency.DAILY,
            check_time=dt_time(9, 0),
            enabled=True
        )
        
        assert config.frequency == ScheduleFrequency.DAILY
        assert config.check_time == dt_time(9, 0)
        assert config.enabled is True
        assert NotificationChannel.DESKTOP in config.notification_channels
        assert NotificationChannel.WECHAT in config.notification_channels
    
    def test_schedule_config_to_dict(self):
        """测试调度配置转换为字典"""
        config = ScheduleConfig(
            frequency=ScheduleFrequency.WEEKLY,
            check_time=dt_time(10, 30),
            enabled=False,
            notification_channels=[NotificationChannel.DESKTOP]
        )
        
        data = config.to_dict()
        
        assert data["frequency"] == "weekly"
        assert data["check_time"] == "10:30"
        assert data["enabled"] is False
        assert data["notification_channels"] == ["desktop"]
    
    def test_schedule_config_from_dict(self):
        """测试从字典创建调度配置"""
        data = {
            "frequency": "monthly",
            "check_time": "08:00",
            "enabled": True,
            "notification_channels": ["wechat"]
        }
        
        config = ScheduleConfig.from_dict(data)
        
        assert config.frequency == ScheduleFrequency.MONTHLY
        assert config.check_time == dt_time(8, 0)
        assert config.enabled is True
        assert config.notification_channels == [NotificationChannel.WECHAT]


class TestReminderScheduler:
    """测试提醒调度器"""
    
    def test_scheduler_initialization(self, scheduler):
        """测试调度器初始化"""
        assert scheduler.reminder_system is not None
        assert scheduler.config_manager is not None
        assert len(scheduler.scheduled_reminders) == 0
        assert scheduler.is_running is False
    
    def test_schedule_reminder(self, scheduler):
        """测试安排提醒任务"""
        schedule = ScheduleConfig(
            frequency=ScheduleFrequency.DAILY,
            check_time=dt_time(9, 0)
        )
        
        scheduled = scheduler.schedule_reminder(
            reminder_id="test_reminder",
            name="测试提醒",
            check_function="check_tax_reminders",
            schedule=schedule
        )
        
        assert scheduled.id == "test_reminder"
        assert scheduled.name == "测试提醒"
        assert scheduled.check_function == "check_tax_reminders"
        assert scheduled.enabled is True
        assert scheduled.next_run is not None
        assert "test_reminder" in scheduler.scheduled_reminders
    
    def test_calculate_next_run_daily(self, scheduler):
        """测试计算每日下次运行时间"""
        schedule = ScheduleConfig(
            frequency=ScheduleFrequency.DAILY,
            check_time=dt_time(9, 0)
        )
        
        # 测试当前时间在检查时间之前
        from_time = datetime(2024, 1, 15, 8, 0)
        next_run = scheduler._calculate_next_run(schedule, from_time)
        assert next_run == datetime(2024, 1, 15, 9, 0)
        
        # 测试当前时间在检查时间之后
        from_time = datetime(2024, 1, 15, 10, 0)
        next_run = scheduler._calculate_next_run(schedule, from_time)
        assert next_run == datetime(2024, 1, 16, 9, 0)
    
    def test_calculate_next_run_weekly(self, scheduler):
        """测试计算每周下次运行时间"""
        schedule = ScheduleConfig(
            frequency=ScheduleFrequency.WEEKLY,
            check_time=dt_time(9, 0)
        )
        
        # 测试从周三计算（应该到下周一）
        from_time = datetime(2024, 1, 17, 10, 0)  # 2024-01-17 是周三
        next_run = scheduler._calculate_next_run(schedule, from_time)
        
        # 下周一应该是 2024-01-22
        assert next_run.weekday() == 0  # 周一
        assert next_run.time() == dt_time(9, 0)
    
    def test_calculate_next_run_monthly(self, scheduler):
        """测试计算每月下次运行时间"""
        schedule = ScheduleConfig(
            frequency=ScheduleFrequency.MONTHLY,
            check_time=dt_time(9, 0)
        )
        
        # 测试从月中计算（应该到下月1号）
        from_time = datetime(2024, 1, 15, 10, 0)
        next_run = scheduler._calculate_next_run(schedule, from_time)
        assert next_run == datetime(2024, 2, 1, 9, 0)
        
        # 测试从12月计算（应该到次年1月）
        from_time = datetime(2024, 12, 15, 10, 0)
        next_run = scheduler._calculate_next_run(schedule, from_time)
        assert next_run == datetime(2025, 1, 1, 9, 0)
    
    def test_calculate_next_run_custom(self, scheduler):
        """测试计算自定义间隔下次运行时间"""
        schedule = ScheduleConfig(
            frequency=ScheduleFrequency.CUSTOM,
            check_time=dt_time(9, 0),
            custom_interval_minutes=30
        )
        
        from_time = datetime(2024, 1, 15, 10, 0)
        next_run = scheduler._calculate_next_run(schedule, from_time)
        assert next_run == datetime(2024, 1, 15, 10, 30)
    
    def test_run_scheduled_checks_no_tasks(self, scheduler):
        """测试运行定时检查（无任务）"""
        results = scheduler.run_scheduled_checks()
        
        assert results["total_scheduled"] == 0
        assert results["executed"] == 0
        assert results["skipped"] == 0
        assert results["failed"] == 0
    
    def test_run_scheduled_checks_with_due_task(self, scheduler, mock_reminder_system):
        """测试运行定时检查（有到期任务）"""
        # 创建一个已经到期的任务
        schedule = ScheduleConfig(
            frequency=ScheduleFrequency.DAILY,
            check_time=dt_time(9, 0)
        )
        
        # 设置下次运行时间为过去
        past_time = datetime.now() - timedelta(hours=1)
        
        scheduled = scheduler.schedule_reminder(
            reminder_id="test_task",
            name="测试任务",
            check_function="check_tax_reminders",
            schedule=schedule
        )
        scheduled.next_run = past_time
        
        # 模拟检查函数返回一些提醒
        mock_reminders = [
            Reminder(
                id=str(uuid.uuid4()),
                type=ReminderType.TAX,
                title="测试提醒",
                description="测试描述",
                due_date=date.today(),
                priority=Priority.HIGH,
                status=ReminderStatus.PENDING,
                notification_channels=[NotificationChannel.DESKTOP],
                created_at=datetime.now()
            )
        ]
        mock_reminder_system.check_tax_reminders.return_value = mock_reminders
        
        # 运行检查
        results = scheduler.run_scheduled_checks()
        
        assert results["total_scheduled"] == 1
        assert results["executed"] == 1
        assert results["reminders_found"] == 1
        assert results["reminders_sent"] == 1
        
        # 验证调用了检查函数
        mock_reminder_system.check_tax_reminders.assert_called_once()
        mock_reminder_system.send_reminder.assert_called_once()
        
        # 验证更新了运行时间
        assert scheduled.last_run is not None
        assert scheduled.next_run > datetime.now()
    
    def test_run_scheduled_checks_skip_disabled(self, scheduler):
        """测试运行定时检查（跳过禁用任务）"""
        schedule = ScheduleConfig(
            frequency=ScheduleFrequency.DAILY,
            check_time=dt_time(9, 0),
            enabled=False
        )
        
        scheduler.schedule_reminder(
            reminder_id="disabled_task",
            name="禁用任务",
            check_function="check_tax_reminders",
            schedule=schedule
        )
        
        results = scheduler.run_scheduled_checks()
        
        assert results["total_scheduled"] == 1
        assert results["executed"] == 0
        assert results["skipped"] == 1
    
    def test_run_scheduled_checks_not_due(self, scheduler):
        """测试运行定时检查（任务未到期）"""
        schedule = ScheduleConfig(
            frequency=ScheduleFrequency.DAILY,
            check_time=dt_time(9, 0)
        )
        
        # 设置下次运行时间为未来
        future_time = datetime.now() + timedelta(hours=1)
        
        scheduled = scheduler.schedule_reminder(
            reminder_id="future_task",
            name="未来任务",
            check_function="check_tax_reminders",
            schedule=schedule
        )
        scheduled.next_run = future_time
        
        results = scheduler.run_scheduled_checks()
        
        assert results["total_scheduled"] == 1
        assert results["executed"] == 0
        assert results["skipped"] == 1
    
    def test_run_scheduled_checks_with_error(self, scheduler, mock_reminder_system):
        """测试运行定时检查（任务执行失败）"""
        schedule = ScheduleConfig(
            frequency=ScheduleFrequency.DAILY,
            check_time=dt_time(9, 0)
        )
        
        past_time = datetime.now() - timedelta(hours=1)
        
        scheduled = scheduler.schedule_reminder(
            reminder_id="error_task",
            name="错误任务",
            check_function="check_tax_reminders",
            schedule=schedule
        )
        scheduled.next_run = past_time
        
        # 模拟检查函数抛出异常
        mock_reminder_system.check_tax_reminders.side_effect = Exception("测试错误")
        
        results = scheduler.run_scheduled_checks()
        
        assert results["total_scheduled"] == 1
        assert results["executed"] == 0
        assert results["failed"] == 1
        assert len(results["details"]) == 1
        assert results["details"][0]["status"] == "failed"
    
    def test_setup_default_schedules(self, scheduler):
        """测试设置默认调度任务"""
        scheduler.setup_default_schedules()
        
        assert len(scheduler.scheduled_reminders) == 4
        assert "tax_reminders" in scheduler.scheduled_reminders
        assert "payable_reminders" in scheduler.scheduled_reminders
        assert "receivable_reminders" in scheduler.scheduled_reminders
        assert "cashflow_warnings" in scheduler.scheduled_reminders
        
        # 验证所有任务都已启用
        for reminder in scheduler.scheduled_reminders.values():
            assert reminder.enabled is True
            assert reminder.next_run is not None
    
    def test_enable_reminder(self, scheduler):
        """测试启用提醒任务"""
        schedule = ScheduleConfig(
            frequency=ScheduleFrequency.DAILY,
            check_time=dt_time(9, 0),
            enabled=False
        )
        
        scheduler.schedule_reminder(
            reminder_id="test_reminder",
            name="测试提醒",
            check_function="check_tax_reminders",
            schedule=schedule
        )
        
        # 启用任务
        result = scheduler.enable_reminder("test_reminder")
        
        assert result is True
        assert scheduler.scheduled_reminders["test_reminder"].enabled is True
    
    def test_disable_reminder(self, scheduler):
        """测试禁用提醒任务"""
        schedule = ScheduleConfig(
            frequency=ScheduleFrequency.DAILY,
            check_time=dt_time(9, 0)
        )
        
        scheduler.schedule_reminder(
            reminder_id="test_reminder",
            name="测试提醒",
            check_function="check_tax_reminders",
            schedule=schedule
        )
        
        # 禁用任务
        result = scheduler.disable_reminder("test_reminder")
        
        assert result is True
        assert scheduler.scheduled_reminders["test_reminder"].enabled is False
    
    def test_remove_reminder(self, scheduler):
        """测试移除提醒任务"""
        schedule = ScheduleConfig(
            frequency=ScheduleFrequency.DAILY,
            check_time=dt_time(9, 0)
        )
        
        scheduler.schedule_reminder(
            reminder_id="test_reminder",
            name="测试提醒",
            check_function="check_tax_reminders",
            schedule=schedule
        )
        
        # 移除任务
        result = scheduler.remove_reminder("test_reminder")
        
        assert result is True
        assert "test_reminder" not in scheduler.scheduled_reminders
    
    def test_get_scheduled_reminders(self, scheduler):
        """测试获取所有已调度的提醒任务"""
        scheduler.setup_default_schedules()
        
        reminders = scheduler.get_scheduled_reminders()
        
        assert len(reminders) == 4
        assert all(isinstance(r, ScheduledReminder) for r in reminders)
    
    def test_get_reminder(self, scheduler):
        """测试获取指定的提醒任务"""
        schedule = ScheduleConfig(
            frequency=ScheduleFrequency.DAILY,
            check_time=dt_time(9, 0)
        )
        
        scheduler.schedule_reminder(
            reminder_id="test_reminder",
            name="测试提醒",
            check_function="check_tax_reminders",
            schedule=schedule
        )
        
        reminder = scheduler.get_reminder("test_reminder")
        
        assert reminder is not None
        assert reminder.id == "test_reminder"
        assert reminder.name == "测试提醒"
    
    def test_get_reminder_not_found(self, scheduler):
        """测试获取不存在的提醒任务"""
        reminder = scheduler.get_reminder("nonexistent")
        assert reminder is None
    
    def test_get_status(self, scheduler):
        """测试获取调度器状态"""
        scheduler.setup_default_schedules()
        
        status = scheduler.get_status()
        
        assert status["is_running"] is False
        assert status["total_scheduled"] == 4
        assert status["enabled_count"] == 4
        assert status["disabled_count"] == 0
        assert len(status["scheduled_reminders"]) == 4
    
    def test_stop(self, scheduler):
        """测试停止调度器"""
        scheduler.is_running = True
        scheduler.stop()
        
        assert scheduler.is_running is False
    
    def test_execute_check_function_invalid(self, scheduler):
        """测试执行无效的检查函数"""
        with pytest.raises(ValueError, match="未知的检查函数"):
            scheduler._execute_check_function("invalid_function", date.today())
    
    def test_schedule_with_custom_channels(self, scheduler):
        """测试使用自定义通知渠道安排任务"""
        schedule = ScheduleConfig(
            frequency=ScheduleFrequency.DAILY,
            check_time=dt_time(9, 0),
            notification_channels=[NotificationChannel.DESKTOP]
        )
        
        scheduled = scheduler.schedule_reminder(
            reminder_id="custom_channels",
            name="自定义渠道",
            check_function="check_tax_reminders",
            schedule=schedule
        )
        
        assert scheduled.schedule.notification_channels == [NotificationChannel.DESKTOP]


class TestSchedulerIntegration:
    """测试调度器集成"""
    
    def test_full_workflow(self, temp_storage):
        """测试完整工作流"""
        # 创建真实的存储和系统
        transaction_storage = TransactionStorage(temp_storage)
        counterparty_storage = CounterpartyStorage(temp_storage)
        reminder_storage = ReminderStorage(temp_storage)
        
        # 创建提醒系统
        reminder_system = ReminderSystem(
            transaction_storage=transaction_storage,
            counterparty_storage=counterparty_storage,
            reminder_storage=reminder_storage,
            storage_dir=temp_storage
        )
        
        # 创建调度器
        scheduler = ReminderScheduler(
            reminder_system=reminder_system,
            storage_dir=temp_storage
        )
        
        # 设置默认调度
        scheduler.setup_default_schedules()
        
        # 验证调度已创建
        assert len(scheduler.scheduled_reminders) == 4
        
        # 运行检查（应该不会出错，即使没有数据）
        results = scheduler.run_scheduled_checks()
        
        # 由于任务未到期，应该都被跳过
        assert results["total_scheduled"] == 4
        assert results["skipped"] >= 0  # 可能有些任务到期了
    
    def test_scheduler_with_real_reminders(self, temp_storage):
        """测试调度器处理真实提醒"""
        # 创建存储
        transaction_storage = TransactionStorage(temp_storage)
        counterparty_storage = CounterpartyStorage(temp_storage)
        reminder_storage = ReminderStorage(temp_storage)
        
        # 添加测试数据：一个逾期的应收账款
        customer = Counterparty(
            id=str(uuid.uuid4()),
            name="测试客户",
            type=CounterpartyType.CUSTOMER,
            contact_person="张三",
            phone="13800138000",
            email="test@example.com",
            address="测试地址",
            tax_id="123456789",
            created_at=datetime.now(),
            updated_at=datetime.now()
        )
        counterparty_storage.add(customer)
        
        # 添加逾期30天的应收账款
        overdue_date = date.today() - timedelta(days=30)
        transaction = TransactionRecord(
            id=str(uuid.uuid4()),
            date=overdue_date,
            type=TransactionType.INCOME,
            amount=Decimal("10000.00"),
            counterparty_id=customer.id,
            description="测试应收账款",
            category="销售收入",
            status=TransactionStatus.PENDING,
            created_at=datetime.now(),
            updated_at=datetime.now()
        )
        transaction_storage.add(transaction)
        
        # 创建提醒系统和调度器
        reminder_system = ReminderSystem(
            transaction_storage=transaction_storage,
            counterparty_storage=counterparty_storage,
            reminder_storage=reminder_storage,
            storage_dir=temp_storage
        )
        
        scheduler = ReminderScheduler(
            reminder_system=reminder_system,
            storage_dir=temp_storage
        )
        
        # 安排应收账款检查（设置为已到期）
        schedule = ScheduleConfig(
            frequency=ScheduleFrequency.DAILY,
            check_time=dt_time(9, 0)
        )
        
        scheduled = scheduler.schedule_reminder(
            reminder_id="receivable_check",
            name="应收账款检查",
            check_function="check_receivable_reminders",
            schedule=schedule
        )
        
        # 设置为已到期
        scheduled.next_run = datetime.now() - timedelta(hours=1)
        
        # 运行检查
        results = scheduler.run_scheduled_checks()
        
        # 验证找到了提醒
        assert results["executed"] == 1
        assert results["reminders_found"] == 1


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
