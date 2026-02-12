#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
快速测试委外加工管理器
"""

import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from datetime import date
from decimal import Decimal
import tempfile

from business.outsourced_processing_manager import OutsourcedProcessingManager
from database.db_manager import DatabaseManager
from models.business_models import (
    ProcessType, Supplier, ProcessingOrder, Customer,
    PricingUnit, OrderStatus
)


def test_outsourced_processing():
    """快速测试委外加工功能"""
    # 创建临时数据库
    temp_db = tempfile.NamedTemporaryFile(delete=False, suffix='.db')
    temp_db.close()
    
    try:
        # 初始化数据库
        db = DatabaseManager(temp_db.name)
        db.connect()
        
        # 创建供应商
        supplier = Supplier(
            name="测试委外供应商",
            contact="张三",
            phone="13800138000",
            business_type="委外加工"
        )
        db.save_supplier(supplier)
        print(f"✓ 创建供应商: {supplier.name}")
        
        # 创建客户和订单
        customer = Customer(
            name="测试客户",
            contact="李四",
            phone="13900139000"
        )
        db.save_customer(customer)
        
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
        db.save_order(order)
        print(f"✓ 创建订单: {order.order_no}")
        
        # 创建委外加工管理器
        processing_manager = OutsourcedProcessingManager(db)
        
        # 测试1: 创建委外加工记录
        processing = processing_manager.create_processing(
            order_id=order.id,
            supplier_id=supplier.id,
            supplier_name=supplier.name,
            process_type=ProcessType.SANDBLASTING,
            quantity=Decimal("100"),
            unit_price=Decimal("2"),
            process_description="喷砂处理"
        )
        print(f"✓ 创建委外加工记录: {processing.process_type.value}, 总成本: {processing.total_cost}")
        
        # 测试2: 获取委外加工记录
        retrieved = processing_manager.get_processing(processing.id)
        assert retrieved is not None
        assert retrieved.total_cost == Decimal("200")
        print(f"✓ 获取委外加工记录成功")
        
        # 测试3: 按订单查询
        order_processing = processing_manager.list_processing_by_order(order.id)
        assert len(order_processing) == 1
        print(f"✓ 按订单查询: 找到 {len(order_processing)} 条记录")
        
        # 测试4: 记录付款
        updated = processing_manager.record_payment(processing.id, Decimal("100"))
        assert updated.paid_amount == Decimal("100")
        assert updated.get_unpaid_amount() == Decimal("100")
        print(f"✓ 记录付款: 已付 {updated.paid_amount}, 未付 {updated.get_unpaid_amount()}")
        
        # 测试5: 获取订单总成本
        total_cost = processing_manager.get_order_total_cost(order.id)
        assert total_cost == Decimal("200")
        print(f"✓ 订单委外总成本: {total_cost}")
        
        # 测试6: 创建第二个委外加工记录
        processing2 = processing_manager.create_processing(
            order_id=order.id,
            supplier_id=supplier.id,
            supplier_name=supplier.name,
            process_type=ProcessType.POLISHING,
            quantity=Decimal("100"),
            unit_price=Decimal("1.5")
        )
        print(f"✓ 创建第二个委外加工记录: {processing2.process_type.value}, 总成本: {processing2.total_cost}")
        
        # 测试7: 分配付款到多个记录
        allocations = {
            processing.id: Decimal("50"),
            processing2.id: Decimal("75")
        }
        results = processing_manager.allocate_payment_to_multiple(allocations)
        assert all(results.values())
        print(f"✓ 分配付款到多个记录成功")
        
        # 测试8: 获取供应商未付清记录
        unpaid = processing_manager.get_supplier_unpaid_processing(supplier.id)
        print(f"✓ 供应商未付清记录: {len(unpaid)} 条")
        
        # 测试9: 统计信息
        stats = processing_manager.get_statistics_by_supplier()
        assert supplier.id in stats
        print(f"✓ 供应商统计: 总记录 {stats[supplier.id]['total_count']}, 总成本 {stats[supplier.id]['total_cost']}")
        
        print("\n" + "="*50)
        print("所有测试通过! ✓")
        print("="*50)
        
        db.close()
        
    finally:
        # 清理临时文件
        if os.path.exists(temp_db.name):
            os.unlink(temp_db.name)


if __name__ == "__main__":
    test_outsourced_processing()
