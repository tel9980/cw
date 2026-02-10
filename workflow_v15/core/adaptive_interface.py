"""
Adaptive Interface Learning System

This module provides adaptive interface capabilities that learn from user behavior
and optimize the interface layout, notification timing, and provide personalized
insights and recommendations.

Requirements:
- 8.1: Track user interaction patterns and optimize interface layout
- 8.4: Adapt notification timing and content based on user response patterns
- 8.5: Provide personalized insights and recommendations

Author: V1.5 Development Team
Date: 2026-02-10
"""

from dataclasses import dataclass, field, asdict
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Set, Tuple
from collections import defaultdict, Counter
from enum import Enum
import json
import os


class InteractionType(Enum):
    """Types of user interactions"""
    CLICK = "click"
    VIEW = "view"
    EDIT = "edit"
    DELETE = "delete"
    SEARCH = "search"
    NAVIGATE = "navigate"


class NotificationPriority(Enum):
    """Notification priority levels"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    URGENT = "urgent"


@dataclass
class UserInteraction:
    """Record of a user interaction"""
    interaction_id: str
    user_id: str
    interaction_type: InteractionType
    feature_id: str
    feature_name: str
    timestamp: datetime
    duration_seconds: float = 0.0
    context: dict = field(default_factory=dict)
    
    def to_dict(self) -> dict:
        """Convert to dictionary"""
        data = asdict(self)
        data['interaction_type'] = self.interaction_type.value
        data['timestamp'] = self.timestamp.isoformat()
        return data
    
    @classmethod
    def from_dict(cls, data: dict) -> 'UserInteraction':
        """Create from dictionary"""
        data = data.copy()
        data['interaction_type'] = InteractionType(data['interaction_type'])
        data['timestamp'] = datetime.fromisoformat(data['timestamp'])
        return cls(**data)


@dataclass
class InterfaceLayout:
    """Optimized interface layout"""
    layout_id: str
    user_id: str
    primary_features: List[str]  # Top features to show
    secondary_features: List[str]  # Secondary features
    hidden_features: List[str]  # Hidden features
    feature_positions: Dict[str, int]  # Feature ID -> position
    created_at: datetime
    confidence_score: float = 0.0


@dataclass
class NotificationSchedule:
    """Adaptive notification schedule"""
    user_id: str
    notification_type: str
    preferred_times: List[int]  # Hours of day (0-23)
    avoid_times: List[int]  # Hours to avoid
    max_per_day: int = 5
    priority_threshold: NotificationPriority = NotificationPriority.MEDIUM


@dataclass
class PersonalizedInsight:
    """Personalized insight or recommendation"""
    insight_id: str
    user_id: str
    insight_type: str  # efficiency, pattern, suggestion, warning
    title: str
    description: str
    action_items: List[str]
    priority: NotificationPriority
    created_at: datetime
    expires_at: Optional[datetime] = None
    is_read: bool = False


class AdaptiveInterfaceManager:
    """
    Manages adaptive interface learning and optimization.
    
    This manager provides:
    - User interaction pattern tracking
    - Interface layout optimization based on usage
    - Adaptive notification timing and content
    - Personalized insights and recommendations
    """
    
    def __init__(self, storage_path: str = "财务数据/adaptive_interface"):
        """
        Initialize adaptive interface manager.
        
        Args:
            storage_path: Path to storage directory
        """
        self.storage_path = storage_path
        self.interactions: List[UserInteraction] = []
        self.layouts: Dict[str, InterfaceLayout] = {}
        self.notification_schedules: Dict[str, NotificationSchedule] = {}
        self.insights: Dict[str, PersonalizedInsight] = {}
        
        # Analytics caches
        self.feature_usage: Dict[str, Dict[str, int]] = defaultdict(lambda: defaultdict(int))
        self.time_patterns: Dict[str, Dict[int, int]] = defaultdict(lambda: defaultdict(int))
        self.notification_responses: Dict[str, Dict[str, int]] = defaultdict(lambda: defaultdict(int))
        
        # Create storage directory
        os.makedirs(storage_path, exist_ok=True)
        
        # Load data
        self._load_data()
    
    def track_interaction(
        self,
        user_id: str,
        interaction_type: InteractionType,
        feature_id: str,
        feature_name: str,
        duration_seconds: float = 0.0,
        context: Optional[dict] = None
    ) -> UserInteraction:
        """
        Track a user interaction.
        
        Args:
            user_id: User ID
            interaction_type: Type of interaction
            feature_id: Feature ID
            feature_name: Feature name
            duration_seconds: Duration of interaction
            context: Additional context
            
        Returns:
            Created interaction record
        """
        interaction_id = f"int_{datetime.now().strftime('%Y%m%d%H%M%S%f')}"
        
        interaction = UserInteraction(
            interaction_id=interaction_id,
            user_id=user_id,
            interaction_type=interaction_type,
            feature_id=feature_id,
            feature_name=feature_name,
            timestamp=datetime.now(),
            duration_seconds=duration_seconds,
            context=context or {}
        )
        
        self.interactions.append(interaction)
        
        # Update analytics caches
        self.feature_usage[user_id][feature_id] += 1
        hour = interaction.timestamp.hour
        self.time_patterns[user_id][hour] += 1
        
        # Save periodically (every 10 interactions)
        if len(self.interactions) % 10 == 0:
            self._save_data()
        
        return interaction
    
    def get_feature_usage_stats(
        self,
        user_id: str,
        top_n: int = 10
    ) -> List[Tuple[str, int]]:
        """
        Get feature usage statistics.
        
        Args:
            user_id: User ID
            top_n: Number of top features to return
            
        Returns:
            List of (feature_id, usage_count) tuples
        """
        usage = self.feature_usage.get(user_id, {})
        return sorted(usage.items(), key=lambda x: x[1], reverse=True)[:top_n]
    
    def optimize_interface_layout(
        self,
        user_id: str,
        available_features: List[str],
        primary_count: int = 5,
        secondary_count: int = 10
    ) -> InterfaceLayout:
        """
        Optimize interface layout based on usage patterns.
        
        Args:
            user_id: User ID
            available_features: List of available feature IDs
            primary_count: Number of primary features to show
            secondary_count: Number of secondary features
            
        Returns:
            Optimized interface layout
        """
        # Get feature usage statistics
        usage_stats = dict(self.get_feature_usage_stats(user_id, len(available_features)))
        
        # Sort features by usage
        sorted_features = sorted(
            available_features,
            key=lambda f: usage_stats.get(f, 0),
            reverse=True
        )
        
        # Divide into primary, secondary, and hidden
        primary_features = sorted_features[:primary_count]
        secondary_features = sorted_features[primary_count:primary_count + secondary_count]
        hidden_features = sorted_features[primary_count + secondary_count:]
        
        # Create position mapping
        feature_positions = {
            feature: idx for idx, feature in enumerate(sorted_features)
        }
        
        # Calculate confidence score based on data volume
        total_interactions = sum(usage_stats.values())
        confidence_score = min(1.0, total_interactions / 100.0)  # 100 interactions = full confidence
        
        layout_id = f"layout_{user_id}_{datetime.now().strftime('%Y%m%d%H%M%S')}"
        
        layout = InterfaceLayout(
            layout_id=layout_id,
            user_id=user_id,
            primary_features=primary_features,
            secondary_features=secondary_features,
            hidden_features=hidden_features,
            feature_positions=feature_positions,
            created_at=datetime.now(),
            confidence_score=confidence_score
        )
        
        self.layouts[layout_id] = layout
        self._save_data()
        
        return layout
    
    def get_current_layout(self, user_id: str) -> Optional[InterfaceLayout]:
        """Get current layout for user"""
        user_layouts = [
            layout for layout in self.layouts.values()
            if layout.user_id == user_id
        ]
        
        if not user_layouts:
            return None
        
        # Return most recent layout
        return max(user_layouts, key=lambda l: l.created_at)
    
    def analyze_time_patterns(self, user_id: str) -> Dict[str, List[int]]:
        """
        Analyze user's time-based activity patterns.
        
        Args:
            user_id: User ID
            
        Returns:
            Dictionary with peak_hours, low_hours, and preferred_hours
        """
        time_data = self.time_patterns.get(user_id, {})
        
        if not time_data:
            # Default patterns (9-5 workday)
            return {
                'peak_hours': [9, 10, 14, 15],
                'low_hours': [0, 1, 2, 3, 4, 5, 6, 22, 23],
                'preferred_hours': [9, 10, 11, 14, 15, 16]
            }
        
        # Calculate average activity
        total_activity = sum(time_data.values())
        avg_activity = total_activity / len(time_data) if time_data else 0
        
        # Identify peak hours (above average)
        peak_hours = [hour for hour, count in time_data.items() if count > avg_activity * 1.5]
        
        # Identify low hours (below average)
        low_hours = [hour for hour, count in time_data.items() if count < avg_activity * 0.5]
        
        # Preferred hours (above average but not necessarily peak)
        preferred_hours = [hour for hour, count in time_data.items() if count >= avg_activity]
        
        return {
            'peak_hours': sorted(peak_hours),
            'low_hours': sorted(low_hours),
            'preferred_hours': sorted(preferred_hours)
        }
    
    def create_notification_schedule(
        self,
        user_id: str,
        notification_type: str,
        max_per_day: int = 5,
        priority_threshold: NotificationPriority = NotificationPriority.MEDIUM
    ) -> NotificationSchedule:
        """
        Create adaptive notification schedule.
        
        Args:
            user_id: User ID
            notification_type: Type of notification
            max_per_day: Maximum notifications per day
            priority_threshold: Minimum priority to send
            
        Returns:
            Notification schedule
        """
        time_patterns = self.analyze_time_patterns(user_id)
        
        schedule = NotificationSchedule(
            user_id=user_id,
            notification_type=notification_type,
            preferred_times=time_patterns['preferred_hours'],
            avoid_times=time_patterns['low_hours'],
            max_per_day=max_per_day,
            priority_threshold=priority_threshold
        )
        
        schedule_key = f"{user_id}_{notification_type}"
        self.notification_schedules[schedule_key] = schedule
        self._save_data()
        
        return schedule
    
    def should_send_notification(
        self,
        user_id: str,
        notification_type: str,
        priority: NotificationPriority,
        current_time: Optional[datetime] = None
    ) -> bool:
        """
        Determine if notification should be sent now.
        
        Args:
            user_id: User ID
            notification_type: Type of notification
            priority: Notification priority
            current_time: Current time (defaults to now)
            
        Returns:
            True if notification should be sent
        """
        current_time = current_time or datetime.now()
        current_hour = current_time.hour
        
        schedule_key = f"{user_id}_{notification_type}"
        schedule = self.notification_schedules.get(schedule_key)
        
        if not schedule:
            # Create default schedule
            schedule = self.create_notification_schedule(user_id, notification_type)
        
        # Check priority threshold
        priority_values = {
            NotificationPriority.LOW: 1,
            NotificationPriority.MEDIUM: 2,
            NotificationPriority.HIGH: 3,
            NotificationPriority.URGENT: 4
        }
        
        if priority_values[priority] < priority_values[schedule.priority_threshold]:
            return False
        
        # Urgent notifications always go through
        if priority == NotificationPriority.URGENT:
            return True
        
        # Check if current hour is in avoid times
        if current_hour in schedule.avoid_times:
            return False
        
        # Prefer sending during preferred times
        if current_hour in schedule.preferred_times:
            return True
        
        # Allow during non-avoid times for high priority
        if priority == NotificationPriority.HIGH:
            return True
        
        return False
    
    def track_notification_response(
        self,
        user_id: str,
        notification_type: str,
        response: str  # opened, dismissed, ignored
    ) -> None:
        """
        Track user response to notification.
        
        Args:
            user_id: User ID
            notification_type: Type of notification
            response: User response
        """
        key = f"{user_id}_{notification_type}"
        self.notification_responses[key][response] += 1
        self._save_data()
    
    def generate_personalized_insights(
        self,
        user_id: str
    ) -> List[PersonalizedInsight]:
        """
        Generate personalized insights and recommendations.
        
        Args:
            user_id: User ID
            
        Returns:
            List of personalized insights
        """
        insights = []
        
        # Insight 1: Feature usage efficiency
        usage_stats = self.get_feature_usage_stats(user_id, 5)
        if usage_stats:
            top_feature = usage_stats[0]
            insight = PersonalizedInsight(
                insight_id=f"insight_{datetime.now().strftime('%Y%m%d%H%M%S%f')}",
                user_id=user_id,
                insight_type="efficiency",
                title="最常用功能",
                description=f"您最常使用的功能是 {top_feature[0]}，使用了 {top_feature[1]} 次",
                action_items=["考虑为此功能创建快捷键", "查看相关的高级功能"],
                priority=NotificationPriority.LOW,
                created_at=datetime.now()
            )
            insights.append(insight)
        
        # Insight 2: Time pattern analysis
        time_patterns = self.analyze_time_patterns(user_id)
        if time_patterns['peak_hours']:
            peak_hours_str = ', '.join([f"{h}:00" for h in time_patterns['peak_hours'][:3]])
            insight = PersonalizedInsight(
                insight_id=f"insight_{datetime.now().strftime('%Y%m%d%H%M%S%f')}",
                user_id=user_id,
                insight_type="pattern",
                title="工作时间模式",
                description=f"您通常在 {peak_hours_str} 最活跃",
                action_items=["在高峰时段安排重要任务", "设置提醒以优化工作流程"],
                priority=NotificationPriority.LOW,
                created_at=datetime.now()
            )
            insights.append(insight)
        
        # Insight 3: Unused features
        all_features = set(self.feature_usage.get(user_id, {}).keys())
        if len(all_features) < 10:  # User hasn't explored many features
            insight = PersonalizedInsight(
                insight_id=f"insight_{datetime.now().strftime('%Y%m%d%H%M%S%f')}",
                user_id=user_id,
                insight_type="suggestion",
                title="探索更多功能",
                description="系统还有许多功能可以帮助您提高效率",
                action_items=["查看功能导览", "尝试智能自动化功能"],
                priority=NotificationPriority.MEDIUM,
                created_at=datetime.now(),
                expires_at=datetime.now() + timedelta(days=7)
            )
            insights.append(insight)
        
        # Store insights
        for insight in insights:
            self.insights[insight.insight_id] = insight
        
        self._save_data()
        
        return insights
    
    def get_unread_insights(self, user_id: str) -> List[PersonalizedInsight]:
        """Get unread insights for user"""
        now = datetime.now()
        return [
            insight for insight in self.insights.values()
            if insight.user_id == user_id
            and not insight.is_read
            and (insight.expires_at is None or insight.expires_at > now)
        ]
    
    def mark_insight_read(self, insight_id: str) -> bool:
        """Mark insight as read"""
        insight = self.insights.get(insight_id)
        if insight:
            insight.is_read = True
            self._save_data()
            return True
        return False
    
    def get_interaction_history(
        self,
        user_id: str,
        days: int = 7
    ) -> List[UserInteraction]:
        """
        Get interaction history for user.
        
        Args:
            user_id: User ID
            days: Number of days to look back
            
        Returns:
            List of interactions
        """
        cutoff = datetime.now() - timedelta(days=days)
        return [
            interaction for interaction in self.interactions
            if interaction.user_id == user_id and interaction.timestamp >= cutoff
        ]
    
    def _load_data(self) -> None:
        """Load data from storage"""
        # Load interactions
        interactions_file = os.path.join(self.storage_path, "interactions.json")
        if os.path.exists(interactions_file):
            try:
                with open(interactions_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self.interactions = [
                        UserInteraction.from_dict(item) for item in data
                    ]
                    
                    # Rebuild analytics caches
                    for interaction in self.interactions:
                        self.feature_usage[interaction.user_id][interaction.feature_id] += 1
                        self.time_patterns[interaction.user_id][interaction.timestamp.hour] += 1
            except Exception:
                pass
        
        # Load other data (layouts, schedules, insights)
        # Simplified for now - can be expanded as needed
    
    def _save_data(self) -> None:
        """Save data to storage"""
        # Save interactions (keep last 1000)
        interactions_file = os.path.join(self.storage_path, "interactions.json")
        recent_interactions = self.interactions[-1000:] if len(self.interactions) > 1000 else self.interactions
        
        with open(interactions_file, 'w', encoding='utf-8') as f:
            data = [interaction.to_dict() for interaction in recent_interactions]
            json.dump(data, f, ensure_ascii=False, indent=2)
