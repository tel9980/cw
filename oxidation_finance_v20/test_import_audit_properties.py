#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试导入审计属性测试模块
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    print("尝试导入测试模块...")
    from tests import test_audit_properties
    print("✓ 成功导入 test_audit_properties")
    
    # 列出测试类
    test_classes = [
        name for name in dir(test_audit_properties)
        if name.startswith('Test')
    ]
    print(f"\n找到 {len(test_classes)} 个测试类:")
    for cls_name in test_classes:
        cls = getattr(test_audit_properties, cls_name)
        test_methods = [
            method for method in dir(cls)
            if method.startswith('test_')
        ]
        print(f"  - {cls_name}: {len(test_methods)} 个测试方法")
    
    print("\n✅ 模块导入成功，测试文件结构正确")
    sys.exit(0)
    
except Exception as e:
    print(f"\n❌ 导入失败: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
