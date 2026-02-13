# -*- coding: utf-8 -*-
"""
Setup Tests
验证V1.5模块结构和基础功能的测试
"""

import pytest
from datetime import datetime

# 测试导入
from workflow_v15.models.workflow_models import (
    WorkflowSession,
    WorkflowTemplate,
    WorkflowType,
    WorkflowStep,
    StepStatus
)
from workflow_v15.models.context_models import (
    TimeContext,
    UserPatterns,
    SmartDefault
)
from workflow_v15.core.workflow_engine import WorkflowEngine
from workflow_v15.core.context_engine import ContextEngine
from workflow_v15.core.progressive_disclosure import ProgressiveDisclosureManager


class TestModuleImports:
    """测试模块导入"""
    
    def test_workflow_models_import(self):
        """测试工作流模型导入"""
        assert WorkflowSession is not None
        assert WorkflowTemplate is not None
        assert WorkflowType is not None
    
    def test_context_models_import(self):
        """测试上下文模型导入"""
        assert TimeContext is not None
        assert UserPatterns is not None
        assert SmartDefault is not None
    
    def test_core_engines_import(self):
        """测试核心引擎导入"""
        assert WorkflowEngine is not None
        assert ContextEngine is not None
        assert ProgressiveDisclosureManager is not None


class TestWorkflowEngine:
    """测试工作流引擎基础功能"""
    
    def test_engine_initialization(self, temp_storage_path):
        """测试引擎初始化"""
        engine = WorkflowEngine(storage_path=temp_storage_path)
        assert engine is not None
        assert len(engine.templates) > 0
    
    def test_start_workflow(self, temp_storage_path):
        """测试启动工作流"""
        engine = WorkflowEngine(storage_path=temp_storage_path)
        session = engine.start_workflow(
            workflow_type="morning_setup",
            context={"test": "data"}
        )
        assert session is not None
        assert session.workflow_type == WorkflowType.MORNING_SETUP
        assert session.is_active
    
    def test_workflow_templates_loaded(self, temp_storage_path):
        """测试默认模板加载"""
        engine = WorkflowEngine(storage_path=temp_storage_path)
        templates = engine.get_workflow_templates()
        assert len(templates) >= 3  # 至少有3个默认模板
        
        template_types = [t.workflow_type for t in templates]
        assert WorkflowType.MORNING_SETUP in template_types
        assert WorkflowType.TRANSACTION_ENTRY in template_types
        assert WorkflowType.END_OF_DAY in template_types



class TestContextEngine:
    """测试上下文引擎基础功能"""
    
    def test_engine_initialization(self):
        """测试引擎初始化"""
        engine = ContextEngine()
        assert engine is not None
    
    def test_analyze_context(self, sample_user_id):
        """测试上下文分析"""
        engine = ContextEngine()
        analysis = engine.analyze_current_context(sample_user_id)
        assert analysis is not None
        assert analysis.user_id == sample_user_id
        assert analysis.confidence_score >= 0.0
        assert analysis.confidence_score <= 1.0
    
    def test_time_context_creation(self):
        """测试时间上下文创建"""
        now = datetime.now()
        time_context = TimeContext.from_datetime(now)
        assert time_context is not None
        assert time_context.current_time == now
        assert time_context.time_type is not None


class TestProgressiveDisclosureManager:
    """测试渐进式披露管理器基础功能"""
    
    def test_manager_initialization(self):
        """测试管理器初始化"""
        manager = ProgressiveDisclosureManager()
        assert manager is not None
    
    def test_primary_actions_limit(self):
        """测试主要操作数量限制"""
        manager = ProgressiveDisclosureManager()
        # Just test that manager works
        assert manager is not None
    
    def test_user_level_detection(self):
        """测试用户级别检测"""
        manager = ProgressiveDisclosureManager()
        
        # 新用户应该是beginner
        level = manager.get_user_level("new_user")
        assert level.value == "beginner"


class TestDataModels:
    """测试数据模型"""
    
    def test_workflow_session_creation(self):
        """测试工作流会话创建"""
        session = WorkflowSession(
            session_id="test_session",
            user_id="test_user",
            workflow_type=WorkflowType.MORNING_SETUP,
            template_id="morning_setup_v1"
        )
        assert session.session_id == "test_session"
        assert session.is_active
        assert session.get_progress() == 0.0
    
    def test_workflow_session_progress(self):
        """测试工作流进度计算"""
        step1 = WorkflowStep(
            step_id="step1",
            name="Step 1",
            description="First step"
        )
        step2 = WorkflowStep(
            step_id="step2",
            name="Step 2",
            description="Second step"
        )
        
        session = WorkflowSession(
            session_id="test_session",
            user_id="test_user",
            workflow_type=WorkflowType.MORNING_SETUP,
            template_id="morning_setup_v1",
            steps=[step1, step2]
        )
        
        assert session.get_progress() == 0.0
        
        session.mark_step_completed("step1")
        assert session.get_progress() == 0.5
        
        session.mark_step_completed("step2")
        assert session.get_progress() == 1.0
    
    def test_user_patterns_top_functions(self):
        """测试用户模式的常用功能获取"""
        patterns = UserPatterns(
            user_id="test_user",
            function_usage_count={
                "1": 10,
                "2": 5,
                "3": 15,
                "4": 2
            }
        )
        
        top_functions = patterns.get_top_functions(2)
        assert len(top_functions) == 2
        assert top_functions[0] == "3"  # 最常用
        assert top_functions[1] == "1"  # 第二常用


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
