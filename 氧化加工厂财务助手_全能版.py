# -*- coding: utf-8 -*-
"""
氧化加工厂财务助手 V1.3 - 全能版
专为小企业会计设计的全功能财务管理工具
涵盖：订单管理、收支记录、银行对账、税务管理、报表生成等
"""

import os
import sys
import json
import time
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Any
from decimal import Decimal, ROUND_HALF_UP

# 导入氧化加工厂模块
try:
    from oxidation_factory import get_config, get_storage
    from oxidation_factory.order_wizard import create_order_interactive
    from oxidation_factory.order_manager import Order
    from 财务数据管理器 import financial_manager
    print("✅ 氧化加工厂模块加载成功")
except Exception as e:
    print(f"⚠️ 模块加载失败: {e}")
    print("💡 提示：请确保 oxidation_factory 模块在当前目录")
    sys.exit(1)

# 设置日志
def setup_logging():
    """设置日志记录"""
    log_dir = "财务数据/运行日志"
    os.makedirs(log_dir, exist_ok=True)
    
    log_file = os.path.join(log_dir, f"app_{datetime.now().strftime('%Y%m%d')}.log")
    
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_file, encoding='utf-8'),
            logging.StreamHandler()
        ]
    )

setup_logging()
logger = logging.getLogger(__name__)

class Color:
    HEADER = '\033[95m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    GREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'

class UserMessage:
    """用户消息工具类"""
    
    @staticmethod
    def success(message: str):
        print(f"\n✅ {message}")
        logger.info(f"SUCCESS: {message}")
    
    @staticmethod
    def warning(message: str):
        print(f"\n⚠️ {message}")
        logger.warning(f"WARNING: {message}")
    
    @staticmethod
    def error(message: str):
        print(f"\n❌ {message}")
        logger.error(f"ERROR: {message}")
    
    @staticmethod
    def info(message: str):
        print(f"\n💡 {message}")
        logger.info(f"INFO: {message}")
    
    @staticmethod
    def confirm(message: str) -> bool:
        """确认对话框"""
        while True:
            response = input(f"\n❓ {message} (y/n): ").strip().lower()
            if response in ['y', 'yes', '是', '确定']:
                return True
            elif response in ['n', 'no', '否', '取消']:
                return False
            else:
                print("请输入 y 或 n")

class FinanceManager:
    """财务管理器"""
    
    def __init__(self):
        self.data_dir = "财务数据"
        self.ensure_directories()
    
    def ensure_directories(self):
        """确保目录存在"""
        dirs = [
            f"{self.data_dir}/收支记录",
            f"{self.data_dir}/银行流水",
            f"{self.data_dir}/税务资料",
            f"{self.data_dir}/月度报表",
            f"{self.data_dir}/年度报表",
            f"{self.data_dir}/凭证档案",
            f"{self.data_dir}/合同档案"
        ]
        for dir_path in dirs:
            os.makedirs(dir_path, exist_ok=True)
    
    def load_transactions(self) -> List[Dict]:
        """加载收支记录"""
        file_path = f"{self.data_dir}/收支记录/transactions.json"
        try:
            if os.path.exists(file_path):
                with open(file_path, 'r', encoding='utf-8') as f:
                    return json.load(f)
        except Exception as e:
            logger.error(f"加载收支记录失败: {e}")
        return []
    
    def save_transactions(self, transactions: List[Dict]):
        """保存收支记录"""
        file_path = f"{self.data_dir}/收支记录/transactions.json"
        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(transactions, f, ensure_ascii=False, indent=2)
            return True
        except Exception as e:
            logger.error(f"保存收支记录失败: {e}")
            return False
    
    def add_transaction(self, transaction: Dict) -> bool:
        """添加收支记录"""
        transactions = self.load_transactions()
        transaction['id'] = len(transactions) + 1
        transaction['created_at'] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        transactions.append(transaction)
        return self.save_transactions(transactions)

# 全局财务管理器
finance_manager = FinanceManager()

def progress_bar(current: int, total: int, desc: str = "处理中"):
    """显示进度条"""
    if total == 0:
        return
    
    percent = (current / total) * 100
    bar_length = 30
    filled_length = int(bar_length * current // total)
    bar = '█' * filled_length + '-' * (bar_length - filled_length)
    print(f'\r{desc}: |{bar}| {percent:.1f}% ({current}/{total})', end='', flush=True)
    
    if current == total:
        print()  # 换行

def show_main_menu():
    """显示主菜单"""
    print("\n" + "=" * 80)
    print(f"{Color.HEADER}            氧化加工厂财务助手 V1.3 - 全能版{Color.ENDC}")
    print("=" * 80)
    
    print(f"\n{Color.CYAN}【订单管理】{Color.ENDC}")
    print("  01. 📋 新建加工订单        02. 📖 查看订单列表")
    print("  03. ✏️  编辑订单信息        04. 🔍 搜索订单")
    print("  05. 💰 记录收款            06. 📊 订单统计分析")
    print("  07. 📤 导出订单到Excel")
    
    print(f"\n{Color.CYAN}【收支管理】{Color.ENDC}")
    print("  11. 💸 记录支出            12. 💵 记录收入")
    print("  13. 📋 查看收支明细        14. 📊 收支统计")
    print("  15. 🏦 银行流水管理        16. 📤 导出收支报表")
    
    print(f"\n{Color.CYAN}【税务管理】{Color.ENDC}")
    print("  21. 🧾 增值税管理          22. 📋 所得税计算")
    print("  23. 📊 税务报表            24. 📁 税务资料归档")
    
    print(f"\n{Color.CYAN}【报表中心】{Color.ENDC}")
    print("  31. 📈 利润表              32. 📊 资产负债表")
    print("  33. 💰 现金流量表          34. 📋 财务分析报告")
    print("  35. 📅 月度汇总            36. 📆 年度汇总")
    
    print(f"\n{Color.CYAN}【档案管理】{Color.ENDC}")
    print("  41. 📄 凭证管理            42. 📋 合同管理")
    print("  43. 👥 客户档案            44. 🏪 供应商档案")
    
    print(f"\n{Color.CYAN}【系统管理】{Color.ENDC}")
    print("  51. 📊 生成示例数据        52. 🗑️  数据清理")
    print("  53. 💾 数据备份            54. 📥 数据恢复")
    print("  55. ⚙️  系统配置            56. 📖 使用教程")
    print("  57. 📋 查看运行日志")
    
    print(f"\n{Color.CYAN}【其他功能】{Color.ENDC}")
    print("  99. 🚪 退出系统")
    
    print("\n" + "=" * 80)

def record_expense():
    """记录支出"""
    print("\n" + "=" * 70)
    print("     记录支出")
    print("=" * 70)
    
    try:
        # 获取支出分类
        config = get_config()
        categories = config.get_default_categories().get('支出', [])
        
        print("\n💡 支出分类：")
        for i, category in enumerate(categories, 1):
            print(f"  {i:2d}. {category}")
        
        # 输入支出信息
        date_str = input("\n支出日期（格式：2026-01-01，直接回车使用今天）: ").strip()
        if not date_str:
            date_str = datetime.now().strftime("%Y-%m-%d")
        
        amount_str = input("支出金额: ").strip()
        if not amount_str:
            UserMessage.info("操作已取消")
            return
        
        try:
            amount = float(amount_str)
            if amount <= 0:
                UserMessage.error("金额必须大于0")
                return
        except ValueError:
            UserMessage.error("请输入有效的金额")
            return
        
        # 选择分类
        category_choice = input(f"选择支出分类（1-{len(categories)}）: ").strip()
        try:
            category_idx = int(category_choice) - 1
            if 0 <= category_idx < len(categories):
                category = categories[category_idx]
            else:
                UserMessage.error("无效的分类选择")
                return
        except ValueError:
            UserMessage.error("请输入有效的数字")
            return
        
        description = input("支出说明: ").strip()
        if not description:
            description = category
        
        # 选择支付方式
        print("\n支付方式：")
        print("  1. G银行基本户")
        print("  2. N银行")
        print("  3. 微信")
        print("  4. 现金")
        print("  5. 其他")
        
        payment_choice = input("选择支付方式（1-5）: ").strip()
        payment_methods = {
            "1": "G银行基本户", "2": "N银行", "3": "微信", 
            "4": "现金", "5": "其他"
        }
        payment_method = payment_methods.get(payment_choice, "其他")
        
        # 确认信息
        print(f"\n支出信息确认：")
        print(f"  日期：{date_str}")
        print(f"  金额：{amount:.2f} 元")
        print(f"  分类：{category}")
        print(f"  说明：{description}")
        print(f"  支付方式：{payment_method}")
        
        if not UserMessage.confirm("确认记录此支出？"):
            UserMessage.info("操作已取消")
            return
        
        # 保存支出记录
        transaction = {
            'type': '支出',
            'date': date_str,
            'amount': amount,
            'category': category,
            'description': description,
            'payment_method': payment_method,
            'status': '已支付'
        }
        
        if finance_manager.add_transaction(transaction):
            UserMessage.success("支出记录成功！")
            logger.info(f"支出记录: {amount}元 - {category}")
        else:
            UserMessage.error("支出记录失败")
            
    except Exception as e:
        UserMessage.error(f"记录支出时发生错误: {str(e)}")
        logger.error(f"记录支出异常: {str(e)}", exc_info=True)

def record_income():
    """记录收入"""
    print("\n" + "=" * 70)
    print("     记录收入")
    print("=" * 70)
    
    try:
        # 获取收入分类
        config = get_config()
        categories = config.get_default_categories().get('收入', [])
        
        print("\n💡 收入分类：")
        for i, category in enumerate(categories, 1):
            print(f"  {i:2d}. {category}")
        
        # 输入收入信息
        date_str = input("\n收入日期（格式：2026-01-01，直接回车使用今天）: ").strip()
        if not date_str:
            date_str = datetime.now().strftime("%Y-%m-%d")
        
        amount_str = input("收入金额: ").strip()
        if not amount_str:
            UserMessage.info("操作已取消")
            return
        
        try:
            amount = float(amount_str)
            if amount <= 0:
                UserMessage.error("金额必须大于0")
                return
        except ValueError:
            UserMessage.error("请输入有效的金额")
            return
        
        # 选择分类
        category_choice = input(f"选择收入分类（1-{len(categories)}）: ").strip()
        try:
            category_idx = int(category_choice) - 1
            if 0 <= category_idx < len(categories):
                category = categories[category_idx]
            else:
                UserMessage.error("无效的分类选择")
                return
        except ValueError:
            UserMessage.error("请输入有效的数字")
            return
        
        description = input("收入说明: ").strip()
        if not description:
            description = category
        
        customer = input("客户名称（可选）: ").strip()
        
        # 选择收款方式
        print("\n收款方式：")
        print("  1. G银行基本户")
        print("  2. N银行")
        print("  3. 微信")
        print("  4. 现金")
        print("  5. 其他")
        
        payment_choice = input("选择收款方式（1-5）: ").strip()
        payment_methods = {
            "1": "G银行基本户", "2": "N银行", "3": "微信", 
            "4": "现金", "5": "其他"
        }
        payment_method = payment_methods.get(payment_choice, "其他")
        
        # 发票信息
        has_invoice = UserMessage.confirm("是否开具发票？")
        invoice_no = ""
        if has_invoice:
            invoice_no = input("发票号码: ").strip()
        
        # 确认信息
        print(f"\n收入信息确认：")
        print(f"  日期：{date_str}")
        print(f"  金额：{amount:.2f} 元")
        print(f"  分类：{category}")
        print(f"  说明：{description}")
        if customer:
            print(f"  客户：{customer}")
        print(f"  收款方式：{payment_method}")
        if has_invoice:
            print(f"  发票号码：{invoice_no}")
        
        if not UserMessage.confirm("确认记录此收入？"):
            UserMessage.info("操作已取消")
            return
        
        # 保存收入记录
        transaction = {
            'type': '收入',
            'date': date_str,
            'amount': amount,
            'category': category,
            'description': description,
            'customer': customer,
            'payment_method': payment_method,
            'has_invoice': has_invoice,
            'invoice_no': invoice_no,
            'status': '已收款'
        }
        
        if finance_manager.add_transaction(transaction):
            UserMessage.success("收入记录成功！")
            logger.info(f"收入记录: {amount}元 - {category}")
        else:
            UserMessage.error("收入记录失败")
            
    except Exception as e:
        UserMessage.error(f"记录收入时发生错误: {str(e)}")
        logger.error(f"记录收入异常: {str(e)}", exc_info=True)

def view_transactions():
    """查看收支明细"""
    print("\n" + "=" * 70)
    print("     收支明细")
    print("=" * 70)
    
    try:
        transactions = finance_manager.load_transactions()
        
        if not transactions:
            UserMessage.warning("暂无收支记录")
            UserMessage.info("请先记录收入（功能12）或支出（功能11）")
            return
        
        # 按日期排序（最新的在前）
        transactions.sort(key=lambda x: x.get("date", ""), reverse=True)
        
        print(f"\n📊 共有 {len(transactions)} 条记录\n")
        
        # 显示收支列表
        for i, trans in enumerate(transactions[-20:], 1):  # 只显示最近20条
            type_color = Color.GREEN if trans['type'] == '收入' else Color.FAIL
            print(f"{i:2d}. {trans['date']} - {type_color}{trans['type']}{Color.ENDC}")
            print(f"    金额：{trans['amount']:.2f}元 | 分类：{trans['category']}")
            print(f"    说明：{trans['description']}")
            if trans.get('customer'):
                print(f"    客户：{trans['customer']}")
            print(f"    方式：{trans['payment_method']}")
            print()
        
        if len(transactions) > 20:
            print(f"💡 显示最近20条记录，共有 {len(transactions)} 条记录")
        
        # 简单统计
        total_income = sum(t['amount'] for t in transactions if t['type'] == '收入')
        total_expense = sum(t['amount'] for t in transactions if t['type'] == '支出')
        net_profit = total_income - total_expense
        
        print(f"\n📊 收支汇总：")
        print(f"  总收入：{Color.GREEN}{total_income:.2f}元{Color.ENDC}")
        print(f"  总支出：{Color.FAIL}{total_expense:.2f}元{Color.ENDC}")
        profit_color = Color.GREEN if net_profit >= 0 else Color.FAIL
        print(f"  净利润：{profit_color}{net_profit:.2f}元{Color.ENDC}")
        
    except Exception as e:
        UserMessage.error(f"查看收支明细时发生错误: {str(e)}")
        logger.error(f"查看收支明细异常: {str(e)}", exc_info=True)

def generate_profit_report():
    """生成利润表"""
    print("\n" + "=" * 70)
    print("     利润表")
    print("=" * 70)
    
    try:
        # 选择报表期间
        print("\n报表期间：")
        print("  1. 本月")
        print("  2. 上月")
        print("  3. 本年")
        print("  4. 自定义")
        
        period_choice = input("选择报表期间（1-4）: ").strip()
        
        today = datetime.now()
        if period_choice == "1":  # 本月
            start_date = today.replace(day=1)
            end_date = today
            period_name = f"{today.year}年{today.month}月"
        elif period_choice == "2":  # 上月
            if today.month == 1:
                last_month = today.replace(year=today.year-1, month=12, day=1)
            else:
                last_month = today.replace(month=today.month-1, day=1)
            start_date = last_month
            if last_month.month == 12:
                end_date = last_month.replace(year=last_month.year+1, month=1, day=1) - timedelta(days=1)
            else:
                end_date = last_month.replace(month=last_month.month+1, day=1) - timedelta(days=1)
            period_name = f"{last_month.year}年{last_month.month}月"
        elif period_choice == "3":  # 本年
            start_date = today.replace(month=1, day=1)
            end_date = today
            period_name = f"{today.year}年"
        else:  # 自定义
            start_str = input("开始日期（格式：2026-01-01）: ").strip()
            end_str = input("结束日期（格式：2026-12-31）: ").strip()
            try:
                start_date = datetime.strptime(start_str, "%Y-%m-%d")
                end_date = datetime.strptime(end_str, "%Y-%m-%d")
                period_name = f"{start_str} 至 {end_str}"
            except ValueError:
                UserMessage.error("日期格式错误")
                return
        
        # 获取期间内的交易记录
        transactions = finance_manager.load_transactions()
        period_transactions = []
        
        for trans in transactions:
            trans_date = datetime.strptime(trans['date'], "%Y-%m-%d")
            if start_date <= trans_date <= end_date:
                period_transactions.append(trans)
        
        if not period_transactions:
            UserMessage.warning(f"{period_name}期间无交易记录")
            return
        
        # 计算利润表数据
        income_by_category = {}
        expense_by_category = {}
        
        for trans in period_transactions:
            if trans['type'] == '收入':
                category = trans['category']
                if category not in income_by_category:
                    income_by_category[category] = 0
                income_by_category[category] += trans['amount']
            else:
                category = trans['category']
                if category not in expense_by_category:
                    expense_by_category[category] = 0
                expense_by_category[category] += trans['amount']
        
        # 生成利润表
        print(f"\n" + "=" * 70)
        print(f"                利润表")
        print(f"              {period_name}")
        print("=" * 70)
        
        print(f"\n{Color.CYAN}一、营业收入{Color.ENDC}")
        total_income = 0
        for category, amount in income_by_category.items():
            print(f"  {category:<20} {amount:>15,.2f}")
            total_income += amount
        print(f"  {'营业收入合计':<20} {Color.GREEN}{total_income:>15,.2f}{Color.ENDC}")
        
        print(f"\n{Color.CYAN}二、营业成本及费用{Color.ENDC}")
        total_expense = 0
        for category, amount in expense_by_category.items():
            print(f"  {category:<20} {amount:>15,.2f}")
            total_expense += amount
        print(f"  {'营业成本及费用合计':<20} {Color.FAIL}{total_expense:>15,.2f}{Color.ENDC}")
        
        print(f"\n{Color.CYAN}三、利润{Color.ENDC}")
        gross_profit = total_income - total_expense
        profit_color = Color.GREEN if gross_profit >= 0 else Color.FAIL
        print(f"  {'营业利润':<20} {profit_color}{gross_profit:>15,.2f}{Color.ENDC}")
        
        # 计算利润率
        if total_income > 0:
            profit_rate = (gross_profit / total_income) * 100
            print(f"  {'利润率':<20} {profit_color}{profit_rate:>14.1f}%{Color.ENDC}")
        
        print("=" * 70)
        
        # 询问是否保存报表
        if UserMessage.confirm("是否保存此利润表？"):
            report_dir = "财务数据/月度报表"
            os.makedirs(report_dir, exist_ok=True)
            
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"{report_dir}/利润表_{period_name.replace('年', '').replace('月', '').replace(' 至 ', '_')}_{timestamp}.txt"
            
            try:
                with open(filename, 'w', encoding='utf-8') as f:
                    f.write(f"利润表\n")
                    f.write(f"{period_name}\n")
                    f.write("=" * 50 + "\n\n")
                    
                    f.write("一、营业收入\n")
                    for category, amount in income_by_category.items():
                        f.write(f"  {category:<15} {amount:>12,.2f}\n")
                    f.write(f"  {'营业收入合计':<15} {total_income:>12,.2f}\n\n")
                    
                    f.write("二、营业成本及费用\n")
                    for category, amount in expense_by_category.items():
                        f.write(f"  {category:<15} {amount:>12,.2f}\n")
                    f.write(f"  {'营业成本及费用合计':<15} {total_expense:>12,.2f}\n\n")
                    
                    f.write("三、利润\n")
                    f.write(f"  {'营业利润':<15} {gross_profit:>12,.2f}\n")
                    if total_income > 0:
                        f.write(f"  {'利润率':<15} {profit_rate:>11.1f}%\n")
                
                UserMessage.success(f"利润表已保存：{filename}")
                logger.info(f"利润表保存成功: {filename}")
                
            except Exception as e:
                UserMessage.error(f"保存利润表失败：{str(e)}")
        
    except Exception as e:
        UserMessage.error(f"生成利润表时发生错误: {str(e)}")
        logger.error(f"生成利润表异常: {str(e)}", exc_info=True)
def tax_management():
    """税务管理"""
    print("\n" + "=" * 70)
    print("     增值税管理")
    print("=" * 70)
    
    try:
        # 选择税务期间
        print("\n税务期间：")
        print("  1. 本月")
        print("  2. 上月")
        print("  3. 本季度")
        print("  4. 自定义")
        
        period_choice = input("选择税务期间（1-4）: ").strip()
        
        today = datetime.now()
        if period_choice == "1":  # 本月
            start_date = today.replace(day=1)
            end_date = today
            period_name = f"{today.year}年{today.month}月"
        elif period_choice == "2":  # 上月
            if today.month == 1:
                last_month = today.replace(year=today.year-1, month=12, day=1)
            else:
                last_month = today.replace(month=today.month-1, day=1)
            start_date = last_month
            if last_month.month == 12:
                end_date = last_month.replace(year=last_month.year+1, month=1, day=1) - timedelta(days=1)
            else:
                end_date = last_month.replace(month=last_month.month+1, day=1) - timedelta(days=1)
            period_name = f"{last_month.year}年{last_month.month}月"
        elif period_choice == "3":  # 本季度
            quarter = (today.month - 1) // 3 + 1
            start_month = (quarter - 1) * 3 + 1
            start_date = today.replace(month=start_month, day=1)
            end_date = today
            period_name = f"{today.year}年第{quarter}季度"
        else:  # 自定义
            start_str = input("开始日期（格式：2026-01-01）: ").strip()
            end_str = input("结束日期（格式：2026-12-31）: ").strip()
            try:
                start_date = datetime.strptime(start_str, "%Y-%m-%d")
                end_date = datetime.strptime(end_str, "%Y-%m-%d")
                period_name = f"{start_str} 至 {end_str}"
            except ValueError:
                UserMessage.error("日期格式错误")
                return
        
        # 获取期间内的收入记录（用于计算增值税）
        transactions = finance_manager.load_transactions()
        income_transactions = []
        
        for trans in transactions:
            trans_date = datetime.strptime(trans['date'], "%Y-%m-%d")
            if start_date <= trans_date <= end_date and trans['type'] == '收入':
                income_transactions.append(trans)
        
        if not income_transactions:
            UserMessage.warning(f"{period_name}期间无收入记录")
            return
        
        # 计算增值税
        print(f"\n" + "=" * 70)
        print(f"                增值税计算表")
        print(f"              {period_name}")
        print("=" * 70)
        
        # 分类统计收入
        taxable_income = 0  # 应税收入
        tax_free_income = 0  # 免税收入
        
        for trans in income_transactions:
            if trans.get('has_invoice', False):
                taxable_income += trans['amount']
            else:
                tax_free_income += trans['amount']
        
        total_income = taxable_income + tax_free_income
        
        print(f"\n{Color.CYAN}收入明细：{Color.ENDC}")
        print(f"  应税收入（含税）：{taxable_income:>12,.2f} 元")
        print(f"  免税收入：      {tax_free_income:>12,.2f} 元")
        print(f"  收入合计：      {total_income:>12,.2f} 元")
        
        # 增值税计算（假设小规模纳税人，征收率3%）
        vat_rate = 0.03  # 3%征收率
        
        # 不含税收入 = 含税收入 / (1 + 征收率)
        income_without_tax = taxable_income / (1 + vat_rate) if taxable_income > 0 else 0
        vat_amount = taxable_income - income_without_tax
        
        print(f"\n{Color.CYAN}增值税计算：{Color.ENDC}")
        print(f"  不含税收入：    {income_without_tax:>12,.2f} 元")
        print(f"  应纳增值税：    {Color.WARNING}{vat_amount:>12,.2f} 元{Color.ENDC}")
        print(f"  征收率：        {vat_rate*100:>11.1f} %")
        
        # 小规模纳税人月销售额15万以下免征增值税
        monthly_limit = 150000  # 15万元
        if period_choice in ["1", "2"]:  # 月度
            if income_without_tax <= monthly_limit:
                actual_vat = 0
                print(f"\n{Color.GREEN}💡 月销售额未超过15万元，免征增值税{Color.ENDC}")
            else:
                actual_vat = vat_amount
        else:
            actual_vat = vat_amount
        
        print(f"  实际应纳税额：  {Color.FAIL if actual_vat > 0 else Color.GREEN}{actual_vat:>12,.2f} 元{Color.ENDC}")
        
        # 询问是否保存税务资料
        if UserMessage.confirm("是否保存此税务计算表？"):
            tax_dir = "财务数据/税务资料"
            os.makedirs(tax_dir, exist_ok=True)
            
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"{tax_dir}/增值税计算表_{period_name.replace('年', '').replace('月', '').replace('季度', 'Q').replace(' 至 ', '_')}_{timestamp}.txt"
            
            try:
                with open(filename, 'w', encoding='utf-8') as f:
                    f.write(f"增值税计算表\n")
                    f.write(f"{period_name}\n")
                    f.write("=" * 50 + "\n\n")
                    
                    f.write("收入明细：\n")
                    f.write(f"  应税收入（含税）：{taxable_income:>12,.2f} 元\n")
                    f.write(f"  免税收入：      {tax_free_income:>12,.2f} 元\n")
                    f.write(f"  收入合计：      {total_income:>12,.2f} 元\n\n")
                    
                    f.write("增值税计算：\n")
                    f.write(f"  不含税收入：    {income_without_tax:>12,.2f} 元\n")
                    f.write(f"  应纳增值税：    {vat_amount:>12,.2f} 元\n")
                    f.write(f"  征收率：        {vat_rate*100:>11.1f} %\n")
                    f.write(f"  实际应纳税额：  {actual_vat:>12,.2f} 元\n")
                    
                    if actual_vat == 0 and vat_amount > 0:
                        f.write(f"\n备注：月销售额未超过15万元，享受小规模纳税人免税政策\n")
                
                UserMessage.success(f"税务计算表已保存：{filename}")
                logger.info(f"税务计算表保存成功: {filename}")
                
            except Exception as e:
                UserMessage.error(f"保存税务计算表失败：{str(e)}")
        
    except Exception as e:
        UserMessage.error(f"税务管理时发生错误: {str(e)}")
        logger.error(f"税务管理异常: {str(e)}", exc_info=True)

def customer_management():
    """客户档案管理"""
    print("\n" + "=" * 70)
    print("     客户档案管理")
    print("=" * 70)
    
    try:
        # 加载客户档案
        customer_file = "财务数据/档案管理/customers.json"
        customers = []
        
        if os.path.exists(customer_file):
            try:
                with open(customer_file, 'r', encoding='utf-8') as f:
                    customers = json.load(f)
            except Exception as e:
                logger.error(f"加载客户档案失败: {e}")
        
        print("\n客户档案功能：")
        print("  1. 查看客户列表")
        print("  2. 新增客户")
        print("  3. 编辑客户")
        print("  4. 客户交易统计")
        
        choice = input("请选择功能（1-4）: ").strip()
        
        if choice == "1":  # 查看客户列表
            if not customers:
                UserMessage.warning("暂无客户档案")
                return
            
            print(f"\n📋 客户列表（共{len(customers)}个）：")
            for i, customer in enumerate(customers, 1):
                print(f"{i:2d}. {customer['name']}")
                print(f"    联系人：{customer.get('contact', '未填写')}")
                print(f"    电话：{customer.get('phone', '未填写')}")
                print(f"    地址：{customer.get('address', '未填写')}")
                print(f"    创建时间：{customer.get('created_at', '未知')}")
                print()
        
        elif choice == "2":  # 新增客户
            print("\n新增客户档案：")
            name = input("客户名称: ").strip()
            if not name:
                UserMessage.info("操作已取消")
                return
            
            # 检查是否已存在
            if any(c['name'] == name for c in customers):
                UserMessage.error("客户已存在")
                return
            
            contact = input("联系人: ").strip()
            phone = input("联系电话: ").strip()
            address = input("客户地址: ").strip()
            remark = input("备注: ").strip()
            
            customer = {
                'id': len(customers) + 1,
                'name': name,
                'contact': contact,
                'phone': phone,
                'address': address,
                'remark': remark,
                'created_at': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            }
            
            customers.append(customer)
            
            # 保存客户档案
            os.makedirs(os.path.dirname(customer_file), exist_ok=True)
            with open(customer_file, 'w', encoding='utf-8') as f:
                json.dump(customers, f, ensure_ascii=False, indent=2)
            
            UserMessage.success("客户档案创建成功")
            logger.info(f"新增客户: {name}")
        
        elif choice == "3":  # 编辑客户
            if not customers:
                UserMessage.warning("暂无客户档案")
                return
            
            print("\n客户列表：")
            for i, customer in enumerate(customers, 1):
                print(f"  {i}. {customer['name']}")
            
            try:
                idx = int(input("选择要编辑的客户编号: ").strip()) - 1
                if 0 <= idx < len(customers):
                    customer = customers[idx]
                    print(f"\n编辑客户：{customer['name']}")
                    
                    new_contact = input(f"联系人（当前：{customer.get('contact', '未填写')}）: ").strip()
                    new_phone = input(f"联系电话（当前：{customer.get('phone', '未填写')}）: ").strip()
                    new_address = input(f"客户地址（当前：{customer.get('address', '未填写')}）: ").strip()
                    new_remark = input(f"备注（当前：{customer.get('remark', '未填写')}）: ").strip()
                    
                    if new_contact:
                        customer['contact'] = new_contact
                    if new_phone:
                        customer['phone'] = new_phone
                    if new_address:
                        customer['address'] = new_address
                    if new_remark:
                        customer['remark'] = new_remark
                    
                    customer['updated_at'] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    
                    # 保存更新
                    with open(customer_file, 'w', encoding='utf-8') as f:
                        json.dump(customers, f, ensure_ascii=False, indent=2)
                    
                    UserMessage.success("客户档案更新成功")
                    logger.info(f"更新客户: {customer['name']}")
                else:
                    UserMessage.error("无效的客户编号")
            except ValueError:
                UserMessage.error("请输入有效的数字")
        
        elif choice == "4":  # 客户交易统计
            if not customers:
                UserMessage.warning("暂无客户档案")
                return
            
            # 统计客户交易
            transactions = finance_manager.load_transactions()
            orders = get_storage().get_all_orders()
            
            customer_stats = {}
            
            # 统计收入交易
            for trans in transactions:
                if trans['type'] == '收入' and trans.get('customer'):
                    customer = trans['customer']
                    if customer not in customer_stats:
                        customer_stats[customer] = {'income': 0, 'orders': 0}
                    customer_stats[customer]['income'] += trans['amount']
            
            # 统计订单
            for order in orders:
                customer = order['customer']
                if customer not in customer_stats:
                    customer_stats[customer] = {'income': 0, 'orders': 0}
                customer_stats[customer]['orders'] += 1
            
            print(f"\n📊 客户交易统计：")
            if customer_stats:
                # 按收入排序
                sorted_customers = sorted(customer_stats.items(), 
                                        key=lambda x: x[1]['income'], reverse=True)
                
                for customer, stats in sorted_customers:
                    print(f"  {customer}:")
                    print(f"    收入金额：{stats['income']:>10,.2f} 元")
                    print(f"    订单数量：{stats['orders']:>10} 个")
                    print()
            else:
                print("  暂无客户交易记录")
        
    except Exception as e:
        UserMessage.error(f"客户档案管理时发生错误: {str(e)}")
        logger.error(f"客户档案管理异常: {str(e)}", exc_info=True)

def monthly_summary():
    """月度汇总"""
    print("\n" + "=" * 70)
    print("     月度汇总")
    print("=" * 70)
    
    try:
        # 选择月份
        year = input("年份（直接回车使用今年）: ").strip()
        if not year:
            year = str(datetime.now().year)
        
        month = input("月份（1-12，直接回车使用本月）: ").strip()
        if not month:
            month = str(datetime.now().month)
        
        try:
            year = int(year)
            month = int(month)
            if not (1 <= month <= 12):
                UserMessage.error("月份必须在1-12之间")
                return
        except ValueError:
            UserMessage.error("请输入有效的年份和月份")
            return
        
        # 计算月份的开始和结束日期
        start_date = datetime(year, month, 1)
        if month == 12:
            end_date = datetime(year + 1, 1, 1) - timedelta(days=1)
        else:
            end_date = datetime(year, month + 1, 1) - timedelta(days=1)
        
        period_name = f"{year}年{month}月"
        
        print(f"\n正在生成{period_name}汇总报告...")
        
        # 获取月度数据
        transactions = finance_manager.load_transactions()
        orders = get_storage().get_all_orders()
        
        # 筛选月度交易
        monthly_transactions = []
        for trans in transactions:
            trans_date = datetime.strptime(trans['date'], "%Y-%m-%d")
            if start_date <= trans_date <= end_date:
                monthly_transactions.append(trans)
        
        # 筛选月度订单
        monthly_orders = []
        for order in orders:
            order_date = datetime.strptime(order['order_date'], "%Y-%m-%d")
            if start_date <= order_date <= end_date:
                monthly_orders.append(order)
        
        # 生成汇总报告
        print(f"\n" + "=" * 70)
        print(f"                月度汇总报告")
        print(f"                {period_name}")
        print("=" * 70)
        
        # 1. 订单汇总
        print(f"\n{Color.CYAN}一、订单汇总{Color.ENDC}")
        if monthly_orders:
            total_orders = len(monthly_orders)
            total_amount = sum(order['order_amount'] for order in monthly_orders)
            total_paid = sum(order['paid_amount'] for order in monthly_orders)
            total_unpaid = sum(order['unpaid_amount'] for order in monthly_orders)
            
            print(f"  订单总数：      {total_orders:>8} 个")
            print(f"  订单总额：      {total_amount:>12,.2f} 元")
            print(f"  已收款：        {total_paid:>12,.2f} 元")
            print(f"  未收款：        {total_unpaid:>12,.2f} 元")
            
            if total_amount > 0:
                collection_rate = (total_paid / total_amount) * 100
                print(f"  收款率：        {collection_rate:>11.1f} %")
            
            # 按状态统计
            status_stats = {}
            for order in monthly_orders:
                status = order['status']
                if status not in status_stats:
                    status_stats[status] = 0
                status_stats[status] += 1
            
            print(f"\n  按状态分布：")
            for status, count in status_stats.items():
                print(f"    {status}：{count:>6} 个")
        else:
            print("  本月无订单记录")
        
        # 2. 收支汇总
        print(f"\n{Color.CYAN}二、收支汇总{Color.ENDC}")
        if monthly_transactions:
            income_total = sum(t['amount'] for t in monthly_transactions if t['type'] == '收入')
            expense_total = sum(t['amount'] for t in monthly_transactions if t['type'] == '支出')
            net_profit = income_total - expense_total
            
            print(f"  总收入：        {Color.GREEN}{income_total:>12,.2f} 元{Color.ENDC}")
            print(f"  总支出：        {Color.FAIL}{expense_total:>12,.2f} 元{Color.ENDC}")
            profit_color = Color.GREEN if net_profit >= 0 else Color.FAIL
            print(f"  净利润：        {profit_color}{net_profit:>12,.2f} 元{Color.ENDC}")
            
            if income_total > 0:
                profit_rate = (net_profit / income_total) * 100
                print(f"  利润率：        {profit_color}{profit_rate:>11.1f} %{Color.ENDC}")
            
            # 收入分类统计
            income_by_category = {}
            expense_by_category = {}
            
            for trans in monthly_transactions:
                if trans['type'] == '收入':
                    category = trans['category']
                    if category not in income_by_category:
                        income_by_category[category] = 0
                    income_by_category[category] += trans['amount']
                else:
                    category = trans['category']
                    if category not in expense_by_category:
                        expense_by_category[category] = 0
                    expense_by_category[category] += trans['amount']
            
            if income_by_category:
                print(f"\n  收入分类：")
                for category, amount in income_by_category.items():
                    print(f"    {category}：{amount:>10,.2f} 元")
            
            if expense_by_category:
                print(f"\n  支出分类：")
                for category, amount in expense_by_category.items():
                    print(f"    {category}：{amount:>10,.2f} 元")
        else:
            print("  本月无收支记录")
        
        # 3. 客户分析
        print(f"\n{Color.CYAN}三、客户分析{Color.ENDC}")
        if monthly_orders:
            customer_stats = {}
            for order in monthly_orders:
                customer = order['customer']
                if customer not in customer_stats:
                    customer_stats[customer] = {'count': 0, 'amount': 0}
                customer_stats[customer]['count'] += 1
                customer_stats[customer]['amount'] += order['order_amount']
            
            # 按金额排序
            sorted_customers = sorted(customer_stats.items(), 
                                    key=lambda x: x[1]['amount'], reverse=True)
            
            print(f"  主要客户（前5名）：")
            for i, (customer, stats) in enumerate(sorted_customers[:5], 1):
                print(f"    {i}. {customer}：{stats['count']}个订单，{stats['amount']:,.2f}元")
        else:
            print("  本月无客户数据")
        
        print("=" * 70)
        
        # 询问是否保存报告
        if UserMessage.confirm("是否保存此月度汇总报告？"):
            report_dir = "财务数据/月度报表"
            os.makedirs(report_dir, exist_ok=True)
            
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"{report_dir}/月度汇总_{year}{month:02d}_{timestamp}.txt"
            
            try:
                with open(filename, 'w', encoding='utf-8') as f:
                    f.write(f"月度汇总报告\n")
                    f.write(f"{period_name}\n")
                    f.write("=" * 50 + "\n\n")
                    
                    # 写入订单汇总
                    f.write("一、订单汇总\n")
                    if monthly_orders:
                        f.write(f"  订单总数：      {total_orders:>8} 个\n")
                        f.write(f"  订单总额：      {total_amount:>12,.2f} 元\n")
                        f.write(f"  已收款：        {total_paid:>12,.2f} 元\n")
                        f.write(f"  未收款：        {total_unpaid:>12,.2f} 元\n")
                        if total_amount > 0:
                            f.write(f"  收款率：        {collection_rate:>11.1f} %\n")
                    else:
                        f.write("  本月无订单记录\n")
                    
                    # 写入收支汇总
                    f.write("\n二、收支汇总\n")
                    if monthly_transactions:
                        f.write(f"  总收入：        {income_total:>12,.2f} 元\n")
                        f.write(f"  总支出：        {expense_total:>12,.2f} 元\n")
                        f.write(f"  净利润：        {net_profit:>12,.2f} 元\n")
                        if income_total > 0:
                            f.write(f"  利润率：        {profit_rate:>11.1f} %\n")
                    else:
                        f.write("  本月无收支记录\n")
                    
                    # 写入客户分析
                    f.write("\n三、客户分析\n")
                    if monthly_orders and customer_stats:
                        f.write("  主要客户（前5名）：\n")
                        for i, (customer, stats) in enumerate(sorted_customers[:5], 1):
                            f.write(f"    {i}. {customer}：{stats['count']}个订单，{stats['amount']:,.2f}元\n")
                    else:
                        f.write("  本月无客户数据\n")
                
                UserMessage.success(f"月度汇总报告已保存：{filename}")
                logger.info(f"月度汇总报告保存成功: {filename}")
                
            except Exception as e:
                UserMessage.error(f"保存月度汇总报告失败：{str(e)}")
        
    except Exception as e:
        UserMessage.error(f"生成月度汇总时发生错误: {str(e)}")
        logger.error(f"生成月度汇总异常: {str(e)}", exc_info=True)
# 从小白专版导入其他必要功能
def create_order():
    """创建订单"""
    print("\n" + "=" * 70)
    print("     新建加工订单")
    print("=" * 70)
    
    UserMessage.info("订单将自动保存到本地，位置：财务数据/本地订单/orders.json")
    
    try:
        # 使用向导创建订单
        order = create_order_interactive()
        
        if order:
            # 保存到本地
            storage = get_storage()
            if storage.save_order(order):
                UserMessage.success("订单创建成功！")
                print("\n📋 订单详情:")
                print(f"  订单编号: {order.order_no}")
                print(f"  客户名称: {order.customer}")
                print(f"  物品名称: {order.item_name}")
                print(f"  计价方式: {order.quantity} {order.pricing_unit} × {order.unit_price} 元")
                print(f"  订单金额: {order.order_amount:.2f} 元")
                if order.outsourced_cost > 0:
                    print(f"  外发成本: {order.outsourced_cost:.2f} 元")
                    print(f"  预计利润: {order.order_amount - order.outsourced_cost:.2f} 元")
                logger.info(f"订单创建成功: {order.order_no}")
            else:
                UserMessage.error("订单保存失败")
        else:
            UserMessage.info("订单创建已取消")
    except Exception as e:
        UserMessage.error(f"创建订单时发生错误: {str(e)}")
        logger.error(f"创建订单异常: {str(e)}", exc_info=True)

def list_orders():
    """查看订单列表"""
    print("\n" + "=" * 70)
    print("     订单列表")
    print("=" * 70)
    
    try:
        storage = get_storage()
        orders = storage.get_all_orders()
        
        if not orders:
            UserMessage.warning("暂无订单数据")
            UserMessage.info("请先创建订单（功能01）或生成示例数据（功能51）")
            return
        
        print(f"\n📊 共有 {len(orders)} 个订单\n")
        
        # 按日期排序（最新的在前）
        orders.sort(key=lambda x: x.get("order_date", ""), reverse=True)
        
        # 显示订单列表
        for i, order in enumerate(orders[-10:], 1):  # 只显示最近10个
            status_color = Color.GREEN if order['status'] == '已结算' else Color.WARNING
            print(f"{i:2d}. {order['order_no']} - {order['customer']}")
            print(f"    物品：{order['item_name']}")
            print(f"    金额：{order['order_amount']:.2f}元 | 状态：{status_color}{order['status']}{Color.ENDC}")
            print(f"    日期：{order['order_date']}")
            print()
        
        if len(orders) > 10:
            print(f"💡 显示最近10个订单，共有 {len(orders)} 个订单")
        
    except Exception as e:
        UserMessage.error(f"查看订单列表时发生错误: {str(e)}")
        logger.error(f"查看订单列表异常: {str(e)}", exc_info=True)

def generate_demo_data():
    """生成示例数据"""
    print("\n" + "=" * 70)
    print("     生成示例数据")
    print("=" * 70)
    
    UserMessage.info("正在生成示例数据，请稍候...")
    
    try:
        # 运行示例数据生成脚本
        import subprocess
        
        # 显示进度
        for i in range(1, 6):
            progress_bar(i, 5, "生成进度")
            time.sleep(0.8)
        
        result = subprocess.run([sys.executable, "create_oxidation_demo_data.py"], 
                              capture_output=True, text=True, encoding='utf-8')
        
        if result.returncode == 0:
            print(result.stdout)
            UserMessage.success("示例数据生成成功！")
            print(f"📁 文件位置：财务数据/示例数据/")
            logger.info("示例数据生成成功")
            
            # 同时生成一些收支记录示例
            generate_sample_transactions()
        else:
            UserMessage.error(f"生成失败：{result.stderr}")
            
    except Exception as e:
        UserMessage.error(f"生成示例数据时发生错误: {str(e)}")
        logger.error(f"生成示例数据异常: {str(e)}", exc_info=True)

def generate_sample_transactions():
    """生成示例收支记录"""
    try:
        sample_transactions = [
            # 收入记录
            {
                'type': '收入',
                'date': '2026-02-01',
                'amount': 15000.00,
                'category': '加工费收入',
                'description': '铝合金氧化加工费',
                'customer': '张三机械厂',
                'payment_method': 'G银行基本户',
                'has_invoice': True,
                'invoice_no': 'FP20260201001',
                'status': '已收款'
            },
            {
                'type': '收入',
                'date': '2026-02-03',
                'amount': 8500.00,
                'category': '加工费收入',
                'description': '不锈钢拉丝加工费',
                'customer': '李四五金',
                'payment_method': 'N银行',
                'has_invoice': False,
                'invoice_no': '',
                'status': '已收款'
            },
            # 支出记录
            {
                'type': '支出',
                'date': '2026-02-02',
                'amount': 3200.00,
                'category': '原材料-三酸',
                'description': '硫酸、硝酸采购',
                'payment_method': 'G银行基本户',
                'status': '已支付'
            },
            {
                'type': '支出',
                'date': '2026-02-04',
                'amount': 1800.00,
                'category': '外发加工-喷砂',
                'description': '外发喷砂处理费',
                'payment_method': '现金',
                'status': '已支付'
            },
            {
                'type': '支出',
                'date': '2026-02-05',
                'amount': 2500.00,
                'category': '水电费',
                'description': '1月份水电费',
                'payment_method': 'G银行基本户',
                'status': '已支付'
            },
            {
                'type': '支出',
                'date': '2026-02-06',
                'amount': 8000.00,
                'category': '工资',
                'description': '员工1月份工资',
                'payment_method': 'G银行基本户',
                'status': '已支付'
            }
        ]
        
        # 保存示例交易记录
        for trans in sample_transactions:
            finance_manager.add_transaction(trans)
        
        UserMessage.success("示例收支记录生成成功！")
        
    except Exception as e:
        logger.error(f"生成示例收支记录失败: {e}")

def show_tutorial():
    """显示使用教程"""
    print("\n" + "=" * 70)
    print("     使用教程")
    print("=" * 70)
    
    print(f"\n{Color.CYAN}📖 全能版功能介绍{Color.ENDC}")
    print("本版本专为小企业会计设计，涵盖财务管理的各个方面：")
    print()
    
    print(f"{Color.CYAN}【订单管理】{Color.ENDC} - 完整的订单生命周期管理")
    print("  ✅ 订单创建、编辑、查询、统计")
    print("  ✅ 收款记录、状态跟踪")
    print("  ✅ Excel导出、数据分析")
    
    print(f"\n{Color.CYAN}【收支管理】{Color.ENDC} - 全面的收支记录和分析")
    print("  ✅ 收入支出分类记录")
    print("  ✅ 银行流水管理")
    print("  ✅ 收支统计分析")
    
    print(f"\n{Color.CYAN}【税务管理】{Color.ENDC} - 专业的税务计算和申报")
    print("  ✅ 增值税自动计算")
    print("  ✅ 所得税预估")
    print("  ✅ 税务报表生成")
    
    print(f"\n{Color.CYAN}【报表中心】{Color.ENDC} - 专业的财务报表")
    print("  ✅ 利润表、资产负债表")
    print("  ✅ 现金流量表")
    print("  ✅ 月度、年度汇总")
    
    print(f"\n{Color.CYAN}【档案管理】{Color.ENDC} - 完整的档案管理系统")
    print("  ✅ 客户档案、供应商档案")
    print("  ✅ 合同管理、凭证管理")
    print("  ✅ 交易统计分析")
    
    print(f"\n{Color.CYAN}💡 快速开始建议{Color.ENDC}")
    print("1. 首次使用：生成示例数据（功能51）")
    print("2. 录入订单：新建加工订单（功能01）")
    print("3. 记录收支：记录收入（功能12）和支出（功能11）")
    print("4. 客户管理：建立客户档案（功能43）")
    print("5. 查看报表：利润表（功能31）和月度汇总（功能35）")
    print("6. 税务管理：增值税管理（功能21）")
    
    print(f"\n{Color.CYAN}🎯 适用场景{Color.ENDC}")
    print("✅ 小型制造企业财务管理")
    print("✅ 加工贸易企业账务处理")
    print("✅ 个体工商户记账报税")
    print("✅ 小规模纳税人税务管理")

def show_logs():
    """查看运行日志"""
    print("\n" + "=" * 70)
    print("     运行日志")
    print("=" * 70)
    
    try:
        from pathlib import Path
        
        log_dir = Path("财务数据/运行日志")
        if not log_dir.exists():
            UserMessage.warning("未找到日志目录")
            return
        
        # 查找今天的日志文件
        today = datetime.now().strftime('%Y%m%d')
        log_file = log_dir / f"app_{today}.log"
        
        if not log_file.exists():
            UserMessage.warning("未找到今天的日志文件")
            return
        
        print(f"\n📋 今天的运行日志：")
        print("-" * 70)
        
        # 读取并显示最后50行日志
        with open(log_file, 'r', encoding='utf-8') as f:
            lines = f.readlines()
            
        if not lines:
            print("日志文件为空")
            return
        
        # 显示最后50行
        recent_lines = lines[-50:] if len(lines) > 50 else lines
        
        for line in recent_lines:
            line = line.strip()
            if 'ERROR' in line:
                print(f"{Color.FAIL}{line}{Color.ENDC}")
            elif 'WARNING' in line:
                print(f"{Color.WARNING}{line}{Color.ENDC}")
            elif 'SUCCESS' in line:
                print(f"{Color.GREEN}{line}{Color.ENDC}")
            else:
                print(line)
        
        if len(lines) > 50:
            print(f"\n💡 显示最近50条日志，共有 {len(lines)} 条记录")
        
        print("-" * 70)
        print(f"📁 完整日志文件：{log_file}")
        
    except Exception as e:
        UserMessage.error(f"查看日志时发生错误: {str(e)}")

def transaction_statistics():
    """收支统计"""
    print("\n" + "=" * 70)
    print("     收支统计")
    print("=" * 70)
    
    try:
        transactions = finance_manager.load_transactions()
        
        if not transactions:
            UserMessage.warning("暂无收支记录")
            return
        
        # 选择统计期间
        print("\n统计期间：")
        print("  1. 本月")
        print("  2. 本年")
        print("  3. 全部")
        print("  4. 自定义")
        
        period_choice = input("选择统计期间（1-4）: ").strip()
        
        today = datetime.now()
        if period_choice == "1":  # 本月
            start_date = today.replace(day=1).strftime("%Y-%m-%d")
            end_date = today.strftime("%Y-%m-%d")
            period_name = f"{today.year}年{today.month}月"
        elif period_choice == "2":  # 本年
            start_date = today.replace(month=1, day=1).strftime("%Y-%m-%d")
            end_date = today.strftime("%Y-%m-%d")
            period_name = f"{today.year}年"
        elif period_choice == "3":  # 全部
            start_date = "2000-01-01"
            end_date = "2099-12-31"
            period_name = "全部期间"
        else:  # 自定义
            start_date = input("开始日期（格式：2026-01-01）: ").strip()
            end_date = input("结束日期（格式：2026-12-31）: ").strip()
            period_name = f"{start_date} 至 {end_date}"
        
        # 筛选期间内的交易
        period_transactions = []
        for trans in transactions:
            trans_date = trans.get('date', '')
            if start_date <= trans_date <= end_date:
                period_transactions.append(trans)
        
        if not period_transactions:
            UserMessage.warning(f"{period_name}期间无交易记录")
            return
        
        # 统计分析
        income_total = sum(t['amount'] for t in period_transactions if t['type'] == '收入')
        expense_total = sum(t['amount'] for t in period_transactions if t['type'] == '支出')
        net_profit = income_total - expense_total
        
        # 分类统计
        income_by_category = {}
        expense_by_category = {}
        by_payment_method = {}
        
        for trans in period_transactions:
            category = trans.get('category', '未分类')
            payment_method = trans.get('payment_method', '未知')
            amount = trans.get('amount', 0)
            
            if trans['type'] == '收入':
                if category not in income_by_category:
                    income_by_category[category] = 0
                income_by_category[category] += amount
            else:
                if category not in expense_by_category:
                    expense_by_category[category] = 0
                expense_by_category[category] += amount
            
            # 按支付方式统计
            if payment_method not in by_payment_method:
                by_payment_method[payment_method] = {'income': 0, 'expense': 0}
            
            if trans['type'] == '收入':
                by_payment_method[payment_method]['income'] += amount
            else:
                by_payment_method[payment_method]['expense'] += amount
        
        # 显示统计结果
        print(f"\n" + "=" * 70)
        print(f"                收支统计报告")
        print(f"              {period_name}")
        print("=" * 70)
        
        print(f"\n{Color.CYAN}总体情况：{Color.ENDC}")
        print(f"  交易笔数：      {len(period_transactions):>8} 笔")
        print(f"  总收入：        {Color.GREEN}{income_total:>12,.2f} 元{Color.ENDC}")
        print(f"  总支出：        {Color.FAIL}{expense_total:>12,.2f} 元{Color.ENDC}")
        profit_color = Color.GREEN if net_profit >= 0 else Color.FAIL
        print(f"  净利润：        {profit_color}{net_profit:>12,.2f} 元{Color.ENDC}")
        
        if income_total > 0:
            profit_rate = (net_profit / income_total) * 100
            print(f"  利润率：        {profit_color}{profit_rate:>11.1f} %{Color.ENDC}")
        
        # 收入分类统计
        if income_by_category:
            print(f"\n{Color.CYAN}收入分类：{Color.ENDC}")
            sorted_income = sorted(income_by_category.items(), key=lambda x: x[1], reverse=True)
            for category, amount in sorted_income:
                percentage = (amount / income_total * 100) if income_total > 0 else 0
                print(f"  {category:<15} {amount:>12,.2f} 元 ({percentage:>5.1f}%)")
        
        # 支出分类统计
        if expense_by_category:
            print(f"\n{Color.CYAN}支出分类：{Color.ENDC}")
            sorted_expense = sorted(expense_by_category.items(), key=lambda x: x[1], reverse=True)
            for category, amount in sorted_expense:
                percentage = (amount / expense_total * 100) if expense_total > 0 else 0
                print(f"  {category:<15} {amount:>12,.2f} 元 ({percentage:>5.1f}%)")
        
        # 支付方式统计
        if by_payment_method:
            print(f"\n{Color.CYAN}支付方式：{Color.ENDC}")
            for method, amounts in by_payment_method.items():
                total = amounts['income'] + amounts['expense']
                if total > 0:
                    print(f"  {method}：收入 {amounts['income']:,.2f} 元，支出 {amounts['expense']:,.2f} 元")
        
        print("=" * 70)
        
    except Exception as e:
        UserMessage.error(f"收支统计时发生错误: {str(e)}")
        logger.error(f"收支统计异常: {str(e)}", exc_info=True)

def bank_statement_management():
    """银行流水管理"""
    print("\n" + "=" * 70)
    print("     银行流水管理")
    print("=" * 70)
    
    try:
        from 银行流水管理 import bank_manager
        
        print("\n银行流水管理功能：")
        print("  1. 导入银行流水")
        print("  2. 查看银行流水")
        print("  3. 自动对账")
        print("  4. 对账报告")
        
        choice = input("请选择功能（1-4）: ").strip()
        
        if choice == "1":  # 导入银行流水
            print("\n支持的银行：")
            print("  1. G银行基本户")
            print("  2. N银行")
            print("  3. 其他银行")
            
            bank_choice = input("选择银行（1-3）: ").strip()
            bank_names = {"1": "G银行基本户", "2": "N银行", "3": "其他银行"}
            bank_name = bank_names.get(bank_choice, "其他银行")
            
            file_path = input("Excel文件路径: ").strip()
            if not file_path:
                UserMessage.info("操作已取消")
                return
            
            if not os.path.exists(file_path):
                UserMessage.error("文件不存在")
                return
            
            success, message = bank_manager.import_from_excel(file_path, bank_name)
            if success:
                UserMessage.success(message)
            else:
                UserMessage.error(message)
        
        elif choice == "2":  # 查看银行流水
            print("\n选择银行：")
            print("  1. G银行基本户")
            print("  2. N银行")
            print("  3. 全部银行")
            
            bank_choice = input("选择银行（1-3）: ").strip()
            bank_names = {"1": "G银行基本户", "2": "N银行"}
            bank_name = bank_names.get(bank_choice) if bank_choice in bank_names else None
            
            statements = financial_manager.load_bank_statements(bank_name)
            
            if not statements:
                UserMessage.warning("暂无银行流水记录")
                return
            
            print(f"\n📊 银行流水记录（共{len(statements)}条）：")
            
            # 显示最近20条
            recent_statements = sorted(statements, key=lambda x: x.get('date', ''), reverse=True)[:20]
            
            for i, stmt in enumerate(recent_statements, 1):
                type_color = Color.GREEN if stmt.get('type') == '收入' else Color.FAIL
                matched_mark = "✓" if stmt.get('matched') else "○"
                print(f"{i:2d}. {stmt.get('date')} - {type_color}{stmt.get('type')}{Color.ENDC} {matched_mark}")
                print(f"    金额：{stmt.get('amount', 0):,.2f}元 | 银行：{stmt.get('bank_name', '')}")
                print(f"    摘要：{stmt.get('description', '')}")
                print()
        
        elif choice == "3":  # 自动对账
            print("\n选择银行：")
            print("  1. G银行基本户")
            print("  2. N银行")
            
            bank_choice = input("选择银行（1-2）: ").strip()
            bank_names = {"1": "G银行基本户", "2": "N银行"}
            bank_name = bank_names.get(bank_choice)
            
            if not bank_name:
                UserMessage.error("请选择有效的银行")
                return
            
            UserMessage.info("正在执行自动对账...")
            result = bank_manager.auto_match_transactions(bank_name)
            
            if 'error' in result:
                UserMessage.error(f"对账失败：{result['error']}")
            else:
                UserMessage.success(f"对账完成！")
                print(f"  匹配成功：{result['matched_count']} 笔")
                print(f"  未匹配银行流水：{result['unmatched_statements']} 笔")
                print(f"  未匹配收支记录：{result['unmatched_transactions']} 笔")
        
        elif choice == "4":  # 对账报告
            print("\n选择银行：")
            print("  1. G银行基本户")
            print("  2. N银行")
            
            bank_choice = input("选择银行（1-2）: ").strip()
            bank_names = {"1": "G银行基本户", "2": "N银行"}
            bank_name = bank_names.get(bank_choice)
            
            if not bank_name:
                UserMessage.error("请选择有效的银行")
                return
            
            start_date = input("开始日期（格式：2026-01-01）: ").strip()
            end_date = input("结束日期（格式：2026-12-31）: ").strip()
            
            if not start_date or not end_date:
                UserMessage.info("操作已取消")
                return
            
            UserMessage.info("正在生成对账报告...")
            report = bank_manager.generate_reconciliation_report(bank_name, start_date, end_date)
            
            if 'error' in report:
                UserMessage.error(f"生成报告失败：{report['error']}")
            else:
                print(f"\n对账报告 - {report['bank_name']} ({report['period']})")
                print("-" * 50)
                print(f"银行流水：{report['bank_summary']['total_statements']}笔")
                print(f"  收入：{report['bank_summary']['income']:,.2f}元")
                print(f"  支出：{report['bank_summary']['expense']:,.2f}元")
                print(f"记账记录：{report['record_summary']['total_transactions']}笔")
                print(f"  收入：{report['record_summary']['income']:,.2f}元")
                print(f"  支出：{report['record_summary']['expense']:,.2f}元")
                print(f"匹配率：{report['reconciliation']['match_rate']:.1f}%")
                
                if UserMessage.confirm("是否导出详细报告到Excel？"):
                    output_file = bank_manager.export_reconciliation_report(report)
                    if output_file:
                        UserMessage.success(f"报告已导出：{output_file}")
                    else:
                        UserMessage.error("导出失败")
        
    except ImportError:
        UserMessage.error("银行流水管理模块加载失败")
    except Exception as e:
        UserMessage.error(f"银行流水管理时发生错误: {str(e)}")
        logger.error(f"银行流水管理异常: {str(e)}", exc_info=True)

def export_transaction_report():
    """导出收支报表"""
    print("\n" + "=" * 70)
    print("     导出收支报表")
    print("=" * 70)
    
    try:
        print("\n导出选项：")
        print("  1. 导出全部收支记录")
        print("  2. 导出指定期间记录")
        
        choice = input("请选择（1-2）: ").strip()
        
        if choice == "1":
            # 导出全部
            output_file = financial_manager.export_transactions_to_excel()
        elif choice == "2":
            # 导出指定期间
            start_date = input("开始日期（格式：2026-01-01）: ").strip()
            end_date = input("结束日期（格式：2026-12-31）: ").strip()
            
            if not start_date or not end_date:
                UserMessage.info("操作已取消")
                return
            
            output_file = financial_manager.export_transactions_to_excel(start_date, end_date)
        else:
            UserMessage.error("无效选择")
            return
        
        if output_file:
            UserMessage.success(f"收支报表导出成功：{output_file}")
            logger.info(f"收支报表导出成功: {output_file}")
        else:
            UserMessage.error("导出失败，可能是没有数据或文件写入错误")
        
    except Exception as e:
        UserMessage.error(f"导出收支报表时发生错误: {str(e)}")
        logger.error(f"导出收支报表异常: {str(e)}", exc_info=True)

def income_tax_calculation():
    """所得税计算"""
    print("\n" + "=" * 70)
    print("     所得税计算")
    print("=" * 70)
    
    try:
        # 选择计算期间
        print("\n计算期间：")
        print("  1. 本年度")
        print("  2. 自定义年度")
        
        period_choice = input("选择计算期间（1-2）: ").strip()
        
        if period_choice == "1":
            year = datetime.now().year
        else:
            year_input = input("请输入年份（如：2026）: ").strip()
            try:
                year = int(year_input)
            except ValueError:
                UserMessage.error("请输入有效的年份")
                return
        
        start_date = f"{year}-01-01"
        end_date = f"{year}-12-31"
        
        # 获取年度收支数据
        stats = financial_manager.get_transaction_statistics(start_date, end_date)
        
        total_income = stats['total_income']
        total_expense = stats['total_expense']
        net_profit = stats['net_profit']
        
        print(f"\n" + "=" * 70)
        print(f"                所得税计算表")
        print(f"                {year}年度")
        print("=" * 70)
        
        print(f"\n{Color.CYAN}一、收入情况{Color.ENDC}")
        print(f"  营业收入：      {total_income:>12,.2f} 元")
        
        print(f"\n{Color.CYAN}二、成本费用{Color.ENDC}")
        print(f"  营业成本及费用：{total_expense:>12,.2f} 元")
        
        print(f"\n{Color.CYAN}三、利润计算{Color.ENDC}")
        profit_color = Color.GREEN if net_profit >= 0 else Color.FAIL
        print(f"  利润总额：      {profit_color}{net_profit:>12,.2f} 元{Color.ENDC}")
        
        # 小型微利企业所得税计算
        if net_profit <= 0:
            taxable_income = 0
            tax_amount = 0
            tax_rate = 0
            print(f"\n{Color.GREEN}💡 本年度亏损，无需缴纳所得税{Color.ENDC}")
        elif net_profit <= 1000000:  # 100万以下
            taxable_income = net_profit
            tax_amount = net_profit * 0.025  # 2.5%优惠税率
            tax_rate = 2.5
            print(f"\n{Color.GREEN}💡 符合小型微利企业条件，享受2.5%优惠税率{Color.ENDC}")
        elif net_profit <= 3000000:  # 100-300万
            # 100万以下部分按2.5%，超过部分按5%
            tax_amount_1 = 1000000 * 0.025
            tax_amount_2 = (net_profit - 1000000) * 0.05
            tax_amount = tax_amount_1 + tax_amount_2
            taxable_income = net_profit
            tax_rate = (tax_amount / net_profit) * 100
            print(f"\n{Color.GREEN}💡 符合小型微利企业条件，分段计税{Color.ENDC}")
        else:  # 300万以上
            taxable_income = net_profit
            tax_amount = net_profit * 0.25  # 25%标准税率
            tax_rate = 25
            print(f"\n{Color.WARNING}💡 按标准税率25%计算{Color.ENDC}")
        
        print(f"\n{Color.CYAN}四、所得税计算{Color.ENDC}")
        print(f"  应纳税所得额：  {taxable_income:>12,.2f} 元")
        print(f"  适用税率：      {tax_rate:>11.1f} %")
        print(f"  应纳所得税：    {Color.WARNING}{tax_amount:>12,.2f} 元{Color.ENDC}")
        
        # 计算税后利润
        after_tax_profit = net_profit - tax_amount
        print(f"  税后利润：      {Color.GREEN if after_tax_profit >= 0 else Color.FAIL}{after_tax_profit:>12,.2f} 元{Color.ENDC}")
        
        print("=" * 70)
        
        # 询问是否保存计算结果
        if UserMessage.confirm("是否保存所得税计算表？"):
            tax_dir = "财务数据/税务资料"
            os.makedirs(tax_dir, exist_ok=True)
            
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"{tax_dir}/所得税计算表_{year}年_{timestamp}.txt"
            
            try:
                with open(filename, 'w', encoding='utf-8') as f:
                    f.write(f"所得税计算表\n")
                    f.write(f"{year}年度\n")
                    f.write("=" * 50 + "\n\n")
                    
                    f.write("一、收入情况\n")
                    f.write(f"  营业收入：      {total_income:>12,.2f} 元\n\n")
                    
                    f.write("二、成本费用\n")
                    f.write(f"  营业成本及费用：{total_expense:>12,.2f} 元\n\n")
                    
                    f.write("三、利润计算\n")
                    f.write(f"  利润总额：      {net_profit:>12,.2f} 元\n\n")
                    
                    f.write("四、所得税计算\n")
                    f.write(f"  应纳税所得额：  {taxable_income:>12,.2f} 元\n")
                    f.write(f"  适用税率：      {tax_rate:>11.1f} %\n")
                    f.write(f"  应纳所得税：    {tax_amount:>12,.2f} 元\n")
                    f.write(f"  税后利润：      {after_tax_profit:>12,.2f} 元\n")
                
                UserMessage.success(f"所得税计算表已保存：{filename}")
                logger.info(f"所得税计算表保存成功: {filename}")
                
            except Exception as e:
                UserMessage.error(f"保存所得税计算表失败：{str(e)}")
        
    except Exception as e:
        UserMessage.error(f"所得税计算时发生错误: {str(e)}")
        logger.error(f"所得税计算异常: {str(e)}", exc_info=True)

def tax_report_center():
    """税务报表中心"""
    print("\n" + "=" * 70)
    print("     税务报表中心")
    print("=" * 70)
    
    try:
        print("\n税务报表类型：")
        print("  1. 增值税申报表")
        print("  2. 所得税申报表")
        print("  3. 税务汇总表")
        
        choice = input("请选择报表类型（1-3）: ").strip()
        
        if choice == "1":
            # 增值税申报表
            period = input("申报期间（格式：2026-01，直接回车使用本月）: ").strip()
            if not period:
                today = datetime.now()
                period = f"{today.year}-{today.month:02d}"
            
            try:
                year, month = period.split('-')
                year, month = int(year), int(month)
                start_date = f"{year}-{month:02d}-01"
                
                if month == 12:
                    end_date = f"{year}-12-31"
                else:
                    next_month = datetime(year, month + 1, 1)
                    last_day = next_month - timedelta(days=1)
                    end_date = last_day.strftime("%Y-%m-%d")
                
                vat_info = financial_manager.calculate_vat(start_date, end_date)
                
                print(f"\n增值税申报表 - {period}")
                print("-" * 50)
                print(f"申报期间：{vat_info['period']}")
                print(f"含税销售额：{vat_info['taxable_income']:,.2f} 元")
                print(f"不含税销售额：{vat_info['income_without_tax']:,.2f} 元")
                print(f"应纳税额：{vat_info['actual_vat']:,.2f} 元")
                
                if vat_info['exempt_reason']:
                    print(f"减免说明：{vat_info['exempt_reason']}")
                
            except ValueError:
                UserMessage.error("期间格式错误，请使用 YYYY-MM 格式")
        
        elif choice == "2":
            UserMessage.info("请使用功能22进行所得税计算")
        
        elif choice == "3":
            # 税务汇总表
            year = input("汇总年度（直接回车使用本年）: ").strip()
            if not year:
                year = str(datetime.now().year)
            
            try:
                year = int(year)
                
                # 按季度汇总增值税
                print(f"\n{year}年度税务汇总表")
                print("=" * 50)
                
                quarterly_vat = []
                for quarter in range(1, 5):
                    start_month = (quarter - 1) * 3 + 1
                    end_month = quarter * 3
                    
                    start_date = f"{year}-{start_month:02d}-01"
                    if end_month == 12:
                        end_date = f"{year}-12-31"
                    else:
                        next_month = datetime(year, end_month + 1, 1)
                        last_day = next_month - timedelta(days=1)
                        end_date = last_day.strftime("%Y-%m-%d")
                    
                    vat_info = financial_manager.calculate_vat(start_date, end_date)
                    quarterly_vat.append(vat_info)
                    
                    print(f"第{quarter}季度：")
                    print(f"  销售额：{vat_info['income_without_tax']:>10,.2f} 元")
                    print(f"  增值税：{vat_info['actual_vat']:>10,.2f} 元")
                
                # 年度汇总
                annual_sales = sum(q['income_without_tax'] for q in quarterly_vat)
                annual_vat = sum(q['actual_vat'] for q in quarterly_vat)
                
                print(f"\n年度汇总：")
                print(f"  全年销售额：{annual_sales:>12,.2f} 元")
                print(f"  全年增值税：{annual_vat:>12,.2f} 元")
                
            except ValueError:
                UserMessage.error("请输入有效的年份")
        
    except Exception as e:
        UserMessage.error(f"税务报表时发生错误: {str(e)}")
        logger.error(f"税务报表异常: {str(e)}", exc_info=True)

def tax_document_archive():
    """税务资料归档"""
    print("\n" + "=" * 70)
    print("     税务资料归档")
    print("=" * 70)
    
    try:
        archive_dir = "财务数据/税务资料"
        
        print("\n归档管理功能：")
        print("  1. 查看已归档资料")
        print("  2. 归档当前税务资料")
        print("  3. 清理过期资料")
        
        choice = input("请选择功能（1-3）: ").strip()
        
        if choice == "1":
            # 查看已归档资料
            if not os.path.exists(archive_dir):
                UserMessage.warning("税务资料目录不存在")
                return
            
            files = [f for f in os.listdir(archive_dir) if f.endswith(('.txt', '.xlsx', '.pdf'))]
            
            if not files:
                UserMessage.warning("暂无归档资料")
                return
            
            print(f"\n📁 已归档税务资料（共{len(files)}个文件）：")
            
            # 按类型分组显示
            vat_files = [f for f in files if '增值税' in f]
            income_tax_files = [f for f in files if '所得税' in f]
            other_files = [f for f in files if f not in vat_files and f not in income_tax_files]
            
            if vat_files:
                print(f"\n  增值税资料：")
                for f in sorted(vat_files):
                    print(f"    {f}")
            
            if income_tax_files:
                print(f"\n  所得税资料：")
                for f in sorted(income_tax_files):
                    print(f"    {f}")
            
            if other_files:
                print(f"\n  其他税务资料：")
                for f in sorted(other_files):
                    print(f"    {f}")
        
        elif choice == "2":
            # 归档当前税务资料
            UserMessage.info("正在归档当前税务资料...")
            
            # 生成当前月度增值税资料
            today = datetime.now()
            current_month = f"{today.year}-{today.month:02d}"
            
            start_date = f"{today.year}-{today.month:02d}-01"
            if today.month == 12:
                end_date = f"{today.year}-12-31"
            else:
                next_month = datetime(today.year, today.month + 1, 1)
                last_day = next_month - timedelta(days=1)
                end_date = last_day.strftime("%Y-%m-%d")
            
            vat_info = financial_manager.calculate_vat(start_date, end_date)
            
            # 保存增值税资料
            os.makedirs(archive_dir, exist_ok=True)
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            vat_filename = f"{archive_dir}/增值税资料_{current_month}_{timestamp}.txt"
            
            with open(vat_filename, 'w', encoding='utf-8') as f:
                f.write(f"增值税申报资料\n")
                f.write(f"申报期间：{vat_info['period']}\n")
                f.write("=" * 40 + "\n\n")
                
                f.write("销售情况：\n")
                f.write(f"  含税销售额：{vat_info['taxable_income']:>12,.2f} 元\n")
                f.write(f"  不含税销售额：{vat_info['income_without_tax']:>12,.2f} 元\n")
                f.write(f"  免税销售额：{vat_info['tax_free_income']:>12,.2f} 元\n\n")
                
                f.write("税额计算：\n")
                f.write(f"  征收率：{vat_info['vat_rate']*100:>11.1f} %\n")
                f.write(f"  应纳税额：{vat_info['vat_amount']:>12,.2f} 元\n")
                f.write(f"  实际缴纳：{vat_info['actual_vat']:>12,.2f} 元\n")
                
                if vat_info['exempt_reason']:
                    f.write(f"\n减免说明：{vat_info['exempt_reason']}\n")
            
            UserMessage.success(f"税务资料归档成功：{vat_filename}")
            logger.info(f"税务资料归档: {vat_filename}")
        
        elif choice == "3":
            # 清理过期资料
            if not os.path.exists(archive_dir):
                UserMessage.warning("税务资料目录不存在")
                return
            
            cutoff_date = datetime.now() - timedelta(days=365*3)  # 3年前
            
            files = os.listdir(archive_dir)
            old_files = []
            
            for filename in files:
                file_path = os.path.join(archive_dir, filename)
                if os.path.isfile(file_path):
                    file_time = datetime.fromtimestamp(os.path.getmtime(file_path))
                    if file_time < cutoff_date:
                        old_files.append(filename)
            
            if not old_files:
                UserMessage.info("没有需要清理的过期资料")
                return
            
            print(f"\n发现 {len(old_files)} 个超过3年的资料文件：")
            for f in old_files[:10]:  # 只显示前10个
                print(f"  {f}")
            
            if len(old_files) > 10:
                print(f"  ... 还有 {len(old_files)-10} 个文件")
            
            if UserMessage.confirm("确定要删除这些过期资料吗？"):
                deleted_count = 0
                for filename in old_files:
                    try:
                        os.remove(os.path.join(archive_dir, filename))
                        deleted_count += 1
                    except Exception as e:
                        logger.error(f"删除文件失败 {filename}: {e}")
                
                UserMessage.success(f"已清理 {deleted_count} 个过期资料文件")
                logger.info(f"清理过期税务资料: {deleted_count} 个文件")
        
    except Exception as e:
        UserMessage.error(f"税务资料归档时发生错误: {str(e)}")
        logger.error(f"税务资料归档异常: {str(e)}", exc_info=True)

def balance_sheet_report():
    """资产负债表"""
    print("\n" + "=" * 70)
    print("     资产负债表")
    print("=" * 70)
    
    try:
        # 选择报表日期
        date_str = input("报表日期（格式：2026-12-31，直接回车使用今天）: ").strip()
        if not date_str:
            date_str = datetime.now().strftime("%Y-%m-%d")
        
        try:
            report_date = datetime.strptime(date_str, "%Y-%m-%d")
        except ValueError:
            UserMessage.error("日期格式错误")
            return
        
        # 获取截至报表日的数据
        end_date = date_str
        start_date = "2000-01-01"  # 从很早开始累计
        
        stats = financial_manager.get_transaction_statistics(start_date, end_date)
        
        # 简化的资产负债表（适合小企业）
        print(f"\n" + "=" * 70)
        print(f"                资产负债表")
        print(f"              截至 {date_str}")
        print("=" * 70)
        
        # 资产部分
        print(f"\n{Color.CYAN}资产{Color.ENDC}")
        
        # 流动资产（简化计算）
        cash_balance = 0  # 现金余额（需要从银行流水计算）
        accounts_receivable = 0  # 应收账款（从未收款订单计算）
        
        # 从订单计算应收账款
        try:
            orders = get_storage().get_all_orders()
            for order in orders:
                if order.get('order_date', '') <= end_date:
                    accounts_receivable += order.get('unpaid_amount', 0)
        except:
            pass
        
        # 从银行流水计算现金余额
        try:
            from 银行流水管理 import bank_manager
            statements = financial_manager.load_bank_statements()
            if statements:
                # 取最新的余额
                latest_statement = max(statements, key=lambda x: x.get('date', ''))
                if latest_statement.get('date', '') <= end_date:
                    cash_balance = latest_statement.get('balance', 0)
        except:
            # 如果没有银行流水，用收支差额估算
            cash_balance = max(0, stats['net_profit'])
        
        current_assets = cash_balance + accounts_receivable
        
        print(f"  流动资产：")
        print(f"    货币资金        {cash_balance:>15,.2f}")
        print(f"    应收账款        {accounts_receivable:>15,.2f}")
        print(f"    流动资产合计    {current_assets:>15,.2f}")
        
        # 固定资产（简化）
        fixed_assets = 0  # 小企业通常固定资产较少，暂设为0
        print(f"  固定资产：")
        print(f"    固定资产净值    {fixed_assets:>15,.2f}")
        
        total_assets = current_assets + fixed_assets
        print(f"  {Color.BOLD}资产总计          {total_assets:>15,.2f}{Color.ENDC}")
        
        # 负债和所有者权益部分
        print(f"\n{Color.CYAN}负债和所有者权益{Color.ENDC}")
        
        # 流动负债
        accounts_payable = 0  # 应付账款（简化为0）
        tax_payable = 0  # 应交税费
        
        # 计算应交税费
        current_year = report_date.year
        year_start = f"{current_year}-01-01"
        year_stats = financial_manager.get_transaction_statistics(year_start, end_date)
        
        if year_stats['total_income'] > 0:
            # 估算应交增值税
            vat_info = financial_manager.calculate_vat(year_start, end_date)
            tax_payable += vat_info['actual_vat']
            
            # 估算应交所得税
            if year_stats['net_profit'] > 0:
                if year_stats['net_profit'] <= 1000000:
                    tax_payable += year_stats['net_profit'] * 0.025
                else:
                    tax_payable += year_stats['net_profit'] * 0.05  # 简化计算
        
        current_liabilities = accounts_payable + tax_payable
        
        print(f"  流动负债：")
        print(f"    应付账款        {accounts_payable:>15,.2f}")
        print(f"    应交税费        {tax_payable:>15,.2f}")
        print(f"    流动负债合计    {current_liabilities:>15,.2f}")
        
        # 所有者权益
        paid_capital = 100000  # 实收资本（假设10万）
        retained_earnings = total_assets - current_liabilities - paid_capital
        
        owners_equity = paid_capital + retained_earnings
        
        print(f"  所有者权益：")
        print(f"    实收资本        {paid_capital:>15,.2f}")
        print(f"    未分配利润      {retained_earnings:>15,.2f}")
        print(f"    所有者权益合计  {owners_equity:>15,.2f}")
        
        total_liab_equity = current_liabilities + owners_equity
        print(f"  {Color.BOLD}负债和所有者权益总计 {total_liab_equity:>12,.2f}{Color.ENDC}")
        
        # 平衡检查
        balance_diff = total_assets - total_liab_equity
        if abs(balance_diff) < 0.01:
            print(f"\n{Color.GREEN}✅ 资产负债表平衡{Color.ENDC}")
        else:
            print(f"\n{Color.WARNING}⚠️ 不平衡差额：{balance_diff:,.2f} 元{Color.ENDC}")
        
        print("=" * 70)
        
        # 询问是否保存
        if UserMessage.confirm("是否保存此资产负债表？"):
            report_dir = "财务数据/月度报表"
            os.makedirs(report_dir, exist_ok=True)
            
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"{report_dir}/资产负债表_{date_str.replace('-', '')}_{timestamp}.txt"
            
            try:
                with open(filename, 'w', encoding='utf-8') as f:
                    f.write(f"资产负债表\n")
                    f.write(f"截至 {date_str}\n")
                    f.write("=" * 50 + "\n\n")
                    
                    f.write("资产\n")
                    f.write("  流动资产：\n")
                    f.write(f"    货币资金        {cash_balance:>15,.2f}\n")
                    f.write(f"    应收账款        {accounts_receivable:>15,.2f}\n")
                    f.write(f"    流动资产合计    {current_assets:>15,.2f}\n")
                    f.write("  固定资产：\n")
                    f.write(f"    固定资产净值    {fixed_assets:>15,.2f}\n")
                    f.write(f"  资产总计          {total_assets:>15,.2f}\n\n")
                    
                    f.write("负债和所有者权益\n")
                    f.write("  流动负债：\n")
                    f.write(f"    应付账款        {accounts_payable:>15,.2f}\n")
                    f.write(f"    应交税费        {tax_payable:>15,.2f}\n")
                    f.write(f"    流动负债合计    {current_liabilities:>15,.2f}\n")
                    f.write("  所有者权益：\n")
                    f.write(f"    实收资本        {paid_capital:>15,.2f}\n")
                    f.write(f"    未分配利润      {retained_earnings:>15,.2f}\n")
                    f.write(f"    所有者权益合计  {owners_equity:>15,.2f}\n")
                    f.write(f"  负债和所有者权益总计 {total_liab_equity:>12,.2f}\n")
                
                UserMessage.success(f"资产负债表已保存：{filename}")
                logger.info(f"资产负债表保存成功: {filename}")
                
            except Exception as e:
                UserMessage.error(f"保存资产负债表失败：{str(e)}")
        
    except Exception as e:
        UserMessage.error(f"生成资产负债表时发生错误: {str(e)}")
        logger.error(f"生成资产负债表异常: {str(e)}", exc_info=True)

def cash_flow_statement():
    """现金流量表"""
    print("\n" + "=" * 70)
    print("     现金流量表")
    print("=" * 70)
    
    try:
        # 选择报表期间
        print("\n报表期间：")
        print("  1. 本月")
        print("  2. 本年")
        print("  3. 自定义")
        
        period_choice = input("选择报表期间（1-3）: ").strip()
        
        today = datetime.now()
        if period_choice == "1":  # 本月
            start_date = today.replace(day=1)
            end_date = today
            period_name = f"{today.year}年{today.month}月"
        elif period_choice == "2":  # 本年
            start_date = today.replace(month=1, day=1)
            end_date = today
            period_name = f"{today.year}年"
        else:  # 自定义
            start_str = input("开始日期（格式：2026-01-01）: ").strip()
            end_str = input("结束日期（格式：2026-12-31）: ").strip()
            try:
                start_date = datetime.strptime(start_str, "%Y-%m-%d")
                end_date = datetime.strptime(end_str, "%Y-%m-%d")
                period_name = f"{start_str} 至 {end_str}"
            except ValueError:
                UserMessage.error("日期格式错误")
                return
        
        start_date_str = start_date.strftime("%Y-%m-%d")
        end_date_str = end_date.strftime("%Y-%m-%d")
        
        # 获取期间内的交易数据
        stats = financial_manager.get_transaction_statistics(start_date_str, end_date_str)
        
        print(f"\n" + "=" * 70)
        print(f"                现金流量表")
        print(f"              {period_name}")
        print("=" * 70)
        
        # 一、经营活动现金流量
        print(f"\n{Color.CYAN}一、经营活动产生的现金流量{Color.ENDC}")
        
        # 销售商品收到的现金
        cash_from_sales = stats['total_income']
        print(f"  销售商品、提供劳务收到的现金  {cash_from_sales:>12,.2f}")
        
        # 经营活动现金流入小计
        operating_inflow = cash_from_sales
        print(f"  经营活动现金流入小计          {operating_inflow:>12,.2f}")
        
        # 购买商品支付的现金
        material_expense = 0
        labor_expense = 0
        other_expense = 0
        
        for category, amount in stats['expense_by_category'].items():
            if '原材料' in category or '采购' in category:
                material_expense += amount
            elif '工资' in category or '人工' in category:
                labor_expense += amount
            else:
                other_expense += amount
        
        print(f"  购买商品、接受劳务支付的现金  {material_expense:>12,.2f}")
        print(f"  支付给职工的现金              {labor_expense:>12,.2f}")
        print(f"  支付的各项税费                {0:>12,.2f}")  # 简化处理
        print(f"  支付其他与经营活动有关的现金  {other_expense:>12,.2f}")
        
        operating_outflow = material_expense + labor_expense + other_expense
        print(f"  经营活动现金流出小计          {operating_outflow:>12,.2f}")
        
        net_operating_flow = operating_inflow - operating_outflow
        flow_color = Color.GREEN if net_operating_flow >= 0 else Color.FAIL
        print(f"  {Color.BOLD}经营活动产生的现金流量净额    {flow_color}{net_operating_flow:>12,.2f}{Color.ENDC}")
        
        # 二、投资活动现金流量（小企业通常较少）
        print(f"\n{Color.CYAN}二、投资活动产生的现金流量{Color.ENDC}")
        print(f"  投资活动现金流入小计          {0:>12,.2f}")
        print(f"  投资活动现金流出小计          {0:>12,.2f}")
        print(f"  投资活动产生的现金流量净额    {0:>12,.2f}")
        
        # 三、筹资活动现金流量（小企业通常较少）
        print(f"\n{Color.CYAN}三、筹资活动产生的现金流量{Color.ENDC}")
        print(f"  筹资活动现金流入小计          {0:>12,.2f}")
        print(f"  筹资活动现金流出小计          {0:>12,.2f}")
        print(f"  筹资活动产生的现金流量净额    {0:>12,.2f}")
        
        # 四、现金净增加额
        print(f"\n{Color.CYAN}四、现金及现金等价物净增加额{Color.ENDC}")
        net_cash_increase = net_operating_flow  # 简化计算
        print(f"  现金及现金等价物净增加额      {flow_color}{net_cash_increase:>12,.2f}{Color.ENDC}")
        
        print("=" * 70)
        
        # 现金流量分析
        print(f"\n{Color.CYAN}💡 现金流量分析：{Color.ENDC}")
        if net_operating_flow > 0:
            print("  ✅ 经营活动现金流为正，经营状况良好")
        else:
            print("  ⚠️ 经营活动现金流为负，需要关注资金状况")
        
        if operating_inflow > 0:
            operating_efficiency = (net_operating_flow / operating_inflow) * 100
            print(f"  经营现金流效率：{operating_efficiency:.1f}%")
        
        # 询问是否保存
        if UserMessage.confirm("是否保存此现金流量表？"):
            report_dir = "财务数据/月度报表"
            os.makedirs(report_dir, exist_ok=True)
            
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"{report_dir}/现金流量表_{period_name.replace('年', '').replace('月', '').replace(' 至 ', '_')}_{timestamp}.txt"
            
            try:
                with open(filename, 'w', encoding='utf-8') as f:
                    f.write(f"现金流量表\n")
                    f.write(f"{period_name}\n")
                    f.write("=" * 50 + "\n\n")
                    
                    f.write("一、经营活动产生的现金流量\n")
                    f.write(f"  销售商品、提供劳务收到的现金  {cash_from_sales:>12,.2f}\n")
                    f.write(f"  经营活动现金流入小计          {operating_inflow:>12,.2f}\n")
                    f.write(f"  购买商品、接受劳务支付的现金  {material_expense:>12,.2f}\n")
                    f.write(f"  支付给职工的现金              {labor_expense:>12,.2f}\n")
                    f.write(f"  支付其他与经营活动有关的现金  {other_expense:>12,.2f}\n")
                    f.write(f"  经营活动现金流出小计          {operating_outflow:>12,.2f}\n")
                    f.write(f"  经营活动产生的现金流量净额    {net_operating_flow:>12,.2f}\n\n")
                    
                    f.write("二、投资活动产生的现金流量\n")
                    f.write(f"  投资活动产生的现金流量净额    {0:>12,.2f}\n\n")
                    
                    f.write("三、筹资活动产生的现金流量\n")
                    f.write(f"  筹资活动产生的现金流量净额    {0:>12,.2f}\n\n")
                    
                    f.write("四、现金及现金等价物净增加额\n")
                    f.write(f"  现金及现金等价物净增加额      {net_cash_increase:>12,.2f}\n")
                
                UserMessage.success(f"现金流量表已保存：{filename}")
                logger.info(f"现金流量表保存成功: {filename}")
                
            except Exception as e:
                UserMessage.error(f"保存现金流量表失败：{str(e)}")
        
    except Exception as e:
        UserMessage.error(f"生成现金流量表时发生错误: {str(e)}")
        logger.error(f"生成现金流量表异常: {str(e)}", exc_info=True)

def financial_analysis_report():
    """财务分析报告"""
    print("\n" + "=" * 70)
    print("     财务分析报告")
    print("=" * 70)
    
    try:
        # 选择分析期间
        print("\n分析期间：")
        print("  1. 本月")
        print("  2. 本季度")
        print("  3. 本年")
        
        period_choice = input("选择分析期间（1-3）: ").strip()
        
        today = datetime.now()
        if period_choice == "1":  # 本月
            start_date = today.replace(day=1)
            end_date = today
            period_name = f"{today.year}年{today.month}月"
        elif period_choice == "2":  # 本季度
            quarter = (today.month - 1) // 3 + 1
            start_month = (quarter - 1) * 3 + 1
            start_date = today.replace(month=start_month, day=1)
            end_date = today
            period_name = f"{today.year}年第{quarter}季度"
        else:  # 本年
            start_date = today.replace(month=1, day=1)
            end_date = today
            period_name = f"{today.year}年"
        
        start_date_str = start_date.strftime("%Y-%m-%d")
        end_date_str = end_date.strftime("%Y-%m-%d")
        
        # 获取财务数据
        stats = financial_manager.get_transaction_statistics(start_date_str, end_date_str)
        
        # 获取订单数据
        try:
            orders = get_storage().get_all_orders()
            period_orders = []
            for order in orders:
                order_date = order.get('order_date', '')
                if start_date_str <= order_date <= end_date_str:
                    period_orders.append(order)
        except:
            period_orders = []
        
        print(f"\n" + "=" * 70)
        print(f"                财务分析报告")
        print(f"              {period_name}")
        print("=" * 70)
        
        # 一、经营规模分析
        print(f"\n{Color.CYAN}一、经营规模分析{Color.ENDC}")
        print(f"  营业收入：      {stats['total_income']:>12,.2f} 元")
        print(f"  营业成本：      {stats['total_expense']:>12,.2f} 元")
        print(f"  订单数量：      {len(period_orders):>12} 个")
        print(f"  交易笔数：      {stats['transaction_count']:>12} 笔")
        
        # 二、盈利能力分析
        print(f"\n{Color.CYAN}二、盈利能力分析{Color.ENDC}")
        net_profit = stats['net_profit']
        profit_color = Color.GREEN if net_profit >= 0 else Color.FAIL
        print(f"  净利润：        {profit_color}{net_profit:>12,.2f} 元{Color.ENDC}")
        
        if stats['total_income'] > 0:
            profit_margin = (net_profit / stats['total_income']) * 100
            print(f"  净利润率：      {profit_color}{profit_margin:>11.1f} %{Color.ENDC}")
            
            # 成本率分析
            cost_ratio = (stats['total_expense'] / stats['total_income']) * 100
            print(f"  成本率：        {cost_ratio:>11.1f} %")
        
        # 三、收入结构分析
        print(f"\n{Color.CYAN}三、收入结构分析{Color.ENDC}")
        if stats['income_by_category']:
            total_income = stats['total_income']
            for category, amount in sorted(stats['income_by_category'].items(), 
                                         key=lambda x: x[1], reverse=True):
                percentage = (amount / total_income * 100) if total_income > 0 else 0
                print(f"  {category}：{amount:>10,.2f} 元 ({percentage:>5.1f}%)")
        
        # 四、成本结构分析
        print(f"\n{Color.CYAN}四、成本结构分析{Color.ENDC}")
        if stats['expense_by_category']:
            total_expense = stats['total_expense']
            for category, amount in sorted(stats['expense_by_category'].items(), 
                                         key=lambda x: x[1], reverse=True):
                percentage = (amount / total_expense * 100) if total_expense > 0 else 0
                print(f"  {category}：{amount:>10,.2f} 元 ({percentage:>5.1f}%)")
        
        # 五、客户分析
        print(f"\n{Color.CYAN}五、客户分析{Color.ENDC}")
        if period_orders:
            customer_stats = {}
            for order in period_orders:
                customer = order.get('customer', '未知')
                if customer not in customer_stats:
                    customer_stats[customer] = {'count': 0, 'amount': 0}
                customer_stats[customer]['count'] += 1
                customer_stats[customer]['amount'] += order.get('order_amount', 0)
            
            print(f"  客户总数：      {len(customer_stats):>12} 个")
            
            # 主要客户（前5名）
            top_customers = sorted(customer_stats.items(), 
                                 key=lambda x: x[1]['amount'], reverse=True)[:5]
            
            print(f"  主要客户：")
            for i, (customer, data) in enumerate(top_customers, 1):
                contribution = (data['amount'] / stats['total_income'] * 100) if stats['total_income'] > 0 else 0
                print(f"    {i}. {customer}：{data['count']}单，{data['amount']:,.2f}元 ({contribution:.1f}%)")
        
        # 六、经营建议
        print(f"\n{Color.CYAN}六、经营建议{Color.ENDC}")
        
        if net_profit > 0:
            print("  ✅ 经营状况良好，建议：")
            if profit_margin < 10:
                print("    • 利润率偏低，可考虑优化成本结构或提高售价")
            else:
                print("    • 利润率健康，可考虑扩大经营规模")
        else:
            print("  ⚠️ 经营亏损，建议：")
            print("    • 分析主要亏损原因，控制成本支出")
            print("    • 提高产品质量和服务水平，增加收入")
            print("    • 优化客户结构，重点维护优质客户")
        
        # 成本控制建议
        if stats['expense_by_category']:
            max_expense_category = max(stats['expense_by_category'].items(), key=lambda x: x[1])
            print(f"    • 重点关注{max_expense_category[0]}支出，占总成本{max_expense_category[1]/stats['total_expense']*100:.1f}%")
        
        print("=" * 70)
        
        # 询问是否保存
        if UserMessage.confirm("是否保存此财务分析报告？"):
            report_dir = "财务数据/月度报表"
            os.makedirs(report_dir, exist_ok=True)
            
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"{report_dir}/财务分析报告_{period_name.replace('年', '').replace('月', '').replace('季度', 'Q')}_{timestamp}.txt"
            
            try:
                with open(filename, 'w', encoding='utf-8') as f:
                    f.write(f"财务分析报告\n")
                    f.write(f"{period_name}\n")
                    f.write("=" * 50 + "\n\n")
                    
                    f.write("一、经营规模分析\n")
                    f.write(f"  营业收入：      {stats['total_income']:>12,.2f} 元\n")
                    f.write(f"  营业成本：      {stats['total_expense']:>12,.2f} 元\n")
                    f.write(f"  订单数量：      {len(period_orders):>12} 个\n")
                    f.write(f"  交易笔数：      {stats['transaction_count']:>12} 笔\n\n")
                    
                    f.write("二、盈利能力分析\n")
                    f.write(f"  净利润：        {net_profit:>12,.2f} 元\n")
                    if stats['total_income'] > 0:
                        f.write(f"  净利润率：      {profit_margin:>11.1f} %\n")
                        f.write(f"  成本率：        {cost_ratio:>11.1f} %\n")
                    f.write("\n")
                    
                    # 保存其他分析内容...
                
                UserMessage.success(f"财务分析报告已保存：{filename}")
                logger.info(f"财务分析报告保存成功: {filename}")
                
            except Exception as e:
                UserMessage.error(f"保存财务分析报告失败：{str(e)}")
        
    except Exception as e:
        UserMessage.error(f"生成财务分析报告时发生错误: {str(e)}")
        logger.error(f"生成财务分析报告异常: {str(e)}", exc_info=True)

def annual_summary():
    """年度汇总"""
    print("\n" + "=" * 70)
    print("     年度汇总")
    print("=" * 70)
    
    try:
        # 选择年份
        year = input("年份（直接回车使用今年）: ").strip()
        if not year:
            year = str(datetime.now().year)
        
        try:
            year = int(year)
        except ValueError:
            UserMessage.error("请输入有效的年份")
            return
        
        start_date = f"{year}-01-01"
        end_date = f"{year}-12-31"
        
        print(f"\n正在生成{year}年度汇总报告...")
        
        # 获取年度数据
        stats = financial_manager.get_transaction_statistics(start_date, end_date)
        
        # 获取订单数据
        try:
            orders = get_storage().get_all_orders()
            annual_orders = []
            for order in orders:
                order_date = order.get('order_date', '')
                if start_date <= order_date <= end_date:
                    annual_orders.append(order)
        except:
            annual_orders = []
        
        print(f"\n" + "=" * 70)
        print(f"                年度汇总报告")
        print(f"                {year}年")
        print("=" * 70)
        
        # 一、经营概况
        print(f"\n{Color.CYAN}一、经营概况{Color.ENDC}")
        print(f"  营业收入：      {Color.GREEN}{stats['total_income']:>12,.2f} 元{Color.ENDC}")
        print(f"  营业成本：      {Color.FAIL}{stats['total_expense']:>12,.2f} 元{Color.ENDC}")
        net_profit = stats['net_profit']
        profit_color = Color.GREEN if net_profit >= 0 else Color.FAIL
        print(f"  净利润：        {profit_color}{net_profit:>12,.2f} 元{Color.ENDC}")
        
        if stats['total_income'] > 0:
            profit_rate = (net_profit / stats['total_income']) * 100
            print(f"  净利润率：      {profit_color}{profit_rate:>11.1f} %{Color.ENDC}")
        
        # 二、订单情况
        print(f"\n{Color.CYAN}二、订单情况{Color.ENDC}")
        if annual_orders:
            total_orders = len(annual_orders)
            total_amount = sum(order.get('order_amount', 0) for order in annual_orders)
            total_paid = sum(order.get('paid_amount', 0) for order in annual_orders)
            
            print(f"  订单总数：      {total_orders:>12} 个")
            print(f"  订单总额：      {total_amount:>12,.2f} 元")
            print(f"  已收款：        {total_paid:>12,.2f} 元")
            
            if total_amount > 0:
                collection_rate = (total_paid / total_amount) * 100
                print(f"  收款率：        {collection_rate:>11.1f} %")
            
            # 月度分布
            monthly_orders = {}
            for order in annual_orders:
                month = order.get('order_date', '')[:7]  # YYYY-MM
                if month not in monthly_orders:
                    monthly_orders[month] = {'count': 0, 'amount': 0}
                monthly_orders[month]['count'] += 1
                monthly_orders[month]['amount'] += order.get('order_amount', 0)
            
            print(f"\n  月度分布：")
            for month in sorted(monthly_orders.keys()):
                data = monthly_orders[month]
                print(f"    {month}：{data['count']:>3}单，{data['amount']:>10,.2f}元")
        else:
            print("  本年度无订单记录")
        
        # 三、收入分析
        print(f"\n{Color.CYAN}三、收入分析{Color.ENDC}")
        if stats['income_by_category']:
            for category, amount in sorted(stats['income_by_category'].items(), 
                                         key=lambda x: x[1], reverse=True):
                percentage = (amount / stats['total_income'] * 100) if stats['total_income'] > 0 else 0
                print(f"  {category}：{amount:>12,.2f} 元 ({percentage:>5.1f}%)")
        
        # 四、成本分析
        print(f"\n{Color.CYAN}四、成本分析{Color.ENDC}")
        if stats['expense_by_category']:
            for category, amount in sorted(stats['expense_by_category'].items(), 
                                         key=lambda x: x[1], reverse=True):
                percentage = (amount / stats['total_expense'] * 100) if stats['total_expense'] > 0 else 0
                print(f"  {category}：{amount:>12,.2f} 元 ({percentage:>5.1f}%)")
        
        # 五、税务情况
        print(f"\n{Color.CYAN}五、税务情况{Color.ENDC}")
        vat_info = financial_manager.calculate_vat(start_date, end_date)
        print(f"  全年销售额：    {vat_info['income_without_tax']:>12,.2f} 元")
        print(f"  应纳增值税：    {vat_info['actual_vat']:>12,.2f} 元")
        
        # 所得税估算
        if net_profit > 0:
            if net_profit <= 1000000:
                income_tax = net_profit * 0.025
                tax_rate_desc = "2.5%（小微企业优惠）"
            elif net_profit <= 3000000:
                income_tax = 1000000 * 0.025 + (net_profit - 1000000) * 0.05
                tax_rate_desc = "分段计税（小微企业优惠）"
            else:
                income_tax = net_profit * 0.25
                tax_rate_desc = "25%（标准税率）"
            
            print(f"  应纳所得税：    {income_tax:>12,.2f} 元")
            print(f"  所得税率：      {tax_rate_desc}")
        else:
            print(f"  应纳所得税：    {0:>12,.2f} 元（亏损）")
        
        # 六、客户分析
        print(f"\n{Color.CYAN}六、客户分析{Color.ENDC}")
        if annual_orders:
            customer_stats = {}
            for order in annual_orders:
                customer = order.get('customer', '未知')
                if customer not in customer_stats:
                    customer_stats[customer] = {'count': 0, 'amount': 0}
                customer_stats[customer]['count'] += 1
                customer_stats[customer]['amount'] += order.get('order_amount', 0)
            
            print(f"  客户总数：      {len(customer_stats):>12} 个")
            
            # 主要客户（前10名）
            top_customers = sorted(customer_stats.items(), 
                                 key=lambda x: x[1]['amount'], reverse=True)[:10]
            
            print(f"  主要客户（前10名）：")
            for i, (customer, data) in enumerate(top_customers, 1):
                contribution = (data['amount'] / stats['total_income'] * 100) if stats['total_income'] > 0 else 0
                print(f"    {i:2d}. {customer}：{data['count']:>3}单，{data['amount']:>10,.2f}元 ({contribution:>5.1f}%)")
        
        print("=" * 70)
        
        # 询问是否保存报告
        if UserMessage.confirm("是否保存此年度汇总报告？"):
            report_dir = "财务数据/年度报表"
            os.makedirs(report_dir, exist_ok=True)
            
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"{report_dir}/年度汇总_{year}_{timestamp}.txt"
            
            try:
                with open(filename, 'w', encoding='utf-8') as f:
                    f.write(f"年度汇总报告\n")
                    f.write(f"{year}年\n")
                    f.write("=" * 50 + "\n\n")
                    
                    # 写入各部分内容...
                    f.write("一、经营概况\n")
                    f.write(f"  营业收入：      {stats['total_income']:>12,.2f} 元\n")
                    f.write(f"  营业成本：      {stats['total_expense']:>12,.2f} 元\n")
                    f.write(f"  净利润：        {net_profit:>12,.2f} 元\n")
                    if stats['total_income'] > 0:
                        f.write(f"  净利润率：      {profit_rate:>11.1f} %\n")
                    f.write("\n")
                    
                    # 其他部分内容...
                
                UserMessage.success(f"年度汇总报告已保存：{filename}")
                logger.info(f"年度汇总报告保存成功: {filename}")
                
            except Exception as e:
                UserMessage.error(f"保存年度汇总报告失败：{str(e)}")
        
    except Exception as e:
        UserMessage.error(f"生成年度汇总时发生错误: {str(e)}")
        logger.error(f"生成年度汇总异常: {str(e)}", exc_info=True)

def voucher_management():
    """凭证管理"""
    print("\n" + "=" * 70)
    print("     凭证管理")
    print("=" * 70)
    
    try:
        voucher_dir = "财务数据/凭证档案"
        os.makedirs(voucher_dir, exist_ok=True)
        
        print("\n凭证管理功能：")
        print("  1. 查看凭证列表")
        print("  2. 新建凭证")
        print("  3. 凭证归档")
        print("  4. 凭证统计")
        
        choice = input("请选择功能（1-4）: ").strip()
        
        if choice == "1":
            # 查看凭证列表
            voucher_file = f"{voucher_dir}/vouchers.json"
            vouchers = []
            
            if os.path.exists(voucher_file):
                try:
                    with open(voucher_file, 'r', encoding='utf-8') as f:
                        vouchers = json.load(f)
                except Exception as e:
                    logger.error(f"加载凭证失败: {e}")
            
            if not vouchers:
                UserMessage.warning("暂无凭证记录")
                return
            
            print(f"\n📋 凭证列表（共{len(vouchers)}张）：")
            
            # 按日期排序显示
            vouchers.sort(key=lambda x: x.get('date', ''), reverse=True)
            
            for i, voucher in enumerate(vouchers[:20], 1):  # 显示最近20张
                print(f"{i:2d}. {voucher.get('voucher_no', '')} - {voucher.get('date', '')}")
                print(f"    摘要：{voucher.get('summary', '')}")
                print(f"    金额：{voucher.get('amount', 0):,.2f}元")
                print()
        
        elif choice == "2":
            # 新建凭证
            print("\n新建记账凭证：")
            
            date_str = input("凭证日期（格式：2026-01-01，直接回车使用今天）: ").strip()
            if not date_str:
                date_str = datetime.now().strftime("%Y-%m-%d")
            
            summary = input("摘要: ").strip()
            if not summary:
                UserMessage.info("操作已取消")
                return
            
            amount_str = input("金额: ").strip()
            try:
                amount = float(amount_str)
            except ValueError:
                UserMessage.error("请输入有效的金额")
                return
            
            debit_account = input("借方科目: ").strip()
            credit_account = input("贷方科目: ").strip()
            
            # 生成凭证号
            today = datetime.now()
            voucher_no = f"JZ{today.strftime('%Y%m%d')}{today.strftime('%H%M%S')}"
            
            voucher = {
                'voucher_no': voucher_no,
                'date': date_str,
                'summary': summary,
                'amount': amount,
                'debit_account': debit_account,
                'credit_account': credit_account,
                'created_at': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            }
            
            # 保存凭证
            voucher_file = f"{voucher_dir}/vouchers.json"
            vouchers = []
            
            if os.path.exists(voucher_file):
                try:
                    with open(voucher_file, 'r', encoding='utf-8') as f:
                        vouchers = json.load(f)
                except Exception as e:
                    logger.error(f"加载凭证失败: {e}")
            
            vouchers.append(voucher)
            
            try:
                with open(voucher_file, 'w', encoding='utf-8') as f:
                    json.dump(vouchers, f, ensure_ascii=False, indent=2)
                
                UserMessage.success(f"凭证创建成功！凭证号：{voucher_no}")
                logger.info(f"新建凭证: {voucher_no}")
                
            except Exception as e:
                UserMessage.error(f"保存凭证失败：{str(e)}")
        
        elif choice == "3":
            # 凭证归档
            UserMessage.info("凭证归档功能开发中")
        
        elif choice == "4":
            # 凭证统计
            voucher_file = f"{voucher_dir}/vouchers.json"
            vouchers = []
            
            if os.path.exists(voucher_file):
                try:
                    with open(voucher_file, 'r', encoding='utf-8') as f:
                        vouchers = json.load(f)
                except Exception as e:
                    logger.error(f"加载凭证失败: {e}")
            
            if not vouchers:
                UserMessage.warning("暂无凭证记录")
                return
            
            print(f"\n📊 凭证统计：")
            print(f"  凭证总数：      {len(vouchers):>8} 张")
            
            total_amount = sum(v.get('amount', 0) for v in vouchers)
            print(f"  总金额：        {total_amount:>12,.2f} 元")
            
            # 按月统计
            monthly_stats = {}
            for voucher in vouchers:
                month = voucher.get('date', '')[:7]  # YYYY-MM
                if month not in monthly_stats:
                    monthly_stats[month] = {'count': 0, 'amount': 0}
                monthly_stats[month]['count'] += 1
                monthly_stats[month]['amount'] += voucher.get('amount', 0)
            
            if monthly_stats:
                print(f"\n  月度分布：")
                for month in sorted(monthly_stats.keys(), reverse=True)[:6]:  # 最近6个月
                    data = monthly_stats[month]
                    print(f"    {month}：{data['count']:>3}张，{data['amount']:>10,.2f}元")
        
    except Exception as e:
        UserMessage.error(f"凭证管理时发生错误: {str(e)}")
        logger.error(f"凭证管理异常: {str(e)}", exc_info=True)

def contract_management():
    """合同管理"""
    print("\n" + "=" * 70)
    print("     合同管理")
    print("=" * 70)
    
    try:
        contract_dir = "财务数据/合同档案"
        os.makedirs(contract_dir, exist_ok=True)
        
        print("\n合同管理功能：")
        print("  1. 查看合同列表")
        print("  2. 新建合同")
        print("  3. 合同到期提醒")
        print("  4. 合同统计")
        
        choice = input("请选择功能（1-4）: ").strip()
        
        if choice == "1":
            # 查看合同列表
            contract_file = f"{contract_dir}/contracts.json"
            contracts = []
            
            if os.path.exists(contract_file):
                try:
                    with open(contract_file, 'r', encoding='utf-8') as f:
                        contracts = json.load(f)
                except Exception as e:
                    logger.error(f"加载合同失败: {e}")
            
            if not contracts:
                UserMessage.warning("暂无合同记录")
                return
            
            print(f"\n📋 合同列表（共{len(contracts)}个）：")
            
            for i, contract in enumerate(contracts, 1):
                status_color = Color.GREEN if contract.get('status') == '执行中' else Color.WARNING
                print(f"{i:2d}. {contract.get('contract_no', '')} - {contract.get('partner', '')}")
                print(f"    合同名称：{contract.get('name', '')}")
                print(f"    合同金额：{contract.get('amount', 0):,.2f}元")
                print(f"    状态：{status_color}{contract.get('status', '')}{Color.ENDC}")
                print(f"    期限：{contract.get('start_date', '')} 至 {contract.get('end_date', '')}")
                print()
        
        elif choice == "2":
            # 新建合同
            print("\n新建合同档案：")
            
            name = input("合同名称: ").strip()
            if not name:
                UserMessage.info("操作已取消")
                return
            
            partner = input("合作方: ").strip()
            amount_str = input("合同金额: ").strip()
            
            try:
                amount = float(amount_str) if amount_str else 0
            except ValueError:
                UserMessage.error("请输入有效的金额")
                return
            
            start_date = input("开始日期（格式：2026-01-01）: ").strip()
            end_date = input("结束日期（格式：2026-12-31）: ").strip()
            
            # 生成合同编号
            today = datetime.now()
            contract_no = f"HT{today.strftime('%Y%m%d')}{today.strftime('%H%M%S')}"
            
            contract = {
                'contract_no': contract_no,
                'name': name,
                'partner': partner,
                'amount': amount,
                'start_date': start_date,
                'end_date': end_date,
                'status': '执行中',
                'created_at': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            }
            
            # 保存合同
            contract_file = f"{contract_dir}/contracts.json"
            contracts = []
            
            if os.path.exists(contract_file):
                try:
                    with open(contract_file, 'r', encoding='utf-8') as f:
                        contracts = json.load(f)
                except Exception as e:
                    logger.error(f"加载合同失败: {e}")
            
            contracts.append(contract)
            
            try:
                with open(contract_file, 'w', encoding='utf-8') as f:
                    json.dump(contracts, f, ensure_ascii=False, indent=2)
                
                UserMessage.success(f"合同创建成功！合同编号：{contract_no}")
                logger.info(f"新建合同: {contract_no}")
                
            except Exception as e:
                UserMessage.error(f"保存合同失败：{str(e)}")
        
        elif choice == "3":
            # 合同到期提醒
            contract_file = f"{contract_dir}/contracts.json"
            contracts = []
            
            if os.path.exists(contract_file):
                try:
                    with open(contract_file, 'r', encoding='utf-8') as f:
                        contracts = json.load(f)
                except Exception as e:
                    logger.error(f"加载合同失败: {e}")
            
            if not contracts:
                UserMessage.warning("暂无合同记录")
                return
            
            today = datetime.now()
            warning_date = today + timedelta(days=30)  # 30天内到期
            
            expiring_contracts = []
            for contract in contracts:
                if contract.get('end_date') and contract.get('status') == '执行中':
                    try:
                        end_date = datetime.strptime(contract['end_date'], '%Y-%m-%d')
                        if today <= end_date <= warning_date:
                            days_left = (end_date - today).days
                            contract['days_left'] = days_left
                            expiring_contracts.append(contract)
                    except ValueError:
                        continue
            
            if not expiring_contracts:
                UserMessage.info("30天内无合同到期")
                return
            
            print(f"\n⚠️ 即将到期的合同（{len(expiring_contracts)}个）：")
            
            for contract in sorted(expiring_contracts, key=lambda x: x['days_left']):
                days_color = Color.FAIL if contract['days_left'] <= 7 else Color.WARNING
                print(f"  {contract.get('contract_no', '')} - {contract.get('partner', '')}")
                print(f"    合同名称：{contract.get('name', '')}")
                print(f"    到期日期：{contract.get('end_date', '')}")
                print(f"    剩余天数：{days_color}{contract['days_left']}天{Color.ENDC}")
                print()
        
        elif choice == "4":
            # 合同统计
            contract_file = f"{contract_dir}/contracts.json"
            contracts = []
            
            if os.path.exists(contract_file):
                try:
                    with open(contract_file, 'r', encoding='utf-8') as f:
                        contracts = json.load(f)
                except Exception as e:
                    logger.error(f"加载合同失败: {e}")
            
            if not contracts:
                UserMessage.warning("暂无合同记录")
                return
            
            print(f"\n📊 合同统计：")
            print(f"  合同总数：      {len(contracts):>8} 个")
            
            total_amount = sum(c.get('amount', 0) for c in contracts)
            print(f"  合同总额：      {total_amount:>12,.2f} 元")
            
            # 按状态统计
            status_stats = {}
            for contract in contracts:
                status = contract.get('status', '未知')
                if status not in status_stats:
                    status_stats[status] = 0
                status_stats[status] += 1
            
            print(f"\n  按状态分布：")
            for status, count in status_stats.items():
                print(f"    {status}：{count:>6} 个")
        
    except Exception as e:
        UserMessage.error(f"合同管理时发生错误: {str(e)}")
        logger.error(f"合同管理异常: {str(e)}", exc_info=True)

def supplier_management():
    """供应商档案管理"""
    print("\n" + "=" * 70)
    print("     供应商档案管理")
    print("=" * 70)
    
    try:
        supplier_dir = "财务数据/供应商档案"
        os.makedirs(supplier_dir, exist_ok=True)
        
        print("\n供应商档案功能：")
        print("  1. 查看供应商列表")
        print("  2. 新增供应商")
        print("  3. 编辑供应商")
        print("  4. 供应商交易统计")
        
        choice = input("请选择功能（1-4）: ").strip()
        
        if choice == "1":
            # 查看供应商列表
            supplier_file = f"{supplier_dir}/suppliers.json"
            suppliers = []
            
            if os.path.exists(supplier_file):
                try:
                    with open(supplier_file, 'r', encoding='utf-8') as f:
                        suppliers = json.load(f)
                except Exception as e:
                    logger.error(f"加载供应商档案失败: {e}")
            
            if not suppliers:
                UserMessage.warning("暂无供应商档案")
                return
            
            print(f"\n📋 供应商列表（共{len(suppliers)}个）：")
            for i, supplier in enumerate(suppliers, 1):
                print(f"{i:2d}. {supplier['name']}")
                print(f"    联系人：{supplier.get('contact', '未填写')}")
                print(f"    电话：{supplier.get('phone', '未填写')}")
                print(f"    地址：{supplier.get('address', '未填写')}")
                print(f"    主营：{supplier.get('business', '未填写')}")
                print()
        
        elif choice == "2":
            # 新增供应商
            print("\n新增供应商档案：")
            name = input("供应商名称: ").strip()
            if not name:
                UserMessage.info("操作已取消")
                return
            
            # 检查是否已存在
            supplier_file = f"{supplier_dir}/suppliers.json"
            suppliers = []
            
            if os.path.exists(supplier_file):
                try:
                    with open(supplier_file, 'r', encoding='utf-8') as f:
                        suppliers = json.load(f)
                except Exception as e:
                    logger.error(f"加载供应商档案失败: {e}")
            
            if any(s['name'] == name for s in suppliers):
                UserMessage.error("供应商已存在")
                return
            
            contact = input("联系人: ").strip()
            phone = input("联系电话: ").strip()
            address = input("供应商地址: ").strip()
            business = input("主营业务: ").strip()
            remark = input("备注: ").strip()
            
            supplier = {
                'id': len(suppliers) + 1,
                'name': name,
                'contact': contact,
                'phone': phone,
                'address': address,
                'business': business,
                'remark': remark,
                'created_at': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            }
            
            suppliers.append(supplier)
            
            try:
                with open(supplier_file, 'w', encoding='utf-8') as f:
                    json.dump(suppliers, f, ensure_ascii=False, indent=2)
                
                UserMessage.success("供应商档案创建成功")
                logger.info(f"新增供应商: {name}")
                
            except Exception as e:
                UserMessage.error(f"保存供应商档案失败：{str(e)}")
        
        elif choice == "3":
            # 编辑供应商
            UserMessage.info("供应商编辑功能开发中")
        
        elif choice == "4":
            # 供应商交易统计
            supplier_file = f"{supplier_dir}/suppliers.json"
            suppliers = []
            
            if os.path.exists(supplier_file):
                try:
                    with open(supplier_file, 'r', encoding='utf-8') as f:
                        suppliers = json.load(f)
                except Exception as e:
                    logger.error(f"加载供应商档案失败: {e}")
            
            if not suppliers:
                UserMessage.warning("暂无供应商档案")
                return
            
            # 统计供应商相关的支出
            transactions = finance_manager.load_transactions()
            supplier_stats = {}
            
            # 简单匹配：在支出记录的描述中查找供应商名称
            for trans in transactions:
                if trans['type'] == '支出':
                    description = trans.get('description', '').lower()
                    for supplier in suppliers:
                        supplier_name = supplier['name'].lower()
                        if supplier_name in description:
                            if supplier['name'] not in supplier_stats:
                                supplier_stats[supplier['name']] = {'expense': 0, 'count': 0}
                            supplier_stats[supplier['name']]['expense'] += trans['amount']
                            supplier_stats[supplier['name']]['count'] += 1
                            break
            
            print(f"\n📊 供应商交易统计：")
            if supplier_stats:
                # 按支出金额排序
                sorted_suppliers = sorted(supplier_stats.items(), 
                                        key=lambda x: x[1]['expense'], reverse=True)
                
                for supplier, stats in sorted_suppliers:
                    print(f"  {supplier}:")
                    print(f"    支出金额：{stats['expense']:>10,.2f} 元")
                    print(f"    交易次数：{stats['count']:>10} 次")
                    print()
            else:
                print("  暂无供应商交易记录")
        
    except Exception as e:
        UserMessage.error(f"供应商档案管理时发生错误: {str(e)}")
        logger.error(f"供应商档案管理异常: {str(e)}", exc_info=True)

def data_cleanup():
    """数据清理"""
    print("\n" + "=" * 70)
    print("     数据清理")
    print("=" * 70)
    
    try:
        print("\n数据清理选项：")
        print("  1. 清理重复记录")
        print("  2. 清理无效数据")
        print("  3. 清理临时文件")
        print("  4. 清理过期日志")
        
        choice = input("请选择清理类型（1-4）: ").strip()
        
        if choice == "1":
            # 清理重复记录
            UserMessage.info("正在检查重复的收支记录...")
            
            transactions = finance_manager.load_transactions()
            if not transactions:
                UserMessage.info("无收支记录需要清理")
                return
            
            # 查找重复记录（相同日期、金额、类型、描述）
            seen = set()
            duplicates = []
            unique_transactions = []
            
            for trans in transactions:
                key = (trans.get('date'), trans.get('amount'), 
                      trans.get('type'), trans.get('description'))
                
                if key in seen:
                    duplicates.append(trans)
                else:
                    seen.add(key)
                    unique_transactions.append(trans)
            
            if duplicates:
                print(f"\n发现 {len(duplicates)} 条重复记录：")
                for i, dup in enumerate(duplicates[:5], 1):  # 只显示前5条
                    print(f"  {i}. {dup.get('date')} - {dup.get('type')} - {dup.get('amount')}元")
                
                if len(duplicates) > 5:
                    print(f"  ... 还有 {len(duplicates)-5} 条重复记录")
                
                if UserMessage.confirm("确定要删除这些重复记录吗？"):
                    if finance_manager.save_transactions(unique_transactions):
                        UserMessage.success(f"已清理 {len(duplicates)} 条重复记录")
                        logger.info(f"数据清理: 删除{len(duplicates)}条重复记录")
                    else:
                        UserMessage.error("清理失败")
            else:
                UserMessage.info("未发现重复记录")
        
        elif choice == "2":
            # 清理无效数据
            UserMessage.info("正在检查无效数据...")
            
            transactions = finance_manager.load_transactions()
            if not transactions:
                UserMessage.info("无收支记录需要清理")
                return
            
            # 查找无效记录（金额为0或负数、缺少必要字段）
            invalid_transactions = []
            valid_transactions = []
            
            for trans in transactions:
                is_invalid = False
                
                # 检查必要字段
                if not trans.get('date') or not trans.get('type') or not trans.get('amount'):
                    is_invalid = True
                
                # 检查金额
                try:
                    amount = float(trans.get('amount', 0))
                    if amount <= 0:
                        is_invalid = True
                except (ValueError, TypeError):
                    is_invalid = True
                
                # 检查日期格式
                try:
                    datetime.strptime(trans.get('date', ''), '%Y-%m-%d')
                except ValueError:
                    is_invalid = True
                
                if is_invalid:
                    invalid_transactions.append(trans)
                else:
                    valid_transactions.append(trans)
            
            if invalid_transactions:
                print(f"\n发现 {len(invalid_transactions)} 条无效记录")
                
                if UserMessage.confirm("确定要删除这些无效记录吗？"):
                    if finance_manager.save_transactions(valid_transactions):
                        UserMessage.success(f"已清理 {len(invalid_transactions)} 条无效记录")
                        logger.info(f"数据清理: 删除{len(invalid_transactions)}条无效记录")
                    else:
                        UserMessage.error("清理失败")
            else:
                UserMessage.info("未发现无效记录")
        
        elif choice == "3":
            # 清理临时文件
            UserMessage.info("正在清理临时文件...")
            
            temp_patterns = ['*.tmp', '*.temp', '*~', '.DS_Store']
            deleted_count = 0
            
            import glob
            for pattern in temp_patterns:
                for file_path in glob.glob(f"财务数据/**/{pattern}", recursive=True):
                    try:
                        os.remove(file_path)
                        deleted_count += 1
                    except Exception as e:
                        logger.error(f"删除临时文件失败 {file_path}: {e}")
            
            UserMessage.success(f"已清理 {deleted_count} 个临时文件")
            logger.info(f"数据清理: 删除{deleted_count}个临时文件")
        
        elif choice == "4":
            # 清理过期日志
            UserMessage.info("正在清理过期日志...")
            
            log_dir = "财务数据/运行日志"
            if not os.path.exists(log_dir):
                UserMessage.info("无日志文件需要清理")
                return
            
            cutoff_date = datetime.now() - timedelta(days=30)  # 30天前
            deleted_count = 0
            
            for filename in os.listdir(log_dir):
                if filename.endswith('.log'):
                    file_path = os.path.join(log_dir, filename)
                    try:
                        file_time = datetime.fromtimestamp(os.path.getmtime(file_path))
                        if file_time < cutoff_date:
                            os.remove(file_path)
                            deleted_count += 1
                    except Exception as e:
                        logger.error(f"删除日志文件失败 {filename}: {e}")
            
            UserMessage.success(f"已清理 {deleted_count} 个过期日志文件")
            logger.info(f"数据清理: 删除{deleted_count}个过期日志")
        
    except Exception as e:
        UserMessage.error(f"数据清理时发生错误: {str(e)}")
        logger.error(f"数据清理异常: {str(e)}", exc_info=True)

def data_backup():
    """数据备份"""
    print("\n" + "=" * 70)
    print("     数据备份")
    print("=" * 70)
    
    try:
        backup_path = financial_manager.backup_all_data()
        
        if backup_path:
            UserMessage.success(f"数据备份成功！")
            print(f"📁 备份位置：{backup_path}")
            logger.info(f"数据备份成功: {backup_path}")
        else:
            UserMessage.error("数据备份失败")
        
    except Exception as e:
        UserMessage.error(f"数据备份时发生错误: {str(e)}")
        logger.error(f"数据备份异常: {str(e)}", exc_info=True)

def data_restore():
    """数据恢复"""
    print("\n" + "=" * 70)
    print("     数据恢复")
    print("=" * 70)
    
    try:
        backup_dir = "财务数据/自动备份"
        
        if not os.path.exists(backup_dir):
            UserMessage.warning("未找到备份目录")
            return
        
        # 列出可用的备份
        backups = [d for d in os.listdir(backup_dir) 
                  if os.path.isdir(os.path.join(backup_dir, d)) and d.startswith('财务数据备份_')]
        
        if not backups:
            UserMessage.warning("未找到可用的备份")
            return
        
        print(f"\n可用的备份（共{len(backups)}个）：")
        backups.sort(reverse=True)  # 最新的在前
        
        for i, backup in enumerate(backups[:10], 1):  # 只显示最近10个
            backup_time = backup.replace('财务数据备份_', '')
            print(f"  {i}. {backup_time}")
        
        choice = input(f"选择要恢复的备份（1-{min(len(backups), 10)}）: ").strip()
        
        try:
            backup_idx = int(choice) - 1
            if 0 <= backup_idx < min(len(backups), 10):
                selected_backup = backups[backup_idx]
                backup_path = os.path.join(backup_dir, selected_backup)
                
                UserMessage.warning("数据恢复将覆盖当前数据！")
                if not UserMessage.confirm("确定要继续吗？"):
                    UserMessage.info("操作已取消")
                    return
                
                # 执行恢复（简化实现）
                import shutil
                
                # 备份当前数据
                current_backup = financial_manager.backup_all_data()
                if current_backup:
                    print(f"当前数据已备份到：{current_backup}")
                
                # 恢复数据文件
                restored_count = 0
                
                # 恢复收支记录
                source_file = os.path.join(backup_path, "收支记录/transactions.json")
                target_file = "财务数据/收支记录/transactions.json"
                
                if os.path.exists(source_file):
                    os.makedirs(os.path.dirname(target_file), exist_ok=True)
                    shutil.copy2(source_file, target_file)
                    restored_count += 1
                
                # 恢复客户档案
                source_file = os.path.join(backup_path, "客户档案/customers.json")
                target_file = "财务数据/客户档案/customers.json"
                
                if os.path.exists(source_file):
                    os.makedirs(os.path.dirname(target_file), exist_ok=True)
                    shutil.copy2(source_file, target_file)
                    restored_count += 1
                
                # 恢复订单数据
                source_file = os.path.join(backup_path, "本地订单/orders.json")
                target_file = "财务数据/本地订单/orders.json"
                
                if os.path.exists(source_file):
                    os.makedirs(os.path.dirname(target_file), exist_ok=True)
                    shutil.copy2(source_file, target_file)
                    restored_count += 1
                
                UserMessage.success(f"数据恢复成功！恢复了 {restored_count} 个数据文件")
                logger.info(f"数据恢复成功: {selected_backup}, 恢复{restored_count}个文件")
                
            else:
                UserMessage.error("无效的选择")
        
        except ValueError:
            UserMessage.error("请输入有效的数字")
        
    except Exception as e:
        UserMessage.error(f"数据恢复时发生错误: {str(e)}")
        logger.error(f"数据恢复异常: {str(e)}", exc_info=True)

def system_configuration():
    """系统配置"""
    print("\n" + "=" * 70)
    print("     系统配置")
    print("=" * 70)
    
    try:
        print("\n系统配置选项：")
        print("  1. 查看当前配置")
        print("  2. 修改企业信息")
        print("  3. 修改税务设置")
        print("  4. 修改分类设置")
        
        choice = input("请选择配置项（1-4）: ").strip()
        
        if choice == "1":
            # 查看当前配置
            try:
                config = get_config()
                
                print(f"\n📋 当前系统配置：")
                print(f"\n企业信息：")
                print(f"  企业名称：氧化加工厂")
                print(f"  纳税人类型：小规模纳税人")
                print(f"  增值税率：3%")
                
                print(f"\n计价单位：")
                pricing_units = config.get_pricing_units()
                for unit in pricing_units:
                    print(f"  {unit}")
                
                print(f"\n外发工序：")
                processes = config.get_outsourced_processes()
                for process in processes:
                    print(f"  {process}")
                
                print(f"\n收支分类：")
                categories = config.get_default_categories()
                for cat_type, cat_list in categories.items():
                    print(f"  {cat_type}：{', '.join(cat_list)}")
                
            except Exception as e:
                UserMessage.error(f"读取配置失败：{str(e)}")
        
        elif choice == "2":
            # 修改企业信息
            UserMessage.info("企业信息修改功能开发中")
        
        elif choice == "3":
            # 修改税务设置
            UserMessage.info("税务设置修改功能开发中")
        
        elif choice == "4":
            # 修改分类设置
            UserMessage.info("分类设置修改功能开发中")
        
    except Exception as e:
        UserMessage.error(f"系统配置时发生错误: {str(e)}")
        logger.error(f"系统配置异常: {str(e)}", exc_info=True)

def main():
    """主函数"""
    print(f"\n{Color.GREEN}{'=' * 80}{Color.ENDC}")
    print(f"{Color.GREEN}       欢迎使用氧化加工厂财务助手 V1.3 - 全能版！{Color.ENDC}")
    print(f"{Color.GREEN}{'=' * 80}{Color.ENDC}")
    
    print(f"\n{Color.CYAN}🎉 V1.3 全能版特色：{Color.ENDC}")
    print("  ✅ 订单管理 - 完整的订单生命周期管理")
    print("  ✅ 收支管理 - 全面的收支记录和分析")
    print("  ✅ 税务管理 - 专业的税务计算和申报")
    print("  ✅ 报表中心 - 专业的财务报表系统")
    print("  ✅ 档案管理 - 完整的客户供应商档案")
    print("  ✅ 系统管理 - 数据备份恢复和日志记录")
    
    print(f"\n{Color.CYAN}💡 专为小企业会计设计：{Color.ENDC}")
    print("  ✅ 涵盖财务管理各个环节")
    print("  ✅ 支持小规模纳税人税务处理")
    print("  ✅ 自动生成各类财务报表")
    print("  ✅ 简单易用，无需专业培训")
    print("  ✅ 数据安全，本地存储")
    
    logger.info("系统启动成功")
    
    while True:
        try:
            show_main_menu()
            
            choice = input(f"\n{Color.BOLD}请选择功能编号：{Color.ENDC}").strip()
            
            # 订单管理
            if choice == "01":
                create_order()
            elif choice == "02":
                list_orders()
            elif choice == "03":
                UserMessage.info("订单编辑功能请使用小白专版")
            elif choice == "04":
                UserMessage.info("订单搜索功能请使用小白专版")
            elif choice == "05":
                UserMessage.info("收款记录功能请使用小白专版")
            elif choice == "06":
                UserMessage.info("订单统计功能请使用小白专版")
            elif choice == "07":
                UserMessage.info("订单导出功能请使用小白专版")
            
            # 收支管理
            elif choice == "11":
                record_expense()
            elif choice == "12":
                record_income()
            elif choice == "13":
                view_transactions()
            elif choice == "14":
                transaction_statistics()
            elif choice == "15":
                bank_statement_management()
            elif choice == "16":
                export_transaction_report()
            
            # 税务管理
            elif choice == "21":
                tax_management()
            elif choice == "22":
                income_tax_calculation()
            elif choice == "23":
                tax_report_center()
            elif choice == "24":
                tax_document_archive()
            
            # 报表中心
            elif choice == "31":
                generate_profit_report()
            elif choice == "32":
                balance_sheet_report()
            elif choice == "33":
                cash_flow_statement()
            elif choice == "34":
                financial_analysis_report()
            elif choice == "35":
                monthly_summary()
            elif choice == "36":
                annual_summary()
            
            # 档案管理
            elif choice == "41":
                voucher_management()
            elif choice == "42":
                contract_management()
            elif choice == "43":
                customer_management()
            elif choice == "44":
                supplier_management()
            
            # 系统管理
            elif choice == "51":
                generate_demo_data()
            elif choice == "52":
                data_cleanup()
            elif choice == "53":
                data_backup()
            elif choice == "54":
                data_restore()
            elif choice == "55":
                system_configuration()
            elif choice == "56":
                show_tutorial()
            elif choice == "57":
                show_logs()
            
            elif choice == "99":
                logger.info("用户正常退出系统")
                print(f"\n{Color.GREEN}👋 感谢使用，再见！{Color.ENDC}\n")
                break
            else:
                UserMessage.error("无效选择，请重新输入")
            
            input(f"\n{Color.CYAN}按回车键继续...{Color.ENDC}")
            
        except KeyboardInterrupt:
            logger.warning("用户中断操作")
            print(f"\n\n{Color.WARNING}⚠️ 用户中断操作{Color.ENDC}")
            if UserMessage.confirm("确定要退出系统吗？"):
                logger.info("用户确认退出系统")
                print(f"{Color.GREEN}👋 感谢使用，再见！{Color.ENDC}\n")
                break
        except Exception as e:
            logger.critical(f"主程序异常: {str(e)}", exc_info=True)
            UserMessage.error(f"程序异常：{str(e)}")
            UserMessage.info("系统将继续运行，如问题持续请查看日志")

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        logger.critical(f"程序启动异常: {str(e)}", exc_info=True)
        print(f"\n{Color.FAIL}❌ 程序启动异常：{str(e)}{Color.ENDC}\n")
        import traceback
        traceback.print_exc()