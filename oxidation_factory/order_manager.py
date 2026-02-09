# -*- coding: utf-8 -*-
"""
订单管理模块
负责加工订单的创建、查询、更新和统计
"""

from datetime import datetime
from typing import List, Dict, Optional, Any
import lark_oapi as lark
from lark_oapi.api.bitable.v1 import *
from .config import get_config

class Order:
    """订单数据模型"""
    
    def __init__(self, **kwargs):
        self.order_no = kwargs.get('order_no', '')  # 订单编号
        self.customer = kwargs.get('customer', '')  # 客户名称
        self.order_date = kwargs.get('order_date', datetime.now())  # 订单日期
        self.item_name = kwargs.get('item_name', '')  # 物品名称
        self.pricing_unit = kwargs.get('pricing_unit', '件')  # 计价单位
        self.quantity = kwargs.get('quantity', 0)  # 数量
        self.unit_price = kwargs.get('unit_price', 0.0)  # 单价
        self.order_amount = kwargs.get('order_amount', 0.0)  # 订单金额
        self.paid_amount = kwargs.get('paid_amount', 0.0)  # 已收款金额
        self.unpaid_amount = kwargs.get('unpaid_amount', 0.0)  # 未收款金额
        self.process_details = kwargs.get('process_details', '')  # 工序明细
        self.outsourced_processes = kwargs.get('outsourced_processes', [])  # 外发工序
        self.outsourced_cost = kwargs.get('outsourced_cost', 0.0)  # 外发成本
        self.status = kwargs.get('status', '待生产')  # 订单状态
        self.remark = kwargs.get('remark', '')  # 备注
        self.record_id = kwargs.get('record_id', None)  # 飞书记录ID
    
    def calculate_amount(self):
        """计算订单金额"""
        self.order_amount = self.quantity * self.unit_price
        return self.order_amount
    
    def calculate_unpaid(self):
        """计算未收款金额"""
        self.unpaid_amount = self.order_amount - self.paid_amount
        return self.unpaid_amount
    
    def to_feishu_fields(self) -> Dict[str, Any]:
        """转换为飞书字段格式"""
        # 转换日期为时间戳（毫秒）
        if isinstance(self.order_date, datetime):
            date_ts = int(self.order_date.timestamp() * 1000)
        else:
            date_ts = int(datetime.now().timestamp() * 1000)
        
        return {
            "订单编号": self.order_no,
            "客户名称": self.customer,
            "订单日期": date_ts,
            "物品名称": self.item_name,
            "计价单位": self.pricing_unit,
            "数量": float(self.quantity),
            "单价": float(self.unit_price),
            "已收款金额": float(self.paid_amount),
            "工序明细": self.process_details,
            "外发成本": float(self.outsourced_cost),
            "订单状态": self.status,
            "备注": self.remark
        }
    
    @staticmethod
    def from_feishu_record(record) -> 'Order':
        """从飞书记录创建订单对象"""
        fields = record.fields
        
        # 转换时间戳为datetime
        date_ts = fields.get("订单日期", 0)
        if date_ts:
            order_date = datetime.fromtimestamp(date_ts / 1000)
        else:
            order_date = datetime.now()
        
        return Order(
            record_id=record.record_id,
            order_no=fields.get("订单编号", ""),
            customer=fields.get("客户名称", ""),
            order_date=order_date,
            item_name=fields.get("物品名称", ""),
            pricing_unit=fields.get("计价单位", "件"),
            quantity=fields.get("数量", 0),
            unit_price=fields.get("单价", 0.0),
            order_amount=fields.get("订单金额", 0.0),
            paid_amount=fields.get("已收款金额", 0.0),
            unpaid_amount=fields.get("未收款金额", 0.0),
            process_details=fields.get("工序明细", ""),
            outsourced_cost=fields.get("外发成本", 0.0),
            status=fields.get("订单状态", "待生产"),
            remark=fields.get("备注", "")
        )


class OrderManager:
    """订单管理器"""
    
    def __init__(self, client, app_token, table_id):
        """
        初始化订单管理器
        
        Args:
            client: 飞书客户端
            app_token: 多维表格的app_token
            table_id: 加工订单表的table_id
        """
        self.client = client
        self.app_token = app_token
        self.table_id = table_id
        self.config = get_config()
    
    def create_order(self, order: Order) -> bool:
        """
        创建订单
        
        Args:
            order: 订单对象
        
        Returns:
            bool: 是否创建成功
        """
        try:
            # 验证订单数据
            if not self.validate_order(order):
                return False
            
            # 计算金额
            order.calculate_amount()
            order.calculate_unpaid()
            
            # 转换为飞书字段
            fields = order.to_feishu_fields()
            
            # 创建记录
            req = CreateAppTableRecordRequest.builder() \
                .app_token(self.app_token) \
                .table_id(self.table_id) \
                .request_body(AppTableRecord.builder()
                    .fields(fields)
                    .build()) \
                .build()
            
            resp = self.client.bitable.v1.app_table_record.create(req)
            
            if resp.success():
                order.record_id = resp.data.record.record_id
                print(f"✅ 订单创建成功：{order.order_no}")
                return True
            else:
                print(f"❌ 订单创建失败：{resp.msg}")
                return False
                
        except Exception as e:
            print(f"❌ 订单创建异常：{str(e)}")
            return False
    
    def validate_order(self, order: Order) -> bool:
        """
        验证订单数据
        
        Args:
            order: 订单对象
        
        Returns:
            bool: 数据是否有效
        """
        # 必填字段检查
        if not order.order_no:
            print("❌ 订单编号不能为空")
            return False
        
        if not order.customer:
            print("❌ 客户名称不能为空")
            return False
        
        if not order.item_name:
            print("❌ 物品名称不能为空")
            return False
        
        # 数量和单价检查
        if order.quantity <= 0:
            print("❌ 数量必须大于0")
            return False
        
        if order.unit_price <= 0:
            print("❌ 单价必须大于0")
            return False
        
        # 计价单位检查
        valid_units = self.config.get_pricing_units()
        if order.pricing_unit not in valid_units:
            print(f"❌ 计价单位无效，必须是以下之一：{', '.join(valid_units)}")
            return False
        
        return True
    
    def query_orders(self, 
                     customer: str = None,
                     status: str = None,
                     date_from: datetime = None,
                     date_to: datetime = None) -> List[Order]:
        """
        查询订单
        
        Args:
            customer: 客户名称（可选）
            status: 订单状态（可选）
            date_from: 开始日期（可选）
            date_to: 结束日期（可选）
        
        Returns:
            List[Order]: 订单列表
        """
        try:
            # 构建过滤条件
            filter_conditions = []
            
            if customer:
                filter_conditions.append(f'CurrentValue.[客户名称]="{customer}"')
            
            if status:
                filter_conditions.append(f'CurrentValue.[订单状态]="{status}"')
            
            if date_from:
                ts_from = int(date_from.timestamp() * 1000)
                filter_conditions.append(f'CurrentValue.[订单日期]>={ts_from}')
            
            if date_to:
                ts_to = int(date_to.timestamp() * 1000)
                filter_conditions.append(f'CurrentValue.[订单日期]<={ts_to}')
            
            # 组合过滤条件
            filter_str = "&&".join(filter_conditions) if filter_conditions else None
            
            # 查询记录
            orders = []
            page_token = None
            
            while True:
                builder = ListAppTableRecordRequest.builder() \
                    .app_token(self.app_token) \
                    .table_id(self.table_id) \
                    .page_size(100)
                
                if filter_str:
                    builder.filter(filter_str)
                
                if page_token:
                    builder.page_token(page_token)
                
                req = builder.build()
                resp = self.client.bitable.v1.app_table_record.list(req)
                
                if not resp.success():
                    print(f"❌ 查询失败：{resp.msg}")
                    break
                
                if resp.data.items:
                    for record in resp.data.items:
                        order = Order.from_feishu_record(record)
                        orders.append(order)
                
                if not resp.data.has_more:
                    break
                
                page_token = resp.data.page_token
            
            return orders
            
        except Exception as e:
            print(f"❌ 查询异常：{str(e)}")
            return []
    
    def update_order_status(self, order_no: str, new_status: str) -> bool:
        """
        更新订单状态
        
        Args:
            order_no: 订单编号
            new_status: 新状态
        
        Returns:
            bool: 是否更新成功
        """
        try:
            # 查找订单
            orders = self.query_orders()
            target_order = None
            
            for order in orders:
                if order.order_no == order_no:
                    target_order = order
                    break
            
            if not target_order:
                print(f"❌ 未找到订单：{order_no}")
                return False
            
            # 更新状态
            req = UpdateAppTableRecordRequest.builder() \
                .app_token(self.app_token) \
                .table_id(self.table_id) \
                .record_id(target_order.record_id) \
                .request_body(AppTableRecord.builder()
                    .fields({"订单状态": new_status})
                    .build()) \
                .build()
            
            resp = self.client.bitable.v1.app_table_record.update(req)
            
            if resp.success():
                print(f"✅ 订单状态更新成功：{order_no} -> {new_status}")
                return True
            else:
                print(f"❌ 更新失败：{resp.msg}")
                return False
                
        except Exception as e:
            print(f"❌ 更新异常：{str(e)}")
            return False
    
    def update_paid_amount(self, order_no: str, paid_amount: float) -> bool:
        """
        更新已收款金额
        
        Args:
            order_no: 订单编号
            paid_amount: 已收款金额
        
        Returns:
            bool: 是否更新成功
        """
        try:
            # 查找订单
            orders = self.query_orders()
            target_order = None
            
            for order in orders:
                if order.order_no == order_no:
                    target_order = order
                    break
            
            if not target_order:
                print(f"❌ 未找到订单：{order_no}")
                return False
            
            # 更新已收款金额
            req = UpdateAppTableRecordRequest.builder() \
                .app_token(self.app_token) \
                .table_id(self.table_id) \
                .record_id(target_order.record_id) \
                .request_body(AppTableRecord.builder()
                    .fields({"已收款金额": float(paid_amount)})
                    .build()) \
                .build()
            
            resp = self.client.bitable.v1.app_table_record.update(req)
            
            if resp.success():
                print(f"✅ 已收款金额更新成功：{order_no} -> {paid_amount}元")
                
                # 如果全额收款，更新状态为已结算
                if paid_amount >= target_order.order_amount:
                    self.update_order_status(order_no, "已结算")
                
                return True
            else:
                print(f"❌ 更新失败：{resp.msg}")
                return False
                
        except Exception as e:
            print(f"❌ 更新异常：{str(e)}")
            return False
    
    def get_statistics(self, customer: str = None) -> Dict[str, Any]:
        """
        获取订单统计信息
        
        Args:
            customer: 客户名称（可选，为空则统计所有）
        
        Returns:
            Dict: 统计信息
        """
        orders = self.query_orders(customer=customer)
        
        if not orders:
            return {
                "total_orders": 0,
                "total_amount": 0.0,
                "total_paid": 0.0,
                "total_unpaid": 0.0,
                "by_status": {},
                "by_unit": {}
            }
        
        # 统计
        total_amount = sum(o.order_amount for o in orders)
        total_paid = sum(o.paid_amount for o in orders)
        total_unpaid = sum(o.unpaid_amount for o in orders)
        
        # 按状态统计
        by_status = {}
        for order in orders:
            status = order.status
            if status not in by_status:
                by_status[status] = {"count": 0, "amount": 0.0}
            by_status[status]["count"] += 1
            by_status[status]["amount"] += order.order_amount
        
        # 按计价单位统计
        by_unit = {}
        for order in orders:
            unit = order.pricing_unit
            if unit not in by_unit:
                by_unit[unit] = {"count": 0, "quantity": 0, "amount": 0.0}
            by_unit[unit]["count"] += 1
            by_unit[unit]["quantity"] += order.quantity
            by_unit[unit]["amount"] += order.order_amount
        
        return {
            "total_orders": len(orders),
            "total_amount": total_amount,
            "total_paid": total_paid,
            "total_unpaid": total_unpaid,
            "by_status": by_status,
            "by_unit": by_unit
        }
