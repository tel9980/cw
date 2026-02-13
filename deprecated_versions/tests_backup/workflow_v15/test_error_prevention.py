# -*- coding: utf-8 -*-
import pytest
from pathlib import Path
import tempfile
import shutil
from workflow_v15.core.error_prevention import ErrorPreventionManager, OperationType, ValidationSeverity

@pytest.fixture
def temp_dir():
    temp_path = Path(tempfile.mkdtemp())
    yield temp_path
    shutil.rmtree(temp_path)

@pytest.fixture
def error_manager(temp_dir):
    return ErrorPreventionManager(storage_dir=temp_dir / "error_prevention")

class TestValidation:
    def test_validate_transaction_valid(self, error_manager):
        data = {"amount": 1000.0, "date": "2026-02-10", "entity_id": "customer_001"}
        results = error_manager.validate("transaction", data)
        assert not error_manager.has_errors(results)
    
    def test_validate_transaction_negative_amount(self, error_manager):
        data = {"amount": -100.0, "date": "2026-02-10", "entity_id": "customer_001"}
        results = error_manager.validate("transaction", data)
        assert error_manager.has_errors(results)
    
    def test_validate_transaction_missing_date(self, error_manager):
        data = {"amount": 1000.0, "entity_id": "customer_001"}
        results = error_manager.validate("transaction", data)
        assert error_manager.has_errors(results)
        error_result = next(r for r in results if r.severity == ValidationSeverity.ERROR)
        assert error_result.auto_fixable
    
    def test_validate_order_valid(self, error_manager):
        data = {"total_amount": 10000.0, "paid_amount": 5000.0, "customer_id": "c001", "quantity": 100, "unit_price": 100.0}
        results = error_manager.validate("order", data)
        assert not error_manager.has_errors(results)
    
    def test_validate_order_paid_exceeds_total(self, error_manager):
        data = {"total_amount": 10000.0, "paid_amount": 15000.0, "customer_id": "c001", "quantity": 100, "unit_price": 100.0}
        results = error_manager.validate("order", data)
        assert error_manager.has_errors(results)
    
    def test_validate_entity_valid(self, error_manager):
        data = {"name": "Test Company", "type": "customer"}
        results = error_manager.validate("entity", data)
        assert not error_manager.has_errors(results)
    
    def test_auto_fix_missing_date(self, error_manager):
        data = {"amount": 1000.0, "entity_id": "customer_001"}
        results = error_manager.validate("transaction", data)
        fixed_data, messages = error_manager.auto_fix("transaction", data, results)
        assert "date" in fixed_data
        assert len(messages) > 0

class TestUndoRedo:
    def test_record_operation(self, error_manager):
        before = {"id": "trans_001", "amount": 1000.0}
        after = {"id": "trans_001", "amount": 1500.0}
        operation = error_manager.record_operation(OperationType.UPDATE, "transaction", "trans_001", before, after)
        assert operation is not None
        assert error_manager.can_undo()
    
    def test_undo_operation(self, error_manager):
        before = {"id": "trans_001", "amount": 1000.0}
        after = {"id": "trans_001", "amount": 1500.0}
        error_manager.record_operation(OperationType.UPDATE, "transaction", "trans_001", before, after)
        undone_op = error_manager.undo()
        assert undone_op is not None
        assert error_manager.can_redo()
    
    def test_redo_operation(self, error_manager):
        before = {"id": "trans_001", "amount": 1000.0}
        after = {"id": "trans_001", "amount": 1500.0}
        error_manager.record_operation(OperationType.UPDATE, "transaction", "trans_001", before, after)
        error_manager.undo()
        redone_op = error_manager.redo()
        assert redone_op is not None
        assert error_manager.can_undo()
    
    def test_multiple_undo_redo(self, error_manager):
        for i in range(3):
            error_manager.record_operation(OperationType.CREATE, "transaction", f"trans_{i}", None, {"id": f"trans_{i}"})
        assert len(error_manager.undo_stack) == 3
        error_manager.undo()
        error_manager.undo()
        error_manager.undo()
        assert len(error_manager.undo_stack) == 0
        assert len(error_manager.redo_stack) == 3
    
    def test_new_operation_clears_redo(self, error_manager):
        error_manager.record_operation(OperationType.CREATE, "transaction", "trans_001", None, {"id": "trans_001"})
        error_manager.undo()
        assert error_manager.can_redo()
        error_manager.record_operation(OperationType.CREATE, "transaction", "trans_002", None, {"id": "trans_002"})
        assert not error_manager.can_redo()

class TestDraftManagement:
    def test_save_draft(self, error_manager):
        data = {"amount": 1000.0}
        draft = error_manager.save_draft("transaction", data)
        assert draft is not None
        assert draft.auto_saved
    
    def test_load_draft(self, error_manager):
        data = {"amount": 1000.0}
        draft_id = "draft_001"
        error_manager.save_draft("transaction", data, draft_id=draft_id)
        loaded = error_manager.load_draft(draft_id)
        assert loaded is not None
        assert loaded.data == data
    
    def test_list_drafts(self, error_manager):
        error_manager.save_draft("transaction", {"amount": 1000.0}, "draft_001")
        error_manager.save_draft("order", {"total_amount": 5000.0}, "draft_002")
        all_drafts = error_manager.list_drafts()
        assert len(all_drafts) == 2
        trans_drafts = error_manager.list_drafts(entity_type="transaction")
        assert len(trans_drafts) == 1
    
    def test_delete_draft(self, error_manager):
        draft_id = "draft_001"
        error_manager.save_draft("transaction", {"amount": 1000.0}, draft_id)
        result = error_manager.delete_draft(draft_id)
        assert result is True
        assert error_manager.load_draft(draft_id) is None

class TestDestructiveOperations:
    def test_is_destructive_operation(self, error_manager):
        assert error_manager.is_destructive_operation("delete_transaction")
        assert error_manager.is_destructive_operation("clear_all_data")
        assert not error_manager.is_destructive_operation("create_transaction")
    
    def test_confirm_destructive_operation(self, error_manager):
        confirmation = error_manager.confirm_destructive_operation("delete_transaction")
        assert confirmation["operation"] == "delete_transaction"
        assert confirmation["requires_confirmation"]
        assert confirmation["severity"] == "medium"
    
    def test_confirm_clear_all_high_severity(self, error_manager):
        confirmation = error_manager.confirm_destructive_operation("clear_all_data")
        assert confirmation["severity"] == "high"

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
