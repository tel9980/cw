#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
氧化加工厂财务系统 V2.4 - 小企业专用模拟数据生成器
专为小企业小会计设计，演示真实业务场景：
- 客户付款不一定一一对应订单
- 供应商付款不一定一一对应支出
- G银行大多有票，N银行与微信结合作为现金
- 权责发生制实际应用
- 小会计的日常工作模拟
"""

import sys
import random
from datetime import date, datetime, timedelta
from decimal import Decimal
from pathlib import Path

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from oxidation_finance_v20.models.business_models import (
    Customer, Supplier, ProcessingOrder, Income, Expense,
    BankAccount, BankTransaction, PricingUnit, ProcessType,
    OrderStatus, ExpenseType, BankType
)
from oxidation_finance_v20.database.db_manager import DatabaseManager
from oxidation_finance_v20.business.finance_manager import FinanceManager
from oxidation_finance_v20.business.voucher_manager import VoucherManager


def generate_small_business_demo():
    """生成小企业真实业务场景的模拟数据"""
    print("=" * 70)
    print("🏭 氧化加工厂财务系统 V2.4 - 小企业模拟数据生成")
    print("=" * 70)
    print("\n📋 业务场景说明：")
    print("  - 4个核心客户，付款不一定一一对应订单")
    print("  - 5个主要供应商，付款不一定一一对应支出")
    print("  - G银行用于有票正式交易")
    print("  - N银行作为现金等价物（微信现金混合）")
    print("  - 包含预付款、预收款场景")
    print("  - 包含延期付款场景")
    print("  - 包含委外加工场景")
    print("")

    # 初始化数据库
    db_path = Path(__file__).parent.parent / "oxidation_finance_demo_ready.db"
    db = DatabaseManager(str(db_path))
    db.connect()

    finance_manager = FinanceManager(db)
    voucher_manager = VoucherManager(db)

    # 清空并重建表（保留原有表结构）
    print("🔧 初始化数据库...")

    # ========== 1. 创建客户 ==========
    print("\n👥 创建客户数据...")
    customers = []
    customer_data = [
        ("宏达五金制品厂", "张经理", "13800138001"),
        ("精密机械配件公司", "王厂长", "13800138002"),
        ("创新电子科技", "李采购", "13800138003"),
        ("顺达金属表面处理", "赵总", "13800138004"),
    ]

    for name, contact, phone in customer_data:
        customer = Customer(name=name, contact=contact, phone=phone)
        db.save_customer(customer)
        customers.append(customer)
        print(f"  ✓ {name}")

    # ========== 2. 创建供应商 ==========
    print("\n🏪 创建供应商数据...")
    suppliers = []
    supplier_data = [
        ("化工原料批发部", ExpenseType.ACID_THREE),
        ("化工助剂有限公司", ExpenseType.CAUSTIC_SODA),
        ("色粉颜料专营", ExpenseType.COLOR_POWDER),
        ("包装材料制品厂", ExpenseType.OTHER),
        ("诚信委外加工厂", ExpenseType.OUTSOURCING),
    ]

    for name, expense_type in supplier_data:
        supplier = Supplier(name=name, business_type=expense_type.value)
        db.save_supplier(supplier)
        suppliers.append(supplier)
        print(f"  ✓ {name}")

    # ========== 3. 创建订单（45天业务周期） ==========
    print("\n📝 创建订单数据（模拟45天业务周期）...")
    today = date.today()
    start_date = today - timedelta(days=45)

    orders = []
    pricing_units = [PricingUnit.PIECE, PricingUnit.PIECE, PricingUnit.PIECE, 
                     PricingUnit.METER, PricingUnit.KILOGRAM]

    order_descriptions = [
        "铝件氧化", "不锈钢着色", "五金件钝化", "锌合金镀彩",
        "铁件发黑", "铝型材阳极氧化", "精密零件硬质氧化"
    ]

    for day_offset in range(45):
        order_date = start_date + timedelta(days=day_offset)
        
        # 每天随机生成0-3个订单
        num_orders = random.randint(0, 3)
        
        for _ in range(num_orders):
            customer = random.choice(customers)
            quantity = Decimal(str(random.randint(50, 500)))
            unit_price = Decimal(str(random.randint(5, 50)))
            total_amount = quantity * unit_price
            
            processes = []
            if random.random() > 0.3:
                processes.append(ProcessType.OXIDATION)
            if random.random() > 0.6:
                processes.append(ProcessType.SANDBLASTING)
            if random.random() > 0.8:
                processes.append(ProcessType.POLISHING)
            
            order = ProcessingOrder(
                order_no=f"ORD{order_date.strftime('%Y%m%d')}{random.randint(100, 999)}",
                customer_id=customer.id,
                customer_name=customer.name,
                item_description=random.choice(order_descriptions),
                quantity=quantity,
                pricing_unit=random.choice(pricing_units),
                unit_price=unit_price,
                processes=processes,
                total_amount=total_amount,
                outsourcing_cost=Decimal("0"),
                status=OrderStatus.PENDING,
                order_date=order_date,
            )
            
            # 随机设置一些订单为已完成或已收款
            if day_offset < 30:
                if random.random() > 0.5:
                    order.status = OrderStatus.COMPLETED
                    order.completion_date = order_date + timedelta(days=random.randint(3, 10))
            
            db.save_order(order)
            orders.append(order)
    
    print(f"  ✓ 已生成 {len(orders)} 个订单")

    # ========== 4. 创建收入（客户付款，非一一对应） ==========
    print("\n💰 创建收入数据（模拟非一一对应付款）...")
    incomes = []
    
    for day_offset in range(45):
        income_date = start_date + timedelta(days=day_offset)
        
        # 每天0-2笔收入
        num_incomes = random.randint(0, 2)
        
        for _ in range(num_incomes):
            customer = random.choice(customers)
            
            # 金额随机：300-20000
            amount = Decimal(str(random.randint(300, 20000)))
            
            # G银行70%有票，N银行30%（现金）
            if random.random() < 0.7:
                bank_type = BankType.G_BANK
                has_invoice = random.random() < 0.8  # G银行大多有票
            else:
                bank_type = BankType.N_BANK
                has_invoice = random.random() < 0.2  # N银行很少有票
            
            # 找客户未付款订单
            customer_orders = [o for o in orders if o.customer_id == customer.id and 
                             o.received_amount < o.total_amount]
            
            # 权责发生制：业务发生日期和付款日期可能不同
            occurrence_date = income_date
            payment_date = None
            
            if customer_orders and random.random() > 0.3:
                # 选择较早的订单
                customer_orders.sort(key=lambda o: o.order_date)
                target_order = customer_orders[0]
                occurrence_date = target_order.order_date
                
                # 随机决定是否是预付款或延期付款
                if random.random() < 0.15:  # 预付款
                    payment_date = occurrence_date - timedelta(days=random.randint(2, 7))
                    income = finance_manager.record_accrual_income(
                        customer_id=customer.id,
                        customer_name=customer.name,
                        amount=min(amount, target_order.total_amount - target_order.received_amount),
                        bank_type=bank_type,
                        occurrence_date=occurrence_date,
                        payment_date=payment_date,
                        has_invoice=has_invoice,
                        notes=f"对应订单: {target_order.order_no}"
                    )
                elif random.random() < 0.2:  # 延期付款
                    payment_date = occurrence_date + timedelta(days=random.randint(15, 30))
                    income = finance_manager.record_accrual_income(
                        customer_id=customer.id,
                        customer_name=customer.name,
                        amount=min(amount, target_order.total_amount - target_order.received_amount),
                        bank_type=bank_type,
                        occurrence_date=occurrence_date,
                        payment_date=payment_date,
                        has_invoice=has_invoice,
                        notes=f"对应订单: {target_order.order_no}"
                    )
                else:
                    # 正常付款
                    income = finance_manager.record_income(
                        customer_id=customer.id,
                        customer_name=customer.name,
                        amount=min(amount, target_order.total_amount - target_order.received_amount),
                        bank_type=bank_type,
                        income_date=occurrence_date,
                        has_invoice=has_invoice,
                        notes=f"对应订单: {target_order.order_no}"
                    )
                
                # 分配到订单（演示非一一对应）
                if target_order.total_amount - target_order.received_amount > amount:
                    # 部分分配
                    finance_manager.allocate_payment_to_orders(
                        income.id,
                        {target_order.id: amount}
                    )
                else:
                    # 完全分配
                    to_allocate = target_order.total_amount - target_order.received_amount
                    if to_allocate > 0:
                        finance_manager.allocate_payment_to_orders(
                            income.id,
                            {target_order.id: to_allocate}
                        )
            else:
                # 不关联特定订单（预收款）
                income = finance_manager.record_accrual_income(
                    customer_id=customer.id,
                    customer_name=customer.name,
                    amount=amount,
                    bank_type=bank_type,
                    occurrence_date=occurrence_date,
                    has_invoice=has_invoice,
                    notes="预收款，待后续分配"
                )
            
            incomes.append(income)
            print(f"  ✓ {customer.name} {amount}元 {'G银行' if bank_type == BankType.G_BANK else 'N银行'} {'有票' if has_invoice else '无票'}")

    # ========== 5. 创建支出（供应商付款，非一一对应） ==========
    print("\n💸 创建支出数据（模拟非一一对应付款）...")
    expenses = []
    
    expense_types = [
        (ExpenseType.ACID_THREE, "化工原料批发部"),
        (ExpenseType.CAUSTIC_SODA, "化工助剂有限公司"),
        (ExpenseType.COLOR_POWDER, "色粉颜料专营"),
        (ExpenseType.DEGREASER, "化工原料批发部"),
        (ExpenseType.FIXTURES, "包装材料制品厂"),
        (ExpenseType.OUTSOURCING, "诚信委外加工厂"),
        (ExpenseType.RENT, "房东"),
        (ExpenseType.SALARY, "员工"),
        (ExpenseType.UTILITIES, "电力公司"),
        (ExpenseType.DAILY_EXPENSE, "其他"),
    ]

    for day_offset in range(45):
        expense_date = start_date + timedelta(days=day_offset)
        
        # 每天1-4笔支出
        num_expenses = random.randint(1, 4)
        
        for _ in range(num_expenses):
            exp_type, supplier_name = random.choice(expense_types)
            
            amount = Decimal(str(random.randint(100, 8000)))
            
            # G银行70%有票，N银行30%现金
            if random.random() < 0.7:
                bank_type = BankType.G_BANK
                has_invoice = random.random() < 0.85
            else:
                bank_type = BankType.N_BANK
                has_invoice = random.random() < 0.15
            
            # 找对应供应商
            supplier = next((s for s in suppliers if s.name == supplier_name), None)
            supplier_id = supplier.id if supplier else None
            
            # 权责发生制
            occurrence_date = expense_date
            payment_date = None
            
            if random.random() < 0.1:  # 预付款
                payment_date = occurrence_date - timedelta(days=random.randint(3, 10))
                expense = finance_manager.record_accrual_expense(
                    expense_type=exp_type,
                    amount=amount,
                    bank_type=bank_type,
                    occurrence_date=occurrence_date,
                    payment_date=payment_date,
                    supplier_id=supplier_id,
                    supplier_name=supplier_name,
                    has_invoice=has_invoice,
                    description=f"{exp_type.value}采购"
                )
            elif random.random() < 0.15:  # 延期付款
                payment_date = occurrence_date + timedelta(days=random.randint(20, 40))
                expense = finance_manager.record_accrual_expense(
                    expense_type=exp_type,
                    amount=amount,
                    bank_type=bank_type,
                    occurrence_date=occurrence_date,
                    payment_date=payment_date,
                    supplier_id=supplier_id,
                    supplier_name=supplier_name,
                    has_invoice=has_invoice,
                    description=f"{exp_type.value}采购"
                )
            else:
                # 正常支出
                expense = finance_manager.record_expense(
                    expense_type=exp_type,
                    amount=amount,
                    bank_type=bank_type,
                    expense_date=expense_date,
                    supplier_id=supplier_id,
                    supplier_name=supplier_name,
                    has_invoice=has_invoice,
                    description=f"{exp_type.value}采购"
                )
            
            expenses.append(expense)
            print(f"  ✓ {supplier_name} {exp_type.value} {amount}元 {'G银行' if bank_type == BankType.G_BANK else 'N银行'}")

    # ========== 6. 创建银行账户 ==========
    print("\n🏦 创建银行账户...")
    g_bank = BankAccount(
        bank_type=BankType.G_BANK,
        account_name="公司基本户（G银行）",
        account_number="G-7890123456",
        balance=Decimal("50000"),
        notes="用于有票的正式交易"
    )
    n_bank = BankAccount(
        bank_type=BankType.N_BANK,
        account_name="微信现金户（N银行）",
        account_number="N-1234567890",
        balance=Decimal("20000"),
        notes="作为现金等价物处理"
    )
    db.save_bank_account(g_bank)
    db.save_bank_account(n_bank)
    print("  ✓ G银行（有票）和 N银行（现金）账户已创建")

    # ========== 7. 自动生成一些会计凭证 ==========
    print("\n📜 自动生成会计凭证（演示小企业会计准则）...")
    accounting_period = f"{today.year}年{today.month}月"
    
    # 为最近的收入生成凭证
    recent_incomes = [i for i in incomes if i.income_date > today - timedelta(days=30)]
    for income in recent_incomes[:10]:  # 只处理部分，避免太多
        try:
            voucher = voucher_manager.create_voucher_from_income(
                income=income,
                accounting_period=accounting_period
            )
            print(f"  ✓ 收入凭证: {income.customer_name} {income.amount}元")
        except Exception as e:
            print(f"  ⚠ 跳过：{e}")

    # ========== 8. 统计输出 ==========
    print("\n" + "=" * 70)
    print("📊 数据生成完成！统计信息：")
    print("=" * 70)
    
    total_income = sum(i.amount for i in incomes)
    total_expense = sum(e.amount for e in expenses)
    
    g_income = sum(i.amount for i in incomes if i.bank_type == BankType.G_BANK)
    n_income = sum(i.amount for i in incomes if i.bank_type == BankType.N_BANK)
    g_expense = sum(e.amount for e in expenses if e.bank_type == BankType.G_BANK)
    n_expense = sum(e.amount for e in expenses if e.bank_type == BankType.N_BANK)
    
    print(f"\n📝 核心业务数据：")
    print(f"  客户数: {len(customers)}")
    print(f"  供应商数: {len(suppliers)}")
    print(f"  订单数: {len(orders)}")
    print(f"  收入记录: {len(incomes)}")
    print(f"  支出记录: {len(expenses)}")
    
    print(f"\n💰 资金统计：")
    print(f"  总收入: ¥{total_income:,.2f}")
    print(f"    - G银行: ¥{g_income:,.2f} (有票正式交易)")
    print(f"    - N银行: ¥{n_income:,.2f} (微信现金)")
    print(f"  总支出: ¥{total_expense:,.2f}")
    print(f"    - G银行: ¥{g_expense:,.2f} (有票正式交易)")
    print(f"    - N银行: ¥{n_expense:,.2f} (微信现金)")
    print(f"  净现金流: ¥{total_income - total_expense:,.2f}")
    
    print(f"\n📋 业务特点演示：")
    print(f"  ✅ 收付款非一一对应")
    print(f"  ✅ 预收款/预付款场景")
    print(f"  ✅ 延期收付款场景")
    print(f"  ✅ 权责发生制应用")
    print(f"  ✅ G/N银行分离（有票/现金）")
    print(f"  ✅ 委外加工场景")
    
    print("\n" + "=" * 70)
    print("🎯 使用提示：")
    print("=" * 70)
    print("  1. 启动Web界面查看数据可视化")
    print("  2. 使用统一启动器进行日常操作")
    print("  3. 查看会计凭证和财务报表")
    print("  4. 参考模拟数据的业务场景")
    print("\n🚀 模拟数据准备完毕，系统可以开始使用！")
    
    db.close()
    return True


if __name__ == "__main__":
    generate_small_business_demo()
