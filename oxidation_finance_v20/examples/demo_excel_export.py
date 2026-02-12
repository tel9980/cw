#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
演示Excel导出功能

这个脚本展示如何使用报表导出功能：
1. 生成示例报表数据
2. 导出为Excel格式
3. 提供报表模板和示例数据
"""

import sys
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from oxidation_finance_v20.reports.report_templates import ReportTemplates
from oxidation_finance_v20.reports.excel_exporter import ExcelExporter


def demo_export_individual_reports():
    """演示导出单个报表"""
    print("=" * 60)
    print("演示1: 导出单个报表")
    print("=" * 60)
    
    exporter = ExcelExporter()
    output_dir = Path("output_reports")
    output_dir.mkdir(exist_ok=True)
    
    # 1. 导出资产负债表
    print("\n1. 导出资产负债表...")
    balance_sheet_data = ReportTemplates.get_sample_balance_sheet()
    balance_file = output_dir / "资产负债表_示例.xlsx"
    exporter.export_balance_sheet(balance_sheet_data, str(balance_file))
    print(f"   ✓ 已生成: {balance_file}")
    
    # 2. 导出利润表
    print("\n2. 导出利润表...")
    income_data = ReportTemplates.get_sample_income_statement()
    income_file = output_dir / "利润表_示例.xlsx"
    exporter.export_income_statement(income_data, str(income_file))
    print(f"   ✓ 已生成: {income_file}")
    
    # 3. 导出现金流量表
    print("\n3. 导出现金流量表...")
    cash_flow_data = ReportTemplates.get_sample_cash_flow_statement()
    cash_flow_file = output_dir / "现金流量表_示例.xlsx"
    exporter.export_cash_flow_statement(cash_flow_data, str(cash_flow_file))
    print(f"   ✓ 已生成: {cash_flow_file}")
    
    # 4. 导出业务分析报告
    print("\n4. 导出业务分析报告...")
    analysis_data = ReportTemplates.get_sample_business_analysis()
    analysis_file = output_dir / "业务分析报告_示例.xlsx"
    exporter.export_business_analysis(analysis_data, str(analysis_file))
    print(f"   ✓ 已生成: {analysis_file}")
    print(f"   (包含4个工作表: 关键指标、客户分析、计价方式分析、成本分析)")


def demo_generate_all_samples():
    """演示一键生成所有示例报表"""
    print("\n" + "=" * 60)
    print("演示2: 一键生成所有示例报表")
    print("=" * 60)
    
    output_dir = Path("sample_reports")
    output_dir.mkdir(exist_ok=True)
    
    print(f"\n正在生成示例报表到目录: {output_dir}")
    file_paths = ReportTemplates.generate_sample_excel_reports(str(output_dir))
    
    print("\n已生成以下示例报表:")
    for report_type, file_path in file_paths.items():
        print(f"  ✓ {report_type}: {file_path}")


def demo_report_data_structure():
    """演示报表数据结构"""
    print("\n" + "=" * 60)
    print("演示3: 报表数据结构说明")
    print("=" * 60)
    
    print("\n资产负债表数据结构:")
    print("-" * 40)
    balance_sheet = ReportTemplates.get_sample_balance_sheet()
    print(f"  报表名称: {balance_sheet['report_name']}")
    print(f"  报表日期: {balance_sheet['report_date']}")
    print(f"  总资产: {balance_sheet['assets']['total_assets']}")
    print(f"  总负债: {balance_sheet['liabilities']['total_liabilities']}")
    print(f"  所有者权益: {balance_sheet['equity']['total_equity']}")
    print(f"  是否平衡: {balance_sheet['balance_check']['is_balanced']}")
    
    print("\n利润表数据结构:")
    print("-" * 40)
    income_statement = ReportTemplates.get_sample_income_statement()
    print(f"  报表名称: {income_statement['report_name']}")
    print(f"  期间: {income_statement['period']['start_date']} 至 {income_statement['period']['end_date']}")
    print(f"  营业收入: {income_statement['revenue']['operating_revenue']}")
    print(f"  营业成本: {income_statement['cost_of_goods_sold']['total']}")
    print(f"  毛利润: {income_statement['gross_profit']['amount']}")
    print(f"  净利润: {income_statement['net_profit']['amount']}")
    print(f"  利润率: {income_statement['net_profit']['margin_percent']}%")
    
    print("\n现金流量表数据结构:")
    print("-" * 40)
    cash_flow = ReportTemplates.get_sample_cash_flow_statement()
    print(f"  报表名称: {cash_flow['report_name']}")
    print(f"  经营活动现金流入: {cash_flow['operating_activities']['cash_inflow']}")
    print(f"  经营活动现金流出: {cash_flow['operating_activities']['cash_outflow']}")
    print(f"  经营活动净现金流: {cash_flow['operating_activities']['net_cash_flow']}")
    print(f"  期初现金余额: {cash_flow['cash_balance']['beginning_balance']}")
    print(f"  期末现金余额: {cash_flow['cash_balance']['ending_balance']}")


def main():
    """主函数"""
    print("\n" + "=" * 60)
    print("氧化加工厂财务系统 - Excel报表导出功能演示")
    print("=" * 60)
    
    try:
        # 演示1: 导出单个报表
        demo_export_individual_reports()
        
        # 演示2: 一键生成所有示例报表
        demo_generate_all_samples()
        
        # 演示3: 报表数据结构说明
        demo_report_data_structure()
        
        print("\n" + "=" * 60)
        print("演示完成!")
        print("=" * 60)
        print("\n提示:")
        print("  1. 所有报表已导出为Excel格式(.xlsx)")
        print("  2. 报表包含专业格式和样式")
        print("  3. 可以直接在Excel中打开查看和编辑")
        print("  4. 示例数据可作为模板参考")
        print("\n生成的文件位置:")
        print("  - output_reports/  (单个报表示例)")
        print("  - sample_reports/  (完整示例报表集)")
        
    except Exception as e:
        print(f"\n错误: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    return 0


if __name__ == '__main__':
    sys.exit(main())
