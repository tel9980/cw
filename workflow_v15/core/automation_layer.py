"""
Automation Layer for V1.5 Workflow System

This module provides intelligent automation including:
1. Pattern recognition for repeated user actions
2. Automation rule creation and management
3. Recurring transaction automation
4. Intelligent reminder system
5. User approval workflow for automated actions

Requirements: 6.1, 6.2, 6.3, 6.4, 6.5
"""

from typing import Dict, List, Optional, Any, Callable
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from enum import Enum
import json
from pathlib import Path
from collections import defaultdict, Counter


class AutomationTrigger(Enum):
    """Types of automation triggers"""
    TIME_BASED = "time_based"  # Trigger at specific time
    PATTERN_BASED = "pattern_based"  # Trigger when pattern detected
    EVENT_BASED = "event_based"  # Trigger on specific event
    MANUAL = "manual"  # User manually triggers


class AutomationStatus(Enum):
    """Status of automation rules"""
    ACTIVE = "active"
    PAUSED = "paused"
    PENDING_APPROVAL = "pending_approval"
    DISABLED = "disabled"


@dataclass
class Pattern:
    """Represents a detected user behavior pattern"""
    pattern_id: str
    pattern_type: str  # transaction, workflow, operation
    frequency: int  # How many times observed
    confidence: float  # 0.0 to 1.0
    description: str
    template: Dict[str, Any]  # Template for automation
    first_seen: datetime = field(default_factory=datetime.now)
    last_seen: datetime = field(default_factory=datetime.now)
    suggested_automation: bool = False


@dataclass
class AutomationRule:
    """Represents an automation rule"""
    rule_id: str
    name: str
    description: str
    trigger: AutomationTrigger
    trigger_config: Dict[str, Any]  # Trigger-specific configuration
    action_type: str  # transaction, reminder, workflow
    action_config: Dict[str, Any]  # Action-specific configuration
    status: AutomationStatus = AutomationStatus.PENDING_APPROVAL
    created_at: datetime = field(default_factory=datetime.now)
    last_executed: Optional[datetime] = None
    execution_count: int = 0
    requires_approval: bool = True
    created_from_pattern: Optional[str] = None


@dataclass
class AutomationExecution:
    """Represents an automation execution"""
    execution_id: str
    rule_id: str
    executed_at: datetime
    success: bool
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    approved_by_user: bool = False


@dataclass
class Reminder:
    """Represents a reminder"""
    reminder_id: str
    title: str
    description: str
    due_date: datetime
    priority: str = "medium"  # low, medium, high
    completed: bool = False
    recurring: bool = False
    recurrence_pattern: Optional[str] = None  # daily, weekly, monthly
    related_entity_type: Optional[str] = None
    related_entity_id: Optional[str] = None


class AutomationLayer:
    """
    Manages intelligent automation for the financial system.
    
    Features:
    - Pattern recognition from user actions
    - Automation rule creation and management
    - Recurring transaction automation
    - Intelligent reminder system
    - User approval workflow
    """
    
    def __init__(self, storage_dir: Optional[Path] = None):
        """
        Initialize the automation layer.
        
        Args:
            storage_dir: Directory for storing automation data
        """
        self.storage_dir = storage_dir or Path("财务数据/automation")
        self.storage_dir.mkdir(parents=True, exist_ok=True)
        
        # Pattern detection
        self.patterns: Dict[str, Pattern] = {}
        self.action_history: List[Dict[str, Any]] = []
        self.pattern_threshold = 3  # Minimum occurrences to suggest automation
        
        # Automation rules
        self.rules: Dict[str, AutomationRule] = {}
        self.executions: List[AutomationExecution] = []
        
        # Reminders
        self.reminders: Dict[str, Reminder] = {}
        
        # Load persisted data
        self._load_state()
    
    def record_action(
        self,
        user_id: str,
        action_type: str,
        action_data: Dict[str, Any]
    ):
        """
        Record a user action for pattern detection.
        
        Args:
            user_id: User ID
            action_type: Type of action (transaction, workflow, etc.)
            action_data: Action data
        """
        action = {
            "user_id": user_id,
            "action_type": action_type,
            "action_data": action_data,
            "timestamp": datetime.now().isoformat()
        }
        
        self.action_history.append(action)
        
        # Limit history size
        if len(self.action_history) > 1000:
            self.action_history = self.action_history[-1000:]
        
        # Detect patterns
        self._detect_patterns(user_id, action_type)
    
    def _detect_patterns(self, user_id: str, action_type: str):
        """Detect patterns in user actions"""
        # Get recent actions of this type
        recent_actions = [
            a for a in self.action_history[-100:]
            if a["user_id"] == user_id and a["action_type"] == action_type
        ]
        
        if len(recent_actions) < self.pattern_threshold:
            return
        
        # Detect recurring transactions
        if action_type == "transaction":
            self._detect_recurring_transactions(user_id, recent_actions)
        
        # Detect workflow patterns
        elif action_type == "workflow":
            self._detect_workflow_patterns(user_id, recent_actions)
    
    def _detect_recurring_transactions(
        self,
        user_id: str,
        actions: List[Dict[str, Any]]
    ):
        """Detect recurring transaction patterns"""
        # Group by entity and amount
        transaction_groups = defaultdict(list)
        
        for action in actions:
            data = action["action_data"]
            entity_id = data.get("entity_id", "")
            amount = data.get("amount", 0)
            category = data.get("category", "")
            
            key = f"{entity_id}_{amount}_{category}"
            transaction_groups[key].append(action)
        
        # Check for patterns
        for key, group in transaction_groups.items():
            if len(group) >= self.pattern_threshold:
                # Calculate time intervals
                timestamps = [
                    datetime.fromisoformat(a["timestamp"])
                    for a in group
                ]
                timestamps.sort()
                
                if len(timestamps) >= 2:
                    intervals = [
                        (timestamps[i+1] - timestamps[i]).days
                        for i in range(len(timestamps) - 1)
                    ]
                    
                    # Check if intervals are consistent (within 3 days)
                    avg_interval = sum(intervals) / len(intervals)
                    if all(abs(interval - avg_interval) <= 3 for interval in intervals):
                        # Found a recurring pattern
                        pattern_id = f"recurring_trans_{key}"
                        
                        if pattern_id not in self.patterns:
                            template = group[-1]["action_data"].copy()
                            
                            pattern = Pattern(
                                pattern_id=pattern_id,
                                pattern_type="recurring_transaction",
                                frequency=len(group),
                                confidence=min(0.9, len(group) / 10),
                                description=f"Recurring transaction every {int(avg_interval)} days",
                                template=template
                            )
                            
                            self.patterns[pattern_id] = pattern
    
    def _detect_workflow_patterns(
        self,
        user_id: str,
        actions: List[Dict[str, Any]]
    ):
        """Detect workflow sequence patterns"""
        # Group by workflow type
        workflow_sequences = defaultdict(list)
        
        for action in actions:
            data = action["action_data"]
            workflow_type = data.get("workflow_type", "")
            workflow_sequences[workflow_type].append(action)
        
        # Check for patterns
        for workflow_type, sequence in workflow_sequences.items():
            if len(sequence) >= self.pattern_threshold:
                pattern_id = f"workflow_{workflow_type}"
                
                if pattern_id not in self.patterns:
                    # Calculate average execution time
                    timestamps = [
                        datetime.fromisoformat(a["timestamp"])
                        for a in sequence
                    ]
                    
                    hours = [t.hour for t in timestamps]
                    avg_hour = sum(hours) / len(hours)
                    
                    pattern = Pattern(
                        pattern_id=pattern_id,
                        pattern_type="workflow_sequence",
                        frequency=len(sequence),
                        confidence=min(0.8, len(sequence) / 10),
                        description=f"Workflow '{workflow_type}' typically executed around {int(avg_hour)}:00",
                        template={"workflow_type": workflow_type, "typical_hour": int(avg_hour)}
                    )
                    
                    self.patterns[pattern_id] = pattern
    
    def get_suggested_automations(
        self,
        user_id: str
    ) -> List[Dict[str, Any]]:
        """
        Get automation suggestions based on detected patterns.
        
        Args:
            user_id: User ID
            
        Returns:
            List of automation suggestions
        """
        suggestions = []
        
        for pattern in self.patterns.values():
            if pattern.suggested_automation:
                continue
            
            if pattern.confidence >= 0.7 and pattern.frequency >= self.pattern_threshold:
                suggestion = {
                    "pattern_id": pattern.pattern_id,
                    "pattern_type": pattern.pattern_type,
                    "description": pattern.description,
                    "confidence": pattern.confidence,
                    "frequency": pattern.frequency,
                    "suggested_rule": self._create_rule_from_pattern(pattern)
                }
                suggestions.append(suggestion)
        
        return suggestions
    
    def _create_rule_from_pattern(self, pattern: Pattern) -> Dict[str, Any]:
        """Create an automation rule suggestion from a pattern"""
        if pattern.pattern_type == "recurring_transaction":
            return {
                "name": f"Auto-create recurring transaction",
                "description": pattern.description,
                "trigger": AutomationTrigger.TIME_BASED.value,
                "trigger_config": {
                    "recurrence": "monthly",  # Could be calculated from pattern
                    "day_of_month": 1
                },
                "action_type": "create_transaction",
                "action_config": pattern.template
            }
        
        elif pattern.pattern_type == "workflow_sequence":
            typical_hour = pattern.template.get("typical_hour", 9)
            return {
                "name": f"Remind to execute workflow",
                "description": pattern.description,
                "trigger": AutomationTrigger.TIME_BASED.value,
                "trigger_config": {
                    "time": f"{typical_hour:02d}:00",
                    "days": ["monday", "tuesday", "wednesday", "thursday", "friday"]
                },
                "action_type": "create_reminder",
                "action_config": {
                    "title": f"Execute {pattern.template['workflow_type']} workflow",
                    "priority": "medium"
                }
            }
        
        return {}
    
    def create_rule(
        self,
        name: str,
        description: str,
        trigger: AutomationTrigger,
        trigger_config: Dict[str, Any],
        action_type: str,
        action_config: Dict[str, Any],
        requires_approval: bool = True,
        pattern_id: Optional[str] = None
    ) -> AutomationRule:
        """
        Create a new automation rule.
        
        Args:
            name: Rule name
            description: Rule description
            trigger: Trigger type
            trigger_config: Trigger configuration
            action_type: Action type
            action_config: Action configuration
            requires_approval: Whether execution requires user approval
            pattern_id: Optional pattern ID this rule was created from
            
        Returns:
            Created automation rule
        """
        rule_id = f"rule_{datetime.now().timestamp()}"
        
        rule = AutomationRule(
            rule_id=rule_id,
            name=name,
            description=description,
            trigger=trigger,
            trigger_config=trigger_config,
            action_type=action_type,
            action_config=action_config,
            requires_approval=requires_approval,
            created_from_pattern=pattern_id
        )
        
        self.rules[rule_id] = rule
        
        # Mark pattern as used
        if pattern_id and pattern_id in self.patterns:
            self.patterns[pattern_id].suggested_automation = True
        
        self._save_state()
        
        return rule
    
    def approve_rule(self, rule_id: str) -> bool:
        """Approve a pending automation rule"""
        if rule_id not in self.rules:
            return False
        
        rule = self.rules[rule_id]
        if rule.status == AutomationStatus.PENDING_APPROVAL:
            rule.status = AutomationStatus.ACTIVE
            self._save_state()
            return True
        
        return False
    
    def pause_rule(self, rule_id: str) -> bool:
        """Pause an active automation rule"""
        if rule_id not in self.rules:
            return False
        
        rule = self.rules[rule_id]
        if rule.status == AutomationStatus.ACTIVE:
            rule.status = AutomationStatus.PAUSED
            self._save_state()
            return True
        
        return False
    
    def resume_rule(self, rule_id: str) -> bool:
        """Resume a paused automation rule"""
        if rule_id not in self.rules:
            return False
        
        rule = self.rules[rule_id]
        if rule.status == AutomationStatus.PAUSED:
            rule.status = AutomationStatus.ACTIVE
            self._save_state()
            return True
        
        return False
    
    def delete_rule(self, rule_id: str) -> bool:
        """Delete an automation rule"""
        if rule_id in self.rules:
            del self.rules[rule_id]
            self._save_state()
            return True
        return False
    
    def execute_rule(
        self,
        rule_id: str,
        user_approved: bool = False
    ) -> AutomationExecution:
        """
        Execute an automation rule.
        
        Args:
            rule_id: Rule ID to execute
            user_approved: Whether user has approved this execution
            
        Returns:
            Execution result
        """
        if rule_id not in self.rules:
            return AutomationExecution(
                execution_id=f"exec_{datetime.now().timestamp()}",
                rule_id=rule_id,
                executed_at=datetime.now(),
                success=False,
                error="Rule not found"
            )
        
        rule = self.rules[rule_id]
        
        # Check if rule is active
        if rule.status != AutomationStatus.ACTIVE:
            return AutomationExecution(
                execution_id=f"exec_{datetime.now().timestamp()}",
                rule_id=rule_id,
                executed_at=datetime.now(),
                success=False,
                error=f"Rule is {rule.status.value}"
            )
        
        # Check if approval is required
        if rule.requires_approval and not user_approved:
            return AutomationExecution(
                execution_id=f"exec_{datetime.now().timestamp()}",
                rule_id=rule_id,
                executed_at=datetime.now(),
                success=False,
                error="User approval required"
            )
        
        # Execute the action
        try:
            result = self._execute_action(rule.action_type, rule.action_config)
            
            execution = AutomationExecution(
                execution_id=f"exec_{datetime.now().timestamp()}",
                rule_id=rule_id,
                executed_at=datetime.now(),
                success=True,
                result=result,
                approved_by_user=user_approved
            )
            
            # Update rule statistics
            rule.last_executed = datetime.now()
            rule.execution_count += 1
            
        except Exception as e:
            execution = AutomationExecution(
                execution_id=f"exec_{datetime.now().timestamp()}",
                rule_id=rule_id,
                executed_at=datetime.now(),
                success=False,
                error=str(e)
            )
        
        self.executions.append(execution)
        self._save_state()
        
        return execution
    
    def _execute_action(
        self,
        action_type: str,
        action_config: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Execute an automation action"""
        if action_type == "create_transaction":
            # Would create a transaction in the actual system
            return {
                "action": "create_transaction",
                "transaction_id": f"trans_{datetime.now().timestamp()}",
                "data": action_config
            }
        
        elif action_type == "create_reminder":
            reminder_id = self.create_reminder(
                title=action_config.get("title", "Reminder"),
                description=action_config.get("description", ""),
                due_date=datetime.now() + timedelta(days=1),
                priority=action_config.get("priority", "medium")
            )
            return {
                "action": "create_reminder",
                "reminder_id": reminder_id
            }
        
        elif action_type == "execute_workflow":
            return {
                "action": "execute_workflow",
                "workflow_type": action_config.get("workflow_type")
            }
        
        return {"action": action_type, "config": action_config}
    
    def create_reminder(
        self,
        title: str,
        description: str,
        due_date: datetime,
        priority: str = "medium",
        recurring: bool = False,
        recurrence_pattern: Optional[str] = None,
        related_entity_type: Optional[str] = None,
        related_entity_id: Optional[str] = None
    ) -> str:
        """
        Create a reminder.
        
        Args:
            title: Reminder title
            description: Reminder description
            due_date: Due date
            priority: Priority level (low, medium, high)
            recurring: Whether reminder is recurring
            recurrence_pattern: Recurrence pattern (daily, weekly, monthly)
            related_entity_type: Related entity type
            related_entity_id: Related entity ID
            
        Returns:
            Reminder ID
        """
        reminder_id = f"reminder_{datetime.now().timestamp()}"
        
        reminder = Reminder(
            reminder_id=reminder_id,
            title=title,
            description=description,
            due_date=due_date,
            priority=priority,
            recurring=recurring,
            recurrence_pattern=recurrence_pattern,
            related_entity_type=related_entity_type,
            related_entity_id=related_entity_id
        )
        
        self.reminders[reminder_id] = reminder
        self._save_state()
        
        return reminder_id
    
    def get_due_reminders(
        self,
        include_overdue: bool = True
    ) -> List[Reminder]:
        """
        Get reminders that are due.
        
        Args:
            include_overdue: Whether to include overdue reminders
            
        Returns:
            List of due reminders
        """
        now = datetime.now()
        due_reminders = []
        
        for reminder in self.reminders.values():
            if reminder.completed:
                continue
            
            if include_overdue:
                if reminder.due_date <= now:
                    due_reminders.append(reminder)
            else:
                if reminder.due_date.date() == now.date():
                    due_reminders.append(reminder)
        
        # Sort by priority and due date
        priority_order = {"high": 0, "medium": 1, "low": 2}
        due_reminders.sort(
            key=lambda r: (priority_order.get(r.priority, 1), r.due_date)
        )
        
        return due_reminders
    
    def complete_reminder(self, reminder_id: str) -> bool:
        """Mark a reminder as completed"""
        if reminder_id not in self.reminders:
            return False
        
        reminder = self.reminders[reminder_id]
        reminder.completed = True
        
        # Handle recurring reminders
        if reminder.recurring and reminder.recurrence_pattern:
            # Create next occurrence
            if reminder.recurrence_pattern == "daily":
                next_due = reminder.due_date + timedelta(days=1)
            elif reminder.recurrence_pattern == "weekly":
                next_due = reminder.due_date + timedelta(weeks=1)
            elif reminder.recurrence_pattern == "monthly":
                next_due = reminder.due_date + timedelta(days=30)
            else:
                next_due = reminder.due_date + timedelta(days=1)
            
            self.create_reminder(
                title=reminder.title,
                description=reminder.description,
                due_date=next_due,
                priority=reminder.priority,
                recurring=True,
                recurrence_pattern=reminder.recurrence_pattern,
                related_entity_type=reminder.related_entity_type,
                related_entity_id=reminder.related_entity_id
            )
        
        self._save_state()
        return True
    
    def get_active_rules(self) -> List[AutomationRule]:
        """Get all active automation rules"""
        return [
            rule for rule in self.rules.values()
            if rule.status == AutomationStatus.ACTIVE
        ]
    
    def get_pending_rules(self) -> List[AutomationRule]:
        """Get all pending approval rules"""
        return [
            rule for rule in self.rules.values()
            if rule.status == AutomationStatus.PENDING_APPROVAL
        ]
    
    def get_execution_history(
        self,
        rule_id: Optional[str] = None,
        limit: int = 10
    ) -> List[AutomationExecution]:
        """
        Get execution history.
        
        Args:
            rule_id: Optional rule ID to filter by
            limit: Maximum number of executions to return
            
        Returns:
            List of executions
        """
        executions = self.executions
        
        if rule_id:
            executions = [e for e in executions if e.rule_id == rule_id]
        
        # Sort by execution time descending
        executions.sort(key=lambda e: e.executed_at, reverse=True)
        
        return executions[:limit]
    
    def _load_state(self):
        """Load persisted automation state"""
        # Load patterns
        patterns_file = self.storage_dir / "patterns.json"
        if patterns_file.exists():
            try:
                with open(patterns_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    for pattern_data in data:
                        pattern = Pattern(
                            pattern_id=pattern_data["pattern_id"],
                            pattern_type=pattern_data["pattern_type"],
                            frequency=pattern_data["frequency"],
                            confidence=pattern_data["confidence"],
                            description=pattern_data["description"],
                            template=pattern_data["template"],
                            first_seen=datetime.fromisoformat(pattern_data["first_seen"]),
                            last_seen=datetime.fromisoformat(pattern_data["last_seen"]),
                            suggested_automation=pattern_data.get("suggested_automation", False)
                        )
                        self.patterns[pattern.pattern_id] = pattern
            except Exception as e:
                print(f"Failed to load patterns: {e}")
        
        # Load rules
        rules_file = self.storage_dir / "rules.json"
        if rules_file.exists():
            try:
                with open(rules_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    for rule_data in data:
                        rule = AutomationRule(
                            rule_id=rule_data["rule_id"],
                            name=rule_data["name"],
                            description=rule_data["description"],
                            trigger=AutomationTrigger(rule_data["trigger"]),
                            trigger_config=rule_data["trigger_config"],
                            action_type=rule_data["action_type"],
                            action_config=rule_data["action_config"],
                            status=AutomationStatus(rule_data["status"]),
                            created_at=datetime.fromisoformat(rule_data["created_at"]),
                            last_executed=datetime.fromisoformat(rule_data["last_executed"]) if rule_data.get("last_executed") else None,
                            execution_count=rule_data.get("execution_count", 0),
                            requires_approval=rule_data.get("requires_approval", True),
                            created_from_pattern=rule_data.get("created_from_pattern")
                        )
                        self.rules[rule.rule_id] = rule
            except Exception as e:
                print(f"Failed to load rules: {e}")
        
        # Load reminders
        reminders_file = self.storage_dir / "reminders.json"
        if reminders_file.exists():
            try:
                with open(reminders_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    for reminder_data in data:
                        reminder = Reminder(
                            reminder_id=reminder_data["reminder_id"],
                            title=reminder_data["title"],
                            description=reminder_data["description"],
                            due_date=datetime.fromisoformat(reminder_data["due_date"]),
                            priority=reminder_data.get("priority", "medium"),
                            completed=reminder_data.get("completed", False),
                            recurring=reminder_data.get("recurring", False),
                            recurrence_pattern=reminder_data.get("recurrence_pattern"),
                            related_entity_type=reminder_data.get("related_entity_type"),
                            related_entity_id=reminder_data.get("related_entity_id")
                        )
                        self.reminders[reminder.reminder_id] = reminder
            except Exception as e:
                print(f"Failed to load reminders: {e}")
    
    def _save_state(self):
        """Save automation state to disk"""
        # Save patterns
        patterns_file = self.storage_dir / "patterns.json"
        try:
            patterns_data = [
                {
                    "pattern_id": p.pattern_id,
                    "pattern_type": p.pattern_type,
                    "frequency": p.frequency,
                    "confidence": p.confidence,
                    "description": p.description,
                    "template": p.template,
                    "first_seen": p.first_seen.isoformat(),
                    "last_seen": p.last_seen.isoformat(),
                    "suggested_automation": p.suggested_automation
                }
                for p in self.patterns.values()
            ]
            
            with open(patterns_file, 'w', encoding='utf-8') as f:
                json.dump(patterns_data, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"Failed to save patterns: {e}")
        
        # Save rules
        rules_file = self.storage_dir / "rules.json"
        try:
            rules_data = [
                {
                    "rule_id": r.rule_id,
                    "name": r.name,
                    "description": r.description,
                    "trigger": r.trigger.value,
                    "trigger_config": r.trigger_config,
                    "action_type": r.action_type,
                    "action_config": r.action_config,
                    "status": r.status.value,
                    "created_at": r.created_at.isoformat(),
                    "last_executed": r.last_executed.isoformat() if r.last_executed else None,
                    "execution_count": r.execution_count,
                    "requires_approval": r.requires_approval,
                    "created_from_pattern": r.created_from_pattern
                }
                for r in self.rules.values()
            ]
            
            with open(rules_file, 'w', encoding='utf-8') as f:
                json.dump(rules_data, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"Failed to save rules: {e}")
        
        # Save reminders
        reminders_file = self.storage_dir / "reminders.json"
        try:
            reminders_data = [
                {
                    "reminder_id": r.reminder_id,
                    "title": r.title,
                    "description": r.description,
                    "due_date": r.due_date.isoformat(),
                    "priority": r.priority,
                    "completed": r.completed,
                    "recurring": r.recurring,
                    "recurrence_pattern": r.recurrence_pattern,
                    "related_entity_type": r.related_entity_type,
                    "related_entity_id": r.related_entity_id
                }
                for r in self.reminders.values()
            ]
            
            with open(reminders_file, 'w', encoding='utf-8') as f:
                json.dump(reminders_data, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"Failed to save reminders: {e}")
