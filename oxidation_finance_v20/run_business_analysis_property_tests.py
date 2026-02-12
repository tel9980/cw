#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
运行业务分析属性测试
"""

import sys
import os

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import subprocess

if __name__ == "__main__":
    print("=" * 80)
    print("运行业务分析属性测试 (Property 24)")
    print("=" * 80)
    
    # 运行pytest
    test_file = os.path.join(
        os.path.dirname(__file__),
        "tests",
        "test_business_analysis_properties.py"
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
