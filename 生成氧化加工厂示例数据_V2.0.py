#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
氧化加工厂财务系统 V2.0 - 示例数据生成器
为小白会计生成完整的、真实的示例数据
"""

import json
import random
from datetime import date, datetime, timedelta
from decimal import Decimal
from pathlib import Path
import sys

# 添加模块路径
sys.path.insert(0, str(Path(__file__).parent))

from oxidation_finance_v20.models.business_models import (
    Customer, Supplier, ProcessingOrder, Income, Expense,
    BankAccount, BankTransaction,
    PricingUnit, ProcessType, OrderStatus, ExpenseType, BankType
)


def generate_demo_data():
    """生成完整的示例数据"""
    print("🎨 正在生成氧化加工厂示例数据...")
    print("=" * 60)
    
    # 1. 生成客户数据
    print("\n📋 生成客户数据...")
    customers = generate_customers()
    print(f"✅ 已生成 {len(customers)} 个客户")
    
    # 2. 生成供应商数据
    print("\n📋 生成供应商数据...")
    suppliers = generate_suppliers()
    print(f"✅ 已生成 {len(suppliers)} 个供应商")
    
    # 3. 生成订单数据
    print("\n📋 生成加工订单...")
    orders = generate_orders(customers)
    print(f"✅ 已生成 {len(orders)} 个订单")
    
    # 4. 生成收入数据
    print("\n📋 生成收入记录...")
    incomes = generate_incomes(customers, orders)
    print(f"✅ 已生成 {len(incomes)} 条收入记录")
    
    # 5. 生成支出数据
    print("\n📋 生成支出记录...")
    expenses = generate_expenses(suppliers, orders)
    print(f"✅ 已生成 {len(expenses)} 条支出记录")
    
    # 6. 生成银行账户
    print("\n📋 生成银行账户...")
    bank_accounts = generate_bank_accounts()
    print(f"✅ 已生成 {len(bank_accounts)} 个银行账户")
    
    # 7. 生成银行交易
    print("\n📋 生成银行交易记录...")
    transactions = generate_bank_transactions(incomes, expenses)
    print(f"✅ 已生成 {len(transactions)} 条银行交易")
    
    # 8. 保存数据
    print("\n💾 保存示例数据...")
    save_demo_data({
        'customers': [serialize_customer(c) for c in customers],
        'suppliers': [serialize_supplier(s) for s in suppliers],
        'orders': [serialize_order(o) for o in orders],
        'incomes': [serialize_income(i) for i in incomes],
        'expenses': [serialize_expense(e) for e in expenses],
        'bank_accounts': [serialize_bank_account(b) for b in bank_accounts],
        'bank_transactions': [serialize_transaction(t) for t in transactions]
    })
    
    print("\n" + "=" * 60)
    print("🎉 示例数据生成完成！")
    print("\n📊 数据统计：")
    print(f"   客户数量: {len(customers)}")
    print(f"   供应商数量: {len(suppliers)}")
    print(f"   订单数量: {len(orders)}")
    print(f"   收入记录: {len(incomes)}")
    print(f"   支出记录: {len(expenses)}")
    print(f"   银行交易: {len(transactions)}")
    
    # 计算总金额
    total_income = sum(i.amount for i in incomes)
    total_expense = sum(e.amount for e in expenses)
    profit = total_income - total_expense
    
    print(f"\n💰 财务概况：")
    print(f"   总收入: ¥{total_income:,.2f}")
    print(f"   总支出: ¥{total_expense:,.2f}")
    print(f"   利润: ¥{profit:,.2f}")
    
    print("\n🚀 现在可以启动系统查看示例数据了！")
    print("   运行: python 氧化加工厂财务助手_V2.0_完整版.py")


def generate_customers():
    """生成客户数据"""
    customers = [
        Customer(
            name="优质客户有限公司",
            contact="张经理",
            phone="138****1234",
            address="广东省深圳市宝安区工业园A区",
            credit_limit=Decimal("100000"),
            notes="长期合作客户，信誉良好，月结30天"
        ),
        Customer(
            name="新兴科技股份有限公司",
            contact="李总",
            phone="139****5678",
            address="广东省东莞市松山湖高新区",
            credit_limit=Decimal("50000"),
            notes="新客户，订单量逐步增加"
        ),
        Customer(
            name="长期合作伙伴公司",
            contact="王主管",
            phone="136****9012",
            address="广东省佛山市南海区",
            credit_limit=Decimal("80000"),
            notes="5年老客户，付款及时"
        ),
        Customer(
            name="精密制造企业",
            contact="赵工",
            phone="137****3456",
            address="广东省惠州市惠阳区",
            credit_limit=Decimal("60000"),
            notes="对质量要求高，价格合理"
        ),
        Customer(
            name="五金配件厂",
            contact="钱老板",
            phone="135****7890",
            address="广东省中山市小榄镇",
            credit_limit=Decimal("40000"),
            notes="小批量多品种订单"
        )
    ]
    return customers


def generate_suppliers():
    """生成供应商数据"""
    suppliers = [
        Supplier(
            name="化工原料供应商",
            contact="孙经理",
            phone="138****2345",
            address="广东省广州市黄埔区",
            business_type="原料供应商",
            notes="供应三酸、片碱、亚钠等化工原料"
        ),
        Supplier(
            name="喷砂加工厂",
            contact="周师傅",
            phone="139****6789",
            address="广东省深圳市龙岗区",
            business_type="委外加工商",
            notes="专业喷砂处理，质量稳定"
        ),
        Supplier(
            name="拉丝抛光中心",
            contact="吴老板",
            phone="136****0123",
            address="广东省东莞市长安镇",
            business_type="委外加工商",
            notes="拉丝和抛光一条龙服务"
        ),
        Supplier(
            name="色粉供应商",
            contact="郑总",
            phone="137****4567",
            address="广东省佛山市顺德区",
            business_type="原料供应商",
            notes="各种颜色色粉，质量可靠"
        ),
        Supplier(
            name="挂具制造厂",
            contact="冯工",
            phone="135****8901",
            address="广东省中山市",
            business_type="设备供应商",
            notes="定制各种挂具夹具"
        )
    ]
    return suppliers


def generate_orders(customers):
    """生成加工订单"""
    orders = []
    start_date = date.today() - timedelta(days=90)  # 最近3个月的订单
    
    # 订单模板
    order_templates = [
        {
            "item": "铝型材6063",
            "unit": PricingUnit.METER,
            "quantity_range": (50, 200),
            "price_range": (3, 8),
            "processes": [ProcessType.SANDBLASTING, ProcessType.OXIDATION],
            "outsourced": [ProcessType.SANDBLASTING]
        },
        {
            "item": "不锈钢螺丝M6",
            "unit": PricingUnit.PIECE,
            "quantity_range": (1000, 5000),
            "price_range": (0.1, 0.3),
            "processes": [ProcessType.POLISHING, ProcessType.OXIDATION],
            "outsourced": [ProcessType.POLISHING]
        },
        {
            "item": "铝板5052",
            "unit": PricingUnit.SQUARE_METER,
            "quantity_range": (10, 50),
            "price_range": (15, 30),
            "processes": [ProcessType.WIRE_DRAWING, ProcessType.OXIDATION],
            "outsourced": [ProcessType.WIRE_DRAWING]
        },
        {
            "item": "铝合金把手",
            "unit": PricingUnit.UNIT,
            "quantity_range": (100, 500),
            "price_range": (2, 5),
            "processes": [ProcessType.POLISHING, ProcessType.OXIDATION],
            "outsourced": []
        },
        {
            "item": "铝条6061",
            "unit": PricingUnit.STRIP,
            "quantity_range": (50, 300),
            "price_range": (1.5, 4),
            "processes": [ProcessType.SANDBLASTING, ProcessType.OXIDATION],
            "outsourced": [ProcessType.SANDBLASTING]
        }
    ]
    
    order_no = 1
    for day_offset in range(0, 90, 3):  # 每3天一个订单
        order_date = start_date + timedelta(days=day_offset)
        customer = random.choice(customers)
        template = random.choice(order_templates)
        
        quantity = Decimal(str(random.randint(*template["quantity_range"])))
        unit_price = Decimal(str(random.uniform(*template["price_range"]))).quantize(Decimal("0.01"))
        total_amount = quantity * unit_price
        
        # 计算委外成本
        outsourcing_cost = Decimal("0")
        if template["outsourced"]:
            outsourcing_cost = total_amount * Decimal("0.2")  # 委外成本约20%
        
        # 确定订单状态
        days_since_order = (date.today() - order_date).days
        if days_since_order > 30:
            status = OrderStatus.PAID
            completion_date = order_date + timedelta(days=random.randint(5, 15))
            delivery_date = completion_date + timedelta(days=random.randint(1, 3))
            received_amount = total_amount
        elif days_since_order > 15:
            status = OrderStatus.DELIVERED
            completion_date = order_date + timedelta(days=random.randint(5, 15))
            delivery_date = completion_date + timedelta(days=random.randint(1, 3))
            received_amount = total_amount * Decimal(str(random.uniform(0.5, 1.0)))
        elif days_since_order > 7:
            status = OrderStatus.COMPLETED
            completion_date = order_date + timedelta(days=random.randint(5, 15))
            delivery_date = None
            received_amount = Decimal("0")
        else:
            status = OrderStatus.IN_PROGRESS
            completion_date = None
            delivery_date = None
            received_amount = Decimal("0")
        
        order = ProcessingOrder(
            order_no=f"OX{order_date.strftime('%Y%m')}{order_no:03d}",
            customer_id=customer.id,
            customer_name=customer.name,
            item_description=template["item"],
            quantity=quantity,
            pricing_unit=template["unit"],
            unit_price=unit_price,
            processes=template["processes"],
            outsourced_processes=[p.value for p in template["outsourced"]],
            total_amount=total_amount,
            outsourcing_cost=outsourcing_cost,
            status=status,
            order_date=order_date,
            completion_date=completion_date,
            delivery_date=delivery_date,
            received_amount=received_amount.quantize(Decimal("0.01")),
            notes=f"示例订单 - {template['item']}"
        )
        
        orders.append(order)
        order_no += 1
    
    return orders


def generate_incomes(customers, orders):
    """生成收入记录"""
    incomes = []
    
    # 为已收款的订单生成收入记录
    paid_orders = [o for o in orders if o.received_amount > 0]
    
    for order in paid_orders:
        # 70%的订单一次性收款，30%分多次收款
        if random.random() < 0.7:
            # 一次性收款
            income = Income(
                customer_id=order.customer_id,
                customer_name=order.customer_name,
                amount=order.received_amount,
                bank_type=BankType.G_BANK if random.random() < 0.8 else BankType.N_BANK,
                has_invoice=random.random() < 0.9,
                related_orders=[order.id],
                allocation={order.id: order.received_amount},
                income_date=order.delivery_date or order.completion_date or order.order_date,
                notes=f"订单{order.order_no}收款"
            )
            incomes.append(income)
        else:
            # 分两次收款
            first_amount = order.received_amount * Decimal("0.6")
            second_amount = order.received_amount - first_amount
            
            income1 = Income(
                customer_id=order.customer_id,
                customer_name=order.customer_name,
                amount=first_amount.quantize(Decimal("0.01")),
                bank_type=BankType.G_BANK,
                has_invoice=True,
                related_orders=[order.id],
                allocation={order.id: first_amount},
                income_date=order.order_date + timedelta(days=random.randint(1, 5)),
                notes=f"订单{order.order_no}首款"
            )
            incomes.append(income1)
            
            income2 = Income(
                customer_id=order.customer_id,
                customer_name=order.customer_name,
                amount=second_amount.quantize(Decimal("0.01")),
                bank_type=BankType.N_BANK if random.random() < 0.3 else BankType.G_BANK,
                has_invoice=random.random() < 0.7,
                related_orders=[order.id],
                allocation={order.id: second_amount},
                income_date=order.delivery_date or order.completion_date or (order.order_date + timedelta(days=15)),
                notes=f"订单{order.order_no}尾款"
            )
            incomes.append(income2)
    
    # 生成一些不对应订单的收款（预收款）
    for _ in range(3):
        customer = random.choice(customers)
        income = Income(
            customer_id=customer.id,
            customer_name=customer.name,
            amount=Decimal(str(random.randint(5000, 20000))),
            bank_type=BankType.G_BANK if random.random() < 0.7 else BankType.N_BANK,
            has_invoice=False,
            related_orders=[],
            allocation={},
            income_date=date.today() - timedelta(days=random.randint(1, 30)),
            notes="预收款，待分配"
        )
        incomes.append(income)
    
    return incomes


def generate_expenses(suppliers, orders):
    """生成支出记录"""
    expenses = []
    start_date = date.today() - timedelta(days=90)
    
    # 1. 固定支出（每月）
    for month_offset in range(3):  # 最近3个月
        expense_date = start_date + timedelta(days=month_offset * 30)
        
        # 房租
        expenses.append(Expense(
            expense_type=ExpenseType.RENT,
            supplier_name="工业园物业管理处",
            amount=Decimal("8000"),
            bank_type=BankType.G_BANK,
            has_invoice=True,
            expense_date=expense_date,
            description="厂房租金",
            notes=f"{expense_date.year}年{expense_date.month}月房租"
        ))
        
        # 水电费
        expenses.append(Expense(
            expense_type=ExpenseType.UTILITIES,
            supplier_name="供电局/自来水公司",
            amount=Decimal(str(random.randint(3000, 6000))),
            bank_type=BankType.G_BANK,
            has_invoice=True,
            expense_date=expense_date + timedelta(days=5),
            description="水电费",
            notes=f"{expense_date.year}年{expense_date.month}月水电费"
        ))
        
        # 工资
        expenses.append(Expense(
            expense_type=ExpenseType.SALARY,
            supplier_name="员工工资",
            amount=Decimal(str(random.randint(25000, 35000))),
            bank_type=BankType.G_BANK,
            has_invoice=False,
            expense_date=expense_date + timedelta(days=10),
            description="员工工资",
            notes=f"{expense_date.year}年{expense_date.month}月工资"
        ))
    
    # 2. 原料采购
    chemical_supplier = [s for s in suppliers if "化工" in s.name][0]
    color_supplier = [s for s in suppliers if "色粉" in s.name][0]
    
    for _ in range(10):  # 10次原料采购
        expense_date = start_date + timedelta(days=random.randint(0, 90))
        
        # 三酸采购
        if random.random() < 0.7:
            expenses.append(Expense(
                expense_type=ExpenseType.ACID_THREE,
                supplier_id=chemical_supplier.id,
                supplier_name=chemical_supplier.name,
                amount=Decimal(str(random.randint(3000, 8000))),
                bank_type=BankType.G_BANK,
                has_invoice=True,
                expense_date=expense_date,
                description="硫酸、硝酸、盐酸采购",
                notes="氧化用酸"
            ))
        
        # 其他化工原料
        for expense_type in [ExpenseType.CAUSTIC_SODA, ExpenseType.SODIUM_SULFITE, ExpenseType.DEGREASER]:
            if random.random() < 0.5:
                expenses.append(Expense(
                    expense_type=expense_type,
                    supplier_id=chemical_supplier.id,
                    supplier_name=chemical_supplier.name,
                    amount=Decimal(str(random.randint(1000, 3000))),
                    bank_type=BankType.G_BANK,
                    has_invoice=True,
                    expense_date=expense_date,
                    description=f"{expense_type.value}采购",
                    notes=""
                ))
        
        # 色粉采购
        if random.random() < 0.6:
            expenses.append(Expense(
                expense_type=ExpenseType.COLOR_POWDER,
                supplier_id=color_supplier.id,
                supplier_name=color_supplier.name,
                amount=Decimal(str(random.randint(500, 2000))),
                bank_type=BankType.G_BANK,
                has_invoice=True,
                expense_date=expense_date,
                description="氧化色粉采购",
                notes="黑色、金色、银色等"
            ))
    
    # 3. 委外加工费用
    sandblast_supplier = [s for s in suppliers if "喷砂" in s.name][0]
    polish_supplier = [s for s in suppliers if "拉丝" in s.name][0]
    
    outsourced_orders = [o for o in orders if o.outsourcing_cost > 0 and o.status in [OrderStatus.COMPLETED, OrderStatus.DELIVERED, OrderStatus.PAID]]
    
    for order in outsourced_orders:
        if ProcessType.SANDBLASTING.value in order.outsourced_processes:
            expenses.append(Expense(
                expense_type=ExpenseType.OUTSOURCING,
                supplier_id=sandblast_supplier.id,
                supplier_name=sandblast_supplier.name,
                amount=order.outsourcing_cost * Decimal("0.5"),  # 喷砂占一半
                bank_type=BankType.G_BANK if random.random() < 0.8 else BankType.N_BANK,
                has_invoice=random.random() < 0.9,
                related_order_id=order.id,
                expense_date=order.order_date + timedelta(days=random.randint(3, 10)),
                description=f"订单{order.order_no}喷砂加工费",
                notes=""
            ))
        
        if ProcessType.WIRE_DRAWING.value in order.outsourced_processes or ProcessType.POLISHING.value in order.outsourced_processes:
            expenses.append(Expense(
                expense_type=ExpenseType.OUTSOURCING,
                supplier_id=polish_supplier.id,
                supplier_name=polish_supplier.name,
                amount=order.outsourcing_cost * Decimal("0.5"),  # 拉丝/抛光占一半
                bank_type=BankType.G_BANK if random.random() < 0.8 else BankType.N_BANK,
                has_invoice=random.random() < 0.9,
                related_order_id=order.id,
                expense_date=order.order_date + timedelta(days=random.randint(3, 10)),
                description=f"订单{order.order_no}拉丝/抛光加工费",
                notes=""
            ))
    
    # 4. 日常费用
    for _ in range(15):
        expense_date = start_date + timedelta(days=random.randint(0, 90))
        expenses.append(Expense(
            expense_type=ExpenseType.DAILY_EXPENSE,
            supplier_name="",
            amount=Decimal(str(random.randint(100, 1000))),
            bank_type=BankType.N_BANK if random.random() < 0.6 else BankType.G_BANK,
            has_invoice=random.random() < 0.3,
            expense_date=expense_date,
            description=random.choice(["办公用品", "维修费", "运输费", "招待费", "通讯费"]),
            notes=""
        ))
    
    return expenses


def generate_bank_accounts():
    """生成银行账户"""
    return [
        BankAccount(
            bank_type=BankType.G_BANK,
            account_name="G银行对公账户",
            account_number="6222****1234",
            balance=Decimal("150000"),
            notes="主要用于有票据的正式交易"
        ),
        BankAccount(
            bank_type=BankType.N_BANK,
            account_name="N银行现金账户",
            account_number="6228****5678",
            balance=Decimal("35000"),
            notes="与微信结合，用于现金交易"
        )
    ]


def generate_bank_transactions(incomes, expenses):
    """生成银行交易记录"""
    transactions = []
    
    # 为每笔收入生成银行交易
    for income in incomes:
        transaction = BankTransaction(
            bank_type=income.bank_type,
            transaction_date=income.income_date,
            amount=income.amount,
            counterparty=income.customer_name,
            description=income.notes or "客户付款",
            matched=True,
            matched_income_id=income.id,
            notes="已匹配到收入记录"
        )
        transactions.append(transaction)
    
    # 为每笔支出生成银行交易
    for expense in expenses:
        transaction = BankTransaction(
            bank_type=expense.bank_type,
            transaction_date=expense.expense_date,
            amount=-expense.amount,  # 支出为负数
            counterparty=expense.supplier_name or expense.description,
            description=expense.description,
            matched=True,
            matched_expense_id=expense.id,
            notes="已匹配到支出记录"
        )
        transactions.append(transaction)
    
    # 按日期排序
    transactions.sort(key=lambda t: t.transaction_date)
    
    return transactions


def serialize_customer(customer):
    """序列化客户对象"""
    data = customer.__dict__.copy()
    data['credit_limit'] = float(customer.credit_limit)
    data['created_at'] = customer.created_at.isoformat()
    return data


def serialize_supplier(supplier):
    """序列化供应商对象"""
    data = supplier.__dict__.copy()
    data['created_at'] = supplier.created_at.isoformat()
    return data


def serialize_bank_account(account):
    """序列化银行账户对象"""
    data = account.__dict__.copy()
    data['bank_type'] = account.bank_type.value
    data['balance'] = float(account.balance)
    return data


def serialize_order(order):
    """序列化订单对象"""
    data = order.__dict__.copy()
    data['pricing_unit'] = order.pricing_unit.value
    data['processes'] = [p.value for p in order.processes]
    data['status'] = order.status.value
    data['order_date'] = order.order_date.isoformat()
    data['completion_date'] = order.completion_date.isoformat() if order.completion_date else None
    data['delivery_date'] = order.delivery_date.isoformat() if order.delivery_date else None
    data['total_amount'] = float(order.total_amount)
    data['outsourcing_cost'] = float(order.outsourcing_cost)
    data['received_amount'] = float(order.received_amount)
    data['quantity'] = float(order.quantity)
    data['unit_price'] = float(order.unit_price)
    data['created_at'] = order.created_at.isoformat()
    data['updated_at'] = order.updated_at.isoformat()
    return data


def serialize_income(income):
    """序列化收入对象"""
    data = income.__dict__.copy()
    data['bank_type'] = income.bank_type.value
    data['amount'] = float(income.amount)
    data['allocation'] = {k: float(v) for k, v in income.allocation.items()}
    data['income_date'] = income.income_date.isoformat()
    data['created_at'] = income.created_at.isoformat()
    return data


def serialize_expense(expense):
    """序列化支出对象"""
    data = expense.__dict__.copy()
    data['expense_type'] = expense.expense_type.value
    data['bank_type'] = expense.bank_type.value
    data['amount'] = float(expense.amount)
    data['expense_date'] = expense.expense_date.isoformat()
    data['created_at'] = expense.created_at.isoformat()
    return data


def serialize_transaction(transaction):
    """序列化银行交易对象"""
    data = transaction.__dict__.copy()
    data['bank_type'] = transaction.bank_type.value
    data['amount'] = float(transaction.amount)
    data['transaction_date'] = transaction.transaction_date.isoformat()
    data['created_at'] = transaction.created_at.isoformat()
    return data


def save_demo_data(data):
    """保存示例数据到文件"""
    output_dir = Path("demo_data_v20")
    output_dir.mkdir(exist_ok=True)
    
    output_file = output_dir / "oxidation_factory_demo_data.json"
    
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    
    print(f"✅ 数据已保存到: {output_file}")


if __name__ == "__main__":
    try:
        generate_demo_data()
    except Exception as e:
        print(f"\n❌ 生成数据时出错: {e}")
        import traceback
        traceback.print_exc()