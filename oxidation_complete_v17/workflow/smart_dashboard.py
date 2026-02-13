"""
Smart Dashboard for Oxidation Factory - 氧化加工厂智能工作台

从V1.5复用MorningDashboard并扩展氧化加工厂特色功能:
- 今日优先任务显示
- 超期未收款提醒
- 税务申报提醒
- 现金流预警
- 快捷操作入口

Requirements: B1
"""

from datetime import datetime, date, timedelta
from typing import List, Dict, Optional, Any
from dataclasses import dataclass, field
from enum import Enum


class TaskPriority(Enum):
    """任务优先级"""
    CRITICAL = "critical"  # 必须今天完成
    HIGH = "high"  # 应该今天完成
    MEDIUM = "medium"  # 可以今天完成
    LOW = "low"  # 有时间再做


class TaskStatus(Enum):
    """任务状态"""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    OVERDUE = "overdue"


class AlertType(Enum):
    """提醒类型"""
    OVERDUE_PAYMENT = "overdue_payment"  # 超期未收款
    TAX_FILING = "tax_filing"  # 税务申报
    CASH_FLOW = "cash_flow"  # 现金流预警
    PROCESSING_ORDER = "processing_order"  # 加工订单
    OUTSOURCED_PROCESSING = "outsourced_processing"  # 外发加工
    GENERAL = "general"  # 一般提醒


@dataclass
class PriorityTask:
    """优先任务"""
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
        """检查是否逾期"""
        if not self.due_date:
            return False
        return self.due_date < date.today() and self.status != TaskStatus.COMPLETED
    
    def is_due_today(self) -> bool:
        """检查是否今天到期"""
        if not self.due_date:
            return False
        return self.due_date == date.today()
    
    def is_due_soon(self, days: int = 3) -> bool:
        """检查是否即将到期"""
        if not self.due_date:
            return False
        return date.today() <= self.due_date <= date.today() + timedelta(days=days)


@dataclass
class DashboardAlert:
    """工作台提醒"""
    alert_id: str
    alert_type: AlertType
    title: str
    message: str
    severity: str  # "info", "warning", "critical"
    created_date: date
    action_text: Optional[str] = None
    action_data: Optional[Dict[str, Any]] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class QuickAction:
    """快捷操作"""
    action_id: str
    label: str
    description: str
    icon: str
    function_code: str
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class DashboardSummary:
    """工作台汇总统计"""
    total_tasks: int
    completed_today: int
    pending_tasks: int
    overdue_tasks: int
    due_today: int
    estimated_time_minutes: int
    
    # 氧化加工厂特色统计
    overdue_payments_count: int = 0
    overdue_payments_amount: float = 0.0
    pending_orders_count: int = 0
    pending_outsourced_count: int = 0
    cash_balance: float = 0.0
    
    def completion_rate(self) -> float:
        """计算完成率"""
        if self.total_tasks == 0:
            return 0.0
        return self.completed_today / self.total_tasks


@dataclass
class SmartDashboard:
    """智能工作台完整数据"""
    user_id: str
    generated_at: datetime
    greeting: str
    summary: DashboardSummary
    priority_tasks: List[PriorityTask]
    alerts: List[DashboardAlert]
    quick_actions: List[QuickAction]
    insights: List[str]


class SmartDashboardManager:
    """
    智能工作台管理器 - 氧化加工厂版
    
    功能:
    - 优先任务识别和显示
    - 超期未收款提醒
    - 税务申报提醒
    - 现金流预警
    - 快捷操作入口
    - 个性化洞察和建议
    """
    
    def __init__(
        self,
        transaction_storage=None,
        counterparty_storage=None,
        processing_order_manager=None,
        outsourced_processing_manager=None,
        bank_account_manager=None
    ):
        """
        初始化智能工作台管理器
        
        Args:
            transaction_storage: 交易存储
            counterparty_storage: 往来单位存储
            processing_order_manager: 加工订单管理器
            outsourced_processing_manager: 外发加工管理器
            bank_account_manager: 银行账户管理器
        """
        self.transaction_storage = transaction_storage
        self.counterparty_storage = counterparty_storage
        self.processing_order_manager = processing_order_manager
        self.outsourced_processing_manager = outsourced_processing_manager
        self.bank_account_manager = bank_account_manager
        
        self.tasks: Dict[str, PriorityTask] = {}
        self.alerts: Dict[str, DashboardAlert] = {}
        self.user_preferences: Dict[str, Any] = {}
    
    def add_task(self, task: PriorityTask):
        """添加任务"""
        self.tasks[task.task_id] = task
    
    def update_task_status(self, task_id: str, status: TaskStatus):
        """更新任务状态"""
        if task_id in self.tasks:
            self.tasks[task_id].status = status
    
    def add_alert(self, alert: DashboardAlert):
        """添加提醒"""
        self.alerts[alert.alert_id] = alert
    
    def remove_alert(self, alert_id: str):
        """移除提醒"""
        self.alerts.pop(alert_id, None)
    
    def set_user_preferences(self, user_id: str, preferences: Dict[str, Any]):
        """设置用户偏好"""
        self.user_preferences[user_id] = preferences
    
    def generate_dashboard(self, user_id: str) -> SmartDashboard:
        """
        生成智能工作台
        
        Args:
            user_id: 用户ID
            
        Returns:
            SmartDashboard: 完整的工作台数据
        """
        now = datetime.now()
        
        # 生成问候语
        greeting = self._generate_greeting(user_id, now)
        
        # 获取优先任务
        priority_tasks = self._get_priority_tasks(user_id)
        
        # 生成提醒
        alerts = self._generate_alerts(user_id)
        
        # 生成汇总统计
        summary = self._generate_summary(priority_tasks, alerts)
        
        # 生成快捷操作
        quick_actions = self._generate_quick_actions(user_id)
        
        # 生成洞察
        insights = self._generate_insights(user_id, summary, alerts)
        
        return SmartDashboard(
            user_id=user_id,
            generated_at=now,
            greeting=greeting,
            summary=summary,
            priority_tasks=priority_tasks,
            alerts=alerts,
            quick_actions=quick_actions,
            insights=insights
        )
    
    def _generate_greeting(self, user_id: str, now: datetime) -> str:
        """生成个性化问候语"""
        hour = now.hour
        
        if hour < 12:
            time_greeting = "早上好"
        elif hour < 18:
            time_greeting = "下午好"
        else:
            time_greeting = "晚上好"
        
        prefs = self.user_preferences.get(user_id, {})
        user_name = prefs.get("name", "")
        
        if user_name:
            return f"{time_greeting}，{user_name}！"
        else:
            return f"{time_greeting}！"
    
    def _get_priority_tasks(self, user_id: str) -> List[PriorityTask]:
        """
        获取优先任务
        
        优先级顺序:
        1. 逾期任务
        2. 今天到期任务
        3. 高优先级任务
        4. 即将到期任务
        5. 其他任务按优先级
        """
        tasks = list(self.tasks.values())
        
        # 更新逾期状态
        for task in tasks:
            if task.is_overdue():
                task.status = TaskStatus.OVERDUE
        
        # 过滤已完成任务
        active_tasks = [t for t in tasks if t.status != TaskStatus.COMPLETED]
        
        # 排序
        def task_sort_key(task: PriorityTask):
            if task.is_overdue():
                return (0, task.due_date or date.max)
            if task.is_due_today():
                return (1, task.priority.value)
            if task.priority == TaskPriority.CRITICAL:
                return (2, task.due_date or date.max)
            if task.is_due_soon():
                return (3, task.due_date or date.max)
            
            priority_order = {
                TaskPriority.CRITICAL: 4,
                TaskPriority.HIGH: 5,
                TaskPriority.MEDIUM: 6,
                TaskPriority.LOW: 7
            }
            return (priority_order.get(task.priority, 8), task.due_date or date.max)
        
        sorted_tasks = sorted(active_tasks, key=task_sort_key)
        
        # 限制显示数量
        max_tasks = self.user_preferences.get(user_id, {}).get("max_dashboard_tasks", 10)
        return sorted_tasks[:max_tasks]
    
    def _generate_alerts(self, user_id: str) -> List[DashboardAlert]:
        """
        生成提醒列表
        
        包括:
        - 超期未收款提醒
        - 税务申报提醒
        - 现金流预警
        - 加工订单提醒
        - 外发加工提醒
        """
        alerts = list(self.alerts.values())
        
        # 生成超期未收款提醒
        if self.processing_order_manager:
            overdue_alerts = self._generate_overdue_payment_alerts()
            alerts.extend(overdue_alerts)
        
        # 生成税务申报提醒
        tax_alerts = self._generate_tax_filing_alerts()
        alerts.extend(tax_alerts)
        
        # 生成现金流预警
        if self.bank_account_manager:
            cash_flow_alerts = self._generate_cash_flow_alerts()
            alerts.extend(cash_flow_alerts)
        
        # 生成加工订单提醒
        if self.processing_order_manager:
            order_alerts = self._generate_processing_order_alerts()
            alerts.extend(order_alerts)
        
        # 生成外发加工提醒
        if self.outsourced_processing_manager:
            outsourced_alerts = self._generate_outsourced_processing_alerts()
            alerts.extend(outsourced_alerts)
        
        # 按严重程度和日期排序
        def alert_sort_key(alert: DashboardAlert):
            severity_order = {"critical": 0, "warning": 1, "info": 2}
            return (severity_order.get(alert.severity, 3), alert.created_date)
        
        sorted_alerts = sorted(alerts, key=alert_sort_key)
        
        # 限制显示数量
        max_alerts = self.user_preferences.get(user_id, {}).get("max_dashboard_alerts", 10)
        return sorted_alerts[:max_alerts]
    
    def _generate_overdue_payment_alerts(self) -> List[DashboardAlert]:
        """生成超期未收款提醒"""
        alerts = []
        
        try:
            # 获取所有未完全收款的订单
            all_orders = self.processing_order_manager.get_all_orders()
            overdue_orders = [
                order for order in all_orders
                if order.amount_received < order.total_amount
                and order.order_date < date.today() - timedelta(days=30)
            ]
            
            if overdue_orders:
                total_overdue = sum(
                    order.total_amount - order.amount_received
                    for order in overdue_orders
                )
                
                alert = DashboardAlert(
                    alert_id=f"overdue_payment_{date.today().isoformat()}",
                    alert_type=AlertType.OVERDUE_PAYMENT,
                    title="超期未收款提醒",
                    message=f"有 {len(overdue_orders)} 笔订单超过30天未收款，合计 ¥{total_overdue:,.2f}",
                    severity="warning",
                    created_date=date.today(),
                    action_text="查看详情",
                    action_data={"order_ids": [o.order_id for o in overdue_orders]},
                    metadata={"count": len(overdue_orders), "amount": total_overdue}
                )
                alerts.append(alert)
        except Exception:
            pass
        
        return alerts
    
    def _generate_tax_filing_alerts(self) -> List[DashboardAlert]:
        """生成税务申报提醒"""
        alerts = []
        
        today = date.today()
        
        # 增值税申报提醒(每月15日前)
        if today.day <= 15:
            alert = DashboardAlert(
                alert_id=f"vat_filing_{today.isoformat()}",
                alert_type=AlertType.TAX_FILING,
                title="增值税申报提醒",
                message=f"本月增值税申报截止日期为 {today.year}-{today.month:02d}-15",
                severity="warning" if today.day >= 10 else "info",
                created_date=today,
                action_text="查看报表",
                action_data={"report_type": "vat"}
            )
            alerts.append(alert)
        
        # 所得税申报提醒(季度末)
        if today.month in [3, 6, 9, 12] and today.day <= 15:
            alert = DashboardAlert(
                alert_id=f"income_tax_filing_{today.isoformat()}",
                alert_type=AlertType.TAX_FILING,
                title="所得税申报提醒",
                message=f"本季度所得税申报截止日期为 {today.year}-{today.month:02d}-15",
                severity="warning" if today.day >= 10 else "info",
                created_date=today,
                action_text="查看报表",
                action_data={"report_type": "income_tax"}
            )
            alerts.append(alert)
        
        return alerts
    
    def _generate_cash_flow_alerts(self) -> List[DashboardAlert]:
        """生成现金流预警"""
        alerts = []
        
        try:
            # 获取所有账户余额
            accounts = self.bank_account_manager.get_all_accounts()
            total_balance = sum(acc.balance for acc in accounts)
            
            # 现金账户余额
            cash_accounts = [acc for acc in accounts if acc.account_type == "现金"]
            cash_balance = sum(acc.balance for acc in cash_accounts)
            
            # 低余额预警
            if total_balance < 10000:
                alert = DashboardAlert(
                    alert_id=f"low_balance_{date.today().isoformat()}",
                    alert_type=AlertType.CASH_FLOW,
                    title="账户余额预警",
                    message=f"当前总余额 ¥{total_balance:,.2f}，建议关注现金流",
                    severity="warning",
                    created_date=date.today(),
                    action_text="查看账户",
                    action_data={"view": "accounts"},
                    metadata={"total_balance": total_balance, "cash_balance": cash_balance}
                )
                alerts.append(alert)
        except Exception:
            pass
        
        return alerts
    
    def _generate_processing_order_alerts(self) -> List[DashboardAlert]:
        """生成加工订单提醒"""
        alerts = []
        
        try:
            # 获取待处理订单
            all_orders = self.processing_order_manager.get_all_orders()
            pending_orders = [
                order for order in all_orders
                if order.status == "进行中"
            ]
            
            if len(pending_orders) > 10:
                alert = DashboardAlert(
                    alert_id=f"pending_orders_{date.today().isoformat()}",
                    alert_type=AlertType.PROCESSING_ORDER,
                    title="待处理订单较多",
                    message=f"当前有 {len(pending_orders)} 个订单正在进行中",
                    severity="info",
                    created_date=date.today(),
                    action_text="查看订单",
                    action_data={"filter": "pending"},
                    metadata={"count": len(pending_orders)}
                )
                alerts.append(alert)
        except Exception:
            pass
        
        return alerts
    
    def _generate_outsourced_processing_alerts(self) -> List[DashboardAlert]:
        """生成外发加工提醒"""
        alerts = []
        
        try:
            # 获取待结算的外发加工
            all_outsourced = self.outsourced_processing_manager.get_all_outsourced()
            pending_outsourced = [
                op for op in all_outsourced
                if op.status == "进行中"
            ]
            
            if len(pending_outsourced) > 5:
                alert = DashboardAlert(
                    alert_id=f"pending_outsourced_{date.today().isoformat()}",
                    alert_type=AlertType.OUTSOURCED_PROCESSING,
                    title="待结算外发加工",
                    message=f"当前有 {len(pending_outsourced)} 笔外发加工待结算",
                    severity="info",
                    created_date=date.today(),
                    action_text="查看外发",
                    action_data={"filter": "pending"},
                    metadata={"count": len(pending_outsourced)}
                )
                alerts.append(alert)
        except Exception:
            pass
        
        return alerts
    
    def _generate_summary(
        self,
        priority_tasks: List[PriorityTask],
        alerts: List[DashboardAlert]
    ) -> DashboardSummary:
        """生成汇总统计"""
        all_tasks = list(self.tasks.values())
        
        # 任务统计
        total_tasks = len(all_tasks)
        completed_today = sum(1 for t in all_tasks if t.status == TaskStatus.COMPLETED)
        pending_tasks = sum(
            1 for t in all_tasks
            if t.status in [TaskStatus.PENDING, TaskStatus.IN_PROGRESS]
        )
        overdue_tasks = sum(1 for t in priority_tasks if t.is_overdue())
        due_today = sum(1 for t in priority_tasks if t.is_due_today())
        estimated_time = sum(
            t.estimated_minutes for t in priority_tasks
            if t.status != TaskStatus.COMPLETED
        )
        
        # 氧化加工厂特色统计
        overdue_payments_count = 0
        overdue_payments_amount = 0.0
        pending_orders_count = 0
        pending_outsourced_count = 0
        cash_balance = 0.0
        
        # 超期未收款统计
        overdue_payment_alerts = [
            a for a in alerts
            if a.alert_type == AlertType.OVERDUE_PAYMENT
        ]
        if overdue_payment_alerts:
            alert = overdue_payment_alerts[0]
            overdue_payments_count = alert.metadata.get("count", 0)
            overdue_payments_amount = alert.metadata.get("amount", 0.0)
        
        # 待处理订单统计
        order_alerts = [
            a for a in alerts
            if a.alert_type == AlertType.PROCESSING_ORDER
        ]
        if order_alerts:
            pending_orders_count = order_alerts[0].metadata.get("count", 0)
        
        # 待结算外发统计
        outsourced_alerts = [
            a for a in alerts
            if a.alert_type == AlertType.OUTSOURCED_PROCESSING
        ]
        if outsourced_alerts:
            pending_outsourced_count = outsourced_alerts[0].metadata.get("count", 0)
        
        # 现金余额统计
        cash_flow_alerts = [
            a for a in alerts
            if a.alert_type == AlertType.CASH_FLOW
        ]
        if cash_flow_alerts:
            cash_balance = cash_flow_alerts[0].metadata.get("total_balance", 0.0)
        
        return DashboardSummary(
            total_tasks=total_tasks,
            completed_today=completed_today,
            pending_tasks=pending_tasks,
            overdue_tasks=overdue_tasks,
            due_today=due_today,
            estimated_time_minutes=estimated_time,
            overdue_payments_count=overdue_payments_count,
            overdue_payments_amount=overdue_payments_amount,
            pending_orders_count=pending_orders_count,
            pending_outsourced_count=pending_outsourced_count,
            cash_balance=cash_balance
        )
    
    def _generate_quick_actions(self, user_id: str) -> List[QuickAction]:
        """生成快捷操作"""
        actions = [
            QuickAction(
                action_id="record_transaction",
                label="录入交易",
                description="快速录入收支交易",
                icon="plus",
                function_code="transaction_entry"
            ),
            QuickAction(
                action_id="create_order",
                label="新建订单",
                description="创建加工订单",
                icon="file-plus",
                function_code="create_order"
            ),
            QuickAction(
                action_id="import_bank_statement",
                label="导入流水",
                description="导入银行流水",
                icon="upload",
                function_code="import_statement"
            ),
            QuickAction(
                action_id="reconcile",
                label="对账",
                description="银行流水对账",
                icon="check-circle",
                function_code="reconcile"
            ),
            QuickAction(
                action_id="view_reports",
                label="查看报表",
                description="查看财务报表",
                icon="chart-bar",
                function_code="view_reports"
            )
        ]
        
        # 限制显示数量(渐进式展示)
        return actions[:5]
    
    def _generate_insights(
        self,
        user_id: str,
        summary: DashboardSummary,
        alerts: List[DashboardAlert]
    ) -> List[str]:
        """生成洞察和建议"""
        insights = []
        
        # 任务完成情况
        if summary.overdue_tasks > 0:
            insights.append(f"您有 {summary.overdue_tasks} 个逾期任务需要优先处理")
        elif summary.due_today > 0:
            insights.append(f"今天有 {summary.due_today} 个任务需要完成")
        elif summary.completed_today > 0 and summary.pending_tasks == 0:
            insights.append("太棒了！所有任务都已完成")
        
        # 超期未收款
        if summary.overdue_payments_count > 0:
            insights.append(
                f"有 {summary.overdue_payments_count} 笔订单超期未收款，"
                f"合计 ¥{summary.overdue_payments_amount:,.2f}"
            )
        
        # 现金流
        if summary.cash_balance > 0 and summary.cash_balance < 10000:
            insights.append(f"当前账户余额 ¥{summary.cash_balance:,.2f}，建议关注现金流")
        
        # 待处理事项
        if summary.pending_orders_count > 10:
            insights.append(f"当前有 {summary.pending_orders_count} 个订单正在进行中")
        
        if summary.pending_outsourced_count > 5:
            insights.append(f"有 {summary.pending_outsourced_count} 笔外发加工待结算")
        
        # 预计工作时间
        if summary.estimated_time_minutes > 0:
            hours = summary.estimated_time_minutes // 60
            minutes = summary.estimated_time_minutes % 60
            if hours > 0:
                insights.append(f"今日任务预计需要 {hours}小时{minutes}分钟")
            else:
                insights.append(f"今日任务预计需要 {minutes}分钟")
        
        return insights[:5]  # 最多显示5条洞察
    
    def mark_task_completed(self, task_id: str):
        """标记任务完成"""
        if task_id in self.tasks:
            self.tasks[task_id].status = TaskStatus.COMPLETED
    
    def get_task_by_id(self, task_id: str) -> Optional[PriorityTask]:
        """根据ID获取任务"""
        return self.tasks.get(task_id)
    
    def get_alert_by_id(self, alert_id: str) -> Optional[DashboardAlert]:
        """根据ID获取提醒"""
        return self.alerts.get(alert_id)
    
    def get_overdue_tasks(self) -> List[PriorityTask]:
        """获取所有逾期任务"""
        return [t for t in self.tasks.values() if t.is_overdue()]
    
    def get_due_today_tasks(self) -> List[PriorityTask]:
        """获取今天到期的任务"""
        return [t for t in self.tasks.values() if t.is_due_today()]
