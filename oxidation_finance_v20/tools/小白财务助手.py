#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
氧化加工厂财务助手 - 小白专用版
在原有系统基础上优化，专为技术小白设计的一键式操作界面

功能特色：
1. 简化操作流程，菜单式交互
2. 支持氧化加工行业特殊需求
3. 自动处理复杂的财务计算
4. 提供学习模式和示例数据
"""

import os
import sys
import json
from datetime import datetime, date
from decimal import Decimal
import sqlite3

# 在原有系统基础上导入核心模块
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

try:
    from database.db_manager import DatabaseManager
    from utils.config import get_db_path
    HAS_FULL_SYSTEM = True
    print("✅ 检测到完整系统，功能更强大")
except ImportError as e:
    HAS_FULL_SYSTEM = False
    print(f"⚠️  完整系统导入失败: {e}")
    print("ℹ️  使用简化版本，满足基本需求")

class SimpleFinanceHelper:
    """简化版财务助手 - 专为小白设计"""
    
    def __init__(self):
        self.data_file = os.path.join(project_root, "simple_finance_data.json")
        self.db_path = get_db_path() if HAS_FULL_SYSTEM else None
        self.db_manager = None
        
        # 如果有完整系统，初始化数据库连接
        if HAS_FULL_SYSTEM and self.db_path and os.path.exists(self.db_path):
            try:
                self.db_manager = DatabaseManager(self.db_path)
                print("✅ 数据库连接成功")
            except Exception as e:
                print(f"⚠️  数据库连接失败: {e}")
        
        self.load_data()
        
    def load_data(self):
        """加载数据"""
        if os.path.exists(self.data_file):
            try:
                with open(self.data_file, 'r', encoding='utf-8') as f:
                    self.data = json.load(f)
            except Exception as e:
                print(f"⚠️  数据加载失败: {e}")
                self.init_empty_data()
        else:
            self.init_empty_data()
            
    def init_empty_data(self):
        """初始化空数据结构"""
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
            print(f"❌ 数据保存失败: {e}")
            return False
            
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
        
    def add_order(self, customer_id, item_name, quantity, unit_price, pricing_unit, 
                  outsourcing_processes=None):
        """添加订单（支持多种计价方式）"""
        try:
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
                "outsourcing_processes": outsourcing_processes or [],
                "status": "待加工",
                "created_at": str(datetime.now())
            }
            self.data['orders'].append(order)
            self.save_data()
            return order
        except Exception as e:
            print(f"❌ 订单添加失败: {e}")
            return None
            
    def add_income(self, customer_id, amount, bank_type="G银行", description=""):
        """添加收入记录"""
        try:
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
        except Exception as e:
            print(f"❌ 收入记录失败: {e}")
            return None
            
    def add_expense(self, expense_type, amount, description="", supplier=""):
        """添加支出记录"""
        try:
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
        except Exception as e:
            print(f"❌ 支出记录失败: {e}")
            return None
            
    def get_financial_summary(self):
        """获取财务摘要"""
        try:
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
                "支出记录": len(self.data['expenses']),
                "最后更新": self.data.get('last_updated', '未知')
            }
        except Exception as e:
            print(f"❌ 财务统计失败: {e}")
            return {"错误": str(e)}

def create_sample_data(helper):
    """创建氧化加工厂的模拟数据（优先使用完整演示数据）"""
    print("\n🔄 正在生成氧化加工厂模拟数据...")
    
    # 检查是否有完整的演示数据
    complete_demo_file = os.path.join(project_root, "complete_oxidation_factory_demo_data.json")
    if os.path.exists(complete_demo_file):
        print("发现完整演示数据，正在加载...")
        try:
            with open(complete_demo_file, 'r', encoding='utf-8') as f:
                complete_data = json.load(f)
            
            # 合并数据
            helper.data.update(complete_data)
            helper.data['last_updated'] = str(datetime.now())
            helper.save_data()
            print("✅ 完整演示数据加载成功！")
            print("包含：8个客户、20个订单、15笔收入、12笔支出")
            return True
        except Exception as e:
            print(f"⚠️  完整数据加载失败: {e}")
    
    # 如果没有完整数据，则生成基础模拟数据
    print("生成基础模拟数据...")
    
    # 添加典型客户
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
        customer = helper.add_customer(name, contact, phone)
        customer_ids.append(customer['id'])
        print(f"✅ 添加客户: {name}")
    
    # 添加不同计价方式的订单
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
        order = helper.add_order(customer_id, item, qty, price, unit, processes)
        if order:
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
        income = helper.add_income(customer_id, amount, bank, desc)
        if income:
            print(f"✅ 记录收入: {desc} - ¥{amount}")
    
    # 添加支出记录（氧化加工厂典型支出）
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
        expense = helper.add_expense(exp_type, amount, desc, supplier)
        if expense:
            print(f"✅ 记录支出: {exp_type} - ¥{amount}")
    
    print("\n🎉 模拟数据生成完成！")
    return True

def show_main_menu():
    """显示主菜单"""
    print("\n" + "="*60)
    print("🏭 氧化加工厂财务助手 V2.0 - 小白专用版")
    print("="*60)
    if HAS_FULL_SYSTEM:
        print("✅ 检测到完整系统，功能更强大")
    else:
        print("ℹ️  使用简化版本，满足基本需求")
    print("\n📋 主要功能:")
    print("  1. 查看财务概况")
    print("  2. 添加客户信息")
    print("  3. 录入加工订单")
    print("  4. 记录客户收入")
    print("  5. 登记费用支出")
    print("  6. 生成学习数据")
    print("  7. 查看详细数据")
    print("  8. 启动Web界面")
    print("  0. 退出系统")
    print("="*60)

def main():
    """主程序"""
    print("🚀 欢迎使用氧化加工厂财务助手！")
    print("💡 专为技术小白设计，操作简单直观")
    
    helper = SimpleFinanceHelper()
    
    while True:
        show_main_menu()
        try:
            choice = input("\n请选择功能 (0-8): ").strip()
            
            if choice == "0":
                print("\n👋 感谢使用，再见！")
                break
                
            elif choice == "1":
                summary = helper.get_financial_summary()
                print("\n📊 财务概况:")
                print("-" * 40)
                for key, value in summary.items():
                    print(f"{key:10}: {value}")
                    
            elif choice == "2":
                print("\n📝 添加客户信息")
                name = input("客户名称: ").strip()
                if not name:
                    print("❌ 客户名称不能为空")
                    continue
                contact = input("联系人(可选): ").strip()
                phone = input("电话(可选): ").strip()
                customer = helper.add_customer(name, contact, phone)
                print(f"✅ 客户添加成功: {customer['id']} - {name}")
                
            elif choice == "3":
                print("\n📋 录入加工订单")
                print("支持计价方式: 件/条/只/个/米/公斤/平方米")
                
                # 显示现有客户
                if helper.data['customers']:
                    print("\n现有客户:")
                    for customer in helper.data['customers'][-5:]:  # 显示最近5个
                        print(f"  {customer['id']}: {customer['name']}")
                
                customer_id = input("客户ID: ").strip()
                if not customer_id:
                    print("❌ 客户ID不能为空")
                    continue
                    
                item_name = input("物品名称: ").strip()
                if not item_name:
                    print("❌ 物品名称不能为空")
                    continue
                    
                try:
                    quantity = float(input("数量: "))
                    unit_price = float(input("单价: "))
                except ValueError:
                    print("❌ 数量和单价必须是数字")
                    continue
                    
                pricing_unit = input("计价单位(件/条/米/公斤/平方米等): ").strip()
                if not pricing_unit:
                    print("❌ 计价单位不能为空")
                    continue
                
                # 委外工序
                print("委外工序(喷砂/拉丝/抛光，多个用逗号分隔，可留空):")
                outsourcing = input("委外工序: ").strip()
                processes = [p.strip() for p in outsourcing.split(",") if p.strip()] if outsourcing else ["氧化"]
                
                order = helper.add_order(customer_id, item_name, quantity, unit_price, pricing_unit, processes)
                if order:
                    print(f"✅ 订单添加成功: {order['id']}")
                    print(f"   金额: ¥{float(quantity)*float(unit_price):.2f}")
                    print(f"   工序: {' → '.join(processes)}")
                
            elif choice == "4":
                print("\n💰 记录客户收入")
                if helper.data['customers']:
                    print("现有客户:")
                    for customer in helper.data['customers'][-3:]:
                        print(f"  {customer['id']}: {customer['name']}")
                
                customer_id = input("客户ID: ").strip()
                if not customer_id:
                    print("❌ 客户ID不能为空")
                    continue
                    
                try:
                    amount = float(input("金额: "))
                except ValueError:
                    print("❌ 金额必须是数字")
                    continue
                    
                print("银行类型: G银行(有票) / N银行(现金/微信)")
                bank_type = input("银行类型(G/N): ").strip().upper() or "G"
                bank_type = "G银行" if bank_type == "G" else "N银行"
                
                description = input("说明(可选): ").strip()
                
                income = helper.add_income(customer_id, amount, bank_type, description)
                if income:
                    print(f"✅ 收入记录成功: {income['id']} - ¥{amount}")
                    
            elif choice == "5":
                print("\n💸 登记费用支出")
                expense_types = ["房租", "水电费", "三酸", "片碱", "亚钠", "色粉", 
                               "除油剂", "挂具", "外发加工费", "日常费用", "工资", "其他"]
                print("支出类型:", " / ".join(expense_types))
                
                exp_type = input("支出类型: ").strip()
                if not exp_type:
                    print("❌ 支出类型不能为空")
                    continue
                    
                try:
                    amount = float(input("金额: "))
                except ValueError:
                    print("❌ 金额必须是数字")
                    continue
                    
                description = input("说明(可选): ").strip()
                supplier = input("供应商(可选): ").strip()
                
                expense = helper.add_expense(exp_type, amount, description, supplier)
                if expense:
                    print(f"✅ 支出记录成功: {expense['id']} - ¥{amount}")
                    
            elif choice == "6":
                print("\n🎯 生成学习用的模拟数据")
                print("将创建氧化加工厂的完整示例数据:")
                print("• 6个典型客户")
                print("• 10个不同计价方式的订单")
                print("• 6笔收入记录") 
                print("• 12类支出项目")
                
                confirm = input("\n确认生成？(y/N): ").strip().lower()
                if confirm == 'y':
                    if create_sample_data(helper):
                        print("\n✅ 模拟数据已生成，您可以:")
                        print("   • 查看财务概况了解整体情况")
                        print("   • 浏览订单数据学习录入方式")
                        print("   • 修改删除数据进行练习")
                else:
                    print("❌ 取消生成")
                    
            elif choice == "7":
                print("\n📂 详细数据查看")
                print(f"客户数量: {len(helper.data['customers'])}")
                print(f"订单数量: {len(helper.data['orders'])}")
                print(f"收入记录: {len(helper.data['income'])}")
                print(f"支出记录: {len(helper.data['expenses'])}")
                
                if helper.data['orders']:
                    print("\n最近订单:")
                    for order in helper.data['orders'][-3:]:
                        print(f"  {order['id']}: {order['item_name']} "
                              f"({order['quantity']}{order['pricing_unit']}) "
                              f"- ¥{float(order['amount']):.2f}")
                
                if helper.data['income']:
                    print("\n最近收入:")
                    for income in helper.data['income'][-3:]:
                        print(f"  {income['id']}: {income['description']} "
                              f"- ¥{float(income['amount'])} ({income['bank_type']})")
                              
            elif choice == "8":
                print("\n🌐 启动Web界面")
                if HAS_FULL_SYSTEM:
                    try:
                        print("正在启动Web服务...")
                        print("请在浏览器中访问: http://localhost:5000")
                        print("按 Ctrl+C 停止服务")
                        
                        # 启动Web应用
                        web_app_path = os.path.join(project_root, "web_app.py")
                        if os.path.exists(web_app_path):
                            os.system(f"python \"{web_app_path}\"")
                        else:
                            print("❌ 未找到web_app.py文件")
                    except KeyboardInterrupt:
                        print("\n⏹️  Web服务已停止")
                    except Exception as e:
                        print(f"❌ 启动失败: {e}")
                else:
                    print("❌ 完整系统不可用，无法启动Web界面")
                    print("💡 建议使用菜单式操作或生成模拟数据学习")
                    
            else:
                print("❌ 无效选择，请输入 0-8 之间的数字")
                
        except KeyboardInterrupt:
            print("\n\n👋 程序已退出")
            break
        except Exception as e:
            print(f"\n❌ 操作出错: {e}")
            print("💡 请重新选择功能")

if __name__ == "__main__":
    main()