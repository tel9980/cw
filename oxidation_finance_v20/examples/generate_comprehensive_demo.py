#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
氧化加工厂财务系统 V2.0 - 示例数据生成器
为小白会计生成完整的、真实的示例数据
"""

import sys
import io
import json
import random
from datetime import date, datetime, timedelta
from decimal import Decimal
from pathlib import Path

# 设置UTF-8输出
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

# 添加模块路径
sys.path.insert(0, str(Path(__file__).parent))

from oxidation_finance_v20.models.business_models import (
    Customer,
    Supplier,
    ProcessingOrder,
    Income,
    Expense,
    BankAccount,
    BankTransaction,
    PricingUnit,
    ProcessType,
    OrderStatus,
    ExpenseType,
    BankType,
)


def print_ok(msg):
    print(f"[OK] {msg}")


def print_info(msg):
    print(f"[INFO] {msg}")


def print_error(msg):
    print(f"[ERROR] {msg}")


def generate_demo_data():
    """生成完整的示例数据"""
    print("\n" + "=" * 60)
    print("氧化加工厂财务系统 V2.0 - 示例数据生成器")
    print("=" * 60)

    # 1. 生成客户数据
    print_ok("正在生成客户数据...")
    customers = generate_customers()
    print(f"  已生成 {len(customers)} 个客户")

    # 2. 生成供应商数据
    print_ok("正在生成供应商数据...")
    suppliers = generate_suppliers()
    print(f"  已生成 {len(suppliers)} 个供应商")

    # 3. 生成订单数据
    print_ok("正在生成加工订单...")
    orders = generate_orders(customers)
    print(f"  已生成 {len(orders)} 个订单")

    # 4. 生成收入数据
    print_ok("正在生成收入记录...")
    incomes = generate_incomes(customers, orders)
    print(f"  已生成 {len(incomes)} 条收入记录")

    # 5. 生成支出数据
    print_ok("正在生成支出记录...")
    expenses = generate_expenses(suppliers, orders)
    print(f"  已生成 {len(expenses)} 条支出记录")

    # 6. 生成银行账户
    print_ok("正在生成银行账户...")
    bank_accounts = generate_bank_accounts()
    print(f"  已生成 {len(bank_accounts)} 个银行账户")

    # 7. 生成银行交易
    print_ok("正在生成银行交易记录...")
    transactions = generate_bank_transactions(incomes, expenses)
    print(f"  已生成 {len(transactions)} 条银行交易")

    # 8. 保存数据
    print_ok("正在保存示例数据...")
    save_demo_data(
        {
            "customers": [serialize_customer(c) for c in customers],
            "suppliers": [serialize_supplier(s) for s in suppliers],
            "orders": [serialize_order(o) for o in orders],
            "incomes": [serialize_income(i) for i in incomes],
            "expenses": [serialize_expense(e) for e in expenses],
            "bank_accounts": [serialize_bank_account(b) for b in bank_accounts],
            "bank_transactions": [serialize_transaction(t) for t in transactions],
        }
    )

    print("\n" + "=" * 60)
    print("示例数据生成完成！")
    print("=" * 60)
    print("\n数据统计：")
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

    print(f"\n财务概况：")
    print(f"   总收入: ¥{total_income:,.2f}")
    print(f"   总支出: ¥{total_expense:,.2f}")
    print(f"   利润: ¥{profit:,.2f}")

    print("\n" + "-" * 60)
    print("计价方式说明：")
    for unit in PricingUnit:
        print(f"   {unit.value}")

    print("\n加工工序说明：")
    for process in ProcessType:
        print(f"   {process.value}")

    print("\n支出类型说明：")
    for expense in ExpenseType:
        print(f"   {expense.value}")

    print("\n" + "=" * 60)
    print("现在可以启动系统查看示例数据了！")
    print("运行: python 氧化加工厂财务助手_V2.0_完整版.py")
    print("=" * 60 + "\n")


def generate_customers():
    """生成客户数据 - 体现各种计价方式"""
    customers = [
        Customer(
            name="优质客户有限公司",
            contact="张经理",
            phone="13800138001",
            address="广东省深圳市宝安区工业园A区",
            credit_limit=Decimal("100000"),
            notes="长期合作客户，按米计价为主",
        ),
        Customer(
            name="新兴科技股份有限公司",
            contact="李总",
            phone="13900139002",
            address="广东省东莞市松山湖高新区",
            credit_limit=Decimal("50000"),
            notes="新客户，按件计价",
        ),
        Customer(
            name="精密制造企业",
            contact="赵工",
            phone="13700137003",
            address="广东省惠州市惠阳区",
            credit_limit=Decimal("60000"),
            notes="对质量要求高，按公斤计价",
        ),
        Customer(
            name="五金配件厂",
            contact="钱老板",
            phone="13500135004",
            address="广东省中山市小榄镇",
            credit_limit=Decimal("40000"),
            notes="小批量多品种订单，按个计价",
        ),
        Customer(
            name="铝材批发中心",
            contact="周老板",
            phone="13600136005",
            address="广东省佛山市南海区",
            credit_limit=Decimal("80000"),
            notes="大批量订单，按平方米计价",
        ),
        Customer(
            name="电子元件加工厂",
            contact="吴经理",
            phone="13800138006",
            address="广东省深圳市龙岗区",
            credit_limit=Decimal("30000"),
            notes="小零件，按条计价",
        ),
    ]
    return customers


def generate_suppliers():
    """生成供应商数据 - 体现各种支出类型"""
    suppliers = [
        Supplier(
            name="化工原料贸易公司",
            contact="陈经理",
            phone="18800188001",
            address="广东省广州市黄埔区",
            business_type="化工原料供应商",
            notes="供应三酸、片碱、亚钠、除油剂等",
        ),
        Supplier(
            name="专业喷砂加工厂",
            contact="刘老板",
            phone="13900139002",
            address="广东省东莞市长安镇",
            business_type="委外加工商",
            notes="专业喷砂加工，设备齐全",
        ),
        Supplier(
            name="拉丝抛光加工店",
            contact="黄师傅",
            phone="13700137003",
            address="广东省佛山市顺德区",
            business_type="委外加工商",
            notes="手工拉丝、机械抛光",
        ),
        Supplier(
            name="色粉有限公司",
            contact="林经理",
            phone="13600136004",
            address="广东省深圳市光明区",
            business_type="化工原料供应商",
            notes="氧化着色色粉，金色、黑色、古铜色等",
        ),
        Supplier(
            name="挂具制造厂",
            contact="郑老板",
            phone="13500135005",
            address="广东省中山市古镇",
            business_type="工装设备供应商",
            notes="各种规格氧化挂具",
        ),
        Supplier(
            name="工业园物业管理",
            contact="物业中心",
            phone="88888888",
            address="本工业园区",
            business_type="房东",
            notes="厂房租金、物业管理费",
        ),
    ]
    return suppliers


def generate_orders(customers):
    """生成订单数据 - 体现各种计价方式和委外加工"""
    orders = []
    start_date = date.today() - timedelta(days=90)
    order_no = 1

    # 订单模板 - 覆盖所有计价方式和工序组合
    order_templates = [
        # 按米计价 - 铝型材
        {
            "item": "铝型材6063氧化",
            "unit": PricingUnit.METER,
            "quantity_range": (50, 500),
            "price_range": (3, 8),
            "processes": [ProcessType.SANDBLASTING, ProcessType.OXIDATION],
            "outsourced": [ProcessType.SANDBLASTING],
            "unit_name": "米",
        },
        # 按公斤计价 - 铝板材
        {
            "item": "铝板5052氧化",
            "unit": PricingUnit.KILOGRAM,
            "quantity_range": (100, 1000),
            "price_range": (0.5, 1.5),
            "processes": [ProcessType.WIRE_DRAWING, ProcessType.OXIDATION],
            "outsourced": [ProcessType.WIRE_DRAWING],
            "unit_name": "公斤",
        },
        # 按平方米计价 - 铝板大板
        {
            "item": "铝板氧化面板",
            "unit": PricingUnit.SQUARE_METER,
            "quantity_range": (10, 100),
            "price_range": (15, 30),
            "processes": [ProcessType.POLISHING, ProcessType.OXIDATION],
            "outsourced": [ProcessType.POLISHING],
            "unit_name": "平方米",
        },
        # 按件计价 - 小零件
        {
            "item": "不锈钢螺丝M6氧化",
            "unit": PricingUnit.PIECE,
            "quantity_range": (1000, 10000),
            "price_range": (0.05, 0.2),
            "processes": [ProcessType.POLISHING, ProcessType.OXIDATION],
            "outsourced": [],
            "unit_name": "件",
        },
        # 按个计价 - 把手等
        {
            "item": "铝合金把手氧化",
            "unit": PricingUnit.UNIT,
            "quantity_range": (100, 1000),
            "price_range": (2, 8),
            "processes": [
                ProcessType.SANDBLASTING,
                ProcessType.POLISHING,
                ProcessType.OXIDATION,
            ],
            "outsourced": [ProcessType.POLISHING],
            "unit_name": "个",
        },
        # 按条计价 - 铝条
        {
            "item": "铝条6061拉丝氧化",
            "unit": PricingUnit.STRIP,
            "quantity_range": (50, 500),
            "price_range": (1, 5),
            "processes": [ProcessType.WIRE_DRAWING, ProcessType.OXIDATION],
            "outsourced": [],
            "unit_name": "条",
        },
        # 按平方米 - 装饰板材
        {
            "item": "彩色氧化装饰板",
            "unit": PricingUnit.SQUARE_METER,
            "quantity_range": (5, 50),
            "price_range": (50, 100),
            "processes": [
                ProcessType.SANDBLASTING,
                ProcessType.POLISHING,
                ProcessType.OXIDATION,
            ],
            "outsourced": [ProcessType.SANDBLASTING],
            "unit_name": "平方米",
        },
        # 按件 - 电子配件
        {
            "item": "电子外壳氧化",
            "unit": PricingUnit.PIECE,
            "quantity_range": (500, 3000),
            "price_range": (0.3, 1.0),
            "processes": [ProcessType.OXIDATION],
            "outsourced": [],
            "unit_name": "件",
        },
    ]

    for day_offset in range(0, 90, 2):  # 每2天一个订单
        order_date = start_date + timedelta(days=day_offset)
        customer = random.choice(customers)
        template = random.choice(order_templates)

        quantity = Decimal(str(random.randint(*template["quantity_range"])))
        unit_price = Decimal(str(random.uniform(*template["price_range"]))).quantize(
            Decimal("0.01")
        )
        total_amount = quantity * unit_price

        # 计算委外成本（约20-30%）
        outsourcing_cost = Decimal("0")
        if template["outsourced"]:
            outsourcing_cost = total_amount * Decimal(str(random.uniform(0.15, 0.30)))

        # 确定订单状态 - 模拟真实业务场景
        days_since_order = (date.today() - order_date).days
        if days_since_order > 45:
            status = OrderStatus.PAID
            completion_date = order_date + timedelta(days=random.randint(5, 10))
            delivery_date = completion_date + timedelta(days=random.randint(1, 3))
            received_amount = total_amount
        elif days_since_order > 25:
            status = OrderStatus.DELIVERED
            completion_date = order_date + timedelta(days=random.randint(5, 10))
            delivery_date = completion_date + timedelta(days=random.randint(1, 3))
            received_amount = total_amount * Decimal(
                str(random.uniform(0.8, 1.0))
            )  # 已收80-100%
        elif days_since_order > 15:
            status = OrderStatus.COMPLETED
            completion_date = order_date + timedelta(days=random.randint(5, 10))
            delivery_date = None
            received_amount = Decimal("0")
        elif days_since_order > 7:
            status = OrderStatus.IN_PROGRESS
            completion_date = None
            delivery_date = None
            received_amount = Decimal("0")
        else:
            status = OrderStatus.PENDING
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
            outsourcing_cost=outsourcing_cost.quantize(Decimal("0.01")),
            status=status,
            order_date=order_date,
            completion_date=completion_date,
            delivery_date=delivery_date,
            received_amount=received_amount.quantize(Decimal("0.01")),
            notes=f"{template['unit_name']}计价，{template['item']}",
        )

        orders.append(order)
        order_no += 1

    return orders


def generate_incomes(customers, orders):
    """生成收入记录 - 体现收入不一定对应订单的场景"""
    incomes = []

    # 为已收款的订单生成收入记录
    paid_orders = [o for o in orders if o.received_amount > 0]

    for order in paid_orders:
        # 60%一次性收款，40%分多次收款
        if random.random() < 0.6:
            # 一次性收款
            income = Income(
                customer_id=order.customer_id,
                customer_name=order.customer_name,
                amount=order.received_amount,
                bank_type=BankType.G_BANK
                if random.random() < 0.85
                else BankType.N_BANK,
                has_invoice=random.random() < 0.9,
                related_orders=[order.id],
                allocation={order.id: order.received_amount},
                income_date=order.delivery_date
                or order.completion_date
                or order.order_date,
                notes=f"订单{order.order_no}收款",
            )
            incomes.append(income)
        else:
            # 分两次收款（首款+尾款）
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
                income_date=order.order_date + timedelta(days=random.randint(3, 7)),
                notes=f"订单{order.order_no}首款60%",
            )
            incomes.append(income1)

            income2 = Income(
                customer_id=order.customer_id,
                customer_name=order.customer_name,
                amount=second_amount.quantize(Decimal("0.01")),
                bank_type=BankType.N_BANK if random.random() < 0.3 else BankType.G_BANK,
                has_invoice=random.random() < 0.8,
                related_orders=[order.id],
                allocation={order.id: second_amount},
                income_date=order.delivery_date
                or order.completion_date
                or (order.order_date + timedelta(days=20)),
                notes=f"订单{order.order_no}尾款40%",
            )
            incomes.append(income2)

    # 生成预收款（不对应具体订单）
    for _ in range(4):
        customer = random.choice(customers)
        income = Income(
            customer_id=customer.id,
            customer_name=customer.name,
            amount=Decimal(str(random.randint(5000, 30000))),
            bank_type=BankType.G_BANK if random.random() < 0.7 else BankType.N_BANK,
            has_invoice=False,
            related_orders=[],
            allocation={},
            income_date=date.today() - timedelta(days=random.randint(5, 45)),
            notes="预收款，待分配到订单",
        )
        incomes.append(income)

    # 生成其他收入（银行利息等）
    incomes.append(
        Income(
            customer_id="",
            customer_name="银行利息",
            amount=Decimal("128.50"),
            bank_type=BankType.G_BANK,
            has_invoice=False,
            related_orders=[],
            allocation={},
            income_date=date.today() - timedelta(days=30),
            notes="G银行活期利息收入",
        )
    )

    return incomes


def generate_expenses(suppliers, orders):
    """生成支出记录 - 体现各种支出类型"""
    expenses = []
    start_date = date.today() - timedelta(days=90)

    # 1. 固定支出（每月）
    for month_offset in range(3):
        expense_date = start_date + timedelta(days=month_offset * 30)

        # 房租
        expenses.append(
            Expense(
                expense_type=ExpenseType.RENT,
                supplier_name="工业园物业管理",
                amount=Decimal("8500"),
                bank_type=BankType.G_BANK,
                has_invoice=True,
                expense_date=expense_date,
                description="厂房租金",
                notes=f"{expense_date.year}年{expense_date.month}月",
            )
        )

        # 水电费
        expenses.append(
            Expense(
                expense_type=ExpenseType.UTILITIES,
                supplier_name="供电局/自来水公司",
                amount=Decimal(str(random.randint(3500, 5500))),
                bank_type=BankType.G_BANK,
                has_invoice=True,
                expense_date=expense_date + timedelta(days=5),
                description=f"{expense_date.year}年{expense_date.month}月水电费",
                notes="电费为主，水费较少",
            )
        )

        # 工资
        expenses.append(
            Expense(
                expense_type=ExpenseType.SALARY,
                supplier_name="员工工资",
                amount=Decimal(str(random.randint(28000, 35000))),
                bank_type=BankType.G_BANK,
                has_invoice=False,
                expense_date=expense_date + timedelta(days=10),
                description=f"{expense_date.year}年{expense_date.month}月工资",
                notes="6名员工",
            )
        )

    # 2. 化工原料采购
    chemical_supplier = suppliers[0]  # 化工原料贸易公司

    for _ in range(15):
        expense_date = start_date + timedelta(days=random.randint(0, 90))

        # 三酸（硫酸、硝酸、盐酸）
        if random.random() < 0.8:
            expenses.append(
                Expense(
                    expense_type=ExpenseType.ACID_THREE,
                    supplier_id=chemical_supplier.id,
                    supplier_name=chemical_supplier.name,
                    amount=Decimal(str(random.randint(3000, 9000))),
                    bank_type=BankType.G_BANK,
                    has_invoice=True,
                    expense_date=expense_date,
                    description="硫酸、硝酸、盐酸",
                    notes="氧化用主要原料",
                )
            )

        # 片碱
        if random.random() < 0.6:
            expenses.append(
                Expense(
                    expense_type=ExpenseType.CAUSTIC_SODA,
                    supplier_id=chemical_supplier.id,
                    supplier_name=chemical_supplier.name,
                    amount=Decimal(str(random.randint(800, 2000))),
                    bank_type=BankType.G_BANK,
                    has_invoice=True,
                    expense_date=expense_date,
                    description="片碱（氢氧化钠）",
                    notes="除油和中和用",
                )
            )

        # 亚钠
        if random.random() < 0.5:
            expenses.append(
                Expense(
                    expense_type=ExpenseType.SODIUM_SULFITE,
                    supplier_id=chemical_supplier.id,
                    supplier_name=chemical_supplier.name,
                    amount=Decimal(str(random.randint(500, 1500))),
                    bank_type=BankType.G_BANK,
                    has_invoice=True,
                    expense_date=expense_date,
                    description="亚硫酸钠",
                    notes="氧化处理用",
                )
            )

        # 除油剂
        if random.random() < 0.4:
            expenses.append(
                Expense(
                    expense_type=ExpenseType.DEGREASER,
                    supplier_id=chemical_supplier.id,
                    supplier_name=chemical_supplier.name,
                    amount=Decimal(str(random.randint(300, 1000))),
                    bank_type=BankType.G_BANK,
                    has_invoice=True,
                    expense_date=expense_date,
                    description="除油剂",
                    notes="前处理用",
                )
            )

    # 3. 色粉采购
    color_supplier = suppliers[3]
    for _ in range(8):
        expense_date = start_date + timedelta(days=random.randint(0, 90))
        expenses.append(
            Expense(
                expense_type=ExpenseType.COLOR_POWDER,
                supplier_id=color_supplier.id,
                supplier_name=color_supplier.name,
                amount=Decimal(str(random.randint(800, 3000))),
                bank_type=BankType.G_BANK,
                has_invoice=True,
                expense_date=expense_date,
                description="氧化色粉",
                notes=random.choice(["黑色", "金色", "银色", "古铜色", "蓝色"]),
            )
        )

    # 4. 委外加工费用
    sandblast_supplier = suppliers[1]
    polish_supplier = suppliers[2]

    outsourced_orders = [
        o
        for o in orders
        if o.outsourcing_cost > 0
        and o.status in [OrderStatus.COMPLETED, OrderStatus.DELIVERED, OrderStatus.PAID]
    ]

    for order in outsourced_orders[:20]:  # 限制数量
        expense_date = order.order_date + timedelta(days=random.randint(3, 15))

        if ProcessType.SANDBLASTING.value in order.outsourced_processes:
            cost = order.outsourcing_cost * Decimal("0.5")
            expenses.append(
                Expense(
                    expense_type=ExpenseType.OUTSOURCING,
                    supplier_id=sandblast_supplier.id,
                    supplier_name=sandblast_supplier.name,
                    amount=cost.quantize(Decimal("0.01")),
                    bank_type=BankType.G_BANK
                    if random.random() < 0.7
                    else BankType.N_BANK,
                    has_invoice=random.random() < 0.9,
                    related_order_id=order.id,
                    expense_date=expense_date,
                    description=f"订单{order.order_no}喷砂委外",
                    notes="",
                )
            )

        if (
            ProcessType.WIRE_DRAWING.value in order.outsourced_processes
            or ProcessType.POLISHING.value in order.outsourced_processes
        ):
            cost = order.outsourcing_cost * Decimal("0.5")
            expenses.append(
                Expense(
                    expense_type=ExpenseType.OUTSOURCING,
                    supplier_id=polish_supplier.id,
                    supplier_name=polish_supplier.name,
                    amount=cost.quantize(Decimal("0.01")),
                    bank_type=BankType.G_BANK
                    if random.random() < 0.7
                    else BankType.N_BANK,
                    has_invoice=random.random() < 0.9,
                    related_order_id=order.id,
                    expense_date=expense_date,
                    description=f"订单{order.order_no}拉丝/抛光委外",
                    notes="",
                )
            )

    # 5. 挂具采购
    fixture_supplier = suppliers[4]
    for _ in range(3):
        expense_date = start_date + timedelta(days=random.randint(0, 90))
        expenses.append(
            Expense(
                expense_type=ExpenseType.FIXTURES,
                supplier_id=fixture_supplier.id,
                supplier_name=fixture_supplier.name,
                amount=Decimal(str(random.randint(500, 2000))),
                bank_type=BankType.G_BANK,
                has_invoice=True,
                expense_date=expense_date,
                description="氧化挂具",
                notes="各种规格挂篮、挂具",
            )
        )

    # 6. 日常费用（多为N银行/现金）
    for _ in range(20):
        expense_date = start_date + timedelta(days=random.randint(0, 90))
        expense_type = random.choice(
            [
                ExpenseType.DAILY_EXPENSE,
                ExpenseType.DAILY_EXPENSE,
                ExpenseType.DAILY_EXPENSE,
                ExpenseType.DAILY_EXPENSE,
                ExpenseType.OTHER,
            ]
        )
        descriptions = [
            "办公用品",
            "维修费",
            "运输费",
            "招待费",
            "通讯费",
            "快递费",
            "停车费",
            "午餐补贴",
        ]

        expenses.append(
            Expense(
                expense_type=expense_type,
                supplier_name="",
                amount=Decimal(str(random.randint(50, 800))),
                bank_type=BankType.N_BANK if random.random() < 0.6 else BankType.G_BANK,
                has_invoice=random.random() < 0.3,
                expense_date=expense_date,
                description=random.choice(descriptions),
                notes="",
            )
        )

    return expenses


def generate_bank_accounts():
    """生成银行账户"""
    return [
        BankAccount(
            bank_type=BankType.G_BANK,
            account_name="G银行对公账户",
            account_number="6222****1234",
            balance=Decimal("180000"),
            notes="主要用于有票据的正式交易",
        ),
        BankAccount(
            bank_type=BankType.N_BANK,
            account_name="N银行现金账户（微信绑定）",
            account_number="6228****5678",
            balance=Decimal("45000"),
            notes="与微信结合，用于现金交易、小额支付",
        ),
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
            notes="已匹配到收入记录",
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
            notes="已匹配到支出记录",
        )
        transactions.append(transaction)

    # 按日期排序
    transactions.sort(key=lambda t: t.transaction_date)

    return transactions


def serialize_customer(customer):
    """序列化客户对象"""
    data = customer.__dict__.copy()
    data["credit_limit"] = float(customer.credit_limit)
    data["created_at"] = customer.created_at.isoformat()
    return data


def serialize_supplier(supplier):
    """序列化供应商对象"""
    data = supplier.__dict__.copy()
    data["created_at"] = supplier.created_at.isoformat()
    return data


def serialize_bank_account(account):
    """序列化银行账户对象"""
    data = account.__dict__.copy()
    data["bank_type"] = account.bank_type.value
    data["balance"] = float(account.balance)
    return data


def serialize_order(order):
    """序列化订单对象"""
    data = order.__dict__.copy()
    data["pricing_unit"] = order.pricing_unit.value
    data["processes"] = [p.value for p in order.processes]
    data["status"] = order.status.value
    data["order_date"] = order.order_date.isoformat()
    data["completion_date"] = (
        order.completion_date.isoformat() if order.completion_date else None
    )
    data["delivery_date"] = (
        order.delivery_date.isoformat() if order.delivery_date else None
    )
    data["total_amount"] = float(order.total_amount)
    data["outsourcing_cost"] = float(order.outsourcing_cost)
    data["received_amount"] = float(order.received_amount)
    data["quantity"] = float(order.quantity)
    data["unit_price"] = float(order.unit_price)
    data["created_at"] = order.created_at.isoformat()
    data["updated_at"] = order.updated_at.isoformat()
    return data


def serialize_income(income):
    """序列化收入对象"""
    data = income.__dict__.copy()
    data["bank_type"] = income.bank_type.value
    data["amount"] = float(income.amount)
    data["allocation"] = {k: float(v) for k, v in income.allocation.items()}
    data["income_date"] = income.income_date.isoformat()
    data["created_at"] = income.created_at.isoformat()
    return data


def serialize_expense(expense):
    """序列化支出对象"""
    data = expense.__dict__.copy()
    data["expense_type"] = expense.expense_type.value
    data["bank_type"] = expense.bank_type.value
    data["amount"] = float(expense.amount)
    data["expense_date"] = expense.expense_date.isoformat()
    data["created_at"] = expense.created_at.isoformat()
    return data


def serialize_transaction(transaction):
    """序列化银行交易对象"""
    data = transaction.__dict__.copy()
    data["bank_type"] = transaction.bank_type.value
    data["amount"] = float(transaction.amount)
    data["transaction_date"] = transaction.transaction_date.isoformat()
    data["created_at"] = transaction.created_at.isoformat()
    return data


def save_demo_data(data):
    """保存示例数据到文件"""
    output_dir = Path("demo_data_v20")
    output_dir.mkdir(exist_ok=True)

    output_file = output_dir / "oxidation_factory_demo_data.json"

    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    print_ok(f"数据已保存到: {output_file}")


if __name__ == "__main__":
    try:
        generate_demo_data()
    except Exception as e:
        print_error(f"生成数据时出错: {e}")
        import traceback

        traceback.print_exc()
