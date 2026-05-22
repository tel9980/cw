#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试一键初始化功能
非交互式测试脚本
"""

import sys
import subprocess
from pathlib import Path


def print_banner(title):
    print("\n" + "=" * 70)
    print(f"  {title}")
    print("=" * 70)


def test_python_version():
    print_banner("🧪 测试1: Python版本检查")
    required_version = (3, 8)
    current_version = sys.version_info
    
    if current_version >= required_version:
        print(f"  ✅ Python版本: {current_version.major}.{current_version.minor}.{current_version.micro}")
        return True
    else:
        print(f"  ❌ Python版本过低")
        return False


def test_dependencies():
    print_banner("🧪 测试2: 依赖包检查")
    
    try:
        import flask
        print("  ✅ Flask已安装")
    except ImportError:
        print("  ⚠️  Flask未安装，正在安装...")
        subprocess.run([sys.executable, "-m", "pip", "install", "flask"], capture_output=True)
        try:
            import flask
            print("  ✅ Flask安装成功")
        except:
            print("  ❌ Flask安装失败")
            return False
    
    # 检查其他关键依赖
    dependencies = ['decimal', 'datetime', 'json']
    for dep in dependencies:
        try:
            __import__(dep)
            print(f"  ✅ {dep}可用")
        except:
            print(f"  ❌ {dep}不可用")
            return False
    
    return True


def test_demo_data_generation():
    print_banner("🧪 测试3: 演示数据生成")
    
    demo_script = Path(__file__).parent / "examples" / "generate_small_business_demo.py"
    db_path = Path(__file__).parent / "oxidation_finance_demo_ready.db"
    
    # 先备份现有数据库
    if db_path.exists():
        backup_path = Path(__file__).parent / "oxidation_finance_demo_ready.db.backup_test"
        import shutil
        shutil.copy(db_path, backup_path)
        print(f"  ℹ️  已备份现有数据库到: {backup_path.name}")
    
    # 删除现有数据库以测试重新生成
    if db_path.exists():
        import os
        os.remove(db_path)
        print("  ℹ️  已删除现有数据库")
    
    # 运行演示数据生成
    try:
        result = subprocess.run(
            [sys.executable, str(demo_script)],
            cwd=str(Path(__file__).parent),
            capture_output=False,
            timeout=120
        )
        
        if result.returncode == 0:
            print("  ✅ 演示数据生成成功")
        else:
            print(f"  ❌ 演示数据生成失败 (返回码: {result.returncode})")
            return False
            
    except Exception as e:
        print(f"  ❌ 生成演示数据出错: {e}")
        return False
    
    # 验证数据库
    if db_path.exists():
        size_mb = db_path.stat().st_size / 1024 / 1024
        print(f"  ✅ 数据库已生成: {db_path.name} ({size_mb:.2f} MB)")
        
        # 简单验证数据库内容
        import sqlite3
        conn = sqlite3.connect(str(db_path))
        cursor = conn.cursor()
        
        # 检查客户数量
        cursor.execute("SELECT COUNT(*) FROM customers")
        customer_count = cursor.fetchone()[0]
        print(f"  ✅ 客户数: {customer_count}")
        
        # 检查订单数量
        cursor.execute("SELECT COUNT(*) FROM processing_orders")
        order_count = cursor.fetchone()[0]
        print(f"  ✅ 订单数: {order_count}")
        
        # 检查收入记录
        cursor.execute("SELECT COUNT(*) FROM incomes")
        income_count = cursor.fetchone()[0]
        print(f"  ✅ 收入记录: {income_count}")
        
        # 检查支出记录
        cursor.execute("SELECT COUNT(*) FROM expenses")
        expense_count = cursor.fetchone()[0]
        print(f"  ✅ 支出记录: {expense_count}")
        
        conn.close()
        
        if customer_count > 0 and order_count > 0:
            return True
        else:
            print("  ❌ 数据库内容不完整")
            return False
    else:
        print("  ❌ 数据库文件未生成")
        return False


def main():
    print_banner("🏭 氧化加工厂财务系统 - 一键初始化测试")
    
    all_passed = True
    
    if not test_python_version():
        all_passed = False
    
    if not test_dependencies():
        all_passed = False
    
    if not test_demo_data_generation():
        all_passed = False
    
    # 总结
    print_banner("📊 测试总结")
    
    if all_passed:
        print("  🎉 所有测试通过！")
        print("\n  📖 使用方法:")
        print("    python init.py    - 一键初始化系统")
        print("    python web_app.py  - 启动Web应用")
        print("    ./start.sh         - 快速启动（Linux/Mac）")
        print("    start.bat          - 快速启动（Windows）")
    else:
        print("  ❌ 部分测试失败，请检查错误信息")
    
    print("=" * 70)
    return 0 if all_passed else 1


if __name__ == "__main__":
    sys.exit(main())
