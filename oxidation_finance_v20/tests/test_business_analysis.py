#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
业务分析报告单元测试
"""

import pytest
from decimal import Decimal
from datetime import date, timedelta
from pathlib import Path
import sys

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from oxidation_finance_v20.database.db_manager import DatabaseManager
from oxidation_finance_v20.business.finance_manager import FinanceManager
from oxidation_finance_v20.business.order_manager import OrderManager
from oxidation_finance_v20.business.outsourced_processing_manager import OutsourcedProcessingManager
from oxidation_finance_v20.reports.report_manager import ReportManager, ReportPeriod
from oxidation_finance_v20.models.business_models import (
    Customer, Supplier, BankType, ExpenseType, PricingUnit, OrderStatus
)


@pytest.fixture
def db_manager():
    """创建测试数据库管理器"""
    db = DatabaseManager(":memory:")
    db.connect()
    yield db
    db.close()


@pytest.fixture
def finance_manager(db_manager):
    """创建财务管理器"""
    return FinanceManager(db_manager)


@pytest.fixture
def order_manager(db_manager):
    """创建订单管理器"""
    return OrderManager(db_manager)


@pytest.fixture
def outsourced_manager(db_manager):
    """创建委外加工管理器"""
    return OutsourcedProcessingManager(db_manager)


@pytest.fixture
def report_manager(db_manager):
    """创建报表管理器"""
    return ReportManager(db_manager)


@pytest.fixture
def setup_business_data(db_manager, finance_manager, order_manager, outsourced_manager):
    """设置业务分析测试数据"""
    # 创建多个客户
    customers = []
    for i in range(5):
        customer = Customer(
            name=f"客户{chr(65+i)}",  # 客户A, 客户B, ...
            contact=f"联系人{i+1}",
            phone=f"138{i:08d}"
        )
        db_manager.save_customer(customer)
        customers.append(customer)
    
    # 创建供应商
    supplier = Supplier(
        name="委外供应商",
        contact="供应商联系人",
        phone="13900000000",
        business_type="委外加工"
    )
    db_manager.save_supplier(supplier)
    
    # 创建银行账户
    g_bank = finance_manager.create_bank_account(
        bank_type=BankType.G_BANK,
        account_name="G银行账户",
        initial_balance=Decimal("100000")
    )
    
    n_bank = finance_manager.create_bank_account(
        bank_type=BankType.N_BANK,
        account_name="N银行账户",
        initial_balance=Decimal("50000")
    )
    
    # 创建不同计价方式的订单
    base_date = date(2024, 1, 1)
    pricing_units = [
        PricingUnit.PIECE,
        PricingUnit.STRIP,
        PricingUnit.UNIT,
        PricingUnit.ITEM,
        PricingUnit.METER
    ]
    
    orders = []
    for i, customer in enumerate(customers):
        # 每个客户创建2-3个订单
        order_count = 2 + (i % 2)
        for j in range(order_count):
            pricing_unit = pricing_units[j % len(pricing_units)]
            quantity = Decimal(str(100 * (i + 1) * (j + 1)))
            unit_price = Decimal(str(5.0 + i + j * 0.5))
            
            order = order_manager.create_order(
                customer_id=customer.id,
                customer_name=customer.name,
                item_description=f"产品{i+1}-{j+1}",
                quantity=quantity,
                pricing_unit=pricing_unit,
                unit_price=unit_price,
                order_date=base_date + timedelta(days=i*10 + j*3)
            )
            orders.append(order)
            
            # 部分订单收款
            if j == 0:
                # 第一个订单全额收款
                finance_manager.record_income(
                    amount=order.total_amount,
                    customer_id=customer.id,
                    customer_name=customer.name,
                    bank_type=BankType.G_BANK,
                    income_date=order.order_date + timedelta(days=5),
                    order_id=order.id
                )
            elif j == 1:
                # 第二个订单部分收款
                finance_manager.record_income(
                    amount=order.total_amount * Decimal("0.6"),
                    customer_id=customer.id,
                    customer_name=customer.name,
                    bank_type=BankType.N_BANK,
                    income_date=order.order_date + timedelta(days=10),
                    order_id=order.id
                )
    
    # 创建各类支出
    expense_types = [
        (ExpenseType.ACID_THREE, Decimal("5000")),
        (ExpenseType.CAUSTIC_SODA, Decimal("3000")),
        (ExpenseType.COLOR_POWDER, Decimal("2000")),
        (ExpenseType.RENT, Decimal("8000")),
        (ExpenseType.UTILITIES, Decimal("1500")),
        (ExpenseType.SALARY, Decimal("15000")),
    ]
    
    for i, (expense_type, amount) in enumerate(expense_types):
        finance_manager.record_expense(
            amount=amount,
            expense_type=expense_type,
            supplier_id=supplier.id if expense_type == ExpenseType.OUTSOURCING else None,
            supplier_name=supplier.name if expense_type == ExpenseType.OUTSOURCING else f"供应商{i}",
            bank_type=BankType.G_BANK,
            expense_date=base_date + timedelta(days=5 + i*2),
            description=f"{expense_type.value}支出"
        )
    
    # 创建委外加工记录
    if orders:
        outsourced = outsourced_manager.create_outsourced_processing(
            order_id=orders[0].id,
            supplier_id=supplier.id,
            supplier_name=supplier.name,
            process_type="抛光",
            process_description="外发抛光处理",
            quantity=Decimal("100"),
            unit_cost=Decimal("2.0"),
            process_date=base_date + timedelta(days=3)
        )
        
        # 部分付款
        finance_manager.record_expense(
            amount=Decimal("100"),
            expense_type=ExpenseType.OUTSOURCING,
            supplier_id=supplier.id,
            supplier_name=supplier.name,
            bank_type=BankType.G_BANK,
            expense_date=base_date + timedelta(days=10),
            description="委外加工费用",
            outsourced_id=outsourced.id
        )
    
    return {
        "customers": customers,
        "supplier": supplier,
        "orders": orders,
        "base_date": base_date
    }


class TestCustomerRevenueRanking:
    """测试客户收入排行功能"""
    
    def test_generate_customer_revenue_ranking(self, report_manager, setup_business_data):
        """测试生成客户收入排行"""
        data = setup_business_data
        start_date = data["base_date"]
        end_date = start_date + timedelta(days=60)
        
        report = report_manager.generate_customer_revenue_ranking(
            start_date=start_date,
            end_date=end_date,
            top_n=10
        )
        
        # 验证报表结构
        assert report["report_name"] == "客户收入排行及盈利能力分析"
        assert "period" in report
        assert "summary" in report
        assert "top_customers" in report
        
        # 验证汇总数据
        summary = report["summary"]
        assert summary["total_revenue"] > 0
        assert summary["total_customers"] == 5
        assert summary["total_orders"] > 0
        
        # 验证客户排序（按收入降序）
        top_customers = report["top_customers"]
        assert len(top_customers) <= 10
        for i in range(len(top_customers) - 1):
            assert top_customers[i]["total_revenue"] >= top_customers[i+1]["total_revenue"]
    
    def test_customer_profitability_metrics(self, report_manager, setup_business_data):
        """测试客户盈利能力指标"""
        data = setup_business_data
        start_date = data["base_date"]
        end_date = start_date + timedelta(days=60)
        
        report = report_manager.generate_customer_revenue_ranking(
            start_date=start_date,
            end_date=end_date
        )
        
        # 验证每个客户的指标
        for customer in report["top_customers"]:
            assert "customer_name" in customer
            assert "total_revenue" in customer
            assert "total_received" in customer
            assert "payment_rate" in customer
            assert "avg_order_amount" in customer
            assert "outstanding_amount" in customer
            assert "revenue_percentage" in customer
            
            # 验证计算正确性
            assert customer["outstanding_amount"] == customer["total_revenue"] - customer["total_received"]
            assert customer["avg_order_amount"] == customer["total_revenue"] / customer["order_count"]
    
    def test_top_n_limit(self, report_manager, setup_business_data):
        """测试top_n参数限制"""
        data = setup_business_data
        start_date = data["base_date"]
        end_date = start_date + timedelta(days=60)
        
        # 请求前3名
        report = report_manager.generate_customer_revenue_ranking(
            start_date=start_date,
            end_date=end_date,
            top_n=3
        )
        
        assert len(report["top_customers"]) <= 3
        assert report["summary"]["top_n_count"] <= 3


class TestPricingMethodAnalysis:
    """测试计价方式分析功能"""
    
    def test_generate_pricing_method_analysis(self, report_manager, setup_business_data):
        """测试生成计价方式分析"""
        data = setup_business_data
        start_date = data["base_date"]
        end_date = start_date + timedelta(days=60)
        
        report = report_manager.generate_pricing_method_analysis(
            start_date=start_date,
            end_date=end_date
        )
        
        # 验证报表结构
        assert report["report_name"] == "计价方式收入构成分析"
        assert "period" in report
        assert "summary" in report
        assert "by_pricing_method" in report
        assert "chart_data" in report
        
        # 验证汇总数据
        summary = report["summary"]
        assert summary["total_revenue"] > 0
        assert summary["pricing_method_count"] > 0
    
    def test_pricing_method_metrics(self, report_manager, setup_business_data):
        """测试计价方式指标"""
        data = setup_business_data
        start_date = data["base_date"]
        end_date = start_date + timedelta(days=60)
        
        report = report_manager.generate_pricing_method_analysis(
            start_date=start_date,
            end_date=end_date
        )
        
        # 验证每种计价方式的指标
        total_percentage = Decimal("0")
        for method in report["by_pricing_method"]:
            assert "pricing_unit" in method
            assert "total_revenue" in method
            assert "total_quantity" in method
            assert "order_count" in method
            assert "avg_unit_price" in method
            assert "revenue_percentage" in method
            
            total_percentage += method["revenue_percentage"]
            
            # 验证平均单价计算
            if method["total_quantity"] > 0:
                expected_avg = method["total_revenue"] / method["total_quantity"]
                assert abs(method["avg_unit_price"] - expected_avg) < Decimal("0.01")
        
        # 验证百分比总和接近100%
        assert abs(total_percentage - Decimal("100")) < Decimal("1")
    
    def test_chart_data_generation(self, report_manager, setup_business_data):
        """测试图表数据生成"""
        data = setup_business_data
        start_date = data["base_date"]
        end_date = start_date + timedelta(days=60)
        
        report = report_manager.generate_pricing_method_analysis(
            start_date=start_date,
            end_date=end_date
        )
        
        chart_data = report["chart_data"]
        assert "labels" in chart_data
        assert "revenue" in chart_data
        assert "percentages" in chart_data
        
        # 验证数据长度一致
        assert len(chart_data["labels"]) == len(chart_data["revenue"])
        assert len(chart_data["labels"]) == len(chart_data["percentages"])


class TestCostStructureAnalysis:
    """测试成本结构分析功能"""
    
    def test_generate_cost_structure_analysis(self, report_manager, setup_business_data):
        """测试生成成本结构分析"""
        data = setup_business_data
        start_date = data["base_date"]
        end_date = start_date + timedelta(days=60)
        
        report = report_manager.generate_cost_structure_analysis(
            start_date=start_date,
            end_date=end_date
        )
        
        # 验证报表结构
        assert report["report_name"] == "成本结构分析"
        assert "period" in report
        assert "summary" in report
        assert "cost_classification" in report
        assert "by_expense_type" in report
        assert "chart_data" in report
        
        # 验证汇总数据
        summary = report["summary"]
        assert summary["total_cost"] > 0
        assert summary["cost_ratio"] >= 0
    
    def test_cost_classification(self, report_manager, setup_business_data):
        """测试成本分类"""
        data = setup_business_data
        start_date = data["base_date"]
        end_date = start_date + timedelta(days=60)
        
        report = report_manager.generate_cost_structure_analysis(
            start_date=start_date,
            end_date=end_date
        )
        
        classification = report["cost_classification"]
        assert "direct_costs" in classification
        assert "indirect_costs" in classification
        
        # 验证直接成本和间接成本
        direct = classification["direct_costs"]
        indirect = classification["indirect_costs"]
        
        assert direct["amount"] >= 0
        assert indirect["amount"] >= 0
        assert "percentage" in direct
        assert "percentage" in indirect
        assert "revenue_ratio" in direct
        assert "revenue_ratio" in indirect
        
        # 验证百分比总和接近100%
        total_percentage = direct["percentage"] + indirect["percentage"]
        assert abs(total_percentage - Decimal("100")) < Decimal("1")
    
    def test_expense_type_breakdown(self, report_manager, setup_business_data):
        """测试支出类型明细"""
        data = setup_business_data
        start_date = data["base_date"]
        end_date = start_date + timedelta(days=60)
        
        report = report_manager.generate_cost_structure_analysis(
            start_date=start_date,
            end_date=end_date
        )
        
        # 验证支出类型排序（按金额降序）
        expense_types = report["by_expense_type"]
        for i in range(len(expense_types) - 1):
            assert expense_types[i]["total_amount"] >= expense_types[i+1]["total_amount"]
        
        # 验证每种支出类型的数据
        total_percentage = Decimal("0")
        for expense_type in expense_types:
            assert "expense_type" in expense_type
            assert "total_amount" in expense_type
            assert "expense_count" in expense_type
            assert "cost_percentage" in expense_type
            
            total_percentage += expense_type["cost_percentage"]
        
        # 验证百分比总和接近100%
        assert abs(total_percentage - Decimal("100")) < Decimal("1")


class TestCashFlowForecast:
    """测试现金流预测功能"""
    
    def test_generate_cash_flow_forecast(self, report_manager, setup_business_data):
        """测试生成现金流预测"""
        data = setup_business_data
        forecast_date = data["base_date"] + timedelta(days=30)
        
        report = report_manager.generate_cash_flow_forecast(
            forecast_date=forecast_date,
            forecast_days=30
        )
        
        # 验证报表结构
        assert report["report_name"] == "现金流预测及资金需求分析"
        assert "forecast_period" in report
        assert "current_status" in report
        assert "expected_inflows" in report
        assert "expected_outflows" in report
        assert "forecast" in report
        assert "risk_assessment" in report
    
    def test_current_cash_balance(self, report_manager, setup_business_data):
        """测试当前现金余额"""
        data = setup_business_data
        forecast_date = data["base_date"] + timedelta(days=30)
        
        report = report_manager.generate_cash_flow_forecast(
            forecast_date=forecast_date,
            forecast_days=30
        )
        
        current_status = report["current_status"]
        assert "current_cash_balance" in current_status
        assert "by_bank" in current_status
        assert current_status["current_cash_balance"] > 0
        
        # 验证银行账户明细
        assert len(current_status["by_bank"]) > 0
        for bank in current_status["by_bank"]:
            assert "bank_type" in bank
            assert "account_name" in bank
            assert "balance" in bank
    
    def test_expected_cash_flows(self, report_manager, setup_business_data):
        """测试预期现金流"""
        data = setup_business_data
        forecast_date = data["base_date"] + timedelta(days=30)
        
        report = report_manager.generate_cash_flow_forecast(
            forecast_date=forecast_date,
            forecast_days=30
        )
        
        # 验证预期流入
        inflows = report["expected_inflows"]
        assert "total" in inflows
        assert "count" in inflows
        assert "items" in inflows
        
        # 验证预期流出
        outflows = report["expected_outflows"]
        assert "payables" in outflows
        assert "daily_expenses" in outflows
        assert "total" in outflows
        
        # 验证流出总额计算
        expected_total = outflows["payables"]["total"] + outflows["daily_expenses"]["estimated_total"]
        assert abs(outflows["total"] - expected_total) < Decimal("0.01")
    
    def test_forecast_calculation(self, report_manager, setup_business_data):
        """测试预测计算"""
        data = setup_business_data
        forecast_date = data["base_date"] + timedelta(days=30)
        
        report = report_manager.generate_cash_flow_forecast(
            forecast_date=forecast_date,
            forecast_days=30
        )
        
        forecast = report["forecast"]
        assert "forecasted_cash_balance" in forecast
        assert "net_change" in forecast
        assert "net_change_percentage" in forecast
        
        # 验证净变化计算
        current_balance = report["current_status"]["current_cash_balance"]
        expected_net_change = forecast["forecasted_cash_balance"] - current_balance
        assert abs(forecast["net_change"] - expected_net_change) < Decimal("0.01")
    
    def test_risk_assessment(self, report_manager, setup_business_data):
        """测试风险评估"""
        data = setup_business_data
        forecast_date = data["base_date"] + timedelta(days=30)
        
        report = report_manager.generate_cash_flow_forecast(
            forecast_date=forecast_date,
            forecast_days=30
        )
        
        risk = report["risk_assessment"]
        assert "risk_level" in risk
        assert "risk_notes" in risk
        assert risk["risk_level"] in ["低", "中", "高"]
        assert isinstance(risk["risk_notes"], list)


class TestBusinessAnalysisReport:
    """测试综合业务分析报告"""
    
    def test_generate_comprehensive_report(self, report_manager, setup_business_data):
        """测试生成综合业务分析报告"""
        data = setup_business_data
        start_date = data["base_date"]
        end_date = start_date + timedelta(days=60)
        
        report = report_manager.generate_business_analysis_report(
            start_date=start_date,
            end_date=end_date,
            include_forecast=True,
            forecast_days=30
        )
        
        # 验证报表结构
        assert report["report_name"] == "业务分析综合报告"
        assert "period" in report
        assert "key_metrics" in report
        assert "customer_analysis" in report
        assert "pricing_analysis" in report
        assert "cost_analysis" in report
        assert "cash_flow_forecast" in report
    
    def test_key_metrics(self, report_manager, setup_business_data):
        """测试关键指标"""
        data = setup_business_data
        start_date = data["base_date"]
        end_date = start_date + timedelta(days=60)
        
        report = report_manager.generate_business_analysis_report(
            start_date=start_date,
            end_date=end_date
        )
        
        metrics = report["key_metrics"]
        assert "total_revenue" in metrics
        assert "total_cost" in metrics
        assert "net_profit" in metrics
        assert "profit_margin" in metrics
        assert "customer_count" in metrics
        assert "order_count" in metrics
        
        # 验证利润计算
        assert metrics["net_profit"] == metrics["total_revenue"] - metrics["total_cost"]
        
        # 验证利润率计算
        if metrics["total_revenue"] > 0:
            expected_margin = metrics["net_profit"] / metrics["total_revenue"] * 100
            assert abs(metrics["profit_margin"] - expected_margin) < Decimal("0.01")
    
    def test_report_without_forecast(self, report_manager, setup_business_data):
        """测试不包含预测的报告"""
        data = setup_business_data
        start_date = data["base_date"]
        end_date = start_date + timedelta(days=60)
        
        report = report_manager.generate_business_analysis_report(
            start_date=start_date,
            end_date=end_date,
            include_forecast=False
        )
        
        assert report["cash_flow_forecast"] is None
    
    def test_integrated_analysis(self, report_manager, setup_business_data):
        """测试集成分析的一致性"""
        data = setup_business_data
        start_date = data["base_date"]
        end_date = start_date + timedelta(days=60)
        
        # 生成综合报告
        comprehensive = report_manager.generate_business_analysis_report(
            start_date=start_date,
            end_date=end_date
        )
        
        # 单独生成各项分析
        customer_report = report_manager.generate_customer_revenue_ranking(start_date, end_date)
        pricing_report = report_manager.generate_pricing_method_analysis(start_date, end_date)
        cost_report = report_manager.generate_cost_structure_analysis(start_date, end_date)
        
        # 验证数据一致性
        assert comprehensive["customer_analysis"]["summary"]["total_revenue"] == customer_report["summary"]["total_revenue"]
        assert comprehensive["pricing_analysis"]["summary"]["total_revenue"] == pricing_report["summary"]["total_revenue"]
        assert comprehensive["cost_analysis"]["summary"]["total_cost"] == cost_report["summary"]["total_cost"]


class TestEdgeCases:
    """测试边界情况"""
    
    def test_empty_period(self, report_manager, db_manager):
        """测试空期间（无数据）"""
        start_date = date(2025, 1, 1)
        end_date = date(2025, 1, 31)
        
        # 客户收入排行
        customer_report = report_manager.generate_customer_revenue_ranking(start_date, end_date)
        assert customer_report["summary"]["total_revenue"] == 0
        assert len(customer_report["top_customers"]) == 0
        
        # 计价方式分析
        pricing_report = report_manager.generate_pricing_method_analysis(start_date, end_date)
        assert pricing_report["summary"]["total_revenue"] == 0
        
        # 成本结构分析
        cost_report = report_manager.generate_cost_structure_analysis(start_date, end_date)
        assert cost_report["summary"]["total_cost"] == 0
    
    def test_single_customer(self, report_manager, db_manager, finance_manager, order_manager):
        """测试单个客户"""
        # 创建单个客户和订单
        customer = Customer(name="单一客户", contact="联系人", phone="13800000000")
        db_manager.save_customer(customer)
        
        finance_manager.create_bank_account(
            bank_type=BankType.G_BANK,
            account_name="测试账户",
            initial_balance=Decimal("10000")
        )
        
        order = order_manager.create_order(
            customer_id=customer.id,
            customer_name=customer.name,
            item_description="测试产品",
            quantity=Decimal("100"),
            pricing_unit=PricingUnit.PIECE,
            unit_price=Decimal("10"),
            order_date=date(2024, 1, 1)
        )
        
        report = report_manager.generate_customer_revenue_ranking(
            start_date=date(2024, 1, 1),
            end_date=date(2024, 1, 31)
        )
        
        assert report["summary"]["total_customers"] == 1
        assert len(report["top_customers"]) == 1
        assert report["top_customers"][0]["revenue_percentage"] == 100


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
