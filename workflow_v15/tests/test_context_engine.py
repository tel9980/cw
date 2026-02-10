# -*- coding: utf-8 -*-
"""
Context Engine Tests
上下文引擎的单元测试
"""

import pytest
from datetime import datetime, timedelta
from pathlib import Path

from workflow_v15.core.context_engine import ContextEngine
from workflow_v15.models.context_models import (
    Activity,
    TimeContext,
    BusinessCyclePosition,
    TaskPriority
)


class TestContextEngineBasics:
    """测试上下文引擎基础功能"""
    
    def test_engine_initialization(self, temp_storage_path):
        """测试引擎初始化"""
        engine = ContextEngine(storage_path=temp_storage_path)
        assert engine is not None
        assert engine.storage_path.exists()
        assert isinstance(engine.user_patterns_cache, dict)
        assert isinstance(engine.activity_history, dict)
        assert isinstance(engine.transaction_history, dict)
        assert isinstance(engine.entity_patterns, dict)
    
    def test_analyze_current_context(self, temp_storage_path, sample_user_id):
        """测试分析当前上下文"""
        engine = ContextEngine(storage_path=temp_storage_path)
        
        analysis = engine.analyze_current_context(sample_user_id)
        
        assert analysis is not None
        assert analysis.user_id == sample_user_id
        assert analysis.user_patterns is not None
        assert analysis.current_time_context is not None
        assert isinstance(analysis.pending_tasks, list)
        assert isinstance(analysis.recent_activities, list)
        assert 0.0 <= analysis.confidence_score <= 1.0


class TestActivityRecording:
    """测试活动记录功能（Requirement 8.1）"""
    
    def test_record_activity(self, temp_storage_path, sample_user_id):
        """测试记录用户活动"""
        engine = ContextEngine(storage_path=temp_storage_path)
        
        activity = Activity(
            activity_id="act_001",
            user_id=sample_user_id,
            action_type="function_call",
            function_code="F001",
            timestamp=datetime.now(),
            duration=5.0,
            success=True
        )
        
        engine.record_activity(sample_user_id, activity)
        
        # 验证活动已记录
        assert sample_user_id in engine.activity_history
        assert len(engine.activity_history[sample_user_id]) == 1
        assert engine.activity_history[sample_user_id][0] == activity
        
        # 验证用户模式已更新
        patterns = engine._get_user_patterns(sample_user_id)
        assert patterns.function_usage_count["F001"] == 1
    
    def test_record_multiple_activities(self, temp_storage_path, sample_user_id):
        """测试记录多个活动"""
        engine = ContextEngine(storage_path=temp_storage_path)
        
        for i in range(5):
            activity = Activity(
                activity_id=f"act_{i:03d}",
                user_id=sample_user_id,
                action_type="function_call",
                function_code=f"F{i % 3:03d}",
                timestamp=datetime.now() - timedelta(hours=i),
                duration=5.0,
                success=True
            )
            engine.record_activity(sample_user_id, activity)
        
        assert len(engine.activity_history[sample_user_id]) == 5
        
        # 验证功能使用计数
        patterns = engine._get_user_patterns(sample_user_id)
        assert patterns.function_usage_count["F000"] == 2
        assert patterns.function_usage_count["F001"] == 2
        assert patterns.function_usage_count["F002"] == 1
    
    def test_activity_time_preference_tracking(self, temp_storage_path, sample_user_id):
        """测试活动时间偏好跟踪"""
        engine = ContextEngine(storage_path=temp_storage_path)
        
        # 在不同时间记录同一功能
        for hour in [9, 10, 9, 14, 9]:
            activity = Activity(
                activity_id=f"act_{hour}",
                user_id=sample_user_id,
                action_type="function_call",
                function_code="F001",
                timestamp=datetime.now().replace(hour=hour),
                duration=5.0,
                success=True
            )
            engine.record_activity(sample_user_id, activity)
        
        patterns = engine._get_user_patterns(sample_user_id)
        assert "F001" in patterns.preferred_time_slots
        assert 9 in patterns.preferred_time_slots["F001"]
        assert patterns.preferred_time_slots["F001"].count(9) == 3


class TestTransactionRecording:
    """测试交易记录功能（Requirements 4.1, 4.2）"""
    
    def test_record_transaction(self, temp_storage_path, sample_user_id):
        """测试记录交易"""
        engine = ContextEngine(storage_path=temp_storage_path)
        
        transaction_data = {
            'entity_id': 'customer_001',
            'amount': 1000.0,
            'category': '销售收入',
            'payment_terms': '30天'
        }
        
        engine.record_transaction(sample_user_id, 'income', transaction_data)
        
        # 验证交易已记录
        assert sample_user_id in engine.transaction_history
        assert len(engine.transaction_history[sample_user_id]) == 1
        
        # 验证实体模式已创建
        assert 'customer_001' in engine.entity_patterns
        entity_pattern = engine.entity_patterns['customer_001']
        assert entity_pattern['transaction_count'] == 1
        assert entity_pattern['typical_categories']['销售收入'] == 1
        assert entity_pattern['typical_payment_terms']['30天'] == 1
    
    def test_entity_pattern_accumulation(self, temp_storage_path, sample_user_id):
        """测试实体模式累积"""
        engine = ContextEngine(storage_path=temp_storage_path)
        
        # 记录多笔交易
        for i in range(5):
            transaction_data = {
                'entity_id': 'customer_001',
                'amount': 1000.0 + i * 100,
                'category': '销售收入' if i < 3 else '服务收入',
                'payment_terms': '30天'
            }
            engine.record_transaction(sample_user_id, 'income', transaction_data)
        
        entity_pattern = engine.entity_patterns['customer_001']
        assert entity_pattern['transaction_count'] == 5
        assert entity_pattern['typical_categories']['销售收入'] == 3
        assert entity_pattern['typical_categories']['服务收入'] == 2
        assert len(entity_pattern['typical_amounts']) == 5
    
    def test_multiple_entities(self, temp_storage_path, sample_user_id):
        """测试多个实体的模式跟踪"""
        engine = ContextEngine(storage_path=temp_storage_path)
        
        # 为不同实体记录交易
        for entity_id in ['customer_001', 'customer_002', 'vendor_001']:
            transaction_data = {
                'entity_id': entity_id,
                'amount': 1000.0,
                'category': '销售收入',
                'payment_terms': '30天'
            }
            engine.record_transaction(sample_user_id, 'income', transaction_data)
        
        assert len(engine.entity_patterns) == 3
        assert all(entity_id in engine.entity_patterns 
                  for entity_id in ['customer_001', 'customer_002', 'vendor_001'])


class TestSmartDefaults:
    """测试智能默认值生成（Requirements 4.1, 4.2, 4.5）"""
    
    def test_generate_basic_defaults(self, temp_storage_path):
        """测试生成基本默认值"""
        engine = ContextEngine(storage_path=temp_storage_path)
        
        defaults = engine.generate_smart_defaults(
            'income',
            {'user_id': 'test_user'}
        )
        
        assert 'date' in defaults
        assert defaults['date'].confidence == 1.0
        assert defaults['date'].source == 'business_rules'
    
    def test_entity_based_defaults(self, temp_storage_path, sample_user_id):
        """测试基于实体的默认值"""
        engine = ContextEngine(storage_path=temp_storage_path)
        
        # 先记录一些交易建立模式
        for i in range(5):
            transaction_data = {
                'entity_id': 'customer_001',
                'amount': 1000.0,
                'category': '销售收入',
                'payment_terms': '30天'
            }
            engine.record_transaction(sample_user_id, 'income', transaction_data)
        
        # 生成默认值
        defaults = engine.generate_smart_defaults(
            'income',
            {'user_id': sample_user_id, 'entity_id': 'customer_001'}
        )
        
        assert 'category' in defaults
        assert defaults['category'].suggested_value == '销售收入'
        assert defaults['category'].source == 'entity_pattern'
        assert defaults['category'].confidence > 0.5
        
        assert 'amount' in defaults
        assert defaults['amount'].suggested_value == 1000.0
        
        assert 'payment_terms' in defaults
        assert defaults['payment_terms'].suggested_value == '30天'
    
    def test_user_pattern_based_defaults(self, temp_storage_path, sample_user_id):
        """测试基于用户模式的默认值"""
        engine = ContextEngine(storage_path=temp_storage_path)
        
        # 记录用户的交易模式
        for i in range(10):
            transaction_data = {
                'category': '销售收入' if i < 7 else '服务收入',
                'amount': 1000.0
            }
            engine.record_transaction(sample_user_id, 'income', transaction_data)
        
        # 生成默认值（不指定实体）
        defaults = engine.generate_smart_defaults(
            'income',
            {'user_id': sample_user_id}
        )
        
        assert 'category' in defaults
        assert defaults['category'].suggested_value == '销售收入'
        assert defaults['category'].source == 'user_pattern'
        assert len(defaults['category'].alternatives) > 0
    
    def test_business_cycle_defaults(self, temp_storage_path, sample_user_id):
        """测试基于业务周期的默认值"""
        engine = ContextEngine(storage_path=temp_storage_path)
        
        # 模拟月末时间
        month_end_time = datetime.now().replace(day=28)
        
        defaults = engine.generate_smart_defaults(
            'expense',
            {
                'user_id': sample_user_id,
                'current_time': month_end_time
            }
        )
        
        # 月末可能有特殊的默认值
        if 'notes' in defaults:
            assert defaults['notes'].source == 'business_cycle'


class TestLearningFromCorrections:
    """测试从纠正中学习（Requirements 4.3, 8.2）"""
    
    def test_learn_from_simple_correction(self, temp_storage_path, sample_user_id):
        """测试从简单纠正中学习"""
        engine = ContextEngine(storage_path=temp_storage_path)
        
        prediction = {
            'category': '销售收入',
            'amount': 1000.0
        }
        
        actual = {
            'user_id': sample_user_id,
            'category': '服务收入',
            'amount': 1000.0,
            'transaction_type': 'income'
        }
        
        engine.learn_from_correction(prediction, actual)
        
        # 验证纠正已记录
        assert sample_user_id in engine.correction_history
        assert len(engine.correction_history[sample_user_id]) == 1
        
        correction_record = engine.correction_history[sample_user_id][0]
        assert len(correction_record['corrections']) == 1
        assert correction_record['corrections'][0]['field'] == 'category'
        assert correction_record['corrections'][0]['predicted_value'] == '销售收入'
        assert correction_record['corrections'][0]['actual_value'] == '服务收入'
    
    def test_learn_from_entity_correction(self, temp_storage_path, sample_user_id):
        """测试从实体相关纠正中学习"""
        engine = ContextEngine(storage_path=temp_storage_path)
        
        # 先建立实体模式
        transaction_data = {
            'entity_id': 'customer_001',
            'category': '销售收入',
            'payment_terms': '30天'
        }
        engine.record_transaction(sample_user_id, 'income', transaction_data)
        
        # 进行纠正
        prediction = {
            'category': '销售收入',
            'payment_terms': '30天'
        }
        
        actual = {
            'user_id': sample_user_id,
            'entity_id': 'customer_001',
            'category': '服务收入',
            'payment_terms': '60天',
            'transaction_type': 'income'
        }
        
        engine.learn_from_correction(prediction, actual)
        
        # 验证实体模式已更新
        entity_pattern = engine.entity_patterns['customer_001']
        assert entity_pattern['typical_categories']['服务收入'] == 2  # 增加权重
        assert entity_pattern['typical_payment_terms']['60天'] == 2
    
    def test_no_correction_when_values_match(self, temp_storage_path, sample_user_id):
        """测试值匹配时不记录纠正"""
        engine = ContextEngine(storage_path=temp_storage_path)
        
        prediction = {
            'category': '销售收入',
            'amount': 1000.0
        }
        
        actual = {
            'user_id': sample_user_id,
            'category': '销售收入',
            'amount': 1000.0,
            'transaction_type': 'income'
        }
        
        engine.learn_from_correction(prediction, actual)
        
        # 没有纠正应该不记录
        assert len(engine.correction_history[sample_user_id]) == 0
    
    def test_correction_history_limit(self, temp_storage_path, sample_user_id):
        """测试纠正历史记录限制"""
        engine = ContextEngine(storage_path=temp_storage_path)
        
        # 记录大量纠正
        for i in range(1100):
            prediction = {'category': '销售收入'}
            actual = {
                'user_id': sample_user_id,
                'category': f'类别{i}',
                'transaction_type': 'income'
            }
            engine.learn_from_correction(prediction, actual)
        
        # 验证历史记录被限制在1000条
        assert len(engine.correction_history[sample_user_id]) == 1000


class TestPredictNextAction:
    """测试预测下一步操作（Requirement 8.1）"""
    
    def test_predict_based_on_frequent_functions(self, temp_storage_path, sample_user_id):
        """测试基于常用功能的预测"""
        engine = ContextEngine(storage_path=temp_storage_path)
        
        # 记录一些活动
        for i in range(10):
            activity = Activity(
                activity_id=f"act_{i}",
                user_id=sample_user_id,
                action_type="function_call",
                function_code="F001" if i < 7 else "F002",
                timestamp=datetime.now(),
                duration=5.0,
                success=True
            )
            engine.record_activity(sample_user_id, activity)
        
        predictions = engine.predict_next_action({
            'user_id': sample_user_id
        })
        
        assert len(predictions) > 0
        # F001应该是最高置信度的预测
        assert predictions[0]['function_code'] == 'F001'
        assert predictions[0]['confidence'] > 0.5
    
    def test_predict_based_on_time_preference(self, temp_storage_path, sample_user_id):
        """测试基于时间偏好的预测"""
        engine = ContextEngine(storage_path=temp_storage_path)
        
        # 在特定时间记录活动
        morning_time = datetime.now().replace(hour=9)
        for i in range(5):
            activity = Activity(
                activity_id=f"act_{i}",
                user_id=sample_user_id,
                action_type="function_call",
                function_code="F001",
                timestamp=morning_time,
                duration=5.0,
                success=True
            )
            engine.record_activity(sample_user_id, activity)
        
        # 在早晨时间预测
        predictions = engine.predict_next_action({
            'user_id': sample_user_id,
            'current_time': morning_time
        })
        
        # F001应该有较高置信度（因为时间匹配）
        f001_pred = next((p for p in predictions if p['function_code'] == 'F001'), None)
        assert f001_pred is not None
        assert f001_pred['confidence'] > 0.6
    
    def test_predict_based_on_workflow_sequence(self, temp_storage_path, sample_user_id):
        """测试基于工作流序列的预测"""
        engine = ContextEngine(storage_path=temp_storage_path)
        
        # 记录一个重复的工作流序列
        sequence = ['F001', 'F002', 'F003']
        for _ in range(3):
            for func_code in sequence:
                activity = Activity(
                    activity_id=f"act_{func_code}",
                    user_id=sample_user_id,
                    action_type="function_call",
                    function_code=func_code,
                    timestamp=datetime.now(),
                    duration=5.0,
                    success=True
                )
                engine.record_activity(sample_user_id, activity)
        
        # 分析模式
        engine.analyze_workflow_patterns(sample_user_id)
        
        # 执行序列的前两步
        for func_code in ['F001', 'F002']:
            activity = Activity(
                activity_id=f"act_new_{func_code}",
                user_id=sample_user_id,
                action_type="function_call",
                function_code=func_code,
                timestamp=datetime.now(),
                duration=5.0,
                success=True
            )
            engine.record_activity(sample_user_id, activity)
        
        # 预测下一步
        predictions = engine.predict_next_action({
            'user_id': sample_user_id
        })
        
        # F003应该被预测（因为序列模式）
        f003_pred = next((p for p in predictions if p['function_code'] == 'F003'), None)
        assert f003_pred is not None
    
    def test_predict_with_time_context(self, temp_storage_path, sample_user_id):
        """测试基于时间上下文的预测"""
        engine = ContextEngine(storage_path=temp_storage_path)
        
        # 早晨时间
        morning_time = datetime.now().replace(hour=9)
        predictions = engine.predict_next_action({
            'user_id': sample_user_id,
            'current_time': morning_time
        })
        
        # 应该包含早晨相关的预测
        dashboard_pred = next(
            (p for p in predictions if 'dashboard' in p['function_code'].lower()),
            None
        )
        assert dashboard_pred is not None


class TestWorkflowPatternAnalysis:
    """测试工作流模式分析（Requirement 8.1）"""
    
    def test_analyze_simple_pattern(self, temp_storage_path, sample_user_id):
        """测试分析简单模式"""
        engine = ContextEngine(storage_path=temp_storage_path)
        
        # 记录重复的序列
        sequence = ['F001', 'F002', 'F003']
        for _ in range(3):
            for func_code in sequence:
                activity = Activity(
                    activity_id=f"act_{func_code}_{_}",
                    user_id=sample_user_id,
                    action_type="function_call",
                    function_code=func_code,
                    timestamp=datetime.now(),
                    duration=5.0,
                    success=True
                )
                engine.record_activity(sample_user_id, activity)
        
        patterns = engine.analyze_workflow_patterns(sample_user_id)
        
        assert len(patterns) > 0
        # 应该识别出完整序列
        assert sequence in patterns
    
    def test_analyze_multiple_patterns(self, temp_storage_path, sample_user_id):
        """测试分析多个模式"""
        engine = ContextEngine(storage_path=temp_storage_path)
        
        # 记录两个不同的序列
        sequence1 = ['F001', 'F002', 'F003']
        sequence2 = ['F004', 'F005']
        
        for _ in range(3):
            for func_code in sequence1:
                activity = Activity(
                    activity_id=f"act1_{func_code}_{_}",
                    user_id=sample_user_id,
                    action_type="function_call",
                    function_code=func_code,
                    timestamp=datetime.now(),
                    duration=5.0,
                    success=True
                )
                engine.record_activity(sample_user_id, activity)
            
            for func_code in sequence2:
                activity = Activity(
                    activity_id=f"act2_{func_code}_{_}",
                    user_id=sample_user_id,
                    action_type="function_call",
                    function_code=func_code,
                    timestamp=datetime.now(),
                    duration=5.0,
                    success=True
                )
                engine.record_activity(sample_user_id, activity)
        
        patterns = engine.analyze_workflow_patterns(sample_user_id)
        
        assert len(patterns) >= 2
    
    def test_pattern_persistence(self, temp_storage_path, sample_user_id):
        """测试模式持久化"""
        engine = ContextEngine(storage_path=temp_storage_path)
        
        # 记录序列
        sequence = ['F001', 'F002', 'F003']
        for _ in range(3):
            for func_code in sequence:
                activity = Activity(
                    activity_id=f"act_{func_code}_{_}",
                    user_id=sample_user_id,
                    action_type="function_call",
                    function_code=func_code,
                    timestamp=datetime.now(),
                    duration=5.0,
                    success=True
                )
                engine.record_activity(sample_user_id, activity)
        
        patterns = engine.analyze_workflow_patterns(sample_user_id)
        
        # 验证模式已保存到用户模式中
        user_patterns = engine._get_user_patterns(sample_user_id)
        assert len(user_patterns.typical_workflow_sequences) > 0
        assert sequence in user_patterns.typical_workflow_sequences


class TestCorrectionInsights:
    """测试纠正洞察（Requirements 4.3, 8.2）"""
    
    def test_get_correction_insights_empty(self, temp_storage_path, sample_user_id):
        """测试空纠正历史的洞察"""
        engine = ContextEngine(storage_path=temp_storage_path)
        
        insights = engine.get_correction_insights(sample_user_id)
        
        assert insights['total_corrections'] == 0
        assert len(insights['field_accuracy']) == 0
        assert len(insights['improvement_areas']) == 0
    
    def test_get_correction_insights_with_data(self, temp_storage_path, sample_user_id):
        """测试有数据的纠正洞察"""
        engine = ContextEngine(storage_path=temp_storage_path)
        
        # 记录一些纠正
        for i in range(10):
            prediction = {
                'category': '销售收入',
                'amount': 1000.0
            }
            actual = {
                'user_id': sample_user_id,
                'category': '服务收入',
                'amount': 1000.0 if i < 8 else 2000.0,
                'transaction_type': 'income'
            }
            engine.learn_from_correction(prediction, actual)
        
        insights = engine.get_correction_insights(sample_user_id)
        
        assert insights['total_corrections'] > 0
        assert 'category' in insights['field_accuracy']
        assert 'amount' in insights['field_accuracy']
        
        # category被纠正了10次，amount被纠正了2次
        # category的准确率应该更低（因为被纠正的次数更多）
        assert insights['field_accuracy']['category'] <= insights['field_accuracy']['amount']
        
        # 验证纠正次数统计
        most_corrected = dict(insights['most_corrected_fields'])
        assert most_corrected['category'] == 10
        assert most_corrected['amount'] == 2
    
    def test_get_field_specific_insights(self, temp_storage_path, sample_user_id):
        """测试特定字段的洞察"""
        engine = ContextEngine(storage_path=temp_storage_path)
        
        # 记录纠正
        for i in range(5):
            prediction = {'category': '销售收入'}
            actual = {
                'user_id': sample_user_id,
                'category': '服务收入',
                'transaction_type': 'income'
            }
            engine.learn_from_correction(prediction, actual)
        
        insights = engine.get_correction_insights(sample_user_id, field='category')
        
        assert 'field_specific' in insights
        assert insights['field_specific']['field'] == 'category'
        assert insights['field_specific']['correction_count'] == 5


class TestEntityInsights:
    """测试实体洞察（Requirement 4.2）"""
    
    def test_get_entity_insights_nonexistent(self, temp_storage_path):
        """测试不存在的实体"""
        engine = ContextEngine(storage_path=temp_storage_path)
        
        insights = engine.get_entity_insights('nonexistent_entity')
        
        assert insights is None
    
    def test_get_entity_insights_with_data(self, temp_storage_path, sample_user_id):
        """测试有数据的实体洞察"""
        engine = ContextEngine(storage_path=temp_storage_path)
        
        # 记录交易
        for i in range(5):
            transaction_data = {
                'entity_id': 'customer_001',
                'amount': 1000.0 + i * 100,
                'category': '销售收入',
                'payment_terms': '30天'
            }
            engine.record_transaction(sample_user_id, 'income', transaction_data)
        
        insights = engine.get_entity_insights('customer_001')
        
        assert insights is not None
        assert insights['entity_id'] == 'customer_001'
        assert insights['transaction_count'] == 5
        assert '销售收入' in insights['typical_categories']
        assert '30天' in insights['typical_payment_terms']
        assert 'amount_statistics' in insights
        assert insights['amount_statistics']['average'] == 1200.0
        assert insights['amount_statistics']['min'] == 1000.0
        assert insights['amount_statistics']['max'] == 1400.0


class TestPersonalizedDashboard:
    """测试个性化仪表板"""
    
    def test_get_personalized_dashboard(self, temp_storage_path, sample_user_id):
        """测试生成个性化仪表板"""
        engine = ContextEngine(storage_path=temp_storage_path)
        
        dashboard = engine.get_personalized_dashboard(sample_user_id)
        
        assert dashboard is not None
        assert dashboard.user_id == sample_user_id
        assert dashboard.context is not None
        assert isinstance(dashboard.priority_tasks, list)
        assert isinstance(dashboard.quick_actions, list)
        assert isinstance(dashboard.pending_items, list)
        assert isinstance(dashboard.insights, list)
    
    def test_dashboard_with_activities(self, temp_storage_path, sample_user_id):
        """测试有活动历史的仪表板"""
        engine = ContextEngine(storage_path=temp_storage_path)
        
        # 记录一些活动
        for i in range(5):
            activity = Activity(
                activity_id=f"act_{i}",
                user_id=sample_user_id,
                action_type="function_call",
                function_code=f"F{i % 3:03d}",
                timestamp=datetime.now(),
                duration=5.0,
                success=True
            )
            engine.record_activity(sample_user_id, activity)
        
        dashboard = engine.get_personalized_dashboard(sample_user_id)
        
        # 应该有快速操作建议
        assert len(dashboard.quick_actions) > 0


class TestDataPersistence:
    """测试数据持久化"""
    
    def test_user_patterns_persistence(self, temp_storage_path, sample_user_id):
        """测试用户模式持久化"""
        engine = ContextEngine(storage_path=temp_storage_path)
        
        # 记录活动
        activity = Activity(
            activity_id="act_001",
            user_id=sample_user_id,
            action_type="function_call",
            function_code="F001",
            timestamp=datetime.now(),
            duration=5.0,
            success=True
        )
        engine.record_activity(sample_user_id, activity)
        
        # 创建新引擎实例
        engine2 = ContextEngine(storage_path=temp_storage_path)
        
        # 验证数据已加载
        patterns = engine2._get_user_patterns(sample_user_id)
        assert patterns.function_usage_count.get("F001", 0) == 1
    
    def test_transaction_history_persistence(self, temp_storage_path, sample_user_id):
        """测试交易历史持久化"""
        engine = ContextEngine(storage_path=temp_storage_path)
        
        transaction_data = {
            'entity_id': 'customer_001',
            'amount': 1000.0,
            'category': '销售收入'
        }
        engine.record_transaction(sample_user_id, 'income', transaction_data)
        
        # 创建新引擎实例
        engine2 = ContextEngine(storage_path=temp_storage_path)
        
        # 验证数据已加载
        assert sample_user_id in engine2.transaction_history
        assert len(engine2.transaction_history[sample_user_id]) == 1
    
    def test_entity_patterns_persistence(self, temp_storage_path, sample_user_id):
        """测试实体模式持久化"""
        engine = ContextEngine(storage_path=temp_storage_path)
        
        transaction_data = {
            'entity_id': 'customer_001',
            'amount': 1000.0,
            'category': '销售收入'
        }
        engine.record_transaction(sample_user_id, 'income', transaction_data)
        
        # 创建新引擎实例
        engine2 = ContextEngine(storage_path=temp_storage_path)
        
        # 验证数据已加载
        assert 'customer_001' in engine2.entity_patterns
        assert engine2.entity_patterns['customer_001']['transaction_count'] == 1


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
