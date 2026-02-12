#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
委外加工管理器单元测试
"""

import pytest
from datetime import date
from decimal import Decimal
import tempfile
import os

from business.outsourced_processing_manager import OutsourcedProcessingManager
from database.db_manager import DatabaseManager
from models.business_models import (
    ProcessType, Supplier, ProcessingOrder, Customer,
    PricingUnit, OrderStatus
)


@pytest.fixture
def db_manager():
    """创建临时数据库管理器"""
    temp_db = tempfile.NamedTemporaryFile(delete=False, suffix='.db')
    temp_db.close()
    
    db = DatabaseManager(temp_db.name)
    db.connect()
    
    yield db
    
    db.close()
    os.unlink(temp_db.name)


@pytest.fixture
def processing_manager(db_manager):
    """创建委外加工管理器"""
    return OutsourcedProcessingManager(db_manager)


@pytest.fixture
def sample_supplier(db_manager):
    """创建示例供应商"""
    supplier = Supplier(
        name="测试委外供应商",
        contact="张三",
        phone="13800138000",
        business_type="委外加工"
    )
    db_manager.save_supplier(supplier)
    return supplier


@pytest.fixture
def sample_order(db_manager):
    """创建示例订单"""
    customer = Customer(
        name="测试客户",
        contact="李四",
        phone="13900139000"
    )
    db_manager.save_customer(customer)
    
    order = ProcessingOrder(
        order_no="ORD-20240101-0001",
        customer_id=customer.id,
        customer_name=customer.name,
        item_description="铝型材",
        quantity=Decimal("100"),
        pricing_unit=PricingUnit.PIECE,
        unit_price=Decimal("10"),
        processes=[ProcessType.SANDBLASTING, ProcessType.OXIDATION],
        total_amount=Decimal("1000"),
        status=OrderStatus.PENDING
    )
    db_manager.save_order(order)
    return order


class TestOutsourcedProcessingManager:
    """委外加工管理器测试类"""
    
    def test_create_processing(self, processing_manager, sample_order, sample_supplier):
        """测试创建委外加工记录"""
        processing = processing_manager.create_processing(
            order_id=sample_order.id,
            supplier_id=sample_supplier.id,
            supplier_name=sample_supplier.name,
            process_type=ProcessType.SANDBLASTING,
            quantity=Decimal("100"),
            unit_price=Decimal("2"),
            process_description="喷砂处理"
        )
        
        assert processing.id is not None
        assert processing.order_id == sample_order.id
        assert processing.supplier_id == sample_supplier.id
        assert processing.process_type == ProcessType.SANDBLASTING
        assert processing.quantity == Decimal("100")
        assert processing.unit_price == Decimal("2")
        assert processing.total_cost == Decimal("200")
        assert processing.paid_amount == Decimal("0")
    
    def test_get_processing(self, processing_manager, sample_order, sample_supplier):
        """测试获取委外加工记录"""
        # 创建记录
        created = processing_manager.create_processing(
            order_id=sample_order.id,
            supplier_id=sample_supplier.id,
            supplier_name=sample_supplier.name,
            process_type=ProcessType.WIRE_DRAWING,
            quantity=Decimal("50"),
            unit_price=Decimal("3")
        )
        
        # 获取记录
        retrieved = processing_manager.get_processing(created.id)
        
        assert retrieved is not None
        assert retrieved.id == created.id
        assert retrieved.process_type == ProcessType.WIRE_DRAWING
        assert retrieved.total_cost == Decimal("150")
    
    def test_list_processing_by_order(self, processing_manager, sample_order, sample_supplier):
        """测试按订单查询委外加工记录"""
        # 创建多个委外加工记录
        processing_manager.create_processing(
            order_id=sample_order.id,
            supplier_id=sample_supplier.id,
            supplier_name=sample_supplier.name,
            process_type=ProcessType.SANDBLASTING,
            quantity=Decimal("100"),
            unit_price=Decimal("2")
        )
        
        processing_manager.create_processing(
            order_id=sample_order.id,
            supplier_id=sample_supplier.id,
            supplier_name=sample_supplier.name,
            process_type=ProcessType.POLISHING,
            quantity=Decimal("100"),
            unit_price=Decimal("1.5")
        )
        
        # 查询订单的委外加工记录
        processing_list = processing_manager.list_processing_by_order(sample_order.id)
        
        assert len(processing_list) == 2
        assert all(p.order_id == sample_order.id for p in processing_list)
    
    def test_list_processing_by_supplier(self, processing_manager, sample_order, sample_supplier):
        """测试按供应商查询委外加工记录"""
        # 创建委外加工记录
        processing_manager.create_processing(
            order_id=sample_order.id,
            supplier_id=sample_supplier.id,
            supplier_name=sample_supplier.name,
            process_type=ProcessType.SANDBLASTING,
            quantity=Decimal("100"),
            unit_price=Decimal("2")
        )
        
        # 查询供应商的委外加工记录
        processing_list = processing_manager.list_processing_by_supplier(sample_supplier.id)
        
        assert len(processing_list) >= 1
        assert all(p.supplier_id == sample_supplier.id for p in processing_list)
    
    def test_get_order_total_cost(self, processing_manager, sample_order, sample_supplier):
        """测试获取订单的委外加工总成本"""
        # 创建多个委外加工记录
        processing_manager.create_processing(
            order_id=sample_order.id,
            supplier_id=sample_supplier.id,
            supplier_name=sample_supplier.name,
            process_type=ProcessType.SANDBLASTING,
            quantity=Decimal("100"),
            unit_price=Decimal("2")
        )
        
        processing_manager.create_processing(
            order_id=sample_order.id,
            supplier_id=sample_supplier.id,
            supplier_name=sample_supplier.name,
            process_type=ProcessType.POLISHING,
            quantity=Decimal("100"),
            unit_price=Decimal("1.5")
        )
        
        # 获取总成本
        total_cost = processing_manager.get_order_total_cost(sample_order.id)
        
        assert total_cost == Decimal("350")  # 200 + 150
    
    def test_record_payment(self, processing_manager, sample_order, sample_supplier):
        """测试记录委外加工付款"""
        # 创建委外加工记录
        processing = processing_manager.create_processing(
            order_id=sample_order.id,
            supplier_id=sample_supplier.id,
            supplier_name=sample_supplier.name,
            process_type=ProcessType.SANDBLASTING,
            quantity=Decimal("100"),
            unit_price=Decimal("2")
        )
        
        # 记录付款
        updated = processing_manager.record_payment(processing.id, Decimal("100"))
        
        assert updated is not None
        assert updated.paid_amount == Decimal("100")
        assert updated.get_unpaid_amount() == Decimal("100")
        assert not updated.is_fully_paid()
        
        # 再次付款
        updated = processing_manager.record_payment(processing.id, Decimal("100"))
        
        assert updated.paid_amount == Decimal("200")
        assert updated.get_unpaid_amount() == Decimal("0")
        assert updated.is_fully_paid()
    
    def test_allocate_payment_to_multiple(self, processing_manager, sample_order, sample_supplier):
        """测试将付款分配到多个委外加工记录"""
        # 创建多个委外加工记录
        p1 = processing_manager.create_processing(
            order_id=sample_order.id,
            supplier_id=sample_supplier.id,
            supplier_name=sample_supplier.name,
            process_type=ProcessType.SANDBLASTING,
            quantity=Decimal("100"),
            unit_price=Decimal("2")
        )
        
        p2 = processing_manager.create_processing(
            order_id=sample_order.id,
            supplier_id=sample_supplier.id,
            supplier_name=sample_supplier.name,
            process_type=ProcessType.POLISHING,
            quantity=Decimal("100"),
            unit_price=Decimal("1.5")
        )
        
        # 分配付款
        allocations = {
            p1.id: Decimal("100"),
            p2.id: Decimal("75")
        }
        results = processing_manager.allocate_payment_to_multiple(allocations)
        
        assert all(results.values())
        
        # 验证付款金额
        updated_p1 = processing_manager.get_processing(p1.id)
        updated_p2 = processing_manager.get_processing(p2.id)
        
        assert updated_p1.paid_amount == Decimal("100")
        assert updated_p2.paid_amount == Decimal("75")
    
    def test_get_supplier_unpaid_processing(self, processing_manager, sample_order, sample_supplier):
        """测试获取供应商的未付清委外加工记录"""
        # 创建委外加工记录
        p1 = processing_manager.create_processing(
            order_id=sample_order.id,
            supplier_id=sample_supplier.id,
            supplier_name=sample_supplier.name,
            process_type=ProcessType.SANDBLASTING,
            quantity=Decimal("100"),
            unit_price=Decimal("2")
        )
        
        p2 = processing_manager.create_processing(
            order_id=sample_order.id,
            supplier_id=sample_supplier.id,
            supplier_name=sample_supplier.name,
            process_type=ProcessType.POLISHING,
            quantity=Decimal("100"),
            unit_price=Decimal("1.5")
        )
        
        # 付清第一个记录
        processing_manager.record_payment(p1.id, Decimal("200"))
        
        # 获取未付清记录
        unpaid = processing_manager.get_supplier_unpaid_processing(sample_supplier.id)
        
        assert len(unpaid) == 1
        assert unpaid[0].id == p2.id
    
    def test_get_supplier_total_unpaid(self, processing_manager, sample_order, sample_supplier):
        """测试获取供应商的未付总额"""
        # 创建委外加工记录
        p1 = processing_manager.create_processing(
            order_id=sample_order.id,
            supplier_id=sample_supplier.id,
            supplier_name=sample_supplier.name,
            process_type=ProcessType.SANDBLASTING,
            quantity=Decimal("100"),
            unit_price=Decimal("2")
        )
        
        p2 = processing_manager.create_processing(
            order_id=sample_order.id,
            supplier_id=sample_supplier.id,
            supplier_name=sample_supplier.name,
            process_type=ProcessType.POLISHING,
            quantity=Decimal("100"),
            unit_price=Decimal("1.5")
        )
        
        # 部分付款
        processing_manager.record_payment(p1.id, Decimal("100"))
        
        # 获取未付总额
        total_unpaid = processing_manager.get_supplier_total_unpaid(sample_supplier.id)
        
        assert total_unpaid == Decimal("250")  # (200-100) + 150
    
    def test_get_statistics_by_supplier(self, processing_manager, sample_order, sample_supplier):
        """测试按供应商统计委外加工情况"""
        # 创建委外加工记录
        processing_manager.create_processing(
            order_id=sample_order.id,
            supplier_id=sample_supplier.id,
            supplier_name=sample_supplier.name,
            process_type=ProcessType.SANDBLASTING,
            quantity=Decimal("100"),
            unit_price=Decimal("2")
        )
        
        processing_manager.create_processing(
            order_id=sample_order.id,
            supplier_id=sample_supplier.id,
            supplier_name=sample_supplier.name,
            process_type=ProcessType.POLISHING,
            quantity=Decimal("100"),
            unit_price=Decimal("1.5")
        )
        
        # 获取统计信息
        stats = processing_manager.get_statistics_by_supplier()
        
        assert sample_supplier.id in stats
        supplier_stats = stats[sample_supplier.id]
        
        assert supplier_stats["total_count"] == 2
        assert supplier_stats["total_cost"] == Decimal("350")
        assert "喷砂" in supplier_stats["by_process_type"]
        assert "抛光" in supplier_stats["by_process_type"]
    
    def test_get_statistics_by_process_type(self, processing_manager, sample_order, sample_supplier):
        """测试按工序类型统计委外加工情况"""
        # 创建委外加工记录
        processing_manager.create_processing(
            order_id=sample_order.id,
            supplier_id=sample_supplier.id,
            supplier_name=sample_supplier.name,
            process_type=ProcessType.SANDBLASTING,
            quantity=Decimal("100"),
            unit_price=Decimal("2")
        )
        
        processing_manager.create_processing(
            order_id=sample_order.id,
            supplier_id=sample_supplier.id,
            supplier_name=sample_supplier.name,
            process_type=ProcessType.SANDBLASTING,
            quantity=Decimal("50"),
            unit_price=Decimal("2.5")
        )
        
        # 获取统计信息
        stats = processing_manager.get_statistics_by_process_type()
        
        assert "喷砂" in stats
        sandblasting_stats = stats["喷砂"]
        
        assert sandblasting_stats["count"] == 2
        assert sandblasting_stats["total_cost"] == Decimal("325")  # 200 + 125
        assert sandblasting_stats["total_quantity"] == Decimal("150")
    
    def test_delete_processing(self, processing_manager, sample_order, sample_supplier):
        """测试删除委外加工记录"""
        # 创建委外加工记录
        processing = processing_manager.create_processing(
            order_id=sample_order.id,
            supplier_id=sample_supplier.id,
            supplier_name=sample_supplier.name,
            process_type=ProcessType.SANDBLASTING,
            quantity=Decimal("100"),
            unit_price=Decimal("2")
        )
        
        # 删除记录
        result = processing_manager.delete_processing(processing.id)
        
        assert result is True
        
        # 验证记录已删除
        deleted = processing_manager.get_processing(processing.id)
        assert deleted is None
    
    def test_delete_processing_with_payment_fails(self, processing_manager, sample_order, sample_supplier):
        """测试删除已付款的委外加工记录应该失败"""
        # 创建委外加工记录并付款
        processing = processing_manager.create_processing(
            order_id=sample_order.id,
            supplier_id=sample_supplier.id,
            supplier_name=sample_supplier.name,
            process_type=ProcessType.SANDBLASTING,
            quantity=Decimal("100"),
            unit_price=Decimal("2")
        )
        
        processing_manager.record_payment(processing.id, Decimal("100"))
        
        # 尝试删除应该失败
        with pytest.raises(ValueError, match="已付款的委外加工记录不能删除"):
            processing_manager.delete_processing(processing.id)
    
    def test_update_processing(self, processing_manager, sample_order, sample_supplier):
        """测试更新委外加工记录"""
        # 创建委外加工记录
        processing = processing_manager.create_processing(
            order_id=sample_order.id,
            supplier_id=sample_supplier.id,
            supplier_name=sample_supplier.name,
            process_type=ProcessType.SANDBLASTING,
            quantity=Decimal("100"),
            unit_price=Decimal("2")
        )
        
        # 更新数量和单价
        processing.quantity = Decimal("150")
        processing.unit_price = Decimal("2.5")
        
        updated = processing_manager.update_processing(processing)
        
        assert updated.quantity == Decimal("150")
        assert updated.unit_price == Decimal("2.5")
        assert updated.total_cost == Decimal("375")  # 自动重新计算
