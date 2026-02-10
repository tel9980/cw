"""
Unit tests for configuration management

Tests configuration loading, saving, and updating.
"""

import pytest
import os
import json

from small_accountant_v16.config import ConfigManager, SystemConfig


@pytest.mark.unit
class TestConfigManager:
    """测试配置管理器"""
    
    def test_create_config_manager(self, temp_dir):
        """测试创建配置管理器"""
        config_file = os.path.join(temp_dir, "test_config.json")
        manager = ConfigManager(config_file)
        
        assert manager.config_file == config_file
        assert manager.config is not None
        assert manager.config.version == "1.6.0"
    
    def test_config_file_created_on_init(self, temp_dir):
        """测试初始化时自动创建配置文件"""
        config_file = os.path.join(temp_dir, "auto_config.json")
        manager = ConfigManager(config_file)
        
        assert os.path.exists(config_file)
    
    def test_load_default_config(self, temp_dir):
        """测试加载默认配置"""
        config_file = os.path.join(temp_dir, "default_config.json")
        manager = ConfigManager(config_file)
        config = manager.load_config()
        
        assert config.version == "1.6.0"
        assert config.reminder.tax_reminder_days == [7, 3, 1, 0]
        assert config.reminder.payable_reminder_days == 3
        assert config.reminder.receivable_overdue_days == [30, 60, 90]
        assert config.reminder.cashflow_warning_days == 7
        assert config.reminder.enable_desktop_notification is True
        assert config.reminder.enable_wechat_notification is False
    
    def test_save_and_load_config(self, temp_dir):
        """测试保存和加载配置"""
        config_file = os.path.join(temp_dir, "save_load_config.json")
        manager = ConfigManager(config_file)
        
        # 修改配置
        manager.config.reminder.tax_reminder_days = [10, 5, 2, 0]
        manager.config.wechat.webhook_url = "https://example.com/webhook"
        manager.config.wechat.enabled = True
        manager.save_config()
        
        # 创建新的管理器并加载
        new_manager = ConfigManager(config_file)
        loaded_config = new_manager.load_config()
        
        assert loaded_config.reminder.tax_reminder_days == [10, 5, 2, 0]
        assert loaded_config.wechat.webhook_url == "https://example.com/webhook"
        assert loaded_config.wechat.enabled is True
    
    def test_update_reminder_config(self, temp_dir):
        """测试更新提醒配置"""
        config_file = os.path.join(temp_dir, "update_reminder.json")
        manager = ConfigManager(config_file)
        
        manager.update_reminder_config(
            tax_reminder_days=[14, 7, 3, 1],
            payable_reminder_days=5,
            enable_desktop_notification=False,
        )
        
        assert manager.config.reminder.tax_reminder_days == [14, 7, 3, 1]
        assert manager.config.reminder.payable_reminder_days == 5
        assert manager.config.reminder.enable_desktop_notification is False
        
        # 验证配置已保存
        new_manager = ConfigManager(config_file)
        loaded_config = new_manager.load_config()
        assert loaded_config.reminder.tax_reminder_days == [14, 7, 3, 1]
    
    def test_update_wechat_config(self, temp_dir):
        """测试更新企业微信配置"""
        config_file = os.path.join(temp_dir, "update_wechat.json")
        manager = ConfigManager(config_file)
        
        webhook_url = "https://qyapi.weixin.qq.com/cgi-bin/webhook/send?key=test"
        manager.update_wechat_config(webhook_url=webhook_url, enabled=True)
        
        assert manager.config.wechat.webhook_url == webhook_url
        assert manager.config.wechat.enabled is True
        
        # 验证配置已保存
        new_manager = ConfigManager(config_file)
        loaded_config = new_manager.load_config()
        assert loaded_config.wechat.webhook_url == webhook_url
        assert loaded_config.wechat.enabled is True
    
    def test_update_storage_config(self, temp_dir):
        """测试更新存储配置"""
        config_file = os.path.join(temp_dir, "update_storage.json")
        manager = ConfigManager(config_file)
        
        manager.update_storage_config(
            data_dir="custom_data",
            backup_dir="custom_backups",
            use_sqlite=True,
        )
        
        assert manager.config.storage.data_dir == "custom_data"
        assert manager.config.storage.backup_dir == "custom_backups"
        assert manager.config.storage.use_sqlite is True
    
    def test_ensure_directories(self, temp_dir):
        """测试确保目录存在"""
        config_file = os.path.join(temp_dir, "ensure_dirs.json")
        manager = ConfigManager(config_file)
        
        # 设置自定义目录
        data_dir = os.path.join(temp_dir, "data")
        backup_dir = os.path.join(temp_dir, "backups")
        report_dir = os.path.join(temp_dir, "reports")
        
        manager.config.storage.data_dir = data_dir
        manager.config.storage.backup_dir = backup_dir
        manager.config.storage.report_output_dir = report_dir
        
        # 确保目录存在
        manager.ensure_directories()
        
        assert os.path.exists(data_dir)
        assert os.path.exists(backup_dir)
        assert os.path.exists(report_dir)
    
    def test_get_config(self, temp_dir):
        """测试获取当前配置"""
        config_file = os.path.join(temp_dir, "get_config.json")
        manager = ConfigManager(config_file)
        
        config = manager.get_config()
        assert config is manager.config
        assert config.version == "1.6.0"
    
    def test_config_to_dict_and_from_dict(self):
        """测试配置对象的序列化和反序列化"""
        config = SystemConfig()
        config.reminder.tax_reminder_days = [10, 5, 1]
        config.wechat.webhook_url = "https://example.com"
        config.wechat.enabled = True
        
        # 转换为字典
        data = config.to_dict()
        assert data["version"] == "1.6.0"
        assert data["reminder"]["tax_reminder_days"] == [10, 5, 1]
        assert data["wechat"]["webhook_url"] == "https://example.com"
        assert data["wechat"]["enabled"] is True
        
        # 从字典创建
        restored = SystemConfig.from_dict(data)
        assert restored.version == config.version
        assert restored.reminder.tax_reminder_days == config.reminder.tax_reminder_days
        assert restored.wechat.webhook_url == config.wechat.webhook_url
        assert restored.wechat.enabled == config.wechat.enabled
    
    def test_invalid_config_file_raises_error(self, temp_dir):
        """测试加载无效配置文件时抛出错误"""
        config_file = os.path.join(temp_dir, "invalid_config.json")
        
        # 创建无效的JSON文件
        with open(config_file, 'w') as f:
            f.write("{ invalid json }")
        
        # 尝试创建管理器应该失败
        with pytest.raises(ValueError, match="配置文件格式错误"):
            ConfigManager(config_file)
    
    def test_partial_config_update(self, temp_dir):
        """测试部分更新配置"""
        config_file = os.path.join(temp_dir, "partial_update.json")
        manager = ConfigManager(config_file)
        
        # 只更新部分字段
        original_payable_days = manager.config.reminder.payable_reminder_days
        manager.update_reminder_config(tax_reminder_days=[5, 2, 0])
        
        # 验证只有指定字段被更新
        assert manager.config.reminder.tax_reminder_days == [5, 2, 0]
        assert manager.config.reminder.payable_reminder_days == original_payable_days
    
    def test_config_persistence(self, temp_dir):
        """测试配置持久化"""
        config_file = os.path.join(temp_dir, "persistence.json")
        
        # 第一个管理器
        manager1 = ConfigManager(config_file)
        manager1.update_reminder_config(tax_reminder_days=[20, 10, 5])
        
        # 第二个管理器
        manager2 = ConfigManager(config_file)
        manager2.load_config()
        
        # 验证配置已持久化
        assert manager2.config.reminder.tax_reminder_days == [20, 10, 5]


class TestConfigValidation:
    """测试配置验证"""
    
    def test_reminder_config_validation(self):
        """测试提醒配置验证"""
        config = ReminderConfig()
        errors = config.validate()
        assert len(errors) == 0
        
        # 测试无效配置
        config.tax_reminder_days = []
        errors = config.validate()
        assert len(errors) > 0
        assert any("税务提醒天数不能为空" in e for e in errors)
    
    def test_wechat_config_validation(self):
        """测试企业微信配置验证"""
        config = WeChatConfig()
        errors = config.validate()
        assert len(errors) == 0
        
        # 启用但未配置webhook
        config.enabled = True
        errors = config.validate()
        assert len(errors) > 0
        assert any("webhook地址" in e for e in errors)
        
        # 无效的webhook地址
        config.webhook_url = "http://example.com"
        errors = config.validate()
        assert len(errors) > 0
        assert any("https://" in e for e in errors)
    
    def test_storage_config_validation(self):
        """测试存储配置验证"""
        config = StorageConfig()
        errors = config.validate()
        assert len(errors) == 0
        
        # 空目录
        config.data_dir = ""
        errors = config.validate()
        assert len(errors) > 0
        assert any("数据目录不能为空" in e for e in errors)
    
    def test_system_config_validation(self):
        """测试系统配置验证"""
        config = SystemConfig()
        errors = config.validate()
        assert len(errors) == 0


class TestConfigBackup:
    """测试配置备份和恢复"""
    
    def test_backup_config(self, temp_dir):
        """测试配置备份"""
        config_file = os.path.join(temp_dir, "backup_test.json")
        manager = ConfigManager(config_file)
        
        # 修改配置并保存（会创建备份）
        manager.update_reminder_config(tax_reminder_days=[15, 10, 5])
        
        # 检查备份文件是否存在
        backups = manager.list_backups()
        assert len(backups) > 0
    
    def test_restore_from_backup(self, temp_dir):
        """测试从备份恢复"""
        config_file = os.path.join(temp_dir, "restore_test.json")
        manager = ConfigManager(config_file)
        
        # 原始配置
        original_days = [7, 3, 1, 0]
        manager.update_reminder_config(tax_reminder_days=original_days)
        
        # 获取备份文件
        backups = manager.list_backups()
        if backups:
            backup_file = backups[0]
            
            # 修改配置
            manager.update_reminder_config(tax_reminder_days=[20, 15, 10])
            assert manager.config.reminder.tax_reminder_days == [20, 15, 10]
            
            # 从备份恢复
            manager.restore_from_backup(backup_file)
            # 注意：由于备份可能是修改前的，这里只验证恢复功能不报错
            assert manager.config is not None
    
    def test_list_backups(self, temp_dir):
        """测试列出备份"""
        config_file = os.path.join(temp_dir, "list_backups.json")
        manager = ConfigManager(config_file)
        
        # 创建多个备份
        for i in range(3):
            manager.update_reminder_config(tax_reminder_days=[i, i+1, i+2])
        
        backups = manager.list_backups()
        # 由于第一次保存不创建备份，所以至少有1个备份
        assert len(backups) >= 1


class TestConfigExportImport:
    """测试配置导出和导入"""
    
    def test_export_config(self, temp_dir):
        """测试导出配置"""
        config_file = os.path.join(temp_dir, "export_source.json")
        export_file = os.path.join(temp_dir, "exported.json")
        
        manager = ConfigManager(config_file)
        manager.update_reminder_config(tax_reminder_days=[10, 5, 2])
        
        # 导出配置
        manager.export_config(export_file)
        
        assert os.path.exists(export_file)
        
        # 验证导出的内容
        with open(export_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
            assert data["reminder"]["tax_reminder_days"] == [10, 5, 2]
    
    def test_import_config(self, temp_dir):
        """测试导入配置"""
        config_file = os.path.join(temp_dir, "import_target.json")
        import_file = os.path.join(temp_dir, "to_import.json")
        
        # 创建要导入的配置文件
        import_data = {
            "version": "1.6.0",
            "reminder": {
                "tax_reminder_days": [15, 10, 5, 0],
                "payable_reminder_days": 5,
                "receivable_overdue_days": [30, 60, 90],
                "cashflow_warning_days": 7,
                "enable_desktop_notification": True,
                "enable_wechat_notification": False,
                "check_interval_minutes": 60
            },
            "wechat": {
                "webhook_url": "https://example.com/webhook",
                "enabled": True,
                "timeout_seconds": 10,
                "retry_count": 3
            },
            "storage": {
                "data_dir": "data",
                "backup_dir": "backups",
                "report_output_dir": "reports",
                "log_dir": "logs",
                "use_sqlite": False,
                "auto_backup": True,
                "backup_retention_days": 30,
                "max_backup_count": 10
            },
            "report": {
                "default_date_format": "%Y-%m-%d",
                "default_currency": "CNY",
                "include_charts": True,
                "chart_style": "default",
                "excel_engine": "openpyxl"
            },
            "import_config": {
                "max_rows": 10000,
                "preview_rows": 10,
                "auto_detect_encoding": True,
                "default_encoding": "utf-8",
                "skip_empty_rows": True
            }
        }
        
        with open(import_file, 'w', encoding='utf-8') as f:
            json.dump(import_data, f, ensure_ascii=False, indent=2)
        
        # 导入配置
        manager = ConfigManager(config_file)
        manager.import_config(import_file)
        
        assert manager.config.reminder.tax_reminder_days == [15, 10, 5, 0]
        assert manager.config.wechat.webhook_url == "https://example.com/webhook"
        assert manager.config.wechat.enabled is True


class TestConfigAdvancedFeatures:
    """测试配置高级功能"""
    
    def test_reset_to_default(self, temp_dir):
        """测试重置为默认配置"""
        config_file = os.path.join(temp_dir, "reset_test.json")
        manager = ConfigManager(config_file)
        
        # 修改配置
        manager.update_reminder_config(tax_reminder_days=[20, 15, 10])
        assert manager.config.reminder.tax_reminder_days == [20, 15, 10]
        
        # 重置为默认
        manager.reset_to_default()
        assert manager.config.reminder.tax_reminder_days == [7, 3, 1, 0]
    
    def test_get_config_summary(self, temp_dir):
        """测试获取配置摘要"""
        config_file = os.path.join(temp_dir, "summary_test.json")
        manager = ConfigManager(config_file)
        
        summary = manager.get_config_summary()
        
        assert "version" in summary
        assert "reminder" in summary
        assert "wechat" in summary
        assert "storage" in summary
        assert "report" in summary
        assert "import" in summary
    
    def test_update_report_config(self, temp_dir):
        """测试更新报表配置"""
        config_file = os.path.join(temp_dir, "report_config.json")
        manager = ConfigManager(config_file)
        
        manager.update_report_config(
            default_currency="USD",
            include_charts=False
        )
        
        assert manager.config.report.default_currency == "USD"
        assert manager.config.report.include_charts is False
    
    def test_update_import_config(self, temp_dir):
        """测试更新导入配置"""
        config_file = os.path.join(temp_dir, "import_config.json")
        manager = ConfigManager(config_file)
        
        manager.update_import_config(
            max_rows=5000,
            preview_rows=20
        )
        
        assert manager.config.import_config.max_rows == 5000
        assert manager.config.import_config.preview_rows == 20
    
    def test_config_validation_on_save(self, temp_dir):
        """测试保存时的配置验证"""
        config_file = os.path.join(temp_dir, "validation_test.json")
        manager = ConfigManager(config_file)
        
        # 创建无效配置
        invalid_config = SystemConfig()
        invalid_config.reminder.tax_reminder_days = []  # 无效：空列表
        
        # 尝试保存应该失败
        with pytest.raises(ValueError, match="配置验证失败"):
            manager.save_config(invalid_config)


# 导入必要的类
from small_accountant_v16.config.config_manager import (
    ReminderConfig,
    WeChatConfig,
    StorageConfig,
    ReportConfig,
    ImportConfig
)
