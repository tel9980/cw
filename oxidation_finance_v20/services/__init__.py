#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Web应用服务层 - 为Web路由提供业务逻辑和数据访问
"""

from datetime import date, datetime
from decimal import Decimal
from typing import Any, Dict, List, Optional

from ..database.db_manager import DatabaseManager


class WebService:
    """Web应用服务 - 封装所有数据操作，隔离Web层与数据库"""

    def __init__(self, db_manager: DatabaseManager):
        """
        初始化Web服务

        Args:
            db_manager: 已连接的数据库管理器
        """
        self.db = db_manager

    # ==================== 辅助方法 ====================

    def _get_connection(self):
        """获取数据库连接"""
        return self.db.conn

    # ==================== 仪表盘 ====================

    def get_dashboard_stats(self) -> Dict[str, Any]:
        """获取首页统计数据"""
        conn = self._get_connection()
        if not conn:
            raise RuntimeError("数据库未连接")

        today = date.today().isoformat()

        today_income = (
            conn.execute(
                "SELECT SUM(amount) FROM incomes WHERE income_date = ?", (today,)
            ).fetchone()[0]
            or 0
        )
        today_expense = (
            conn.execute(
                "SELECT SUM(amount) FROM expenses WHERE expense_date = ?", (today,)
            ).fetchone()[0]
            or 0
        )
        pending_orders = (
            conn.execute(
                "SELECT COUNT(*) FROM processing_orders WHERE status IN ('待加工', '加工中')"
            ).fetchone()[0]
            or 0
        )
        unpaid_orders = (
            conn.execute(
                "SELECT COUNT(*) FROM processing_orders WHERE received_amount < total_amount"
            ).fetchone()[0]
            or 0
        )
        month_start = date.today().replace(day=1).isoformat()
        month_income = (
            conn.execute(
                "SELECT SUM(amount) FROM incomes WHERE income_date >= ?", (month_start,)
            ).fetchone()[0]
            or 0
        )
        month_expense = (
            conn.execute(
                "SELECT SUM(amount) FROM expenses WHERE expense_date >= ?",
                (month_start,),
            ).fetchone()[0]
            or 0
        )

        return {
            "today_income": float(today_income),
            "today_expense": float(today_expense),
            "today_profit": float(today_income - today_expense),
            "pending_orders": pending_orders,
            "unpaid_orders": unpaid_orders,
            "month_income": float(month_income),
            "month_expense": float(month_expense),
            "month_profit": float(month_income - month_expense),
        }

    def get_recent_orders(self, limit: int = 5) -> List[Any]:
        """获取最近订单"""
        conn = self._get_connection()
        if not conn:
            return []
        return conn.execute(
            "SELECT order_no, customer_name, total_amount, status, order_date FROM processing_orders ORDER BY order_date DESC LIMIT ?",
            (limit,),
        ).fetchall()

    # ==================== 订单管理 ====================

    def create_order(self, form_data: Dict[str, Any]) -> str:
        """
        创建新订单

        Args:
            form_data: 表单数据

        Returns:
            新订单ID

        Raises:
            ValueError: 如果表单数据无效
        """
        conn = self._get_connection()
        if not conn:
            raise RuntimeError("数据库未连接")

        # 验证必填字段
        required = [
            "customer_name",
            "item_description",
            "quantity",
            "unit_price",
            "pricing_unit",
        ]
        for field in required:
            if field not in form_data or not form_data[field]:
                raise ValueError(f"缺少必填字段: {field}")

        # 生成订单号
        order_no = f"OX{date.today().strftime('%Y%m')}{conn.execute('SELECT COUNT(*) FROM processing_orders').fetchone()[0] + 1:03d}"

        # 获取或创建客户
        customer_name = form_data["customer_name"]
        customer = conn.execute(
            "SELECT id FROM customers WHERE name = ?", (customer_name,)
        ).fetchone()

        if not customer:
            import uuid

            customer_id = str(uuid.uuid4())
            conn.execute(
                "INSERT INTO customers (id, name, created_at) VALUES (?, ?, ?)",
                (customer_id, customer_name, datetime.now().isoformat()),
            )
        else:
            customer_id = customer["id"]

        # 计算金额
        quantity = float(form_data["quantity"])
        unit_price = float(form_data["unit_price"])
        total_amount = quantity * unit_price

        # 插入订单
        import uuid

        order_id = str(uuid.uuid4())
        conn.execute(
            """
            INSERT INTO processing_orders 
            (id, order_no, customer_id, customer_name, item_description, quantity,
             pricing_unit, unit_price, total_amount, processes, status, order_date, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                order_id,
                order_no,
                customer_id,
                customer_name,
                form_data["item_description"],
                quantity,
                form_data["pricing_unit"],
                unit_price,
                total_amount,
                form_data.get("processes", "氧化"),
                "待加工",
                date.today().isoformat(),
                datetime.now().isoformat(),
                datetime.now().isoformat(),
            ),
        )
        conn.commit()
        return order_id

    def get_orders(self, status: Optional[str] = None) -> List[Any]:
        """
        获取订单列表

        Args:
            status: 按状态筛选（可选）

        Returns:
            订单Row列表
        """
        conn = self._get_connection()
        if not conn:
            return []
        if status:
            return conn.execute(
                "SELECT * FROM processing_orders WHERE status = ? ORDER BY order_date DESC",
                (status,),
            ).fetchall()
        else:
            return conn.execute(
                "SELECT * FROM processing_orders ORDER BY order_date DESC LIMIT 50"
            ).fetchall()

    def get_order(self, order_id: str) -> Optional[Any]:
        """获取订单详情"""
        conn = self._get_connection()
        if not conn:
            return None
        return conn.execute(
            "SELECT * FROM processing_orders WHERE id = ?", (order_id,)
        ).fetchone()

    def update_order(self, order_id: str, form_data: Dict[str, Any]) -> bool:
        """更新订单"""
        conn = self._get_connection()
        if not conn:
            return False

        order = self.get_order(order_id)
        if not order:
            return False

        # 构建更新字段
        updates = []
        params = []

        if "customer_name" in form_data:
            updates.append("customer_name = ?")
            params.append(form_data["customer_name"])
        if "item_description" in form_data:
            updates.append("item_description = ?")
            params.append(form_data["item_description"])
        if "quantity" in form_data and "unit_price" in form_data:
            quantity = float(form_data["quantity"])
            unit_price = float(form_data["unit_price"])
            total_amount = quantity * unit_price
            updates.extend(["quantity = ?", "unit_price = ?", "total_amount = ?"])
            params.extend([quantity, unit_price, total_amount])
        if "processes" in form_data:
            updates.append("processes = ?")
            params.append(form_data["processes"])
        if "status" in form_data:
            updates.append("status = ?")
            params.append(form_data["status"])

        updates.append("updated_at = ?")
        params.append(datetime.now().isoformat())
        params.append(order_id)

        if not updates:
            return False

        conn.execute(
            f"UPDATE processing_orders SET {', '.join(updates)} WHERE id = ?",
            params,
        )
        conn.commit()
        return True

    def delete_order(self, order_id: str) -> bool:
        """删除订单"""
        conn = self._get_connection()
        if not conn:
            return False
        conn.execute("DELETE FROM processing_orders WHERE id = ?", (order_id,))
        conn.commit()
        return True

    # ==================== 收入管理 ====================

    def create_income(self, form_data: Dict[str, Any]) -> str:
        """
        创建收入记录

        Args:
            form_data: 表单数据

        Returns:
            收入记录ID
        """
        conn = self._get_connection()
        if not conn:
            raise RuntimeError("数据库未连接")

        required = ["customer_name", "amount", "bank_type"]
        for field in required:
            if field not in form_data or not form_data[field]:
                raise ValueError(f"缺少必填字段: {field}")

        import uuid

        income_id = str(uuid.uuid4())
        conn.execute(
            """
            INSERT INTO incomes (id, customer_name, amount, bank_type, income_date, notes, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                income_id,
                form_data["customer_name"],
                float(form_data["amount"]),
                form_data["bank_type"],
                form_data.get("income_date", date.today().isoformat()),
                form_data.get("description", ""),
                datetime.now().isoformat(),
            ),
        )
        conn.commit()
        return income_id

    def get_income(self, income_id: str) -> Optional[Any]:
        """获取收入记录详情"""
        conn = self._get_connection()
        if not conn:
            return None
        return conn.execute(
            "SELECT * FROM incomes WHERE id = ?", (income_id,)
        ).fetchone()

    def update_income(self, income_id: str, form_data: Dict[str, Any]) -> bool:
        """更新收入记录"""
        conn = self._get_connection()
        if not conn:
            return False

        income = self.get_income(income_id)
        if not income:
            return False

        updates = []
        params = []

        if "customer_name" in form_data:
            updates.append("customer_name = ?")
            params.append(form_data["customer_name"])
        if "amount" in form_data:
            updates.append("amount = ?")
            params.append(float(form_data["amount"]))
        if "bank_type" in form_data:
            updates.append("bank_type = ?")
            params.append(form_data["bank_type"])
        if "income_date" in form_data:
            updates.append("income_date = ?")
            params.append(form_data["income_date"])
        if "description" in form_data:
            updates.append("notes = ?")
            params.append(form_data["description"])

        updates.append("updated_at = ?")
        params.append(datetime.now().isoformat())
        params.append(income_id)

        if not updates:
            return False

        conn.execute(
            f"UPDATE incomes SET {', '.join(updates)} WHERE id = ?",
            params,
        )
        conn.commit()
        return True

    # ==================== 支出管理 ====================

    def create_expense(self, form_data: Dict[str, Any]) -> str:
        """
        创建支出记录

        Args:
            form_data: 表单数据

        Returns:
            支出记录ID
        """
        conn = self._get_connection()
        if not conn:
            raise RuntimeError("数据库未连接")

        required = ["expense_type", "amount", "bank_type"]
        for field in required:
            if field not in form_data or not form_data[field]:
                raise ValueError(f"缺少必填字段: {field}")

        import uuid

        expense_id = str(uuid.uuid4())
        conn.execute(
            """
            INSERT INTO expenses (id, expense_type, supplier_name, amount, bank_type,
                                expense_date, description, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                expense_id,
                form_data["expense_type"],
                form_data.get("supplier_name", ""),
                float(form_data["amount"]),
                form_data["bank_type"],
                form_data.get("expense_date", date.today().isoformat()),
                form_data.get("description", ""),
                datetime.now().isoformat(),
            ),
        )
        conn.commit()
        return expense_id

    def get_expense(self, expense_id: str) -> Optional[Any]:
        """获取支出记录详情"""
        conn = self._get_connection()
        if not conn:
            return None
        return conn.execute(
            "SELECT * FROM expenses WHERE id = ?", (expense_id,)
        ).fetchone()

    def update_expense(self, expense_id: str, form_data: Dict[str, Any]) -> bool:
        """更新支出记录"""
        conn = self._get_connection()
        if not conn:
            return False

        expense = self.get_expense(expense_id)
        if not expense:
            return False

        updates = []
        params = []

        if "expense_type" in form_data:
            updates.append("expense_type = ?")
            params.append(form_data["expense_type"])
        if "supplier_name" in form_data:
            updates.append("supplier_name = ?")
            params.append(form_data["supplier_name"])
        if "amount" in form_data:
            updates.append("amount = ?")
            params.append(float(form_data["amount"]))
        if "bank_type" in form_data:
            updates.append("bank_type = ?")
            params.append(form_data["bank_type"])
        if "expense_date" in form_data:
            updates.append("expense_date = ?")
            params.append(form_data["expense_date"])
        if "description" in form_data:
            updates.append("description = ?")
            params.append(form_data["description"])

        updates.append("updated_at = ?")
        params.append(datetime.now().isoformat())
        params.append(expense_id)

        if not updates:
            return False

        conn.execute(
            f"UPDATE expenses SET {', '.join(updates)} WHERE id = ?",
            params,
        )
        conn.commit()
        return True

    # ==================== 客户管理 ====================

    def get_customers(self) -> List[Any]:
        """获取所有客户列表"""
        conn = self._get_connection()
        if not conn:
            return []
        return conn.execute("SELECT * FROM customers ORDER BY name").fetchall()

    # ==================== 报表数据 ====================

    def get_reports_summary(self) -> Dict[str, Any]:
        """获取报表汇总数据"""
        conn = self._get_connection()
        if not conn:
            return {}

        total_income = (
            conn.execute("SELECT SUM(amount) FROM incomes").fetchone()[0] or 0
        )
        total_expense = (
            conn.execute("SELECT SUM(amount) FROM expenses").fetchone()[0] or 0
        )
        order_count = (
            conn.execute("SELECT COUNT(*) FROM processing_orders").fetchone()[0] or 0
        )

        # 月度统计
        monthly_stats = conn.execute("""
            SELECT 
                strftime('%Y-%m', income_date) as month,
                COALESCE(SUM(i.amount), 0) as income,
                0 as expense
            FROM incomes i
            GROUP BY month
            UNION ALL
            SELECT 
                strftime('%Y-%m', expense_date) as month,
                0 as income,
                COALESCE(SUM(e.amount), 0) as expense
            FROM expenses e
            GROUP BY month
            ORDER BY month
        """).fetchall()

        # 聚合月度数据
        monthly_data = {}
        for row in monthly_stats:
            month = row["month"]
            if month not in monthly_data:
                monthly_data[month] = {"income": 0, "expense": 0}
            monthly_data[month]["income"] += row["income"]
            monthly_data[month]["expense"] += row["expense"]

        monthly_stats_list = [
            {
                "month": k,
                "income": v["income"],
                "expense": v["expense"],
                "profit": v["income"] - v["expense"],
            }
            for k, v in monthly_data.items()
        ]
        monthly_stats_list = sorted(
            monthly_stats_list, key=lambda x: x["month"], reverse=True
        )[:12]

        # 客户排名
        top_customers = conn.execute("""
            SELECT c.name, COUNT(o.id) as order_count, COALESCE(SUM(o.total_amount), 0) as total
            FROM customers c
            LEFT JOIN processing_orders o ON c.id = o.customer_id
            GROUP BY c.id
            ORDER BY total DESC
            LIMIT 10
        """).fetchall()

        # 支出分类
        expense_by_type = conn.execute("""
            SELECT expense_type, SUM(amount) as total
            FROM expenses
            GROUP BY expense_type
            ORDER BY total DESC
        """).fetchall()

        return {
            "total_income": float(total_income),
            "total_expense": float(total_expense),
            "order_count": order_count,
            "monthly_stats": monthly_stats_list,
            "top_customers": top_customers,
            "expense_by_type": expense_by_type,
        }

    # ==================== 搜索与统计 ====================

    def search(self, keyword: str) -> Dict[str, Any]:
        """
        全局搜索

        Args:
            keyword: 搜索关键词

        Returns:
            包含客户和订单的字典
        """
        conn = self._get_connection()
        if not conn or not keyword:
            return {"customers": [], "orders": []}

        kw = f"%{keyword}%"
        customers = conn.execute(
            "SELECT name, contact FROM customers WHERE name LIKE ? LIMIT 5",
            (kw,),
        ).fetchall()
        orders = conn.execute(
            "SELECT order_no, customer_name, total_amount FROM processing_orders WHERE order_no LIKE ? OR customer_name LIKE ? LIMIT 5",
            (kw, kw),
        ).fetchall()

        return {
            "customers": [
                {"name": c["name"], "contact": c["contact"]} for c in customers
            ],
            "orders": [
                {
                    "order_no": o["order_no"],
                    "customer": o["customer_name"],
                    "amount": float(o["total_amount"]),
                }
                for o in orders
            ],
        }

    def get_stats(self) -> Dict[str, Any]:
        """获取统计API数据"""
        conn = self._get_connection()
        if not conn:
            return {}

        today = date.today().isoformat()
        stats = {
            "today_income": conn.execute(
                "SELECT SUM(amount) FROM incomes WHERE income_date = ?", (today,)
            ).fetchone()[0]
            or 0,
            "today_expense": conn.execute(
                "SELECT SUM(amount) FROM expenses WHERE expense_date = ?", (today,)
            ).fetchone()[0]
            or 0,
            "pending_orders": conn.execute(
                "SELECT COUNT(*) FROM processing_orders WHERE status IN ('待加工', '加工中')"
            ).fetchone()[0]
            or 0,
            "unpaid_orders": conn.execute(
                "SELECT COUNT(*) FROM processing_orders WHERE received_amount < total_amount"
            ).fetchone()[0]
            or 0,
        }
        # 转换为浮点数以便JSON序列化
        return {k: float(v) if isinstance(v, Decimal) else v for k, v in stats.items()}
