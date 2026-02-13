"""
Outsourced Processing Manager for Oxidation Factory

This module manages outsourced processing records (喷砂、拉丝、抛光).
Provides CRUD operations and cost statistics for outsourced processing.
"""

from datetime import date, datetime
from decimal import Decimal
from typing import List, Optional, Dict
import uuid
import json
import os

from ..models.core_models import (
    OutsourcedProcessing,
    ProcessType
)


class OutsourcedProcessingManager:
    """外发加工管理器
    
    功能:
    - 创建外发加工记录
    - 关联外发加工与订单
    - 统计外发加工成本
    - 按工序类型和供应商统计
    """
    
    def __init__(self, data_dir: str = "财务数据"):
        """初始化外发加工管理器
        
        Args:
            data_dir: 数据存储目录
        """
        self.data_dir = data_dir
        self.processing_file = os.path.join(data_dir, "outsourced_processing.json")
        self._ensure_data_dir()
        self.processing_records: Dict[str, OutsourcedProcessing] = {}
        self._load_processing_records()
    
    def _ensure_data_dir(self):
        """确保数据目录存在"""
        if not os.path.exists(self.data_dir):
            os.makedirs(self.data_dir)
    
    def _load_processing_records(self):
        """从文件加载外发加工记录"""
        if os.path.exists(self.processing_file):
            try:
                with open(self.processing_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    for record_data in data:
                        record = OutsourcedProcessing.from_dict(record_data)
                        self.processing_records[record.id] = record
            except Exception as e:
                print(f"加载外发加工记录失败: {e}")
                self.processing_records = {}
    
    def _save_processing_records(self):
        """保存外发加工记录到文件"""
        try:
            data = [record.to_dict() for record in self.processing_records.values()]
            with open(self.processing_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"保存外发加工记录失败: {e}")
            raise
    
    def create_processing(
        self,
        order_id: str,
        supplier_id: str,
        process_type: ProcessType,
        process_date: date,
        quantity: Decimal,
        unit_price: Decimal,
        notes: str = ""
    ) -> OutsourcedProcessing:
        """创建外发加工记录
        
        Args:
            order_id: 关联的加工订单ID
            supplier_id: 供应商ID
            process_type: 工序类型
            process_date: 加工日期
            quantity: 数量
            unit_price: 单价
            notes: 备注
            
        Returns:
            创建的外发加工记录
        """
        # 自动计算总成本
        total_cost = quantity * unit_price
        
        # 创建记录
        processing = OutsourcedProcessing(
            id=str(uuid.uuid4()),
            order_id=order_id,
            supplier_id=supplier_id,
            process_type=process_type,
            process_date=process_date,
            quantity=quantity,
            unit_price=unit_price,
            total_cost=total_cost,
            notes=notes,
            created_at=datetime.now(),
            updated_at=datetime.now()
        )
        
        # 保存记录
        self.processing_records[processing.id] = processing
        self._save_processing_records()
        
        return processing
    
    def get_processing(self, processing_id: str) -> Optional[OutsourcedProcessing]:
        """获取外发加工记录
        
        Args:
            processing_id: 记录ID
            
        Returns:
            外发加工记录,如果不存在返回None
        """
        return self.processing_records.get(processing_id)
    
    def get_processing_by_order(self, order_id: str) -> List[OutsourcedProcessing]:
        """获取订单的所有外发加工记录
        
        Args:
            order_id: 订单ID
            
        Returns:
            外发加工记录列表
        """
        results = []
        for processing in self.processing_records.values():
            if processing.order_id == order_id:
                results.append(processing)
        
        # 按加工日期排序
        results.sort(key=lambda x: x.process_date)
        
        return results
    
    def query_processing(
        self,
        order_id: Optional[str] = None,
        supplier_id: Optional[str] = None,
        process_type: Optional[ProcessType] = None,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None
    ) -> List[OutsourcedProcessing]:
        """查询外发加工记录
        
        Args:
            order_id: 订单ID(可选)
            supplier_id: 供应商ID(可选)
            process_type: 工序类型(可选)
            start_date: 开始日期(可选)
            end_date: 结束日期(可选)
            
        Returns:
            符合条件的外发加工记录列表
        """
        results = []
        
        for processing in self.processing_records.values():
            # 按订单筛选
            if order_id and processing.order_id != order_id:
                continue
            
            # 按供应商筛选
            if supplier_id and processing.supplier_id != supplier_id:
                continue
            
            # 按工序类型筛选
            if process_type and processing.process_type != process_type:
                continue
            
            # 按日期范围筛选
            if start_date and processing.process_date < start_date:
                continue
            if end_date and processing.process_date > end_date:
                continue
            
            results.append(processing)
        
        # 按加工日期降序排序
        results.sort(key=lambda x: x.process_date, reverse=True)
        
        return results
    
    def get_order_total_cost(self, order_id: str) -> Decimal:
        """获取订单的外发加工总成本
        
        Args:
            order_id: 订单ID
            
        Returns:
            外发加工总成本
        """
        processing_list = self.get_processing_by_order(order_id)
        return sum(p.total_cost for p in processing_list)
    
    def get_all_processing(self) -> List[OutsourcedProcessing]:
        """获取所有外发加工记录
        
        Returns:
            所有外发加工记录列表
        """
        records = list(self.processing_records.values())
        records.sort(key=lambda x: x.process_date, reverse=True)
        return records
    
    def get_statistics_by_process_type(
        self,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None
    ) -> Dict:
        """按工序类型统计外发加工成本
        
        Args:
            start_date: 开始日期(可选)
            end_date: 结束日期(可选)
            
        Returns:
            按工序类型的统计信息
        """
        records = self.query_processing(start_date=start_date, end_date=end_date)
        
        stats = {}
        for process_type in ProcessType:
            type_records = [r for r in records if r.process_type == process_type]
            total_cost = sum(r.total_cost for r in type_records)
            total_quantity = sum(r.quantity for r in type_records)
            
            stats[process_type.value] = {
                "count": len(type_records),
                "total_cost": str(total_cost),
                "total_quantity": str(total_quantity),
                "avg_unit_price": str(total_cost / total_quantity) if total_quantity > 0 else "0"
            }
        
        return stats
    
    def get_statistics_by_supplier(
        self,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None
    ) -> Dict:
        """按供应商统计外发加工成本
        
        Args:
            start_date: 开始日期(可选)
            end_date: 结束日期(可选)
            
        Returns:
            按供应商的统计信息
        """
        records = self.query_processing(start_date=start_date, end_date=end_date)
        
        # 按供应商分组
        supplier_records = {}
        for record in records:
            if record.supplier_id not in supplier_records:
                supplier_records[record.supplier_id] = []
            supplier_records[record.supplier_id].append(record)
        
        # 统计每个供应商
        stats = {}
        for supplier_id, supplier_records_list in supplier_records.items():
            total_cost = sum(r.total_cost for r in supplier_records_list)
            
            # 按工序类型细分
            process_type_breakdown = {}
            for process_type in ProcessType:
                type_records = [r for r in supplier_records_list if r.process_type == process_type]
                if type_records:
                    process_type_breakdown[process_type.value] = {
                        "count": len(type_records),
                        "total_cost": str(sum(r.total_cost for r in type_records))
                    }
            
            stats[supplier_id] = {
                "total_records": len(supplier_records_list),
                "total_cost": str(total_cost),
                "process_type_breakdown": process_type_breakdown
            }
        
        return stats
    
    def get_overall_statistics(
        self,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None
    ) -> Dict:
        """获取外发加工总体统计
        
        Args:
            start_date: 开始日期(可选)
            end_date: 结束日期(可选)
            
        Returns:
            总体统计信息
        """
        records = self.query_processing(start_date=start_date, end_date=end_date)
        
        total_records = len(records)
        total_cost = sum(r.total_cost for r in records)
        total_quantity = sum(r.quantity for r in records)
        
        # 按工序类型统计
        by_process_type = self.get_statistics_by_process_type(start_date, end_date)
        
        # 按供应商统计
        by_supplier = self.get_statistics_by_supplier(start_date, end_date)
        
        return {
            "total_records": total_records,
            "total_cost": str(total_cost),
            "total_quantity": str(total_quantity),
            "avg_unit_price": str(total_cost / total_quantity) if total_quantity > 0 else "0",
            "by_process_type": by_process_type,
            "by_supplier": by_supplier
        }
