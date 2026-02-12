#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
运行委外加工属性测试
"""

import sys
import subprocess

def main():
    """运行属性测试"""
    print("="*60)
    print("运行委外加工属性测试 (Task 2.4)")
    print("="*60)
    print()
    
    # 运行属性测试
    result = subprocess.run(
        [sys.executable, "-m", "pytest", 
         "tests/test_outsourced_processing_properties.py", 
         "-v", "--tb=short"],
        capture_output=False
    )
    
    return result.returncode

if __name__ == "__main__":
    sys.exit(main())
