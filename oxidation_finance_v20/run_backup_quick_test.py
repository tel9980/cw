#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
运行快速备份测试
"""

import sys
import subprocess

def main():
    """运行快速备份测试"""
    result = subprocess.run(
        [sys.executable, "test_backup_quick.py"],
        capture_output=False
    )
    return result.returncode

if __name__ == "__main__":
    sys.exit(main())
