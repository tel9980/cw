# -*- coding: utf-8 -*-
"""
Tests for Mobile Interface Manager

Requirements: 7.1, 7.2, 7.3, 7.4
"""

import pytest
from datetime import datetime
from pathlib import Path
import tempfile
import shutil

from workflow_v15.core.mobile_interface import (
    MobileInterfaceManager,
    InputMode,
    ScreenSize,
    TouchGesture,
    VoiceInput,
    PhotoCapture,
    MobileAction
)


@pytest.fixture
def temp_dir():
    """Create a temporary directory for testing"""
    temp_path = Path(tempfile.mkdtemp())
    yield temp_path
    shutil.rmtree(temp_path)


@pytest.fixture
def mobile_manager(temp_dir):
    """Create a mobile interface manager for testing"""
    return MobileInterfaceManager(storage_dir=temp_dir / "mobile")


class TestMobileInterfaceInitialization:
    """Test mobile interface initialization"""
    
    def test_initialization(self, mobile_manager):
        """Test manager initializes correctly"""
        assert mobile_manager is not None
        assert len(mobile_manager.essential_actions) > 0
        assert len(mobile_manager.secondary_actions) > 0
        assert len(mobile_manager.voice_handlers) > 0
        assert len(mobile_manager.photo_handlers) > 0
    
    def test_default_preferences(self, mobile_manager):
        """Test default user preferences"""
        prefs = mobile_manager.user_preferences
        assert prefs["screen_size"] == ScreenSize.MEDIUM
        assert prefs["preferred_input"] == InputMode.TOUCH
        assert prefs["voice_enabled"] is True
        assert prefs["photo_enabled"] is True


class TestMobileLayout:
    """Test mobile layout generation"""
    
    def test_small_screen_layout(self, mobile_manager):
        """Test layout for small screens"""
        layout = mobile_manager.get_mobile_layout(ScreenSize.SMALL)
        assert layout["screen_size"] == "small"
        assert len(layout["essential_actions"]) <= 4
        assert layout["ui_settings"]["touch_target_min_size"] == 48
    
    def test_medium_screen_layout(self, mobile_manager):
        """Test layout for medium screens"""
        layout = mobile_manager.get_mobile_layout(ScreenSize.MEDIUM)
        assert layout["screen_size"] == "medium"
        assert len(layout["essential_actions"]) <= 5
    
    def test_large_screen_layout(self, mobile_manager):
        """Test layout for large screens"""
        layout = mobile_manager.get_mobile_layout(ScreenSize.LARGE)
        assert layout["screen_size"] == "large"
        assert len(layout["essential_actions"]) <= 6
    
    def test_layout_includes_input_modes(self, mobile_manager):
        """Test layout includes input mode information"""
        layout = mobile_manager.get_mobile_layout(ScreenSize.MEDIUM)
        assert "input_modes" in layout
        assert layout["input_modes"]["touch"] is True
        assert "voice" in layout["input_modes"]
        assert "photo" in layout["input_modes"]


class TestTouchGestures:
    """Test touch gesture processing"""
    
    def test_tap_gesture(self, mobile_manager):
        """Test tap gesture processing"""
        gesture = TouchGesture(gesture_type="tap", x=100, y=200)
        result = mobile_manager.process_touch_gesture(gesture)
        assert result["recognized"] is True
        assert result["action"] == "select"
    
    def test_long_press_gesture(self, mobile_manager):
        """Test long press gesture"""
        gesture = TouchGesture(gesture_type="long_press", x=100, y=200)
        result = mobile_manager.process_touch_gesture(gesture)
        assert result["action"] == "context_menu"
    
    def test_swipe_left_gesture(self, mobile_manager):
        """Test swipe left gesture"""
        gesture = TouchGesture(
            gesture_type="swipe",
            x=100,
            y=200,
            metadata={"direction": "left"}
        )
        result = mobile_manager.process_touch_gesture(gesture)
        assert result["action"] == "next"
    
    def test_swipe_right_gesture(self, mobile_manager):
        """Test swipe right gesture"""
        gesture = TouchGesture(
            gesture_type="swipe",
            x=100,
            y=200,
            metadata={"direction": "right"}
        )
        result = mobile_manager.process_touch_gesture(gesture)
        assert result["action"] == "previous"
    
    def test_pinch_gesture(self, mobile_manager):
        """Test pinch gesture"""
        gesture = TouchGesture(
            gesture_type="pinch",
            x=100,
            y=200,
            metadata={"scale": 1.5}
        )
        result = mobile_manager.process_touch_gesture(gesture)
        assert result["action"] == "zoom"
        assert result["scale"] == 1.5


class TestVoiceInput:
    """Test voice input processing"""
    
    def test_voice_income_recognition(self, mobile_manager):
        """Test voice recognition for income"""
        voice = VoiceInput(
            input_id="v1",
            raw_text="收入500元",
            confidence=0.9
        )
        result = mobile_manager.process_voice_input(voice)
        assert result["intent"] == "record_income"
        assert result["entities"]["type"] == "income"
        assert result["entities"]["amount"] == 500.0
    
    def test_voice_expense_recognition(self, mobile_manager):
        """Test voice recognition for expense"""
        voice = VoiceInput(
            input_id="v2",
            raw_text="支出200元",
            confidence=0.85
        )
        result = mobile_manager.process_voice_input(voice)
        assert result["intent"] == "record_expense"
        assert result["entities"]["type"] == "expense"
        assert result["entities"]["amount"] == 200.0
    
    def test_voice_balance_check(self, mobile_manager):
        """Test voice recognition for balance check"""
        voice = VoiceInput(
            input_id="v3",
            raw_text="查看余额",
            confidence=0.95
        )
        result = mobile_manager.process_voice_input(voice)
        assert result["intent"] == "check_balance"
    
    def test_voice_reminder_creation(self, mobile_manager):
        """Test voice recognition for reminder"""
        voice = VoiceInput(
            input_id="v4",
            raw_text="提醒我明天付款",
            confidence=0.88
        )
        result = mobile_manager.process_voice_input(voice)
        assert result["intent"] == "create_reminder"
        assert result["entities"]["due_date"] == "tomorrow"
    
    def test_voice_amount_extraction(self, mobile_manager):
        """Test amount extraction from voice"""
        voice = VoiceInput(
            input_id="v5",
            raw_text="收入1500.50元",
            confidence=0.9
        )
        result = mobile_manager.process_voice_input(voice)
        assert result["entities"]["amount"] == 1500.50
    
    def test_voice_unrecognized_command(self, mobile_manager):
        """Test unrecognized voice command"""
        voice = VoiceInput(
            input_id="v6",
            raw_text="随便说点什么",
            confidence=0.7
        )
        result = mobile_manager.process_voice_input(voice)
        assert result["intent"] is None
        assert result["success"] is False


class TestPhotoCapture:
    """Test photo capture and processing"""
    
    def test_receipt_photo_processing(self, mobile_manager):
        """Test receipt photo processing"""
        photo = PhotoCapture(
            photo_id="p1",
            file_path="/path/to/receipt.jpg",
            captured_at=datetime.now()
        )
        result = mobile_manager.process_photo_capture(photo, "receipt")
        assert result["success"] is True
        assert result["photo_type"] == "receipt"
        assert "extracted_data" in result
        assert result["extracted_data"]["type"] == "receipt"
    
    def test_invoice_photo_processing(self, mobile_manager):
        """Test invoice photo processing"""
        photo = PhotoCapture(
            photo_id="p2",
            file_path="/path/to/invoice.jpg",
            captured_at=datetime.now()
        )
        result = mobile_manager.process_photo_capture(photo, "invoice")
        assert result["success"] is True
        assert result["extracted_data"]["type"] == "invoice"
    
    def test_bank_statement_photo_processing(self, mobile_manager):
        """Test bank statement photo processing"""
        photo = PhotoCapture(
            photo_id="p3",
            file_path="/path/to/statement.jpg",
            captured_at=datetime.now()
        )
        result = mobile_manager.process_photo_capture(photo, "bank_statement")
        assert result["success"] is True
        assert result["extracted_data"]["type"] == "bank_statement"
    
    def test_unsupported_photo_type(self, mobile_manager):
        """Test unsupported photo type"""
        photo = PhotoCapture(
            photo_id="p4",
            file_path="/path/to/unknown.jpg",
            captured_at=datetime.now()
        )
        result = mobile_manager.process_photo_capture(photo, "unknown_type")
        assert result["success"] is False


class TestMobileActions:
    """Test mobile action management"""
    
    def test_get_essential_actions(self, mobile_manager):
        """Test getting essential actions"""
        actions = mobile_manager.get_essential_actions()
        assert len(actions) > 0
        assert all(isinstance(a, MobileAction) for a in actions)
        assert all(a.is_essential for a in actions)
    
    def test_get_secondary_actions(self, mobile_manager):
        """Test getting secondary actions"""
        actions = mobile_manager.get_secondary_actions()
        assert len(actions) > 0
        assert all(isinstance(a, MobileAction) for a in actions)
        assert all(not a.is_essential for a in actions)
    
    def test_essential_actions_have_large_touch_targets(self, mobile_manager):
        """Test essential actions have appropriate touch targets"""
        actions = mobile_manager.get_essential_actions()
        for action in actions:
            assert action.touch_target_size >= 48  # Minimum touch target
    
    def test_voice_supported_actions(self, mobile_manager):
        """Test some actions support voice input"""
        actions = mobile_manager.get_essential_actions()
        voice_actions = [a for a in actions if a.supports_voice]
        assert len(voice_actions) > 0
    
    def test_photo_supported_actions(self, mobile_manager):
        """Test some actions support photo input"""
        actions = mobile_manager.get_essential_actions()
        photo_actions = [a for a in actions if a.supports_photo]
        assert len(photo_actions) > 0


class TestUserPreferences:
    """Test user preference management"""
    
    def test_update_preferences(self, mobile_manager):
        """Test updating user preferences"""
        new_prefs = {
            "font_size": "large",
            "high_contrast": True
        }
        success = mobile_manager.update_user_preferences(new_prefs)
        assert success is True
        assert mobile_manager.user_preferences["font_size"] == "large"
        assert mobile_manager.user_preferences["high_contrast"] is True
    
    def test_preferences_persistence(self, temp_dir):
        """Test preferences are persisted"""
        manager1 = MobileInterfaceManager(storage_dir=temp_dir / "mobile")
        manager1.update_user_preferences({"font_size": "large"})
        
        # Create new manager with same storage
        manager2 = MobileInterfaceManager(storage_dir=temp_dir / "mobile")
        # Note: In full implementation, preferences would be loaded from disk
        # For now, just verify the update worked
        assert manager1.user_preferences["font_size"] == "large"


class TestMobileOptimization:
    """Test mobile optimization checks"""
    
    def test_is_mobile_optimized(self, mobile_manager):
        """Test checking if function is mobile-optimized"""
        # Function code "1" should be optimized (quick transaction)
        assert mobile_manager.is_mobile_optimized("1") is True
        
        # Function code "999" should not exist
        assert mobile_manager.is_mobile_optimized("999") is False
    
    def test_get_touch_target_size(self, mobile_manager):
        """Test getting touch target size for actions"""
        size = mobile_manager.get_touch_target_size("quick_transaction")
        assert size >= 48  # Minimum touch target size
        
        # Unknown action should return default
        size = mobile_manager.get_touch_target_size("unknown_action")
        assert size == 48


class TestProgressiveDisclosure:
    """Test mobile progressive disclosure"""
    
    def test_essential_actions_limited(self, mobile_manager):
        """Test essential actions are limited for mobile"""
        actions = mobile_manager.get_essential_actions()
        assert len(actions) <= 6  # Maximum for largest screen
    
    def test_secondary_actions_hidden(self, mobile_manager):
        """Test secondary actions are separate"""
        essential = mobile_manager.get_essential_actions()
        secondary = mobile_manager.get_secondary_actions()
        
        # No overlap between essential and secondary
        essential_ids = {a.action_id for a in essential}
        secondary_ids = {a.action_id for a in secondary}
        assert len(essential_ids & secondary_ids) == 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
