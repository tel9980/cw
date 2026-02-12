#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Pytest配置文件 - 提供测试fixtures
"""

import pytest
import tempfile
import os
from pathlib import Path
from datetime import date, datetime
from decimal import Decimal

from oxidation_finance_v20.database.db_manager import DatabaseManager
from oxidation_finance_v20.business.order_manager import OrderManager
from oxidation_finance_v20.business.outsourced_processing_manager import OutsourcedProcessingManager
from oxidation_finance_v20.models.business_models import (
    Customer, Supplier, ProcessingOrder, Income, Expense,
    BankAccount, BankTransaction,
    PricingUnit, ProcessType, OrderStatus, ExpenseType, BankType
)


@pytest.fixture
def temp_db():
    """创建临时数据库用于测试"""
    # 创建临时文件
    fd, path = tempfile.mkstemp(suffix='.db')
    os.close(fd)
    
    # 创建数据库管理器
    db = DatabaseManager(path)
    db.connect()
    
    yield db
    
    # 清理
    db.close()
    if os.path.exists(path):
        os.unlink(path)


@pytest.fixture
def db_manager():
    """创建数据库管理器用于测试（别名）"""
    # 创建临时文件
    fd, path = tempfile.mkstemp(suffix='.db')
    os.close(fd)
    
    # 创建数据库管理器
    db = DatabaseManager(path)
    db.connect()
    
    yield db
    
    # 清理
    db.close()
    if os.path.exists(path):
        os.unlink(path)


@pytest.fixture
def order_manager(db_manager):
    """创建订单管理器用于测试"""
    return OrderManager(db_manager)


@pytest.fixture
def outsourced_manager(db_manager):
    """创建委外加工管理器用于测试"""
    return OutsourcedProcessingManager(db_manager)


@pytest.fixture
def sample_customer():
    """创建示例客户"""
    return Customer(
        name="测试客户有限公司",
        contact="张经理",
        phone="138****1234",
        address="广东省深圳市",
        credit_limit=Decimal("50000"),
        notes="测试客户"
    )


@pytest.fixture
def sample_supplier():
    """创建示例供应商"""
    return Supplier(
        name="测试供应商",
        contact="李经理",
        phone="139****5678",
        address="广东省东莞市",
        business_type="原料供应商",
        notes="测试供应商"
    )


@pytest.fixture
def sample_order(sample_customer):
    """创建示例订单"""
    return ProcessingOrder(
        order_no="OX202401001",
        customer_id=sample_customer.id,
        customer_name=sample_customer.name,
        item_description="铝型材6063",
        quantity=Decimal("100"),
        pricing_unit=PricingUnit.METER,
        unit_price=Decimal("5.50"),
        processes=[ProcessType.SANDBLASTING, ProcessType.OXIDATION],
        outsourced_processes=[ProcessType.SANDBLASTING.value],
        total_amount=Decimal("550.00"),
        outsourcing_cost=Decimal("110.00"),
        status=OrderStatus.PENDING,
        order_date=date.today(),
        notes="测试订单"
    )


@pytest.fixture
def sample_income(sample_customer):
    """创建示例收入"""
    return Income(
        customer_id=sample_customer.id,
        customer_name=sample_customer.name,
        amount=Decimal("10000.00"),
        bank_type=BankType.G_BANK,
        has_invoice=True,
        related_orders=[],
        allocation={},
        income_date=date.today(),
        notes="测试收入"
    )


@pytest.fixture
def sample_expense(sample_supplier):
    """创建示例支出"""
    return Expense(
        expense_type=ExpenseType.ACID_THREE,
        supplier_id=sample_supplier.id,
        supplier_name=sample_supplier.name,
        amount=Decimal("5000.00"),
        bank_type=BankType.G_BANK,
        has_invoice=True,
        expense_date=date.today(),
        description="三酸采购",
        notes="测试支出"
    )


@pytest.fixture
def sample_bank_account():
    """创建示例银行账户"""
    return BankAccount(
        bank_type=BankType.G_BANK,
        account_name="G银行对公账户",
        account_number="6222****1234",
        balance=Decimal("100000.00"),
        notes="测试账户"
    )


@pytest.fixture
def sample_bank_transaction():
    """创建示例银行交易"""
    return BankTransaction(
        bank_type=BankType.G_BANK,
        transaction_date=date.today(),
        amount=Decimal("10000.00"),
        counterparty="测试客户",
        description="客户付款",
        matched=False,
        notes="测试交易"
    )
