"""
Property-based tests for ReminderSystem - Tax reminder timing

Feature: small-accountant-practical-enhancement
Property 5: Tax reminder timing
Validates: Requirements 2.1
"""

import pytest
from datetime import date, timedelta
from decimal import Decimal
from hypothesis import given, strategies as st, settings, assume
from hypothesis import HealthCheck
from typing import List
import uuid
import tempfile
import os

from small_accountant_v16.reminders.reminder_system import ReminderSystem, TaxDeadline
from small_accountant_v16.models.core_models import (
    Reminder, ReminderType, ReminderStatus, Priority,
    NotificationChannel
)
from small_accountant_v16.storage.transaction_storage import TransactionStorage
from small_accountant_v16.storage.counterparty_storage import CounterpartyStorage
from small_accountant_v16.storage.reminder_storage import ReminderStorage


# Hypothesis strategies for generating test data
@st.composite
def valid_check_date(draw):
    """生成有效的检查日期"""
    return draw(st.dates(
        min_value=date(2020, 1, 1),
        max_value=date(2030, 12, 31)
    ))


@st.composite
def vat_deadline_scenario(draw):
    """生成增值税申报截止日期场景"""
    check_date = draw(valid_check_date())
    
    # 计算当月增值税截止日期
    current_month_deadline = date(check_date.year, check_date.month, TaxDeadline.VAT_DAY)
    
    # 如果检查日期已过当月截止日期，使用下月截止日期
    if check_date > current_month_deadline:
        if check_date.month == 12:
            next_deadline = date(check_date.year + 1, 1, TaxDeadline.VAT_DAY)
        else:
            next_deadline = date(check_date.year, check_date.month + 1, TaxDeadline.VAT_DAY)
    else:
        next_deadline = current_month_deadline
    
    return check_date, next_deadline


@st.composite
def income_tax_deadline_scenario(draw):
    """生成所得税申报截止日期场景"""
    check_date = draw(valid_check_date())
    
    # 计算当前季度
    current_quarter = (check_date.month - 1) // 3 + 1
    
    # 计算季度所得税申报截止日期
    deadline_month, deadline_day = TaxDeadline.INCOME_TAX_QUARTERS[current_quarter]
    
    # 处理跨年情况（Q4的截止日期在次年1月）
    if current_quarter == 4 and check_date.month == 12:
        deadline_year = check_date.year + 1
    else:
        deadline_year = check_date.year
    
    current_quarter_deadline = date(deadline_year, deadline_month, deadline_day)
    
    # 如果已经过了本季度截止日期，计算下季度截止日期
    if check_date > current_quarter_deadline:
        next_quarter = (current_quarter % 4) + 1
        deadline_month, deadline_day = TaxDeadline.INCOME_TAX_QUARTERS[next_quarter]
        
        if next_quarter == 1:
            deadline_year = check_date.year + 1
        else:
            deadline_year = check_date.year
        
        next_deadline = date(deadline_year, deadline_month, deadline_day)
    else:
        next_deadline = current_quarter_deadline
    
    return check_date, next_deadline, current_quarter


class TestReminderSystemTaxProperties:
    """Property-based tests for reminder system tax reminders
    
    **Property 5: Tax reminder timing**
    For any valid check date, when checking tax reminders, the system should
    generate reminders at the correct timing intervals (7, 3, 1, 0 days before
    deadline) and with appropriate priority levels.
    **Validates: Requirements 2.1**
    """
    
    @given(scenario=vat_deadline_scenario())
    @settings(max_examples=50, suppress_health_check=[HealthCheck.function_scoped_fixture], deadline=None)
    def test_vat_reminder_timing_property(self, scenario):
        """
        Property: 增值税提醒时机属性
        
        验证：
        1. 在正确的时间点（截止日期前7、3、1、0天）生成增值税提醒
        2. 提醒优先级根据剩余天数正确设置
        3. 提醒内容包含正确的截止日期信息
        4. 不在提醒时间点时不生成提醒
        """
        check_date, vat_deadline = scenario
        
        # 创建临时存储
        with tempfile.TemporaryDirectory() as temp_dir:
            transaction_storage = TransactionStorage(temp_dir)
            counterparty_storage = CounterpartyStorage(temp_dir)
            reminder_storage = ReminderStorage(temp_dir)
            
            # 创建提醒系统
            reminder_system = ReminderSystem(
                transaction_storage=transaction_storage,
                counterparty_storage=counterparty_storage,
                reminder_storage=reminder_storage
            )
            
            # 检查税务提醒
            reminders = reminder_system.check_tax_reminders(check_date)
            
            # 计算距离截止日期的天数
            days_until_deadline = (vat_deadline - check_date).days
            
            # 验证提醒生成逻辑
            if days_until_deadline in ReminderSystem.TAX_REMINDER_DAYS:
                # 应该生成增值税提醒
                vat_reminders = [r for r in reminders if "增值税" in r.title]
                assert len(vat_reminders) >= 1, \
                    f"在截止日期前{days_until_deadline}天应该生成增值税提醒"
                
                vat_reminder = vat_reminders[0]
                
                # 验证提醒类型
                assert vat_reminder.type == ReminderType.TAX, \
                    f"增值税提醒类型应该为TAX，但为{vat_reminder.type}"
                
                # 验证截止日期
                assert vat_reminder.due_date == vat_deadline, \
                    f"增值税提醒截止日期应该为{vat_deadline}，但为{vat_reminder.due_date}"
                
                # 验证优先级
                expected_priority = Priority.HIGH if days_until_deadline <= 1 else Priority.MEDIUM
                assert vat_reminder.priority == expected_priority, \
                    f"增值税提醒优先级应该为{expected_priority}，但为{vat_reminder.priority}"
                
                # 验证提醒标题包含天数信息
                assert f"{days_until_deadline}天后到期" in vat_reminder.title, \
                    f"增值税提醒标题应该包含'{days_until_deadline}天后到期'"
                
                # 验证提醒描述包含截止日期
                expected_date_str = vat_deadline.strftime('%Y年%m月%d日')
                assert expected_date_str in vat_reminder.description, \
                    f"增值税提醒描述应该包含截止日期'{expected_date_str}'"
                
                # 验证提醒状态
                assert vat_reminder.status == ReminderStatus.PENDING, \
                    f"增值税提醒状态应该为PENDING，但为{vat_reminder.status}"
                
                # 验证通知渠道
                assert NotificationChannel.DESKTOP in vat_reminder.notification_channels, \
                    "增值税提醒应该包含桌面通知渠道"
                assert NotificationChannel.WECHAT in vat_reminder.notification_channels, \
                    "增值税提醒应该包含企业微信通知渠道"
            
            else:
                # 不应该生成增值税提醒
                vat_reminders = [r for r in reminders if "增值税" in r.title]
                assert len(vat_reminders) == 0, \
                    f"在截止日期前{days_until_deadline}天不应该生成增值税提醒，但生成了{len(vat_reminders)}个"
    
    @given(scenario=income_tax_deadline_scenario())
    @settings(max_examples=50, suppress_health_check=[HealthCheck.function_scoped_fixture], deadline=None)
    def test_income_tax_reminder_timing_property(self, scenario):
        """
        Property: 所得税提醒时机属性
        
        验证：
        1. 在正确的时间点（截止日期前7、3、1、0天）生成所得税提醒
        2. 提醒优先级根据剩余天数正确设置
        3. 提醒内容包含正确的截止日期信息
        4. 季度截止日期计算正确
        """
        check_date, income_tax_deadline, current_quarter = scenario
        
        # 创建临时存储
        with tempfile.TemporaryDirectory() as temp_dir:
            transaction_storage = TransactionStorage(temp_dir)
            counterparty_storage = CounterpartyStorage(temp_dir)
            reminder_storage = ReminderStorage(temp_dir)
            
            # 创建提醒系统
            reminder_system = ReminderSystem(
                transaction_storage=transaction_storage,
                counterparty_storage=counterparty_storage,
                reminder_storage=reminder_storage
            )
            
            # 检查税务提醒
            reminders = reminder_system.check_tax_reminders(check_date)
            
            # 计算距离截止日期的天数
            days_until_deadline = (income_tax_deadline - check_date).days
            
            # 验证提醒生成逻辑
            if days_until_deadline in ReminderSystem.TAX_REMINDER_DAYS:
                # 应该生成所得税提醒
                income_tax_reminders = [r for r in reminders if "所得税" in r.title]
                assert len(income_tax_reminders) >= 1, \
                    f"在截止日期前{days_until_deadline}天应该生成所得税提醒"
                
                income_tax_reminder = income_tax_reminders[0]
                
                # 验证提醒类型
                assert income_tax_reminder.type == ReminderType.TAX, \
                    f"所得税提醒类型应该为TAX，但为{income_tax_reminder.type}"
                
                # 验证截止日期
                assert income_tax_reminder.due_date == income_tax_deadline, \
                    f"所得税提醒截止日期应该为{income_tax_deadline}，但为{income_tax_reminder.due_date}"
                
                # 验证优先级
                expected_priority = Priority.HIGH if days_until_deadline <= 1 else Priority.MEDIUM
                assert income_tax_reminder.priority == expected_priority, \
                    f"所得税提醒优先级应该为{expected_priority}，但为{income_tax_reminder.priority}"
                
                # 验证提醒标题包含天数信息
                assert f"{days_until_deadline}天后到期" in income_tax_reminder.title, \
                    f"所得税提醒标题应该包含'{days_until_deadline}天后到期'"
                
                # 验证提醒描述包含截止日期
                expected_date_str = income_tax_deadline.strftime('%Y年%m月%d日')
                assert expected_date_str in income_tax_reminder.description, \
                    f"所得税提醒描述应该包含截止日期'{expected_date_str}'"
                
                # 验证提醒状态
                assert income_tax_reminder.status == ReminderStatus.PENDING, \
                    f"所得税提醒状态应该为PENDING，但为{income_tax_reminder.status}"
                
                # 验证通知渠道
                assert NotificationChannel.DESKTOP in income_tax_reminder.notification_channels, \
                    "所得税提醒应该包含桌面通知渠道"
                assert NotificationChannel.WECHAT in income_tax_reminder.notification_channels, \
                    "所得税提醒应该包含企业微信通知渠道"
            
            else:
                # 不应该生成所得税提醒
                income_tax_reminders = [r for r in reminders if "所得税" in r.title]
                assert len(income_tax_reminders) == 0, \
                    f"在截止日期前{days_until_deadline}天不应该生成所得税提醒，但生成了{len(income_tax_reminders)}个"
    
    @given(check_date=valid_check_date())
    @settings(max_examples=30, suppress_health_check=[HealthCheck.function_scoped_fixture], deadline=None)
    def test_tax_reminder_deadline_calculation_property(self, check_date):
        """
        Property: 税务提醒截止日期计算属性
        
        验证：
        1. 增值税截止日期始终为每月15日
        2. 所得税截止日期按季度正确计算
        3. 跨年情况处理正确
        4. 过期截止日期自动计算下一个周期
        """
        # 创建临时存储
        with tempfile.TemporaryDirectory() as temp_dir:
            transaction_storage = TransactionStorage(temp_dir)
            counterparty_storage = CounterpartyStorage(temp_dir)
            reminder_storage = ReminderStorage(temp_dir)
            
            # 创建提醒系统
            reminder_system = ReminderSystem(
                transaction_storage=transaction_storage,
                counterparty_storage=counterparty_storage,
                reminder_storage=reminder_storage
            )
            
            # 检查税务提醒
            reminders = reminder_system.check_tax_reminders(check_date)
            
            # 验证增值税截止日期计算
            vat_reminders = [r for r in reminders if "增值税" in r.title]
            for vat_reminder in vat_reminders:
                # 增值税截止日期应该是15日
                assert vat_reminder.due_date.day == TaxDeadline.VAT_DAY, \
                    f"增值税截止日期应该是{TaxDeadline.VAT_DAY}日，但为{vat_reminder.due_date.day}日"
                
                # 截止日期应该在检查日期之后
                assert vat_reminder.due_date >= check_date, \
                    f"增值税截止日期{vat_reminder.due_date}应该在检查日期{check_date}之后"
                
                # 截止日期与检查日期的差距应该在合理范围内（不超过45天）
                days_diff = (vat_reminder.due_date - check_date).days
                assert 0 <= days_diff <= 45, \
                    f"增值税截止日期与检查日期的差距{days_diff}天应该在0-45天范围内"
            
            # 验证所得税截止日期计算
            income_tax_reminders = [r for r in reminders if "所得税" in r.title]
            for income_tax_reminder in income_tax_reminders:
                # 截止日期应该在检查日期之后
                assert income_tax_reminder.due_date >= check_date, \
                    f"所得税截止日期{income_tax_reminder.due_date}应该在检查日期{check_date}之后"
                
                # 验证截止日期是否为有效的季度申报日期
                deadline_month = income_tax_reminder.due_date.month
                deadline_day = income_tax_reminder.due_date.day
                
                valid_deadlines = list(TaxDeadline.INCOME_TAX_QUARTERS.values())
                assert (deadline_month, deadline_day) in valid_deadlines, \
                    f"所得税截止日期{deadline_month}月{deadline_day}日不是有效的季度申报日期"
                
                # 截止日期与检查日期的差距应该在合理范围内（不超过120天）
                days_diff = (income_tax_reminder.due_date - check_date).days
                assert 0 <= days_diff <= 120, \
                    f"所得税截止日期与检查日期的差距{days_diff}天应该在0-120天范围内"
    
    @given(check_date=valid_check_date())
    @settings(max_examples=20, suppress_health_check=[HealthCheck.function_scoped_fixture], deadline=None)
    def test_tax_reminder_consistency_property(self, check_date):
        """
        Property: 税务提醒一致性属性
        
        验证：
        1. 相同检查日期多次调用结果一致
        2. 提醒ID唯一性
        3. 提醒保存到存储中
        4. 提醒数据完整性
        """
        # 创建临时存储
        with tempfile.TemporaryDirectory() as temp_dir:
            transaction_storage = TransactionStorage(temp_dir)
            counterparty_storage = CounterpartyStorage(temp_dir)
            reminder_storage = ReminderStorage(temp_dir)
            
            # 创建提醒系统
            reminder_system = ReminderSystem(
                transaction_storage=transaction_storage,
                counterparty_storage=counterparty_storage,
                reminder_storage=reminder_storage
            )
            
            # 第一次检查税务提醒
            reminders1 = reminder_system.check_tax_reminders(check_date)
            
            # 第二次检查税务提醒
            reminders2 = reminder_system.check_tax_reminders(check_date)
            
            # 验证结果一致性（每次都会生成新的提醒，因为系统设计为每次检查都创建新提醒）
            assert len(reminders2) == len(reminders1), \
                f"相同日期的检查应该生成相同数量的提醒，第一次{len(reminders1)}个，第二次{len(reminders2)}个"
            
            # 验证提醒类型一致性
            if len(reminders1) > 0 and len(reminders2) > 0:
                reminder1_types = sorted([r.title for r in reminders1])
                reminder2_types = sorted([r.title for r in reminders2])
                assert reminder1_types == reminder2_types, \
                    f"相同日期的检查应该生成相同类型的提醒"
            
            # 验证提醒ID唯一性
            all_reminders = reminders1 + reminders2
            reminder_ids = [r.id for r in all_reminders]
            unique_ids = set(reminder_ids)
            
            assert len(unique_ids) == len(reminder_ids), \
                f"提醒ID应该唯一，但有{len(reminder_ids) - len(unique_ids)}个重复ID"
            
            # 验证提醒保存到存储中
            stored_reminders = reminder_storage.get_all()
            assert len(stored_reminders) == len(all_reminders), \
                f"存储中应该有{len(all_reminders)}个提醒，但只有{len(stored_reminders)}个"
            
            # 验证提醒数据完整性
            for reminder in all_reminders:
                assert reminder.id is not None and reminder.id != "", \
                    "提醒ID不能为空"
                
                assert reminder.type == ReminderType.TAX, \
                    f"税务提醒类型应该为TAX，但为{reminder.type}"
                
                assert reminder.title is not None and reminder.title != "", \
                    "提醒标题不能为空"
                
                assert reminder.description is not None and reminder.description != "", \
                    "提醒描述不能为空"
                
                assert reminder.due_date is not None, \
                    "提醒截止日期不能为空"
                
                assert reminder.priority in [Priority.HIGH, Priority.MEDIUM, Priority.LOW], \
                    f"提醒优先级应该为有效值，但为{reminder.priority}"
                
                assert reminder.status == ReminderStatus.PENDING, \
                    f"新创建的提醒状态应该为PENDING，但为{reminder.status}"
                
                assert len(reminder.notification_channels) > 0, \
                    "提醒应该至少包含一个通知渠道"
                
                assert reminder.created_at is not None, \
                    "提醒创建时间不能为空"
    
    @given(data=st.data())
    @settings(max_examples=20, suppress_health_check=[HealthCheck.function_scoped_fixture], deadline=None)
    def test_tax_reminder_edge_cases_property(self, data):
        """
        Property: 税务提醒边界情况属性
        
        验证：
        1. 月末和月初的增值税提醒处理
        2. 季度末和季度初的所得税提醒处理
        3. 年末和年初的跨年处理
        4. 特殊日期（如2月29日）的处理
        """
        # 生成边界日期
        edge_dates = [
            # 月末月初
            date(2024, 1, 31),  # 1月末
            date(2024, 2, 1),   # 2月初
            date(2024, 2, 29),  # 闰年2月29日
            date(2024, 3, 1),   # 3月初
            
            # 季度末季度初
            date(2024, 3, 31),  # Q1末
            date(2024, 4, 1),   # Q2初
            date(2024, 6, 30),  # Q2末
            date(2024, 7, 1),   # Q3初
            date(2024, 9, 30),  # Q3末
            date(2024, 10, 1),  # Q4初
            date(2024, 12, 31), # Q4末
            
            # 年末年初
            date(2023, 12, 31), # 年末
            date(2024, 1, 1),   # 年初
        ]
        
        check_date = data.draw(st.sampled_from(edge_dates))
        
        # 创建临时存储
        with tempfile.TemporaryDirectory() as temp_dir:
            transaction_storage = TransactionStorage(temp_dir)
            counterparty_storage = CounterpartyStorage(temp_dir)
            reminder_storage = ReminderStorage(temp_dir)
            
            # 创建提醒系统
            reminder_system = ReminderSystem(
                transaction_storage=transaction_storage,
                counterparty_storage=counterparty_storage,
                reminder_storage=reminder_storage
            )
            
            # 检查税务提醒（不应该抛出异常）
            try:
                reminders = reminder_system.check_tax_reminders(check_date)
                
                # 验证返回结果是列表
                assert isinstance(reminders, list), \
                    f"税务提醒检查应该返回列表，但返回了{type(reminders)}"
                
                # 验证所有提醒都有有效的截止日期
                for reminder in reminders:
                    assert reminder.due_date >= check_date, \
                        f"提醒截止日期{reminder.due_date}应该在检查日期{check_date}之后"
                    
                    # 验证截止日期是有效日期
                    assert isinstance(reminder.due_date, date), \
                        f"提醒截止日期应该是date对象，但为{type(reminder.due_date)}"
                
            except Exception as e:
                pytest.fail(f"边界日期{check_date}的税务提醒检查不应该抛出异常，但抛出了: {e}")