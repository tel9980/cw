#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
订单管理器 - 负责加工订单的创建、更新和查询
"""

from datetime import date, datetime
from decimal import Decimal
from typing import List, Optional, Dict
import uuid

from ..models.business_models import (
    ProcessingOrder, Customer, OrderStatus, PricingUnit, ProcessType
)
from ..database.db_manager import DatabaseManager


class OrderManager:
    """订单管理器 - 支持订单的增删改查、七种计价方式和工序状态跟踪"""
    
    def __init__(self, db_manager: DatabaseManager):
        """初始化订单管理器
        
        Args:
            db_manager: 数据库管理器实例
        """
        self.db = db_manager
    
    def create_order(
        self,
        customer_id: str,
        customer_name: str,
        item_description: str,
        quantity: Decimal,
        pricing_unit: PricingUnit,
        unit_price: Decimal,
        processes: List[ProcessType],
        order_date: Optional[date] = None,
        outsourced_processes: Optional[List[str]] = None,
        notes: str = ""
    ) -> ProcessingOrder:
        """创建新订单
        
        Args:
            customer_id: 客户ID
            customer_name: 客户名称
            item_description: 物品描述
            quantity: 数量
            pricing_unit: 计价单位（七种之一）
            unit_price: 单价
            processes: 工序列表
            order_date: 订单日期（默认今天）
            outsourced_processes: 委外工序列表
            notes: 备注
            
        Returns:
            创建的订单对象
        """
        # 生成订单编号
        order_no = self._generate_order_no()
        
        # 计算总金额
        total_amount = quantity * unit_price
        
        # 创建订单对象
        order = ProcessingOrder(
            id=str(uuid.uuid4()),
            order_no=order_no,
            customer_id=customer_id,
            customer_name=customer_name,
            item_description=item_description,
            quantity=quantity,
            pricing_unit=pricing_unit,
            unit_price=unit_price,
            processes=processes,
            outsourced_processes=outsourced_processes or [],
            total_amount=total_amount,
            outsourcing_cost=Decimal("0"),
            status=OrderStatus.PENDING,
            order_date=order_date or date.today(),
            notes=notes,
            created_at=datetime.now(),
            updated_at=datetime.now()
        )
        
        # 保存到数据库
        self.db.save_order(order)
        
        return order
    
    def get_order(self, order_id: str) -> Optional[ProcessingOrder]:
        """获取订单详情
        
        Args:
            order_id: 订单ID
            
        Returns:
            订单对象，如果不存在返回None
        """
        return self.db.get_order(order_id)
    
    def get_order_by_no(self, order_no: str) -> Optional[ProcessingOrder]:
        """根据订单编号获取订单
        
        Args:
            order_no: 订单编号
            
        Returns:
            订单对象，如果不存在返回None
        """
        orders = self.list_orders()
        for order in orders:
            if order.order_no == order_no:
                return order
        return None
    
    def update_order(self, order: ProcessingOrder) -> ProcessingOrder:
        """更新订单信息
        
        Args:
            order: 订单对象
            
        Returns:
            更新后的订单对象
        """
        order.updated_at = datetime.now()
        self.db.save_order(order)
        return order
    
    def update_order_status(
        self,
        order_id: str,
        new_status: OrderStatus,
        completion_date: Optional[date] = None,
        delivery_date: Optional[date] = None
    ) -> Optional[ProcessingOrder]:
        """更新订单状态
        
        Args:
            order_id: 订单ID
            new_status: 新状态
            completion_date: 完工日期（状态为已完工时）
            delivery_date: 交付日期（状态为已交付时）
            
        Returns:
            更新后的订单对象，如果订单不存在返回None
        """
        order = self.get_order(order_id)
        if not order:
            return None
        
        order.status = new_status
        
        # 根据状态更新相关日期
        if new_status == OrderStatus.COMPLETED and completion_date:
            order.completion_date = completion_date
        elif new_status == OrderStatus.DELIVERED and delivery_date:
            order.delivery_date = delivery_date
        
        return self.update_order(order)
    
    def update_outsourcing_cost(
        self,
        order_id: str,
        outsourcing_cost: Decimal
    ) -> Optional[ProcessingOrder]:
        """更新委外加工成本
        
        Args:
            order_id: 订单ID
            outsourcing_cost: 委外加工成本
            
        Returns:
            更新后的订单对象，如果订单不存在返回None
        """
        order = self.get_order(order_id)
        if not order:
            return None
        
        order.outsourcing_cost = outsourcing_cost
        return self.update_order(order)
    
    def calculate_processing_fee(self, order_id: str) -> Optional[Decimal]:
        """计算订单的加工费用
        
        Args:
            order_id: 订单ID
            
        Returns:
            加工费用总额，如果订单不存在返回None
        """
        order = self.get_order(order_id)
        if not order:
            return None
        
        # 总加工费 = 基础加工费 + 委外加工费
        return order.total_amount + order.outsourcing_cost
    
    def list_orders(
        self,
        customer_id: Optional[str] = None,
        status: Optional[OrderStatus] = None
    ) -> List[ProcessingOrder]:
        """查询订单列表
        
        Args:
            customer_id: 客户ID（可选，用于筛选）
            status: 订单状态（可选，用于筛选）
            
        Returns:
            订单列表
        """
        return self.db.list_orders(customer_id=customer_id, status=status)
    
    def delete_order(self, order_id: str) -> bool:
        """删除订单
        
        Args:
            order_id: 订单ID
            
        Returns:
            是否删除成功
        """
        order = self.get_order(order_id)
        if not order:
            return False
        
        # 检查订单是否可以删除（例如：已收款的订单不能删除）
        if order.received_amount > 0:
            raise ValueError("已收款的订单不能删除")
        
        # 从数据库删除
        cursor = self.db.conn.cursor()
        cursor.execute("DELETE FROM processing_orders WHERE id = ?", (order_id,))
        self.db.conn.commit()
        
        return True
    
    def get_order_balance(self, order_id: str) -> Optional[Decimal]:
        """获取订单的未收款余额
        
        Args:
            order_id: 订单ID
            
        Returns:
            未收款余额，如果订单不存在返回None
        """
        order = self.get_order(order_id)
        if not order:
            return None
        
        total_fee = self.calculate_processing_fee(order_id)
        return total_fee - order.received_amount
    
    def record_payment(
        self,
        order_id: str,
        payment_amount: Decimal
    ) -> Optional[ProcessingOrder]:
        """记录订单收款
        
        Args:
            order_id: 订单ID
            payment_amount: 收款金额
            
        Returns:
            更新后的订单对象，如果订单不存在返回None
        """
        order = self.get_order(order_id)
        if not order:
            return None
        
        # 更新已收金额
        order.received_amount += payment_amount
        
        # 如果全额收款，更新状态为已收款
        total_fee = self.calculate_processing_fee(order_id)
        if order.received_amount >= total_fee:
            order.status = OrderStatus.PAID
        
        return self.update_order(order)
    
    def track_process_status(self, order_id: str) -> Optional[Dict[str, str]]:
        """跟踪订单的工序状态
        
        Args:
            order_id: 订单ID
            
        Returns:
            工序状态字典，如果订单不存在返回None
        """
        order = self.get_order(order_id)
        if not order:
            return None
        
        # 根据订单状态推断工序状态
        process_status = {}
        
        for process in order.processes:
            process_name = process.value
            
            # 判断工序是否委外
            if process_name in order.outsourced_processes:
                if order.status in [OrderStatus.OUTSOURCED, OrderStatus.IN_PROGRESS]:
                    process_status[process_name] = "委外中"
                elif order.status in [OrderStatus.COMPLETED, OrderStatus.DELIVERED, OrderStatus.PAID]:
                    process_status[process_name] = "已完成"
                else:
                    process_status[process_name] = "待加工"
            else:
                # 根据订单状态判断工序状态
                if order.status == OrderStatus.PENDING:
                    process_status[process_name] = "待加工"
                elif order.status in [OrderStatus.IN_PROGRESS, OrderStatus.OUTSOURCED]:
                    # 委外中状态时，非委外工序也可能在加工中
                    process_status[process_name] = "加工中"
                elif order.status in [OrderStatus.COMPLETED, OrderStatus.DELIVERED, OrderStatus.PAID]:
                    process_status[process_name] = "已完成"
                else:
                    process_status[process_name] = "未知"
        
        return process_status
    
    def get_orders_by_pricing_unit(
        self,
        pricing_unit: PricingUnit
    ) -> List[ProcessingOrder]:
        """根据计价方式查询订单
        
        Args:
            pricing_unit: 计价单位
            
        Returns:
            订单列表
        """
        all_orders = self.list_orders()
        return [order for order in all_orders if order.pricing_unit == pricing_unit]
    
    def get_customer_orders(
        self,
        customer_id: str,
        include_paid: bool = True
    ) -> List[ProcessingOrder]:
        """获取客户的所有订单
        
        Args:
            customer_id: 客户ID
            include_paid: 是否包含已收款订单
            
        Returns:
            订单列表
        """
        orders = self.list_orders(customer_id=customer_id)
        
        if not include_paid:
            orders = [order for order in orders if order.status != OrderStatus.PAID]
        
        return orders
    
    def _generate_order_no(self) -> str:
        """生成订单编号
        
        Returns:
            订单编号，格式：ORD-YYYYMMDD-XXXX
        """
        today = date.today()
        date_str = today.strftime("%Y%m%d")
        
        # 查询今天已有的订单数量
        all_orders = self.list_orders()
        today_orders = [
            order for order in all_orders
            if order.order_date == today
        ]
        
        # 生成序号
        seq = len(today_orders) + 1
        
        return f"ORD-{date_str}-{seq:04d}"
