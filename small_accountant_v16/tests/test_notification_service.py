"""
Unit tests for NotificationService

Tests desktop notifications, WeChat notifications, retry logic, and error handling.
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
import time
from small_accountant_v16.reminders.notification_service import (
    NotificationService,
    NotificationResult
)


class TestNotificationService:
    """测试NotificationService类"""
    
    def test_initialization_default_params(self):
        """测试默认参数初始化"""
        service = NotificationService()
        assert service.max_retries == 3
        assert service.retry_delay == 2
    
    def test_initialization_custom_params(self):
        """测试自定义参数初始化"""
        service = NotificationService(max_retries=5, retry_delay=1)
        assert service.max_retries == 5
        assert service.retry_delay == 1
    
    @patch('small_accountant_v16.reminders.notification_service.PLYER_AVAILABLE', True)
    @patch('small_accountant_v16.reminders.notification_service.plyer_notification')
    def test_send_desktop_notification_success(self, mock_plyer):
        """测试桌面通知发送成功"""
        service = NotificationService()
        service.desktop_available = True
        
        result = service.send_desktop_notification(
            title="测试标题",
            message="测试消息"
        )
        
        assert result is True
        mock_plyer.notify.assert_called_once()
        call_args = mock_plyer.notify.call_args[1]
        assert call_args['title'] == "测试标题"
        assert call_args['message'] == "测试消息"
        assert call_args['app_name'] == "小会计助手"
        assert call_args['timeout'] == 10
    
    @patch('small_accountant_v16.reminders.notification_service.PLYER_AVAILABLE', True)
    @patch('small_accountant_v16.reminders.notification_service.plyer_notification')
    def test_send_desktop_notification_custom_params(self, mock_plyer):
        """测试自定义参数的桌面通知"""
        service = NotificationService()
        service.desktop_available = True
        
        result = service.send_desktop_notification(
            title="自定义标题",
            message="自定义消息",
            app_name="自定义应用",
            timeout=5
        )
        
        assert result is True
        call_args = mock_plyer.notify.call_args[1]
        assert call_args['app_name'] == "自定义应用"
        assert call_args['timeout'] == 5
    
    @patch('small_accountant_v16.reminders.notification_service.PLYER_AVAILABLE', False)
    def test_send_desktop_notification_library_unavailable(self):
        """测试plyer库不可用时的处理"""
        service = NotificationService()
        service.desktop_available = False
        
        result = service.send_desktop_notification(
            title="测试",
            message="测试"
        )
        
        assert result is False
    
    @patch('small_accountant_v16.reminders.notification_service.PLYER_AVAILABLE', True)
    @patch('small_accountant_v16.reminders.notification_service.plyer_notification')
    def test_send_desktop_notification_retry_on_failure(self, mock_plyer):
        """测试桌面通知失败后重试"""
        service = NotificationService(max_retries=3, retry_delay=0.1)
        service.desktop_available = True
        
        # First two attempts fail, third succeeds
        mock_plyer.notify.side_effect = [
            Exception("第一次失败"),
            Exception("第二次失败"),
            None  # 第三次成功
        ]
        
        result = service.send_desktop_notification(
            title="测试",
            message="测试"
        )
        
        assert result is True
        assert mock_plyer.notify.call_count == 3
    
    @patch('small_accountant_v16.reminders.notification_service.PLYER_AVAILABLE', True)
    @patch('small_accountant_v16.reminders.notification_service.plyer_notification')
    def test_send_desktop_notification_max_retries_exceeded(self, mock_plyer):
        """测试桌面通知超过最大重试次数"""
        service = NotificationService(max_retries=2, retry_delay=0.1)
        service.desktop_available = True
        
        # All attempts fail
        mock_plyer.notify.side_effect = Exception("持续失败")
        
        result = service.send_desktop_notification(
            title="测试",
            message="测试"
        )
        
        assert result is False
        assert mock_plyer.notify.call_count == 2
    
    @patch('small_accountant_v16.reminders.notification_service.REQUESTS_AVAILABLE', True)
    @patch('small_accountant_v16.reminders.notification_service.requests')
    def test_send_wechat_notification_success(self, mock_requests):
        """测试企业微信通知发送成功"""
        service = NotificationService()
        service.wechat_available = True
        
        # Mock successful response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"errcode": 0, "errmsg": "ok"}
        mock_requests.post.return_value = mock_response
        
        result = service.send_wechat_notification(
            webhook_url="https://qyapi.weixin.qq.com/cgi-bin/webhook/send?key=test",
            message="测试消息"
        )
        
        assert result is True
        mock_requests.post.assert_called_once()
        
        # Verify payload
        call_args = mock_requests.post.call_args
        payload = call_args[1]['json']
        assert payload['msgtype'] == 'text'
        assert payload['text']['content'] == "测试消息"
    
    @patch('small_accountant_v16.reminders.notification_service.REQUESTS_AVAILABLE', True)
    @patch('small_accountant_v16.reminders.notification_service.requests')
    def test_send_wechat_notification_with_mentions(self, mock_requests):
        """测试带@用户的企业微信通知"""
        service = NotificationService()
        service.wechat_available = True
        
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"errcode": 0, "errmsg": "ok"}
        mock_requests.post.return_value = mock_response
        
        result = service.send_wechat_notification(
            webhook_url="https://qyapi.weixin.qq.com/cgi-bin/webhook/send?key=test",
            message="测试消息",
            mentioned_list=["user1", "user2"],
            mentioned_mobile_list=["13800138000"]
        )
        
        assert result is True
        
        # Verify mentions in payload
        payload = mock_requests.post.call_args[1]['json']
        assert payload['text']['mentioned_list'] == ["user1", "user2"]
        assert payload['text']['mentioned_mobile_list'] == ["13800138000"]
    
    @patch('small_accountant_v16.reminders.notification_service.REQUESTS_AVAILABLE', False)
    def test_send_wechat_notification_library_unavailable(self):
        """测试requests库不可用时的处理"""
        service = NotificationService()
        service.wechat_available = False
        
        result = service.send_wechat_notification(
            webhook_url="https://qyapi.weixin.qq.com/cgi-bin/webhook/send?key=test",
            message="测试"
        )
        
        assert result is False
    
    @patch('small_accountant_v16.reminders.notification_service.REQUESTS_AVAILABLE', True)
    def test_send_wechat_notification_empty_webhook_url(self):
        """测试webhook地址为空时的处理"""
        service = NotificationService()
        service.wechat_available = True
        
        result = service.send_wechat_notification(
            webhook_url="",
            message="测试"
        )
        
        assert result is False
    
    @patch('small_accountant_v16.reminders.notification_service.REQUESTS_AVAILABLE', True)
    @patch('small_accountant_v16.reminders.notification_service.requests')
    def test_send_wechat_notification_api_error(self, mock_requests):
        """测试企业微信API返回错误"""
        service = NotificationService()
        service.wechat_available = True
        
        # Mock error response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"errcode": 40001, "errmsg": "invalid webhook url"}
        mock_requests.post.return_value = mock_response
        
        result = service.send_wechat_notification(
            webhook_url="https://qyapi.weixin.qq.com/cgi-bin/webhook/send?key=invalid",
            message="测试"
        )
        
        assert result is False
    
    @patch('small_accountant_v16.reminders.notification_service.REQUESTS_AVAILABLE', True)
    @patch('small_accountant_v16.reminders.notification_service.requests')
    def test_send_wechat_notification_http_error(self, mock_requests):
        """测试HTTP错误"""
        service = NotificationService()
        service.wechat_available = True
        
        # Mock HTTP error
        mock_response = Mock()
        mock_response.status_code = 500
        mock_requests.post.return_value = mock_response
        
        result = service.send_wechat_notification(
            webhook_url="https://qyapi.weixin.qq.com/cgi-bin/webhook/send?key=test",
            message="测试"
        )
        
        assert result is False
    
    @patch('small_accountant_v16.reminders.notification_service.REQUESTS_AVAILABLE', True)
    @patch('small_accountant_v16.reminders.notification_service.requests')
    def test_send_wechat_notification_timeout(self, mock_requests):
        """测试请求超时"""
        service = NotificationService(max_retries=2, retry_delay=0.1)
        service.wechat_available = True
        
        # Mock timeout
        import requests as real_requests
        mock_requests.post.side_effect = real_requests.exceptions.Timeout("请求超时")
        mock_requests.exceptions = real_requests.exceptions
        
        result = service.send_wechat_notification(
            webhook_url="https://qyapi.weixin.qq.com/cgi-bin/webhook/send?key=test",
            message="测试"
        )
        
        assert result is False
        assert mock_requests.post.call_count == 2
    
    @patch('small_accountant_v16.reminders.notification_service.REQUESTS_AVAILABLE', True)
    @patch('small_accountant_v16.reminders.notification_service.requests')
    def test_send_wechat_notification_retry_on_failure(self, mock_requests):
        """测试企业微信通知失败后重试"""
        service = NotificationService(max_retries=3, retry_delay=0.1)
        service.wechat_available = True
        
        # First two attempts fail, third succeeds
        mock_response_fail = Mock()
        mock_response_fail.status_code = 500
        
        mock_response_success = Mock()
        mock_response_success.status_code = 200
        mock_response_success.json.return_value = {"errcode": 0, "errmsg": "ok"}
        
        mock_requests.post.side_effect = [
            mock_response_fail,
            mock_response_fail,
            mock_response_success
        ]
        
        result = service.send_wechat_notification(
            webhook_url="https://qyapi.weixin.qq.com/cgi-bin/webhook/send?key=test",
            message="测试"
        )
        
        assert result is True
        assert mock_requests.post.call_count == 3
    
    @patch('small_accountant_v16.reminders.notification_service.PLYER_AVAILABLE', True)
    @patch('small_accountant_v16.reminders.notification_service.plyer_notification')
    @patch('small_accountant_v16.reminders.notification_service.REQUESTS_AVAILABLE', True)
    @patch('small_accountant_v16.reminders.notification_service.requests')
    def test_send_notification_multiple_channels(self, mock_requests, mock_plyer):
        """测试通过多个渠道发送通知"""
        service = NotificationService()
        service.desktop_available = True
        service.wechat_available = True
        
        # Mock successful responses
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"errcode": 0, "errmsg": "ok"}
        mock_requests.post.return_value = mock_response
        
        results = service.send_notification(
            title="测试标题",
            message="测试消息",
            channels=["desktop", "wechat"],
            wechat_webhook_url="https://qyapi.weixin.qq.com/cgi-bin/webhook/send?key=test"
        )
        
        assert results["desktop"] is True
        assert results["wechat"] is True
        mock_plyer.notify.assert_called_once()
        mock_requests.post.assert_called_once()
    
    @patch('small_accountant_v16.reminders.notification_service.PLYER_AVAILABLE', True)
    @patch('small_accountant_v16.reminders.notification_service.plyer_notification')
    def test_send_notification_desktop_only(self, mock_plyer):
        """测试仅通过桌面渠道发送通知"""
        service = NotificationService()
        service.desktop_available = True
        
        results = service.send_notification(
            title="测试标题",
            message="测试消息",
            channels=["desktop"]
        )
        
        assert results["desktop"] is True
        assert "wechat" not in results
        mock_plyer.notify.assert_called_once()
    
    @patch('small_accountant_v16.reminders.notification_service.REQUESTS_AVAILABLE', True)
    @patch('small_accountant_v16.reminders.notification_service.requests')
    def test_send_notification_wechat_without_url(self, mock_requests):
        """测试企业微信通知但未提供webhook地址"""
        service = NotificationService()
        service.wechat_available = True
        
        results = service.send_notification(
            title="测试标题",
            message="测试消息",
            channels=["wechat"]
        )
        
        assert results["wechat"] is False
        mock_requests.post.assert_not_called()
    
    def test_send_notification_unknown_channel(self):
        """测试未知的通知渠道"""
        service = NotificationService()
        
        results = service.send_notification(
            title="测试标题",
            message="测试消息",
            channels=["unknown_channel"]
        )
        
        assert results["unknown_channel"] is False
    
    @patch('small_accountant_v16.reminders.notification_service.PLYER_AVAILABLE', True)
    @patch('small_accountant_v16.reminders.notification_service.plyer_notification')
    def test_test_desktop_notification(self, mock_plyer):
        """测试桌面通知测试功能"""
        service = NotificationService()
        service.desktop_available = True
        
        result = service.test_desktop_notification()
        
        assert result is True
        mock_plyer.notify.assert_called_once()
        call_args = mock_plyer.notify.call_args[1]
        assert call_args['title'] == "测试通知"
        assert "测试通知" in call_args['message']
    
    @patch('small_accountant_v16.reminders.notification_service.REQUESTS_AVAILABLE', True)
    @patch('small_accountant_v16.reminders.notification_service.requests')
    def test_test_wechat_notification(self, mock_requests):
        """测试企业微信通知测试功能"""
        service = NotificationService()
        service.wechat_available = True
        
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"errcode": 0, "errmsg": "ok"}
        mock_requests.post.return_value = mock_response
        
        result = service.test_wechat_notification(
            webhook_url="https://qyapi.weixin.qq.com/cgi-bin/webhook/send?key=test"
        )
        
        assert result is True
        mock_requests.post.assert_called_once()
        payload = mock_requests.post.call_args[1]['json']
        assert "测试通知" in payload['text']['content']


class TestEdgeCases:
    """测试边界情况"""
    
    def test_empty_title_and_message(self):
        """测试空标题和消息"""
        service = NotificationService()
        service.desktop_available = False  # 避免实际发送
        
        # Should not crash with empty strings
        result = service.send_desktop_notification(title="", message="")
        assert result is False  # Fails because desktop not available
    
    def test_very_long_message(self):
        """测试超长消息"""
        service = NotificationService()
        service.desktop_available = False
        
        long_message = "测试" * 1000
        result = service.send_desktop_notification(
            title="测试",
            message=long_message
        )
        assert result is False  # Fails because desktop not available
    
    def test_special_characters_in_message(self):
        """测试消息中的特殊字符"""
        service = NotificationService()
        service.desktop_available = False
        
        special_message = "测试\n换行\t制表符\"引号\"'单引号'<>特殊符号"
        result = service.send_desktop_notification(
            title="测试",
            message=special_message
        )
        assert result is False  # Fails because desktop not available
    
    @patch('small_accountant_v16.reminders.notification_service.REQUESTS_AVAILABLE', True)
    @patch('small_accountant_v16.reminders.notification_service.requests')
    def test_invalid_webhook_url_format(self, mock_requests):
        """测试无效的webhook URL格式"""
        service = NotificationService()
        service.wechat_available = True
        
        import requests as real_requests
        mock_requests.post.side_effect = real_requests.exceptions.RequestException("Invalid URL")
        mock_requests.exceptions = real_requests.exceptions
        
        result = service.send_wechat_notification(
            webhook_url="not-a-valid-url",
            message="测试"
        )
        
        assert result is False
    
    def test_zero_retries(self):
        """测试零重试次数"""
        service = NotificationService(max_retries=0, retry_delay=0)
        assert service.max_retries == 0
        # Service should still work but won't retry
    
    def test_negative_retry_delay(self):
        """测试负数重试延迟"""
        service = NotificationService(max_retries=3, retry_delay=-1)
        assert service.retry_delay == -1
        # Service should still work (time.sleep handles negative values)
