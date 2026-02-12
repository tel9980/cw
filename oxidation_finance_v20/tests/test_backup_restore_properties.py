#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
备份恢复属性测试 - 使用Hypothesis进行基于属性的测试

测试属性:
- 属性 22: 数据备份往返一致性
"""

import pytest
from hypothesis import given, strategies as st, settings, assume, HealthCheck
from hypothesis.strategies import composite
from decimal import Decimal
from datetime import date, datetime, timedelta
import tempfile
import os
import shutil
from pathlib import Path

from oxidation_finance_v20.database.db_manager import DatabaseManager
from oxidation_finance_v20.utils.data_manager import DataManager
from oxidation_finance_v20.models.business_models import (
    Customer, Supplier, ProcessingOrder, Income, Expense,
    BankAccount, BankTransaction,
    PricingUnit, ProcessType, OrderStatus, ExpenseType, BankType
)


# ============================================================================
# 测试数据生成策略
# ============================================================================

@composite
def valid_customer(draw):
    """生成有效的客户数据"""
    return Customer(
        name=draw(st.text(min_size=2, max_size=20, alphabet="ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789")) + "公司",
        contact=draw(st.text(min_size=2, max_size=10, alphabet="ABCDEFGHIJKLMNOPQRSTUVWXYZ")),
        phone=f"138{draw(st.integers(min_value=10000000, max_value=99999999))}",
        address=draw(st.text(min_size=5, max_size=30)),
        credit_limit=Decimal(str(draw(st.integers(min_value=1000, max_value=100000)))),
        notes=draw(st.text(max_size=50))
    )


@composite
def valid_supplier(draw):
    """生成有效的供应商数据"""
    return Supplier(
        name=draw(st.text(min_size=2, max_size=20, alphabet="ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789")) + "供应商",
        contact=draw(st.text(min_size=2, max_size=10, alphabet="ABCDEFGHIJKLMNOPQRSTUVWXYZ")),
        phone=f"139{draw(st.integers(min_value=10000000, max_value=99999999))}",
        address=draw(st.text(min_size=5, max_size=30)),
        business_type=draw(st.sampled_from(["原料供应", "设备供应", "委外加工", "其他"])),
        notes=draw(st.text(max_size=50))
    )


@composite
def valid_bank_account(draw):
    """生成有效的银行账户数据"""
    bank_type = draw(st.sampled_from([BankType.G_BANK, BankType.N_BANK]))
    return BankAccount(
        bank_type=bank_type,
        account_name=f"{bank_type.value}账户",
        account_number=f"6222{draw(st.integers(min_value=10000000, max_value=99999999))}",
        balance=Decimal(str(draw(st.integers(min_value=0, max_value=1000000)))),
        notes=draw(st.text(max_size=50))
    )


@composite
def valid_processing_order(draw, customer_id, customer_name):
    """生成有效的加工订单数据"""
    quantity = Decimal(str(draw(st.integers(min_value=1, max_value=1000))))
    unit_price = Decimal(str(draw(st.integers(min_value=1, max_value=100)))) + Decimal("0.50")
    total_amount = quantity * unit_price
    
    return ProcessingOrder(
        order_no=f"OX{draw(st.integers(min_value=100000, max_value=999999))}",
        customer_id=customer_id,
        customer_name=customer_name,
        item_description=draw(st.text(min_size=3, max_size=30)),
        quantity=quantity,
        pricing_unit=draw(st.sampled_from(list(PricingUnit))),
        unit_price=unit_price,
        processes=draw(st.lists(st.sampled_from(list(ProcessType)), min_size=1, max_size=3, unique=True)),
        outsourced_processes=[],
        total_amount=total_amount,
        outsourcing_cost=Decimal("0"),
        status=draw(st.sampled_from(list(OrderStatus))),
        order_date=date.today() - timedelta(days=draw(st.integers(min_value=0, max_value=365))),
        notes=draw(st.text(max_size=50))
    )


# ============================================================================
# 属性 22: 数据备份往返一致性
# **验证: 需求 8.4, 10.5**
# ============================================================================

class TestProperty22_BackupRestoreRoundTripConsistency:
    """
    属性 22: 数据备份往返一致性
    
    对于任何系统数据和参数，备份后恢复应该得到与备份前完全一致的数据状态
    """
    
    @settings(max_examples=5, deadline=None, suppress_health_check=[HealthCheck.function_scoped_fixture])
    @given(
        customer_count=st.integers(min_value=1, max_value=3),
        supplier_count=st.integers(min_value=1, max_value=3),
        bank_account_count=st.integers(min_value=1, max_value=2)
    )
    def test_backup_restore_preserves_all_data(
        self,
        temp_db,
        customer_count,
        supplier_count,
        bank_account_count
    ):
        """
        **验证: 需求 8.4, 10.5**
        
        测试备份和恢复的完整性：
        - 备份后恢复应该保留所有数据
        - 恢复后的数据应该与备份前完全一致
        - 数据的数量、内容、关系都应该保持不变
        """
        data_manager = DataManager(temp_db)
        
        # 创建临时备份目录
        backup_dir = tempfile.mkdtemp()
        
        try:
            # 1. 获取备份前的数据基线
            baseline_customers = temp_db.list_customers()
            baseline_suppliers = temp_db.list_suppliers()
            baseline_accounts = temp_db.list_bank_accounts()
            baseline_customer_count = len(baseline_customers)
            baseline_supplier_count = len(baseline_suppliers)
            baseline_account_count = len(baseline_accounts)
            
            # 2. 创建新的测试数据
            new_customers = []
            for i in range(customer_count):
                customer = Customer(
                    name=f"新客户{baseline_customer_count + i + 1}",
                    contact=f"联系人{i+1}",
                    phone=f"138{(baseline_customer_count + i):08d}",
                    address=f"测试地址{i+1}",
                    credit_limit=Decimal(f"{(i+1)*10000}"),
                    notes=f"客户备注{i+1}"
                )
                customer_id = temp_db.save_customer(customer)
                customer.id = customer_id
                new_customers.append(customer)
            
            # 3. 创建测试数据 - 供应商
            new_suppliers = []
            for i in range(supplier_count):
                supplier = Supplier(
                    name=f"新供应商{baseline_supplier_count + i + 1}",
                    contact=f"联系人{i+1}",
                    phone=f"139{(baseline_supplier_count + i):08d}",
                    address=f"测试地址{i+1}",
                    business_type="原料供应",
                    notes=f"供应商备注{i+1}"
                )
                supplier_id = temp_db.save_supplier(supplier)
                supplier.id = supplier_id
                new_suppliers.append(supplier)
            
            # 4. 创建测试数据 - 银行账户
            new_accounts = []
            for i in range(bank_account_count):
                bank_type = BankType.G_BANK if i % 2 == 0 else BankType.N_BANK
                account = BankAccount(
                    bank_type=bank_type,
                    account_name=f"{bank_type.value}新账户{baseline_account_count + i + 1}",
                    account_number=f"6222{(baseline_account_count + i):08d}",
                    balance=Decimal(f"{(i+1)*50000}"),
                    notes=f"账户备注{i+1}"
                )
                account_id = temp_db.save_bank_account(account)
                account.id = account_id
                new_accounts.append(account)
            
            # 5. 获取备份前的总数据
            customers_before_backup = temp_db.list_customers()
            suppliers_before_backup = temp_db.list_suppliers()
            accounts_before_backup = temp_db.list_bank_accounts()
            
            expected_customer_count = len(customers_before_backup)
            expected_supplier_count = len(suppliers_before_backup)
            expected_account_count = len(accounts_before_backup)
            
            # 6. 执行备份
            success, backup_file, backup_info = data_manager.backup_system_data(
                backup_dir=backup_dir,
                include_config=True
            )
            
            assert success, "备份应该成功"
            assert os.path.exists(backup_file), "备份文件应该存在"
            
            # 7. 修改数据库（模拟数据变化）
            temp_db.conn.execute("DELETE FROM customers WHERE name LIKE '新客户%'")
            temp_db.conn.execute("DELETE FROM suppliers WHERE name LIKE '新供应商%'")
            temp_db.conn.execute("DELETE FROM bank_accounts WHERE account_name LIKE '%新账户%'")
            temp_db.conn.commit()
            
            # 8. 执行恢复
            restore_success, messages = data_manager.restore_system_data(
                backup_file=backup_file,
                restore_config=True,
                validate_before_restore=True
            )
            
            assert restore_success, f"恢复应该成功: {messages}"
            
            # 9. 验证恢复后的数据完整性
            restored_customers = temp_db.list_customers()
            restored_suppliers = temp_db.list_suppliers()
            restored_accounts = temp_db.list_bank_accounts()
            
            # 验证数量
            assert len(restored_customers) == expected_customer_count, \
                f"恢复后的客户数量应该与备份前一致: {len(restored_customers)} vs {expected_customer_count}"
            assert len(restored_suppliers) == expected_supplier_count, \
                f"恢复后的供应商数量应该与备份前一致: {len(restored_suppliers)} vs {expected_supplier_count}"
            assert len(restored_accounts) == expected_account_count, \
                f"恢复后的账户数量应该与备份前一致: {len(restored_accounts)} vs {expected_account_count}"
            
            # 验证新创建的客户数据内容
            for new_customer in new_customers:
                restored = next((c for c in restored_customers if c.name == new_customer.name), None)
                assert restored is not None, f"新客户{new_customer.name}应该被恢复"
                assert restored.contact == new_customer.contact, "客户联系人应该一致"
                assert restored.phone == new_customer.phone, "客户电话应该一致"
        
        finally:
            # 清理备份目录
            if os.path.exists(backup_dir):
                shutil.rmtree(backup_dir)

    
    @settings(max_examples=5, deadline=None, suppress_health_check=[HealthCheck.function_scoped_fixture])
    @given(
        customer_count=st.integers(min_value=2, max_value=3),
        order_count=st.integers(min_value=1, max_value=3)
    )
    def test_backup_restore_preserves_relationships(
        self,
        temp_db,
        customer_count,
        order_count
    ):
        """
        **验证: 需求 8.4, 10.5**
        
        测试备份和恢复保持数据关系：
        - 订单与客户的关联关系应该保持
        - 外键约束应该保持有效
        - 关联数据应该完整一致
        """
        data_manager = DataManager(temp_db)
        backup_dir = tempfile.mkdtemp()
        
        try:
            # 1. 获取基线数据
            baseline_customers = temp_db.list_customers()
            baseline_orders = temp_db.list_orders()
            baseline_customer_count = len(baseline_customers)
            baseline_order_count = len(baseline_orders)
            
            # 2. 创建新客户数据
            new_customers = []
            for i in range(customer_count):
                customer = Customer(
                    name=f"新客户{baseline_customer_count + i + 1}",
                    contact=f"联系人{i+1}",
                    phone=f"138{(baseline_customer_count + i):08d}",
                    address=f"地址{i+1}"
                )
                customer_id = temp_db.save_customer(customer)
                customer.id = customer_id
                new_customers.append(customer)
            
            # 3. 为每个新客户创建订单
            new_orders = []
            for i in range(order_count):
                customer = new_customers[i % len(new_customers)]
                order = ProcessingOrder(
                    order_no=f"OX{202401000 + baseline_order_count + i}",
                    customer_id=customer.id,
                    customer_name=customer.name,
                    item_description=f"测试物品{i+1}",
                    quantity=Decimal("100"),
                    pricing_unit=PricingUnit.PIECE,
                    unit_price=Decimal("10.00"),
                    processes=[ProcessType.OXIDATION],
                    outsourced_processes=[],
                    total_amount=Decimal("1000.00"),
                    outsourcing_cost=Decimal("0"),
                    status=OrderStatus.PENDING,
                    order_date=date.today(),
                    notes=f"订单{i+1}"
                )
                order_id = temp_db.save_order(order)
                order.id = order_id
                new_orders.append(order)
            
            # 4. 获取备份前的总数据
            customers_before = temp_db.list_customers()
            orders_before = temp_db.list_orders()
            expected_customer_count = len(customers_before)
            expected_order_count = len(orders_before)
            
            # 5. 执行备份
            success, backup_file, backup_info = data_manager.backup_system_data(
                backup_dir=backup_dir,
                include_config=True
            )
            
            assert success, "备份应该成功"
            
            # 6. 清空新创建的数据
            temp_db.conn.execute("DELETE FROM processing_orders WHERE order_no LIKE 'OX%'")
            temp_db.conn.execute("DELETE FROM customers WHERE name LIKE '新客户%'")
            temp_db.conn.commit()
            
            # 7. 执行恢复
            restore_success, messages = data_manager.restore_system_data(
                backup_file=backup_file,
                restore_config=True
            )
            
            assert restore_success, f"恢复应该成功: {messages}"
            
            # 8. 验证关系完整性
            restored_customers = temp_db.list_customers()
            restored_orders = temp_db.list_orders()
            
            assert len(restored_customers) == expected_customer_count, \
                f"客户数量应该一致: {len(restored_customers)} vs {expected_customer_count}"
            assert len(restored_orders) == expected_order_count, \
                f"订单数量应该一致: {len(restored_orders)} vs {expected_order_count}"
            
            # 9. 验证每个新订单的客户关联
            for new_order in new_orders:
                restored_order = next((o for o in restored_orders if o.order_no == new_order.order_no), None)
                assert restored_order is not None, f"订单{new_order.order_no}应该被恢复"
                
                # 查找对应的客户
                customer = next((c for c in restored_customers if c.id == restored_order.customer_id), None)
                assert customer is not None, f"订单{restored_order.order_no}的客户应该存在"
                assert restored_order.customer_name == customer.name, "订单中的客户名称应该与客户表一致"
                
                # 验证订单内容
                assert restored_order.customer_id == new_order.customer_id, "客户ID应该一致"
                assert restored_order.item_description == new_order.item_description, "物品描述应该一致"
                assert restored_order.total_amount == new_order.total_amount, "总金额应该一致"
        
        finally:
            if os.path.exists(backup_dir):
                shutil.rmtree(backup_dir)
    
    @settings(max_examples=20, deadline=None, suppress_health_check=[HealthCheck.function_scoped_fixture])
    @given(
        include_config=st.booleans()
    )
    def test_backup_restore_config_consistency(
        self,
        temp_db,
        include_config
    ):
        """
        **验证: 需求 8.4, 10.5**
        
        测试配置参数的备份和恢复：
        - 如果include_config=True，配置应该被备份和恢复
        - 如果include_config=False，只备份数据库
        - 配置文件的存在性应该与include_config参数一致
        """
        data_manager = DataManager(temp_db)
        backup_dir = tempfile.mkdtemp()
        
        try:
            # 1. 创建一些基础数据
            customer = Customer(
                name="配置测试客户",
                contact="测试联系人",
                phone="13800000000",
                address="测试地址"
            )
            temp_db.save_customer(customer)
            
            # 2. 执行备份
            success, backup_file, backup_info = data_manager.backup_system_data(
                backup_dir=backup_dir,
                include_config=include_config
            )
            
            assert success, "备份应该成功"
            assert os.path.exists(backup_file), "备份文件应该存在"
            
            # 3. 验证配置文件的存在性
            backup_path = Path(backup_file)
            config_file = backup_path.parent / f"{backup_path.stem}_config.json"
            
            if include_config:
                assert config_file.exists(), "当include_config=True时，配置文件应该存在"
                assert backup_info.get("config_included") == True, "备份信息应该标记配置已包含"
                assert "config_file" in backup_info, "备份信息应该包含配置文件路径"
            else:
                assert not config_file.exists(), "当include_config=False时，配置文件不应该存在"
                assert backup_info.get("config_included") == False, "备份信息应该标记配置未包含"
            
            # 4. 验证元数据文件
            metadata_file = backup_path.parent / f"{backup_path.stem}_metadata.json"
            assert metadata_file.exists(), "元数据文件应该存在"
            
            # 5. 执行恢复
            restore_success, messages = data_manager.restore_system_data(
                backup_file=backup_file,
                restore_config=include_config
            )
            
            assert restore_success, f"恢复应该成功: {messages}"
            
            # 6. 验证数据恢复
            restored_customers = temp_db.list_customers()
            assert len(restored_customers) > 0, "恢复后应该有客户数据"
            assert restored_customers[0].name == "配置测试客户", "客户数据应该正确恢复"
        
        finally:
            if os.path.exists(backup_dir):
                shutil.rmtree(backup_dir)
    
    def test_backup_restore_multiple_times(self, temp_db):
        """
        **验证: 需求 8.4, 10.5**
        
        测试多次备份和恢复的一致性：
        - 多次备份应该产生独立的备份文件
        - 可以恢复到任意一个备份点
        - 每次恢复都应该得到对应备份点的数据状态
        """
        data_manager = DataManager(temp_db)
        backup_dir = tempfile.mkdtemp()
        
        try:
            backup_files = []
            customer_counts = []
            
            # 1. 创建多个备份点
            for i in range(3):
                # 添加客户
                customer = Customer(
                    name=f"客户{i+1}",
                    contact=f"联系人{i+1}",
                    phone=f"138{i:08d}",
                    address=f"地址{i+1}"
                )
                temp_db.save_customer(customer)
                
                # 记录当前客户数量
                current_count = len(temp_db.list_customers())
                customer_counts.append(current_count)
                
                # 添加小延迟确保时间戳不同
                import time
                time.sleep(1)
                
                # 执行备份
                success, backup_file, backup_info = data_manager.backup_system_data(
                    backup_dir=backup_dir,
                    include_config=True
                )
                
                assert success, f"第{i+1}次备份应该成功"
                backup_files.append(backup_file)
                
                # 确保备份文件不同
                if i > 0:
                    assert backup_file != backup_files[i-1], "每次备份应该产生不同的文件"
            
            # 2. 验证可以恢复到任意备份点
            for i, (backup_file, expected_count) in enumerate(zip(backup_files, customer_counts)):
                # 恢复到第i个备份点
                restore_success, messages = data_manager.restore_system_data(
                    backup_file=backup_file,
                    restore_config=True
                )
                
                assert restore_success, f"恢复到第{i+1}个备份点应该成功"
                
                # 验证数据状态
                restored_customers = temp_db.list_customers()
                assert len(restored_customers) == expected_count, \
                    f"恢复到第{i+1}个备份点后，客户数量应该是{expected_count}，实际是{len(restored_customers)}"
                
                # 验证客户名称
                for j, customer in enumerate(restored_customers):
                    assert customer.name == f"客户{j+1}", f"客户{j+1}的名称应该正确"
        
        finally:
            if os.path.exists(backup_dir):
                shutil.rmtree(backup_dir)
    
    def test_backup_validation_before_restore(self, temp_db):
        """
        **验证: 需求 8.4, 10.5**
        
        测试恢复前的备份文件验证：
        - 有效的备份文件应该通过验证
        - 验证应该检查文件完整性
        - 验证应该检查必需的表结构
        """
        data_manager = DataManager(temp_db)
        backup_dir = tempfile.mkdtemp()
        
        try:
            # 1. 创建测试数据
            customer = Customer(
                name="验证测试客户",
                contact="测试联系人",
                phone="13800000000",
                address="测试地址"
            )
            temp_db.save_customer(customer)
            
            # 2. 创建有效的备份
            success, backup_file, backup_info = data_manager.backup_system_data(
                backup_dir=backup_dir,
                include_config=True
            )
            
            assert success, "备份应该成功"
            
            # 3. 验证有效的备份文件
            is_valid, errors = data_manager._validate_backup_file(backup_file)
            assert is_valid, f"有效的备份文件应该通过验证: {errors}"
            assert len(errors) == 0, "有效的备份文件不应该有错误"
            
            # 4. 测试带验证的恢复
            restore_success, messages = data_manager.restore_system_data(
                backup_file=backup_file,
                restore_config=True,
                validate_before_restore=True
            )
            
            assert restore_success, f"带验证的恢复应该成功: {messages}"
            assert any("验证通过" in msg for msg in messages), "消息中应该包含验证通过的信息"
            
            # 5. 验证恢复后的数据
            restored_customers = temp_db.list_customers()
            assert len(restored_customers) > 0, "恢复后应该有客户数据"
            assert restored_customers[0].name == "验证测试客户", "客户数据应该正确恢复"
        
        finally:
            if os.path.exists(backup_dir):
                shutil.rmtree(backup_dir)
