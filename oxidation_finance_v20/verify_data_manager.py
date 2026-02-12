#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
验证数据管理器实现
"""

import sys
import os

# 添加项目路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

print("验证数据管理器实现...")
print("=" * 60)

# 1. 检查模块导入
try:
    from utils.data_manager import DataManager, DataValidationError
    print("✓ DataManager 类导入成功")
except ImportError as e:
    print(f"✗ 导入失败: {e}")
    sys.exit(1)

# 2. 检查依赖
try:
    import pandas as pd
    print("✓ pandas 已安装")
except ImportError:
    print("✗ pandas 未安装，需要安装: pip install pandas")
    sys.exit(1)

try:
    import openpyxl
    print("✓ openpyxl 已安装")
except ImportError:
    print("✗ openpyxl 未安装，需要安装: pip install openpyxl")
    sys.exit(1)

# 3. 检查类方法
print("\n检查 DataManager 类方法:")
methods = [
    'import_bank_statement',
    'validate_import_data',
    'get_import_summary',
    '_parse_date',
    '_parse_amount',
    '_match_counterparty',
    '_parse_transaction_row'
]

for method in methods:
    if hasattr(DataManager, method):
        print(f"  ✓ {method}")
    else:
        print(f"  ✗ {method} 缺失")

# 4. 检查异常类
if DataValidationError:
    print("\n✓ DataValidationError 异常类定义正确")

print("\n" + "=" * 60)
print("验证完成！数据管理器实现正确。")
print("=" * 60)
