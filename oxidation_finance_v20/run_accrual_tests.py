#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
运行实际发生制记账测试
"""

import sys
import subprocess

def main():
    """运行测试"""
    print("=" * 60)
    print("运行实际发生制记账测试")
    print("=" * 60)
    
    # 运行测试
    result = subprocess.run(
        [sys.executable, "-m", "pytest", 
         "tests/test_accrual_accounting.py", 
         "-v", "--tb=short"],
        cwd=".",
        capture_output=False
    )
    
    if result.returncode == 0:
        print("\n" + "=" * 60)
        print("✓ 所有测试通过!")
        print("=" * 60)
    else:
        print("\n" + "=" * 60)
        print("✗ 测试失败")
        print("=" * 60)
        sys.exit(1)

if __name__ == "__main__":
    main()
