# -*- coding: utf-8 -*-
"""
Workflow Engine
工作流引擎 - 编排多步骤财务流程并维护工作流状态
"""

import uuid
import json
import logging
from datetime import datetime
from typing import Dict, List, Optional, Any
from pathlib import Path

from ..models.workflow_models import (
    WorkflowSession,
    WorkflowTemplate,
    WorkflowAction,
    StepResult,
    WorkflowType,
    WorkflowStep,
    StepStatus
)

logger = logging.getLogger(__name__)


class WorkflowEngine:
    """
    工作流引擎
    
    负责：
    - 创建和管理工作流会话
    - 执行工作流步骤
    - 提供下一步建议
    - 保存和恢复工作流状态
    - 管理工作流模板
    - 支持工作流自定义和个性化（Requirement 1.5）
    """
    
    def __init__(self, storage_path: str = "财务数据/workflow_sessions"):
        """
        初始化工作流引擎
        
        Args:
            storage_path: 工作流会话存储路径
        """
        self.storage_path = Path(storage_path)
        self.storage_path.mkdir(parents=True, exist_ok=True)
        
        # 用户自定义配置存储路径
        self.customization_path = self.storage_path / "customizations"
        self.customization_path.mkdir(parents=True, exist_ok=True)
        
        self.templates: Dict[str, WorkflowTemplate] = {}
        self.active_sessions: Dict[str, WorkflowSession] = {}
        self.user_customizations: Dict[str, Dict[str, Any]] = {}  # user_id -> customizations
        
        self._load_default_templates()
        self._load_user_customizations()
        logger.info("WorkflowEngine initialized")

    def _load_default_templates(self) -> None:
        """加载默认工作流模板"""
        # 早晨设置工作流
        morning_template = WorkflowTemplate(
            template_id="morning_setup_v1",
            name="早晨设置",
            description="每日早晨的优先任务检查和系统状态确认",
            workflow_type=WorkflowType.MORNING_SETUP,
            steps=[
                WorkflowStep(
                    step_id="morning_1",
                    name="查看今日优先任务",
                    description="检查今天需要完成的重要任务",
                    function_codes=["57"],  # 查看日志
                    estimated_duration=60
                ),
                WorkflowStep(
                    step_id="morning_2",
                    name="检查待处理事项",
                    description="查看待对账、待补录等待处理项",
                    function_codes=["15", "16"],  # 银行流水相关
                    estimated_duration=120
                ),
                WorkflowStep(
                    step_id="morning_3",
                    name="系统状态确认",
                    description="确认系统运行正常，数据完整",
                    function_codes=["53"],  # 备份
                    estimated_duration=30
                )
            ]
        )
        self.templates[morning_template.template_id] = morning_template

        # 交易录入工作流
        transaction_template = WorkflowTemplate(
            template_id="transaction_entry_v1",
            name="交易录入",
            description="智能交易录入流程，带上下文感知默认值",
            workflow_type=WorkflowType.TRANSACTION_ENTRY,
            steps=[
                WorkflowStep(
                    step_id="trans_1",
                    name="选择交易类型",
                    description="选择收入、支出或其他交易类型",
                    function_codes=["1", "2"],  # 收支记录
                    estimated_duration=30
                ),
                WorkflowStep(
                    step_id="trans_2",
                    name="录入交易详情",
                    description="填写交易金额、日期、客户等信息",
                    function_codes=["1", "2"],
                    estimated_duration=120
                ),
                WorkflowStep(
                    step_id="trans_3",
                    name="验证并保存",
                    description="验证数据完整性并保存交易",
                    function_codes=["1", "2"],
                    estimated_duration=30
                )
            ]
        )
        self.templates[transaction_template.template_id] = transaction_template

        # 日终工作流
        end_of_day_template = WorkflowTemplate(
            template_id="end_of_day_v1",
            name="日终处理",
            description="每日结束时的汇总、备份和准备工作",
            workflow_type=WorkflowType.END_OF_DAY,
            steps=[
                WorkflowStep(
                    step_id="eod_1",
                    name="生成日结报告",
                    description="生成今日财务汇总报告",
                    function_codes=["31"],  # 日结报告
                    estimated_duration=60
                ),
                WorkflowStep(
                    step_id="eod_2",
                    name="数据备份",
                    description="备份今日所有财务数据",
                    function_codes=["53"],  # 备份
                    estimated_duration=30
                ),
                WorkflowStep(
                    step_id="eod_3",
                    name="准备明日任务",
                    description="查看明日待办事项和提醒",
                    function_codes=["57"],  # 查看日志
                    estimated_duration=60
                )
            ]
        )
        self.templates[end_of_day_template.template_id] = end_of_day_template
        
        logger.info(f"Loaded {len(self.templates)} default workflow templates")

    def _load_user_customizations(self) -> None:
        """加载用户自定义配置（Requirement 1.5）"""
        try:
            for customization_file in self.customization_path.glob("*.json"):
                user_id = customization_file.stem
                with open(customization_file, 'r', encoding='utf-8') as f:
                    self.user_customizations[user_id] = json.load(f)
            logger.info(f"Loaded customizations for {len(self.user_customizations)} users")
        except Exception as e:
            logger.error(f"Failed to load user customizations: {e}")

    def _save_user_customizations(self, user_id: str) -> bool:
        """保存用户自定义配置（Requirement 1.5）"""
        try:
            customization_file = self.customization_path / f"{user_id}.json"
            customizations = self.user_customizations.get(user_id, {})
            with open(customization_file, 'w', encoding='utf-8') as f:
                json.dump(customizations, f, ensure_ascii=False, indent=2)
            logger.debug(f"Saved customizations for user {user_id}")
            return True
        except Exception as e:
            logger.error(f"Failed to save user customizations: {e}")
            return False

    def apply_user_customizations(
        self, 
        template: WorkflowTemplate, 
        user_id: str
    ) -> WorkflowTemplate:
        """
        应用用户自定义配置到工作流模板（Requirement 1.5）
        
        Args:
            template: 原始模板
            user_id: 用户ID
            
        Returns:
            WorkflowTemplate: 应用自定义后的模板
        """
        customizations = self.user_customizations.get(user_id, {})
        template_customizations = customizations.get(template.template_id, {})
        
        if not template_customizations:
            return template
        
        # 创建模板副本
        import copy
        customized_template = copy.deepcopy(template)
        
        # 应用步骤顺序自定义
        if 'step_order' in template_customizations:
            step_order = template_customizations['step_order']
            step_dict = {step.step_id: step for step in customized_template.steps}
            customized_template.steps = [
                step_dict[step_id] for step_id in step_order 
                if step_id in step_dict
            ]
        
        # 应用步骤跳过设置
        if 'skipped_steps' in template_customizations:
            skipped_steps = set(template_customizations['skipped_steps'])
            for step in customized_template.steps:
                if step.step_id in skipped_steps:
                    step.required = False
        
        # 应用步骤自定义参数
        if 'step_params' in template_customizations:
            step_params = template_customizations['step_params']
            for step in customized_template.steps:
                if step.step_id in step_params:
                    step.metadata.update(step_params[step.step_id])
        
        logger.debug(f"Applied customizations for user {user_id} to template {template.template_id}")
        return customized_template

    def save_workflow_customization(
        self,
        user_id: str,
        template_id: str,
        customizations: Dict[str, Any]
    ) -> bool:
        """
        保存工作流自定义配置（Requirement 1.5）
        
        Args:
            user_id: 用户ID
            template_id: 模板ID
            customizations: 自定义配置
            
        Returns:
            bool: 是否保存成功
        """
        if user_id not in self.user_customizations:
            self.user_customizations[user_id] = {}
        
        self.user_customizations[user_id][template_id] = customizations
        return self._save_user_customizations(user_id)

    def start_workflow(
        self, 
        workflow_type: str, 
        context: Dict[str, Any],
        user_id: str = "default_user"
    ) -> WorkflowSession:
        """
        启动新的工作流会话（Requirements 1.2, 1.3, 1.5）
        
        Args:
            workflow_type: 工作流类型（字符串）
            context: 上下文信息
            user_id: 用户ID
            
        Returns:
            WorkflowSession: 新创建的工作流会话
        """
        # 转换工作流类型
        try:
            wf_type = WorkflowType(workflow_type)
        except ValueError:
            wf_type = WorkflowType.CUSTOM
            logger.warning(f"Unknown workflow type: {workflow_type}, using CUSTOM")
        
        # 查找对应的模板
        template = self._find_template_for_type(wf_type)
        if not template:
            raise ValueError(f"No template found for workflow type: {workflow_type}")
        
        # 应用用户自定义配置（Requirement 1.5）
        customized_template = self.apply_user_customizations(template, user_id)
        
        # 创建会话
        session_id = str(uuid.uuid4())
        session = WorkflowSession(
            session_id=session_id,
            user_id=user_id,
            workflow_type=wf_type,
            template_id=template.template_id,
            steps=customized_template.steps.copy(),
            context=context
        )
        
        self.active_sessions[session_id] = session
        self.save_workflow_state(session_id)
        
        logger.info(f"Started workflow session {session_id} of type {workflow_type} for user {user_id}")
        return session

    def _find_template_for_type(self, workflow_type: WorkflowType) -> Optional[WorkflowTemplate]:
        """查找指定类型的模板"""
        for template in self.templates.values():
            if template.workflow_type == workflow_type:
                return template
        return None
    
    def execute_step(
        self, 
        session_id: str, 
        step_data: Dict[str, Any]
    ) -> StepResult:
        """
        执行工作流步骤
        
        Args:
            session_id: 会话ID
            step_data: 步骤数据
            
        Returns:
            StepResult: 步骤执行结果
        """
        session = self.active_sessions.get(session_id)
        if not session:
            return StepResult(
                step_id="",
                status=StepStatus.FAILED,
                success=False,
                message=f"Session {session_id} not found"
            )
        
        current_step = session.get_current_step()
        if not current_step:
            return StepResult(
                step_id="",
                status=StepStatus.FAILED,
                success=False,
                message="No current step available"
            )
        
        # 执行步骤（这里是简化版本，实际会调用V1.4功能）
        start_time = datetime.now()
        try:
            # 更新步骤状态
            current_step.status = StepStatus.IN_PROGRESS
            session.step_data[current_step.step_id] = step_data
            
            # 标记步骤完成
            current_step.status = StepStatus.COMPLETED
            session.mark_step_completed(current_step.step_id)
            session.current_step += 1
            
            execution_time = (datetime.now() - start_time).total_seconds()
            
            # 获取下一步建议
            next_suggestions = self.get_next_suggestions(session_id)
            
            result = StepResult(
                step_id=current_step.step_id,
                status=StepStatus.COMPLETED,
                success=True,
                message=f"Step {current_step.name} completed successfully",
                data=step_data,
                next_suggestions=next_suggestions,
                execution_time=execution_time
            )
            
            self.save_workflow_state(session_id)
            logger.info(f"Executed step {current_step.step_id} in session {session_id}")
            
            return result
            
        except Exception as e:
            current_step.status = StepStatus.FAILED
            logger.error(f"Failed to execute step {current_step.step_id}: {e}")
            return StepResult(
                step_id=current_step.step_id,
                status=StepStatus.FAILED,
                success=False,
                message=str(e)
            )

    def get_next_suggestions(self, session_id: str) -> List[WorkflowAction]:
        """
        获取下一步建议（Requirement 1.2 - 自动建议下一步）
        
        Args:
            session_id: 会话ID
            
        Returns:
            List[WorkflowAction]: 建议的下一步操作列表
        """
        session = self.active_sessions.get(session_id)
        if not session:
            return []
        
        suggestions = []
        current_step = session.get_current_step()
        
        if current_step:
            # 为当前步骤创建建议（Requirement 1.3 - 单一上下文界面）
            for func_code in current_step.function_codes:
                action = WorkflowAction(
                    action_id=f"action_{current_step.step_id}_{func_code}",
                    name=current_step.name,
                    description=current_step.description,
                    function_code=func_code,
                    is_primary=True,
                    confidence=0.9,
                    metadata={
                        'step_id': current_step.step_id,
                        'estimated_duration': current_step.estimated_duration
                    }
                )
                suggestions.append(action)
            
            # 如果当前步骤有依赖关系，检查是否可以跳过
            if not current_step.required and len(session.steps) > session.current_step + 1:
                next_step = session.steps[session.current_step + 1]
                skip_action = WorkflowAction(
                    action_id=f"skip_{current_step.step_id}",
                    name=f"跳过并继续到：{next_step.name}",
                    description=f"跳过当前步骤，继续到下一步：{next_step.description}",
                    function_code="skip",
                    is_primary=False,
                    confidence=0.6,
                    metadata={'skip_to_step': next_step.step_id}
                )
                suggestions.append(skip_action)
        else:
            # 工作流已完成，建议相关的后续操作（Requirement 1.2）
            if session.workflow_type == WorkflowType.MORNING_SETUP:
                suggestions.append(WorkflowAction(
                    action_id="next_transaction",
                    name="开始录入交易",
                    description="开始今日的交易录入工作",
                    function_code="1",
                    is_primary=True,
                    confidence=0.8
                ))
                suggestions.append(WorkflowAction(
                    action_id="check_bank_statements",
                    name="查看银行流水",
                    description="检查和对账银行流水",
                    function_code="15",
                    is_primary=True,
                    confidence=0.7
                ))
            elif session.workflow_type == WorkflowType.TRANSACTION_ENTRY:
                suggestions.append(WorkflowAction(
                    action_id="continue_entry",
                    name="继续录入交易",
                    description="录入更多交易",
                    function_code="1",
                    is_primary=True,
                    confidence=0.8
                ))
                suggestions.append(WorkflowAction(
                    action_id="view_reports",
                    name="查看报表",
                    description="查看今日交易汇总",
                    function_code="31",
                    is_primary=False,
                    confidence=0.5
                ))
            elif session.workflow_type == WorkflowType.END_OF_DAY:
                suggestions.append(WorkflowAction(
                    action_id="review_tomorrow",
                    name="查看明日任务",
                    description="查看明天的待办事项",
                    function_code="57",
                    is_primary=True,
                    confidence=0.7
                ))
        
        return suggestions[:5]  # 最多返回5个建议

    def get_workflow_context(self, session_id: str) -> Dict[str, Any]:
        """
        获取工作流的完整上下文（Requirement 1.3 - 单一上下文界面）
        
        返回工作流相关的所有功能和信息，无需导航到其他区域
        
        Args:
            session_id: 会话ID
            
        Returns:
            Dict[str, Any]: 包含所有相关功能和信息的上下文
        """
        session = self.active_sessions.get(session_id)
        if not session:
            return {}
        
        # 收集所有相关功能代码
        all_function_codes = set()
        for step in session.steps:
            all_function_codes.update(step.function_codes)
        
        # 获取当前步骤
        current_step = session.get_current_step()
        
        # 构建完整上下文
        context = {
            'session_id': session_id,
            'workflow_type': session.workflow_type.value,
            'workflow_name': self._get_workflow_name(session.workflow_type),
            'progress': session.get_progress(),
            'current_step': {
                'step_id': current_step.step_id if current_step else None,
                'name': current_step.name if current_step else None,
                'description': current_step.description if current_step else None,
                'estimated_duration': current_step.estimated_duration if current_step else 0
            } if current_step else None,
            'all_steps': [
                {
                    'step_id': step.step_id,
                    'name': step.name,
                    'description': step.description,
                    'status': step.status.value,
                    'required': step.required,
                    'function_codes': step.function_codes
                }
                for step in session.steps
            ],
            'related_functions': list(all_function_codes),
            'completed_steps': session.completed_steps,
            'next_suggestions': self.get_next_suggestions(session_id),
            'context_data': session.context
        }
        
        return context

    def _get_workflow_name(self, workflow_type: WorkflowType) -> str:
        """获取工作流类型的中文名称"""
        names = {
            WorkflowType.MORNING_SETUP: "早晨设置",
            WorkflowType.TRANSACTION_ENTRY: "交易录入",
            WorkflowType.END_OF_DAY: "日终处理",
            WorkflowType.MONTHLY_CLOSE: "月度结账",
            WorkflowType.CUSTOM: "自定义工作流"
        }
        return names.get(workflow_type, "未知工作流")

    def save_workflow_state(self, session_id: str) -> bool:
        """
        保存工作流状态
        
        Args:
            session_id: 会话ID
            
        Returns:
            bool: 是否保存成功
        """
        session = self.active_sessions.get(session_id)
        if not session:
            return False
        
        try:
            file_path = self.storage_path / f"{session_id}.json"
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(session.to_dict(), f, ensure_ascii=False, indent=2)
            logger.debug(f"Saved workflow state for session {session_id}")
            return True
        except Exception as e:
            logger.error(f"Failed to save workflow state: {e}")
            return False
    
    def load_workflow_state(self, session_id: str) -> Optional[WorkflowSession]:
        """
        加载工作流状态
        
        Args:
            session_id: 会话ID
            
        Returns:
            Optional[WorkflowSession]: 工作流会话，如果不存在则返回None
        """
        try:
            file_path = self.storage_path / f"{session_id}.json"
            if not file_path.exists():
                return None
            
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # 重建WorkflowSession对象（简化版本）
            session = WorkflowSession(
                session_id=data['session_id'],
                user_id=data['user_id'],
                workflow_type=WorkflowType(data['workflow_type']),
                template_id=data['template_id'],
                current_step=data['current_step'],
                step_data=data['step_data'],
                context=data['context'],
                is_active=data['is_active'],
                completed_steps=data['completed_steps'],
                customizations=data['customizations']
            )
            
            self.active_sessions[session_id] = session
            logger.info(f"Loaded workflow state for session {session_id}")
            return session
            
        except Exception as e:
            logger.error(f"Failed to load workflow state: {e}")
            return None

    def get_workflow_templates(
        self, 
        user_patterns: Optional[Dict[str, Any]] = None
    ) -> List[WorkflowTemplate]:
        """
        获取工作流模板列表
        
        Args:
            user_patterns: 用户行为模式（用于个性化推荐）
            
        Returns:
            List[WorkflowTemplate]: 工作流模板列表
        """
        templates = list(self.templates.values())
        
        # 如果提供了用户模式，可以根据模式排序模板
        if user_patterns:
            # 这里可以添加基于用户模式的排序逻辑
            pass
        
        return templates
    
    def get_active_session(self, user_id: str) -> Optional[WorkflowSession]:
        """
        获取用户的活跃会话
        
        Args:
            user_id: 用户ID
            
        Returns:
            Optional[WorkflowSession]: 活跃的工作流会话
        """
        for session in self.active_sessions.values():
            if session.user_id == user_id and session.is_active:
                return session
        return None
    
    def close_session(self, session_id: str) -> bool:
        """
        关闭工作流会话
        
        Args:
            session_id: 会话ID
            
        Returns:
            bool: 是否成功关闭
        """
        session = self.active_sessions.get(session_id)
        if not session:
            return False
        
        session.is_active = False
        self.save_workflow_state(session_id)
        logger.info(f"Closed workflow session {session_id}")
        return True

    def resume_session(self, session_id: str) -> Optional[WorkflowSession]:
        """
        恢复工作流会话（Requirement 1.4 - 工作流状态管理）
        
        Args:
            session_id: 会话ID
            
        Returns:
            Optional[WorkflowSession]: 恢复的会话，如果不存在则返回None
        """
        # 如果会话已在内存中，直接返回
        if session_id in self.active_sessions:
            session = self.active_sessions[session_id]
            if not session.is_active:
                session.is_active = True
                self.save_workflow_state(session_id)
            return session
        
        # 从存储加载会话
        session = self.load_workflow_state(session_id)
        if session:
            session.is_active = True
            self.save_workflow_state(session_id)
            logger.info(f"Resumed workflow session {session_id}")
        return session

    def get_user_sessions(
        self, 
        user_id: str, 
        active_only: bool = True
    ) -> List[WorkflowSession]:
        """
        获取用户的所有会话（Requirement 1.4 - 会话管理）
        
        Args:
            user_id: 用户ID
            active_only: 是否只返回活跃会话
            
        Returns:
            List[WorkflowSession]: 用户的会话列表
        """
        sessions = []
        
        # 从内存中的活跃会话获取
        for session in self.active_sessions.values():
            if session.user_id == user_id:
                if not active_only or session.is_active:
                    sessions.append(session)
        
        # 从存储中加载其他会话
        try:
            for session_file in self.storage_path.glob("*.json"):
                session_id = session_file.stem
                if session_id not in self.active_sessions:
                    session = self.load_workflow_state(session_id)
                    if session and session.user_id == user_id:
                        if not active_only or session.is_active:
                            sessions.append(session)
        except Exception as e:
            logger.error(f"Failed to load user sessions: {e}")
        
        return sessions

    def skip_current_step(self, session_id: str) -> StepResult:
        """
        跳过当前步骤（用于可选步骤）
        
        Args:
            session_id: 会话ID
            
        Returns:
            StepResult: 步骤执行结果
        """
        session = self.active_sessions.get(session_id)
        if not session:
            return StepResult(
                step_id="",
                status=StepStatus.FAILED,
                success=False,
                message=f"Session {session_id} not found"
            )
        
        current_step = session.get_current_step()
        if not current_step:
            return StepResult(
                step_id="",
                status=StepStatus.FAILED,
                success=False,
                message="No current step available"
            )
        
        if current_step.required:
            return StepResult(
                step_id=current_step.step_id,
                status=StepStatus.FAILED,
                success=False,
                message="Cannot skip required step"
            )
        
        # 标记步骤为跳过
        current_step.status = StepStatus.SKIPPED
        session.current_step += 1
        
        # 获取下一步建议
        next_suggestions = self.get_next_suggestions(session_id)
        
        result = StepResult(
            step_id=current_step.step_id,
            status=StepStatus.SKIPPED,
            success=True,
            message=f"Skipped step {current_step.name}",
            next_suggestions=next_suggestions
        )
        
        self.save_workflow_state(session_id)
        logger.info(f"Skipped step {current_step.step_id} in session {session_id}")
        
        return result
