"""
Core data models for V1.6 Small Accountant Practical Enhancement

This module defines all the core data structures used throughout the system.
"""

from dataclasses import dataclass, field
from datetime import date, datetime
from decimal import Decimal
from enum import Enum
from typing import List, Optional, Dict
import json


# Enumerations

class TransactionType(Enum):
    """交易类型"""
    INCOME = "income"  # 收入
    EXPENSE = "expense"  # 支出
    ORDER = "order"  # 订单


class TransactionStatus(Enum):
    """交易状态"""
    PENDING = "pending"  # 待处理
    COMPLETED = "completed"  # 已完成
    CANCELLED = "cancelled"  # 已取消


class CounterpartyType(Enum):
    """往来单位类型"""
    CUSTOMER = "customer"  # 客户
    SUPPLIER = "supplier"  # 供应商


class ReminderType(Enum):
    """提醒类型"""
    TAX = "tax"  # 税务申报
    PAYABLE = "payable"  # 应付账款
    RECEIVABLE = "receivable"  # 应收账款
    CASHFLOW = "cashflow"  # 现金流预警


class ReminderStatus(Enum):
    """提醒状态"""
    PENDING = "pending"  # 待发送
    SENT = "sent"  # 已发送
    COMPLETED = "completed"  # 已完成


class Priority(Enum):
    """优先级"""
    HIGH = "high"  # 高
    MEDIUM = "medium"  # 中
    LOW = "low"  # 低


class ReportType(Enum):
    """报表类型"""
    MANAGEMENT = "management"  # 管理报表
    TAX_VAT = "tax_vat"  # 增值税申报表
    TAX_INCOME = "tax_income"  # 所得税申报表
    BANK_LOAN = "bank_loan"  # 银行贷款报表


class NotificationChannel(Enum):
    """通知渠道"""
    DESKTOP = "desktop"  # 桌面通知
    WECHAT = "wechat"  # 企业微信


class DiscrepancyType(Enum):
    """差异类型"""
    AMOUNT_DIFF = "amount_diff"  # 金额差异
    MISSING_BANK = "missing_bank"  # 银行流水缺失
    MISSING_SYSTEM = "missing_system"  # 系统记录缺失



# NEW: Oxidation Factory Specific Enumerations

class PricingUnit(Enum):
    """计价单位"""
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
    BUSINESS = "business"  # 对公账户
    CASH = "cash"  # 现金账户


# Core Data Models

@dataclass
class TransactionRecord:
    """交易记录"""
    id: str
    date: date
    type: TransactionType
    amount: Decimal
    counterparty_id: str
    description: str
    category: str
    status: TransactionStatus
    created_at: datetime
    updated_at: datetime
    # NEW: 氧化加工厂扩展字段
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
    """往来单位（客户/供应商）"""
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
    # NEW: 氧化加工厂扩展字段
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
class Reminder:
    """提醒事项"""
    id: str
    type: ReminderType
    title: str
    description: str
    due_date: date
    priority: Priority
    status: ReminderStatus
    notification_channels: List[NotificationChannel]
    created_at: datetime
    
    def to_dict(self) -> dict:
        """转换为字典"""
        return {
            "id": self.id,
            "type": self.type.value,
            "title": self.title,
            "description": self.description,
            "due_date": self.due_date.isoformat(),
            "priority": self.priority.value,
            "status": self.status.value,
            "notification_channels": [ch.value for ch in self.notification_channels],
            "created_at": self.created_at.isoformat(),
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> "Reminder":
        """从字典创建"""
        return cls(
            id=data["id"],
            type=ReminderType(data["type"]),
            title=data["title"],
            description=data["description"],
            due_date=date.fromisoformat(data["due_date"]),
            priority=Priority(data["priority"]),
            status=ReminderStatus(data["status"]),
            notification_channels=[NotificationChannel(ch) for ch in data["notification_channels"]],
            created_at=datetime.fromisoformat(data["created_at"]),
        )


@dataclass
class BankRecord:
    """银行流水记录"""
    id: str
    transaction_date: date
    description: str
    amount: Decimal
    balance: Decimal
    transaction_type: str  # DEBIT, CREDIT
    counterparty: str
    
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
        )


@dataclass
class Discrepancy:
    """差异记录"""
    id: str
    type: DiscrepancyType
    bank_record: Optional[BankRecord]
    system_record: Optional[TransactionRecord]
    difference_amount: Decimal
    description: str
    
    def to_dict(self) -> dict:
        """转换为字典"""
        return {
            "id": self.id,
            "type": self.type.value,
            "bank_record": self.bank_record.to_dict() if self.bank_record else None,
            "system_record": self.system_record.to_dict() if self.system_record else None,
            "difference_amount": str(self.difference_amount),
            "description": self.description,
        }


@dataclass
class ReconciliationResult:
    """对账结果"""
    matched_count: int
    unmatched_bank_records: List[BankRecord]
    unmatched_system_records: List[TransactionRecord]
    discrepancies: List[Discrepancy]
    reconciliation_date: datetime
    
    def to_dict(self) -> dict:
        """转换为字典"""
        return {
            "matched_count": self.matched_count,
            "unmatched_bank_records": [r.to_dict() for r in self.unmatched_bank_records],
            "unmatched_system_records": [r.to_dict() for r in self.unmatched_system_records],
            "discrepancies": [d.to_dict() for d in self.discrepancies],
            "reconciliation_date": self.reconciliation_date.isoformat(),
        }


@dataclass
class DateRange:
    """日期范围"""
    start_date: date
    end_date: date
    
    def to_dict(self) -> dict:
        """转换为字典"""
        return {
            "start_date": self.start_date.isoformat(),
            "end_date": self.end_date.isoformat(),
        }


@dataclass
class ReportResult:
    """报表生成结果"""
    report_type: ReportType
    file_path: str
    generation_date: datetime
    data_period: DateRange
    success: bool
    error_message: Optional[str] = None
    
    def to_dict(self) -> dict:
        """转换为字典"""
        return {
            "report_type": self.report_type.value,
            "file_path": self.file_path,
            "generation_date": self.generation_date.isoformat(),
            "data_period": self.data_period.to_dict(),
            "success": self.success,
            "error_message": self.error_message,
        }


@dataclass
class ImportError:
    """导入错误"""
    row_number: int
    field: str
    error_message: str
    
    def to_dict(self) -> dict:
        """转换为字典"""
        return {
            "row_number": self.row_number,
            "field": self.field,
            "error_message": self.error_message,
        }


@dataclass
class ImportResult:
    """导入结果"""
    import_id: str
    total_rows: int
    successful_rows: int
    failed_rows: int
    errors: List[ImportError]
    import_date: datetime
    can_undo: bool
    
    def to_dict(self) -> dict:
        """转换为字典"""
        return {
            "import_id": self.import_id,
            "total_rows": self.total_rows,
            "successful_rows": self.successful_rows,
            "failed_rows": self.failed_rows,
            "errors": [e.to_dict() for e in self.errors],
            "import_date": self.import_date.isoformat(),
            "can_undo": self.can_undo,
        }


@dataclass
class ColumnMapping:
    """列映射"""
    source_columns: List[str]
    target_fields: Dict[str, str]
    confidence: float  # 识别置信度 (0.0 - 1.0)
    unmapped_columns: List[str] = field(default_factory=list)
    missing_required_fields: List[str] = field(default_factory=list)
    
    def to_dict(self) -> dict:
        """转换为字典"""
        return {
            "source_columns": self.source_columns,
            "target_fields": self.target_fields,
            "confidence": self.confidence,
            "unmapped_columns": self.unmapped_columns,
            "missing_required_fields": self.missing_required_fields,
        }


@dataclass
class ValidationError:
    """验证错误"""
    row_number: int
    field_name: str
    field_value: str
    error_message: str
    error_type: str  # 'missing', 'invalid_format', 'invalid_value', 'duplicate'
    
    def to_dict(self) -> dict:
        """转换为字典"""
        return {
            "row_number": self.row_number,
            "field_name": self.field_name,
            "field_value": self.field_value,
            "error_message": self.error_message,
            "error_type": self.error_type,
        }


@dataclass
class PreviewResult:
    """导入预览结果"""
    column_mapping: ColumnMapping
    sample_data: any  # pandas DataFrame or list of dicts
    validation_errors: List[ValidationError]
    estimated_rows: int
    
    def to_dict(self) -> dict:
        """转换为字典"""
        # Convert DataFrame to list of dicts if needed
        if hasattr(self.sample_data, 'to_dict'):
            sample_data_dict = self.sample_data.to_dict('records')
        else:
            sample_data_dict = self.sample_data
            
        return {
            "column_mapping": self.column_mapping.to_dict(),
            "sample_data": sample_data_dict,
            "validation_errors": [e.to_dict() for e in self.validation_errors],
            "estimated_rows": self.estimated_rows,
        }


# ============================================================================
# V1.7 Oxidation Factory Specific Models
# ============================================================================

@dataclass
class ProcessingOrder:
    """加工订单"""
    id: str
    order_number: str
    customer_id: str
    order_date: date
    product_name: str
    pricing_unit: PricingUnit
    quantity: Decimal
    unit_price: Decimal
    total_amount: Decimal
    status: OrderStatus
    received_amount: Decimal
    outsourced_cost: Decimal
    notes: str
    created_at: datetime
    updated_at: datetime
    
    def to_dict(self) -> dict:
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
    
    def calculate_total(self) -> Decimal:
        return self.quantity * self.unit_price
    
    def get_balance(self) -> Decimal:
        return self.total_amount - self.received_amount
    
    def get_profit(self) -> Decimal:
        return self.total_amount - self.outsourced_cost


@dataclass
class OutsourcedProcessing:
    """外发加工记录"""
    id: str
    order_id: str
    supplier_id: str
    process_type: ProcessType
    process_date: date
    quantity: Decimal
    unit_price: Decimal
    total_cost: Decimal
    notes: str
    created_at: datetime
    updated_at: datetime
    
    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "order_id": self.order_id,
            "supplier_id": self.supplier_id,
            "process_type": self.process_type.value,
            "process_date": self.process_date.isoformat(),
            "quantity": str(self.quantity),
            "unit_price": str(self.unit_price),
            "total_cost": str(self.total_cost),
            "notes": self.notes,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> "OutsourcedProcessing":
        return cls(
            id=data["id"],
            order_id=data["order_id"],
            supplier_id=data["supplier_id"],
            process_type=ProcessType(data["process_type"]),
            process_date=date.fromisoformat(data["process_date"]),
            quantity=Decimal(data["quantity"]),
            unit_price=Decimal(data["unit_price"]),
            total_cost=Decimal(data["total_cost"]),
            notes=data["notes"],
            created_at=datetime.fromisoformat(data["created_at"]),
            updated_at=datetime.fromisoformat(data["updated_at"]),
        )
    
    def calculate_total(self) -> Decimal:
        return self.quantity * self.unit_price


@dataclass
class BankAccount:
    """银行账户"""
    id: str
    name: str
    account_number: str
    account_type: AccountType
    has_invoice: bool
    balance: Decimal
    description: str
    created_at: datetime
    updated_at: datetime
    
    def to_dict(self) -> dict:
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
    """对账匹配记录"""
    id: str
    match_date: datetime
    bank_record_ids: List[str]
    order_ids: List[str]
    total_bank_amount: Decimal
    total_order_amount: Decimal
    difference: Decimal
    notes: str
    created_by: str
    created_at: datetime
    
    def to_dict(self) -> dict:
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
    
    def is_one_to_many(self) -> bool:
        return len(self.bank_record_ids) == 1 and len(self.order_ids) > 1
    
    def is_many_to_one(self) -> bool:
        return len(self.bank_record_ids) > 1 and len(self.order_ids) == 1
