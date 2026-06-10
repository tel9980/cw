#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
会计科目管理器 - 财务系统核心骨架
负责会计科目CRUD、科目余额管理、辅助核算项管理
"""

import sqlite3
import uuid
from datetime import datetime
from decimal import Decimal
from typing import List, Optional, Dict, Tuple, Any


class AccountManager:
    """会计科目管理器"""

    def __init__(self, db_path: str = None, conn: sqlite3.Connection = None):
        """初始化科目管理器

        Args:
            db_path: 数据库文件路径
            conn: 可传入已有连接（优先使用）
        """
        if conn:
            self.conn = conn
            self.conn.row_factory = sqlite3.Row
            self.owns_connection = False
        else:
            from pathlib import Path
            path = db_path or str(Path(__file__).resolve().parent.parent / "oxidation_finance_demo_ready.db")
            self.conn = sqlite3.connect(path)
            self.conn.row_factory = sqlite3.Row
            self.owns_connection = True

    def __del__(self):
        """析构时关闭连接（如果是我们自己创建的）"""
        try:
            if self.owns_connection and self.conn:
                self.conn.close()
        except Exception:
            pass

    # =============== 会计科目CRUD ===============

    def create_account(
        self,
        code: str,
        name: str,
        account_type: str,
        parent_id: Optional[str] = None,
        parent_code: Optional[str] = None,
        level: int = 1,
        balance_direction: str = "借",
        is_controlled: bool = False,
        aux_customer: bool = False,
        aux_supplier: bool = False,
        aux_department: bool = False,
        aux_project: bool = False,
        aux_employee: bool = False,
        sort_order: Optional[int] = None,
        notes: str = "",
    ) -> Tuple[bool, str, Optional[str]]:
        """创建新会计科目

        Returns:
            (成功?, 消息, 科目ID)
        """
        try:
            cursor = self.conn.cursor()

            # 检查科目编码是否已存在
            existing = cursor.execute(
                "SELECT id FROM chart_of_accounts WHERE code = ?", (code,)
            ).fetchone()
            if existing:
                return False, f"科目编码 {code} 已存在", None

            # 检查科目名称是否已存在
            existing_name = cursor.execute(
                "SELECT id FROM chart_of_accounts WHERE name = ?", (name,)
            ).fetchone()
            if existing_name:
                return False, f"科目名称 '{name}' 已存在", None

            # 如果有父级科目，确定level
            if parent_code:
                parent = cursor.execute(
                    "SELECT id, level FROM chart_of_accounts WHERE code = ?", (parent_code,)
                ).fetchone()
                if parent:
                    parent_id = parent["id"]
                    level = parent["level"] + 1

            # 自动计算排序
            if sort_order is None:
                max_sort = cursor.execute(
                    "SELECT COALESCE(MAX(sort_order), 0) FROM chart_of_accounts"
                ).fetchone()[0]
                sort_order = max_sort + 10

            now = datetime.now().isoformat()
            account_id = str(uuid.uuid4())

            cursor.execute(
                """
                INSERT INTO chart_of_accounts
                (id, code, name, account_type, parent_id, level, balance_direction,
                 is_active, is_controlled, aux_customer, aux_supplier,
                 aux_department, aux_project, aux_employee, sort_order, notes,
                 created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, 1, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    account_id, code, name, account_type, parent_id, level,
                    balance_direction, 1 if is_controlled else 0,
                    1 if aux_customer else 0,
                    1 if aux_supplier else 0,
                    1 if aux_department else 0,
                    1 if aux_project else 0,
                    1 if aux_employee else 0,
                    sort_order, notes, now, now,
                ),
            )

            self.conn.commit()
            return True, f"科目创建成功：{code} {name}", account_id

        except Exception as e:
            self.conn.rollback()
            return False, f"创建科目失败：{e}", None

    def get_account_by_code(self, code: str) -> Optional[Dict[str, Any]]:
        """根据科目编码获取科目详情"""
        cursor = self.conn.cursor()
        row = cursor.execute(
            "SELECT * FROM chart_of_accounts WHERE code = ?", (code,)
        ).fetchone()
        return dict(row) if row else None

    def get_account_by_id(self, account_id: str) -> Optional[Dict[str, Any]]:
        """根据ID获取科目"""
        cursor = self.conn.cursor()
        row = cursor.execute(
            "SELECT * FROM chart_of_accounts WHERE id = ?", (account_id,)
        ).fetchone()
        return dict(row) if row else None

    def list_accounts(
        self,
        account_type: Optional[str] = None,
        is_active: Optional[bool] = None,
        level: Optional[int] = None,
    ) -> List[Dict[str, Any]]:
        """获取科目列表（支持筛选）

        返回按科目编码排序的科目列表，适合树形展示
        """
        cursor = self.conn.cursor()

        conditions = []
        params = []
        if account_type:
            conditions.append("account_type = ?")
            params.append(account_type)
        if is_active is not None:
            conditions.append("is_active = ?")
            params.append(1 if is_active else 0)
        if level:
            conditions.append("level = ?")
            params.append(level)

        where = ""
        if conditions:
            where = "WHERE " + " AND ".join(conditions)

        rows = cursor.execute(
            f"SELECT * FROM chart_of_accounts {where} ORDER BY code, sort_order",
            params,
        ).fetchall()

        return [dict(r) for r in rows]

    def get_account_tree(self) -> List[Dict[str, Any]]:
        """获取科目树（层级结构，用于树形展示）"""
        all_accounts = self.list_accounts()

        # 按ID建索引
        account_map = {a["id"]: {**a, "children": []} for a in all_accounts}

        # 建立树：把非一级科目挂到父科目下
        roots = []
        for acc in all_accounts:
            if acc.get("parent_id") and acc["parent_id"] in account_map:
                account_map[acc["parent_id"]]["children"].append(account_map[acc["id"]])
            else:
                roots.append(account_map[acc["id"]])

        return roots

    def update_account(
        self,
        account_id: str,
        name: Optional[str] = None,
        balance_direction: Optional[str] = None,
        is_active: Optional[bool] = None,
        notes: Optional[str] = None,
        aux_flags: Optional[Dict[str, bool]] = None,
    ) -> Tuple[bool, str]:
        """更新科目信息

        注意：不允许修改科目编码和科目类型（控制科目不可删除）
        """
        try:
            cursor = self.conn.cursor()

            # 检查是否为控制科目
            acc = cursor.execute(
                "SELECT is_controlled, code FROM chart_of_accounts WHERE id = ?",
                (account_id,),
            ).fetchone()
            if not acc:
                return False, "科目不存在"

            updates = []
            params = []
            if name is not None:
                updates.append("name = ?")
                params.append(name)
            if balance_direction is not None:
                updates.append("balance_direction = ?")
                params.append(balance_direction)
            if is_active is not None:
                updates.append("is_active = ?")
                params.append(1 if is_active else 0)
            if notes is not None:
                updates.append("notes = ?")
                params.append(notes)
            if aux_flags:
                for key in ["aux_customer", "aux_supplier", "aux_department",
                            "aux_project", "aux_employee"]:
                    if key in aux_flags:
                        updates.append(f"{key} = ?")
                        params.append(1 if aux_flags[key] else 0)

            if not updates:
                return True, "无内容需要更新"

            updates.append("updated_at = ?")
            params.append(datetime.now().isoformat())
            params.append(account_id)

            cursor.execute(
                f"UPDATE chart_of_accounts SET {', '.join(updates)} WHERE id = ?",
                params,
            )
            self.conn.commit()
            return True, "科目更新成功"

        except Exception as e:
            self.conn.rollback()
            return False, f"更新失败：{e}"

    def delete_account(self, account_id: str) -> Tuple[bool, str]:
        """删除科目

        规则：
        1. 控制科目不可删除
        2. 有子科目的不可删除
        3. 已有凭证使用的不可删除
        4. 有余额的不可删除
        """
        try:
            cursor = self.conn.cursor()

            acc = cursor.execute(
                "SELECT is_controlled, code, name FROM chart_of_accounts WHERE id = ?",
                (account_id,),
            ).fetchone()
            if not acc:
                return False, "科目不存在"

            if acc["is_controlled"]:
                return False, f"控制科目不可删除：{acc['code']} {acc['name']}"

            # 检查是否有子科目
            children = cursor.execute(
                "SELECT COUNT(*) FROM chart_of_accounts WHERE parent_id = ?", (account_id,)
            ).fetchone()[0]
            if children > 0:
                return False, "存在下级科目，无法删除"

            # 检查是否已被凭证使用
            used = cursor.execute(
                "SELECT COUNT(*) FROM voucher_lines WHERE account_code = ?", (acc["code"],)
            ).fetchone()[0]
            if used > 0:
                return False, f"该科目已有 {used} 条凭证明细，不可删除"

            # 检查是否有余额
            has_balance = cursor.execute(
                "SELECT COUNT(*) FROM account_balances WHERE account_code = ? AND ABS(closing_balance) > 0.01",
                (acc["code"],),
            ).fetchone()[0]
            if has_balance > 0:
                return False, "该科目存在余额，不可删除"

            cursor.execute("DELETE FROM chart_of_accounts WHERE id = ?", (account_id,))
            self.conn.commit()
            return True, f"删除成功：{acc['code']} {acc['name']}"

        except Exception as e:
            self.conn.rollback()
            return False, f"删除失败：{e}"

    def search_accounts(self, keyword: str, limit: int = 50) -> List[Dict[str, Any]]:
        """搜索科目（按编码或名称模糊匹配）"""
        cursor = self.conn.cursor()
        kw = f"%{keyword}%"
        rows = cursor.execute(
            """
            SELECT * FROM chart_of_accounts
            WHERE code LIKE ? OR name LIKE ?
            AND is_active = 1
            ORDER BY code
            LIMIT ?
            """,
            (kw, kw, limit),
        ).fetchall()
        return [dict(r) for r in rows]

    # =============== 科目余额管理 ===============

    def get_account_balance(
        self, account_code: str, period_id: str
    ) -> Optional[Dict[str, Any]]:
        """获取指定科目在指定期间的余额"""
        cursor = self.conn.cursor()
        row = cursor.execute(
            "SELECT * FROM account_balances WHERE account_code = ? AND period_id = ?",
            (account_code, period_id),
        ).fetchone()
        return dict(row) if row else None

    def get_or_create_balance(
        self, account_code: str, period_id: str, opening_balance: Decimal = Decimal("0")
    ) -> Dict[str, Any]:
        """获取或创建科目在某期间的余额记录"""
        balance = self.get_account_balance(account_code, period_id)
        if balance:
            return balance

        cursor = self.conn.cursor()
        now = datetime.now().isoformat()
        cursor.execute(
            """
            INSERT INTO account_balances
            (id, account_code, period_id, opening_balance, debit_amount,
             credit_amount, closing_balance, created_at, updated_at)
            VALUES (?, ?, ?, 0, 0, 0, ?, ?)
            """,
            (str(uuid.uuid4()), account_code, period_id, 0, now, now),
        )
        self.conn.commit()
        return self.get_account_balance(account_code, period_id)

    def update_balance_from_vouchers(self, period_id: str) -> Tuple[bool, str, Dict]:
        """根据凭证重新计算指定期间所有科目的发生额和期末余额

        核心算法：
        1. 汇总本期间所有"已记账"凭证的借贷发生额
        2. 取上期期末余额作为本期期初
        3. 按科目方向计算期末余额
        """
        try:
            cursor = self.conn.cursor()

            # 1. 获取上期ID（计算期间）
            current = cursor.execute(
                "SELECT start_date, end_date FROM accounting_periods WHERE period_name = ? OR id = ?",
                (period_id, period_id),
            ).fetchone()
            period_name = period_id

            if current:
                period_name = period_id if "-" in period_id else period_id
                # 根据日期获取上期
                start = current["start_date"]
                prev_end = start[:7] + "-01"  # 粗略，用本月1日前一天
                prev_row = cursor.execute(
                    "SELECT id, period_name FROM accounting_periods WHERE end_date < ? ORDER BY end_date DESC LIMIT 1",
                    (start,),
                ).fetchone()
                prev_period_id = prev_row["id"] if prev_row else None
            else:
                prev_period_id = None

            # 2. 汇总本期所有已记账凭证的借贷发生（按科目）
            cursor.execute(
                """
                SELECT
                    vl.account_code,
                    COALESCE(SUM(CAST(vl.debit AS REAL)), 0) AS debit_total,
                    COALESCE(SUM(CAST(vl.credit AS REAL)), 0) AS credit_total
                FROM accounting_vouchers v
                JOIN voucher_lines vl ON v.id = vl.voucher_id
                WHERE (v.accounting_period = ? OR v.accounting_period = ?)
                  AND v.status = '已记账'
                GROUP BY vl.account_code
                """,
                (period_id, period_name),
            )
            period_totals = {r["account_code"]: (Decimal(str(r["debit_total"])),
                                                   Decimal(str(r["credit_total"])))
                             for r in cursor.fetchall()}

            # 3. 处理每一个活跃科目
            accounts = self.list_accounts(is_active=True)
            updated = 0
            for acc in accounts:
                code = acc["code"]
                direction = acc["balance_direction"]
                debit, credit = period_totals.get(code, (Decimal("0"), Decimal("0")))

                # 取上期期末余额作为本期期初
                opening = Decimal("0")
                if prev_period_id:
                    prev_bal = cursor.execute(
                        "SELECT closing_balance FROM account_balances WHERE account_code = ? AND period_id = ?",
                        (code, prev_period_id),
                    ).fetchone()
                    if prev_bal:
                        opening = Decimal(str(prev_bal["closing_balance"]))

                # 计算期末
                if direction == "借":
                    closing = opening + debit - credit
                else:
                    closing = opening + credit - debit

                # 写入或更新
                existing = cursor.execute(
                    "SELECT id FROM account_balances WHERE account_code = ? AND period_id = ?",
                    (code, period_id),
                ).fetchone()
                now = datetime.now().isoformat()
                if existing:
                    cursor.execute(
                        """
                        UPDATE account_balances
                        SET opening_balance = ?, debit_amount = ?, credit_amount = ?,
                            closing_balance = ?, updated_at = ?
                        WHERE id = ?
                        """,
                        (float(opening), float(debit), float(credit), float(closing), now, existing["id"]),
                    )
                else:
                    cursor.execute(
                        """
                        INSERT INTO account_balances
                        (id, account_code, period_id, opening_balance, debit_amount,
                         credit_amount, closing_balance, created_at, updated_at)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                        """,
                        (str(uuid.uuid4()), code, period_id, float(opening),
                         float(debit), float(credit), float(closing), now, now),
                    )
                updated += 1

            self.conn.commit()
            return True, f"已更新 {updated} 个科目的余额", {
                "period": period_id,
                "account_count": updated,
            }

        except Exception as e:
            self.conn.rollback()
            return False, f"余额计算失败：{e}", {}

    def list_balances(
        self,
        period_id: str,
        account_type: Optional[str] = None,
        include_zero: bool = True,
    ) -> List[Dict[str, Any]]:
        """获取期间科目余额表（返回含科目信息的完整列表）"""
        cursor = self.conn.cursor()

        sql = """
            SELECT a.*,
                   COALESCE(b.opening_balance, 0) AS opening_balance,
                   COALESCE(b.debit_amount, 0) AS debit_amount,
                   COALESCE(b.credit_amount, 0) AS credit_amount,
                   COALESCE(b.closing_balance, 0) AS closing_balance
            FROM chart_of_accounts a
            LEFT JOIN account_balances b ON a.code = b.account_code AND b.period_id = ?
            WHERE a.is_active = 1
        """
        params = [period_id]
        if account_type:
            sql += " AND a.account_type = ?"
            params.append(account_type)

        if not include_zero:
            sql += " AND (ABS(b.debit_amount) > 0.01 OR ABS(b.credit_amount) > 0.01 OR ABS(b.closing_balance) > 0.01)"

        sql += " ORDER BY a.code"
        rows = cursor.execute(sql, params).fetchall()
        return [dict(r) for r in rows]

    # =============== 辅助核算项管理 ===============

    def create_department(self, code: str, name: str, manager: str = "",
                          notes: str = "") -> Tuple[bool, str, Optional[str]]:
        """创建部门"""
        try:
            cursor = self.conn.cursor()
            existing = cursor.execute(
                "SELECT id FROM departments WHERE code = ? OR name = ?", (code, name)
            ).fetchone()
            if existing:
                return False, "部门编码或名称已存在", None

            now = datetime.now().isoformat()
            dept_id = str(uuid.uuid4())
            max_sort = cursor.execute("SELECT COALESCE(MAX(sort_order), 0) FROM departments").fetchone()[0]
            cursor.execute(
                """
                INSERT INTO departments (id, code, name, manager, is_active, sort_order, notes, created_at, updated_at)
                VALUES (?, ?, ?, ?, 1, ?, ?, ?, ?)
                """,
                (dept_id, code, name, manager, max_sort + 10, notes, now, now),
            )
            self.conn.commit()
            return True, f"部门创建成功：{code} {name}", dept_id
        except Exception as e:
            self.conn.rollback()
            return False, f"创建失败：{e}", None

    def list_departments(self) -> List[Dict[str, Any]]:
        """获取部门列表"""
        cursor = self.conn.cursor()
        rows = cursor.execute(
            "SELECT * FROM departments ORDER BY sort_order, code"
        ).fetchall()
        return [dict(r) for r in rows]

    def create_project(self, code: str, name: str, status: str = "进行中",
                       budget: Decimal = Decimal("0"), manager: str = "",
                       start_date: str = None, end_date: str = None,
                       notes: str = "") -> Tuple[bool, str, Optional[str]]:
        """创建项目"""
        try:
            cursor = self.conn.cursor()
            existing = cursor.execute(
                "SELECT id FROM projects WHERE code = ? OR name = ?", (code, name)
            ).fetchone()
            if existing:
                return False, "项目编码或名称已存在", None

            now = datetime.now().isoformat()
            project_id = str(uuid.uuid4())
            cursor.execute(
                """
                INSERT INTO projects (id, code, name, status, start_date, end_date,
                                     budget, manager, notes, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (project_id, code, name, status, start_date, end_date,
                 float(budget), manager, notes, now, now),
            )
            self.conn.commit()
            return True, f"项目创建成功：{code} {name}", project_id
        except Exception as e:
            self.conn.rollback()
            return False, f"创建失败：{e}", None

    def list_projects(self, status: Optional[str] = None) -> List[Dict[str, Any]]:
        """获取项目列表"""
        cursor = self.conn.cursor()
        if status:
            rows = cursor.execute(
                "SELECT * FROM projects WHERE status = ? ORDER BY code", (status,)
            ).fetchall()
        else:
            rows = cursor.execute("SELECT * FROM projects ORDER BY code").fetchall()
        return [dict(r) for r in rows]

    # =============== 标准科目初始化 ===============

    def init_standard_accounts(self) -> Tuple[bool, str, Dict]:
        """初始化小企业会计准则的标准科目

        这是系统初始化的关键步骤，会建立完整的科目骨架
        """
        try:
            cursor = self.conn.cursor()

            # 检查是否已经初始化
            count = cursor.execute("SELECT COUNT(*) FROM chart_of_accounts").fetchone()[0]
            if count > 0:
                return True, "科目已存在，跳过初始化", {"count": count, "action": "skipped"}

            # 小企业会计准则标准科目表（精简版）
            # 结构：(编码, 名称, 类型, 余额方向, 控制科目, [辅助核算项])
            standard_accounts = [
                # ============= 资产类 =============
                ("1001", "库存现金", "资产类", "借", True, []),
                ("1002", "银行存款", "资产类", "借", True, []),
                ("1012", "其他货币资金", "资产类", "借", True, []),
                ("1101", "短期投资", "资产类", "借", True, []),
                ("1121", "应收票据", "资产类", "借", True, []),
                ("1122", "应收账款", "资产类", "借", True, ["客户"]),
                ("1123", "预付账款", "资产类", "借", True, ["供应商"]),
                ("1131", "应收股利", "资产类", "借", True, []),
                ("1132", "应收利息", "资产类", "借", True, []),
                ("1221", "其他应收款", "资产类", "借", True, ["客户", "员工"]),
                ("1401", "材料采购", "资产类", "借", True, []),
                ("1402", "在途物资", "资产类", "借", True, []),
                ("1403", "原材料", "资产类", "借", True, []),
                ("1404", "材料成本差异", "资产类", "借", True, []),
                ("1405", "库存商品", "资产类", "借", True, []),
                ("1408", "委托加工物资", "资产类", "借", True, ["供应商"]),
                ("1411", "周转材料", "资产类", "借", True, []),
                ("1501", "消耗性生物资产", "资产类", "借", True, []),
                ("1511", "长期股权投资", "资产类", "借", True, []),
                ("1601", "固定资产", "资产类", "借", True, []),
                ("1602", "累计折旧", "资产类", "贷", True, []),
                ("1604", "在建工程", "资产类", "借", True, []),
                ("1605", "工程物资", "资产类", "借", True, []),
                ("1606", "固定资产清理", "资产类", "借", True, []),
                ("1701", "无形资产", "资产类", "借", True, []),
                ("1702", "累计摊销", "资产类", "贷", True, []),
                ("1801", "长期待摊费用", "资产类", "借", True, []),
                ("1901", "待处理财产损溢", "资产类", "借", True, []),

                # ============= 负债类 =============
                ("2001", "短期借款", "负债类", "贷", True, []),
                ("2201", "应付票据", "负债类", "贷", True, []),
                ("2202", "应付账款", "负债类", "贷", True, ["供应商"]),
                ("2203", "预收账款", "负债类", "贷", True, ["客户"]),
                ("2211", "应付职工薪酬", "负债类", "贷", True, ["部门"]),
                ("2221", "应交税费", "负债类", "贷", True, []),
                ("2231", "应付利息", "负债类", "贷", True, []),
                ("2232", "应付利润", "负债类", "贷", True, []),
                ("2241", "其他应付款", "负债类", "贷", True, []),
                ("2401", "递延收益", "负债类", "贷", True, []),
                ("2501", "长期借款", "负债类", "贷", True, []),
                ("2701", "长期应付款", "负债类", "贷", True, []),

                # ============= 所有者权益类 =============
                ("3001", "实收资本", "权益类", "贷", True, []),
                ("3002", "资本公积", "权益类", "贷", True, []),
                ("3101", "盈余公积", "权益类", "贷", True, []),
                ("3103", "本年利润", "权益类", "贷", True, []),
                ("3104", "利润分配", "权益类", "贷", True, []),

                # ============= 成本类 =============
                ("4001", "生产成本", "成本类", "借", True, ["项目", "部门"]),
                ("4101", "制造费用", "成本类", "借", True, ["部门"]),
                ("4301", "研发支出", "成本类", "借", True, ["项目"]),
                ("4401", "工程施工", "成本类", "借", True, ["项目"]),

                # ============= 损益类（收入） =============
                ("5001", "主营业务收入", "损益类", "贷", True, ["客户", "项目"]),
                ("5051", "其他业务收入", "损益类", "贷", True, []),
                ("5111", "投资收益", "损益类", "贷", True, []),
                ("5301", "营业外收入", "损益类", "贷", True, []),

                # ============= 损益类（费用） =============
                ("5401", "主营业务成本", "损益类", "借", True, []),
                ("5402", "其他业务成本", "损益类", "借", True, []),
                ("5403", "税金及附加", "损益类", "借", True, []),
                ("5601", "销售费用", "损益类", "借", True, ["部门"]),
                ("5602", "管理费用", "损益类", "借", True, ["部门"]),
                ("5603", "财务费用", "损益类", "借", True, []),
                ("5711", "营业外支出", "损益类", "借", True, []),
                ("5801", "所得税费用", "损益类", "借", True, []),
            ]

            now = datetime.now().isoformat()
            created_count = 0
            for idx, (code, name, acct_type, direction, controlled, aux) in enumerate(standard_accounts):
                aux_customer = "客户" in aux
                aux_supplier = "供应商" in aux
                aux_department = "部门" in aux
                aux_project = "项目" in aux
                aux_employee = "员工" in aux

                cursor.execute(
                    """
                    INSERT INTO chart_of_accounts
                    (id, code, name, account_type, parent_id, level, balance_direction,
                     is_active, is_controlled, aux_customer, aux_supplier,
                     aux_department, aux_project, aux_employee, sort_order, notes,
                     created_at, updated_at)
                    VALUES (?, ?, ?, ?, NULL, 1, ?, 1, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        str(uuid.uuid4()), code, name, acct_type, direction,
                        1 if controlled else 0,
                        1 if aux_customer else 0,
                        1 if aux_supplier else 0,
                        1 if aux_department else 0,
                        1 if aux_project else 0,
                        1 if aux_employee else 0,
                        (idx + 1) * 10,
                        "系统预设-小企业会计准则", now, now,
                    ),
                )
                created_count += 1

            self.conn.commit()
            return True, f"成功初始化 {created_count} 个标准会计科目", {
                "count": created_count,
                "action": "initialized",
            }

        except Exception as e:
            self.conn.rollback()
            return False, f"初始化失败：{e}", {}

    def get_init_status(self) -> Dict[str, Any]:
        """获取初始化状态"""
        cursor = self.conn.cursor()
        account_count = cursor.execute(
            "SELECT COUNT(*) FROM chart_of_accounts"
        ).fetchone()[0]
        controlled_count = cursor.execute(
            "SELECT COUNT(*) FROM chart_of_accounts WHERE is_controlled = 1"
        ).fetchone()[0]
        by_type = cursor.execute(
            """
            SELECT account_type, COUNT(*) AS cnt FROM chart_of_accounts
            GROUP BY account_type ORDER BY account_type
            """
        ).fetchall()

        return {
            "total_accounts": account_count,
            "controlled_accounts": controlled_count,
            "is_initialized": account_count > 0,
            "by_type": {r["account_type"]: r["cnt"] for r in by_type},
        }

    def get_account_type_list(self) -> List[str]:
        """获取所有科目类型列表"""
        return ["资产类", "负债类", "权益类", "成本类", "损益类"]
