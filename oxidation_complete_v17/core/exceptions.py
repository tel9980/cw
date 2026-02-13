"""
自定义异常类

定义系统中使用的所有自定义异常，提供用户友好的中文错误消息
"""

from typing import Optional, Dict, Any


class SmallAccountantError(Exception):
    """小会计系统基础异常类"""
    
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        self.message = message
        self.details = details or {}
        super().__init__(self.message)
    
    def __str__(self):
        return self.message
    
    def get_user_message(self) -> str:
        """获取用户友好的错误消息"""
        return self.message


# ============================================================================
# 报表生成相关异常
# ============================================================================

class ReportGenerationError(SmallAccountantError):
    """报表生成错误"""
    pass


class InsufficientDataError(ReportGenerationError):
    """数据不足错误"""
    
    def __init__(self, report_type: str, missing_data: str):
        message = f"生成{report_type}报表失败：缺少必要数据 - {missing_data}"
        super().__init__(message, {"report_type": report_type, "missing_data": missing_data})


class InvalidDateRangeError(ReportGenerationError):
    """无效日期范围错误"""
    
    def __init__(self, start_date: str, end_date: str):
        message = f"日期范围无效：开始日期({start_date})不能晚于结束日期({end_date})"
        super().__init__(message, {"start_date": start_date, "end_date": end_date})


class TemplateLoadError(ReportGenerationError):
    """模板加载错误"""
    
    def __init__(self, template_name: str, reason: str = ""):
        message = f"加载报表模板失败：{template_name}"
        if reason:
            message += f" - {reason}"
        super().__init__(message, {"template_name": template_name, "reason": reason})


class ChartGenerationError(ReportGenerationError):
    """图表生成错误"""
    
    def __init__(self, chart_type: str, reason: str = ""):
        message = f"生成图表失败：{chart_type}"
        if reason:
            message += f" - {reason}"
        super().__init__(message, {"chart_type": chart_type, "reason": reason})


# ============================================================================
# 提醒系统相关异常
# ============================================================================

class ReminderError(SmallAccountantError):
    """提醒系统错误"""
    pass


class NotificationDeliveryError(ReminderError):
    """通知发送错误"""
    
    def __init__(self, channel: str, reason: str = ""):
        message = f"发送{channel}通知失败"
        if reason:
            message += f"：{reason}"
        super().__init__(message, {"channel": channel, "reason": reason})


class InvalidReminderConfigError(ReminderError):
    """无效提醒配置错误"""
    
    def __init__(self, config_key: str, reason: str = ""):
        message = f"提醒配置无效：{config_key}"
        if reason:
            message += f" - {reason}"
        super().__init__(message, {"config_key": config_key, "reason": reason})


class CollectionLetterError(ReminderError):
    """催款函生成错误"""
    
    def __init__(self, customer_name: str, reason: str = ""):
        message = f"生成催款函失败：客户 {customer_name}"
        if reason:
            message += f" - {reason}"
        super().__init__(message, {"customer_name": customer_name, "reason": reason})


# ============================================================================
# 对账相关异常
# ============================================================================

class ReconciliationError(SmallAccountantError):
    """对账错误"""
    pass


class InvalidExcelFormatError(ReconciliationError):
    """无效Excel格式错误"""
    
    def __init__(self, file_path: str, reason: str = ""):
        message = f"Excel文件格式无效：{file_path}"
        if reason:
            message += f"\n原因：{reason}"
        message += "\n\n请确保文件是有效的Excel格式(.xlsx或.xls)"
        super().__init__(message, {"file_path": file_path, "reason": reason})


class ColumnRecognitionError(ReconciliationError):
    """列识别错误"""
    
    def __init__(self, file_path: str, missing_columns: list):
        columns_str = "、".join(missing_columns)
        message = f"无法识别Excel文件中的必要列：{columns_str}\n"
        message += f"文件：{file_path}\n"
        message += "请手动指定列映射或调整Excel文件格式"
        super().__init__(message, {"file_path": file_path, "missing_columns": missing_columns})


class MatchingError(ReconciliationError):
    """匹配错误"""
    
    def __init__(self, reason: str = ""):
        message = "对账匹配过程出现错误"
        if reason:
            message += f"：{reason}"
        super().__init__(message, {"reason": reason})


# ============================================================================
# 导入相关异常
# ============================================================================

class ImportError(SmallAccountantError):
    """导入错误"""
    pass


class FileReadError(ImportError):
    """文件读取错误"""
    
    def __init__(self, file_path: str, reason: str = ""):
        message = f"无法读取文件：{file_path}"
        if reason:
            message += f"\n原因：{reason}"
        message += "\n\n请确保：\n1. 文件存在且未被其他程序占用\n2. 文件格式正确(.xlsx或.xls)\n3. 您有读取该文件的权限"
        super().__init__(message, {"file_path": file_path, "reason": reason})


class ValidationError(ImportError):
    """数据验证错误"""
    
    def __init__(self, errors: list):
        error_count = len(errors)
        message = f"数据验证失败，发现 {error_count} 个错误：\n"
        for i, error in enumerate(errors[:5], 1):  # 只显示前5个错误
            message += f"{i}. {error}\n"
        if error_count > 5:
            message += f"... 还有 {error_count - 5} 个错误"
        super().__init__(message, {"errors": errors, "error_count": error_count})


class DuplicateRecordError(ImportError):
    """重复记录错误"""
    
    def __init__(self, record_type: str, duplicate_count: int):
        message = f"发现 {duplicate_count} 条重复的{record_type}记录\n"
        message += "请选择处理方式：\n1. 跳过重复记录\n2. 更新现有记录\n3. 全部导入为新记录"
        super().__init__(message, {"record_type": record_type, "duplicate_count": duplicate_count})


class UndoError(ImportError):
    """撤销导入错误"""
    
    def __init__(self, import_id: str, reason: str = ""):
        message = f"无法撤销导入操作：{import_id}"
        if reason:
            message += f"\n原因：{reason}"
        super().__init__(message, {"import_id": import_id, "reason": reason})


# ============================================================================
# 存储相关异常
# ============================================================================

class StorageError(SmallAccountantError):
    """存储错误"""
    pass


class DataNotFoundError(StorageError):
    """数据未找到错误"""
    
    def __init__(self, data_type: str, identifier: str):
        message = f"未找到{data_type}：{identifier}"
        super().__init__(message, {"data_type": data_type, "identifier": identifier})


class DataCorruptionError(StorageError):
    """数据损坏错误"""
    
    def __init__(self, file_path: str, reason: str = ""):
        message = f"数据文件已损坏：{file_path}"
        if reason:
            message += f"\n原因：{reason}"
        message += "\n\n建议：\n1. 尝试从备份恢复\n2. 联系技术支持"
        super().__init__(message, {"file_path": file_path, "reason": reason})


class DataIntegrityError(StorageError):
    """数据完整性错误"""
    
    def __init__(self, reason: str):
        message = f"数据完整性检查失败：{reason}\n"
        message += "操作已回滚，数据未被修改"
        super().__init__(message, {"reason": reason})


# ============================================================================
# 配置相关异常
# ============================================================================

class ConfigurationError(SmallAccountantError):
    """配置错误"""
    pass


class InvalidConfigError(ConfigurationError):
    """无效配置错误"""
    
    def __init__(self, config_key: str, reason: str = ""):
        message = f"配置项无效：{config_key}"
        if reason:
            message += f" - {reason}"
        super().__init__(message, {"config_key": config_key, "reason": reason})


class ConfigLoadError(ConfigurationError):
    """配置加载错误"""
    
    def __init__(self, config_file: str, reason: str = ""):
        message = f"加载配置文件失败：{config_file}"
        if reason:
            message += f"\n原因：{reason}"
        message += "\n\n将使用默认配置"
        super().__init__(message, {"config_file": config_file, "reason": reason})


class ConfigSaveError(ConfigurationError):
    """配置保存错误"""
    
    def __init__(self, config_file: str, reason: str = ""):
        message = f"保存配置文件失败：{config_file}"
        if reason:
            message += f"\n原因：{reason}"
        super().__init__(message, {"config_file": config_file, "reason": reason})
