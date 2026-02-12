#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
业务分析属性测试 - 使用Hypothesis进行基于属性的测试
"""

import pytest
from decimal import Decimal
from datetime import date, timedelta
from pathlib import Path
import sys
from hypothesis import given, strategies as st, settings, assume, HealthCheck

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


# ==================== 测试数据生成策略 ====================

@st.composite
def customer_strategy(draw):
    """生成客户数据"""
    customer_id = draw(st.integers(min_value=1, max_value=100))
    return Customer(
        id=customer_id,
        name=f"客户{customer_id}",
        contact=f"联系人{customer_id}",
        phone=f"138{customer_id:08d}"
    )


@st.composite
def supplier_strategy(draw):
    """生成供应商数据"""
    supplier_id = draw(st.integers(min_value=1, max_value=50))
    return Supplier(
        id=supplier_id,
        name=f"供应商{supplier_id}",
        contact=f"联系人{supplier_id}",
        phone=f"139{supplier_id:08d}",
        business_type="委外加工"
    )


@st.composite
def order_data_strategy(draw):
    """生成订单数据"""
    quantity = draw(st.decimals(min_value=1, max_value=1000, places=2))
    unit_price = draw(st.decimals(min_value=0.1, max_value=100, places=2))
    pricing_unit = draw(st.sampled_from(list(PricingUnit)))
    days_offset = draw(st.integers(min_value=0, max_value=365))
    
    return {
        "quantity": quantity,
        "unit_price": unit_price,
        "pricing_unit": pricing_unit,
        "days_offset": days_offset
    }


@st.composite
def income_data_strategy(draw):
    """生成收入数据"""
    amount = draw(st.decimals(min_value=1, max_value=100000, places=2))
    bank_type = draw(st.sampled_from([BankType.G_BANK, BankType.N_BANK]))
    days_offset = draw(st.integers(min_value=0, max_value=365))
    
    return {
        "amount": amount,
        "bank_type": bank_type,
        "days_offset": days_offset
    }


@st.composite
def expense_data_strategy(draw):
    """生成支出数据"""
    amount = draw(st.decimals(min_value=1, max_value=50000, places=2))
    expense_type = draw(st.sampled_from(list(ExpenseType)))
    bank_type = draw(st.sampled_from([BankType.G_BANK, BankType.N_BANK]))
    days_offset = draw(st.integers(min_value=0, max_value=365))
    
    return {
        "amount": amount,
        "expense_type": expense_type,
        "bank_type": bank_type,
        "days_offset": days_offset
    }


# ==================== 属性测试 ====================

class TestBusinessAnalysisProperties:
    """
    属性 24: 业务分析数据准确性
    
    对于任何业务分析报告，分析结果应该基于完整的业务数据，且计算逻辑应该是可重现的
    
    **验证: 需求 9.1, 9.2, 9.3, 9.4**
    """
    
    @pytest.fixture
    def db_manager(self):
        """创建测试数据库管理器"""
        db = DatabaseManager(":memory:")
        db.connect()
        yield db
        db.close()
    
    @pytest.fixture
    def managers(self, db_manager):
        """创建所有管理器"""
        return {
            "finance": FinanceManager(db_manager),
            "order": OrderManager(db_manager),
            "outsourced": OutsourcedProcessingManager(db_manager),
            "report": ReportManager(db_manager),
            "db": db_manager
        }
    
    @settings(max_examples=100, deadline=None, suppress_health_check=[HealthCheck.function_scoped_fixture])
    @given(
        customers=st.lists(customer_strategy(), min_size=1, max_size=10, unique_by=lambda c: c.name),
        orders_per_customer=st.lists(order_data_strategy(), min_size=1, max_size=5)
    )
    def test_customer_revenue_ranking_completeness(self, managers, customers, orders_per_customer):
        """
        属性 24.1: 客户收入排行基于完整数据
        
        验证客户收入排行报告包含所有客户的订单数据，且收入计算准确
        
        **验证: 需求 9.1**
        """
        db = managers["db"]
        order_mgr = managers["order"]
        report_mgr = managers["report"]
        finance_mgr = managers["finance"]
        
        # 创建银行账户
        finance_mgr.create_bank_account(
            bank_type=BankType.G_BANK,
            account_name="测试G银行",
            initial_balance=Decimal("1000000")
        )
        
        # 保存客户并创建订单
        base_date = date(2024, 1, 1)
        all_orders = []
        expected_revenue_by_customer = {}
        
        for customer in customers:
            db.save_customer(customer)
            expected_revenue_by_customer[customer.id] = Decimal("0")
            
            for order_data in orders_per_customer:
                order = order_mgr.create_order(
                    customer_id=customer.id,
                    customer_name=customer.name,
                    item_description=f"产品-{customer.id}",
                    quantity=order_data["quantity"],
                    pricing_unit=order_data["pricing_unit"],
                    unit_price=order_data["unit_price"],
                    order_date=base_date + timedelta(days=order_data["days_offset"])
                )
                all_orders.append(order)
                expected_revenue_by_customer[customer.id] += order.total_amount
        
        # 生成客户收入排行报告
        end_date = base_date + timedelta(days=400)
        report = report_mgr.generate_customer_revenue_ranking(
            start_date=base_date,
            end_date=end_date,
            top_n=100
        )
        
        # 验证：报告包含所有客户
        assert report["summary"]["total_customers"] == len(customers)
        
        # 验证：总收入等于所有订单金额之和
        expected_total_revenue = sum(expected_revenue_by_customer.values())
        assert abs(report["summary"]["total_revenue"] - expected_total_revenue) < Decimal("0.01")
        
        # 验证：每个客户的收入计算准确
        for customer_data in report["all_customers"]:
            customer_id = customer_data["customer_id"]
            expected_revenue = expected_revenue_by_customer[customer_id]
            assert abs(customer_data["total_revenue"] - expected_revenue) < Decimal("0.01")
        
        # 验证：客户按收入降序排列
        for i in range(len(report["top_customers"]) - 1):
            assert report["top_customers"][i]["total_revenue"] >= report["top_customers"][i+1]["total_revenue"]
    
    @settings(max_examples=100, deadline=None, suppress_health_check=[HealthCheck.function_scoped_fixture])
    @given(
        pricing_units=st.lists(
            st.sampled_from(list(PricingUnit)),
            min_size=1,
            max_size=7,
            unique=True
        ),
        orders_per_unit=st.integers(min_value=1, max_value=5)
    )
    def test_pricing_method_analysis_accuracy(self, managers, pricing_units, orders_per_unit):
        """
        属性 24.2: 计价方式分析计算准确
        
        验证计价方式分析报告正确统计各计价方式的收入，且百分比计算准确
        
        **验证: 需求 9.2**
        """
        db = managers["db"]
        order_mgr = managers["order"]
        report_mgr = managers["report"]
        finance_mgr = managers["finance"]
        
        # 创建银行账户和客户
        finance_mgr.create_bank_account(
            bank_type=BankType.G_BANK,
            account_name="测试G银行",
            initial_balance=Decimal("1000000")
        )
        
        customer = Customer(name="测试客户", contact="联系人", phone="13800000000")
        db.save_customer(customer)
        
        # 为每种计价方式创建订单
        base_date = date(2024, 1, 1)
        expected_revenue_by_pricing = {}
        
        for pricing_unit in pricing_units:
            expected_revenue_by_pricing[pricing_unit.value] = Decimal("0")
            
            for i in range(orders_per_unit):
                quantity = Decimal(str(10 + i * 5))
                unit_price = Decimal(str(5.0 + i))
                
                order = order_mgr.create_order(
                    customer_id=customer.id,
                    customer_name=customer.name,
                    item_description=f"产品-{pricing_unit.value}",
                    quantity=quantity,
                    pricing_unit=pricing_unit,
                    unit_price=unit_price,
                    order_date=base_date + timedelta(days=i)
                )
                expected_revenue_by_pricing[pricing_unit.value] += order.total_amount
        
        # 生成计价方式分析报告
        end_date = base_date + timedelta(days=30)
        report = report_mgr.generate_pricing_method_analysis(
            start_date=base_date,
            end_date=end_date
        )
        
        # 验证：报告包含所有计价方式
        assert report["summary"]["pricing_method_count"] == len(pricing_units)
        
        # 验证：总收入等于所有计价方式收入之和
        expected_total_revenue = sum(expected_revenue_by_pricing.values())
        assert abs(report["summary"]["total_revenue"] - expected_total_revenue) < Decimal("0.01")
        
        # 验证：每种计价方式的收入计算准确
        total_percentage = Decimal("0")
        for pricing_data in report["by_pricing_method"]:
            pricing_unit_name = pricing_data["pricing_unit"]
            expected_revenue = expected_revenue_by_pricing[pricing_unit_name]
            assert abs(pricing_data["total_revenue"] - expected_revenue) < Decimal("0.01")
            
            # 验证百分比计算
            expected_percentage = (expected_revenue / expected_total_revenue * 100) if expected_total_revenue > 0 else Decimal("0")
            assert abs(pricing_data["revenue_percentage"] - expected_percentage) < Decimal("0.1")
            
            total_percentage += pricing_data["revenue_percentage"]
        
        # 验证：百分比总和接近100%
        if expected_total_revenue > 0:
            assert abs(total_percentage - Decimal("100")) < Decimal("1")
    
    @settings(max_examples=100, deadline=None, suppress_health_check=[HealthCheck.function_scoped_fixture])
    @given(
        expense_types=st.lists(
            st.sampled_from(list(ExpenseType)),
            min_size=1,
            max_size=10,
            unique=True
        ),
        expenses_per_type=st.integers(min_value=1, max_value=3)
    )
    def test_cost_structure_analysis_completeness(self, managers, expense_types, expenses_per_type):
        """
        属性 24.3: 成本结构分析基于完整数据
        
        验证成本结构分析报告包含所有支出类型，且成本分类和占比计算准确
        
        **验证: 需求 9.3**
        """
        db = managers["db"]
        finance_mgr = managers["finance"]
        report_mgr = managers["report"]
        
        # 创建银行账户和供应商
        finance_mgr.create_bank_account(
            bank_type=BankType.G_BANK,
            account_name="测试G银行",
            initial_balance=Decimal("1000000")
        )
        
        supplier = Supplier(name="测试供应商", contact="联系人", phone="13900000000", business_type="原料供应")
        db.save_supplier(supplier)
        
        # 创建各类支出
        base_date = date(2024, 1, 1)
        expected_cost_by_type = {}
        
        for expense_type in expense_types:
            expected_cost_by_type[expense_type.value] = Decimal("0")
            
            for i in range(expenses_per_type):
                amount = Decimal(str(100 + i * 50))
                
                finance_mgr.record_expense(
                    amount=amount,
                    expense_type=expense_type,
                    supplier_id=supplier.id,
                    supplier_name=supplier.name,
                    bank_type=BankType.G_BANK,
                    expense_date=base_date + timedelta(days=i),
                    description=f"{expense_type.value}支出"
                )
                expected_cost_by_type[expense_type.value] += amount
        
        # 生成成本结构分析报告
        end_date = base_date + timedelta(days=30)
        report = report_mgr.generate_cost_structure_analysis(
            start_date=base_date,
            end_date=end_date
        )
        
        # 验证：报告包含所有支出类型
        assert report["summary"]["expense_type_count"] == len(expense_types)
        
        # 验证：总成本等于所有支出之和
        expected_total_cost = sum(expected_cost_by_type.values())
        assert abs(report["summary"]["total_cost"] - expected_total_cost) < Decimal("0.01")
        
        # 验证：每种支出类型的成本计算准确
        total_percentage = Decimal("0")
        for expense_data in report["by_expense_type"]:
            expense_type_name = expense_data["expense_type"]
            expected_cost = expected_cost_by_type[expense_type_name]
            assert abs(expense_data["total_amount"] - expected_cost) < Decimal("0.01")
            
            # 验证百分比计算
            expected_percentage = (expected_cost / expected_total_cost * 100) if expected_total_cost > 0 else Decimal("0")
            assert abs(expense_data["cost_percentage"] - expected_percentage) < Decimal("0.1")
            
            total_percentage += expense_data["cost_percentage"]
        
        # 验证：百分比总和接近100%
        if expected_total_cost > 0:
            assert abs(total_percentage - Decimal("100")) < Decimal("1")
        
        # 验证：直接成本和间接成本分类正确
        direct_cost_types = [
            ExpenseType.ACID_THREE.value,
            ExpenseType.CAUSTIC_SODA.value,
            ExpenseType.SODIUM_SULFITE.value,
            ExpenseType.COLOR_POWDER.value,
            ExpenseType.DEGREASER.value,
            ExpenseType.OUTSOURCING.value
        ]
        
        expected_direct_costs = sum(
            expected_cost_by_type.get(t, Decimal("0"))
            for t in direct_cost_types
        )
        expected_indirect_costs = expected_total_cost - expected_direct_costs
        
        classification = report["cost_classification"]
        assert abs(classification["direct_costs"]["amount"] - expected_direct_costs) < Decimal("0.01")
        assert abs(classification["indirect_costs"]["amount"] - expected_indirect_costs) < Decimal("0.01")
        
        # 验证：直接成本和间接成本百分比总和为100%
        total_class_percentage = classification["direct_costs"]["percentage"] + classification["indirect_costs"]["percentage"]
        if expected_total_cost > 0:
            assert abs(total_class_percentage - Decimal("100")) < Decimal("0.1")
    
    @settings(max_examples=100, deadline=None, suppress_health_check=[HealthCheck.function_scoped_fixture])
    @given(
        current_balance=st.decimals(min_value=1000, max_value=100000, places=2),
        receivables_count=st.integers(min_value=0, max_value=10),
        payables_count=st.integers(min_value=0, max_value=10)
    )
    def test_cash_flow_forecast_reproducibility(self, managers, current_balance, receivables_count, payables_count):
        """
        属性 24.4: 现金流预测计算可重现
        
        验证现金流预测基于当前数据计算，且多次运行结果一致
        
        **验证: 需求 9.4**
        """
        db = managers["db"]
        finance_mgr = managers["finance"]
        order_mgr = managers["order"]
        outsourced_mgr = managers["outsourced"]
        report_mgr = managers["report"]
        
        # 创建银行账户
        finance_mgr.create_bank_account(
            bank_type=BankType.G_BANK,
            account_name="测试G银行",
            initial_balance=current_balance
        )
        
        # 创建客户和供应商
        customer = Customer(name="测试客户", contact="联系人", phone="13800000000")
        db.save_customer(customer)
        
        supplier = Supplier(name="测试供应商", contact="联系人", phone="13900000000", business_type="委外加工")
        db.save_supplier(supplier)
        
        # 创建应收账款（未收款订单）
        base_date = date(2024, 1, 1)
        expected_receivables = Decimal("0")
        
        for i in range(receivables_count):
            order = order_mgr.create_order(
                customer_id=customer.id,
                customer_name=customer.name,
                item_description=f"产品{i}",
                quantity=Decimal(str(10 + i)),
                pricing_unit=PricingUnit.PIECE,
                unit_price=Decimal(str(10.0 + i)),
                order_date=base_date + timedelta(days=i)
            )
            # 不记录收款，保持应收状态
            expected_receivables += order.total_amount
        
        # 创建应付账款（未付款委外加工）
        expected_payables = Decimal("0")
        
        for i in range(payables_count):
            if receivables_count > 0:  # 需要有订单才能创建委外加工
                outsourced = outsourced_mgr.create_outsourced_processing(
                    order_id=1,  # 使用第一个订单
                    supplier_id=supplier.id,
                    supplier_name=supplier.name,
                    process_type="抛光",
                    process_description=f"委外加工{i}",
                    quantity=Decimal(str(5 + i)),
                    unit_cost=Decimal(str(5.0 + i)),
                    process_date=base_date + timedelta(days=i)
                )
                # 不记录付款，保持应付状态
                expected_payables += outsourced.total_cost
        
        # 生成现金流预测报告（第一次）
        forecast_date = base_date + timedelta(days=20)
        report1 = report_mgr.generate_cash_flow_forecast(
            forecast_date=forecast_date,
            forecast_days=30
        )
        
        # 再次生成现金流预测报告（第二次）
        report2 = report_mgr.generate_cash_flow_forecast(
            forecast_date=forecast_date,
            forecast_days=30
        )
        
        # 验证：当前现金余额准确
        assert abs(report1["current_status"]["current_cash_balance"] - current_balance) < Decimal("0.01")
        
        # 验证：两次预测结果完全一致（可重现性）
        assert report1["current_status"]["current_cash_balance"] == report2["current_status"]["current_cash_balance"]
        assert report1["expected_inflows"]["total"] == report2["expected_inflows"]["total"]
        assert report1["expected_outflows"]["total"] == report2["expected_outflows"]["total"]
        assert report1["forecast"]["forecasted_cash_balance"] == report2["forecast"]["forecasted_cash_balance"]
        
        # 验证：预测现金余额计算逻辑正确
        current_cash = report1["current_status"]["current_cash_balance"]
        expected_inflow = report1["expected_inflows"]["total"]
        expected_outflow = report1["expected_outflows"]["total"]
        forecasted_balance = report1["forecast"]["forecasted_cash_balance"]
        
        # 预测余额 = 当前余额 + 预期流入 - 预期流出
        expected_forecasted = current_cash + expected_inflow - expected_outflow
        assert abs(forecasted_balance - expected_forecasted) < Decimal("0.01")
        
        # 验证：净变化计算正确
        net_change = report1["forecast"]["net_change"]
        expected_net_change = forecasted_balance - current_cash
        assert abs(net_change - expected_net_change) < Decimal("0.01")
    
    @settings(max_examples=100, deadline=None, suppress_health_check=[HealthCheck.function_scoped_fixture])
    @given(
        customers_count=st.integers(min_value=1, max_value=5),
        orders_per_customer=st.integers(min_value=1, max_value=3),
        expense_types_count=st.integers(min_value=1, max_value=5)
    )
    def test_comprehensive_business_analysis_consistency(
        self, managers, customers_count, orders_per_customer, expense_types_count
    ):
        """
        属性 24.5: 综合业务分析报告数据一致性
        
        验证综合业务分析报告中各部分数据与单独生成的报告一致
        
        **验证: 需求 9.1, 9.2, 9.3, 9.4**
        """
        db = managers["db"]
        finance_mgr = managers["finance"]
        order_mgr = managers["order"]
        report_mgr = managers["report"]
        
        # 创建银行账户
        finance_mgr.create_bank_account(
            bank_type=BankType.G_BANK,
            account_name="测试G银行",
            initial_balance=Decimal("100000")
        )
        
        # 创建客户和订单
        base_date = date(2024, 1, 1)
        
        for i in range(customers_count):
            customer = Customer(
                name=f"客户{i}",
                contact=f"联系人{i}",
                phone=f"138{i:08d}"
            )
            db.save_customer(customer)
            
            for j in range(orders_per_customer):
                order_mgr.create_order(
                    customer_id=customer.id,
                    customer_name=customer.name,
                    item_description=f"产品{i}-{j}",
                    quantity=Decimal(str(10 + j)),
                    pricing_unit=PricingUnit.PIECE,
                    unit_price=Decimal(str(10.0 + i)),
                    order_date=base_date + timedelta(days=i * 5 + j)
                )
                
                # 部分订单收款
                if j == 0:
                    finance_mgr.record_income(
                        amount=Decimal(str((10 + j) * (10.0 + i))),
                        customer_id=customer.id,
                        customer_name=customer.name,
                        bank_type=BankType.G_BANK,
                        income_date=base_date + timedelta(days=i * 5 + j + 2)
                    )
        
        # 创建支出
        supplier = Supplier(name="测试供应商", contact="联系人", phone="13900000000", business_type="原料供应")
        db.save_supplier(supplier)
        
        expense_types = list(ExpenseType)[:expense_types_count]
        for i, expense_type in enumerate(expense_types):
            finance_mgr.record_expense(
                amount=Decimal(str(100 + i * 50)),
                expense_type=expense_type,
                supplier_id=supplier.id,
                supplier_name=supplier.name,
                bank_type=BankType.G_BANK,
                expense_date=base_date + timedelta(days=i * 2),
                description=f"{expense_type.value}支出"
            )
        
        # 生成综合业务分析报告
        end_date = base_date + timedelta(days=60)
        comprehensive_report = report_mgr.generate_business_analysis_report(
            start_date=base_date,
            end_date=end_date,
            include_forecast=False
        )
        
        # 单独生成各项分析报告
        customer_report = report_mgr.generate_customer_revenue_ranking(base_date, end_date)
        pricing_report = report_mgr.generate_pricing_method_analysis(base_date, end_date)
        cost_report = report_mgr.generate_cost_structure_analysis(base_date, end_date)
        
        # 验证：综合报告中的客户分析数据与单独报告一致
        assert comprehensive_report["customer_analysis"]["summary"]["total_revenue"] == customer_report["summary"]["total_revenue"]
        assert comprehensive_report["customer_analysis"]["summary"]["total_customers"] == customer_report["summary"]["total_customers"]
        
        # 验证：综合报告中的计价方式分析数据与单独报告一致
        assert comprehensive_report["pricing_analysis"]["summary"]["total_revenue"] == pricing_report["summary"]["total_revenue"]
        assert comprehensive_report["pricing_analysis"]["summary"]["pricing_method_count"] == pricing_report["summary"]["pricing_method_count"]
        
        # 验证：综合报告中的成本分析数据与单独报告一致
        assert comprehensive_report["cost_analysis"]["summary"]["total_cost"] == cost_report["summary"]["total_cost"]
        assert comprehensive_report["cost_analysis"]["summary"]["expense_type_count"] == cost_report["summary"]["expense_type_count"]
        
        # 验证：关键指标计算正确
        key_metrics = comprehensive_report["key_metrics"]
        assert key_metrics["total_revenue"] == customer_report["summary"]["total_revenue"]
        assert key_metrics["total_cost"] == cost_report["summary"]["total_cost"]
        assert key_metrics["net_profit"] == key_metrics["total_revenue"] - key_metrics["total_cost"]
        
        # 验证：利润率计算正确
        if key_metrics["total_revenue"] > 0:
            expected_margin = key_metrics["net_profit"] / key_metrics["total_revenue"] * 100
            assert abs(key_metrics["profit_margin"] - expected_margin) < Decimal("0.1")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
