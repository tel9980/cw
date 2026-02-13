# -*- coding: utf-8 -*-
import pytest
from datetime import datetime, timedelta
from pathlib import Path
import tempfile
import shutil

from workflow_v15.core.automation_layer import (
    AutomationLayer,
    AutomationTrigger,
    AutomationStatus,
    Pattern,
    AutomationRule,
    Reminder
)


@pytest.fixture
def temp_dir():
    temp_path = Path(tempfile.mkdtemp())
    yield temp_path
    shutil.rmtree(temp_path)


@pytest.fixture
def automation_layer(temp_dir):
    return AutomationLayer(storage_dir=temp_dir / "automation")


class TestPatternDetection:
    def test_record_action(self, automation_layer):
        automation_layer.record_action(
            user_id="user_001",
            action_type="transaction",
            action_data={"amount": 1000.0, "entity_id": "customer_001"}
        )
        assert len(automation_layer.action_history) == 1
    
    def test_detect_recurring_transaction_pattern(self, automation_layer):
        # Record same transaction multiple times
        for i in range(5):
            automation_layer.record_action(
                user_id="user_001",
                action_type="transaction",
                action_data={
                    "amount": 5000.0,
                    "entity_id": "customer_001",
                    "category": "rent"
                }
            )
        
        # Should detect pattern
        assert len(automation_layer.patterns) > 0
    
    def test_get_suggested_automations(self, automation_layer):
        # Create a pattern with high confidence
        pattern = Pattern(
            pattern_id="test_pattern",
            pattern_type="recurring_transaction",
            frequency=5,
            confidence=0.8,
            description="Test pattern",
            template={"amount": 1000.0}
        )
        automation_layer.patterns[pattern.pattern_id] = pattern
        
        suggestions = automation_layer.get_suggested_automations("user_001")
        assert len(suggestions) > 0
        assert suggestions[0]["confidence"] >= 0.7


class TestAutomationRules:
    def test_create_rule(self, automation_layer):
        rule = automation_layer.create_rule(
            name="Test Rule",
            description="Test automation rule",
            trigger=AutomationTrigger.TIME_BASED,
            trigger_config={"time": "09:00"},
            action_type="create_reminder",
            action_config={"title": "Test"}
        )
        
        assert rule is not None
        assert rule.status == AutomationStatus.PENDING_APPROVAL
        assert rule.name == "Test Rule"
    
    def test_approve_rule(self, automation_layer):
        rule = automation_layer.create_rule(
            name="Test Rule",
            description="Test",
            trigger=AutomationTrigger.TIME_BASED,
            trigger_config={},
            action_type="create_reminder",
            action_config={}
        )
        
        result = automation_layer.approve_rule(rule.rule_id)
        assert result is True
        assert automation_layer.rules[rule.rule_id].status == AutomationStatus.ACTIVE
    
    def test_pause_rule(self, automation_layer):
        rule = automation_layer.create_rule(
            name="Test Rule",
            description="Test",
            trigger=AutomationTrigger.TIME_BASED,
            trigger_config={},
            action_type="create_reminder",
            action_config={}
        )
        automation_layer.approve_rule(rule.rule_id)
        
        result = automation_layer.pause_rule(rule.rule_id)
        assert result is True
        assert automation_layer.rules[rule.rule_id].status == AutomationStatus.PAUSED
    
    def test_resume_rule(self, automation_layer):
        rule = automation_layer.create_rule(
            name="Test Rule",
            description="Test",
            trigger=AutomationTrigger.TIME_BASED,
            trigger_config={},
            action_type="create_reminder",
            action_config={}
        )
        automation_layer.approve_rule(rule.rule_id)
        automation_layer.pause_rule(rule.rule_id)
        
        result = automation_layer.resume_rule(rule.rule_id)
        assert result is True
        assert automation_layer.rules[rule.rule_id].status == AutomationStatus.ACTIVE
    
    def test_delete_rule(self, automation_layer):
        rule = automation_layer.create_rule(
            name="Test Rule",
            description="Test",
            trigger=AutomationTrigger.TIME_BASED,
            trigger_config={},
            action_type="create_reminder",
            action_config={}
        )
        
        result = automation_layer.delete_rule(rule.rule_id)
        assert result is True
        assert rule.rule_id not in automation_layer.rules
    
    def test_execute_rule_requires_approval(self, automation_layer):
        rule = automation_layer.create_rule(
            name="Test Rule",
            description="Test",
            trigger=AutomationTrigger.TIME_BASED,
            trigger_config={},
            action_type="create_reminder",
            action_config={"title": "Test"},
            requires_approval=True
        )
        automation_layer.approve_rule(rule.rule_id)
        
        # Execute without approval
        execution = automation_layer.execute_rule(rule.rule_id, user_approved=False)
        assert not execution.success
        assert "approval required" in execution.error.lower()
        
        # Execute with approval
        execution = automation_layer.execute_rule(rule.rule_id, user_approved=True)
        assert execution.success
    
    def test_execute_rule_updates_statistics(self, automation_layer):
        rule = automation_layer.create_rule(
            name="Test Rule",
            description="Test",
            trigger=AutomationTrigger.TIME_BASED,
            trigger_config={},
            action_type="create_reminder",
            action_config={"title": "Test"},
            requires_approval=False
        )
        automation_layer.approve_rule(rule.rule_id)
        
        initial_count = rule.execution_count
        automation_layer.execute_rule(rule.rule_id)
        
        assert rule.execution_count == initial_count + 1
        assert rule.last_executed is not None


class TestReminders:
    def test_create_reminder(self, automation_layer):
        due_date = datetime.now() + timedelta(days=1)
        reminder_id = automation_layer.create_reminder(
            title="Test Reminder",
            description="Test description",
            due_date=due_date,
            priority="high"
        )
        
        assert reminder_id in automation_layer.reminders
        reminder = automation_layer.reminders[reminder_id]
        assert reminder.title == "Test Reminder"
        assert reminder.priority == "high"
    
    def test_get_due_reminders(self, automation_layer):
        # Create overdue reminder
        overdue_date = datetime.now() - timedelta(days=1)
        automation_layer.create_reminder(
            title="Overdue",
            description="Test",
            due_date=overdue_date
        )
        
        # Create future reminder
        future_date = datetime.now() + timedelta(days=1)
        automation_layer.create_reminder(
            title="Future",
            description="Test",
            due_date=future_date
        )
        
        due_reminders = automation_layer.get_due_reminders(include_overdue=True)
        assert len(due_reminders) == 1
        assert due_reminders[0].title == "Overdue"
    
    def test_complete_reminder(self, automation_layer):
        due_date = datetime.now() + timedelta(days=1)
        reminder_id = automation_layer.create_reminder(
            title="Test",
            description="Test",
            due_date=due_date
        )
        
        result = automation_layer.complete_reminder(reminder_id)
        assert result is True
        assert automation_layer.reminders[reminder_id].completed
    
    def test_recurring_reminder(self, automation_layer):
        due_date = datetime.now() + timedelta(days=1)
        reminder_id = automation_layer.create_reminder(
            title="Recurring Test",
            description="Test",
            due_date=due_date,
            recurring=True,
            recurrence_pattern="daily"
        )
        
        initial_count = len(automation_layer.reminders)
        automation_layer.complete_reminder(reminder_id)
        
        # Should create next occurrence
        assert len(automation_layer.reminders) == initial_count + 1


class TestRuleManagement:
    def test_get_active_rules(self, automation_layer):
        # Create and approve a rule
        rule1 = automation_layer.create_rule(
            name="Active Rule",
            description="Test",
            trigger=AutomationTrigger.TIME_BASED,
            trigger_config={},
            action_type="create_reminder",
            action_config={}
        )
        automation_layer.approve_rule(rule1.rule_id)
        
        # Create but don't approve
        rule2 = automation_layer.create_rule(
            name="Pending Rule",
            description="Test",
            trigger=AutomationTrigger.TIME_BASED,
            trigger_config={},
            action_type="create_reminder",
            action_config={}
        )
        
        active_rules = automation_layer.get_active_rules()
        assert len(active_rules) == 1
        assert active_rules[0].rule_id == rule1.rule_id
    
    def test_get_pending_rules(self, automation_layer):
        rule = automation_layer.create_rule(
            name="Pending Rule",
            description="Test",
            trigger=AutomationTrigger.TIME_BASED,
            trigger_config={},
            action_type="create_reminder",
            action_config={}
        )
        
        pending_rules = automation_layer.get_pending_rules()
        assert len(pending_rules) == 1
        assert pending_rules[0].rule_id == rule.rule_id
    
    def test_get_execution_history(self, automation_layer):
        rule = automation_layer.create_rule(
            name="Test Rule",
            description="Test",
            trigger=AutomationTrigger.TIME_BASED,
            trigger_config={},
            action_type="create_reminder",
            action_config={"title": "Test"},
            requires_approval=False
        )
        automation_layer.approve_rule(rule.rule_id)
        
        # Execute multiple times
        automation_layer.execute_rule(rule.rule_id)
        automation_layer.execute_rule(rule.rule_id)
        
        history = automation_layer.get_execution_history(rule_id=rule.rule_id)
        assert len(history) == 2


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
