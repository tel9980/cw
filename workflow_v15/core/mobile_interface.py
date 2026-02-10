# -*- coding: utf-8 -*-
"""
Mobile Interface Layer for V1.5 Workflow System

This module provides mobile-optimized interface components including:
1. Touch-friendly UI components
2. Mobile-specific progressive disclosure (essential functions only)
3. Voice input handlers for common data entry tasks
4. Photo capture with automatic data extraction

Requirements: 7.1, 7.2, 7.3, 7.4
"""

import logging
from typing import Dict, List, Optional, Any, Callable
from datetime import datetime
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
import json

logger = logging.getLogger(__name__)


class InputMode(Enum):
    """Input modes for mobile interface"""
    TOUCH = "touch"
    VOICE = "voice"
    PHOTO = "photo"
    KEYBOARD = "keyboard"


class ScreenSize(Enum):
    """Mobile screen size categories"""
    SMALL = "small"  # < 5 inches
    MEDIUM = "medium"  # 5-6.5 inches
    LARGE = "large"  # > 6.5 inches


@dataclass
class TouchGesture:
    """Represents a touch gesture"""
    gesture_type: str  # tap, long_press, swipe, pinch
    x: float
    y: float
    timestamp: datetime = field(default_factory=datetime.now)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class VoiceInput:
    """Represents voice input"""
    input_id: str
    raw_text: str
    confidence: float
    intent: Optional[str] = None
    entities: Dict[str, Any] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=datetime.now)


@dataclass
class PhotoCapture:
    """Represents a captured photo"""
    photo_id: str
    file_path: str
    captured_at: datetime
    extracted_data: Dict[str, Any] = field(default_factory=dict)
    ocr_confidence: float = 0.0


@dataclass
class MobileAction:
    """Represents a mobile-optimized action"""
    action_id: str
    title: str
    icon: str
    description: str
    function_code: str
    is_essential: bool = True
    touch_target_size: int = 48  # Minimum 48dp for touch targets
    supports_voice: bool = False
    supports_photo: bool = False


class MobileInterfaceManager:
    """
    Manages mobile-optimized interface for the financial system.
    
    Features:
    - Touch-friendly UI components
    - Mobile progressive disclosure
    - Voice input processing
    - Photo capture and OCR
    """
    
    def __init__(self, storage_dir: Optional[Path] = None):
        """
        Initialize the mobile interface manager.
        
        Args:
            storage_dir: Directory for storing mobile data
        """
        self.storage_dir = storage_dir or Path("财务数据/mobile")
        self.storage_dir.mkdir(parents=True, exist_ok=True)
        
        # Mobile actions registry
        self.essential_actions: List[MobileAction] = []
        self.secondary_actions: List[MobileAction] = []
        
        # Voice command handlers
        self.voice_handlers: Dict[str, Callable] = {}
        
        # Photo processing handlers
        self.photo_handlers: Dict[str, Callable] = {}
        
        # User preferences
        self.user_preferences: Dict[str, Any] = {
            "screen_size": ScreenSize.MEDIUM,
            "preferred_input": InputMode.TOUCH,
            "voice_enabled": True,
            "photo_enabled": True,
            "font_size": "medium",
            "high_contrast": False
        }
        
        # Register default actions and handlers
        self._register_default_actions()
        self._register_default_voice_handlers()
        self._register_default_photo_handlers()
        
        logger.info("MobileInterfaceManager initialized")
    
    def _register_default_actions(self):
        """Register default mobile-optimized actions"""
        # Essential actions (always visible on mobile)
        self.essential_actions = [
            MobileAction(
                action_id="quick_transaction",
                title="快速记账",
                icon="💰",
                description="快速录入收支",
                function_code="1",
                is_essential=True,
                supports_voice=True,
                supports_photo=True
            ),
            MobileAction(
                action_id="view_balance",
                title="查看余额",
                icon="📊",
                description="查看账户余额",
                function_code="31",
                is_essential=True
            ),
            MobileAction(
                action_id="scan_receipt",
                title="扫描票据",
                icon="📷",
                description="拍照识别票据",
                function_code="1",
                is_essential=True,
                supports_photo=True
            ),
            MobileAction(
                action_id="voice_entry",
                title="语音记账",
                icon="🎤",
                description="语音输入交易",
                function_code="1",
                is_essential=True,
                supports_voice=True
            ),
            MobileAction(
                action_id="view_reminders",
                title="待办提醒",
                icon="🔔",
                description="查看待办事项",
                function_code="57",
                is_essential=True
            )
        ]
        
        # Secondary actions (accessible via menu)
        self.secondary_actions = [
            MobileAction(
                action_id="manage_orders",
                title="订单管理",
                icon="📦",
                description="管理加工订单",
                function_code="5",
                is_essential=False
            ),
            MobileAction(
                action_id="bank_statements",
                title="银行流水",
                icon="🏦",
                description="查看银行流水",
                function_code="15",
                is_essential=False
            ),
            MobileAction(
                action_id="reports",
                title="财务报表",
                icon="📈",
                description="查看财务报表",
                function_code="31",
                is_essential=False
            )
        ]
    
    def _register_default_voice_handlers(self):
        """Register default voice command handlers"""
        self.voice_handlers = {
            "record_income": self._handle_voice_income,
            "record_expense": self._handle_voice_expense,
            "check_balance": self._handle_voice_balance,
            "create_reminder": self._handle_voice_reminder
        }
    
    def _register_default_photo_handlers(self):
        """Register default photo processing handlers"""
        self.photo_handlers = {
            "receipt": self._handle_receipt_photo,
            "invoice": self._handle_invoice_photo,
            "bank_statement": self._handle_bank_statement_photo
        }
    
    def get_mobile_layout(
        self,
        screen_size: ScreenSize,
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Get mobile-optimized layout configuration.
        
        Args:
            screen_size: Screen size category
            context: Optional context for personalization
            
        Returns:
            Layout configuration
        """
        # Adjust number of visible actions based on screen size
        max_essential = {
            ScreenSize.SMALL: 4,
            ScreenSize.MEDIUM: 5,
            ScreenSize.LARGE: 6
        }
        
        visible_count = max_essential.get(screen_size, 5)
        
        # Get essential actions (limited by screen size)
        visible_actions = self.essential_actions[:visible_count]
        
        layout = {
            "screen_size": screen_size.value,
            "essential_actions": [
                {
                    "action_id": action.action_id,
                    "title": action.title,
                    "icon": action.icon,
                    "description": action.description,
                    "function_code": action.function_code,
                    "touch_target_size": action.touch_target_size,
                    "supports_voice": action.supports_voice,
                    "supports_photo": action.supports_photo
                }
                for action in visible_actions
            ],
            "secondary_actions_count": len(self.secondary_actions),
            "input_modes": {
                "touch": True,
                "voice": self.user_preferences["voice_enabled"],
                "photo": self.user_preferences["photo_enabled"]
            },
            "ui_settings": {
                "font_size": self.user_preferences["font_size"],
                "high_contrast": self.user_preferences["high_contrast"],
                "touch_target_min_size": 48  # dp
            }
        }
        
        return layout
    
    def process_touch_gesture(
        self,
        gesture: TouchGesture
    ) -> Dict[str, Any]:
        """
        Process a touch gesture.
        
        Args:
            gesture: Touch gesture data
            
        Returns:
            Processing result
        """
        result = {
            "gesture_type": gesture.gesture_type,
            "recognized": True,
            "action": None
        }
        
        if gesture.gesture_type == "tap":
            # Handle tap gesture
            result["action"] = "select"
            result["message"] = "项目已选择"
        
        elif gesture.gesture_type == "long_press":
            # Handle long press (show context menu)
            result["action"] = "context_menu"
            result["message"] = "显示更多选项"
        
        elif gesture.gesture_type == "swipe":
            # Handle swipe gesture
            direction = gesture.metadata.get("direction", "unknown")
            if direction == "left":
                result["action"] = "next"
            elif direction == "right":
                result["action"] = "previous"
            elif direction == "down":
                result["action"] = "refresh"
        
        elif gesture.gesture_type == "pinch":
            # Handle pinch gesture (zoom)
            scale = gesture.metadata.get("scale", 1.0)
            result["action"] = "zoom"
            result["scale"] = scale
        
        return result
    
    def process_voice_input(
        self,
        voice_input: VoiceInput
    ) -> Dict[str, Any]:
        """
        Process voice input and extract intent/entities.
        
        Args:
            voice_input: Voice input data
            
        Returns:
            Processing result with extracted data
        """
        text = voice_input.raw_text.lower()
        
        # Simple intent recognition (in production, use NLP service)
        intent = None
        entities = {}
        
        # Detect income recording
        if any(keyword in text for keyword in ["收入", "收款", "进账"]):
            intent = "record_income"
            entities = self._extract_transaction_entities(text, "income")
        
        # Detect reminder creation (check before expense to avoid conflict)
        elif any(keyword in text for keyword in ["提醒", "待办", "记得"]):
            intent = "create_reminder"
            entities = self._extract_reminder_entities(text)
        
        # Detect expense recording
        elif any(keyword in text for keyword in ["支出", "付款", "花费"]):
            intent = "record_expense"
            entities = self._extract_transaction_entities(text, "expense")
        
        # Detect balance check
        elif any(keyword in text for keyword in ["余额", "多少钱", "账户"]):
            intent = "check_balance"
        
        voice_input.intent = intent
        voice_input.entities = entities
        
        # Execute handler if available
        result = {
            "input_id": voice_input.input_id,
            "raw_text": voice_input.raw_text,
            "intent": intent,
            "entities": entities,
            "confidence": voice_input.confidence,
            "success": False
        }
        
        if intent and intent in self.voice_handlers:
            try:
                handler_result = self.voice_handlers[intent](entities)
                result["success"] = True
                result["data"] = handler_result
                result["message"] = "语音命令已执行"
            except Exception as e:
                result["error"] = str(e)
                result["message"] = f"执行失败: {e}"
        else:
            result["message"] = "未识别的语音命令"
        
        return result
    
    def _extract_transaction_entities(
        self,
        text: str,
        trans_type: str
    ) -> Dict[str, Any]:
        """Extract transaction entities from voice text"""
        entities = {"type": trans_type}
        
        # Extract amount (simple pattern matching)
        import re
        amount_patterns = [
            r'(\d+\.?\d*)\s*元',
            r'(\d+\.?\d*)\s*块',
            r'(\d+\.?\d*)\s*钱'
        ]
        
        for pattern in amount_patterns:
            match = re.search(pattern, text)
            if match:
                entities["amount"] = float(match.group(1))
                break
        
        # Extract entity name (simplified)
        if "给" in text:
            parts = text.split("给")
            if len(parts) > 1:
                entity_part = parts[1].split()[0] if parts[1].split() else ""
                entities["entity_name"] = entity_part
        
        return entities
    
    def _extract_reminder_entities(self, text: str) -> Dict[str, Any]:
        """Extract reminder entities from voice text"""
        entities = {}
        
        # Extract time references
        if "明天" in text:
            entities["due_date"] = "tomorrow"
        elif "今天" in text:
            entities["due_date"] = "today"
        elif "下周" in text:
            entities["due_date"] = "next_week"
        
        # Extract reminder content (simplified)
        entities["content"] = text
        
        return entities
    
    def _handle_voice_income(self, entities: Dict[str, Any]) -> Dict[str, Any]:
        """Handle voice income recording"""
        return {
            "action": "create_transaction",
            "type": "income",
            "amount": entities.get("amount"),
            "entity_name": entities.get("entity_name"),
            "date": datetime.now().strftime("%Y-%m-%d")
        }
    
    def _handle_voice_expense(self, entities: Dict[str, Any]) -> Dict[str, Any]:
        """Handle voice expense recording"""
        return {
            "action": "create_transaction",
            "type": "expense",
            "amount": entities.get("amount"),
            "entity_name": entities.get("entity_name"),
            "date": datetime.now().strftime("%Y-%m-%d")
        }
    
    def _handle_voice_balance(self, entities: Dict[str, Any]) -> Dict[str, Any]:
        """Handle voice balance check"""
        return {
            "action": "check_balance",
            "account": entities.get("account", "default")
        }
    
    def _handle_voice_reminder(self, entities: Dict[str, Any]) -> Dict[str, Any]:
        """Handle voice reminder creation"""
        return {
            "action": "create_reminder",
            "content": entities.get("content"),
            "due_date": entities.get("due_date", "today")
        }
    
    def process_photo_capture(
        self,
        photo: PhotoCapture,
        photo_type: str = "receipt"
    ) -> Dict[str, Any]:
        """
        Process captured photo and extract data.
        
        Args:
            photo: Photo capture data
            photo_type: Type of photo (receipt, invoice, bank_statement)
            
        Returns:
            Processing result with extracted data
        """
        result = {
            "photo_id": photo.photo_id,
            "photo_type": photo_type,
            "success": False,
            "extracted_data": {}
        }
        
        # Execute appropriate handler
        if photo_type in self.photo_handlers:
            try:
                extracted = self.photo_handlers[photo_type](photo)
                photo.extracted_data = extracted
                result["success"] = True
                result["extracted_data"] = extracted
                result["message"] = "数据提取成功"
            except Exception as e:
                result["error"] = str(e)
                result["message"] = f"提取失败: {e}"
        else:
            result["message"] = f"不支持的照片类型: {photo_type}"
        
        return result
    
    def _handle_receipt_photo(self, photo: PhotoCapture) -> Dict[str, Any]:
        """Handle receipt photo processing (OCR simulation)"""
        # In production, this would use OCR service
        # For now, return simulated extraction
        return {
            "type": "receipt",
            "amount": 0.0,  # Would be extracted from OCR
            "date": datetime.now().strftime("%Y-%m-%d"),
            "merchant": "",  # Would be extracted from OCR
            "items": [],  # Would be extracted from OCR
            "ocr_confidence": 0.85
        }
    
    def _handle_invoice_photo(self, photo: PhotoCapture) -> Dict[str, Any]:
        """Handle invoice photo processing"""
        return {
            "type": "invoice",
            "invoice_number": "",
            "amount": 0.0,
            "date": datetime.now().strftime("%Y-%m-%d"),
            "vendor": "",
            "ocr_confidence": 0.80
        }
    
    def _handle_bank_statement_photo(self, photo: PhotoCapture) -> Dict[str, Any]:
        """Handle bank statement photo processing"""
        return {
            "type": "bank_statement",
            "transactions": [],
            "account_number": "",
            "period": "",
            "ocr_confidence": 0.75
        }
    
    def get_essential_actions(
        self,
        context: Optional[Dict[str, Any]] = None
    ) -> List[MobileAction]:
        """
        Get essential actions for mobile interface.
        
        Args:
            context: Optional context for personalization
            
        Returns:
            List of essential actions
        """
        return self.essential_actions
    
    def get_secondary_actions(self) -> List[MobileAction]:
        """Get secondary actions (accessible via menu)"""
        return self.secondary_actions
    
    def update_user_preferences(
        self,
        preferences: Dict[str, Any]
    ) -> bool:
        """
        Update user preferences for mobile interface.
        
        Args:
            preferences: Preference updates
            
        Returns:
            Success status
        """
        try:
            self.user_preferences.update(preferences)
            
            # Save to disk (convert enums to strings for JSON serialization)
            prefs_file = self.storage_dir / "user_preferences.json"
            prefs_to_save = {}
            for key, value in self.user_preferences.items():
                if isinstance(value, Enum):
                    prefs_to_save[key] = value.value
                else:
                    prefs_to_save[key] = value
            
            with open(prefs_file, 'w', encoding='utf-8') as f:
                json.dump(prefs_to_save, f, ensure_ascii=False, indent=2)
            
            return True
        except Exception as e:
            logger.error(f"Failed to update preferences: {e}")
            return False
    
    def is_mobile_optimized(self, function_code: str) -> bool:
        """Check if a function is mobile-optimized"""
        all_actions = self.essential_actions + self.secondary_actions
        return any(action.function_code == function_code for action in all_actions)
    
    def get_touch_target_size(self, action_id: str) -> int:
        """Get recommended touch target size for an action"""
        all_actions = self.essential_actions + self.secondary_actions
        action = next((a for a in all_actions if a.action_id == action_id), None)
        return action.touch_target_size if action else 48
