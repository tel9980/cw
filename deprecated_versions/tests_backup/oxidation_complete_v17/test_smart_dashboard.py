"""
Unit Tests for Smart Dashboard - 智能工作台单元测试

测试智能工作台的所有功能
"""

import pytest
from datetime import date, datetime, timedelta
from oxidation_complete_v17.workflow.smart_dashboard import (
    SmartDashboardManager,
    PriorityTask,
    DashboardAlert,
    QuickAction,
    TaskPriority,
    TaskStatus,
    AlertType
)


class TestSmartDashboardManager:
    """测试智能工作台管理器"""
    
    @pytest.fixture
    def dashboard_manager(self):
        """创建工作台管理器实例"""
        return SmartDashboardManager()
    
    def test_add_task(self, dashboard_manager):
        """测试添加任务"""
        task = PriorityTask(
            task_id="task_001",
            title="录入交易",
            description="录入今日交易记录",
            priority=TaskPriority.HIGH,
            status=TaskStatus.PENDING,
            due_date=date.today(),
            estimated_minutes=30
        )
        
        dashboard_manager.add_task(task)
        assert "task_001" in dashboard_manager.tasks
        assert dashboard_manager.tasks["task_001"].title == "录入交易"
    
    def test_update_task_status(self, dashboard_manager):
        """测试更新任务状态"""
        task = PriorityTask(
            task_id="task_002",
            title="对账",
            description="银行流水对账",
            priority=TaskPriority.MEDIUM,
            status=TaskStatus.PENDING
        )
        
        dashboard_manager.add_task(task)
        dashboard_manager.update_task_status("task_002", TaskStatus.COMPLETED)
        
        assert dashboard_manager.tasks["task_002"].status == TaskStatus.COMPLETED
    
    def test_add_alert(self, dashboard_manager):
        """测试添加提醒"""
        alert = DashboardAlert(
            alert_id="alert_001",
            alert_type=AlertType.OVERDUE_PAYMENT,
            title="超期未收款",
            message="有3笔订单超期未收款",
            severity="warning",
            created_date=date.today()
        )
        
        dashboard_manager.add_alert(alert)
        assert "alert_001" in dashboard_manager.alerts
        assert dashboard_manager.alerts["alert_001"].title == "超期未收款"
    
    def test_remove_alert(self, dashboard_manager):
        """测试移除提醒"""
        alert = DashboardAlert(
            alert_id="alert_002",
            alert_type=AlertType.TAX_FILING,
            title="税务申报",
            message="增值税申报截止日期临近",
            severity="info",
            created_date=date.today()
        )
        
        dashboard_manager.add_alert(alert)
        dashboard_manager.remove_alert("alert_002")
        
        assert "alert_002" not in dashboard_manager.alerts
    
    def test_set_user_preferences(self, dashboard_manager):
        """测试设置用户偏好"""
        preferences = {
            "name": "张会计",
            "max_dashboard_tasks": 8,
            "max_dashboard_alerts": 6
        }
        
        dashboard_manager.set_user_preferences("user_001", preferences)
        assert "user_001" in dashboard_manager.user_preferences
        assert dashboard_manager.user_preferences["user_001"]["name"] == "张会计"
    
    def test_generate_greeting_morning(self, dashboard_manager):
        """测试生成早晨问候语"""
        morning_time = datetime(2026, 2, 10, 9, 0, 0)
        greeting = dashboard_manager._generate_greeting("user_001", morning_time)
        assert "早上好" in greeting
    
    def test_generate_greeting_afternoon(self, dashboard_manager):
        """测试生成下午问候语"""
        afternoon_time = datetime(2026, 2, 10, 14, 0, 0)
        greeting = dashboard_manager._generate_greeting("user_001", afternoon_time)
        assert "下午好" in greeting
    
    def test_generate_greeting_evening(self, dashboard_manager):
        """测试生成晚上问候语"""
        evening_time = datetime(2026, 2, 10, 20, 0, 0)
        greeting = dashboard_manager._generate_greeting("user_001", evening_time)
        assert "晚上好" in greeting
    
    def test_generate_greeting_with_name(self, dashboard_manager):
        """测试生成带用户名的问候语"""
        dashboard_manager.set_user_preferences("user_001", {"name": "李会计"})
        morning_time = datetime(2026, 2, 10, 9, 0, 0)
        greeting = dashboard_manager._generate_greeting("user_001", morning_time)
        assert "李会计" in greeting
    
    def test_task_is_overdue(self):
        """测试任务逾期判断"""
        overdue_task = PriorityTask(
            task_id="task_003",
            title="逾期任务",
            description="这是一个逾期任务",
            priority=TaskPriority.HIGH,
            status=TaskStatus.PENDING,
            due_date=date.today() - timedelta(days=1)
        )
        
        assert overdue_task.is_overdue() is True
    
    def test_task_is_due_today(self):
        """测试任务今天到期判断"""
        today_task = PriorityTask(
            task_id="task_004",
            title="今日任务",
            description="今天到期的任务",
            priority=TaskPriority.MEDIUM,
            status=TaskStatus.PENDING,
            due_date=date.today()
        )
        
        assert today_task.is_due_today() is True
    
    def test_task_is_due_soon(self):
        """测试任务即将到期判断"""
        soon_task = PriorityTask(
            task_id="task_005",
            title="即将到期任务",
            description="3天后到期的任务",
            priority=TaskPriority.LOW,
            status=TaskStatus.PENDING,
            due_date=date.today() + timedelta(days=2)
        )
        
        assert soon_task.is_due_soon(days=3) is True
    
    def test_get_priority_tasks_sorting(self, dashboard_manager):
        """测试优先任务排序"""
        # 添加不同优先级和到期日期的任务
        tasks = [
            PriorityTask(
                task_id="task_low",
                title="低优先级",
                description="低优先级任务",
                priority=TaskPriority.LOW,
                status=TaskStatus.PENDING,
                due_date=date.today() + timedelta(days=7)
            ),
            PriorityTask(
                task_id="task_overdue",
                title="逾期任务",
                description="逾期的任务",
                priority=TaskPriority.MEDIUM,
                status=TaskStatus.PENDING,
                due_date=date.today() - timedelta(days=1)
            ),
            PriorityTask(
                task_id="task_today",
                title="今日任务",
                description="今天到期的任务",
                priority=TaskPriority.HIGH,
                status=TaskStatus.PENDING,
                due_date=date.today()
            ),
            PriorityTask(
                task_id="task_critical",
                title="紧急任务",
                description="紧急任务",
                priority=TaskPriority.CRITICAL,
                status=TaskStatus.PENDING,
                due_date=date.today() + timedelta(days=1)
            )
        ]
        
        for task in tasks:
            dashboard_manager.add_task(task)
        
        priority_tasks = dashboard_manager._get_priority_tasks("user_001")
        
        # 验证排序:逾期任务应该在最前面
        assert priority_tasks[0].task_id == "task_overdue"
        # 今日任务应该在第二位
        assert priority_tasks[1].task_id == "task_today"
    
    def test_get_priority_tasks_excludes_completed(self, dashboard_manager):
        """测试优先任务列表不包含已完成任务"""
        completed_task = PriorityTask(
            task_id="task_completed",
            title="已完成任务",
            description="这是已完成的任务",
            priority=TaskPriority.HIGH,
            status=TaskStatus.COMPLETED,
            due_date=date.today()
        )
        
        pending_task = PriorityTask(
            task_id="task_pending",
            title="待处理任务",
            description="这是待处理的任务",
            priority=TaskPriority.MEDIUM,
            status=TaskStatus.PENDING,
            due_date=date.today()
        )
        
        dashboard_manager.add_task(completed_task)
        dashboard_manager.add_task(pending_task)
        
        priority_tasks = dashboard_manager._get_priority_tasks("user_001")
        
        # 只应该包含待处理任务
        assert len(priority_tasks) == 1
        assert priority_tasks[0].task_id == "task_pending"
    
    def test_get_priority_tasks_max_limit(self, dashboard_manager):
        """测试优先任务列表数量限制"""
        # 设置最大显示5个任务
        dashboard_manager.set_user_preferences("user_001", {"max_dashboard_tasks": 5})
        
        # 添加10个任务
        for i in range(10):
            task = PriorityTask(
                task_id=f"task_{i}",
                title=f"任务{i}",
                description=f"任务{i}描述",
                priority=TaskPriority.MEDIUM,
                status=TaskStatus.PENDING
            )
            dashboard_manager.add_task(task)
        
        priority_tasks = dashboard_manager._get_priority_tasks("user_001")
        
        # 应该只返回5个任务
        assert len(priority_tasks) <= 5
    
    def test_generate_tax_filing_alerts_vat(self, dashboard_manager):
        """测试生成增值税申报提醒"""
        # 模拟当前日期为月初
        alerts = dashboard_manager._generate_tax_filing_alerts()
        
        # 应该包含增值税申报提醒
        vat_alerts = [a for a in alerts if a.alert_type == AlertType.TAX_FILING and "增值税" in a.title]
        assert len(vat_alerts) > 0
    
    def test_generate_quick_actions(self, dashboard_manager):
        """测试生成快捷操作"""
        quick_actions = dashboard_manager._generate_quick_actions("user_001")
        
        # 应该返回5个快捷操作
        assert len(quick_actions) == 5
        
        # 验证快捷操作内容
        action_labels = [action.label for action in quick_actions]
        assert "录入交易" in action_labels
        assert "新建订单" in action_labels
        assert "导入流水" in action_labels
        assert "对账" in action_labels
        assert "查看报表" in action_labels
    
    def test_generate_summary(self, dashboard_manager):
        """测试生成汇总统计"""
        # 添加任务
        tasks = [
            PriorityTask(
                task_id="task_1",
                title="任务1",
                description="任务1",
                priority=TaskPriority.HIGH,
                status=TaskStatus.COMPLETED
            ),
            PriorityTask(
                task_id="task_2",
                title="任务2",
                description="任务2",
                priority=TaskPriority.MEDIUM,
                status=TaskStatus.PENDING,
                due_date=date.today()
            ),
            PriorityTask(
                task_id="task_3",
                title="任务3",
                description="任务3",
                priority=TaskPriority.LOW,
                status=TaskStatus.PENDING,
                due_date=date.today() - timedelta(days=1)
            )
        ]
        
        for task in tasks:
            dashboard_manager.add_task(task)
        
        priority_tasks = dashboard_manager._get_priority_tasks("user_001")
        alerts = []
        
        summary = dashboard_manager._generate_summary(priority_tasks, alerts)
        
        # 验证统计数据
        assert summary.total_tasks == 3
        assert summary.completed_today == 1
        # pending_tasks只计算PENDING和IN_PROGRESS状态的任务,不包括OVERDUE
        # 因为task_3会被标记为OVERDUE状态
        assert summary.pending_tasks == 1  # 只有task_2
        assert summary.overdue_tasks == 1  # task_3
        assert summary.due_today == 1  # task_2
    
    def test_generate_insights_overdue_tasks(self, dashboard_manager):
        """测试生成逾期任务洞察"""
        # 添加逾期任务
        overdue_task = PriorityTask(
            task_id="task_overdue",
            title="逾期任务",
            description="逾期任务",
            priority=TaskPriority.HIGH,
            status=TaskStatus.PENDING,
            due_date=date.today() - timedelta(days=1)
        )
        dashboard_manager.add_task(overdue_task)
        
        priority_tasks = dashboard_manager._get_priority_tasks("user_001")
        alerts = []
        summary = dashboard_manager._generate_summary(priority_tasks, alerts)
        
        insights = dashboard_manager._generate_insights("user_001", summary, alerts)
        
        # 应该包含逾期任务提示
        assert any("逾期任务" in insight for insight in insights)
    
    def test_generate_insights_all_completed(self, dashboard_manager):
        """测试生成全部完成洞察"""
        # 添加已完成任务
        completed_task = PriorityTask(
            task_id="task_completed",
            title="已完成任务",
            description="已完成任务",
            priority=TaskPriority.HIGH,
            status=TaskStatus.COMPLETED
        )
        dashboard_manager.add_task(completed_task)
        
        priority_tasks = dashboard_manager._get_priority_tasks("user_001")
        alerts = []
        summary = dashboard_manager._generate_summary(priority_tasks, alerts)
        
        insights = dashboard_manager._generate_insights("user_001", summary, alerts)
        
        # 应该包含完成提示
        assert any("完成" in insight for insight in insights)
    
    def test_mark_task_completed(self, dashboard_manager):
        """测试标记任务完成"""
        task = PriorityTask(
            task_id="task_mark",
            title="待标记任务",
            description="待标记任务",
            priority=TaskPriority.MEDIUM,
            status=TaskStatus.PENDING
        )
        dashboard_manager.add_task(task)
        
        dashboard_manager.mark_task_completed("task_mark")
        
        assert dashboard_manager.tasks["task_mark"].status == TaskStatus.COMPLETED
    
    def test_get_task_by_id(self, dashboard_manager):
        """测试根据ID获取任务"""
        task = PriorityTask(
            task_id="task_get",
            title="获取任务",
            description="获取任务",
            priority=TaskPriority.LOW,
            status=TaskStatus.PENDING
        )
        dashboard_manager.add_task(task)
        
        retrieved_task = dashboard_manager.get_task_by_id("task_get")
        
        assert retrieved_task is not None
        assert retrieved_task.title == "获取任务"
    
    def test_get_alert_by_id(self, dashboard_manager):
        """测试根据ID获取提醒"""
        alert = DashboardAlert(
            alert_id="alert_get",
            alert_type=AlertType.GENERAL,
            title="获取提醒",
            message="获取提醒",
            severity="info",
            created_date=date.today()
        )
        dashboard_manager.add_alert(alert)
        
        retrieved_alert = dashboard_manager.get_alert_by_id("alert_get")
        
        assert retrieved_alert is not None
        assert retrieved_alert.title == "获取提醒"
    
    def test_get_overdue_tasks(self, dashboard_manager):
        """测试获取所有逾期任务"""
        overdue_task = PriorityTask(
            task_id="task_overdue_1",
            title="逾期任务1",
            description="逾期任务1",
            priority=TaskPriority.HIGH,
            status=TaskStatus.PENDING,
            due_date=date.today() - timedelta(days=1)
        )
        
        normal_task = PriorityTask(
            task_id="task_normal",
            title="正常任务",
            description="正常任务",
            priority=TaskPriority.MEDIUM,
            status=TaskStatus.PENDING,
            due_date=date.today() + timedelta(days=1)
        )
        
        dashboard_manager.add_task(overdue_task)
        dashboard_manager.add_task(normal_task)
        
        overdue_tasks = dashboard_manager.get_overdue_tasks()
        
        assert len(overdue_tasks) == 1
        assert overdue_tasks[0].task_id == "task_overdue_1"
    
    def test_get_due_today_tasks(self, dashboard_manager):
        """测试获取今天到期的任务"""
        today_task = PriorityTask(
            task_id="task_today_1",
            title="今日任务1",
            description="今日任务1",
            priority=TaskPriority.HIGH,
            status=TaskStatus.PENDING,
            due_date=date.today()
        )
        
        future_task = PriorityTask(
            task_id="task_future",
            title="未来任务",
            description="未来任务",
            priority=TaskPriority.MEDIUM,
            status=TaskStatus.PENDING,
            due_date=date.today() + timedelta(days=1)
        )
        
        dashboard_manager.add_task(today_task)
        dashboard_manager.add_task(future_task)
        
        due_today_tasks = dashboard_manager.get_due_today_tasks()
        
        assert len(due_today_tasks) == 1
        assert due_today_tasks[0].task_id == "task_today_1"
    
    def test_generate_dashboard_complete(self, dashboard_manager):
        """测试生成完整工作台"""
        # 添加任务
        task = PriorityTask(
            task_id="task_complete",
            title="完整测试任务",
            description="完整测试任务",
            priority=TaskPriority.HIGH,
            status=TaskStatus.PENDING,
            due_date=date.today()
        )
        dashboard_manager.add_task(task)
        
        # 添加提醒
        alert = DashboardAlert(
            alert_id="alert_complete",
            alert_type=AlertType.GENERAL,
            title="完整测试提醒",
            message="完整测试提醒",
            severity="info",
            created_date=date.today()
        )
        dashboard_manager.add_alert(alert)
        
        # 生成工作台
        dashboard = dashboard_manager.generate_dashboard("user_001")
        
        # 验证工作台数据
        assert dashboard.user_id == "user_001"
        assert dashboard.greeting is not None
        assert dashboard.summary is not None
        assert len(dashboard.priority_tasks) > 0
        assert len(dashboard.alerts) > 0
        assert len(dashboard.quick_actions) == 5
        assert len(dashboard.insights) > 0
    
    def test_dashboard_summary_completion_rate(self):
        """测试工作台汇总完成率计算"""
        from oxidation_complete_v17.workflow.smart_dashboard import DashboardSummary
        
        summary = DashboardSummary(
            total_tasks=10,
            completed_today=7,
            pending_tasks=3,
            overdue_tasks=0,
            due_today=2,
            estimated_time_minutes=60
        )
        
        assert summary.completion_rate() == 0.7
    
    def test_dashboard_summary_completion_rate_zero_tasks(self):
        """测试零任务时的完成率"""
        from oxidation_complete_v17.workflow.smart_dashboard import DashboardSummary
        
        summary = DashboardSummary(
            total_tasks=0,
            completed_today=0,
            pending_tasks=0,
            overdue_tasks=0,
            due_today=0,
            estimated_time_minutes=0
        )
        
        assert summary.completion_rate() == 0.0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
