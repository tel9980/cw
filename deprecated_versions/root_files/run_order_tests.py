#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
运行订单管理器测试
"""

import subprocess
import sys

def main():
    """运行测试"""
    print("=" * 60)
    print("运行订单管理器测试")
    print("=" * 60)
    
    # 运行pytest
    result = subprocess.run(
        [sys.executable, "-m", "pytest", 
         "oxidation_finance_v20/tests/test_order_manager.py", 
         "-v", "--tb=short"],
        capture_output=False
    )
    
    return result.returncode

if __name__ == "__main__":
    sys.exit(main())
