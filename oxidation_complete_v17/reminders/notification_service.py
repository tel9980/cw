"""
Notification Service Module

Handles sending notifications through multiple channels:
- Desktop notifications (Windows)
- WeChat webhook notifications

Includes retry logic for failed notifications.
"""

import logging
import time
from typing import Optional, Dict, Any
from enum import Enum
import platform

# Import for desktop notifications
try:
    from plyer import notification as plyer_notification
    PLYER_AVAILABLE = True
except ImportError:
    plyer_notification = None
    PLYER_AVAILABLE = False

# Import for HTTP requests (WeChat webhook)
try:
    import requests
    REQUESTS_AVAILABLE = True
except ImportError:
    REQUESTS_AVAILABLE = False


# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class NotificationResult(Enum):
    """通知发送结果"""
    SUCCESS = "success"
    FAILED = "failed"
    SKIPPED = "skipped"


class NotificationService:
    """
    通知服务
    
    支持多种通知渠道：
    - 桌面通知（Windows）
    - 企业微信webhook通知
    
    包含失败重试逻辑
    """
    
    DEFAULT_MAX_RETRIES = 3
    DEFAULT_RETRY_DELAY = 2  # seconds
    
    def __init__(
        self, 
        max_retries: int = DEFAULT_MAX_RETRIES,
        retry_delay: int = DEFAULT_RETRY_DELAY
    ):
        """
        初始化通知服务
        
        Args:
            max_retries: 最大重试次数（默认3次）
            retry_delay: 重试延迟秒数（默认2秒）
        """
        self.max_retries = max_retries
        self.retry_delay = retry_delay
        
        # Check platform and library availability
        self.is_windows = platform.system() == "Windows"
        self.desktop_available = PLYER_AVAILABLE
        self.wechat_available = REQUESTS_AVAILABLE
        
        if not self.desktop_available:
            logger.warning("plyer库未安装，桌面通知功能不可用。请运行: pip install plyer")
        
        if not self.wechat_available:
            logger.warning("requests库未安装，企业微信通知功能不可用。请运行: pip install requests")
    
    def send_desktop_notification(
        self, 
        title: str,
        message: str,
        app_name: str = "小会计助手",
        timeout: int = 10
    ) -> bool:
        """
        发送桌面通知
        
        Args:
            title: 通知标题
            message: 通知内容
            app_name: 应用名称（默认"小会计助手"）
            timeout: 通知显示时长（秒，默认10秒）
        
        Returns:
            bool: 是否发送成功
        """
        if not self.desktop_available:
            logger.error("桌面通知功能不可用：plyer库未安装")
            return False
        
        # Retry logic
        for attempt in range(1, self.max_retries + 1):
            try:
                logger.info(f"发送桌面通知（尝试 {attempt}/{self.max_retries}）: {title}")
                
                plyer_notification.notify(
                    title=title,
                    message=message,
                    app_name=app_name,
                    timeout=timeout
                )
                
                logger.info(f"桌面通知发送成功: {title}")
                return True
                
            except Exception as e:
                logger.error(f"桌面通知发送失败（尝试 {attempt}/{self.max_retries}）: {e}")
                
                if attempt < self.max_retries:
                    logger.info(f"等待 {self.retry_delay} 秒后重试...")
                    time.sleep(self.retry_delay)
                else:
                    logger.error(f"桌面通知发送失败，已达到最大重试次数: {title}")
                    return False
        
        return False
    
    def send_wechat_notification(
        self, 
        webhook_url: str,
        message: str,
        mentioned_list: Optional[list] = None,
        mentioned_mobile_list: Optional[list] = None
    ) -> bool:
        """
        发送企业微信通知
        
        Args:
            webhook_url: 企业微信webhook地址
            message: 通知内容
            mentioned_list: @的用户列表（userid）
            mentioned_mobile_list: @的用户手机号列表
        
        Returns:
            bool: 是否发送成功
        """
        if not self.wechat_available:
            logger.error("企业微信通知功能不可用：requests库未安装")
            return False
        
        if not webhook_url:
            logger.error("企业微信webhook地址为空，无法发送通知")
            return False
        
        # Prepare WeChat message payload
        payload = {
            "msgtype": "text",
            "text": {
                "content": message
            }
        }
        
        # Add mentioned users if provided
        if mentioned_list or mentioned_mobile_list:
            payload["text"]["mentioned_list"] = mentioned_list or []
            payload["text"]["mentioned_mobile_list"] = mentioned_mobile_list or []
        
        # Retry logic
        for attempt in range(1, self.max_retries + 1):
            try:
                logger.info(f"发送企业微信通知（尝试 {attempt}/{self.max_retries}）")
                
                response = requests.post(
                    webhook_url,
                    json=payload,
                    timeout=10
                )
                
                # Check response
                if response.status_code == 200:
                    result = response.json()
                    if result.get("errcode") == 0:
                        logger.info("企业微信通知发送成功")
                        return True
                    else:
                        error_msg = result.get("errmsg", "未知错误")
                        logger.error(f"企业微信通知发送失败: {error_msg}")
                else:
                    logger.error(f"企业微信通知发送失败: HTTP {response.status_code}")
                
            except requests.exceptions.Timeout:
                logger.error(f"企业微信通知发送超时（尝试 {attempt}/{self.max_retries}）")
            except requests.exceptions.RequestException as e:
                logger.error(f"企业微信通知发送失败（尝试 {attempt}/{self.max_retries}）: {e}")
            except Exception as e:
                logger.error(f"企业微信通知发送异常（尝试 {attempt}/{self.max_retries}）: {e}")
            
            # Retry if not the last attempt
            if attempt < self.max_retries:
                logger.info(f"等待 {self.retry_delay} 秒后重试...")
                time.sleep(self.retry_delay)
            else:
                logger.error("企业微信通知发送失败，已达到最大重试次数")
                return False
        
        return False
    
    def send_notification(
        self,
        title: str,
        message: str,
        channels: list,
        wechat_webhook_url: Optional[str] = None,
        **kwargs
    ) -> Dict[str, bool]:
        """
        通过多个渠道发送通知
        
        Args:
            title: 通知标题
            message: 通知内容
            channels: 通知渠道列表（如 ["desktop", "wechat"]）
            wechat_webhook_url: 企业微信webhook地址（如果使用微信通知）
            **kwargs: 其他参数
        
        Returns:
            Dict[str, bool]: 各渠道发送结果 {"desktop": True, "wechat": False}
        """
        results = {}
        
        for channel in channels:
            if channel == "desktop":
                results["desktop"] = self.send_desktop_notification(
                    title=title,
                    message=message,
                    **{k: v for k, v in kwargs.items() if k in ["app_name", "timeout"]}
                )
            elif channel == "wechat":
                if wechat_webhook_url:
                    results["wechat"] = self.send_wechat_notification(
                        webhook_url=wechat_webhook_url,
                        message=f"{title}\n\n{message}",
                        **{k: v for k, v in kwargs.items() if k in ["mentioned_list", "mentioned_mobile_list"]}
                    )
                else:
                    logger.warning("企业微信webhook地址未配置，跳过微信通知")
                    results["wechat"] = False
            else:
                logger.warning(f"未知的通知渠道: {channel}")
                results[channel] = False
        
        return results
    
    def test_desktop_notification(self) -> bool:
        """
        测试桌面通知功能
        
        Returns:
            bool: 测试是否成功
        """
        return self.send_desktop_notification(
            title="测试通知",
            message="这是一条测试通知，如果您看到这条消息，说明桌面通知功能正常工作。",
            timeout=5
        )
    
    def test_wechat_notification(self, webhook_url: str) -> bool:
        """
        测试企业微信通知功能
        
        Args:
            webhook_url: 企业微信webhook地址
        
        Returns:
            bool: 测试是否成功
        """
        return self.send_wechat_notification(
            webhook_url=webhook_url,
            message="【测试通知】\n这是一条测试通知，如果您收到这条消息，说明企业微信通知功能正常工作。"
        )
