#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
费用计算引擎单元测试
"""

import pytest
from decimal import Decimal
from datetime import date, timedelta

from oxidation_finance_v20.business.cost_calculation_engine import CostCalculationEngine
from oxidation_finance_v20.business.order_manager import OrderManager
from oxidation_finance_v20.business.outsourced_processing_manager import (
    OutsourcedProcessingManager,
)
from oxidation_finance_v20.models.business_models import PricingUnit, ProcessType


class TestCostCalculationEngine:
    """费用计算引擎测试"""

    def test_calculate_base_processing_fee_simple(self, db_manager):
        """测试基础加工费计算 - 简单情况"""
        engine = CostCalculationEngine(db_manager)

        # 10件 × 5元/件 = 50元
        fee = engine.calculate_base_processing_fee(
            Decimal("10"), Decimal("5.00"), PricingUnit.PIECE
        )

        assert fee == Decimal("50.00")

    def test_calculate_base_processing_fee_decimal(self, db_manager):
        """测试基础加工费计算 - 小数情况"""
        engine = CostCalculationEngine(db_manager)

        # 15.5米 × 12.8元/米 = 198.40元
        fee = engine.calculate_base_processing_fee(
            Decimal("15.5"), Decimal("12.8"), PricingUnit.METER
        )

        assert fee == Decimal("198.40")

    def test_calculate_base_processing_fee_rounding(self, db_manager):
        """测试基础加工费计算 - 四舍五入"""
        engine = CostCalculationEngine(db_manager)

        # 测试四舍五入到两位小数
        fee = engine.calculate_base_processing_fee(
            Decimal("3"), Decimal("1.666"), PricingUnit.PIECE
        )

        # 3 × 1.666 = 4.998，四舍五入为 5.00
        assert fee == Decimal("5.00")

    def test_calculate_base_processing_fee_zero_quantity(self, db_manager):
        """测试基础加工费计算 - 零数量"""
        engine = CostCalculationEngine(db_manager)

        fee = engine.calculate_base_processing_fee(
            Decimal("0"), Decimal("10.00"), PricingUnit.PIECE
        )

        assert fee == Decimal("0.00")

    def test_calculate_base_processing_fee_zero_price(self, db_manager):
        """测试基础加工费计算 - 零单价"""
        engine = CostCalculationEngine(db_manager)

        fee = engine.calculate_base_processing_fee(
            Decimal("100"), Decimal("0"), PricingUnit.PIECE
        )

        assert fee == Decimal("0.00")

    def test_calculate_base_processing_fee_negative_quantity(self, db_manager):
        """测试基础加工费计算 - 负数量（应该抛出异常）"""
        engine = CostCalculationEngine(db_manager)

        with pytest.raises(ValueError, match="数量不能为负数"):
            engine.calculate_base_processing_fee(
                Decimal("-10"), Decimal("5.00"), PricingUnit.PIECE
            )

    def test_calculate_base_processing_fee_negative_price(self, db_manager):
        """测试基础加工费计算 - 负单价（应该抛出异常）"""
        engine = CostCalculationEngine(db_manager)

        with pytest.raises(ValueError, match="单价不能为负数"):
            engine.calculate_base_processing_fee(
                Decimal("10"), Decimal("-5.00"), PricingUnit.PIECE
            )

    def test_calculate_base_processing_fee_all_pricing_units(self, db_manager):
        """测试所有七种计价方式"""
        engine = CostCalculationEngine(db_manager)

        # 测试所有七种计价单位
        for pricing_unit in PricingUnit:
            fee = engine.calculate_base_processing_fee(
                Decimal("10"), Decimal("5.00"), pricing_unit
            )
            assert fee == Decimal("50.00")

    def test_calculate_outsourcing_cost_no_outsourcing(self, db_manager, order_manager):
        """测试委外加工费计算 - 无委外"""
        engine = CostCalculationEngine(db_manager)

        # 创建订单（无委外）
        order = order_manager.create_order(
            customer_id="C001",
            customer_name="测试客户",
            item_description="铝型材",
            quantity=Decimal("100"),
            pricing_unit=PricingUnit.PIECE,
            unit_price=Decimal("10.00"),
            processes=[ProcessType.OXIDATION],
        )

        cost = engine.calculate_outsourcing_cost(order.id)
        assert cost == Decimal("0.00")

    def test_calculate_outsourcing_cost_single(
        self, db_manager, order_manager, outsourced_manager
    ):
        """测试委外加工费计算 - 单个委外"""
        engine = CostCalculationEngine(db_manager)

        # 创建订单
        order = order_manager.create_order(
            customer_id="C001",
            customer_name="测试客户",
            item_description="铝型材",
            quantity=Decimal("100"),
            pricing_unit=PricingUnit.PIECE,
            unit_price=Decimal("10.00"),
            processes=[ProcessType.SANDBLASTING, ProcessType.OXIDATION],
            outsourced_processes=["喷砂"],
        )

        # 添加委外加工记录
        outsourced_manager.create_processing(
            order_id=order.id,
            supplier_id="S001",
            supplier_name="喷砂供应商",
            process_type=ProcessType.SANDBLASTING,
            quantity=Decimal("100"),
            unit_price=Decimal("2.00"),
        )

        cost = engine.calculate_outsourcing_cost(order.id)
        assert cost == Decimal("200.00")

    def test_calculate_outsourcing_cost_multiple(
        self, db_manager, order_manager, outsourced_manager
    ):
        """测试委外加工费计算 - 多个委外"""
        engine = CostCalculationEngine(db_manager)

        # 创建订单
        order = order_manager.create_order(
            customer_id="C001",
            customer_name="测试客户",
            item_description="铝型材",
            quantity=Decimal("100"),
            pricing_unit=PricingUnit.PIECE,
            unit_price=Decimal("10.00"),
            processes=[
                ProcessType.SANDBLASTING,
                ProcessType.POLISHING,
                ProcessType.OXIDATION,
            ],
            outsourced_processes=["喷砂", "抛光"],
        )

        # 添加第一个委外加工记录
        outsourced_manager.create_processing(
            order_id=order.id,
            supplier_id="S001",
            supplier_name="喷砂供应商",
            process_type=ProcessType.SANDBLASTING,
            quantity=Decimal("100"),
            unit_price=Decimal("2.00"),
        )

        # 添加第二个委外加工记录
        outsourced_manager.create_processing(
            order_id=order.id,
            supplier_id="S002",
            supplier_name="抛光供应商",
            process_type=ProcessType.POLISHING,
            quantity=Decimal("100"),
            unit_price=Decimal("3.00"),
        )

        cost = engine.calculate_outsourcing_cost(order.id)
        # 200 + 300 = 500
        assert cost == Decimal("500.00")

    def test_calculate_total_processing_fee_no_outsourcing(
        self, db_manager, order_manager
    ):
        """测试总加工费计算 - 无委外"""
        engine = CostCalculationEngine(db_manager)

        # 创建订单
        order = order_manager.create_order(
            customer_id="C001",
            customer_name="测试客户",
            item_description="铝型材",
            quantity=Decimal("100"),
            pricing_unit=PricingUnit.PIECE,
            unit_price=Decimal("10.00"),
            processes=[ProcessType.OXIDATION],
        )

        total_fee = engine.calculate_total_processing_fee(order.id)
        # 基础费用 = 100 × 10 = 1000
        # 委外费用 = 0
        # 总费用 = 1000
        assert total_fee == Decimal("1000.00")

    def test_calculate_total_processing_fee_with_outsourcing(
        self, db_manager, order_manager, outsourced_manager
    ):
        """测试总加工费计算 - 含委外"""
        engine = CostCalculationEngine(db_manager)

        # 创建订单
        order = order_manager.create_order(
            customer_id="C001",
            customer_name="测试客户",
            item_description="铝型材",
            quantity=Decimal("100"),
            pricing_unit=PricingUnit.PIECE,
            unit_price=Decimal("10.00"),
            processes=[ProcessType.SANDBLASTING, ProcessType.OXIDATION],
            outsourced_processes=["喷砂"],
        )

        # 添加委外加工记录
        outsourced_manager.create_processing(
            order_id=order.id,
            supplier_id="S001",
            supplier_name="喷砂供应商",
            process_type=ProcessType.SANDBLASTING,
            quantity=Decimal("100"),
            unit_price=Decimal("2.00"),
        )

        total_fee = engine.calculate_total_processing_fee(order.id)
        # 基础费用 = 100 × 10 = 1000
        # 委外费用 = 100 × 2 = 200
        # 总费用 = 1200
        assert total_fee == Decimal("1200.00")

    def test_calculate_total_processing_fee_nonexistent_order(self, db_manager):
        """测试总加工费计算 - 订单不存在"""
        engine = CostCalculationEngine(db_manager)

        with pytest.raises(ValueError, match="订单不存在"):
            engine.calculate_total_processing_fee("nonexistent-id")

    def test_update_order_costs(self, db_manager, order_manager, outsourced_manager):
        """测试更新订单费用"""
        engine = CostCalculationEngine(db_manager)

        # 创建订单
        order = order_manager.create_order(
            customer_id="C001",
            customer_name="测试客户",
            item_description="铝型材",
            quantity=Decimal("100"),
            pricing_unit=PricingUnit.PIECE,
            unit_price=Decimal("10.00"),
            processes=[ProcessType.SANDBLASTING, ProcessType.OXIDATION],
            outsourced_processes=["喷砂"],
        )

        # 添加委外加工记录
        outsourced_manager.create_processing(
            order_id=order.id,
            supplier_id="S001",
            supplier_name="喷砂供应商",
            process_type=ProcessType.SANDBLASTING,
            quantity=Decimal("100"),
            unit_price=Decimal("2.00"),
        )

        # 更新订单费用
        updated_order = engine.update_order_costs(order.id)

        assert updated_order.total_amount == Decimal("1000.00")
        assert updated_order.outsourcing_cost == Decimal("200.00")

    def test_calculate_order_profit(
        self, db_manager, order_manager, outsourced_manager
    ):
        """测试订单利润计算"""
        engine = CostCalculationEngine(db_manager)

        # 创建订单
        order = order_manager.create_order(
            customer_id="C001",
            customer_name="测试客户",
            item_description="铝型材",
            quantity=Decimal("100"),
            pricing_unit=PricingUnit.PIECE,
            unit_price=Decimal("10.00"),
            processes=[ProcessType.SANDBLASTING, ProcessType.OXIDATION],
            outsourced_processes=["喷砂"],
        )

        # 添加委外加工记录
        outsourced_manager.create_processing(
            order_id=order.id,
            supplier_id="S001",
            supplier_name="喷砂供应商",
            process_type=ProcessType.SANDBLASTING,
            quantity=Decimal("100"),
            unit_price=Decimal("2.00"),
        )

        profit = engine.calculate_order_profit(order.id)
        # 总费用 = 1000 + 200 = 1200
        # 委外费用 = 200
        # 利润 = 1200 - 200 = 1000
        assert profit == Decimal("1000.00")

    def test_calculate_order_profit_margin(
        self, db_manager, order_manager, outsourced_manager
    ):
        """测试订单利润率计算"""
        engine = CostCalculationEngine(db_manager)

        # 创建订单
        order = order_manager.create_order(
            customer_id="C001",
            customer_name="测试客户",
            item_description="铝型材",
            quantity=Decimal("100"),
            pricing_unit=PricingUnit.PIECE,
            unit_price=Decimal("10.00"),
            processes=[ProcessType.SANDBLASTING, ProcessType.OXIDATION],
            outsourced_processes=["喷砂"],
        )

        # 添加委外加工记录
        outsourced_manager.create_processing(
            order_id=order.id,
            supplier_id="S001",
            supplier_name="喷砂供应商",
            process_type=ProcessType.SANDBLASTING,
            quantity=Decimal("100"),
            unit_price=Decimal("2.00"),
        )

        margin = engine.calculate_order_profit_margin(order.id)
        # 总费用 = 1200
        # 利润 = 1000
        # 利润率 = (1000 / 1200) × 100% = 83.33%
        assert margin == Decimal("83.33")

    def test_calculate_order_profit_margin_zero_fee(self, db_manager, order_manager):
        """测试订单利润率计算 - 零费用"""
        engine = CostCalculationEngine(db_manager)

        # 创建零费用订单
        order = order_manager.create_order(
            customer_id="C001",
            customer_name="测试客户",
            item_description="铝型材",
            quantity=Decimal("0"),
            pricing_unit=PricingUnit.PIECE,
            unit_price=Decimal("10.00"),
            processes=[ProcessType.OXIDATION],
        )

        margin = engine.calculate_order_profit_margin(order.id)
        assert margin == Decimal("0")

    def test_validate_order_costs_valid(
        self, db_manager, order_manager, outsourced_manager
    ):
        """测试订单费用验证 - 有效"""
        engine = CostCalculationEngine(db_manager)

        # 创建订单
        order = order_manager.create_order(
            customer_id="C001",
            customer_name="测试客户",
            item_description="铝型材",
            quantity=Decimal("100"),
            pricing_unit=PricingUnit.PIECE,
            unit_price=Decimal("10.00"),
            processes=[ProcessType.SANDBLASTING, ProcessType.OXIDATION],
            outsourced_processes=["喷砂"],
        )

        # 添加委外加工记录
        outsourced_manager.create_processing(
            order_id=order.id,
            supplier_id="S001",
            supplier_name="喷砂供应商",
            process_type=ProcessType.SANDBLASTING,
            quantity=Decimal("100"),
            unit_price=Decimal("2.00"),
        )

        # 更新订单费用
        engine.update_order_costs(order.id)

        # 验证
        result = engine.validate_order_costs(order.id)

        assert result["valid"] is True
        assert result["base_fee_match"] is True
        assert result["outsourcing_match"] is True
        assert result["total_match"] is True

    def test_calculate_pricing_unit_statistics(self, db_manager, order_manager):
        """测试按计价方式统计"""
        engine = CostCalculationEngine(db_manager)

        # 创建多个订单
        for i in range(3):
            order_manager.create_order(
                customer_id=f"C{i:03d}",
                customer_name=f"客户{i}",
                item_description="铝型材",
                quantity=Decimal("100"),
                pricing_unit=PricingUnit.PIECE,
                unit_price=Decimal("10.00"),
                processes=[ProcessType.OXIDATION],
            )

        stats = engine.calculate_pricing_unit_statistics(PricingUnit.PIECE)

        assert stats["total_orders"] == 3
        assert stats["total_quantity"] == Decimal("300")
        assert stats["total_base_fee"] == Decimal("3000.00")
        assert stats["avg_unit_price"] == Decimal("10.00")

    def test_calculate_all_pricing_units_statistics(self, db_manager, order_manager):
        """测试所有计价方式统计"""
        engine = CostCalculationEngine(db_manager)

        # 创建不同计价方式的订单
        order_manager.create_order(
            customer_id="C001",
            customer_name="客户1",
            item_description="螺丝",
            quantity=Decimal("1000"),
            pricing_unit=PricingUnit.PIECE,
            unit_price=Decimal("0.50"),
            processes=[ProcessType.OXIDATION],
        )

        order_manager.create_order(
            customer_id="C002",
            customer_name="客户2",
            item_description="铝型材",
            quantity=Decimal("50"),
            pricing_unit=PricingUnit.METER,
            unit_price=Decimal("15.00"),
            processes=[ProcessType.OXIDATION],
        )

        stats_list = engine.calculate_all_pricing_units_statistics()

        # 应该有两种计价方式
        assert len(stats_list) == 2

        # 检查是否包含两种计价方式
        pricing_units = [s["pricing_unit"] for s in stats_list]
        assert "件" in pricing_units
        assert "米" in pricing_units
