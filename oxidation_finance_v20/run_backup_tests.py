#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
快速运行备份恢复测试
"""

import sys
import subprocess

def main():
    """运行备份恢复测试"""
    print("=" * 60)
    print("运行备份恢复测试")
    print("=" * 60)
    
    # 运行测试
    result = subprocess.run(
        [
            sys.executable, "-m", "pytest",
            "tests/test_backup_restore.py",
            "-v",
            "--tb=short",
            "-x"
        ],
        capture_output=False
    )
    
    return result.returncode

if __name__ == "__main__":
    sys.exit(main())
