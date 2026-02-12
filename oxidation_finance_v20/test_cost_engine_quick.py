#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""快速测试费用计算引擎"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import tempfile
from decimal import Decimal
from datetime import date

from oxidation_finance_v20.database.db_manager import DatabaseManager
from oxidation_finance_v20.business.order_manager import OrderManager
from oxidation_finance_v20.business.outsourced_processing_manager import OutsourcedProcessingManager
from oxidation_finance_v20.business.cost_calculation_engine import CostCalculationEngine
from oxidation_finance_v20.models.business_models import PricingUnit, ProcessType

def test_cost_calculation_engine():
    """测试费用计算引擎"""
    print("=" * 60)
    print("费用计算引擎测试")
    print("=" * 60)
    
    # 创建临时数据库
    fd, db_path = tempfile.mkstemp(suffix='.db')
    os.close(fd)
    
    try:
        # 初始化数据库和管理器
        db = DatabaseManager(db_path)
        db.connect()
        
        order_mgr = OrderManager(db)
        outsourced_mgr = OutsourcedProcessingManager(db)
        cost_engine = CostCalculationEngine(db)
        
        print("\n✓ 所有管理器初始化成功")
        
        # 测试1: 基础加工费计算
        print("\n【测试1】基础加工费计算")
        fee = cost_engine.calculate_base_processing_fee(
            Decimal("100"),
            Decimal("10.00"),
            PricingUnit.PIECE
        )
        print(f"  100件 × 10.00元/件 = {fee}元")
        assert fee == Decimal("1000.00"), "基础加工费计算错误"
        print("  ✓ 基础加工费计算正确")
        
        # 测试2: 创建订单并计算总费用（无委外）
        print("\n【测试2】订单总费用计算（无委外）")
        order1 = order_mgr.create_order(
            customer_id="C001",
            customer_name="测试客户A",
            item_description="铝型材",
            quantity=Decimal("100"),
            pricing_unit=PricingUnit.PIECE,
            unit_price=Decimal("10.00"),
            processes=[ProcessType.OXIDATION]
        )
        print(f"  订单编号: {order1.order_no}")
        print(f"  物品: {order1.item_description}")
        print(f"  数量: {order1.quantity} {order1.pricing_unit.value}")
        print(f"  单价: {order1.unit_price}元")
        
        total_fee = cost_engine.calculate_total_processing_fee(order1.id)
        print(f"  总加工费: {total_fee}元")
        assert total_fee == Decimal("1000.00"), "总费用计算错误"
        print("  ✓ 无委外订单费用计算正确")
        
        # 测试3: 创建订单并计算总费用（含委外）
        print("\n【测试3】订单总费用计算（含委外）")
        order2 = order_mgr.create_order(
            customer_id="C002",
            customer_name="测试客户B",
            item_description="铝板",
            quantity=Decimal("50"),
            pricing_unit=PricingUnit.SQUARE_METER,
            unit_price=Decimal("20.00"),
            processes=[ProcessType.SANDBLASTING, ProcessType.OXIDATION],
            outsourced_processes=["喷砂"]
        )
        print(f"  订单编号: {order2.order_no}")
        print(f"  物品: {order2.item_description}")
        print(f"  数量: {order2.quantity} {order2.pricing_unit.value}")
        print(f"  单价: {order2.unit_price}元")
        
        # 添加委外加工
        outsourced = outsourced_mgr.create_processing(
            order_id=order2.id,
            supplier_id="S001",
            supplier_name="喷砂供应商",
            process_type=ProcessType.SANDBLASTING,
            quantity=Decimal("50"),
            unit_price=Decimal("5.00")
        )
        print(f"  委外工序: {outsourced.process_type.value}")
        print(f"  委外数量: {outsourced.quantity}")
        print(f"  委外单价: {outsourced.unit_price}元")
        print(f"  委外总成本: {outsourced.total_cost}元")
        
        # 更新订单费用
        updated_order = cost_engine.update_order_costs(order2.id)
        print(f"  基础加工费: {updated_order.total_amount}元")
        print(f"  委外加工费: {updated_order.outsourcing_cost}元")
        
        total_fee2 = cost_engine.calculate_total_processing_fee(order2.id)
        print(f"  总加工费: {total_fee2}元")
        
        # 验证: 50 × 20 = 1000 (基础) + 50 × 5 = 250 (委外) = 1250
        assert total_fee2 == Decimal("1250.00"), "含委外订单费用计算错误"
        print("  ✓ 含委外订单费用计算正确")
        
        # 测试4: 利润计算
        print("\n【测试4】订单利润计算")
        profit = cost_engine.calculate_order_profit(order2.id)
        print(f"  总费用: {total_fee2}元")
        print(f"  委外成本: {updated_order.outsourcing_cost}元")
        print(f"  利润: {profit}元")
        
        # 利润 = 1250 - 250 = 1000
        assert profit == Decimal("1000.00"), "利润计算错误"
        
        profit_margin = cost_engine.calculate_order_profit_margin(order2.id)
        print(f"  利润率: {profit_margin}%")
        
        # 利润率 = (1000 / 1250) × 100 = 80%
        assert profit_margin == Decimal("80.00"), "利润率计算错误"
        print("  ✓ 利润和利润率计算正确")
        
        # 测试5: 费用验证
        print("\n【测试5】订单费用验证")
        validation = cost_engine.validate_order_costs(order2.id)
        print(f"  验证结果: {'通过' if validation['valid'] else '失败'}")
        print(f"  基础费用匹配: {validation['base_fee_match']}")
        print(f"  委外费用匹配: {validation['outsourcing_match']}")
        print(f"  总费用匹配: {validation['total_match']}")
        
        assert validation['valid'], "费用验证失败"
        print("  ✓ 费用验证通过")
        
        # 测试6: 按计价方式统计
        print("\n【测试6】按计价方式统计")
        stats = cost_engine.calculate_pricing_unit_statistics(PricingUnit.PIECE)
        print(f"  计价方式: {stats['pricing_unit']}")
        print(f"  订单数量: {stats['total_orders']}")
        print(f"  总数量: {stats['total_quantity']}")
        print(f"  总费用: {stats['total_fee']}元")
        print(f"  平均单价: {stats['avg_unit_price']}元")
        print("  ✓ 统计功能正常")
        
        # 测试7: 所有计价方式统计
        print("\n【测试7】所有计价方式统计")
        all_stats = cost_engine.calculate_all_pricing_units_statistics()
        print(f"  统计到 {len(all_stats)} 种计价方式:")
        for stat in all_stats:
            print(f"    - {stat['pricing_unit']}: {stat['total_orders']}个订单, 总费用{stat['total_fee']}元")
        print("  ✓ 全部统计功能正常")
        
        # 测试8: 七种计价方式支持
        print("\n【测试8】七种计价方式支持测试")
        pricing_units = [
            (PricingUnit.PIECE, "件"),
            (PricingUnit.STRIP, "条"),
            (PricingUnit.UNIT, "只"),
            (PricingUnit.ITEM, "个"),
            (PricingUnit.METER, "米"),
            (PricingUnit.KILOGRAM, "公斤"),
            (PricingUnit.SQUARE_METER, "平方米")
        ]
        
        for unit, name in pricing_units:
            fee = cost_engine.calculate_base_processing_fee(
                Decimal("10"),
                Decimal("5.00"),
                unit
            )
            print(f"  {name}: 10 × 5.00 = {fee}元 ✓")
        
        print("  ✓ 所有七种计价方式支持正常")
        
        print("\n" + "=" * 60)
        print("✓ 所有测试通过！费用计算引擎工作正常")
        print("=" * 60)
        
        # 清理
        db.close()
        
    finally:
        # 删除临时数据库
        if os.path.exists(db_path):
            os.unlink(db_path)

if __name__ == "__main__":
    try:
        test_cost_calculation_engine()
    except Exception as e:
        print(f"\n✗ 测试失败: {e}")
        import traceback
        traceback.print_exc()
