#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
小会计工作助手 - 专为小企业小会计设计
提高日常工作效率的实用工具集
"""

from decimal import Decimal
from datetime import date, datetime, timedelta
from typing import Dict, List, Optional, Tuple
from collections import defaultdict

from ..models.business_models import (
    Income, Expense, ProcessingOrder, Customer, Supplier,
    BankType, ExpenseType, OrderStatus
)
from ..business.finance_manager import FinanceManager


class AccountantAssistant:
    """小会计工作助手"""

    def __init__(self, finance_manager: FinanceManager):
        self.finance = finance_manager
        self.db = finance_manager.db

    # ==================== 每日工作检查 ====================

    def get_daily_work_checklist(self, check_date: Optional[date] = None) -> Dict:
        """
        每日工作检查清单
        帮助小会计快速了解当天需要完成的工作
        """
        if check_date is None:
            check_date = date.today()

        # 获取今日到期的订单
        today_orders = [
            o for o in self.db.list_orders()
            if o.order_date == check_date
        ]

        # 获取今日到期的收付款
        today_incomes = [
            i for i in self.db.list_incomes()
            if i.income_date == check_date
        ]

        today_expenses = [
            e for e in self.db.list_expenses()
            if e.expense_date == check_date
        ]

        # 获取需要跟进的应收账款
        receivables = self.finance.get_customer_receivables("")
        overdue_orders = []
        for order in self.db.list_orders():
            unpaid = order.total_amount - order.received_amount
            if unpaid > 0:
                overdue_orders.append({
                    "order_no": order.order_no,
                    "customer": order.customer_name,
                    "amount": unpaid,
                    "days_since_order": (check_date - order.order_date).days
                })

        return {
            "check_date": check_date,
            "today_orders": {
                "count": len(today_orders),
                "total_amount": sum(o.total_amount for o in today_orders),
                "details": [{"order_no": o.order_no, "customer": o.customer_name, "amount": o.total_amount} 
                           for o in today_orders]
            },
            "today_incomes": {
                "count": len(today_incomes),
                "total_amount": sum(i.amount for i in today_incomes),
                "details": [{"customer": i.customer_name, "amount": i.amount, "bank": i.bank_type.value} 
                           for i in today_incomes]
            },
            "today_expenses": {
                "count": len(today_expenses),
                "total_amount": sum(e.amount for e in today_expenses),
                "details": [{"supplier": e.supplier_name, "type": e.expense_type.value, "amount": e.amount} 
                           for e in today_expenses]
            },
            "receivables_summary": receivables,
            "work_priority": self._suggest_work_priority(overdue_orders)
        }

    def _suggest_work_priority(self, overdue_orders: List[Dict]) -> List[Dict]:
        """根据业务情况建议工作优先级"""
        priorities = []

        # 非常紧急：逾期30天以上的大额欠款
        urgent = [o for o in overdue_orders if o["days_since_order"] > 30 and o["amount"] > 1000]
        if urgent:
            priorities.append({
                "priority": "紧急",
                "tasks": ["跟进大额逾期应收账款", "电话联系关键客户"]
            })

        # 较紧急：逾期15天以上
        medium = [o for o in overdue_orders if 15 <= o["days_since_order"] <= 30]
        if medium:
            priorities.append({
                "priority": "重要",
                "tasks": ["跟进中期逾期款项", "发送提醒通知"]
            })

        return priorities

    # ==================== 快速记账助手 ====================

    def quick_record_income(
        self,
        customer_name: str,
        amount: float,
        has_invoice: bool = False,
        is_n_bank: bool = False,  # 默认用G银行
        notes: str = ""
    ) -> Tuple[bool, str, Optional[Income]]:
        """
        快速记录收入 - 简化操作
        小会计常用的快捷操作
        """
        try:
            amount_decimal = Decimal(str(amount))
            bank_type = BankType.N_BANK if is_n_bank else BankType.G_BANK

            # 查找或创建客户
            customers = self.db.list_customers()
            customer = next((c for c in customers if c.name == customer_name), None)

            if not customer:
                customer = Customer(name=customer_name)
                self.db.save_customer(customer)

            income = self.finance.record_income(
                customer_id=customer.id,
                customer_name=customer.name,
                amount=amount_decimal,
                bank_type=bank_type,
                income_date=date.today(),
                has_invoice=has_invoice,
                notes=notes
            )

            return True, "快速记录收入成功", income

        except Exception as e:
            return False, f"快速记录失败: {e}", None

    def quick_record_expense(
        self,
        expense_type: str,
        amount: float,
        supplier_name: str = "",
        has_invoice: bool = False,
        is_n_bank: bool = False,
        description: str = ""
    ) -> Tuple[bool, str, Optional[Expense]]:
        """
        快速记录支出 - 简化操作
        """
        try:
            amount_decimal = Decimal(str(amount))
            bank_type = BankType.N_BANK if is_n_bank else BankType.G_BANK

            # 转换支出类型
            expense_type_enum = None
            for et in ExpenseType:
                if expense_type in et.value or et.value in expense_type:
                    expense_type_enum = et
                    break
            if not expense_type_enum:
                expense_type_enum = ExpenseType.OTHER

            # 查找或创建供应商
            supplier = None
            if supplier_name:
                suppliers = self.db.list_suppliers()
                supplier = next((s for s in suppliers if s.name == supplier_name), None)
                if not supplier:
                    supplier = Supplier(name=supplier_name)
                    self.db.save_supplier(supplier)

            expense = self.finance.record_expense(
                expense_type=expense_type_enum,
                amount=amount_decimal,
                bank_type=bank_type,
                expense_date=date.today(),
                supplier_id=supplier.id if supplier else None,
                supplier_name=supplier_name,
                has_invoice=has_invoice,
                description=description
            )

            return True, "快速记录支出成功", expense

        except Exception as e:
            return False, f"快速记录失败: {e}", None

    # ==================== 对账助手 ====================

    def smart_reconciliation(self) -> Dict:
        """
        智能对账助手
        帮助小会计快速核对银行交易
        """
        summary = self.finance.reconcile_bank_accounts()

        # 找出可能的匹配建议
        unmatched_transactions = self.finance.get_unmatched_transactions()

        suggestions = []
        for trans in unmatched_transactions:
            if trans.amount > 0:
                # 收入匹配建议
                incomes = self.db.list_incomes()
                for income in incomes:
                    if (abs(income.amount - abs(trans.amount)) < Decimal("0.01") and
                        income.bank_type == trans.bank_type and
                        not any(t.matched and t.matched_income_id == income.id
                               for t in self.db.list_bank_transactions())):
                        suggestions.append({
                            "type": "收入匹配建议",
                            "transaction_amount": abs(trans.amount),
                            "income_customer": income.customer_name,
                            "income_amount": income.amount,
                            "confidence": "高"
                        })
                        break
            else:
                # 支出匹配建议
                expenses = self.db.list_expenses()
                for expense in expenses:
                    if (abs(expense.amount - abs(trans.amount)) < Decimal("0.01") and
                        expense.bank_type == trans.bank_type):
                        suggestions.append({
                            "type": "支出匹配建议",
                            "transaction_amount": abs(trans.amount),
                            "expense_type": expense.expense_type.value,
                            "expense_amount": expense.amount,
                            "confidence": "高"
                        })
                        break

        return {
            "reconciliation_summary": summary,
            "match_suggestions": suggestions[:10],  # 限制建议数量
            "unmatched_count": summary["total_unmatched_transactions"],
            "action_required": summary["total_unmatched_transactions"] > 0
        }

    # ==================== 月度结账助手 ====================

    def monthly_close_assistant(self, year: int, month: int) -> Dict:
        """
        月度结账助手
        帮助小会计快速完成月末结账
        """
        start_date = date(year, month, 1)
        if month == 12:
            end_date = date(year + 1, 1, 1) - timedelta(days=1)
        else:
            end_date = date(year, month + 1, 1) - timedelta(days=1)

        # 当月收支汇总
        period_summary = self.finance.get_accrual_period_summary(start_date, end_date)

        # 预收预付款分析
        prepayments = self.finance.get_prepayment_analysis(start_date, end_date)

        # 待办事项
        to_dos = []
        if period_summary["income"]["count"] == 0:
            to_dos.append("⚠ 检查当月收入记录是否完整")
        if period_summary["expense"]["count"] < 10:
            to_dos.append("⚠ 检查当月支出记录是否完整")

        # 结账检查清单
        checklist = [
            "✅ 本月收入是否全部入账",
            "✅ 本月支出是否全部入账",
            "✅ 银行对账是否完成",
            "✅ 应收账款是否跟进",
            "✅ 是否需要生成会计凭证"
        ]

        return {
            "period": f"{year}年{month}月",
            "summary": period_summary,
            "prepayment_analysis": prepayments,
            "todo_list": to_dos,
            "checklist": checklist,
            "can_close": len(to_dos) == 0
        }

    # ==================== 报表生成助手 ====================

    def generate_simple_report(self, days: int = 30) -> Dict:
        """
        生成简单易懂的财务报表
        适合小企业主查看
        """
        end_date = date.today()
        start_date = end_date - timedelta(days=days)

        summary = self.finance.get_accrual_period_summary(start_date, end_date)

        # 生成简单版的利润表
        simple_profit = {
            "期间": f"过去{days}天",
            "总收入": summary["income"]["total"],
            "总支出": summary["expense"]["total"],
            "净利润": summary["net_profit"],
            "收入构成": {
                "G银行": summary["income"]["g_bank"],
                "N银行": summary["income"]["n_bank"]
            },
            "支出构成": summary["expense"]["by_type"]
        }

        # 按银行统计
        bank_summary = self.finance.reconcile_bank_accounts()

        return {
            "simple_profit": simple_profit,
            "bank_summary": bank_summary,
            "generated_at": datetime.now().isoformat()
        }

    # ==================== 数据导入导出助手 ====================

    def export_to_excel_template(self, data_type: str = "incomes") -> List[Dict]:
        """
        导出Excel模板格式数据
        便于小会计在Excel中操作
        """
        if data_type == "incomes":
            incomes = self.db.list_incomes()
            return [
                {
                    "日期": i.income_date.isoformat(),
                    "客户": i.customer_name,
                    "金额": float(i.amount),
                    "银行": i.bank_type.value,
                    "有票": "是" if i.has_invoice else "否",
                    "备注": i.notes
                }
                for i in incomes
            ]
        elif data_type == "expenses":
            expenses = self.db.list_expenses()
            return [
                {
                    "日期": e.expense_date.isoformat(),
                    "类型": e.expense_type.value,
                    "供应商": e.supplier_name,
                    "金额": float(e.amount),
                    "银行": e.bank_type.value,
                    "有票": "是" if e.has_invoice else "否",
                    "备注": e.notes
                }
                for e in expenses
            ]
        else:
            return []

    # ==================== 智能提醒 ====================

    def get_smart_reminders(self) -> List[Dict]:
        """
        获取智能提醒
        帮助小会计不遗漏重要事项
        """
        reminders = []
        today = date.today()

        # 1. 大额支出提醒（>5000元）
        recent_expenses = [
            e for e in self.db.list_expenses()
            if e.expense_date >= today - timedelta(days=7) and e.amount > Decimal("5000")
        ]
        if recent_expenses:
            reminders.append({
                "type": "大额支出提醒",
                "content": f"近7天有{len(recent_expenses)}笔大额支出，请注意审核",
                "priority": "中"
            })

        # 2. 无票支出提醒
        no_invoice_expenses = [
            e for e in self.db.list_expenses()
            if not e.has_invoice and e.expense_date >= today - timedelta(days=30)
        ]
        if len(no_invoice_expenses) > 5:
            reminders.append({
                "type": "发票提醒",
                "content": f"近30天有{len(no_invoice_expenses)}笔无票支出，请尽快索取发票",
                "priority": "中"
            })

        # 3. 预收预付款提醒
        prepayment_analysis = self.finance.get_prepayment_analysis()
        if prepayment_analysis["advance_receipts"]["count"] > 0:
            reminders.append({
                "type": "预收账款提醒",
                "content": f"有{prepayment_analysis['advance_receipts']['count']}笔预收款，请及时核销",
                "priority": "低"
            })

        # 4. 月末提醒
        if today.day >= 25:
            reminders.append({
                "type": "月末提醒",
                "content": "月末将至，请准备结账工作",
                "priority": "高"
            })

        return reminders
