#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
会计凭证管理器 - 负责凭证的创建、审核、记账等功能
符合小企业会计准则的凭证管理
"""

from decimal import Decimal
from datetime import date, datetime
from typing import Optional, List, Dict, Tuple
import json

from ..models.accounting_models import (
    AccountingVoucher,
    VoucherLine,
    VoucherStatus,
    AccountCode
)
from ..models.business_models import Income, Expense, ProcessingOrder
from ..database.db_manager import DatabaseManager


class VoucherManager:
    """会计凭证管理器"""
    
    def __init__(self, db_manager: DatabaseManager):
        """初始化凭证管理器"""
        self.db = db_manager
    
    def _generate_voucher_no(self, voucher_date: date) -> str:
        """生成凭证编号
        
        格式：YYYY-MM-001
        """
        period = voucher_date.strftime("%Y-%m")
        # 查询当前期间的凭证数量
        conn = getattr(self.db, 'conn', None)
        if conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT COUNT(*) FROM accounting_vouchers 
                WHERE accounting_period = ?
                """,
                (period,)
            )
            count = cursor.fetchone()[0]
        else:
            count = 0
        
        seq = count + 1
        return f"{period}-{seq:03d}"
    
    def create_voucher_from_income(
        self,
        income: Income,
        accounting_period: str
    ) -> AccountingVoucher:
        """根据收入记录自动生成会计凭证
        
        分录：
        借：银行存款/库存现金
        贷：主营业务收入
        """
        voucher = AccountingVoucher(
            voucher_no=self._generate_voucher_no(income.income_date),
            voucher_date=income.income_date,
            accounting_period=accounting_period,
            summary=f"收{income.customer_name}货款",
            created_by="系统自动",
            source_type="INCOME",
            source_id=income.id
        )
        
        # 借方：银行存款
        bank_line = VoucherLine(
            voucher_id=voucher.id,
            account_code=AccountCode.BANK_DEPOSIT.code,
            account_name=AccountCode.BANK_DEPOSIT.display_name,
            debit=income.amount,
            credit=Decimal("0"),
            summary=f"收{income.customer_name}货款",
            related_entity_type="INCOME",
            related_entity_id=income.id
        )
        
        # 贷方：主营业务收入
        income_line = VoucherLine(
            voucher_id=voucher.id,
            account_code=AccountCode.MAIN_BUSINESS_INCOME.code,
            account_name=AccountCode.MAIN_BUSINESS_INCOME.display_name,
            debit=Decimal("0"),
            credit=income.amount,
            summary=f"收{income.customer_name}货款",
            related_entity_type="INCOME",
            related_entity_id=income.id
        )
        
        voucher.lines = [bank_line, income_line]
        voucher.calculate_totals()
        
        # 保存凭证
        self._save_voucher(voucher)
        
        return voucher
    
    def create_voucher_from_expense(
        self,
        expense: Expense,
        accounting_period: str
    ) -> AccountingVoucher:
        """根据支出记录自动生成会计凭证
        
        分录：
        借：主营业务成本/管理费用等
        贷：银行存款
        """
        # 根据支出类型确定借方科目
        debit_account = self._get_debit_account_for_expense(expense.expense_type)
        
        voucher = AccountingVoucher(
            voucher_no=self._generate_voucher_no(expense.expense_date),
            voucher_date=expense.expense_date,
            accounting_period=accounting_period,
            summary=expense.description or f"付{expense.supplier_name}款",
            created_by="系统自动",
            source_type="EXPENSE",
            source_id=expense.id
        )
        
        # 借方：对应费用科目
        debit_line = VoucherLine(
            voucher_id=voucher.id,
            account_code=debit_account.code,
            account_name=debit_account.display_name,
            debit=expense.amount,
            credit=Decimal("0"),
            summary=expense.description or f"付{expense.supplier_name}款",
            related_entity_type="EXPENSE",
            related_entity_id=expense.id
        )
        
        # 贷方：银行存款
        credit_line = VoucherLine(
            voucher_id=voucher.id,
            account_code=AccountCode.BANK_DEPOSIT.code,
            account_name=AccountCode.BANK_DEPOSIT.display_name,
            debit=Decimal("0"),
            credit=expense.amount,
            summary=expense.description or f"付{expense.supplier_name}款",
            related_entity_type="EXPENSE",
            related_entity_id=expense.id
        )
        
        voucher.lines = [debit_line, credit_line]
        voucher.calculate_totals()
        
        # 保存凭证
        self._save_voucher(voucher)
        
        return voucher
    
    def create_voucher_for_order_completion(
        self,
        order: ProcessingOrder,
        accounting_period: str,
        material_cost: Decimal,
        labor_cost: Decimal,
        manufacturing_expense: Decimal
    ) -> AccountingVoucher:
        """订单完工时生成结转成本凭证
        
        分录：
        借：主营业务成本
        贷：生产成本
        """
        total_cost = material_cost + labor_cost + manufacturing_expense
        
        voucher = AccountingVoucher(
            voucher_no=self._generate_voucher_no(date.today()),
            voucher_date=date.today(),
            accounting_period=accounting_period,
            summary=f"结转订单{order.order_no}成本",
            created_by="系统自动",
            source_type="ORDER",
            source_id=order.id
        )
        
        # 借方：主营业务成本
        debit_line = VoucherLine(
            voucher_id=voucher.id,
            account_code=AccountCode.MAIN_BUSINESS_COST.code,
            account_name=AccountCode.MAIN_BUSINESS_COST.display_name,
            debit=total_cost,
            credit=Decimal("0"),
            summary=f"结转订单{order.order_no}成本",
            related_entity_type="ORDER",
            related_entity_id=order.id
        )
        
        # 贷方：生产成本
        credit_line = VoucherLine(
            voucher_id=voucher.id,
            account_code=AccountCode.PRODUCTION_COSTS.code,
            account_name=AccountCode.PRODUCTION_COSTS.display_name,
            debit=Decimal("0"),
            credit=total_cost,
            summary=f"结转订单{order.order_no}成本",
            related_entity_type="ORDER",
            related_entity_id=order.id
        )
        
        voucher.lines = [debit_line, credit_line]
        voucher.calculate_totals()
        
        # 保存凭证
        self._save_voucher(voucher)
        
        return voucher
    
    def _get_debit_account_for_expense(self, expense_type) -> AccountCode:
        """根据支出类型确定借方科目"""
        expense_name = expense_type.value if hasattr(expense_type, 'value') else str(expense_type)
        
        # 委外加工费 -> 主营业务成本
        if "委外" in expense_name or "加工" in expense_name:
            return AccountCode.MAIN_BUSINESS_COST
        
        # 原材料 -> 主营业务成本
        raw_materials = ["三酸", "片碱", "亚钠", "色粉", "除油剂", "挂具"]
        if any(m in expense_name for m in raw_materials):
            return AccountCode.MAIN_BUSINESS_COST
        
        # 房租、水电费 -> 制造费用
        if "房租" in expense_name or "水电费" in expense_name:
            return AccountCode.MANUFACTURING_EXPENSES
        
        # 工资 -> 管理费用或生产成本
        if "工资" in expense_name:
            return AccountCode.ADMINISTRATIVE_EXPENSES
        
        # 默认 -> 管理费用
        return AccountCode.ADMINISTRATIVE_EXPENSES
    
    def _save_voucher(self, voucher: AccountingVoucher):
        """保存凭证到数据库"""
        conn = getattr(self.db, 'conn', None)
        if not conn:
            return
        
        try:
            cursor = conn.cursor()
            
            # 保存凭证头
            cursor.execute(
                """
                INSERT OR REPLACE INTO accounting_vouchers
                (id, voucher_no, voucher_date, accounting_period, summary,
                 total_debit, total_credit, created_by, reviewed_by, posted_by,
                 reviewed_at, posted_at, status, source_type, source_id, notes,
                 created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    voucher.id,
                    voucher.voucher_no,
                    voucher.voucher_date.isoformat(),
                    voucher.accounting_period,
                    voucher.summary,
                    str(voucher.total_debit),
                    str(voucher.total_credit),
                    voucher.created_by,
                    voucher.reviewed_by,
                    voucher.posted_by,
                    voucher.reviewed_at.isoformat() if voucher.reviewed_at else None,
                    voucher.posted_at.isoformat() if voucher.posted_at else None,
                    voucher.status.value,
                    voucher.source_type,
                    voucher.source_id,
                    voucher.notes,
                    voucher.created_at.isoformat(),
                    voucher.updated_at.isoformat()
                )
            )
            
            # 删除旧的凭证明细
            cursor.execute(
                "DELETE FROM voucher_lines WHERE voucher_id = ?",
                (voucher.id,)
            )
            
            # 保存凭证明细
            for line in voucher.lines:
                cursor.execute(
                    """
                    INSERT INTO voucher_lines
                    (id, voucher_id, account_code, account_name, debit, credit,
                     summary, related_entity_type, related_entity_id)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        line.id,
                        line.voucher_id,
                        line.account_code,
                        line.account_name,
                        str(line.debit),
                        str(line.credit),
                        line.summary,
                        line.related_entity_type,
                        line.related_entity_id
                    )
                )
            
            conn.commit()
            
            # 记录审计日志
            try:
                self.db.log_audit(
                    operation_type="CREATE",
                    entity_type="VOUCHER",
                    entity_id=voucher.id,
                    entity_name=voucher.voucher_no,
                    old_value=None,
                    new_value=str(voucher),
                    description=f"创建会计凭证 {voucher.voucher_no}"
                )
            except Exception:
                pass
                
        except Exception as e:
            conn.rollback()
            raise
    
    def review_voucher(
        self,
        voucher_id: str,
        reviewer: str
    ) -> Tuple[bool, str]:
        """审核凭证"""
        voucher = self.get_voucher_by_id(voucher_id)
        if not voucher:
            return False, "凭证不存在"
        
        if voucher.status != VoucherStatus.DRAFT:
            return False, "只有草稿状态的凭证才能审核"
        
        if not voucher.validate_balance():
            return False, "凭证借贷不平衡，无法审核"
        
        voucher.status = VoucherStatus.REVIEWED
        voucher.reviewed_by = reviewer
        voucher.reviewed_at = datetime.now()
        voucher.updated_at = datetime.now()
        
        self._save_voucher(voucher)
        
        return True, f"凭证 {voucher.voucher_no} 审核成功"
    
    def post_voucher(
        self,
        voucher_id: str,
        poster: str
    ) -> Tuple[bool, str]:
        """记账"""
        voucher = self.get_voucher_by_id(voucher_id)
        if not voucher:
            return False, "凭证不存在"
        
        if voucher.status != VoucherStatus.REVIEWED:
            return False, "只有已审核的凭证才能记账"
        
        voucher.status = VoucherStatus.POSTED
        voucher.posted_by = poster
        voucher.posted_at = datetime.now()
        voucher.updated_at = datetime.now()
        
        self._save_voucher(voucher)
        
        return True, f"凭证 {voucher.voucher_no} 记账成功"
    
    def get_voucher_by_id(self, voucher_id: str) -> Optional[AccountingVoucher]:
        """根据ID获取凭证"""
        conn = getattr(self.db, 'conn', None)
        if not conn:
            return None
        
        cursor = conn.cursor()
        cursor.execute(
            "SELECT * FROM accounting_vouchers WHERE id = ?",
            (voucher_id,)
        )
        row = cursor.fetchone()
        
        if not row:
            return None
        
        return self._row_to_voucher(row)
    
    def list_vouchers_by_period(
        self,
        accounting_period: str,
        status: Optional[VoucherStatus] = None
    ) -> List[AccountingVoucher]:
        """获取指定期间的凭证列表"""
        conn = getattr(self.db, 'conn', None)
        if not conn:
            return []
        
        cursor = conn.cursor()
        if status:
            cursor.execute(
                """
                SELECT * FROM accounting_vouchers 
                WHERE accounting_period = ? AND status = ?
                ORDER BY voucher_date
                """,
                (accounting_period, status.value)
            )
        else:
            cursor.execute(
                """
                SELECT * FROM accounting_vouchers 
                WHERE accounting_period = ?
                ORDER BY voucher_date
                """,
                (accounting_period,)
            )
        
        vouchers = []
        for row in cursor.fetchall():
            vouchers.append(self._row_to_voucher(row))
        
        return vouchers
    
    def _row_to_voucher(self, row) -> AccountingVoucher:
        """将数据库行转换为凭证对象"""
        # 先获取凭证明细
        lines = self._get_voucher_lines(row[0])
        
        return AccountingVoucher(
            id=row[0],
            voucher_no=row[1],
            voucher_date=date.fromisoformat(row[2]),
            accounting_period=row[3],
            lines=lines,
            summary=row[4],
            total_debit=Decimal(row[5]),
            total_credit=Decimal(row[6]),
            created_by=row[7],
            reviewed_by=row[8],
            posted_by=row[9],
            reviewed_at=datetime.fromisoformat(row[10]) if row[10] else None,
            posted_at=datetime.fromisoformat(row[11]) if row[11] else None,
            status=VoucherStatus(row[12]),
            source_type=row[13],
            source_id=row[14],
            notes=row[15],
            created_at=datetime.fromisoformat(row[16]),
            updated_at=datetime.fromisoformat(row[17])
        )
    
    def _get_voucher_lines(self, voucher_id: str) -> List[VoucherLine]:
        """获取凭证明细"""
        conn = getattr(self.db, 'conn', None)
        if not conn:
            return []
        
        cursor = conn.cursor()
        cursor.execute(
            "SELECT * FROM voucher_lines WHERE voucher_id = ? ORDER BY id",
            (voucher_id,)
        )
        
        lines = []
        for row in cursor.fetchall():
            line = VoucherLine(
                id=row[0],
                voucher_id=row[1],
                account_code=row[2],
                account_name=row[3],
                debit=Decimal(row[4]),
                credit=Decimal(row[5]),
                summary=row[6],
                related_entity_type=row[7],
                related_entity_id=row[8]
            )
            lines.append(line)
        
        return lines
