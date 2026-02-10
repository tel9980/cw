"""
Example usage of ReminderSystem

Demonstrates all reminder types:
- Tax reminders (VAT, income tax)
- Payable reminders
- Receivable reminders (with collection letters)
- Cash flow warnings
- Sending reminders via multiple channels
"""

import uuid
from datetime import date, datetime, timedelta
from decimal import Decimal
from pathlib import Path

from small_accountant_v16.models.core_models import (
    TransactionRecord, TransactionType, TransactionStatus,
    Counterparty, CounterpartyType,
    NotificationChannel
)
from small_accountant_v16.storage.transaction_storage import TransactionStorage
from small_accountant_v16.storage.counterparty_storage import CounterpartyStorage
from small_accountant_v16.storage.reminder_storage import ReminderStorage
from small_accountant_v16.reminders.reminder_system import ReminderSystem
from small_accountant_v16.reminders.notification_service import NotificationService
from small_accountant_v16.reminders.collection_letter_generator import CollectionLetterGenerator


def setup_demo_data(
    transaction_storage: TransactionStorage,
    counterparty_storage: CounterpartyStorage
):
    """设置演示数据"""
    print("=" * 60)
    print("设置演示数据...")
    print("=" * 60)
    
    # 创建客户
    customer1 = Counterparty(
        id="CUST001",
        name="ABC贸易公司",
        type=CounterpartyType.CUSTOMER,
        contact_person="张经理",
        phone="13800138001",
        email="zhang@abc.com",
        address="北京市朝阳区建国路88号",
        tax_id="91110000123456789A",
        created_at=datetime.now(),
        updated_at=datetime.now()
    )
    counterparty_storage.add(customer1)
    print(f"✓ 创建客户: {customer1.name}")
    
    customer2 = Counterparty(
        id="CUST002",
        name="XYZ科技有限公司",
        type=CounterpartyType.CUSTOMER,
        contact_person="李总",
        phone="13800138002",
        email="li@xyz.com",
        address="上海市浦东新区世纪大道100号",
        tax_id="91310000987654321B",
        created_at=datetime.now(),
        updated_at=datetime.now()
    )
    counterparty_storage.add(customer2)
    print(f"✓ 创建客户: {customer2.name}")
    
    # 创建供应商
    supplier1 = Counterparty(
        id="SUPP001",
        name="优质原材料供应商",
        type=CounterpartyType.SUPPLIER,
        contact_person="王经理",
        phone="13900139001",
        email="wang@supplier.com",
        address="广州市天河区天河路200号",
        tax_id="91440000111222333C",
        created_at=datetime.now(),
        updated_at=datetime.now()
    )
    counterparty_storage.add(supplier1)
    print(f"✓ 创建供应商: {supplier1.name}")
    
    supplier2 = Counterparty(
        id="SUPP002",
        name="快速物流公司",
        type=CounterpartyType.SUPPLIER,
        contact_person="赵主管",
        phone="13900139002",
        email="zhao@logistics.com",
        address="深圳市南山区科技园南路300号",
        tax_id="91440300444555666D",
        created_at=datetime.now(),
        updated_at=datetime.now()
    )
    counterparty_storage.add(supplier2)
    print(f"✓ 创建供应商: {supplier2.name}")
    
    today = date.today()
    
    # 创建已完成的收入（用于计算当前余额）
    for i in range(5):
        transaction = TransactionRecord(
            id=str(uuid.uuid4()),
            date=today - timedelta(days=30 + i * 5),
            type=TransactionType.INCOME,
            amount=Decimal(f"{50000 + i * 10000}.00"),
            counterparty_id=customer1.id,
            description=f"销售产品 - 已收款 {i+1}",
            category="销售收入",
            status=TransactionStatus.COMPLETED,
            created_at=datetime.now(),
            updated_at=datetime.now()
        )
        transaction_storage.add(transaction)
    print(f"✓ 创建5笔已完成的收入交易")
    
    # 创建已完成的支出（用于计算当前余额）
    for i in range(3):
        transaction = TransactionRecord(
            id=str(uuid.uuid4()),
            date=today - timedelta(days=25 + i * 5),
            type=TransactionType.EXPENSE,
            amount=Decimal(f"{30000 + i * 5000}.00"),
            counterparty_id=supplier1.id,
            description=f"采购原材料 - 已付款 {i+1}",
            category="采购成本",
            status=TransactionStatus.COMPLETED,
            created_at=datetime.now(),
            updated_at=datetime.now()
        )
        transaction_storage.add(transaction)
    print(f"✓ 创建3笔已完成的支出交易")
    
    # 创建应付账款（即将到期）
    payable1 = TransactionRecord(
        id=str(uuid.uuid4()),
        date=today + timedelta(days=3),
        type=TransactionType.EXPENSE,
        amount=Decimal("25000.00"),
        counterparty_id=supplier1.id,
        description="采购原材料 - 待付款",
        category="采购成本",
        status=TransactionStatus.PENDING,
        created_at=datetime.now(),
        updated_at=datetime.now()
    )
    transaction_storage.add(payable1)
    print(f"✓ 创建应付账款: {payable1.amount} 元（3天后到期）")
    
    payable2 = TransactionRecord(
        id=str(uuid.uuid4()),
        date=today + timedelta(days=1),
        type=TransactionType.EXPENSE,
        amount=Decimal("8000.00"),
        counterparty_id=supplier2.id,
        description="物流费用 - 待付款",
        category="运输费用",
        status=TransactionStatus.PENDING,
        created_at=datetime.now(),
        updated_at=datetime.now()
    )
    transaction_storage.add(payable2)
    print(f"✓ 创建应付账款: {payable2.amount} 元（1天后到期）")
    
    # 创建应收账款（逾期）
    receivable1 = TransactionRecord(
        id=str(uuid.uuid4()),
        date=today - timedelta(days=30),
        type=TransactionType.INCOME,
        amount=Decimal("45000.00"),
        counterparty_id=customer1.id,
        description="销售产品 - 待收款",
        category="销售收入",
        status=TransactionStatus.PENDING,
        created_at=datetime.now(),
        updated_at=datetime.now()
    )
    transaction_storage.add(receivable1)
    print(f"✓ 创建应收账款: {receivable1.amount} 元（逾期30天）")
    
    receivable2 = TransactionRecord(
        id=str(uuid.uuid4()),
        date=today - timedelta(days=60),
        type=TransactionType.INCOME,
        amount=Decimal("32000.00"),
        counterparty_id=customer2.id,
        description="提供服务 - 待收款",
        category="服务收入",
        status=TransactionStatus.PENDING,
        created_at=datetime.now(),
        updated_at=datetime.now()
    )
    transaction_storage.add(receivable2)
    print(f"✓ 创建应收账款: {receivable2.amount} 元（逾期60天）")
    
    receivable3 = TransactionRecord(
        id=str(uuid.uuid4()),
        date=today - timedelta(days=90),
        type=TransactionType.INCOME,
        amount=Decimal("28000.00"),
        counterparty_id=customer1.id,
        description="销售产品 - 待收款",
        category="销售收入",
        status=TransactionStatus.PENDING,
        created_at=datetime.now(),
        updated_at=datetime.now()
    )
    transaction_storage.add(receivable3)
    print(f"✓ 创建应收账款: {receivable3.amount} 元（逾期90天）")
    
    # 创建未来的大额支出（用于现金流预警）
    future_expense = TransactionRecord(
        id=str(uuid.uuid4()),
        date=today + timedelta(days=5),
        type=TransactionType.EXPENSE,
        amount=Decimal("150000.00"),
        counterparty_id=supplier1.id,
        description="大额采购 - 待付款",
        category="采购成本",
        status=TransactionStatus.PENDING,
        created_at=datetime.now(),
        updated_at=datetime.now()
    )
    transaction_storage.add(future_expense)
    print(f"✓ 创建未来大额支出: {future_expense.amount} 元（5天后）")
    
    print("\n演示数据设置完成！\n")


def demo_tax_reminders(reminder_system: ReminderSystem):
    """演示税务提醒"""
    print("=" * 60)
    print("1. 税务提醒检查")
    print("=" * 60)
    
    # 检查税务提醒
    tax_reminders = reminder_system.check_tax_reminders()
    
    if tax_reminders:
        print(f"\n找到 {len(tax_reminders)} 条税务提醒：\n")
        for reminder in tax_reminders:
            print(f"【{reminder.priority.value.upper()}】{reminder.title}")
            print(f"  到期日期: {reminder.due_date.strftime('%Y年%m月%d日')}")
            print(f"  说明: {reminder.description}")
            print()
    else:
        print("\n当前没有需要发送的税务提醒。")
        print("（税务提醒在截止日期前7天、3天、1天和当天发送）\n")


def demo_payable_reminders(reminder_system: ReminderSystem):
    """演示应付账款提醒"""
    print("=" * 60)
    print("2. 应付账款提醒检查")
    print("=" * 60)
    
    # 检查应付账款提醒
    payable_reminders = reminder_system.check_payable_reminders()
    
    if payable_reminders:
        print(f"\n找到 {len(payable_reminders)} 条应付账款提醒：\n")
        for reminder in payable_reminders:
            print(f"【{reminder.priority.value.upper()}】{reminder.title}")
            print(f"  到期日期: {reminder.due_date.strftime('%Y年%m月%d日')}")
            print(f"  详情:")
            for line in reminder.description.split('\n'):
                if line.strip():
                    print(f"    {line}")
            print()
    else:
        print("\n当前没有即将到期的应付账款。\n")


def demo_receivable_reminders(reminder_system: ReminderSystem):
    """演示应收账款提醒"""
    print("=" * 60)
    print("3. 应收账款提醒检查")
    print("=" * 60)
    
    # 检查应收账款提醒
    receivable_reminders = reminder_system.check_receivable_reminders()
    
    if receivable_reminders:
        print(f"\n找到 {len(receivable_reminders)} 条应收账款提醒：\n")
        for reminder in receivable_reminders:
            print(f"【{reminder.priority.value.upper()}】{reminder.title}")
            print(f"  原到期日期: {reminder.due_date.strftime('%Y年%m月%d日')}")
            print(f"  详情:")
            for line in reminder.description.split('\n'):
                if line.strip():
                    print(f"    {line}")
            print()
    else:
        print("\n当前没有逾期的应收账款。\n")


def demo_cashflow_warnings(reminder_system: ReminderSystem):
    """演示现金流预警"""
    print("=" * 60)
    print("4. 现金流预警检查")
    print("=" * 60)
    
    # 检查现金流预警
    cashflow_warnings = reminder_system.check_cashflow_warnings()
    
    if cashflow_warnings:
        print(f"\n⚠️  发现现金流预警！\n")
        for warning in cashflow_warnings:
            print(f"【{warning.priority.value.upper()}】{warning.title}")
            print(f"  预警日期: {warning.due_date.strftime('%Y年%m月%d日')}")
            print(f"  详情:")
            for line in warning.description.split('\n'):
                if line.strip():
                    print(f"    {line}")
            print()
    else:
        print("\n✓ 现金流正常，未来7天资金充足。\n")


def demo_run_all_checks(reminder_system: ReminderSystem):
    """演示运行所有检查"""
    print("=" * 60)
    print("5. 运行所有提醒检查")
    print("=" * 60)
    
    # 运行所有检查
    all_reminders = reminder_system.run_all_checks()
    
    print("\n检查结果汇总：")
    print(f"  税务提醒: {len(all_reminders['tax'])} 条")
    print(f"  应付账款提醒: {len(all_reminders['payable'])} 条")
    print(f"  应收账款提醒: {len(all_reminders['receivable'])} 条")
    print(f"  现金流预警: {len(all_reminders['cashflow'])} 条")
    
    total = sum(len(reminders) for reminders in all_reminders.values())
    print(f"\n总计: {total} 条提醒\n")


def demo_send_reminders(reminder_system: ReminderSystem):
    """演示发送提醒"""
    print("=" * 60)
    print("6. 发送提醒")
    print("=" * 60)
    
    # 获取所有待发送的提醒
    pending_reminders = reminder_system.reminder_storage.get_pending()
    
    if not pending_reminders:
        print("\n没有待发送的提醒。\n")
        return
    
    print(f"\n找到 {len(pending_reminders)} 条待发送的提醒。")
    print("\n注意：")
    print("  - 桌面通知需要安装 plyer 库")
    print("  - 企业微信通知需要配置 webhook URL")
    print("\n开始发送提醒...\n")
    
    # 批量发送所有待发送的提醒
    stats = reminder_system.send_all_pending_reminders()
    
    print(f"\n发送完成：")
    print(f"  成功: {stats['sent']} 条")
    print(f"  失败: {stats['failed']} 条\n")


def demo_reminder_storage(reminder_storage: ReminderStorage):
    """演示提醒存储查询"""
    print("=" * 60)
    print("7. 提醒存储查询")
    print("=" * 60)
    
    # 获取所有提醒
    all_reminders = reminder_storage.get_all()
    print(f"\n总提醒数: {len(all_reminders)}")
    
    # 按类型统计
    from small_accountant_v16.models.core_models import ReminderType
    print("\n按类型统计:")
    for reminder_type in ReminderType:
        count = len(reminder_storage.get_by_type(reminder_type))
        print(f"  {reminder_type.value}: {count} 条")
    
    # 按状态统计
    from small_accountant_v16.models.core_models import ReminderStatus
    print("\n按状态统计:")
    for status in ReminderStatus:
        count = len(reminder_storage.get_by_status(status))
        print(f"  {status.value}: {count} 条")
    
    # 获取即将到期的提醒
    upcoming = reminder_storage.get_upcoming_reminders(days=7)
    print(f"\n未来7天内到期: {len(upcoming)} 条")
    
    # 获取逾期提醒
    overdue = reminder_storage.get_overdue_reminders()
    print(f"已逾期: {len(overdue)} 条\n")


def main():
    """主函数"""
    print("\n" + "=" * 60)
    print("智能提醒系统 - 完整演示")
    print("=" * 60)
    print()
    
    # 初始化存储
    storage_dir = "demo_data"
    transaction_storage = TransactionStorage(storage_dir)
    counterparty_storage = CounterpartyStorage(storage_dir)
    reminder_storage = ReminderStorage(storage_dir)
    
    # 初始化服务
    notification_service = NotificationService()
    
    # 初始化催款函生成器（可选）
    try:
        collection_letter_generator = CollectionLetterGenerator(
            company_name="示例科技有限公司",
            company_address="北京市海淀区中关村大街1号",
            company_phone="010-88888888",
            company_contact="财务部 - 陈会计",
            output_dir=f"{storage_dir}/collection_letters"
        )
        print("✓ 催款函生成器已启用")
    except ImportError:
        collection_letter_generator = None
        print("⚠️  python-docx 未安装，催款函生成功能不可用")
        print("   安装方法: pip install python-docx\n")
    
    # 初始化提醒系统
    reminder_system = ReminderSystem(
        transaction_storage=transaction_storage,
        counterparty_storage=counterparty_storage,
        reminder_storage=reminder_storage,
        notification_service=notification_service,
        collection_letter_generator=collection_letter_generator,
        storage_dir=storage_dir,
        wechat_webhook_url=None  # 如需使用企业微信通知，请配置webhook URL
    )
    
    print("✓ 提醒系统初始化完成\n")
    
    # 设置演示数据
    setup_demo_data(transaction_storage, counterparty_storage)
    
    # 演示各种提醒功能
    demo_tax_reminders(reminder_system)
    demo_payable_reminders(reminder_system)
    demo_receivable_reminders(reminder_system)
    demo_cashflow_warnings(reminder_system)
    demo_run_all_checks(reminder_system)
    demo_send_reminders(reminder_system)
    demo_reminder_storage(reminder_storage)
    
    print("=" * 60)
    print("演示完成！")
    print("=" * 60)
    print()
    print("提示：")
    print("  - 所有数据已保存到 'demo_data' 目录")
    print("  - 催款函已保存到 'demo_data/collection_letters' 目录")
    print("  - 可以查看生成的提醒记录和催款函文档")
    print()


if __name__ == "__main__":
    main()
