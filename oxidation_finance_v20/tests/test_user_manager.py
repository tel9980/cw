#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
用户权限管理器测试
"""

import pytest
import sqlite3
import tempfile
import shutil
from pathlib import Path
from datetime import datetime, timedelta

import sys

project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from oxidation_finance_v20.security.user_manager import (
    UserManager,
    User,
    UserRole,
    Permission,
    OperationLog,
)


@pytest.fixture
def temp_dir():
    temp_path = tempfile.mkdtemp()
    yield temp_path
    shutil.rmtree(temp_path)


@pytest.fixture
def db_path(temp_dir):
    db_file = Path(temp_dir) / "test.db"
    return str(db_file)


@pytest.fixture
def user_manager(db_path):
    return UserManager(db_path)


class TestUserManager:
    """用户管理器测试"""

    def test_create_user(self, user_manager):
        """测试创建用户"""
        user = user_manager.create_user(
            username="test_user",
            password="test123",
            role=UserRole.ACCOUNTANT,
            display_name="测试用户",
            email="test@example.com",
            phone="13800138000",
        )

        assert user is not None
        assert user.username == "test_user"
        assert user.role == UserRole.ACCOUNTANT
        assert user.is_active is True

    def test_authenticate_success(self, user_manager):
        """测试认证成功"""
        user_manager.create_user(
            username="test_user",
            password="test123",
            role=UserRole.ACCOUNTANT,
        )

        authenticated = user_manager.authenticate("test_user", "test123")
        assert authenticated is not None
        assert authenticated.username == "test_user"

    def test_authenticate_wrong_password(self, user_manager):
        """测试密码错误"""
        user_manager.create_user(
            username="test_user",
            password="test123",
            role=UserRole.ACCOUNTANT,
        )

        authenticated = user_manager.authenticate("test_user", "wrong_password")
        assert authenticated is None

    def test_authenticate_nonexistent_user(self, user_manager):
        """测试用户不存在"""
        authenticated = user_manager.authenticate("nonexistent", "password")
        assert authenticated is None

    def test_get_user(self, user_manager):
        """测试获取用户"""
        user_manager.create_user(
            username="test_user",
            password="test123",
            role=UserRole.ACCOUNTANT,
        )

        user = user_manager.get_user_by_username("test_user")
        assert user is not None
        assert user.username == "test_user"

    def test_list_users(self, user_manager):
        """测试列出用户"""
        user_manager.create_user("user1", "pass1", UserRole.VIEWER)
        user_manager.create_user("user2", "pass2", UserRole.ACCOUNTANT)

        users = user_manager.list_users()
        assert len(users) >= 2  # 包含admin

    def test_update_user(self, user_manager):
        """测试更新用户"""
        user = user_manager.create_user(
            username="test_user",
            password="test123",
            role=UserRole.VIEWER,
        )

        user.display_name = "新名称"
        user.role = UserRole.ACCOUNTANT
        result = user_manager.update_user(user)

        assert result is True

        updated = user_manager.get_user(user.id)
        assert updated.display_name == "新名称"
        assert updated.role == UserRole.ACCOUNTANT

    def test_change_password(self, user_manager):
        """测试修改密码"""
        user = user_manager.create_user(
            username="test_user",
            password="test123",
            role=UserRole.VIEWER,
        )

        result = user_manager.change_password(user.id, "new_password")
        assert result is True

        # 旧密码应该失效
        authenticated = user_manager.authenticate("test_user", "test123")
        assert authenticated is None

        # 新密码应该有效
        authenticated = user_manager.authenticate("test_user", "new_password")
        assert authenticated is not None

    def test_delete_user(self, user_manager):
        """测试删除用户（软删除）"""
        user = user_manager.create_user(
            username="test_user",
            password="test123",
            role=UserRole.VIEWER,
        )

        result = user_manager.delete_user(user.id)
        assert result is True

        # 用户应该无法认证
        authenticated = user_manager.authenticate("test_user", "test123")
        assert authenticated is None

    def test_default_admin_exists(self, user_manager):
        """测试默认管理员存在"""
        admin = user_manager.authenticate("admin", "admin123")
        assert admin is not None
        assert admin.role == UserRole.ADMIN


class TestPermissions:
    """权限测试"""

    def test_admin_has_all_permissions(self, user_manager):
        """测试管理员拥有所有权限"""
        admin = user_manager.get_user_by_username("admin")

        for permission in Permission:
            assert user_manager.has_permission(admin, permission) is True

    def test_accountant_permissions(self, user_manager):
        """测试会计权限"""
        accountant = User(
            username="test",
            role=UserRole.ACCOUNTANT,
        )

        # 应该有权
        assert user_manager.has_permission(accountant, Permission.ORDER_CREATE) is True
        assert user_manager.has_permission(accountant, Permission.INCOME_CREATE) is True
        assert user_manager.has_permission(accountant, Permission.REPORT_VIEW) is True

        # 应该无权
        assert user_manager.has_permission(accountant, Permission.USER_MANAGE) is False
        assert (
            user_manager.has_permission(accountant, Permission.SYSTEM_CONFIG) is False
        )

    def test_viewer_permissions(self, user_manager):
        """测试查看者权限"""
        viewer = User(
            username="test",
            role=UserRole.VIEWER,
        )

        # 应该只有查看权限
        assert user_manager.has_permission(viewer, Permission.ORDER_VIEW) is True
        assert user_manager.has_permission(viewer, Permission.INCOME_VIEW) is True

        # 应该无权创建或修改
        assert user_manager.has_permission(viewer, Permission.ORDER_CREATE) is False
        assert user_manager.has_permission(viewer, Permission.ORDER_EDIT) is False

    def test_require_permission_success(self, user_manager):
        """测试权限检查成功"""
        admin = user_manager.get_user_by_username("admin")

        # 不应该抛出异常
        user_manager.require_permission(admin, Permission.ORDER_CREATE)
        user_manager.require_permission(admin, Permission.SYSTEM_CONFIG)

    def test_require_permission_denied(self, user_manager):
        """测试权限不足"""
        viewer = User(
            username="test",
            role=UserRole.VIEWER,
        )

        with pytest.raises(Exception):  # PermissionDeniedError
            user_manager.require_permission(viewer, Permission.SYSTEM_CONFIG)


class TestOperationLogs:
    """操作日志测试"""

    def test_log_action(self, user_manager):
        """测试记录日志"""
        user = user_manager.create_user(
            username="test_user",
            password="test123",
            role=UserRole.ACCOUNTANT,
        )

        user_manager.log_action(
            user=user,
            action="CREATE",
            module="orders",
            resource_type="order",
            resource_id="test_order_001",
            details={"amount": 1000},
            ip_address="192.168.1.1",
        )

        logs = user_manager.get_logs(limit=10)
        assert len(logs) >= 1

        # 查找我们添加的日志
        found = False
        for log in logs:
            if log.action == "CREATE" and log.module == "orders":
                found = True
                break

        assert found is True

    def test_get_logs_by_module(self, user_manager):
        """测试按模块获取日志"""
        user = user_manager.create_user(
            username="test_user",
            password="test123",
            role=UserRole.ACCOUNTANT,
        )

        # 添加不同模块的日志
        user_manager.log_action(user, "CREATE", "orders")
        user_manager.log_action(user, "VIEW", "customers")
        user_manager.log_action(user, "UPDATE", "incomes")

        order_logs = user_manager.get_logs(module="orders")
        customer_logs = user_manager.get_logs(module="customers")

        assert len(order_logs) >= 1
        assert len(customer_logs) >= 1

    def test_get_logs_by_user(self, user_manager):
        """测试按用户获取日志"""
        user = user_manager.create_user(
            username="test_user",
            password="test123",
            role=UserRole.ACCOUNTANT,
        )

        user_manager.log_action(user, "CREATE", "orders")
        user_manager.log_action(user, "UPDATE", "orders")

        logs = user_manager.get_logs(user_id=user.id)
        assert len(logs) >= 2

    def test_get_user_activity(self, user_manager):
        """测试获取用户活动"""
        user = user_manager.create_user(
            username="test_user",
            password="test123",
            role=UserRole.ACCOUNTANT,
        )

        user_manager.log_action(user, "VIEW", "orders")
        user_manager.log_action(user, "VIEW", "orders")
        user_manager.log_action(user, "VIEW", "orders")
        user_manager.log_action(user, "VIEW", "orders")
        user_manager.log_action(user, "VIEW", "orders")

        # 验证日志已记录
        all_logs = user_manager.get_logs(user_id=user.id, limit=100)
        assert len(all_logs) >= 5  # 验证至少5条

    def test_get_statistics(self, user_manager):
        """测试获取统计"""
        user = user_manager.create_user(
            username="test_user",
            password="test123",
            role=UserRole.ACCOUNTANT,
        )

        # 添加一些日志
        for i in range(3):
            user_manager.log_action(user, "CREATE", "orders")
        for i in range(2):
            user_manager.log_action(user, "VIEW", "customers")

        stats = user_manager.get_statistics()

        assert "by_module" in stats
        assert "by_action" in stats
        assert "total_logs" in stats
        assert stats["total_logs"] >= 5


class TestUserModel:
    """用户模型测试"""

    def test_password_hash(self):
        """测试密码哈希"""
        user = User(username="test", password_hash="")
        user.set_password("test123")

        assert user.password_hash != "test123"
        assert user.check_password("test123") is True
        assert user.check_password("wrong") is False

    def test_user_default_values(self):
        """测试用户默认值"""
        user = User(username="test")

        assert user.id != ""
        assert user.role == UserRole.VIEWER
        assert user.is_active is True
        assert user.login_count == 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
