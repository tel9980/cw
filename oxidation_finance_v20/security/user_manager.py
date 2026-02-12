#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
用户权限和日志管理器 - 提供用户认证、权限控制和操作日志记录功能
"""

import sqlite3
import hashlib
import uuid
from pathlib import Path
from datetime import datetime, date
from typing import Optional, List, Dict, Any
from enum import Enum
from dataclasses import dataclass, field
import json


class UserRole(Enum):
    """用户角色"""

    ADMIN = "admin"  # 管理员 - 全部权限
    MANAGER = "manager"  # 经理 - 查看全部，编辑部分
    ACCOUNTANT = "accountant"  # 会计 - 日常操作
    VIEWER = "viewer"  # 查看者 - 只读权限


class Permission(Enum):
    """权限枚举"""

    # 订单权限
    ORDER_VIEW = "order_view"
    ORDER_CREATE = "order_create"
    ORDER_EDIT = "order_edit"
    ORDER_DELETE = "order_delete"

    # 收入权限
    INCOME_VIEW = "income_view"
    INCOME_CREATE = "income_create"
    INCOME_EDIT = "income_edit"
    INCOME_DELETE = "income_delete"

    # 支出权限
    EXPENSE_VIEW = "expense_view"
    EXPENSE_CREATE = "expense_create"
    EXPENSE_EDIT = "expense_edit"
    EXPENSE_DELETE = "expense_delete"

    # 客户权限
    CUSTOMER_VIEW = "customer_view"
    CUSTOMER_CREATE = "customer_create"
    CUSTOMER_EDIT = "customer_edit"
    CUSTOMER_DELETE = "customer_delete"

    # 报表权限
    REPORT_VIEW = "report_view"
    REPORT_EXPORT = "report_export"

    # 系统权限
    SYSTEM_CONFIG = "system_config"
    USER_MANAGE = "user_manage"
    LOG_VIEW = "log_view"


# 角色权限映射
ROLE_PERMISSIONS = {
    UserRole.ADMIN: list(Permission),  # 全部权限
    UserRole.MANAGER: [
        Permission.ORDER_VIEW,
        Permission.ORDER_CREATE,
        Permission.ORDER_EDIT,
        Permission.INCOME_VIEW,
        Permission.INCOME_CREATE,
        Permission.INCOME_EDIT,
        Permission.EXPENSE_VIEW,
        Permission.EXPENSE_CREATE,
        Permission.EXPENSE_EDIT,
        Permission.CUSTOMER_VIEW,
        Permission.CUSTOMER_CREATE,
        Permission.CUSTOMER_EDIT,
        Permission.REPORT_VIEW,
        Permission.REPORT_EXPORT,
    ],
    UserRole.ACCOUNTANT: [
        Permission.ORDER_VIEW,
        Permission.ORDER_CREATE,
        Permission.ORDER_EDIT,
        Permission.INCOME_VIEW,
        Permission.INCOME_CREATE,
        Permission.INCOME_EDIT,
        Permission.EXPENSE_VIEW,
        Permission.EXPENSE_CREATE,
        Permission.EXPENSE_EDIT,
        Permission.CUSTOMER_VIEW,
        Permission.CUSTOMER_CREATE,
        Permission.REPORT_VIEW,
    ],
    UserRole.VIEWER: [
        Permission.ORDER_VIEW,
        Permission.INCOME_VIEW,
        Permission.EXPENSE_VIEW,
        Permission.CUSTOMER_VIEW,
        Permission.REPORT_VIEW,
    ],
}


@dataclass
class User:
    """用户信息"""

    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    username: str = ""
    password_hash: str = ""
    role: UserRole = UserRole.VIEWER
    display_name: str = ""
    email: str = ""
    phone: str = ""
    is_active: bool = True
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    last_login: Optional[str] = None
    login_count: int = 0

    def set_password(self, password: str):
        """设置密码"""
        self.password_hash = hashlib.sha256(password.encode()).hexdigest()

    def check_password(self, password: str) -> bool:
        """验证密码"""
        return self.password_hash == hashlib.sha256(password.encode()).hexdigest()


@dataclass
class OperationLog:
    """操作日志"""

    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str = ""
    username: str = ""
    action: str = ""
    module: str = ""  # orders, incomes, expenses, customers, reports, system
    resource_type: str = ""
    resource_id: str = ""
    details: str = ""  # JSON格式的详细信息
    ip_address: str = ""
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "id": self.id,
            "user_id": self.user_id,
            "username": self.username,
            "action": self.action,
            "module": self.module,
            "resource_type": self.resource_type,
            "resource_id": self.resource_id,
            "details": self.details,
            "ip_address": self.ip_address,
            "created_at": self.created_at,
        }


class PermissionDeniedError(Exception):
    """权限不足错误"""

    pass


class UserManager:
    """用户管理器 - 用户认证和权限控制"""

    def __init__(self, db_path: str):
        """
        初始化用户管理器

        Args:
            db_path: 数据库路径
        """
        self.db_path = db_path
        self._init_tables()
        self._create_default_admin()

    def _get_connection(self) -> sqlite3.Connection:
        """获取数据库连接"""
        return sqlite3.connect(self.db_path)

    def _init_tables(self):
        """初始化数据库表"""
        conn = self._get_connection()
        cursor = conn.cursor()

        # 用户表
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id TEXT PRIMARY KEY,
                username TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL,
                role TEXT NOT NULL DEFAULT 'viewer',
                display_name TEXT DEFAULT '',
                email TEXT DEFAULT '',
                phone TEXT DEFAULT '',
                is_active INTEGER DEFAULT 1,
                created_at TEXT,
                last_login TEXT,
                login_count INTEGER DEFAULT 0
            )
        """)

        # 操作日志表
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS operation_logs (
                id TEXT PRIMARY KEY,
                user_id TEXT NOT NULL,
                username TEXT,
                action TEXT NOT NULL,
                module TEXT DEFAULT '',
                resource_type TEXT DEFAULT '',
                resource_id TEXT DEFAULT '',
                details TEXT DEFAULT '',
                ip_address TEXT DEFAULT '',
                created_at TEXT NOT NULL,
                FOREIGN KEY (user_id) REFERENCES users(id)
            )
        """)

        # 创建索引
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_logs_user_id ON operation_logs(user_id)
        """)
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_logs_created_at ON operation_logs(created_at)
        """)
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_logs_module ON operation_logs(module)
        """)

        conn.commit()
        conn.close()

    def _create_default_admin(self):
        """创建默认管理员"""
        conn = self._get_connection()
        cursor = conn.cursor()

        # 检查是否存在管理员
        cursor.execute("SELECT COUNT(*) FROM users WHERE role = 'admin'")
        count = cursor.fetchone()[0]

        if count == 0:
            # 创建默认管理员
            admin = User(
                username="admin",
                role=UserRole.ADMIN,
                display_name="系统管理员",
            )
            admin.set_password("admin123")  # 默认密码
            admin.is_active = True

            cursor.execute(
                """
                INSERT INTO users (id, username, password_hash, role, display_name, 
                                   email, phone, is_active, created_at, login_count)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
                (
                    admin.id,
                    admin.username,
                    admin.password_hash,
                    admin.role.value,
                    admin.display_name,
                    admin.email,
                    admin.phone,
                    1 if admin.is_active else 0,
                    admin.created_at,
                    admin.login_count,
                ),
            )

            conn.commit()
            print("[INFO] 默认管理员已创建 - 用户名: admin, 密码: admin123")

        conn.close()

    # ==================== 用户管理 ====================

    def create_user(
        self,
        username: str,
        password: str,
        role: UserRole,
        display_name: str = "",
        email: str = "",
        phone: str = "",
    ) -> Optional[User]:
        """
        创建用户

        Args:
            username: 用户名
            password: 密码
            role: 角色
            display_name: 显示名称
            email: 邮箱
            phone: 电话

        Returns:
            创建的用户，失败返回None
        """
        conn = self._get_connection()
        cursor = conn.cursor()

        try:
            # 检查用户名是否已存在
            cursor.execute("SELECT COUNT(*) FROM users WHERE username = ?", (username,))
            if cursor.fetchone()[0] > 0:
                print(f"[ERROR] 用户名 '{username}' 已存在")
                return None

            # 创建用户
            user = User(
                username=username,
                role=role,
                display_name=display_name or username,
                email=email,
                phone=phone,
            )
            user.set_password(password)

            cursor.execute(
                """
                INSERT INTO users (id, username, password_hash, role, display_name,
                                   email, phone, is_active, created_at, login_count)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
                (
                    user.id,
                    user.username,
                    user.password_hash,
                    user.role.value,
                    user.display_name,
                    user.email,
                    user.phone,
                    1,
                    user.created_at,
                    user.login_count,
                ),
            )

            conn.commit()
            print(f"[OK] 用户 '{username}' 创建成功")
            return user

        except Exception as e:
            print(f"[ERROR] 创建用户失败: {e}")
            return None
        finally:
            conn.close()

    def authenticate(self, username: str, password: str) -> Optional[User]:
        """
        用户认证

        Args:
            username: 用户名
            password: 密码

        Returns:
            认证成功返回用户对象，失败返回None
        """
        conn = self._get_connection()
        cursor = conn.cursor()

        cursor.execute(
            """
            SELECT * FROM users WHERE username = ? AND is_active = 1
        """,
            (username,),
        )

        row = cursor.fetchone()

        if row is None:
            conn.close()
            return None

        user = User(
            id=row[0],
            username=row[1],
            password_hash=row[2],
            role=UserRole(row[3]),
            display_name=row[4] or "",
            email=row[5] or "",
            phone=row[6] or "",
            is_active=bool(row[7]),
            created_at=row[8],
            last_login=row[9],
            login_count=row[10] or 0,
        )

        if not user.check_password(password):
            conn.close()
            return None

        # 更新登录信息
        user.last_login = datetime.now().isoformat()
        user.login_count += 1

        cursor.execute(
            """
            UPDATE users SET last_login = ?, login_count = ? WHERE id = ?
        """,
            (user.last_login, user.login_count, user.id),
        )

        conn.commit()
        conn.close()

        return user

    def get_user(self, user_id: str) -> Optional[User]:
        """获取用户"""
        conn = self._get_connection()
        cursor = conn.cursor()

        cursor.execute("SELECT * FROM users WHERE id = ?", (user_id,))
        row = cursor.fetchone()

        conn.close()

        if row is None:
            return None

        return User(
            id=row[0],
            username=row[1],
            password_hash=row[2],
            role=UserRole(row[3]),
            display_name=row[4] or "",
            email=row[5] or "",
            phone=row[6] or "",
            is_active=bool(row[7]),
            created_at=row[8],
            last_login=row[9],
            login_count=row[10] or 0,
        )

    def get_user_by_username(self, username: str) -> Optional[User]:
        """根据用户名获取用户"""
        conn = self._get_connection()
        cursor = conn.cursor()

        cursor.execute("SELECT * FROM users WHERE username = ?", (username,))
        row = cursor.fetchone()

        conn.close()

        if row is None:
            return None

        return User(
            id=row[0],
            username=row[1],
            password_hash=row[2],
            role=UserRole(row[3]),
            display_name=row[4] or "",
            email=row[5] or "",
            phone=row[6] or "",
            is_active=bool(row[7]),
            created_at=row[8],
            last_login=row[9],
            login_count=row[10] or 0,
        )

    def list_users(self, include_inactive: bool = False) -> List[User]:
        """列出所有用户"""
        conn = self._get_connection()
        cursor = conn.cursor()

        if include_inactive:
            cursor.execute("SELECT * FROM users ORDER BY created_at DESC")
        else:
            cursor.execute(
                "SELECT * FROM users WHERE is_active = 1 ORDER BY created_at DESC"
            )

        users = []
        for row in cursor.fetchall():
            users.append(
                User(
                    id=row[0],
                    username=row[1],
                    password_hash=row[2],
                    role=UserRole(row[3]),
                    display_name=row[4] or "",
                    email=row[5] or "",
                    phone=row[6] or "",
                    is_active=bool(row[7]),
                    created_at=row[8],
                    last_login=row[9],
                    login_count=row[10] or 0,
                )
            )

        conn.close()
        return users

    def update_user(self, user: User) -> bool:
        """更新用户信息"""
        conn = self._get_connection()
        cursor = conn.cursor()

        try:
            cursor.execute(
                """
                UPDATE users SET display_name = ?, email = ?, phone = ?, 
                               role = ?, is_active = ? WHERE id = ?
            """,
                (
                    user.display_name,
                    user.email,
                    user.phone,
                    user.role.value,
                    1 if user.is_active else 0,
                    user.id,
                ),
            )

            conn.commit()
            return True

        except Exception as e:
            print(f"[ERROR] 更新用户失败: {e}")
            return False
        finally:
            conn.close()

    def change_password(self, user_id: str, new_password: str) -> bool:
        """修改密码"""
        conn = self._get_connection()
        cursor = conn.cursor()

        try:
            new_hash = hashlib.sha256(new_password.encode()).hexdigest()
            cursor.execute(
                "UPDATE users SET password_hash = ? WHERE id = ?", (new_hash, user_id)
            )
            conn.commit()
            return True
        except Exception as e:
            print(f"[ERROR] 修改密码失败: {e}")
            return False
        finally:
            conn.close()

    def delete_user(self, user_id: str) -> bool:
        """删除用户（软删除）"""
        conn = self._get_connection()
        cursor = conn.cursor()

        try:
            cursor.execute("UPDATE users SET is_active = 0 WHERE id = ?", (user_id,))
            conn.commit()
            return True
        except Exception as e:
            print(f"[ERROR] 删除用户失败: {e}")
            return False
        finally:
            conn.close()

    # ==================== 权限控制 ====================

    def has_permission(self, user: User, permission: Permission) -> bool:
        """检查用户是否有指定权限"""
        if not user.is_active:
            return False

        user_permissions = ROLE_PERMISSIONS.get(user.role, [])
        return permission in user_permissions

    def get_user_permissions(self, user: User) -> List[Permission]:
        """获取用户的所有权限"""
        return ROLE_PERMISSIONS.get(user.role, [])

    def require_permission(self, user: User, permission: Permission):
        """检查权限，不足则抛出异常"""
        if not self.has_permission(user, permission):
            raise PermissionDeniedError(
                f"用户 '{user.username}' 缺少权限: {permission.value}"
            )

    def can_access_module(self, user: User, module: str) -> bool:
        """检查用户是否可以访问指定模块"""
        # 基于权限检查
        permission_map = {
            "orders": [Permission.ORDER_VIEW],
            "incomes": [Permission.INCOME_VIEW],
            "expenses": [Permission.EXPENSE_VIEW],
            "customers": [Permission.CUSTOMER_VIEW],
            "reports": [Permission.REPORT_VIEW],
            "system": [Permission.SYSTEM_CONFIG],
            "users": [Permission.USER_MANAGE],
            "logs": [Permission.LOG_VIEW],
        }

        required = permission_map.get(module, [])
        for perm in required:
            if self.has_permission(user, perm):
                return True
        return False

    # ==================== 操作日志 ====================

    def log_action(
        self,
        user: User,
        action: str,
        module: str,
        resource_type: str = "",
        resource_id: str = "",
        details: Dict[str, Any] = None,
        ip_address: str = "",
    ):
        """
        记录操作日志

        Args:
            user: 执行操作的用户
            action: 操作类型 (CREATE, UPDATE, DELETE, VIEW, LOGIN, LOGOUT, EXPORT)
            module: 模块名 (orders, incomes, expenses, customers, reports, system)
            resource_type: 资源类型
            resource_id: 资源ID
            details: 详细信息字典
            ip_address: IP地址
        """
        conn = self._get_connection()
        cursor = conn.cursor()

        log = OperationLog(
            user_id=user.id,
            username=user.username,
            action=action.upper(),
            module=module,
            resource_type=resource_type,
            resource_id=resource_id,
            details=json.dumps(details or {}, ensure_ascii=False),
            ip_address=ip_address,
        )

        try:
            cursor.execute(
                """
                INSERT INTO operation_logs 
                (id, user_id, username, action, module, resource_type, 
                 resource_id, details, ip_address, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
                (
                    log.id,
                    log.user_id,
                    log.username,
                    log.action,
                    log.module,
                    log.resource_type,
                    log.resource_id,
                    log.details,
                    log.ip_address,
                    log.created_at,
                ),
            )

            conn.commit()

        except Exception as e:
            print(f"[ERROR] 记录日志失败: {e}")
        finally:
            conn.close()

    def get_logs(
        self,
        user_id: str = None,
        module: str = None,
        start_date: str = None,
        end_date: str = None,
        limit: int = 100,
    ) -> List[OperationLog]:
        """
        获取操作日志

        Args:
            user_id: 用户ID过滤
            module: 模块过滤
            start_date: 开始日期
            end_date: 结束日期
            limit: 返回数量限制

        Returns:
            操作日志列表
        """
        conn = self._get_connection()
        cursor = conn.cursor()

        query = "SELECT * FROM operation_logs WHERE 1=1"
        params = []

        if user_id:
            query += " AND user_id = ?"
            params.append(user_id)

        if module:
            query += " AND module = ?"
            params.append(module)

        if start_date:
            query += " AND created_at >= ?"
            params.append(start_date)

        if end_date:
            query += " AND created_at <= ?"
            params.append(end_date)

        query += " ORDER BY created_at DESC LIMIT ?"
        params.append(limit)

        cursor.execute(query, params)

        logs = []
        for row in cursor.fetchall():
            logs.append(
                OperationLog(
                    id=row[0],
                    user_id=row[1],
                    username=row[2],
                    action=row[3],
                    module=row[4] or "",
                    resource_type=row[5] or "",
                    resource_id=row[6] or "",
                    details=row[7] or "",
                    ip_address=row[8] or "",
                    created_at=row[9],
                )
            )

        conn.close()
        return logs

    def get_logs_by_resource(
        self, resource_type: str, resource_id: str
    ) -> List[OperationLog]:
        """获取指定资源的操作日志"""
        conn = self._get_connection()
        cursor = conn.cursor()

        cursor.execute(
            """
            SELECT * FROM operation_logs 
            WHERE resource_type = ? AND resource_id = ?
            ORDER BY created_at DESC
        """,
            (resource_type, resource_id),
        )

        logs = []
        for row in cursor.fetchall():
            logs.append(
                OperationLog(
                    id=row[0],
                    user_id=row[1],
                    username=row[2],
                    action=row[3],
                    module=row[4] or "",
                    resource_type=row[5] or "",
                    resource_id=row[6] or "",
                    details=row[7] or "",
                    ip_address=row[8] or "",
                    created_at=row[9],
                )
            )

        conn.close()
        return logs

    def get_user_activity(self, user_id: str, days: int = 30) -> List[OperationLog]:
        """获取用户最近活动"""
        conn = self._get_connection()
        cursor = conn.cursor()

        cursor.execute(
            """
            SELECT * FROM operation_logs 
            WHERE user_id = ? 
            ORDER BY created_at DESC 
            LIMIT ?
        """,
            (user_id, days),
        )

        logs = []
        for row in cursor.fetchall():
            logs.append(
                OperationLog(
                    id=row[0],
                    user_id=row[1],
                    username=row[2],
                    action=row[3],
                    module=row[4] or "",
                    resource_type=row[5] or "",
                    resource_id=row[6] or "",
                    details=row[7] or "",
                    ip_address=row[8] or "",
                    created_at=row[9],
                )
            )

        conn.close()
        return logs

    def clear_old_logs(self, days: int = 90) -> int:
        """
        清理旧日志

        Args:
            days: 保留天数

        Returns:
            删除的日志数量
        """
        conn = self._get_connection()
        cursor = conn.cursor()

        cursor.execute(
            """
            DELETE FROM operation_logs 
            WHERE created_at < datetime('now', ?)
        """,
            (f"-{days} days",),
        )

        count = cursor.rowcount
        conn.commit()
        conn.close()

        return count

    def get_statistics(self) -> Dict[str, Any]:
        """获取日志统计"""
        conn = self._get_connection()
        cursor = conn.cursor()

        stats = {}

        # 按模块统计
        cursor.execute("""
            SELECT module, COUNT(*) FROM operation_logs 
            GROUP BY module
        """)
        stats["by_module"] = dict(cursor.fetchall())

        # 按操作统计
        cursor.execute("""
            SELECT action, COUNT(*) FROM operation_logs 
            GROUP BY action
        """)
        stats["by_action"] = dict(cursor.fetchall())

        # 用户活跃度
        cursor.execute("""
            SELECT username, COUNT(*) as cnt 
            FROM operation_logs 
            GROUP BY user_id 
            ORDER BY cnt DESC 
            LIMIT 10
        """)
        stats["top_users"] = [(row[0], row[1]) for row in cursor.fetchall()]

        # 总日志数
        cursor.execute("SELECT COUNT(*) FROM operation_logs")
        stats["total_logs"] = cursor.fetchone()[0]

        conn.close()
        return stats
