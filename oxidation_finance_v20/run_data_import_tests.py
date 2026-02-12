#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
快速运行数据导入属性测试
"""

import sys
import subprocess

def main():
    """运行数据导入属性测试"""
    print("=" * 60)
    print("运行数据导入属性测试")
    print("=" * 60)
    
    # 运行属性测试
    result = subprocess.run(
        [
            sys.executable, "-m", "pytest",
            "tests/test_data_import_properties.py",
            "-v",
            "--tb=short",
            "-x"
        ],
        capture_output=False
    )
    
    return result.returncode

if __name__ == "__main__":
    sys.exit(main())
