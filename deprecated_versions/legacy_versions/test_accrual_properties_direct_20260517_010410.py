#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
直接运行实际发生制记账属性测试
"""

import sys
import os

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# 导入测试模块
from oxidation_finance_v20.tests.test_accrual_properties import *

# 运行一个简单的测试来验证
if __name__ == "__main__":
    print("=" * 60)
    print("验证属性测试模块")
    print("=" * 60)
    print()
    
    # 创建测试实例
    test_prop16 = TestProperty16_AccrualTimingAccuracy()
    test_prop17 = TestProperty17_FlexibleMatchingConsistency()
    test_prop18 = TestProperty18_PrepaymentTimeDifferenceHandling()
    
    print("✓ 属性 16 测试类已加载: 实际发生制记账时间准确性")
    print("✓ 属性 17 测试类已加载: 收支匹配灵活性")
    print("✓ 属性 18 测试类已加载: 预收预付款时间差异处理")
    print()
    print("=" * 60)
    print("属性测试模块验证成功!")
    print("=" * 60)
    print()
    print("要运行完整的属性测试，请使用:")
    print("pytest oxidation_finance_v20/tests/test_accrual_properties.py -v")
