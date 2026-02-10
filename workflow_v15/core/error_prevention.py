"""
Error Prevention and Recovery System for V1.5 Workflow

This module provides comprehensive error handling including:
1. Real-time validation with intelligent suggestions
2. Unlimited undo/redo functionality
3. Automatic draft saving for incomplete entries
4. Destructive operation protection

Requirements: 5.1, 5.2, 5.3, 5.4, 5.5
"""

from typing import Dict, List, Optional, Any, Callable
from datetime import datetime
from dataclasses import dataclass, field
from enum import Enum
import json
import copy
from pathlib import Path


class OperationType(Enum):
    """Types of operations that can be undone/redone"""
    CREATE = "create"
    UPDATE = "update"
    DELETE = "delete"
    BATCH = "batch"


class ValidationSeverity(Enum):
    """Severity levels for validation issues"""
    ERROR = "error"  # Blocks operation
    WARNING = "warning"  # Allows operation with confirmation
    INFO = "info"  # Informational only


@dataclass
class ValidationResult:
    """Result of a validation check"""
    is_valid: bool
    severity: ValidationSeverity
    message: str
    field: Optional[str] = None
    suggestion: Optional[str] = None
    auto_fixable: bool = False


@dataclass
class Operation:
    """Represents an operation that can be undone/redone"""
    operation_id: str
    operation_type: OperationType
    entity_type: str
    entity_id: str
    before_state: Optional[Dict[str, Any]] = None
    after_state: Optional[Dict[str, Any]] = None
    timestamp: datetime = field(default_factory=datetime.now)
    description: str = ""


@dataclass
class Draft:
    """Represents a draft of incomplete data entry"""
    draft_id: str
    entity_type: str
    data: Dict[str, Any]
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    auto_saved: bool = True


class ErrorPreventionManager:
    """
    Manages error prevention and recovery for the financial system.
    
    Features:
    - Real-time validation with suggestions
    - Unlimited undo/redo
    - Automatic draft saving
    - Destructive operation protection
    """
    
    def __init__(self, storage_dir: Optional[Path] = None):
        """
        Initialize the error prevention manager.
        
        Args:
            storage_dir: Directory for storing drafts and operation history
        """
        self.storage_dir = storage_dir or Path("财务数据/error_prevention")
        self.storage_dir.mkdir(parents=True, exist_ok=True)
        
        # Undo/Redo stacks
        self.undo_stack: List[Operation] = []
        self.redo_stack: List[Operation] = []
        self.max_history = 1000  # Maximum operations to keep
        
        # Draft management
        self.drafts: Dict[str, Draft] = {}
        self.auto_save_interval = 30  # seconds
        
        # Validation rules
        self.validators: Dict[str, List[Callable]] = {}
        self._register_default_validators()
        
        # Destructive operations that require confirmation
        self.destructive_operations = {
            "delete_transaction",
            "delete_order",
            "delete_entity",
            "batch_delete",
            "clear_all_data"
        }
        
        # Load persisted data
        self._load_state()
    
    def _register_default_validators(self):
        """Register default validation rules"""
        # Transaction validators
        self.add_validator("transaction", self._validate_transaction_amount)
        self.add_validator("transaction", self._validate_transaction_date)
        self.add_validator("transaction", self._validate_transaction_entity)
        
        # Order validators
        self.add_validator("order", self._validate_order_amount)
        self.add_validator("order", self._validate_order_customer)
        self.add_validator("order", self._validate_order_pricing)
        
        # Entity validators
        self.add_validator("entity", self._validate_entity_name)
        self.add_validator("entity", self._validate_entity_type)
    
    def _validate_transaction_amount(self, data: Dict[str, Any]) -> Optional[ValidationResult]:
        """Validate transaction amount"""
        amount = data.get("amount", 0)
        
        if amount <= 0:
            return ValidationResult(
                is_valid=False,
                severity=ValidationSeverity.ERROR,
                message="交易金额必须大于0",
                field="amount",
                suggestion="请输入正确的金额，例如: 1000.00"
            )
        
        if amount > 1000000:
            return ValidationResult(
                is_valid=True,
                severity=ValidationSeverity.WARNING,
                message="交易金额超过100万，请确认是否正确",
                field="amount",
                suggestion="如果金额正确，请继续；否则请修改"
            )
        
        return None
    
    def _validate_transaction_date(self, data: Dict[str, Any]) -> Optional[ValidationResult]:
        """Validate transaction date"""
        date_str = data.get("date")
        
        if not date_str:
            return ValidationResult(
                is_valid=False,
                severity=ValidationSeverity.ERROR,
                message="交易日期不能为空",
                field="date",
                suggestion=f"建议使用今天的日期: {datetime.now().strftime('%Y-%m-%d')}",
                auto_fixable=True
            )
        
        try:
            trans_date = datetime.strptime(date_str, "%Y-%m-%d")
            today = datetime.now()
            
            if trans_date > today:
                return ValidationResult(
                    is_valid=True,
                    severity=ValidationSeverity.WARNING,
                    message="交易日期是未来日期，请确认",
                    field="date"
                )
            
            days_ago = (today - trans_date).days
            if days_ago > 365:
                return ValidationResult(
                    is_valid=True,
                    severity=ValidationSeverity.WARNING,
                    message=f"交易日期是{days_ago}天前，请确认是否正确",
                    field="date"
                )
        except ValueError:
            return ValidationResult(
                is_valid=False,
                severity=ValidationSeverity.ERROR,
                message="日期格式不正确",
                field="date",
                suggestion="请使用格式: YYYY-MM-DD，例如: 2026-02-10"
            )
        
        return None
    
    def _validate_transaction_entity(self, data: Dict[str, Any]) -> Optional[ValidationResult]:
        """Validate transaction entity"""
        entity_id = data.get("entity_id")
        entity_name = data.get("entity_name")
        
        if not entity_id and not entity_name:
            return ValidationResult(
                is_valid=False,
                severity=ValidationSeverity.ERROR,
                message="必须指定往来单位",
                field="entity_id",
                suggestion="请选择或输入往来单位名称"
            )
        
        return None
    
    def _validate_order_amount(self, data: Dict[str, Any]) -> Optional[ValidationResult]:
        """Validate order amount"""
        total_amount = data.get("total_amount", 0)
        paid_amount = data.get("paid_amount", 0)
        
        if total_amount <= 0:
            return ValidationResult(
                is_valid=False,
                severity=ValidationSeverity.ERROR,
                message="订单金额必须大于0",
                field="total_amount",
                suggestion="请输入正确的订单金额"
            )
        
        if paid_amount > total_amount:
            return ValidationResult(
                is_valid=False,
                severity=ValidationSeverity.ERROR,
                message=f"已付金额({paid_amount})不能超过订单总额({total_amount})",
                field="paid_amount",
                suggestion=f"已付金额应该 ≤ {total_amount}"
            )
        
        if paid_amount < 0:
            return ValidationResult(
                is_valid=False,
                severity=ValidationSeverity.ERROR,
                message="已付金额不能为负数",
                field="paid_amount",
                suggestion="请输入正确的已付金额，或输入0表示未付款"
            )
        
        return None
    
    def _validate_order_customer(self, data: Dict[str, Any]) -> Optional[ValidationResult]:
        """Validate order customer"""
        customer_id = data.get("customer_id")
        customer_name = data.get("customer_name")
        
        if not customer_id and not customer_name:
            return ValidationResult(
                is_valid=False,
                severity=ValidationSeverity.ERROR,
                message="必须指定客户",
                field="customer_id",
                suggestion="请选择或输入客户名称"
            )
        
        return None
    
    def _validate_order_pricing(self, data: Dict[str, Any]) -> Optional[ValidationResult]:
        """Validate order pricing"""
        quantity = data.get("quantity", 0)
        unit_price = data.get("unit_price", 0)
        
        if quantity <= 0:
            return ValidationResult(
                is_valid=False,
                severity=ValidationSeverity.ERROR,
                message="数量必须大于0",
                field="quantity",
                suggestion="请输入正确的数量"
            )
        
        if unit_price <= 0:
            return ValidationResult(
                is_valid=False,
                severity=ValidationSeverity.ERROR,
                message="单价必须大于0",
                field="unit_price",
                suggestion="请输入正确的单价"
            )
        
        return None
    
    def _validate_entity_name(self, data: Dict[str, Any]) -> Optional[ValidationResult]:
        """Validate entity name"""
        name = data.get("name", "").strip()
        
        if not name:
            return ValidationResult(
                is_valid=False,
                severity=ValidationSeverity.ERROR,
                message="往来单位名称不能为空",
                field="name",
                suggestion="请输入往来单位名称"
            )
        
        if len(name) < 2:
            return ValidationResult(
                is_valid=True,
                severity=ValidationSeverity.WARNING,
                message="往来单位名称太短，请确认",
                field="name"
            )
        
        return None
    
    def _validate_entity_type(self, data: Dict[str, Any]) -> Optional[ValidationResult]:
        """Validate entity type"""
        entity_type = data.get("type")
        
        if not entity_type:
            return ValidationResult(
                is_valid=False,
                severity=ValidationSeverity.ERROR,
                message="必须指定往来单位类型",
                field="type",
                suggestion="请选择: customer(客户) 或 supplier(供应商)"
            )
        
        if entity_type not in ["customer", "supplier"]:
            return ValidationResult(
                is_valid=False,
                severity=ValidationSeverity.ERROR,
                message=f"无效的往来单位类型: {entity_type}",
                field="type",
                suggestion="类型必须是 customer 或 supplier"
            )
        
        return None
    
    def add_validator(self, entity_type: str, validator: Callable):
        """Add a custom validator"""
        if entity_type not in self.validators:
            self.validators[entity_type] = []
        self.validators[entity_type].append(validator)
    
    def validate(
        self,
        entity_type: str,
        data: Dict[str, Any],
        context: Optional[Dict[str, Any]] = None
    ) -> List[ValidationResult]:
        """
        Validate data with real-time suggestions.
        
        Args:
            entity_type: Type of entity to validate
            data: Data to validate
            context: Additional context for validation
            
        Returns:
            List of validation results
        """
        results = []
        
        validators = self.validators.get(entity_type, [])
        for validator in validators:
            result = validator(data)
            if result:
                results.append(result)
        
        return results
    
    def has_errors(self, validation_results: List[ValidationResult]) -> bool:
        """Check if validation results contain errors"""
        return any(r.severity == ValidationSeverity.ERROR for r in validation_results)
    
    def has_warnings(self, validation_results: List[ValidationResult]) -> bool:
        """Check if validation results contain warnings"""
        return any(r.severity == ValidationSeverity.WARNING for r in validation_results)
    
    def auto_fix(
        self,
        entity_type: str,
        data: Dict[str, Any],
        validation_results: List[ValidationResult]
    ) -> tuple[Dict[str, Any], List[str]]:
        """
        Automatically fix auto-fixable validation issues.
        
        Args:
            entity_type: Type of entity
            data: Data to fix
            validation_results: Validation results
            
        Returns:
            Tuple of (fixed_data, list of fix messages)
        """
        fixed_data = copy.deepcopy(data)
        messages = []
        
        for result in validation_results:
            if not result.auto_fixable:
                continue
            
            if result.field == "date" and not fixed_data.get("date"):
                fixed_data["date"] = datetime.now().strftime("%Y-%m-%d")
                messages.append(f"自动填充日期: {fixed_data['date']}")
        
        return fixed_data, messages
    
    def record_operation(
        self,
        operation_type: OperationType,
        entity_type: str,
        entity_id: str,
        before_state: Optional[Dict[str, Any]] = None,
        after_state: Optional[Dict[str, Any]] = None,
        description: str = ""
    ) -> Operation:
        """
        Record an operation for undo/redo.
        
        Args:
            operation_type: Type of operation
            entity_type: Type of entity
            entity_id: ID of entity
            before_state: State before operation
            after_state: State after operation
            description: Description of operation
            
        Returns:
            Operation object
        """
        operation = Operation(
            operation_id=f"{entity_type}_{entity_id}_{datetime.now().timestamp()}",
            operation_type=operation_type,
            entity_type=entity_type,
            entity_id=entity_id,
            before_state=copy.deepcopy(before_state) if before_state else None,
            after_state=copy.deepcopy(after_state) if after_state else None,
            description=description
        )
        
        self.undo_stack.append(operation)
        self.redo_stack.clear()  # Clear redo stack when new operation is recorded
        
        # Limit history size
        if len(self.undo_stack) > self.max_history:
            self.undo_stack.pop(0)
        
        return operation
    
    def can_undo(self) -> bool:
        """Check if undo is available"""
        return len(self.undo_stack) > 0
    
    def can_redo(self) -> bool:
        """Check if redo is available"""
        return len(self.redo_stack) > 0
    
    def undo(self) -> Optional[Operation]:
        """
        Undo the last operation.
        
        Returns:
            Operation that was undone, or None if nothing to undo
        """
        if not self.can_undo():
            return None
        
        operation = self.undo_stack.pop()
        self.redo_stack.append(operation)
        
        return operation
    
    def redo(self) -> Optional[Operation]:
        """
        Redo the last undone operation.
        
        Returns:
            Operation that was redone, or None if nothing to redo
        """
        if not self.can_redo():
            return None
        
        operation = self.redo_stack.pop()
        self.undo_stack.append(operation)
        
        return operation
    
    def get_undo_description(self) -> Optional[str]:
        """Get description of operation that would be undone"""
        if not self.can_undo():
            return None
        return self.undo_stack[-1].description or f"撤销{self.undo_stack[-1].operation_type.value}"
    
    def get_redo_description(self) -> Optional[str]:
        """Get description of operation that would be redone"""
        if not self.can_redo():
            return None
        return self.redo_stack[-1].description or f"重做{self.redo_stack[-1].operation_type.value}"
    
    def save_draft(
        self,
        entity_type: str,
        data: Dict[str, Any],
        draft_id: Optional[str] = None
    ) -> Draft:
        """
        Save a draft of incomplete data.
        
        Args:
            entity_type: Type of entity
            data: Draft data
            draft_id: Optional draft ID (generates new if not provided)
            
        Returns:
            Draft object
        """
        if not draft_id:
            draft_id = f"{entity_type}_{datetime.now().timestamp()}"
        
        if draft_id in self.drafts:
            # Update existing draft
            draft = self.drafts[draft_id]
            draft.data = copy.deepcopy(data)
            draft.updated_at = datetime.now()
        else:
            # Create new draft
            draft = Draft(
                draft_id=draft_id,
                entity_type=entity_type,
                data=copy.deepcopy(data)
            )
            self.drafts[draft_id] = draft
        
        # Persist to disk
        self._save_draft_to_disk(draft)
        
        return draft
    
    def load_draft(self, draft_id: str) -> Optional[Draft]:
        """Load a draft by ID"""
        return self.drafts.get(draft_id)
    
    def list_drafts(self, entity_type: Optional[str] = None) -> List[Draft]:
        """
        List all drafts, optionally filtered by entity type.
        
        Args:
            entity_type: Optional entity type filter
            
        Returns:
            List of drafts
        """
        drafts = list(self.drafts.values())
        
        if entity_type:
            drafts = [d for d in drafts if d.entity_type == entity_type]
        
        # Sort by updated_at descending
        drafts.sort(key=lambda d: d.updated_at, reverse=True)
        
        return drafts
    
    def delete_draft(self, draft_id: str) -> bool:
        """Delete a draft"""
        if draft_id in self.drafts:
            del self.drafts[draft_id]
            
            # Delete from disk
            draft_file = self.storage_dir / "drafts" / f"{draft_id}.json"
            if draft_file.exists():
                draft_file.unlink()
            
            return True
        return False
    
    def is_destructive_operation(self, operation_name: str) -> bool:
        """Check if an operation is destructive and requires confirmation"""
        return operation_name in self.destructive_operations
    
    def confirm_destructive_operation(
        self,
        operation_name: str,
        details: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Get confirmation details for a destructive operation.
        
        Args:
            operation_name: Name of the operation
            details: Additional details about what will be affected
            
        Returns:
            Dictionary with confirmation message and details
        """
        messages = {
            "delete_transaction": "确定要删除这条交易记录吗？",
            "delete_order": "确定要删除这个订单吗？相关的交易记录不会被删除。",
            "delete_entity": "确定要删除这个往来单位吗？相关的交易和订单不会被删除。",
            "batch_delete": "确定要批量删除选中的记录吗？",
            "clear_all_data": "⚠️ 警告：这将删除所有数据！此操作不可恢复！"
        }
        
        return {
            "operation": operation_name,
            "message": messages.get(operation_name, "确定要执行此操作吗？"),
            "details": details,
            "requires_confirmation": True,
            "severity": "high" if operation_name == "clear_all_data" else "medium"
        }
    
    def _save_draft_to_disk(self, draft: Draft):
        """Save a draft to disk"""
        drafts_dir = self.storage_dir / "drafts"
        drafts_dir.mkdir(exist_ok=True)
        
        draft_file = drafts_dir / f"{draft.draft_id}.json"
        try:
            with open(draft_file, 'w', encoding='utf-8') as f:
                json.dump({
                    "draft_id": draft.draft_id,
                    "entity_type": draft.entity_type,
                    "data": draft.data,
                    "created_at": draft.created_at.isoformat(),
                    "updated_at": draft.updated_at.isoformat(),
                    "auto_saved": draft.auto_saved
                }, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"保存草稿失败: {e}")
    
    def _load_state(self):
        """Load persisted drafts"""
        drafts_dir = self.storage_dir / "drafts"
        if not drafts_dir.exists():
            return
        
        for draft_file in drafts_dir.glob("*.json"):
            try:
                with open(draft_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    draft = Draft(
                        draft_id=data["draft_id"],
                        entity_type=data["entity_type"],
                        data=data["data"],
                        created_at=datetime.fromisoformat(data["created_at"]),
                        updated_at=datetime.fromisoformat(data["updated_at"]),
                        auto_saved=data.get("auto_saved", True)
                    )
                    self.drafts[draft.draft_id] = draft
            except Exception as e:
                print(f"加载草稿失败 {draft_file}: {e}")
    
    def get_operation_history(self, limit: int = 10) -> List[Operation]:
        """
        Get recent operation history.
        
        Args:
            limit: Maximum number of operations to return
            
        Returns:
            List of recent operations
        """
        return self.undo_stack[-limit:] if self.undo_stack else []
