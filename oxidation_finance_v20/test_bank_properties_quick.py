#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
快速验证银行账户属性测试
"""

import sys
import os

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# 导入测试模块验证语法
try:
    from oxidation_finance_v20.tests import test_bank_account_properties
    print("✓ 测试模块导入成功")
    
    # 检查测试类
    assert hasattr(test_bank_account_properties, 'TestProperty8_BankAccountTypeIdentificationAccuracy')
    print("✓ 属性8测试类存在")
    
    assert hasattr(test_bank_account_properties, 'TestProperty12_BankAccountIndependentManagement')
    print("✓ 属性12测试类存在")
    
    # 检查测试方法数量
    prop8_class = test_bank_account_properties.TestProperty8_BankAccountTypeIdentificationAccuracy
    prop8_methods = [m for m in dir(prop8_class) if m.startswith('test_')]
    print(f"✓ 属性8有 {len(prop8_methods)} 个测试方法")
    
    prop12_class = test_bank_account_properties.TestProperty12_BankAccountIndependentManagement
    prop12_methods = [m for m in dir(prop12_class) if m.startswith('test_')]
    print(f"✓ 属性12有 {len(prop12_methods)} 个测试方法")
    
    print("\n所有验证通过！测试文件结构正确。")
    print("\n现在运行实际的属性测试...")
    
    # 运行pytest
    import pytest
    exit_code = pytest.main([
        'tests/test_bank_account_properties.py',
        '-v',
        '--tb=short',
        '-x'  # 遇到第一个失败就停止
    ])
    
    sys.exit(exit_code)
    
except Exception as e:
    print(f"✗ 错误: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
