#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
运行报表管理器测试
"""

import sys
import subprocess

if __name__ == "__main__":
    # 运行测试
    result = subprocess.run(
        [sys.executable, "-m", "pytest", "tests/test_report_manager.py", "-v", "--tb=short"],
        cwd=".",
        capture_output=False
    )
    
    sys.exit(result.returncode)
