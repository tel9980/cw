#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
CWZS系统快速测试脚本
验证核心功能是否正常工作
"""

import os
import sys
import json
from datetime import datetime

def test_system():
    print("🔍 CWZS系统快速功能测试")
    print("="*40)
    
    # 测试1: 检查工作目录
    print(f"📋 当前目录: {os.getcwd()}")
    
    # 测试2: 检查必要文件
    required_files = [
        'tools/小白财务助手.py',
        '../一键部署.bat',
        '../启动CWZS.bat'
    ]
    
    print("\n📁 文件检查:")
    for file_path in required_files:
        if os.path.exists(file_path):
            print(f"✅ {file_path}")
        else:
            print(f"❌ {file_path}")
    
    # 测试3: 检查Python模块导入
    print("\n🐍 模块导入测试:")
    try:
        sys.path.insert(0, '.')
        from tools.小白财务助手 import SimpleFinanceHelper
        print("✅ 小白财务助手模块导入成功")
        
        # 创建实例测试
        helper = SimpleFinanceHelper()
        print("✅ 小白财务助手实例创建成功")
        
        # 测试数据文件
        if os.path.exists(helper.data_file):
            print("✅ 数据文件存在")
            with open(helper.data_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                print(f"📊 数据统计: 客户{len(data.get('customers', []))}个, 订单{len(data.get('orders', []))}个")
        else:
            print("ℹ️  数据文件不存在（首次运行正常）")
            
    except Exception as e:
        print(f"❌ 模块测试失败: {e}")
        return False
    
    # 测试4: 检查系统配置
    print("\n⚙️  系统配置检查:")
    print(f"✅ Python版本: {sys.version.split()[0]}")
    print(f"✅ 工作目录: {os.getcwd()}")
    
    print("\n🎉 系统测试完成！")
    print("\n🚀 现在可以:")
    print("1. 双击 启动CWZS.bat 使用系统")
    print("2. 或者在当前目录运行: python tools/小白财务助手.py")
    
    return True

if __name__ == "__main__":
    try:
        test_system()
    except Exception as e:
        print(f"❌ 测试过程中出现错误: {e}")
    finally:
        input("\n按任意键退出...")