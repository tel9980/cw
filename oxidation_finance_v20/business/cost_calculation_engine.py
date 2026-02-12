#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
费用自动计算引擎 - 负责订单费用的自动计算
支持不同计价方式和委外加工费用的集成
"""

from decimal import Decimal
from typing import Optional, Dict, List
from datetime import date

from ..models.business_models import (
    ProcessingOrder, PricingUnit, OutsourcedProcessing
)
from ..database.db_manager import DatabaseManager


class CostCalculationEngine:
    """费用自动计算引擎
    
    支持七种计价方式的费用计算，并集成委外加工费用
    确保费用计算的准确性和一致性
    """
    
    def __init__(self, db_manager: DatabaseManager):
        """初始化费用计算引擎
        
        Args:
            db_manager: 数据库管理器实例
        """
        self.db = db_manager
    
    def calculate_base_processing_fee(
        self,
        quantity: Decimal,
        unit_price: Decimal,
        pricing_unit: PricingUnit
    ) -> Decimal:
        """计算基础加工费用
        
        根据数量、单价和计价单位计算基础加工费
        
        Args:
            quantity: 数量
            unit_price: 单价
            pricing_unit: 计价单位（七种之一）
            
        Returns:
            基础加工费用
        """
        # 验证输入
        if quantity < 0:
            raise ValueError("数量不能为负数")
        if unit_price < 0:
            raise ValueError("单价不能为负数")
        
        # 计算基础费用：数量 × 单价
        base_fee = quantity * unit_price
        
        # 保留两位小数
        return base_fee.quantize(Decimal("0.01"))
    
    def calculate_outsourcing_cost(
        self,
        order_id: str
    ) -> Decimal:
        """计算订单的委外加工总成本
        
        Args:
            order_id: 订单ID
            
        Returns:
            委外加工总成本
        """
        # 获取订单的所有委外加工记录
        outsourced_list = self.db.list_outsourced_processing(order_id=order_id)
        
        # 累加所有委外加工的总成本
        total_cost = sum(
            processing.total_cost 
            for processing in outsourced_list
        ) if outsourced_list else Decimal("0")
        
        # 确保返回Decimal类型
        if not isinstance(total_cost, Decimal):
            total_cost = Decimal(str(total_cost))
        
        return total_cost.quantize(Decimal("0.01"))
    
    def calculate_total_processing_fee(
        self,
        order_id: str
    ) -> Decimal:
        """计算订单的总加工费用
        
        总加工费 = 基础加工费 + 委外加工费
        
        Args:
            order_id: 订单ID
            
        Returns:
            总加工费用
        """
        # 获取订单信息
        order = self.db.get_order(order_id)
        if not order:
            raise ValueError(f"订单不存在: {order_id}")
        
        # 计算基础加工费
        base_fee = self.calculate_base_processing_fee(
            order.quantity,
            order.unit_price,
            order.pricing_unit
        )
        
        # 计算委外加工费
        outsourcing_cost = self.calculate_outsourcing_cost(order_id)
        
        # 总费用 = 基础费用 + 委外费用
        total_fee = base_fee + outsourcing_cost
        
        return total_fee.quantize(Decimal("0.01"))
    
    def update_order_costs(
        self,
        order_id: str
    ) -> ProcessingOrder:
        """更新订单的费用信息
        
        重新计算并更新订单的基础加工费和委外加工费
        
        Args:
            order_id: 订单ID
            
        Returns:
            更新后的订单对象
        """
        # 获取订单
        order = self.db.get_order(order_id)
        if not order:
            raise ValueError(f"订单不存在: {order_id}")
        
        # 重新计算基础加工费
        base_fee = self.calculate_base_processing_fee(
            order.quantity,
            order.unit_price,
            order.pricing_unit
        )
        
        # 重新计算委外加工费
        outsourcing_cost = self.calculate_outsourcing_cost(order_id)
        
        # 更新订单费用信息
        order.total_amount = base_fee
        order.outsourcing_cost = outsourcing_cost
        
        # 保存到数据库
        self.db.save_order(order)
        
        return order
    
    def calculate_order_profit(
        self,
        order_id: str
    ) -> Decimal:
        """计算订单的利润
        
        利润 = 总加工费 - 委外加工费
        
        Args:
            order_id: 订单ID
            
        Returns:
            订单利润
        """
        total_fee = self.calculate_total_processing_fee(order_id)
        outsourcing_cost = self.calculate_outsourcing_cost(order_id)
        
        profit = total_fee - outsourcing_cost
        
        return profit.quantize(Decimal("0.01"))
    
    def calculate_order_profit_margin(
        self,
        order_id: str
    ) -> Decimal:
        """计算订单的利润率
        
        利润率 = (利润 / 总加工费) × 100%
        
        Args:
            order_id: 订单ID
            
        Returns:
            利润率（百分比）
        """
        total_fee = self.calculate_total_processing_fee(order_id)
        
        if total_fee == 0:
            return Decimal("0")
        
        profit = self.calculate_order_profit(order_id)
        profit_margin = (profit / total_fee) * 100
        
        return profit_margin.quantize(Decimal("0.01"))
    
    def calculate_pricing_unit_statistics(
        self,
        pricing_unit: PricingUnit,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None
    ) -> Dict:
        """按计价方式统计费用
        
        Args:
            pricing_unit: 计价单位
            start_date: 开始日期（可选）
            end_date: 结束日期（可选）
            
        Returns:
            统计信息字典
        """
        # 获取所有订单
        all_orders = self.db.list_orders()
        
        # 筛选指定计价方式的订单
        filtered_orders = [
            order for order in all_orders
            if order.pricing_unit == pricing_unit
        ]
        
        # 按日期筛选
        if start_date:
            filtered_orders = [
                order for order in filtered_orders
                if order.order_date >= start_date
            ]
        if end_date:
            filtered_orders = [
                order for order in filtered_orders
                if order.order_date <= end_date
            ]
        
        # 统计
        total_orders = len(filtered_orders)
        total_quantity = sum(order.quantity for order in filtered_orders)
        total_base_fee = sum(order.total_amount for order in filtered_orders)
        total_outsourcing = sum(order.outsourcing_cost for order in filtered_orders)
        total_fee = total_base_fee + total_outsourcing
        
        avg_unit_price = (
            total_base_fee / total_quantity 
            if total_quantity > 0 
            else Decimal("0")
        )
        
        return {
            "pricing_unit": pricing_unit.value,
            "total_orders": total_orders,
            "total_quantity": total_quantity,
            "total_base_fee": total_base_fee,
            "total_outsourcing_cost": total_outsourcing,
            "total_fee": total_fee,
            "avg_unit_price": avg_unit_price.quantize(Decimal("0.01"))
        }
    
    def calculate_all_pricing_units_statistics(
        self,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None
    ) -> List[Dict]:
        """统计所有计价方式的费用
        
        Args:
            start_date: 开始日期（可选）
            end_date: 结束日期（可选）
            
        Returns:
            所有计价方式的统计信息列表
        """
        statistics = []
        
        for pricing_unit in PricingUnit:
            stats = self.calculate_pricing_unit_statistics(
                pricing_unit,
                start_date,
                end_date
            )
            
            # 只包含有订单的计价方式
            if stats["total_orders"] > 0:
                statistics.append(stats)
        
        return statistics
    
    def validate_order_costs(
        self,
        order_id: str
    ) -> Dict[str, bool]:
        """验证订单费用计算的正确性
        
        检查订单的费用是否与实际计算一致
        
        Args:
            order_id: 订单ID
            
        Returns:
            验证结果字典
        """
        order = self.db.get_order(order_id)
        if not order:
            return {"valid": False, "error": "订单不存在"}
        
        # 重新计算费用
        calculated_base_fee = self.calculate_base_processing_fee(
            order.quantity,
            order.unit_price,
            order.pricing_unit
        )
        calculated_outsourcing = self.calculate_outsourcing_cost(order_id)
        calculated_total = calculated_base_fee + calculated_outsourcing
        
        # 比较
        base_fee_match = order.total_amount == calculated_base_fee
        outsourcing_match = order.outsourcing_cost == calculated_outsourcing
        
        stored_total = order.total_amount + order.outsourcing_cost
        total_match = stored_total == calculated_total
        
        return {
            "valid": base_fee_match and outsourcing_match and total_match,
            "base_fee_match": base_fee_match,
            "outsourcing_match": outsourcing_match,
            "total_match": total_match,
            "stored_base_fee": order.total_amount,
            "calculated_base_fee": calculated_base_fee,
            "stored_outsourcing": order.outsourcing_cost,
            "calculated_outsourcing": calculated_outsourcing,
            "stored_total": stored_total,
            "calculated_total": calculated_total
        }
    
    def recalculate_all_orders(self) -> Dict[str, int]:
        """重新计算所有订单的费用
        
        用于数据修复或批量更新
        
        Returns:
            更新结果统计
        """
        all_orders = self.db.list_orders()
        
        updated_count = 0
        error_count = 0
        
        for order in all_orders:
            try:
                self.update_order_costs(order.id)
                updated_count += 1
            except Exception as e:
                error_count += 1
                print(f"更新订单 {order.order_no} 失败: {e}")
        
        return {
            "total_orders": len(all_orders),
            "updated": updated_count,
            "errors": error_count
        }
