"""
错误处理器测试

测试统一错误处理、日志记录和优雅降级功能
"""

import pytest
import os
import tempfile
import shutil
from pathlib import Path
from datetime import datetime

from small_accountant_v16.core.error_handler import (
    ErrorHandler,
    get_error_handler,
    log_error,
    log_warning,
    log_info,
    handle_error,
    with_error_handling,
    safe_execute
)
from small_accountant_v16.core.exceptions import (
    SmallAccountantError,
    ReportGenerationError,
    InsufficientDataError,
    InvalidDateRangeError,
    NotificationDeliveryError,
    InvalidExcelFormatError,
    FileReadError,
    ValidationError
)


@pytest.fixture
def temp_log_dir():
    """创建临时日志目录"""
    temp_dir = tempfile.mkdtemp()
    yield temp_dir
    shutil.rmtree(temp_dir, ignore_errors=True)


@pytest.fixture
def error_handler(temp_log_dir):
    """创建错误处理器实例"""
    return ErrorHandler(log_dir=temp_log_dir)


class TestErrorHandler:
    """测试ErrorHandler类"""
    
    def test_initialization(self, temp_log_dir):
        """测试错误处理器初始化"""
        handler = ErrorHandler(log_dir=temp_log_dir)
        
        assert handler.log_dir == Path(temp_log_dir)
        assert handler.log_dir.exists()
        assert handler.logger is not None
    
    def test_log_dir_creation(self, temp_log_dir):
        """测试日志目录自动创建"""
        log_path = os.path.join(temp_log_dir, "nested", "logs")
        handler = ErrorHandler(log_dir=log_path)
        
        assert Path(log_path).exists()
    
    def test_log_file_creation(self, error_handler, temp_log_dir):
        """测试日志文件创建"""
        error_handler.log_info("测试消息")
        
        # 检查日志文件是否创建
        log_files = list(Path(temp_log_dir).glob("*.log"))
        assert len(log_files) > 0
        
        # 检查日志文件名格式
        log_file = log_files[0]
        today = datetime.now().strftime('%Y%m%d')
        assert today in log_file.name


class TestLogging:
    """测试日志记录功能"""
    
    def test_log_error(self, error_handler):
        """测试错误日志记录"""
        error = ValueError("测试错误")
        context = {"key": "value"}
        
        # 不应该抛出异常
        error_handler.log_error(error, context)
    
    def test_log_error_with_traceback(self, error_handler):
        """测试带堆栈跟踪的错误日志"""
        try:
            raise RuntimeError("测试运行时错误")
        except RuntimeError as e:
            # 不应该抛出异常
            error_handler.log_error(e, include_traceback=True)
    
    def test_log_warning(self, error_handler):
        """测试警告日志记录"""
        # 不应该抛出异常
        error_handler.log_warning("测试警告", {"context": "test"})
    
    def test_log_info(self, error_handler):
        """测试信息日志记录"""
        # 不应该抛出异常
        error_handler.log_info("测试信息", {"context": "test"})


class TestErrorHandling:
    """测试错误处理功能"""
    
    def test_handle_error_with_fallback(self, error_handler, capsys):
        """测试错误处理并返回降级值"""
        error = ValueError("测试错误")
        fallback = "降级值"
        
        result = error_handler.handle_error(
            error,
            context={"test": "context"},
            user_message="操作失败，使用默认值",
            fallback_value=fallback
        )
        
        assert result == fallback
        captured = capsys.readouterr()
        assert "操作失败，使用默认值" in captured.out
    
    def test_handle_custom_error(self, error_handler, capsys):
        """测试处理自定义异常"""
        error = InsufficientDataError("管理报表", "交易记录")
        
        result = error_handler.handle_error(error, fallback_value=None)
        
        assert result is None
        captured = capsys.readouterr()
        assert "生成管理报表报表失败" in captured.out
        assert "缺少必要数据" in captured.out
    
    def test_handle_error_without_user_message(self, error_handler, capsys):
        """测试处理错误（无自定义消息）"""
        error = RuntimeError("系统错误")
        
        error_handler.handle_error(error)
        
        captured = capsys.readouterr()
        assert "操作失败" in captured.out
        assert "系统错误" in captured.out


class TestErrorDecorator:
    """测试错误处理装饰器"""
    
    def test_decorator_success(self, error_handler):
        """测试装饰器（函数成功执行）"""
        @error_handler.with_error_handling()
        def successful_function():
            return "成功"
        
        result = successful_function()
        assert result == "成功"
    
    def test_decorator_with_error(self, error_handler, capsys):
        """测试装饰器（函数抛出异常）"""
        @error_handler.with_error_handling(
            user_message="函数执行失败",
            fallback_value="降级值"
        )
        def failing_function():
            raise ValueError("测试错误")
        
        result = failing_function()
        assert result == "降级值"
        
        captured = capsys.readouterr()
        assert "函数执行失败" in captured.out
    
    def test_decorator_with_reraise(self, error_handler):
        """测试装饰器（重新抛出异常）"""
        @error_handler.with_error_handling(reraise=True)
        def failing_function():
            raise ValueError("测试错误")
        
        with pytest.raises(ValueError, match="测试错误"):
            failing_function()
    
    def test_decorator_with_args(self, error_handler):
        """测试装饰器（带参数的函数）"""
        @error_handler.with_error_handling(fallback_value=0)
        def add_numbers(a, b):
            if not isinstance(a, (int, float)) or not isinstance(b, (int, float)):
                raise TypeError("参数必须是数字")
            return a + b
        
        # 正常情况
        assert add_numbers(1, 2) == 3
        
        # 错误情况
        assert add_numbers("a", "b") == 0


class TestSafeExecute:
    """测试安全执行功能"""
    
    def test_safe_execute_success(self, error_handler):
        """测试安全执行（成功）"""
        def successful_function(x, y):
            return x + y
        
        result = error_handler.safe_execute(successful_function, 1, 2)
        assert result == 3
    
    def test_safe_execute_with_error(self, error_handler, capsys):
        """测试安全执行（失败）"""
        def failing_function():
            raise RuntimeError("测试错误")
        
        result = error_handler.safe_execute(
            failing_function,
            user_message="执行失败",
            fallback_value="默认值"
        )
        
        assert result == "默认值"
        captured = capsys.readouterr()
        assert "执行失败" in captured.out
    
    def test_safe_execute_with_kwargs(self, error_handler):
        """测试安全执行（带关键字参数）"""
        def function_with_kwargs(a, b=10):
            return a + b
        
        result = error_handler.safe_execute(function_with_kwargs, 5, b=20)
        assert result == 25


class TestGlobalFunctions:
    """测试全局便捷函数"""
    
    def test_get_error_handler(self):
        """测试获取全局错误处理器"""
        handler1 = get_error_handler()
        handler2 = get_error_handler()
        
        # 应该返回同一个实例
        assert handler1 is handler2
    
    def test_global_log_error(self):
        """测试全局log_error函数"""
        error = ValueError("测试错误")
        # 不应该抛出异常
        log_error(error, {"context": "test"})
    
    def test_global_log_warning(self):
        """测试全局log_warning函数"""
        log_warning("测试警告", {"context": "test"})
    
    def test_global_log_info(self):
        """测试全局log_info函数"""
        log_info("测试信息", {"context": "test"})
    
    def test_global_handle_error(self, capsys):
        """测试全局handle_error函数"""
        error = RuntimeError("测试错误")
        result = handle_error(error, fallback_value="降级值")
        
        assert result == "降级值"
        captured = capsys.readouterr()
        assert "操作失败" in captured.out
    
    def test_global_with_error_handling(self):
        """测试全局with_error_handling装饰器"""
        @with_error_handling(fallback_value=0)
        def test_function():
            raise ValueError("测试错误")
        
        result = test_function()
        assert result == 0
    
    def test_global_safe_execute(self):
        """测试全局safe_execute函数"""
        def test_function(x):
            return x * 2
        
        result = safe_execute(test_function, 5)
        assert result == 10


class TestCustomExceptions:
    """测试自定义异常"""
    
    def test_insufficient_data_error(self):
        """测试数据不足错误"""
        error = InsufficientDataError("管理报表", "交易记录")
        
        assert "管理报表" in str(error)
        assert "交易记录" in str(error)
        assert error.details["report_type"] == "管理报表"
        assert error.details["missing_data"] == "交易记录"
    
    def test_invalid_date_range_error(self):
        """测试无效日期范围错误"""
        error = InvalidDateRangeError("2024-12-31", "2024-01-01")
        
        assert "2024-12-31" in str(error)
        assert "2024-01-01" in str(error)
        assert "不能晚于" in str(error)
    
    def test_notification_delivery_error(self):
        """测试通知发送错误"""
        error = NotificationDeliveryError("企业微信", "网络连接失败")
        
        assert "企业微信" in str(error)
        assert "网络连接失败" in str(error)
    
    def test_invalid_excel_format_error(self):
        """测试无效Excel格式错误"""
        error = InvalidExcelFormatError("test.xlsx", "文件已损坏")
        
        assert "test.xlsx" in str(error)
        assert "文件已损坏" in str(error)
        assert "有效的Excel格式" in str(error)
    
    def test_file_read_error(self):
        """测试文件读取错误"""
        error = FileReadError("data.xlsx", "文件不存在")
        
        assert "data.xlsx" in str(error)
        assert "文件不存在" in str(error)
        assert "文件存在" in str(error)  # 包含建议
    
    def test_validation_error(self):
        """测试数据验证错误"""
        errors = ["错误1", "错误2", "错误3"]
        error = ValidationError(errors)
        
        assert "3 个错误" in str(error)
        assert "错误1" in str(error)
        assert error.details["error_count"] == 3


class TestErrorHandlingIntegration:
    """测试错误处理集成场景"""
    
    def test_nested_error_handling(self, error_handler):
        """测试嵌套错误处理"""
        @error_handler.with_error_handling(fallback_value="外层降级")
        def outer_function():
            @error_handler.with_error_handling(fallback_value="内层降级")
            def inner_function():
                raise ValueError("内层错误")
            
            result = inner_function()
            if result == "内层降级":
                raise RuntimeError("外层错误")
            return result
        
        result = outer_function()
        assert result == "外层降级"
    
    def test_error_context_preservation(self, error_handler):
        """测试错误上下文保留"""
        context = {
            "user_id": "12345",
            "operation": "生成报表",
            "timestamp": "2024-01-01"
        }
        
        error = ReportGenerationError("报表生成失败")
        # 不应该抛出异常
        error_handler.log_error(error, context)
