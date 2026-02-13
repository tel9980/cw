"""
Outsourced Processing Manager for Oxidation Factory Workflow Optimization

This module manages outsourced processing records (喷砂、拉丝、抛光).
Provides CRUD operations, cost statistics, and payment tracking for outsourced processing.

Reused and adapted from oxidation_complete_v17/industry/outsourced_processing_manager.py

Requirements: 5.1, 5.2, 5.3, 5.5, 5.6, 2.3, 2.4
"""

from datetime import date, datetime
from decimal import Decimal
from typing import List, Optional, Dict, Tuple
import uuid
import json
import os

from ..models.core_models import (
    OutsourcedProcessing,
    ProcessType,
    TransactionRecord,
    TransactionType,
    TransactionStatus
)


class SupplierPaymentAllocation:
    """供应商付款分配记录
    
    记录一笔付款如何分配到多个委外加工记录
    
    Requirements: 2.3, 2.4
    """
    
    def __init__(
        self,
        payment_id: str,
        processing_id: str,
        allocated_amount: Decimal,
        allocation_date: datetime
    ):
        self.payment_id = payment_id
        self.processing_id = processing_id
        self.allocated_amount = allocated_amount
        self.allocation_date = allocation_date
    
    def to_dict(self) -> dict:
        """转换为字典"""
        return {
            "payment_id": self.payment_id,
            "processing_id": self.processing_id,
            "allocated_amount": str(self.allocated_amount),
            "allocation_date": self.allocation_date.isoformat()
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> "SupplierPaymentAllocation":
        """从字典创建"""
        return cls(
            payment_id=data["payment_id"],
            processing_id=data["processing_id"],
            allocated_amount=Decimal(data["allocated_amount"]),
            allocation_date=datetime.fromisoformat(data["allocation_date"])
        )


class OutsourcedProcessingManager:
    """外发加工管理器
    
    功能:
    - 创建外发加工记录
    - 关联外发加工与订单
    - 统计外发加工成本
    - 按工序类型和供应商统计
    - 跟踪供应商付款状态
    - 支持一次付款关联多个委外加工
    
    Requirements: 5.1, 5.2, 5.3, 5.5, 5.6, 2.3, 2.4
    """
    
    def __init__(self, data_dir: str = "data"):
        """初始化外发加工管理器
        
        Args:
            data_dir: 数据存储目录
        """
        self.data_dir = data_dir
        self.processing_file = os.path.join(data_dir, "outsourced_processing.json")
        self.supplier_payments_file = os.path.join(data_dir, "supplier_payments.json")
        self.supplier_allocations_file = os.path.join(data_dir, "supplier_payment_allocations.json")
        self._ensure_data_dir()
        
        # 存储数据
        self.processing_records: Dict[str, OutsourcedProcessing] = {}
        self.supplier_payments: Dict[str, TransactionRecord] = {}
        self.supplier_allocations: List[SupplierPaymentAllocation] = []
        
        self._load_data()
    
    def _ensure_data_dir(self):
        """确保数据目录存在"""
        if not os.path.exists(self.data_dir):
            os.makedirs(self.data_dir)
    
    def _load_data(self):
        """从文件加载所有数据"""
        # 加载外发加工记录
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
        
        # 加载供应商付款记录
        if os.path.exists(self.supplier_payments_file):
            try:
                with open(self.supplier_payments_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    for payment_data in data:
                        payment = TransactionRecord.from_dict(payment_data)
                        self.supplier_payments[payment.id] = payment
            except Exception as e:
                print(f"加载供应商付款记录失败: {e}")
                self.supplier_payments = {}
        
        # 加载付款分配关系
        if os.path.exists(self.supplier_allocations_file):
            try:
                with open(self.supplier_allocations_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self.supplier_allocations = [
                        SupplierPaymentAllocation.from_dict(alloc_data)
                        for alloc_data in data
                    ]
            except Exception as e:
                print(f"加载付款分配记录失败: {e}")
                self.supplier_allocations = []
    
    def _save_data(self):
        """保存所有数据到文件"""
        try:
            # 保存外发加工记录
            processing_data = [record.to_dict() for record in self.processing_records.values()]
            with open(self.processing_file, 'w', encoding='utf-8') as f:
                json.dump(processing_data, f, ensure_ascii=False, indent=2)
            
            # 保存供应商付款记录
            payment_data = [payment.to_dict() for payment in self.supplier_payments.values()]
            with open(self.supplier_payments_file, 'w', encoding='utf-8') as f:
                json.dump(payment_data, f, ensure_ascii=False, indent=2)
            
            # 保存付款分配关系
            allocation_data = [alloc.to_dict() for alloc in self.supplier_allocations]
            with open(self.supplier_allocations_file, 'w', encoding='utf-8') as f:
                json.dump(allocation_data, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"保存数据失败: {e}")
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
        
        支持三种工序类型：喷砂、拉丝、抛光
        
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
            
        Requirements: 5.1, 5.2, 5.3
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
            paid_amount=Decimal("0"),  # 初始未付款
            notes=notes,
            created_at=datetime.now(),
            updated_at=datetime.now()
        )
        
        # 保存记录
        self.processing_records[processing.id] = processing
        self._save_data()
        
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
            
        Requirements: 5.5
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
    
    def update_processing(
        self,
        processing_id: str,
        quantity: Optional[Decimal] = None,
        unit_price: Optional[Decimal] = None,
        notes: Optional[str] = None
    ) -> bool:
        """更新外发加工记录
        
        Args:
            processing_id: 记录ID
            quantity: 新数量(可选)
            unit_price: 新单价(可选)
            notes: 新备注(可选)
            
        Returns:
            是否更新成功
        """
        processing = self.processing_records.get(processing_id)
        if not processing:
            return False
        
        # 更新字段
        if quantity is not None:
            processing.quantity = quantity
        if unit_price is not None:
            processing.unit_price = unit_price
        if notes is not None:
            processing.notes = notes
        
        # 重新计算总成本
        processing.total_cost = processing.quantity * processing.unit_price
        processing.updated_at = datetime.now()
        
        self._save_data()
        return True
    
    def record_supplier_payment(
        self,
        payment_date: date,
        amount: Decimal,
        supplier_id: str,
        bank_account_id: str,
        description: str = "",
        processing_allocations: Optional[Dict[str, Decimal]] = None
    ) -> Tuple[TransactionRecord, bool]:
        """记录供应商付款
        
        支持一次付款关联多个委外加工记录
        
        Args:
            payment_date: 付款日期
            amount: 付款金额
            supplier_id: 供应商ID
            bank_account_id: 银行账户ID
            description: 付款描述
            processing_allocations: 委外加工分配字典 {processing_id: allocated_amount}
                                   如果为None，则创建未分配的付款
        
        Returns:
            Tuple[TransactionRecord, bool]: (付款记录, 是否成功)
        
        Requirements: 2.3, 2.4, 5.6
        """
        # 验证分配金额
        if processing_allocations:
            total_allocated = sum(processing_allocations.values())
            if total_allocated > amount:
                raise ValueError(f"分配金额总和 ({total_allocated}) 超过付款金额 ({amount})")
        
        # 创建付款记录
        payment = TransactionRecord(
            id=str(uuid.uuid4()),
            date=payment_date,
            type=TransactionType.EXPENSE,
            amount=amount,
            counterparty_id=supplier_id,
            description=description or f"供应商付款 - {supplier_id}",
            category="外发加工费用",
            status=TransactionStatus.COMPLETED,
            bank_account_id=bank_account_id,
            created_at=datetime.now(),
            updated_at=datetime.now()
        )
        
        # 保存付款记录
        self.supplier_payments[payment.id] = payment
        
        # 如果指定了委外加工分配，创建分配关系并更新付款金额
        if processing_allocations:
            for processing_id, allocated_amount in processing_allocations.items():
                if allocated_amount <= 0:
                    continue
                
                # 验证委外加工记录存在
                processing = self.processing_records.get(processing_id)
                if not processing:
                    raise ValueError(f"委外加工记录不存在: {processing_id}")
                
                # 创建分配记录
                allocation = SupplierPaymentAllocation(
                    payment_id=payment.id,
                    processing_id=processing_id,
                    allocated_amount=allocated_amount,
                    allocation_date=datetime.now()
                )
                self.supplier_allocations.append(allocation)
                
                # 更新委外加工已付款金额
                processing.paid_amount += allocated_amount
                processing.updated_at = datetime.now()
        
        # 保存数据
        self._save_data()
        
        return payment, True
    
    def allocate_payment_to_processing(
        self,
        payment_id: str,
        processing_allocations: Dict[str, Decimal]
    ) -> bool:
        """将已有付款分配到委外加工记录
        
        支持一次付款分配到多个委外加工记录
        
        Args:
            payment_id: 付款ID
            processing_allocations: 委外加工分配字典 {processing_id: allocated_amount}
        
        Returns:
            bool: 是否成功
        
        Requirements: 2.3
        """
        # 获取付款记录
        payment = self.supplier_payments.get(payment_id)
        if not payment:
            return False
        
        # 计算已分配金额
        already_allocated = self.get_payment_allocated_amount(payment_id)
        
        # 计算新分配金额
        new_allocation_total = sum(processing_allocations.values())
        
        # 验证分配金额
        if already_allocated + new_allocation_total > payment.amount:
            raise ValueError(
                f"分配金额总和 ({already_allocated + new_allocation_total}) "
                f"超过付款金额 ({payment.amount})"
            )
        
        # 创建分配记录并更新委外加工
        for processing_id, allocated_amount in processing_allocations.items():
            if allocated_amount <= 0:
                continue
            
            # 验证委外加工记录存在
            processing = self.processing_records.get(processing_id)
            if not processing:
                raise ValueError(f"委外加工记录不存在: {processing_id}")
            
            # 创建分配记录
            allocation = SupplierPaymentAllocation(
                payment_id=payment_id,
                processing_id=processing_id,
                allocated_amount=allocated_amount,
                allocation_date=datetime.now()
            )
            self.supplier_allocations.append(allocation)
            
            # 更新委外加工已付款金额
            processing.paid_amount += allocated_amount
            processing.updated_at = datetime.now()
        
        # 保存数据
        self._save_data()
        
        return True
    
    def get_payment_allocated_amount(self, payment_id: str) -> Decimal:
        """获取付款已分配金额
        
        Args:
            payment_id: 付款ID
        
        Returns:
            Decimal: 已分配金额
        """
        total = Decimal("0")
        for allocation in self.supplier_allocations:
            if allocation.payment_id == payment_id:
                total += allocation.allocated_amount
        return total
    
    def get_payment_unallocated_amount(self, payment_id: str) -> Optional[Decimal]:
        """获取付款未分配金额
        
        Args:
            payment_id: 付款ID
        
        Returns:
            Decimal: 未分配金额，如果付款不存在返回None
        """
        payment = self.supplier_payments.get(payment_id)
        if not payment:
            return None
        
        allocated = self.get_payment_allocated_amount(payment_id)
        return payment.amount - allocated
    
    def get_processing_payments(
        self,
        processing_id: str
    ) -> List[Tuple[TransactionRecord, Decimal]]:
        """获取委外加工的所有付款记录
        
        支持一个委外加工分批付款（多笔付款）
        
        Args:
            processing_id: 委外加工ID
        
        Returns:
            List[Tuple[TransactionRecord, Decimal]]: 付款记录和分配金额的列表
        
        Requirements: 2.4
        """
        result = []
        
        for allocation in self.supplier_allocations:
            if allocation.processing_id == processing_id:
                payment = self.supplier_payments.get(allocation.payment_id)
                if payment:
                    result.append((payment, allocation.allocated_amount))
        
        # 按付款日期排序
        result.sort(key=lambda x: x[0].date)
        
        return result
    
    def get_payment_processing_records(
        self,
        payment_id: str
    ) -> List[Tuple[str, Decimal]]:
        """获取付款分配到的所有委外加工记录
        
        支持一次付款关联多个委外加工
        
        Args:
            payment_id: 付款ID
        
        Returns:
            List[Tuple[str, Decimal]]: 委外加工ID和分配金额的列表
        
        Requirements: 2.3
        """
        result = []
        
        for allocation in self.supplier_allocations:
            if allocation.payment_id == payment_id:
                result.append((allocation.processing_id, allocation.allocated_amount))
        
        return result
    
    def get_processing_payment_status(self, processing_id: str) -> Dict:
        """获取委外加工的付款状态详情
        
        Args:
            processing_id: 委外加工ID
        
        Returns:
            Dict: 付款状态详情
        
        Requirements: 5.6
        """
        processing = self.processing_records.get(processing_id)
        if not processing:
            return {}
        
        payments = self.get_processing_payments(processing_id)
        
        return {
            "processing_id": processing_id,
            "total_cost": str(processing.total_cost),
            "paid_amount": str(processing.paid_amount),
            "unpaid_amount": str(processing.get_unpaid_amount()),
            "payment_status": processing.get_payment_status(),
            "is_fully_paid": processing.is_fully_paid(),
            "payment_count": len(payments),
            "payments": [
                {
                    "payment_id": payment.id,
                    "payment_date": payment.date.isoformat(),
                    "allocated_amount": str(allocated_amount),
                    "description": payment.description
                }
                for payment, allocated_amount in payments
            ]
        }
    
    def get_supplier_unpaid_processing(self, supplier_id: str) -> List[OutsourcedProcessing]:
        """获取供应商的未付清委外加工记录
        
        Args:
            supplier_id: 供应商ID
        
        Returns:
            List[OutsourcedProcessing]: 未付清的委外加工记录列表
        
        Requirements: 5.6
        """
        result = []
        
        for processing in self.processing_records.values():
            if processing.supplier_id == supplier_id and not processing.is_fully_paid():
                result.append(processing)
        
        # 按加工日期排序
        result.sort(key=lambda x: x.process_date)
        
        return result
    
    def get_unallocated_payments(self) -> List[TransactionRecord]:
        """获取所有未完全分配的供应商付款
        
        Returns:
            List[TransactionRecord]: 未完全分配的付款列表
        """
        result = []
        
        for payment in self.supplier_payments.values():
            unallocated = self.get_payment_unallocated_amount(payment.id)
            if unallocated and unallocated > Decimal("0"):
                result.append(payment)
        
        # 按日期降序排序
        result.sort(key=lambda x: x.date, reverse=True)
        
        return result
    
    def get_order_total_cost(self, order_id: str) -> Decimal:
        """获取订单的外发加工总成本
        
        Args:
            order_id: 订单ID
            
        Returns:
            外发加工总成本
            
        Requirements: 5.5
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
