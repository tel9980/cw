# -*- coding: utf-8 -*-
"""
Workflow Engine Tests
工作流引擎的单元测试
"""

import pytest
import json
from pathlib import Path
from datetime import datetime

from workflow_v15.core.workflow_engine import WorkflowEngine
from workflow_v15.models.workflow_models import (
    WorkflowSession,
    WorkflowType,
    StepStatus,
    WorkflowStep
)


class TestWorkflowEngineBasics:
    """测试工作流引擎基础功能"""
    
    def test_engine_initialization(self, temp_storage_path):
        """测试引擎初始化"""
        engine = WorkflowEngine(storage_path=temp_storage_path)
        assert engine is not None
        assert len(engine.templates) > 0
        assert engine.storage_path.exists()
        assert engine.customization_path.exists()
    
    def test_default_templates_loaded(self, temp_storage_path):
        """测试默认模板加载"""
        engine = WorkflowEngine(storage_path=temp_storage_path)
        templates = engine.get_workflow_templates()
        
        assert len(templates) >= 3
        template_types = [t.workflow_type for t in templates]
        assert WorkflowType.MORNING_SETUP in template_types
        assert WorkflowType.TRANSACTION_ENTRY in template_types
        assert WorkflowType.END_OF_DAY in template_types


class TestWorkflowSessionManagement:
    """测试工作流会话管理（Requirement 1.4）"""
    
    def test_start_workflow_creates_session(self, temp_storage_path, sample_user_id):
        """测试启动工作流创建会话"""
        engine = WorkflowEngine(storage_path=temp_storage_path)
        session = engine.start_workflow(
            workflow_type="morning_setup",
            context={"date": "2024-01-15"},
            user_id=sample_user_id
        )
        
        assert session is not None
        assert session.workflow_type == WorkflowType.MORNING_SETUP
        assert session.user_id == sample_user_id
        assert session.is_active
        assert session.session_id in engine.active_sessions
    
    def test_session_persistence(self, temp_storage_path, sample_user_id):
        """测试会话持久化"""
        engine = WorkflowEngine(storage_path=temp_storage_path)
        session = engine.start_workflow(
            workflow_type="morning_setup",
            context={"date": "2024-01-15"},
            user_id=sample_user_id
        )
        
        session_id = session.session_id
        
        # 验证会话文件已创建
        session_file = Path(temp_storage_path) / f"{session_id}.json"
        assert session_file.exists()
        
        # 验证可以加载会话
        loaded_session = engine.load_workflow_state(session_id)
        assert loaded_session is not None
        assert loaded_session.session_id == session_id
        assert loaded_session.user_id == sample_user_id
    
    def test_resume_session(self, temp_storage_path, sample_user_id):
        """测试恢复会话（Requirement 1.4）"""
        engine = WorkflowEngine(storage_path=temp_storage_path)
        
        # 创建并关闭会话
        session = engine.start_workflow(
            workflow_type="morning_setup",
            context={"date": "2024-01-15"},
            user_id=sample_user_id
        )
        session_id = session.session_id
        engine.close_session(session_id)
        
        # 验证会话已关闭
        assert not session.is_active
        
        # 恢复会话
        resumed_session = engine.resume_session(session_id)
        assert resumed_session is not None
        assert resumed_session.session_id == session_id
        assert resumed_session.is_active
    
    def test_get_user_sessions(self, temp_storage_path, sample_user_id):
        """测试获取用户会话列表"""
        engine = WorkflowEngine(storage_path=temp_storage_path)
        
        # 创建多个会话
        session1 = engine.start_workflow(
            workflow_type="morning_setup",
            context={},
            user_id=sample_user_id
        )
        session2 = engine.start_workflow(
            workflow_type="transaction_entry",
            context={},
            user_id=sample_user_id
        )
        
        # 关闭一个会话
        engine.close_session(session1.session_id)
        
        # 获取活跃会话
        active_sessions = engine.get_user_sessions(sample_user_id, active_only=True)
        assert len(active_sessions) == 1
        assert active_sessions[0].session_id == session2.session_id
        
        # 获取所有会话
        all_sessions = engine.get_user_sessions(sample_user_id, active_only=False)
        assert len(all_sessions) == 2
    
    def test_get_active_session(self, temp_storage_path, sample_user_id):
        """测试获取用户的活跃会话"""
        engine = WorkflowEngine(storage_path=temp_storage_path)
        
        # 没有活跃会话时
        active_session = engine.get_active_session(sample_user_id)
        assert active_session is None
        
        # 创建会话后
        session = engine.start_workflow(
            workflow_type="morning_setup",
            context={},
            user_id=sample_user_id
        )
        
        active_session = engine.get_active_session(sample_user_id)
        assert active_session is not None
        assert active_session.session_id == session.session_id


class TestWorkflowStepExecution:
    """测试工作流步骤执行"""
    
    def test_execute_step_success(self, temp_storage_path, sample_user_id):
        """测试成功执行步骤"""
        engine = WorkflowEngine(storage_path=temp_storage_path)
        session = engine.start_workflow(
            workflow_type="morning_setup",
            context={},
            user_id=sample_user_id
        )
        
        # 执行第一步
        result = engine.execute_step(
            session_id=session.session_id,
            step_data={"action": "completed"}
        )
        
        assert result.success
        assert result.status == StepStatus.COMPLETED
        assert len(result.next_suggestions) > 0
    
    def test_execute_step_updates_session(self, temp_storage_path, sample_user_id):
        """测试执行步骤更新会话状态"""
        engine = WorkflowEngine(storage_path=temp_storage_path)
        session = engine.start_workflow(
            workflow_type="morning_setup",
            context={},
            user_id=sample_user_id
        )
        
        initial_step = session.current_step
        
        # 执行步骤
        engine.execute_step(
            session_id=session.session_id,
            step_data={"action": "completed"}
        )
        
        # 验证步骤已前进
        assert session.current_step == initial_step + 1
        assert len(session.completed_steps) == 1
    
    def test_skip_optional_step(self, temp_storage_path, sample_user_id):
        """测试跳过可选步骤"""
        engine = WorkflowEngine(storage_path=temp_storage_path)
        session = engine.start_workflow(
            workflow_type="morning_setup",
            context={},
            user_id=sample_user_id
        )
        
        # 将当前步骤设为可选
        current_step = session.get_current_step()
        current_step.required = False
        
        # 跳过步骤
        result = engine.skip_current_step(session.session_id)
        
        assert result.success
        assert result.status == StepStatus.SKIPPED
        assert session.current_step == 1
    
    def test_cannot_skip_required_step(self, temp_storage_path, sample_user_id):
        """测试不能跳过必需步骤"""
        engine = WorkflowEngine(storage_path=temp_storage_path)
        session = engine.start_workflow(
            workflow_type="morning_setup",
            context={},
            user_id=sample_user_id
        )
        
        # 尝试跳过必需步骤
        result = engine.skip_current_step(session.session_id)
        
        assert not result.success
        assert result.status == StepStatus.FAILED
        assert "Cannot skip required step" in result.message


class TestNextStepSuggestions:
    """测试下一步建议（Requirement 1.2）"""
    
    def test_get_next_suggestions_for_current_step(self, temp_storage_path, sample_user_id):
        """测试获取当前步骤的下一步建议"""
        engine = WorkflowEngine(storage_path=temp_storage_path)
        session = engine.start_workflow(
            workflow_type="morning_setup",
            context={},
            user_id=sample_user_id
        )
        
        suggestions = engine.get_next_suggestions(session.session_id)
        
        assert len(suggestions) > 0
        assert len(suggestions) <= 5  # 最多5个建议
        assert all(s.is_primary for s in suggestions[:3])  # 前几个应该是主要建议
    
    def test_suggestions_after_workflow_completion(self, temp_storage_path, sample_user_id):
        """测试工作流完成后的建议"""
        engine = WorkflowEngine(storage_path=temp_storage_path)
        session = engine.start_workflow(
            workflow_type="morning_setup",
            context={},
            user_id=sample_user_id
        )
        
        # 完成所有步骤
        while session.get_current_step():
            engine.execute_step(
                session_id=session.session_id,
                step_data={"action": "completed"}
            )
        
        # 获取后续建议
        suggestions = engine.get_next_suggestions(session.session_id)
        
        assert len(suggestions) > 0
        # 早晨工作流完成后应该建议开始交易录入
        assert any("交易" in s.name or "transaction" in s.action_id.lower() 
                  for s in suggestions)
    
    def test_suggestions_include_skip_option_for_optional_steps(
        self, temp_storage_path, sample_user_id
    ):
        """测试可选步骤的建议包含跳过选项"""
        engine = WorkflowEngine(storage_path=temp_storage_path)
        session = engine.start_workflow(
            workflow_type="morning_setup",
            context={},
            user_id=sample_user_id
        )
        
        # 将当前步骤设为可选
        current_step = session.get_current_step()
        current_step.required = False
        
        suggestions = engine.get_next_suggestions(session.session_id)
        
        # 应该包含跳过选项
        skip_suggestions = [s for s in suggestions if "skip" in s.action_id]
        assert len(skip_suggestions) > 0


class TestWorkflowContext:
    """测试工作流上下文（Requirement 1.3）"""
    
    def test_get_workflow_context(self, temp_storage_path, sample_user_id):
        """测试获取工作流完整上下文"""
        engine = WorkflowEngine(storage_path=temp_storage_path)
        session = engine.start_workflow(
            workflow_type="morning_setup",
            context={"date": "2024-01-15"},
            user_id=sample_user_id
        )
        
        context = engine.get_workflow_context(session.session_id)
        
        assert context is not None
        assert context['session_id'] == session.session_id
        assert context['workflow_type'] == "morning_setup"
        assert 'workflow_name' in context
        assert 'progress' in context
        assert 'current_step' in context
        assert 'all_steps' in context
        assert 'related_functions' in context
        assert 'next_suggestions' in context
    
    def test_context_includes_all_related_functions(self, temp_storage_path, sample_user_id):
        """测试上下文包含所有相关功能（Requirement 1.3）"""
        engine = WorkflowEngine(storage_path=temp_storage_path)
        session = engine.start_workflow(
            workflow_type="morning_setup",
            context={},
            user_id=sample_user_id
        )
        
        context = engine.get_workflow_context(session.session_id)
        
        # 验证包含所有步骤的功能代码
        all_function_codes = set()
        for step in session.steps:
            all_function_codes.update(step.function_codes)
        
        assert set(context['related_functions']) == all_function_codes
    
    def test_context_shows_progress(self, temp_storage_path, sample_user_id):
        """测试上下文显示进度"""
        engine = WorkflowEngine(storage_path=temp_storage_path)
        session = engine.start_workflow(
            workflow_type="morning_setup",
            context={},
            user_id=sample_user_id
        )
        
        # 初始进度
        context = engine.get_workflow_context(session.session_id)
        assert context['progress'] == 0.0
        
        # 执行一步
        engine.execute_step(
            session_id=session.session_id,
            step_data={"action": "completed"}
        )
        
        # 更新后的进度
        context = engine.get_workflow_context(session.session_id)
        assert context['progress'] > 0.0


class TestWorkflowCustomization:
    """测试工作流自定义（Requirement 1.5）"""
    
    def test_save_workflow_customization(self, temp_storage_path, sample_user_id):
        """测试保存工作流自定义配置"""
        engine = WorkflowEngine(storage_path=temp_storage_path)
        
        customizations = {
            'step_order': ['morning_2', 'morning_1', 'morning_3'],
            'skipped_steps': ['morning_3']
        }
        
        result = engine.save_workflow_customization(
            user_id=sample_user_id,
            template_id="morning_setup_v1",
            customizations=customizations
        )
        
        assert result is True
        assert sample_user_id in engine.user_customizations
        assert "morning_setup_v1" in engine.user_customizations[sample_user_id]
    
    def test_customization_persistence(self, temp_storage_path, sample_user_id):
        """测试自定义配置持久化"""
        engine = WorkflowEngine(storage_path=temp_storage_path)
        
        customizations = {
            'step_order': ['morning_2', 'morning_1', 'morning_3']
        }
        
        engine.save_workflow_customization(
            user_id=sample_user_id,
            template_id="morning_setup_v1",
            customizations=customizations
        )
        
        # 创建新引擎实例，验证配置已加载
        engine2 = WorkflowEngine(storage_path=temp_storage_path)
        
        assert sample_user_id in engine2.user_customizations
        assert engine2.user_customizations[sample_user_id]["morning_setup_v1"] == customizations
    
    def test_apply_user_customizations(self, temp_storage_path, sample_user_id):
        """测试应用用户自定义配置"""
        engine = WorkflowEngine(storage_path=temp_storage_path)
        
        # 保存自定义配置
        customizations = {
            'step_order': ['morning_2', 'morning_1', 'morning_3'],
            'skipped_steps': ['morning_3']
        }
        
        engine.save_workflow_customization(
            user_id=sample_user_id,
            template_id="morning_setup_v1",
            customizations=customizations
        )
        
        # 获取原始模板
        template = engine.templates["morning_setup_v1"]
        original_step_order = [s.step_id for s in template.steps]
        
        # 应用自定义
        customized_template = engine.apply_user_customizations(template, sample_user_id)
        customized_step_order = [s.step_id for s in customized_template.steps]
        
        # 验证步骤顺序已改变
        assert customized_step_order != original_step_order
        assert customized_step_order == customizations['step_order']
        
        # 验证跳过的步骤标记为非必需
        for step in customized_template.steps:
            if step.step_id in customizations['skipped_steps']:
                assert not step.required
    
    def test_customizations_applied_on_workflow_start(self, temp_storage_path, sample_user_id):
        """测试启动工作流时应用自定义配置（Requirement 1.5）"""
        engine = WorkflowEngine(storage_path=temp_storage_path)
        
        # 保存自定义配置
        customizations = {
            'step_order': ['morning_2', 'morning_1', 'morning_3']
        }
        
        engine.save_workflow_customization(
            user_id=sample_user_id,
            template_id="morning_setup_v1",
            customizations=customizations
        )
        
        # 启动工作流
        session = engine.start_workflow(
            workflow_type="morning_setup",
            context={},
            user_id=sample_user_id
        )
        
        # 验证会话使用了自定义的步骤顺序
        session_step_order = [s.step_id for s in session.steps]
        assert session_step_order == customizations['step_order']
    
    def test_customization_with_step_params(self, temp_storage_path, sample_user_id):
        """测试步骤参数自定义"""
        engine = WorkflowEngine(storage_path=temp_storage_path)
        
        customizations = {
            'step_params': {
                'morning_1': {
                    'custom_param': 'custom_value',
                    'priority': 'high'
                }
            }
        }
        
        engine.save_workflow_customization(
            user_id=sample_user_id,
            template_id="morning_setup_v1",
            customizations=customizations
        )
        
        # 应用自定义
        template = engine.templates["morning_setup_v1"]
        customized_template = engine.apply_user_customizations(template, sample_user_id)
        
        # 验证步骤参数已更新
        morning_1_step = next(s for s in customized_template.steps if s.step_id == 'morning_1')
        assert 'custom_param' in morning_1_step.metadata
        assert morning_1_step.metadata['custom_param'] == 'custom_value'


class TestWorkflowTemplates:
    """测试工作流模板管理"""
    
    def test_get_workflow_templates(self, temp_storage_path):
        """测试获取工作流模板列表"""
        engine = WorkflowEngine(storage_path=temp_storage_path)
        templates = engine.get_workflow_templates()
        
        assert len(templates) > 0
        assert all(hasattr(t, 'template_id') for t in templates)
        assert all(hasattr(t, 'workflow_type') for t in templates)
    
    def test_find_template_for_type(self, temp_storage_path):
        """测试查找指定类型的模板"""
        engine = WorkflowEngine(storage_path=temp_storage_path)
        
        template = engine._find_template_for_type(WorkflowType.MORNING_SETUP)
        assert template is not None
        assert template.workflow_type == WorkflowType.MORNING_SETUP
    
    def test_workflow_templates_have_steps(self, temp_storage_path):
        """测试工作流模板包含步骤"""
        engine = WorkflowEngine(storage_path=temp_storage_path)
        templates = engine.get_workflow_templates()
        
        for template in templates:
            assert len(template.steps) > 0
            assert all(isinstance(step, WorkflowStep) for step in template.steps)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
