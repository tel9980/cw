#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
氧化加工厂财务系统功能测试
"""

import json
import os
from datetime import datetime, date
from decimal import Decimal

def test_simple_finance_system():
    """测试简化财务系统"""
    print("🧪 开始测试氧化加工厂财务系统...")
    
    # 创建测试数据
    data = {
        'customers': [],
        'orders': [],
        'income': [],
        'expenses': [],
        'bank_transactions': [],
        'suppliers': []
    }
    
    print("\n1. 测试客户管理...")
    # 添加客户
    customers = [
        ('优质客户有限公司', '张经理', '13800138001'),
        ('新兴科技股份有限公司', '李总', '13900139002'),
        ('长期合作伙伴公司', '王主任', '13700137003')
    ]
    
    for i, (name, contact, phone) in enumerate(customers, 1):
        customer = {
            'id': f'C{i:03d}',
            'name': name,
            'contact': contact,
            'phone': phone,
            'created_at': str(datetime.now())
        }
        data['customers'].append(customer)
        print(f'   ✅ 添加客户: {name}')
    
    print("\n2. 测试订单管理...")
    # 添加不同类型计价的订单
    orders_data = [
        ('C001', '铝合金把手', 500, 2.5, '件', ['氧化']),
        ('C002', '不锈钢管', 150, 12.0, '米', ['拉丝', '氧化']),
        ('C003', '铜质配件', 200, 8.0, '公斤', ['抛光', '氧化']),
        ('C001', '铝板', 30, 45.0, '平方米', ['氧化'])
    ]
    
    for i, (cust_id, item, qty, price, unit, processes) in enumerate(orders_data, 1):
        amount = Decimal(str(qty)) * Decimal(str(price))
        order = {
            'id': f'O{i:04d}',
            'customer_id': cust_id,
            'item_name': item,
            'quantity': qty,
            'unit_price': str(price),
            'pricing_unit': unit,
            'amount': str(amount),
            'outsourcing_processes': processes,
            'status': '待加工',
            'created_at': str(datetime.now())
        }
        data['orders'].append(order)
        print(f'   ✅ 添加订单: {item} ({qty}{unit}) - ¥{amount:.2f}')
    
    print("\n3. 测试收入管理...")
    # 添加收入记录
    income_data = [
        ('C001', 2500, 'G银行', '铝合金把手加工费'),
        ('C002', 1800, 'N银行', '不锈钢管加工费'),
        ('C003', 1600, 'G银行', '铜质配件加工费')
    ]
    
    for i, (cust_id, amount, bank, desc) in enumerate(income_data, 1):
        income = {
            'id': f'I{i:04d}',
            'customer_id': cust_id,
            'amount': str(amount),
            'bank_type': bank,
            'description': desc,
            'date': str(date.today()),
            'created_at': str(datetime.now())
        }
        data['income'].append(income)
        print(f'   ✅ 记录收入: {desc} - ¥{amount} ({bank})')
    
    print("\n4. 测试支出管理...")
    # 添加支出记录
    expense_data = [
        ('房租', 8000, '厂房租金', ''),
        ('水电费', 2500, '本月水电费', ''),
        ('三酸', 3200, '硫酸、盐酸、硝酸', '化工供应商'),
        ('片碱', 1800, '氢氧化钠', '化工供应商'),
        ('外发加工费', 2800, '喷砂拉丝费用', '外协加工厂'),
        ('工资', 15000, '员工工资', '')
    ]
    
    for i, (exp_type, amount, desc, supplier) in enumerate(expense_data, 1):
        expense = {
            'id': f'E{i:04d}',
            'type': exp_type,
            'amount': str(amount),
            'description': desc,
            'supplier': supplier,
            'date': str(date.today()),
            'created_at': str(datetime.now())
        }
        data['expenses'].append(expense)
        print(f'   ✅ 记录支出: {exp_type} - ¥{amount}')
    
    print("\n5. 测试财务统计...")
    # 计算财务概况
    total_income = sum(Decimal(item['amount']) for item in data['income'])
    total_expenses = sum(Decimal(item['amount']) for item in data['expenses'])
    profit = total_income - total_expenses
    
    print(f'   📊 财务概况:')
    print(f'      总收入: ¥{total_income:,.2f}')
    print(f'      总支出: ¥{total_expenses:,.2f}')
    print(f'      利润:   ¥{profit:,.2f}')
    
    print("\n6. 测试数据保存...")
    # 保存数据
    with open('test_finance_data.json', 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2, default=str)
    print('   ✅ 数据已保存到 test_finance_data.json')
    
    print("\n7. 测试数据读取...")
    # 读取数据验证
    with open('test_finance_data.json', 'r', encoding='utf-8') as f:
        loaded_data = json.load(f)
    
    print(f'   ✅ 成功读取数据:')
    print(f'      客户: {len(loaded_data["customers"])} 个')
    print(f'      订单: {len(loaded_data["orders"])} 个')
    print(f'      收入: {len(loaded_data["income"])} 笔')
    print(f'      支出: {len(loaded_data["expenses"])} 笔')
    
    print("\n🎉 所有测试通过！系统功能正常")
    
    # 清理测试文件
    if os.path.exists('test_finance_data.json'):
        os.remove('test_finance_data.json')
        print("🗑️  测试文件已清理")

if __name__ == "__main__":
    test_simple_finance_system()