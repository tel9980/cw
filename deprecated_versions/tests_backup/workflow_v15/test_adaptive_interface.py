"""
Unit tests for Adaptive Interface Learning System

Tests cover:
- User interaction tracking
- Interface layout optimization
- Time pattern analysis
- Notification scheduling
- Personalized insights generation

Author: V1.5 Development Team
Date: 2026-02-10
"""

import unittest
import tempfile
import shutil
import os
from datetime import datetime, timedelta
from workflow_v15.core.adaptive_interface import (
    AdaptiveInterfaceManager,
    UserInteraction,
    InterfaceLayout,
    NotificationSchedule,
    PersonalizedInsight,
    InteractionType,
    NotificationPriority
)


class TestAdaptiveInterfaceInit(unittest.TestCase):
    """Test adaptive interface manager initialization"""
    
    def setUp(self):
        """Set up test environment"""
        self.temp_dir = tempfile.mkdtemp()
        self.storage_path = os.path.join(self.temp_dir, "adaptive_interface")
    
    def tearDown(self):
        """Clean up test environment"""
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_initialization(self):
        """Test manager initialization"""
        manager = AdaptiveInterfaceManager(self.storage_path)
        
        self.assertEqual(len(manager.interactions), 0)
        self.assertEqual(len(manager.layouts), 0)
        self.assertEqual(len(manager.notification_schedules), 0)
        self.assertEqual(len(manager.insights), 0)
        self.assertTrue(os.path.exists(self.storage_path))


class TestInteractionTracking(unittest.TestCase):
    """Test user interaction tracking"""
    
    def setUp(self):
        """Set up test environment"""
        self.temp_dir = tempfile.mkdtemp()
        self.storage_path = os.path.join(self.temp_dir, "adaptive_interface")
        self.manager = AdaptiveInterfaceManager(self.storage_path)
    
    def tearDown(self):
        """Clean up test environment"""
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_track_interaction(self):
        """Test tracking a single interaction"""
        interaction = self.manager.track_interaction(
            user_id="user1",
            interaction_type=InteractionType.CLICK,
            feature_id="feature_income",
            feature_name="收入录入",
            duration_seconds=5.0
        )
        
        self.assertIsNotNone(interaction)
        self.assertEqual(interaction.user_id, "user1")
        self.assertEqual(interaction.interaction_type, InteractionType.CLICK)
        self.assertEqual(interaction.feature_id, "feature_income")
        self.assertEqual(len(self.manager.interactions), 1)
    
    def test_track_multiple_interactions(self):
        """Test tracking multiple interactions"""
        for i in range(5):
            self.manager.track_interaction(
                user_id="user1",
                interaction_type=InteractionType.CLICK,
                feature_id=f"feature_{i}",
                feature_name=f"功能{i}"
            )
        
        self.assertEqual(len(self.manager.interactions), 5)
    
    def test_feature_usage_tracking(self):
        """Test feature usage is tracked correctly"""
        # Track same feature multiple times
        for _ in range(3):
            self.manager.track_interaction(
                user_id="user1",
                interaction_type=InteractionType.CLICK,
                feature_id="feature_income",
                feature_name="收入录入"
            )
        
        usage = self.manager.feature_usage["user1"]["feature_income"]
        self.assertEqual(usage, 3)
    
    def test_time_pattern_tracking(self):
        """Test time patterns are tracked"""
        interaction = self.manager.track_interaction(
            user_id="user1",
            interaction_type=InteractionType.CLICK,
            feature_id="feature_income",
            feature_name="收入录入"
        )
        
        hour = interaction.timestamp.hour
        self.assertGreater(self.manager.time_patterns["user1"][hour], 0)


class TestFeatureUsageStats(unittest.TestCase):
    """Test feature usage statistics"""
    
    def setUp(self):
        """Set up test environment"""
        self.temp_dir = tempfile.mkdtemp()
        self.storage_path = os.path.join(self.temp_dir, "adaptive_interface")
        self.manager = AdaptiveInterfaceManager(self.storage_path)
        
        # Create test data
        features = ["income", "expense", "report", "order", "bank"]
        usage_counts = [10, 8, 5, 3, 1]
        
        for feature, count in zip(features, usage_counts):
            for _ in range(count):
                self.manager.track_interaction(
                    user_id="user1",
                    interaction_type=InteractionType.CLICK,
                    feature_id=feature,
                    feature_name=feature
                )
    
    def tearDown(self):
        """Clean up test environment"""
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_get_feature_usage_stats(self):
        """Test getting feature usage statistics"""
        stats = self.manager.get_feature_usage_stats("user1", top_n=5)
        
        self.assertEqual(len(stats), 5)
        # Should be sorted by usage count descending
        self.assertEqual(stats[0][0], "income")
        self.assertEqual(stats[0][1], 10)
        self.assertEqual(stats[1][0], "expense")
        self.assertEqual(stats[1][1], 8)
    
    def test_top_n_limit(self):
        """Test top_n parameter limits results"""
        stats = self.manager.get_feature_usage_stats("user1", top_n=3)
        
        self.assertEqual(len(stats), 3)
        self.assertEqual(stats[0][0], "income")
        self.assertEqual(stats[1][0], "expense")
        self.assertEqual(stats[2][0], "report")


class TestInterfaceLayoutOptimization(unittest.TestCase):
    """Test interface layout optimization"""
    
    def setUp(self):
        """Set up test environment"""
        self.temp_dir = tempfile.mkdtemp()
        self.storage_path = os.path.join(self.temp_dir, "adaptive_interface")
        self.manager = AdaptiveInterfaceManager(self.storage_path)
        
        # Create usage data
        features = ["income", "expense", "report", "order", "bank", "customer", "vendor"]
        usage_counts = [10, 8, 5, 3, 2, 1, 1]
        
        for feature, count in zip(features, usage_counts):
            for _ in range(count):
                self.manager.track_interaction(
                    user_id="user1",
                    interaction_type=InteractionType.CLICK,
                    feature_id=feature,
                    feature_name=feature
                )
    
    def tearDown(self):
        """Clean up test environment"""
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_optimize_interface_layout(self):
        """Test interface layout optimization"""
        available_features = ["income", "expense", "report", "order", "bank", "customer", "vendor"]
        
        layout = self.manager.optimize_interface_layout(
            user_id="user1",
            available_features=available_features,
            primary_count=3,
            secondary_count=3
        )
        
        self.assertIsNotNone(layout)
        self.assertEqual(len(layout.primary_features), 3)
        self.assertEqual(len(layout.secondary_features), 3)
        self.assertEqual(len(layout.hidden_features), 1)
    
    def test_layout_sorted_by_usage(self):
        """Test layout features are sorted by usage"""
        available_features = ["income", "expense", "report", "order", "bank"]
        
        layout = self.manager.optimize_interface_layout(
            user_id="user1",
            available_features=available_features,
            primary_count=3
        )
        
        # Most used features should be primary
        self.assertIn("income", layout.primary_features)
        self.assertIn("expense", layout.primary_features)
        self.assertIn("report", layout.primary_features)
    
    def test_layout_confidence_score(self):
        """Test layout confidence score calculation"""
        available_features = ["income", "expense"]
        
        layout = self.manager.optimize_interface_layout(
            user_id="user1",
            available_features=available_features
        )
        
        # Should have some confidence based on interactions
        self.assertGreater(layout.confidence_score, 0.0)
        self.assertLessEqual(layout.confidence_score, 1.0)
    
    def test_get_current_layout(self):
        """Test getting current layout"""
        available_features = ["income", "expense", "report"]
        
        layout1 = self.manager.optimize_interface_layout(
            user_id="user1",
            available_features=available_features
        )
        
        current = self.manager.get_current_layout("user1")
        
        self.assertIsNotNone(current)
        self.assertEqual(current.layout_id, layout1.layout_id)


class TestTimePatternAnalysis(unittest.TestCase):
    """Test time pattern analysis"""
    
    def setUp(self):
        """Set up test environment"""
        self.temp_dir = tempfile.mkdtemp()
        self.storage_path = os.path.join(self.temp_dir, "adaptive_interface")
        self.manager = AdaptiveInterfaceManager(self.storage_path)
    
    def tearDown(self):
        """Clean up test environment"""
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_analyze_time_patterns_no_data(self):
        """Test time pattern analysis with no data"""
        patterns = self.manager.analyze_time_patterns("user1")
        
        # Should return default patterns
        self.assertIn('peak_hours', patterns)
        self.assertIn('low_hours', patterns)
        self.assertIn('preferred_hours', patterns)
        self.assertIsInstance(patterns['peak_hours'], list)
    
    def test_analyze_time_patterns_with_data(self):
        """Test time pattern analysis with data"""
        # Simulate activity at specific hours
        for hour in [9, 9, 9, 10, 10, 14, 14, 14, 14]:
            self.manager.time_patterns["user1"][hour] += 1
        
        patterns = self.manager.analyze_time_patterns("user1")
        
        # Should identify peak hours
        self.assertIn(9, patterns['peak_hours'] + patterns['preferred_hours'])
        self.assertIn(14, patterns['peak_hours'] + patterns['preferred_hours'])


class TestNotificationScheduling(unittest.TestCase):
    """Test notification scheduling"""
    
    def setUp(self):
        """Set up test environment"""
        self.temp_dir = tempfile.mkdtemp()
        self.storage_path = os.path.join(self.temp_dir, "adaptive_interface")
        self.manager = AdaptiveInterfaceManager(self.storage_path)
        
        # Set up time patterns
        for hour in [9, 10, 14, 15]:
            self.manager.time_patterns["user1"][hour] = 10
        for hour in [0, 1, 2, 22, 23]:
            self.manager.time_patterns["user1"][hour] = 1
    
    def tearDown(self):
        """Clean up test environment"""
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_create_notification_schedule(self):
        """Test creating notification schedule"""
        schedule = self.manager.create_notification_schedule(
            user_id="user1",
            notification_type="reminder"
        )
        
        self.assertIsNotNone(schedule)
        self.assertEqual(schedule.user_id, "user1")
        self.assertEqual(schedule.notification_type, "reminder")
        self.assertIsInstance(schedule.preferred_times, list)
    
    def test_should_send_notification_urgent(self):
        """Test urgent notifications always sent"""
        # Create schedule
        self.manager.create_notification_schedule("user1", "reminder")
        
        # Urgent should always be sent
        test_time = datetime.now().replace(hour=2)  # Low activity hour
        should_send = self.manager.should_send_notification(
            user_id="user1",
            notification_type="reminder",
            priority=NotificationPriority.URGENT,
            current_time=test_time
        )
        
        self.assertTrue(should_send)
    
    def test_should_send_notification_avoid_times(self):
        """Test notifications avoided during low activity"""
        schedule = self.manager.create_notification_schedule("user1", "reminder")
        
        # Low priority during avoid times should not be sent
        if schedule.avoid_times:
            test_time = datetime.now().replace(hour=schedule.avoid_times[0])
            should_send = self.manager.should_send_notification(
                user_id="user1",
                notification_type="reminder",
                priority=NotificationPriority.LOW,
                current_time=test_time
            )
            
            self.assertFalse(should_send)
    
    def test_should_send_notification_preferred_times(self):
        """Test notifications sent during preferred times"""
        schedule = self.manager.create_notification_schedule("user1", "reminder")
        
        # Should send during preferred times
        if schedule.preferred_times:
            test_time = datetime.now().replace(hour=schedule.preferred_times[0])
            should_send = self.manager.should_send_notification(
                user_id="user1",
                notification_type="reminder",
                priority=NotificationPriority.MEDIUM,
                current_time=test_time
            )
            
            self.assertTrue(should_send)
    
    def test_track_notification_response(self):
        """Test tracking notification responses"""
        self.manager.track_notification_response(
            user_id="user1",
            notification_type="reminder",
            response="opened"
        )
        
        key = "user1_reminder"
        self.assertEqual(self.manager.notification_responses[key]["opened"], 1)


class TestPersonalizedInsights(unittest.TestCase):
    """Test personalized insights generation"""
    
    def setUp(self):
        """Set up test environment"""
        self.temp_dir = tempfile.mkdtemp()
        self.storage_path = os.path.join(self.temp_dir, "adaptive_interface")
        self.manager = AdaptiveInterfaceManager(self.storage_path)
        
        # Create usage data
        for _ in range(10):
            self.manager.track_interaction(
                user_id="user1",
                interaction_type=InteractionType.CLICK,
                feature_id="income",
                feature_name="收入录入"
            )
    
    def tearDown(self):
        """Clean up test environment"""
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_generate_personalized_insights(self):
        """Test generating personalized insights"""
        insights = self.manager.generate_personalized_insights("user1")
        
        self.assertIsInstance(insights, list)
        self.assertGreater(len(insights), 0)
        
        # Check insight structure
        for insight in insights:
            self.assertIsInstance(insight, PersonalizedInsight)
            self.assertEqual(insight.user_id, "user1")
            self.assertIsNotNone(insight.title)
            self.assertIsNotNone(insight.description)
    
    def test_get_unread_insights(self):
        """Test getting unread insights"""
        # Generate insights
        self.manager.generate_personalized_insights("user1")
        
        unread = self.manager.get_unread_insights("user1")
        
        self.assertGreater(len(unread), 0)
        for insight in unread:
            self.assertFalse(insight.is_read)
    
    def test_mark_insight_read(self):
        """Test marking insight as read"""
        insights = self.manager.generate_personalized_insights("user1")
        insight_id = insights[0].insight_id
        
        result = self.manager.mark_insight_read(insight_id)
        
        self.assertTrue(result)
        
        # Verify it's marked as read
        insight = self.manager.insights[insight_id]
        self.assertTrue(insight.is_read)
    
    def test_expired_insights_not_returned(self):
        """Test expired insights are not returned"""
        # Create an expired insight
        expired_insight = PersonalizedInsight(
            insight_id="expired_1",
            user_id="user1",
            insight_type="test",
            title="过期提示",
            description="这是一个过期的提示",
            action_items=[],
            priority=NotificationPriority.LOW,
            created_at=datetime.now() - timedelta(days=10),
            expires_at=datetime.now() - timedelta(days=1)
        )
        
        self.manager.insights[expired_insight.insight_id] = expired_insight
        
        unread = self.manager.get_unread_insights("user1")
        
        # Expired insight should not be in unread list
        expired_ids = [i.insight_id for i in unread]
        self.assertNotIn("expired_1", expired_ids)


class TestInteractionHistory(unittest.TestCase):
    """Test interaction history retrieval"""
    
    def setUp(self):
        """Set up test environment"""
        self.temp_dir = tempfile.mkdtemp()
        self.storage_path = os.path.join(self.temp_dir, "adaptive_interface")
        self.manager = AdaptiveInterfaceManager(self.storage_path)
    
    def tearDown(self):
        """Clean up test environment"""
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_get_interaction_history(self):
        """Test getting interaction history"""
        # Create interactions
        for i in range(5):
            self.manager.track_interaction(
                user_id="user1",
                interaction_type=InteractionType.CLICK,
                feature_id=f"feature_{i}",
                feature_name=f"功能{i}"
            )
        
        history = self.manager.get_interaction_history("user1", days=7)
        
        self.assertEqual(len(history), 5)
    
    def test_interaction_history_time_filter(self):
        """Test interaction history filters by time"""
        # Create old interaction (manually)
        old_interaction = UserInteraction(
            interaction_id="old_1",
            user_id="user1",
            interaction_type=InteractionType.CLICK,
            feature_id="old_feature",
            feature_name="旧功能",
            timestamp=datetime.now() - timedelta(days=10)
        )
        self.manager.interactions.append(old_interaction)
        
        # Create recent interaction
        self.manager.track_interaction(
            user_id="user1",
            interaction_type=InteractionType.CLICK,
            feature_id="new_feature",
            feature_name="新功能"
        )
        
        # Get last 7 days
        history = self.manager.get_interaction_history("user1", days=7)
        
        # Should only include recent interaction
        self.assertEqual(len(history), 1)
        self.assertEqual(history[0].feature_id, "new_feature")


class TestDataPersistence(unittest.TestCase):
    """Test data persistence"""
    
    def setUp(self):
        """Set up test environment"""
        self.temp_dir = tempfile.mkdtemp()
        self.storage_path = os.path.join(self.temp_dir, "adaptive_interface")
    
    def tearDown(self):
        """Clean up test environment"""
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_interactions_persist(self):
        """Test interactions are saved and loaded"""
        # Create manager and add interactions
        manager1 = AdaptiveInterfaceManager(self.storage_path)
        
        for i in range(5):
            manager1.track_interaction(
                user_id="user1",
                interaction_type=InteractionType.CLICK,
                feature_id=f"feature_{i}",
                feature_name=f"功能{i}"
            )
        
        manager1._save_data()
        
        # Create new manager instance
        manager2 = AdaptiveInterfaceManager(self.storage_path)
        
        # Verify interactions were loaded
        self.assertEqual(len(manager2.interactions), 5)
    
    def test_feature_usage_cache_rebuilt(self):
        """Test feature usage cache is rebuilt on load"""
        # Create manager and add interactions
        manager1 = AdaptiveInterfaceManager(self.storage_path)
        
        for _ in range(3):
            manager1.track_interaction(
                user_id="user1",
                interaction_type=InteractionType.CLICK,
                feature_id="income",
                feature_name="收入"
            )
        
        manager1._save_data()
        
        # Create new manager instance
        manager2 = AdaptiveInterfaceManager(self.storage_path)
        
        # Verify cache was rebuilt
        self.assertEqual(manager2.feature_usage["user1"]["income"], 3)


if __name__ == '__main__':
    unittest.main()
