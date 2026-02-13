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
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> "TransactionRecord":
        """从字典创建"""
        # 处理日期字段 - 可能是date或datetime格式
        date_str = data["date"]
        if 'T' in date_str:
            # datetime格式，提取日期部分
            trans_date = datetime.fromisoformat(date_str).date()
        else:
            # date格式
            trans_date = date.fromisoformat(date_str)
        
        return cls(
            id=data["id"],
            date=trans_date,
            type=TransactionType(data["type"]),
            amount=Decimal(data["amount"]),
            counterparty_id=data["counterparty_id"],
            description=data["description"],
            category=data["category"],
            status=TransactionStatus(data["status"]),
            created_at=datetime.fromisoformat(data["created_at"]),
            updated_at=datetime.fromisoformat(data["updated_at"]),
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
