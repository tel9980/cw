# -*- coding: utf-8 -*-
"""
Automation Data Models
自动化相关的数据模型定义
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, List, Any, Optional
from enum import Enum


class AutomationStatus(Enum):
    """自动化状态"""
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    EXECUTING = "executing"
    COMPLETED = "completed"
    FAILED = "failed"


class ScheduleType(Enum):
    """调度类型"""
    DAILY = "daily"
    WEEKLY = "weekly"
    MONTHLY = "monthly"
    CUSTOM = "custom"


@dataclass
class AutomatedAction:
    """自动化动作"""
    action_id: str
    name: str
    function_code: str  # V1.4功能代码
    parameters: Dict[str, Any] = field(default_factory=dict)
    order: int = 0  # 执行顺序
    retry_on_failure: bool = True
    max_retries: int = 3
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class AutomationRule:
    """自动化规则"""
    rule_id: str
    name: str
    description: str
    trigger_pattern: Dict[str, Any]  # 触发模式
    actions: List[AutomatedAction]
    approval_required: bool = True
    is_active: bool = True
    success_rate: float = 0.0
    execution_count: int = 0
    last_executed: Optional[datetime] = None
    created_at: datetime = field(default_factory=datetime.now)
    created_by: str = ""
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def update_success_rate(self, success: bool) -> None:
        """更新成功率"""
        self.execution_count += 1
        if success:
            # 使用移动平均更新成功率
            self.success_rate = (
                (self.success_rate * (self.execution_count - 1) + 1.0) 
                / self.execution_count
            )
        else:
            self.success_rate = (
                (self.success_rate * (self.execution_count - 1)) 
                / self.execution_count
            )


@dataclass
class AutomationSuggestion:
    """自动化建议"""
    suggestion_id: str
    name: str
    description: str
    detected_pattern: Dict[str, Any]
    suggested_rule: AutomationRule
    confidence: float
    potential_time_savings: int  # 预计节省时间（分钟/月）
    occurrences: int  # 模式出现次数
    created_at: datetime = field(default_factory=datetime.now)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class AutomationResult:
    """自动化执行结果"""
    result_id: str
    rule_id: str
    status: AutomationStatus
    success: bool
    message: str = ""
    executed_actions: List[str] = field(default_factory=list)
    failed_actions: List[str] = field(default_factory=list)
    execution_time: float = 0.0  # 执行耗时（秒）
    timestamp: datetime = field(default_factory=datetime.now)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ScheduledTask:
    """计划任务"""
    task_id: str
    name: str
    description: str
    rule_id: str
    schedule_type: ScheduleType
    schedule_config: Dict[str, Any]  # 调度配置（如：{"hour": 9, "minute": 0}）
    next_run: datetime
    last_run: Optional[datetime] = None
    is_active: bool = True
    created_at: datetime = field(default_factory=datetime.now)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class PendingAutomation:
    """待审批的自动化"""
    pending_id: str
    rule_id: str
    rule_name: str
    description: str
    trigger_data: Dict[str, Any]
    proposed_actions: List[AutomatedAction]
    estimated_impact: str
    confidence: float
    created_at: datetime = field(default_factory=datetime.now)
    expires_at: Optional[datetime] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
