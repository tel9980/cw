#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
运行银行账户管理属性测试
"""

import sys
import subprocess

def main():
    """运行属性测试"""
    print("="*60)
    print("运行银行账户管理属性测试 (Task 4.6)")
    print("="*60)
    print()
    
    # 运行属性测试
    result = subprocess.run(
        [sys.executable, "-m", "pytest", 
         "tests/test_bank_account_properties.py", 
         "-v", "--tb=short"],
        capture_output=False
    )
    
    return result.returncode

if __name__ == "__main__":
    sys.exit(main())
