#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
数据导入功能演示
展示如何使用DataManager导入银行流水
"""

import sys
import os
from pathlib import Path

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from utils.data_manager import DataManager
from models.business_models import BankType, Customer, Supplier
from database.db_manager import DatabaseManager


def demo_data_import():
    """演示数据导入功能"""
    
    print("=" * 70)
    print("数据导入功能演示")
    print("=" * 70)
    
    # 1. 初始化数据库
    print("\n步骤 1: 初始化数据库...")
    db_path = "demo_import.db"
    db = DatabaseManager(db_path)
    db.connect()
    print("✓ 数据库连接成功")
    
    # 2. 创建示例客户和供应商数据
    print("\n步骤 2: 创建示例客户和供应商...")
    
    customers = [
        Customer(name="张三公司", contact="张三", phone="13800138000"),
        Customer(name="李四工厂", contact="李四", phone="13900139000"),
        Customer(name="王五贸易", contact="王五", phone="13700137000"),
        Customer(name="赵六企业", contact="赵六", phone="13600136000")
    ]
    
    suppliers = [
        Supplier(name="化工原料供应商", contact="供应商A", business_type="原料供应"),
        Supplier(name="喷砂加工厂", contact="供应商B", business_type="委外加工"),
        Supplier(name="电力公司", contact="供应商C", business_type="公用事业"),
        Supplier(name="水务公司", contact="供应商D", business_type="公用事业")
    ]
    
    for customer in customers:
        db.save_customer(customer)
    print(f"✓ 创建了 {len(customers)} 个客户")
    
    for supplier in suppliers:
        db.save_supplier(supplier)
    print(f"✓ 创建了 {len(suppliers)} 个供应商")
    
    # 3. 创建示例Excel文件
    print("\n步骤 3: 创建示例银行流水Excel文件...")
    from sample_bank_statement import create_sample_bank_statement
    excel_file = create_sample_bank_statement()
    
    # 4. 验证导入数据
    print("\n步骤 4: 验证导入数据...")
    data_manager = DataManager(db)
    
    is_valid, errors = data_manager.validate_import_data(str(excel_file))
    if is_valid:
        print("✓ 数据验证通过")
    else:
        print("✗ 数据验证失败:")
        for error in errors:
            print(f"  - {error}")
        return
    
    # 5. 获取导入摘要
    print("\n步骤 5: 获取导入摘要...")
    summary = data_manager.get_import_summary(str(excel_file))
    print(f"✓ 文件信息:")
    print(f"  - 总行数: {summary['total_rows']}")
    print(f"  - 列名: {', '.join(summary['columns'])}")
    if 'date_range' in summary:
        print(f"  - 日期范围: {summary['date_range']['start']} 至 {summary['date_range']['end']}")
    if 'amount_stats' in summary:
        stats = summary['amount_stats']
        print(f"  - 金额统计:")
        print(f"    最小值: {stats['min']:.2f}")
        print(f"    最大值: {stats['max']:.2f}")
        print(f"    总和: {stats['sum']:.2f}")
        print(f"    记录数: {stats['count']}")
    
    # 6. 导入银行流水
    print("\n步骤 6: 导入银行流水到G银行账户...")
    count, errors = data_manager.import_bank_statement(
        str(excel_file),
        BankType.G_BANK
    )
    
    print(f"✓ 成功导入 {count} 条记录")
    if errors:
        print(f"⚠ 发现 {len(errors)} 个错误:")
        for error in errors[:5]:  # 只显示前5个错误
            print(f"  - {error}")
    
    # 7. 查询导入的数据
    print("\n步骤 7: 查询导入的交易记录...")
    transactions = db.list_bank_transactions(BankType.G_BANK)
    print(f"✓ 数据库中共有 {len(transactions)} 条G银行交易记录")
    
    print("\n前5条记录:")
    print("-" * 70)
    for i, trans in enumerate(transactions[:5], 1):
        print(f"{i}. 日期: {trans.transaction_date}")
        print(f"   金额: {trans.amount:>10.2f} {'(收入)' if trans.amount > 0 else '(支出)'}")
        print(f"   交易对手: {trans.counterparty}")
        print(f"   摘要: {trans.description}")
        print("-" * 70)
    
    # 8. 统计信息
    print("\n步骤 8: 统计信息...")
    total_income = sum(t.amount for t in transactions if t.amount > 0)
    total_expense = sum(abs(t.amount) for t in transactions if t.amount < 0)
    net_amount = total_income - total_expense
    
    print(f"✓ 统计结果:")
    print(f"  - 总收入: {total_income:>10.2f}")
    print(f"  - 总支出: {total_expense:>10.2f}")
    print(f"  - 净额: {net_amount:>10.2f}")
    
    # 9. 展示交易对手匹配结果
    print("\n步骤 9: 交易对手匹配结果...")
    matched_customers = set()
    matched_suppliers = set()
    unmatched = set()
    
    customer_names = {c.name for c in customers}
    supplier_names = {s.name for s in suppliers}
    
    for trans in transactions:
        if trans.counterparty in customer_names:
            matched_customers.add(trans.counterparty)
        elif trans.counterparty in supplier_names:
            matched_suppliers.add(trans.counterparty)
        else:
            unmatched.add(trans.counterparty)
    
    print(f"✓ 匹配统计:")
    print(f"  - 匹配到客户: {len(matched_customers)} 个")
    for name in matched_customers:
        print(f"    • {name}")
    print(f"  - 匹配到供应商: {len(matched_suppliers)} 个")
    for name in matched_suppliers:
        print(f"    • {name}")
    if unmatched:
        print(f"  - 未匹配: {len(unmatched)} 个")
        for name in unmatched:
            print(f"    • {name}")
    
    # 10. 清理
    db.close()
    print("\n" + "=" * 70)
    print("演示完成！")
    print(f"数据库文件: {db_path}")
    print(f"Excel文件: {excel_file}")
    print("=" * 70)


if __name__ == "__main__":
    try:
        demo_data_import()
    except Exception as e:
        print(f"\n✗ 演示过程中出错: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
