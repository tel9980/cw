#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
运行业务分析报告测试
"""

import sys
import subprocess
from pathlib import Path

if __name__ == "__main__":
    # 运行测试
    result = subprocess.run(
        [sys.executable, "-m", "pytest", "tests/test_business_analysis.py", "-v", "--tb=short"],
        cwd=".",
        capture_output=False
    )
    
    sys.exit(result.returncode)
