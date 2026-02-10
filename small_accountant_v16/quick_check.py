"""
快速检查脚本

显示系统当前状态和待办事项
适合每天早上打开查看

使用方法：
    python quick_check.py
"""

import sys
from pathlib import Path
from datetime import date, datetime, timedelta
from dateutil.relativedelta import relativedelta

# 添加项目根目录到路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from storage.transaction_storage import TransactionStorage
from storage.counterparty_storage import CounterpartyStorage
from storage.reminder_storage import ReminderStorage
from config.config_manager import ConfigManager


def print_header(title):
    """打印标题"""
    print()
    print("=" * 60)
    print(f"  {title}")
    print("=" * 60)
    print()


def print_section(title):
    """打印小节标题"""
    print()
    print(f"📊 {title}")
    print("-" * 60)


def check_system_status():
    """检查系统状态"""
    
    print_header("小会计 - 系统状态检查")
    print(f"检查时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # 初始化
    try:
        config_manager = ConfigManager()
        config = config_manager.get_config()
        
        transaction_storage = TransactionStorage(config.storage.data_dir)
        counterparty_storage = CounterpartyStorage(config.storage.data_dir)
        reminder_storage = ReminderStorage(config.storage.data_dir)
    except Exception as e:
        print(f"❌ 初始化失败：{e}")
        return
    
    # 1. 数据统计
    print_section("数据统计")
    
    try:
        all_transactions = transaction_storage.get_all()
        all_counterparties = counterparty_storage.get_all()
        all_reminders = reminder_storage.get_all()
        
        print(f"  交易记录：{len(all_transactions)} 笔")
        print(f"  往来单位：{len(all_counterparties)} 个")
        print(f"  提醒事项：{len(all_reminders)} 条")
    except Exception as e:
        print(f"  ❌ 获取数据失败：{e}")
    
    # 2. 本月收支
    print_section("本月收支汇总")
    
    try:
        today = date.today()
        month_start = today.replace(day=1)
        month_end = (month_start + relativedelta(months=1)) - timedelta(days=1)
        
        month_transactions = transaction_storage.get_by_date_range(month_start, month_end)
        
        income = sum(t.amount for t in month_transactions if t.transaction_type == "收入")
        expense = sum(t.amount for t in month_transactions if t.transaction_type == "支出")
        profit = income - expense
        
        print(f"  本月期间：{month_start} 至 {month_end}")
        print(f"  收入：¥{income:,.2f}")
        print(f"  支出：¥{expense:,.2f}")
        print(f"  利润：¥{profit:,.2f}")
        print(f"  交易笔数：{len(month_transactions)} 笔")
    except Exception as e:
        print(f"  ❌ 计算失败：{e}")
    
    # 3. 应收账款
    print_section("应收账款（前5名）")
    
    try:
        receivables = {}
        for t in all_transactions:
            if t.transaction_type == "收入" and t.status != "已完成":
                counterparty = t.counterparty_name
                receivables[counterparty] = receivables.get(counterparty, 0) + t.amount
        
        if receivables:
            sorted_receivables = sorted(receivables.items(), key=lambda x: x[1], reverse=True)[:5]
            for i, (name, amount) in enumerate(sorted_receivables, 1):
                print(f"  {i}. {name}: ¥{amount:,.2f}")
            
            total_receivable = sum(receivables.values())
            print(f"  ---")
            print(f"  应收账款总计：¥{total_receivable:,.2f}")
        else:
            print(f"  ✓ 无应收账款")
    except Exception as e:
        print(f"  ❌ 计算失败：{e}")
    
    # 4. 应付账款
    print_section("应付账款（前5名）")
    
    try:
        payables = {}
        for t in all_transactions:
            if t.transaction_type == "支出" and t.status != "已完成":
                counterparty = t.counterparty_name
                payables[counterparty] = payables.get(counterparty, 0) + t.amount
        
        if payables:
            sorted_payables = sorted(payables.items(), key=lambda x: x[1], reverse=True)[:5]
            for i, (name, amount) in enumerate(sorted_payables, 1):
                print(f"  {i}. {name}: ¥{amount:,.2f}")
            
            total_payable = sum(payables.values())
            print(f"  ---")
            print(f"  应付账款总计：¥{total_payable:,.2f}")
        else:
            print(f"  ✓ 无应付账款")
    except Exception as e:
        print(f"  ❌ 计算失败：{e}")
    
    # 5. 近期提醒
    print_section("近期提醒（未来7天）")
    
    try:
        today = date.today()
        next_week = today + timedelta(days=7)
        
        upcoming_reminders = [
            r for r in all_reminders 
            if r.reminder_date and today <= r.reminder_date <= next_week and not r.is_completed
        ]
        
        if upcoming_reminders:
            upcoming_reminders.sort(key=lambda x: x.reminder_date)
            for r in upcoming_reminders[:5]:
                days_left = (r.reminder_date - today).days
                if days_left == 0:
                    time_str = "今天"
                elif days_left == 1:
                    time_str = "明天"
                else:
                    time_str = f"{days_left}天后"
                print(f"  • {time_str} - {r.title}")
        else:
            print(f"  ✓ 未来7天无提醒事项")
    except Exception as e:
        print(f"  ❌ 获取失败：{e}")
    
    # 6. 系统健康
    print_section("系统健康")
    
    try:
        # 检查数据目录
        data_dir = Path(config.storage.data_dir)
        if data_dir.exists():
            print(f"  ✓ 数据目录正常")
        else:
            print(f"  ⚠ 数据目录不存在")
        
        # 检查配置文件
        config_file = Path("config.json")
        if config_file.exists():
            print(f"  ✓ 配置文件正常")
        else:
            print(f"  ⚠ 配置文件不存在")
        
        # 检查最后备份时间（假设备份文件夹以"备份_"开头）
        backup_dirs = sorted([d for d in Path(".").iterdir() if d.is_dir() and d.name.startswith("备份_")])
        if backup_dirs:
            last_backup = backup_dirs[-1].name
            print(f"  ✓ 最后备份：{last_backup}")
        else:
            print(f"  ⚠ 未找到备份（建议立即备份）")
        
    except Exception as e:
        print(f"  ❌ 检查失败：{e}")
    
    # 7. 下一步建议
    print_section("下一步建议")
    
    print(f"  1. 记录今天的收支流水")
    print(f"  2. 整理今天的发票单据")
    
    if receivables:
        print(f"  3. 跟进应收账款催收")
    
    if payables:
        print(f"  4. 安排应付账款支付")
    
    # 检查是否需要生成月度报表
    if today.day <= 5:
        print(f"  5. 生成上月月度报表（双击"生成月度报表.bat"）")
    
    # 检查是否需要备份
    if not backup_dirs or (datetime.now() - datetime.fromtimestamp(backup_dirs[-1].stat().st_mtime)).days > 7:
        print(f"  6. 备份数据（双击"数据备份.bat"）")
    
    print()
    print("=" * 60)
    print("✅ 检查完成！")
    print("=" * 60)
    print()


def main():
    """主函数"""
    try:
        check_system_status()
    except KeyboardInterrupt:
        print()
        print("操作已取消")
        sys.exit(0)
    except Exception as e:
        print(f"❌ 错误：{e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
