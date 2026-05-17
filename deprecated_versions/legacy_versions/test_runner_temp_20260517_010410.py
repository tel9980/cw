#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""临时测试运行器"""

import sys
sys.path.insert(0, '.')

from oxidation_finance_v20.tests.test_properties import TestProperty1_OrderIntegrity
from oxidation_finance_v20.models.business_models import Customer
from decimal import Decimal

# 创建测试实例
test_instance = TestProperty1_OrderIntegrity()

# 创建一个简单的客户
customer = Customer(
    name="测试客户",
    contact="张三",
    phone="13800138000",
    address="深圳市",
    credit_limit=Decimal("50000"),
    notes="测试"
)

# 运行测试
try:
    test_instance.test_order_information_integrity(customer)
    print("✅ test_order_information_integrity 通过")
except Exception as e:
    print(f"❌ test_order_information_integrity 失败: {e}")

try:
    test_instance.test_order_with_all_pricing_units(customer)
    print("✅ test_order_with_all_pricing_units 通过")
except Exception as e:
    print(f"❌ test_order_with_all_pricing_units 失败: {e}")

try:
    test_instance.test_order_with_all_process_types(customer)
    print("✅ test_order_with_all_process_types 通过")
except Exception as e:
    print(f"❌ test_order_with_all_process_types 失败: {e}")

print("\n所有测试完成!")
