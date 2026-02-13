"""
Processing Order Manager for Oxidation Factory

This module manages processing orders with multiple pricing units support.
Provides CRUD operations and query capabilities for processing orders.
"""

from datetime import date, datetime
from decimal import Decimal
from typing import List, Optional, Dict
import uuid
import json
import os

from ..models.core_models import (
    ProcessingOrder,
    OrderStatus,
    PricingUnit
)


class ProcessingOrderManager:
    """加工订单管理器
    
    功能:
    - 创建加工订单(支持多种计价单位)
    - 自动计算订单金额
    - 查询订单(按客户、日期、状态、计价单位)
    - 更新订单(状态、已收款、外发成本)
    """
    
    def __init__(self, data_dir: str = "财务数据"):
        """初始化订单管理器
        
        Args:
            data_dir: 数据存储目录
        """
        self.data_dir = data_dir
        self.orders_file = os.path.join(data_dir, "processing_orders.json")
        self._ensure_data_dir()
        self.orders: Dict[str, ProcessingOrder] = {}
        self._load_orders()
    
    def _ensure_data_dir(self):
        """确保数据目录存在"""
        if not os.path.exists(self.data_dir):
            os.makedirs(self.data_dir)
    
    def _load_orders(self):
        """从文件加载订单数据"""
        if os.path.exists(self.orders_file):
            try:
                with open(self.orders_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    for order_data in data:
                        order = ProcessingOrder.from_dict(order_data)
                        self.orders[order.id] = order
            except Exception as e:
                print(f"加载订单数据失败: {e}")
                self.orders = {}
    
    def _save_orders(self):
        """保存订单数据到文件"""
        try:
            data = [order.to_dict() for order in self.orders.values()]
            with open(self.orders_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"保存订单数据失败: {e}")
            raise
    
    def create_order(
        self,
        order_number: str,
        customer_id: str,
        order_date: date,
        product_name: str,
        pricing_unit: PricingUnit,
        quantity: Decimal,
        unit_price: Decimal,
        notes: str = ""
    ) -> ProcessingOrder:
        """创建加工订单
        
        Args:
            order_number: 订单编号
            customer_id: 客户ID
            order_date: 订单日期
            product_name: 产品名称
            pricing_unit: 计价单位
            quantity: 数量
            unit_price: 单价
            notes: 备注
            
        Returns:
            创建的订单对象
        """
        # 自动计算总金额
        total_amount = quantity * unit_price
        
        # 创建订单
        order = ProcessingOrder(
            id=str(uuid.uuid4()),
            order_number=order_number,
            customer_id=customer_id,
            order_date=order_date,
            product_name=product_name,
            pricing_unit=pricing_unit,
            quantity=quantity,
            unit_price=unit_price,
            total_amount=total_amount,
            status=OrderStatus.PENDING,
            received_amount=Decimal("0"),
            outsourced_cost=Decimal("0"),
            notes=notes,
            created_at=datetime.now(),
            updated_at=datetime.now()
        )
        
        # 保存订单
        self.orders[order.id] = order
        self._save_orders()
        
        return order
    
    def get_order(self, order_id: str) -> Optional[ProcessingOrder]:
        """获取订单
        
        Args:
            order_id: 订单ID
            
        Returns:
            订单对象,如果不存在返回None
        """
        return self.orders.get(order_id)
    
    def get_order_by_number(self, order_number: str) -> Optional[ProcessingOrder]:
        """根据订单编号获取订单
        
        Args:
            order_number: 订单编号
            
        Returns:
            订单对象,如果不存在返回None
        """
        for order in self.orders.values():
            if order.order_number == order_number:
                return order
        return None
    
    def query_orders(
        self,
        customer_id: Optional[str] = None,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
        status: Optional[OrderStatus] = None,
        pricing_unit: Optional[PricingUnit] = None
    ) -> List[ProcessingOrder]:
        """查询订单
        
        Args:
            customer_id: 客户ID(可选)
            start_date: 开始日期(可选)
            end_date: 结束日期(可选)
            status: 订单状态(可选)
            pricing_unit: 计价单位(可选)
            
        Returns:
            符合条件的订单列表
        """
        results = []
        
        for order in self.orders.values():
            # 按客户筛选
            if customer_id and order.customer_id != customer_id:
                continue
            
            # 按日期范围筛选
            if start_date and order.order_date < start_date:
                continue
            if end_date and order.order_date > end_date:
                continue
            
            # 按状态筛选
            if status and order.status != status:
                continue
            
            # 按计价单位筛选
            if pricing_unit and order.pricing_unit != pricing_unit:
                continue
            
            results.append(order)
        
        # 按订单日期降序排序
        results.sort(key=lambda x: x.order_date, reverse=True)
        
        return results
    
    def update_order_status(
        self,
        order_id: str,
        status: OrderStatus
    ) -> bool:
        """更新订单状态
        
        Args:
            order_id: 订单ID
            status: 新状态
            
        Returns:
            是否更新成功
        """
        order = self.orders.get(order_id)
        if not order:
            return False
        
        order.status = status
        order.updated_at = datetime.now()
        self._save_orders()
        
        return True
    
    def update_received_amount(
        self,
        order_id: str,
        amount: Decimal,
        add: bool = True
    ) -> bool:
        """更新已收款金额
        
        Args:
            order_id: 订单ID
            amount: 金额
            add: True表示增加,False表示设置为指定值
            
        Returns:
            是否更新成功
        """
        order = self.orders.get(order_id)
        if not order:
            return False
        
        if add:
            order.received_amount += amount
        else:
            order.received_amount = amount
        
        order.updated_at = datetime.now()
        self._save_orders()
        
        return True
    
    def update_outsourced_cost(
        self,
        order_id: str,
        cost: Decimal,
        add: bool = True
    ) -> bool:
        """更新外发加工成本
        
        Args:
            order_id: 订单ID
            cost: 成本
            add: True表示增加,False表示设置为指定值
            
        Returns:
            是否更新成功
        """
        order = self.orders.get(order_id)
        if not order:
            return False
        
        if add:
            order.outsourced_cost += cost
        else:
            order.outsourced_cost = cost
        
        order.updated_at = datetime.now()
        self._save_orders()
        
        return True
    
    def get_order_balance(self, order_id: str) -> Optional[Decimal]:
        """获取订单未收款余额
        
        Args:
            order_id: 订单ID
            
        Returns:
            未收款余额,如果订单不存在返回None
        """
        order = self.orders.get(order_id)
        if not order:
            return None
        
        return order.get_balance()
    
    def get_order_profit(self, order_id: str) -> Optional[Decimal]:
        """获取订单利润
        
        Args:
            order_id: 订单ID
            
        Returns:
            订单利润,如果订单不存在返回None
        """
        order = self.orders.get(order_id)
        if not order:
            return None
        
        return order.get_profit()
    
    def get_all_orders(self) -> List[ProcessingOrder]:
        """获取所有订单
        
        Returns:
            所有订单列表
        """
        orders = list(self.orders.values())
        orders.sort(key=lambda x: x.order_date, reverse=True)
        return orders
    
    def get_orders_by_date_range(
        self,
        start_date: date,
        end_date: date
    ) -> List[ProcessingOrder]:
        """获取日期范围内的订单
        
        Args:
            start_date: 开始日期
            end_date: 结束日期
            
        Returns:
            日期范围内的订单列表
        """
        return self.query_orders(start_date=start_date, end_date=end_date)
    
    def get_statistics(
        self,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None
    ) -> Dict:
        """获取订单统计信息
        
        Args:
            start_date: 开始日期(可选)
            end_date: 结束日期(可选)
            
        Returns:
            统计信息字典
        """
        orders = self.query_orders(start_date=start_date, end_date=end_date)
        
        total_orders = len(orders)
        total_amount = sum(order.total_amount for order in orders)
        total_received = sum(order.received_amount for order in orders)
        total_outsourced_cost = sum(order.outsourced_cost for order in orders)
        total_balance = sum(order.get_balance() for order in orders)
        total_profit = sum(order.get_profit() for order in orders)
        
        # 按状态统计
        status_stats = {}
        for status in OrderStatus:
            count = sum(1 for order in orders if order.status == status)
            status_stats[status.value] = count
        
        # 按计价单位统计
        unit_stats = {}
        for unit in PricingUnit:
            unit_orders = [o for o in orders if o.pricing_unit == unit]
            unit_stats[unit.value] = {
                "count": len(unit_orders),
                "total_amount": sum(o.total_amount for o in unit_orders)
            }
        
        return {
            "total_orders": total_orders,
            "total_amount": str(total_amount),
            "total_received": str(total_received),
            "total_outsourced_cost": str(total_outsourced_cost),
            "total_balance": str(total_balance),
            "total_profit": str(total_profit),
            "status_statistics": status_stats,
            "pricing_unit_statistics": unit_stats
        }
