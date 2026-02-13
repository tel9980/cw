"""
Integration tests for Outsourced Processing Manager and Order Manager

Tests the integration between outsourced processing and order management,
including cost tracking and order updates.

Requirements: 5.5
"""

import pytest
import tempfile
import shutil
from datetime import date
from decimal import Decimal

from oxidation_workflow_v18.models.core_models import (
    ProcessType,
    PricingUnit
)
from oxidation_workflow_v18.business.order_manager import ProcessingOrderManager
from oxidation_workflow_v18.business.outsourced_processing_manager import (
    OutsourcedProcessingManager
)


@pytest.fixture
def temp_data_dir():
    """创建临时数据目录"""
    temp_dir = tempfile.mkdtemp()
    yield temp_dir
    shutil.rmtree(temp_dir)


@pytest.fixture
def order_manager(temp_data_dir):
    """创建订单管理器实例"""
    return ProcessingOrderManager(data_dir=temp_data_dir)


@pytest.fixture
def processing_manager(temp_data_dir):
    """创建外发加工管理器实例"""
    return OutsourcedProcessingManager(data_dir=temp_data_dir)


class TestOutsourcedProcessingOrderIntegration:
    """测试外发加工与订单的集成"""
    
    def test_link_outsourced_processing_to_order(
        self,
        order_manager,
        processing_manager
    ):
        """测试将外发加工关联到订单
        
        Requirements: 5.5
        """
        # 1. 创建订单
        order = order_manager.create_order(
            order_number="ORD-001",
            customer_id="customer-001",
            order_date=date(2024, 1, 15),
            product_name="铝型材氧化",
            pricing_unit=PricingUnit.PIECE,
            quantity=Decimal("100"),
            unit_price=Decimal("50"),
            notes="测试订单"
        )
        
        assert order.total_amount == Decimal("5000")
        assert order.outsourced_cost == Decimal("0")
        
        # 2. 创建外发加工记录
        processing1 = processing_manager.create_processing(
            order_id=order.id,
            supplier_id="supplier-001",
            process_type=ProcessType.SANDBLASTING,
            process_date=date(2024, 1, 16),
            quantity=Decimal("100"),
            unit_price=Decimal("2.5"),
            notes="喷砂加工"
        )
        
        processing2 = processing_manager.create_processing(
            order_id=order.id,
            supplier_id="supplier-002",
            process_type=ProcessType.WIRE_DRAWING,
            process_date=date(2024, 1, 17),
            quantity=Decimal("100"),
            unit_price=Decimal("3.0"),
            notes="拉丝加工"
        )
        
        # 3. 计算外发加工总成本
        total_outsourced_cost = processing_manager.get_order_total_cost(order.id)
        assert total_outsourced_cost == Decimal("550")  # 250 + 300
        
        # 4. 更新订单的外发成本
        order_manager.update_outsourced_cost(order.id, total_outsourced_cost, add=False)
        
        # 5. 验证订单利润
        updated_order = order_manager.get_order(order.id)
        assert updated_order.outsourced_cost == Decimal("550")
        assert updated_order.get_profit() == Decimal("4450")  # 5000 - 550
    
    def test_multiple_orders_with_outsourced_processing(
        self,
        order_manager,
        processing_manager
    ):
        """测试多个订单的外发加工管理
        
        Requirements: 5.5
        """
        # 创建两个订单
        order1 = order_manager.create_order(
            order_number="ORD-001",
            customer_id="customer-001",
            order_date=date(2024, 1, 15),
            product_name="铝型材氧化",
            pricing_unit=PricingUnit.PIECE,
            quantity=Decimal("100"),
            unit_price=Decimal("50")
        )
        
        order2 = order_manager.create_order(
            order_number="ORD-002",
            customer_id="customer-002",
            order_date=date(2024, 1, 16),
            product_name="铝板氧化",
            pricing_unit=PricingUnit.SQUARE_METER,
            quantity=Decimal("50"),
            unit_price=Decimal("80")
        )
        
        # 为订单1创建外发加工
        processing_manager.create_processing(
            order_id=order1.id,
            supplier_id="supplier-001",
            process_type=ProcessType.SANDBLASTING,
            process_date=date(2024, 1, 16),
            quantity=Decimal("100"),
            unit_price=Decimal("2.5")
        )
        
        # 为订单2创建外发加工
        processing_manager.create_processing(
            order_id=order2.id,
            supplier_id="supplier-002",
            process_type=ProcessType.POLISHING,
            process_date=date(2024, 1, 17),
            quantity=Decimal("50"),
            unit_price=Decimal("5.0")
        )
        
        # 验证各订单的外发成本
        order1_cost = processing_manager.get_order_total_cost(order1.id)
        order2_cost = processing_manager.get_order_total_cost(order2.id)
        
        assert order1_cost == Decimal("250")
        assert order2_cost == Decimal("250")
        
        # 更新订单成本
        order_manager.update_outsourced_cost(order1.id, order1_cost, add=False)
        order_manager.update_outsourced_cost(order2.id, order2_cost, add=False)
        
        # 验证利润
        updated_order1 = order_manager.get_order(order1.id)
        updated_order2 = order_manager.get_order(order2.id)
        
        assert updated_order1.get_profit() == Decimal("4750")  # 5000 - 250
        assert updated_order2.get_profit() == Decimal("3750")  # 4000 - 250
    
    def test_update_outsourced_processing_updates_order_cost(
        self,
        order_manager,
        processing_manager
    ):
        """测试更新外发加工后更新订单成本
        
        Requirements: 5.5
        """
        # 创建订单
        order = order_manager.create_order(
            order_number="ORD-001",
            customer_id="customer-001",
            order_date=date(2024, 1, 15),
            product_name="铝型材氧化",
            pricing_unit=PricingUnit.PIECE,
            quantity=Decimal("100"),
            unit_price=Decimal("50")
        )
        
        # 创建外发加工
        processing = processing_manager.create_processing(
            order_id=order.id,
            supplier_id="supplier-001",
            process_type=ProcessType.SANDBLASTING,
            process_date=date(2024, 1, 16),
            quantity=Decimal("100"),
            unit_price=Decimal("2.5")
        )
        
        # 初始成本
        initial_cost = processing_manager.get_order_total_cost(order.id)
        order_manager.update_outsourced_cost(order.id, initial_cost, add=False)
        
        updated_order = order_manager.get_order(order.id)
        assert updated_order.outsourced_cost == Decimal("250")
        
        # 更新外发加工数量
        processing_manager.update_processing(
            processing.id,
            quantity=Decimal("150")
        )
        
        # 重新计算成本
        new_cost = processing_manager.get_order_total_cost(order.id)
        order_manager.update_outsourced_cost(order.id, new_cost, add=False)
        
        updated_order = order_manager.get_order(order.id)
        assert updated_order.outsourced_cost == Decimal("375")  # 150 * 2.5
        assert updated_order.get_profit() == Decimal("4625")  # 5000 - 375
    
    def test_query_orders_with_outsourced_processing(
        self,
        order_manager,
        processing_manager
    ):
        """测试查询带有外发加工的订单
        
        Requirements: 5.5
        """
        # 创建多个订单
        order1 = order_manager.create_order(
            order_number="ORD-001",
            customer_id="customer-001",
            order_date=date(2024, 1, 15),
            product_name="铝型材氧化",
            pricing_unit=PricingUnit.PIECE,
            quantity=Decimal("100"),
            unit_price=Decimal("50")
        )
        
        order2 = order_manager.create_order(
            order_number="ORD-002",
            customer_id="customer-001",
            order_date=date(2024, 1, 16),
            product_name="铝板氧化",
            pricing_unit=PricingUnit.SQUARE_METER,
            quantity=Decimal("50"),
            unit_price=Decimal("80")
        )
        
        # 只为订单1创建外发加工
        processing_manager.create_processing(
            order_id=order1.id,
            supplier_id="supplier-001",
            process_type=ProcessType.SANDBLASTING,
            process_date=date(2024, 1, 16),
            quantity=Decimal("100"),
            unit_price=Decimal("2.5")
        )
        
        # 查询客户的所有订单
        customer_orders = order_manager.query_orders(customer_id="customer-001")
        assert len(customer_orders) == 2
        
        # 检查哪些订单有外发加工
        for order in customer_orders:
            outsourced_cost = processing_manager.get_order_total_cost(order.id)
            if order.id == order1.id:
                assert outsourced_cost == Decimal("250")
            else:
                assert outsourced_cost == Decimal("0")
    
    def test_complete_order_workflow_with_outsourcing(
        self,
        order_manager,
        processing_manager
    ):
        """测试完整的订单工作流（包含外发加工）
        
        Requirements: 5.1, 5.2, 5.3, 5.5
        """
        # 1. 创建订单
        order = order_manager.create_order(
            order_number="ORD-001",
            customer_id="customer-001",
            order_date=date(2024, 1, 15),
            product_name="铝型材氧化",
            pricing_unit=PricingUnit.PIECE,
            quantity=Decimal("100"),
            unit_price=Decimal("50"),
            notes="客户订单"
        )
        
        # 2. 添加多个外发加工工序
        processing_manager.create_processing(
            order_id=order.id,
            supplier_id="supplier-001",
            process_type=ProcessType.SANDBLASTING,
            process_date=date(2024, 1, 16),
            quantity=Decimal("100"),
            unit_price=Decimal("2.5"),
            notes="喷砂处理"
        )
        
        processing_manager.create_processing(
            order_id=order.id,
            supplier_id="supplier-002",
            process_type=ProcessType.WIRE_DRAWING,
            process_date=date(2024, 1, 17),
            quantity=Decimal("100"),
            unit_price=Decimal("3.0"),
            notes="拉丝处理"
        )
        
        processing_manager.create_processing(
            order_id=order.id,
            supplier_id="supplier-003",
            process_type=ProcessType.POLISHING,
            process_date=date(2024, 1, 18),
            quantity=Decimal("100"),
            unit_price=Decimal("4.0"),
            notes="抛光处理"
        )
        
        # 3. 计算总外发成本
        total_outsourced_cost = processing_manager.get_order_total_cost(order.id)
        assert total_outsourced_cost == Decimal("950")  # 250 + 300 + 400
        
        # 4. 更新订单成本
        order_manager.update_outsourced_cost(order.id, total_outsourced_cost, add=False)
        
        # 5. 记录收款
        order_manager.update_received_amount(order.id, Decimal("3000"), add=True)
        
        # 6. 验证订单状态
        updated_order = order_manager.get_order(order.id)
        assert updated_order.total_amount == Decimal("5000")
        assert updated_order.outsourced_cost == Decimal("950")
        assert updated_order.received_amount == Decimal("3000")
        assert updated_order.get_balance() == Decimal("2000")  # 未收款
        assert updated_order.get_profit() == Decimal("4050")  # 5000 - 950
        
        # 7. 获取外发加工明细
        processing_records = processing_manager.get_processing_by_order(order.id)
        assert len(processing_records) == 3
        
        # 验证按日期排序
        assert processing_records[0].process_date == date(2024, 1, 16)
        assert processing_records[1].process_date == date(2024, 1, 17)
        assert processing_records[2].process_date == date(2024, 1, 18)
        
        # 8. 获取统计信息
        stats = processing_manager.get_statistics_by_process_type()
        assert stats[ProcessType.SANDBLASTING.value]["count"] == 1
        assert stats[ProcessType.WIRE_DRAWING.value]["count"] == 1
        assert stats[ProcessType.POLISHING.value]["count"] == 1
