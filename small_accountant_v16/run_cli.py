#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
V1.6 小会计实用增强版 - 启动脚本

使用方法：
    python run_cli.py              # 启动CLI界面
    python run_cli.py --status     # 查看系统状态
    python run_cli.py --verify     # 验证数据完整性
    python run_cli.py --help       # 显示帮助信息
"""

import sys
import os
import argparse
import logging
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from small_accountant_v16.ui.cli import SmallAccountantCLI
from small_accountant_v16.config import ConfigManager
from small_accountant_v16.storage import (
    TransactionStorage,
    CounterpartyStorage,
    ReminderStorage
)


def setup_logging():
    """设置日志"""
    log_dir = Path("logs")
    log_dir.mkdir(exist_ok=True)
    
    from datetime import datetime
    log_file = log_dir / f"small_accountant_{datetime.now().strftime('%Y%m%d')}.log"
    
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_file, encoding='utf-8'),
            logging.StreamHandler()
        ]
    )


def check_system_status():
    """检查系统状态"""
    print("=" * 60)
    print("V1.6 小会计实用增强版 - 系统状态")
    print("=" * 60)
    
    # 检查配置
    config_manager = ConfigManager()
    print(f"\n✅ 配置文件: {config_manager.config_file}")
    
    # 检查数据目录
    data_dir = Path(config_manager.config.storage.data_dir)
    print(f"✅ 数据目录: {data_dir}")
    print(f"   - 存在: {data_dir.exists()}")
    
    # 检查数据文件
    transaction_file = data_dir / "transactions.json"
    counterparty_file = data_dir / "counterparties.json"
    reminder_file = data_dir / "reminders.json"
    
    print(f"\n📊 数据文件:")
    print(f"   - 交易记录: {transaction_file.exists()} ({transaction_file})")
    print(f"   - 往来单位: {counterparty_file.exists()} ({counterparty_file})")
    print(f"   - 提醒事项: {reminder_file.exists()} ({reminder_file})")
    
    # 统计数据
    if transaction_file.exists():
        transaction_storage = TransactionStorage(str(data_dir))
        transactions = transaction_storage.get_all()
        print(f"\n📈 数据统计:")
        print(f"   - 交易记录: {len(transactions)} 条")
    
    if counterparty_file.exists():
        counterparty_storage = CounterpartyStorage(str(data_dir))
        counterparties = counterparty_storage.get_all()
        print(f"   - 往来单位: {len(counterparties)} 个")
    
    if reminder_file.exists():
        reminder_storage = ReminderStorage(str(data_dir))
        reminders = reminder_storage.get_all()
        print(f"   - 提醒事项: {len(reminders)} 条")
    
    # 检查报表目录
    report_dir = Path(config_manager.config.storage.report_output_dir)
    print(f"\n📁 报表目录: {report_dir}")
    print(f"   - 存在: {report_dir.exists()}")
    if report_dir.exists():
        reports = list(report_dir.glob("*.xlsx"))
        print(f"   - 报表数量: {len(reports)} 个")
    
    print("\n" + "=" * 60)


def verify_data_integrity():
    """验证数据完整性"""
    print("=" * 60)
    print("V1.6 小会计实用增强版 - 数据完整性验证")
    print("=" * 60)
    
    config_manager = ConfigManager()
    data_dir = Path(config_manager.config.storage.data_dir)
    
    errors = []
    warnings = []
    
    # 验证交易记录
    print("\n🔍 验证交易记录...")
    try:
        transaction_storage = TransactionStorage(str(data_dir))
        transactions = transaction_storage.get_all()
        print(f"   ✅ 成功加载 {len(transactions)} 条交易记录")
        
        # 检查数据完整性
        for txn in transactions:
            if not txn.id:
                errors.append(f"交易记录缺少ID: {txn}")
            if not txn.date:
                errors.append(f"交易记录缺少日期: {txn.id}")
            if txn.amount <= 0:
                warnings.append(f"交易记录金额异常: {txn.id} - {txn.amount}")
    
    except Exception as e:
        errors.append(f"交易记录验证失败: {e}")
    
    # 验证往来单位
    print("\n🔍 验证往来单位...")
    try:
        counterparty_storage = CounterpartyStorage(str(data_dir))
        counterparties = counterparty_storage.get_all()
        print(f"   ✅ 成功加载 {len(counterparties)} 个往来单位")
        
        # 检查数据完整性
        for cp in counterparties:
            if not cp.id:
                errors.append(f"往来单位缺少ID: {cp}")
            if not cp.name:
                errors.append(f"往来单位缺少名称: {cp.id}")
    
    except Exception as e:
        errors.append(f"往来单位验证失败: {e}")
    
    # 验证提醒事项
    print("\n🔍 验证提醒事项...")
    try:
        reminder_storage = ReminderStorage(str(data_dir))
        reminders = reminder_storage.get_all()
        print(f"   ✅ 成功加载 {len(reminders)} 条提醒事项")
    
    except Exception as e:
        errors.append(f"提醒事项验证失败: {e}")
    
    # 输出结果
    print("\n" + "=" * 60)
    print("验证结果:")
    print("=" * 60)
    
    if not errors and not warnings:
        print("✅ 数据完整性验证通过，未发现问题")
    else:
        if errors:
            print(f"\n❌ 发现 {len(errors)} 个错误:")
            for error in errors:
                print(f"   - {error}")
        
        if warnings:
            print(f"\n⚠️  发现 {len(warnings)} 个警告:")
            for warning in warnings:
                print(f"   - {warning}")
    
    print("\n" + "=" * 60)


def main():
    """主函数"""
    parser = argparse.ArgumentParser(
        description="V1.6 小会计实用增强版",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  python run_cli.py              启动CLI界面
  python run_cli.py --status     查看系统状态
  python run_cli.py --verify     验证数据完整性
  python run_cli.py --help       显示帮助信息
        """
    )
    
    parser.add_argument(
        '--status',
        action='store_true',
        help='查看系统状态'
    )
    
    parser.add_argument(
        '--verify',
        action='store_true',
        help='验证数据完整性'
    )
    
    parser.add_argument(
        '--debug',
        action='store_true',
        help='启用调试模式'
    )
    
    args = parser.parse_args()
    
    # 设置日志
    setup_logging()
    
    if args.debug:
        logging.getLogger().setLevel(logging.DEBUG)
    
    # 处理命令
    if args.status:
        check_system_status()
        return
    
    if args.verify:
        verify_data_integrity()
        return
    
    # 默认启动CLI
    try:
        cli = SmallAccountantCLI()
        cli.run()
    except KeyboardInterrupt:
        print("\n\n👋 感谢使用！再见！")
    except Exception as e:
        logging.error(f"系统运行错误: {e}", exc_info=True)
        print(f"\n❌ 系统运行错误: {e}")
        print("请查看日志文件获取详细信息")
        sys.exit(1)


if __name__ == "__main__":
    main()
