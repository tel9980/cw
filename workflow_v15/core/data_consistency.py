"""
Data Consistency Manager for V1.5 Workflow System

This module ensures data consistency across all financial records by:
1. Automatically propagating changes to related records
2. Maintaining referential integrity
3. Real-time validation across modules
4. Automatic discrepancy detection and reconciliation

Requirements: 3.4, 9.1, 9.2, 9.3, 9.4, 9.5
"""

from typing import Dict, List, Optional, Any, Set, Callable
from datetime import datetime
from dataclasses import dataclass, field
from enum import Enum
import json
from pathlib import Path


class EntityType(Enum):
    """Entity types in the system"""
    TRANSACTION = "transaction"
    ORDER = "order"
    ENTITY = "entity"  # Customer/Supplier
    BANK_STATEMENT = "bank_statement"
    REPORT = "report"


class ChangeType(Enum):
    """Types of changes"""
    CREATE = "create"
    UPDATE = "update"
    DELETE = "delete"


@dataclass
class DataChange:
    """Represents a data change event"""
    entity_type: EntityType
    entity_id: str
    change_type: ChangeType
    field_name: Optional[str] = None
    old_value: Any = None
    new_value: Any = None
    timestamp: datetime = field(default_factory=datetime.now)
    propagated: bool = False


@dataclass
class ValidationRule:
    """Validation rule definition"""
    name: str
    entity_type: EntityType
    validator: Callable[[Any], tuple[bool, Optional[str]]]
    severity: str = "error"  # error, warning, info


@dataclass
class ConsistencyIssue:
    """Represents a data consistency issue"""
    issue_id: str
    entity_type: EntityType
    entity_id: str
    description: str
    severity: str
    detected_at: datetime = field(default_factory=datetime.now)
    resolved: bool = False
    auto_fixable: bool = False


class DataConsistencyManager:
    """
    Manages data consistency across all financial records.
    
    Features:
    - Automatic change propagation to related records
    - Real-time validation across modules
    - Referential integrity maintenance
    - Discrepancy detection and reconciliation
    """
    
    def __init__(self, storage_dir: Optional[Path] = None):
        """
        Initialize the data consistency manager.
        
        Args:
            storage_dir: Directory for storing consistency data
        """
        self.storage_dir = storage_dir or Path("财务数据/consistency")
        self.storage_dir.mkdir(parents=True, exist_ok=True)
        
        # Change tracking
        self.change_history: List[DataChange] = []
        self.pending_propagations: List[DataChange] = []
        
        # Validation rules
        self.validation_rules: Dict[EntityType, List[ValidationRule]] = {}
        self._register_default_rules()
        
        # Consistency issues
        self.issues: List[ConsistencyIssue] = []
        
        # Relationship mappings
        self.relationships: Dict[str, Set[str]] = {}
        
        # Load persisted data
        self._load_state()
    
    def _register_default_rules(self):
        """Register default validation rules"""
        # Transaction validation rules
        self.add_validation_rule(ValidationRule(
            name="transaction_amount_positive",
            entity_type=EntityType.TRANSACTION,
            validator=lambda t: (
                t.get("amount", 0) > 0,
                "交易金额必须大于0" if t.get("amount", 0) <= 0 else None
            )
        ))
        
        self.add_validation_rule(ValidationRule(
            name="transaction_has_date",
            entity_type=EntityType.TRANSACTION,
            validator=lambda t: (
                bool(t.get("date")),
                "交易必须有日期" if not t.get("date") else None
            )
        ))
        
        self.add_validation_rule(ValidationRule(
            name="transaction_has_entity",
            entity_type=EntityType.TRANSACTION,
            validator=lambda t: (
                bool(t.get("entity_id") or t.get("entity_name")),
                "交易必须关联往来单位" if not (t.get("entity_id") or t.get("entity_name")) else None
            )
        ))
        
        # Order validation rules
        self.add_validation_rule(ValidationRule(
            name="order_amount_positive",
            entity_type=EntityType.ORDER,
            validator=lambda o: (
                o.get("total_amount", 0) > 0,
                "订单金额必须大于0" if o.get("total_amount", 0) <= 0 else None
            )
        ))
        
        self.add_validation_rule(ValidationRule(
            name="order_paid_not_exceed_total",
            entity_type=EntityType.ORDER,
            validator=lambda o: (
                o.get("paid_amount", 0) <= o.get("total_amount", 0),
                f"已付金额({o.get('paid_amount', 0)})不能超过订单总额({o.get('total_amount', 0)})"
                if o.get("paid_amount", 0) > o.get("total_amount", 0) else None
            )
        ))
        
        # Entity validation rules
        self.add_validation_rule(ValidationRule(
            name="entity_has_name",
            entity_type=EntityType.ENTITY,
            validator=lambda e: (
                bool(e.get("name")),
                "往来单位必须有名称" if not e.get("name") else None
            )
        ))
    
    def add_validation_rule(self, rule: ValidationRule):
        """Add a validation rule"""
        if rule.entity_type not in self.validation_rules:
            self.validation_rules[rule.entity_type] = []
        self.validation_rules[rule.entity_type].append(rule)
    
    def record_change(
        self,
        entity_type: EntityType,
        entity_id: str,
        change_type: ChangeType,
        field_name: Optional[str] = None,
        old_value: Any = None,
        new_value: Any = None
    ) -> DataChange:
        """
        Record a data change event.
        
        Args:
            entity_type: Type of entity changed
            entity_id: ID of the entity
            change_type: Type of change
            field_name: Name of changed field (for updates)
            old_value: Previous value
            new_value: New value
            
        Returns:
            DataChange object
        """
        change = DataChange(
            entity_type=entity_type,
            entity_id=entity_id,
            change_type=change_type,
            field_name=field_name,
            old_value=old_value,
            new_value=new_value
        )
        
        self.change_history.append(change)
        self.pending_propagations.append(change)
        
        return change
    
    def propagate_changes(self, data_store: Dict[str, Any]) -> List[str]:
        """
        Propagate pending changes to related records.
        
        Args:
            data_store: Dictionary containing all data (transactions, orders, entities)
            
        Returns:
            List of propagation messages
        """
        messages = []
        
        for change in self.pending_propagations[:]:
            if change.propagated:
                continue
            
            # Propagate based on entity type and change type
            if change.entity_type == EntityType.ENTITY:
                msgs = self._propagate_entity_change(change, data_store)
                messages.extend(msgs)
            
            elif change.entity_type == EntityType.ORDER:
                msgs = self._propagate_order_change(change, data_store)
                messages.extend(msgs)
            
            elif change.entity_type == EntityType.TRANSACTION:
                msgs = self._propagate_transaction_change(change, data_store)
                messages.extend(msgs)
            
            change.propagated = True
            self.pending_propagations.remove(change)
        
        return messages
    
    def _propagate_entity_change(
        self,
        change: DataChange,
        data_store: Dict[str, Any]
    ) -> List[str]:
        """Propagate entity (customer/supplier) changes"""
        messages = []
        entity_id = change.entity_id
        
        # Update all transactions referencing this entity
        transactions = data_store.get("transactions", [])
        updated_count = 0
        
        for trans in transactions:
            if trans.get("entity_id") == entity_id:
                if change.field_name == "name" and change.new_value:
                    trans["entity_name"] = change.new_value
                    updated_count += 1
        
        if updated_count > 0:
            messages.append(f"更新了{updated_count}条交易记录的往来单位名称")
        
        # Update all orders referencing this entity
        orders = data_store.get("orders", [])
        updated_count = 0
        
        for order in orders:
            if order.get("customer_id") == entity_id:
                if change.field_name == "name" and change.new_value:
                    order["customer_name"] = change.new_value
                    updated_count += 1
        
        if updated_count > 0:
            messages.append(f"更新了{updated_count}个订单的客户名称")
        
        return messages
    
    def _propagate_order_change(
        self,
        change: DataChange,
        data_store: Dict[str, Any]
    ) -> List[str]:
        """Propagate order changes"""
        messages = []
        order_id = change.entity_id
        
        # If order amount changed, check related transactions
        if change.field_name in ["total_amount", "paid_amount"]:
            transactions = data_store.get("transactions", [])
            related_trans = [t for t in transactions if t.get("order_id") == order_id]
            
            if related_trans:
                total_paid = sum(t.get("amount", 0) for t in related_trans)
                orders = data_store.get("orders", [])
                order = next((o for o in orders if o.get("id") == order_id), None)
                
                if order and abs(total_paid - order.get("paid_amount", 0)) > 0.01:
                    messages.append(
                        f"订单{order_id}的已付金额({order.get('paid_amount', 0)})与"
                        f"关联交易总额({total_paid})不一致"
                    )
        
        return messages
    
    def _propagate_transaction_change(
        self,
        change: DataChange,
        data_store: Dict[str, Any]
    ) -> List[str]:
        """Propagate transaction changes"""
        messages = []
        
        # If transaction is linked to an order, update order paid amount
        transactions = data_store.get("transactions", [])
        trans = next((t for t in transactions if t.get("id") == change.entity_id), None)
        
        if trans and trans.get("order_id"):
            order_id = trans["order_id"]
            orders = data_store.get("orders", [])
            order = next((o for o in orders if o.get("id") == order_id), None)
            
            if order:
                # Recalculate total paid amount for this order
                related_trans = [t for t in transactions if t.get("order_id") == order_id]
                total_paid = sum(t.get("amount", 0) for t in related_trans)
                
                old_paid = order.get("paid_amount", 0)
                if abs(total_paid - old_paid) > 0.01:
                    order["paid_amount"] = total_paid
                    order["balance"] = order.get("total_amount", 0) - total_paid
                    messages.append(
                        f"订单{order_id}已付金额从{old_paid}更新为{total_paid}"
                    )
        
        return messages
    
    def validate_entity(
        self,
        entity_type: EntityType,
        entity_data: Dict[str, Any]
    ) -> tuple[bool, List[str]]:
        """
        Validate an entity against all applicable rules.
        
        Args:
            entity_type: Type of entity to validate
            entity_data: Entity data dictionary
            
        Returns:
            Tuple of (is_valid, list of error messages)
        """
        errors = []
        
        rules = self.validation_rules.get(entity_type, [])
        for rule in rules:
            is_valid, error_msg = rule.validator(entity_data)
            if not is_valid and error_msg:
                errors.append(f"[{rule.name}] {error_msg}")
        
        return len(errors) == 0, errors
    
    def validate_all(
        self,
        data_store: Dict[str, Any]
    ) -> Dict[EntityType, List[tuple[str, List[str]]]]:
        """
        Validate all entities in the data store.
        
        Args:
            data_store: Dictionary containing all data
            
        Returns:
            Dictionary mapping entity types to lists of (entity_id, errors)
        """
        validation_results = {}
        
        # Validate transactions
        transactions = data_store.get("transactions", [])
        trans_errors = []
        for trans in transactions:
            is_valid, errors = self.validate_entity(EntityType.TRANSACTION, trans)
            if not is_valid:
                trans_errors.append((trans.get("id", "unknown"), errors))
        if trans_errors:
            validation_results[EntityType.TRANSACTION] = trans_errors
        
        # Validate orders
        orders = data_store.get("orders", [])
        order_errors = []
        for order in orders:
            is_valid, errors = self.validate_entity(EntityType.ORDER, order)
            if not is_valid:
                order_errors.append((order.get("id", "unknown"), errors))
        if order_errors:
            validation_results[EntityType.ORDER] = order_errors
        
        # Validate entities
        entities = data_store.get("entities", {})
        entity_errors = []
        for entity_id, entity_data in entities.items():
            is_valid, errors = self.validate_entity(EntityType.ENTITY, entity_data)
            if not is_valid:
                entity_errors.append((entity_id, errors))
        if entity_errors:
            validation_results[EntityType.ENTITY] = entity_errors
        
        return validation_results
    
    def detect_discrepancies(
        self,
        data_store: Dict[str, Any]
    ) -> List[ConsistencyIssue]:
        """
        Detect data discrepancies and inconsistencies.
        
        Args:
            data_store: Dictionary containing all data
            
        Returns:
            List of consistency issues found
        """
        issues = []
        
        # Check order-transaction consistency
        orders = data_store.get("orders", [])
        transactions = data_store.get("transactions", [])
        
        for order in orders:
            order_id = order.get("id")
            if not order_id:
                continue
            
            # Find all transactions for this order
            order_trans = [t for t in transactions if t.get("order_id") == order_id]
            trans_total = sum(t.get("amount", 0) for t in order_trans)
            order_paid = order.get("paid_amount", 0)
            
            if abs(trans_total - order_paid) > 0.01:
                issue = ConsistencyIssue(
                    issue_id=f"order_trans_mismatch_{order_id}",
                    entity_type=EntityType.ORDER,
                    entity_id=order_id,
                    description=(
                        f"订单{order_id}的已付金额({order_paid})与"
                        f"关联交易总额({trans_total})不一致，差额{abs(trans_total - order_paid)}"
                    ),
                    severity="warning",
                    auto_fixable=True
                )
                issues.append(issue)
        
        # Check entity references
        entity_ids = set(data_store.get("entities", {}).keys())
        
        for trans in transactions:
            entity_id = trans.get("entity_id")
            if entity_id and entity_id not in entity_ids:
                issue = ConsistencyIssue(
                    issue_id=f"trans_entity_missing_{trans.get('id')}",
                    entity_type=EntityType.TRANSACTION,
                    entity_id=trans.get("id", "unknown"),
                    description=f"交易引用的往来单位{entity_id}不存在",
                    severity="error",
                    auto_fixable=False
                )
                issues.append(issue)
        
        self.issues.extend(issues)
        return issues
    
    def auto_fix_discrepancies(
        self,
        data_store: Dict[str, Any],
        issues: Optional[List[ConsistencyIssue]] = None
    ) -> List[str]:
        """
        Automatically fix discrepancies that can be auto-fixed.
        
        Args:
            data_store: Dictionary containing all data
            issues: List of issues to fix (if None, uses self.issues)
            
        Returns:
            List of fix messages
        """
        messages = []
        issues_to_fix = issues or self.issues
        
        for issue in issues_to_fix:
            if not issue.auto_fixable or issue.resolved:
                continue
            
            if issue.entity_type == EntityType.ORDER:
                # Fix order-transaction mismatch
                order_id = issue.entity_id
                orders = data_store.get("orders", [])
                order = next((o for o in orders if o.get("id") == order_id), None)
                
                if order:
                    transactions = data_store.get("transactions", [])
                    order_trans = [t for t in transactions if t.get("order_id") == order_id]
                    trans_total = sum(t.get("amount", 0) for t in order_trans)
                    
                    old_paid = order.get("paid_amount", 0)
                    order["paid_amount"] = trans_total
                    order["balance"] = order.get("total_amount", 0) - trans_total
                    
                    issue.resolved = True
                    messages.append(
                        f"已修复订单{order_id}：已付金额从{old_paid}更新为{trans_total}"
                    )
        
        return messages
    
    def get_related_entities(
        self,
        entity_type: EntityType,
        entity_id: str,
        data_store: Dict[str, Any]
    ) -> Dict[EntityType, List[str]]:
        """
        Get all entities related to a given entity.
        
        Args:
            entity_type: Type of the source entity
            entity_id: ID of the source entity
            data_store: Dictionary containing all data
            
        Returns:
            Dictionary mapping entity types to lists of related entity IDs
        """
        related = {}
        
        if entity_type == EntityType.ENTITY:
            # Find all transactions and orders for this entity
            transactions = data_store.get("transactions", [])
            related_trans = [t.get("id") for t in transactions if t.get("entity_id") == entity_id]
            if related_trans:
                related[EntityType.TRANSACTION] = related_trans
            
            orders = data_store.get("orders", [])
            related_orders = [o.get("id") for o in orders if o.get("customer_id") == entity_id]
            if related_orders:
                related[EntityType.ORDER] = related_orders
        
        elif entity_type == EntityType.ORDER:
            # Find all transactions for this order
            transactions = data_store.get("transactions", [])
            related_trans = [t.get("id") for t in transactions if t.get("order_id") == entity_id]
            if related_trans:
                related[EntityType.TRANSACTION] = related_trans
        
        return related
    
    def _load_state(self):
        """Load persisted consistency state"""
        state_file = self.storage_dir / "consistency_state.json"
        if state_file.exists():
            try:
                with open(state_file, 'r', encoding='utf-8') as f:
                    state = json.load(f)
                    # Load issues
                    for issue_data in state.get("issues", []):
                        issue = ConsistencyIssue(
                            issue_id=issue_data["issue_id"],
                            entity_type=EntityType(issue_data["entity_type"]),
                            entity_id=issue_data["entity_id"],
                            description=issue_data["description"],
                            severity=issue_data["severity"],
                            detected_at=datetime.fromisoformat(issue_data["detected_at"]),
                            resolved=issue_data["resolved"],
                            auto_fixable=issue_data["auto_fixable"]
                        )
                        self.issues.append(issue)
            except Exception as e:
                print(f"加载一致性状态失败: {e}")
    
    def save_state(self):
        """Save consistency state to disk"""
        state_file = self.storage_dir / "consistency_state.json"
        try:
            state = {
                "issues": [
                    {
                        "issue_id": issue.issue_id,
                        "entity_type": issue.entity_type.value,
                        "entity_id": issue.entity_id,
                        "description": issue.description,
                        "severity": issue.severity,
                        "detected_at": issue.detected_at.isoformat(),
                        "resolved": issue.resolved,
                        "auto_fixable": issue.auto_fixable
                    }
                    for issue in self.issues
                ],
                "last_updated": datetime.now().isoformat()
            }
            
            with open(state_file, 'w', encoding='utf-8') as f:
                json.dump(state, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"保存一致性状态失败: {e}")
