"""
Pytest configuration and shared fixtures for testing
"""

import pytest
import os
import tempfile
import shutil
from datetime import date, datetime
from decimal import Decimal
from pathlib import Path

from small_accountant_v16.models import (
    TransactionRecord,
    Counterparty,
    Reminder,
    BankRecord,
    TransactionType,
    CounterpartyType,
    ReminderType,
    TransactionStatus,
    ReminderStatus,
    Priority,
    NotificationChannel,
)
from small_accountant_v16.config import ConfigManager


@pytest.fixture
def temp_dir():
    """创建临时目录用于测试"""
    temp_path = tempfile.mkdtemp()
    yield temp_path
    # 清理
    shutil.rmtree(temp_path, ignore_errors=True)


@pytest.fixture
def config_manager(temp_dir):
    """创建配置管理器用于测试"""
    config_file = os.path.join(temp_dir, "test_config.json")
    manager = ConfigManager(config_file)
    manager.config.storage.data_dir = os.path.join(temp_dir, "data")
    manager.config.storage.backup_dir = os.path.join(temp_dir, "backups")
    manager.config.storage.report_output_dir = os.path.join(temp_dir, "reports")
    manager.ensure_directories()
    return manager


@pytest.fixture
def sample_transaction():
    """创建示例交易记录"""
    return TransactionRecord(
        id="T001",
        date=date(2024, 1, 15),
        type=TransactionType.INCOME,
        amount=Decimal("10000.00"),
        counterparty_id="C001",
        description="销售收入",
        category="销售",
        status=TransactionStatus.COMPLETED,
        created_at=datetime(2024, 1, 15, 10, 0, 0),
        updated_at=datetime(2024, 1, 15, 10, 0, 0),
    )


@pytest.fixture
def sample_counterparty():
    """创建示例往来单位"""
    return Counterparty(
        id="C001",
        name="测试客户有限公司",
        type=CounterpartyType.CUSTOMER,
        contact_person="张三",
        phone="13800138000",
        email="zhangsan@example.com",
        address="北京市朝阳区测试路123号",
        tax_id="91110000000000000X",
        created_at=datetime(2024, 1, 1, 0, 0, 0),
        updated_at=datetime(2024, 1, 1, 0, 0, 0),
    )


@pytest.fixture
def sample_reminder():
    """创建示例提醒"""
    return Reminder(
        id="R001",
        type=ReminderType.TAX,
        title="增值税申报提醒",
        description="请在2024年1月15日前完成增值税申报",
        due_date=date(2024, 1, 15),
        priority=Priority.HIGH,
        status=ReminderStatus.PENDING,
        notification_channels=[NotificationChannel.DESKTOP, NotificationChannel.WECHAT],
        created_at=datetime(2024, 1, 1, 0, 0, 0),
    )


@pytest.fixture
def sample_bank_record():
    """创建示例银行流水"""
    return BankRecord(
        id="B001",
        transaction_date=date(2024, 1, 15),
        description="收款-测试客户有限公司",
        amount=Decimal("10000.00"),
        balance=Decimal("50000.00"),
        transaction_type="CREDIT",
        counterparty="测试客户有限公司",
    )


# Hypothesis strategies for property-based testing
from hypothesis import strategies as st

@st.composite
def transaction_strategy(draw):
    """生成随机交易记录的策略"""
    return TransactionRecord(
        id=draw(st.text(min_size=1, max_size=20, alphabet=st.characters(whitelist_categories=('Lu', 'Ll', 'Nd')))),
        date=draw(st.dates(min_value=date(2020, 1, 1), max_value=date(2030, 12, 31))),
        type=draw(st.sampled_from(list(TransactionType))),
        amount=Decimal(str(draw(st.floats(min_value=0.01, max_value=1000000.0, allow_nan=False, allow_infinity=False)))),
        counterparty_id=draw(st.text(min_size=1, max_size=20, alphabet=st.characters(whitelist_categories=('Lu', 'Ll', 'Nd')))),
        description=draw(st.text(min_size=1, max_size=100)),
        category=draw(st.text(min_size=1, max_size=50)),
        status=draw(st.sampled_from(list(TransactionStatus))),
        created_at=draw(st.datetimes(min_value=datetime(2020, 1, 1), max_value=datetime(2030, 12, 31))),
        updated_at=draw(st.datetimes(min_value=datetime(2020, 1, 1), max_value=datetime(2030, 12, 31))),
    )


@st.composite
def counterparty_strategy(draw):
    """生成随机往来单位的策略"""
    return Counterparty(
        id=draw(st.text(min_size=1, max_size=20, alphabet=st.characters(whitelist_categories=('Lu', 'Ll', 'Nd')))),
        name=draw(st.text(min_size=1, max_size=100)),
        type=draw(st.sampled_from(list(CounterpartyType))),
        contact_person=draw(st.text(min_size=1, max_size=50)),
        phone=draw(st.text(min_size=11, max_size=11, alphabet='0123456789')),
        email=draw(st.emails()),
        address=draw(st.text(min_size=1, max_size=200)),
        tax_id=draw(st.text(min_size=18, max_size=18, alphabet=st.characters(whitelist_categories=('Lu', 'Ll', 'Nd')))),
        created_at=draw(st.datetimes(min_value=datetime(2020, 1, 1), max_value=datetime(2030, 12, 31))),
        updated_at=draw(st.datetimes(min_value=datetime(2020, 1, 1), max_value=datetime(2030, 12, 31))),
    )


@st.composite
def bank_record_strategy(draw):
    """生成随机银行流水的策略"""
    return BankRecord(
        id=draw(st.text(min_size=1, max_size=20, alphabet=st.characters(whitelist_categories=('Lu', 'Ll', 'Nd')))),
        transaction_date=draw(st.dates(min_value=date(2020, 1, 1), max_value=date(2030, 12, 31))),
        description=draw(st.text(min_size=1, max_size=200)),
        amount=Decimal(str(draw(st.floats(min_value=0.01, max_value=1000000.0, allow_nan=False, allow_infinity=False)))),
        balance=Decimal(str(draw(st.floats(min_value=0.0, max_value=10000000.0, allow_nan=False, allow_infinity=False)))),
        transaction_type=draw(st.sampled_from(["DEBIT", "CREDIT"])),
        counterparty=draw(st.text(min_size=1, max_size=100)),
    )
