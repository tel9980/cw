#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""检查测试文件"""

import sys
import importlib.util

# 加载测试模块
spec = importlib.util.spec_from_file_location(
    "test_data_import_properties",
    "tests/test_data_import_properties.py"
)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)

# 列出所有类
print("Module attributes:")
for name in dir(module):
    obj = getattr(module, name)
    if isinstance(obj, type):
        print(f"  Class: {name}")
        # 列出类的方法
        for method_name in dir(obj):
            if method_name.startswith('test_'):
                print(f"    Method: {method_name}")
