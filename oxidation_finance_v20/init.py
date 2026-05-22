#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
氧化加工厂财务系统 - 一键初始化脚本
自动完成所有必要的初始化工作
"""

import sys
import subprocess
import time
from pathlib import Path


def print_banner(title):
    """打印标题横幅"""
    print("\n" + "=" * 70)
    print(f"  {title}")
    print("=" * 70)


def check_python_version():
    """检查Python版本"""
    print("\n🔍 检查Python环境...")
    required_version = (3, 8)
    current_version = sys.version_info
    
    if current_version >= required_version:
        print(f"  ✓ Python版本: {current_version.major}.{current_version.minor}.{current_version.micro}")
        return True
    else:
        print(f"  ✗ Python版本过低，需要3.8+，当前版本: {current_version.major}.{current_version.minor}")
        return False


def install_dependencies():
    """安装依赖包"""
    print("\n📦 检查并安装依赖包...")
    requirements_file = Path(__file__).parent / "requirements.txt"
    
    if not requirements_file.exists():
        print(f"  ⚠️  依赖文件不存在: {requirements_file}")
        return False
    
    try:
        print("  正在安装依赖...")
        result = subprocess.run(
            [sys.executable, "-m", "pip", "install", "-r", str(requirements_file)],
            capture_output=True,
            text=True
        )
        
        if result.returncode == 0:
            print("  ✓ 基础依赖安装完成")
        else:
            print(f"  ⚠️  依赖安装可能有问题: {result.stderr}")
        
        # 安装Flask
        print("  安装Flask...")
        subprocess.run(
            [sys.executable, "-m", "pip", "install", "flask"],
            capture_output=True,
            text=True
        )
        print("  ✓ Flask安装完成")
        return True
        
    except Exception as e:
        print(f"  ✗ 安装依赖失败: {e}")
        return False


def generate_demo_data():
    """生成演示数据"""
    print("\n🎲 生成小企业模拟数据...")
    demo_script = Path(__file__).parent / "examples" / "generate_small_business_demo.py"
    
    if not demo_script.exists():
        print(f"  ✗ 演示数据生成脚本不存在: {demo_script}")
        return False
    
    try:
        result = subprocess.run(
            [sys.executable, str(demo_script)],
            cwd=str(Path(__file__).parent),
            capture_output=False
        )
        
        if result.returncode == 0:
            print("  ✓ 演示数据生成完成")
            return True
        else:
            print(f"  ✗ 演示数据生成失败")
            return False
            
    except Exception as e:
        print(f"  ✗ 生成演示数据出错: {e}")
        return False


def verify_database():
    """验证数据库"""
    print("\n✅ 验证数据库...")
    db_path = Path(__file__).parent / "oxidation_finance_demo_ready.db"
    
    if db_path.exists():
        size_mb = db_path.stat().st_size / 1024 / 1024
        print(f"  ✓ 数据库文件存在: {db_path.name} ({size_mb:.2f} MB)")
        return True
    else:
        print(f"  ✗ 数据库文件不存在: {db_path}")
        return False


def print_usage_instructions():
    """打印使用说明"""
    print("\n" + "=" * 70)
    print("  🎉 系统初始化完成！")
    print("=" * 70)
    print("\n📖 使用说明:")
    print("\n1. 启动Web应用:")
    print("   python web_app.py")
    print("\n2. 访问系统:")
    print("   http://localhost:5000")
    print("\n3. 主要功能页面:")
    print("   - 首页仪表盘: http://localhost:5000")
    print("   - 小会计助手: http://localhost:5000/assistant")
    print("   - 订单管理: http://localhost:5000/orders")
    print("   - 客户管理: http://localhost:5000/customers")
    print("   - 报表中心: http://localhost:5000/reports")
    print("\n4. 快速操作:")
    print("   - 快速记录收入: http://localhost:5000/quick-income")
    print("   - 快速记录支出: http://localhost:5000/quick-expense")
    print("\n💡 提示:")
    print("   - 演示数据已包含在 oxidation_finance_demo_ready.db 中")
    print("   - G银行用于有票交易，N银行用于微信/现金交易")
    print("   - 收付款支持非一一对应分配")
    print("=" * 70)


def main():
    """主函数"""
    print_banner("🏭 氧化加工厂财务系统 - 一键初始化")
    
    # 步骤1: 检查Python版本
    if not check_python_version():
        print("\n❌ 初始化失败，请使用Python 3.8或更高版本")
        return
    
    # 步骤2: 安装依赖
    if not install_dependencies():
        print("\n⚠️  依赖安装可能不完整，但继续尝试...")
    
    # 步骤3: 生成演示数据
    if not generate_demo_data():
        print("\n❌ 演示数据生成失败")
        return
    
    # 步骤4: 验证
    if not verify_database():
        print("\n❌ 数据库验证失败")
        return
    
    # 完成
    print_usage_instructions()
    
    # 询问是否立即启动
    print("\n" + "-" * 70)
    response = input("🚀 是否立即启动Web应用? (y/n): ").strip().lower()
    
    if response == 'y':
        print("\n🎯 正在启动Web应用...")
        print("   按 Ctrl+C 停止服务")
        print("-" * 70 + "\n")
        time.sleep(1)
        
        web_app = Path(__file__).parent / "web_app.py"
        subprocess.run([sys.executable, str(web_app)])


if __name__ == "__main__":
    main()
