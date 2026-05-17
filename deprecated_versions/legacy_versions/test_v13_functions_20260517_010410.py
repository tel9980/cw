# -*- coding: utf-8 -*-
"""
测试V1.3全能版的主要功能
"""

import sys
import os

# 添加当前目录到路径
sys.path.insert(0, os.getcwd())

def test_imports():
    """测试模块导入"""
    try:
        from 氧化加工厂财务助手_全能版 import (
            transaction_statistics, bank_statement_management, 
            export_transaction_report, income_tax_calculation,
            tax_report_center, tax_document_archive,
            balance_sheet_report, cash_flow_statement,
            financial_analysis_report, annual_summary,
            voucher_management, contract_management,
            supplier_management, data_cleanup,
            data_backup, data_restore, system_configuration
        )
        print("✅ 所有新增函数导入成功")
        return True
    except ImportError as e:
        print(f"❌ 函数导入失败: {e}")
        return False

def test_financial_manager():
    """测试财务管理器"""
    try:
        from 财务数据管理器 import financial_manager
        
        # 测试基本功能
        transactions = financial_manager.load_transactions()
        print(f"✅ 财务管理器工作正常，当前有 {len(transactions)} 条记录")
        
        # 测试统计功能
        stats = financial_manager.get_transaction_statistics()
        print(f"✅ 统计功能正常，总收入: {stats['total_income']:.2f}元")
        
        return True
    except Exception as e:
        print(f"❌ 财务管理器测试失败: {e}")
        return False

def test_bank_manager():
    """测试银行流水管理器"""
    try:
        from 银行流水管理 import bank_manager
        print("✅ 银行流水管理器导入成功")
        return True
    except Exception as e:
        print(f"❌ 银行流水管理器测试失败: {e}")
        return False

def main():
    """主测试函数"""
    print("=" * 60)
    print("    V1.3全能版功能测试")
    print("=" * 60)
    
    tests = [
        ("模块导入测试", test_imports),
        ("财务管理器测试", test_financial_manager),
        ("银行流水管理器测试", test_bank_manager)
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        print(f"\n🔍 {test_name}...")
        try:
            if test_func():
                passed += 1
            else:
                print(f"❌ {test_name} 失败")
        except Exception as e:
            print(f"❌ {test_name} 异常: {e}")
    
    print(f"\n" + "=" * 60)
    print(f"测试结果: {passed}/{total} 通过")
    
    if passed == total:
        print("🎉 所有测试通过！V1.3全能版功能完整")
    else:
        print("⚠️ 部分测试失败，需要检查相关功能")
    
    print("=" * 60)

if __name__ == "__main__":
    main()