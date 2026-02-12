#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
运行审计属性测试
"""

import sys
import os

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import subprocess

if __name__ == "__main__":
    print("=" * 60)
    print("运行审计功能属性测试")
    print("=" * 60)
    
    # 运行pytest
    test_file = os.path.join(
        os.path.dirname(__file__),
        "tests",
        "test_audit_properties.py"
    )
    
    cmd = [
        sys.executable,
        "-m", "pytest",
        test_file,
        "-v",
        "--tb=short",
        "-x"  # 遇到第一个失败就停止
    ]
    
    print(f"\n执行命令: {' '.join(cmd)}\n")
    
    result = subprocess.run(cmd)
    
    sys.exit(result.returncode)
