"""
Reminder System Module

Core reminder system that checks for various types of reminders:
- Tax filing reminders (VAT, income tax)
- Accounts payable reminders
- Accounts receivable reminders (with collection letters)
- Cash flow warnings

Integrates with NotificationService and CollectionLetterGenerator.
"""

import logging
import uuid
from datetime import date, datetime, timedelta
from decimal import Decimal
from typing import List, Optional, Dict, Any
from pathlib import Path

from ..models.core_models import (
    Reminder, ReminderType, ReminderStatus, Priority,
    NotificationChannel, TransactionType, TransactionStatus,
    CounterpartyType
)
from ..storage.transaction_storage import TransactionStorage
from ..storage.counterparty_storage import CounterpartyStorage
from ..storage.reminder_storage import ReminderStorage
from .notification_service import NotificationService
from .collection_letter_generator import CollectionLetterGenerator, LetterTemplate


# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class TaxDeadline:
    """税务申报截止日期配置"""
    
    # 增值税申报截止日期（每月15日）
    VAT_DAY = 15
    
    # 所得税申报截止日期（季度后次月15日）
    INCOME_TAX_QUARTERS = {
        1: (4, 15),  # Q1: 4月15日
        2: (7, 15),  # Q2: 7月15日
        3: (10, 15), # Q3: 10月15日
        4: (1, 15),  # Q4: 次年1月15日
    }
    
    # 年度所得税申报截止日期（次年5月31日）
    ANNUAL_INCOME_TAX = (5, 31)


class ReminderSystem:
    """
    智能提醒系统
    
    功能：
    - 检查税务申报提醒（增值税、所得税）
    - 检查应付账款提醒
    - 检查应收账款提醒（含催款函生成）
    - 检查现金流预警
    - 发送多渠道通知
    """
    
    # 提醒时间配置（提前N天）
    TAX_REMINDER_DAYS = [7, 3, 1, 0]  # 7天、3天、1天、当天
    PAYABLE_REMINDER_DAYS = 3  # 应付账款提前3天提醒
    RECEIVABLE_OVERDUE_DAYS = [30, 60, 90]  # 应收账款逾期30、60、90天提醒
    CASHFLOW_WARNING_DAYS = 7  # 现金流预警提前7天
    
    def __init__(
        self,
        transaction_storage: Optional[TransactionStorage] = None,
        counterparty_storage: Optional[CounterpartyStorage] = None,
        reminder_storage: Optional[ReminderStorage] = None,
        notification_service: Optional[NotificationService] = None,
        collection_letter_generator: Optional[CollectionLetterGenerator] = None,
        storage_dir: str = "data",
        wechat_webhook_url: Optional[str] = None
    ):
        """
        初始化提醒系统
        
        Args:
            transaction_storage: 交易记录存储（可选）
            counterparty_storage: 往来单位存储（可选）
            reminder_storage: 提醒事项存储（可选）
            notification_service: 通知服务（可选）
            collection_letter_generator: 催款函生成器（可选）
            storage_dir: 数据存储目录
            wechat_webhook_url: 企业微信webhook地址
        """
        # Initialize storage
        self.transaction_storage = transaction_storage or TransactionStorage(storage_dir)
        self.counterparty_storage = counterparty_storage or CounterpartyStorage(storage_dir)
        self.reminder_storage = reminder_storage or ReminderStorage(storage_dir)
        
        # Initialize services
        self.notification_service = notification_service or NotificationService()
        self.collection_letter_generator = collection_letter_generator
        
        # Configuration
        self.wechat_webhook_url = wechat_webhook_url
        
        logger.info("提醒系统初始化完成")
    
    def check_tax_reminders(self, check_date: Optional[date] = None) -> List[Reminder]:
        """
        检查税务申报提醒
        
        检查增值税和所得税申报截止日期，生成提醒事项。
        
        Args:
            check_date: 检查日期（默认今天）
        
        Returns:
            List[Reminder]: 需要发送的税务提醒列表
        """
        if check_date is None:
            check_date = date.today()
        
        logger.info(f"检查税务提醒: {check_date}")
        reminders = []
        
        # 检查增值税申报提醒
        vat_reminders = self._check_vat_reminders(check_date)
        reminders.extend(vat_reminders)
        
        # 检查所得税申报提醒
        income_tax_reminders = self._check_income_tax_reminders(check_date)
        reminders.extend(income_tax_reminders)
        
        logger.info(f"找到 {len(reminders)} 条税务提醒")
        return reminders
    
    def _check_vat_reminders(self, check_date: date) -> List[Reminder]:
        """检查增值税申报提醒"""
        reminders = []
        
        # 计算本月增值税申报截止日期
        vat_deadline = date(check_date.year, check_date.month, TaxDeadline.VAT_DAY)
        
        # 如果已经过了本月截止日期，检查下月
        if check_date > vat_deadline:
            if check_date.month == 12:
                vat_deadline = date(check_date.year + 1, 1, TaxDeadline.VAT_DAY)
            else:
                vat_deadline = date(check_date.year, check_date.month + 1, TaxDeadline.VAT_DAY)
        
        # 检查是否需要提醒
        days_until_deadline = (vat_deadline - check_date).days
        
        if days_until_deadline in self.TAX_REMINDER_DAYS:
            reminder = self._create_tax_reminder(
                title=f"增值税申报提醒（{days_until_deadline}天后到期）",
                description=f"增值税申报截止日期为 {vat_deadline.strftime('%Y年%m月%d日')}，请及时完成申报。",
                due_date=vat_deadline,
                priority=Priority.HIGH if days_until_deadline <= 1 else Priority.MEDIUM
            )
            reminders.append(reminder)
        
        return reminders
    
    def _check_income_tax_reminders(self, check_date: date) -> List[Reminder]:
        """检查所得税申报提醒"""
        reminders = []
        
        # 计算当前季度
        current_quarter = (check_date.month - 1) // 3 + 1
        
        # 计算季度所得税申报截止日期
        deadline_month, deadline_day = TaxDeadline.INCOME_TAX_QUARTERS[current_quarter]
        
        # 处理跨年情况（Q4的截止日期在次年1月）
        if current_quarter == 4 and check_date.month == 12:
            deadline_year = check_date.year + 1
        else:
            deadline_year = check_date.year
        
        income_tax_deadline = date(deadline_year, deadline_month, deadline_day)
        
        # 如果已经过了本季度截止日期，检查下季度
        if check_date > income_tax_deadline:
            next_quarter = (current_quarter % 4) + 1
            deadline_month, deadline_day = TaxDeadline.INCOME_TAX_QUARTERS[next_quarter]
            
            if next_quarter == 1:
                deadline_year = check_date.year + 1
            else:
                deadline_year = check_date.year
            
            income_tax_deadline = date(deadline_year, deadline_month, deadline_day)
        
        # 检查是否需要提醒
        days_until_deadline = (income_tax_deadline - check_date).days
        
        if days_until_deadline in self.TAX_REMINDER_DAYS:
            reminder = self._create_tax_reminder(
                title=f"所得税申报提醒（{days_until_deadline}天后到期）",
                description=f"季度所得税申报截止日期为 {income_tax_deadline.strftime('%Y年%m月%d日')}，请及时完成申报。",
                due_date=income_tax_deadline,
                priority=Priority.HIGH if days_until_deadline <= 1 else Priority.MEDIUM
            )
            reminders.append(reminder)
        
        return reminders
    
    def _create_tax_reminder(
        self,
        title: str,
        description: str,
        due_date: date,
        priority: Priority
    ) -> Reminder:
        """创建税务提醒"""
        reminder = Reminder(
            id=str(uuid.uuid4()),
            type=ReminderType.TAX,
            title=title,
            description=description,
            due_date=due_date,
            priority=priority,
            status=ReminderStatus.PENDING,
            notification_channels=[NotificationChannel.DESKTOP, NotificationChannel.WECHAT],
            created_at=datetime.now()
        )
        
        # 保存到存储
        self.reminder_storage.add(reminder)
        
        return reminder
    
    def check_payable_reminders(self, check_date: Optional[date] = None) -> List[Reminder]:
        """
        检查应付账款提醒
        
        检查即将到期的应付账款，生成提醒事项。
        
        Args:
            check_date: 检查日期（默认今天）
        
        Returns:
            List[Reminder]: 需要发送的应付账款提醒列表
        """
        if check_date is None:
            check_date = date.today()
        
        logger.info(f"检查应付账款提醒: {check_date}")
        reminders = []
        
        # 获取所有待处理的支出交易
        all_transactions = self.transaction_storage.get_by_type(TransactionType.EXPENSE)
        pending_payables = [t for t in all_transactions if t.status == TransactionStatus.PENDING]
        
        # 检查即将到期的应付账款
        reminder_date = check_date + timedelta(days=self.PAYABLE_REMINDER_DAYS)
        
        for transaction in pending_payables:
            # 假设交易日期就是到期日期（实际应用中可能需要单独的到期日期字段）
            if transaction.date <= reminder_date and transaction.date >= check_date:
                # 获取供应商信息
                supplier = self.counterparty_storage.get(transaction.counterparty_id)
                supplier_name = supplier.name if supplier else "未知供应商"
                
                days_until_due = (transaction.date - check_date).days
                
                reminder = Reminder(
                    id=str(uuid.uuid4()),
                    type=ReminderType.PAYABLE,
                    title=f"应付账款提醒：{supplier_name}（{days_until_due}天后到期）",
                    description=(
                        f"供应商：{supplier_name}\n"
                        f"金额：{transaction.amount:,.2f} 元\n"
                        f"到期日期：{transaction.date.strftime('%Y年%m月%d日')}\n"
                        f"说明：{transaction.description}"
                    ),
                    due_date=transaction.date,
                    priority=Priority.HIGH if days_until_due <= 1 else Priority.MEDIUM,
                    status=ReminderStatus.PENDING,
                    notification_channels=[NotificationChannel.DESKTOP, NotificationChannel.WECHAT],
                    created_at=datetime.now()
                )
                
                # 保存到存储
                self.reminder_storage.add(reminder)
                reminders.append(reminder)
        
        logger.info(f"找到 {len(reminders)} 条应付账款提醒")
        return reminders
    
    def check_receivable_reminders(self, check_date: Optional[date] = None) -> List[Reminder]:
        """
        检查应收账款提醒
        
        检查逾期的应收账款，生成提醒事项并自动生成催款函。
        
        Args:
            check_date: 检查日期（默认今天）
        
        Returns:
            List[Reminder]: 需要发送的应收账款提醒列表
        """
        if check_date is None:
            check_date = date.today()
        
        logger.info(f"检查应收账款提醒: {check_date}")
        reminders = []
        
        # 获取所有待处理的收入交易
        all_transactions = self.transaction_storage.get_by_type(TransactionType.INCOME)
        pending_receivables = [t for t in all_transactions if t.status == TransactionStatus.PENDING]
        
        # 检查逾期的应收账款
        for transaction in pending_receivables:
            overdue_days = (check_date - transaction.date).days
            
            # 只在特定逾期天数时提醒（30、60、90天）
            if overdue_days in self.RECEIVABLE_OVERDUE_DAYS:
                # 获取客户信息
                customer = self.counterparty_storage.get(transaction.counterparty_id)
                customer_name = customer.name if customer else "未知客户"
                
                # 生成催款函（如果配置了生成器）
                collection_letter_path = None
                if self.collection_letter_generator and customer:
                    try:
                        collection_letter_path = self.collection_letter_generator.generate_collection_letter(
                            customer=customer,
                            overdue_days=overdue_days,
                            amount=transaction.amount,
                            due_date=transaction.date
                        )
                        logger.info(f"已生成催款函: {collection_letter_path}")
                    except Exception as e:
                        logger.error(f"生成催款函失败: {e}")
                
                # 创建提醒
                description = (
                    f"客户：{customer_name}\n"
                    f"金额：{transaction.amount:,.2f} 元\n"
                    f"原到期日期：{transaction.date.strftime('%Y年%m月%d日')}\n"
                    f"逾期天数：{overdue_days} 天\n"
                    f"说明：{transaction.description}"
                )
                
                if collection_letter_path:
                    description += f"\n\n催款函已生成：{collection_letter_path}"
                
                reminder = Reminder(
                    id=str(uuid.uuid4()),
                    type=ReminderType.RECEIVABLE,
                    title=f"应收账款逾期提醒：{customer_name}（逾期{overdue_days}天）",
                    description=description,
                    due_date=transaction.date,
                    priority=Priority.HIGH,
                    status=ReminderStatus.PENDING,
                    notification_channels=[NotificationChannel.DESKTOP, NotificationChannel.WECHAT],
                    created_at=datetime.now()
                )
                
                # 保存到存储
                self.reminder_storage.add(reminder)
                reminders.append(reminder)
        
        logger.info(f"找到 {len(reminders)} 条应收账款提醒")
        return reminders
    
    def check_cashflow_warnings(self, check_date: Optional[date] = None) -> List[Reminder]:
        """
        检查现金流预警
        
        预测未来7天的现金流，如果预计不足则发出警告。
        
        Args:
            check_date: 检查日期（默认今天）
        
        Returns:
            List[Reminder]: 现金流预警提醒列表
        """
        if check_date is None:
            check_date = date.today()
        
        logger.info(f"检查现金流预警: {check_date}")
        reminders = []
        
        # 计算未来7天的日期范围
        future_date = check_date + timedelta(days=self.CASHFLOW_WARNING_DAYS)
        
        # 获取未来7天内的预期收入和支出
        all_transactions = self.transaction_storage.get_by_date_range(check_date, future_date)
        
        # 计算预期收入（已完成的收入）
        completed_income = sum(
            t.amount for t in all_transactions
            if t.type == TransactionType.INCOME and t.status == TransactionStatus.COMPLETED
        )
        
        # 计算预期支出（待处理的支出）
        pending_expenses = sum(
            t.amount for t in all_transactions
            if t.type == TransactionType.EXPENSE and t.status == TransactionStatus.PENDING
        )
        
        # 计算当前余额（简化版本：所有已完成收入 - 所有已完成支出）
        all_completed = self.transaction_storage.get_by_status(TransactionStatus.COMPLETED)
        current_balance = sum(
            t.amount if t.type == TransactionType.INCOME else -t.amount
            for t in all_completed
        )
        
        # 预测未来余额
        predicted_balance = current_balance + completed_income - pending_expenses
        
        # 如果预测余额不足，发出警告
        if predicted_balance < Decimal('0'):
            reminder = Reminder(
                id=str(uuid.uuid4()),
                type=ReminderType.CASHFLOW,
                title=f"现金流预警：未来{self.CASHFLOW_WARNING_DAYS}天资金可能不足",
                description=(
                    f"当前余额：{current_balance:,.2f} 元\n"
                    f"未来{self.CASHFLOW_WARNING_DAYS}天预期收入：{completed_income:,.2f} 元\n"
                    f"未来{self.CASHFLOW_WARNING_DAYS}天预期支出：{pending_expenses:,.2f} 元\n"
                    f"预测余额：{predicted_balance:,.2f} 元\n\n"
                    f"建议：请及时安排资金，避免资金链断裂。"
                ),
                due_date=future_date,
                priority=Priority.HIGH,
                status=ReminderStatus.PENDING,
                notification_channels=[NotificationChannel.DESKTOP, NotificationChannel.WECHAT],
                created_at=datetime.now()
            )
            
            # 保存到存储
            self.reminder_storage.add(reminder)
            reminders.append(reminder)
            
            logger.warning(f"现金流预警：预测余额 {predicted_balance:,.2f} 元")
        else:
            logger.info(f"现金流正常：预测余额 {predicted_balance:,.2f} 元")
        
        return reminders
    
    def send_reminder(
        self,
        reminder: Reminder,
        channels: Optional[List[NotificationChannel]] = None
    ) -> Dict[str, bool]:
        """
        发送提醒
        
        通过配置的通知渠道发送提醒。
        
        Args:
            reminder: 提醒事项
            channels: 通知渠道列表（可选，默认使用提醒中配置的渠道）
        
        Returns:
            Dict[str, bool]: 各渠道发送结果
        """
        if channels is None:
            channels = reminder.notification_channels
        
        logger.info(f"发送提醒: {reminder.title}")
        
        # 准备通知内容
        title = reminder.title
        message = reminder.description
        
        # 转换通知渠道为字符串列表
        channel_names = [ch.value for ch in channels]
        
        # 发送通知
        results = self.notification_service.send_notification(
            title=title,
            message=message,
            channels=channel_names,
            wechat_webhook_url=self.wechat_webhook_url
        )
        
        # 更新提醒状态
        if any(results.values()):
            reminder.status = ReminderStatus.SENT
            self.reminder_storage.update(reminder)
            logger.info(f"提醒已发送: {reminder.id}")
        else:
            logger.error(f"提醒发送失败: {reminder.id}")
        
        return results
    
    def run_all_checks(self, check_date: Optional[date] = None) -> Dict[str, List[Reminder]]:
        """
        运行所有提醒检查
        
        Args:
            check_date: 检查日期（默认今天）
        
        Returns:
            Dict[str, List[Reminder]]: 各类提醒的字典
        """
        if check_date is None:
            check_date = date.today()
        
        logger.info(f"运行所有提醒检查: {check_date}")
        
        results = {
            "tax": self.check_tax_reminders(check_date),
            "payable": self.check_payable_reminders(check_date),
            "receivable": self.check_receivable_reminders(check_date),
            "cashflow": self.check_cashflow_warnings(check_date)
        }
        
        total_reminders = sum(len(reminders) for reminders in results.values())
        logger.info(f"检查完成，共找到 {total_reminders} 条提醒")
        
        return results
    
    def send_all_pending_reminders(self) -> Dict[str, int]:
        """
        发送所有待发送的提醒
        
        Returns:
            Dict[str, int]: 发送统计 {"sent": 成功数, "failed": 失败数}
        """
        logger.info("发送所有待发送的提醒")
        
        pending_reminders = self.reminder_storage.get_pending()
        
        sent_count = 0
        failed_count = 0
        
        for reminder in pending_reminders:
            results = self.send_reminder(reminder)
            
            if any(results.values()):
                sent_count += 1
            else:
                failed_count += 1
        
        logger.info(f"发送完成：成功 {sent_count} 条，失败 {failed_count} 条")
        
        return {"sent": sent_count, "failed": failed_count}
