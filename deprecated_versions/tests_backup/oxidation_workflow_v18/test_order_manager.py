"""
Unit tests for ProcessingOrderManager

Tests order creation, querying, filtering, and status updates
with all 7 pricing units.

Requirements: 1.1-1.6
"""

import pytest
import os
import tempfile
import shutil
from datetime import date, datetime
from decimal import Decimal

from oxidation_workflow_v18.models.core_models import (
    ProcessingOrder,
    OrderStatus,
    PricingUnit
)
from oxidation_workflow_v18.business.order_manager import ProcessingOrderManager


@pytest.fixture
def temp_data_dir():
    """创建临时数据目录"""
    temp_dir = tempfile.mkdtemp()
    yield temp_dir
    # 清理
    shutil.rmtree(temp_dir)


@pytest.fixture
def order_manager(temp_data_dir):
    """创建订单管理器实例"""
    return ProcessingOrderManager(data_dir=temp_data_dir)


class TestOrderCreation:
    """测试订单创建功能"""
    
    def test_create_order_with_piece_unit(self, order_manager):
        """测试按件计价的订单创建 - Requirements 1.1"""
        order = order_manager.create_order(
            order_number="ORD001",
            customer_id="CUST001",
            order_date=date(2024, 1, 15),
            product_name="铝型材氧化",
            pricing_unit=PricingUnit.PIECE,
            quantity=Decimal("100"),
            unit_price=Decimal("5.50"),
            notes="测试订单"
        )
        
        assert order.order_number == "ORD001"
        assert order.pricing_unit == PricingUnit.PIECE
        assert order.quantity == Decimal("100")
        assert order.unit_price == Decimal("5.50")
        assert order.total_amount == Decimal("550.00")
        assert order.status == OrderStatus.PENDING
        assert order.received_amount == Decimal("0")
        assert order.outsourced_cost == Decimal("0")
    
    def test_create_order_with_strip_unit(self, order_manager):
        """测试按条计价的订单创建 - Requirements 1.1"""
        order = order_manager.create_order(
            order_number="ORD002",
            customer_id="CUST001",
            order_date=date(2024, 1, 16),
            product_name="铝条氧化",
            pricing_unit=PricingUnit.STRIP,
            quantity=Decimal("200"),
            unit_price=Decimal("3.20"),
            notes=""
        )
        
        assert order.pricing_unit == PricingUnit.STRIP
        assert order.total_amount == Decimal("640.00")
    
    def test_create_order_with_item_unit(self, order_manager):
        """测试按只计价的订单创建 - Requirements 1.2"""
        order = order_manager.create_order(
            order_number="ORD003",
            customer_id="CUST002",
            order_date=date(2024, 1, 17),
            product_name="铝件氧化",
            pricing_unit=PricingUnit.ITEM,
            quantity=Decimal("50"),
            unit_price=Decimal("12.00"),
            notes=""
        )
        
        assert order.pricing_unit == PricingUnit.ITEM
        assert order.total_amount == Decimal("600.00")
    
    def test_create_order_with_unit_unit(self, order_manager):
        """测试按个计价的订单创建 - Requirements 1.2"""
        order = order_manager.create_order(
            order_number="ORD004",
            customer_id="CUST002",
            order_date=date(2024, 1, 18),
            product_name="铝配件氧化",
            pricing_unit=PricingUnit.UNIT,
            quantity=Decimal("300"),
            unit_price=Decimal("2.50"),
            notes=""
        )
        
        assert order.pricing_unit == PricingUnit.UNIT
        assert order.total_amount == Decimal("750.00")
    
    def test_create_order_with_meter_length_unit(self, order_manager):
        """测试按米长计价的订单创建 - Requirements 1.3"""
        order = order_manager.create_order(
            order_number="ORD005",
            customer_id="CUST003",
            order_date=date(2024, 1, 19),
            product_name="长铝材氧化",
            pricing_unit=PricingUnit.METER_LENGTH,
            quantity=Decimal("150.5"),
            unit_price=Decimal("8.00"),
            notes=""
        )
        
        assert order.pricing_unit == PricingUnit.METER_LENGTH
        assert order.total_amount == Decimal("1204.00")
    
    def test_create_order_with_meter_weight_unit(self, order_manager):
        """测试按米重计价的订单创建 - Requirements 1.3"""
        order = order_manager.create_order(
            order_number="ORD006",
            customer_id="CUST003",
            order_date=date(2024, 1, 20),
            product_name="重型铝材氧化",
            pricing_unit=PricingUnit.METER_WEIGHT,
            quantity=Decimal("85.3"),
            unit_price=Decimal("15.50"),
            notes=""
        )
        
        assert order.pricing_unit == PricingUnit.METER_WEIGHT
        assert order.total_amount == Decimal("1322.15")
    
    def test_create_order_with_square_meter_unit(self, order_manager):
        """测试按平方计价的订单创建 - Requirements 1.4"""
        order = order_manager.create_order(
            order_number="ORD007",
            customer_id="CUST004",
            order_date=date(2024, 1, 21),
            product_name="铝板氧化",
            pricing_unit=PricingUnit.SQUARE_METER,
            quantity=Decimal("25.8"),
            unit_price=Decimal("45.00"),
            notes=""
        )
        
        assert order.pricing_unit == PricingUnit.SQUARE_METER
        assert order.total_amount == Decimal("1161.00")
    
    def test_order_total_calculation(self, order_manager):
        """测试订单金额自动计算 - Requirements 1.5"""
        order = order_manager.create_order(
            order_number="ORD008",
            customer_id="CUST001",
            order_date=date(2024, 1, 22),
            product_name="测试产品",
            pricing_unit=PricingUnit.PIECE,
            quantity=Decimal("123.45"),
            unit_price=Decimal("67.89"),
            notes=""
        )
        
        expected_total = Decimal("123.45") * Decimal("67.89")
        assert order.total_amount == expected_total
    
    def test_order_persistence(self, order_manager):
        """测试订单数据持久化"""
        order = order_manager.create_order(
            order_number="ORD009",
            customer_id="CUST001",
            order_date=date(2024, 1, 23),
            product_name="持久化测试",
            pricing_unit=PricingUnit.PIECE,
            quantity=Decimal("10"),
            unit_price=Decimal("5"),
            notes=""
        )
        
        # 创建新的管理器实例，应该能加载之前保存的订单
        new_manager = ProcessingOrderManager(data_dir=order_manager.data_dir)
        loaded_order = new_manager.get_order(order.id)
        
        assert loaded_order is not None
        assert loaded_order.order_number == "ORD009"
        assert loaded_order.total_amount == Decimal("50")


class TestOrderQuery:
    """测试订单查询功能"""
    
    @pytest.fixture
    def populated_manager(self, order_manager):
        """创建包含多个订单的管理器"""
        # 创建不同客户、日期、状态的订单
        order_manager.create_order(
            "ORD101", "CUST001", date(2024, 1, 10),
            "产品A", PricingUnit.PIECE, Decimal("100"), Decimal("5")
        )
        order_manager.create_order(
            "ORD102", "CUST001", date(2024, 1, 15),
            "产品B", PricingUnit.STRIP, Decimal("200"), Decimal("3")
        )
        order_manager.create_order(
            "ORD103", "CUST002", date(2024, 1, 20),
            "产品C", PricingUnit.METER_LENGTH, Decimal("150"), Decimal("8")
        )
        order_manager.create_order(
            "ORD104", "CUST002", date(2024, 2, 5),
            "产品D", PricingUnit.SQUARE_METER, Decimal("50"), Decimal("45")
        )
        
        # 更新部分订单状态
        # ORD101 (CUST001, Jan 10) -> COMPLETED
        # ORD102 (CUST001, Jan 15) -> IN_PROGRESS
        order1 = order_manager.get_order_by_number("ORD101")
        order2 = order_manager.get_order_by_number("ORD102")
        order_manager.update_order_status(order1.id, OrderStatus.COMPLETED)
        order_manager.update_order_status(order2.id, OrderStatus.IN_PROGRESS)
        
        return order_manager
    
    def test_get_order_by_id(self, populated_manager):
        """测试按ID获取订单"""
        orders = populated_manager.get_all_orders()
        order = populated_manager.get_order(orders[0].id)
        
        assert order is not None
        assert order.id == orders[0].id
    
    def test_get_order_by_number(self, populated_manager):
        """测试按订单编号获取订单"""
        order = populated_manager.get_order_by_number("ORD102")
        
        assert order is not None
        assert order.order_number == "ORD102"
    
    def test_query_orders_by_customer(self, populated_manager):
        """测试按客户筛选订单"""
        orders = populated_manager.query_orders(customer_id="CUST001")
        
        assert len(orders) == 2
        assert all(o.customer_id == "CUST001" for o in orders)
    
    def test_query_orders_by_date_range(self, populated_manager):
        """测试按日期范围筛选订单"""
        orders = populated_manager.query_orders(
            start_date=date(2024, 1, 12),
            end_date=date(2024, 1, 25)
        )
        
        assert len(orders) == 2
        assert all(date(2024, 1, 12) <= o.order_date <= date(2024, 1, 25) for o in orders)
    
    def test_query_orders_by_status(self, populated_manager):
        """测试按状态筛选订单"""
        orders = populated_manager.query_orders(status=OrderStatus.PENDING)
        
        assert len(orders) == 2
        assert all(o.status == OrderStatus.PENDING for o in orders)
    
    def test_query_orders_by_pricing_unit(self, populated_manager):
        """测试按计价单位筛选订单"""
        orders = populated_manager.query_orders(pricing_unit=PricingUnit.PIECE)
        
        assert len(orders) == 1
        assert orders[0].pricing_unit == PricingUnit.PIECE
    
    def test_query_orders_with_multiple_filters(self, populated_manager):
        """测试组合筛选条件"""
        orders = populated_manager.query_orders(
            customer_id="CUST001",
            start_date=date(2024, 1, 1),
            end_date=date(2024, 1, 31),
            status=OrderStatus.IN_PROGRESS
        )
        
        assert len(orders) == 1
        assert orders[0].customer_id == "CUST001"
        assert orders[0].status == OrderStatus.IN_PROGRESS
    
    def test_get_all_orders(self, populated_manager):
        """测试获取所有订单"""
        orders = populated_manager.get_all_orders()
        
        assert len(orders) == 4
        # 验证按日期降序排序
        for i in range(len(orders) - 1):
            assert orders[i].order_date >= orders[i + 1].order_date


class TestOrderUpdates:
    """测试订单更新功能"""
    
    @pytest.fixture
    def order_with_manager(self, order_manager):
        """创建一个订单并返回管理器和订单"""
        order = order_manager.create_order(
            "ORD201", "CUST001", date(2024, 1, 10),
            "测试产品", PricingUnit.PIECE, Decimal("100"), Decimal("10")
        )
        return order_manager, order
    
    def test_update_order_status(self, order_with_manager):
        """测试更新订单状态"""
        manager, order = order_with_manager
        
        success = manager.update_order_status(order.id, OrderStatus.IN_PROGRESS)
        assert success is True
        
        updated_order = manager.get_order(order.id)
        assert updated_order.status == OrderStatus.IN_PROGRESS
    
    def test_update_received_amount_add(self, order_with_manager):
        """测试增加已收款金额"""
        manager, order = order_with_manager
        
        # 第一次收款
        success = manager.update_received_amount(order.id, Decimal("300"), add=True)
        assert success is True
        
        updated_order = manager.get_order(order.id)
        assert updated_order.received_amount == Decimal("300")
        
        # 第二次收款
        manager.update_received_amount(order.id, Decimal("200"), add=True)
        updated_order = manager.get_order(order.id)
        assert updated_order.received_amount == Decimal("500")
    
    def test_update_received_amount_set(self, order_with_manager):
        """测试设置已收款金额"""
        manager, order = order_with_manager
        
        success = manager.update_received_amount(order.id, Decimal("800"), add=False)
        assert success is True
        
        updated_order = manager.get_order(order.id)
        assert updated_order.received_amount == Decimal("800")
    
    def test_update_outsourced_cost_add(self, order_with_manager):
        """测试增加外发成本"""
        manager, order = order_with_manager
        
        # 第一次外发
        success = manager.update_outsourced_cost(order.id, Decimal("150"), add=True)
        assert success is True
        
        updated_order = manager.get_order(order.id)
        assert updated_order.outsourced_cost == Decimal("150")
        
        # 第二次外发
        manager.update_outsourced_cost(order.id, Decimal("100"), add=True)
        updated_order = manager.get_order(order.id)
        assert updated_order.outsourced_cost == Decimal("250")
    
    def test_update_outsourced_cost_set(self, order_with_manager):
        """测试设置外发成本"""
        manager, order = order_with_manager
        
        success = manager.update_outsourced_cost(order.id, Decimal("400"), add=False)
        assert success is True
        
        updated_order = manager.get_order(order.id)
        assert updated_order.outsourced_cost == Decimal("400")
    
    def test_update_nonexistent_order(self, order_manager):
        """测试更新不存在的订单"""
        success = order_manager.update_order_status("INVALID_ID", OrderStatus.COMPLETED)
        assert success is False


class TestOrderCalculations:
    """测试订单计算功能"""
    
    def test_get_order_balance(self, order_manager):
        """测试获取订单余额"""
        order = order_manager.create_order(
            "ORD301", "CUST001", date(2024, 1, 10),
            "测试产品", PricingUnit.PIECE, Decimal("100"), Decimal("10")
        )
        
        # 初始余额应该等于总金额
        balance = order_manager.get_order_balance(order.id)
        assert balance == Decimal("1000")
        
        # 收款后余额减少
        order_manager.update_received_amount(order.id, Decimal("300"))
        balance = order_manager.get_order_balance(order.id)
        assert balance == Decimal("700")
    
    def test_get_order_profit(self, order_manager):
        """测试获取订单利润"""
        order = order_manager.create_order(
            "ORD302", "CUST001", date(2024, 1, 10),
            "测试产品", PricingUnit.PIECE, Decimal("100"), Decimal("10")
        )
        
        # 初始利润等于总金额（无成本）
        profit = order_manager.get_order_profit(order.id)
        assert profit == Decimal("1000")
        
        # 增加外发成本后利润减少
        order_manager.update_outsourced_cost(order.id, Decimal("400"))
        profit = order_manager.get_order_profit(order.id)
        assert profit == Decimal("600")


class TestOrderStatistics:
    """测试订单统计功能"""
    
    @pytest.fixture
    def manager_with_data(self, order_manager):
        """创建包含多个订单的管理器"""
        # 创建不同状态和计价单位的订单
        order1 = order_manager.create_order(
            "ORD401", "CUST001", date(2024, 1, 10),
            "产品A", PricingUnit.PIECE, Decimal("100"), Decimal("10")
        )
        order2 = order_manager.create_order(
            "ORD402", "CUST002", date(2024, 1, 15),
            "产品B", PricingUnit.METER_LENGTH, Decimal("50"), Decimal("20")
        )
        order3 = order_manager.create_order(
            "ORD403", "CUST001", date(2024, 2, 5),
            "产品C", PricingUnit.SQUARE_METER, Decimal("30"), Decimal("50")
        )
        
        # 更新收款和成本
        order_manager.update_received_amount(order1.id, Decimal("500"))
        order_manager.update_outsourced_cost(order1.id, Decimal("300"))
        order_manager.update_order_status(order1.id, OrderStatus.COMPLETED)
        
        order_manager.update_received_amount(order2.id, Decimal("1000"))
        order_manager.update_order_status(order2.id, OrderStatus.IN_PROGRESS)
        
        return order_manager
    
    def test_get_statistics_all_orders(self, manager_with_data):
        """测试获取所有订单统计"""
        stats = manager_with_data.get_statistics()
        
        assert stats["total_orders"] == 3
        assert Decimal(stats["total_amount"]) == Decimal("3500")  # 1000 + 1000 + 1500
        assert Decimal(stats["total_received"]) == Decimal("1500")  # 500 + 1000
        assert Decimal(stats["total_outsourced_cost"]) == Decimal("300")
        assert Decimal(stats["total_balance"]) == Decimal("2000")  # 3500 - 1500
        assert Decimal(stats["total_profit"]) == Decimal("3200")  # 3500 - 300
    
    def test_get_statistics_by_date_range(self, manager_with_data):
        """测试按日期范围统计"""
        stats = manager_with_data.get_statistics(
            start_date=date(2024, 1, 1),
            end_date=date(2024, 1, 31)
        )
        
        assert stats["total_orders"] == 2
        assert Decimal(stats["total_amount"]) == Decimal("2000")  # 1000 + 1000
    
    def test_statistics_by_status(self, manager_with_data):
        """测试按状态统计"""
        stats = manager_with_data.get_statistics()
        
        assert stats["status_statistics"]["completed"] == 1
        assert stats["status_statistics"]["in_progress"] == 1
        assert stats["status_statistics"]["pending"] == 1
    
    def test_statistics_by_pricing_unit(self, manager_with_data):
        """测试按计价单位统计"""
        stats = manager_with_data.get_statistics()
        
        unit_stats = stats["pricing_unit_statistics"]
        assert unit_stats["piece"]["count"] == 1
        assert Decimal(unit_stats["piece"]["total_amount"]) == Decimal("1000")
        assert unit_stats["meter_length"]["count"] == 1
        assert Decimal(unit_stats["meter_length"]["total_amount"]) == Decimal("1000")
        assert unit_stats["square_meter"]["count"] == 1
        assert Decimal(unit_stats["square_meter"]["total_amount"]) == Decimal("1500")


class TestEdgeCases:
    """测试边界情况"""
    
    def test_create_order_with_zero_quantity(self, order_manager):
        """测试创建数量为0的订单"""
        order = order_manager.create_order(
            "ORD501", "CUST001", date(2024, 1, 10),
            "测试产品", PricingUnit.PIECE, Decimal("0"), Decimal("10")
        )
        
        assert order.total_amount == Decimal("0")
    
    def test_create_order_with_decimal_quantity(self, order_manager):
        """测试创建小数数量的订单"""
        order = order_manager.create_order(
            "ORD502", "CUST001", date(2024, 1, 10),
            "测试产品", PricingUnit.METER_LENGTH, Decimal("12.345"), Decimal("8.99")
        )
        
        expected_total = Decimal("12.345") * Decimal("8.99")
        assert order.total_amount == expected_total
    
    def test_query_with_no_results(self, order_manager):
        """测试查询无结果的情况"""
        orders = order_manager.query_orders(customer_id="NONEXISTENT")
        
        assert len(orders) == 0
    
    def test_get_nonexistent_order(self, order_manager):
        """测试获取不存在的订单"""
        order = order_manager.get_order("INVALID_ID")
        
        assert order is None
    
    def test_get_balance_for_nonexistent_order(self, order_manager):
        """测试获取不存在订单的余额"""
        balance = order_manager.get_order_balance("INVALID_ID")
        
        assert balance is None
