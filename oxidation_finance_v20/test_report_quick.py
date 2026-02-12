#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
快速测试报表管理器
"""

import sys
from pathlib import Path
from decimal import Decimal
from datetime import date

# 添加项目根目录到路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from database.db_manager import DatabaseManager
from business.finance_manager import FinanceManager
from business.order_manager import OrderManager
from business.outsourced_processing_manager import OutsourcedProcessingManager
from reports.report_manager import ReportManager, ReportPeriod
from models.business_models import (
    Customer, Supplier, BankType, ExpenseType, PricingUnit
)


def test_report_manager():
    """测试报表管理器基本功能"""
    print("=" * 60)
    print("测试报表管理器")
    print("=" * 60)
    
    # 创建数据库管理器
    db = DatabaseManager(":memory:")
    finance_manager = FinanceManager(db)
    order_manager = OrderManager(db)
    outsourced_manager = OutsourcedProcessingManager(db)
    report_manager = ReportManager(db)
    
    # 创建测试数据
    print("\n1. 创建测试数据...")
    
    # 创建客户
    customer = Customer(
        name="测试客户A",
        contact="张三",
        phone="13800138000"
    )
    db.save_customer(customer)
    print(f"   ✓ 创建客户: {customer.name}")
    
    # 创建供应商
    supplier = Supplier(
        name="测试供应商B",
        contact="李四",
        phone="13900139000",
        business_type="委外加工"
    )
    db.save_supplier(supplier)
    print(f"   ✓ 创建供应商: {supplier.name}")
    
    # 创建银行账户
    g_bank = finance_manager.create_bank_account(
        bank_type=BankType.G_BANK,
        account_name="G银行账户",
        initial_balance=Decimal("50000")
    )
    print(f"   ✓ 创建G银行账户，初始余额: {g_bank.balance}")
    
    n_bank = finance_manager.create_bank_account(
        bank_type=BankType.N_BANK,
        account_name="N银行账户",
        initial_balance=Decimal("30000")
    )
    print(f"   ✓ 创建N银行账户，初始余额: {n_bank.balance}")
    
    # 创建订单
    order = order_manager.create_order(
        customer_id=customer.id,
        customer_name=customer.name,
        item_description="铝型材氧化处理",
        quantity=Decimal("1000"),
        pricing_unit=PricingUnit.PIECE,
        unit_price=Decimal("5.0"),
        processes=["喷砂", "氧化"],
        order_date=date(2024, 1, 15)
    )
    print(f"   ✓ 创建订单: {order.order_no}, 金额: {order.total_amount}")
    
    # 记录收入
    income = finance_manager.record_income(
        customer_id=customer.id,
        customer_name=customer.name,
        amount=Decimal("3000"),
        bank_type=BankType.G_BANK,
        income_date=date(2024, 1, 20),
        has_invoice=True
    )
    print(f"   ✓ 记录收入: {income.amount}")
    
    # 分配付款
    finance_manager.allocate_payment_to_orders(
        income_id=income.id,
        allocations={order.id: Decimal("3000")}
    )
    print(f"   ✓ 分配付款到订单")
    
    # 记录支出
    expense1 = finance_manager.record_expense(
        expense_type=ExpenseType.ACID_THREE,
        amount=Decimal("800"),
        bank_type=BankType.G_BANK,
        expense_date=date(2024, 1, 10),
        supplier_name="化工供应商",
        description="硫酸采购"
    )
    print(f"   ✓ 记录支出(三酸): {expense1.amount}")
    
    expense2 = finance_manager.record_expense(
        expense_type=ExpenseType.RENT,
        amount=Decimal("5000"),
        bank_type=BankType.N_BANK,
        expense_date=date(2024, 1, 5),
        description="1月份房租"
    )
    print(f"   ✓ 记录支出(房租): {expense2.amount}")
    
    expense3 = finance_manager.record_expense(
        expense_type=ExpenseType.SALARY,
        amount=Decimal("8000"),
        bank_type=BankType.N_BANK,
        expense_date=date(2024, 1, 25),
        description="员工工资"
    )
    print(f"   ✓ 记录支出(工资): {expense3.amount}")
    
    # 委外加工
    outsourced = outsourced_manager.create_outsourced_processing(
        order_id=order.id,
        supplier_id=supplier.id,
        supplier_name=supplier.name,
        process_type="抛光",
        process_description="表面抛光处理",
        quantity=Decimal("1000"),
        unit_price=Decimal("0.5"),
        process_date=date(2024, 1, 18)
    )
    print(f"   ✓ 创建委外加工: {outsourced.total_cost}")
    
    expense4 = finance_manager.record_expense(
        expense_type=ExpenseType.OUTSOURCING,
        amount=Decimal("500"),
        bank_type=BankType.G_BANK,
        expense_date=date(2024, 1, 22),
        supplier_id=supplier.id,
        supplier_name=supplier.name,
        related_order_id=order.id,
        description="抛光委外费用"
    )
    print(f"   ✓ 记录委外费用: {expense4.amount}")
    
    # 记录银行交易
    finance_manager.record_bank_transaction(
        bank_type=BankType.G_BANK,
        amount=Decimal("3000"),
        transaction_date=date(2024, 1, 20),
        counterparty="测试客户A",
        description="收到货款",
        is_income=True
    )
    print(f"   ✓ 记录银行交易(收入): 3000")
    
    finance_manager.record_bank_transaction(
        bank_type=BankType.G_BANK,
        amount=Decimal("800"),
        transaction_date=date(2024, 1, 10),
        counterparty="化工供应商",
        description="采购原料",
        is_income=False
    )
    print(f"   ✓ 记录银行交易(支出): 800")
    
    # 测试资产负债表
    print("\n2. 测试资产负债表...")
    balance_sheet = report_manager.generate_balance_sheet(
        end_date=date(2024, 1, 31),
        period_type=ReportPeriod.MONTHLY
    )
    
    print(f"   报表名称: {balance_sheet['report_name']}")
    print(f"   报表日期: {balance_sheet['report_date']}")
    print(f"   期间类型: {balance_sheet['period_type']}")
    print(f"\n   资产:")
    print(f"     现金及银行存款: {balance_sheet['assets']['current_assets']['cash_and_bank']}")
    print(f"     应收账款: {balance_sheet['assets']['current_assets']['accounts_receivable']}")
    print(f"     总资产: {balance_sheet['assets']['total_assets']}")
    print(f"\n   负债:")
    print(f"     应付账款: {balance_sheet['liabilities']['current_liabilities']['accounts_payable']}")
    print(f"     总负债: {balance_sheet['liabilities']['total_liabilities']}")
    print(f"\n   所有者权益:")
    print(f"     留存收益: {balance_sheet['equity']['retained_earnings']}")
    print(f"     总权益: {balance_sheet['equity']['total_equity']}")
    print(f"\n   会计恒等式检查:")
    print(f"     资产: {balance_sheet['balance_check']['assets']}")
    print(f"     负债+权益: {balance_sheet['balance_check']['liabilities_and_equity']}")
    print(f"     差额: {balance_sheet['balance_check']['difference']}")
    print(f"     是否平衡: {balance_sheet['balance_check']['is_balanced']}")
    
    assert balance_sheet['balance_check']['is_balanced'], "资产负债表不平衡!"
    print("   ✓ 资产负债表测试通过")
    
    # 测试利润表
    print("\n3. 测试利润表...")
    income_statement = report_manager.generate_income_statement(
        start_date=date(2024, 1, 1),
        end_date=date(2024, 1, 31),
        period_type=ReportPeriod.MONTHLY
    )
    
    print(f"   报表名称: {income_statement['report_name']}")
    print(f"   期间: {income_statement['period']['start_date']} 至 {income_statement['period']['end_date']}")
    print(f"\n   收入:")
    print(f"     营业收入: {income_statement['revenue']['operating_revenue']}")
    print(f"     G银行收入: {income_statement['revenue']['by_bank_type']['g_bank']}")
    print(f"     N银行收入: {income_statement['revenue']['by_bank_type']['n_bank']}")
    print(f"\n   成本:")
    print(f"     营业成本: {income_statement['cost_of_goods_sold']['total']}")
    print(f"     原料成本: {income_statement['cost_of_goods_sold']['materials']['acid_three']}")
    print(f"     委外成本: {income_statement['cost_of_goods_sold']['outsourcing']}")
    print(f"\n   毛利润:")
    print(f"     金额: {income_statement['gross_profit']['amount']}")
    print(f"     毛利率: {income_statement['gross_profit']['margin_percent']}%")
    print(f"\n   营业费用:")
    print(f"     总计: {income_statement['operating_expenses']['total']}")
    print(f"     房租: {income_statement['operating_expenses']['breakdown']['rent']}")
    print(f"     工资: {income_statement['operating_expenses']['breakdown']['wages']}")
    print(f"\n   净利润:")
    print(f"     金额: {income_statement['net_profit']['amount']}")
    print(f"     净利率: {income_statement['net_profit']['margin_percent']}%")
    
    assert income_statement['revenue']['operating_revenue'] == Decimal("3000"), "收入金额不正确"
    print("   ✓ 利润表测试通过")
    
    # 测试现金流量表
    print("\n4. 测试现金流量表...")
    cash_flow = report_manager.generate_cash_flow_statement(
        start_date=date(2024, 1, 1),
        end_date=date(2024, 1, 31),
        period_type=ReportPeriod.MONTHLY
    )
    
    print(f"   报表名称: {cash_flow['report_name']}")
    print(f"   期间: {cash_flow['period']['start_date']} 至 {cash_flow['period']['end_date']}")
    print(f"\n   经营活动现金流:")
    print(f"     现金流入: {cash_flow['operating_activities']['cash_inflow']}")
    print(f"     现金流出: {cash_flow['operating_activities']['cash_outflow']}")
    print(f"     净现金流: {cash_flow['operating_activities']['net_cash_flow']}")
    print(f"\n   按银行类型:")
    print(f"     G银行净流入: {cash_flow['operating_activities']['by_bank_type']['g_bank']['net']}")
    print(f"     N银行净流入: {cash_flow['operating_activities']['by_bank_type']['n_bank']['net']}")
    print(f"\n   现金余额:")
    print(f"     期初余额: {cash_flow['cash_balance']['beginning_balance']}")
    print(f"     期末余额: {cash_flow['cash_balance']['ending_balance']}")
    print(f"     净变化: {cash_flow['cash_balance']['net_change']}")
    
    assert cash_flow['operating_activities']['cash_inflow'] > 0, "现金流入应大于0"
    print("   ✓ 现金流量表测试通过")
    
    # 测试月度报告
    print("\n5. 测试月度报告...")
    monthly_report = report_manager.generate_monthly_report(2024, 1)
    
    print(f"   报告类型: {monthly_report['report_type']}")
    print(f"   年份: {monthly_report['year']}")
    print(f"   月份: {monthly_report['month']}")
    print(f"   包含报表: balance_sheet, income_statement, cash_flow_statement")
    
    assert "balance_sheet" in monthly_report, "月度报告应包含资产负债表"
    assert "income_statement" in monthly_report, "月度报告应包含利润表"
    assert "cash_flow_statement" in monthly_report, "月度报告应包含现金流量表"
    print("   ✓ 月度报告测试通过")
    
    # 测试季度报告
    print("\n6. 测试季度报告...")
    quarterly_report = report_manager.generate_quarterly_report(2024, 1)
    
    print(f"   报告类型: {quarterly_report['report_type']}")
    print(f"   年份: {quarterly_report['year']}")
    print(f"   季度: {quarterly_report['quarter']}")
    print(f"   期间: {quarterly_report['period']['start_date']} 至 {quarterly_report['period']['end_date']}")
    
    assert quarterly_report['period']['start_date'] == date(2024, 1, 1), "季度开始日期不正确"
    assert quarterly_report['period']['end_date'] == date(2024, 3, 31), "季度结束日期不正确"
    print("   ✓ 季度报告测试通过")
    
    # 测试年度报告
    print("\n7. 测试年度报告...")
    annual_report = report_manager.generate_annual_report(2024)
    
    print(f"   报告类型: {annual_report['report_type']}")
    print(f"   年份: {annual_report['year']}")
    print(f"   期间: {annual_report['period']['start_date']} 至 {annual_report['period']['end_date']}")
    
    assert annual_report['period']['start_date'] == date(2024, 1, 1), "年度开始日期不正确"
    assert annual_report['period']['end_date'] == date(2024, 12, 31), "年度结束日期不正确"
    print("   ✓ 年度报告测试通过")
    
    # 清理
    db.close()
    
    print("\n" + "=" * 60)
    print("✓ 所有测试通过!")
    print("=" * 60)


if __name__ == "__main__":
    try:
        test_report_manager()
    except Exception as e:
        print(f"\n✗ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        exit(1)
