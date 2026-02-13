#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
运行配置管理器属性测试
"""

import subprocess
import sys
from pathlib import Path


def main():
    """运行配置管理器属性测试"""
    print("=" * 60)
    print("配置管理器属性测试")
    print("=" * 60)
    print()

    # 获取当前目录
    project_dir = Path(__file__).parent.absolute()

    # 运行属性测试
    cmd = [
        sys.executable,
        "-m",
        "pytest",
        "tests/test_config_properties.py",
        "-v",  # 详细输出
        "--tb=short",  # 简短traceback
        "-x",  # 遇到第一个失败即停止
    ]

    result = subprocess.run(cmd, cwd=str(project_dir))

    print()
    print("=" * 60)
    if result.returncode == 0:
        print("所有属性测试通过！")
    else:
        print("存在失败的测试")
    print("=" * 60)

    return result.returncode


if __name__ == "__main__":
    sys.exit(main())
