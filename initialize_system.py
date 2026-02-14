#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
CWZS系统初始化脚本
用于生产环境的系统初始化和配置
"""

import os
import sys
import json
from datetime import datetime

def initialize_system():
    """初始化CWZS系统"""
    print("🔧 CWZS系统初始化开始...")
    print("="*50)
    
    # 1. 创建必要目录
    print("\n1. 创建系统目录结构...")
    directories = [
        'data',
        'logs', 
        'temp',
        'cache',
        'backup',
        'exports'
    ]
    
    for directory in directories:
        if not os.path.exists(directory):
            os.makedirs(directory)
            print(f"   ✅ 创建目录: {directory}")
        else:
            print(f"   ℹ️  目录已存在: {directory}")
    
    # 2. 复制配置文件
    print("\n2. 配置系统参数...")
    if not os.path.exists('.env'):
        if os.path.exists('.env.example'):
            import shutil
            shutil.copy('.env.example', '.env')
            print("   ✅ 创建环境配置文件")
        else:
            print("   ⚠️  未找到示例配置文件")
    else:
        print("   ℹ️  环境配置文件已存在")
    
    # 3. 初始化数据文件
    print("\n3. 初始化数据存储...")
    data_file = 'oxidation_finance_v20/simple_finance_data.json'
    if not os.path.exists(data_file):
        # 创建初始数据结构
        initial_data = {
            "customers": [],
            "orders": [],
            "income": [],
            "expenses": [],
            "bank_transactions": [],
            "suppliers": [],
            "settings": {
                "company_name": "氧化加工厂",
                "currency": "¥",
                "created_at": str(datetime.now())
            },
            "last_updated": str(datetime.now())
        }
        
        with open(data_file, 'w', encoding='utf-8') as f:
            json.dump(initial_data, f, ensure_ascii=False, indent=2, default=str)
        print("   ✅ 创建初始数据文件")
    else:
        print("   ℹ️  数据文件已存在")
    
    # 4. 验证系统组件
    print("\n4. 验证系统组件...")
    try:
        # 验证核心模块
        sys.path.insert(0, 'oxidation_finance_v20')
        from utils.config import get_db_path
        print("   ✅ 核心配置模块验证通过")
        
        # 验证工具模块
        from tools.小白财务助手 import SimpleFinanceHelper
        print("   ✅ 小白财务助手模块验证通过")
        
    except ImportError as e:
        print(f"   ⚠️  模块验证警告: {e}")
    
    # 5. 创建启动快捷方式
    print("\n5. 创建系统快捷方式...")
    with open('启动财务系统.bat', 'w', encoding='utf-8') as f:
        f.write('@echo off\n')
        f.write('cd /d "%~dp0"\n')
        f.write('call "启动CWZS.bat"\n')
    print("   ✅ 创建启动快捷方式")
    
    # 6. 系统信息输出
    print("\n" + "="*50)
    print("🎉 系统初始化完成！")
    print("\n系统信息:")
    print(f"   工作目录: {os.getcwd()}")
    print(f"   Python版本: {sys.version.split()[0]}")
    print(f"   初始化时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    print("\n推荐使用步骤:")
    print("1. 双击 启动CWZS.bat 启动系统")
    print("2. 首次使用建议生成学习数据")
    print("3. 熟悉操作后可录入真实业务数据")
    
    print("\n技术支持:")
    print("   • 查看 docs/ 目录下的使用文档")
    print("   • 遇到问题可重新初始化系统")
    print("   • 定期备份 data/ 目录下的数据文件")

if __name__ == "__main__":
    try:
        initialize_system()
    except Exception as e:
        print(f"\n❌ 初始化过程出错: {e}")
        print("💡 请检查系统环境和权限设置")
    finally:
        input("\n按任意键退出...")