# -*- coding: utf-8 -*-
"""
测试优化版应用程序的新功能
"""

import sys
import os
from datetime import datetime

# 测试本地存储模块
print("=" * 70)
print("测试1：本地存储模块导入")
print("=" * 70)

try:
    from oxidation_factory import get_storage
    from oxidation_factory.order_manager import Order
    print("✅ 本地存储模块导入成功")
except Exception as e:
    print(f"❌ 模块导入失败：{e}")
    sys.exit(1)

# 测试创建订单并保存
print("\n" + "=" * 70)
print("测试2：创建订单并保存到本地")
print("=" * 70)

try:
    storage = get_storage()
    
    # 创建测试订单
    order = Order(
        order_no="TEST_OPT_001",
        customer="测试客户A",
        order_date=datetime.now(),
        item_name="测试物品",
        pricing_unit="件",
        quantity=100,
        unit_price=2.5,
        process_details="氧化",
        outsourced_processes=["喷砂"],
        outsourced_cost=50.0,
        status="待生产"
    )
    
    order.calculate_amount()
    order.calculate_unpaid()
    
    if storage.save_order(order):
        print("✅ 订单保存成功")
    else:
        print("❌ 订单保存失败")
        
except Exception as e:
    print(f"❌ 测试失败：{e}")
    import traceback
    traceback.print_exc()

# 测试获取所有订单
print("\n" + "=" * 70)
print("测试3：获取所有订单")
print("=" * 70)

try:
    orders = storage.get_all_orders()
    print(f"✅ 成功获取 {len(orders)} 个订单")
    
    if orders:
        print("\n订单列表：")
        for order in orders[:5]:  # 只显示前5个
            print(f"  - {order['order_no']}: {order['customer']} - {order['order_amount']}元")
            
except Exception as e:
    print(f"❌ 测试失败：{e}")

# 测试搜索订单
print("\n" + "=" * 70)
print("测试4：搜索订单")
print("=" * 70)

try:
    results = storage.search_orders(customer="测试")
    print(f"✅ 搜索到 {len(results)} 个订单")
    
except Exception as e:
    print(f"❌ 测试失败：{e}")

# 测试统计功能
print("\n" + "=" * 70)
print("测试5：订单统计")
print("=" * 70)

try:
    stats = storage.get_statistics()
    print(f"✅ 统计成功")
    print(f"  订单总数: {stats['total_orders']}")
    print(f"  订单总额: {stats['total_amount']:.2f}元")
    print(f"  已收款: {stats['total_paid']:.2f}元")
    print(f"  未收款: {stats['total_unpaid']:.2f}元")
    
except Exception as e:
    print(f"❌ 测试失败：{e}")

# 测试导出功能
print("\n" + "=" * 70)
print("测试6：导出到Excel")
print("=" * 70)

try:
    # 检查是否安装了pandas
    import pandas as pd
    import openpyxl
    
    test_file = "财务数据/本地订单/测试导出.xlsx"
    if storage.export_to_excel(test_file):
        print("✅ 导出成功")
        if os.path.exists(test_file):
            print(f"  文件已创建：{test_file}")
            # 清理测试文件
            os.remove(test_file)
            print("  测试文件已清理")
    else:
        print("⚠️ 导出失败（可能缺少依赖）")
        
except ImportError:
    print("⚠️ 跳过导出测试（需要安装 pandas 和 openpyxl）")
    print("💡 运行：pip install pandas openpyxl")
except Exception as e:
    print(f"❌ 测试失败：{e}")

# 测试文件存在性
print("\n" + "=" * 70)
print("测试7：检查文件")
print("=" * 70)

files_to_check = [
    "氧化加工厂财务助手_优化版.py",
    "oxidation_factory/local_storage.py",
    "快速使用指南.txt"
]

for file in files_to_check:
    if os.path.exists(file):
        print(f"✅ {file}")
    else:
        print(f"❌ {file} 不存在")

print("\n" + "=" * 70)
print("✅ 所有测试完成！")
print("=" * 70)

print("\n💡 新功能说明：")
print("  1. 订单自动保存到本地JSON文件")
print("  2. 查看订单列表和详情")
print("  3. 搜索订单（按客户、状态、日期）")
print("  4. 订单统计分析")
print("  5. 导出订单到Excel")

print("\n🚀 运行优化版：")
print("  python 氧化加工厂财务助手_优化版.py")
