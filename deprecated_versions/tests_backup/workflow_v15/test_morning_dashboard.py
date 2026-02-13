"""
Tests for Morning Dashboard Implementation

Requirements: 1.1
"""

import pytest
from datetime import datetime, date, timedelta

from workflow_v15.core.morning_dashboard import (
    MorningDashboardManager,
    PriorityTask,
    PendingItem,
    TaskPriority,
    TaskStatus,
    DashboardInsight
)


@pytest.fixture
def dashboard_manager():
    """Create dashboard manager instance"""
    return MorningDashboardManager()


@pytest.fixture
def sample_tasks():
    """Create sample tasks for testing"""
    today = date.today()
    return [
        PriorityTask(
            task_id="task1",
            title="Process payroll",
            description="Monthly payroll processing",
            priority=TaskPriority.CRITICAL,
            status=TaskStatus.PENDING,
            due_date=today,
            estimated_minutes=120,
            category="payroll"
        ),
        PriorityTask(
            task_id="task2",
            title="Review invoices",
            description="Review pending invoices",
            priority=TaskPriority.HIGH,
            status=TaskStatus.PENDING,
            due_date=today + timedelta(days=1),
            estimated_minutes=60,
            category="invoices"
        ),
        PriorityTask(
            task_id="task3",
            title="Update ledger",
            description="Update general ledger",
            priority=TaskPriority.MEDIUM,
            status=TaskStatus.IN_PROGRESS,
            due_date=today + timedelta(days=3),
            estimated_minutes=45,
            category="accounting"
        ),
        PriorityTask(
            task_id="task4",
            title="File documents",
            description="File completed documents",
            priority=TaskPriority.LOW,
            status=TaskStatus.PENDING,
            due_date=today + timedelta(days=7),
            estimated_minutes=30,
            category="admin"
        ),
        PriorityTask(
            task_id="task5",
            title="Overdue report",
            description="Generate overdue report",
            priority=TaskPriority.HIGH,
            status=TaskStatus.PENDING,
            due_date=today - timedelta(days=2),
            estimated_minutes=90,
            category="reports"
        )
    ]


@pytest.fixture
def sample_pending_items():
    """Create sample pending items"""
    today = date.today()
    return [
        PendingItem(
            item_id="item1",
            title="Approve expense",
            description="Approve employee expense",
            item_type="approval",
            created_date=today - timedelta(days=1),
            urgency="high"
        ),
        PendingItem(
            item_id="item2",
            title="Review transaction",
            description="Review flagged transaction",
            item_type="review",
            created_date=today - timedelta(days=3),
            urgency="normal"
        ),
        PendingItem(
            item_id="item3",
            title="Old pending item",
            description="Very old pending item",
            item_type="review",
            created_date=today - timedelta(days=10),
            urgency="low"
        )
    ]


class TestPriorityTask:
    """Test PriorityTask functionality"""
    
    def test_task_creation(self):
        """Test creating a priority task"""
        task = PriorityTask(
            task_id="test1",
            title="Test Task",
            description="Test description",
            priority=TaskPriority.HIGH,
            status=TaskStatus.PENDING
        )
        
        assert task.task_id == "test1"
        assert task.title == "Test Task"
        assert task.priority == TaskPriority.HIGH
        assert task.status == TaskStatus.PENDING
    
    def test_is_overdue(self):
        """Test overdue detection"""
        yesterday = date.today() - timedelta(days=1)
        
        overdue_task = PriorityTask(
            task_id="overdue",
            title="Overdue",
            description="",
            priority=TaskPriority.HIGH,
            status=TaskStatus.PENDING,
            due_date=yesterday
        )
        
        assert overdue_task.is_overdue() is True
    
    def test_not_overdue_when_completed(self):
        """Test completed tasks are not overdue"""
        yesterday = date.today() - timedelta(days=1)
        
        completed_task = PriorityTask(
            task_id="completed",
            title="Completed",
            description="",
            priority=TaskPriority.HIGH,
            status=TaskStatus.COMPLETED,
            due_date=yesterday
        )
        
        assert completed_task.is_overdue() is False
    
    def test_is_due_today(self):
        """Test due today detection"""
        today_task = PriorityTask(
            task_id="today",
            title="Due Today",
            description="",
            priority=TaskPriority.HIGH,
            status=TaskStatus.PENDING,
            due_date=date.today()
        )
        
        assert today_task.is_due_today() is True
    
    def test_is_due_soon(self):
        """Test due soon detection"""
        soon_task = PriorityTask(
            task_id="soon",
            title="Due Soon",
            description="",
            priority=TaskPriority.HIGH,
            status=TaskStatus.PENDING,
            due_date=date.today() + timedelta(days=2)
        )
        
        assert soon_task.is_due_soon(days=3) is True
        assert soon_task.is_due_soon(days=1) is False


class TestPendingItem:
    """Test PendingItem functionality"""
    
    def test_pending_item_creation(self):
        """Test creating a pending item"""
        item = PendingItem(
            item_id="item1",
            title="Test Item",
            description="Test description",
            item_type="approval",
            created_date=date.today(),
            urgency="high"
        )
        
        assert item.item_id == "item1"
        assert item.title == "Test Item"
        assert item.urgency == "high"
    
    def test_days_pending(self):
        """Test days pending calculation"""
        created = date.today() - timedelta(days=5)
        
        item = PendingItem(
            item_id="item1",
            title="Old Item",
            description="",
            item_type="review",
            created_date=created
        )
        
        assert item.days_pending() == 5


class TestDashboardManager:
    """Test MorningDashboardManager functionality"""
    
    def test_manager_initialization(self, dashboard_manager):
        """Test manager initializes correctly"""
        assert dashboard_manager.tasks == {}
        assert dashboard_manager.pending_items == {}
        assert dashboard_manager.user_preferences == {}
    
    def test_add_task(self, dashboard_manager):
        """Test adding a task"""
        task = PriorityTask(
            task_id="task1",
            title="Test",
            description="",
            priority=TaskPriority.HIGH,
            status=TaskStatus.PENDING
        )
        
        dashboard_manager.add_task(task)
        
        assert "task1" in dashboard_manager.tasks
        assert dashboard_manager.tasks["task1"] == task
    
    def test_update_task_status(self, dashboard_manager):
        """Test updating task status"""
        task = PriorityTask(
            task_id="task1",
            title="Test",
            description="",
            priority=TaskPriority.HIGH,
            status=TaskStatus.PENDING
        )
        
        dashboard_manager.add_task(task)
        dashboard_manager.update_task_status("task1", TaskStatus.COMPLETED)
        
        assert dashboard_manager.tasks["task1"].status == TaskStatus.COMPLETED
    
    def test_add_pending_item(self, dashboard_manager):
        """Test adding a pending item"""
        item = PendingItem(
            item_id="item1",
            title="Test",
            description="",
            item_type="approval",
            created_date=date.today()
        )
        
        dashboard_manager.add_pending_item(item)
        
        assert "item1" in dashboard_manager.pending_items
    
    def test_remove_pending_item(self, dashboard_manager):
        """Test removing a pending item"""
        item = PendingItem(
            item_id="item1",
            title="Test",
            description="",
            item_type="approval",
            created_date=date.today()
        )
        
        dashboard_manager.add_pending_item(item)
        dashboard_manager.remove_pending_item("item1")
        
        assert "item1" not in dashboard_manager.pending_items
    
    def test_set_user_preferences(self, dashboard_manager):
        """Test setting user preferences"""
        prefs = {
            "name": "张三",
            "max_dashboard_tasks": 15,
            "max_pending_items": 8
        }
        
        dashboard_manager.set_user_preferences("user1", prefs)
        
        assert dashboard_manager.user_preferences["user1"] == prefs


class TestDashboardGeneration:
    """Test dashboard generation"""
    
    def test_generate_dashboard_basic(self, dashboard_manager):
        """Test basic dashboard generation"""
        dashboard = dashboard_manager.generate_dashboard("user1")
        
        assert dashboard.user_id == "user1"
        assert dashboard.generated_at is not None
        assert dashboard.greeting is not None
        assert dashboard.summary is not None
        assert isinstance(dashboard.priority_tasks, list)
        assert isinstance(dashboard.pending_items, list)
        assert isinstance(dashboard.insights, list)
        assert isinstance(dashboard.quick_actions, list)
    
    def test_generate_dashboard_with_tasks(self, dashboard_manager, sample_tasks):
        """Test dashboard with tasks"""
        for task in sample_tasks:
            dashboard_manager.add_task(task)
        
        dashboard = dashboard_manager.generate_dashboard("user1")
        
        assert len(dashboard.priority_tasks) > 0
        assert dashboard.summary.total_tasks == len(sample_tasks)
    
    def test_generate_dashboard_with_pending_items(
        self,
        dashboard_manager,
        sample_pending_items
    ):
        """Test dashboard with pending items"""
        for item in sample_pending_items:
            dashboard_manager.add_pending_item(item)
        
        dashboard = dashboard_manager.generate_dashboard("user1")
        
        assert len(dashboard.pending_items) > 0
        assert dashboard.summary.pending_items_count > 0
    
    def test_greeting_generation_morning(self, dashboard_manager):
        """Test morning greeting"""
        # This test depends on time of day, so we test the method exists
        greeting = dashboard_manager._generate_greeting("user1", datetime(2024, 1, 1, 9, 0))
        assert "早上好" in greeting
    
    def test_greeting_generation_afternoon(self, dashboard_manager):
        """Test afternoon greeting"""
        greeting = dashboard_manager._generate_greeting("user1", datetime(2024, 1, 1, 14, 0))
        assert "下午好" in greeting
    
    def test_greeting_generation_evening(self, dashboard_manager):
        """Test evening greeting"""
        greeting = dashboard_manager._generate_greeting("user1", datetime(2024, 1, 1, 20, 0))
        assert "晚上好" in greeting
    
    def test_greeting_with_user_name(self, dashboard_manager):
        """Test greeting with user name"""
        dashboard_manager.set_user_preferences("user1", {"name": "李明"})
        greeting = dashboard_manager._generate_greeting("user1", datetime(2024, 1, 1, 9, 0))
        assert "李明" in greeting


class TestPriorityTaskSorting:
    """Test priority task sorting logic"""
    
    def test_overdue_tasks_first(self, dashboard_manager, sample_tasks):
        """Test overdue tasks appear first"""
        for task in sample_tasks:
            dashboard_manager.add_task(task)
        
        priority_tasks = dashboard_manager._get_priority_tasks("user1")
        
        # First task should be the overdue one
        assert priority_tasks[0].task_id == "task5"
        assert priority_tasks[0].is_overdue()
    
    def test_due_today_tasks_priority(self, dashboard_manager, sample_tasks):
        """Test due today tasks have high priority"""
        for task in sample_tasks:
            dashboard_manager.add_task(task)
        
        priority_tasks = dashboard_manager._get_priority_tasks("user1")
        
        # After overdue, should have due today tasks
        due_today_tasks = [t for t in priority_tasks if t.is_due_today()]
        assert len(due_today_tasks) > 0
    
    def test_completed_tasks_excluded(self, dashboard_manager, sample_tasks):
        """Test completed tasks are excluded"""
        for task in sample_tasks:
            dashboard_manager.add_task(task)
        
        # Mark one task as completed
        dashboard_manager.update_task_status("task1", TaskStatus.COMPLETED)
        
        priority_tasks = dashboard_manager._get_priority_tasks("user1")
        
        # Completed task should not appear
        task_ids = [t.task_id for t in priority_tasks]
        assert "task1" not in task_ids
    
    def test_max_tasks_limit(self, dashboard_manager, sample_tasks):
        """Test maximum tasks limit"""
        for task in sample_tasks:
            dashboard_manager.add_task(task)
        
        # Set max tasks to 3
        dashboard_manager.set_user_preferences("user1", {"max_dashboard_tasks": 3})
        
        priority_tasks = dashboard_manager._get_priority_tasks("user1")
        
        assert len(priority_tasks) <= 3


class TestPendingItemsSorting:
    """Test pending items sorting"""
    
    def test_high_urgency_first(self, dashboard_manager, sample_pending_items):
        """Test high urgency items appear first"""
        for item in sample_pending_items:
            dashboard_manager.add_pending_item(item)
        
        pending_items = dashboard_manager._get_pending_items("user1")
        
        # First item should be high urgency
        assert pending_items[0].urgency == "high"
    
    def test_max_items_limit(self, dashboard_manager, sample_pending_items):
        """Test maximum items limit"""
        for item in sample_pending_items:
            dashboard_manager.add_pending_item(item)
        
        # Set max items to 2
        dashboard_manager.set_user_preferences("user1", {"max_pending_items": 2})
        
        pending_items = dashboard_manager._get_pending_items("user1")
        
        assert len(pending_items) <= 2


class TestSummaryGeneration:
    """Test summary statistics generation"""
    
    def test_summary_with_no_tasks(self, dashboard_manager):
        """Test summary with no tasks"""
        summary = dashboard_manager._generate_summary([], [])
        
        assert summary.total_tasks == 0
        assert summary.completed_today == 0
        assert summary.pending_tasks == 0
        assert summary.overdue_tasks == 0
    
    def test_summary_with_tasks(self, dashboard_manager, sample_tasks):
        """Test summary with tasks"""
        for task in sample_tasks:
            dashboard_manager.add_task(task)
        
        priority_tasks = dashboard_manager._get_priority_tasks("user1")
        summary = dashboard_manager._generate_summary(priority_tasks, [])
        
        assert summary.total_tasks == len(sample_tasks)
        assert summary.overdue_tasks > 0
        assert summary.due_today > 0
    
    def test_summary_estimated_time(self, dashboard_manager, sample_tasks):
        """Test estimated time calculation"""
        for task in sample_tasks:
            dashboard_manager.add_task(task)
        
        priority_tasks = dashboard_manager._get_priority_tasks("user1")
        summary = dashboard_manager._generate_summary(priority_tasks, [])
        
        # Should sum up estimated minutes for active tasks
        assert summary.estimated_time_minutes > 0
    
    def test_summary_completion_rate(self, dashboard_manager, sample_tasks):
        """Test completion rate calculation"""
        for task in sample_tasks:
            dashboard_manager.add_task(task)
        
        # Mark some tasks as completed
        dashboard_manager.update_task_status("task1", TaskStatus.COMPLETED)
        dashboard_manager.update_task_status("task2", TaskStatus.COMPLETED)
        
        priority_tasks = dashboard_manager._get_priority_tasks("user1")
        summary = dashboard_manager._generate_summary(priority_tasks, [])
        
        assert summary.completed_today == 2
        assert summary.completion_rate() > 0


class TestInsightsGeneration:
    """Test insights generation"""
    
    def test_overdue_warning_insight(self, dashboard_manager, sample_tasks):
        """Test overdue warning insight"""
        for task in sample_tasks:
            dashboard_manager.add_task(task)
        
        dashboard = dashboard_manager.generate_dashboard("user1")
        
        # Should have overdue warning
        overdue_insights = [
            i for i in dashboard.insights
            if i.insight_id == "overdue_warning"
        ]
        assert len(overdue_insights) > 0
        assert overdue_insights[0].insight_type == "warning"
    
    def test_due_today_insight(self, dashboard_manager, sample_tasks):
        """Test due today insight"""
        for task in sample_tasks:
            dashboard_manager.add_task(task)
        
        dashboard = dashboard_manager.generate_dashboard("user1")
        
        # Should have due today insight
        due_today_insights = [
            i for i in dashboard.insights
            if i.insight_id == "due_today"
        ]
        assert len(due_today_insights) > 0
    
    def test_time_estimate_insight(self, dashboard_manager, sample_tasks):
        """Test time estimate insight"""
        for task in sample_tasks:
            dashboard_manager.add_task(task)
        
        dashboard = dashboard_manager.generate_dashboard("user1")
        
        # Should have time estimate
        time_insights = [
            i for i in dashboard.insights
            if i.insight_id == "time_estimate"
        ]
        assert len(time_insights) > 0
    
    def test_old_pending_insight(self, dashboard_manager, sample_pending_items):
        """Test old pending items insight"""
        for item in sample_pending_items:
            dashboard_manager.add_pending_item(item)
        
        dashboard = dashboard_manager.generate_dashboard("user1")
        
        # Should have old pending warning
        old_pending_insights = [
            i for i in dashboard.insights
            if i.insight_id == "old_pending"
        ]
        assert len(old_pending_insights) > 0
        assert old_pending_insights[0].insight_type == "warning"
    
    def test_all_done_insight(self, dashboard_manager):
        """Test all done success insight"""
        # Add only completed tasks
        task = PriorityTask(
            task_id="task1",
            title="Completed",
            description="",
            priority=TaskPriority.HIGH,
            status=TaskStatus.COMPLETED
        )
        dashboard_manager.add_task(task)
        
        dashboard = dashboard_manager.generate_dashboard("user1")
        
        # Should have success insight
        success_insights = [
            i for i in dashboard.insights
            if i.insight_type == "success"
        ]
        assert len(success_insights) > 0


class TestQuickActions:
    """Test quick actions generation"""
    
    def test_quick_actions_generated(self, dashboard_manager):
        """Test quick actions are generated"""
        dashboard = dashboard_manager.generate_dashboard("user1")
        
        assert len(dashboard.quick_actions) > 0
        assert len(dashboard.quick_actions) <= 5  # Progressive disclosure limit
    
    def test_start_priority_task_action(self, dashboard_manager, sample_tasks):
        """Test start priority task action"""
        for task in sample_tasks:
            dashboard_manager.add_task(task)
        
        dashboard = dashboard_manager.generate_dashboard("user1")
        
        # Should have action to start first priority task
        start_actions = [
            a for a in dashboard.quick_actions
            if a["action_id"] == "start_priority_task"
        ]
        assert len(start_actions) > 0
    
    def test_common_quick_actions(self, dashboard_manager):
        """Test common quick actions are included"""
        dashboard = dashboard_manager.generate_dashboard("user1")
        
        action_ids = [a["action_id"] for a in dashboard.quick_actions]
        
        # Should have common actions
        assert "new_transaction" in action_ids or len(dashboard.quick_actions) == 5


class TestHelperMethods:
    """Test helper methods"""
    
    def test_get_task_by_id(self, dashboard_manager, sample_tasks):
        """Test getting task by ID"""
        for task in sample_tasks:
            dashboard_manager.add_task(task)
        
        task = dashboard_manager.get_task_by_id("task1")
        
        assert task is not None
        assert task.task_id == "task1"
    
    def test_get_nonexistent_task(self, dashboard_manager):
        """Test getting non-existent task"""
        task = dashboard_manager.get_task_by_id("nonexistent")
        
        assert task is None
    
    def test_mark_task_completed(self, dashboard_manager, sample_tasks):
        """Test marking task as completed"""
        dashboard_manager.add_task(sample_tasks[0])
        
        dashboard_manager.mark_task_completed("task1")
        
        task = dashboard_manager.get_task_by_id("task1")
        assert task.status == TaskStatus.COMPLETED
    
    def test_get_tasks_by_category(self, dashboard_manager, sample_tasks):
        """Test getting tasks by category"""
        for task in sample_tasks:
            dashboard_manager.add_task(task)
        
        payroll_tasks = dashboard_manager.get_tasks_by_category("payroll")
        
        assert len(payroll_tasks) > 0
        assert all(t.category == "payroll" for t in payroll_tasks)
    
    def test_get_tasks_by_priority(self, dashboard_manager, sample_tasks):
        """Test getting tasks by priority"""
        for task in sample_tasks:
            dashboard_manager.add_task(task)
        
        critical_tasks = dashboard_manager.get_tasks_by_priority(TaskPriority.CRITICAL)
        
        assert len(critical_tasks) > 0
        assert all(t.priority == TaskPriority.CRITICAL for t in critical_tasks)
    
    def test_get_overdue_tasks(self, dashboard_manager, sample_tasks):
        """Test getting overdue tasks"""
        for task in sample_tasks:
            dashboard_manager.add_task(task)
        
        overdue_tasks = dashboard_manager.get_overdue_tasks()
        
        assert len(overdue_tasks) > 0
        assert all(t.is_overdue() for t in overdue_tasks)
    
    def test_get_due_today_tasks(self, dashboard_manager, sample_tasks):
        """Test getting due today tasks"""
        for task in sample_tasks:
            dashboard_manager.add_task(task)
        
        due_today_tasks = dashboard_manager.get_due_today_tasks()
        
        assert len(due_today_tasks) > 0
        assert all(t.is_due_today() for t in due_today_tasks)


class TestIntegration:
    """Integration tests for morning dashboard"""
    
    def test_complete_dashboard_workflow(
        self,
        dashboard_manager,
        sample_tasks,
        sample_pending_items
    ):
        """Test complete dashboard workflow"""
        # Set up user preferences
        dashboard_manager.set_user_preferences("user1", {
            "name": "王芳",
            "max_dashboard_tasks": 10,
            "max_pending_items": 5
        })
        
        # Add tasks and pending items
        for task in sample_tasks:
            dashboard_manager.add_task(task)
        
        for item in sample_pending_items:
            dashboard_manager.add_pending_item(item)
        
        # Generate dashboard
        dashboard = dashboard_manager.generate_dashboard("user1")
        
        # Verify dashboard structure
        assert dashboard.user_id == "user1"
        assert "王芳" in dashboard.greeting
        assert len(dashboard.priority_tasks) > 0
        assert len(dashboard.pending_items) > 0
        assert len(dashboard.insights) > 0
        assert len(dashboard.quick_actions) > 0
        
        # Verify summary
        assert dashboard.summary.total_tasks == len(sample_tasks)
        assert dashboard.summary.overdue_tasks > 0
        assert dashboard.summary.due_today > 0
        assert dashboard.summary.estimated_time_minutes > 0
        
        # Verify task prioritization
        first_task = dashboard.priority_tasks[0]
        assert first_task.is_overdue()  # Overdue tasks should be first
    
    def test_dashboard_updates_with_task_completion(
        self,
        dashboard_manager,
        sample_tasks
    ):
        """Test dashboard updates when tasks are completed"""
        for task in sample_tasks:
            dashboard_manager.add_task(task)
        
        # Generate initial dashboard
        dashboard1 = dashboard_manager.generate_dashboard("user1")
        initial_pending = dashboard1.summary.pending_tasks
        
        # Complete a task
        dashboard_manager.mark_task_completed("task1")
        
        # Generate updated dashboard
        dashboard2 = dashboard_manager.generate_dashboard("user1")
        
        # Verify changes
        assert dashboard2.summary.completed_today > dashboard1.summary.completed_today
        assert "task1" not in [t.task_id for t in dashboard2.priority_tasks]
