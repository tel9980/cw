# -*- coding: utf-8 -*-
"""
Progressive Disclosure Manager Tests
渐进式披露管理器的单元测试
"""

import pytest
import json
from pathlib import Path
from datetime import datetime, timedelta

from workflow_v15.core.progressive_disclosure import (
    ProgressiveDisclosureManager,
    Action,
    HelpContent,
    MenuConfiguration,
    UserLevel,
    FeatureComplexity,
    HelpTriggerType
)


@pytest.fixture
def temp_disclosure_path(tmp_path):
    """临时存储路径"""
    return str(tmp_path / "progressive_disclosure")


@pytest.fixture
def sample_user_id():
    """示例用户ID"""
    return "test_user_001"


@pytest.fixture
def manager(temp_disclosure_path):
    """创建ProgressiveDisclosureManager实例"""
    return ProgressiveDisclosureManager(storage_path=temp_disclosure_path)


@pytest.fixture
def sample_actions():
    """示例操作列表"""
    return [
        Action('action1', '收入记录', '记录收入', '1', FeatureComplexity.BASIC, True, 10),
        Action('action2', '支出记录', '记录支出', '2', FeatureComplexity.BASIC, True, 8),
        Action('action3', '客户管理', '管理客户', '3', FeatureComplexity.INTERMEDIATE, False, 5),
        Action('action4', '供应商管理', '管理供应商', '4', FeatureComplexity.INTERMEDIATE, False, 3),
        Action('action5', '高级报表', '生成高级报表', '5', FeatureComplexity.ADVANCED, False, 1),
        Action('action6', '银行流水', '查看流水', '15', FeatureComplexity.BASIC, True, 7),
        Action('action7', '对账', '银行对账', '16', FeatureComplexity.INTERMEDIATE, True, 4),
        Action('action8', '日结报告', '生成日结', '31', FeatureComplexity.BASIC, True, 6),
    ]



class TestProgressiveDisclosureManagerBasics:
    """测试渐进式披露管理器基础功能"""
    
    def test_manager_initialization(self, temp_disclosure_path):
        """测试管理器初始化"""
        manager = ProgressiveDisclosureManager(storage_path=temp_disclosure_path)
        assert manager is not None
        assert manager.storage_path.exists()
        assert len(manager.feature_complexity) > 0
        assert len(manager.help_contents) > 0
    
    def test_default_user_level_is_beginner(self, manager, sample_user_id):
        """测试新用户默认级别为初学者"""
        level = manager.get_user_level(sample_user_id)
        assert level == UserLevel.BEGINNER
    
    def test_set_user_level(self, manager, sample_user_id):
        """测试手动设置用户级别"""
        manager.set_user_level(sample_user_id, UserLevel.ADVANCED)
        level = manager.get_user_level(sample_user_id)
        assert level == UserLevel.ADVANCED


class TestPrimaryActionLimitation:
    """测试主要操作限制（Requirement 2.1）"""
    
    def test_primary_actions_max_five(self, manager, sample_user_id, sample_actions):
        """测试主要操作最多5个"""
        primary = manager.get_primary_actions(
            context='general',
            user_id=sample_user_id,
            available_actions=sample_actions,
            max_items=5
        )
        assert len(primary) <= 5
    
    def test_primary_actions_respects_max_items(self, manager, sample_user_id, sample_actions):
        """测试主要操作数量遵守max_items参数"""
        for max_items in [1, 3, 5, 7]:
            primary = manager.get_primary_actions(
                context='general',
                user_id=sample_user_id,
                available_actions=sample_actions,
                max_items=max_items
            )
            assert len(primary) <= max_items
    
    def test_primary_actions_prioritize_by_usage(self, manager, sample_user_id, sample_actions):
        """测试主要操作按使用频率优先"""
        # 记录一些使用
        manager.record_feature_usage(sample_user_id, '1')  # 收入记录
        manager.record_feature_usage(sample_user_id, '1')
        manager.record_feature_usage(sample_user_id, '1')
        manager.record_feature_usage(sample_user_id, '15')  # 银行流水
        manager.record_feature_usage(sample_user_id, '15')
        
        primary = manager.get_primary_actions(
            context='general',
            user_id=sample_user_id,
            available_actions=sample_actions,
            max_items=5
        )
        
        # 验证最常用的功能在主要操作中
        primary_codes = [a.function_code for a in primary]
        assert '1' in primary_codes
        assert '15' in primary_codes



class TestAdvancedFeatureHiding:
    """测试高级功能隐藏（Requirement 2.2）"""
    
    def test_beginner_sees_only_basic_features(self, manager):
        """测试初学者只看到基础功能"""
        user_level = UserLevel.BEGINNER
        
        assert manager.should_show_advanced_feature('1', user_level) is True  # BASIC
        assert manager.should_show_advanced_feature('3', user_level) is False  # INTERMEDIATE
        assert manager.should_show_advanced_feature('5', user_level) is False  # ADVANCED
    
    def test_intermediate_sees_basic_and_intermediate(self, manager):
        """测试中级用户看到基础和中级功能"""
        user_level = UserLevel.INTERMEDIATE
        
        assert manager.should_show_advanced_feature('1', user_level) is True  # BASIC
        assert manager.should_show_advanced_feature('3', user_level) is True  # INTERMEDIATE
        assert manager.should_show_advanced_feature('5', user_level) is False  # ADVANCED
    
    def test_advanced_sees_all_features(self, manager):
        """测试高级用户看到所有功能"""
        user_level = UserLevel.ADVANCED
        
        assert manager.should_show_advanced_feature('1', user_level) is True  # BASIC
        assert manager.should_show_advanced_feature('3', user_level) is True  # INTERMEDIATE
        assert manager.should_show_advanced_feature('5', user_level) is True  # ADVANCED
    
    def test_secondary_actions_exclude_primary(self, manager, sample_user_id, sample_actions):
        """测试次要操作不包含主要操作"""
        primary = manager.get_primary_actions(
            context='general',
            user_id=sample_user_id,
            available_actions=sample_actions
        )
        
        secondary = manager.get_secondary_actions(
            context='general',
            user_id=sample_user_id,
            available_actions=sample_actions
        )
        
        primary_ids = {a.action_id for a in primary}
        secondary_ids = {a.action_id for a in secondary}
        
        # 主要和次要操作不应有交集
        assert len(primary_ids & secondary_ids) == 0


class TestContextualHelp:
    """测试上下文帮助（Requirement 2.4）"""
    
    def test_provide_help_on_hover(self, manager, sample_user_id):
        """测试悬停时提供帮助"""
        help_content = manager.provide_contextual_help(
            current_action='1',
            user_id=sample_user_id,
            trigger_type=HelpTriggerType.HOVER
        )
        
        assert help_content is not None
        assert help_content.title is not None
        assert help_content.content is not None
    
    def test_first_use_help(self, manager, sample_user_id):
        """测试首次使用帮助"""
        # 第一次使用应该返回首次使用帮助
        help_content = manager.provide_contextual_help(
            current_action='new_feature',
            user_id=sample_user_id,
            trigger_type=HelpTriggerType.FIRST_USE
        )
        
        assert help_content is not None
        assert help_content.trigger_type == HelpTriggerType.FIRST_USE
        
        # 第二次使用不应该返回首次使用帮助
        help_content2 = manager.provide_contextual_help(
            current_action='new_feature',
            user_id=sample_user_id,
            trigger_type=HelpTriggerType.FIRST_USE
        )
        
        # 应该返回None或其他帮助
        if help_content2:
            assert help_content2.trigger_type != HelpTriggerType.FIRST_USE
    
    def test_error_help(self, manager, sample_user_id):
        """测试错误时提供帮助"""
        help_content = manager.provide_contextual_help(
            current_action='any_action',
            user_id=sample_user_id,
            trigger_type=HelpTriggerType.ERROR
        )
        
        assert help_content is not None
        assert 'error' in help_content.help_id.lower() or 'failed' in help_content.title.lower()



class TestAdaptiveMenuPrioritization:
    """测试自适应菜单优先级（Requirements 2.5, 3.5）"""
    
    def test_adapt_menu_based_on_usage(self, manager, sample_user_id):
        """测试基于使用模式调整菜单"""
        # 模拟用户使用模式
        user_patterns = {
            'function_usage_count': {
                '1': 50,  # 收入记录 - 高频
                '2': 30,  # 支出记录 - 中频
                '15': 20,  # 银行流水 - 中频
                '3': 5,   # 客户管理 - 低频
            },
            'current_context': 'general'
        }
        
        menu_config = manager.adapt_menu_priority(user_patterns, sample_user_id)
        
        assert menu_config is not None
        assert isinstance(menu_config, MenuConfiguration)
        assert len(menu_config.primary_actions) <= 5
        
        # 验证高频功能在主要操作中
        primary_codes = [a.function_code for a in menu_config.primary_actions]
        assert '1' in primary_codes  # 最常用的应该在主要操作中
    
    def test_menu_adapts_to_user_level(self, manager, sample_user_id):
        """测试菜单根据用户级别调整"""
        # 设置为初学者
        manager.set_user_level(sample_user_id, UserLevel.BEGINNER)
        
        user_patterns = {
            'function_usage_count': {'1': 10, '2': 5},
            'current_context': 'general'
        }
        
        menu_config = manager.adapt_menu_priority(user_patterns, sample_user_id)
        
        # 初学者不应该看到高级功能
        all_visible_codes = (
            [a.function_code for a in menu_config.primary_actions] +
            [a.function_code for a in menu_config.secondary_actions]
        )
        
        # 检查是否有高级功能被隐藏
        assert len(menu_config.hidden_actions) > 0
    
    def test_frequent_functions_prioritized(self, manager, sample_user_id):
        """测试常用功能被优先显示"""
        # 记录大量使用
        for _ in range(100):
            manager.record_feature_usage(sample_user_id, '1')
        for _ in range(50):
            manager.record_feature_usage(sample_user_id, '2')
        for _ in range(10):
            manager.record_feature_usage(sample_user_id, '3')
        
        user_patterns = {
            'function_usage_count': manager.usage_patterns[sample_user_id],
            'current_context': 'general'
        }
        
        menu_config = manager.adapt_menu_priority(user_patterns, sample_user_id)
        
        # 最常用的功能应该在主要操作的前面
        primary_codes = [a.function_code for a in menu_config.primary_actions]
        if '1' in primary_codes and '3' in primary_codes:
            assert primary_codes.index('1') < primary_codes.index('3')


class TestUserLevelTracking:
    """测试用户级别跟踪"""
    
    def test_user_level_progression(self, manager, sample_user_id):
        """测试用户级别随使用增长"""
        # 初始为初学者
        assert manager.get_user_level(sample_user_id) == UserLevel.BEGINNER
        
        # 模拟中等使用（50-200次，5-15个功能）
        for i in range(1, 8):
            for _ in range(15):
                manager.record_feature_usage(sample_user_id, str(i))
        
        # 应该升级到中级
        level = manager.get_user_level(sample_user_id)
        assert level == UserLevel.INTERMEDIATE
        
        # 模拟大量使用（>200次或>15个功能）
        for i in range(1, 20):
            for _ in range(15):
                manager.record_feature_usage(sample_user_id, str(i))
        
        # 应该升级到高级
        level = manager.get_user_level(sample_user_id)
        assert level == UserLevel.ADVANCED
    
    def test_usage_statistics(self, manager, sample_user_id):
        """测试使用统计"""
        # 记录一些使用
        manager.record_feature_usage(sample_user_id, '1')
        manager.record_feature_usage(sample_user_id, '1')
        manager.record_feature_usage(sample_user_id, '2')
        
        stats = manager.get_usage_statistics(sample_user_id, top_n=5)
        
        assert stats['user_id'] == sample_user_id
        assert stats['total_usage'] == 3
        assert stats['unique_features'] == 2
        assert len(stats['top_features']) > 0
        assert stats['top_features'][0]['feature_code'] == '1'
        assert stats['top_features'][0]['count'] == 2



class TestFeatureUsageRecording:
    """测试功能使用记录"""
    
    def test_record_feature_usage(self, manager, sample_user_id):
        """测试记录功能使用"""
        initial_count = manager.usage_patterns[sample_user_id].get('1', 0)
        
        manager.record_feature_usage(sample_user_id, '1', context='transaction_entry')
        
        new_count = manager.usage_patterns[sample_user_id]['1']
        assert new_count == initial_count + 1
    
    def test_usage_history_maintained(self, manager, sample_user_id):
        """测试使用历史被维护"""
        manager.record_feature_usage(sample_user_id, '1', context='test')
        
        assert len(manager.feature_usage_history[sample_user_id]) > 0
        
        last_record = manager.feature_usage_history[sample_user_id][-1]
        assert last_record['feature_code'] == '1'
        assert last_record['context'] == 'test'
        assert 'timestamp' in last_record
    
    def test_usage_history_size_limit(self, manager, sample_user_id):
        """测试使用历史大小限制"""
        # 记录超过1000次使用
        for i in range(1100):
            manager.record_feature_usage(sample_user_id, str(i % 10))
        
        # 历史记录应该被限制在1000条
        assert len(manager.feature_usage_history[sample_user_id]) <= 1000


class TestDataPersistence:
    """测试数据持久化"""
    
    def test_user_levels_persistence(self, temp_disclosure_path, sample_user_id):
        """测试用户级别持久化"""
        # 创建管理器并设置用户级别
        manager1 = ProgressiveDisclosureManager(storage_path=temp_disclosure_path)
        manager1.set_user_level(sample_user_id, UserLevel.ADVANCED)
        
        # 创建新的管理器实例（模拟重启）
        manager2 = ProgressiveDisclosureManager(storage_path=temp_disclosure_path)
        
        # 验证用户级别被保存
        level = manager2.get_user_level(sample_user_id)
        assert level == UserLevel.ADVANCED
    
    def test_usage_patterns_persistence(self, temp_disclosure_path, sample_user_id):
        """测试使用模式持久化"""
        # 创建管理器并记录使用
        manager1 = ProgressiveDisclosureManager(storage_path=temp_disclosure_path)
        manager1.record_feature_usage(sample_user_id, '1')
        manager1.record_feature_usage(sample_user_id, '1')
        manager1.record_feature_usage(sample_user_id, '2')
        
        # 创建新的管理器实例
        manager2 = ProgressiveDisclosureManager(storage_path=temp_disclosure_path)
        
        # 验证使用模式被保存
        assert manager2.usage_patterns[sample_user_id]['1'] == 2
        assert manager2.usage_patterns[sample_user_id]['2'] == 1
    
    def test_first_use_tracking_persistence(self, temp_disclosure_path, sample_user_id):
        """测试首次使用跟踪持久化"""
        # 创建管理器并触发首次使用
        manager1 = ProgressiveDisclosureManager(storage_path=temp_disclosure_path)
        manager1.provide_contextual_help(
            'feature_x',
            sample_user_id,
            HelpTriggerType.FIRST_USE
        )
        
        # 创建新的管理器实例
        manager2 = ProgressiveDisclosureManager(storage_path=temp_disclosure_path)
        
        # 验证首次使用标记被保存
        assert 'feature_x' in manager2.first_use_tracking[sample_user_id]


class TestActionPriorityCalculation:
    """测试操作优先级计算"""
    
    def test_priority_increases_with_usage(self, manager, sample_user_id):
        """测试优先级随使用增加"""
        action = Action('test', '测试', '测试操作', '99', FeatureComplexity.BASIC)
        
        # 无使用时的优先级
        score1 = manager._calculate_action_priority(
            action, UserLevel.BEGINNER, {}, 'general'
        )
        
        # 有使用时的优先级
        score2 = manager._calculate_action_priority(
            action, UserLevel.BEGINNER, {'99': 10}, 'general'
        )
        
        assert score2 > score1
    
    def test_priority_matches_user_level(self, manager):
        """测试优先级匹配用户级别"""
        basic_action = Action('basic', '基础', '基础操作', '1', FeatureComplexity.BASIC)
        advanced_action = Action('adv', '高级', '高级操作', '99', FeatureComplexity.ADVANCED)
        
        # 确保管理器知道功能99是高级功能
        manager.feature_complexity['99'] = FeatureComplexity.ADVANCED
        
        # 初学者应该优先看到基础功能
        beginner_basic_score = manager._calculate_action_priority(
            basic_action, UserLevel.BEGINNER, {}, 'general'
        )
        beginner_advanced_score = manager._calculate_action_priority(
            advanced_action, UserLevel.BEGINNER, {}, 'general'
        )
        
        assert beginner_basic_score > beginner_advanced_score
        
        # 高级用户应该优先看到高级功能
        advanced_basic_score = manager._calculate_action_priority(
            basic_action, UserLevel.ADVANCED, {}, 'general'
        )
        advanced_advanced_score = manager._calculate_action_priority(
            advanced_action, UserLevel.ADVANCED, {}, 'general'
        )
        
        assert advanced_advanced_score > advanced_basic_score


class TestEdgeCases:
    """测试边界情况"""
    
    def test_empty_actions_list(self, manager, sample_user_id):
        """测试空操作列表"""
        primary = manager.get_primary_actions(
            context='general',
            user_id=sample_user_id,
            available_actions=[],
            max_items=5
        )
        
        assert primary == []
    
    def test_fewer_actions_than_max(self, manager, sample_user_id):
        """测试操作数少于最大值"""
        actions = [
            Action('a1', 'A1', 'Action 1', '1', FeatureComplexity.BASIC),
            Action('a2', 'A2', 'Action 2', '2', FeatureComplexity.BASIC),
        ]
        
        primary = manager.get_primary_actions(
            context='general',
            user_id=sample_user_id,
            available_actions=actions,
            max_items=5
        )
        
        assert len(primary) == 2
    
    def test_unknown_feature_complexity(self, manager):
        """测试未知功能复杂度"""
        # 未定义的功能应该默认为BASIC
        result = manager.should_show_advanced_feature(
            'unknown_feature_999',
            UserLevel.BEGINNER
        )
        
        assert result is True  # 默认为BASIC，对初学者可见
