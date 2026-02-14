#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
氧化加工厂财务助手 V2.0 - 小白专用版
专为技术小白设计的一键式财务管理系统
"""

import sys
import os
import json
from datetime import datetime, date
from decimal import Decimal
import sqlite3

# 添加项目路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'oxidation_finance_v20'))

try:
    from database.db_manager import DatabaseManager
    from reports.report_manager import ReportManager
    HAS_FULL_SYSTEM = True
except ImportError as e:
    print(f"⚠️  完整系统导入失败: {e}")
    HAS_FULL_SYSTEM = False

class SimpleFinanceManager:
    """简化版财务管理器 - 专为小白设计"""
    
    def __init__(self):
        self.data_file = "simple_finance_data.json"
        self.load_data()
        
    def load_data(self):
        """加载数据"""
        if os.path.exists(self.data_file):
            with open(self.data_file, 'r', encoding='utf-8') as f:
                self.data = json.load(f)
        else:
            self.data = {
                "customers": [],
                "orders": [],
                "income": [],
                "expenses": [],
                "bank_transactions": [],
                "suppliers": []
            }
            
    def save_data(self):
        """保存数据"""
        with open(self.data_file, 'w', encoding='utf-8') as f:
            json.dump(self.data, f, ensure_ascii=False, indent=2, default=str)
            
    def add_customer(self, name, contact="", phone=""):
        """添加客户"""
        customer = {
            "id": f"C{len(self.data['customers']) + 1:03d}",
            "name": name,
            "contact": contact,
            "phone": phone,
            "created_at": str(datetime.now())
        }
        self.data['customers'].append(customer)
        self.save_data()
        return customer
        
    def add_order(self, customer_id, item_name, quantity, unit_price, pricing_unit, 
                  outsourcing_processes=None):
        """添加订单"""
        # 计算金额
        amount = Decimal(str(quantity)) * Decimal(str(unit_price))
        
        order = {
            "id": f"O{len(self.data['orders']) + 1:04d}",
            "customer_id": customer_id,
            "item_name": item_name,
            "quantity": quantity,
            "unit_price": str(unit_price),
            "pricing_unit": pricing_unit,
            "amount": str(amount),
            "outsourcing_processes": outsourcing_processes or [],
            "status": "待加工",
            "created_at": str(datetime.now())
        }
        self.data['orders'].append(order)
        self.save_data()
        return order
        
    def add_income(self, customer_id, amount, bank_type="G银行", description=""):
        """添加收入"""
        income = {
            "id": f"I{len(self.data['income']) + 1:04d}",
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
        expense = {
            "id": f"E{len(self.data['expenses']) + 1:04d}",
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
        
    def get_financial_summary(self):
        """获取财务摘要"""
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

def create_sample_data():
    """创建模拟数据"""
    fm = SimpleFinanceManager()
    
    # 添加客户
    customers = [
        ("优质客户有限公司", "张经理", "13800138001"),
        ("新兴科技股份有限公司", "李总", "13900139002"),
        ("长期合作伙伴公司", "王主任", "13700137003"),
        ("诚信贸易公司", "陈经理", "13600136004"),
        ("实力制造企业", "刘总", "13500135005"),
        ("可靠供应商集团", "赵主任", "13400134006")
    ]
    
    customer_ids = []
    for name, contact, phone in customers:
        customer = fm.add_customer(name, contact, phone)
        customer_ids.append(customer['id'])
        print(f"✅ 添加客户: {name}")
    
    # 添加订单（包含各种计价方式）
    orders_data = [
        # 按件计价
        (customer_ids[0], "铝合金把手", 500, 2.5, "件", ["氧化"]),
        (customer_ids[1], "不锈钢螺丝", 1000, 0.8, "件", ["氧化"]),
        
        # 按条计价
        (customer_ids[2], "铜管", 200, 15.0, "条", ["氧化"]),
        
        # 按米计价
        (customer_ids[0], "铝型材", 150, 12.0, "米", ["拉丝", "氧化"]),
        (customer_ids[3], "不锈钢管", 80, 25.0, "米", ["喷砂", "氧化"]),
        
        # 按公斤计价
        (customer_ids[1], "铁质零件", 300, 8.0, "公斤", ["氧化"]),
        (customer_ids[4], "铜质配件", 150, 28.0, "公斤", ["抛光", "氧化"]),
        
        # 按平方米计价
        (customer_ids[2], "铝板", 50, 45.0, "平方米", ["氧化"]),
        (customer_ids[5], "不锈钢板", 30, 68.0, "平方米", ["拉丝", "氧化"]),
        
        # 委外加工订单
        (customer_ids[3], "精密零件", 200, 18.0, "件", ["喷砂", "拉丝", "氧化"]),
        (customer_ids[4], "装饰件", 500, 3.2, "件", ["抛光", "氧化"])
    ]
    
    for customer_id, item, qty, price, unit, processes in orders_data:
        order = fm.add_order(customer_id, item, qty, price, unit, processes)
        print(f"✅ 添加订单: {item} ({qty}{unit}) - ¥{float(qty)*float(price):.2f}")
    
    # 添加收入记录
    income_data = [
        (customer_ids[0], 2500, "G银行", "铝合金把手加工费"),
        (customer_ids[1], 1800, "G银行", "不锈钢螺丝加工费"),
        (customer_ids[2], 3000, "N银行", "铜管加工费"),
        (customer_ids[0], 1200, "N银行", "部分款项"),
        (customer_ids[3], 2800, "G银行", "不锈钢管加工费"),
        (customer_ids[1], 1500, "N银行", "铁质零件加工费")
    ]
    
    for customer_id, amount, bank, desc in income_data:
        income = fm.add_income(customer_id, amount, bank, desc)
        print(f"✅ 记录收入: {desc} - ¥{amount}")
    
    # 添加支出记录
    expense_data = [
        ("房租", 8000, "厂房租金", ""),
        ("水电费", 2500, "本月水电费", ""),
        ("三酸", 3200, "硫酸、盐酸、硝酸", "化工供应商"),
        ("片碱", 1800, "氢氧化钠", "化工供应商"),
        ("亚钠", 1200, "亚硝酸钠", "化工供应商"),
        ("色粉", 800, "各种颜色粉末", "颜料供应商"),
        ("除油剂", 600, "金属表面处理剂", "表面处理供应商"),
        ("挂具", 1500, "电镀挂具", "设备供应商"),
        ("外发加工费", 2800, "喷砂拉丝费用", "外协加工厂"),
        ("日常费用", 1200, "办公用品等", ""),
        ("工资", 15000, "员工工资", ""),
        ("其他", 500, "杂项支出", "")
    ]
    
    for exp_type, amount, desc, supplier in expense_data:
        expense = fm.add_expense(exp_type, amount, desc, supplier)
        print(f"✅ 记录支出: {exp_type} - ¥{amount}")
    
    return fm

def show_menu():
    """显示菜单"""
    print("\n" + "="*60)
    print("🏭 氧化加工厂财务助手 V2.0 - 小白专用版")
    print("="*60)
    print("📋 主要功能:")
    print("  1. 查看财务概况")
    print("  2. 添加客户")
    print("  3. 添加订单")
    print("  4. 记录收入")
    print("  5. 记录支出")
    print("  6. 生成模拟数据")
    print("  7. 查看所有数据")
    print("  0. 退出系统")
    print("="*60)

def main():
    """主程序"""
    print("🚀 欢迎使用氧化加工厂财务助手！")
    
    # 检查是否有完整系统
    if HAS_FULL_SYSTEM:
        print("✅ 检测到完整系统，功能更强大")
    else:
        print("ℹ️  使用简化版本，满足基本需求")
    
    fm = SimpleFinanceManager()
    
    while True:
        show_menu()
        try:
            choice = input("\n请选择功能 (0-7): ").strip()
            
            if choice == "0":
                print("👋 感谢使用，再见！")
                break
                
            elif choice == "1":
                summary = fm.get_financial_summary()
                print("\n📊 财务概况:")
                print("-" * 30)
                for key, value in summary.items():
                    print(f"{key:8}: {value}")
                    
            elif choice == "2":
                name = input("客户名称: ")
                contact = input("联系人(可选): ")
                phone = input("电话(可选): ")
                customer = fm.add_customer(name, contact, phone)
                print(f"✅ 客户添加成功: {customer['id']} - {name}")
                
            elif choice == "3":
                print("计价方式: 件/条/只/个/米/公斤/平方米")
                customer_id = input("客户ID: ")
                item_name = input("物品名称: ")
                quantity = float(input("数量: "))
                unit_price = float(input("单价: "))
                pricing_unit = input("计价单位: ")
                order = fm.add_order(customer_id, item_name, quantity, unit_price, pricing_unit)
                print(f"✅ 订单添加成功: {order['id']}")
                
            elif choice == "4":
                customer_id = input("客户ID: ")
                amount = float(input("金额: "))
                bank_type = input("银行(G银行/N银行): ") or "G银行"
                description = input("说明: ")
                income = fm.add_income(customer_id, amount, bank_type, description)
                print(f"✅ 收入记录成功: {income['id']}")
                
            elif choice == "5":
                print("支出类型: 房租/水电费/三酸/片碱/亚钠/色粉/除油剂/挂具/外发加工费/日常费用/工资/其他")
                exp_type = input("支出类型: ")
                amount = float(input("金额: "))
                description = input("说明: ")
                supplier = input("供应商(可选): ")
                expense = fm.add_expense(exp_type, amount, description, supplier)
                print(f"✅ 支出记录成功: {expense['id']}")
                
            elif choice == "6":
                print("🔄 正在生成模拟数据...")
                create_sample_data()
                print("✅ 模拟数据生成完成！")
                
            elif choice == "7":
                print("\n📂 当前数据:")
                print(f"客户: {len(fm.data['customers'])} 个")
                print(f"订单: {len(fm.data['orders'])} 个")
                print(f"收入: {len(fm.data['income'])} 笔")
                print(f"支出: {len(fm.data['expenses'])} 笔")
                
                # 显示最近几条记录
                print("\n最近订单:")
                for order in fm.data['orders'][-3:]:
                    print(f"  {order['id']}: {order['item_name']} - {order['quantity']}{order['pricing_unit']}")
                    
            else:
                print("❌ 无效选择，请重新输入")
                
        except KeyboardInterrupt:
            print("\n\n👋 程序已退出")
            break
        except Exception as e:
            print(f"❌ 操作出错: {e}")

if __name__ == "__main__":
    main()