#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
订单管理器单元测试
"""

import pytest
from datetime import date, datetime
from decimal import Decimal
import tempfile
import os

from oxidation_finance_v20.models.business_models import (
    ProcessingOrder, Customer, OrderStatus, PricingUnit, ProcessType
)
from oxidation_finance_v20.database.db_manager import DatabaseManager
from oxidation_finance_v20.business.order_manager import OrderManager


@pytest.fixture
def db_manager():
    """创建临时数据库管理器"""
    # 创建临时数据库文件
    fd, db_path = tempfile.mkstemp(suffix='.db')
    os.close(fd)
    
    db = DatabaseManager(db_path)
    db.connect()
    
    yield db
    
    # 清理
    db.close()
    os.unlink(db_path)


@pytest.fixture
def order_manager(db_manager):
    """创建订单管理器"""
    return OrderManager(db_manager)


@pytest.fixture
def sample_customer(db_manager):
    """创建示例客户"""
    customer = Customer(
        name="测试客户",
        contact="张三",
        phone="13800138000",
        address="测试地址",
        credit_limit=Decimal("100000")
    )
    db_manager.save_customer(customer)
    return customer


class TestOrderCreation:
    """测试订单创建功能"""
    
    def test_create_basic_order(self, order_manager, sample_customer):
        """测试创建基本订单"""
        order = order_manager.create_order(
            customer_id=sample_customer.id,
            customer_name=sample_customer.name,
            item_description="铝型材",
            quantity=Decimal("100"),
            pricing_unit=PricingUnit.PIECE,
            unit_price=Decimal("5.5"),
            processes=[ProcessType.SANDBLASTING, ProcessType.OXIDATION]
        )
        
        assert order is not None
        assert order.customer_id == sample_customer.id
        assert order.customer_name == sample_customer.name
        assert order.item_description == "铝型材"
        assert order.quantity == Decimal("100")
        assert order.pricing_unit == PricingUnit.PIECE
        assert order.unit_price == Decimal("5.5")
        assert order.total_amount == Decimal("550")  # 100 * 5.5
        assert order.status == OrderStatus.PENDING
        assert len(order.processes) == 2
        assert ProcessType.SANDBLASTING in order.processes
        assert ProcessType.OXIDATION in order.processes
    
    def test_create_order_with_all_pricing_units(self, order_manager, sample_customer):
        """测试七种计价方式"""
        pricing_units = [
            PricingUnit.PIECE,      # 件
            PricingUnit.STRIP,      # 条
            PricingUnit.UNIT,       # 只
            PricingUnit.ITEM,       # 个
            PricingUnit.METER,      # 米
            PricingUnit.KILOGRAM,   # 公斤
            PricingUnit.SQUARE_METER  # 平方米
        ]
        
        for pricing_unit in pricing_units:
            order = order_manager.create_order(
                customer_id=sample_customer.id,
                customer_name=sample_customer.name,
                item_description=f"测试物品-{pricing_unit.value}",
                quantity=Decimal("10"),
                pricing_unit=pricing_unit,
                unit_price=Decimal("2.0"),
                processes=[ProcessType.OXIDATION]
            )
            
            assert order.pricing_unit == pricing_unit
            assert order.total_amount == Decimal("20")  # 10 * 2.0
    
    def test_create_order_with_outsourced_processes(self, order_manager, sample_customer):
        """测试创建包含委外工序的订单"""
        order = order_manager.create_order(
            customer_id=sample_customer.id,
            customer_name=sample_customer.name,
            item_description="铝板",
            quantity=Decimal("50"),
            pricing_unit=PricingUnit.SQUARE_METER,
            unit_price=Decimal("15.0"),
            processes=[ProcessType.POLISHING, ProcessType.OXIDATION],
            outsourced_processes=["抛光"]
        )
        
        assert order is not None
        assert len(order.outsourced_processes) == 1
        assert "抛光" in order.outsourced_processes
    
    def test_order_number_generation(self, order_manager, sample_customer):
        """测试订单编号生成"""
        order1 = order_manager.create_order(
            customer_id=sample_customer.id,
            customer_name=sample_customer.name,
            item_description="物品1",
            quantity=Decimal("10"),
            pricing_unit=PricingUnit.PIECE,
            unit_price=Decimal("1.0"),
            processes=[ProcessType.OXIDATION]
        )
        
        order2 = order_manager.create_order(
            customer_id=sample_customer.id,
            customer_name=sample_customer.name,
            item_description="物品2",
            quantity=Decimal("20"),
            pricing_unit=PricingUnit.PIECE,
            unit_price=Decimal("2.0"),
            processes=[ProcessType.OXIDATION]
        )
        
        # 订单编号应该不同
        assert order1.order_no != order2.order_no
        
        # 订单编号格式应该正确
        today = date.today().strftime("%Y%m%d")
        assert order1.order_no.startswith(f"ORD-{today}-")
        assert order2.order_no.startswith(f"ORD-{today}-")


class TestOrderRetrieval:
    """测试订单查询功能"""
    
    def test_get_order_by_id(self, order_manager, sample_customer):
        """测试根据ID获取订单"""
        created_order = order_manager.create_order(
            customer_id=sample_customer.id,
            customer_name=sample_customer.name,
            item_description="测试物品",
            quantity=Decimal("10"),
            pricing_unit=PricingUnit.PIECE,
            unit_price=Decimal("5.0"),
            processes=[ProcessType.OXIDATION]
        )
        
        retrieved_order = order_manager.get_order(created_order.id)
        
        assert retrieved_order is not None
        assert retrieved_order.id == created_order.id
        assert retrieved_order.item_description == "测试物品"
    
    def test_get_order_by_no(self, order_manager, sample_customer):
        """测试根据订单编号获取订单"""
        created_order = order_manager.create_order(
            customer_id=sample_customer.id,
            customer_name=sample_customer.name,
            item_description="测试物品",
            quantity=Decimal("10"),
            pricing_unit=PricingUnit.PIECE,
            unit_price=Decimal("5.0"),
            processes=[ProcessType.OXIDATION]
        )
        
        retrieved_order = order_manager.get_order_by_no(created_order.order_no)
        
        assert retrieved_order is not None
        assert retrieved_order.order_no == created_order.order_no
    
    def test_list_all_orders(self, order_manager, sample_customer):
        """测试列出所有订单"""
        # 创建多个订单
        for i in range(3):
            order_manager.create_order(
                customer_id=sample_customer.id,
                customer_name=sample_customer.name,
                item_description=f"物品{i}",
                quantity=Decimal("10"),
                pricing_unit=PricingUnit.PIECE,
                unit_price=Decimal("1.0"),
                processes=[ProcessType.OXIDATION]
            )
        
        orders = order_manager.list_orders()
        assert len(orders) == 3
    
    def test_list_orders_by_customer(self, order_manager, db_manager):
        """测试按客户筛选订单"""
        # 创建两个客户
        customer1 = Customer(name="客户1")
        customer2 = Customer(name="客户2")
        db_manager.save_customer(customer1)
        db_manager.save_customer(customer2)
        
        # 为客户1创建2个订单
        for i in range(2):
            order_manager.create_order(
                customer_id=customer1.id,
                customer_name=customer1.name,
                item_description=f"物品{i}",
                quantity=Decimal("10"),
                pricing_unit=PricingUnit.PIECE,
                unit_price=Decimal("1.0"),
                processes=[ProcessType.OXIDATION]
            )
        
        # 为客户2创建1个订单
        order_manager.create_order(
            customer_id=customer2.id,
            customer_name=customer2.name,
            item_description="物品X",
            quantity=Decimal("10"),
            pricing_unit=PricingUnit.PIECE,
            unit_price=Decimal("1.0"),
            processes=[ProcessType.OXIDATION]
        )
        
        # 查询客户1的订单
        customer1_orders = order_manager.list_orders(customer_id=customer1.id)
        assert len(customer1_orders) == 2
        
        # 查询客户2的订单
        customer2_orders = order_manager.list_orders(customer_id=customer2.id)
        assert len(customer2_orders) == 1
    
    def test_list_orders_by_status(self, order_manager, sample_customer):
        """测试按状态筛选订单"""
        # 创建不同状态的订单
        order1 = order_manager.create_order(
            customer_id=sample_customer.id,
            customer_name=sample_customer.name,
            item_description="物品1",
            quantity=Decimal("10"),
            pricing_unit=PricingUnit.PIECE,
            unit_price=Decimal("1.0"),
            processes=[ProcessType.OXIDATION]
        )
        
        order2 = order_manager.create_order(
            customer_id=sample_customer.id,
            customer_name=sample_customer.name,
            item_description="物品2",
            quantity=Decimal("10"),
            pricing_unit=PricingUnit.PIECE,
            unit_price=Decimal("1.0"),
            processes=[ProcessType.OXIDATION]
        )
        
        # 更新订单2的状态
        order_manager.update_order_status(order2.id, OrderStatus.COMPLETED)
        
        # 查询待加工订单
        pending_orders = order_manager.list_orders(status=OrderStatus.PENDING)
        assert len(pending_orders) == 1
        assert pending_orders[0].id == order1.id
        
        # 查询已完工订单
        completed_orders = order_manager.list_orders(status=OrderStatus.COMPLETED)
        assert len(completed_orders) == 1
        assert completed_orders[0].id == order2.id


class TestOrderUpdate:
    """测试订单更新功能"""
    
    def test_update_order_status(self, order_manager, sample_customer):
        """测试更新订单状态"""
        order = order_manager.create_order(
            customer_id=sample_customer.id,
            customer_name=sample_customer.name,
            item_description="测试物品",
            quantity=Decimal("10"),
            pricing_unit=PricingUnit.PIECE,
            unit_price=Decimal("5.0"),
            processes=[ProcessType.OXIDATION]
        )
        
        # 更新状态为加工中
        updated_order = order_manager.update_order_status(
            order.id,
            OrderStatus.IN_PROGRESS
        )
        
        assert updated_order is not None
        assert updated_order.status == OrderStatus.IN_PROGRESS
        
        # 更新状态为已完工
        completion_date = date.today()
        updated_order = order_manager.update_order_status(
            order.id,
            OrderStatus.COMPLETED,
            completion_date=completion_date
        )
        
        assert updated_order.status == OrderStatus.COMPLETED
        assert updated_order.completion_date == completion_date
    
    def test_update_outsourcing_cost(self, order_manager, sample_customer):
        """测试更新委外加工成本"""
        order = order_manager.create_order(
            customer_id=sample_customer.id,
            customer_name=sample_customer.name,
            item_description="测试物品",
            quantity=Decimal("10"),
            pricing_unit=PricingUnit.PIECE,
            unit_price=Decimal("5.0"),
            processes=[ProcessType.POLISHING, ProcessType.OXIDATION],
            outsourced_processes=["抛光"]
        )
        
        # 更新委外成本
        updated_order = order_manager.update_outsourcing_cost(
            order.id,
            Decimal("100.0")
        )
        
        assert updated_order is not None
        assert updated_order.outsourcing_cost == Decimal("100.0")


class TestOrderCalculations:
    """测试订单计算功能"""
    
    def test_calculate_processing_fee(self, order_manager, sample_customer):
        """测试计算加工费用"""
        order = order_manager.create_order(
            customer_id=sample_customer.id,
            customer_name=sample_customer.name,
            item_description="测试物品",
            quantity=Decimal("10"),
            pricing_unit=PricingUnit.PIECE,
            unit_price=Decimal("5.0"),
            processes=[ProcessType.OXIDATION]
        )
        
        # 基础加工费
        fee = order_manager.calculate_processing_fee(order.id)
        assert fee == Decimal("50.0")  # 10 * 5.0
        
        # 添加委外成本
        order_manager.update_outsourcing_cost(order.id, Decimal("20.0"))
        
        # 总加工费 = 基础加工费 + 委外成本
        total_fee = order_manager.calculate_processing_fee(order.id)
        assert total_fee == Decimal("70.0")  # 50.0 + 20.0
    
    def test_get_order_balance(self, order_manager, sample_customer):
        """测试获取订单余额"""
        order = order_manager.create_order(
            customer_id=sample_customer.id,
            customer_name=sample_customer.name,
            item_description="测试物品",
            quantity=Decimal("10"),
            pricing_unit=PricingUnit.PIECE,
            unit_price=Decimal("5.0"),
            processes=[ProcessType.OXIDATION]
        )
        
        # 初始余额应该等于总金额
        balance = order_manager.get_order_balance(order.id)
        assert balance == Decimal("50.0")
        
        # 记录部分收款
        order_manager.record_payment(order.id, Decimal("30.0"))
        
        # 余额应该减少
        balance = order_manager.get_order_balance(order.id)
        assert balance == Decimal("20.0")  # 50.0 - 30.0


class TestOrderPayment:
    """测试订单收款功能"""
    
    def test_record_payment(self, order_manager, sample_customer):
        """测试记录收款"""
        order = order_manager.create_order(
            customer_id=sample_customer.id,
            customer_name=sample_customer.name,
            item_description="测试物品",
            quantity=Decimal("10"),
            pricing_unit=PricingUnit.PIECE,
            unit_price=Decimal("5.0"),
            processes=[ProcessType.OXIDATION]
        )
        
        # 记录部分收款
        updated_order = order_manager.record_payment(order.id, Decimal("30.0"))
        
        assert updated_order.received_amount == Decimal("30.0")
        assert updated_order.status != OrderStatus.PAID  # 未全额收款
        
        # 记录剩余收款
        updated_order = order_manager.record_payment(order.id, Decimal("20.0"))
        
        assert updated_order.received_amount == Decimal("50.0")
        assert updated_order.status == OrderStatus.PAID  # 全额收款


class TestProcessTracking:
    """测试工序跟踪功能"""
    
    def test_track_process_status(self, order_manager, sample_customer):
        """测试跟踪工序状态"""
        order = order_manager.create_order(
            customer_id=sample_customer.id,
            customer_name=sample_customer.name,
            item_description="测试物品",
            quantity=Decimal("10"),
            pricing_unit=PricingUnit.PIECE,
            unit_price=Decimal("5.0"),
            processes=[ProcessType.SANDBLASTING, ProcessType.POLISHING, ProcessType.OXIDATION]
        )
        
        # 待加工状态
        status = order_manager.track_process_status(order.id)
        assert status is not None
        assert status["喷砂"] == "待加工"
        assert status["抛光"] == "待加工"
        assert status["氧化"] == "待加工"
        
        # 更新为加工中
        order_manager.update_order_status(order.id, OrderStatus.IN_PROGRESS)
        status = order_manager.track_process_status(order.id)
        assert status["喷砂"] == "加工中"
        assert status["抛光"] == "加工中"
        assert status["氧化"] == "加工中"
        
        # 更新为已完工
        order_manager.update_order_status(order.id, OrderStatus.COMPLETED)
        status = order_manager.track_process_status(order.id)
        assert status["喷砂"] == "已完成"
        assert status["抛光"] == "已完成"
        assert status["氧化"] == "已完成"
    
    def test_track_outsourced_process_status(self, order_manager, sample_customer):
        """测试跟踪委外工序状态"""
        order = order_manager.create_order(
            customer_id=sample_customer.id,
            customer_name=sample_customer.name,
            item_description="测试物品",
            quantity=Decimal("10"),
            pricing_unit=PricingUnit.PIECE,
            unit_price=Decimal("5.0"),
            processes=[ProcessType.POLISHING, ProcessType.OXIDATION],
            outsourced_processes=["抛光"]
        )
        
        # 更新为委外中
        order_manager.update_order_status(order.id, OrderStatus.OUTSOURCED)
        status = order_manager.track_process_status(order.id)
        
        assert status["抛光"] == "委外中"
        assert status["氧化"] == "加工中"  # 委外中状态时，非委外工序也可能在加工中


class TestOrderDeletion:
    """测试订单删除功能"""
    
    def test_delete_order(self, order_manager, sample_customer):
        """测试删除订单"""
        order = order_manager.create_order(
            customer_id=sample_customer.id,
            customer_name=sample_customer.name,
            item_description="测试物品",
            quantity=Decimal("10"),
            pricing_unit=PricingUnit.PIECE,
            unit_price=Decimal("5.0"),
            processes=[ProcessType.OXIDATION]
        )
        
        # 删除订单
        result = order_manager.delete_order(order.id)
        assert result is True
        
        # 确认订单已删除
        deleted_order = order_manager.get_order(order.id)
        assert deleted_order is None
    
    def test_cannot_delete_paid_order(self, order_manager, sample_customer):
        """测试不能删除已收款的订单"""
        order = order_manager.create_order(
            customer_id=sample_customer.id,
            customer_name=sample_customer.name,
            item_description="测试物品",
            quantity=Decimal("10"),
            pricing_unit=PricingUnit.PIECE,
            unit_price=Decimal("5.0"),
            processes=[ProcessType.OXIDATION]
        )
        
        # 记录收款
        order_manager.record_payment(order.id, Decimal("10.0"))
        
        # 尝试删除应该失败
        with pytest.raises(ValueError, match="已收款的订单不能删除"):
            order_manager.delete_order(order.id)


class TestPricingUnitQueries:
    """测试按计价方式查询"""
    
    def test_get_orders_by_pricing_unit(self, order_manager, sample_customer):
        """测试按计价方式查询订单"""
        # 创建不同计价方式的订单
        order_manager.create_order(
            customer_id=sample_customer.id,
            customer_name=sample_customer.name,
            item_description="按件计价",
            quantity=Decimal("10"),
            pricing_unit=PricingUnit.PIECE,
            unit_price=Decimal("1.0"),
            processes=[ProcessType.OXIDATION]
        )
        
        order_manager.create_order(
            customer_id=sample_customer.id,
            customer_name=sample_customer.name,
            item_description="按米计价",
            quantity=Decimal("20"),
            pricing_unit=PricingUnit.METER,
            unit_price=Decimal("2.0"),
            processes=[ProcessType.OXIDATION]
        )
        
        order_manager.create_order(
            customer_id=sample_customer.id,
            customer_name=sample_customer.name,
            item_description="按件计价2",
            quantity=Decimal("30"),
            pricing_unit=PricingUnit.PIECE,
            unit_price=Decimal("3.0"),
            processes=[ProcessType.OXIDATION]
        )
        
        # 查询按件计价的订单
        piece_orders = order_manager.get_orders_by_pricing_unit(PricingUnit.PIECE)
        assert len(piece_orders) == 2
        
        # 查询按米计价的订单
        meter_orders = order_manager.get_orders_by_pricing_unit(PricingUnit.METER)
        assert len(meter_orders) == 1
