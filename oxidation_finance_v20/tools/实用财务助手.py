#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
氧化加工厂财务助手 - 实用版
根据国内小型氧化加工厂实际情况优化，提高会计工作效率

功能特点：
1. 日常高频操作快捷入口
2. 快速录单/收款/付款
3. 实用报表一键生成
4. 减少输入步骤，智能提示
"""

import os
import sys
import json
from datetime import datetime, date, timedelta
from decimal import Decimal

# 设置项目路径
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

try:
    from database.db_manager import DatabaseManager
    from utils.config import get_db_path
    HAS_FULL_SYSTEM = True
except ImportError:
    HAS_FULL_SYSTEM = False
    get_db_path = lambda: "oxidation_finance_demo_ready.db"


class PracticalFinanceHelper:
    """实用版财务助手 - 提高工作效率"""
    
    def __init__(self):
        self.data_file = os.path.join(project_root, "simple_finance_data.json")
        self.load_data()
        
    def load_data(self):
        """加载数据"""
        if os.path.exists(self.data_file):
            try:
                with open(self.data_file, 'r', encoding='utf-8') as f:
                    self.data = json.load(f)
            except:
                self.init_empty_data()
        else:
            self.init_empty_data()
            
    def init_empty_data(self):
        """初始化空数据"""
        self.data = {
            "customers": [],
            "orders": [],
            "income": [],
            "expenses": [],
            "bank_transactions": [],
            "suppliers": [],
            "last_updated": str(datetime.now())
        }
        
    def save_data(self):
        """保存数据"""
        self.data['last_updated'] = str(datetime.now())
        try:
            with open(self.data_file, 'w', encoding='utf-8') as f:
                json.dump(self.data, f, ensure_ascii=False, indent=2, default=str)
            return True
        except Exception as e:
            print(f"保存失败: {e}")
            return False
    
    # ========== 核心业务功能 ==========
    
    def add_customer(self, name, contact="", phone=""):
        """添加客户"""
        customer_id = f"C{len(self.data['customers']) + 1:03d}"
        customer = {
            "id": customer_id,
            "name": name,
            "contact": contact,
            "phone": phone,
            "created_at": str(datetime.now())
        }
        self.data['customers'].append(customer)
        self.save_data()
        return customer
    
    def add_order(self, customer_id, item_name, quantity, unit_price, pricing_unit, processes=None):
        """添加订单"""
        amount = Decimal(str(quantity)) * Decimal(str(unit_price))
        order_id = f"O{len(self.data['orders']) + 1:04d}"
        order = {
            "id": order_id,
            "customer_id": customer_id,
            "item_name": item_name,
            "quantity": float(quantity),
            "unit_price": str(unit_price),
            "pricing_unit": pricing_unit,
            "amount": str(amount),
            "outsourcing_processes": processes or [],
            "status": "待加工",
            "created_at": str(datetime.now())
        }
        self.data['orders'].append(order)
        self.save_data()
        return order
    
    def add_income(self, customer_id, amount, bank_type="G银行", description=""):
        """添加收入"""
        income_id = f"I{len(self.data['income']) + 1:04d}"
        income = {
            "id": income_id,
            "customer_id": customer_id,
            "amount": str(amount),
            "bank_type": bank_type,
            "description": description,
            "date": str(date.today()),
            "created_at": str(datetime.now())
        }
        self.data['income'].append(income)
        self.save_data()
        return income
    
    def add_expense(self, expense_type, amount, description="", supplier=""):
        """添加支出"""
        expense_id = f"E{len(self.data['expenses']) + 1:04d}"
        expense = {
            "id": expense_id,
            "type": expense_type,
            "amount": str(amount),
            "description": description,
            "supplier": supplier,
            "date": str(date.today()),
            "created_at": str(datetime.now())
        }
        self.data['expenses'].append(expense)
        self.save_data()
        return expense
    
    # ========== 高效功能 ==========
    
    def quick_add_income(self):
        """快速收款 - 减少输入步骤"""
        print("\n" + "="*50)
        print("💰 快速收款")
        print("="*50)
        
        # 显示客户列表供选择
        if not self.data['customers']:
            print("暂无客户，请先添加客户")
            return None
        
        print("\n客户列表:")
        for i, c in enumerate(self.data['customers'], 1):
            print(f"  {i}. {c['name']}")
        
        try:
            # 选择客户
            idx = int(input("\n选择客户编号: ")) - 1
            if idx < 0 or idx >= len(self.data['customers']):
                print("无效选择")
                return None
            
            customer = self.data['customers'][idx]
            
            # 输入金额
            amount = input("收款金额: ")
            if not amount:
                return None
            amount = float(amount)
            
            # 选择银行
            print("\n银行类型: 1.G银行(有票)  2.N银行(现金)  3.微信")
            bank_choice = input("选择 [1-3]: ")
            bank_map = {"1": "G银行", "2": "N银行", "3": "微信"}
            bank_type = bank_map.get(bank_choice, "G银行")
            
            # 描述
            desc = input("备注说明: ")
            
            # 添加收入
            self.add_income(customer['id'], amount, bank_type, desc or f"{customer['name']}收款")
            print(f"\n✅ 收款成功！{customer['name']} - ¥{amount}")
            return True
            
        except (ValueError, IndexError):
            print("输入错误")
            return None
    
    def quick_add_expense(self):
        """快速付款 - 减少输入步骤"""
        print("\n" + "="*50)
        print("💸 快速付款")
        print("="*50)
        
        # 显示支出类型
        expense_types = [
            ("房租", "厂房/办公租金"),
            ("水电费", "水费和电费"),
            ("三酸", "硫酸/盐酸/硝酸"),
            ("片碱", "氢氧化钠"),
            ("亚钠", "亚硝酸钠"),
            ("色粉", "各种颜色粉末"),
            ("除油剂", "金属表面处理剂"),
            ("挂具", "电镀/氧化挂具"),
            ("外发加工费", "喷砂/拉丝/抛光外包"),
            ("工资", "员工工资"),
            ("日常费用", "办公/交通/通讯"),
            ("其他", "其他支出")
        ]
        
        print("\n支出类型:")
        for i, (etype, desc) in enumerate(expense_types, 1):
            print(f"  {i}. {etype} - {desc}")
        
        try:
            idx = int(input("\n选择支出类型 [1-12]: ")) - 1
            if idx < 0 or idx >= len(expense_types):
                print("无效选择")
                return None
            
            expense_type = expense_types[idx][0]
            
            # 输入金额
            amount = input("付款金额: ")
            if not amount:
                return None
            amount = float(amount)
            
            # 描述
            desc = input("备注说明: ")
            
            # 添加支出
            self.add_expense(expense_type, amount, desc or expense_type)
            print(f"\n✅ 付款记录成功！{expense_type} - ¥{amount}")
            return True
            
        except (ValueError, IndexError):
            print("输入错误")
            return None
    
    def quick_add_order(self):
        """快速录单 - 简化流程"""
        print("\n" + "="*50)
        print("📋 快速录单")
        print("="*50)
        
        # 显示客户列表
        if not self.data['customers']:
            print("暂无客户，请先添加客户")
            return None
        
        print("\n客户列表:")
        for i, c in enumerate(self.data['customers'], 1):
            print(f"  {i}. {c['name']}")
        
        try:
            # 选择客户
            idx = int(input("\n选择客户: ")) - 1
            if idx < 0 or idx >= len(self.data['customers']):
                print("无效选择")
                return None
            
            customer = self.data['customers'][idx]
            
            # 产品名称
            item_name = input("产品名称: ")
            if not item_name:
                return None
            
            # 数量
            quantity = float(input("数量: "))
            
            # 计价方式
            print("\n计价方式: 1.件  2.条  3.米  4.公斤  5.平方米")
            unit_choice = input("选择 [1-5]: ")
            unit_map = {"1": "件", "2": "条", "3": "米", "4": "公斤", "5": "平方米"}
            unit = unit_map.get(unit_choice, "件")
            
            # 单价
            unit_price = input(f"单价(元/{unit}): ")
            if not unit_price:
                return None
            unit_price = float(unit_price)
            
            # 委外工序
            print("\n委外工序(可选): 1.喷砂  2.拉丝  3.抛光  4.氧化(必选)")
            processes = ["氧化"]  # 氧化是必选的
            
            process_input = input("选择工序(空格分隔，如: 1 2): ")
            if process_input:
                process_map = {"1": "喷砂", "2": "拉丝", "3": "抛光"}
                for p in process_input.split():
                    if p in process_map and process_map[p] not in processes:
                        processes.append(process_map[p])
            
            # 添加订单
            order = self.add_order(customer['id'], item_name, quantity, unit_price, unit, processes)
            total = quantity * unit_price
            print(f"\n✅ 订单添加成功！")
            print(f"   客户: {customer['name']}")
            print(f"   产品: {item_name} {quantity}{unit} × ¥{unit_price}")
            print(f"   金额: ¥{total}")
            print(f"   工序: {' → '.join(processes)}")
            return True
            
        except (ValueError, IndexError):
            print("输入错误")
            return None
    
    # ========== 实用报表 ==========
    
    def show_daily_report(self):
        """今日收支报表"""
        print("\n" + "="*50)
        print("📊 今日收支报表")
        print(f"   日期: {date.today()}")
        print("="*50)
        
        today = str(date.today())
        
        # 今日收入
        today_income = [i for i in self.data['income'] if i.get('date', '').startswith(today[:7]) or i.get('date', '') == today]
        total_income = sum(Decimal(i['amount']) for i in today_income)
        
        # 今日支出
        today_expense = [e for e in self.data['expenses'] if e.get('date', '').startswith(today[:7]) or e.get('date', '') == today]
        total_expense = sum(Decimal(e['amount']) for e in today_expense)
        
        print(f"\n💰 今日收入: ¥{total_income:,.2f}")
        for inc in today_income:
            customer_name = "未知"
            for c in self.data['customers']:
                if c['id'] == inc.get('customer_id', ''):
                    customer_name = c['name']
                    break
            print(f"   - {customer_name}: ¥{inc['amount']} ({inc.get('bank_type', '')}) {inc.get('description', '')}")
        
        print(f"\n💸 今日支出: ¥{total_expense:,.2f}")
        for exp in today_expense:
            print(f"   - {exp['type']}: ¥{exp['amount']} {exp.get('description', '')}")
        
        profit = total_income - total_expense
        print(f"\n📈 今日利润: ¥{profit:,.2f}")
        
    def show_monthly_report(self):
        """本月统计报表"""
        print("\n" + "="*50)
        print("📊 本月统计报表")
        this_month = date.today().strftime("%Y-%m")
        print(f"   月份: {this_month}")
        print("="*50)
        
        # 本月收入
        month_income = [i for i in self.data['income'] if i.get('date', '').startswith(this_month)]
        total_income = sum(Decimal(i['amount']) for i in month_income)
        
        # 本月支出
        month_expense = [e for e in self.data['expenses'] if e.get('date', '').startswith(this_month)]
        total_expense = sum(Decimal(e['amount']) for e in month_expense)
        
        # 按银行分类收入
        g_income = sum(Decimal(i['amount']) for i in month_income if i.get('bank_type') == 'G银行')
        n_income = sum(Decimal(i['amount']) for i in month_income if i.get('bank_type') == 'N银行')
        wx_income = sum(Decimal(i['amount']) for i in month_income if i.get('bank_type') == '微信')
        
        # 按类型分类支出
        expense_by_type = {}
        for e in month_expense:
            t = e['type']
            expense_by_type[t] = expense_by_type.get(t, 0) + Decimal(e['amount'])
        
        print(f"\n💰 本月收入合计: ¥{total_income:,.2f}")
        print(f"   G银行(有票): ¥{g_income:,.2f}")
        print(f"   N银行(现金): ¥{n_income:,.2f}")
        print(f"   微信: ¥{wx_income:,.2f}")
        
        print(f"\n💸 本月支出合计: ¥{total_expense:,.2f}")
        for etype, amount in sorted(expense_by_type.items(), key=lambda x: -x[1]):
            print(f"   - {etype}: ¥{amount:,.2f}")
        
        profit = total_income - total_expense
        print(f"\n📈 本月利润: ¥{profit:,.2f}")
        print(f"   利润率: {(profit/total_income*100):.1f}%" if total_income > 0 else "   (无收入)")
        
    def show_customer_summary(self):
        """客户往来汇总"""
        print("\n" + "="*50)
        print("👥 客户往来汇总")
        print("="*50)
        
        for customer in self.data['customers']:
            # 该客户的订单总额
            customer_orders = [o for o in self.data['orders'] if o['customer_id'] == customer['id']]
            total_orders = sum(Decimal(o['amount']) for o in customer_orders)
            
            # 该客户的已收款
            customer_income = [i for i in self.data['income'] if i['customer_id'] == customer['id']]
            total_received = sum(Decimal(i['amount']) for i in customer_income)
            
            # 应收款
            receivable = total_orders - total_received
            
            print(f"\n{customer['name']}")
            print(f"   订单总额: ¥{total_orders:,.2f}")
            print(f"   已收款项: ¥{total_received:,.2f}")
            print(f"   应收余额: ¥{receivable:,.2f}")
    
    def get_financial_summary(self):
        """财务摘要"""
        total_income = sum(Decimal(item['amount']) for item in self.data['income'])
        total_expenses = sum(Decimal(item['amount']) for item in self.data['expenses'])
        profit = total_income - total_expenses
        
        return {
            "总收入": f"¥{total_income:,.2f}",
            "总支出": f"¥{total_expenses:,.2f}",
            "利润": f"¥{profit:,.2f}",
            "客户数": len(self.data['customers']),
            "订单数": len(self.data['orders']),
            "收入记录": len(self.data['income']),
            "支出记录": len(self.data['expenses'])
        }
    
    def show_summary(self):
        """显示财务概况"""
        summary = self.get_financial_summary()
        
        print("\n" + "="*50)
        print("📊 财务概况")
        print("="*50)
        for key, value in summary.items():
            print(f"  {key}: {value}")


def main():
    """主函数"""
    print("\n" + "="*60)
    print("🏭 氧化加工厂财务助手 - 实用版")
    print("   提高小会计工作效率，专为国内小型工厂优化")
    print("="*60)
    
    helper = PracticalFinanceHelper()
    
    while True:
        print("\n" + "-"*50)
        print("📋 主菜单 - 选择功能")
        print("-"*50)
        print("  【快捷操作】")
        print("    1. 快速收款    - 减少步骤，快速记录客户付款")
        print("    2. 快速付款    - 减少步骤，快速记录支出")
        print("    3. 快速录单    - 减少步骤，快速录入加工订单")
        print()
        print("  【日常管理】")
        print("    4. 查看财务概况   - 总收入/支出/利润")
        print("    5. 今日收支报表   - 今日收支明细")
        print("    6. 本月统计报表   - 本月收支汇总")
        print("    7. 客户往来汇总   - 各客户应收应付")
        print("    8. 添加客户      - 新增客户档案")
        print()
        print("  【其他】")
        print("    9. 生成学习数据  - 创建示例数据")
        print("    0. 退出系统")
        print("-"*50)
        
        choice = input("请选择 [0-9]: ").strip()
        
        if choice == "1":
            helper.quick_add_income()
        elif choice == "2":
            helper.quick_add_expense()
        elif choice == "3":
            helper.quick_add_order()
        elif choice == "4":
            helper.show_summary()
        elif choice == "5":
            helper.show_daily_report()
        elif choice == "6":
            helper.show_monthly_report()
        elif choice == "7":
            helper.show_customer_summary()
        elif choice == "8":
            name = input("客户名称: ")
            contact = input("联系人: ")
            phone = input("联系电话: ")
            helper.add_customer(name, contact, phone)
            print(f"✅ 客户添加成功: {name}")
        elif choice == "9":
            # 生成学习数据
            helper.add_customer("优质客户有限公司", "张经理", "13800138001")
            helper.add_customer("新兴科技公司", "李总", "13900139002")
            helper.add_customer("长期合作伙伴", "王主任", "13700137003")
            
            helper.add_order("C001", "铝合金把手", 500, 2.5, "件", ["氧化"])
            helper.add_order("C001", "不锈钢螺丝", 1000, 0.8, "件", ["氧化"])
            helper.add_order("C002", "铜管", 200, 15.0, "条", ["氧化"])
            helper.add_order("C002", "铝型材", 150, 12.0, "米", ["拉丝", "氧化"])
            helper.add_order("C003", "铁质零件", 300, 8.0, "公斤", ["氧化"])
            
            helper.add_income("C001", 2500, "G银行", "铝合金把手加工费")
            helper.add_income("C001", 1200, "N银行", "部分款项")
            helper.add_income("C002", 1800, "微信", "铜管加工费")
            
            for etype, amount in [("房租", 8000), ("水电费", 2500), ("三酸", 3200), 
                                  ("片碱", 1800), ("工资", 15000), ("外发加工费", 2800)]:
                helper.add_expense(etype, amount, etype)
            
            print("✅ 学习数据生成完成！包含：")
            print("   - 3个典型客户")
            print("   - 5个示例订单（涵盖各种计价方式）")
            print("   - 3笔收入记录（G银行/N银行/微信）")
            print("   - 6类支出记录（房租/水电/化工原料/工资/外发）")
        elif choice == "0":
            print("\n👋 感谢使用！祝工作顺利！")
            break
        else:
            print("无效选择，请重试")


if __name__ == "__main__":
    main()
