"""
统一错误处理器

提供统一的错误处理、日志记录和优雅降级功能
"""

import logging
import traceback
import sys
from datetime import datetime
from pathlib import Path
from typing import Optional, Callable, Any
from functools import wraps

from .exceptions import SmallAccountantError


class ErrorHandler:
    """统一错误处理器"""
    
    def __init__(self, log_dir: str = "logs"):
        """
        初始化错误处理器
        
        Args:
            log_dir: 日志目录路径
        """
        self.log_dir = Path(log_dir)
        self.log_dir.mkdir(parents=True, exist_ok=True)
        
        # 配置日志
        self._setup_logging()
    
    def _setup_logging(self):
        """配置日志系统"""
        # 创建日志文件名（按日期）
        log_file = self.log_dir / f"small_accountant_{datetime.now().strftime('%Y%m%d')}.log"
        
        # 配置日志格式
        log_format = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        date_format = '%Y-%m-%d %H:%M:%S'
        
        # 配置根日志记录器
        logging.basicConfig(
            level=logging.INFO,
            format=log_format,
            datefmt=date_format,
            handlers=[
                logging.FileHandler(log_file, encoding='utf-8'),
                logging.StreamHandler(sys.stdout)
            ]
        )
        
        self.logger = logging.getLogger('SmallAccountant')
    
    def log_error(
        self,
        error: Exception,
        context: Optional[dict] = None,
        include_traceback: bool = True
    ):
        """
        记录错误日志
        
        Args:
            error: 异常对象
            context: 错误上下文信息
            include_traceback: 是否包含堆栈跟踪
        """
        error_info = {
            "error_type": type(error).__name__,
            "error_message": str(error),
            "timestamp": datetime.now().isoformat()
        }
        
        if context:
            error_info["context"] = context
        
        # 记录错误信息
        self.logger.error(f"错误发生: {error_info}")
        
        # 记录堆栈跟踪
        if include_traceback:
            self.logger.error(f"堆栈跟踪:\n{traceback.format_exc()}")
    
    def log_warning(self, message: str, context: Optional[dict] = None):
        """
        记录警告日志
        
        Args:
            message: 警告消息
            context: 上下文信息
        """
        warning_info = {"message": message, "timestamp": datetime.now().isoformat()}
        if context:
            warning_info["context"] = context
        
        self.logger.warning(f"警告: {warning_info}")
    
    def log_info(self, message: str, context: Optional[dict] = None):
        """
        记录信息日志
        
        Args:
            message: 信息消息
            context: 上下文信息
        """
        info = {"message": message, "timestamp": datetime.now().isoformat()}
        if context:
            info["context"] = context
        
        self.logger.info(f"信息: {info}")
    
    def handle_error(
        self,
        error: Exception,
        context: Optional[dict] = None,
        user_message: Optional[str] = None,
        fallback_value: Any = None
    ) -> Any:
        """
        处理错误并返回降级值
        
        Args:
            error: 异常对象
            context: 错误上下文
            user_message: 用户友好的错误消息
            fallback_value: 降级返回值
        
        Returns:
            降级值或None
        """
        # 记录错误
        self.log_error(error, context)
        
        # 显示用户友好的错误消息
        if user_message:
            print(f"\n❌ {user_message}")
        elif isinstance(error, SmallAccountantError):
            print(f"\n❌ {error.get_user_message()}")
        else:
            print(f"\n❌ 操作失败：{str(error)}")
        
        return fallback_value
    
    def with_error_handling(
        self,
        user_message: Optional[str] = None,
        fallback_value: Any = None,
        reraise: bool = False
    ):
        """
        错误处理装饰器
        
        Args:
            user_message: 用户友好的错误消息
            fallback_value: 降级返回值
            reraise: 是否重新抛出异常
        
        Returns:
            装饰器函数
        """
        def decorator(func: Callable) -> Callable:
            @wraps(func)
            def wrapper(*args, **kwargs):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    # 构建上下文
                    context = {
                        "function": func.__name__,
                        "args": str(args)[:200],  # 限制长度
                        "kwargs": str(kwargs)[:200]
                    }
                    
                    # 处理错误
                    result = self.handle_error(
                        error=e,
                        context=context,
                        user_message=user_message,
                        fallback_value=fallback_value
                    )
                    
                    # 是否重新抛出
                    if reraise:
                        raise
                    
                    return result
            
            return wrapper
        return decorator
    
    def safe_execute(
        self,
        func: Callable,
        *args,
        user_message: Optional[str] = None,
        fallback_value: Any = None,
        **kwargs
    ) -> Any:
        """
        安全执行函数，捕获并处理异常
        
        Args:
            func: 要执行的函数
            *args: 函数参数
            user_message: 用户友好的错误消息
            fallback_value: 降级返回值
            **kwargs: 函数关键字参数
        
        Returns:
            函数返回值或降级值
        """
        try:
            return func(*args, **kwargs)
        except Exception as e:
            context = {
                "function": func.__name__,
                "args": str(args)[:200],
                "kwargs": str(kwargs)[:200]
            }
            return self.handle_error(
                error=e,
                context=context,
                user_message=user_message,
                fallback_value=fallback_value
            )


# 全局错误处理器实例
_global_error_handler: Optional[ErrorHandler] = None


def get_error_handler(log_dir: str = "logs") -> ErrorHandler:
    """
    获取全局错误处理器实例
    
    Args:
        log_dir: 日志目录路径
    
    Returns:
        ErrorHandler实例
    """
    global _global_error_handler
    if _global_error_handler is None:
        _global_error_handler = ErrorHandler(log_dir)
    return _global_error_handler


def log_error(error: Exception, context: Optional[dict] = None):
    """记录错误（便捷函数）"""
    handler = get_error_handler()
    handler.log_error(error, context)


def log_warning(message: str, context: Optional[dict] = None):
    """记录警告（便捷函数）"""
    handler = get_error_handler()
    handler.log_warning(message, context)


def log_info(message: str, context: Optional[dict] = None):
    """记录信息（便捷函数）"""
    handler = get_error_handler()
    handler.log_info(message, context)


def handle_error(
    error: Exception,
    context: Optional[dict] = None,
    user_message: Optional[str] = None,
    fallback_value: Any = None
) -> Any:
    """处理错误（便捷函数）"""
    handler = get_error_handler()
    return handler.handle_error(error, context, user_message, fallback_value)


def with_error_handling(
    user_message: Optional[str] = None,
    fallback_value: Any = None,
    reraise: bool = False
):
    """错误处理装饰器（便捷函数）"""
    handler = get_error_handler()
    return handler.with_error_handling(user_message, fallback_value, reraise)


def safe_execute(
    func: Callable,
    *args,
    user_message: Optional[str] = None,
    fallback_value: Any = None,
    **kwargs
) -> Any:
    """安全执行函数（便捷函数）"""
    handler = get_error_handler()
    return handler.safe_execute(func, *args, user_message=user_message, fallback_value=fallback_value, **kwargs)
