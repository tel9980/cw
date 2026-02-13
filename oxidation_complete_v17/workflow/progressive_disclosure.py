# -*- coding: utf-8 -*-
"""
Progressive Disclosure Manager
渐进式披露管理器 - 控制信息呈现以最小化认知负荷
"""

import logging
import json
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional, Any, Set
from collections import Counter, defaultdict
from enum import Enum

logger = logging.getLogger(__name__)


class UserLevel(Enum):
    """用户级别枚举"""
    BEGINNER = "beginner"
    INTERMEDIATE = "intermediate"
    ADVANCED = "advanced"


class FeatureComplexity(Enum):
    """功能复杂度枚举"""
    BASIC = "basic"
    INTERMEDIATE = "intermediate"
    ADVANCED = "advanced"
    EXPERT = "expert"


class HelpTriggerType(Enum):
    """帮助触发类型"""
    HOVER = "hover"
    FIRST_USE = "first_use"
    ERROR = "error"
    INACTIVITY = "inactivity"
    MANUAL = "manual"


class Action:
    """动作/选项类"""
    def __init__(
        self,
        action_id: str,
        name: str,
        description: str,
        function_code: str,
        complexity: FeatureComplexity = FeatureComplexity.BASIC,
        is_primary: bool = True,
        usage_count: int = 0,
        last_used: Optional[datetime] = None,
        metadata: Optional[Dict[str, Any]] = None
    ):
        self.action_id = action_id
        self.name = name
        self.description = description
        self.function_code = function_code
        self.complexity = complexity
        self.is_primary = is_primary
        self.usage_count = usage_count
        self.last_used = last_used
        self.metadata = metadata or {}
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            'action_id': self.action_id,
            'name': self.name,
            'description': self.description,
            'function_code': self.function_code,
            'complexity': self.complexity.value,
            'is_primary': self.is_primary,
            'usage_count': self.usage_count,
            'last_used': self.last_used.isoformat() if self.last_used else None,
            'metadata': self.metadata
        }


class HelpContent:
    """帮助内容类"""
    def __init__(
        self,
        help_id: str,
        title: str,
        content: str,
        trigger_type: HelpTriggerType,
        context: Optional[str] = None,
        related_actions: Optional[List[str]] = None
    ):
        self.help_id = help_id
        self.title = title
        self.content = content
        self.trigger_type = trigger_type
        self.context = context
        self.related_actions = related_actions or []
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            'help_id': self.help_id,
            'title': self.title,
            'content': self.content,
            'trigger_type': self.trigger_type.value,
            'context': self.context,
            'related_actions': self.related_actions
        }



class MenuConfiguration:
    """菜单配置类"""
    def __init__(
        self,
        context: str,
        primary_actions: List[Action],
        secondary_actions: List[Action],
        hidden_actions: List[Action],
        user_level: UserLevel
    ):
        self.context = context
        self.primary_actions = primary_actions
        self.secondary_actions = secondary_actions
        self.hidden_actions = hidden_actions
        self.user_level = user_level
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            'context': self.context,
            'primary_actions': [a.to_dict() for a in self.primary_actions],
            'secondary_actions': [a.to_dict() for a in self.secondary_actions],
            'hidden_actions': [a.to_dict() for a in self.hidden_actions],
            'user_level': self.user_level.value
        }



class ProgressiveDisclosureManager:
    """
    渐进式披露管理器
    
    负责：
    - 限制主要操作数量（最多5个）
    - 隐藏和显示高级功能
    - 提供上下文帮助
    - 基于使用模式自适应菜单优先级
    - 跟踪用户级别
    
    Requirements: 2.1, 2.2, 2.4, 2.5, 3.5
    """
    
    def __init__(self, storage_path: str = "财务数据/progressive_disclosure"):
        """
        初始化渐进式披露管理器
        
        Args:
            storage_path: 数据存储路径
        """
        self.storage_path = Path(storage_path)
        self.storage_path.mkdir(parents=True, exist_ok=True)
        
        # 用户级别跟踪
        self.user_levels: Dict[str, UserLevel] = {}
        
        # 用户使用模式
        self.usage_patterns: Dict[str, Dict[str, int]] = defaultdict(lambda: defaultdict(int))
        
        # 功能使用历史（用于自适应优先级）
        self.feature_usage_history: Dict[str, List[Dict[str, Any]]] = defaultdict(list)
        
        # 帮助内容库
        self.help_contents: Dict[str, HelpContent] = {}
        
        # 功能复杂度映射
        self.feature_complexity: Dict[str, FeatureComplexity] = {}
        
        # 上下文帮助触发器
        self.help_triggers: Dict[str, Set[HelpTriggerType]] = defaultdict(set)
        
        # 用户首次使用跟踪
        self.first_use_tracking: Dict[str, Set[str]] = defaultdict(set)
        
        # 加载持久化数据
        self._load_persistent_data()
        
        # 初始化默认功能复杂度和帮助内容
        self._initialize_defaults()
        
        logger.info("ProgressiveDisclosureManager initialized with storage at %s", self.storage_path)

    
    def _initialize_defaults(self) -> None:
        """初始化默认功能复杂度和帮助内容"""
        # 定义功能复杂度（基于V1.4的62个功能）
        basic_functions = ['1', '2', '15', '16', '31', '53', '57']  # 基础功能
        intermediate_functions = ['3', '4', '17', '18', '32', '33']  # 中级功能
        advanced_functions = ['5', '6', '7', '8', '19', '20', '34', '35']  # 高级功能
        
        for func in basic_functions:
            self.feature_complexity[func] = FeatureComplexity.BASIC
        
        for func in intermediate_functions:
            self.feature_complexity[func] = FeatureComplexity.INTERMEDIATE
        
        for func in advanced_functions:
            self.feature_complexity[func] = FeatureComplexity.ADVANCED
        
        # 初始化帮助内容
        self._initialize_help_contents()
    
    def _initialize_help_contents(self) -> None:
        """初始化帮助内容库"""
        # 基础功能帮助
        self.help_contents['income_entry'] = HelpContent(
            help_id='income_entry',
            title='收入记录',
            content='记录企业的收入交易，包括销售收入、服务收入等。',
            trigger_type=HelpTriggerType.HOVER,
            context='transaction_entry',
            related_actions=['1']
        )
        
        self.help_contents['expense_entry'] = HelpContent(
            help_id='expense_entry',
            title='支出记录',
            content='记录企业的支出交易，包括采购成本、运营费用等。',
            trigger_type=HelpTriggerType.HOVER,
            context='transaction_entry',
            related_actions=['2']
        )
        
        self.help_contents['bank_statement'] = HelpContent(
            help_id='bank_statement',
            title='银行流水',
            content='查看和管理银行账户流水，进行对账操作。',
            trigger_type=HelpTriggerType.HOVER,
            context='reconciliation',
            related_actions=['15', '16']
        )
        
        # 首次使用帮助
        self.help_contents['first_time_user'] = HelpContent(
            help_id='first_time_user',
            title='欢迎使用',
            content='这是您第一次使用此功能。建议先查看相关说明或从简单操作开始。',
            trigger_type=HelpTriggerType.FIRST_USE,
            context='general'
        )

    
    def get_primary_actions(
        self,
        context: str,
        user_id: str = "default_user",
        available_actions: Optional[List[Action]] = None,
        max_items: int = 5
    ) -> List[Action]:
        """
        获取主要操作列表（最多5个）
        
        基于以下因素选择主要操作：
        - 用户使用频率
        - 功能复杂度（优先显示适合用户级别的功能）
        - 上下文相关性
        - 最近使用时间
        
        Args:
            context: 当前上下文
            user_id: 用户ID
            available_actions: 可用操作列表（如果为None，使用所有操作）
            max_items: 最大主要操作数量（默认5）
        
        Returns:
            List[Action]: 主要操作列表
        
        Requirements: 2.1
        """
        if available_actions is None:
            available_actions = self._get_all_actions(context)
        
        user_level = self.get_user_level(user_id)
        usage_pattern = self.usage_patterns[user_id]
        
        # 为每个操作计算优先级分数
        scored_actions = []
        for action in available_actions:
            score = self._calculate_action_priority(
                action, user_level, usage_pattern, context
            )
            scored_actions.append((score, action))
        
        # 按分数排序
        scored_actions.sort(key=lambda x: x[0], reverse=True)
        
        # 返回前max_items个操作
        primary_actions = [action for _, action in scored_actions[:max_items]]
        
        logger.debug(
            f"Selected {len(primary_actions)} primary actions for context '{context}' "
            f"and user '{user_id}'"
        )
        
        return primary_actions

    
    def get_secondary_actions(
        self,
        context: str,
        user_id: str = "default_user",
        available_actions: Optional[List[Action]] = None
    ) -> List[Action]:
        """
        获取次要操作列表（按需显示）
        
        Args:
            context: 当前上下文
            user_id: 用户ID
            available_actions: 可用操作列表
        
        Returns:
            List[Action]: 次要操作列表
        
        Requirements: 2.2
        """
        if available_actions is None:
            available_actions = self._get_all_actions(context)
        
        # 获取主要操作
        primary_actions = self.get_primary_actions(context, user_id, available_actions)
        primary_action_ids = {a.action_id for a in primary_actions}
        
        # 次要操作是不在主要操作中的其他操作
        secondary_actions = [
            action for action in available_actions
            if action.action_id not in primary_action_ids
        ]
        
        # 按使用频率排序
        usage_pattern = self.usage_patterns[user_id]
        secondary_actions.sort(
            key=lambda a: usage_pattern.get(a.function_code, 0),
            reverse=True
        )
        
        logger.debug(
            f"Selected {len(secondary_actions)} secondary actions for context '{context}'"
        )
        
        return secondary_actions

    
    def should_show_advanced_feature(
        self,
        feature: str,
        user_level: UserLevel,
        user_id: Optional[str] = None
    ) -> bool:
        """
        判断是否应该显示高级功能
        
        基于用户级别和功能复杂度决定是否显示。
        
        Args:
            feature: 功能代码
            user_level: 用户级别
            user_id: 用户ID（可选，用于检查使用历史）
        
        Returns:
            bool: 是否应该显示该功能
        
        Requirements: 2.2
        """
        feature_complexity = self.feature_complexity.get(
            feature, FeatureComplexity.BASIC
        )
        
        # 基础功能对所有用户可见
        if feature_complexity == FeatureComplexity.BASIC:
            return True
        
        # 中级功能对中级和高级用户可见
        if feature_complexity == FeatureComplexity.INTERMEDIATE:
            return user_level in [UserLevel.INTERMEDIATE, UserLevel.ADVANCED]
        
        # 高级功能只对高级用户可见
        if feature_complexity == FeatureComplexity.ADVANCED:
            return user_level == UserLevel.ADVANCED
        
        # 专家功能需要明确请求或有使用历史
        if feature_complexity == FeatureComplexity.EXPERT:
            if user_id and user_id in self.usage_patterns:
                # 如果用户曾经使用过，则显示
                return self.usage_patterns[user_id].get(feature, 0) > 0
            return False
        
        return False

    
    def adapt_menu_priority(
        self,
        user_patterns: Dict[str, Any],
        user_id: str = "default_user"
    ) -> MenuConfiguration:
        """
        基于用户模式自适应调整菜单优先级
        
        分析用户的使用模式，动态调整菜单中功能的优先级。
        
        Args:
            user_patterns: 用户行为模式
            user_id: 用户ID
        
        Returns:
            MenuConfiguration: 调整后的菜单配置
        
        Requirements: 2.5, 3.5
        """
        # 更新使用模式
        if 'function_usage_count' in user_patterns:
            for func_code, count in user_patterns['function_usage_count'].items():
                self.usage_patterns[user_id][func_code] = count
        
        # 获取用户级别
        user_level = self.get_user_level(user_id)
        
        # 获取上下文（从用户模式中推断）
        context = user_patterns.get('current_context', 'general')
        
        # 获取所有可用操作
        all_actions = self._get_all_actions(context)
        
        # 过滤掉用户级别不应看到的高级功能
        visible_actions = [
            action for action in all_actions
            if self.should_show_advanced_feature(
                action.function_code, user_level, user_id
            )
        ]
        
        # 获取主要操作
        primary_actions = self.get_primary_actions(
            context, user_id, visible_actions
        )
        
        # 获取次要操作
        secondary_actions = self.get_secondary_actions(
            context, user_id, visible_actions
        )
        
        # 隐藏的操作（高级功能）
        primary_ids = {a.action_id for a in primary_actions}
        secondary_ids = {a.action_id for a in secondary_actions}
        hidden_actions = [
            action for action in all_actions
            if action.action_id not in primary_ids
            and action.action_id not in secondary_ids
        ]
        
        menu_config = MenuConfiguration(
            context=context,
            primary_actions=primary_actions,
            secondary_actions=secondary_actions,
            hidden_actions=hidden_actions,
            user_level=user_level
        )
        
        logger.info(
            f"Adapted menu for user {user_id}: "
            f"{len(primary_actions)} primary, "
            f"{len(secondary_actions)} secondary, "
            f"{len(hidden_actions)} hidden"
        )
        
        return menu_config

    
    def provide_contextual_help(
        self,
        current_action: str,
        user_id: str = "default_user",
        trigger_type: HelpTriggerType = HelpTriggerType.HOVER
    ) -> Optional[HelpContent]:
        """
        提供上下文帮助
        
        基于当前操作和触发类型自动提供帮助内容。
        
        Args:
            current_action: 当前操作/功能代码
            user_id: 用户ID
            trigger_type: 帮助触发类型
        
        Returns:
            Optional[HelpContent]: 帮助内容，如果没有则返回None
        
        Requirements: 2.4
        """
        # 检查是否是首次使用
        if trigger_type == HelpTriggerType.FIRST_USE:
            if current_action not in self.first_use_tracking[user_id]:
                self.first_use_tracking[user_id].add(current_action)
                self._save_first_use_tracking()
                
                # 返回首次使用帮助
                return self.help_contents.get('first_time_user')
        
        # 查找与当前操作相关的帮助内容
        for help_content in self.help_contents.values():
            if current_action in help_content.related_actions:
                if trigger_type in [help_content.trigger_type, HelpTriggerType.MANUAL]:
                    logger.debug(
                        f"Providing help '{help_content.help_id}' for action '{current_action}'"
                    )
                    return help_content
        
        # 如果没有找到特定帮助，返回通用帮助
        if trigger_type == HelpTriggerType.ERROR:
            return HelpContent(
                help_id='generic_error',
                title='操作失败',
                content='操作未能成功完成。请检查输入数据是否正确，或联系支持。',
                trigger_type=HelpTriggerType.ERROR,
                context='general'
            )
        
        return None

    
    def get_user_level(self, user_id: str, force_recalculate: bool = False) -> UserLevel:
        """
        获取用户级别
        
        基于用户的使用历史自动判断用户级别。
        
        Args:
            user_id: 用户ID
            force_recalculate: 是否强制重新计算（忽略缓存）
        
        Returns:
            UserLevel: 用户级别
        """
        if not force_recalculate and user_id in self.user_levels:
            return self.user_levels[user_id]
        
        # 基于使用模式自动判断用户级别
        usage_pattern = self.usage_patterns[user_id]
        
        if not usage_pattern:
            # 新用户默认为初学者
            self.user_levels[user_id] = UserLevel.BEGINNER
            return UserLevel.BEGINNER
        
        # 计算总使用次数和不同功能数量
        total_usage = sum(usage_pattern.values())
        unique_functions = len(usage_pattern)
        
        # 判断标准：
        # - 初学者：总使用次数 < 50 且 不同功能 < 5
        # - 中级：总使用次数 50-200 或 不同功能 5-15
        # - 高级：总使用次数 > 200 或 不同功能 > 15
        
        if total_usage < 50 and unique_functions < 5:
            level = UserLevel.BEGINNER
        elif total_usage > 200 or unique_functions > 15:
            level = UserLevel.ADVANCED
        else:
            level = UserLevel.INTERMEDIATE
        
        self.user_levels[user_id] = level
        self._save_user_levels()
        
        logger.info(
            f"Determined user level for {user_id}: {level.value} "
            f"(usage: {total_usage}, functions: {unique_functions})"
        )
        
        return level
    
    def set_user_level(self, user_id: str, level: UserLevel) -> None:
        """
        手动设置用户级别
        
        Args:
            user_id: 用户ID
            level: 用户级别
        """
        self.user_levels[user_id] = level
        self._save_user_levels()
        logger.info(f"Set user level for {user_id} to {level.value}")

    
    def record_feature_usage(
        self,
        user_id: str,
        feature_code: str,
        context: Optional[str] = None
    ) -> None:
        """
        记录功能使用情况
        
        用于跟踪用户行为和自适应调整。
        
        Args:
            user_id: 用户ID
            feature_code: 功能代码
            context: 上下文（可选）
        """
        # 更新使用计数
        self.usage_patterns[user_id][feature_code] += 1
        
        # 记录使用历史
        usage_record = {
            'feature_code': feature_code,
            'timestamp': datetime.now().isoformat(),
            'context': context
        }
        self.feature_usage_history[user_id].append(usage_record)
        
        # 保持历史记录在合理大小（最多1000条）
        if len(self.feature_usage_history[user_id]) > 1000:
            self.feature_usage_history[user_id] = self.feature_usage_history[user_id][-1000:]
        
        # 重新评估用户级别（强制重新计算）
        self.get_user_level(user_id, force_recalculate=True)
        
        # 持久化
        self._save_usage_patterns()
        
        logger.debug(f"Recorded usage of feature {feature_code} for user {user_id}")
    
    def get_usage_statistics(
        self,
        user_id: str,
        top_n: int = 10
    ) -> Dict[str, Any]:
        """
        获取用户使用统计
        
        Args:
            user_id: 用户ID
            top_n: 返回前N个最常用功能
        
        Returns:
            Dict: 使用统计信息
        """
        usage_pattern = self.usage_patterns[user_id]
        
        # 获取最常用功能
        top_features = Counter(usage_pattern).most_common(top_n)
        
        # 计算总使用次数
        total_usage = sum(usage_pattern.values())
        
        # 获取用户级别
        user_level = self.get_user_level(user_id)
        
        statistics = {
            'user_id': user_id,
            'user_level': user_level.value,
            'total_usage': total_usage,
            'unique_features': len(usage_pattern),
            'top_features': [
                {'feature_code': code, 'count': count, 'percentage': count / total_usage * 100}
                for code, count in top_features
            ],
            'usage_history_count': len(self.feature_usage_history[user_id])
        }
        
        return statistics

    
    def _calculate_action_priority(
        self,
        action: Action,
        user_level: UserLevel,
        usage_pattern: Dict[str, int],
        context: str
    ) -> float:
        """
        计算操作的优先级分数
        
        Args:
            action: 操作
            user_level: 用户级别
            usage_pattern: 使用模式
            context: 上下文
        
        Returns:
            float: 优先级分数（越高越优先）
        """
        score = 0.0
        
        # 1. 基于使用频率（权重：40%）
        usage_count = usage_pattern.get(action.function_code, 0)
        if usage_count > 0:
            # 使用对数缩放避免极端值
            import math
            score += math.log(usage_count + 1) * 4.0
        
        # 2. 基于功能复杂度和用户级别匹配（权重：30%）
        feature_complexity = self.feature_complexity.get(
            action.function_code, FeatureComplexity.BASIC
        )
        
        if user_level == UserLevel.BEGINNER:
            if feature_complexity == FeatureComplexity.BASIC:
                score += 3.0
            elif feature_complexity == FeatureComplexity.INTERMEDIATE:
                score += 1.0
            # ADVANCED gets 0 bonus for beginners
        elif user_level == UserLevel.INTERMEDIATE:
            if feature_complexity == FeatureComplexity.INTERMEDIATE:
                score += 3.0
            elif feature_complexity == FeatureComplexity.BASIC:
                score += 2.0
            elif feature_complexity == FeatureComplexity.ADVANCED:
                score += 1.0
        else:  # ADVANCED
            if feature_complexity == FeatureComplexity.ADVANCED:
                score += 3.0
            elif feature_complexity == FeatureComplexity.INTERMEDIATE:
                score += 2.0
            else:
                score += 1.0
        
        # 3. 基于是否标记为主要操作（权重：20%）
        if action.is_primary:
            score += 2.0
        
        # 4. 基于最近使用时间（权重：10%）
        if action.last_used:
            days_since_use = (datetime.now() - action.last_used).days
            if days_since_use < 7:
                score += 1.0 * (7 - days_since_use) / 7
        
        return score
    
    def _get_all_actions(self, context: str) -> List[Action]:
        """
        获取指定上下文的所有可用操作
        
        Args:
            context: 上下文
        
        Returns:
            List[Action]: 操作列表
        """
        # 这里返回一些示例操作
        # 实际应用中应该从配置或数据库加载
        actions = []
        
        if context in ['general', 'transaction_entry']:
            actions.extend([
                Action('income_entry', '收入记录', '记录收入交易', '1',
                       FeatureComplexity.BASIC, True),
                Action('expense_entry', '支出记录', '记录支出交易', '2',
                       FeatureComplexity.BASIC, True),
                Action('customer_mgmt', '客户管理', '管理客户信息', '3',
                       FeatureComplexity.INTERMEDIATE, False),
                Action('vendor_mgmt', '供应商管理', '管理供应商信息', '4',
                       FeatureComplexity.INTERMEDIATE, False),
            ])
        
        if context in ['general', 'reconciliation']:
            actions.extend([
                Action('bank_statement', '银行流水', '查看银行流水', '15',
                       FeatureComplexity.BASIC, True),
                Action('reconciliation', '对账', '进行银行对账', '16',
                       FeatureComplexity.INTERMEDIATE, True),
            ])
        
        if context in ['general', 'reporting']:
            actions.extend([
                Action('daily_report', '日结报告', '生成日结报告', '31',
                       FeatureComplexity.BASIC, True),
                Action('monthly_report', '月度报告', '生成月度报告', '32',
                       FeatureComplexity.INTERMEDIATE, False),
            ])
        
        return actions

    
    def _load_persistent_data(self) -> None:
        """加载持久化数据"""
        # 加载用户级别
        user_levels_file = self.storage_path / "user_levels.json"
        if user_levels_file.exists():
            try:
                with open(user_levels_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self.user_levels = {
                        user_id: UserLevel(level)
                        for user_id, level in data.items()
                    }
                logger.info(f"Loaded user levels for {len(self.user_levels)} users")
            except Exception as e:
                logger.error(f"Failed to load user levels: {e}")
        
        # 加载使用模式
        usage_patterns_file = self.storage_path / "usage_patterns.json"
        if usage_patterns_file.exists():
            try:
                with open(usage_patterns_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self.usage_patterns = defaultdict(
                        lambda: defaultdict(int),
                        {k: defaultdict(int, v) for k, v in data.items()}
                    )
                logger.info(f"Loaded usage patterns for {len(self.usage_patterns)} users")
            except Exception as e:
                logger.error(f"Failed to load usage patterns: {e}")
        
        # 加载首次使用跟踪
        first_use_file = self.storage_path / "first_use_tracking.json"
        if first_use_file.exists():
            try:
                with open(first_use_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self.first_use_tracking = defaultdict(
                        set,
                        {k: set(v) for k, v in data.items()}
                    )
                logger.info(f"Loaded first use tracking for {len(self.first_use_tracking)} users")
            except Exception as e:
                logger.error(f"Failed to load first use tracking: {e}")
    
    def _save_user_levels(self) -> None:
        """保存用户级别"""
        user_levels_file = self.storage_path / "user_levels.json"
        try:
            data = {
                user_id: level.value
                for user_id, level in self.user_levels.items()
            }
            with open(user_levels_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
        except Exception as e:
            logger.error(f"Failed to save user levels: {e}")
    
    def _save_usage_patterns(self) -> None:
        """保存使用模式"""
        usage_patterns_file = self.storage_path / "usage_patterns.json"
        try:
            data = {
                user_id: dict(pattern)
                for user_id, pattern in self.usage_patterns.items()
            }
            with open(usage_patterns_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
        except Exception as e:
            logger.error(f"Failed to save usage patterns: {e}")
    
    def _save_first_use_tracking(self) -> None:
        """保存首次使用跟踪"""
        first_use_file = self.storage_path / "first_use_tracking.json"
        try:
            data = {
                user_id: list(features)
                for user_id, features in self.first_use_tracking.items()
            }
            with open(first_use_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
        except Exception as e:
            logger.error(f"Failed to save first use tracking: {e}")
