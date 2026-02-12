#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
验证 Task 2.4 - 委外加工属性测试

这个脚本验证属性测试文件是否存在并且结构正确
"""

import os
import sys

def verify_property_tests():
    """验证属性测试文件"""
    print("="*60)
    print("Task 2.4 验证 - 委外加工属性测试")
    print("="*60)
    print()
    
    # 检查文件是否存在
    test_file = "tests/test_outsourced_processing_properties.py"
    if not os.path.exists(test_file):
        print(f"❌ 错误: 测试文件不存在: {test_file}")
        return False
    
    print(f"✓ 测试文件存在: {test_file}")
    
    # 读取文件内容
    with open(test_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 验证关键内容
    checks = [
        ("属性 3: 委外加工信息关联性", "属性定义"),
        ("验证: 需求 1.3, 3.3", "需求验证标记"),
        ("test_outsourced_processing_order_association", "订单关联测试"),
        ("test_outsourced_processing_supplier_association", "供应商关联测试"),
        ("test_outsourced_processing_cost_calculation", "费用计算测试"),
        ("test_order_total_outsourcing_cost", "订单总成本测试"),
        ("test_outsourced_processing_payment_tracking", "付款跟踪测试"),
        ("test_payment_allocation_to_multiple_processing", "付款分配测试"),
        ("@given", "Hypothesis装饰器"),
        ("OutsourcedProcessingManager", "委外加工管理器导入"),
    ]
    
    all_passed = True
    for check_str, description in checks:
        if check_str in content:
            print(f"✓ {description}: 找到")
        else:
            print(f"❌ {description}: 未找到")
            all_passed = False
    
    print()
    print("="*60)
    
    if all_passed:
        print("✓ 所有验证通过!")
        print()
        print("属性测试文件包含以下测试:")
        print("  1. 委外加工记录与订单的关联性")
        print("  2. 委外加工记录与供应商的关联性")
        print("  3. 委外加工费用计算准确性")
        print("  4. 订单委外加工总成本计算准确性")
        print("  5. 委外加工付款跟踪准确性")
        print("  6. 付款分配到多个委外加工记录的一致性")
        print()
        print("这些测试验证了:")
        print("  - 需求 1.3: 委外加工信息记录")
        print("  - 需求 3.3: 委外加工费用管理")
        print()
        print("属性 3: 委外加工信息关联性")
        print("  对于任何包含委外加工的订单，委外供应商和费用信息")
        print("  应该与订单正确关联，并且能够通过订单查询到完整的")
        print("  委外信息")
        return True
    else:
        print("❌ 部分验证失败")
        return False

if __name__ == "__main__":
    success = verify_property_tests()
    sys.exit(0 if success else 1)
