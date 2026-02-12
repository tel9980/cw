#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
验证银行账户属性测试
"""

import sys
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

print("=" * 60)
print("验证银行账户属性测试文件")
print("=" * 60)

# 1. 导入测试模块
try:
    from tests import test_bank_account_properties
    print("✓ 测试模块导入成功")
except Exception as e:
    print(f"✗ 测试模块导入失败: {e}")
    sys.exit(1)

# 2. 检查属性8测试类
try:
    prop8_class = test_bank_account_properties.TestProperty8_BankAccountTypeIdentificationAccuracy
    prop8_methods = [m for m in dir(prop8_class) if m.startswith('test_')]
    print(f"✓ 属性8测试类存在，包含 {len(prop8_methods)} 个测试方法:")
    for method in prop8_methods:
        print(f"  - {method}")
except Exception as e:
    print(f"✗ 属性8测试类检查失败: {e}")
    sys.exit(1)

# 3. 检查属性12测试类
try:
    prop12_class = test_bank_account_properties.TestProperty12_BankAccountIndependentManagement
    prop12_methods = [m for m in dir(prop12_class) if m.startswith('test_')]
    print(f"✓ 属性12测试类存在，包含 {len(prop12_methods)} 个测试方法:")
    for method in prop12_methods:
        print(f"  - {method}")
except Exception as e:
    print(f"✗ 属性12测试类检查失败: {e}")
    sys.exit(1)

# 4. 验证测试装饰器
try:
    import hypothesis
    print(f"✓ Hypothesis版本: {hypothesis.__version__}")
except Exception as e:
    print(f"✗ Hypothesis未安装: {e}")
    sys.exit(1)

print("\n" + "=" * 60)
print("验证完成！测试文件结构正确。")
print("=" * 60)
print("\n提示: 运行 'python run_bank_property_tests.py' 执行完整的属性测试")
