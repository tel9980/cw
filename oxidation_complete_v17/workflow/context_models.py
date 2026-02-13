# -*- coding: utf-8 -*-
"""
Context Models for Oxidation Factory
氧化加工厂上下文数据模型

从V1.5复用并适配氧化加工厂业务特点
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, List, Optional
from enum import Enum


class TaskPriority(Enum):
    """任务优先级"""
    URGENT = "urgent"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


@dataclass
class UserPatterns:
    """用户行为模式"""
    user_id: str
    function_usage_count: Dict[str, int] = field(default_factory=dict)
    preferred_time_slots: Dict[str, List[int]] = field(default_factory=dict)
    typical_workflow_sequences: List[List[str]] = field(default_factory=list)
    average_session_duration: float = 0.0
    last_updated: Optional[datetime] = None
    
    def get_top_functions(self, n: int = 10) -> List[str]:
        """获取最常用的N个功能"""
        sorted_functions = sorted(
            self.function_usage_count.items(),
            key=lambda x: x[1],
            reverse=True
        )
        return [func for func, _ in sorted_functions[:n]]


@dataclass
class SmartDefault:
    """智能默认值"""
    field_name: str
    suggested_value: any
    confidence: float
    reasoning: str
    source: str  # 'business_rules', 'entity_pattern', 'user_pattern', 'correction_learning'
    alternatives: List['Alternative'] = field(default_factory=list)


@dataclass
class Alternative:
    """备选值"""
    value: any
    confidence: float
    reasoning: str


@dataclass
class Activity:
    """用户活动记录"""
    activity_id: str
    user_id: str
    function_code: str
    timestamp: datetime
    duration: Optional[float] = None
    metadata: Dict = field(default_factory=dict)
