#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Task 7.3 测试脚本 - 应收应付账款报表
"""

from decimal import Decimal
from datetime import date
from database.db_manager import DatabaseManager
from business.finance_manager import FinanceManager
from business.order_manager import OrderManager
from business.outsourced_processing_manager import OutsourcedProcessingManager
from reports.report_manager import ReportManager
from models.business_models import (
    Customer, Supplier, BankType, ExpenseType, PricingUnit
)


def test_accounts_receivable_report():
    """测试应收账款报表"""
    print("\n" + "="*60)
    print("测试应收账款报表")
    print("="*60)
    
    # 创建数据库和管理器
    db = DatabaseManager(":memory:")
    db.connect()
    
    finance_mgr = FinanceManager(db)
    order_mgr = OrderManager(db)
    report_mgr = ReportManager(db)
    
    # 创建客户
    customer = Customer(name="测试客户A", contact="张三", phone="13800138000")
    db.save_customer(customer)
    
    # 创建订单（部分付款）
    order1 = order_mgr.create_order(
        customer_id=customer.id,
        customer_name=customer.name,
        item_description="铝型材氧化",
        quantity=Decimal("1000"),
        pricing_unit=PricingUnit.PIECE,
        unit_price=Decimal("5.0"),
        processes=["喷砂", "氧化"],
        order_date=date(2024, 1, 10)
    )
    print(f"✓ 创建订单: {order1.order_no}, 总金额: {order1.total_amount}")
    
    # 记录部分收款
    income = finance_mgr.record_income(
        customer_id=customer.id,
        customer_name=customer.name,
        amount=Decimal("3000"),
        bank_type=BankType.G_BANK,
        income_date=date(2024, 1, 20)
    )
    
    # 分配付款
    finance_mgr.allocate_payment_to_orders(
        income_id=income.id,
        allocations={order1.id: Decimal("3000")}
    )
    print(f"✓ 记录收款: {income.amount}, 已收: {order1.received_amount}")
    
    # 生成应收账款报表
    ar_report = report_mgr.generate_accounts_receivable_report(
        as_of_date=date(2024, 1, 31),
        include_aging=True
    )
    
    print(f"\n应收账款报表:")
    print(f"  报表名称: {ar_report['report_name']}")
    print(f"  截止日期: {ar_report['as_of_date']}")
    print(f"  应收总额: {ar_report['summary']['total_receivable']}")
    print(f"  客户数量: {ar_report['summary']['customer_count']}")
    print(f"  订单数量: {ar_report['summary']['order_count']}")
    
    if ar_report['aging_analysis']:
        print(f"\n  账龄分析:")
        for bucket, amount in ar_report['aging_analysis']['buckets'].items():
            if amount > 0:
                percentage = ar_report['aging_analysis']['percentages'][bucket]
                print(f"    {bucket}: {amount} ({percentage}%)")
    
    # 验证结果
    assert ar_report['summary']['total_receivable'] == Decimal("2000"), "应收账款总额错误"
    assert ar_report['summary']['customer_count'] == 1, "客户数量错误"
    assert ar_report['summary']['order_count'] == 1, "订单数量错误"
    
    print("\n✓ 应收账款报表测试通过!")
    db.close()


def test_accounts_payable_report():
    """测试应付账款报表"""
    print("\n" + "="*60)
    print("测试应付账款报表")
    print("="*60)
    
    # 创建数据库和管理器
    db = DatabaseManager(":memory:")
    db.connect()
    
    finance_mgr = FinanceManager(db)
    order_mgr = OrderManager(db)
    outsourced_mgr = OutsourcedProcessingManager(db)
    report_mgr = ReportManager(db)
    
    # 创建客户和供应商
    customer = Customer(name="测试客户B", contact="李四")
    db.save_customer(customer)
    
    supplier = Supplier(name="测试供应商A", contact="王五", business_type="委外加工")
    db.save_supplier(supplier)
    
    # 创建订单
    order = order_mgr.create_order(
        customer_id=customer.id,
        customer_name=customer.name,
        item_description="不锈钢抛光",
        quantity=Decimal("500"),
        pricing_unit=PricingUnit.PIECE,
        unit_price=Decimal("10.0"),
        processes=["抛光", "氧化"],
        order_date=date(2024, 1, 15)
    )
    print(f"✓ 创建订单: {order.order_no}, 总金额: {order.total_amount}")
    
    # 创建委外加工（部分付款）
    outsourced = outsourced_mgr.create_processing(
        order_id=order.id,
        supplier_id=supplier.id,
        supplier_name=supplier.name,
        process_type="抛光",
        process_description="表面抛光处理",
        quantity=Decimal("500"),
        unit_price=Decimal("2.0"),
        process_date=date(2024, 1, 18)
    )
    print(f"✓ 创建委外加工: 总成本 {outsourced.total_cost}")
    
    # 记录部分付款
    finance_mgr.record_expense(
        expense_type=ExpenseType.OUTSOURCING,
        amount=Decimal("600"),
        bank_type=BankType.G_BANK,
        expense_date=date(2024, 1, 25),
        supplier_id=supplier.id,
        supplier_name=supplier.name,
        related_order_id=order.id
    )
    
    # 更新委外加工的已付金额
    outsourced.paid_amount = Decimal("600")
    db.save_outsourced_processing(outsourced)
    print(f"✓ 记录付款: 600, 已付: {outsourced.paid_amount}")
    
    # 生成应付账款报表
    ap_report = report_mgr.generate_accounts_payable_report(
        as_of_date=date(2024, 1, 31),
        include_supplier_statement=True
    )
    
    print(f"\n应付账款报表:")
    print(f"  报表名称: {ap_report['report_name']}")
    print(f"  截止日期: {ap_report['as_of_date']}")
    print(f"  应付总额: {ap_report['summary']['total_payable']}")
    print(f"  供应商数量: {ap_report['summary']['supplier_count']}")
    print(f"  项目数量: {ap_report['summary']['item_count']}")
    
    if ap_report['supplier_statements']:
        print(f"\n  供应商对账单:")
        for supplier_id, statement in ap_report['supplier_statements'].items():
            print(f"    供应商: {statement['supplier_name']}")
            print(f"      应付款: {statement['total_payable']}")
            print(f"      已付款: {statement['total_paid']}")
            print(f"      总业务额: {statement['total_business']}")
    
    # 验证结果
    assert ap_report['summary']['total_payable'] == Decimal("400"), "应付账款总额错误"
    assert ap_report['summary']['supplier_count'] == 1, "供应商数量错误"
    
    print("\n✓ 应付账款报表测试通过!")
    db.close()


def test_bank_reconciliation_report():
    """测试银行余额调节表"""
    print("\n" + "="*60)
    print("测试银行余额调节表")
    print("="*60)
    
    # 创建数据库和管理器
    db = DatabaseManager(":memory:")
    db.connect()
    
    finance_mgr = FinanceManager(db)
    report_mgr = ReportManager(db)
    
    # 创建银行账户
    g_bank = finance_mgr.create_bank_account(
        bank_type=BankType.G_BANK,
        account_name="G银行主账户",
        initial_balance=Decimal("50000")
    )
    print(f"✓ 创建G银行账户, 初始余额: {g_bank.balance}")
    
    n_bank = finance_mgr.create_bank_account(
        bank_type=BankType.N_BANK,
        account_name="N银行账户",
        initial_balance=Decimal("30000")
    )
    print(f"✓ 创建N银行账户, 初始余额: {n_bank.balance}")
    
    # 记录一些银行交易
    finance_mgr.record_bank_transaction(
        bank_type=BankType.G_BANK,
        amount=Decimal("10000"),
        transaction_date=date(2024, 1, 15),
        counterparty="客户A",
        description="收到货款",
        is_income=True
    )
    
    finance_mgr.record_bank_transaction(
        bank_type=BankType.G_BANK,
        amount=Decimal("5000"),
        transaction_date=date(2024, 1, 20),
        counterparty="供应商B",
        description="支付材料款",
        is_income=False
    )
    
    finance_mgr.record_bank_transaction(
        bank_type=BankType.N_BANK,
        amount=Decimal("3000"),
        transaction_date=date(2024, 1, 18),
        counterparty="客户C",
        description="微信收款",
        is_income=True
    )
    print(f"✓ 记录3笔银行交易")
    
    # 生成单个银行的余额调节表
    g_bank_reconciliation = report_mgr.generate_bank_reconciliation_report(
        as_of_date=date(2024, 1, 31),
        bank_type=BankType.G_BANK
    )
    
    print(f"\nG银行余额调节表:")
    print(f"  报表名称: {g_bank_reconciliation['report_name']}")
    print(f"  银行类型: {g_bank_reconciliation['bank_type']}")
    print(f"  账面余额: {g_bank_reconciliation['book_balance']}")
    print(f"  调节后余额: {g_bank_reconciliation['adjusted_balance']}")
    print(f"  差异: {g_bank_reconciliation['difference']}")
    
    tx_summary = g_bank_reconciliation['transaction_summary']
    print(f"\n  交易汇总:")
    print(f"    总交易数: {tx_summary['total_transactions']}")
    print(f"    已匹配: {tx_summary['matched_transactions']}")
    print(f"    未匹配: {tx_summary['unmatched_transactions']}")
    print(f"    匹配率: {tx_summary['match_rate']}%")
    
    # 生成所有银行的汇总调节表
    all_banks_reconciliation = report_mgr.generate_bank_reconciliation_report(
        as_of_date=date(2024, 1, 31)
    )
    
    print(f"\n所有银行余额调节表（汇总）:")
    print(f"  报表名称: {all_banks_reconciliation['report_name']}")
    summary = all_banks_reconciliation['summary']
    print(f"  总账面余额: {summary['total_book_balance']}")
    print(f"  总调节后余额: {summary['total_adjusted_balance']}")
    print(f"  总差异: {summary['total_difference']}")
    
    # 验证结果
    assert g_bank_reconciliation['book_balance'] == Decimal("55000"), "G银行账面余额错误"
    assert summary['total_book_balance'] == Decimal("88000"), "总账面余额错误"
    
    print("\n✓ 银行余额调节表测试通过!")
    db.close()


if __name__ == "__main__":
    try:
        test_accounts_receivable_report()
        test_accounts_payable_report()
        test_bank_reconciliation_report()
        
        print("\n" + "="*60)
        print("所有测试通过! ✓")
        print("="*60)
        print("\nTask 7.3 实现完成:")
        print("  ✓ 应收账款明细和账龄分析")
        print("  ✓ 应付账款明细和供应商对账单")
        print("  ✓ 银行余额调节表")
        
    except Exception as e:
        print(f"\n✗ 测试失败: {e}")
        import traceback
        traceback.print_exc()
