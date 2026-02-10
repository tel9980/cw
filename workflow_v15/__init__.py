# -*- coding: utf-8 -*-
"""
V1.5 Small Accountant Workflow Optimization
智能工作流优化模块 - 专为小会计设计的工作流引擎

This module provides workflow-centric financial management capabilities
built on top of the existing V1.4 foundation.
"""

__version__ = "1.5.0"
__author__ = "Oxidation Factory Financial Assistant Team"

from .core.workflow_engine import WorkflowEngine
from .core.context_engine import ContextEngine
from .core.progressive_disclosure import ProgressiveDisclosureManager
from .models.workflow_models import (
    WorkflowSession,
    WorkflowTemplate,
    WorkflowAction,
    StepResult
)
from .models.context_models import (
    ContextAnalysis,
    UserPatterns,
    TimeContext,
    SmartDefault
)

__all__ = [
    'WorkflowEngine',
    'ContextEngine',
    'ProgressiveDisclosureManager',
    'WorkflowSession',
    'WorkflowTemplate',
    'WorkflowAction',
    'StepResult',
    'ContextAnalysis',
    'UserPatterns',
    'TimeContext',
    'SmartDefault',
]
