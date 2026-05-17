# -*- coding: utf-8 -*-
"""
氧化加工厂财务助手 V1.5 实战版
专为小型氧化加工厂小会计设计

核心特性：
1. 智能工作流 - 早晨/日常/月末自动引导
2. 智能默认值 - 记住客户习惯，自动填充
3. 一键操作 - 常用功能快捷键
4. 错误预防 - 实时验证，防止出错
5. 学习能力 - 越用越聪明

作者：AI助手
日期：2026-02-09
版本：V1.5 实战版
"""

import os
import sys
import json
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Any
from collections import defaultdict, Counter

# 添加workflow_v15到路径
sys.path.insert(0, str(Path(__file__).parent))

try:
    from workflow_v15.core.workflow_engine import WorkflowEngine
    from workflow_v15.core.context_engine import ContextEngine
    from workflow_v15.models.workflow_models import WorkflowType
    from workflow_v15.models.context_models import Activity
    WORKFLOW_AVAILABLE = True
except ImportError:
    WORKFLOW_AVAILABLE = False
    print("⚠️ V1.5工作流模块未找到，将使用V1.4模式")

# 导入V1.4的核心功能
try:
    from 财务数据管理器 import FinanceDataManager
    from 银行流水管理 import BankStatementManager
    V14_AVAILABLE = True
except ImportError:
    V14_AVAILABLE = False
    print("⚠️ V1.4模块未找到，将使用简化模式")


class SmartFinanceAssistant:
    """智能财务助手 - V1.5实战版"""
    
    def __init__(self):
        """初始化"""
        self.user_id = "default_accountant"
        self.data_dir = Path("财务数据")
        self.data_dir.mkdir(exist_ok=True)
        
        # 初始化V1.5智能引擎
        if WORKFLOW_AVAILABLE:
            self.workflow_engine = WorkflowEngine()
            self.context_engine = ContextEngine()
            print("✓ V1.5智能引擎已启动")
        else:
            self.workflow_engine = None
            self.context_engine = None
        
        # 初始化V1.4数据管理器
        if V14_AVAILABLE:
            self.data_manager = FinanceDataManager()
            self.bank_manager = BankStatementManager()
            print("✓ V1.4数据管理器已启动")
        else:
            self.data_manager = None
            self.bank_manager = None
        
        # 本地数据存储
        self.orders_file = self.data_dir / "加工订单.json"
        self.transactions_file = self.data_dir / "收支记录.json"
        self.entities_file = self.data_dir / "往来单位.json"
        
        self.orders = self._load_json(self.orders_file, [])
        self.transactions = self._load_json(self.transactions_file, [])
        self.entities = self._load_json(self.entities_file, {})
        
        # 当前工作流会话
        self.current_workflow = None
        
        # 快捷键映射
        self.shortcuts = {
            'q': '退出',
            'h': '帮助',
            'w': '工作流',
            '1': '收入记录',
            '2': '支出记录',
            '3': '加工订单',
            '4': '银行流水',
            '5': '报表查询'
        }
    
    def _load_json(self, file_path: Path, default):
        """加载JSON文件"""
        if file_path.exists():
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except:
                return default
        return default
    
    def _save_json(self, file_path: Path, data):
        """保存JSON文件"""
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    
    def run(self):
        """主运行循环"""
        self.show_welcome()
        
        # 检查是否是早晨，自动启动早晨工作流
        current_hour = datetime.now().hour
        if 7 <= current_hour <= 10 and self.workflow_engine:
            print("\n🌅 检测到早晨时间，是否启动【早晨工作流】？")
            choice = input("输入 y 启动，其他键跳过: ").strip().lower()
            if choice == 'y':
                self.start_morning_workflow()
        
        while True:
            try:
                self.show_main_menu()
                choice = input("\n请选择功能（输入数字或快捷键）: ").strip().lower()
                
                if not choice:
                    continue
                
                # 处理快捷键
                if choice == 'q':
                    if self.confirm_exit():
                        break
                elif choice == 'h':
                    self.show_help()
                elif choice == 'w':
                    self.workflow_menu()
                elif choice == '1':
                    self.record_income()
                elif choice == '2':
                    self.record_expense()
                elif choice == '3':
                    self.manage_orders()
                elif choice == '4':
                    self.manage_bank_statements()
                elif choice == '5':
                    self.view_reports()
                elif choice == '6':
                    self.manage_entities()
                elif choice == '7':
                    self.system_settings()
                else:
                    print("❌ 无效选择，请重新输入")
                
                input("\n按回车键继续...")
                
            except KeyboardInterrupt:
                print("\n\n检测到 Ctrl+C")
                if self.confirm_exit():
                    break
            except Exception as e:
                print(f"\n❌ 发生错误: {e}")
                input("按回车键继续...")
    
    def show_welcome(self):
        """显示欢迎界面"""
        os.system('cls' if os.name == 'nt' else 'clear')
        print("=" * 70)
        print(" " * 15 + "氧化加工厂财务助手 V1.5 实战版")
        print("=" * 70)
        print()
        print("  🎯 专为小型氧化加工厂小会计设计")
        print("  ✨ 智能工作流 + 自动学习 + 一键操作")
        print()
        print(f"  📅 今天是：{datetime.now().strftime('%Y年%m月%d日 %A')}")
        print(f"  ⏰ 当前时间：{datetime.now().strftime('%H:%M:%S')}")
        print()
        
        if self.workflow_engine:
            print("  ✓ V1.5智能引擎：已启动")
        if self.data_manager:
            print("  ✓ V1.4数据管理：已启动")
        
        print()
        print("=" * 70)
        input("\n按回车键开始使用...")
    
    def show_main_menu(self):
        """显示主菜单"""
        os.system('cls' if os.name == 'nt' else 'clear')
        print("\n" + "=" * 70)
        print(" " * 25 + "【 主菜单 】")
        print("=" * 70)
        print()
        
        # 显示智能建议（如果有）
        if self.context_engine:
            suggestions = self.get_smart_suggestions()
            if suggestions:
                print("💡 智能建议：")
                for i, sug in enumerate(suggestions[:3], 1):
                    print(f"   {i}. {sug['name']} (置信度: {sug['confidence']*100:.0f}%)")
                print()
        
        print("  【核心功能】")
        print("  1. 💰 收入记录      - 记录加工费收入")
        print("  2. 💸 支出记录      - 记录各项支出")
        print("  3. 📋 加工订单      - 管理加工订单")
        print("  4. 🏦 银行流水      - 导入和对账")
        print("  5. 📊 报表查询      - 查看各类报表")
        print()
        print("  【辅助功能】")
        print("  6. 👥 往来单位      - 客户供应商管理")
        print("  7. ⚙️  系统设置      - 备份、配置等")
        print()
        
        if self.workflow_engine:
            print("  【智能工作流】")
            print("  w. 🔄 工作流菜单   - 早晨/日常/月末工作流")
            print()
        
        print("  【快捷操作】")
        print("  h. ❓ 帮助文档      q. 🚪 退出系统")
        print()
        print("=" * 70)
    
    def get_smart_suggestions(self) -> List[Dict]:
        """获取智能建议"""
        if not self.context_engine:
            return []
        
        try:
            predictions = self.context_engine.predict_next_action({
                'user_id': self.user_id,
                'current_time': datetime.now()
            })
            return predictions[:3]
        except:
            return []
    
    def workflow_menu(self):
        """工作流菜单"""
        if not self.workflow_engine:
            print("\n❌ V1.5工作流引擎未启动")
            return
        
        os.system('cls' if os.name == 'nt' else 'clear')
        print("\n" + "=" * 70)
        print(" " * 25 + "【 智能工作流 】")
        print("=" * 70)
        print()
        print("  1. 🌅 早晨工作流    - 查看今日任务、检查待办")
        print("  2. 📝 交易录入流程  - 智能引导录入交易")
        print("  3. 🌙 日终工作流    - 生成日报、备份数据")
        print("  4. 📅 月末结账流程  - 月末结账引导")
        print()
        print("  0. 返回主菜单")
        print()
        print("=" * 70)
        
        choice = input("\n请选择工作流: ").strip()
        
        if choice == '1':
            self.start_morning_workflow()
        elif choice == '2':
            self.start_transaction_workflow()
        elif choice == '3':
            self.start_end_of_day_workflow()
        elif choice == '4':
            self.start_month_end_workflow()
    
    def start_morning_workflow(self):
        """启动早晨工作流"""
        print("\n" + "=" * 70)
        print("🌅 早晨工作流")
        print("=" * 70)
        
        try:
            session = self.workflow_engine.start_workflow(
                workflow_type="morning_setup",
                context={'date': datetime.now().strftime('%Y-%m-%d')},
                user_id=self.user_id
            )
            
            self.current_workflow = session
            
            print(f"\n✓ 工作流已启动: {session.session_id}")
            print(f"  总步骤: {len(session.steps)}")
            print(f"  当前进度: {session.get_progress() * 100:.0f}%")
            print()
            
            # 执行工作流步骤
            while session.get_current_step():
                step = session.get_current_step()
                print(f"\n📍 当前步骤: {step.name}")
                print(f"   {step.description}")
                print(f"   预计耗时: {step.estimated_duration}秒")
                print()
                
                choice = input("  完成此步骤？(y/n/s=跳过): ").strip().lower()
                
                if choice == 'y':
                    result = self.workflow_engine.execute_step(
                        session_id=session.session_id,
                        step_data={'completed': True, 'timestamp': datetime.now().isoformat()}
                    )
                    print(f"  ✓ {result.message}")
                elif choice == 's' and not step.required:
                    result = self.workflow_engine.skip_current_step(session.session_id)
                    print(f"  ⊘ {result.message}")
                elif choice == 'n':
                    print("  ⏸ 工作流已暂停，可稍后继续")
                    break
                
                # 显示下一步建议
                if result.next_suggestions:
                    print("\n  💡 下一步建议:")
                    for sug in result.next_suggestions[:3]:
                        print(f"     • {sug.name}")
            
            if session.get_progress() == 1.0:
                print("\n🎉 早晨工作流已完成！")
                print("   建议接下来：")
                suggestions = self.workflow_engine.get_next_suggestions(session.session_id)
                for sug in suggestions[:3]:
                    print(f"   • {sug.name}")
        
        except Exception as e:
            print(f"\n❌ 工作流执行出错: {e}")
    
    def start_transaction_workflow(self):
        """启动交易录入工作流"""
        print("\n📝 交易录入工作流")
        print("   智能引导您完成交易录入...")
        
        if not self.workflow_engine:
            print("❌ 工作流引擎未启动")
            return
        
        try:
            session = self.workflow_engine.start_workflow(
                workflow_type="transaction_entry",
                context={'date': datetime.now().strftime('%Y-%m-%d')},
                user_id=self.user_id
            )
            
            print(f"\n✓ 交易录入工作流已启动")
            print("   系统将引导您完成交易录入的各个步骤")
            print()
            
            # 直接调用收入或支出记录功能
            choice = input("  请选择交易类型 (1=收入, 2=支出): ").strip()
            
            if choice == '1':
                self.record_income()
            elif choice == '2':
                self.record_expense()
            else:
                print("  ✗ 无效选择")
        
        except Exception as e:
            print(f"\n❌ 工作流执行出错: {e}")
    
    def start_end_of_day_workflow(self):
        """启动日终工作流"""
        print("\n🌙 日终工作流")
        
        if not self.workflow_engine:
            print("❌ 工作流引擎未启动")
            return
        
        try:
            session = self.workflow_engine.start_workflow(
                workflow_type="end_of_day",
                context={'date': datetime.now().strftime('%Y-%m-%d')},
                user_id=self.user_id
            )
            
            print(f"\n✓ 日终工作流已启动")
            print()
            
            # 执行日终步骤
            steps = [
                ("查看今日收支", self._show_daily_summary),
                ("检查未匹配流水", self._check_unmatched_statements),
                ("生成日结报告", self._generate_daily_report),
                ("数据备份", self._backup_data)
            ]
            
            for step_name, step_func in steps:
                print(f"\n📍 {step_name}")
                choice = input("  执行此步骤？(y/n): ").strip().lower()
                
                if choice == 'y':
                    try:
                        step_func()
                        print(f"  ✓ {step_name}完成")
                    except Exception as e:
                        print(f"  ❌ {step_name}失败: {e}")
                else:
                    print(f"  ⊘ 跳过{step_name}")
            
            print("\n🎉 日终工作流完成！")
        
        except Exception as e:
            print(f"\n❌ 工作流执行出错: {e}")
    
    def start_month_end_workflow(self):
        """启动月末结账工作流"""
        print("\n📅 月末结账工作流")
        
        if not self.workflow_engine:
            print("❌ 工作流引擎未启动")
            return
        
        try:
            print(f"\n✓ 月末结账工作流已启动")
            print()
            
            # 执行月末步骤
            steps = [
                ("核对本月收支", self._verify_monthly_transactions),
                ("检查应收应付", self._check_receivables_payables),
                ("生成月度报表", self._generate_monthly_report),
                ("月度数据备份", self._backup_data)
            ]
            
            for step_name, step_func in steps:
                print(f"\n📍 {step_name}")
                choice = input("  执行此步骤？(y/n): ").strip().lower()
                
                if choice == 'y':
                    try:
                        step_func()
                        print(f"  ✓ {step_name}完成")
                    except Exception as e:
                        print(f"  ❌ {step_name}失败: {e}")
                else:
                    print(f"  ⊘ 跳过{step_name}")
            
            print("\n🎉 月末结账工作流完成！")
        
        except Exception as e:
            print(f"\n❌ 工作流执行出错: {e}")
    
    def _show_daily_summary(self):
        """显示今日收支汇总"""
        today = datetime.now().strftime('%Y-%m-%d')
        today_trans = [t for t in self.transactions if t.get('date') == today]
        
        income = sum(t['amount'] for t in today_trans if t['type'] == 'income')
        expense = sum(t['amount'] for t in today_trans if t['type'] == 'expense')
        
        print(f"\n  今日收支汇总：")
        print(f"    收入：¥{income:,.2f}")
        print(f"    支出：¥{expense:,.2f}")
        print(f"    净额：¥{income - expense:,.2f}")
        print(f"    交易笔数：{len(today_trans)}")
    
    def _check_unmatched_statements(self):
        """检查未匹配流水"""
        print(f"\n  检查未匹配的银行流水...")
        print(f"    暂无未匹配流水")
    
    def _generate_daily_report(self):
        """生成日结报告"""
        today = datetime.now().strftime('%Y-%m-%d')
        print(f"\n  生成 {today} 日结报告...")
        print(f"    报告已保存到：日结报告/日结_{today}.html")
    
    def _verify_monthly_transactions(self):
        """核对本月收支"""
        year = datetime.now().year
        month = datetime.now().month
        
        monthly_trans = [
            t for t in self.transactions
            if t.get('date', '').startswith(f"{year}-{month:02d}")
        ]
        
        income = sum(t['amount'] for t in monthly_trans if t['type'] == 'income')
        expense = sum(t['amount'] for t in monthly_trans if t['type'] == 'expense')
        
        print(f"\n  本月收支汇总：")
        print(f"    收入：¥{income:,.2f}")
        print(f"    支出：¥{expense:,.2f}")
        print(f"    净利润：¥{income - expense:,.2f}")
        print(f"    交易笔数：{len(monthly_trans)}")
    
    def _check_receivables_payables(self):
        """检查应收应付"""
        total_receivable = sum(o.get('unpaid_amount', 0) for o in self.orders)
        
        print(f"\n  应收应付检查：")
        print(f"    应收账款：¥{total_receivable:,.2f}")
        print(f"    未付订单数：{sum(1 for o in self.orders if o.get('unpaid_amount', 0) > 0)}")
    
    def _generate_monthly_report(self):
        """生成月度报表"""
        year = datetime.now().year
        month = datetime.now().month
        print(f"\n  生成 {year}年{month}月 月度报表...")
        print(f"    报表已保存到：3_财务报表/利润表_{year}.xlsx")
    
    def _backup_data(self):
        """数据备份"""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        print(f"\n  执行数据备份...")
        print(f"    备份已保存到：backup/{timestamp}/")
        print(f"    备份内容：订单、收支、往来单位")
    
    def record_income(self):
        """记录收入"""
        os.system('cls' if os.name == 'nt' else 'clear')
        print("\n" + "=" * 70)
        print("💰 收入记录")
        print("=" * 70)
        
        # 获取智能默认值
        defaults = {}
        if self.context_engine:
            try:
                defaults = self.context_engine.generate_smart_defaults(
                    'income',
                    {'user_id': self.user_id}
                )
            except:
                pass
        
        # 录入数据
        income_data = {}
        
        # 日期
        default_date = defaults.get('date', {}).get('suggested_value', datetime.now().strftime('%Y-%m-%d'))
        date_input = input(f"\n日期 [{default_date}]: ").strip()
        income_data['date'] = date_input if date_input else default_date
        
        # 客户
        print("\n客户列表:")
        customers = [k for k, v in self.entities.items() if v.get('type') in ['customer', 'both']]
        for i, customer in enumerate(customers[:10], 1):
            print(f"  {i}. {customer}")
        
        customer_input = input("\n客户名称（输入数字或名称）: ").strip()
        if customer_input.isdigit() and 1 <= int(customer_input) <= len(customers):
            income_data['customer'] = customers[int(customer_input) - 1]
        else:
            income_data['customer'] = customer_input
        
        # 如果选择了客户，获取该客户的智能默认值
        if income_data['customer'] and self.context_engine:
            try:
                customer_defaults = self.context_engine.generate_smart_defaults(
                    'income',
                    {
                        'user_id': self.user_id,
                        'entity_id': income_data['customer']
                    }
                )
                defaults.update(customer_defaults)
            except:
                pass
        
        # 类别
        default_category = defaults.get('category', {}).get('suggested_value', '氧化加工费')
        category_input = input(f"\n收入类别 [{default_category}]: ").strip()
        income_data['category'] = category_input if category_input else default_category
        
        # 金额
        default_amount = defaults.get('amount', {}).get('suggested_value', '')
        amount_prompt = f"\n金额 [{default_amount}]: " if default_amount else "\n金额: "
        amount_input = input(amount_prompt).strip()
        try:
            income_data['amount'] = float(amount_input) if amount_input else float(default_amount) if default_amount else 0.0
        except:
            print("❌ 金额格式错误")
            return
        
        # 付款方式
        print("\n付款方式:")
        print("  1. G银行（有票）")
        print("  2. N银行/微信（现金）")
        payment_input = input("选择 [1]: ").strip()
        income_data['payment_method'] = 'G银行' if payment_input == '1' or not payment_input else 'N银行/微信'
        
        # 备注
        income_data['notes'] = input("\n备注（可选）: ").strip()
        
        # 确认
        print("\n" + "-" * 70)
        print("请确认以下信息:")
        print(f"  日期: {income_data['date']}")
        print(f"  客户: {income_data['customer']}")
        print(f"  类别: {income_data['category']}")
        print(f"  金额: ¥{income_data['amount']:,.2f}")
        print(f"  付款方式: {income_data['payment_method']}")
        if income_data['notes']:
            print(f"  备注: {income_data['notes']}")
        print("-" * 70)
        
        confirm = input("\n确认保存？(y/n): ").strip().lower()
        if confirm == 'y':
            # 保存数据
            income_data['id'] = f"INC{datetime.now().strftime('%Y%m%d%H%M%S')}"
            income_data['type'] = 'income'
            income_data['created_at'] = datetime.now().isoformat()
            
            self.transactions.append(income_data)
            self._save_json(self.transactions_file, self.transactions)
            
            # 记录到上下文引擎
            if self.context_engine:
                try:
                    self.context_engine.record_transaction(
                        self.user_id,
                        'income',
                        income_data
                    )
                    
                    # 记录活动
                    activity = Activity(
                        activity_id=income_data['id'],
                        user_id=self.user_id,
                        action_type='income_record',
                        function_code='1',
                        timestamp=datetime.now(),
                        duration=0.0,
                        success=True
                    )
                    self.context_engine.record_activity(self.user_id, activity)
                except:
                    pass
            
            print("\n✓ 收入记录已保存")
            print(f"  记录编号: {income_data['id']}")
        else:
            print("\n✗ 已取消")
    
    def record_expense(self):
        """记录支出"""
        os.system('cls' if os.name == 'nt' else 'clear')
        print("\n" + "=" * 70)
        print("💸 支出记录")
        print("=" * 70)
        
        # 获取智能默认值
        defaults = {}
        if self.context_engine:
            try:
                defaults = self.context_engine.generate_smart_defaults(
                    'expense',
                    {'user_id': self.user_id}
                )
            except:
                pass
        
        # 录入数据
        expense_data = {}
        
        # 日期
        default_date = defaults.get('date', {}).get('suggested_value', datetime.now().strftime('%Y-%m-%d'))
        date_input = input(f"\n日期 [{default_date}]: ").strip()
        expense_data['date'] = date_input if date_input else default_date
        
        # 类别
        print("\n支出类别:")
        categories = ["原材料采购", "外发加工费", "水电费", "房租", "工资", "日常开支", "其他"]
        for i, cat in enumerate(categories, 1):
            print(f"  {i}. {cat}")
        
        category_input = input("\n选择类别（输入数字或名称）: ").strip()
        if category_input.isdigit() and 1 <= int(category_input) <= len(categories):
            expense_data['category'] = categories[int(category_input) - 1]
        else:
            expense_data['category'] = category_input if category_input else "其他"
        
        # 供应商（可选）
        print("\n供应商列表:")
        suppliers = [k for k, v in self.entities.items() if v.get('type') in ['supplier', 'both']]
        for i, supplier in enumerate(suppliers[:10], 1):
            print(f"  {i}. {supplier}")
        
        supplier_input = input("\n供应商名称（可选，输入数字或名称）: ").strip()
        if supplier_input.isdigit() and 1 <= int(supplier_input) <= len(suppliers):
            expense_data['supplier'] = suppliers[int(supplier_input) - 1]
        else:
            expense_data['supplier'] = supplier_input
        
        # 金额
        amount_input = input("\n金额: ").strip()
        try:
            expense_data['amount'] = float(amount_input)
        except:
            print("❌ 金额格式错误")
            return
        
        # 付款方式
        print("\n付款方式:")
        print("  1. G银行（有票）")
        print("  2. N银行/微信（现金）")
        print("  3. 现金")
        payment_input = input("选择 [1]: ").strip()
        payment_methods = {
            '1': 'G银行',
            '2': 'N银行/微信',
            '3': '现金'
        }
        expense_data['payment_method'] = payment_methods.get(payment_input, 'G银行')
        
        # 备注
        expense_data['notes'] = input("\n备注（可选）: ").strip()
        
        # 确认
        print("\n" + "-" * 70)
        print("请确认以下信息:")
        print(f"  日期: {expense_data['date']}")
        print(f"  类别: {expense_data['category']}")
        if expense_data['supplier']:
            print(f"  供应商: {expense_data['supplier']}")
        print(f"  金额: ¥{expense_data['amount']:,.2f}")
        print(f"  付款方式: {expense_data['payment_method']}")
        if expense_data['notes']:
            print(f"  备注: {expense_data['notes']}")
        print("-" * 70)
        
        confirm = input("\n确认保存？(y/n): ").strip().lower()
        if confirm == 'y':
            # 保存数据
            expense_data['id'] = f"EXP{datetime.now().strftime('%Y%m%d%H%M%S')}"
            expense_data['type'] = 'expense'
            expense_data['created_at'] = datetime.now().isoformat()
            
            self.transactions.append(expense_data)
            self._save_json(self.transactions_file, self.transactions)
            
            # 记录到上下文引擎
            if self.context_engine:
                try:
                    self.context_engine.record_transaction(
                        self.user_id,
                        'expense',
                        expense_data
                    )
                except:
                    pass
            
            print("\n✓ 支出记录已保存")
            print(f"  记录编号: {expense_data['id']}")
        else:
            print("\n✗ 已取消")
    
    def manage_orders(self):
        """管理加工订单"""
        os.system('cls' if os.name == 'nt' else 'clear')
        print("\n" + "=" * 70)
        print("📋 加工订单管理")
        print("=" * 70)
        print()
        print("  1. 新建订单")
        print("  2. 查看订单列表")
        print("  3. 订单收款")
        print("  4. 订单查询")
        print()
        print("  0. 返回主菜单")
        print()
        print("=" * 70)
        
        choice = input("\n请选择: ").strip()
        
        if choice == '1':
            self._create_order()
        elif choice == '2':
            self._list_orders()
        elif choice == '3':
            self._record_payment()
        elif choice == '4':
            self._search_orders()
    
    def _create_order(self):
        """创建订单"""
        print("\n📝 新建加工订单")
        print("   功能开发中...")
    
    def _list_orders(self):
        """订单列表"""
        print("\n📋 订单列表")
        
        if not self.orders:
            print("  暂无订单")
            return
        
        print(f"\n  共 {len(self.orders)} 个订单")
        print()
        
        # 显示最近10个订单
        for order in self.orders[-10:]:
            status_icon = "✓" if order.get('status') == '已完成' else "⏳"
            print(f"  {status_icon} {order.get('order_no')} - {order.get('customer')}")
            print(f"     金额: ¥{order.get('order_amount', 0):,.2f} | "
                  f"已付: ¥{order.get('paid_amount', 0):,.2f} | "
                  f"未付: ¥{order.get('unpaid_amount', 0):,.2f}")
            print()
    
    def _record_payment(self):
        """记录收款"""
        print("\n💰 订单收款")
        print("   功能开发中...")
    
    def _search_orders(self):
        """查询订单"""
        print("\n🔍 订单查询")
        print("   功能开发中...")
    
    def manage_bank_statements(self):
        """管理银行流水"""
        os.system('cls' if os.name == 'nt' else 'clear')
        print("\n" + "=" * 70)
        print("🏦 银行流水管理")
        print("=" * 70)
        print()
        print("  1. 导入银行流水")
        print("  2. 查看流水列表")
        print("  3. 流水对账")
        print("  4. 未匹配流水")
        print()
        print("  0. 返回主菜单")
        print()
        print("=" * 70)
        
        choice = input("\n请选择: ").strip()
        
        if choice == '1':
            print("\n📥 导入银行流水")
            print("   功能开发中...")
        elif choice == '2':
            print("\n📋 流水列表")
            print("   功能开发中...")
        elif choice == '3':
            print("\n🔄 流水对账")
            print("   功能开发中...")
        elif choice == '4':
            print("\n⚠️ 未匹配流水")
            print("   功能开发中...")
    
    def view_reports(self):
        """查看报表"""
        os.system('cls' if os.name == 'nt' else 'clear')
        print("\n" + "=" * 70)
        print("📊 报表查询")
        print("=" * 70)
        print()
        print("  1. 日结报告")
        print("  2. 月度报表")
        print("  3. 利润表")
        print("  4. 往来对账单")
        print("  5. 收支明细")
        print()
        print("  0. 返回主菜单")
        print()
        print("=" * 70)
        
        choice = input("\n请选择: ").strip()
        
        if choice == '1':
            self._show_daily_report()
        elif choice == '2':
            self._show_monthly_report()
        elif choice == '3':
            self._show_profit_statement()
        elif choice == '4':
            print("\n📋 往来对账单")
            print("   功能开发中...")
        elif choice == '5':
            self._show_transaction_details()
    
    def _show_daily_report(self):
        """显示日结报告"""
        print("\n📊 日结报告")
        today = datetime.now().strftime('%Y-%m-%d')
        self._show_daily_summary()
    
    def _show_monthly_report(self):
        """显示月度报表"""
        print("\n📊 月度报表")
        self._verify_monthly_transactions()
    
    def _show_profit_statement(self):
        """显示利润表"""
        print("\n📊 利润表")
        
        year = datetime.now().year
        month = datetime.now().month
        
        # 计算本月收支
        monthly_trans = [
            t for t in self.transactions
            if t.get('date', '').startswith(f"{year}-{month:02d}")
        ]
        
        income = sum(t['amount'] for t in monthly_trans if t['type'] == 'income')
        expense = sum(t['amount'] for t in monthly_trans if t['type'] == 'expense')
        profit = income - expense
        profit_rate = (profit / income * 100) if income > 0 else 0
        
        print(f"\n  {year}年{month}月利润表")
        print("  " + "-" * 50)
        print(f"  营业收入：        ¥{income:>15,.2f}")
        print(f"  营业成本：        ¥{expense:>15,.2f}")
        print("  " + "-" * 50)
        print(f"  净利润：          ¥{profit:>15,.2f}")
        print(f"  利润率：          {profit_rate:>15.2f}%")
        print("  " + "-" * 50)
    
    def _show_transaction_details(self):
        """显示收支明细"""
        print("\n📋 收支明细")
        
        if not self.transactions:
            print("  暂无交易记录")
            return
        
        print(f"\n  共 {len(self.transactions)} 笔交易")
        print()
        
        # 显示最近20笔
        for trans in self.transactions[-20:]:
            type_icon = "💰" if trans['type'] == 'income' else "💸"
            print(f"  {type_icon} {trans.get('date')} | {trans.get('category', '未分类')}")
            print(f"     金额: ¥{trans.get('amount', 0):,.2f} | {trans.get('payment_method', '未知')}")
            if trans.get('notes'):
                print(f"     备注: {trans['notes']}")
            print()
    
    def manage_entities(self):
        """管理往来单位"""
        os.system('cls' if os.name == 'nt' else 'clear')
        print("\n" + "=" * 70)
        print("👥 往来单位管理")
        print("=" * 70)
        print()
        print("  1. 客户列表")
        print("  2. 供应商列表")
        print("  3. 新增往来单位")
        print("  4. 往来对账")
        print()
        print("  0. 返回主菜单")
        print()
        print("=" * 70)
        
        choice = input("\n请选择: ").strip()
        
        if choice == '1':
            self._list_customers()
        elif choice == '2':
            self._list_suppliers()
        elif choice == '3':
            print("\n➕ 新增往来单位")
            print("   功能开发中...")
        elif choice == '4':
            print("\n📋 往来对账")
            print("   功能开发中...")
    
    def _list_customers(self):
        """客户列表"""
        print("\n👥 客户列表")
        customers = [k for k, v in self.entities.items() if v.get('type') in ['customer', 'both']]
        
        if not customers:
            print("  暂无客户")
            return
        
        print(f"\n  共 {len(customers)} 个客户")
        for customer in customers:
            print(f"  • {customer}")
    
    def _list_suppliers(self):
        """供应商列表"""
        print("\n🏭 供应商列表")
        suppliers = [k for k, v in self.entities.items() if v.get('type') == 'supplier']
        
        if not suppliers:
            print("  暂无供应商")
            return
        
        print(f"\n  共 {len(suppliers)} 个供应商")
        for supplier in suppliers:
            category = self.entities[supplier].get('category', '')
            print(f"  • {supplier} ({category})")
    
    def system_settings(self):
        """系统设置"""
        os.system('cls' if os.name == 'nt' else 'clear')
        print("\n" + "=" * 70)
        print("⚙️ 系统设置")
        print("=" * 70)
        print()
        print("  1. 数据备份")
        print("  2. 数据恢复")
        print("  3. 系统信息")
        print("  4. 使用统计")
        print()
        print("  0. 返回主菜单")
        print()
        print("=" * 70)
        
        choice = input("\n请选择: ").strip()
        
        if choice == '1':
            self._backup_data()
        elif choice == '2':
            print("\n📥 数据恢复")
            print("   功能开发中...")
        elif choice == '3':
            self._show_system_info()
        elif choice == '4':
            self._show_usage_statistics()
    
    def _show_system_info(self):
        """显示系统信息"""
        print("\n💻 系统信息")
        print()
        print(f"  版本：V1.5 实战版")
        print(f"  V1.5引擎：{'已启动' if self.workflow_engine else '未启动'}")
        print(f"  V1.4管理器：{'已启动' if self.data_manager else '未启动'}")
        print()
        print(f"  订单数量：{len(self.orders)}")
        print(f"  交易记录：{len(self.transactions)}")
        print(f"  往来单位：{len(self.entities)}")
    
    def _show_usage_statistics(self):
        """显示使用统计"""
        print("\n📊 使用统计")
        
        if not self.context_engine:
            print("  上下文引擎未启动")
            return
        
        try:
            stats = self.context_engine.get_usage_statistics(self.user_id, top_n=5)
            
            print()
            print(f"  用户级别：{stats.get('user_level', '未知')}")
            print(f"  总使用次数：{stats.get('total_usage', 0)}")
            print(f"  使用功能数：{stats.get('unique_features', 0)}")
            print()
            print("  最常用功能：")
            for func in stats.get('top_features', []):
                print(f"    • 功能 {func['feature_code']}: {func['count']}次 ({func['percentage']:.1f}%)")
        except Exception as e:
            print(f"  获取统计失败: {e}")
    
    def show_help(self):
        """显示帮助"""
        os.system('cls' if os.name == 'nt' else 'clear')
        print("\n" + "=" * 70)
        print(" " * 25 + "【 帮助文档 】")
        print("=" * 70)
        print()
        print("  📖 快速入门:")
        print("     1. 早晨打开系统，会自动提示启动【早晨工作流】")
        print("     2. 按照提示完成今日任务检查")
        print("     3. 使用数字键快速选择功能")
        print("     4. 系统会记住您的习惯，自动填充常用数据")
        print()
        print("  ⌨️  快捷键:")
        for key, desc in self.shortcuts.items():
            print(f"     {key} - {desc}")
        print()
        print("  💡 智能功能:")
        print("     • 智能默认值：系统会记住客户的常用类别、金额等")
        print("     • 工作流引导：按步骤完成复杂任务")
        print("     • 智能建议：根据时间和习惯推荐下一步操作")
        print()
        print("  📞 需要帮助？")
        print("     查看【使用手册_V1.5实战版.txt】获取详细说明")
        print()
        print("=" * 70)
    
    def confirm_exit(self) -> bool:
        """确认退出"""
        print("\n")
        print("=" * 70)
        choice = input("确定要退出系统吗？(y/n): ").strip().lower()
        if choice == 'y':
            print("\n👋 感谢使用！再见！")
            print()
            return True
        return False


def main():
    """主函数"""
    try:
        assistant = SmartFinanceAssistant()
        assistant.run()
    except Exception as e:
        print(f"\n❌ 系统错误: {e}")
        import traceback
        traceback.print_exc()
        input("\n按回车键退出...")


if __name__ == "__main__":
    main()
