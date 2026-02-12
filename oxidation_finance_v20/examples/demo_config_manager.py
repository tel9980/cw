#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
配置管理器使用示例
演示如何使用ConfigManager管理系统配置
"""

import sys
from pathlib import Path
from decimal import Decimal

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from config.config_manager import ConfigManager
from models.business_models import Customer, Supplier
from database.db_manager import DatabaseManager


def demo_config_manager():
    """演示配置管理器的使用"""
    print("=" * 70)
    print("配置管理器使用示例")
    print("=" * 70)
    
    # 创建数据库管理器
    db = DatabaseManager("demo_config.db")
    db.connect()
    
    # 创建配置管理器
    config_manager = ConfigManager("demo_config.db", "demo_config_data")
    print("\n✓ 配置管理器创建成功\n")
    
    # ==================== 客户管理示例 ====================
    print("【客户管理】")
    print("-" * 70)
    
    # 添加客户
    customer1 = Customer(
        name="深圳市XX电子有限公司",
        contact="张经理",
        phone="13800138000",
        address="深圳市南山区科技园",
        credit_limit=Decimal("50000"),
        notes="长期合作客户，信誉良好"
    )
    config_manager.add_customer(customer1)
    print(f"✓ 添加客户: {customer1.name}")
    
    customer2 = Customer(
        name="东莞市YY五金厂",
        contact="李总",
        phone="13900139000",
        credit_limit=Decimal("30000")
    )
    config_manager.add_customer(customer2)
    print(f"✓ 添加客户: {customer2.name}")
    
    # 列出所有客户
    customers = config_manager.list_customers()
    print(f"\n当前客户总数: {len(customers)}")
    for customer in customers:
        print(f"  - {customer.name} (联系人: {customer.contact}, 信用额度: ¥{customer.credit_limit})")
    
    # ==================== 供应商管理示例 ====================
    print("\n【供应商管理】")
    print("-" * 70)
    
    # 添加供应商
    supplier1 = Supplier(
        name="广州市化工原料公司",
        contact="王经理",
        phone="13700137000",
        business_type="原料供应商",
        notes="主要供应三酸、片碱等化工原料"
    )
    config_manager.add_supplier(supplier1)
    print(f"✓ 添加供应商: {supplier1.name}")
    
    supplier2 = Supplier(
        name="佛山市喷砂加工厂",
        contact="赵师傅",
        phone="13600136000",
        business_type="委外加工商",
        notes="专业喷砂、拉丝加工"
    )
    config_manager.add_supplier(supplier2)
    print(f"✓ 添加供应商: {supplier2.name}")
    
    # 列出所有供应商
    suppliers = config_manager.list_suppliers()
    print(f"\n当前供应商总数: {len(suppliers)}")
    for supplier in suppliers:
        print(f"  - {supplier.name} (类型: {supplier.business_type}, 联系人: {supplier.contact})")
    
    # ==================== 计价方式配置示例 ====================
    print("\n【计价方式配置】")
    print("-" * 70)
    
    # 获取所有计价方式
    pricing_methods = config_manager.get_pricing_methods()
    print(f"系统支持的计价方式 (共 {len(pricing_methods)} 种):")
    for method in pricing_methods:
        print(f"  - {method['name']}: {method['description']}")
    
    # 添加自定义计价方式
    config_manager.add_pricing_method(
        "BATCH", "批次", "按批次计价，适用于批量小件"
    )
    print("\n✓ 添加自定义计价方式: 批次")
    
    # ==================== 工序类型配置示例 ====================
    print("\n【工序类型配置】")
    print("-" * 70)
    
    # 获取所有工序类型
    process_types = config_manager.get_process_types()
    print(f"系统支持的工序类型 (共 {len(process_types)} 种):")
    for ptype in process_types:
        print(f"  {ptype['order']}. {ptype['name']}: {ptype['description']}")
    
    # 添加自定义工序
    config_manager.add_process_type(
        "COATING", "喷涂", "表面喷涂保护层", 5
    )
    print("\n✓ 添加自定义工序: 喷涂")
    
    # ==================== 会计科目配置示例 ====================
    print("\n【会计科目配置】")
    print("-" * 70)
    
    # 获取会计科目结构
    account_structure = config_manager.get_account_structure()
    print("会计科目结构:")
    for category, accounts in account_structure.items():
        print(f"\n  {category.upper()} (共 {len(accounts)} 个科目):")
        for account in accounts[:3]:  # 只显示前3个
            print(f"    - {account['code']} {account['name']} ({account['category']})")
        if len(accounts) > 3:
            print(f"    ... 还有 {len(accounts) - 3} 个科目")
    
    # 添加自定义会计科目
    config_manager.add_account(
        "assets", "1403", "原材料", "流动资产"
    )
    print("\n✓ 添加自定义会计科目: 1403 原材料")
    
    # ==================== 报表格式配置示例 ====================
    print("\n【报表格式配置】")
    print("-" * 70)
    
    # 获取报表格式
    report_formats = config_manager.get_report_formats()
    print("系统支持的报表格式:")
    for report_type, config in report_formats.items():
        print(f"\n  {config['name']} ({report_type}):")
        print(f"    格式: {config['format']}")
        print(f"    章节: {', '.join(config['sections'])}")
    
    # ==================== 配置导出导入示例 ====================
    print("\n【配置导出导入】")
    print("-" * 70)
    
    # 导出配置
    export_path = "exported_configs"
    config_manager.export_all_configs(export_path)
    print(f"✓ 配置已导出到: {export_path}/")
    
    # 导入配置
    config_manager.import_all_configs(export_path)
    print(f"✓ 配置已从 {export_path}/ 导入")
    
    print("\n" + "=" * 70)
    print("配置管理器演示完成！")
    print("=" * 70)
    
    # 清理
    db.close()
    
    # 提示
    print("\n提示:")
    print("  - 数据库文件: demo_config.db")
    print("  - 配置文件目录: demo_config_data/")
    print("  - 导出配置目录: exported_configs/")
    print("  - 可以查看这些文件了解配置管理器的工作方式")


if __name__ == "__main__":
    try:
        demo_config_manager()
    except Exception as e:
        print(f"\n错误: {e}")
        import traceback
        traceback.print_exc()
