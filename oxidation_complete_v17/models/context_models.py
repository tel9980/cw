# -*- coding: utf-8 -*-
"""
Context Data Models
上下文分析相关的数据模型定义
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, List, Any, Optional
from enum import Enum


class TimeContextType(Enum):
    """时间上下文类型"""
    MORNING = "morning"  # 早上 (6:00-12:00)
    AFTERNOON = "afternoon"  # 下午 (12:00-18:00)
    EVENING = "evening"  # 晚上 (18:00-22:00)
    NIGHT = "night"  # 深夜 (22:00-6:00)


class BusinessCyclePosition(Enum):
    """业务周期位置"""
    MONTH_START = "month_start"  # 月初 (1-5日)
    MONTH_MID = "month_mid"  # 月中 (6-25日)
    MONTH_END = "month_end"  # 月末 (26-31日)
    QUARTER_END = "quarter_end"  # 季度末
    YEAR_END = "year_end"  # 年末


class TaskPriority(Enum):
    """任务优先级"""
    URGENT = "urgent"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


@dataclass
class TimeContext:
    """时间上下文"""
    current_time: datetime
    time_type: TimeContextType
    is_business_day: bool
    day_of_month: int
    day_of_week: int
    business_cycle: BusinessCyclePosition
    
    @classmethod
    def from_datetime(cls, dt: datetime) -> 'TimeContext':
        """从datetime创建时间上下文"""
        hour = dt.hour
        if 6 <= hour < 12:
            time_type = TimeContextType.MORNING
        elif 12 <= hour < 18:
            time_type = TimeContextType.AFTERNOON
        elif 18 <= hour < 22:
            time_type = TimeContextType.EVENING
        else:
            time_type = TimeContextType.NIGHT
        
        # 判断是否工作日（周一到周五）
        is_business_day = dt.weekday() < 5
        
        # 判断业务周期位置
        day = dt.day
        month = dt.month
        if day <= 5:
            cycle = BusinessCyclePosition.MONTH_START
        elif day >= 26:
            cycle = BusinessCyclePosition.MONTH_END
        else:
            cycle = BusinessCyclePosition.MONTH_MID
        
        # 特殊处理季度末和年末
        if month in [3, 6, 9, 12] and day >= 26:
            cycle = BusinessCyclePosition.QUARTER_END
        if month == 12 and day >= 26:
            cycle = BusinessCyclePosition.YEAR_END
        
        return cls(
            current_time=dt,
            time_type=time_type,
            is_business_day=is_business_day,
            day_of_month=day,
            day_of_week=dt.weekday(),
            business_cycle=cycle
        )


@dataclass
class Task:
    """任务"""
    task_id: str
    name: str
    description: str
    priority: TaskPriority
    due_date: Optional[datetime] = None
    estimated_duration: int = 0  # 预计耗时（分钟）
    is_completed: bool = False
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class Activity:
    """用户活动记录"""
    activity_id: str
    user_id: str
    action_type: str
    function_code: str
    timestamp: datetime
    duration: float = 0.0  # 耗时（秒）
    success: bool = True
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class UserPatterns:
    """用户行为模式"""
    user_id: str
    frequent_functions: List[str] = field(default_factory=list)  # 常用功能代码
    function_usage_count: Dict[str, int] = field(default_factory=dict)
    typical_workflow_sequences: List[List[str]] = field(default_factory=list)
    preferred_time_slots: Dict[str, List[int]] = field(default_factory=dict)  # 功能->小时列表
    average_session_duration: float = 0.0  # 平均会话时长（分钟）
    last_updated: datetime = field(default_factory=datetime.now)
    
    def get_top_functions(self, n: int = 10) -> List[str]:
        """获取最常用的N个功能"""
        sorted_functions = sorted(
            self.function_usage_count.items(),
            key=lambda x: x[1],
            reverse=True
        )
        return [func for func, _ in sorted_functions[:n]]


@dataclass
class Priority:
    """优先级项"""
    item_id: str
    title: str
    description: str
    priority: TaskPriority
    reason: str  # 优先级原因
    suggested_action: str
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class Alternative:
    """备选值"""
    value: Any
    confidence: float
    reasoning: str
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class SmartDefault:
    """智能默认值"""
    field_name: str
    suggested_value: Any
    confidence: float
    reasoning: str
    alternatives: List[Alternative] = field(default_factory=list)
    learn_from_correction: bool = True
    source: str = "pattern_analysis"  # 来源：pattern_analysis, historical_data, business_rules
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ContextAnalysis:
    """上下文分析结果"""
    user_id: str
    analysis_time: datetime
    user_patterns: UserPatterns
    current_time_context: TimeContext
    pending_tasks: List[Task]
    recent_activities: List[Activity]
    business_cycle_position: BusinessCyclePosition
    suggested_priorities: List[Priority]
    confidence_score: float
    smart_defaults: Dict[str, SmartDefault] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def get_high_priority_tasks(self) -> List[Task]:
        """获取高优先级任务"""
        return [
            task for task in self.pending_tasks
            if task.priority in [TaskPriority.URGENT, TaskPriority.HIGH]
        ]
    
    def get_suggested_next_actions(self, max_count: int = 5) -> List[Priority]:
        """获取建议的下一步操作"""
        return sorted(
            self.suggested_priorities,
            key=lambda p: (p.priority.value, p.title)
        )[:max_count]


@dataclass
class Dashboard:
    """智能仪表板"""
    user_id: str
    generated_at: datetime
    context: ContextAnalysis
    priority_tasks: List[Task]
    quick_actions: List[Dict[str, Any]]
    pending_items: List[Dict[str, Any]]
    insights: List[str]
    warnings: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
