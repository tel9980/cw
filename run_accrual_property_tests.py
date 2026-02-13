#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
运行实际发生制记账属性测试
"""

import sys
import subprocess

def main():
    """运行属性测试"""
    print("=" * 60)
    print("运行实际发生制记账属性测试")
    print("=" * 60)
    print()
    
    # 运行属性测试
    result = subprocess.run(
        [sys.executable, "-m", "pytest", 
         "oxidation_finance_v20/tests/test_accrual_properties.py",
         "-v", "--tb=short", "-s"],
        capture_output=False
    )
    
    print()
    print("=" * 60)
    if result.returncode == 0:
        print("✓ 所有属性测试通过!")
    else:
        print("✗ 部分测试失败，请检查输出")
    print("=" * 60)
    
    return result.returncode

if __name__ == "__main__":
    sys.exit(main())
