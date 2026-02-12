#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""快速测试"""

try:
    from business.order_manager import OrderManager
    from database.db_manager import DatabaseManager
    from models.business_models import PricingUnit, ProcessType, OrderStatus
    print("✓ 所有模块导入成功")
    print("✓ OrderManager 类已定义")
    print("✓ 支持的计价方式:")
    for unit in PricingUnit:
        print(f"  - {unit.value}")
    print("✓ 支持的工序类型:")
    for process in ProcessType:
        print(f"  - {process.value}")
    print("✓ 订单状态:")
    for status in OrderStatus:
        print(f"  - {status.value}")
except Exception as e:
    print(f"✗ 导入失败: {e}")
    import traceback
    traceback.print_exc()
