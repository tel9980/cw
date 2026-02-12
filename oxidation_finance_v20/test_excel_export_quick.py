#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
快速测试Excel导出功能
"""

import sys
from pathlib import Path
from decimal import Decimal
from datetime import date

# 添加项目根目录到路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from reports.excel_exporter import ExcelExporter
from reports.report_templates import ReportTemplates


def test_basic_export():
    """测试基本导出功能"""
    print("测试1: 基本导出功能")
    print("-" * 50)
    
    try:
        exporter = ExcelExporter()
        print("✓ ExcelExporter 创建成功")
        
        # 测试格式化值
        assert exporter._format_value(Decimal("100.50")) == 100.50
        assert exporter._format_value(date(2024, 1, 15)) == "2024-01-15"
        assert exporter._format_value(None) == ''
        print("✓ 值格式化功能正常")
        
        return True
    except Exception as e:
        print(f"✗ 错误: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_sample_data():
    """测试示例数据生成"""
    print("\n测试2: 示例数据生成")
    print("-" * 50)
    
    try:
        # 测试资产负债表示例
        balance_sheet = ReportTemplates.get_sample_balance_sheet()
        assert balance_sheet['report_name'] == "资产负债表"
        assert balance_sheet['balance_check']['is_balanced'] is True
        print("✓ 资产负债表示例数据正常")
        
        # 测试利润表示例
        income_statement = ReportTemplates.get_sample_income_statement()
        assert income_statement['report_name'] == "利润表"
        assert 'revenue' in income_statement
        print("✓ 利润表示例数据正常")
        
        # 测试现金流量表示例
        cash_flow = ReportTemplates.get_sample_cash_flow_statement()
        assert cash_flow['report_name'] == "现金流量表"
        assert 'operating_activities' in cash_flow
        print("✓ 现金流量表示例数据正常")
        
        # 测试业务分析报告示例
        business_analysis = ReportTemplates.get_sample_business_analysis()
        assert business_analysis['report_name'] == "业务分析综合报告"
        assert 'key_metrics' in business_analysis
        print("✓ 业务分析报告示例数据正常")
        
        return True
    except Exception as e:
        print(f"✗ 错误: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_export_to_file():
    """测试导出到文件"""
    print("\n测试3: 导出到文件")
    print("-" * 50)
    
    try:
        import tempfile
        import os
        
        exporter = ExcelExporter()
        
        with tempfile.TemporaryDirectory() as tmpdir:
            # 测试导出资产负债表
            balance_file = os.path.join(tmpdir, "test_balance.xlsx")
            balance_data = ReportTemplates.get_sample_balance_sheet()
            result = exporter.export_balance_sheet(balance_data, balance_file)
            assert os.path.exists(result)
            print(f"✓ 资产负债表导出成功: {result}")
            
            # 测试导出利润表
            income_file = os.path.join(tmpdir, "test_income.xlsx")
            income_data = ReportTemplates.get_sample_income_statement()
            result = exporter.export_income_statement(income_data, income_file)
            assert os.path.exists(result)
            print(f"✓ 利润表导出成功: {result}")
            
            # 测试导出现金流量表
            cash_file = os.path.join(tmpdir, "test_cash.xlsx")
            cash_data = ReportTemplates.get_sample_cash_flow_statement()
            result = exporter.export_cash_flow_statement(cash_data, cash_file)
            assert os.path.exists(result)
            print(f"✓ 现金流量表导出成功: {result}")
            
            # 测试导出业务分析报告
            analysis_file = os.path.join(tmpdir, "test_analysis.xlsx")
            analysis_data = ReportTemplates.get_sample_business_analysis()
            result = exporter.export_business_analysis(analysis_data, analysis_file)
            assert os.path.exists(result)
            print(f"✓ 业务分析报告导出成功: {result}")
        
        return True
    except Exception as e:
        print(f"✗ 错误: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_generate_samples():
    """测试生成示例报表"""
    print("\n测试4: 生成示例报表")
    print("-" * 50)
    
    try:
        import tempfile
        import os
        
        with tempfile.TemporaryDirectory() as tmpdir:
            file_paths = ReportTemplates.generate_sample_excel_reports(tmpdir)
            
            assert 'balance_sheet' in file_paths
            assert 'income_statement' in file_paths
            assert 'cash_flow_statement' in file_paths
            assert 'business_analysis' in file_paths
            
            for report_type, file_path in file_paths.items():
                assert os.path.exists(file_path)
                print(f"✓ {report_type}: {file_path}")
        
        return True
    except Exception as e:
        print(f"✗ 错误: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """主函数"""
    print("=" * 60)
    print("Excel导出功能快速测试")
    print("=" * 60)
    
    results = []
    
    # 运行所有测试
    results.append(("基本导出功能", test_basic_export()))
    results.append(("示例数据生成", test_sample_data()))
    results.append(("导出到文件", test_export_to_file()))
    results.append(("生成示例报表", test_generate_samples()))
    
    # 汇总结果
    print("\n" + "=" * 60)
    print("测试结果汇总")
    print("=" * 60)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = "✓ 通过" if result else "✗ 失败"
        print(f"{status}: {test_name}")
    
    print(f"\n总计: {passed}/{total} 测试通过")
    
    if passed == total:
        print("\n✓ 所有测试通过!")
        return 0
    else:
        print(f"\n✗ {total - passed} 个测试失败")
        return 1


if __name__ == '__main__':
    sys.exit(main())
