#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
验证业务分析属性测试文件
"""

import sys
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

try:
    print("正在导入测试模块...")
    from oxidation_finance_v20.tests import test_business_analysis_properties
    print("✓ 测试模块导入成功")
    
    print("\n正在检查测试类...")
    test_class = test_business_analysis_properties.TestBusinessAnalysisProperties
    print(f"✓ 找到测试类: {test_class.__name__}")
    
    print("\n测试方法:")
    test_methods = [m for m in dir(test_class) if m.startswith('test_')]
    for i, method in enumerate(test_methods, 1):
        print(f"  {i}. {method}")
    
    print(f"\n✓ 共找到 {len(test_methods)} 个测试方法")
    
    print("\n" + "=" * 80)
    print("验证完成！测试文件结构正确。")
    print("=" * 80)
    
    # 尝试运行一个简单的测试
    print("\n正在尝试运行测试...")
    import pytest
    
    test_file = Path(__file__).parent / "tests" / "test_business_analysis_properties.py"
    exit_code = pytest.main([
        str(test_file),
        "-v",
        "--tb=short",
        "-x",  # 第一个失败就停止
        "--maxfail=1"
    ])
    
    if exit_code == 0:
        print("\n✓ 所有测试通过！")
    else:
        print(f"\n✗ 测试失败，退出码: {exit_code}")
    
    sys.exit(exit_code)
    
except Exception as e:
    print(f"\n✗ 错误: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
