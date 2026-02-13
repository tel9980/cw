"""
Unit tests for Data Consistency Manager

Tests cover:
- Change recording and propagation
- Validation rules
- Discrepancy detection
- Auto-fix capabilities
- Related entity tracking
"""

import pytest
from datetime import datetime
from pathlib import Path
import tempfile
import shutil

from workflow_v15.core.data_consistency import (
    DataConsistencyManager,
    EntityType,
    ChangeType,
    DataChange,
    ValidationRule,
    ConsistencyIssue
)


@pytest.fixture
def temp_dir():
    """Create a temporary directory for testing"""
    temp_path = Path(tempfile.mkdtemp())
    yield temp_path
    shutil.rmtree(temp_path)


@pytest.fixture
def consistency_manager(temp_dir):
    """Create a consistency manager for testing"""
    return DataConsistencyManager(storage_dir=temp_dir / "consistency")


@pytest.fixture
def sample_data():
    """Create sample data for testing"""
    return {
        "entities": {
            "customer_001": {
                "id": "customer_001",
                "name": "京东办公用品",
                "type": "customer"
            },
            "supplier_001": {
                "id": "supplier_001",
                "name": "三酸供应商",
                "type": "supplier"
            }
        },
        "orders": [
            {
                "id": "order_001",
                "customer_id": "customer_001",
                "customer_name": "京东办公用品",
                "total_amount": 10000.0,
                "paid_amount": 5000.0,
                "balance": 5000.0
            },
            {
                "id": "order_002",
                "customer_id": "customer_001",
                "customer_name": "京东办公用品",
                "total_amount": 8000.0,
                "paid_amount": 8000.0,
                "balance": 0.0
            }
        ],
        "transactions": [
            {
                "id": "trans_001",
                "date": "2026-02-01",
                "entity_id": "customer_001",
                "entity_name": "京东办公用品",
                "order_id": "order_001",
                "amount": 3000.0,
                "type": "income"
            },
            {
                "id": "trans_002",
                "date": "2026-02-05",
                "entity_id": "customer_001",
                "entity_name": "京东办公用品",
                "order_id": "order_001",
                "amount": 2000.0,
                "type": "income"
            },
            {
                "id": "trans_003",
                "date": "2026-02-10",
                "entity_id": "supplier_001",
                "entity_name": "三酸供应商",
                "amount": 1500.0,
                "type": "expense"
            }
        ]
    }


class TestDataConsistencyManager:
    """Test suite for DataConsistencyManager"""
    
    def test_initialization(self, consistency_manager):
        """Test manager initialization"""
        assert consistency_manager is not None
        assert consistency_manager.storage_dir.exists()
        assert len(consistency_manager.validation_rules) > 0
        assert EntityType.TRANSACTION in consistency_manager.validation_rules
        assert EntityType.ORDER in consistency_manager.validation_rules
    
    def test_record_change(self, consistency_manager):
        """Test recording a data change"""
        change = consistency_manager.record_change(
            entity_type=EntityType.ENTITY,
            entity_id="customer_001",
            change_type=ChangeType.UPDATE,
            field_name="name",
            old_value="旧名称",
            new_value="新名称"
        )
        
        assert change is not None
        assert change.entity_type == EntityType.ENTITY
        assert change.entity_id == "customer_001"
        assert change.change_type == ChangeType.UPDATE
        assert change.field_name == "name"
        assert change.old_value == "旧名称"
        assert change.new_value == "新名称"
        assert not change.propagated
        
        assert len(consistency_manager.change_history) == 1
        assert len(consistency_manager.pending_propagations) == 1
    
    def test_propagate_entity_name_change(self, consistency_manager, sample_data):
        """Test propagating entity name changes to transactions and orders"""
        # Record entity name change
        consistency_manager.record_change(
            entity_type=EntityType.ENTITY,
            entity_id="customer_001",
            change_type=ChangeType.UPDATE,
            field_name="name",
            old_value="京东办公用品",
            new_value="京东办公用品（新）"
        )
        
        # Propagate changes
        messages = consistency_manager.propagate_changes(sample_data)
        
        assert len(messages) == 2  # One for transactions, one for orders
        assert "交易记录" in messages[0]
        assert "订单" in messages[1]
        
        # Verify transactions updated
        for trans in sample_data["transactions"]:
            if trans["entity_id"] == "customer_001":
                assert trans["entity_name"] == "京东办公用品（新）"
        
        # Verify orders updated
        for order in sample_data["orders"]:
            if order["customer_id"] == "customer_001":
                assert order["customer_name"] == "京东办公用品（新）"
    
    def test_propagate_transaction_to_order(self, consistency_manager, sample_data):
        """Test propagating transaction changes to order paid amount"""
        # Add a new transaction for order_001
        new_trans = {
            "id": "trans_004",
            "date": "2026-02-15",
            "entity_id": "customer_001",
            "entity_name": "京东办公用品",
            "order_id": "order_001",
            "amount": 1000.0,
            "type": "income"
        }
        sample_data["transactions"].append(new_trans)
        
        # Record the change
        consistency_manager.record_change(
            entity_type=EntityType.TRANSACTION,
            entity_id="trans_004",
            change_type=ChangeType.CREATE
        )
        
        # Propagate changes
        messages = consistency_manager.propagate_changes(sample_data)
        
        # Verify order paid amount updated
        order = next(o for o in sample_data["orders"] if o["id"] == "order_001")
        expected_paid = 3000.0 + 2000.0 + 1000.0  # Sum of all transactions
        assert order["paid_amount"] == expected_paid
        assert order["balance"] == order["total_amount"] - expected_paid
        
        assert len(messages) > 0
        assert "order_001" in messages[0]
    
    def test_validate_transaction_positive_amount(self, consistency_manager):
        """Test transaction amount validation"""
        # Valid transaction
        valid_trans = {
            "id": "trans_001",
            "date": "2026-02-01",
            "entity_id": "customer_001",
            "amount": 1000.0
        }
        is_valid, errors = consistency_manager.validate_entity(
            EntityType.TRANSACTION,
            valid_trans
        )
        assert is_valid
        assert len(errors) == 0
        
        # Invalid transaction (negative amount)
        invalid_trans = {
            "id": "trans_002",
            "date": "2026-02-01",
            "entity_id": "customer_001",
            "amount": -100.0
        }
        is_valid, errors = consistency_manager.validate_entity(
            EntityType.TRANSACTION,
            invalid_trans
        )
        assert not is_valid
        assert len(errors) > 0
        assert "金额必须大于0" in errors[0]
    
    def test_validate_transaction_has_date(self, consistency_manager):
        """Test transaction date validation"""
        # Missing date
        trans = {
            "id": "trans_001",
            "entity_id": "customer_001",
            "amount": 1000.0
        }
        is_valid, errors = consistency_manager.validate_entity(
            EntityType.TRANSACTION,
            trans
        )
        assert not is_valid
        assert any("日期" in err for err in errors)
    
    def test_validate_transaction_has_entity(self, consistency_manager):
        """Test transaction entity validation"""
        # Missing entity
        trans = {
            "id": "trans_001",
            "date": "2026-02-01",
            "amount": 1000.0
        }
        is_valid, errors = consistency_manager.validate_entity(
            EntityType.TRANSACTION,
            trans
        )
        assert not is_valid
        assert any("往来单位" in err for err in errors)
    
    def test_validate_order_amount_positive(self, consistency_manager):
        """Test order amount validation"""
        # Valid order
        valid_order = {
            "id": "order_001",
            "total_amount": 10000.0,
            "paid_amount": 5000.0
        }
        is_valid, errors = consistency_manager.validate_entity(
            EntityType.ORDER,
            valid_order
        )
        assert is_valid
        
        # Invalid order (zero amount)
        invalid_order = {
            "id": "order_002",
            "total_amount": 0.0,
            "paid_amount": 0.0
        }
        is_valid, errors = consistency_manager.validate_entity(
            EntityType.ORDER,
            invalid_order
        )
        assert not is_valid
        assert any("金额必须大于0" in err for err in errors)
    
    def test_validate_order_paid_not_exceed_total(self, consistency_manager):
        """Test order paid amount doesn't exceed total"""
        # Paid exceeds total
        order = {
            "id": "order_001",
            "total_amount": 10000.0,
            "paid_amount": 15000.0
        }
        is_valid, errors = consistency_manager.validate_entity(
            EntityType.ORDER,
            order
        )
        assert not is_valid
        assert any("不能超过订单总额" in err for err in errors)
    
    def test_validate_entity_has_name(self, consistency_manager):
        """Test entity name validation"""
        # Valid entity
        valid_entity = {
            "id": "customer_001",
            "name": "京东办公用品"
        }
        is_valid, errors = consistency_manager.validate_entity(
            EntityType.ENTITY,
            valid_entity
        )
        assert is_valid
        
        # Invalid entity (no name)
        invalid_entity = {
            "id": "customer_002"
        }
        is_valid, errors = consistency_manager.validate_entity(
            EntityType.ENTITY,
            invalid_entity
        )
        assert not is_valid
        assert any("名称" in err for err in errors)
    
    def test_validate_all(self, consistency_manager, sample_data):
        """Test validating all entities"""
        # Add some invalid data
        sample_data["transactions"].append({
            "id": "trans_invalid",
            "amount": -100.0  # Invalid: negative amount
        })
        
        sample_data["orders"].append({
            "id": "order_invalid",
            "total_amount": 10000.0,
            "paid_amount": 15000.0  # Invalid: paid > total
        })
        
        results = consistency_manager.validate_all(sample_data)
        
        assert EntityType.TRANSACTION in results
        assert EntityType.ORDER in results
        
        # Check transaction errors
        trans_errors = results[EntityType.TRANSACTION]
        assert len(trans_errors) > 0
        assert any("trans_invalid" in err[0] for err in trans_errors)
        
        # Check order errors
        order_errors = results[EntityType.ORDER]
        assert len(order_errors) > 0
        assert any("order_invalid" in err[0] for err in order_errors)
    
    def test_detect_order_transaction_discrepancy(self, consistency_manager, sample_data):
        """Test detecting order-transaction amount discrepancies"""
        # Modify order paid amount to create discrepancy
        order = next(o for o in sample_data["orders"] if o["id"] == "order_001")
        order["paid_amount"] = 10000.0  # Incorrect, should be 5000.0
        
        issues = consistency_manager.detect_discrepancies(sample_data)
        
        assert len(issues) > 0
        order_issue = next((i for i in issues if i.entity_id == "order_001"), None)
        assert order_issue is not None
        assert "不一致" in order_issue.description
        assert order_issue.auto_fixable
    
    def test_detect_missing_entity_reference(self, consistency_manager, sample_data):
        """Test detecting missing entity references"""
        # Add transaction with non-existent entity
        sample_data["transactions"].append({
            "id": "trans_orphan",
            "date": "2026-02-01",
            "entity_id": "nonexistent_entity",
            "amount": 1000.0
        })
        
        issues = consistency_manager.detect_discrepancies(sample_data)
        
        orphan_issue = next(
            (i for i in issues if i.entity_id == "trans_orphan"),
            None
        )
        assert orphan_issue is not None
        assert "不存在" in orphan_issue.description
        assert not orphan_issue.auto_fixable
    
    def test_auto_fix_order_transaction_mismatch(self, consistency_manager, sample_data):
        """Test auto-fixing order-transaction amount mismatches"""
        # Create discrepancy
        order = next(o for o in sample_data["orders"] if o["id"] == "order_001")
        order["paid_amount"] = 10000.0  # Incorrect
        
        # Detect issues
        issues = consistency_manager.detect_discrepancies(sample_data)
        
        # Auto-fix
        messages = consistency_manager.auto_fix_discrepancies(sample_data, issues)
        
        assert len(messages) > 0
        assert "已修复" in messages[0]
        
        # Verify fix
        order = next(o for o in sample_data["orders"] if o["id"] == "order_001")
        expected_paid = 3000.0 + 2000.0  # Sum of transactions
        assert order["paid_amount"] == expected_paid
        assert order["balance"] == order["total_amount"] - expected_paid
    
    def test_get_related_entities_for_customer(self, consistency_manager, sample_data):
        """Test getting related entities for a customer"""
        related = consistency_manager.get_related_entities(
            EntityType.ENTITY,
            "customer_001",
            sample_data
        )
        
        assert EntityType.TRANSACTION in related
        assert EntityType.ORDER in related
        
        # Should have 2 transactions
        assert len(related[EntityType.TRANSACTION]) == 2
        assert "trans_001" in related[EntityType.TRANSACTION]
        assert "trans_002" in related[EntityType.TRANSACTION]
        
        # Should have 2 orders
        assert len(related[EntityType.ORDER]) == 2
        assert "order_001" in related[EntityType.ORDER]
        assert "order_002" in related[EntityType.ORDER]
    
    def test_get_related_entities_for_order(self, consistency_manager, sample_data):
        """Test getting related entities for an order"""
        related = consistency_manager.get_related_entities(
            EntityType.ORDER,
            "order_001",
            sample_data
        )
        
        assert EntityType.TRANSACTION in related
        assert len(related[EntityType.TRANSACTION]) == 2
        assert "trans_001" in related[EntityType.TRANSACTION]
        assert "trans_002" in related[EntityType.TRANSACTION]
    
    def test_add_custom_validation_rule(self, consistency_manager):
        """Test adding custom validation rules"""
        # Add custom rule
        custom_rule = ValidationRule(
            name="custom_test_rule",
            entity_type=EntityType.TRANSACTION,
            validator=lambda t: (
                t.get("amount", 0) < 100000,
                "金额不能超过10万" if t.get("amount", 0) >= 100000 else None
            )
        )
        
        consistency_manager.add_validation_rule(custom_rule)
        
        # Test with transaction exceeding limit
        trans = {
            "id": "trans_001",
            "date": "2026-02-01",
            "entity_id": "customer_001",
            "amount": 150000.0
        }
        
        is_valid, errors = consistency_manager.validate_entity(
            EntityType.TRANSACTION,
            trans
        )
        
        assert not is_valid
        assert any("不能超过10万" in err for err in errors)
    
    def test_change_propagation_marks_as_propagated(self, consistency_manager, sample_data):
        """Test that propagated changes are marked correctly"""
        # Record change
        consistency_manager.record_change(
            entity_type=EntityType.ENTITY,
            entity_id="customer_001",
            change_type=ChangeType.UPDATE,
            field_name="name",
            new_value="新名称"
        )
        
        assert len(consistency_manager.pending_propagations) == 1
        
        # Propagate
        consistency_manager.propagate_changes(sample_data)
        
        # Should be marked as propagated and removed from pending
        assert len(consistency_manager.pending_propagations) == 0
        assert consistency_manager.change_history[0].propagated
    
    def test_multiple_changes_propagation(self, consistency_manager, sample_data):
        """Test propagating multiple changes"""
        # Record multiple changes
        consistency_manager.record_change(
            entity_type=EntityType.ENTITY,
            entity_id="customer_001",
            change_type=ChangeType.UPDATE,
            field_name="name",
            new_value="新名称1"
        )
        
        consistency_manager.record_change(
            entity_type=EntityType.ENTITY,
            entity_id="supplier_001",
            change_type=ChangeType.UPDATE,
            field_name="name",
            new_value="新名称2"
        )
        
        assert len(consistency_manager.pending_propagations) == 2
        
        # Propagate all
        messages = consistency_manager.propagate_changes(sample_data)
        
        assert len(messages) >= 2
        assert len(consistency_manager.pending_propagations) == 0
    
    def test_state_persistence(self, consistency_manager, temp_dir):
        """Test saving and loading consistency state"""
        # Create some issues
        issue = ConsistencyIssue(
            issue_id="test_issue_001",
            entity_type=EntityType.ORDER,
            entity_id="order_001",
            description="测试问题",
            severity="warning",
            auto_fixable=True
        )
        consistency_manager.issues.append(issue)
        
        # Save state
        consistency_manager.save_state()
        
        # Create new manager and load state
        new_manager = DataConsistencyManager(storage_dir=temp_dir / "consistency")
        
        assert len(new_manager.issues) == 1
        loaded_issue = new_manager.issues[0]
        assert loaded_issue.issue_id == "test_issue_001"
        assert loaded_issue.entity_type == EntityType.ORDER
        assert loaded_issue.description == "测试问题"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
