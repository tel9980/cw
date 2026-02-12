#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
委外加工管理属性测试

**验证: 需求 1.3, 3.3**

属性 3: 委外加工信息关联性
对于任何包含委外加工的订单，委外供应商和费用信息应该与订单正确关联，
并且能够通过订单查询到完整的委外信息
"""

import pytest
from hypothesis import given, strategies as st, assume, settings
from datetime import date, timedelta
from decimal import Decimal
import tempfile
import os

from business.outsourced_processing_manager import OutsourcedProcessingManager
from business.order_manager import OrderManager
from database.db_manager import DatabaseManager
from models.business_models import (
    ProcessType, Supplier, ProcessingOrder, Customer,
    PricingUnit, OrderStatus
)


# 策略定义
@st.composite
def supplier_strategy(draw):
    """生成供应商数据"""
    return Supplier(
        name=draw(st.text(min_size=1, max_size=20, alphabet=st.characters(whitelist_categories=('Lu', 'Ll', 'Nd')))),
        contact=draw(st.text(min_size=1, max_size=10, alphabet=st.characters(whitelist_categories=('Lu', 'Ll')))),
        phone=draw(st.text(min_size=11, max_size=11, alphabet='0123456789')),
        business_type="委外加工"
    )


@st.composite
def order_strategy(draw, customer_id, customer_name):
    """生成订单数据"""
    quantity = draw(st.decimals(min_value=1, max_value=1000, places=2))
    unit_price = draw(st.decimals(min_value=0.01, max_value=100, places=2))
    
    return ProcessingOrder(
        order_no=f"ORD-{draw(st.integers(min_value=20240101, max_value=20241231))}-{draw(st.integers(min_value=1, max_value=9999)):04d}",
        customer_id=customer_id,
        customer_name=customer_name,
        item_description=draw(st.text(min_size=1, max_size=20, alphabet=st.characters(whitelist_categories=('Lu', 'Ll')))),
        quantity=quantity,
        pricing_unit=draw(st.sampled_from(list(PricingUnit))),
        unit_price=unit_price,
        processes=draw(st.lists(st.sampled_from(list(ProcessType)), min_size=1, max_size=4, unique=True)),
        total_amount=quantity * unit_price,
        status=OrderStatus.PENDING
    )


@st.composite
def outsourced_processing_strategy(draw, order_id, supplier_id, supplier_name):
    """生成委外加工数据"""
    quantity = draw(st.decimals(min_value=1, max_value=1000, places=2))
    unit_price = draw(st.decimals(min_value=0.01, max_value=50, places=2))
    
    return {
        'order_id': order_id,
        'supplier_id': supplier_id,
        'supplier_name': supplier_name,
        'process_type': draw(st.sampled_from(list(ProcessType))),
        'quantity': quantity,
        'unit_price': unit_price,
        'process_description': draw(st.text(min_size=0, max_size=50, alphabet=st.characters(whitelist_categories=('Lu', 'Ll', 'Nd')))),
        'notes': draw(st.text(min_size=0, max_size=50, alphabet=st.characters(whitelist_categories=('Lu', 'Ll', 'Nd'))))
    }


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


class TestProperty3_OutsourcedProcessingAssociation:
    """
    属性 3: 委外加工信息关联性
    
    **验证: 需求 1.3, 3.3**
    
    对于任何包含委外加工的订单，委外供应商和费用信息应该与订单正确关联，
    并且能够通过订单查询到完整的委外信息
    """
    
    @given(
        supplier_data=supplier_strategy(),
        process_count=st.integers(min_value=1, max_value=5)
    )
    @settings(max_examples=50, deadline=None)
    def test_outsourced_processing_order_association(self, db_manager, supplier_data, process_count):
        """
        属性: 委外加工记录与订单的关联性
        
        对于任何订单和委外加工记录，通过订单ID应该能够查询到所有关联的委外加工记录
        """
        # 创建供应商
        db_manager.save_supplier(supplier_data)
        
        # 创建客户和订单
        customer = Customer(name="测试客户", contact="测试", phone="13800138000")
        db_manager.save_customer(customer)
        
        order = ProcessingOrder(
            order_no=f"ORD-TEST-{id(supplier_data)}",
            customer_id=customer.id,
            customer_name=customer.name,
            item_description="测试物品",
            quantity=Decimal("100"),
            pricing_unit=PricingUnit.PIECE,
            unit_price=Decimal("10"),
            processes=[ProcessType.SANDBLASTING],
            total_amount=Decimal("1000"),
            status=OrderStatus.PENDING
        )
        db_manager.save_order(order)
        
        # 创建委外加工管理器
        processing_manager = OutsourcedProcessingManager(db_manager)
        
        # 创建多个委外加工记录
        created_processing_ids = []
        for i in range(process_count):
            processing = processing_manager.create_processing(
                order_id=order.id,
                supplier_id=supplier_data.id,
                supplier_name=supplier_data.name,
                process_type=ProcessType.SANDBLASTING,
                quantity=Decimal("10") * (i + 1),
                unit_price=Decimal("2")
            )
            created_processing_ids.append(processing.id)
        
        # 验证: 通过订单ID能够查询到所有委外加工记录
        order_processing = processing_manager.list_processing_by_order(order.id)
        
        assert len(order_processing) == process_count, \
            f"应该查询到 {process_count} 条委外加工记录，实际查询到 {len(order_processing)} 条"
        
        # 验证: 所有记录都关联到正确的订单
        for processing in order_processing:
            assert processing.order_id == order.id, \
                "委外加工记录应该关联到正确的订单"
            assert processing.id in created_processing_ids, \
                "查询到的记录应该是创建的记录"
    
    @given(
        supplier_data=supplier_strategy(),
        quantity=st.decimals(min_value=1, max_value=1000, places=2),
        unit_price=st.decimals(min_value=0.01, max_value=50, places=2)
    )
    @settings(max_examples=50, deadline=None)
    def test_outsourced_processing_supplier_association(self, db_manager, supplier_data, quantity, unit_price):
        """
        属性: 委外加工记录与供应商的关联性
        
        对于任何委外加工记录，供应商信息应该正确保存并能够查询
        """
        # 创建供应商
        db_manager.save_supplier(supplier_data)
        
        # 创建客户和订单
        customer = Customer(name="测试客户", contact="测试", phone="13800138000")
        db_manager.save_customer(customer)
        
        order = ProcessingOrder(
            order_no=f"ORD-TEST-{id(supplier_data)}",
            customer_id=customer.id,
            customer_name=customer.name,
            item_description="测试物品",
            quantity=Decimal("100"),
            pricing_unit=PricingUnit.PIECE,
            unit_price=Decimal("10"),
            processes=[ProcessType.SANDBLASTING],
            total_amount=Decimal("1000"),
            status=OrderStatus.PENDING
        )
        db_manager.save_order(order)
        
        # 创建委外加工管理器
        processing_manager = OutsourcedProcessingManager(db_manager)
        
        # 创建委外加工记录
        processing = processing_manager.create_processing(
            order_id=order.id,
            supplier_id=supplier_data.id,
            supplier_name=supplier_data.name,
            process_type=ProcessType.SANDBLASTING,
            quantity=quantity,
            unit_price=unit_price
        )
        
        # 验证: 供应商信息正确保存
        assert processing.supplier_id == supplier_data.id, \
            "委外加工记录应该保存正确的供应商ID"
        assert processing.supplier_name == supplier_data.name, \
            "委外加工记录应该保存正确的供应商名称"
        
        # 验证: 通过供应商ID能够查询到委外加工记录
        supplier_processing = processing_manager.list_processing_by_supplier(supplier_data.id)
        
        assert len(supplier_processing) >= 1, \
            "应该能够通过供应商ID查询到委外加工记录"
        assert any(p.id == processing.id for p in supplier_processing), \
            "查询结果应该包含创建的委外加工记录"
    
    @given(
        supplier_data=supplier_strategy(),
        quantity=st.decimals(min_value=1, max_value=1000, places=2),
        unit_price=st.decimals(min_value=0.01, max_value=50, places=2)
    )
    @settings(max_examples=50, deadline=None)
    def test_outsourced_processing_cost_calculation(self, db_manager, supplier_data, quantity, unit_price):
        """
        属性: 委外加工费用计算准确性
        
        对于任何委外加工记录，总成本应该等于数量乘以单价
        """
        # 创建供应商
        db_manager.save_supplier(supplier_data)
        
        # 创建客户和订单
        customer = Customer(name="测试客户", contact="测试", phone="13800138000")
        db_manager.save_customer(customer)
        
        order = ProcessingOrder(
            order_no=f"ORD-TEST-{id(supplier_data)}",
            customer_id=customer.id,
            customer_name=customer.name,
            item_description="测试物品",
            quantity=Decimal("100"),
            pricing_unit=PricingUnit.PIECE,
            unit_price=Decimal("10"),
            processes=[ProcessType.SANDBLASTING],
            total_amount=Decimal("1000"),
            status=OrderStatus.PENDING
        )
        db_manager.save_order(order)
        
        # 创建委外加工管理器
        processing_manager = OutsourcedProcessingManager(db_manager)
        
        # 创建委外加工记录
        processing = processing_manager.create_processing(
            order_id=order.id,
            supplier_id=supplier_data.id,
            supplier_name=supplier_data.name,
            process_type=ProcessType.SANDBLASTING,
            quantity=quantity,
            unit_price=unit_price
        )
        
        # 验证: 总成本计算准确
        expected_cost = quantity * unit_price
        assert processing.total_cost == expected_cost, \
            f"委外加工总成本应该等于数量({quantity}) × 单价({unit_price}) = {expected_cost}，实际为 {processing.total_cost}"
        
        # 验证: 从数据库查询的记录也保持一致
        retrieved = processing_manager.get_processing(processing.id)
        assert retrieved.total_cost == expected_cost, \
            "从数据库查询的委外加工记录总成本应该保持一致"
    
    @given(
        supplier_data=supplier_strategy(),
        process_count=st.integers(min_value=1, max_value=5)
    )
    @settings(max_examples=50, deadline=None)
    def test_order_total_outsourcing_cost(self, db_manager, supplier_data, process_count):
        """
        属性: 订单委外加工总成本计算准确性
        
        对于任何订单，委外加工总成本应该等于所有委外加工记录成本的总和
        """
        # 创建供应商
        db_manager.save_supplier(supplier_data)
        
        # 创建客户和订单
        customer = Customer(name="测试客户", contact="测试", phone="13800138000")
        db_manager.save_customer(customer)
        
        order = ProcessingOrder(
            order_no=f"ORD-TEST-{id(supplier_data)}",
            customer_id=customer.id,
            customer_name=customer.name,
            item_description="测试物品",
            quantity=Decimal("100"),
            pricing_unit=PricingUnit.PIECE,
            unit_price=Decimal("10"),
            processes=[ProcessType.SANDBLASTING],
            total_amount=Decimal("1000"),
            status=OrderStatus.PENDING
        )
        db_manager.save_order(order)
        
        # 创建委外加工管理器
        processing_manager = OutsourcedProcessingManager(db_manager)
        
        # 创建多个委外加工记录并计算预期总成本
        expected_total_cost = Decimal("0")
        for i in range(process_count):
            quantity = Decimal("10") * (i + 1)
            unit_price = Decimal("2")
            
            processing = processing_manager.create_processing(
                order_id=order.id,
                supplier_id=supplier_data.id,
                supplier_name=supplier_data.name,
                process_type=ProcessType.SANDBLASTING,
                quantity=quantity,
                unit_price=unit_price
            )
            expected_total_cost += processing.total_cost
        
        # 验证: 订单委外加工总成本等于所有记录成本之和
        actual_total_cost = processing_manager.get_order_total_cost(order.id)
        
        assert actual_total_cost == expected_total_cost, \
            f"订单委外加工总成本应该等于所有记录成本之和，预期 {expected_total_cost}，实际 {actual_total_cost}"
    
    @given(
        supplier_data=supplier_strategy(),
        quantity=st.decimals(min_value=1, max_value=1000, places=2),
        unit_price=st.decimals(min_value=0.01, max_value=50, places=2),
        payment_amount=st.decimals(min_value=0.01, max_value=1000, places=2)
    )
    @settings(max_examples=50, deadline=None)
    def test_outsourced_processing_payment_tracking(self, db_manager, supplier_data, quantity, unit_price, payment_amount):
        """
        属性: 委外加工付款跟踪准确性
        
        对于任何委外加工记录，已付金额和未付金额之和应该等于总成本
        """
        # 创建供应商
        db_manager.save_supplier(supplier_data)
        
        # 创建客户和订单
        customer = Customer(name="测试客户", contact="测试", phone="13800138000")
        db_manager.save_customer(customer)
        
        order = ProcessingOrder(
            order_no=f"ORD-TEST-{id(supplier_data)}",
            customer_id=customer.id,
            customer_name=customer.name,
            item_description="测试物品",
            quantity=Decimal("100"),
            pricing_unit=PricingUnit.PIECE,
            unit_price=Decimal("10"),
            processes=[ProcessType.SANDBLASTING],
            total_amount=Decimal("1000"),
            status=OrderStatus.PENDING
        )
        db_manager.save_order(order)
        
        # 创建委外加工管理器
        processing_manager = OutsourcedProcessingManager(db_manager)
        
        # 创建委外加工记录
        processing = processing_manager.create_processing(
            order_id=order.id,
            supplier_id=supplier_data.id,
            supplier_name=supplier_data.name,
            process_type=ProcessType.SANDBLASTING,
            quantity=quantity,
            unit_price=unit_price
        )
        
        # 限制付款金额不超过总成本
        actual_payment = min(payment_amount, processing.total_cost)
        
        # 记录付款
        if actual_payment > 0:
            processing_manager.record_payment(processing.id, actual_payment)
        
        # 重新获取记录
        updated = processing_manager.get_processing(processing.id)
        
        # 验证: 已付金额 + 未付金额 = 总成本
        assert updated.paid_amount + updated.get_unpaid_amount() == updated.total_cost, \
            f"已付金额({updated.paid_amount}) + 未付金额({updated.get_unpaid_amount()}) 应该等于总成本({updated.total_cost})"
        
        # 验证: 已付金额不超过总成本
        assert updated.paid_amount <= updated.total_cost, \
            "已付金额不应该超过总成本"
    
    @given(
        supplier_data=supplier_strategy(),
        process_count=st.integers(min_value=2, max_value=5)
    )
    @settings(max_examples=30, deadline=None)
    def test_payment_allocation_to_multiple_processing(self, db_manager, supplier_data, process_count):
        """
        属性: 付款分配到多个委外加工记录的一致性
        
        对于任何付款分配操作，分配后各记录的已付金额应该正确更新
        """
        # 创建供应商
        db_manager.save_supplier(supplier_data)
        
        # 创建客户和订单
        customer = Customer(name="测试客户", contact="测试", phone="13800138000")
        db_manager.save_customer(customer)
        
        order = ProcessingOrder(
            order_no=f"ORD-TEST-{id(supplier_data)}",
            customer_id=customer.id,
            customer_name=customer.name,
            item_description="测试物品",
            quantity=Decimal("100"),
            pricing_unit=PricingUnit.PIECE,
            unit_price=Decimal("10"),
            processes=[ProcessType.SANDBLASTING],
            total_amount=Decimal("1000"),
            status=OrderStatus.PENDING
        )
        db_manager.save_order(order)
        
        # 创建委外加工管理器
        processing_manager = OutsourcedProcessingManager(db_manager)
        
        # 创建多个委外加工记录
        processing_list = []
        for i in range(process_count):
            processing = processing_manager.create_processing(
                order_id=order.id,
                supplier_id=supplier_data.id,
                supplier_name=supplier_data.name,
                process_type=ProcessType.SANDBLASTING,
                quantity=Decimal("10"),
                unit_price=Decimal("2")
            )
            processing_list.append(processing)
        
        # 准备付款分配
        allocations = {}
        for processing in processing_list:
            allocations[processing.id] = Decimal("10")  # 每个记录分配10元
        
        # 执行付款分配
        results = processing_manager.allocate_payment_to_multiple(allocations)
        
        # 验证: 所有分配都成功
        assert all(results.values()), "所有付款分配应该成功"
        
        # 验证: 每个记录的已付金额正确更新
        for processing in processing_list:
            updated = processing_manager.get_processing(processing.id)
            assert updated.paid_amount == Decimal("10"), \
                f"委外加工记录 {processing.id} 的已付金额应该是 10，实际为 {updated.paid_amount}"
