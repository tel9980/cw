#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
CWZS系统落地测试验证脚本
全面验证系统功能和稳定性
"""

import os
import sys
import json
import subprocess
from datetime import datetime

def run_test(test_name, test_func):
    """运行单个测试"""
    print(f"\n🧪 正在运行测试: {test_name}")
    print("-" * 50)
    try:
        result = test_func()
        if result:
            print(f"✅ {test_name} - 测试通过")
            return True
        else:
            print(f"❌ {test_name} - 测试失败")
            return False
    except Exception as e:
        print(f"❌ {test_name} - 测试异常: {e}")
        return False

def test_python_environment():
    """测试Python环境"""
    try:
        # 检查Python版本
        version = sys.version_info
        if version.major >= 3 and version.minor >= 8:
            print(f"✅ Python版本: {version.major}.{version.minor}.{version.micro}")
        else:
            print(f"⚠️  Python版本较低: {version.major}.{version.minor}.{version.micro}")
            return False
        
        # 检查基本模块
        import json
        import os
        import datetime
        print("✅ 基础模块导入正常")
        
        return True
    except Exception as e:
        print(f"❌ Python环境异常: {e}")
        return False

def test_project_structure():
    """测试项目结构完整性"""
    required_files = [
        '一键部署.bat',
        '启动CWZS.bat',
        'initialize_system.py',
        '.env.example',
        'oxidation_finance_v20/web_app.py',
        'oxidation_finance_v20/tools/小白财务助手.py'
    ]
    
    required_dirs = [
        'oxidation_finance_v20',
        'docs',
        'requirements'
    ]
    
    missing_files = []
    missing_dirs = []
    
    for file_path in required_files:
        if not os.path.exists(file_path):
            missing_files.append(file_path)
    
    for dir_path in required_dirs:
        if not os.path.exists(dir_path):
            missing_dirs.append(dir_path)
    
    if missing_files:
        print(f"❌ 缺少文件: {missing_files}")
        return False
    
    if missing_dirs:
        print(f"❌ 缺少目录: {missing_dirs}")
        return False
    
    print("✅ 项目结构完整")
    return True

def test_core_modules():
    """测试核心模块导入"""
    try:
        # 添加项目路径
        sys.path.insert(0, 'oxidation_finance_v20')
        
        # 测试配置模块
        from utils.config import get_db_path
        print("✅ 配置模块导入成功")
        
        # 测试工具模块
        from tools.小白财务助手 import SimpleFinanceHelper
        print("✅ 小白财务助手模块导入成功")
        
        # 测试Web模块（容错处理）
        try:
            from web_app import app
            print("✅ Web应用模块导入成功")
        except ImportError as e:
            print(f"⚠️  Web模块导入警告: {e}")
        
        return True
    except Exception as e:
        print(f"❌ 核心模块测试失败: {e}")
        return False

def test_data_initialization():
    """测试数据初始化"""
    try:
        # 运行初始化脚本
        result = subprocess.run([
            sys.executable, 'initialize_system.py'
        ], capture_output=True, text=True, timeout=30)
        
        if result.returncode == 0:
            print("✅ 系统初始化脚本运行成功")
            
            # 检查创建的目录
            required_dirs = ['data', 'logs', 'temp', 'cache']
            for directory in required_dirs:
                if os.path.exists(directory):
                    print(f"   ✅ 目录创建成功: {directory}")
                else:
                    print(f"   ⚠️  目录缺失: {directory}")
            
            # 检查数据文件
            data_file = 'oxidation_finance_v20/simple_finance_data.json'
            if os.path.exists(data_file):
                print("✅ 数据文件创建成功")
                # 验证JSON格式
                with open(data_file, 'r', encoding='utf-8') as f:
                    json.load(f)
                print("✅ 数据文件格式正确")
            else:
                print("⚠️  数据文件未创建")
            
            return True
        else:
            print(f"❌ 初始化脚本执行失败: {result.stderr}")
            return False
            
    except subprocess.TimeoutExpired:
        print("❌ 初始化脚本执行超时")
        return False
    except Exception as e:
        print(f"❌ 数据初始化测试异常: {e}")
        return False

def test_batch_scripts():
    """测试批处理脚本"""
    batch_scripts = [
        ('一键部署.bat', '部署脚本'),
        ('启动CWZS.bat', '启动脚本')
    ]
    
    results = []
    for script_name, description in batch_scripts:
        if os.path.exists(script_name):
            print(f"✅ {description}存在: {script_name}")
            # 简单语法检查
            with open(script_name, 'r', encoding='utf-8') as f:
                content = f.read()
                if '@echo off' in content and 'chcp 65001' in content:
                    print(f"   ✅ {description}基本语法正确")
                    results.append(True)
                else:
                    print(f"   ⚠️  {description}可能存在语法问题")
                    results.append(False)
        else:
            print(f"❌ {description}缺失: {script_name}")
            results.append(False)
    
    return all(results)

def test_documentation():
    """测试文档完整性"""
    docs = [
        ('docs/落地使用指南.md', '落地使用指南'),
        ('README.md', '主说明文档'),
        ('README_小白版.md', '小白版说明')
    ]
    
    results = []
    for doc_path, description in docs:
        if os.path.exists(doc_path):
            print(f"✅ {description}存在: {doc_path}")
            # 检查文件大小
            size = os.path.getsize(doc_path)
            if size > 100:  # 至少100字节
                print(f"   ✅ {description}内容充实")
                results.append(True)
            else:
                print(f"   ⚠️  {description}内容可能过少")
                results.append(False)
        else:
            print(f"❌ {description}缺失: {doc_path}")
            results.append(False)
    
    return all(results)

def main():
    """主测试函数"""
    print("🔍 CWZS系统落地测试验证")
    print("="*60)
    print(f"开始时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"工作目录: {os.getcwd()}")
    print()
    
    # 测试列表
    tests = [
        ("Python环境测试", test_python_environment),
        ("项目结构测试", test_project_structure),
        ("核心模块测试", test_core_modules),
        ("数据初始化测试", test_data_initialization),
        ("批处理脚本测试", test_batch_scripts),
        ("文档完整性测试", test_documentation)
    ]
    
    # 运行所有测试
    passed_tests = 0
    total_tests = len(tests)
    
    for test_name, test_func in tests:
        if run_test(test_name, test_func):
            passed_tests += 1
    
    # 输出测试结果
    print("\n" + "="*60)
    print("📊 测试结果汇总")
    print("="*60)
    print(f"总测试数: {total_tests}")
    print(f"通过测试: {passed_tests}")
    print(f"失败测试: {total_tests - passed_tests}")
    print(f"通过率: {(passed_tests/total_tests)*100:.1f}%")
    
    if passed_tests == total_tests:
        print("\n🎉 所有测试通过！系统可以放心使用。")
        print("\n🚀 推荐使用步骤:")
        print("1. 双击 一键部署.bat 完成环境配置")
        print("2. 双击 启动CWZS.bat 开始使用系统")
        print("3. 首次使用建议生成学习数据")
        print("4. 查看 docs/落地使用指南.md 了解更多")
        
        # 创建成功标志文件
        with open('DEPLOYMENT_SUCCESS.txt', 'w', encoding='utf-8') as f:
            f.write(f"CWZS系统部署测试成功\n")
            f.write(f"测试完成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"通过测试: {passed_tests}/{total_tests}\n")
            f.write("系统已准备好投入正常使用！\n")
        
        print("\n✅ 已创建部署成功标志文件: DEPLOYMENT_SUCCESS.txt")
        
    else:
        print(f"\n⚠️  有 {total_tests - passed_tests} 个测试未通过")
        print("💡 建议:")
        print("1. 检查系统环境和依赖")
        print("2. 重新运行 一键部署.bat")
        print("3. 查看具体错误信息进行修复")
    
    print(f"\n结束时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n⚠️  测试被用户中断")
    except Exception as e:
        print(f"\n❌ 测试过程中发生异常: {e}")
    finally:
        input("\n按任意键退出...")