"""
Core data models for Oxidation Factory Workflow Optimization System

This module contains the core data models for the oxidation factory workflow system,
including order management, bank accounts, reconciliation, and related entities.

Reused from oxidation_complete_v17/models/core_models.py with enhancements.
"""

from dataclasses import dataclass, field
from datetime import date, datetime
from decimal import Decimal
from enum import Enum
from typing import List, Optional, Dict


# ============================================================================
# Enumerations
# ============================================================================

class PricingUnit(Enum):
    """计价单位 - 支持多种氧化加工计价方式"""
    PIECE = "piece"  # 件
    STRIP = "strip"  # 条
    ITEM = "item"  # 只
    UNIT = "unit"  # 个
    METER_LENGTH = "meter_length"  # 米长
    METER_WEIGHT = "meter_weight"  # 米重
    SQUARE_METER = "square_meter"  # 平方


class ProcessType(Enum):
    """外发加工工序类型"""
    SANDBLASTING = "sandblasting"  # 喷砂
    WIRE_DRAWING = "wire_drawing"  # 拉丝
    POLISHING = "polishing"  # 抛光


class OrderStatus(Enum):
    """订单状态"""
    PENDING = "pending"  # 待处理
    IN_PROGRESS = "in_progress"  # 进行中
    COMPLETED = "completed"  # 已完成
    CANCELLED = "cancelled"  # 已取消


class AccountType(Enum):
    """银行账户类型"""
    BUSINESS = "business"  # 对公账户（有票）
    CASH = "cash"  # 现金账户（无票）


class TransactionType(Enum):
    """交易类型"""
    INCOME = "income"  # 收入
    EXPENSE = "expense"  # 支出


class TransactionStatus(Enum):
    """交易状态"""
    PENDING = "pending"  # 待处理
    COMPLETED = "completed"  # 已完成
    CANCELLED = "cancelled"  # 已取消


class CounterpartyType(Enum):
    """往来单位类型"""
    CUSTOMER = "customer"  # 客户
    SUPPLIER = "supplier"  # 供应商


# ============================================================================
# Core Data Models
# ============================================================================

@dataclass
class ProcessingOrder:
    """
    加工订单模型
    
    支持多种计价单位的氧化加工订单，包含订单金额计算、收款跟踪、
    外发成本管理等功能。
    
    Requirements: 1.1, 1.2, 1.3, 1.4, 1.5
    """
    id: str
    order_number: str  # 订单编号
    customer_id: str  # 客户ID
    order_date: date  # 订单日期
    product_name: str  # 产品名称
    pricing_unit: PricingUnit  # 计价单位
    quantity: Decimal  # 数量
    unit_price: Decimal  # 单价
    total_amount: Decimal  # 总金额
    status: OrderStatus  # 订单状态
    received_amount: Decimal  # 已收款金额
    outsourced_cost: Decimal  # 外发加工成本
    notes: str  # 备注
    created_at: datetime
    updated_at: datetime
    
    def calculate_total(self) -> Decimal:
        """
        计算订单总金额
        
        Returns:
            Decimal: 数量 × 单价
        """
        return self.quantity * self.unit_price
    
    def get_balance(self) -> Decimal:
        """
        获取未收款余额
        
        Returns:
            Decimal: 总金额 - 已收款金额
        """
        return self.total_amount - self.received_amount
    
    def get_profit(self) -> Decimal:
        """
        获取订单利润
        
        Returns:
            Decimal: 总金额 - 外发成本
        """
        return self.total_amount - self.outsourced_cost
    
    def to_dict(self) -> dict:
        """转换为字典"""
        return {
            "id": self.id,
            "order_number": self.order_number,
            "customer_id": self.customer_id,
            "order_date": self.order_date.isoformat(),
            "product_name": self.product_name,
            "pricing_unit": self.pricing_unit.value,
            "quantity": str(self.quantity),
            "unit_price": str(self.unit_price),
            "total_amount": str(self.total_amount),
            "status": self.status.value,
            "received_amount": str(self.received_amount),
            "outsourced_cost": str(self.outsourced_cost),
            "notes": self.notes,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> "ProcessingOrder":
        """从字典创建"""
        return cls(
            id=data["id"],
            order_number=data["order_number"],
            customer_id=data["customer_id"],
            order_date=date.fromisoformat(data["order_date"]),
            product_name=data["product_name"],
            pricing_unit=PricingUnit(data["pricing_unit"]),
            quantity=Decimal(data["quantity"]),
            unit_price=Decimal(data["unit_price"]),
            total_amount=Decimal(data["total_amount"]),
            status=OrderStatus(data["status"]),
            received_amount=Decimal(data["received_amount"]),
            outsourced_cost=Decimal(data["outsourced_cost"]),
            notes=data["notes"],
            created_at=datetime.fromisoformat(data["created_at"]),
            updated_at=datetime.fromisoformat(data["updated_at"]),
        )


@dataclass
class OutsourcedProcessing:
    """
    外发加工记录
    
    记录喷砂、拉丝、抛光等外发加工工序的详细信息，
    包括供应商、数量、费用等。
    
    Requirements: 5.1, 5.2, 5.3, 5.6
    """
    id: str
    order_id: str  # 关联的加工订单ID
    supplier_id: str  # 供应商ID
    process_type: ProcessType  # 工序类型
    process_date: date  # 加工日期
    quantity: Decimal  # 数量
    unit_price: Decimal  # 单价
    total_cost: Decimal  # 总成本
    paid_amount: Decimal  # 已付款金额
    notes: str  # 备注
    created_at: datetime
    updated_at: datetime
    
    def calculate_total(self) -> Decimal:
        """
        计算总成本
        
        Returns:
            Decimal: 数量 × 单价
        """
        return self.quantity * self.unit_price
    
    def get_unpaid_amount(self) -> Decimal:
        """
        获取未付款金额
        
        Returns:
            Decimal: 总成本 - 已付款金额
        
        Requirements: 5.6
        """
        return self.total_cost - self.paid_amount
    
    def is_fully_paid(self) -> bool:
        """
        是否已全额付款
        
        Returns:
            bool: True if fully paid
        
        Requirements: 5.6
        """
        return self.paid_amount >= self.total_cost
    
    def get_payment_status(self) -> str:
        """
        获取付款状态描述
        
        Returns:
            str: "已付清", "部分付款", "未付款"
        
        Requirements: 5.6
        """
        if self.paid_amount == Decimal("0"):
            return "未付款"
        elif self.paid_amount >= self.total_cost:
            return "已付清"
        else:
            return "部分付款"
    
    def to_dict(self) -> dict:
        """转换为字典"""
        return {
            "id": self.id,
            "order_id": self.order_id,
            "supplier_id": self.supplier_id,
            "process_type": self.process_type.value,
            "process_date": self.process_date.isoformat(),
            "quantity": str(self.quantity),
            "unit_price": str(self.unit_price),
            "total_cost": str(self.total_cost),
            "paid_amount": str(self.paid_amount),
            "notes": self.notes,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> "OutsourcedProcessing":
        """从字典创建"""
        return cls(
            id=data["id"],
            order_id=data["order_id"],
            supplier_id=data["supplier_id"],
            process_type=ProcessType(data["process_type"]),
            process_date=date.fromisoformat(data["process_date"]),
            quantity=Decimal(data["quantity"]),
            unit_price=Decimal(data["unit_price"]),
            total_cost=Decimal(data["total_cost"]),
            paid_amount=Decimal(data.get("paid_amount", "0")),
            notes=data["notes"],
            created_at=datetime.fromisoformat(data["created_at"]),
            updated_at=datetime.fromisoformat(data["updated_at"]),
        )


@dataclass
class BankAccount:
    """
    银行账户模型
    
    支持多种账户类型（G银行、N银行、微信），区分有票/无票账户。
    
    Requirements: 3.1, 3.2, 3.3, 3.5
    """
    id: str
    name: str  # 账户名称（如：G银行、N银行、微信）
    account_number: str  # 账号
    account_type: AccountType  # 账户类型
    has_invoice: bool  # 是否有票据
    balance: Decimal  # 余额
    description: str  # 描述
    created_at: datetime
    updated_at: datetime
    
    def update_balance(self, amount: Decimal, is_credit: bool) -> Decimal:
        """
        更新账户余额
        
        Args:
            amount: 交易金额
            is_credit: True表示收入（增加余额），False表示支出（减少余额）
        
        Returns:
            Decimal: 更新后的余额
        
        Requirements: 3.5
        """
        if is_credit:
            self.balance += amount
        else:
            self.balance -= amount
        return self.balance
    
    def calculate_balance_from_transactions(self, transactions: List['TransactionRecord']) -> Decimal:
        """
        根据交易记录计算账户余额
        
        Args:
            transactions: 该账户的所有交易记录列表
        
        Returns:
            Decimal: 计算得到的余额（收入总额 - 支出总额）
        
        Requirements: 3.5
        """
        total_income = sum(
            t.amount for t in transactions 
            if t.type == TransactionType.INCOME and t.bank_account_id == self.id
        )
        total_expense = sum(
            t.amount for t in transactions 
            if t.type == TransactionType.EXPENSE and t.bank_account_id == self.id
        )
        return total_income - total_expense
    
    def to_dict(self) -> dict:
        """转换为字典"""
        return {
            "id": self.id,
            "name": self.name,
            "account_number": self.account_number,
            "account_type": self.account_type.value,
            "has_invoice": self.has_invoice,
            "balance": str(self.balance),
            "description": self.description,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> "BankAccount":
        """从字典创建"""
        return cls(
            id=data["id"],
            name=data["name"],
            account_number=data["account_number"],
            account_type=AccountType(data["account_type"]),
            has_invoice=data["has_invoice"],
            balance=Decimal(data["balance"]),
            description=data["description"],
            created_at=datetime.fromisoformat(data["created_at"]),
            updated_at=datetime.fromisoformat(data["updated_at"]),
        )


@dataclass
class ReconciliationMatch:
    """
    对账匹配记录
    
    支持灵活的一对多、多对一收付款匹配关系。
    
    Requirements: 2.1, 2.2, 2.3, 2.4
    """
    id: str
    match_date: datetime
    bank_record_ids: List[str]  # 银行流水ID列表（支持多笔）
    order_ids: List[str]  # 订单ID列表（支持多笔）
    total_bank_amount: Decimal  # 银行流水总金额
    total_order_amount: Decimal  # 订单总金额
    difference: Decimal  # 差额
    notes: str  # 备注
    created_by: str  # 创建人
    created_at: datetime
    
    def is_one_to_many(self) -> bool:
        """
        是否为一对多匹配（一笔银行流水对多个订单）
        
        Returns:
            bool: True if one bank record matches many orders
        
        Requirements: 2.1
        """
        return len(self.bank_record_ids) == 1 and len(self.order_ids) > 1
    
    def is_many_to_one(self) -> bool:
        """
        是否为多对一匹配（多笔银行流水对一个订单）
        
        Returns:
            bool: True if many bank records match one order
        
        Requirements: 2.2
        """
        return len(self.bank_record_ids) > 1 and len(self.order_ids) == 1
    
    def is_one_to_one(self) -> bool:
        """
        是否为一对一匹配（一笔银行流水对一个订单）
        
        Returns:
            bool: True if one bank record matches one order
        """
        return len(self.bank_record_ids) == 1 and len(self.order_ids) == 1
    
    def is_many_to_many(self) -> bool:
        """
        是否为多对多匹配（多笔银行流水对多个订单）
        
        Returns:
            bool: True if many bank records match many orders
        """
        return len(self.bank_record_ids) > 1 and len(self.order_ids) > 1
    
    def validate_match(self) -> tuple[bool, str]:
        """
        验证匹配关系的有效性
        
        检查：
        1. 至少有一笔银行流水和一个订单
        2. 金额差异在合理范围内（允许小额差异）
        3. 银行流水ID和订单ID不能为空
        
        Returns:
            tuple[bool, str]: (是否有效, 错误消息)
        
        Requirements: 2.1, 2.2, 2.3, 2.4
        """
        # 检查是否有银行流水和订单
        if not self.bank_record_ids or len(self.bank_record_ids) == 0:
            return False, "至少需要一笔银行流水"
        
        if not self.order_ids or len(self.order_ids) == 0:
            return False, "至少需要一个订单"
        
        # 检查ID是否为空字符串
        if any(not bid or bid.strip() == "" for bid in self.bank_record_ids):
            return False, "银行流水ID不能为空"
        
        if any(not oid or oid.strip() == "" for oid in self.order_ids):
            return False, "订单ID不能为空"
        
        # 检查金额差异（允许0.01的小额差异，考虑浮点精度）
        if abs(self.difference) > Decimal("0.01"):
            # 如果差异较大，给出警告但不阻止
            return True, f"存在金额差异: {self.difference}"
        
        return True, ""
    
    def calculate_difference(self) -> Decimal:
        """
        计算银行流水总额与订单总额的差异
        
        Returns:
            Decimal: 差额（银行流水总额 - 订单总额）
        
        Requirements: 2.5
        """
        return self.total_bank_amount - self.total_order_amount
    
    def get_match_type(self) -> str:
        """
        获取匹配类型的描述
        
        Returns:
            str: 匹配类型（"一对一", "一对多", "多对一", "多对多"）
        """
        if self.is_one_to_one():
            return "一对一"
        elif self.is_one_to_many():
            return "一对多"
        elif self.is_many_to_one():
            return "多对一"
        elif self.is_many_to_many():
            return "多对多"
        else:
            return "未知"
    
    def to_dict(self) -> dict:
        """转换为字典"""
        return {
            "id": self.id,
            "match_date": self.match_date.isoformat(),
            "bank_record_ids": self.bank_record_ids,
            "order_ids": self.order_ids,
            "total_bank_amount": str(self.total_bank_amount),
            "total_order_amount": str(self.total_order_amount),
            "difference": str(self.difference),
            "notes": self.notes,
            "created_by": self.created_by,
            "created_at": self.created_at.isoformat(),
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> "ReconciliationMatch":
        """从字典创建"""
        return cls(
            id=data["id"],
            match_date=datetime.fromisoformat(data["match_date"]),
            bank_record_ids=data["bank_record_ids"],
            order_ids=data["order_ids"],
            total_bank_amount=Decimal(data["total_bank_amount"]),
            total_order_amount=Decimal(data["total_order_amount"]),
            difference=Decimal(data["difference"]),
            notes=data["notes"],
            created_by=data["created_by"],
            created_at=datetime.fromisoformat(data["created_at"]),
        )


@dataclass
class TransactionRecord:
    """
    交易记录
    
    通用的收支交易记录，支持计价单位和银行账户关联。
    
    Requirements: 2.1, 2.2, 3.4, 7.1
    """
    id: str
    date: date
    type: TransactionType
    amount: Decimal
    counterparty_id: str
    description: str
    category: str  # 支出类别
    status: TransactionStatus
    created_at: datetime
    updated_at: datetime
    # 扩展字段
    pricing_unit: Optional[PricingUnit] = None  # 计价单位
    quantity: Optional[Decimal] = None  # 数量
    unit_price: Optional[Decimal] = None  # 单价
    bank_account_id: Optional[str] = None  # 所属银行账户
    
    def to_dict(self) -> dict:
        """转换为字典"""
        return {
            "id": self.id,
            "date": self.date.isoformat(),
            "type": self.type.value,
            "amount": str(self.amount),
            "counterparty_id": self.counterparty_id,
            "description": self.description,
            "category": self.category,
            "status": self.status.value,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "pricing_unit": self.pricing_unit.value if self.pricing_unit else None,
            "quantity": str(self.quantity) if self.quantity else None,
            "unit_price": str(self.unit_price) if self.unit_price else None,
            "bank_account_id": self.bank_account_id,
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> "TransactionRecord":
        """从字典创建"""
        return cls(
            id=data["id"],
            date=date.fromisoformat(data["date"]),
            type=TransactionType(data["type"]),
            amount=Decimal(data["amount"]),
            counterparty_id=data["counterparty_id"],
            description=data["description"],
            category=data["category"],
            status=TransactionStatus(data["status"]),
            created_at=datetime.fromisoformat(data["created_at"]),
            updated_at=datetime.fromisoformat(data["updated_at"]),
            pricing_unit=PricingUnit(data["pricing_unit"]) if data.get("pricing_unit") else None,
            quantity=Decimal(data["quantity"]) if data.get("quantity") else None,
            unit_price=Decimal(data["unit_price"]) if data.get("unit_price") else None,
            bank_account_id=data.get("bank_account_id"),
        )


@dataclass
class Counterparty:
    """
    往来单位（客户/供应商）
    
    支持别名管理，便于灵活对账。
    
    Requirements: 6.2, 6.5
    """
    id: str
    name: str
    type: CounterpartyType
    contact_person: str
    phone: str
    email: str
    address: str
    tax_id: str
    created_at: datetime
    updated_at: datetime
    aliases: List[str] = field(default_factory=list)  # 别名列表
    
    def to_dict(self) -> dict:
        """转换为字典"""
        return {
            "id": self.id,
            "name": self.name,
            "type": self.type.value,
            "contact_person": self.contact_person,
            "phone": self.phone,
            "email": self.email,
            "address": self.address,
            "tax_id": self.tax_id,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "aliases": self.aliases,
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> "Counterparty":
        """从字典创建"""
        return cls(
            id=data["id"],
            name=data["name"],
            type=CounterpartyType(data["type"]),
            contact_person=data["contact_person"],
            phone=data["phone"],
            email=data["email"],
            address=data["address"],
            tax_id=data["tax_id"],
            created_at=datetime.fromisoformat(data["created_at"]),
            updated_at=datetime.fromisoformat(data["updated_at"]),
            aliases=data.get("aliases", []),
        )


@dataclass
class BankRecord:
    """
    银行流水记录
    
    用于对账的银行流水数据。
    
    Requirements: 6.1
    """
    id: str
    transaction_date: date
    description: str
    amount: Decimal
    balance: Decimal
    transaction_type: str  # DEBIT, CREDIT
    counterparty: str
    bank_account_id: Optional[str] = None  # 所属银行账户
    
    def to_dict(self) -> dict:
        """转换为字典"""
        return {
            "id": self.id,
            "transaction_date": self.transaction_date.isoformat(),
            "description": self.description,
            "amount": str(self.amount),
            "balance": str(self.balance),
            "transaction_type": self.transaction_type,
            "counterparty": self.counterparty,
            "bank_account_id": self.bank_account_id,
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> "BankRecord":
        """从字典创建"""
        return cls(
            id=data["id"],
            transaction_date=date.fromisoformat(data["transaction_date"]),
            description=data["description"],
            amount=Decimal(data["amount"]),
            balance=Decimal(data["balance"]),
            transaction_type=data["transaction_type"],
            counterparty=data["counterparty"],
            bank_account_id=data.get("bank_account_id"),
        )
