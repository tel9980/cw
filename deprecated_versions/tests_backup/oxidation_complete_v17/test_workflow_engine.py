"""
Unit Tests for Workflow Engine - 工作流引擎单元测试

测试工作流引擎的所有功能
"""

import pytest
import tempfile
import shutil
from pathlib import Path
from oxidation_complete_v17.workflow.workflow_engine import OxidationWorkflowEngine
from oxidation_complete_v17.workflow.workflow_models import (
    WorkflowType,
    StepStatus
)


class TestOxidationWorkflowEngine:
    """测试氧化加工厂工作流引擎"""
    
    @pytest.fixture
    def temp_storage(self):
        """创建临时存储目录"""
        temp_dir = tempfile.mkdtemp()
        yield temp_dir
        shutil.rmtree(temp_dir)
    
    @pytest.fixture
    def workflow_engine(self, temp_storage):
        """创建工作流引擎实例"""
        return OxidationWorkflowEngine(storage_path=temp_storage)
    
    def test_initialization(self, workflow_engine):
        """测试初始化"""
        assert workflow_engine is not None
        assert len(workflow_engine.templates) == 5  # 5个默认模板
        assert workflow_engine.storage_path.exists()
        assert workflow_engine.customization_path.exists()
    
    def test_load_default_templates(self, workflow_engine):
        """测试加载默认模板"""
        templates = workflow_engine.get_workflow_templates()
        assert len(templates) == 5
        
        # 验证模板类型
        template_types = [t.workflow_type for t in templates]
        assert WorkflowType.MORNING_SETUP in template_types
        assert WorkflowType.ORDER_PROCESSING in template_types
        assert WorkflowType.TRANSACTION_ENTRY in template_types
        assert WorkflowType.REPORT_GENERATION in template_types
        assert WorkflowType.END_OF_DAY in template_types
    
    def test_morning_setup_template(self, workflow_engine):
        """测试早晨准备模板"""
        template = workflow_engine._find_template_for_type(WorkflowType.MORNING_SETUP)
        assert template is not None
        assert template.name == "早晨准备"
        assert len(template.steps) == 3
        assert template.steps[0].name == "查看智能工作台"
    
    def test_order_processing_template(self, workflow_engine):
        """测试订单处理模板"""
        template = workflow_engine._find_template_for_type(WorkflowType.ORDER_PROCESSING)
        assert template is not None
        assert template.name == "订单处理"
        assert len(template.steps) == 4
        assert template.steps[0].name == "创建加工订单"
        # 验证外发加工步骤是可选的
        assert template.steps[1].required is False
    
    def test_transaction_entry_template(self, workflow_engine):
        """测试交易录入模板"""
        template = workflow_engine._find_template_for_type(WorkflowType.TRANSACTION_ENTRY)
        assert template is not None
        assert template.name == "交易录入"
        assert len(template.steps) == 4
        assert template.steps[0].name == "导入银行流水"
    
    def test_report_generation_template(self, workflow_engine):
        """测试报表生成模板"""
        template = workflow_engine._find_template_for_type(WorkflowType.REPORT_GENERATION)
        assert template is not None
        assert template.name == "报表生成"
        assert len(template.steps) == 4
        assert template.steps[0].name == "生成加工费收入明细"
    
    def test_end_of_day_template(self, workflow_engine):
        """测试日终处理模板"""
        template = workflow_engine._find_template_for_type(WorkflowType.END_OF_DAY)
        assert template is not None
        assert template.name == "日终处理"
        assert len(template.steps) == 4
        assert template.steps[0].name == "核对账户余额"
    
    def test_start_workflow(self, workflow_engine):
        """测试启动工作流"""
        session = workflow_engine.start_workflow(
            workflow_type="morning_setup",
            context={"user_name": "张会计"},
            user_id="user_001"
        )
        
        assert session is not None
        assert session.workflow_type == WorkflowType.MORNING_SETUP
        assert session.user_id == "user_001"
        assert session.is_active is True
        assert len(session.steps) == 3
        assert session.current_step == 0
    
    def test_start_workflow_invalid_type(self, workflow_engine):
        """测试启动无效类型的工作流"""
        # 无效类型应该抛出异常,因为没有CUSTOM类型的模板
        with pytest.raises(ValueError, match="No template found"):
            workflow_engine.start_workflow(
                workflow_type="invalid_type",
                context={},
                user_id="user_001"
            )
    
    def test_execute_step(self, workflow_engine):
        """测试执行步骤"""
        session = workflow_engine.start_workflow(
            workflow_type="morning_setup",
            context={},
            user_id="user_001"
        )
        
        result = workflow_engine.execute_step(
            session_id=session.session_id,
            step_data={"completed": True}
        )
        
        assert result.success is True
        assert result.status == StepStatus.COMPLETED
        assert session.current_step == 1
        assert len(session.completed_steps) == 1
    
    def test_execute_step_invalid_session(self, workflow_engine):
        """测试执行无效会话的步骤"""
        result = workflow_engine.execute_step(
            session_id="invalid_session",
            step_data={}
        )
        
        assert result.success is False
        assert "not found" in result.message
    
    def test_get_next_suggestions(self, workflow_engine):
        """测试获取下一步建议"""
        session = workflow_engine.start_workflow(
            workflow_type="morning_setup",
            context={},
            user_id="user_001"
        )
        
        suggestions = workflow_engine.get_next_suggestions(session.session_id)
        
        assert len(suggestions) > 0
        assert suggestions[0].name == "查看智能工作台"
    
    def test_skip_current_step(self, workflow_engine):
        """测试跳过当前步骤"""
        session = workflow_engine.start_workflow(
            workflow_type="order_processing",
            context={},
            user_id="user_001"
        )
        
        # 跳到外发加工步骤(可选)
        workflow_engine.execute_step(session.session_id, {})
        
        result = workflow_engine.skip_current_step(session.session_id)
        
        assert result.success is True
        assert result.status == StepStatus.SKIPPED
        assert session.current_step == 2
    
    def test_skip_required_step(self, workflow_engine):
        """测试跳过必需步骤"""
        session = workflow_engine.start_workflow(
            workflow_type="morning_setup",
            context={},
            user_id="user_001"
        )
        
        result = workflow_engine.skip_current_step(session.session_id)
        
        assert result.success is False
        assert "Cannot skip required step" in result.message
    
    def test_save_and_load_workflow_state(self, workflow_engine):
        """测试保存和加载工作流状态"""
        session = workflow_engine.start_workflow(
            workflow_type="morning_setup",
            context={"test": "data"},
            user_id="user_001"
        )
        
        session_id = session.session_id
        
        # 保存状态
        assert workflow_engine.save_workflow_state(session_id) is True
        
        # 清除内存中的会话
        workflow_engine.active_sessions.clear()
        
        # 加载状态
        loaded_session = workflow_engine.load_workflow_state(session_id)
        
        assert loaded_session is not None
        assert loaded_session.session_id == session_id
        assert loaded_session.user_id == "user_001"
        assert loaded_session.context["test"] == "data"
    
    def test_get_template_by_id(self, workflow_engine):
        """测试根据ID获取模板"""
        template = workflow_engine.get_template_by_id("oxidation_morning_v1")
        
        assert template is not None
        assert template.name == "早晨准备"
    
    def test_get_active_session(self, workflow_engine):
        """测试获取活跃会话"""
        session = workflow_engine.start_workflow(
            workflow_type="morning_setup",
            context={},
            user_id="user_001"
        )
        
        active_session = workflow_engine.get_active_session("user_001")
        
        assert active_session is not None
        assert active_session.session_id == session.session_id
    
    def test_close_session(self, workflow_engine):
        """测试关闭会话"""
        session = workflow_engine.start_workflow(
            workflow_type="morning_setup",
            context={},
            user_id="user_001"
        )
        
        assert workflow_engine.close_session(session.session_id) is True
        assert session.is_active is False
    
    def test_resume_session(self, workflow_engine):
        """测试恢复会话"""
        session = workflow_engine.start_workflow(
            workflow_type="morning_setup",
            context={},
            user_id="user_001"
        )
        
        session_id = session.session_id
        
        # 关闭会话
        workflow_engine.close_session(session_id)
        
        # 恢复会话
        resumed_session = workflow_engine.resume_session(session_id)
        
        assert resumed_session is not None
        assert resumed_session.is_active is True
    
    def test_get_user_sessions(self, workflow_engine):
        """测试获取用户会话"""
        # 创建多个会话
        session1 = workflow_engine.start_workflow(
            workflow_type="morning_setup",
            context={},
            user_id="user_001"
        )
        
        session2 = workflow_engine.start_workflow(
            workflow_type="order_processing",
            context={},
            user_id="user_001"
        )
        
        sessions = workflow_engine.get_user_sessions("user_001")
        
        assert len(sessions) == 2
    
    def test_save_workflow_customization(self, workflow_engine):
        """测试保存工作流自定义"""
        customizations = {
            "step_order": ["morning_2", "morning_1", "morning_3"],
            "skipped_steps": ["morning_3"]
        }
        
        result = workflow_engine.save_workflow_customization(
            user_id="user_001",
            template_id="oxidation_morning_v1",
            customizations=customizations
        )
        
        assert result is True
        assert "user_001" in workflow_engine.user_customizations
    
    def test_apply_user_customizations(self, workflow_engine):
        """测试应用用户自定义"""
        # 保存自定义
        customizations = {
            "step_order": ["morning_2", "morning_1", "morning_3"]
        }
        workflow_engine.save_workflow_customization(
            user_id="user_001",
            template_id="oxidation_morning_v1",
            customizations=customizations
        )
        
        # 获取模板
        template = workflow_engine.get_template_by_id("oxidation_morning_v1")
        
        # 应用自定义
        customized_template = workflow_engine.apply_user_customizations(
            template=template,
            user_id="user_001"
        )
        
        # 验证步骤顺序已改变
        assert customized_template.steps[0].step_id == "morning_2"
        assert customized_template.steps[1].step_id == "morning_1"
    
    def test_workflow_progress(self, workflow_engine):
        """测试工作流进度"""
        session = workflow_engine.start_workflow(
            workflow_type="morning_setup",
            context={},
            user_id="user_001"
        )
        
        # 初始进度应该是0
        assert session.get_progress() == 0.0
        
        # 完成第一步
        workflow_engine.execute_step(session.session_id, {})
        assert session.get_progress() == pytest.approx(1/3, 0.01)
        
        # 完成第二步
        workflow_engine.execute_step(session.session_id, {})
        assert session.get_progress() == pytest.approx(2/3, 0.01)
        
        # 完成第三步
        workflow_engine.execute_step(session.session_id, {})
        assert session.get_progress() == 1.0
    
    def test_workflow_completion_suggestions(self, workflow_engine):
        """测试工作流完成后的建议"""
        session = workflow_engine.start_workflow(
            workflow_type="morning_setup",
            context={},
            user_id="user_001"
        )
        
        # 完成所有步骤
        for _ in range(3):
            workflow_engine.execute_step(session.session_id, {})
        
        # 获取完成后的建议
        suggestions = workflow_engine.get_next_suggestions(session.session_id)
        
        assert len(suggestions) > 0
        # 应该建议开始处理订单
        assert any("订单" in s.description for s in suggestions)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
