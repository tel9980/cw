# -*- coding: utf-8 -*-
"""
Context Engine
上下文引擎 - 分析用户行为、业务模式和当前状态以提供智能辅助
"""

import logging
import json
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from collections import defaultdict, Counter

from ..models.context_models import (
    ContextAnalysis,
    UserPatterns,
    TimeContext,
    SmartDefault,
    Alternative,
    Task,
    Activity,
    Priority,
    Dashboard,
    TaskPriority,
    BusinessCyclePosition
)

logger = logging.getLogger(__name__)


class ContextEngine:
    """
    上下文引擎
    
    负责：
    - 分析用户行为模式
    - 预测下一步操作
    - 生成智能默认值
    - 从用户纠正中学习
    - 生成个性化仪表板
    
    Requirements: 4.1, 4.2, 4.3, 4.5, 8.1, 8.2
    """
    
    def __init__(self, storage_path: str = "财务数据/context_data"):
        """
        初始化上下文引擎
        
        Args:
            storage_path: 上下文数据存储路径
        """
        self.storage_path = Path(storage_path)
        self.storage_path.mkdir(parents=True, exist_ok=True)
        
        self.user_patterns_cache: Dict[str, UserPatterns] = {}
        self.activity_history: Dict[str, List[Activity]] = defaultdict(list)
        
        # 历史交易数据用于智能默认值生成
        self.transaction_history: Dict[str, List[Dict[str, Any]]] = defaultdict(list)
        
        # 纠正学习数据
        self.correction_history: Dict[str, List[Dict[str, Any]]] = defaultdict(list)
        
        # 客户/供应商模式
        self.entity_patterns: Dict[str, Dict[str, Any]] = defaultdict(dict)
        
        # 加载持久化数据
        self._load_persistent_data()
        
        logger.info("ContextEngine initialized with storage at %s", self.storage_path)

    def analyze_current_context(
        self, 
        user_id: str,
        current_time: Optional[datetime] = None
    ) -> ContextAnalysis:
        """
        分析当前上下文
        
        Args:
            user_id: 用户ID
            current_time: 当前时间（可选，默认为现在）
            
        Returns:
            ContextAnalysis: 上下文分析结果
        """
        if current_time is None:
            current_time = datetime.now()
        
        # 获取或创建用户模式
        user_patterns = self._get_user_patterns(user_id)
        
        # 分析时间上下文
        time_context = TimeContext.from_datetime(current_time)
        
        # 获取待处理任务
        pending_tasks = self._get_pending_tasks(user_id, time_context)
        
        # 获取最近活动
        recent_activities = self._get_recent_activities(user_id, hours=24)
        
        # 生成优先级建议
        suggested_priorities = self._generate_priorities(
            user_patterns, 
            time_context, 
            pending_tasks
        )
        
        # 计算置信度
        confidence = self._calculate_confidence(user_patterns, recent_activities)
        
        analysis = ContextAnalysis(
            user_id=user_id,
            analysis_time=current_time,
            user_patterns=user_patterns,
            current_time_context=time_context,
            pending_tasks=pending_tasks,
            recent_activities=recent_activities,
            business_cycle_position=time_context.business_cycle,
            suggested_priorities=suggested_priorities,
            confidence_score=confidence
        )
        
        logger.info(f"Analyzed context for user {user_id}, confidence: {confidence:.2f}")
        return analysis

    def _get_user_patterns(self, user_id: str) -> UserPatterns:
        """获取用户行为模式"""
        if user_id in self.user_patterns_cache:
            return self.user_patterns_cache[user_id]
        
        # 创建新的用户模式
        patterns = UserPatterns(user_id=user_id)
        self.user_patterns_cache[user_id] = patterns
        return patterns
    
    def _get_pending_tasks(
        self, 
        user_id: str, 
        time_context: TimeContext
    ) -> List[Task]:
        """获取待处理任务"""
        tasks = []
        
        # 根据时间上下文生成任务
        if time_context.business_cycle == BusinessCyclePosition.MONTH_END:
            tasks.append(Task(
                task_id="month_end_close",
                name="月末结账",
                description="执行月末结账流程",
                priority=TaskPriority.HIGH,
                estimated_duration=120
            ))
        
        return tasks
    
    def _get_recent_activities(
        self, 
        user_id: str, 
        hours: int = 24
    ) -> List[Activity]:
        """获取最近的活动记录"""
        cutoff_time = datetime.now() - timedelta(hours=hours)
        activities = self.activity_history.get(user_id, [])
        return [a for a in activities if a.timestamp >= cutoff_time]

    def _generate_priorities(
        self,
        user_patterns: UserPatterns,
        time_context: TimeContext,
        pending_tasks: List[Task]
    ) -> List[Priority]:
        """生成优先级建议"""
        priorities = []
        
        # 基于时间上下文的优先级
        if time_context.time_type.value == "morning":
            priorities.append(Priority(
                item_id="morning_review",
                title="查看今日任务",
                description="检查今天需要完成的工作",
                priority=TaskPriority.HIGH,
                reason="早晨开始工作",
                suggested_action="查看日志和待办事项"
            ))
        
        # 基于待处理任务的优先级
        for task in pending_tasks:
            if task.priority in [TaskPriority.URGENT, TaskPriority.HIGH]:
                priorities.append(Priority(
                    item_id=task.task_id,
                    title=task.name,
                    description=task.description,
                    priority=task.priority,
                    reason="重要待办任务",
                    suggested_action=task.name
                ))
        
        return priorities
    
    def _calculate_confidence(
        self,
        user_patterns: UserPatterns,
        recent_activities: List[Activity]
    ) -> float:
        """计算分析置信度"""
        # 基于数据量计算置信度
        activity_count = len(recent_activities)
        pattern_count = len(user_patterns.function_usage_count)
        
        confidence = min(1.0, (activity_count * 0.01 + pattern_count * 0.05))
        return max(0.1, confidence)  # 最小置信度0.1

    def predict_next_action(
        self, 
        current_state: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """
        预测下一步操作
        
        基于以下因素预测：
        - 用户常用功能
        - 时间上下文
        - 工作流序列模式
        - 最近活动
        
        Args:
            current_state: 当前状态信息
            
        Returns:
            List[Dict]: 预测的操作列表，按置信度排序
        
        Requirements: 8.1
        """
        user_id = current_state.get('user_id', 'default_user')
        patterns = self._get_user_patterns(user_id)
        current_time = current_state.get('current_time', datetime.now())
        
        predictions = []
        
        # 1. 基于常用功能预测
        top_functions = patterns.get_top_functions(10)
        for i, func_code in enumerate(top_functions):
            base_confidence = 0.7 - (i * 0.05)  # 递减置信度
            
            # 调整基于时间偏好的置信度
            if func_code in patterns.preferred_time_slots:
                time_slots = patterns.preferred_time_slots[func_code]
                current_hour = current_time.hour
                
                # 如果当前时间是该功能的常用时间，提高置信度
                hour_counter = Counter(time_slots)
                if current_hour in hour_counter:
                    time_boost = min(0.2, hour_counter[current_hour] / len(time_slots))
                    base_confidence += time_boost
            
            predictions.append({
                'function_code': func_code,
                'confidence': min(0.95, base_confidence),
                'reason': '常用功能',
                'metadata': {
                    'usage_count': patterns.function_usage_count.get(func_code, 0)
                }
            })
        
        # 2. 基于工作流序列预测
        recent_activities = self._get_recent_activities(user_id, hours=1)
        if recent_activities:
            recent_sequence = [a.function_code for a in recent_activities[-5:]]
            
            # 查找匹配的工作流序列
            for workflow_seq in patterns.typical_workflow_sequences:
                # 检查最近的活动是否匹配工作流序列的开始部分
                if len(recent_sequence) < len(workflow_seq):
                    match_length = 0
                    for i, func in enumerate(recent_sequence):
                        if i < len(workflow_seq) and workflow_seq[i] == func:
                            match_length += 1
                        else:
                            break
                    
                    # 如果有匹配，预测序列中的下一个功能
                    if match_length > 0 and match_length < len(workflow_seq):
                        next_func = workflow_seq[match_length]
                        confidence = 0.8 * (match_length / len(workflow_seq))
                        
                        # 检查是否已经在预测列表中
                        existing = next((p for p in predictions if p['function_code'] == next_func), None)
                        if existing:
                            # 提高现有预测的置信度
                            existing['confidence'] = min(0.95, existing['confidence'] + confidence * 0.3)
                            existing['reason'] = '常用功能 + 工作流序列'
                        else:
                            predictions.append({
                                'function_code': next_func,
                                'confidence': confidence,
                                'reason': '工作流序列模式',
                                'metadata': {
                                    'sequence_match': recent_sequence,
                                    'expected_sequence': workflow_seq
                                }
                            })
        
        # 3. 基于时间上下文预测
        time_context = TimeContext.from_datetime(current_time)
        
        if time_context.time_type.value == "morning":
            # 早晨可能需要查看报表或处理待办事项
            predictions.append({
                'function_code': 'view_dashboard',
                'confidence': 0.75,
                'reason': '早晨开始工作',
                'metadata': {'time_context': 'morning'}
            })
        
        if time_context.business_cycle == BusinessCyclePosition.MONTH_END:
            # 月末可能需要结账相关功能
            predictions.append({
                'function_code': 'month_end_close',
                'confidence': 0.85,
                'reason': '月末结账',
                'metadata': {'business_cycle': 'month_end'}
            })
        
        # 按置信度排序
        predictions.sort(key=lambda x: x['confidence'], reverse=True)
        
        # 去重（保留置信度最高的）
        seen_functions = set()
        unique_predictions = []
        for pred in predictions:
            if pred['function_code'] not in seen_functions:
                seen_functions.add(pred['function_code'])
                unique_predictions.append(pred)
        
        logger.info(f"Generated {len(unique_predictions)} predictions for user {user_id}")
        return unique_predictions[:10]  # 返回前10个预测
    
    def generate_smart_defaults(
        self, 
        transaction_type: str, 
        context: Dict[str, Any]
    ) -> Dict[str, SmartDefault]:
        """
        生成智能默认值
        
        基于以下因素生成智能默认值：
        - 历史交易模式
        - 客户/供应商关系
        - 业务周期
        - 用户习惯
        
        Args:
            transaction_type: 交易类型
            context: 上下文信息（包含user_id, entity_id等）
            
        Returns:
            Dict[str, SmartDefault]: 字段名到智能默认值的映射
        
        Requirements: 4.1, 4.2, 4.5
        """
        defaults = {}
        user_id = context.get('user_id', 'default_user')
        
        # 日期默认值 - 基于业务规则
        current_time = datetime.now()
        defaults['date'] = SmartDefault(
            field_name='date',
            suggested_value=current_time.strftime('%Y-%m-%d'),
            confidence=1.0,
            reasoning='当前日期',
            source='business_rules'
        )
        
        # 如果提供了实体ID（客户/供应商），使用实体模式
        entity_id = context.get('entity_id')
        if entity_id and entity_id in self.entity_patterns:
            entity_pattern = self.entity_patterns[entity_id]
            
            # 类别默认值 - 基于该实体的历史交易
            if entity_pattern['typical_categories']:
                most_common_category = entity_pattern['typical_categories'].most_common(1)[0]
                category_value, category_count = most_common_category
                total_count = entity_pattern['transaction_count']
                confidence = category_count / total_count if total_count > 0 else 0.5
                
                # 生成备选项
                alternatives = []
                for cat, count in entity_pattern['typical_categories'].most_common(3)[1:]:
                    alt_confidence = count / total_count if total_count > 0 else 0.3
                    alternatives.append(Alternative(
                        value=cat,
                        confidence=alt_confidence,
                        reasoning=f'该实体的次常用类别（{count}次）'
                    ))
                
                defaults['category'] = SmartDefault(
                    field_name='category',
                    suggested_value=category_value,
                    confidence=confidence,
                    reasoning=f'该实体最常用的类别（{category_count}/{total_count}次）',
                    alternatives=alternatives,
                    source='entity_pattern'
                )
            
            # 金额默认值 - 基于历史平均值
            if entity_pattern['typical_amounts']:
                amounts = entity_pattern['typical_amounts']
                avg_amount = sum(amounts) / len(amounts)
                # 使用最近的金额作为更高置信度的建议
                recent_amount = amounts[-1] if amounts else avg_amount
                
                defaults['amount'] = SmartDefault(
                    field_name='amount',
                    suggested_value=recent_amount,
                    confidence=0.8,
                    reasoning=f'该实体最近一次交易金额',
                    alternatives=[
                        Alternative(
                            value=avg_amount,
                            confidence=0.6,
                            reasoning=f'该实体平均交易金额（基于{len(amounts)}笔交易）'
                        )
                    ],
                    source='entity_pattern'
                )
            
            # 付款条款默认值
            if entity_pattern['typical_payment_terms']:
                most_common_terms = entity_pattern['typical_payment_terms'].most_common(1)[0]
                terms_value, terms_count = most_common_terms
                total_count = entity_pattern['transaction_count']
                confidence = terms_count / total_count if total_count > 0 else 0.5
                
                defaults['payment_terms'] = SmartDefault(
                    field_name='payment_terms',
                    suggested_value=terms_value,
                    confidence=confidence,
                    reasoning=f'该实体常用的付款条款（{terms_count}/{total_count}次）',
                    source='entity_pattern'
                )
        
        # 基于交易类型和用户历史提供默认值
        user_transactions = self.transaction_history.get(user_id, [])
        type_transactions = [t for t in user_transactions if t['type'] == transaction_type]
        
        if type_transactions and 'category' not in defaults:
            # 分析该类型交易的类别分布
            category_counter = Counter()
            for trans in type_transactions:
                if 'category' in trans['data']:
                    category_counter[trans['data']['category']] += 1
            
            if category_counter:
                most_common = category_counter.most_common(1)[0]
                category_value, count = most_common
                confidence = count / len(type_transactions)
                
                alternatives = []
                for cat, cat_count in category_counter.most_common(3)[1:]:
                    alternatives.append(Alternative(
                        value=cat,
                        confidence=cat_count / len(type_transactions),
                        reasoning=f'您常用的类别（{cat_count}次）'
                    ))
                
                defaults['category'] = SmartDefault(
                    field_name='category',
                    suggested_value=category_value,
                    confidence=confidence,
                    reasoning=f'您最常用的{transaction_type}类别（{count}/{len(type_transactions)}次）',
                    alternatives=alternatives,
                    source='user_pattern'
                )
        
        # 基于业务周期提供默认值
        time_context = TimeContext.from_datetime(current_time)
        if time_context.business_cycle == BusinessCyclePosition.MONTH_END:
            # 月末可能需要特殊处理
            if 'notes' not in defaults:
                defaults['notes'] = SmartDefault(
                    field_name='notes',
                    suggested_value='月末结账',
                    confidence=0.6,
                    reasoning='当前处于月末，可能是结账相关交易',
                    source='business_cycle'
                )
        
        # 从纠正历史中学习
        corrections = self.correction_history.get(user_id, [])
        relevant_corrections = [
            c for c in corrections
            if c.get('transaction_type') == transaction_type
        ]
        
        if relevant_corrections:
            # 分析用户经常纠正的字段
            for correction in relevant_corrections[-10:]:  # 最近10次纠正
                field = correction.get('field')
                actual_value = correction.get('actual_value')
                
                if field and actual_value and field not in defaults:
                    defaults[field] = SmartDefault(
                        field_name=field,
                        suggested_value=actual_value,
                        confidence=0.7,
                        reasoning='基于您之前的纠正学习',
                        source='correction_learning'
                    )
        
        logger.info(f"Generated {len(defaults)} smart defaults for {transaction_type}")
        return defaults

    def learn_from_correction(
        self, 
        prediction: Dict[str, Any], 
        actual: Dict[str, Any]
    ) -> None:
        """
        从用户纠正中学习
        
        分析预测值和实际值的差异，更新模式以改进未来预测。
        
        Args:
            prediction: 系统预测的值
            actual: 用户实际输入的值
        
        Requirements: 4.3, 8.2
        """
        user_id = actual.get('user_id', 'default_user')
        patterns = self._get_user_patterns(user_id)
        
        # 更新功能使用计数
        if 'function_code' in actual:
            func_code = actual['function_code']
            patterns.function_usage_count[func_code] = \
                patterns.function_usage_count.get(func_code, 0) + 1
        
        # 记录纠正详情
        correction_record = {
            'timestamp': datetime.now().isoformat(),
            'transaction_type': actual.get('transaction_type'),
            'entity_id': actual.get('entity_id'),
            'corrections': []
        }
        
        # 分析每个字段的纠正
        for field, predicted_value in prediction.items():
            if field in actual and actual[field] != predicted_value:
                correction_record['corrections'].append({
                    'field': field,
                    'predicted_value': predicted_value,
                    'actual_value': actual[field],
                    'prediction_confidence': prediction.get(f'{field}_confidence', 0.5)
                })
                
                # 如果是实体相关的纠正，更新实体模式
                entity_id = actual.get('entity_id')
                if entity_id and entity_id in self.entity_patterns:
                    entity_pattern = self.entity_patterns[entity_id]
                    
                    if field == 'category':
                        # 增加实际类别的权重
                        entity_pattern['typical_categories'][actual[field]] += 2
                        # 减少预测类别的权重（如果存在）
                        if predicted_value in entity_pattern['typical_categories']:
                            entity_pattern['typical_categories'][predicted_value] = max(
                                0, entity_pattern['typical_categories'][predicted_value] - 1
                            )
                    
                    elif field == 'payment_terms':
                        # 增加实际付款条款的权重
                        entity_pattern['typical_payment_terms'][actual[field]] += 2
                        if predicted_value in entity_pattern['typical_payment_terms']:
                            entity_pattern['typical_payment_terms'][predicted_value] = max(
                                0, entity_pattern['typical_payment_terms'][predicted_value] - 1
                            )
        
        # 只记录有纠正的情况
        if correction_record['corrections']:
            self.correction_history[user_id].append(correction_record)
            
            # 保持历史记录在合理大小（最多1000条）
            if len(self.correction_history[user_id]) > 1000:
                self.correction_history[user_id] = self.correction_history[user_id][-1000:]
            
            logger.info(
                f"Learned from {len(correction_record['corrections'])} corrections for user {user_id}"
            )
            
            # 持久化
            self._save_correction_history(user_id)
            if actual.get('entity_id'):
                self._save_entity_patterns()
        
        # 记录纠正信息用于未来改进
        patterns.last_updated = datetime.now()
        self._save_user_patterns(user_id, patterns)
    
    def get_personalized_dashboard(
        self, 
        user_id: str, 
        time_context: Optional[str] = None
    ) -> Dashboard:
        """
        生成个性化仪表板
        
        Args:
            user_id: 用户ID
            time_context: 时间上下文（可选）
            
        Returns:
            Dashboard: 个性化仪表板
        """
        # 分析当前上下文
        context = self.analyze_current_context(user_id)
        
        # 获取高优先级任务
        priority_tasks = context.get_high_priority_tasks()
        
        # 生成快速操作
        quick_actions = []
        for func_code in context.user_patterns.get_top_functions(5):
            quick_actions.append({
                'function_code': func_code,
                'name': f'功能 {func_code}',
                'is_frequent': True
            })
        
        # 生成待处理项
        pending_items = [
            {
                'type': 'task',
                'title': task.name,
                'priority': task.priority.value
            }
            for task in context.pending_tasks
        ]
        
        # 生成洞察
        insights = self._generate_insights(context)
        
        dashboard = Dashboard(
            user_id=user_id,
            generated_at=datetime.now(),
            context=context,
            priority_tasks=priority_tasks,
            quick_actions=quick_actions,
            pending_items=pending_items,
            insights=insights
        )
        
        logger.info(f"Generated personalized dashboard for user {user_id}")
        return dashboard
    
    def _generate_insights(self, context: ContextAnalysis) -> List[str]:
        """生成洞察信息"""
        insights = []
        
        if context.current_time_context.business_cycle == BusinessCyclePosition.MONTH_END:
            insights.append("📅 本月即将结束，建议开始准备月末结账工作")
        
        if len(context.pending_tasks) > 5:
            insights.append(f"⚠️ 您有 {len(context.pending_tasks)} 个待处理任务")
        
        return insights
    
    def analyze_workflow_patterns(
        self,
        user_id: str,
        min_sequence_length: int = 3,
        min_occurrences: int = 2
    ) -> List[List[str]]:
        """
        分析用户的工作流序列模式
        
        识别用户经常执行的功能序列，用于预测和建议。
        
        Args:
            user_id: 用户ID
            min_sequence_length: 最小序列长度
            min_occurrences: 最小出现次数
            
        Returns:
            List[List[str]]: 识别出的工作流序列模式
        
        Requirements: 8.1
        """
        activities = self.activity_history.get(user_id, [])
        if len(activities) < min_sequence_length:
            return []
        
        # 提取功能代码序列
        function_sequence = [a.function_code for a in activities]
        
        # 查找重复的子序列
        patterns = []
        sequence_counter = Counter()
        
        # 滑动窗口查找模式
        for length in range(min_sequence_length, min(10, len(function_sequence))):
            for i in range(len(function_sequence) - length + 1):
                subsequence = tuple(function_sequence[i:i+length])
                sequence_counter[subsequence] += 1
        
        # 筛选出现次数足够的模式
        for sequence, count in sequence_counter.items():
            if count >= min_occurrences:
                patterns.append(list(sequence))
        
        # 按序列长度和出现次数排序
        patterns.sort(key=lambda x: (len(x), sequence_counter[tuple(x)]), reverse=True)
        
        # 更新用户模式
        user_patterns = self._get_user_patterns(user_id)
        user_patterns.typical_workflow_sequences = patterns[:20]  # 保留前20个模式
        self._save_user_patterns(user_id, user_patterns)
        
        logger.info(f"Identified {len(patterns)} workflow patterns for user {user_id}")
        return patterns
    
    def get_correction_insights(
        self,
        user_id: str,
        field: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        获取纠正学习的洞察
        
        分析用户的纠正历史，识别系统预测的弱点。
        
        Args:
            user_id: 用户ID
            field: 可选，特定字段的洞察
            
        Returns:
            Dict: 纠正洞察信息
        
        Requirements: 4.3, 8.2
        """
        corrections = self.correction_history.get(user_id, [])
        if not corrections:
            return {
                'total_corrections': 0,
                'field_accuracy': {},
                'improvement_areas': []
            }
        
        # 统计各字段的纠正情况
        field_corrections = Counter()
        field_total = Counter()
        
        for correction_record in corrections:
            for correction in correction_record.get('corrections', []):
                corrected_field = correction['field']
                field_corrections[corrected_field] += 1
                field_total[corrected_field] += 1
        
        # 计算准确率（假设总预测次数是纠正次数的10倍）
        field_accuracy = {}
        for f in field_total:
            estimated_total = field_total[f] * 10
            accuracy = 1.0 - (field_corrections[f] / estimated_total)
            field_accuracy[f] = max(0.0, accuracy)
        
        # 识别需要改进的领域
        improvement_areas = []
        for f, accuracy in field_accuracy.items():
            if accuracy < 0.7:
                improvement_areas.append({
                    'field': f,
                    'accuracy': accuracy,
                    'correction_count': field_corrections[f]
                })
        
        improvement_areas.sort(key=lambda x: x['accuracy'])
        
        insights = {
            'total_corrections': sum(field_corrections.values()),
            'field_accuracy': field_accuracy,
            'improvement_areas': improvement_areas,
            'most_corrected_fields': field_corrections.most_common(5)
        }
        
        if field and field in field_accuracy:
            insights['field_specific'] = {
                'field': field,
                'accuracy': field_accuracy[field],
                'correction_count': field_corrections[field]
            }
        
        return insights
    
    def get_entity_insights(
        self,
        entity_id: str
    ) -> Optional[Dict[str, Any]]:
        """
        获取实体（客户/供应商）的洞察
        
        Args:
            entity_id: 实体ID
            
        Returns:
            Dict: 实体洞察信息，如果实体不存在则返回None
        
        Requirements: 4.2
        """
        if entity_id not in self.entity_patterns:
            return None
        
        pattern = self.entity_patterns[entity_id]
        
        insights = {
            'entity_id': entity_id,
            'transaction_count': pattern['transaction_count'],
            'typical_categories': dict(pattern['typical_categories'].most_common(5)),
            'typical_payment_terms': dict(pattern['typical_payment_terms'].most_common(3)),
            'last_transaction': pattern['last_transaction']
        }
        
        # 计算平均金额和标准差
        if pattern['typical_amounts']:
            amounts = pattern['typical_amounts']
            avg_amount = sum(amounts) / len(amounts)
            variance = sum((x - avg_amount) ** 2 for x in amounts) / len(amounts)
            std_dev = variance ** 0.5
            
            insights['amount_statistics'] = {
                'average': avg_amount,
                'std_deviation': std_dev,
                'min': min(amounts),
                'max': max(amounts),
                'recent': amounts[-1] if amounts else None
            }
        
        return insights
    
    def record_activity(
        self, 
        user_id: str, 
        activity: Activity
    ) -> None:
        """
        记录用户活动
        
        Args:
            user_id: 用户ID
            activity: 活动记录
        """
        self.activity_history[user_id].append(activity)
        
        # 更新用户模式
        patterns = self._get_user_patterns(user_id)
        patterns.function_usage_count[activity.function_code] = \
            patterns.function_usage_count.get(activity.function_code, 0) + 1
        patterns.last_updated = datetime.now()
        
        # 更新时间偏好
        hour = activity.timestamp.hour
        if activity.function_code not in patterns.preferred_time_slots:
            patterns.preferred_time_slots[activity.function_code] = []
        patterns.preferred_time_slots[activity.function_code].append(hour)
        
        # 持久化
        self._save_user_patterns(user_id, patterns)
    
    def record_transaction(
        self,
        user_id: str,
        transaction_type: str,
        transaction_data: Dict[str, Any]
    ) -> None:
        """
        记录交易数据用于模式学习
        
        Args:
            user_id: 用户ID
            transaction_type: 交易类型
            transaction_data: 交易数据
        
        Requirements: 4.1, 4.2
        """
        transaction_record = {
            'type': transaction_type,
            'data': transaction_data,
            'timestamp': datetime.now().isoformat()
        }
        self.transaction_history[user_id].append(transaction_record)
        
        # 更新实体模式（客户/供应商）
        if 'entity_id' in transaction_data:
            entity_id = transaction_data['entity_id']
            if entity_id not in self.entity_patterns:
                self.entity_patterns[entity_id] = {
                    'transaction_count': 0,
                    'typical_amounts': [],
                    'typical_categories': Counter(),
                    'typical_payment_terms': Counter(),
                    'last_transaction': None
                }
            
            entity_pattern = self.entity_patterns[entity_id]
            entity_pattern['transaction_count'] += 1
            
            if 'amount' in transaction_data:
                entity_pattern['typical_amounts'].append(transaction_data['amount'])
            
            if 'category' in transaction_data:
                entity_pattern['typical_categories'][transaction_data['category']] += 1
            
            if 'payment_terms' in transaction_data:
                entity_pattern['typical_payment_terms'][transaction_data['payment_terms']] += 1
            
            entity_pattern['last_transaction'] = transaction_data
        
        # 持久化
        self._save_transaction_history(user_id)
        self._save_entity_patterns()
    
    def _load_persistent_data(self) -> None:
        """加载持久化数据"""
        # 加载用户模式
        patterns_file = self.storage_path / "user_patterns.json"
        if patterns_file.exists():
            try:
                with open(patterns_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    for user_id, pattern_data in data.items():
                        patterns = UserPatterns(
                            user_id=user_id,
                            function_usage_count=pattern_data.get('function_usage_count', {}),
                            preferred_time_slots=pattern_data.get('preferred_time_slots', {}),
                            typical_workflow_sequences=pattern_data.get('typical_workflow_sequences', []),
                            average_session_duration=pattern_data.get('average_session_duration', 0.0)
                        )
                        self.user_patterns_cache[user_id] = patterns
            except Exception as e:
                logger.error(f"Failed to load user patterns: {e}")
        
        # 加载交易历史
        transaction_file = self.storage_path / "transaction_history.json"
        if transaction_file.exists():
            try:
                with open(transaction_file, 'r', encoding='utf-8') as f:
                    self.transaction_history = defaultdict(list, json.load(f))
            except Exception as e:
                logger.error(f"Failed to load transaction history: {e}")
        
        # 加载实体模式
        entity_file = self.storage_path / "entity_patterns.json"
        if entity_file.exists():
            try:
                with open(entity_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    for entity_id, pattern_data in data.items():
                        # 转换Counter对象
                        pattern_data['typical_categories'] = Counter(
                            pattern_data.get('typical_categories', {})
                        )
                        pattern_data['typical_payment_terms'] = Counter(
                            pattern_data.get('typical_payment_terms', {})
                        )
                        self.entity_patterns[entity_id] = pattern_data
            except Exception as e:
                logger.error(f"Failed to load entity patterns: {e}")
        
        # 加载纠正历史
        correction_file = self.storage_path / "correction_history.json"
        if correction_file.exists():
            try:
                with open(correction_file, 'r', encoding='utf-8') as f:
                    self.correction_history = defaultdict(list, json.load(f))
            except Exception as e:
                logger.error(f"Failed to load correction history: {e}")
    
    def _save_user_patterns(self, user_id: str, patterns: UserPatterns) -> None:
        """保存用户模式"""
        patterns_file = self.storage_path / "user_patterns.json"
        
        # 加载现有数据
        all_patterns = {}
        if patterns_file.exists():
            try:
                with open(patterns_file, 'r', encoding='utf-8') as f:
                    all_patterns = json.load(f)
            except Exception as e:
                logger.error(f"Failed to load existing patterns: {e}")
        
        # 更新数据
        all_patterns[user_id] = {
            'function_usage_count': patterns.function_usage_count,
            'preferred_time_slots': patterns.preferred_time_slots,
            'typical_workflow_sequences': patterns.typical_workflow_sequences,
            'average_session_duration': patterns.average_session_duration
        }
        
        # 保存
        try:
            with open(patterns_file, 'w', encoding='utf-8') as f:
                json.dump(all_patterns, f, ensure_ascii=False, indent=2)
        except Exception as e:
            logger.error(f"Failed to save user patterns: {e}")
    
    def _save_transaction_history(self, user_id: str) -> None:
        """保存交易历史"""
        transaction_file = self.storage_path / "transaction_history.json"
        
        try:
            with open(transaction_file, 'w', encoding='utf-8') as f:
                json.dump(dict(self.transaction_history), f, ensure_ascii=False, indent=2)
        except Exception as e:
            logger.error(f"Failed to save transaction history: {e}")
    
    def _save_entity_patterns(self) -> None:
        """保存实体模式"""
        entity_file = self.storage_path / "entity_patterns.json"
        
        # 转换Counter对象为dict
        serializable_patterns = {}
        for entity_id, pattern in self.entity_patterns.items():
            serializable_patterns[entity_id] = {
                'transaction_count': pattern['transaction_count'],
                'typical_amounts': pattern['typical_amounts'],
                'typical_categories': dict(pattern['typical_categories']),
                'typical_payment_terms': dict(pattern['typical_payment_terms']),
                'last_transaction': pattern['last_transaction']
            }
        
        try:
            with open(entity_file, 'w', encoding='utf-8') as f:
                json.dump(serializable_patterns, f, ensure_ascii=False, indent=2)
        except Exception as e:
            logger.error(f"Failed to save entity patterns: {e}")
    
    def _save_correction_history(self, user_id: str) -> None:
        """保存纠正历史"""
        correction_file = self.storage_path / "correction_history.json"
        
        try:
            with open(correction_file, 'w', encoding='utf-8') as f:
                json.dump(dict(self.correction_history), f, ensure_ascii=False, indent=2)
        except Exception as e:
            logger.error(f"Failed to save correction history: {e}")
