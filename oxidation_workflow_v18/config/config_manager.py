"""
Configuration Manager for Oxidation Workflow System

Manages system configuration including:
- Data storage paths
- Backup settings
- Logging configuration
- User preferences
- System defaults
"""

import json
import os
from pathlib import Path
from typing import Any, Dict, Optional
from dataclasses import dataclass, asdict, field
from datetime import datetime


@dataclass
class StorageConfig:
    """Storage configuration."""
    data_path: str = "./data"
    backup_path: str = "./backups"
    log_path: str = "./logs"
    
    def ensure_directories(self):
        """Create directories if they don't exist."""
        for path in [self.data_path, self.backup_path, self.log_path]:
            Path(path).mkdir(parents=True, exist_ok=True)


@dataclass
class BackupConfig:
    """Backup configuration."""
    auto_backup_enabled: bool = True
    auto_backup_interval_hours: int = 24
    max_backup_count: int = 30
    backup_on_exit: bool = True


@dataclass
class SystemConfig:
    """System-wide configuration."""
    demo_mode: bool = False
    log_level: str = "INFO"
    auto_save_enabled: bool = True
    language: str = "zh_CN"


@dataclass
class UserPreferences:
    """User preferences and customizations."""
    default_pricing_unit: str = "件"
    default_bank_account: Optional[str] = None
    show_tips: bool = True
    remember_last_values: bool = True
    custom_expense_categories: list = field(default_factory=list)
    workflow_customizations: Dict[str, Any] = field(default_factory=dict)


@dataclass
class AppConfig:
    """Complete application configuration."""
    storage: StorageConfig = field(default_factory=StorageConfig)
    backup: BackupConfig = field(default_factory=BackupConfig)
    system: SystemConfig = field(default_factory=SystemConfig)
    user_preferences: UserPreferences = field(default_factory=UserPreferences)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert configuration to dictionary."""
        return {
            'storage': asdict(self.storage),
            'backup': asdict(self.backup),
            'system': asdict(self.system),
            'user_preferences': asdict(self.user_preferences)
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'AppConfig':
        """Create configuration from dictionary."""
        return cls(
            storage=StorageConfig(**data.get('storage', {})),
            backup=BackupConfig(**data.get('backup', {})),
            system=SystemConfig(**data.get('system', {})),
            user_preferences=UserPreferences(**data.get('user_preferences', {}))
        )


class ConfigManager:
    """
    Configuration Manager
    
    Handles loading, saving, and managing application configuration.
    Supports environment variables and JSON configuration files.
    """
    
    def __init__(self, config_path: str = "./config.json"):
        """
        Initialize configuration manager.
        
        Args:
            config_path: Path to configuration file
        """
        self.config_path = Path(config_path)
        self.config: AppConfig = AppConfig()
        self._load_config()
        self._load_env_overrides()
        self.config.storage.ensure_directories()
    
    def _load_config(self):
        """Load configuration from file."""
        if self.config_path.exists():
            try:
                with open(self.config_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self.config = AppConfig.from_dict(data)
            except Exception as e:
                print(f"Warning: Failed to load config from {self.config_path}: {e}")
                print("Using default configuration.")
    
    def _load_env_overrides(self):
        """Load configuration overrides from environment variables."""
        # Storage paths
        if data_path := os.getenv('DATA_PATH'):
            self.config.storage.data_path = data_path
        if backup_path := os.getenv('BACKUP_PATH'):
            self.config.storage.backup_path = backup_path
        if log_path := os.getenv('LOG_PATH'):
            self.config.storage.log_path = log_path
        
        # Backup settings
        if auto_backup := os.getenv('AUTO_BACKUP_ENABLED'):
            self.config.backup.auto_backup_enabled = auto_backup.lower() == 'true'
        if backup_interval := os.getenv('AUTO_BACKUP_INTERVAL_HOURS'):
            self.config.backup.auto_backup_interval_hours = int(backup_interval)
        
        # System settings
        if demo_mode := os.getenv('DEMO_MODE'):
            self.config.system.demo_mode = demo_mode.lower() == 'true'
        if log_level := os.getenv('LOG_LEVEL'):
            self.config.system.log_level = log_level
    
    def save_config(self):
        """Save current configuration to file."""
        try:
            with open(self.config_path, 'w', encoding='utf-8') as f:
                json.dump(self.config.to_dict(), f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"Error: Failed to save config to {self.config_path}: {e}")
    
    def get(self, key: str, default: Any = None) -> Any:
        """
        Get configuration value by dot-notation key.
        
        Args:
            key: Configuration key (e.g., 'storage.data_path')
            default: Default value if key not found
            
        Returns:
            Configuration value
        """
        parts = key.split('.')
        value = self.config
        
        for part in parts:
            if hasattr(value, part):
                value = getattr(value, part)
            else:
                return default
        
        return value
    
    def set(self, key: str, value: Any):
        """
        Set configuration value by dot-notation key.
        
        Args:
            key: Configuration key (e.g., 'storage.data_path')
            value: Value to set
        """
        parts = key.split('.')
        obj = self.config
        
        for part in parts[:-1]:
            if hasattr(obj, part):
                obj = getattr(obj, part)
            else:
                raise ValueError(f"Invalid configuration key: {key}")
        
        if hasattr(obj, parts[-1]):
            setattr(obj, parts[-1], value)
        else:
            raise ValueError(f"Invalid configuration key: {key}")
    
    def update_user_preference(self, key: str, value: Any):
        """
        Update user preference.
        
        Args:
            key: Preference key
            value: Preference value
        """
        if hasattr(self.config.user_preferences, key):
            setattr(self.config.user_preferences, key, value)
            self.save_config()
        else:
            raise ValueError(f"Invalid user preference key: {key}")
    
    def add_custom_expense_category(self, category: str):
        """
        Add custom expense category.
        
        Args:
            category: Category name
        """
        if category not in self.config.user_preferences.custom_expense_categories:
            self.config.user_preferences.custom_expense_categories.append(category)
            self.save_config()
    
    def get_all_expense_categories(self) -> list:
        """
        Get all expense categories (predefined + custom).
        
        Returns:
            List of expense categories
        """
        predefined = [
            "房租", "水电费", "三酸", "片碱", "亚钠", "色粉", 
            "除油剂", "挂具", "外发加工费用", "日常费用", "工资"
        ]
        custom = self.config.user_preferences.custom_expense_categories
        return predefined + custom
    
    def save_workflow_customization(self, workflow_type: str, customization: Dict[str, Any]):
        """
        Save workflow customization.
        
        Args:
            workflow_type: Type of workflow
            customization: Customization data
        """
        self.config.user_preferences.workflow_customizations[workflow_type] = customization
        self.save_config()
    
    def get_workflow_customization(self, workflow_type: str) -> Optional[Dict[str, Any]]:
        """
        Get workflow customization.
        
        Args:
            workflow_type: Type of workflow
            
        Returns:
            Customization data or None
        """
        return self.config.user_preferences.workflow_customizations.get(workflow_type)


# Global configuration instance
_config_manager: Optional[ConfigManager] = None


def get_config() -> ConfigManager:
    """
    Get global configuration manager instance.
    
    Returns:
        ConfigManager instance
    """
    global _config_manager
    if _config_manager is None:
        _config_manager = ConfigManager()
    return _config_manager
