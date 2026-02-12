#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
委外加工管理器 - 负责委外加工记录的创建、更新和查询
"""

from datetime import date, datetime
from decimal import Decimal
from typing import List, Optional, Dict
import uuid

from ..models.business_models import (
    OutsourcedProcessing, Supplier, ProcessType, ExpenseType
)
from ..database.db_manager import DatabaseManager


class OutsourcedProcessingManager:
    """委外加工管理器 - 支持委外加工信息记录、费用关联和供应商管理"""
    
    def __init__(self, db_manager: DatabaseManager):
        """初始化委外加工管理器
        
        Args:
            db_manager: 数据库管理器实例
        """
        self.db = db_manager
    
    def create_processing(
        self,
        order_id: str,
        supplier_id: str,
        supplier_name: str,
        process_type: ProcessType,
        quantity: Decimal,
        unit_price: Decimal,
        process_date: Optional[date] = None,
        process_description: str = "",
        notes: str = ""
    ) -> OutsourcedProcessing:
        """创建委外加工记录
        
        Args:
            order_id: 关联的订单ID
            supplier_id: 供应商ID
            supplier_name: 供应商名称
            process_type: 工序类型
            quantity: 数量
            unit_price: 单价
            process_date: 加工日期（默认今天）
            process_description: 工序描述
            notes: 备注
            
        Returns:
            创建的委外加工记录
        """
        # 计算总成本
        total_cost = quantity * unit_price
        
        # 创建委外加工记录
        processing = OutsourcedProcessing(
            id=str(uuid.uuid4()),
            order_id=order_id,
            supplier_id=supplier_id,
            supplier_name=supplier_name,
            process_type=process_type,
            process_description=process_description,
            quantity=quantity,
            unit_price=unit_price,
            total_cost=total_cost,
            paid_amount=Decimal("0"),
            process_date=process_date or date.today(),
            notes=notes,
            created_at=datetime.now(),
            updated_at=datetime.now()
        )
        
        # 保存到数据库
        self.db.save_outsourced_processing(processing)
        
        return processing
    
    def get_processing(self, processing_id: str) -> Optional[OutsourcedProcessing]:
        """获取委外加工记录
        
        Args:
            processing_id: 委外加工记录ID
            
        Returns:
            委外加工记录，如果不存在返回None
        """
        return self.db.get_outsourced_processing(processing_id)
    
    def update_processing(self, processing: OutsourcedProcessing) -> OutsourcedProcessing:
        """更新委外加工记录
        
        Args:
            processing: 委外加工记录对象
            
        Returns:
            更新后的委外加工记录
        """
        processing.updated_at = datetime.now()
        # 重新计算总成本
        processing.total_cost = processing.quantity * processing.unit_price
        self.db.save_outsourced_processing(processing)
        return processing
    
    def list_processing_by_order(self, order_id: str) -> List[OutsourcedProcessing]:
        """获取订单的所有委外加工记录
        
        Args:
            order_id: 订单ID
            
        Returns:
            委外加工记录列表
        """
        return self.db.list_outsourced_processing(order_id=order_id)
    
    def list_processing_by_supplier(self, supplier_id: str) -> List[OutsourcedProcessing]:
        """获取供应商的所有委外加工记录
        
        Args:
            supplier_id: 供应商ID
            
        Returns:
            委外加工记录列表
        """
        return self.db.list_outsourced_processing(supplier_id=supplier_id)
    
    def list_all_processing(self) -> List[OutsourcedProcessing]:
        """获取所有委外加工记录
        
        Returns:
            委外加工记录列表
        """
        return self.db.list_outsourced_processing()
    
    def get_order_total_cost(self, order_id: str) -> Decimal:
        """获取订单的委外加工总成本
        
        Args:
            order_id: 订单ID
            
        Returns:
            委外加工总成本
        """
        processing_list = self.list_processing_by_order(order_id)
        return sum(p.total_cost for p in processing_list)
    
    def get_order_total_paid(self, order_id: str) -> Decimal:
        """获取订单的委外加工已付总额
        
        Args:
            order_id: 订单ID
            
        Returns:
            委外加工已付总额
        """
        processing_list = self.list_processing_by_order(order_id)
        return sum(p.paid_amount for p in processing_list)
    
    def get_order_unpaid_amount(self, order_id: str) -> Decimal:
        """获取订单的委外加工未付金额
        
        Args:
            order_id: 订单ID
            
        Returns:
            委外加工未付金额
        """
        total_cost = self.get_order_total_cost(order_id)
        total_paid = self.get_order_total_paid(order_id)
        return total_cost - total_paid
    
    def record_payment(
        self,
        processing_id: str,
        payment_amount: Decimal
    ) -> Optional[OutsourcedProcessing]:
        """记录委外加工付款
        
        Args:
            processing_id: 委外加工记录ID
            payment_amount: 付款金额
            
        Returns:
            更新后的委外加工记录，如果记录不存在返回None
        """
        processing = self.get_processing(processing_id)
        if not processing:
            return None
        
        # 更新已付金额
        processing.paid_amount += payment_amount
        
        # 确保已付金额不超过总成本
        if processing.paid_amount > processing.total_cost:
            processing.paid_amount = processing.total_cost
        
        return self.update_processing(processing)
    
    def allocate_payment_to_multiple(
        self,
        allocations: Dict[str, Decimal]
    ) -> Dict[str, bool]:
        """将付款分配到多个委外加工记录
        
        Args:
            allocations: 分配字典 {processing_id: payment_amount}
            
        Returns:
            分配结果字典 {processing_id: success}
        """
        results = {}
        
        for processing_id, amount in allocations.items():
            processing = self.record_payment(processing_id, amount)
            results[processing_id] = processing is not None
        
        return results
    
    def get_supplier_unpaid_processing(
        self,
        supplier_id: str
    ) -> List[OutsourcedProcessing]:
        """获取供应商的未付清委外加工记录
        
        Args:
            supplier_id: 供应商ID
            
        Returns:
            未付清的委外加工记录列表
        """
        all_processing = self.list_processing_by_supplier(supplier_id)
        return [p for p in all_processing if not p.is_fully_paid()]
    
    def get_supplier_total_unpaid(self, supplier_id: str) -> Decimal:
        """获取供应商的未付总额
        
        Args:
            supplier_id: 供应商ID
            
        Returns:
            未付总额
        """
        unpaid_processing = self.get_supplier_unpaid_processing(supplier_id)
        return sum(p.get_unpaid_amount() for p in unpaid_processing)
    
    def get_processing_by_type(
        self,
        process_type: ProcessType
    ) -> List[OutsourcedProcessing]:
        """根据工序类型获取委外加工记录
        
        Args:
            process_type: 工序类型
            
        Returns:
            委外加工记录列表
        """
        all_processing = self.list_all_processing()
        return [p for p in all_processing if p.process_type == process_type]
    
    def get_statistics_by_supplier(self) -> Dict[str, Dict]:
        """按供应商统计委外加工情况
        
        Returns:
            统计信息字典 {supplier_id: {统计数据}}
        """
        all_processing = self.list_all_processing()
        
        stats = {}
        for processing in all_processing:
            supplier_id = processing.supplier_id
            
            if supplier_id not in stats:
                stats[supplier_id] = {
                    "supplier_name": processing.supplier_name,
                    "total_count": 0,
                    "total_cost": Decimal("0"),
                    "total_paid": Decimal("0"),
                    "total_unpaid": Decimal("0"),
                    "by_process_type": {}
                }
            
            stats[supplier_id]["total_count"] += 1
            stats[supplier_id]["total_cost"] += processing.total_cost
            stats[supplier_id]["total_paid"] += processing.paid_amount
            stats[supplier_id]["total_unpaid"] += processing.get_unpaid_amount()
            
            # 按工序类型统计
            process_type_name = processing.process_type.value
            if process_type_name not in stats[supplier_id]["by_process_type"]:
                stats[supplier_id]["by_process_type"][process_type_name] = {
                    "count": 0,
                    "total_cost": Decimal("0")
                }
            
            stats[supplier_id]["by_process_type"][process_type_name]["count"] += 1
            stats[supplier_id]["by_process_type"][process_type_name]["total_cost"] += processing.total_cost
        
        return stats
    
    def get_statistics_by_process_type(self) -> Dict[str, Dict]:
        """按工序类型统计委外加工情况
        
        Returns:
            统计信息字典 {process_type: {统计数据}}
        """
        all_processing = self.list_all_processing()
        
        stats = {}
        for process_type in ProcessType:
            type_name = process_type.value
            type_processing = [p for p in all_processing if p.process_type == process_type]
            
            if type_processing:
                total_cost = sum(p.total_cost for p in type_processing)
                total_quantity = sum(p.quantity for p in type_processing)
                
                stats[type_name] = {
                    "count": len(type_processing),
                    "total_cost": total_cost,
                    "total_quantity": total_quantity,
                    "avg_unit_price": total_cost / total_quantity if total_quantity > 0 else Decimal("0")
                }
        
        return stats
    
    def delete_processing(self, processing_id: str) -> bool:
        """删除委外加工记录
        
        Args:
            processing_id: 委外加工记录ID
            
        Returns:
            是否删除成功
        """
        processing = self.get_processing(processing_id)
        if not processing:
            return False
        
        # 检查是否可以删除（已付款的记录不能删除）
        if processing.paid_amount > 0:
            raise ValueError("已付款的委外加工记录不能删除")
        
        # 从数据库删除
        cursor = self.db.conn.cursor()
        cursor.execute("DELETE FROM outsourced_processing WHERE id = ?", (processing_id,))
        self.db.conn.commit()
        
        return True
