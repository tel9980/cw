"""
Workflow Data Models - 工作流数据模型

从V1.5复用并适配氧化加工厂
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, List, Any, Optional
from enum import Enum


class WorkflowType(Enum):
    """工作流类型"""
    MORNING_SETUP = "morning_setup"  # 早晨准备
    TRANSACTION_ENTRY = "transaction_entry"  # 交易录入
    ORDER_PROCESSING = "order_processing"  # 订单处理(氧化加工厂特色)
    BANK_RECONCILIATION = "bank_reconciliation"  # 银行对账
    REPORT_GENERATION = "report_generation"  # 报表生成
    END_OF_DAY = "end_of_day"  # 日终处理
    MONTHLY_CLOSE = "monthly_close"  # 月度结账
    CUSTOM = "custom"  # 自定义


class StepStatus(Enum):
    """步骤状态"""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    SKIPPED = "skipped"
    FAILED = "failed"


@dataclass
class WorkflowStep:
    """工作流步骤"""
    step_id: str
    name: str
    description: str
    required: bool = True
    estimated_duration: int = 0  # 预计耗时(秒)
    dependencies: List[str] = field(default_factory=list)  # 依赖的步骤ID
    function_codes: List[str] = field(default_factory=list)  # 关联的功能代码
    status: StepStatus = StepStatus.PENDING
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class WorkflowTemplate:
    """工作流模板"""
    template_id: str
    name: str
    description: str
    workflow_type: WorkflowType
    steps: List[WorkflowStep]
    is_customizable: bool = True
    created_at: datetime = field(default_factory=datetime.now)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class WorkflowAction:
    """工作流动作"""
    action_id: str
    name: str
    description: str
    function_code: str
    parameters: Dict[str, Any] = field(default_factory=dict)
    is_primary: bool = True  # 是否为主要动作
    confidence: float = 1.0  # 推荐置信度
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class StepResult:
    """步骤执行结果"""
    step_id: str
    status: StepStatus
    success: bool
    message: str = ""
    data: Dict[str, Any] = field(default_factory=dict)
    next_suggestions: List[WorkflowAction] = field(default_factory=list)
    execution_time: float = 0.0  # 执行耗时(秒)
    timestamp: datetime = field(default_factory=datetime.now)


@dataclass
class WorkflowSession:
    """工作流会话"""
    session_id: str
    user_id: str
    workflow_type: WorkflowType
    template_id: str
    current_step: int = 0
    steps: List[WorkflowStep] = field(default_factory=list)
    step_data: Dict[str, Any] = field(default_factory=dict)
    context: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.now)
    last_updated: datetime = field(default_factory=datetime.now)
    is_active: bool = True
    completed_steps: List[str] = field(default_factory=list)
    customizations: Dict[str, Any] = field(default_factory=dict)
    
    def get_current_step(self) -> Optional[WorkflowStep]:
        """获取当前步骤"""
        if 0 <= self.current_step < len(self.steps):
            return self.steps[self.current_step]
        return None
    
    def mark_step_completed(self, step_id: str) -> None:
        """标记步骤为已完成"""
        if step_id not in self.completed_steps:
            self.completed_steps.append(step_id)
        self.last_updated = datetime.now()
    
    def get_progress(self) -> float:
        """获取工作流进度(0-1)"""
        if not self.steps:
            return 0.0
        return len(self.completed_steps) / len(self.steps)
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            'session_id': self.session_id,
            'user_id': self.user_id,
            'workflow_type': self.workflow_type.value,
            'template_id': self.template_id,
            'current_step': self.current_step,
            'step_data': self.step_data,
            'context': self.context,
            'created_at': self.created_at.isoformat(),
            'last_updated': self.last_updated.isoformat(),
            'is_active': self.is_active,
            'completed_steps': self.completed_steps,
            'customizations': self.customizations,
            'progress': self.get_progress()
        }
