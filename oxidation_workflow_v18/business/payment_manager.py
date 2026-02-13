"""
Payment Manager for Oxidation Factory Workflow Optimization

This module manages payment recording with flexible payment-to-order matching.
Supports one payment linked to multiple orders and one order receiving multiple payments.

Requirements: 2.1, 2.2
"""

from datetime import date, datetime
from decimal import Decimal
from typing import List, Optional, Dict, Tuple
import uuid
import json
import os

from ..models.core_models import (
    TransactionRecord,
    TransactionType,
    TransactionStatus
)


class PaymentAllocation:
    """付款分配记录
    
    记录一笔付款如何分配到多个订单，或多笔付款如何分配到一个订单
    """
    
    def __init__(
        self,
        payment_id: str,
        order_id: str,
        allocated_amount: Decimal,
        allocation_date: datetime
    ):
        self.payment_id = payment_id
        self.order_id = order_id
        self.allocated_amount = allocated_amount
        self.allocation_date = allocation_date
    
    def to_dict(self) -> dict:
        """转换为字典"""
        return {
            "payment_id": self.payment_id,
            "order_id": self.order_id,
            "allocated_amount": str(self.allocated_amount),
            "allocation_date": self.allocation_date.isoformat()
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> "PaymentAllocation":
        """从字典创建"""
        return cls(
            payment_id=data["payment_id"],
            order_id=data["order_id"],
            allocated_amount=Decimal(data["allocated_amount"]),
            allocation_date=datetime.fromisoformat(data["allocation_date"])
        )


class PaymentManager:
    """付款管理器
    
    功能:
    - 记录客户付款
    - 支持一次付款关联多个订单 (one-to-many)
    - 支持一个订单分批收款 (many-to-one)
    - 更新订单已收款金额
    - 查询付款分配关系
    
    Requirements: 2.1, 2.2
    """
    
    def __init__(self, data_dir: str = "data", order_manager=None):
        """初始化付款管理器
        
        Args:
            data_dir: 数据存储目录
            order_manager: 订单管理器实例（用于更新订单收款金额）
        """
        self.data_dir = data_dir
        self.order_manager = order_manager
        self.payments_file = os.path.join(data_dir, "payments.json")
        self.allocations_file = os.path.join(data_dir, "payment_allocations.json")
        self._ensure_data_dir()
        
        # 存储付款记录和分配关系
        self.payments: Dict[str, TransactionRecord] = {}
        self.allocations: List[PaymentAllocation] = []
        
        self._load_data()
    
    def _ensure_data_dir(self):
        """确保数据目录存在"""
        if not os.path.exists(self.data_dir):
            os.makedirs(self.data_dir)
    
    def _load_data(self):
        """从文件加载数据"""
        # 加载付款记录
        if os.path.exists(self.payments_file):
            try:
                with open(self.payments_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    for payment_data in data:
                        payment = TransactionRecord.from_dict(payment_data)
                        self.payments[payment.id] = payment
            except Exception as e:
                print(f"加载付款数据失败: {e}")
                self.payments = {}
        
        # 加载分配关系
        if os.path.exists(self.allocations_file):
            try:
                with open(self.allocations_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self.allocations = [
                        PaymentAllocation.from_dict(alloc_data)
                        for alloc_data in data
                    ]
            except Exception as e:
                print(f"加载分配数据失败: {e}")
                self.allocations = []
    
    def _save_data(self):
        """保存数据到文件"""
        try:
            # 保存付款记录
            payment_data = [payment.to_dict() for payment in self.payments.values()]
            with open(self.payments_file, 'w', encoding='utf-8') as f:
                json.dump(payment_data, f, ensure_ascii=False, indent=2)
            
            # 保存分配关系
            allocation_data = [alloc.to_dict() for alloc in self.allocations]
            with open(self.allocations_file, 'w', encoding='utf-8') as f:
                json.dump(allocation_data, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"保存数据失败: {e}")
            raise
    
    def record_payment(
        self,
        payment_date: date,
        amount: Decimal,
        customer_id: str,
        bank_account_id: str,
        description: str = "",
        order_allocations: Optional[Dict[str, Decimal]] = None
    ) -> Tuple[TransactionRecord, bool]:
        """记录客户付款
        
        支持一次付款关联多个订单，或不关联订单（后续手动分配）
        
        Args:
            payment_date: 付款日期
            amount: 付款金额
            customer_id: 客户ID
            bank_account_id: 银行账户ID
            description: 付款描述
            order_allocations: 订单分配字典 {order_id: allocated_amount}
                              如果为None，则创建未分配的付款
        
        Returns:
            Tuple[TransactionRecord, bool]: (付款记录, 是否成功)
        
        Requirements: 2.1, 2.2
        """
        # 验证分配金额
        if order_allocations:
            total_allocated = sum(order_allocations.values())
            if total_allocated > amount:
                raise ValueError(f"分配金额总和 ({total_allocated}) 超过付款金额 ({amount})")
        
        # 创建付款记录
        payment = TransactionRecord(
            id=str(uuid.uuid4()),
            date=payment_date,
            type=TransactionType.INCOME,
            amount=amount,
            counterparty_id=customer_id,
            description=description or f"客户付款 - {customer_id}",
            category="客户收款",
            status=TransactionStatus.COMPLETED,
            bank_account_id=bank_account_id,
            created_at=datetime.now(),
            updated_at=datetime.now()
        )
        
        # 保存付款记录
        self.payments[payment.id] = payment
        
        # 如果指定了订单分配，创建分配关系并更新订单
        if order_allocations:
            for order_id, allocated_amount in order_allocations.items():
                if allocated_amount <= 0:
                    continue
                
                # 创建分配记录
                allocation = PaymentAllocation(
                    payment_id=payment.id,
                    order_id=order_id,
                    allocated_amount=allocated_amount,
                    allocation_date=datetime.now()
                )
                self.allocations.append(allocation)
                
                # 更新订单已收款金额
                if self.order_manager:
                    self.order_manager.update_received_amount(
                        order_id,
                        allocated_amount,
                        add=True
                    )
        
        # 保存数据
        self._save_data()
        
        return payment, True
    
    def allocate_payment_to_orders(
        self,
        payment_id: str,
        order_allocations: Dict[str, Decimal]
    ) -> bool:
        """将已有付款分配到订单
        
        支持一次付款分配到多个订单
        
        Args:
            payment_id: 付款ID
            order_allocations: 订单分配字典 {order_id: allocated_amount}
        
        Returns:
            bool: 是否成功
        
        Requirements: 2.1
        """
        # 获取付款记录
        payment = self.payments.get(payment_id)
        if not payment:
            return False
        
        # 计算已分配金额
        already_allocated = self.get_payment_allocated_amount(payment_id)
        
        # 计算新分配金额
        new_allocation_total = sum(order_allocations.values())
        
        # 验证分配金额
        if already_allocated + new_allocation_total > payment.amount:
            raise ValueError(
                f"分配金额总和 ({already_allocated + new_allocation_total}) "
                f"超过付款金额 ({payment.amount})"
            )
        
        # 创建分配记录并更新订单
        for order_id, allocated_amount in order_allocations.items():
            if allocated_amount <= 0:
                continue
            
            # 创建分配记录
            allocation = PaymentAllocation(
                payment_id=payment_id,
                order_id=order_id,
                allocated_amount=allocated_amount,
                allocation_date=datetime.now()
            )
            self.allocations.append(allocation)
            
            # 更新订单已收款金额
            if self.order_manager:
                self.order_manager.update_received_amount(
                    order_id,
                    allocated_amount,
                    add=True
                )
        
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
        for allocation in self.allocations:
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
        payment = self.payments.get(payment_id)
        if not payment:
            return None
        
        allocated = self.get_payment_allocated_amount(payment_id)
        return payment.amount - allocated
    
    def get_order_payments(self, order_id: str) -> List[Tuple[TransactionRecord, Decimal]]:
        """获取订单的所有付款记录
        
        支持一个订单分批收款（多笔付款）
        
        Args:
            order_id: 订单ID
        
        Returns:
            List[Tuple[TransactionRecord, Decimal]]: 付款记录和分配金额的列表
        
        Requirements: 2.2
        """
        result = []
        
        for allocation in self.allocations:
            if allocation.order_id == order_id:
                payment = self.payments.get(allocation.payment_id)
                if payment:
                    result.append((payment, allocation.allocated_amount))
        
        # 按付款日期排序
        result.sort(key=lambda x: x[0].date)
        
        return result
    
    def get_payment_orders(self, payment_id: str) -> List[Tuple[str, Decimal]]:
        """获取付款分配到的所有订单
        
        支持一次付款关联多个订单
        
        Args:
            payment_id: 付款ID
        
        Returns:
            List[Tuple[str, Decimal]]: 订单ID和分配金额的列表
        
        Requirements: 2.1
        """
        result = []
        
        for allocation in self.allocations:
            if allocation.payment_id == payment_id:
                result.append((allocation.order_id, allocation.allocated_amount))
        
        return result
    
    def get_order_total_received(self, order_id: str) -> Decimal:
        """获取订单已收款总额
        
        Args:
            order_id: 订单ID
        
        Returns:
            Decimal: 已收款总额
        """
        total = Decimal("0")
        for allocation in self.allocations:
            if allocation.order_id == order_id:
                total += allocation.allocated_amount
        return total
    
    def get_unallocated_payments(self) -> List[TransactionRecord]:
        """获取所有未完全分配的付款
        
        Returns:
            List[TransactionRecord]: 未完全分配的付款列表
        """
        result = []
        
        for payment in self.payments.values():
            unallocated = self.get_payment_unallocated_amount(payment.id)
            if unallocated and unallocated > Decimal("0"):
                result.append(payment)
        
        # 按日期降序排序
        result.sort(key=lambda x: x.date, reverse=True)
        
        return result
    
    def get_payment(self, payment_id: str) -> Optional[TransactionRecord]:
        """获取付款记录
        
        Args:
            payment_id: 付款ID
        
        Returns:
            TransactionRecord: 付款记录，如果不存在返回None
        """
        return self.payments.get(payment_id)
    
    def get_all_payments(self) -> List[TransactionRecord]:
        """获取所有付款记录
        
        Returns:
            List[TransactionRecord]: 所有付款记录
        """
        payments = list(self.payments.values())
        payments.sort(key=lambda x: x.date, reverse=True)
        return payments
    
    def get_payments_by_customer(self, customer_id: str) -> List[TransactionRecord]:
        """获取客户的所有付款记录
        
        Args:
            customer_id: 客户ID
        
        Returns:
            List[TransactionRecord]: 客户的付款记录列表
        """
        result = [
            payment for payment in self.payments.values()
            if payment.counterparty_id == customer_id
        ]
        result.sort(key=lambda x: x.date, reverse=True)
        return result
    
    def get_payments_by_date_range(
        self,
        start_date: date,
        end_date: date
    ) -> List[TransactionRecord]:
        """获取日期范围内的付款记录
        
        Args:
            start_date: 开始日期
            end_date: 结束日期
        
        Returns:
            List[TransactionRecord]: 日期范围内的付款记录
        """
        result = [
            payment for payment in self.payments.values()
            if start_date <= payment.date <= end_date
        ]
        result.sort(key=lambda x: x.date, reverse=True)
        return result
