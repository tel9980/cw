#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
订单管理属性测试 - 验证订单管理的核心正确性属性
"""

import pytest
from hypothesis import given, strategies as st, settings
from decimal import Decimal
from datetime import date
import tempfile
import os

from oxidation_finance_v20.models.business_models import (
    Customer, PricingUnit, ProcessType, OrderStatus
)
from oxidation_finance_v20.database.db_manager import DatabaseManager
from oxidation_finance_v20.business.order_manager import OrderManager


# ==================== 策略定义 ====================

@st.composite
def customer_strategy(draw):
    """生成客户数据的策略"""
    return Customer(
        name=draw(st.text(min_size=1, max_size=50, alphabet=st.characters(whitelist_categories=('L', 'N')))),
        contact=draw(st.text(min_size=1, max_size=30, alphabet=st.characters(whitelist_categories=('L', 'N')))),
        phone=draw(st.text(min_size=8, max_size=15, alphabet=st.characters(whitelist_categories=('N',)))),
        address=draw(st.text(min_size=1, max_size=100, alphabet=st.characters(whitelist_categories=('L', 'N')))),
        credit_limit=Decimal(str(draw(st.floats(min_value=0, max_value=1000000, allow_nan=False, allow_infinity=False)))),
        notes=draw(st.text(max_size=200))
    )


# ==================== 属性测试 ====================

class TestProperty2_PricingMethodCompleteness:
    """
    **属性 2: 计价方式支持完整性**
    **Validates: Requirements 1.2**
    
    对于任何七种预定义计价方式（件、条、只、个、米、公斤、平方米），
    系统都应该能够正确处理和应用该计价方式
    """
    
    @given(customer=customer_strategy())
    @settings(max_examples=100, deadline=None)
    def test_all_pricing_methods_supported(self, customer):
        """测试所有七种计价方式都能被正确支持"""
        fd, path = tempfile.mkstemp(suffix='.db')
        os.close(fd)
        
        try:
            with DatabaseManager(path) as db:
                db.save_customer(customer)
                order_manager = OrderManager(db)
                
                # 测试所有7种计价方式
                all_pricing_units = list(PricingUnit)
                assert len(all_pricing_units) == 7, "应该有7种计价方式"
                
                created_orders = []
                for pricing_unit in all_pricing_units:
                    # 创建订单
                    order = order_manager.create_order(
                        customer_id=customer.id,
                        customer_name=customer.name,
                        item_description=f"测试物品-{pricing_unit.value}",
                        quantity=Decimal("100"),
                        pricing_unit=pricing_unit,
                        unit_price=Decimal("5.50"),
                        processes=[ProcessType.OXIDATION]
                    )
                    
                    created_orders.append(order)
                    
                    # 验证订单创建成功
                    assert order is not None, f"计价方式 {pricing_unit.value} 应该能创建订单"
                    assert order.pricing_unit == pricing_unit, f"计价方式应该是 {pricing_unit.value}"
                    
                    # 验证能够查询到订单
                    retrieved = order_manager.get_order(order.id)
                    assert retrieved is not None, f"应该能查询到 {pricing_unit.value} 计价的订单"
                    assert retrieved.pricing_unit == pricing_unit, f"查询到的订单计价方式应该是 {pricing_unit.value}"
                
                # 验证所有订单都能被列出
                all_orders = order_manager.list_orders()
                assert len(all_orders) >= 7, "应该至少有7个订单"
                
                # 验证每种计价方式都能被查询
                for pricing_unit in all_pricing_units:
                    orders_by_unit = order_manager.get_orders_by_pricing_unit(pricing_unit)
                    assert len(orders_by_unit) >= 1, f"应该能查询到 {pricing_unit.value} 计价的订单"
                    assert all(o.pricing_unit == pricing_unit for o in orders_by_unit), \
                        f"查询结果应该都是 {pricing_unit.value} 计价"
        
        finally:
            if os.path.exists(path):
                os.unlink(path)
    
    @given(
        customer=customer_strategy(),
        pricing_unit=st.sampled_from(list(PricingUnit)),
        quantity=st.decimals(min_value=Decimal("0.01"), max_value=Decimal("10000"), places=2),
        unit_price=st.decimals(min_value=Decimal("0.01"), max_value=Decimal("1000"), places=2)
    )
    @settings(max_examples=100, deadline=None)
    def test_pricing_method_calculation_accuracy(self, customer, pricing_unit, quantity, unit_price):
        """测试每种计价方式的费用计算准确性"""
        fd, path = tempfile.mkstemp(suffix='.db')
        os.close(fd)
        
        try:
            with DatabaseManager(path) as db:
                db.save_customer(customer)
                order_manager = OrderManager(db)
                
                # 创建订单
                order = order_manager.create_order(
                    customer_id=customer.id,
                    customer_name=customer.name,
                    item_description=f"测试物品-{pricing_unit.value}",
                    quantity=quantity,
                    pricing_unit=pricing_unit,
                    unit_price=unit_price,
                    processes=[ProcessType.OXIDATION]
                )
                
                # 验证费用计算
                expected_amount = quantity * unit_price
                assert order.total_amount == expected_amount, \
                    f"{pricing_unit.value} 计价方式的费用计算应该准确: {quantity} * {unit_price} = {expected_amount}"
                
                # 验证查询后的费用仍然准确
                retrieved = order_manager.get_order(order.id)
                assert retrieved.total_amount == expected_amount, \
                    f"查询后 {pricing_unit.value} 计价的费用应该保持准确"
        
        finally:
            if os.path.exists(path):
                os.unlink(path)
    
    @given(customer=customer_strategy())
    @settings(max_examples=50, deadline=None)
    def test_pricing_method_persistence(self, customer):
        """测试计价方式在数据库中的持久化"""
        fd, path = tempfile.mkstemp(suffix='.db')
        os.close(fd)
        
        try:
            # 第一次连接：创建订单
            with DatabaseManager(path) as db:
                db.save_customer(customer)
                order_manager = OrderManager(db)
                
                order_ids = {}
                for pricing_unit in PricingUnit:
                    order = order_manager.create_order(
                        customer_id=customer.id,
                        customer_name=customer.name,
                        item_description=f"测试-{pricing_unit.value}",
                        quantity=Decimal("10"),
                        pricing_unit=pricing_unit,
                        unit_price=Decimal("1.0"),
                        processes=[ProcessType.OXIDATION]
                    )
                    order_ids[pricing_unit] = order.id
            
            # 第二次连接：验证持久化
            with DatabaseManager(path) as db:
                order_manager = OrderManager(db)
                
                for pricing_unit, order_id in order_ids.items():
                    retrieved = order_manager.get_order(order_id)
                    assert retrieved is not None, f"{pricing_unit.value} 订单应该被持久化"
                    assert retrieved.pricing_unit == pricing_unit, \
                        f"持久化的计价方式应该是 {pricing_unit.value}"
        
        finally:
            if os.path.exists(path):
                os.unlink(path)


class TestProperty5_OrderStatusTrackingCompleteness:
    """
    **属性 5: 订单状态跟踪完整性**
    **Validates: Requirements 1.5**
    
    对于任何订单，从创建到完工的每个工序状态变更都应该被记录，
    并且状态变更序列应该符合业务流程规则
    """
    
    @given(customer=customer_strategy())
    @settings(max_examples=100, deadline=None)
    def test_order_status_transitions_are_tracked(self, customer):
        """测试订单状态变更被完整跟踪"""
        fd, path = tempfile.mkstemp(suffix='.db')
        os.close(fd)
        
        try:
            with DatabaseManager(path) as db:
                db.save_customer(customer)
                order_manager = OrderManager(db)
                
                # 创建订单
                order = order_manager.create_order(
                    customer_id=customer.id,
                    customer_name=customer.name,
                    item_description="测试物品",
                    quantity=Decimal("100"),
                    pricing_unit=PricingUnit.PIECE,
                    unit_price=Decimal("5.0"),
                    processes=[ProcessType.SANDBLASTING, ProcessType.OXIDATION]
                )
                
                # 初始状态应该是待加工
                assert order.status == OrderStatus.PENDING, "初始状态应该是待加工"
                
                # 测试状态转换序列
                status_sequence = [
                    OrderStatus.IN_PROGRESS,
                    OrderStatus.COMPLETED,
                    OrderStatus.DELIVERED,
                    OrderStatus.PAID
                ]
                
                for new_status in status_sequence:
                    # 更新状态
                    updated_order = order_manager.update_order_status(order.id, new_status)
                    
                    # 验证状态更新成功
                    assert updated_order is not None, f"状态更新到 {new_status.value} 应该成功"
                    assert updated_order.status == new_status, f"订单状态应该是 {new_status.value}"
                    
                    # 验证查询能获取到最新状态
                    retrieved = order_manager.get_order(order.id)
                    assert retrieved.status == new_status, f"查询到的状态应该是 {new_status.value}"
        
        finally:
            if os.path.exists(path):
                os.unlink(path)
    
    @given(
        customer=customer_strategy(),
        processes=st.lists(st.sampled_from(list(ProcessType)), min_size=1, max_size=4, unique=True)
    )
    @settings(max_examples=100, deadline=None)
    def test_process_status_tracking_completeness(self, customer, processes):
        """测试工序状态跟踪的完整性"""
        fd, path = tempfile.mkstemp(suffix='.db')
        os.close(fd)
        
        try:
            with DatabaseManager(path) as db:
                db.save_customer(customer)
                order_manager = OrderManager(db)
                
                # 创建订单
                order = order_manager.create_order(
                    customer_id=customer.id,
                    customer_name=customer.name,
                    item_description="测试物品",
                    quantity=Decimal("100"),
                    pricing_unit=PricingUnit.PIECE,
                    unit_price=Decimal("5.0"),
                    processes=processes
                )
                
                # 跟踪工序状态
                process_status = order_manager.track_process_status(order.id)
                
                # 验证所有工序都被跟踪
                assert process_status is not None, "应该能跟踪工序状态"
                assert len(process_status) == len(processes), "所有工序都应该被跟踪"
                
                # 验证每个工序都有状态
                for process in processes:
                    process_name = process.value
                    assert process_name in process_status, f"工序 {process_name} 应该被跟踪"
                    assert process_status[process_name] in ["待加工", "加工中", "委外中", "已完成", "未知"], \
                        f"工序 {process_name} 的状态应该是有效的"
                
                # 测试不同订单状态下的工序状态
                status_mappings = {
                    OrderStatus.PENDING: "待加工",
                    OrderStatus.IN_PROGRESS: "加工中",
                    OrderStatus.COMPLETED: "已完成",
                    OrderStatus.DELIVERED: "已完成",
                    OrderStatus.PAID: "已完成"
                }
                
                for order_status, expected_process_status in status_mappings.items():
                    order_manager.update_order_status(order.id, order_status)
                    process_status = order_manager.track_process_status(order.id)
                    
                    for process in processes:
                        process_name = process.value
                        assert process_status[process_name] == expected_process_status, \
                            f"订单状态为 {order_status.value} 时，工序 {process_name} 应该是 {expected_process_status}"
        
        finally:
            if os.path.exists(path):
                os.unlink(path)
    
    @given(
        customer=customer_strategy(),
        processes=st.lists(st.sampled_from(list(ProcessType)), min_size=2, max_size=4, unique=True)
    )
    @settings(max_examples=50, deadline=None)
    def test_outsourced_process_status_tracking(self, customer, processes):
        """测试委外工序状态跟踪"""
        fd, path = tempfile.mkstemp(suffix='.db')
        os.close(fd)
        
        try:
            with DatabaseManager(path) as db:
                db.save_customer(customer)
                order_manager = OrderManager(db)
                
                # 选择一个工序作为委外工序
                outsourced_process = processes[0].value
                
                # 创建订单
                order = order_manager.create_order(
                    customer_id=customer.id,
                    customer_name=customer.name,
                    item_description="测试物品",
                    quantity=Decimal("100"),
                    pricing_unit=PricingUnit.PIECE,
                    unit_price=Decimal("5.0"),
                    processes=processes,
                    outsourced_processes=[outsourced_process]
                )
                
                # 更新为委外中状态
                order_manager.update_order_status(order.id, OrderStatus.OUTSOURCED)
                process_status = order_manager.track_process_status(order.id)
                
                # 验证委外工序状态
                assert process_status[outsourced_process] == "委外中", \
                    f"委外工序 {outsourced_process} 应该显示为委外中"
                
                # 验证非委外工序状态
                for process in processes:
                    if process.value != outsourced_process:
                        assert process_status[process.value] in ["待加工", "加工中"], \
                            f"非委外工序 {process.value} 应该是待加工或加工中"
                
                # 更新为已完工状态
                order_manager.update_order_status(order.id, OrderStatus.COMPLETED)
                process_status = order_manager.track_process_status(order.id)
                
                # 所有工序都应该是已完成
                for process in processes:
                    assert process_status[process.value] == "已完成", \
                        f"订单完工后，工序 {process.value} 应该是已完成"
        
        finally:
            if os.path.exists(path):
                os.unlink(path)
    
    @given(customer=customer_strategy())
    @settings(max_examples=50, deadline=None)
    def test_order_status_with_dates(self, customer):
        """测试订单状态变更时相关日期的记录"""
        fd, path = tempfile.mkstemp(suffix='.db')
        os.close(fd)
        
        try:
            with DatabaseManager(path) as db:
                db.save_customer(customer)
                order_manager = OrderManager(db)
                
                # 创建订单
                order = order_manager.create_order(
                    customer_id=customer.id,
                    customer_name=customer.name,
                    item_description="测试物品",
                    quantity=Decimal("100"),
                    pricing_unit=PricingUnit.PIECE,
                    unit_price=Decimal("5.0"),
                    processes=[ProcessType.OXIDATION]
                )
                
                # 更新为已完工状态，记录完工日期
                completion_date = date.today()
                updated_order = order_manager.update_order_status(
                    order.id,
                    OrderStatus.COMPLETED,
                    completion_date=completion_date
                )
                
                assert updated_order.completion_date == completion_date, \
                    "完工日期应该被正确记录"
                
                # 更新为已交付状态，记录交付日期
                delivery_date = date.today()
                updated_order = order_manager.update_order_status(
                    order.id,
                    OrderStatus.DELIVERED,
                    delivery_date=delivery_date
                )
                
                assert updated_order.delivery_date == delivery_date, \
                    "交付日期应该被正确记录"
                
                # 验证查询能获取到日期信息
                retrieved = order_manager.get_order(order.id)
                assert retrieved.completion_date == completion_date, \
                    "查询到的完工日期应该正确"
                assert retrieved.delivery_date == delivery_date, \
                    "查询到的交付日期应该正确"
        
        finally:
            if os.path.exists(path):
                os.unlink(path)
    
    @given(customer=customer_strategy())
    @settings(max_examples=50, deadline=None)
    def test_order_status_filtering(self, customer):
        """测试按状态筛选订单的完整性"""
        fd, path = tempfile.mkstemp(suffix='.db')
        os.close(fd)
        
        try:
            with DatabaseManager(path) as db:
                db.save_customer(customer)
                order_manager = OrderManager(db)
                
                # 创建不同状态的订单
                order_ids_by_status = {}
                for status in OrderStatus:
                    order = order_manager.create_order(
                        customer_id=customer.id,
                        customer_name=customer.name,
                        item_description=f"测试-{status.value}",
                        quantity=Decimal("10"),
                        pricing_unit=PricingUnit.PIECE,
                        unit_price=Decimal("1.0"),
                        processes=[ProcessType.OXIDATION]
                    )
                    
                    # 更新状态
                    if status != OrderStatus.PENDING:
                        order_manager.update_order_status(order.id, status)
                    
                    order_ids_by_status[status] = order.id
                
                # 验证按状态筛选
                for status in OrderStatus:
                    filtered_orders = order_manager.list_orders(status=status)
                    
                    # 应该至少有一个该状态的订单
                    assert len(filtered_orders) >= 1, f"应该能查询到 {status.value} 状态的订单"
                    
                    # 所有查询结果都应该是该状态
                    assert all(o.status == status for o in filtered_orders), \
                        f"查询结果应该都是 {status.value} 状态"
                    
                    # 应该包含我们创建的订单
                    order_ids = [o.id for o in filtered_orders]
                    assert order_ids_by_status[status] in order_ids, \
                        f"应该包含状态为 {status.value} 的订单"
        
        finally:
            if os.path.exists(path):
                os.unlink(path)
