#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
CWZS系统完整功能演示数据生成器
为小型氧化加工厂创建真实的业务场景模拟数据
"""

import json
import os
import random
from datetime import datetime, timedelta
from decimal import Decimal

def generate_complete_demo_data():
    """生成完整的氧化加工厂模拟数据"""
    
    print("🏭 正在生成氧化加工厂完整模拟数据...")
    print("="*50)
    
    # 基础数据结构
    data = {
        "customers": [],
        "orders": [],
        "income": [],
        "expenses": [],
        "bank_transactions": [],
        "suppliers": [],
        "outsourcing_records": [],
        "settings": {
            "company_name": "诚信氧化加工厂",
            "business_type": "五金氧化加工",
            "created_at": str(datetime.now())
        },
        "last_updated": str(datetime.now())
    }
    
    # 1. 生成典型客户数据 (8个)
    print("\n👥 生成客户数据...")
    customers = [
        {
            "id": "C001",
            "name": "优质客户有限公司",
            "contact": "张经理",
            "phone": "13800138001",
            "credit_limit": "50000",
            "payment_terms": "月结30天"
        },
        {
            "id": "C002", 
            "name": "新兴科技股份有限公司",
            "contact": "李总",
            "phone": "13900139002",
            "credit_limit": "30000",
            "payment_terms": "月结60天"
        },
        {
            "id": "C003",
            "name": "长期合作伙伴公司",
            "contact": "王主任",
            "phone": "13700137003", 
            "credit_limit": "80000",
            "payment_terms": "预付款50%"
        },
        {
            "id": "C004",
            "name": "诚信贸易公司",
            "contact": "陈经理",
            "phone": "13600136004",
            "credit_limit": "20000",
            "payment_terms": "货到付款"
        },
        {
            "id": "C005",
            "name": "实力制造企业",
            "contact": "刘总",
            "phone": "13500135005",
            "credit_limit": "100000",
            "payment_terms": "月结90天"
        },
        {
            "id": "C006",
            "name": "可靠供应商集团",
            "contact": "赵主任",
            "phone": "13400134006",
            "credit_limit": "60000",
            "payment_terms": "季度结算"
        },
        {
            "id": "C007",
            "name": "精密零件厂",
            "contact": "孙厂长",
            "phone": "13300133007",
            "credit_limit": "40000",
            "payment_terms": "月结45天"
        },
        {
            "id": "C008",
            "name": "五金制品公司",
            "contact": "周经理",
            "phone": "13200132008",
            "credit_limit": "25000",
            "payment_terms": "预付款30%"
        }
    ]
    
    for customer in customers:
        data["customers"].append(customer)
        print(f"✅ {customer['name']} - {customer['contact']}")
    
    # 2. 生成多样化订单数据 (20个)
    print("\n📋 生成订单数据...")
    order_templates = [
        # 按件计价
        ("铝合金把手", 500, 2.5, "件", ["氧化"]),
        ("不锈钢螺丝", 1000, 0.8, "件", ["氧化"]),
        ("铜质连接器", 300, 5.2, "件", ["抛光", "氧化"]),
        ("铁质支架", 200, 8.6, "件", ["喷砂", "氧化"]),
        
        # 按条计价
        ("铜管", 200, 15.0, "条", ["氧化"]),
        ("铝型材", 150, 12.0, "条", ["拉丝", "氧化"]),
        
        # 按米计价
        ("不锈钢管", 80, 25.0, "米", ["喷砂", "氧化"]),
        ("铝型材", 120, 18.5, "米", ["拉丝", "氧化"]),
        ("铜线", 500, 3.2, "米", ["氧化"]),
        
        # 按公斤计价
        ("铁质零件", 300, 8.0, "公斤", ["氧化"]),
        ("铜质配件", 150, 28.0, "公斤", ["抛光", "氧化"]),
        ("铝合金废料", 200, 12.5, "公斤", ["氧化"]),
        
        # 按平方米计价
        ("铝板", 50, 45.0, "平方米", ["氧化"]),
        ("不锈钢板", 30, 68.0, "平方米", ["拉丝", "氧化"]),
        ("铜板", 25, 85.0, "平方米", ["抛光", "氧化"]),
        
        # 复杂委外订单
        ("精密零件", 200, 18.0, "件", ["喷砂", "拉丝", "氧化"]),
        ("装饰配件", 150, 12.8, "件", ["抛光", "氧化"]),
        ("工业零件", 80, 35.0, "公斤", ["喷砂", "氧化"]),
        ("建筑型材", 60, 42.0, "米", ["拉丝", "氧化"]),
        ("电子元件", 500, 3.6, "件", ["氧化"])
    ]
    
    for i, (item, qty, price, unit, processes) in enumerate(order_templates, 1):
        amount = Decimal(str(qty)) * Decimal(str(price))
        order_date = datetime.now() - timedelta(days=random.randint(1, 60))
        
        order = {
            "id": f"O{i:04d}",
            "customer_id": f"C{random.randint(1, 8):03d}",
            "item_name": item,
            "quantity": float(qty),
            "unit_price": str(price),
            "pricing_unit": unit,
            "amount": str(amount),
            "outsourcing_processes": processes,
            "status": random.choice(["待加工", "加工中", "已完工", "已交付"]),
            "order_date": str(order_date.date()),
            "delivery_date": str((order_date + timedelta(days=random.randint(3, 15))).date()) if random.random() > 0.3 else None,
            "created_at": str(datetime.now())
        }
        data["orders"].append(order)
        print(f"✅ 订单{i:02d}: {item} ({qty}{unit}) - ¥{amount:.2f} - {','.join(processes)}")
    
    # 3. 生成收入记录 (15笔)
    print("\n💰 生成收入数据...")
    income_sources = [
        ("优质客户有限公司", 2500, "G银行", "铝合金把手加工费"),
        ("新兴科技股份有限公司", 1800, "G银行", "不锈钢螺丝加工费"),
        ("长期合作伙伴公司", 3000, "N银行", "铜管加工费"),
        ("优质客户有限公司", 1200, "微信", "部分款项"),
        ("诚信贸易公司", 2800, "G银行", "不锈钢管加工费"),
        ("新兴科技股份有限公司", 1500, "N银行", "铁质零件加工费"),
        ("实力制造企业", 4200, "G银行", "铝板加工费"),
        ("可靠供应商集团", 1800, "微信", "铜质配件加工费"),
        ("精密零件厂", 3200, "G银行", "精密零件加工费"),
        ("五金制品公司", 900, "N银行", "装饰配件加工费"),
        ("长期合作伙伴公司", 2100, "G银行", "工业零件加工费"),
        ("诚信贸易公司", 1600, "微信", "建筑型材加工费"),
        ("实力制造企业", 800, "N银行", "部分付款"),
        ("可靠供应商集团", 2400, "G银行", "电子元件加工费"),
        ("精密零件厂", 1300, "微信", "尾款结算")
    ]
    
    for i, (customer, amount, bank_type, description) in enumerate(income_sources, 1):
        income_date = datetime.now() - timedelta(days=random.randint(1, 30))
        income = {
            "id": f"I{i:04d}",
            "customer_id": next(c["id"] for c in data["customers"] if c["name"] == customer),
            "amount": str(amount),
            "bank_type": bank_type,
            "description": description,
            "date": str(income_date.date()),
            "created_at": str(datetime.now())
        }
        data["income"].append(income)
        print(f"✅ 收入{i:02d}: {customer} - ¥{amount} ({bank_type})")
    
    # 4. 生成支出记录 (所有12类支出)
    print("\n💸 生成支出数据...")
    expense_categories = [
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
    
    for i, (exp_type, amount, desc, supplier) in enumerate(expense_categories, 1):
        expense_date = datetime.now() - timedelta(days=random.randint(1, 45))
        expense = {
            "id": f"E{i:04d}",
            "type": exp_type,
            "amount": str(amount),
            "description": desc,
            "supplier": supplier,
            "date": str(expense_date.date()),
            "created_at": str(datetime.now())
        }
        data["expenses"].append(expense)
        print(f"✅ 支出{i:02d}: {exp_type} - ¥{amount}")
    
    # 5. 生成银行流水记录
    print("\n🏦 生成银行流水...")
    bank_transactions = []
    
    # G银行流水（有票业务）
    g_bank_income = sum(float(inc["amount"]) for inc in data["income"] if inc["bank_type"] == "G银行")
    bank_transactions.append({
        "id": "BT001",
        "bank": "G银行",
        "type": "收入",
        "amount": str(g_bank_income),
        "description": "客户加工费收入",
        "date": str(datetime.now().date()),
        "has_invoice": True
    })
    
    # N银行+微信流水（现金业务）
    n_bank_income = sum(float(inc["amount"]) for inc in data["income"] if inc["bank_type"] in ["N银行", "微信"])
    bank_transactions.append({
        "id": "BT002", 
        "bank": "N银行",
        "type": "收入",
        "amount": str(n_bank_income * 0.6),
        "description": "现金收入",
        "date": str(datetime.now().date()),
        "has_invoice": False
    })
    
    bank_transactions.append({
        "id": "BT003",
        "bank": "微信",
        "type": "收入", 
        "amount": str(n_bank_income * 0.4),
        "description": "微信收款",
        "date": str(datetime.now().date()),
        "has_invoice": False
    })
    
    # 支出流水
    total_expenses = sum(float(exp["amount"]) for exp in data["expenses"])
    bank_transactions.append({
        "id": "BT004",
        "bank": "G银行",
        "type": "支出",
        "amount": str(total_expenses * 0.7),
        "description": "日常经营支出",
        "date": str(datetime.now().date()),
        "has_invoice": True
    })
    
    bank_transactions.append({
        "id": "BT005",
        "bank": "N银行", 
        "type": "支出",
        "amount": str(total_expenses * 0.3),
        "description": "现金支出",
        "date": str(datetime.now().date()),
        "has_invoice": False
    })
    
    data["bank_transactions"] = bank_transactions
    for trans in bank_transactions:
        print(f"✅ {trans['bank']}: {trans['type']} ¥{trans['amount']}")
    
    # 6. 生成委外加工记录
    print("\n🏭 生成委外加工记录...")
    outsourcing_records = []
    outsourcing_counter = 1
    
    for order in data["orders"]:
        if len(order["outsourcing_processes"]) > 1:  # 有多道工序的订单
            base_cost = float(order["amount"]) * 0.3  # 委外成本约占30%
            for i, process in enumerate(order["outsourcing_processes"][:-1]):  # 除了最后一道氧化工序
                if process in ["喷砂", "拉丝", "抛光"]:
                    record = {
                        "id": f"OS{outsourcing_counter:04d}",
                        "order_id": order["id"],
                        "process": process,
                        "supplier": f"{process}外协加工厂",
                        "cost": str(base_cost / len([p for p in order["outsourcing_processes"] if p != "氧化"])),
                        "status": "已完成" if random.random() > 0.2 else "进行中",
                        "date": str((datetime.strptime(order["order_date"], "%Y-%m-%d") + timedelta(days=i*2)).date()),
                        "created_at": str(datetime.now())
                    }
                    outsourcing_records.append(record)
                    outsourcing_counter += 1
                    print(f"✅ 委外{i+1}: {order['item_name']} - {process}")
    
    data["outsourcing_records"] = outsourcing_records
    
    # 保存数据
    output_file = "complete_oxidation_factory_demo_data.json"
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2, default=str)
    
    print("\n" + "="*50)
    print("🎉 完整模拟数据生成完成！")
    print(f"📁 数据文件: {os.path.abspath(output_file)}")
    print("\n📊 数据统计:")
    print(f"   客户: {len(data['customers'])} 个")
    print(f"   订单: {len(data['orders'])} 个")
    print(f"   收入: {len(data['income'])} 笔")
    print(f"   支出: {len(data['expenses'])} 笔")
    print(f"   银行流水: {len(data['bank_transactions'])} 笔")
    print(f"   委外记录: {len(data['outsourcing_records'])} 条")
    print(f"   供应商: {len(set(e['supplier'] for e in data['expenses'] if e['supplier']))} 个")
    
    print("\n💡 系统特色功能演示:")
    print("   ✅ 多种计价方式支持")
    print("   ✅ 灵活委外加工管理")
    print("   ✅ 双银行账户处理")
    print("   ✅ 收支无需一一对应")
    print("   ✅ 完整的成本核算")
    print("   ✅ 自动报表生成")
    
    return data

if __name__ == "__main__":
    try:
        demo_data = generate_complete_demo_data()
        print("\n🚀 现在可以用这些数据测试系统功能了！")
        print("   建议操作流程:")
        print("   1. 运行一键部署")
        print("   2. 启动CWZS系统")
        print("   3. 选择生成学习数据")
        print("   4. 体验各项功能")
    except Exception as e:
        print(f"\n❌ 数据生成过程中出现错误: {e}")
    finally:
        input("\n按任意键退出...")