"""
Example usage of ReminderScheduler

This example demonstrates how to:
1. Set up the reminder scheduler
2. Configure reminder schedules
3. Run scheduled checks manually
4. Run the scheduler as a background service
5. Customize notification channels and timing
"""

from datetime import time as dt_time, date, timedelta
from decimal import Decimal
import uuid

from small_accountant_v16.reminders.reminder_scheduler import (
    ReminderScheduler, ScheduleConfig, ScheduleFrequency
)
from small_accountant_v16.reminders.reminder_system import ReminderSystem
from small_accountant_v16.models.core_models import (
    NotificationChannel, TransactionRecord, TransactionType, TransactionStatus,
    Counterparty, CounterpartyType
)
from small_accountant_v16.storage.transaction_storage import TransactionStorage
from small_accountant_v16.storage.counterparty_storage import CounterpartyStorage
from small_accountant_v16.storage.reminder_storage import ReminderStorage
from small_accountant_v16.config.config_manager import ConfigManager


def example_1_basic_setup():
    """示例1：基本设置"""
    print("=" * 60)
    print("示例1：基本设置和默认调度")
    print("=" * 60)
    
    # 创建调度器
    scheduler = ReminderScheduler(storage_dir="data")
    
    # 设置默认调度任务（每日早上9点检查）
    scheduler.setup_default_schedules()
    
    # 查看已调度的任务
    print(f"\n已调度 {len(scheduler.scheduled_reminders)} 个任务：")
    for reminder in scheduler.get_scheduled_reminders():
        print(f"  - {reminder.name}")
        print(f"    检查函数: {reminder.check_function}")
        print(f"    下次运行: {reminder.next_run}")
        print(f"    状态: {'启用' if reminder.enabled else '禁用'}")
        print()


def example_2_custom_schedule():
    """示例2：自定义调度配置"""
    print("=" * 60)
    print("示例2：自定义调度配置")
    print("=" * 60)
    
    scheduler = ReminderScheduler(storage_dir="data")
    
    # 配置1：每日下午5点检查应收账款
    schedule_daily = ScheduleConfig(
        frequency=ScheduleFrequency.DAILY,
        check_time=dt_time(17, 0),  # 下午5点
        notification_channels=[NotificationChannel.DESKTOP, NotificationChannel.WECHAT]
    )
    
    scheduler.schedule_reminder(
        reminder_id="receivable_evening",
        name="应收账款晚间检查",
        check_function="check_receivable_reminders",
        schedule=schedule_daily
    )
    
    # 配置2：每周一早上8点检查现金流
    schedule_weekly = ScheduleConfig(
        frequency=ScheduleFrequency.WEEKLY,
        check_time=dt_time(8, 0),  # 早上8点
        notification_channels=[NotificationChannel.WECHAT]
    )
    
    scheduler.schedule_reminder(
        reminder_id="cashflow_weekly",
        name="现金流周报",
        check_function="check_cashflow_warnings",
        schedule=schedule_weekly
    )
    
    # 配置3：每月1号检查税务
    schedule_monthly = ScheduleConfig(
        frequency=ScheduleFrequency.MONTHLY,
        check_time=dt_time(9, 0),  # 早上9点
        notification_channels=[NotificationChannel.DESKTOP]
    )
    
    scheduler.schedule_reminder(
        reminder_id="tax_monthly",
        name="税务月度检查",
        check_function="check_tax_reminders",
        schedule=schedule_monthly
    )
    
    # 配置4：每30分钟检查一次（自定义间隔）
    schedule_custom = ScheduleConfig(
        frequency=ScheduleFrequency.CUSTOM,
        check_time=dt_time(0, 0),  # 对于CUSTOM频率，此字段不使用
        custom_interval_minutes=30,
        notification_channels=[NotificationChannel.DESKTOP]
    )
    
    scheduler.schedule_reminder(
        reminder_id="frequent_check",
        name="高频检查",
        check_function="check_payable_reminders",
        schedule=schedule_custom
    )
    
    # 显示所有调度
    print("\n已配置的调度任务：")
    for reminder in scheduler.get_scheduled_reminders():
        print(f"\n{reminder.name}:")
        print(f"  频率: {reminder.schedule.frequency.value}")
        print(f"  检查时间: {reminder.schedule.check_time}")
        print(f"  下次运行: {reminder.next_run}")
        print(f"  通知渠道: {[ch.value for ch in reminder.schedule.notification_channels]}")


def example_3_manual_check():
    """示例3：手动运行检查"""
    print("=" * 60)
    print("示例3：手动运行定时检查")
    print("=" * 60)
    
    # 创建测试数据
    storage_dir = "data"
    transaction_storage = TransactionStorage(storage_dir)
    counterparty_storage = CounterpartyStorage(storage_dir)
    
    # 添加测试客户
    customer = Counterparty(
        id=str(uuid.uuid4()),
        name="示例客户公司",
        type=CounterpartyType.CUSTOMER,
        contact_person="李经理",
        phone="13900139000",
        email="li@example.com",
        address="北京市朝阳区",
        tax_id="91110000123456789X",
        created_at=date.today(),
        updated_at=date.today()
    )
    counterparty_storage.add(customer)
    
    # 添加逾期应收账款
    overdue_transaction = TransactionRecord(
        id=str(uuid.uuid4()),
        date=date.today() - timedelta(days=30),  # 逾期30天
        type=TransactionType.INCOME,
        amount=Decimal("50000.00"),
        counterparty_id=customer.id,
        description="销售货款",
        category="销售收入",
        status=TransactionStatus.PENDING,
        created_at=date.today(),
        updated_at=date.today()
    )
    transaction_storage.add(overdue_transaction)
    
    # 创建调度器
    scheduler = ReminderScheduler(storage_dir=storage_dir)
    scheduler.setup_default_schedules()
    
    # 手动运行检查
    print("\n运行定时检查...")
    results = scheduler.run_scheduled_checks()
    
    # 显示结果
    print(f"\n检查结果：")
    print(f"  总任务数: {results['total_scheduled']}")
    print(f"  已执行: {results['executed']}")
    print(f"  已跳过: {results['skipped']}")
    print(f"  失败: {results['failed']}")
    print(f"  找到提醒: {results['reminders_found']}")
    print(f"  已发送: {results['reminders_sent']}")
    
    if results['details']:
        print("\n详细信息：")
        for detail in results['details']:
            print(f"  - {detail['task']}: {detail['status']}")
            if 'reminders_found' in detail:
                print(f"    找到 {detail['reminders_found']} 条提醒")


def example_4_enable_disable():
    """示例4：启用/禁用任务"""
    print("=" * 60)
    print("示例4：启用和禁用调度任务")
    print("=" * 60)
    
    scheduler = ReminderScheduler(storage_dir="data")
    scheduler.setup_default_schedules()
    
    # 查看初始状态
    status = scheduler.get_status()
    print(f"\n初始状态：")
    print(f"  总任务数: {status['total_scheduled']}")
    print(f"  启用: {status['enabled_count']}")
    print(f"  禁用: {status['disabled_count']}")
    
    # 禁用税务提醒
    print("\n禁用税务提醒...")
    scheduler.disable_reminder("tax_reminders")
    
    # 禁用现金流预警
    print("禁用现金流预警...")
    scheduler.disable_reminder("cashflow_warnings")
    
    # 查看更新后的状态
    status = scheduler.get_status()
    print(f"\n更新后状态：")
    print(f"  总任务数: {status['total_scheduled']}")
    print(f"  启用: {status['enabled_count']}")
    print(f"  禁用: {status['disabled_count']}")
    
    # 重新启用税务提醒
    print("\n重新启用税务提醒...")
    scheduler.enable_reminder("tax_reminders")
    
    # 查看最终状态
    status = scheduler.get_status()
    print(f"\n最终状态：")
    print(f"  总任务数: {status['total_scheduled']}")
    print(f"  启用: {status['enabled_count']}")
    print(f"  禁用: {status['disabled_count']}")


def example_5_configuration():
    """示例5：配置管理"""
    print("=" * 60)
    print("示例5：配置管理")
    print("=" * 60)
    
    # 创建配置管理器
    config_manager = ConfigManager("config.json")
    
    # 配置企业微信webhook
    print("\n配置企业微信通知...")
    config_manager.update_wechat_config(
        webhook_url="https://qyapi.weixin.qq.com/cgi-bin/webhook/send?key=YOUR_KEY",
        enabled=True
    )
    
    # 配置提醒参数
    print("配置提醒参数...")
    config_manager.update_reminder_config(
        tax_reminder_days=[7, 3, 1, 0],
        payable_reminder_days=3,
        receivable_overdue_days=[30, 60, 90],
        cashflow_warning_days=7,
        enable_desktop_notification=True,
        enable_wechat_notification=True
    )
    
    # 创建调度器（会自动使用配置）
    scheduler = ReminderScheduler(
        config_manager=config_manager,
        storage_dir="data"
    )
    
    # 设置默认调度（会根据配置启用相应的通知渠道）
    scheduler.setup_default_schedules()
    
    print("\n调度器已配置完成！")
    print("通知渠道配置：")
    config = config_manager.get_config()
    print(f"  桌面通知: {'启用' if config.reminder.enable_desktop_notification else '禁用'}")
    print(f"  企业微信: {'启用' if config.reminder.enable_wechat_notification else '禁用'}")


def example_6_background_service():
    """示例6：作为后台服务运行（演示代码）"""
    print("=" * 60)
    print("示例6：后台服务模式（演示）")
    print("=" * 60)
    
    print("\n后台服务运行示例代码：")
    print("""
# 创建调度器
scheduler = ReminderScheduler(storage_dir="data")
scheduler.setup_default_schedules()

# 持续运行（每60秒检查一次）
# 注意：这会阻塞当前线程
try:
    print("调度器启动，按 Ctrl+C 停止...")
    scheduler.run_continuous(check_interval_seconds=60)
except KeyboardInterrupt:
    print("\\n调度器已停止")
    scheduler.stop()
""")
    
    print("\n或者使用 cron 定时任务：")
    print("""
# crontab 配置示例（每小时运行一次）
0 * * * * cd /path/to/project && python -c "from small_accountant_v16.reminders.reminder_scheduler import ReminderScheduler; s = ReminderScheduler(); s.setup_default_schedules(); s.run_scheduled_checks()"

# 或者每天早上9点运行
0 9 * * * cd /path/to/project && python run_scheduler.py
""")


def example_7_status_monitoring():
    """示例7：状态监控"""
    print("=" * 60)
    print("示例7：状态监控")
    print("=" * 60)
    
    scheduler = ReminderScheduler(storage_dir="data")
    scheduler.setup_default_schedules()
    
    # 获取详细状态
    status = scheduler.get_status()
    
    print("\n调度器状态：")
    print(f"  运行状态: {'运行中' if status['is_running'] else '已停止'}")
    print(f"  总任务数: {status['total_scheduled']}")
    print(f"  启用任务: {status['enabled_count']}")
    print(f"  禁用任务: {status['disabled_count']}")
    
    print("\n任务详情：")
    for reminder_data in status['scheduled_reminders']:
        print(f"\n  {reminder_data['name']}:")
        print(f"    ID: {reminder_data['id']}")
        print(f"    检查函数: {reminder_data['check_function']}")
        print(f"    频率: {reminder_data['schedule']['frequency']}")
        print(f"    检查时间: {reminder_data['schedule']['check_time']}")
        print(f"    状态: {'启用' if reminder_data['enabled'] else '禁用'}")
        print(f"    上次运行: {reminder_data['last_run'] or '从未运行'}")
        print(f"    下次运行: {reminder_data['next_run']}")


def main():
    """运行所有示例"""
    examples = [
        ("基本设置", example_1_basic_setup),
        ("自定义调度", example_2_custom_schedule),
        ("手动检查", example_3_manual_check),
        ("启用/禁用", example_4_enable_disable),
        ("配置管理", example_5_configuration),
        ("后台服务", example_6_background_service),
        ("状态监控", example_7_status_monitoring),
    ]
    
    print("\n" + "=" * 60)
    print("ReminderScheduler 使用示例")
    print("=" * 60)
    
    for i, (name, func) in enumerate(examples, 1):
        print(f"\n{i}. {name}")
    
    print("\n请选择要运行的示例（1-7），或输入 'all' 运行所有示例：")
    choice = input("> ").strip().lower()
    
    if choice == "all":
        for name, func in examples:
            try:
                func()
                print("\n")
            except Exception as e:
                print(f"示例运行出错: {e}")
    elif choice.isdigit() and 1 <= int(choice) <= len(examples):
        try:
            examples[int(choice) - 1][1]()
        except Exception as e:
            print(f"示例运行出错: {e}")
    else:
        print("无效的选择")


if __name__ == "__main__":
    main()
