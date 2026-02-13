"""
Morning Dashboard Implementation

This module implements the smart morning dashboard that displays priority tasks,
pending items, and personalized content for small business accountants.

Requirements: 1.1
"""

from datetime import datetime, timedelta, date
from typing import List, Dict, Optional, Any
from dataclasses import dataclass, field
from enum import Enum


class TaskPriority(Enum):
    """Task priority levels"""
    CRITICAL = "critical"  # Must be done today
    HIGH = "high"  # Should be done today
    MEDIUM = "medium"  # Can be done today
    LOW = "low"  # Nice to have


class TaskStatus(Enum):
    """Task completion status"""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    OVERDUE = "overdue"


@dataclass
class PriorityTask:
    """A priority task for the dashboard"""
    task_id: str
    title: str
    description: str
    priority: TaskPriority
    status: TaskStatus
    due_date: Optional[date] = None
    estimated_minutes: int = 0
    category: str = "general"
    context: Dict[str, Any] = field(default_factory=dict)
    
    def is_overdue(self) -> bool:
        """Check if task is overdue"""
        if not self.due_date:
            return False
        return self.due_date < date.today() and self.status != TaskStatus.COMPLETED
    
    def is_due_today(self) -> bool:
        """Check if task is due today"""
        if not self.due_date:
            return False
        return self.due_date == date.today()
    
    def is_due_soon(self, days: int = 3) -> bool:
        """Check if task is due within specified days"""
        if not self.due_date:
            return False
        return date.today() <= self.due_date <= date.today() + timedelta(days=days)


@dataclass
class PendingItem:
    """A pending item requiring attention"""
    item_id: str
    title: str
    description: str
    item_type: str  # e.g., "transaction", "approval", "review"
    created_date: date
    urgency: str = "normal"  # "low", "normal", "high"
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def days_pending(self) -> int:
        """Calculate days since creation"""
        return (date.today() - self.created_date).days


@dataclass
class DashboardInsight:
    """An insight or recommendation for the user"""
    insight_id: str
    title: str
    message: str
    insight_type: str  # "tip", "warning", "info", "success"
    action_text: Optional[str] = None
    action_data: Optional[Dict[str, Any]] = None


@dataclass
class DashboardSummary:
    """Summary statistics for the dashboard"""
    total_tasks: int
    completed_today: int
    pending_tasks: int
    overdue_tasks: int
    due_today: int
    estimated_time_minutes: int
    pending_items_count: int
    
    def completion_rate(self) -> float:
        """Calculate completion rate"""
        if self.total_tasks == 0:
            return 0.0
        return self.completed_today / self.total_tasks


@dataclass
class MorningDashboard:
    """Complete morning dashboard data"""
    user_id: str
    generated_at: datetime
    greeting: str
    summary: DashboardSummary
    priority_tasks: List[PriorityTask]
    pending_items: List[PendingItem]
    insights: List[DashboardInsight]
    quick_actions: List[Dict[str, Any]]


class MorningDashboardManager:
    """
    Manages the morning dashboard for small business accountants.
    
    Features:
    - Priority task identification and display
    - Pending items tracking
    - Time-sensitive task highlighting
    - Personalized insights and recommendations
    - Integration with ContextEngine
    """
    
    def __init__(self, context_engine=None):
        self.context_engine = context_engine
        self.tasks: Dict[str, PriorityTask] = {}
        self.pending_items: Dict[str, PendingItem] = {}
        self.user_preferences: Dict[str, Any] = {}
    
    def add_task(self, task: PriorityTask):
        """Add a task to track"""
        self.tasks[task.task_id] = task
    
    def update_task_status(self, task_id: str, status: TaskStatus):
        """Update task status"""
        if task_id in self.tasks:
            self.tasks[task_id].status = status
    
    def add_pending_item(self, item: PendingItem):
        """Add a pending item"""
        self.pending_items[item.item_id] = item
    
    def remove_pending_item(self, item_id: str):
        """Remove a pending item"""
        self.pending_items.pop(item_id, None)
    
    def set_user_preferences(self, user_id: str, preferences: Dict[str, Any]):
        """Set user preferences for dashboard customization"""
        self.user_preferences[user_id] = preferences
    
    def generate_dashboard(self, user_id: str) -> MorningDashboard:
        """
        Generate the morning dashboard for a user.
        
        Args:
            user_id: User identifier
            
        Returns:
            Complete morning dashboard data
        """
        now = datetime.now()
        
        # Generate greeting
        greeting = self._generate_greeting(user_id, now)
        
        # Get priority tasks
        priority_tasks = self._get_priority_tasks(user_id)
        
        # Get pending items
        pending_items = self._get_pending_items(user_id)
        
        # Generate summary
        summary = self._generate_summary(priority_tasks, pending_items)
        
        # Generate insights
        insights = self._generate_insights(user_id, priority_tasks, pending_items, summary)
        
        # Generate quick actions
        quick_actions = self._generate_quick_actions(user_id, priority_tasks)
        
        return MorningDashboard(
            user_id=user_id,
            generated_at=now,
            greeting=greeting,
            summary=summary,
            priority_tasks=priority_tasks,
            pending_items=pending_items,
            insights=insights,
            quick_actions=quick_actions
        )
    
    def _generate_greeting(self, user_id: str, now: datetime) -> str:
        """Generate personalized greeting"""
        hour = now.hour
        
        if hour < 12:
            time_greeting = "早上好"
        elif hour < 18:
            time_greeting = "下午好"
        else:
            time_greeting = "晚上好"
        
        # Get user name from preferences
        prefs = self.user_preferences.get(user_id, {})
        user_name = prefs.get("name", "")
        
        if user_name:
            return f"{time_greeting}，{user_name}！"
        else:
            return f"{time_greeting}！"
    
    def _get_priority_tasks(self, user_id: str) -> List[PriorityTask]:
        """
        Get priority tasks for the user.
        
        Priority order:
        1. Overdue tasks
        2. Due today tasks
        3. High priority tasks
        4. Due soon tasks
        5. Other tasks by priority
        """
        tasks = list(self.tasks.values())
        
        # Update overdue status
        for task in tasks:
            if task.is_overdue():
                task.status = TaskStatus.OVERDUE
        
        # Filter out completed tasks
        active_tasks = [t for t in tasks if t.status != TaskStatus.COMPLETED]
        
        # Sort by priority
        def task_sort_key(task: PriorityTask):
            # Overdue tasks first
            if task.is_overdue():
                return (0, task.due_date or date.max)
            
            # Due today tasks
            if task.is_due_today():
                return (1, task.priority.value)
            
            # High priority tasks
            if task.priority == TaskPriority.CRITICAL:
                return (2, task.due_date or date.max)
            
            # Due soon tasks
            if task.is_due_soon():
                return (3, task.due_date or date.max)
            
            # Other tasks by priority
            priority_order = {
                TaskPriority.CRITICAL: 4,
                TaskPriority.HIGH: 5,
                TaskPriority.MEDIUM: 6,
                TaskPriority.LOW: 7
            }
            return (priority_order.get(task.priority, 8), task.due_date or date.max)
        
        sorted_tasks = sorted(active_tasks, key=task_sort_key)
        
        # Limit to top tasks (configurable)
        max_tasks = self.user_preferences.get(user_id, {}).get("max_dashboard_tasks", 10)
        return sorted_tasks[:max_tasks]
    
    def _get_pending_items(self, user_id: str) -> List[PendingItem]:
        """Get pending items for the user"""
        items = list(self.pending_items.values())
        
        # Sort by urgency and age
        def item_sort_key(item: PendingItem):
            urgency_order = {"high": 0, "normal": 1, "low": 2}
            return (urgency_order.get(item.urgency, 3), -item.days_pending())
        
        sorted_items = sorted(items, key=item_sort_key)
        
        # Limit to top items
        max_items = self.user_preferences.get(user_id, {}).get("max_pending_items", 5)
        return sorted_items[:max_items]
    
    def _generate_summary(
        self,
        priority_tasks: List[PriorityTask],
        pending_items: List[PendingItem]
    ) -> DashboardSummary:
        """Generate summary statistics"""
        all_tasks = list(self.tasks.values())
        
        # Count tasks
        total_tasks = len(all_tasks)
        completed_today = sum(
            1 for t in all_tasks
            if t.status == TaskStatus.COMPLETED
        )
        pending_tasks = sum(
            1 for t in all_tasks
            if t.status in [TaskStatus.PENDING, TaskStatus.IN_PROGRESS]
        )
        overdue_tasks = sum(1 for t in priority_tasks if t.is_overdue())
        due_today = sum(1 for t in priority_tasks if t.is_due_today())
        
        # Calculate estimated time
        estimated_time = sum(
            t.estimated_minutes for t in priority_tasks
            if t.status != TaskStatus.COMPLETED
        )
        
        return DashboardSummary(
            total_tasks=total_tasks,
            completed_today=completed_today,
            pending_tasks=pending_tasks,
            overdue_tasks=overdue_tasks,
            due_today=due_today,
            estimated_time_minutes=estimated_time,
            pending_items_count=len(pending_items)
        )
    
    def _generate_insights(
        self,
        user_id: str,
        priority_tasks: List[PriorityTask],
        pending_items: List[PendingItem],
        summary: DashboardSummary
    ) -> List[DashboardInsight]:
        """Generate insights and recommendations"""
        insights = []
        
        # Overdue tasks warning
        if summary.overdue_tasks > 0:
            insights.append(DashboardInsight(
                insight_id="overdue_warning",
                title="逾期任务提醒",
                message=f"您有 {summary.overdue_tasks} 个逾期任务需要处理",
                insight_type="warning",
                action_text="查看逾期任务",
                action_data={"filter": "overdue"}
            ))
        
        # Due today tasks
        if summary.due_today > 0:
            insights.append(DashboardInsight(
                insight_id="due_today",
                title="今日到期",
                message=f"今天有 {summary.due_today} 个任务需要完成",
                insight_type="info",
                action_text="查看今日任务",
                action_data={"filter": "due_today"}
            ))
        
        # Time estimate
        if summary.estimated_time_minutes > 0:
            hours = summary.estimated_time_minutes // 60
            minutes = summary.estimated_time_minutes % 60
            time_str = f"{hours}小时{minutes}分钟" if hours > 0 else f"{minutes}分钟"
            
            insights.append(DashboardInsight(
                insight_id="time_estimate",
                title="预计工作时间",
                message=f"今日任务预计需要 {time_str}",
                insight_type="info"
            ))
        
        # Pending items alert
        if summary.pending_items_count > 0:
            insights.append(DashboardInsight(
                insight_id="pending_items",
                title="待处理事项",
                message=f"您有 {summary.pending_items_count} 个待处理事项",
                insight_type="info",
                action_text="查看待处理",
                action_data={"view": "pending"}
            ))
        
        # Old pending items
        old_items = [item for item in pending_items if item.days_pending() > 7]
        if old_items:
            insights.append(DashboardInsight(
                insight_id="old_pending",
                title="长期待处理",
                message=f"有 {len(old_items)} 个事项已待处理超过7天",
                insight_type="warning",
                action_text="查看详情",
                action_data={"filter": "old_pending"}
            ))
        
        # Positive feedback
        if summary.completed_today > 0 and summary.pending_tasks == 0:
            insights.append(DashboardInsight(
                insight_id="all_done",
                title="太棒了！",
                message="所有任务都已完成，今天可以早点休息了！",
                insight_type="success"
            ))
        
        # Use context engine for personalized insights
        if self.context_engine:
            context_insights = self._get_context_insights(user_id, priority_tasks)
            insights.extend(context_insights)
        
        return insights
    
    def _get_context_insights(
        self,
        user_id: str,
        priority_tasks: List[PriorityTask]
    ) -> List[DashboardInsight]:
        """Get insights from context engine"""
        insights = []
        
        # This would integrate with the actual ContextEngine
        # For now, return empty list
        # In real implementation:
        # context = self.context_engine.analyze_current_context(user_id)
        # insights = self.context_engine.generate_insights(context, priority_tasks)
        
        return insights
    
    def _generate_quick_actions(
        self,
        user_id: str,
        priority_tasks: List[PriorityTask]
    ) -> List[Dict[str, Any]]:
        """Generate quick action buttons"""
        actions = []
        
        # Start first priority task
        if priority_tasks:
            first_task = priority_tasks[0]
            actions.append({
                "action_id": "start_priority_task",
                "label": f"开始：{first_task.title}",
                "icon": "play",
                "task_id": first_task.task_id
            })
        
        # Common quick actions
        actions.extend([
            {
                "action_id": "new_transaction",
                "label": "录入交易",
                "icon": "plus",
                "workflow": "transaction_entry"
            },
            {
                "action_id": "view_reports",
                "label": "查看报表",
                "icon": "chart",
                "workflow": "view_reports"
            },
            {
                "action_id": "check_pending",
                "label": "待处理事项",
                "icon": "list",
                "workflow": "pending_items"
            }
        ])
        
        # Limit to 5 quick actions (progressive disclosure)
        return actions[:5]
    
    def get_task_by_id(self, task_id: str) -> Optional[PriorityTask]:
        """Get a task by ID"""
        return self.tasks.get(task_id)
    
    def get_pending_item_by_id(self, item_id: str) -> Optional[PendingItem]:
        """Get a pending item by ID"""
        return self.pending_items.get(item_id)
    
    def mark_task_completed(self, task_id: str):
        """Mark a task as completed"""
        if task_id in self.tasks:
            self.tasks[task_id].status = TaskStatus.COMPLETED
    
    def get_tasks_by_category(self, category: str) -> List[PriorityTask]:
        """Get all tasks in a category"""
        return [t for t in self.tasks.values() if t.category == category]
    
    def get_tasks_by_priority(self, priority: TaskPriority) -> List[PriorityTask]:
        """Get all tasks with specific priority"""
        return [t for t in self.tasks.values() if t.priority == priority]
    
    def get_overdue_tasks(self) -> List[PriorityTask]:
        """Get all overdue tasks"""
        return [t for t in self.tasks.values() if t.is_overdue()]
    
    def get_due_today_tasks(self) -> List[PriorityTask]:
        """Get all tasks due today"""
        return [t for t in self.tasks.values() if t.is_due_today()]
