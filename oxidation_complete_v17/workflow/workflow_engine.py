"""
Workflow Engine for Oxidation Factory - 氧化加工厂工作流引擎

从V1.5复用WorkflowEngine并扩展氧化加工厂专用工作流模板

Requirements: B2
"""

import uuid
import json
import logging
from datetime import datetime
from typing import Dict, List, Optional, Any
from pathlib import Path

from .workflow_models import (
    WorkflowSession,
    WorkflowTemplate,
    WorkflowAction,
    StepResult,
    WorkflowType,
    WorkflowStep,
    StepStatus
)

logger = logging.getLogger(__name__)


class OxidationWorkflowEngine:
    """
    氧化加工厂工作流引擎
    
    功能:
    - 创建和管理工作流会话
    - 执行工作流步骤
    - 提供下一步建议
    - 保存和恢复工作流状态
    - 管理工作流模板
    - 支持工作流自定义和个性化
    """
    
    def __init__(self, storage_path: str = "data/workflow_sessions"):
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
        self.user_customizations: Dict[str, Dict[str, Any]] = {}
        
        self._load_default_templates()
        self._load_user_customizations()
        logger.info("OxidationWorkflowEngine initialized")
    
    def _load_default_templates(self) -> None:
        """加载默认工作流模板(氧化加工厂专用)"""
        
        # 1. 早晨准备工作流
        morning_template = WorkflowTemplate(
            template_id="oxidation_morning_v1",
            name="早晨准备",
            description="每日早晨的工作台检查和系统准备",
            workflow_type=WorkflowType.MORNING_SETUP,
            steps=[
                WorkflowStep(
                    step_id="morning_1",
                    name="查看智能工作台",
                    description="查看今日优先任务和提醒",
                    function_codes=["dashboard"],
                    estimated_duration=60
                ),
                WorkflowStep(
                    step_id="morning_2",
                    name="检查超期未收款",
                    description="查看超期未收款订单",
                    function_codes=["overdue_payments"],
                    estimated_duration=120
                ),
                WorkflowStep(
                    step_id="morning_3",
                    name="查看待处理订单",
                    description="查看进行中的加工订单",
                    function_codes=["pending_orders"],
                    estimated_duration=60
                )
            ]
        )
        self.templates[morning_template.template_id] = morning_template
        
        # 2. 订单处理工作流(氧化加工厂特色)
        order_template = WorkflowTemplate(
            template_id="oxidation_order_v1",
            name="订单处理",
            description="加工订单的完整处理流程",
            workflow_type=WorkflowType.ORDER_PROCESSING,
            steps=[
                WorkflowStep(
                    step_id="order_1",
                    name="创建加工订单",
                    description="录入客户、数量、计价单位等信息",
                    function_codes=["create_order"],
                    estimated_duration=180
                ),
                WorkflowStep(
                    step_id="order_2",
                    name="记录外发加工",
                    description="如有外发工序,记录外发加工信息",
                    function_codes=["create_outsourced"],
                    estimated_duration=120,
                    required=False  # 可选步骤
                ),
                WorkflowStep(
                    step_id="order_3",
                    name="更新订单状态",
                    description="更新订单进度和状态",
                    function_codes=["update_order"],
                    estimated_duration=60
                ),
                WorkflowStep(
                    step_id="order_4",
                    name="记录收款",
                    description="记录客户付款",
                    function_codes=["record_payment"],
                    estimated_duration=90
                )
            ]
        )
        self.templates[order_template.template_id] = order_template
        
        # 3. 交易录入工作流
        transaction_template = WorkflowTemplate(
            template_id="oxidation_transaction_v1",
            name="交易录入",
            description="导入流水、分类、对账的完整流程",
            workflow_type=WorkflowType.TRANSACTION_ENTRY,
            steps=[
                WorkflowStep(
                    step_id="trans_1",
                    name="导入银行流水",
                    description="从Excel导入银行流水",
                    function_codes=["import_statement"],
                    estimated_duration=120
                ),
                WorkflowStep(
                    step_id="trans_2",
                    name="自动分类",
                    description="使用行业分类器自动分类交易",
                    function_codes=["auto_classify"],
                    estimated_duration=60
                ),
                WorkflowStep(
                    step_id="trans_3",
                    name="灵活对账",
                    description="进行一对多、多对一对账",
                    function_codes=["reconcile"],
                    estimated_duration=300
                ),
                WorkflowStep(
                    step_id="trans_4",
                    name="生成对账报告",
                    description="生成对账结果报告",
                    function_codes=["reconciliation_report"],
                    estimated_duration=60
                )
            ]
        )
        self.templates[transaction_template.template_id] = transaction_template
        
        # 4. 报表生成工作流
        report_template = WorkflowTemplate(
            template_id="oxidation_report_v1",
            name="报表生成",
            description="生成氧化加工厂行业专用报表",
            workflow_type=WorkflowType.REPORT_GENERATION,
            steps=[
                WorkflowStep(
                    step_id="report_1",
                    name="生成加工费收入明细",
                    description="按客户、计价单位统计收入",
                    function_codes=["income_report"],
                    estimated_duration=90
                ),
                WorkflowStep(
                    step_id="report_2",
                    name="生成外发成本统计",
                    description="按工序类型和供应商统计成本",
                    function_codes=["outsourced_cost_report"],
                    estimated_duration=90
                ),
                WorkflowStep(
                    step_id="report_3",
                    name="生成原材料消耗统计",
                    description="统计三酸、片碱等原材料消耗",
                    function_codes=["material_report"],
                    estimated_duration=90
                ),
                WorkflowStep(
                    step_id="report_4",
                    name="生成图表",
                    description="生成收入趋势、成本结构等图表",
                    function_codes=["generate_charts"],
                    estimated_duration=60
                )
            ]
        )
        self.templates[report_template.template_id] = report_template
        
        # 5. 日终处理工作流
        end_of_day_template = WorkflowTemplate(
            template_id="oxidation_eod_v1",
            name="日终处理",
            description="每日结束时的汇总、备份和准备工作",
            workflow_type=WorkflowType.END_OF_DAY,
            steps=[
                WorkflowStep(
                    step_id="eod_1",
                    name="核对账户余额",
                    description="核对各银行账户余额",
                    function_codes=["check_balance"],
                    estimated_duration=120
                ),
                WorkflowStep(
                    step_id="eod_2",
                    name="生成日报",
                    description="生成今日财务汇总报告",
                    function_codes=["daily_report"],
                    estimated_duration=90
                ),
                WorkflowStep(
                    step_id="eod_3",
                    name="数据备份",
                    description="备份今日所有财务数据",
                    function_codes=["backup"],
                    estimated_duration=60
                ),
                WorkflowStep(
                    step_id="eod_4",
                    name="查看明日任务",
                    description="查看明日待办事项和提醒",
                    function_codes=["tomorrow_tasks"],
                    estimated_duration=60
                )
            ]
        )
        self.templates[end_of_day_template.template_id] = end_of_day_template
        
        logger.info(f"Loaded {len(self.templates)} default workflow templates")
    
    def _load_user_customizations(self) -> None:
        """加载用户自定义配置"""
        try:
            for customization_file in self.customization_path.glob("*.json"):
                user_id = customization_file.stem
                with open(customization_file, 'r', encoding='utf-8') as f:
                    self.user_customizations[user_id] = json.load(f)
            logger.info(f"Loaded customizations for {len(self.user_customizations)} users")
        except Exception as e:
            logger.error(f"Failed to load user customizations: {e}")
    
    def _save_user_customizations(self, user_id: str) -> bool:
        """保存用户自定义配置"""
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
        应用用户自定义配置到工作流模板
        
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
        保存工作流自定义配置
        
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
        启动新的工作流会话
        
        Args:
            workflow_type: 工作流类型(字符串)
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
        
        # 应用用户自定义配置
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
        
        # 执行步骤
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
                message=f"步骤 {current_step.name} 完成",
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
        获取下一步建议
        
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
            # 为当前步骤创建建议
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
            
            # 如果当前步骤可选,提供跳过选项
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
            # 工作流已完成,建议相关的后续操作
            if session.workflow_type == WorkflowType.MORNING_SETUP:
                suggestions.append(WorkflowAction(
                    action_id="next_order",
                    name="开始处理订单",
                    description="开始今日的订单处理工作",
                    function_code="order_processing",
                    is_primary=True,
                    confidence=0.8
                ))
            elif session.workflow_type == WorkflowType.ORDER_PROCESSING:
                suggestions.append(WorkflowAction(
                    action_id="continue_order",
                    name="继续处理订单",
                    description="处理更多订单",
                    function_code="order_processing",
                    is_primary=True,
                    confidence=0.8
                ))
            elif session.workflow_type == WorkflowType.TRANSACTION_ENTRY:
                suggestions.append(WorkflowAction(
                    action_id="generate_report",
                    name="生成报表",
                    description="生成财务报表",
                    function_code="report_generation",
                    is_primary=True,
                    confidence=0.7
                ))
        
        return suggestions[:5]  # 最多返回5个建议
    
    def skip_current_step(self, session_id: str) -> StepResult:
        """
        跳过当前步骤(用于可选步骤)
        
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
            message=f"已跳过步骤 {current_step.name}",
            next_suggestions=next_suggestions
        )
        
        self.save_workflow_state(session_id)
        logger.info(f"Skipped step {current_step.step_id} in session {session_id}")
        
        return result
    
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
            Optional[WorkflowSession]: 工作流会话,如果不存在则返回None
        """
        try:
            file_path = self.storage_path / f"{session_id}.json"
            if not file_path.exists():
                return None
            
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # 重建WorkflowSession对象
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
    
    def get_workflow_templates(self) -> List[WorkflowTemplate]:
        """
        获取工作流模板列表
        
        Returns:
            List[WorkflowTemplate]: 工作流模板列表
        """
        return list(self.templates.values())
    
    def get_template_by_id(self, template_id: str) -> Optional[WorkflowTemplate]:
        """根据ID获取模板"""
        return self.templates.get(template_id)
    
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
        恢复工作流会话
        
        Args:
            session_id: 会话ID
            
        Returns:
            Optional[WorkflowSession]: 恢复的会话,如果不存在则返回None
        """
        # 如果会话已在内存中,直接返回
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
        获取用户的所有会话
        
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
