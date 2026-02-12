#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
验证配置管理器功能
"""

import sys
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

print("开始验证配置管理器...")
print("=" * 60)

try:
    # 测试导入
    from config.config_manager import ConfigManager
    print("✓ ConfigManager 导入成功")
    
    from models.business_models import Customer, Supplier
    print("✓ 业务模型导入成功")
    
    from database.schema import create_tables
    print("✓ 数据库模式导入成功")
    
    import sqlite3
    import tempfile
    from decimal import Decimal
    
    # 创建临时数据库
    temp_db = tempfile.NamedTemporaryFile(suffix='.db', delete=False)
    db_path = temp_db.name
    temp_db.close()
    
    conn = sqlite3.connect(db_path)
    create_tables(conn)
    conn.close()
    print(f"✓ 临时数据库创建成功: {db_path}")
    
    # 创建配置管理器
    config_manager = ConfigManager(db_path)
    print("✓ ConfigManager 实例创建成功")
    
    # 测试客户管理
    customer = Customer(name="测试客户", contact="张三", phone="13800138000")
    result = config_manager.add_customer(customer)
    print(f"✓ 添加客户: {result}")
    
    retrieved = config_manager.get_customer(customer.id)
    if retrieved and retrieved.name == "测试客户":
        print("✓ 获取客户成功")
    else:
        print("✗ 获取客户失败")
    
    customers = config_manager.list_customers()
    print(f"✓ 列出客户: {len(customers)} 个")
    
    # 测试供应商管理
    supplier = Supplier(name="测试供应商", business_type="原料供应商")
    result = config_manager.add_supplier(supplier)
    print(f"✓ 添加供应商: {result}")
    
    # 测试计价方式
    methods = config_manager.get_pricing_methods()
    print(f"✓ 获取计价方式: {len(methods)} 种")
    for method in methods[:3]:
        print(f"  - {method['name']}: {method['description'][:20]}...")
    
    # 测试工序类型
    process_types = config_manager.get_process_types()
    print(f"✓ 获取工序类型: {len(process_types)} 种")
    for ptype in process_types:
        print(f"  - {ptype['name']}: {ptype['description'][:20]}...")
    
    # 测试会计科目
    account_structure = config_manager.get_account_structure()
    print(f"✓ 获取会计科目结构: {len(account_structure)} 个类别")
    for category, accounts in account_structure.items():
        print(f"  - {category}: {len(accounts)} 个科目")
    
    # 测试报表格式
    report_formats = config_manager.get_report_formats()
    print(f"✓ 获取报表格式: {len(report_formats)} 种")
    for report_type, config in report_formats.items():
        print(f"  - {config['name']}")
    
    print("=" * 60)
    print("所有验证通过！✓")
    
    # 清理
    import os
    os.unlink(db_path)
    print("✓ 清理临时文件")
    
except Exception as e:
    print(f"\n✗ 验证失败: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
