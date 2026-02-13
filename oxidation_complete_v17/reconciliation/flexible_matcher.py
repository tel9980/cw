"""
Flexible Reconciliation Matcher for V1.7 Oxidation Factory Complete

This module extends the bank statement matching functionality to support flexible
matching scenarios common in small businesses:
- One-to-many: One bank record matches multiple system records (merged payment)
- Many-to-one: Multiple bank records match one system record (split payment)
- Balance tracking and reconciliation history
"""

from dataclasses import dataclass, field
from datetime import datetime, date
from decimal import Decimal
from typing import List, Optional, Dict, Set, Tuple
from enum import Enum
import json
import os

from oxidation_complete_v17.models.core_models import (
    BankRecord,
    TransactionRecord,
    ProcessingOrder
)


class FlexibleMatchType(Enum):
    """灵活匹配类型"""
    ONE_TO_ONE = "one_to_one"  # 一对一
    ONE_TO_MANY = "one_to_many"  # 一对多(一笔银行流水对应多个订单)
    MANY_TO_ONE = "many_to_one"  # 多对一(多笔银行流水对应一个订单)


@dataclass
class FlexibleMatch:
    """灵活匹配结果"""
    id: str
    match_type: FlexibleMatchType
    bank_records: List[BankRecord]  # 可能有多笔
    system_records: List[TransactionRecord]  # 可能有多笔
    orders: List[ProcessingOrder]  # 关联的订单
    total_bank_amount: Decimal
    total_system_amount: Decimal
    balance: Decimal  # 余额(银行金额 - 系统金额)
    matched_at: datetime
    notes: str = ""
    
    def to_dict(self) -> dict:
        """转换为字典"""
        return {
            "id": self.id,
            "match_type": self.match_type.value,
            "bank_records": [br.to_dict() for br in self.bank_records],
            "system_records": [sr.to_dict() for sr in self.system_records],
            "orders": [o.to_dict() for o in self.orders],
            "total_bank_amount": str(self.total_bank_amount),
            "total_system_amount": str(self.total_system_amount),
            "balance": str(self.balance),
            "matched_at": self.matched_at.isoformat(),
            "notes": self.notes,
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> "FlexibleMatch":
        """从字典创建"""
        return cls(
            id=data["id"],
            match_type=FlexibleMatchType(data["match_type"]),
            bank_records=[BankRecord.from_dict(br) for br in data["bank_records"]],
            system_records=[TransactionRecord.from_dict(sr) for sr in data["system_records"]],
            orders=[ProcessingOrder.from_dict(o) for o in data["orders"]],
            total_bank_amount=Decimal(data["total_bank_amount"]),
            total_system_amount=Decimal(data["total_system_amount"]),
            balance=Decimal(data["balance"]),
            matched_at=datetime.fromisoformat(data["matched_at"]),
            notes=data.get("notes", ""),
        )


@dataclass
class ReconciliationHistory:
    """对账历史记录"""
    id: str
    match_id: str
    action: str  # 'create', 'update', 'undo'
    performed_at: datetime
    performed_by: str
    details: dict
    
    def to_dict(self) -> dict:
        """转换为字典"""
        return {
            "id": self.id,
            "match_id": self.match_id,
            "action": self.action,
            "performed_at": self.performed_at.isoformat(),
            "performed_by": self.performed_by,
            "details": self.details,
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> "ReconciliationHistory":
        """从字典创建"""
        return cls(
            id=data["id"],
            match_id=data["match_id"],
            action=data["action"],
            performed_at=datetime.fromisoformat(data["performed_at"]),
            performed_by=data["performed_by"],
            details=data["details"],
        )


@dataclass
class CounterpartyBalance:
    """往来单位余额"""
    counterparty_id: str
    counterparty_name: str
    total_orders_amount: Decimal  # 订单总金额
    total_received_amount: Decimal  # 已收款总金额
    unreconciled_balance: Decimal  # 未对账余额
    last_updated: datetime
    
    def to_dict(self) -> dict:
        """转换为字典"""
        return {
            "counterparty_id": self.counterparty_id,
            "counterparty_name": self.counterparty_name,
            "total_orders_amount": str(self.total_orders_amount),
            "total_received_amount": str(self.total_received_amount),
            "unreconciled_balance": str(self.unreconciled_balance),
            "last_updated": self.last_updated.isoformat(),
        }


class FlexibleReconciliationMatcher:
    """
    灵活对账匹配器
    
    支持一对多、多对一的灵活匹配场景,适用于小企业实际业务:
    - 客户合并付款(一笔银行流水对应多个订单)
    - 客户分批付款(多笔银行流水对应一个订单)
    - 余额计算和更新
    - 对账历史记录
    - 撤销对账操作
    """
    
    def __init__(self, data_dir: str = "data"):
        """
        初始化灵活对账匹配器
        
        Args:
            data_dir: 数据存储目录
        """
        self.data_dir = data_dir
        self.matches_file = os.path.join(data_dir, "flexible_matches.json")
        self.history_file = os.path.join(data_dir, "reconciliation_history.json")
        
        # 确保数据目录存在
        os.makedirs(data_dir, exist_ok=True)
        
        # 加载数据
        self.matches: Dict[str, FlexibleMatch] = self._load_matches()
        self.history: List[ReconciliationHistory] = self._load_history()
        self._next_match_id = len(self.matches) + 1
        self._next_history_id = len(self.history) + 1
    
    def create_one_to_many_match(
        self,
        bank_record: BankRecord,
        orders: List[ProcessingOrder],
        notes: str = "",
        performed_by: str = "system"
    ) -> FlexibleMatch:
        """
        创建一对多匹配(一笔银行流水对应多个订单)
        
        场景:客户合并付款,一次性支付多个订单的款项
        
        Args:
            bank_record: 银行流水记录
            orders: 订单列表
            notes: 备注
            performed_by: 操作人
        
        Returns:
            FlexibleMatch: 匹配结果
        """
        # 计算订单总金额
        total_orders_amount = sum(order.total_amount for order in orders)
        
        # 创建匹配记录
        match = FlexibleMatch(
            id=f"MATCH-{self._next_match_id:06d}",
            match_type=FlexibleMatchType.ONE_TO_MANY,
            bank_records=[bank_record],
            system_records=[],  # 暂时为空,可以后续关联交易记录
            orders=orders,
            total_bank_amount=bank_record.amount,
            total_system_amount=total_orders_amount,
            balance=bank_record.amount - total_orders_amount,
            matched_at=datetime.now(),
            notes=notes,
        )
        
        # 保存匹配记录
        self.matches[match.id] = match
        self._next_match_id += 1
        
        # 记录历史
        self._add_history(
            match_id=match.id,
            action="create",
            performed_by=performed_by,
            details={
                "match_type": "one_to_many",
                "bank_record_id": bank_record.id,
                "order_ids": [o.id for o in orders],
                "bank_amount": str(bank_record.amount),
                "orders_amount": str(total_orders_amount),
                "balance": str(match.balance),
            }
        )
        
        # 保存到文件
        self._save_matches()
        self._save_history()
        
        return match
    
    def create_many_to_one_match(
        self,
        bank_records: List[BankRecord],
        order: ProcessingOrder,
        notes: str = "",
        performed_by: str = "system"
    ) -> FlexibleMatch:
        """
        创建多对一匹配(多笔银行流水对应一个订单)
        
        场景:客户分批付款,分多次支付一个订单的款项
        
        Args:
            bank_records: 银行流水记录列表
            order: 订单
            notes: 备注
            performed_by: 操作人
        
        Returns:
            FlexibleMatch: 匹配结果
        """
        # 计算银行流水总金额
        total_bank_amount = sum(br.amount for br in bank_records)
        
        # 创建匹配记录
        match = FlexibleMatch(
            id=f"MATCH-{self._next_match_id:06d}",
            match_type=FlexibleMatchType.MANY_TO_ONE,
            bank_records=bank_records,
            system_records=[],  # 暂时为空,可以后续关联交易记录
            orders=[order],
            total_bank_amount=total_bank_amount,
            total_system_amount=order.total_amount,
            balance=total_bank_amount - order.total_amount,
            matched_at=datetime.now(),
            notes=notes,
        )
        
        # 保存匹配记录
        self.matches[match.id] = match
        self._next_match_id += 1
        
        # 记录历史
        self._add_history(
            match_id=match.id,
            action="create",
            performed_by=performed_by,
            details={
                "match_type": "many_to_one",
                "bank_record_ids": [br.id for br in bank_records],
                "order_id": order.id,
                "bank_amount": str(total_bank_amount),
                "order_amount": str(order.total_amount),
                "balance": str(match.balance),
            }
        )
        
        # 保存到文件
        self._save_matches()
        self._save_history()
        
        return match
    
    def update_match_balance(
        self,
        match_id: str,
        new_bank_records: Optional[List[BankRecord]] = None,
        new_orders: Optional[List[ProcessingOrder]] = None,
        performed_by: str = "system"
    ) -> FlexibleMatch:
        """
        更新匹配记录的余额
        
        Args:
            match_id: 匹配记录ID
            new_bank_records: 新增的银行流水记录
            new_orders: 新增的订单
            performed_by: 操作人
        
        Returns:
            FlexibleMatch: 更新后的匹配记录
        """
        if match_id not in self.matches:
            raise ValueError(f"匹配记录不存在: {match_id}")
        
        match = self.matches[match_id]
        
        # 更新银行流水
        if new_bank_records:
            match.bank_records.extend(new_bank_records)
            match.total_bank_amount = sum(br.amount for br in match.bank_records)
        
        # 更新订单
        if new_orders:
            match.orders.extend(new_orders)
            match.total_system_amount = sum(o.total_amount for o in match.orders)
        
        # 重新计算余额
        match.balance = match.total_bank_amount - match.total_system_amount
        
        # 记录历史
        self._add_history(
            match_id=match_id,
            action="update",
            performed_by=performed_by,
            details={
                "new_bank_records": len(new_bank_records) if new_bank_records else 0,
                "new_orders": len(new_orders) if new_orders else 0,
                "new_balance": str(match.balance),
            }
        )
        
        # 保存到文件
        self._save_matches()
        self._save_history()
        
        return match
    
    def undo_match(
        self,
        match_id: str,
        performed_by: str = "system"
    ) -> bool:
        """
        撤销对账操作
        
        Args:
            match_id: 匹配记录ID
            performed_by: 操作人
        
        Returns:
            bool: 是否成功撤销
        """
        if match_id not in self.matches:
            return False
        
        match = self.matches[match_id]
        
        # 记录历史
        self._add_history(
            match_id=match_id,
            action="undo",
            performed_by=performed_by,
            details={
                "match_type": match.match_type.value,
                "bank_records_count": len(match.bank_records),
                "orders_count": len(match.orders),
            }
        )
        
        # 删除匹配记录
        del self.matches[match_id]
        
        # 保存到文件
        self._save_matches()
        self._save_history()
        
        return True
    
    def get_counterparty_balance(
        self,
        counterparty_id: str,
        counterparty_name: str,
        all_orders: List[ProcessingOrder]
    ) -> CounterpartyBalance:
        """
        获取往来单位的未对账余额
        
        Args:
            counterparty_id: 往来单位ID
            counterparty_name: 往来单位名称
            all_orders: 该往来单位的所有订单
        
        Returns:
            CounterpartyBalance: 往来单位余额信息
        """
        # 计算订单总金额
        total_orders_amount = sum(order.total_amount for order in all_orders)
        
        # 计算已对账金额
        total_received_amount = Decimal("0")
        for match in self.matches.values():
            # 检查匹配记录中是否包含该往来单位的订单
            for order in match.orders:
                if order.customer_id == counterparty_id:
                    # 按比例分配银行流水金额
                    if match.total_system_amount > 0:
                        proportion = order.total_amount / match.total_system_amount
                        allocated_amount = match.total_bank_amount * proportion
                        total_received_amount += allocated_amount
        
        # 计算未对账余额
        unreconciled_balance = total_orders_amount - total_received_amount
        
        return CounterpartyBalance(
            counterparty_id=counterparty_id,
            counterparty_name=counterparty_name,
            total_orders_amount=total_orders_amount,
            total_received_amount=total_received_amount,
            unreconciled_balance=unreconciled_balance,
            last_updated=datetime.now(),
        )
    
    def get_match_history(self, match_id: str) -> List[ReconciliationHistory]:
        """
        获取匹配记录的历史
        
        Args:
            match_id: 匹配记录ID
        
        Returns:
            List[ReconciliationHistory]: 历史记录列表
        """
        return [h for h in self.history if h.match_id == match_id]
    
    def get_all_matches(
        self,
        match_type: Optional[FlexibleMatchType] = None,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None
    ) -> List[FlexibleMatch]:
        """
        获取所有匹配记录
        
        Args:
            match_type: 匹配类型过滤
            start_date: 开始日期
            end_date: 结束日期
        
        Returns:
            List[FlexibleMatch]: 匹配记录列表
        """
        results = list(self.matches.values())
        
        # 按匹配类型过滤
        if match_type:
            results = [m for m in results if m.match_type == match_type]
        
        # 按日期过滤
        if start_date:
            results = [m for m in results if m.matched_at.date() >= start_date]
        if end_date:
            results = [m for m in results if m.matched_at.date() <= end_date]
        
        # 按匹配时间降序排序
        results.sort(key=lambda m: m.matched_at, reverse=True)
        
        return results
    
    def _add_history(
        self,
        match_id: str,
        action: str,
        performed_by: str,
        details: dict
    ):
        """添加历史记录"""
        history = ReconciliationHistory(
            id=f"HIST-{self._next_history_id:06d}",
            match_id=match_id,
            action=action,
            performed_at=datetime.now(),
            performed_by=performed_by,
            details=details,
        )
        self.history.append(history)
        self._next_history_id += 1
    
    def _load_matches(self) -> Dict[str, FlexibleMatch]:
        """从文件加载匹配记录"""
        if not os.path.exists(self.matches_file):
            return {}
        
        try:
            with open(self.matches_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                return {
                    match_id: FlexibleMatch.from_dict(match_data)
                    for match_id, match_data in data.items()
                }
        except Exception:
            return {}
    
    def _save_matches(self):
        """保存匹配记录到文件"""
        data = {
            match_id: match.to_dict()
            for match_id, match in self.matches.items()
        }
        with open(self.matches_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    
    def _load_history(self) -> List[ReconciliationHistory]:
        """从文件加载历史记录"""
        if not os.path.exists(self.history_file):
            return []
        
        try:
            with open(self.history_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                return [ReconciliationHistory.from_dict(h) for h in data]
        except Exception:
            return []
    
    def _save_history(self):
        """保存历史记录到文件"""
        data = [h.to_dict() for h in self.history]
        with open(self.history_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
