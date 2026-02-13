"""
命令行界面（CLI）模块

提供简单易用的中文命令行界面，支持：
- 报表生成
- 提醒管理
- 对账功能
- 数据导入
"""

import os
import sys
from datetime import date, datetime, timedelta
from typing import Optional, List
from decimal import Decimal

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from small_accountant_v16.config.config_manager import ConfigManager
from small_accountant_v16.storage.transaction_storage import TransactionStorage
from small_accountant_v16.storage.counterparty_storage import CounterpartyStorage
from small_accountant_v16.storage.reminder_storage import ReminderStorage
from small_accountant_v16.storage.import_history import ImportHistory
from small_accountant_v16.reports.report_generator import ReportGenerator
from small_accountant_v16.reminders.reminder_system import ReminderSystem
from small_accountant_v16.reminders.reminder_scheduler import ReminderScheduler
from small_accountant_v16.reconciliation.reconciliation_assistant import ReconciliationAssistant
from small_accountant_v16.import_engine.import_engine import ImportEngine
from small_accountant_v16.models.core_models import (
    ReportType, ReminderType, TransactionType, CounterpartyType
)


class SmallAccountantCLI:
    """小会计命令行界面"""
    
    def __init__(self, storage_dir: str = "data"):
        """初始化CLI"""
        self.storage_dir = storage_dir
        self.config = ConfigManager(storage_dir)
        
        # 初始化存储层
        self.transaction_storage = TransactionStorage(storage_dir)
        self.counterparty_storage = CounterpartyStorage(storage_dir)
        self.reminder_storage = ReminderStorage(storage_dir)
        
        # 初始化功能模块
        reports_dir = os.path.join(storage_dir, "reports")
        self.report_generator = ReportGenerator(
            self.transaction_storage,
            self.counterparty_storage,
            reports_dir
        )
        
        self.reminder_system = ReminderSystem(
            self.transaction_storage,
            self.counterparty_storage,
            self.reminder_storage,
            self.config
        )
        
        self.reminder_scheduler = ReminderScheduler(
            self.reminder_system,
            self.config,
            storage_dir
        )
        
        reconciliation_dir = os.path.join(storage_dir, "reconciliation")
        self.reconciliation_assistant = ReconciliationAssistant(
            self.transaction_storage,
            self.counterparty_storage,
            reconciliation_dir
        )
        
        # 初始化导入历史
        self.import_history = ImportHistory(storage_dir)
        
        self.import_engine = ImportEngine(
            self.transaction_storage,
            self.counterparty_storage,
            self.import_history
        )
    
    def clear_screen(self):
        """清屏"""
        os.system('cls' if os.name == 'nt' else 'clear')
    
    def print_header(self, title: str):
        """打印标题"""
        print("\n" + "=" * 60)
        print(f"  {title}")
        print("=" * 60 + "\n")
    
    def print_menu(self, title: str, options: List[str]):
        """打印菜单"""
        self.print_header(title)
        for i, option in enumerate(options, 1):
            print(f"  {i}. {option}")
        print(f"  0. 返回上级菜单")
        print()
    
    def get_input(self, prompt: str, default: Optional[str] = None) -> str:
        """获取用户输入"""
        if default:
            prompt = f"{prompt} [{default}]"
        value = input(f"{prompt}: ").strip()
        return value if value else (default or "")
    
    def get_date_input(self, prompt: str, default: Optional[date] = None) -> Optional[date]:
        """获取日期输入"""
        default_str = default.strftime("%Y-%m-%d") if default else None
        date_str = self.get_input(prompt, default_str)
        
        if not date_str:
            return None
        
        try:
            return datetime.strptime(date_str, "%Y-%m-%d").date()
        except ValueError:
            print("❌ 日期格式错误，请使用 YYYY-MM-DD 格式")
            return None
    
    def pause(self):
        """暂停等待用户按键"""
        input("\n按回车键继续...")
    
    def run(self):
        """运行CLI主循环"""
        while True:
            self.clear_screen()
            self.print_menu(
                "小会计 V1.6 - 实用增强版",
                [
                    "📊 报表生成",
                    "⏰ 提醒管理",
                    "🔍 对账功能",
                    "📥 数据导入",
                    "⚙️  系统设置",
                    "❌ 退出系统"
                ]
            )
            
            choice = self.get_input("请选择功能")
            
            if choice == "1":
                self.report_menu()
            elif choice == "2":
                self.reminder_menu()
            elif choice == "3":
                self.reconciliation_menu()
            elif choice == "4":
                self.import_menu()
            elif choice == "5":
                self.settings_menu()
            elif choice == "6" or choice == "0":
                print("\n感谢使用小会计系统！再见！👋\n")
                break
            else:
                print("❌ 无效选择，请重新输入")
                self.pause()
    
    def report_menu(self):
        """报表生成菜单"""
        while True:
            self.clear_screen()
            self.print_menu(
                "📊 报表生成",
                [
                    "管理报表（收支对比、利润趋势、客户排名）",
                    "税务报表（增值税、所得税申报表）",
                    "银行贷款报表（资产负债表、利润表、现金流量表）",
                    "查看已生成报表"
                ]
            )
            
            choice = self.get_input("请选择报表类型")
            
            if choice == "1":
                self.generate_management_report()
            elif choice == "2":
                self.generate_tax_report()
            elif choice == "3":
                self.generate_bank_loan_report()
            elif choice == "4":
                self.view_generated_reports()
            elif choice == "0":
                break
            else:
                print("❌ 无效选择")
                self.pause()
    
    def generate_management_report(self):
        """生成管理报表"""
        self.print_header("生成管理报表")
        
        # 获取日期范围
        default_start = date.today().replace(day=1)
        default_end = date.today()
        
        start_date = self.get_date_input("开始日期 (YYYY-MM-DD)", default_start)
        if not start_date:
            return
        
        end_date = self.get_date_input("结束日期 (YYYY-MM-DD)", default_end)
        if not end_date:
            return
        
        print("\n正在生成管理报表...")
        try:
            result = self.report_generator.generate_management_report(start_date, end_date)
            
            if result.success:
                print(f"\n✅ 报表生成成功！")
                print(f"   文件路径: {result.file_path}")
                print(f"   数据期间: {result.data_period.start_date} 至 {result.data_period.end_date}")
            else:
                print(f"\n❌ 报表生成失败: {result.error_message}")
        except Exception as e:
            print(f"\n❌ 生成报表时出错: {str(e)}")
        
        self.pause()
    
    def generate_tax_report(self):
        """生成税务报表"""
        self.print_header("生成税务报表")
        
        print("请选择税务报表类型:")
        print("  1. 增值税申报表")
        print("  2. 所得税申报表")
        
        choice = self.get_input("请选择")
        
        if choice == "1":
            report_type = ReportType.TAX_VAT
        elif choice == "2":
            report_type = ReportType.TAX_INCOME
        else:
            print("❌ 无效选择")
            self.pause()
            return
        
        period = self.get_input("报税期间 (例如: 2026-01)", date.today().strftime("%Y-%m"))
        
        print("\n正在生成税务报表...")
        try:
            result = self.report_generator.generate_tax_report(report_type, period)
            
            if result.success:
                print(f"\n✅ 报表生成成功！")
                print(f"   文件路径: {result.file_path}")
            else:
                print(f"\n❌ 报表生成失败: {result.error_message}")
        except Exception as e:
            print(f"\n❌ 生成报表时出错: {str(e)}")
        
        self.pause()
    
    def generate_bank_loan_report(self):
        """生成银行贷款报表"""
        self.print_header("生成银行贷款报表")
        
        report_date = self.get_date_input("报表日期 (YYYY-MM-DD)", date.today())
        if not report_date:
            return
        
        print("\n正在生成银行贷款报表...")
        try:
            result = self.report_generator.generate_bank_loan_report(report_date)
            
            if result.success:
                print(f"\n✅ 报表生成成功！")
                print(f"   文件路径: {result.file_path}")
            else:
                print(f"\n❌ 报表生成失败: {result.error_message}")
        except Exception as e:
            print(f"\n❌ 生成报表时出错: {str(e)}")
        
        self.pause()
    
    def view_generated_reports(self):
        """查看已生成的报表"""
        self.print_header("已生成的报表")
        
        reports_dir = os.path.join(self.storage_dir, "reports")
        if not os.path.exists(reports_dir):
            print("暂无已生成的报表")
            self.pause()
            return
        
        files = [f for f in os.listdir(reports_dir) if f.endswith('.xlsx')]
        
        if not files:
            print("暂无已生成的报表")
        else:
            print(f"共找到 {len(files)} 个报表文件:\n")
            for i, file in enumerate(files, 1):
                file_path = os.path.join(reports_dir, file)
                file_size = os.path.getsize(file_path) / 1024  # KB
                mod_time = datetime.fromtimestamp(os.path.getmtime(file_path))
                print(f"  {i}. {file}")
                print(f"     大小: {file_size:.1f} KB | 生成时间: {mod_time.strftime('%Y-%m-%d %H:%M:%S')}")
                print()
        
        self.pause()
    
    def reminder_menu(self):
        """提醒管理菜单"""
        while True:
            self.clear_screen()
            self.print_menu(
                "⏰ 提醒管理",
                [
                    "查看待办提醒",
                    "运行提醒检查",
                    "配置提醒调度",
                    "查看调度状态",
                    "测试通知功能"
                ]
            )
            
            choice = self.get_input("请选择功能")
            
            if choice == "1":
                self.view_pending_reminders()
            elif choice == "2":
                self.run_reminder_checks()
            elif choice == "3":
                self.configure_reminder_schedule()
            elif choice == "4":
                self.view_scheduler_status()
            elif choice == "5":
                self.test_notifications()
            elif choice == "0":
                break
            else:
                print("❌ 无效选择")
                self.pause()
    
    def view_pending_reminders(self):
        """查看待办提醒"""
        self.print_header("待办提醒")
        
        reminders = self.reminder_storage.get_upcoming_reminders(days=30)
        
        if not reminders:
            print("✅ 暂无待办提醒")
        else:
            print(f"共有 {len(reminders)} 条待办提醒:\n")
            for i, reminder in enumerate(reminders, 1):
                priority_icon = "🔴" if reminder.priority.value == "high" else "🟡" if reminder.priority.value == "medium" else "🟢"
                print(f"{i}. {priority_icon} {reminder.title}")
                print(f"   类型: {reminder.type.value} | 到期日: {reminder.due_date}")
                print(f"   {reminder.description}")
                print()
        
        self.pause()
    
    def run_reminder_checks(self):
        """运行提醒检查"""
        self.print_header("运行提醒检查")
        
        print("正在检查各类提醒...")
        
        # 检查税务提醒
        print("\n1. 检查税务申报提醒...")
        tax_reminders = self.reminder_system.check_tax_reminders()
        print(f"   找到 {len(tax_reminders)} 条税务提醒")
        
        # 检查应付账款提醒
        print("\n2. 检查应付账款提醒...")
        payable_reminders = self.reminder_system.check_payable_reminders()
        print(f"   找到 {len(payable_reminders)} 条应付账款提醒")
        
        # 检查应收账款提醒
        print("\n3. 检查应收账款提醒...")
        receivable_reminders = self.reminder_system.check_receivable_reminders()
        print(f"   找到 {len(receivable_reminders)} 条应收账款提醒")
        
        # 检查现金流预警
        print("\n4. 检查现金流预警...")
        cashflow_warnings = self.reminder_system.check_cashflow_warnings()
        print(f"   找到 {len(cashflow_warnings)} 条现金流预警")
        
        # 发送所有提醒
        all_reminders = tax_reminders + payable_reminders + receivable_reminders + cashflow_warnings
        
        if all_reminders:
            print(f"\n共找到 {len(all_reminders)} 条提醒")
            send = self.get_input("是否立即发送这些提醒？(y/n)", "y")
            
            if send.lower() == 'y':
                print("\n正在发送提醒...")
                sent_count = self.reminder_system.send_all_pending_reminders()
                print(f"✅ 已发送 {sent_count} 条提醒")
        else:
            print("\n✅ 暂无需要发送的提醒")
        
        self.pause()
    
    def configure_reminder_schedule(self):
        """配置提醒调度"""
        self.print_header("配置提醒调度")
        
        print("当前调度配置:\n")
        
        reminders = self.reminder_scheduler.get_scheduled_reminders()
        for reminder in reminders:
            status = "✅ 启用" if reminder.enabled else "❌ 禁用"
            print(f"  {reminder.name}")
            print(f"    状态: {status}")
            print(f"    频率: {reminder.schedule.frequency.value}")
            print(f"    检查时间: {reminder.schedule.check_time}")
            print(f"    下次运行: {reminder.next_run}")
            print()
        
        print("\n操作选项:")
        print("  1. 启用/禁用调度任务")
        print("  2. 重置为默认调度")
        print("  0. 返回")
        
        choice = self.get_input("请选择")
        
        if choice == "1":
            task_id = self.get_input("请输入任务ID (例如: tax_reminders)")
            action = self.get_input("启用(e)还是禁用(d)?")
            
            if action.lower() == 'e':
                self.reminder_scheduler.enable_reminder(task_id)
                print(f"✅ 已启用任务: {task_id}")
            elif action.lower() == 'd':
                self.reminder_scheduler.disable_reminder(task_id)
                print(f"✅ 已禁用任务: {task_id}")
            
            self.pause()
        elif choice == "2":
            confirm = self.get_input("确认重置为默认调度？(y/n)", "n")
            if confirm.lower() == 'y':
                self.reminder_scheduler.setup_default_schedules()
                print("✅ 已重置为默认调度")
            self.pause()
    
    def view_scheduler_status(self):
        """查看调度器状态"""
        self.print_header("调度器状态")
        
        status = self.reminder_scheduler.get_status()
        
        print(f"运行状态: {'运行中' if status.get('is_running', False) else '已停止'}")
        print(f"总任务数: {status['total_tasks']}")
        print(f"启用任务: {status['enabled_tasks']}")
        print(f"禁用任务: {status['disabled_tasks']}")
        print()
        
        self.pause()
    
    def test_notifications(self):
        """测试通知功能"""
        self.print_header("测试通知功能")
        
        print("请选择要测试的通知渠道:")
        print("  1. 桌面通知")
        print("  2. 企业微信通知")
        print("  3. 全部渠道")
        
        choice = self.get_input("请选择")
        
        if choice == "1":
            result = self.reminder_system.notification_service.test_desktop_notification()
            if result:
                print("✅ 桌面通知测试成功")
            else:
                print("❌ 桌面通知测试失败")
        elif choice == "2":
            result = self.reminder_system.notification_service.test_wechat_notification()
            if result:
                print("✅ 企业微信通知测试成功")
            else:
                print("❌ 企业微信通知测试失败")
        elif choice == "3":
            desktop_result = self.reminder_system.notification_service.test_desktop_notification()
            wechat_result = self.reminder_system.notification_service.test_wechat_notification()
            
            print(f"桌面通知: {'✅ 成功' if desktop_result else '❌ 失败'}")
            print(f"企业微信通知: {'✅ 成功' if wechat_result else '❌ 失败'}")
        
        self.pause()
    
    def reconciliation_menu(self):
        """对账功能菜单"""
        while True:
            self.clear_screen()
            self.print_menu(
                "🔍 对账功能",
                [
                    "银行对账",
                    "生成客户对账单",
                    "供应商对账",
                    "查看对账报告"
                ]
            )
            
            choice = self.get_input("请选择功能")
            
            if choice == "1":
                self.bank_reconciliation()
            elif choice == "2":
                self.generate_customer_statement()
            elif choice == "3":
                self.supplier_reconciliation()
            elif choice == "4":
                self.view_reconciliation_reports()
            elif choice == "0":
                break
            else:
                print("❌ 无效选择")
                self.pause()
    
    def bank_reconciliation(self):
        """银行对账"""
        self.print_header("银行对账")
        
        bank_file = self.get_input("请输入银行流水Excel文件路径")
        
        if not bank_file or not os.path.exists(bank_file):
            print("❌ 文件不存在")
            self.pause()
            return
        
        print("\n正在进行银行对账...")
        try:
            result = self.reconciliation_assistant.reconcile_bank_statement(bank_file)
            
            print(f"\n✅ 对账完成！")
            print(f"   匹配记录: {result.matched_count}")
            print(f"   未匹配银行记录: {len(result.unmatched_bank_records)}")
            print(f"   未匹配系统记录: {len(result.unmatched_system_records)}")
            print(f"   差异记录: {len(result.discrepancies)}")
            
            if result.discrepancies:
                print("\n差异详情:")
                for i, disc in enumerate(result.discrepancies[:5], 1):
                    print(f"  {i}. {disc.description}")
                    print(f"     差异金额: ¥{disc.difference_amount}")
                
                if len(result.discrepancies) > 5:
                    print(f"\n  ... 还有 {len(result.discrepancies) - 5} 条差异")
        except Exception as e:
            print(f"\n❌ 对账失败: {str(e)}")
        
        self.pause()
    
    def generate_customer_statement(self):
        """生成客户对账单"""
        self.print_header("生成客户对账单")
        
        # 列出所有客户
        customers = [c for c in self.counterparty_storage.get_all() 
                    if c.type == CounterpartyType.CUSTOMER]
        
        if not customers:
            print("暂无客户数据")
            self.pause()
            return
        
        print("客户列表:\n")
        for i, customer in enumerate(customers, 1):
            print(f"  {i}. {customer.name} (ID: {customer.id})")
        
        customer_id = self.get_input("\n请输入客户ID")
        
        default_start = date.today().replace(day=1)
        default_end = date.today()
        
        start_date = self.get_date_input("开始日期 (YYYY-MM-DD)", default_start)
        if not start_date:
            return
        
        end_date = self.get_date_input("结束日期 (YYYY-MM-DD)", default_end)
        if not end_date:
            return
        
        print("\n正在生成客户对账单...")
        try:
            workbook = self.reconciliation_assistant.generate_customer_statement(
                customer_id, start_date, end_date
            )
            
            output_dir = os.path.join(self.storage_dir, "reconciliation")
            os.makedirs(output_dir, exist_ok=True)
            
            filename = f"客户对账单_{customer_id}_{start_date}至{end_date}.xlsx"
            filepath = os.path.join(output_dir, filename)
            workbook.save(filepath)
            
            print(f"\n✅ 对账单生成成功！")
            print(f"   文件路径: {filepath}")
        except Exception as e:
            print(f"\n❌ 生成对账单失败: {str(e)}")
        
        self.pause()
    
    def supplier_reconciliation(self):
        """供应商对账"""
        self.print_header("供应商对账")
        
        # 列出所有供应商
        suppliers = [c for c in self.counterparty_storage.get_all() 
                    if c.type == CounterpartyType.SUPPLIER]
        
        if not suppliers:
            print("暂无供应商数据")
            self.pause()
            return
        
        print("供应商列表:\n")
        for i, supplier in enumerate(suppliers, 1):
            print(f"  {i}. {supplier.name} (ID: {supplier.id})")
        
        supplier_id = self.get_input("\n请输入供应商ID")
        
        print("\n正在进行供应商对账...")
        try:
            result = self.reconciliation_assistant.reconcile_supplier_accounts(supplier_id)
            
            print(f"\n✅ 对账完成！")
            print(f"   匹配记录: {result.matched_count}")
            print(f"   差异记录: {len(result.discrepancies)}")
        except Exception as e:
            print(f"\n❌ 对账失败: {str(e)}")
        
        self.pause()
    
    def view_reconciliation_reports(self):
        """查看对账报告"""
        self.print_header("对账报告")
        
        reports_dir = os.path.join(self.storage_dir, "reconciliation")
        if not os.path.exists(reports_dir):
            print("暂无对账报告")
            self.pause()
            return
        
        files = [f for f in os.listdir(reports_dir) if f.endswith('.xlsx')]
        
        if not files:
            print("暂无对账报告")
        else:
            print(f"共找到 {len(files)} 个对账报告:\n")
            for i, file in enumerate(files, 1):
                file_path = os.path.join(reports_dir, file)
                file_size = os.path.getsize(file_path) / 1024
                mod_time = datetime.fromtimestamp(os.path.getmtime(file_path))
                print(f"  {i}. {file}")
                print(f"     大小: {file_size:.1f} KB | 生成时间: {mod_time.strftime('%Y-%m-%d %H:%M:%S')}")
                print()
        
        self.pause()
    
    def import_menu(self):
        """数据导入菜单"""
        while True:
            self.clear_screen()
            self.print_menu(
                "📥 数据导入",
                [
                    "导入交易记录",
                    "导入往来单位",
                    "查看导入历史",
                    "撤销导入"
                ]
            )
            
            choice = self.get_input("请选择功能")
            
            if choice == "1":
                self.import_transactions()
            elif choice == "2":
                self.import_counterparties()
            elif choice == "3":
                self.view_import_history()
            elif choice == "4":
                self.undo_import()
            elif choice == "0":
                break
            else:
                print("❌ 无效选择")
                self.pause()
    
    def import_transactions(self):
        """导入交易记录"""
        self.print_header("导入交易记录")
        
        excel_file = self.get_input("请输入Excel文件路径")
        
        if not excel_file or not os.path.exists(excel_file):
            print("❌ 文件不存在")
            self.pause()
            return
        
        # 预览导入
        print("\n正在预览导入数据...")
        try:
            preview = self.import_engine.preview_import(excel_file)
            
            print(f"\n预览结果:")
            print(f"  预计导入行数: {preview.estimated_rows}")
            print(f"  列映射置信度: {preview.confidence:.1%}")
            
            if preview.validation_errors:
                print(f"\n⚠️  发现 {len(preview.validation_errors)} 个验证错误:")
                for i, error in enumerate(preview.validation_errors[:5], 1):
                    print(f"  {i}. {error}")
                
                if len(preview.validation_errors) > 5:
                    print(f"  ... 还有 {len(preview.validation_errors) - 5} 个错误")
                
                confirm = self.get_input("\n是否继续导入？(y/n)", "n")
                if confirm.lower() != 'y':
                    print("已取消导入")
                    self.pause()
                    return
            
            # 执行导入
            print("\n正在导入数据...")
            result = self.import_engine.import_transactions(excel_file)
            
            print(f"\n✅ 导入完成！")
            print(f"   总行数: {result.total_rows}")
            print(f"   成功: {result.successful_rows}")
            print(f"   失败: {result.failed_rows}")
            
            if result.errors:
                print(f"\n错误详情:")
                for i, error in enumerate(result.errors[:5], 1):
                    print(f"  {i}. {error}")
        except Exception as e:
            print(f"\n❌ 导入失败: {str(e)}")
        
        self.pause()
    
    def import_counterparties(self):
        """导入往来单位"""
        self.print_header("导入往来单位")
        
        excel_file = self.get_input("请输入Excel文件路径")
        
        if not excel_file or not os.path.exists(excel_file):
            print("❌ 文件不存在")
            self.pause()
            return
        
        print("\n正在导入往来单位...")
        try:
            result = self.import_engine.import_counterparties(excel_file)
            
            print(f"\n✅ 导入完成！")
            print(f"   总行数: {result.total_rows}")
            print(f"   成功: {result.successful_rows}")
            print(f"   失败: {result.failed_rows}")
            
            if result.errors:
                print(f"\n错误详情:")
                for i, error in enumerate(result.errors[:5], 1):
                    print(f"  {i}. {error}")
        except Exception as e:
            print(f"\n❌ 导入失败: {str(e)}")
        
        self.pause()
    
    def view_import_history(self):
        """查看导入历史"""
        self.print_header("导入历史")
        
        history = self.import_history.get_import_history()
        
        if not history:
            print("暂无导入历史")
        else:
            print(f"共有 {len(history)} 条导入记录:\n")
            for i, record in enumerate(history[-10:], 1):  # 显示最近10条
                print(f"{i}. 导入ID: {record.import_id}")
                print(f"   时间: {record.import_date}")
                print(f"   成功: {record.successful_rows}/{record.total_rows}")
                print(f"   可撤销: {'是' if record.can_undo else '否'}")
                print()
        
        self.pause()
    
    def undo_import(self):
        """撤销导入"""
        self.print_header("撤销导入")
        
        import_id = self.get_input("请输入要撤销的导入ID")
        
        confirm = self.get_input(f"确认撤销导入 {import_id}？(y/n)", "n")
        if confirm.lower() != 'y':
            print("已取消")
            self.pause()
            return
        
        print("\n正在撤销导入...")
        try:
            success = self.import_engine.undo_import(import_id)
            
            if success:
                print("✅ 导入已成功撤销")
            else:
                print("❌ 撤销失败")
        except Exception as e:
            print(f"❌ 撤销失败: {str(e)}")
        
        self.pause()
    
    def settings_menu(self):
        """系统设置菜单"""
        while True:
            self.clear_screen()
            self.print_menu(
                "⚙️  系统设置",
                [
                    "配置企业微信通知",
                    "配置提醒参数",
                    "查看系统信息",
                    "数据备份"
                ]
            )
            
            choice = self.get_input("请选择功能")
            
            if choice == "1":
                self.configure_wechat()
            elif choice == "2":
                self.configure_reminders()
            elif choice == "3":
                self.view_system_info()
            elif choice == "4":
                self.backup_data()
            elif choice == "0":
                break
            else:
                print("❌ 无效选择")
                self.pause()
    
    def configure_wechat(self):
        """配置企业微信通知"""
        self.print_header("配置企业微信通知")
        
        current_url = self.config.config.get("wechat_webhook_url", "")
        print(f"当前webhook地址: {current_url if current_url else '未配置'}\n")
        
        new_url = self.get_input("请输入新的webhook地址（留空保持不变）")
        
        if new_url:
            self.config.set("wechat_webhook_url", new_url)
            self.config.save()
            print("✅ 配置已保存")
            
            # 测试通知
            test = self.get_input("是否测试通知？(y/n)", "y")
            if test.lower() == 'y':
                result = self.reminder_system.notification_service.test_wechat_notification()
                if result:
                    print("✅ 测试成功")
                else:
                    print("❌ 测试失败，请检查webhook地址")
        
        self.pause()
    
    def configure_reminders(self):
        """配置提醒参数"""
        self.print_header("配置提醒参数")
        
        print("当前配置:\n")
        print(f"  税务提醒提前天数: {self.config.config.get('tax_reminder_days', [7, 3, 1, 0])}")
        print(f"  应付账款提醒提前天数: {self.config.config.get('payable_reminder_days', 3)}")
        print(f"  应收账款逾期提醒天数: {self.config.config.get('receivable_overdue_days', [30, 60, 90])}")
        print(f"  现金流预警天数: {self.config.config.get('cashflow_warning_days', 7)}")
        
        print("\n如需修改，请直接编辑配置文件")
        self.pause()
    
    def view_system_info(self):
        """查看系统信息"""
        self.print_header("系统信息")
        
        # 统计数据
        transactions = self.transaction_storage.get_all()
        counterparties = self.counterparty_storage.get_all()
        reminders = self.reminder_storage.get_all()
        
        print(f"数据统计:")
        print(f"  交易记录: {len(transactions)} 条")
        print(f"  往来单位: {len(counterparties)} 个")
        print(f"  提醒事项: {len(reminders)} 条")
        print()
        
        print(f"存储目录: {self.storage_dir}")
        print(f"配置文件: {os.path.join(self.storage_dir, 'config.json')}")
        print()
        
        print("系统版本: V1.6 实用增强版")
        print("功能模块:")
        print("  ✅ 智能报表生成器")
        print("  ✅ 智能提醒系统")
        print("  ✅ 快速对账助手")
        print("  ✅ Excel批量导入增强")
        
        self.pause()
    
    def backup_data(self):
        """数据备份"""
        self.print_header("数据备份")
        
        backup_dir = os.path.join(self.storage_dir, "backups")
        os.makedirs(backup_dir, exist_ok=True)
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_name = f"backup_{timestamp}"
        backup_path = os.path.join(backup_dir, backup_name)
        
        print(f"正在备份数据到: {backup_path}")
        
        try:
            import shutil
            shutil.copytree(self.storage_dir, backup_path, 
                          ignore=shutil.ignore_patterns('backups', '__pycache__', '*.pyc'))
            
            print(f"\n✅ 备份完成！")
            print(f"   备份路径: {backup_path}")
        except Exception as e:
            print(f"\n❌ 备份失败: {str(e)}")
        
        self.pause()


def main():
    """主函数"""
    print("\n" + "=" * 60)
    print("  欢迎使用小会计 V1.6 实用增强版")
    print("=" * 60)
    print("\n正在初始化系统...")
    
    try:
        cli = SmallAccountantCLI()
        print("✅ 系统初始化完成\n")
        cli.run()
    except KeyboardInterrupt:
        print("\n\n系统已退出")
    except Exception as e:
        print(f"\n❌ 系统错误: {str(e)}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
