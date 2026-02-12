#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Task 7.4 验证脚本 - 业务分析报告
"""

from decimal import Decimal
from datetime import date, timedelta
from database.db_manager import DatabaseManager
from business.finance_manager import FinanceManager
from business.order_manager import OrderManager
from business.outsourced_processing_manager import OutsourcedProcessingManager
from reports.report_manager import ReportManager
from models.business_models import (
    Customer, Supplier, BankType, ExpenseType, PricingUnit
)


def verify_business_analysis():
    """验证业务分析报告功能"""
    print("\n" + "="*70)
    print("Task 7.4: 业务分析报告功能验证")
    print("="*70)
    
    # 创建数据库和管理器
    db = DatabaseManager(":memory:")
    db.connect()
    
    finance_mgr = FinanceManager(db)
    order_mgr = OrderManager(db)
    outsourced_mgr = OutsourcedProcessingManager(db)
    report_mgr = ReportManager(db)
    
    # 创建测试数据
    print("\n1. 创建测试数据...")
    
    # 创建客户
    customers = []
    for i in range(5):
        customer = Customer(
            name=f"客户{chr(65+i)}",
            contact=f"联系人{i+1}",
            phone=f"138{i:08d}"
        )
        db.save_customer(customer)
        customers.append(customer)
    print(f"   ✓ 创建 {len(customers)} 个客户")
    
    # 创建供应商
    supplier = Supplier(
        name="委外供应商",
        contact="供应商联系人",
        phone="13900000000",
        business_type="委外加工"
    )
    db.save_supplier(supplier)
    
    # 创建银行账户
    g_bank = finance_mgr.create_bank_account(
        bank_type=BankType.G_BANK,
        account_name="G银行账户",
        initial_balance=Decimal("100000")
    )
    n_bank = finance_mgr.create_bank_account(
        bank_type=BankType.N_BANK,
        account_name="N银行账户",
        initial_balance=Decimal("50000")
    )
    
    # 创建订单
    base_date = date(2024, 1, 1)
    pricing_units = [PricingUnit.PIECE, PricingUnit.STRIP, PricingUnit.METER]
    orders = []
    
    for i, customer in enumerate(customers):
        for j in range(2):
            pricing_unit = pricing_units[j % len(pricing_units)]
            quantity = Decimal(str(100 * (i + 1) * (j + 1)))
            unit_price = Decimal(str(5.0 + i + j * 0.5))
            
            order = order_mgr.create_order(
                customer_id=customer.id,
                customer_name=customer.name,
                item_description=f"产品{i+1}-{j+1}",
                quantity=quantity,
                pricing_unit=pricing_unit,
                unit_price=unit_price,
                order_date=base_date + timedelta(days=i*10 + j*3)
            )
            orders.append(order)
            
            # 第一个订单全额收款
            if j == 0:
                finance_mgr.record_income(
                    amount=order.total_amount,
                    customer_id=customer.id,
                    customer_name=customer.name,
                    bank_type=BankType.G_BANK,
                    income_date=order.order_date + timedelta(days=5),
                    order_id=order.id
                )
    
    print(f"   ✓ 创建 {len(orders)} 个订单")
    
    # 创建支出
    expense_data = [
        (ExpenseType.ACID_THREE, Decimal("5000")),
        (ExpenseType.CAUSTIC_SODA, Decimal("3000")),
        (ExpenseType.RENT, Decimal("8000")),
        (ExpenseType.SALARY, Decimal("15000")),
    ]
    
    for i, (expense_type, amount) in enumerate(expense_data):
        finance_mgr.record_expense(
            amount=amount,
            expense_type=expense_type,
            supplier_id=None,
            supplier_name=f"供应商{i}",
            bank_type=BankType.G_BANK,
            expense_date=base_date + timedelta(days=5 + i*2),
            description=f"{expense_type.value}支出"
        )
    
    print(f"   ✓ 创建 {len(expense_data)} 笔支出")
    
    # 创建委外加工
    if orders:
        outsourced = outsourced_mgr.create_outsourced_processing(
            order_id=orders[0].id,
            supplier_id=supplier.id,
            supplier_name=supplier.name,
            process_type="抛光",
            process_description="外发抛光处理",
            quantity=Decimal("100"),
            unit_cost=Decimal("2.0"),
            process_date=base_date + timedelta(days=3)
        )
        print(f"   ✓ 创建委外加工记录")
    
    # 测试1: 客户收入排行
    print("\n2. 测试客户收入排行和盈利能力分析...")
    start_date = base_date
    end_date = base_date + timedelta(days=60)
    
    customer_report = report_mgr.generate_customer_revenue_ranking(
        start_date=start_date,
        end_date=end_date,
        top_n=10
    )
    
    assert customer_report["report_name"] == "客户收入排行及盈利能力分析"
    assert "summary" in customer_report
    assert "top_customers" in customer_report
    assert customer_report["summary"]["total_revenue"] > 0
    assert customer_report["summary"]["total_customers"] == 5
    
    print(f"   ✓ 报表名称: {customer_report['report_name']}")
    print(f"   ✓ 总收入: {customer_report['summary']['total_revenue']}")
    print(f"   ✓ 客户数量: {customer_report['summary']['total_customers']}")
    print(f"   ✓ 前3名客户:")
    for i, cust in enumerate(customer_report['top_customers'][:3], 1):
        print(f"      {i}. {cust['customer_name']}: {cust['total_revenue']} ({cust['revenue_percentage']}%)")
    
    # 测试2: 计价方式分析
    print("\n3. 测试计价方式收入构成分析...")
    pricing_report = report_mgr.generate_pricing_method_analysis(
        start_date=start_date,
        end_date=end_date
    )
    
    assert pricing_report["report_name"] == "计价方式收入构成分析"
    assert "by_pricing_method" in pricing_report
    assert "chart_data" in pricing_report
    assert pricing_report["summary"]["total_revenue"] > 0
    
    print(f"   ✓ 报表名称: {pricing_report['report_name']}")
    print(f"   ✓ 总收入: {pricing_report['summary']['total_revenue']}")
    print(f"   ✓ 计价方式数量: {pricing_report['summary']['pricing_method_count']}")
    print(f"   ✓ 计价方式明细:")
    for method in pricing_report['by_pricing_method']:
        print(f"      - {method['pricing_unit']}: {method['total_revenue']} ({method['revenue_percentage']}%)")
    
    # 测试3: 成本结构分析
    print("\n4. 测试成本结构分析...")
    cost_report = report_mgr.generate_cost_structure_analysis(
        start_date=start_date,
        end_date=end_date
    )
    
    assert cost_report["report_name"] == "成本结构分析"
    assert "cost_classification" in cost_report
    assert "by_expense_type" in cost_report
    assert "chart_data" in cost_report
    assert cost_report["summary"]["total_cost"] > 0
    
    print(f"   ✓ 报表名称: {cost_report['report_name']}")
    print(f"   ✓ 总成本: {cost_report['summary']['total_cost']}")
    print(f"   ✓ 成本率: {cost_report['summary']['cost_ratio']}%")
    print(f"   ✓ 直接成本: {cost_report['cost_classification']['direct_costs']['amount']}")
    print(f"   ✓ 间接成本: {cost_report['cost_classification']['indirect_costs']['amount']}")
    
    # 测试4: 现金流预测
    print("\n5. 测试现金流预测...")
    forecast_date = base_date + timedelta(days=30)
    forecast_report = report_mgr.generate_cash_flow_forecast(
        forecast_date=forecast_date,
        forecast_days=30
    )
    
    assert forecast_report["report_name"] == "现金流预测及资金需求分析"
    assert "current_status" in forecast_report
    assert "expected_inflows" in forecast_report
    assert "expected_outflows" in forecast_report
    assert "forecast" in forecast_report
    assert "risk_assessment" in forecast_report
    
    print(f"   ✓ 报表名称: {forecast_report['report_name']}")
    print(f"   ✓ 当前现金余额: {forecast_report['current_status']['current_cash_balance']}")
    print(f"   ✓ 预期流入: {forecast_report['expected_inflows']['total']}")
    print(f"   ✓ 预期流出: {forecast_report['expected_outflows']['total']}")
    print(f"   ✓ 预测余额: {forecast_report['forecast']['forecasted_cash_balance']}")
    print(f"   ✓ 风险等级: {forecast_report['risk_assessment']['risk_level']}")
    
    # 测试5: 综合业务分析报告
    print("\n6. 测试综合业务分析报告...")
    comprehensive_report = report_mgr.generate_business_analysis_report(
        start_date=start_date,
        end_date=end_date,
        include_forecast=True,
        forecast_days=30
    )
    
    assert comprehensive_report["report_name"] == "业务分析综合报告"
    assert "key_metrics" in comprehensive_report
    assert "customer_analysis" in comprehensive_report
    assert "pricing_analysis" in comprehensive_report
    assert "cost_analysis" in comprehensive_report
    assert "cash_flow_forecast" in comprehensive_report
    
    print(f"   ✓ 报表名称: {comprehensive_report['report_name']}")
    print(f"   ✓ 关键指标:")
    metrics = comprehensive_report['key_metrics']
    print(f"      - 总收入: {metrics['total_revenue']}")
    print(f"      - 总成本: {metrics['total_cost']}")
    print(f"      - 净利润: {metrics['net_profit']}")
    print(f"      - 利润率: {metrics['profit_margin']}%")
    print(f"      - 客户数量: {metrics['customer_count']}")
    print(f"      - 订单数量: {metrics['order_count']}")
    
    # 验证数据一致性
    print("\n7. 验证数据一致性...")
    assert comprehensive_report['customer_analysis']['summary']['total_revenue'] == customer_report['summary']['total_revenue']
    assert comprehensive_report['pricing_analysis']['summary']['total_revenue'] == pricing_report['summary']['total_revenue']
    assert comprehensive_report['cost_analysis']['summary']['total_cost'] == cost_report['summary']['total_cost']
    print("   ✓ 所有数据一致性检查通过")
    
    # 验证图表数据
    print("\n8. 验证可视化图表数据...")
    assert len(pricing_report['chart_data']['labels']) > 0
    assert len(pricing_report['chart_data']['revenue']) > 0
    assert len(cost_report['chart_data']['labels']) > 0
    assert len(cost_report['chart_data']['amounts']) > 0
    print("   ✓ 图表数据生成正确")
    
    print("\n" + "="*70)
    print("✓ Task 7.4 所有功能验证通过！")
    print("="*70)
    print("\n实现的功能:")
    print("  1. ✓ 客户收入排行和盈利能力分析")
    print("  2. ✓ 不同计价方式的收入构成分析")
    print("  3. ✓ 成本结构分析")
    print("  4. ✓ 现金流预测和资金需求分析")
    print("  5. ✓ 可视化图表数据准备")
    print("  6. ✓ 综合业务分析报告")
    print("\n需求覆盖:")
    print("  ✓ 需求 9.1: 客户收入排行和盈利能力分析")
    print("  ✓ 需求 9.2: 不同计价方式的收入构成")
    print("  ✓ 需求 9.3: 成本结构分析")
    print("  ✓ 需求 9.4: 现金流预测")
    print("  ✓ 需求 9.5: 可视化图表")
    print("="*70)
    
    db.close()
    return True


if __name__ == "__main__":
    try:
        verify_business_analysis()
    except Exception as e:
        print(f"\n✗ 验证失败: {e}")
        import traceback
        traceback.print_exc()
        exit(1)
