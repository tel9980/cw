#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
备份和恢复功能测试
"""

import pytest
import tempfile
import shutil
import json
from pathlib import Path
from datetime import datetime, date
from decimal import Decimal

from database.db_manager import DatabaseManager
from utils.data_manager import DataManager
from models.business_models import (
    Customer, Supplier, ProcessingOrder, Income, Expense,
    BankAccount, BankTransaction, PricingUnit, ProcessType,
    OrderStatus, ExpenseType, BankType
)


class TestBackupRestore:
    """测试数据备份和恢复功能"""
    
    @pytest.fixture
    def temp_dir(self):
        """创建临时目录"""
        temp_path = tempfile.mkdtemp()
        yield temp_path
        shutil.rmtree(temp_path, ignore_errors=True)
    
    @pytest.fixture
    def db_manager(self, temp_dir):
        """创建测试数据库管理器"""
        db_path = Path(temp_dir) / "test.db"
        db = DatabaseManager(str(db_path))
        db.connect()
        yield db
        db.close()
    
    @pytest.fixture
    def data_manager(self, db_manager):
        """创建数据管理器"""
        return DataManager(db_manager)
    
    @pytest.fixture
    def sample_data(self, db_manager):
        """创建示例数据"""
        # 创建客户
        customer = Customer(
            name="测试客户",
            contact="张三",
            phone="13800138000",
            address="测试地址",
            credit_limit=Decimal("100000")
        )
        db_manager.save_customer(customer)
        
        # 创建供应商
        supplier = Supplier(
            name="测试供应商",
            contact="李四",
            phone="13900139000",
            address="供应商地址",
            business_type="喷砂"
        )
        db_manager.save_supplier(supplier)
        
        # 创建订单
        order = ProcessingOrder(
            order_no="TEST001",
            customer_id=customer.id,
            customer_name=customer.name,
            item_description="测试产品",
            quantity=Decimal("100"),
            pricing_unit=PricingUnit.PER_PIECE,
            unit_price=Decimal("10.50"),
            processes=[ProcessType.SANDBLASTING, ProcessType.OXIDATION],
            total_amount=Decimal("1050.00"),
            status=OrderStatus.IN_PROGRESS,
            order_date=date.today()
        )
        db_manager.save_order(order)
        
        # 创建收入
        income = Income(
            customer_id=customer.id,
            customer_name=customer.name,
            amount=Decimal("500.00"),
            bank_type=BankType.G_BANK,
            has_invoice=True,
            related_orders=[order.id],
            allocation={order.id: Decimal("500.00")},
            income_date=date.today()
        )
        db_manager.save_income(income)
        
        # 创建支出
        expense = Expense(
            expense_type=ExpenseType.ACIDS,
            supplier_id=supplier.id,
            supplier_name=supplier.name,
            amount=Decimal("200.00"),
            bank_type=BankType.N_BANK,
            has_invoice=False,
            expense_date=date.today(),
            description="购买硫酸"
        )
        db_manager.save_expense(expense)
        
        # 创建银行账户
        account = BankAccount(
            bank_type=BankType.G_BANK,
            account_name="G银行账户",
            account_number="6222000012345678",
            balance=Decimal("50000.00")
        )
        db_manager.save_bank_account(account)
        
        return {
            "customer": customer,
            "supplier": supplier,
            "order": order,
            "income": income,
            "expense": expense,
            "account": account
        }
    
    def test_backup_system_data_success(self, data_manager, sample_data, temp_dir):
        """测试成功备份系统数据"""
        backup_dir = Path(temp_dir) / "backups"
        
        # 执行备份
        success, backup_file, backup_info = data_manager.backup_system_data(
            backup_dir=str(backup_dir),
            include_config=True
        )
        
        # 验证备份成功
        assert success is True
        assert backup_file != ""
        assert Path(backup_file).exists()
        
        # 验证备份信息
        assert "backup_time" in backup_info
        assert "total_records" in backup_info
        assert backup_info["total_records"] > 0
        assert backup_info["customers_count"] >= 1
        assert backup_info["suppliers_count"] >= 1
        assert backup_info["processing_orders_count"] >= 1
        assert backup_info["incomes_count"] >= 1
        assert backup_info["expenses_count"] >= 1
        assert backup_info["bank_accounts_count"] >= 1
        
        # 验证配置文件存在
        assert backup_info["config_included"] is True
        config_file = Path(backup_info["config_file"])
        assert config_file.exists()
        
        # 验证元数据文件存在
        metadata_file = Path(backup_info["metadata_file"])
        assert metadata_file.exists()
    
    def test_backup_without_config(self, data_manager, sample_data, temp_dir):
        """测试不包含配置的备份"""
        backup_dir = Path(temp_dir) / "backups"
        
        success, backup_file, backup_info = data_manager.backup_system_data(
            backup_dir=str(backup_dir),
            include_config=False
        )
        
        assert success is True
        assert backup_info["config_included"] is False
        assert "config_file" not in backup_info
    
    def test_restore_system_data_success(self, data_manager, sample_data, temp_dir):
        """测试成功恢复系统数据"""
        backup_dir = Path(temp_dir) / "backups"
        
        # 1. 创建备份
        success, backup_file, backup_info = data_manager.backup_system_data(
            backup_dir=str(backup_dir),
            include_config=True
        )
        assert success is True
        
        # 2. 修改数据（添加新客户）
        new_customer = Customer(
            name="新客户",
            contact="王五",
            phone="13700137000"
        )
        data_manager.db.save_customer(new_customer)
        
        # 验证新客户存在
        customers_before = data_manager.db.list_customers()
        assert len(customers_before) >= 2
        
        # 3. 恢复备份
        success, messages = data_manager.restore_system_data(
            backup_file=backup_file,
            restore_config=True,
            validate_before_restore=True
        )
        
        # 验证恢复成功
        assert success is True
        assert len(messages) > 0
        assert any("成功" in msg for msg in messages)
        
        # 4. 验证数据已恢复到备份时的状态
        customers_after = data_manager.db.list_customers()
        assert len(customers_after) == len(customers_before) - 1
        
        # 验证原始数据存在
        customer = data_manager.db.get_customer(sample_data["customer"].id)
        assert customer is not None
        assert customer.name == "测试客户"
    
    def test_restore_with_validation(self, data_manager, sample_data, temp_dir):
        """测试带验证的恢复"""
        backup_dir = Path(temp_dir) / "backups"
        
        # 创建备份
        success, backup_file, _ = data_manager.backup_system_data(
            backup_dir=str(backup_dir)
        )
        assert success is True
        
        # 恢复时启用验证
        success, messages = data_manager.restore_system_data(
            backup_file=backup_file,
            validate_before_restore=True
        )
        
        assert success is True
        assert any("验证通过" in msg for msg in messages)
    
    def test_restore_invalid_backup_file(self, data_manager, temp_dir):
        """测试恢复无效的备份文件"""
        # 创建一个空文件
        invalid_file = Path(temp_dir) / "invalid.db"
        invalid_file.touch()
        
        success, messages = data_manager.restore_system_data(
            backup_file=str(invalid_file),
            validate_before_restore=True
        )
        
        assert success is False
        assert len(messages) > 0
        assert any("验证失败" in msg or "为空" in msg for msg in messages)
    
    def test_restore_nonexistent_file(self, data_manager):
        """测试恢复不存在的文件"""
        success, messages = data_manager.restore_system_data(
            backup_file="/nonexistent/backup.db"
        )
        
        assert success is False
        assert len(messages) > 0
        assert any("不存在" in msg for msg in messages)
    
    def test_backup_statistics_accuracy(self, data_manager, sample_data):
        """测试备份统计信息的准确性"""
        stats = data_manager._collect_backup_statistics()
        
        assert "customers_count" in stats
        assert "suppliers_count" in stats
        assert "processing_orders_count" in stats
        assert "incomes_count" in stats
        assert "expenses_count" in stats
        assert "bank_accounts_count" in stats
        assert "total_records" in stats
        
        # 验证统计数字
        assert stats["customers_count"] >= 1
        assert stats["suppliers_count"] >= 1
        assert stats["processing_orders_count"] >= 1
        assert stats["total_records"] > 0
    
    def test_export_system_config(self, data_manager, sample_data):
        """测试导出系统配置"""
        config = data_manager._export_system_config()
        
        assert "version" in config
        assert "export_time" in config
        assert "customers" in config
        assert "suppliers" in config
        assert "bank_accounts" in config
        
        # 验证客户数据
        assert len(config["customers"]) >= 1
        customer_data = config["customers"][0]
        assert "id" in customer_data
        assert "name" in customer_data
        assert customer_data["name"] == "测试客户"
        
        # 验证供应商数据
        assert len(config["suppliers"]) >= 1
        supplier_data = config["suppliers"][0]
        assert "id" in supplier_data
        assert "name" in supplier_data
        assert supplier_data["name"] == "测试供应商"
    
    def test_validate_backup_file_success(self, data_manager, sample_data, temp_dir):
        """测试验证有效的备份文件"""
        backup_dir = Path(temp_dir) / "backups"
        
        # 创建备份
        success, backup_file, _ = data_manager.backup_system_data(
            backup_dir=str(backup_dir)
        )
        assert success is True
        
        # 验证备份文件
        is_valid, errors = data_manager._validate_backup_file(backup_file)
        
        assert is_valid is True
        assert len(errors) == 0
    
    def test_validate_backup_file_empty(self, data_manager, temp_dir):
        """测试验证空备份文件"""
        empty_file = Path(temp_dir) / "empty.db"
        empty_file.touch()
        
        is_valid, errors = data_manager._validate_backup_file(str(empty_file))
        
        assert is_valid is False
        assert len(errors) > 0
        assert any("为空" in err for err in errors)
    
    def test_verify_database_integrity(self, data_manager, sample_data):
        """测试数据库完整性验证"""
        is_ok, errors = data_manager._verify_database_integrity()
        
        # 正常情况下应该没有错误
        assert is_ok is True
        assert len(errors) == 0
    
    def test_list_backups(self, data_manager, sample_data, temp_dir):
        """测试列出所有备份"""
        backup_dir = Path(temp_dir) / "backups"
        
        # 创建多个备份
        for i in range(3):
            success, _, _ = data_manager.backup_system_data(
                backup_dir=str(backup_dir),
                include_config=True
            )
            assert success is True
        
        # 列出备份
        backups = data_manager.list_backups(backup_dir=str(backup_dir))
        
        assert len(backups) == 3
        
        # 验证备份信息
        for backup in backups:
            assert "backup_file" in backup
            assert "backup_name" in backup
            assert "backup_size" in backup
            assert "backup_time" in backup
            assert "has_config" in backup
            assert backup["has_config"] is True
    
    def test_list_backups_empty_directory(self, data_manager, temp_dir):
        """测试列出空目录的备份"""
        backup_dir = Path(temp_dir) / "empty_backups"
        backup_dir.mkdir()
        
        backups = data_manager.list_backups(backup_dir=str(backup_dir))
        
        assert len(backups) == 0
    
    def test_backup_restore_data_consistency(self, data_manager, sample_data, temp_dir):
        """测试备份恢复后的数据一致性"""
        backup_dir = Path(temp_dir) / "backups"
        
        # 1. 获取原始数据
        original_customer = data_manager.db.get_customer(sample_data["customer"].id)
        original_order = data_manager.db.get_order(sample_data["order"].id)
        original_income = data_manager.db.get_income(sample_data["income"].id)
        
        # 2. 创建备份
        success, backup_file, _ = data_manager.backup_system_data(
            backup_dir=str(backup_dir)
        )
        assert success is True
        
        # 3. 修改数据
        original_customer.name = "修改后的客户名"
        data_manager.db.save_customer(original_customer)
        
        # 4. 恢复备份
        success, _ = data_manager.restore_system_data(backup_file=backup_file)
        assert success is True
        
        # 5. 验证数据已恢复
        restored_customer = data_manager.db.get_customer(sample_data["customer"].id)
        assert restored_customer.name == "测试客户"  # 应该恢复到原始值
        
        restored_order = data_manager.db.get_order(sample_data["order"].id)
        assert restored_order.order_no == original_order.order_no
        assert restored_order.total_amount == original_order.total_amount
        
        restored_income = data_manager.db.get_income(sample_data["income"].id)
        assert restored_income.amount == original_income.amount
    
    def test_backup_with_large_dataset(self, data_manager, db_manager, temp_dir):
        """测试大数据集的备份"""
        # 创建大量数据
        for i in range(50):
            customer = Customer(
                name=f"客户{i}",
                contact=f"联系人{i}",
                phone=f"138{i:08d}"
            )
            db_manager.save_customer(customer)
        
        backup_dir = Path(temp_dir) / "backups"
        
        # 执行备份
        success, backup_file, backup_info = data_manager.backup_system_data(
            backup_dir=str(backup_dir)
        )
        
        assert success is True
        assert backup_info["customers_count"] >= 50
        assert Path(backup_file).stat().st_size > 0
    
    def test_multiple_backup_restore_cycles(self, data_manager, sample_data, temp_dir):
        """测试多次备份恢复循环"""
        backup_dir = Path(temp_dir) / "backups"
        
        for cycle in range(3):
            # 备份
            success, backup_file, _ = data_manager.backup_system_data(
                backup_dir=str(backup_dir)
            )
            assert success is True
            
            # 添加新数据
            customer = Customer(
                name=f"循环客户{cycle}",
                contact=f"联系人{cycle}"
            )
            data_manager.db.save_customer(customer)
            
            # 恢复
            success, _ = data_manager.restore_system_data(backup_file=backup_file)
            assert success is True
        
        # 验证最终状态
        customers = data_manager.db.list_customers()
        assert len(customers) >= 1


class TestBackupRestoreEdgeCases:
    """测试备份恢复的边界情况"""
    
    @pytest.fixture
    def temp_dir(self):
        """创建临时目录"""
        temp_path = tempfile.mkdtemp()
        yield temp_path
        shutil.rmtree(temp_path, ignore_errors=True)
    
    @pytest.fixture
    def db_manager(self, temp_dir):
        """创建测试数据库管理器"""
        db_path = Path(temp_dir) / "test.db"
        db = DatabaseManager(str(db_path))
        db.connect()
        yield db
        db.close()
    
    @pytest.fixture
    def data_manager(self, db_manager):
        """创建数据管理器"""
        return DataManager(db_manager)
    
    def test_backup_empty_database(self, data_manager, temp_dir):
        """测试备份空数据库"""
        backup_dir = Path(temp_dir) / "backups"
        
        success, backup_file, backup_info = data_manager.backup_system_data(
            backup_dir=str(backup_dir)
        )
        
        assert success is True
        assert backup_info["total_records"] == 0
        assert Path(backup_file).exists()
    
    def test_restore_to_empty_database(self, data_manager, temp_dir):
        """测试恢复到空数据库"""
        backup_dir = Path(temp_dir) / "backups"
        
        # 添加一些数据并备份
        customer = Customer(name="测试客户", contact="张三")
        data_manager.db.save_customer(customer)
        
        success, backup_file, _ = data_manager.backup_system_data(
            backup_dir=str(backup_dir)
        )
        assert success is True
        
        # 创建新的空数据库
        new_db_path = Path(temp_dir) / "new_test.db"
        new_db = DatabaseManager(str(new_db_path))
        new_db.connect()
        new_data_manager = DataManager(new_db)
        
        # 恢复到新数据库
        success, messages = new_data_manager.restore_system_data(
            backup_file=backup_file
        )
        
        assert success is True
        
        # 验证数据已恢复
        customers = new_data_manager.db.list_customers()
        assert len(customers) >= 1
        
        new_db.close()
    
    def test_backup_with_special_characters(self, data_manager, temp_dir):
        """测试包含特殊字符的数据备份"""
        # 创建包含特殊字符的数据
        customer = Customer(
            name="测试客户™©®",
            contact="张三 & 李四",
            phone="138-0013-8000",
            address="北京市朝阳区 <测试地址>",
            notes="备注：包含特殊字符 @#$%^&*()"
        )
        data_manager.db.save_customer(customer)
        
        backup_dir = Path(temp_dir) / "backups"
        
        # 备份
        success, backup_file, _ = data_manager.backup_system_data(
            backup_dir=str(backup_dir)
        )
        assert success is True
        
        # 恢复
        success, _ = data_manager.restore_system_data(backup_file=backup_file)
        assert success is True
        
        # 验证特殊字符保持完整
        restored_customer = data_manager.db.get_customer(customer.id)
        assert restored_customer.name == customer.name
        assert restored_customer.notes == customer.notes
