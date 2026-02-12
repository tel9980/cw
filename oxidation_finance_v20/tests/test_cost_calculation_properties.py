#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
费用计算引擎属性测试
使用Hypothesis进行基于属性的测试
"""

import pytest
from hypothesis import given, strategies as st, assume, settings, HealthCheck
from decimal import Decimal
from datetime import date, timedelta
import tempfile
import os
from contextlib import contextmanager

from oxidation_finance_v20.database.db_manager import DatabaseManager
from oxidation_finance_v20.business.order_manager import OrderManager
from oxidation_finance_v20.business.outsourced_processing_manager import OutsourcedProcessingManager
from oxidation_finance_v20.business.cost_calculation_engine import CostCalculationEngine
from oxidation_finance_v20.models.business_models import PricingUnit, ProcessType


# 策略定义
pricing_units = st.sampled_from(list(PricingUnit))
process_types = st.sampled_from(list(ProcessType))

# 正数Decimal策略（0.01到10000.00）
positive_decimal = st.decimals(
    min_value=Decimal("0.01"),
    max_value=Decimal("10000.00"),
    places=2
)

# 非负Decimal策略（0到10000.00）
non_negative_decimal = st.decimals(
    min_value=Decimal("0"),
    max_value=Decimal("10000.00"),
    places=2
)

# 数量策略（0到1000）
quantity_decimal = st.decimals(
    min_value=Decimal("0"),
    max_value=Decimal("1000"),
    places=2
)


@contextmanager
def create_test_db():
    """创建测试数据库的上下文管理器"""
    fd, path = tempfile.mkstemp(suffix='.db')
    os.close(fd)
    
    db = DatabaseManager(path)
    db.connect()
    
    try:
        yield db
    finally:
        db.close()
        try:
            os.unlink(path)
        except:
            pass


class TestCostCalculationProperties:
    """费用计算引擎属性测试"""
    
    @given(
        quantity=quantity_decimal,
        unit_price=positive_decimal,
        pricing_unit=pricing_units
    )
    @settings(max_examples=100, deadline=None, suppress_health_check=[HealthCheck.function_scoped_fixture])
    def test_property_4_base_fee_calculation_accuracy(
        self,
        quantity,
        unit_price,
        pricing_unit
    ):
        """
        **属性 4: 费用计算准确性**
        
        对于任何完成的订单，自动计算的总加工费用应该等于
        所有订单项目费用和委外加工费用的总和
        
        **验证: 需求 1.4**
        
        基础加工费 = 数量 × 单价
        """
        with create_test_db() as test_db:
            engine = CostCalculationEngine(test_db)
            
            # 计算基础加工费
            calculated_fee = engine.calculate_base_processing_fee(
                quantity,
                unit_price,
                pricing_unit
            )
            
            # 验证：计算结果应该等于数量乘以单价（保留两位小数）
            expected_fee = (quantity * unit_price).quantize(Decimal("0.01"))
            
            assert calculated_fee == expected_fee, (
                f"基础加工费计算不准确: "
                f"数量={quantity}, 单价={unit_price}, "
                f"计算结果={calculated_fee}, 期望={expected_fee}"
            )
    
    @given(
        quantity=quantity_decimal,
        unit_price=positive_decimal,
        pricing_unit=pricing_units,
        outsourced_quantity=quantity_decimal,
        outsourced_unit_price=positive_decimal
    )
    @settings(max_examples=100, deadline=None, suppress_health_check=[HealthCheck.function_scoped_fixture])
    def test_property_4_total_fee_with_outsourcing(
        self,
        quantity,
        unit_price,
        pricing_unit,
        outsourced_quantity,
        outsourced_unit_price
    ):
        """
        **属性 4: 费用计算准确性（含委外）**
        
        总加工费 = 基础加工费 + 委外加工费
        
        **验证: 需求 1.4**
        """
        with create_test_db() as test_db:
            # 创建管理器
            order_mgr = OrderManager(test_db)
            outsourced_mgr = OutsourcedProcessingManager(test_db)
            engine = CostCalculationEngine(test_db)
            
            # 创建订单
            order = order_mgr.create_order(
                customer_id="C001",
                customer_name="测试客户",
                item_description="测试物品",
                quantity=quantity,
                pricing_unit=pricing_unit,
                unit_price=unit_price,
                processes=[ProcessType.SANDBLASTING, ProcessType.OXIDATION],
                outsourced_processes=["喷砂"]
            )
            
            # 添加委外加工（如果数量大于0）
            if outsourced_quantity > 0:
                outsourced_mgr.create_processing(
                    order_id=order.id,
                    supplier_id="S001",
                    supplier_name="委外供应商",
                    process_type=ProcessType.SANDBLASTING,
                    quantity=outsourced_quantity,
                    unit_price=outsourced_unit_price
                )
            
            # 计算费用
            base_fee = engine.calculate_base_processing_fee(
                quantity,
                unit_price,
                pricing_unit
            )
            outsourcing_cost = engine.calculate_outsourcing_cost(order.id)
            total_fee = engine.calculate_total_processing_fee(order.id)
            
            # 验证：总费用 = 基础费用 + 委外费用
            expected_total = base_fee + outsourcing_cost
            
            assert total_fee == expected_total, (
                f"总费用计算不准确: "
                f"基础费用={base_fee}, 委外费用={outsourcing_cost}, "
                f"计算总费用={total_fee}, 期望总费用={expected_total}"
            )
    
    @given(
        quantity=quantity_decimal,
        unit_price=positive_decimal,
        pricing_unit=pricing_units,
        num_outsourced=st.integers(min_value=0, max_value=5)
    )
    @settings(max_examples=50, deadline=None, suppress_health_check=[HealthCheck.function_scoped_fixture])
    def test_property_4_multiple_outsourcing_sum(
        self,
        quantity,
        unit_price,
        pricing_unit,
        num_outsourced
    ):
        """
        **属性 4: 费用计算准确性（多个委外）**
        
        多个委外加工的总成本应该等于各个委外加工成本的总和
        
        **验证: 需求 1.4**
        """
        with create_test_db() as test_db:
            # 创建管理器
            order_mgr = OrderManager(test_db)
            outsourced_mgr = OutsourcedProcessingManager(test_db)
            engine = CostCalculationEngine(test_db)
            
            # 创建订单
            order = order_mgr.create_order(
                customer_id="C001",
                customer_name="测试客户",
                item_description="测试物品",
                quantity=quantity,
                pricing_unit=pricing_unit,
                unit_price=unit_price,
                processes=[ProcessType.SANDBLASTING, ProcessType.POLISHING, ProcessType.OXIDATION]
            )
            
            # 添加多个委外加工
            expected_total_cost = Decimal("0")
            process_types = [ProcessType.SANDBLASTING, ProcessType.POLISHING, ProcessType.WIRE_DRAWING]
            
            for i in range(num_outsourced):
                outsourced_qty = Decimal(str(10 + i * 5))
                outsourced_price = Decimal(str(2.00 + i * 0.5))
                
                outsourced_mgr.create_processing(
                    order_id=order.id,
                    supplier_id=f"S{i:03d}",
                    supplier_name=f"供应商{i}",
                    process_type=process_types[i % len(process_types)],
                    quantity=outsourced_qty,
                    unit_price=outsourced_price
                )
                
                expected_total_cost += (outsourced_qty * outsourced_price).quantize(Decimal("0.01"))
            
            # 计算委外总成本
            calculated_cost = engine.calculate_outsourcing_cost(order.id)
            
            # 验证：计算的总成本应该等于各个委外成本的总和
            assert calculated_cost == expected_total_cost, (
                f"多个委外加工总成本计算不准确: "
                f"计算结果={calculated_cost}, 期望={expected_total_cost}"
            )
    
    @given(
        quantity=quantity_decimal,
        unit_price=positive_decimal,
        pricing_unit=pricing_units
    )
    @settings(max_examples=100, deadline=None, suppress_health_check=[HealthCheck.function_scoped_fixture])
    def test_property_4_fee_non_negative(
        self,
        quantity,
        unit_price,
        pricing_unit
    ):
        """
        **属性 4: 费用计算准确性（非负性）**
        
        所有费用计算结果都应该是非负数
        
        **验证: 需求 1.4**
        """
        with create_test_db() as test_db:
            engine = CostCalculationEngine(test_db)
            
            # 计算基础加工费
            base_fee = engine.calculate_base_processing_fee(
                quantity,
                unit_price,
                pricing_unit
            )
            
            # 验证：费用应该是非负数
            assert base_fee >= 0, f"基础加工费不应该为负数: {base_fee}"
    
    @given(
        quantity=quantity_decimal,
        unit_price=positive_decimal,
        pricing_unit=pricing_units,
        outsourced_quantity=quantity_decimal,
        outsourced_unit_price=positive_decimal
    )
    @settings(max_examples=100, deadline=None, suppress_health_check=[HealthCheck.function_scoped_fixture])
    def test_property_4_update_costs_consistency(
        self,
        quantity,
        unit_price,
        pricing_unit,
        outsourced_quantity,
        outsourced_unit_price
    ):
        """
        **属性 4: 费用计算准确性（更新一致性）**
        
        更新订单费用后，订单中存储的费用应该与重新计算的费用一致
        
        **验证: 需求 1.4**
        """
        with create_test_db() as test_db:
            # 创建管理器
            order_mgr = OrderManager(test_db)
            outsourced_mgr = OutsourcedProcessingManager(test_db)
            engine = CostCalculationEngine(test_db)
            
            # 创建订单
            order = order_mgr.create_order(
                customer_id="C001",
                customer_name="测试客户",
                item_description="测试物品",
                quantity=quantity,
                pricing_unit=pricing_unit,
                unit_price=unit_price,
                processes=[ProcessType.OXIDATION]
            )
            
            # 添加委外加工（如果数量大于0）
            if outsourced_quantity > 0:
                outsourced_mgr.create_processing(
                    order_id=order.id,
                    supplier_id="S001",
                    supplier_name="委外供应商",
                    process_type=ProcessType.SANDBLASTING,
                    quantity=outsourced_quantity,
                    unit_price=outsourced_unit_price
                )
            
            # 更新订单费用
            updated_order = engine.update_order_costs(order.id)
            
            # 重新计算费用
            recalculated_base = engine.calculate_base_processing_fee(
                quantity,
                unit_price,
                pricing_unit
            )
            recalculated_outsourcing = engine.calculate_outsourcing_cost(order.id)
            
            # 验证：更新后的费用应该与重新计算的费用一致
            assert updated_order.total_amount == recalculated_base, (
                f"更新后的基础费用不一致: "
                f"存储={updated_order.total_amount}, 重新计算={recalculated_base}"
            )
            
            assert updated_order.outsourcing_cost == recalculated_outsourcing, (
                f"更新后的委外费用不一致: "
                f"存储={updated_order.outsourcing_cost}, 重新计算={recalculated_outsourcing}"
            )
    
    @given(
        quantity=quantity_decimal,
        unit_price=positive_decimal,
        pricing_unit=pricing_units,
        outsourced_quantity=quantity_decimal,
        outsourced_unit_price=positive_decimal
    )
    @settings(max_examples=100, deadline=None, suppress_health_check=[HealthCheck.function_scoped_fixture])
    def test_property_4_validation_accuracy(
        self,
        quantity,
        unit_price,
        pricing_unit,
        outsourced_quantity,
        outsourced_unit_price
    ):
        """
        **属性 4: 费用计算准确性（验证功能）**
        
        费用验证功能应该能够正确识别费用是否准确
        
        **验证: 需求 1.4**
        """
        with create_test_db() as test_db:
            # 创建管理器
            order_mgr = OrderManager(test_db)
            outsourced_mgr = OutsourcedProcessingManager(test_db)
            engine = CostCalculationEngine(test_db)
            
            # 创建订单
            order = order_mgr.create_order(
                customer_id="C001",
                customer_name="测试客户",
                item_description="测试物品",
                quantity=quantity,
                pricing_unit=pricing_unit,
                unit_price=unit_price,
                processes=[ProcessType.OXIDATION]
            )
            
            # 添加委外加工（如果数量大于0）
            if outsourced_quantity > 0:
                outsourced_mgr.create_processing(
                    order_id=order.id,
                    supplier_id="S001",
                    supplier_name="委外供应商",
                    process_type=ProcessType.SANDBLASTING,
                    quantity=outsourced_quantity,
                    unit_price=outsourced_unit_price
                )
            
            # 更新订单费用
            engine.update_order_costs(order.id)
            
            # 验证费用
            validation = engine.validate_order_costs(order.id)
            
            # 验证：费用应该是有效的
            assert validation["valid"] is True, (
                f"费用验证失败: {validation}"
            )
            assert validation["base_fee_match"] is True
            assert validation["outsourcing_match"] is True
            assert validation["total_match"] is True
    
    @given(
        pricing_unit=pricing_units
    )
    @settings(max_examples=20, deadline=None, suppress_health_check=[HealthCheck.function_scoped_fixture])
    def test_property_4_all_pricing_units_supported(
        self,
        pricing_unit
    ):
        """
        **属性 4: 费用计算准确性（计价方式支持）**
        
        所有七种计价方式都应该能够正确计算费用
        
        **验证: 需求 1.4, 1.2**
        """
        with create_test_db() as test_db:
            engine = CostCalculationEngine(test_db)
            
            # 使用固定的数量和单价测试
            quantity = Decimal("10.00")
            unit_price = Decimal("5.00")
            
            # 计算费用
            fee = engine.calculate_base_processing_fee(
                quantity,
                unit_price,
                pricing_unit
            )
            
            # 验证：费用应该等于数量乘以单价
            expected = Decimal("50.00")
            assert fee == expected, (
                f"计价方式 {pricing_unit.value} 的费用计算不正确: "
                f"计算结果={fee}, 期望={expected}"
            )
    
    @given(
        quantity=quantity_decimal,
        unit_price=positive_decimal,
        pricing_unit=pricing_units,
        outsourced_quantity=quantity_decimal,
        outsourced_unit_price=positive_decimal
    )
    @settings(max_examples=100, deadline=None, suppress_health_check=[HealthCheck.function_scoped_fixture])
    def test_property_4_profit_calculation_accuracy(
        self,
        quantity,
        unit_price,
        pricing_unit,
        outsourced_quantity,
        outsourced_unit_price
    ):
        """
        **属性 4: 费用计算准确性（利润计算）**
        
        利润 = 总加工费 - 委外加工费
        
        **验证: 需求 1.4**
        """
        with create_test_db() as test_db:
            # 创建管理器
            order_mgr = OrderManager(test_db)
            outsourced_mgr = OutsourcedProcessingManager(test_db)
            engine = CostCalculationEngine(test_db)
            
            # 创建订单
            order = order_mgr.create_order(
                customer_id="C001",
                customer_name="测试客户",
                item_description="测试物品",
                quantity=quantity,
                pricing_unit=pricing_unit,
                unit_price=unit_price,
                processes=[ProcessType.OXIDATION]
            )
            
            # 添加委外加工（如果数量大于0）
            if outsourced_quantity > 0:
                outsourced_mgr.create_processing(
                    order_id=order.id,
                    supplier_id="S001",
                    supplier_name="委外供应商",
                    process_type=ProcessType.SANDBLASTING,
                    quantity=outsourced_quantity,
                    unit_price=outsourced_unit_price
                )
            
            # 计算费用和利润
            total_fee = engine.calculate_total_processing_fee(order.id)
            outsourcing_cost = engine.calculate_outsourcing_cost(order.id)
            profit = engine.calculate_order_profit(order.id)
            
            # 验证：利润 = 总费用 - 委外费用
            expected_profit = total_fee - outsourcing_cost
            
            assert profit == expected_profit, (
                f"利润计算不准确: "
                f"总费用={total_fee}, 委外费用={outsourcing_cost}, "
                f"计算利润={profit}, 期望利润={expected_profit}"
            )
