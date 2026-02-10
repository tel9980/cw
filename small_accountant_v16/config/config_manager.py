"""
Configuration management module

Handles loading, saving, and managing system configuration.
"""

import json
import os
import shutil
from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import List, Optional, Dict, Any
from datetime import datetime


@dataclass
class ReminderConfig:
    """提醒配置"""
    tax_reminder_days: List[int] = field(default_factory=lambda: [7, 3, 1, 0])  # 税务提醒提前天数
    payable_reminder_days: int = 3  # 应付账款提醒提前天数
    receivable_overdue_days: List[int] = field(default_factory=lambda: [30, 60, 90])  # 应收账款逾期天数
    cashflow_warning_days: int = 7  # 现金流预警天数
    enable_desktop_notification: bool = True  # 启用桌面通知
    enable_wechat_notification: bool = False  # 启用企业微信通知
    check_interval_minutes: int = 60  # 检查间隔（分钟）
    
    def validate(self) -> List[str]:
        """验证配置"""
        errors = []
        
        if not self.tax_reminder_days:
            errors.append("税务提醒天数不能为空")
        elif any(d < 0 for d in self.tax_reminder_days):
            errors.append("税务提醒天数不能为负数")
        
        if self.payable_reminder_days < 0:
            errors.append("应付账款提醒天数不能为负数")
        
        if not self.receivable_overdue_days:
            errors.append("应收账款逾期天数不能为空")
        elif any(d <= 0 for d in self.receivable_overdue_days):
            errors.append("应收账款逾期天数必须为正数")
        
        if self.cashflow_warning_days <= 0:
            errors.append("现金流预警天数必须为正数")
        
        if self.check_interval_minutes <= 0:
            errors.append("检查间隔必须为正数")
        
        return errors


@dataclass
class WeChatConfig:
    """企业微信配置"""
    webhook_url: str = ""  # 企业微信webhook地址
    enabled: bool = False  # 是否启用
    timeout_seconds: int = 10  # 请求超时时间（秒）
    retry_count: int = 3  # 重试次数
    
    def validate(self) -> List[str]:
        """验证配置"""
        errors = []
        
        if self.enabled and not self.webhook_url:
            errors.append("启用企业微信通知时必须配置webhook地址")
        
        if self.webhook_url and not self.webhook_url.startswith("https://"):
            errors.append("企业微信webhook地址必须以https://开头")
        
        if self.timeout_seconds <= 0:
            errors.append("超时时间必须为正数")
        
        if self.retry_count < 0:
            errors.append("重试次数不能为负数")
        
        return errors


@dataclass
class StorageConfig:
    """存储配置"""
    data_dir: str = "data"  # 数据目录
    backup_dir: str = "backups"  # 备份目录
    report_output_dir: str = "reports"  # 报表输出目录
    log_dir: str = "logs"  # 日志目录
    use_sqlite: bool = False  # 是否使用SQLite（False则使用JSON）
    auto_backup: bool = True  # 自动备份
    backup_retention_days: int = 30  # 备份保留天数
    max_backup_count: int = 10  # 最大备份数量
    
    def validate(self) -> List[str]:
        """验证配置"""
        errors = []
        
        if not self.data_dir:
            errors.append("数据目录不能为空")
        
        if not self.backup_dir:
            errors.append("备份目录不能为空")
        
        if not self.report_output_dir:
            errors.append("报表输出目录不能为空")
        
        if not self.log_dir:
            errors.append("日志目录不能为空")
        
        if self.backup_retention_days <= 0:
            errors.append("备份保留天数必须为正数")
        
        if self.max_backup_count <= 0:
            errors.append("最大备份数量必须为正数")
        
        return errors


@dataclass
class ReportConfig:
    """报表配置"""
    default_date_format: str = "%Y-%m-%d"  # 默认日期格式
    default_currency: str = "CNY"  # 默认货币
    include_charts: bool = True  # 是否包含图表
    chart_style: str = "default"  # 图表样式
    excel_engine: str = "openpyxl"  # Excel引擎
    
    def validate(self) -> List[str]:
        """验证配置"""
        errors = []
        
        if not self.default_date_format:
            errors.append("日期格式不能为空")
        
        if not self.default_currency:
            errors.append("货币代码不能为空")
        
        if self.excel_engine not in ["openpyxl", "xlsxwriter"]:
            errors.append("Excel引擎必须是openpyxl或xlsxwriter")
        
        return errors


@dataclass
class ImportConfig:
    """导入配置"""
    max_rows: int = 10000  # 最大导入行数
    preview_rows: int = 10  # 预览行数
    auto_detect_encoding: bool = True  # 自动检测编码
    default_encoding: str = "utf-8"  # 默认编码
    skip_empty_rows: bool = True  # 跳过空行
    
    def validate(self) -> List[str]:
        """验证配置"""
        errors = []
        
        if self.max_rows <= 0:
            errors.append("最大导入行数必须为正数")
        
        if self.preview_rows <= 0:
            errors.append("预览行数必须为正数")
        
        if not self.default_encoding:
            errors.append("默认编码不能为空")
        
        return errors


@dataclass
class SystemConfig:
    """系统配置"""
    version: str = "1.6.0"
    reminder: ReminderConfig = field(default_factory=ReminderConfig)
    wechat: WeChatConfig = field(default_factory=WeChatConfig)
    storage: StorageConfig = field(default_factory=StorageConfig)
    report: ReportConfig = field(default_factory=ReportConfig)
    import_config: ImportConfig = field(default_factory=ImportConfig)
    
    def to_dict(self) -> dict:
        """转换为字典"""
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: dict) -> "SystemConfig":
        """从字典创建"""
        return cls(
            version=data.get("version", "1.6.0"),
            reminder=ReminderConfig(**data.get("reminder", {})),
            wechat=WeChatConfig(**data.get("wechat", {})),
            storage=StorageConfig(**data.get("storage", {})),
            report=ReportConfig(**data.get("report", {})),
            import_config=ImportConfig(**data.get("import_config", {})),
        )
    
    def validate(self) -> List[str]:
        """验证所有配置"""
        errors = []
        errors.extend(self.reminder.validate())
        errors.extend(self.wechat.validate())
        errors.extend(self.storage.validate())
        errors.extend(self.report.validate())
        errors.extend(self.import_config.validate())
        return errors


class ConfigManager:
    """配置管理器"""
    
    DEFAULT_CONFIG_FILE = "config.json"
    CONFIG_VERSION = "1.6.0"
    
    def __init__(self, config_file: Optional[str] = None):
        """
        初始化配置管理器
        
        Args:
            config_file: 配置文件路径，如果为None则使用默认路径
        """
        self.config_file = config_file or self.DEFAULT_CONFIG_FILE
        self.config: SystemConfig = SystemConfig()
        self._config_history: List[Dict[str, Any]] = []  # 配置历史
        self._ensure_config_exists()
        self.load_config()
    
    def _ensure_config_exists(self) -> None:
        """确保配置文件存在，如果不存在则创建默认配置"""
        if not os.path.exists(self.config_file):
            self.save_config()
    
    def load_config(self) -> SystemConfig:
        """
        加载配置
        
        Returns:
            SystemConfig: 系统配置对象
            
        Raises:
            ValueError: 配置文件格式错误
        """
        try:
            with open(self.config_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                self.config = SystemConfig.from_dict(data)
                
                # 验证配置
                errors = self.config.validate()
                if errors:
                    print(f"⚠️ 配置验证警告：")
                    for error in errors:
                        print(f"  - {error}")
                    print("将使用默认值继续运行")
                
                # 检查版本并迁移
                if data.get("version") != self.CONFIG_VERSION:
                    self._migrate_config(data.get("version", "1.0.0"))
                
                return self.config
        except FileNotFoundError:
            # 文件不存在，使用默认配置
            self.config = SystemConfig()
            self.save_config()
            return self.config
        except json.JSONDecodeError as e:
            raise ValueError(f"配置文件格式错误: {e}")
        except Exception as e:
            raise ValueError(f"加载配置失败: {e}")
    
    def save_config(self, config: Optional[SystemConfig] = None, create_backup: bool = True) -> None:
        """
        保存配置
        
        Args:
            config: 要保存的配置对象，如果为None则保存当前配置
            create_backup: 是否创建备份
        """
        if config:
            self.config = config
        
        # 验证配置
        errors = self.config.validate()
        if errors:
            raise ValueError(f"配置验证失败：{', '.join(errors)}")
        
        # 创建备份
        if create_backup and os.path.exists(self.config_file):
            self._backup_config()
        
        # 确保配置目录存在
        config_dir = os.path.dirname(self.config_file)
        if config_dir and not os.path.exists(config_dir):
            os.makedirs(config_dir, exist_ok=True)
        
        # 保存配置
        with open(self.config_file, 'w', encoding='utf-8') as f:
            json.dump(self.config.to_dict(), f, ensure_ascii=False, indent=2)
        
        # 记录配置历史
        self._record_config_change()
    
    def _backup_config(self) -> str:
        """
        备份当前配置文件
        
        Returns:
            str: 备份文件路径
        """
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_file = f"{self.config_file}.backup_{timestamp}"
        shutil.copy2(self.config_file, backup_file)
        
        # 清理旧备份
        self._cleanup_old_backups()
        
        return backup_file
    
    def _cleanup_old_backups(self) -> None:
        """清理旧的配置备份"""
        backup_pattern = f"{self.config_file}.backup_*"
        backup_files = sorted(Path(os.path.dirname(self.config_file) or ".").glob(os.path.basename(backup_pattern)))
        
        # 保留最近的10个备份
        max_backups = 10
        if len(backup_files) > max_backups:
            for old_backup in backup_files[:-max_backups]:
                try:
                    old_backup.unlink()
                except Exception:
                    pass
    
    def restore_from_backup(self, backup_file: str) -> None:
        """
        从备份恢复配置
        
        Args:
            backup_file: 备份文件路径
        """
        if not os.path.exists(backup_file):
            raise FileNotFoundError(f"备份文件不存在：{backup_file}")
        
        # 备份当前配置
        self._backup_config()
        
        # 恢复备份
        shutil.copy2(backup_file, self.config_file)
        
        # 重新加载配置
        self.load_config()
    
    def list_backups(self) -> List[str]:
        """
        列出所有配置备份
        
        Returns:
            List[str]: 备份文件列表
        """
        backup_pattern = f"{self.config_file}.backup_*"
        backup_files = sorted(
            Path(os.path.dirname(self.config_file) or ".").glob(os.path.basename(backup_pattern)),
            reverse=True
        )
        return [str(f) for f in backup_files]
    
    def _record_config_change(self) -> None:
        """记录配置变更"""
        change_record = {
            "timestamp": datetime.now().isoformat(),
            "config": self.config.to_dict()
        }
        self._config_history.append(change_record)
        
        # 只保留最近50条记录
        if len(self._config_history) > 50:
            self._config_history = self._config_history[-50:]
    
    def _migrate_config(self, from_version: str) -> None:
        """
        迁移配置到新版本
        
        Args:
            from_version: 原版本号
        """
        print(f"正在迁移配置从版本 {from_version} 到 {self.CONFIG_VERSION}...")
        
        # 这里可以添加版本迁移逻辑
        # 例如：添加新字段、重命名字段、转换数据格式等
        
        self.config.version = self.CONFIG_VERSION
        self.save_config(create_backup=True)
        print("配置迁移完成")
    
    def get_config(self) -> SystemConfig:
        """
        获取当前配置
        
        Returns:
            SystemConfig: 当前系统配置
        """
        return self.config
    
    def reset_to_default(self) -> None:
        """重置为默认配置"""
        # 备份当前配置
        self._backup_config()
        
        # 重置为默认
        self.config = SystemConfig()
        self.save_config(create_backup=False)
    
    def export_config(self, export_file: str) -> None:
        """
        导出配置到文件
        
        Args:
            export_file: 导出文件路径
        """
        with open(export_file, 'w', encoding='utf-8') as f:
            json.dump(self.config.to_dict(), f, ensure_ascii=False, indent=2)
    
    def import_config(self, import_file: str) -> None:
        """
        从文件导入配置
        
        Args:
            import_file: 导入文件路径
        """
        if not os.path.exists(import_file):
            raise FileNotFoundError(f"导入文件不存在：{import_file}")
        
        with open(import_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
            config = SystemConfig.from_dict(data)
            
            # 验证配置
            errors = config.validate()
            if errors:
                raise ValueError(f"导入的配置无效：{', '.join(errors)}")
            
            # 保存配置
            self.save_config(config, create_backup=True)
    
    def update_reminder_config(self, **kwargs) -> None:
        """
        更新提醒配置
        
        Args:
            **kwargs: 要更新的配置项
        """
        for key, value in kwargs.items():
            if hasattr(self.config.reminder, key):
                setattr(self.config.reminder, key, value)
        self.save_config()
    
    def update_wechat_config(self, webhook_url: str = None, enabled: bool = None, **kwargs) -> None:
        """
        更新企业微信配置
        
        Args:
            webhook_url: webhook地址
            enabled: 是否启用
            **kwargs: 其他配置项
        """
        if webhook_url is not None:
            self.config.wechat.webhook_url = webhook_url
        if enabled is not None:
            self.config.wechat.enabled = enabled
        
        for key, value in kwargs.items():
            if hasattr(self.config.wechat, key):
                setattr(self.config.wechat, key, value)
        
        self.save_config()
    
    def update_storage_config(self, **kwargs) -> None:
        """
        更新存储配置
        
        Args:
            **kwargs: 要更新的配置项
        """
        for key, value in kwargs.items():
            if hasattr(self.config.storage, key):
                setattr(self.config.storage, key, value)
        self.save_config()
    
    def update_report_config(self, **kwargs) -> None:
        """
        更新报表配置
        
        Args:
            **kwargs: 要更新的配置项
        """
        for key, value in kwargs.items():
            if hasattr(self.config.report, key):
                setattr(self.config.report, key, value)
        self.save_config()
    
    def update_import_config(self, **kwargs) -> None:
        """
        更新导入配置
        
        Args:
            **kwargs: 要更新的配置项
        """
        for key, value in kwargs.items():
            if hasattr(self.config.import_config, key):
                setattr(self.config.import_config, key, value)
        self.save_config()
    
    def ensure_directories(self) -> None:
        """确保所有必需的目录存在"""
        directories = [
            self.config.storage.data_dir,
            self.config.storage.backup_dir,
            self.config.storage.report_output_dir,
            self.config.storage.log_dir,
        ]
        
        for directory in directories:
            if not os.path.exists(directory):
                os.makedirs(directory, exist_ok=True)
    
    def get_config_summary(self) -> Dict[str, Any]:
        """
        获取配置摘要
        
        Returns:
            Dict[str, Any]: 配置摘要信息
        """
        return {
            "version": self.config.version,
            "reminder": {
                "desktop_enabled": self.config.reminder.enable_desktop_notification,
                "wechat_enabled": self.config.reminder.enable_wechat_notification,
                "check_interval": f"{self.config.reminder.check_interval_minutes}分钟",
            },
            "wechat": {
                "enabled": self.config.wechat.enabled,
                "configured": bool(self.config.wechat.webhook_url),
            },
            "storage": {
                "data_dir": self.config.storage.data_dir,
                "auto_backup": self.config.storage.auto_backup,
                "use_sqlite": self.config.storage.use_sqlite,
            },
            "report": {
                "include_charts": self.config.report.include_charts,
                "currency": self.config.report.default_currency,
            },
            "import": {
                "max_rows": self.config.import_config.max_rows,
                "auto_detect_encoding": self.config.import_config.auto_detect_encoding,
            }
        }
