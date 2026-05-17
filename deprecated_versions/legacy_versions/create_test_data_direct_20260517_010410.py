# -*- coding: utf-8 -*-
"""直接创建测试数据"""
import json
import random
from datetime import datetime, timedelta
from pathlib import Path

print("=" * 70)
print(" " * 20 + "生成V1.5测试数据")
print("=" * 70)
print()

data_dir = Path("财务数据")
data_dir.mkdir(exist_ok=True)

# 1. 生成往来单位
print("1. 生成往来单位数据...")
entities = {}

customers = [
    {"name": "华为精密制造", "type": "customer", "contact": "张经理", "phone": "138****1001"},
    {"name": "比亚迪汽车配件", "type": "customer", "contact": "李总", "phone": "139****2002"},
    {"name": "格力电器零件", "type": "customer", "contact": "王主管", "phone": "136****3003"},
    {"name": "美的家电部件", "type": "customer", "contact": "赵经理", "phone": "137****4004"},
    {"name": "小米科技配件", "type": "customer", "contact": "刘总", "phone": "135****5005"},
]

for customer in customers:
    entities[customer["name"]] = {
        "type": customer["type"],
        "contact": customer["contact"],
        "phone": customer["phone"],
        "payment_terms": random.choice(["现金", "30天", "60天"]),
        "created_at": (datetime.now() - timedelta(days=random.randint(30, 365))).isoformat()
    }

suppliers = [
    {"name": "三酸供应商_化工贸易", "type": "supplier", "category": "原材料"},
    {"name": "片碱供应商_化学品公司", "type": "supplier", "category": "原材料"},
    {"name": "色粉供应商_颜料厂", "type": "supplier", "category": "原材料"},
    {"name": "除油剂供应商_清洁剂厂", "type": "supplier", "category": "原材料"},
    {"name": "喷砂外发_表面处理厂", "type": "supplier", "category": "外发加工"},
    {"name": "拉丝外发_金属加工厂", "type": "supplier", "category": "外发加工"},
    {"name": "抛光外发_精密加工厂", "type": "supplier", "category": "外发加工"},
    {"name": "挂具供应商_工具厂", "type": "supplier", "category": "工具设备"},
]

for supplier in suppliers:
    entities[supplier["name"]] = {
        "type": supplier["type"],
        "category": supplier["category"],
        "payment_terms": random.choice(["现金", "30天", "月结"]),
        "created_at": (datetime.now() - timedelta(days=random.randint(30, 365))).isoformat()
    }

with open(data_dir / "往来单位.json", 'w', encoding='utf-8') as f:
    json.dump(entities, f, ensure_ascii=False, indent=2)
print(f"   ✓ 已生成 {len(entities)} 个往来单位")

# 2. 生成加工订单
print("\n2. 生成加工订单数据...")
orders = []
customer_list = [k for k, v in entities.items() if v.get('type') in ['customer', 'both']]

pricing_units = [
    {"unit": "件", "price_range": (50, 200)},
    {"unit": "条", "price_range": (30, 150)},
    {"unit": "个", "price_range": (20, 100)},
    {"unit": "项", "price_range": (100, 500)},
    {"unit": "米长", "price_range": (10, 50)},
    {"unit": "米重", "price_range": (15, 80)},
    {"unit": "平方米", "price_range": (80, 300)}
]

for i in range(30):
    customer = random.choice(customer_list)
    unit_info = random.choice(pricing_units)
    quantity = random.randint(10, 500)
    unit_price = random.uniform(*unit_info["price_range"])
    order_amount = quantity * unit_price
    
    payment_ratio = random.choice([0, 0.3, 0.5, 0.7, 1.0])
    paid_amount = order_amount * payment_ratio
    unpaid_amount = order_amount - paid_amount
    
    order_date = datetime.now() - timedelta(days=random.randint(1, 90))
    
    order = {
        "order_no": f"OX{order_date.strftime('%Y%m%d')}{i+1:03d}",
        "order_date": order_date.strftime('%Y-%m-%d'),
        "customer": customer,
        "product_name": f"氧化加工_{random.choice(['黑色', '银白', '香槟金', '古铜', '玫瑰金'])}",
        "quantity": quantity,
        "unit": unit_info["unit"],
        "unit_price": round(unit_price, 2),
        "order_amount": round(order_amount, 2),
        "paid_amount": round(paid_amount, 2),
        "unpaid_amount": round(unpaid_amount, 2),
        "status": "已完成" if payment_ratio == 1.0 else "部分付款" if payment_ratio > 0 else "未付款",
        "notes": f"包含外发工序：{random.choice(['喷砂', '拉丝', '抛光', '喷砂+拉丝'])}"
    }
    orders.append(order)

with open(data_dir / "加工订单.json", 'w', encoding='utf-8') as f:
    json.dump(orders, f, ensure_ascii=False, indent=2)
print(f"   ✓ 已生成 {len(orders)} 个加工订单")

# 3. 生成收支记录
print("\n3. 生成收支记录数据...")
transactions = []
supplier_list = [k for k, v in entities.items() if v.get('type') == 'supplier']

# 从订单生成收入
for order in orders:
    if order['paid_amount'] > 0:
        payment_date = datetime.strptime(order['order_date'], '%Y-%m-%d') + timedelta(days=random.randint(0, 30))
        
        transaction = {
            "id": f"INC{payment_date.strftime('%Y%m%d%H%M%S')}{len(transactions):03d}",
            "date": payment_date.strftime('%Y-%m-%d'),
            "type": "income",
            "category": "氧化加工费",
            "amount": round(order['paid_amount'], 2),
            "customer": order['customer'],
            "payment_method": random.choice(["G银行", "N银行/微信"]),
            "order_no": order['order_no'],
            "notes": f"订单 {order['order_no']} 付款",
            "created_at": datetime.now().isoformat()
        }
        transactions.append(transaction)

# 生成支出
expense_categories = [
    {"category": "原材料采购", "amount_range": (500, 5000)},
    {"category": "外发加工费", "amount_range": (1000, 8000)},
    {"category": "水电费", "amount_range": (800, 2000)},
    {"category": "房租", "amount_range": (3000, 5000)},
    {"category": "工资", "amount_range": (15000, 30000)},
    {"category": "日常开支", "amount_range": (200, 1000)}
]

for i in range(50):
    expense_cat = random.choice(expense_categories)
    expense_date = datetime.now() - timedelta(days=random.randint(1, 90))
    amount = random.uniform(*expense_cat["amount_range"])
    
    transaction = {
        "id": f"EXP{expense_date.strftime('%Y%m%d%H%M%S')}{len(transactions):03d}",
        "date": expense_date.strftime('%Y-%m-%d'),
        "type": "expense",
        "category": expense_cat["category"],
        "amount": round(amount, 2),
        "supplier": random.choice(supplier_list) if random.random() > 0.3 else "",
        "payment_method": random.choice(["G银行", "N银行/微信", "现金"]),
        "notes": f"{expense_cat['category']}",
        "created_at": datetime.now().isoformat()
    }
    transactions.append(transaction)

transactions.sort(key=lambda x: x['date'])

with open(data_dir / "收支记录.json", 'w', encoding='utf-8') as f:
    json.dump(transactions, f, ensure_ascii=False, indent=2)
print(f"   ✓ 已生成 {len(transactions)} 条收支记录")

print("\n" + "=" * 70)
print("✓ 测试数据生成完成！")
print()
print("数据文件位置：")
print(f"  • {data_dir / '往来单位.json'}")
print(f"  • {data_dir / '加工订单.json'}")
print(f"  • {data_dir / '收支记录.json'}")
print()
print("现在可以运行【氧化加工厂财务助手_V1.5实战版.py】进行测试！")
print("=" * 70)
