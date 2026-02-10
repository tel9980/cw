"""
一键生成月度报表

快捷脚本，自动生成当月的所有常用报表
适合小企业每月例行财务工作

使用方法：
    python quick_monthly_report.py
    python quick_monthly_report.py --month 2026-01  # 指定月份
"""

import sys
import os
from pathlib import Path
from datetime import date, datetime
from dateutil.relativedelta import relativedelta
import argparse

# 添加项目根目录到路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from reports.report_generator import ReportGenerator
from storage.transaction_storage import TransactionStorage
from storage.counterparty_storage import CounterpartyStorage
from config.config_manager import ConfigManager


def parse_month(month_str):
    """解析月份字符串"""
    try:
        return datetime.strptime(month_str, "%Y-%m").date()
    except ValueError:
        print(f"❌ 月份格式错误：{month_str}")
        print("正确格式：YYYY-MM，例如：2026-01")
        sys.exit(1)


def get_month_range(month_date):
    """获取月份的开始和结束日期"""
    start_date = month_date.replace(day=1)
    # 下个月的第一天减一天 = 本月最后一天
    next_month = start_date + relativedelta(months=1)
    end_date = next_month - relativedelta(days=1)
    return start_date, end_date


def generate_monthly_reports(month_str=None):
    """生成月度报表"""
    
    # 确定月份
    if month_str:
        month_date = parse_month(month_str)
    else:
        # 默认上个月
        today = date.today()
        month_date = (today.replace(day=1) - relativedelta(days=1)).replace(day=1)
    
    start_date, end_date = get_month_range(month_date)
    month_name = month_date.strftime("%Y年%m月")
    
    print("=" * 60)
    print(f"📊 一键生成月度报表 - {month_name}")
    print("=" * 60)
    print()
    print(f"报表期间：{start_date} 至 {end_date}")
    print()
    
    # 初始化
    config_manager = ConfigManager()
    config = config_manager.get_config()
    
    transaction_storage = TransactionStorage(config.storage.data_dir)
    counterparty_storage = CounterpartyStorage(config.storage.data_dir)
    
    report_generator = ReportGenerator(
        transaction_storage=transaction_storage,
        counterparty_storage=counterparty_storage,
        output_dir=config.storage.report_output_dir
    )
    
    # 检查数据
    transactions = transaction_storage.get_by_date_range(start_date, end_date)
    if not transactions:
        print(f"⚠️  {month_name}没有交易记录")
        print()
        print("请先导入数据或选择其他月份")
        return
    
    print(f"✓ 找到 {len(transactions)} 笔交易记录")
    print()
    
    # 生成报表
    reports_generated = []
    
    try:
        # 1. 管理报表
        print("正在生成管理报表...")
        result = report_generator.generate_management_report(start_date, end_date)
        if result.success:
            reports_generated.append(("管理报表", result.file_path))
            print(f"  ✓ {result.file_path}")
        else:
            print(f"  ✗ 失败：{result.error_message}")
        print()
        
        # 2. 税务报表（增值税）
        print("正在生成增值税申报表...")
        result = report_generator.generate_tax_report(
            start_date, end_date, 
            report_type="vat"
        )
        if result.success:
            reports_generated.append(("增值税申报表", result.file_path))
            print(f"  ✓ {result.file_path}")
        else:
            print(f"  ✗ 失败：{result.error_message}")
        print()
        
        # 3. 税务报表（所得税）
        print("正在生成所得税申报表...")
        result = report_generator.generate_tax_report(
            start_date, end_date,
            report_type="income_tax"
        )
        if result.success:
            reports_generated.append(("所得税申报表", result.file_path))
            print(f"  ✓ {result.file_path}")
        else:
            print(f"  ✗ 失败：{result.error_message}")
        print()
        
        # 4. 银行贷款报表
        print("正在生成银行贷款报表...")
        result = report_generator.generate_bank_loan_report(start_date, end_date)
        if result.success:
            reports_generated.append(("银行贷款报表", result.file_path))
            print(f"  ✓ {result.file_path}")
        else:
            print(f"  ✗ 失败：{result.error_message}")
        print()
        
    except Exception as e:
        print(f"❌ 生成报表时出错：{e}")
        return
    
    # 总结
    print("=" * 60)
    print(f"✅ 月度报表生成完成！")
    print("=" * 60)
    print()
    print(f"生成了 {len(reports_generated)} 个报表：")
    for name, path in reports_generated:
        print(f"  • {name}")
        print(f"    {path}")
    print()
    print("💡 提示：")
    print("  - 报表已保存到 reports/ 目录")
    print("  - 可以直接用Excel打开查看")
    print("  - 建议每月备份报表文件")
    print()


def main():
    """主函数"""
    parser = argparse.ArgumentParser(
        description="一键生成月度报表",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例：
  python quick_monthly_report.py              # 生成上个月报表
  python quick_monthly_report.py --month 2026-01  # 生成指定月份报表
  python quick_monthly_report.py --month 2025-12  # 生成2025年12月报表
        """
    )
    
    parser.add_argument(
        '--month', '-m',
        help='指定月份（格式：YYYY-MM），默认为上个月',
        metavar='YYYY-MM'
    )
    
    args = parser.parse_args()
    
    try:
        generate_monthly_reports(args.month)
    except KeyboardInterrupt:
        print()
        print("操作已取消")
        sys.exit(0)
    except Exception as e:
        print(f"❌ 错误：{e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
