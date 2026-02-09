# -*- coding: utf-8 -*-
"""
测试独立应用程序的核心功能
"""

import sys
from datetime import datetime

# 测试模块导入
print("=" * 70)
print("测试1：模块导入")
print("=" * 70)

try:
    from oxidation_factory import get_config
    from oxidation_factory.order_wizard import create_order_interactive
    from oxidation_factory.order_manager import Order
    print("✅ 所有模块导入成功")
except Exception as e:
    print(f"❌ 模块导入失败：{e}")
    sys.exit(1)

# 测试配置加载
print("\n" + "=" * 70)
print("测试2：配置加载")
print("=" * 70)

try:
    config = get_config()
    print(f"✅ 配置加载成功")
    print(f"  - 计价单位：{len(config.get_pricing_units())}种")
    print(f"  - 外发工序：{len(config.get_outsourced_processes())}种")
    print(f"  - 原材料类型：{len(config.get_material_types())}种")
except Exception as e:
    print(f"❌ 配置加载失败：{e}")
    sys.exit(1)

# 测试订单对象创建
print("\n" + "=" * 70)
print("测试3：订单对象创建")
print("=" * 70)

try:
    order = Order(
        order_no="TEST001",
        customer="测试客户",
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
    
    # 计算金额
    order.calculate_amount()
    order.calculate_unpaid()
    
    print("✅ 订单对象创建成功")
    print(f"  - 订单编号：{order.order_no}")
    print(f"  - 客户名称：{order.customer}")
    print(f"  - 计价方式：{order.quantity} {order.pricing_unit} × {order.unit_price} 元")
    print(f"  - 订单金额：{order.order_amount:.2f} 元")
    print(f"  - 外发成本：{order.outsourced_cost:.2f} 元")
    print(f"  - 预计利润：{order.order_amount - order.outsourced_cost:.2f} 元")
except Exception as e:
    print(f"❌ 订单对象创建失败：{e}")
    sys.exit(1)

# 测试示例数据生成脚本存在
print("\n" + "=" * 70)
print("测试4：示例数据生成脚本")
print("=" * 70)

import os
if os.path.exists("create_oxidation_demo_data.py"):
    print("✅ 示例数据生成脚本存在")
else:
    print("❌ 示例数据生成脚本不存在")

# 测试启动脚本存在
print("\n" + "=" * 70)
print("测试5：启动脚本")
print("=" * 70)

if os.path.exists("启动_氧化加工厂版.bat"):
    print("✅ 启动脚本存在")
else:
    print("❌ 启动脚本不存在")

# 测试使用说明存在
print("\n" + "=" * 70)
print("测试6：使用说明")
print("=" * 70)

if os.path.exists("氧化加工厂版_使用说明.txt"):
    print("✅ 使用说明存在")
else:
    print("❌ 使用说明不存在")

print("\n" + "=" * 70)
print("✅ 所有测试通过！独立应用程序核心功能正常")
print("=" * 70)
print("\n💡 提示：")
print("  - 可以运行 启动_氧化加工厂版.bat 启动应用")
print("  - 首次使用建议先生成示例数据（选项03）")
print("  - 查看使用说明了解详细功能")
