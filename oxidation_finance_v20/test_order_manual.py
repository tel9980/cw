#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
手动测试订单管理器
"""

import sys
import os
from decimal import Decimal
from datetime import date

# 添加项目路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from oxidation_finance_v20.models.business_models import (
    Customer, PricingUnit, ProcessType, OrderStatus
)
from oxidation_finance_v20.database.db_manager import DatabaseManager
from oxidation_finance_v20.business.order_manager import OrderManager


def test_order_manager():
    """测试订单管理器"""
    print("=" * 60)
    print("测试订单管理器")
    print("=" * 60)
    
    # 创建数据库管理器
    db = DatabaseManager("test_order.db")
    db.connect()
    
    try:
        # 创建订单管理器
        order_mgr = OrderManager(db)
        
        # 创建测试客户
        customer = Customer(
            name="测试客户",
            contact="张三",
            phone="13800138000"
        )
        db.save_customer(customer)
        print(f"\n✓ 创建客户: {customer.name}")
        
        # 测试1: 创建基本订单
        print("\n--- 测试1: 创建基本订单 ---")
        order1 = order_mgr.create_order(
            customer_id=customer.id,
            customer_name=customer.name,
            item_description="铝型材",
            quantity=Decimal("100"),
            pricing_unit=PricingUnit.PIECE,
            unit_price=Decimal("5.5"),
            processes=[ProcessType.SANDBLASTING, ProcessType.OXIDATION]
        )
        print(f"✓ 订单编号: {order1.order_no}")
        print(f"✓ 物品描述: {order1.item_description}")
        print(f"✓ 数量: {order1.quantity} {order1.pricing_unit.value}")
        print(f"✓ 单价: {order1.unit_price}")
        print(f"✓ 总金额: {order1.total_amount}")
        print(f"✓ 工序: {[p.value for p in order1.processes]}")
        
        # 测试2: 测试七种计价方式
        print("\n--- 测试2: 测试七种计价方式 ---")
        pricing_units = [
            (PricingUnit.PIECE, "螺丝"),
            (PricingUnit.STRIP, "铝条"),
            (PricingUnit.UNIT, "把手"),
            (PricingUnit.ITEM, "配件"),
            (PricingUnit.METER, "铝型材"),
            (PricingUnit.KILOGRAM, "板材"),
            (PricingUnit.SQUARE_METER, "铝板")
        ]
        
        for unit, desc in pricing_units:
            order = order_mgr.create_order(
                customer_id=customer.id,
                customer_name=customer.name,
                item_description=desc,
                quantity=Decimal("10"),
                pricing_unit=unit,
                unit_price=Decimal("2.0"),
                processes=[ProcessType.OXIDATION]
            )
            print(f"✓ {unit.value}: {desc} - 订单编号 {order.order_no}")
        
        # 测试3: 创建包含委外工序的订单
        print("\n--- 测试3: 创建包含委外工序的订单 ---")
        order2 = order_mgr.create_order(
            customer_id=customer.id,
            customer_name=customer.name,
            item_description="铝板",
            quantity=Decimal("50"),
            pricing_unit=PricingUnit.SQUARE_METER,
            unit_price=Decimal("15.0"),
            processes=[ProcessType.POLISHING, ProcessType.OXIDATION],
            outsourced_processes=["抛光"]
        )
        print(f"✓ 订单编号: {order2.order_no}")
        print(f"✓ 委外工序: {order2.outsourced_processes}")
        
        # 测试4: 更新订单状态
        print("\n--- 测试4: 更新订单状态 ---")
        order_mgr.update_order_status(order1.id, OrderStatus.IN_PROGRESS)
        updated = order_mgr.get_order(order1.id)
        print(f"✓ 订单 {order1.order_no} 状态更新为: {updated.status.value}")
        
        # 测试5: 工序状态跟踪
        print("\n--- 测试5: 工序状态跟踪 ---")
        process_status = order_mgr.track_process_status(order1.id)
        print(f"✓ 订单 {order1.order_no} 工序状态:")
        for process, status in process_status.items():
            print(f"  - {process}: {status}")
        
        # 测试6: 更新委外成本
        print("\n--- 测试6: 更新委外成本 ---")
        order_mgr.update_outsourcing_cost(order2.id, Decimal("200.0"))
        updated = order_mgr.get_order(order2.id)
        print(f"✓ 订单 {order2.order_no} 委外成本: {updated.outsourcing_cost}")
        
        # 测试7: 计算加工费用
        print("\n--- 测试7: 计算加工费用 ---")
        total_fee = order_mgr.calculate_processing_fee(order2.id)
        print(f"✓ 订单 {order2.order_no} 总加工费: {total_fee}")
        print(f"  - 基础加工费: {updated.total_amount}")
        print(f"  - 委外成本: {updated.outsourcing_cost}")
        
        # 测试8: 记录收款
        print("\n--- 测试8: 记录收款 ---")
        order_mgr.record_payment(order1.id, Decimal("300.0"))
        updated = order_mgr.get_order(order1.id)
        balance = order_mgr.get_order_balance(order1.id)
        print(f"✓ 订单 {order1.order_no} 已收款: {updated.received_amount}")
        print(f"✓ 未收款余额: {balance}")
        
        # 测试9: 查询订单列表
        print("\n--- 测试9: 查询订单列表 ---")
        all_orders = order_mgr.list_orders()
        print(f"✓ 总订单数: {len(all_orders)}")
        
        customer_orders = order_mgr.list_orders(customer_id=customer.id)
        print(f"✓ 客户 {customer.name} 的订单数: {len(customer_orders)}")
        
        # 测试10: 按计价方式查询
        print("\n--- 测试10: 按计价方式查询 ---")
        piece_orders = order_mgr.get_orders_by_pricing_unit(PricingUnit.PIECE)
        print(f"✓ 按件计价的订单数: {len(piece_orders)}")
        
        print("\n" + "=" * 60)
        print("所有测试通过！✓")
        print("=" * 60)
        
    finally:
        db.close()
        # 清理测试数据库
        if os.path.exists("test_order.db"):
            os.remove("test_order.db")


if __name__ == "__main__":
    test_order_manager()
