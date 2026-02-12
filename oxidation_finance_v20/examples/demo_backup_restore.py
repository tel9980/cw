#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
备份和恢复功能演示

本示例演示如何使用数据管理器进行系统数据的备份和恢复。
"""

import sys
from pathlib import Path
from datetime import date
from decimal import Decimal

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from database.db_manager import DatabaseManager
from utils.data_manager import DataManager
from models.business_models import (
    Customer, Supplier, ProcessingOrder,
    PricingUnit, ProcessType, OrderStatus
)


def demo_backup_restore():
    """演示备份和恢复功能"""
    
    print("=" * 70)
    print("氧化加工厂财务系统 - 数据备份和恢复演示")
    print("=" * 70)
    
    # 1. 连接数据库
    print("\n步骤 1: 连接数据库")
    print("-" * 70)
    
    db = DatabaseManager("oxidation_finance_demo.db")
    db.connect()
    data_manager = DataManager(db)
    
    print("✓ 数据库连接成功")
    
    # 2. 创建一些示例数据（如果不存在）
    print("\n步骤 2: 准备示例数据")
    print("-" * 70)
    
    customers = db.list_customers()
    if len(customers) == 0:
        print("创建示例客户...")
        customer = Customer(
            name="示例客户公司",
            contact="张经理",
            phone="13800138000",
            address="北京市朝阳区示例路123号",
            credit_limit=Decimal("500000")
        )
        db.save_customer(customer)
        print(f"  ✓ 客户: {customer.name}")
    else:
        print(f"  已有 {len(customers)} 个客户")
    
    orders = db.list_orders()
    if len(orders) == 0:
        print("创建示例订单...")
        customers = db.list_customers()
        if customers:
            customer = customers[0]
            order = ProcessingOrder(
                order_no="DEMO001",
                customer_id=customer.id,
                customer_name=customer.name,
                item_description="铝合金外壳",
                quantity=Decimal("500"),
                pricing_unit=PricingUnit.PER_PIECE,
                unit_price=Decimal("15.80"),
                processes=[ProcessType.SANDBLASTING, ProcessType.OXIDATION],
                total_amount=Decimal("7900.00"),
                status=OrderStatus.IN_PROGRESS,
                order_date=date.today()
            )
            db.save_order(order)
            print(f"  ✓ 订单: {order.order_no}, 金额: {order.total_amount}")
    else:
        print(f"  已有 {len(orders)} 个订单")
    
    # 3. 执行数据备份
    print("\n步骤 3: 执行数据备份")
    print("-" * 70)
    
    success, backup_file, backup_info = data_manager.backup_system_data(
        backup_dir="backups",
        include_config=True
    )
    
    if success:
        print("✓ 备份成功!")
        print(f"\n备份信息:")
        print(f"  • 备份文件: {backup_file}")
        print(f"  • 备份时间: {backup_info['backup_time']}")
        print(f"  • 总记录数: {backup_info['total_records']}")
        print(f"  • 客户数: {backup_info['customers_count']}")
        print(f"  • 供应商数: {backup_info['suppliers_count']}")
        print(f"  • 订单数: {backup_info['processing_orders_count']}")
        print(f"  • 收入记录: {backup_info['incomes_count']}")
        print(f"  • 支出记录: {backup_info['expenses_count']}")
        print(f"  • 银行账户: {backup_info['bank_accounts_count']}")
        print(f"  • 数据库大小: {backup_info['database_size']:,} 字节")
        print(f"  • 备份大小: {backup_info['backup_size']:,} 字节")
        print(f"  • 包含配置: {'是' if backup_info['config_included'] else '否'}")
    else:
        print(f"✗ 备份失败: {backup_info}")
        db.close()
        return
    
    # 4. 列出所有备份
    print("\n步骤 4: 列出所有可用备份")
    print("-" * 70)
    
    backups = data_manager.list_backups(backup_dir="backups")
    print(f"找到 {len(backups)} 个备份:\n")
    
    for i, backup in enumerate(backups[:5], 1):  # 只显示最近5个
        print(f"{i}. {backup['backup_name']}")
        print(f"   时间: {backup['backup_time']}")
        print(f"   大小: {backup['backup_size']:,} 字节")
        if 'total_records' in backup:
            print(f"   记录数: {backup['total_records']}")
        print(f"   包含配置: {'是' if backup['has_config'] else '否'}")
        print()
    
    # 5. 演示数据恢复（可选）
    print("\n步骤 5: 数据恢复演示")
    print("-" * 70)
    print("注意: 实际恢复会覆盖当前数据库!")
    print("本演示仅显示恢复过程，不实际执行恢复操作。")
    print("\n如需恢复数据，可以使用以下代码:")
    print("""
    success, messages = data_manager.restore_system_data(
        backup_file=backup_file,
        restore_config=True,
        validate_before_restore=True
    )
    
    if success:
        print("恢复成功!")
        for msg in messages:
            print(f"  • {msg}")
    else:
        print("恢复失败:")
        for msg in messages:
            print(f"  • {msg}")
    """)
    
    # 6. 数据完整性验证
    print("\n步骤 6: 验证数据库完整性")
    print("-" * 70)
    
    is_ok, errors = data_manager._verify_database_integrity()
    if is_ok:
        print("✓ 数据库完整性检查通过")
    else:
        print("✗ 数据库完整性检查发现问题:")
        for err in errors:
            print(f"  • {err}")
    
    # 关闭数据库
    db.close()
    
    print("\n" + "=" * 70)
    print("演示完成!")
    print("=" * 70)
    print("\n备份文件保存在 'backups' 目录中")
    print("您可以随时使用这些备份文件恢复数据")


if __name__ == "__main__":
    try:
        demo_backup_restore()
    except Exception as e:
        print(f"\n错误: {str(e)}")
        import traceback
        traceback.print_exc()
