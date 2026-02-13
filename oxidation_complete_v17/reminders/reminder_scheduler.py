"""
Reminder Scheduler Module

Automates the reminder checking process by scheduling reminder checks
at specific times and intervals. Supports daily, weekly, and monthly schedules.

The scheduler can be run as a background service or cron job.
"""

import logging
import time
from datetime import datetime, date, time as dt_time, timedelta
from typing import Optional, List, Dict, Any, Callable
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path

from ..models.core_models import Reminder, NotificationChannel
from .reminder_system import ReminderSystem
from ..config.config_manager import ConfigManager


# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ScheduleFrequency(Enum):
    """调度频率"""
    DAILY = "daily"  # 每天
    WEEKLY = "weekly"  # 每周
    MONTHLY = "monthly"  # 每月
    CUSTOM = "custom"  # 自定义间隔（分钟）


@dataclass
class ScheduleConfig:
    """调度配置"""
    frequency: ScheduleFrequency
    check_time: dt_time  # 检查时间（时:分）
    enabled: bool = True
    custom_interval_minutes: Optional[int] = None  # 自定义间隔（仅用于CUSTOM频率）
    notification_channels: List[NotificationChannel] = field(
        default_factory=lambda: [NotificationChannel.DESKTOP, NotificationChannel.WECHAT]
    )
    
    def to_dict(self) -> dict:
        """转换为字典"""
        return {
            "frequency": self.frequency.value,
            "check_time": self.check_time.strftime("%H:%M"),
            "enabled": self.enabled,
            "custom_interval_minutes": self.custom_interval_minutes,
            "notification_channels": [ch.value for ch in self.notification_channels]
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> "ScheduleConfig":
        """从字典创建"""
        time_parts = data["check_time"].split(":")
        check_time = dt_time(int(time_parts[0]), int(time_parts[1]))
        
        return cls(
            frequency=ScheduleFrequency(data["frequency"]),
            check_time=check_time,
            enabled=data.get("enabled", True),
            custom_interval_minutes=data.get("custom_interval_minutes"),
            notification_channels=[
                NotificationChannel(ch) for ch in data.get("notification_channels", ["desktop", "wechat"])
            ]
        )


@dataclass
class ScheduledReminder:
    """已调度的提醒任务"""
    id: str
    name: str
    schedule: ScheduleConfig
    check_function: str  # 检查函数名称（如 "check_tax_reminders"）
    last_run: Optional[datetime] = None
    next_run: Optional[datetime] = None
    enabled: bool = True
    
    def to_dict(self) -> dict:
        """转换为字典"""
        return {
            "id": self.id,
            "name": self.name,
            "schedule": self.schedule.to_dict(),
            "check_function": self.check_function,
            "last_run": self.last_run.isoformat() if self.last_run else None,
            "next_run": self.next_run.isoformat() if self.next_run else None,
            "enabled": self.enabled
        }


class ReminderScheduler:
    """
    提醒调度器
    
    功能：
    - 安排提醒检查任务
    - 运行定时检查
    - 支持配置提醒时间和通知渠道
    - 支持每日、每周、每月调度
    - 可作为后台服务或cron任务运行
    """
    
    def __init__(
        self,
        reminder_system: Optional[ReminderSystem] = None,
        config_manager: Optional[ConfigManager] = None,
        storage_dir: str = "data"
    ):
        """
        初始化提醒调度器
        
        Args:
            reminder_system: 提醒系统实例（可选）
            config_manager: 配置管理器（可选）
            storage_dir: 数据存储目录
        """
        self.reminder_system = reminder_system or ReminderSystem(storage_dir=storage_dir)
        self.config_manager = config_manager or ConfigManager()
        self.storage_dir = storage_dir
        
        # 已调度的提醒任务
        self.scheduled_reminders: Dict[str, ScheduledReminder] = {}
        
        # 是否正在运行
        self.is_running = False
        
        logger.info("提醒调度器初始化完成")
    
    def schedule_reminder(
        self,
        reminder_id: str,
        name: str,
        check_function: str,
        schedule: ScheduleConfig
    ) -> ScheduledReminder:
        """
        安排提醒任务
        
        Args:
            reminder_id: 提醒任务ID
            name: 提醒任务名称
            check_function: 检查函数名称（如 "check_tax_reminders"）
            schedule: 调度配置
        
        Returns:
            ScheduledReminder: 已调度的提醒任务
        """
        logger.info(f"安排提醒任务: {name} ({check_function})")
        
        # 计算下次运行时间
        next_run = self._calculate_next_run(schedule)
        
        # 创建调度任务
        scheduled_reminder = ScheduledReminder(
            id=reminder_id,
            name=name,
            schedule=schedule,
            check_function=check_function,
            next_run=next_run,
            enabled=schedule.enabled
        )
        
        # 保存到调度列表
        self.scheduled_reminders[reminder_id] = scheduled_reminder
        
        logger.info(f"提醒任务已安排: {name}, 下次运行时间: {next_run}")
        
        return scheduled_reminder
    
    def _calculate_next_run(
        self,
        schedule: ScheduleConfig,
        from_time: Optional[datetime] = None
    ) -> datetime:
        """
        计算下次运行时间
        
        Args:
            schedule: 调度配置
            from_time: 起始时间（默认为当前时间）
        
        Returns:
            datetime: 下次运行时间
        """
        if from_time is None:
            from_time = datetime.now()
        
        if schedule.frequency == ScheduleFrequency.DAILY:
            # 每天在指定时间运行
            next_run = datetime.combine(from_time.date(), schedule.check_time)
            
            # 如果今天的时间已过，则安排到明天
            if next_run <= from_time:
                next_run += timedelta(days=1)
        
        elif schedule.frequency == ScheduleFrequency.WEEKLY:
            # 每周在指定时间运行（假设每周一）
            next_run = datetime.combine(from_time.date(), schedule.check_time)
            
            # 找到下一个周一
            days_until_monday = (7 - from_time.weekday()) % 7
            if days_until_monday == 0 and next_run <= from_time:
                days_until_monday = 7
            
            next_run += timedelta(days=days_until_monday)
        
        elif schedule.frequency == ScheduleFrequency.MONTHLY:
            # 每月在指定时间运行（假设每月1号）
            next_run = datetime.combine(from_time.date(), schedule.check_time)
            
            # 找到下个月的1号
            if from_time.day > 1 or (from_time.day == 1 and next_run <= from_time):
                if from_time.month == 12:
                    next_run = datetime(from_time.year + 1, 1, 1, 
                                       schedule.check_time.hour, schedule.check_time.minute)
                else:
                    next_run = datetime(from_time.year, from_time.month + 1, 1,
                                       schedule.check_time.hour, schedule.check_time.minute)
            else:
                next_run = datetime(from_time.year, from_time.month, 1,
                                   schedule.check_time.hour, schedule.check_time.minute)
        
        elif schedule.frequency == ScheduleFrequency.CUSTOM:
            # 自定义间隔（分钟）
            if schedule.custom_interval_minutes:
                next_run = from_time + timedelta(minutes=schedule.custom_interval_minutes)
            else:
                # 默认60分钟
                next_run = from_time + timedelta(minutes=60)
        
        else:
            raise ValueError(f"不支持的调度频率: {schedule.frequency}")
        
        return next_run
    
    def run_scheduled_checks(self, check_date: Optional[date] = None) -> Dict[str, Any]:
        """
        运行定时检查
        
        检查所有已调度的提醒任务，如果到了运行时间则执行检查。
        
        Args:
            check_date: 检查日期（默认今天）
        
        Returns:
            Dict[str, Any]: 执行结果统计
        """
        if check_date is None:
            check_date = date.today()
        
        current_time = datetime.now()
        logger.info(f"运行定时检查: {current_time}")
        
        results = {
            "check_time": current_time.isoformat(),
            "total_scheduled": len(self.scheduled_reminders),
            "executed": 0,
            "skipped": 0,
            "failed": 0,
            "reminders_found": 0,
            "reminders_sent": 0,
            "details": []
        }
        
        # 遍历所有已调度的任务
        for reminder_id, scheduled_reminder in self.scheduled_reminders.items():
            # 跳过未启用的任务
            if not scheduled_reminder.enabled:
                results["skipped"] += 1
                logger.info(f"跳过未启用的任务: {scheduled_reminder.name}")
                continue
            
            # 检查是否到了运行时间
            if scheduled_reminder.next_run and scheduled_reminder.next_run <= current_time:
                logger.info(f"执行提醒检查: {scheduled_reminder.name}")
                
                try:
                    # 执行检查函数
                    reminders = self._execute_check_function(
                        scheduled_reminder.check_function,
                        check_date
                    )
                    
                    # 发送提醒
                    sent_count = 0
                    for reminder in reminders:
                        # 使用配置的通知渠道
                        send_results = self.reminder_system.send_reminder(
                            reminder,
                            channels=scheduled_reminder.schedule.notification_channels
                        )
                        
                        if any(send_results.values()):
                            sent_count += 1
                    
                    # 更新统计
                    results["executed"] += 1
                    results["reminders_found"] += len(reminders)
                    results["reminders_sent"] += sent_count
                    
                    # 记录详情
                    results["details"].append({
                        "task": scheduled_reminder.name,
                        "status": "success",
                        "reminders_found": len(reminders),
                        "reminders_sent": sent_count
                    })
                    
                    # 更新最后运行时间和下次运行时间
                    scheduled_reminder.last_run = current_time
                    scheduled_reminder.next_run = self._calculate_next_run(
                        scheduled_reminder.schedule,
                        current_time
                    )
                    
                    logger.info(
                        f"任务执行完成: {scheduled_reminder.name}, "
                        f"找到 {len(reminders)} 条提醒, 发送 {sent_count} 条, "
                        f"下次运行: {scheduled_reminder.next_run}"
                    )
                
                except Exception as e:
                    results["failed"] += 1
                    results["details"].append({
                        "task": scheduled_reminder.name,
                        "status": "failed",
                        "error": str(e)
                    })
                    logger.error(f"任务执行失败: {scheduled_reminder.name}, 错误: {e}")
            else:
                results["skipped"] += 1
                logger.debug(
                    f"任务未到运行时间: {scheduled_reminder.name}, "
                    f"下次运行: {scheduled_reminder.next_run}"
                )
        
        logger.info(
            f"定时检查完成: 执行 {results['executed']} 个任务, "
            f"跳过 {results['skipped']} 个任务, "
            f"失败 {results['failed']} 个任务, "
            f"找到 {results['reminders_found']} 条提醒, "
            f"发送 {results['reminders_sent']} 条提醒"
        )
        
        return results
    
    def _execute_check_function(
        self,
        function_name: str,
        check_date: date
    ) -> List[Reminder]:
        """
        执行检查函数
        
        Args:
            function_name: 函数名称
            check_date: 检查日期
        
        Returns:
            List[Reminder]: 提醒列表
        """
        # 获取ReminderSystem的方法
        if hasattr(self.reminder_system, function_name):
            check_function = getattr(self.reminder_system, function_name)
            return check_function(check_date)
        else:
            raise ValueError(f"未知的检查函数: {function_name}")
    
    def setup_default_schedules(self) -> None:
        """
        设置默认调度任务
        
        创建常用的提醒检查任务：
        - 每日税务提醒检查（早上9点）
        - 每日应付账款检查（早上9点）
        - 每日应收账款检查（早上9点）
        - 每日现金流预警（早上9点）
        """
        logger.info("设置默认调度任务")
        
        # 从配置中获取通知渠道
        config = self.config_manager.get_config()
        channels = []
        if config.reminder.enable_desktop_notification:
            channels.append(NotificationChannel.DESKTOP)
        if config.reminder.enable_wechat_notification and config.wechat.enabled:
            channels.append(NotificationChannel.WECHAT)
        
        # 如果没有配置任何渠道，默认使用桌面通知
        if not channels:
            channels = [NotificationChannel.DESKTOP]
        
        # 默认检查时间：早上9点
        default_check_time = dt_time(9, 0)
        
        # 1. 税务提醒检查（每日）
        self.schedule_reminder(
            reminder_id="tax_reminders",
            name="税务申报提醒检查",
            check_function="check_tax_reminders",
            schedule=ScheduleConfig(
                frequency=ScheduleFrequency.DAILY,
                check_time=default_check_time,
                notification_channels=channels
            )
        )
        
        # 2. 应付账款检查（每日）
        self.schedule_reminder(
            reminder_id="payable_reminders",
            name="应付账款提醒检查",
            check_function="check_payable_reminders",
            schedule=ScheduleConfig(
                frequency=ScheduleFrequency.DAILY,
                check_time=default_check_time,
                notification_channels=channels
            )
        )
        
        # 3. 应收账款检查（每日）
        self.schedule_reminder(
            reminder_id="receivable_reminders",
            name="应收账款提醒检查",
            check_function="check_receivable_reminders",
            schedule=ScheduleConfig(
                frequency=ScheduleFrequency.DAILY,
                check_time=default_check_time,
                notification_channels=channels
            )
        )
        
        # 4. 现金流预警（每日）
        self.schedule_reminder(
            reminder_id="cashflow_warnings",
            name="现金流预警检查",
            check_function="check_cashflow_warnings",
            schedule=ScheduleConfig(
                frequency=ScheduleFrequency.DAILY,
                check_time=default_check_time,
                notification_channels=channels
            )
        )
        
        logger.info(f"已设置 {len(self.scheduled_reminders)} 个默认调度任务")
    
    def enable_reminder(self, reminder_id: str) -> bool:
        """
        启用提醒任务
        
        Args:
            reminder_id: 提醒任务ID
        
        Returns:
            bool: 是否成功
        """
        if reminder_id in self.scheduled_reminders:
            self.scheduled_reminders[reminder_id].enabled = True
            logger.info(f"已启用提醒任务: {reminder_id}")
            return True
        else:
            logger.warning(f"提醒任务不存在: {reminder_id}")
            return False
    
    def disable_reminder(self, reminder_id: str) -> bool:
        """
        禁用提醒任务
        
        Args:
            reminder_id: 提醒任务ID
        
        Returns:
            bool: 是否成功
        """
        if reminder_id in self.scheduled_reminders:
            self.scheduled_reminders[reminder_id].enabled = False
            logger.info(f"已禁用提醒任务: {reminder_id}")
            return True
        else:
            logger.warning(f"提醒任务不存在: {reminder_id}")
            return False
    
    def remove_reminder(self, reminder_id: str) -> bool:
        """
        移除提醒任务
        
        Args:
            reminder_id: 提醒任务ID
        
        Returns:
            bool: 是否成功
        """
        if reminder_id in self.scheduled_reminders:
            del self.scheduled_reminders[reminder_id]
            logger.info(f"已移除提醒任务: {reminder_id}")
            return True
        else:
            logger.warning(f"提醒任务不存在: {reminder_id}")
            return False
    
    def get_scheduled_reminders(self) -> List[ScheduledReminder]:
        """
        获取所有已调度的提醒任务
        
        Returns:
            List[ScheduledReminder]: 提醒任务列表
        """
        return list(self.scheduled_reminders.values())
    
    def get_reminder(self, reminder_id: str) -> Optional[ScheduledReminder]:
        """
        获取指定的提醒任务
        
        Args:
            reminder_id: 提醒任务ID
        
        Returns:
            Optional[ScheduledReminder]: 提醒任务，如果不存在则返回None
        """
        return self.scheduled_reminders.get(reminder_id)
    
    def run_continuous(self, check_interval_seconds: int = 60) -> None:
        """
        持续运行调度器（阻塞模式）
        
        适合作为后台服务运行。
        
        Args:
            check_interval_seconds: 检查间隔（秒，默认60秒）
        """
        logger.info(f"启动持续运行模式，检查间隔: {check_interval_seconds} 秒")
        self.is_running = True
        
        try:
            while self.is_running:
                # 运行定时检查
                self.run_scheduled_checks()
                
                # 等待下次检查
                time.sleep(check_interval_seconds)
        
        except KeyboardInterrupt:
            logger.info("收到中断信号，停止调度器")
            self.is_running = False
        
        except Exception as e:
            logger.error(f"调度器运行异常: {e}")
            self.is_running = False
            raise
    
    def stop(self) -> None:
        """停止持续运行模式"""
        logger.info("停止调度器")
        self.is_running = False
    
    def get_status(self) -> Dict[str, Any]:
        """
        获取调度器状态
        
        Returns:
            Dict[str, Any]: 状态信息
        """
        return {
            "is_running": self.is_running,
            "total_scheduled": len(self.scheduled_reminders),
            "enabled_count": sum(1 for r in self.scheduled_reminders.values() if r.enabled),
            "disabled_count": sum(1 for r in self.scheduled_reminders.values() if not r.enabled),
            "scheduled_reminders": [r.to_dict() for r in self.scheduled_reminders.values()]
        }
