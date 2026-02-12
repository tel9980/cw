#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
快速测试配置管理器
"""

import sys
import tempfile
import shutil
from pathlib import Path
from decimal import Decimal

# 添加项目根目录到路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from config.config_manager import ConfigManager
from models.business_models import Customer, Supplier
from database.schema import create_tables
import sqlite3


def test_config_manager():
    """快速测试配置管理器"""
    print("开始测试配置管理器...")
    
    # 创建临时目录和数据库
    temp_dir = tempfile.mkdtemp()
    db_path = Path(temp_dir) / "test.db"
    config_dir = Path(temp_dir) / "config_data"
    
    try:
        # 初始化数据库
        conn = sqlite3.connect(str(db_path))
        create_tables(conn)
        conn.close()
        
        # 创建配置管理器
        config_manager = ConfigManager(str(db_path), str(config_dir))
        print("✓ 配置管理器创建成功")
        
        # 测试客户管理
        customer = Customer(
            name="测试客户",
            contact="张三",
            phone="13800138000",
            credit_limit=Decimal("10000")
        )
        assert config_manager.add_customer(customer), "添加客户失败"
        print("✓ 添加客户成功")
        
        retrieved = config_manager.get_customer(customer.id)
        assert retrieved is not None, "获取客户失败"
        assert retrieved.name == "测试客户", "客户名称不匹配"
        print("✓ 获取客户成功")
        
        customers = config_manager.list_customers()
        assert len(customers) == 1, "客户列表长度不正确"
        print("✓ 列出客户成功")
        
        # 测试供应商管理
        supplier = Supplier(
            name="测试供应商",
            contact="李四",
            business_type="原料供应商"
        )
        assert config_manager.add_supplier(supplier), "添加供应商失败"
        print("✓ 添加供应商成功")
        
        retrieved_supplier = config_manager.get_supplier(supplier.id)
        assert retrieved_supplier is not None, "获取供应商失败"
        assert retrieved_supplier.name == "测试供应商", "供应商名称不匹配"
        print("✓ 获取供应商成功")
        
        # 测试计价方式配置
        methods = config_manager.get_pricing_methods()
        assert len(methods) == 7, "默认计价方式数量不正确"
        print(f"✓ 获取计价方式成功，共 {len(methods)} 种")
        
        assert config_manager.add_pricing_method("CUSTOM", "自定义", "自定义单位"), "添加计价方式失败"
        methods = config_manager.get_pricing_methods()
        assert len(methods) == 8, "添加计价方式后数量不正确"
        print("✓ 添加计价方式成功")
        
        # 测试工序类型配置
        process_types = config_manager.get_process_types()
        assert len(process_types) == 4, "默认工序类型数量不正确"
        print(f"✓ 获取工序类型成功，共 {len(process_types)} 种")
        
        # 测试会计科目配置
        account_structure = config_manager.get_account_structure()
        assert "assets" in account_structure, "会计科目结构缺少资产类别"
        assert "liabilities" in account_structure, "会计科目结构缺少负债类别"
        print("✓ 获取会计科目结构成功")
        
        # 测试报表格式配置
        report_formats = config_manager.get_report_formats()
        assert "balance_sheet" in report_formats, "报表格式缺少资产负债表"
        assert "income_statement" in report_formats, "报表格式缺少利润表"
        print("✓ 获取报表格式成功")
        
        # 测试配置导出导入
        export_path = Path(temp_dir) / "exported_configs"
        assert config_manager.export_all_configs(str(export_path)), "导出配置失败"
        assert (export_path / "pricing_methods.json").exists(), "计价方式配置文件未导出"
        print("✓ 导出配置成功")
        
        assert config_manager.import_all_configs(str(export_path)), "导入配置失败"
        print("✓ 导入配置成功")
        
        print("\n所有测试通过！✓")
        
    finally:
        # 清理临时目录
        shutil.rmtree(temp_dir)
        print("✓ 清理临时文件成功")


if __name__ == "__main__":
    test_config_manager()
