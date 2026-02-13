"""
Unit tests for ConfigManager.

Tests configuration loading, saving, and management functionality.
"""

import pytest
import json
from pathlib import Path
from oxidation_workflow_v18.config import ConfigManager


@pytest.mark.unit
class TestConfigManager:
    """Test suite for ConfigManager."""
    
    def test_default_config_creation(self, temp_dir):
        """Test that default configuration is created correctly."""
        config_path = temp_dir / "config.json"
        config = ConfigManager(str(config_path))
        
        assert config.config.storage.data_path == "./data"
        assert config.config.backup.auto_backup_enabled is True
        assert config.config.system.demo_mode is False
        assert config.config.user_preferences.show_tips is True
    
    def test_config_save_and_load(self, temp_dir):
        """Test saving and loading configuration."""
        config_path = temp_dir / "config.json"
        
        # Create and modify config
        config1 = ConfigManager(str(config_path))
        config1.set('storage.data_path', '/custom/path')
        config1.set('system.demo_mode', True)
        config1.save_config()
        
        # Load config in new instance
        config2 = ConfigManager(str(config_path))
        assert config2.get('storage.data_path') == '/custom/path'
        assert config2.get('system.demo_mode') is True
    
    def test_get_config_value(self, test_config):
        """Test getting configuration values by dot notation."""
        assert test_config.get('storage.data_path') is not None
        assert test_config.get('backup.auto_backup_enabled') is True
        assert test_config.get('nonexistent.key', 'default') == 'default'
    
    def test_set_config_value(self, test_config):
        """Test setting configuration values by dot notation."""
        test_config.set('backup.max_backup_count', 50)
        assert test_config.get('backup.max_backup_count') == 50
        
        with pytest.raises(ValueError):
            test_config.set('invalid.key', 'value')
    
    def test_update_user_preference(self, test_config):
        """Test updating user preferences."""
        test_config.update_user_preference('show_tips', False)
        assert test_config.config.user_preferences.show_tips is False
        
        with pytest.raises(ValueError):
            test_config.update_user_preference('invalid_key', 'value')
    
    def test_add_custom_expense_category(self, test_config):
        """Test adding custom expense categories."""
        test_config.add_custom_expense_category('测试类别')
        categories = test_config.get_all_expense_categories()
        
        assert '测试类别' in categories
        assert '房租' in categories  # Predefined category
        
        # Adding duplicate should not create duplicate
        test_config.add_custom_expense_category('测试类别')
        categories = test_config.get_all_expense_categories()
        assert categories.count('测试类别') == 1
    
    def test_get_all_expense_categories(self, test_config):
        """Test getting all expense categories."""
        categories = test_config.get_all_expense_categories()
        
        # Check predefined categories
        predefined = ["房租", "水电费", "三酸", "片碱", "亚钠", "色粉", 
                     "除油剂", "挂具", "外发加工费用", "日常费用", "工资"]
        for cat in predefined:
            assert cat in categories
    
    def test_workflow_customization(self, test_config):
        """Test saving and retrieving workflow customizations."""
        customization = {
            'skip_steps': ['step1', 'step2'],
            'default_values': {'field1': 'value1'}
        }
        
        test_config.save_workflow_customization('morning_routine', customization)
        retrieved = test_config.get_workflow_customization('morning_routine')
        
        assert retrieved == customization
        assert test_config.get_workflow_customization('nonexistent') is None
    
    def test_ensure_directories(self, temp_dir):
        """Test that storage directories are created."""
        config_path = temp_dir / "config.json"
        config = ConfigManager(str(config_path))
        
        config.config.storage.data_path = str(temp_dir / "test_data")
        config.config.storage.backup_path = str(temp_dir / "test_backups")
        config.config.storage.log_path = str(temp_dir / "test_logs")
        
        config.config.storage.ensure_directories()
        
        assert (temp_dir / "test_data").exists()
        assert (temp_dir / "test_backups").exists()
        assert (temp_dir / "test_logs").exists()
    
    def test_config_to_dict(self, test_config):
        """Test converting configuration to dictionary."""
        config_dict = test_config.config.to_dict()
        
        assert 'storage' in config_dict
        assert 'backup' in config_dict
        assert 'system' in config_dict
        assert 'user_preferences' in config_dict
        
        assert config_dict['storage']['data_path'] is not None
        assert isinstance(config_dict['backup']['auto_backup_enabled'], bool)
    
    def test_config_from_dict(self):
        """Test creating configuration from dictionary."""
        data = {
            'storage': {'data_path': '/test/path'},
            'backup': {'auto_backup_enabled': False},
            'system': {'demo_mode': True},
            'user_preferences': {'show_tips': False}
        }
        
        from oxidation_workflow_v18.config.config_manager import AppConfig
        config = AppConfig.from_dict(data)
        
        assert config.storage.data_path == '/test/path'
        assert config.backup.auto_backup_enabled is False
        assert config.system.demo_mode is True
        assert config.user_preferences.show_tips is False
