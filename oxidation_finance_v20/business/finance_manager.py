#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
财务管理器 - 处理收入、支出和付款分配
"""

from decimal import Decimal
from datetime import date
from typing import Any, List, Dict, Optional, Tuple
from ..models.business_models import (
    Income,
    Expense,
    ProcessingOrder,
    BankType,
    ExpenseType,
    BankAccount,
    BankTransaction,
    OperationType,
    EntityType,
)
from ..database.db_manager import DatabaseManager


class FinanceManager:
    """财务管理器 - 负责收入和支出管理"""

    def __init__(self, db_manager: DatabaseManager):
        """初始化财务管理器"""
        self.db = db_manager

    # ==================== 收入管理 ====================

    def record_income(
        self,
        customer_id: str,
        customer_name: str,
        amount: Decimal,
        bank_type: BankType,
        income_date: date,
        has_invoice: bool = False,
        notes: str = "",
    ) -> Income:
        """
        记录客户付款

        Args:
            customer_id: 客户ID
            customer_name: 客户名称
            amount: 付款金额
            bank_type: 银行类型（G银行或N银行）
            income_date: 收入日期
            has_invoice: 是否有票据
            notes: 备注

        Returns:
            Income: 收入记录对象
        """
        income = Income(
            customer_id=customer_id,
            customer_name=customer_name,
            amount=amount,
            bank_type=bank_type,
            has_invoice=has_invoice,
            income_date=income_date,
            notes=notes,
        )

        self.db.save_income(income)
        return income

    def allocate_payment_to_orders(
        self, income_id: str, allocations: Dict[str, Decimal]
    ) -> Tuple[bool, str]:
        """
        将付款灵活分配到多个订单

        Args:
            income_id: 收入记录ID
            allocations: 订单ID到分配金额的映射 {order_id: amount}

        Returns:
            Tuple[bool, str]: (是否成功, 消息)
        """
        # 获取收入记录
        income = self.db.get_income(income_id)
        if not income:
            return False, f"收入记录不存在: {income_id}"

        # 验证分配金额总和
        total_allocated = sum(allocations.values())
        if total_allocated > income.amount:
            return False, f"分配金额总和 {total_allocated} 超过付款金额 {income.amount}"

        # 验证每个订单并检查未付余额
        for order_id, allocated_amount in allocations.items():
            order = self.db.get_order(order_id)
            if not order:
                return False, f"订单不存在: {order_id}"

            # 检查订单的未付余额
            unpaid_amount = order.total_amount - order.received_amount
            if allocated_amount > unpaid_amount:
                return (
                    False,
                    f"订单 {order.order_no} 的分配金额 {allocated_amount} 超过未付余额 {unpaid_amount}",
                )

        # 更新收入记录的分配信息
        income.allocation = allocations
        income.related_orders = list(allocations.keys())
        self.db.save_income(income)

        # 更新每个订单的已收金额
        for order_id, allocated_amount in allocations.items():
            order = self.db.get_order(order_id)
            if not order:
                continue  # Skip if order no longer exists
            order.received_amount += allocated_amount
            self.db.save_order(order)

        return True, "付款分配成功"

    def get_customer_incomes(self, customer_id: str) -> List[Income]:
        """
        查询客户的所有收入记录

        Args:
            customer_id: 客户ID

        Returns:
            List[Income]: 收入记录列表
        """
        return self.db.list_incomes(customer_id=customer_id)

    def get_income_by_id(self, income_id: str) -> Optional[Income]:
        """
        根据ID获取收入记录

        Args:
            income_id: 收入记录ID

        Returns:
            Optional[Income]: 收入记录对象，如果不存在则返回None
        """
        return self.db.get_income(income_id)

    def get_order_payment_status(self, order_id: str) -> Dict:
        """
        获取订单的付款状态

        Args:
            order_id: 订单ID

        Returns:
            Dict: 包含订单付款状态的字典
        """
        order = self.db.get_order(order_id)
        if not order:
            return {"error": "订单不存在"}

        unpaid_amount = order.total_amount - order.received_amount
        payment_ratio = (
            (order.received_amount / order.total_amount * 100)
            if order.total_amount > 0
            else 0
        )

        status = "未付款"
        if order.received_amount == 0:
            status = "未付款"
        elif order.received_amount >= order.total_amount:
            status = "已付清"
        else:
            status = "部分付款"

        return {
            "order_id": order.id,
            "order_no": order.order_no,
            "total_amount": order.total_amount,
            "received_amount": order.received_amount,
            "unpaid_amount": unpaid_amount,
            "payment_ratio": round(payment_ratio, 2),
            "status": status,
        }

    def get_customer_receivables(self, customer_id: str) -> Dict:
        """
        获取客户的应收账款汇总

        Args:
            customer_id: 客户ID

        Returns:
            Dict: 应收账款汇总信息
        """
        orders = self.db.list_orders(customer_id=customer_id)

        total_amount = Decimal("0")
        received_amount = Decimal("0")
        unpaid_amount = Decimal("0")

        order_details = []
        for order in orders:
            total_amount += order.total_amount
            received_amount += order.received_amount
            unpaid = order.total_amount - order.received_amount
            unpaid_amount += unpaid

            if unpaid > 0:
                order_details.append(
                    {
                        "order_no": order.order_no,
                        "order_date": order.order_date,
                        "total_amount": order.total_amount,
                        "received_amount": order.received_amount,
                        "unpaid_amount": unpaid,
                    }
                )

        return {
            "customer_id": customer_id,
            "total_amount": total_amount,
            "received_amount": received_amount,
            "unpaid_amount": unpaid_amount,
            "unpaid_orders": order_details,
        }

    # ==================== 支出管理 ====================

    def record_expense(
        self,
        expense_type: ExpenseType,
        amount: Decimal,
        bank_type: BankType,
        expense_date: date,
        supplier_id: Optional[str] = None,
        supplier_name: str = "",
        has_invoice: bool = False,
        related_order_id: Optional[str] = None,
        description: str = "",
        notes: str = "",
    ) -> Expense:
        """
        记录支出

        Args:
            expense_type: 支出类型
            amount: 支出金额
            bank_type: 银行类型
            expense_date: 支出日期
            supplier_id: 供应商ID（可选）
            supplier_name: 供应商名称
            has_invoice: 是否有票据
            related_order_id: 关联订单ID（委外加工费用）
            description: 描述
            notes: 备注

        Returns:
            Expense: 支出记录对象
        """
        expense = Expense(
            expense_type=expense_type,
            supplier_id=supplier_id,
            supplier_name=supplier_name,
            amount=amount,
            bank_type=bank_type,
            has_invoice=has_invoice,
            related_order_id=related_order_id,
            expense_date=expense_date,
            description=description,
            notes=notes,
        )

        self.db.save_expense(expense)
        return expense

    def get_supplier_expenses(self, supplier_id: str) -> List[Expense]:
        """
        查询供应商的所有支出记录

        Args:
            supplier_id: 供应商ID

        Returns:
            List[Expense]: 支出记录列表
        """
        return self.db.list_expenses(supplier_id=supplier_id)

    def get_expenses_by_type(self, expense_type: ExpenseType) -> List[Expense]:
        """
        按类型查询支出记录

        Args:
            expense_type: 支出类型

        Returns:
            List[Expense]: 支出记录列表
        """
        return self.db.list_expenses(expense_type=expense_type)

    def allocate_payment_to_expenses(
        self,
        payment_amount: Decimal,
        allocations: Dict[str, Decimal],
        bank_type: BankType,
        payment_date: date,
        notes: str = "",
    ) -> Tuple[bool, str]:
        """
        将供应商付款灵活分配到多个支出记录

        Args:
            payment_amount: 付款总金额
            allocations: 支出ID到分配金额的映射 {expense_id: amount}
            bank_type: 银行类型
            payment_date: 付款日期
            notes: 备注

        Returns:
            Tuple[bool, str]: (是否成功, 消息)
        """
        # 验证分配金额总和
        total_allocated = sum(allocations.values())
        if total_allocated > payment_amount:
            return (
                False,
                f"分配金额总和 {total_allocated} 超过付款金额 {payment_amount}",
            )

        # 验证每个支出记录存在
        for expense_id, allocated_amount in allocations.items():
            expense = self.db.get_expense(expense_id)
            if not expense:
                return False, f"支出记录不存在: {expense_id}"

            if allocated_amount <= 0:
                return False, f"分配金额必须大于0: {allocated_amount}"

        # 更新每个支出记录的付款信息
        # 注意：这里我们通过在notes中记录付款信息来跟踪
        # 在实际应用中，可能需要一个单独的付款记录表
        for expense_id, allocated_amount in allocations.items():
            expense = self.db.get_expense(expense_id)
            if not expense:
                continue  # Skip if expense no longer exists
            payment_note = f"付款 {allocated_amount} 元 ({payment_date.isoformat()})"
            if expense.notes:
                expense.notes += f"; {payment_note}"
            else:
                expense.notes = payment_note
            self.db.save_expense(expense)

        return True, "供应商付款分配成功"

    def get_supplier_payables(self, supplier_id: str) -> Dict:
        """
        获取供应商的应付账款汇总

        Args:
            supplier_id: 供应商ID

        Returns:
            Dict: 应付账款汇总信息
        """
        expenses = self.db.list_expenses(supplier_id=supplier_id)

        total_amount = Decimal("0")
        expense_details = []

        for expense in expenses:
            total_amount += expense.amount
            expense_details.append(
                {
                    "expense_id": expense.id,
                    "expense_type": expense.expense_type.value,
                    "expense_date": expense.expense_date,
                    "amount": expense.amount,
                    "description": expense.description,
                    "notes": expense.notes,
                }
            )

        return {
            "supplier_id": supplier_id,
            "total_amount": total_amount,
            "expense_count": len(expenses),
            "expense_details": expense_details,
        }

    def get_expense_summary_by_type(
        self, start_date: Optional[date] = None, end_date: Optional[date] = None
    ) -> Dict[str, Decimal]:
        """
        按类型汇总支出

        Args:
            start_date: 开始日期（可选）
            end_date: 结束日期（可选）

        Returns:
            Dict[str, Decimal]: 支出类型到金额的映射
        """
        all_expenses = self.db.list_expenses()

        # 按日期过滤
        if start_date or end_date:
            filtered_expenses = []
            for expense in all_expenses:
                if start_date and expense.expense_date < start_date:
                    continue
                if end_date and expense.expense_date > end_date:
                    continue
                filtered_expenses.append(expense)
            all_expenses = filtered_expenses

        # 按类型汇总
        summary = {}
        for expense in all_expenses:
            expense_type_name = expense.expense_type.value
            if expense_type_name not in summary:
                summary[expense_type_name] = Decimal("0")
            summary[expense_type_name] += expense.amount

        return summary

    def get_professional_materials_expenses(
        self, start_date: Optional[date] = None, end_date: Optional[date] = None
    ) -> Dict:
        """
        获取专业原料支出汇总（三酸、片碱、亚钠、色粉、除油剂）

        Args:
            start_date: 开始日期（可选）
            end_date: 结束日期（可选）

        Returns:
            Dict: 专业原料支出汇总
        """
        professional_types = [
            ExpenseType.ACID_THREE,
            ExpenseType.CAUSTIC_SODA,
            ExpenseType.SODIUM_SULFITE,
            ExpenseType.COLOR_POWDER,
            ExpenseType.DEGREASER,
        ]

        materials_summary = {}
        total_amount = Decimal("0")

        for expense_type in professional_types:
            expenses = self.db.list_expenses(expense_type=expense_type)

            # 按日期过滤
            if start_date or end_date:
                filtered_expenses = []
                for expense in expenses:
                    if start_date and expense.expense_date < start_date:
                        continue
                    if end_date and expense.expense_date > end_date:
                        continue
                    filtered_expenses.append(expense)
                expenses = filtered_expenses

            type_amount = sum(e.amount for e in expenses)
            materials_summary[expense_type.value] = {
                "amount": type_amount,
                "count": len(expenses),
                "expenses": [
                    {
                        "date": e.expense_date,
                        "amount": e.amount,
                        "supplier": e.supplier_name,
                        "description": e.description,
                    }
                    for e in expenses
                ],
            }
            total_amount += type_amount

        return {"total_amount": total_amount, "materials": materials_summary}

    # ==================== 银行账户管理 ====================

    def create_bank_account(
        self,
        bank_type: BankType,
        account_name: str,
        account_number: str = "",
        initial_balance: Decimal = Decimal("0"),
        notes: str = "",
    ) -> BankAccount:
        """
        创建银行账户

        Args:
            bank_type: 银行类型（G银行或N银行）
            account_name: 账户名称
            account_number: 账户号码
            initial_balance: 初始余额
            notes: 备注

        Returns:
            BankAccount: 银行账户对象
        """
        account = BankAccount(
            bank_type=bank_type,
            account_name=account_name,
            account_number=account_number,
            balance=initial_balance,
            notes=notes,
        )

        self.db.save_bank_account(account)
        return account

    def get_bank_account(self, account_id: str) -> Optional[BankAccount]:
        """
        获取银行账户

        Args:
            account_id: 账户ID

        Returns:
            Optional[BankAccount]: 银行账户对象，如果不存在则返回None
        """
        return self.db.get_bank_account(account_id)

    def list_bank_accounts(self) -> List[BankAccount]:
        """
        获取所有银行账户列表

        Returns:
            List[BankAccount]: 银行账户列表
        """
        return self.db.list_bank_accounts()

    def get_account_balance(self, bank_type: BankType) -> Decimal:
        """
        获取指定银行类型的账户余额

        Args:
            bank_type: 银行类型

        Returns:
            Decimal: 账户余额总和
        """
        accounts = self.db.list_bank_accounts()
        total_balance = Decimal("0")

        for account in accounts:
            if account.bank_type == bank_type:
                total_balance += account.balance

        return total_balance

    def update_account_balance(
        self, bank_type: BankType, amount: Decimal, is_income: bool = True
    ) -> Tuple[bool, str]:
        """
        更新账户余额

        Args:
            bank_type: 银行类型
            amount: 金额（正数）
            is_income: 是否为收入（True为收入，False为支出）

        Returns:
            Tuple[bool, str]: (是否成功, 消息)
        """
        accounts = self.db.list_bank_accounts()
        target_account = None

        # 查找对应银行类型的账户
        for account in accounts:
            if account.bank_type == bank_type:
                target_account = account
                break

        if not target_account:
            return False, f"未找到{bank_type.value}账户"

        # 更新余额
        if is_income:
            target_account.balance += amount
        else:
            if target_account.balance < amount:
                return (
                    False,
                    f"账户余额不足：当前余额 {target_account.balance}，需要支出 {amount}",
                )
            target_account.balance -= amount

        self.db.save_bank_account(target_account)
        return True, f"账户余额更新成功，当前余额：{target_account.balance}"

    def record_bank_transaction(
        self,
        bank_type: BankType,
        amount: Decimal,
        transaction_date: date,
        counterparty: str = "",
        description: str = "",
        is_income: bool = True,
        matched_income_id: Optional[str] = None,
        matched_expense_id: Optional[str] = None,
        notes: str = "",
    ) -> BankTransaction:
        """
        记录银行交易

        Args:
            bank_type: 银行类型
            amount: 交易金额（正数为收入，负数为支出）
            transaction_date: 交易日期
            counterparty: 交易对手
            description: 交易描述
            is_income: 是否为收入
            matched_income_id: 匹配的收入记录ID
            matched_expense_id: 匹配的支出记录ID
            notes: 备注

        Returns:
            BankTransaction: 银行交易记录对象
        """
        # 确保金额符号正确
        if not is_income and amount > 0:
            amount = -amount

        transaction = BankTransaction(
            bank_type=bank_type,
            transaction_date=transaction_date,
            amount=amount,
            counterparty=counterparty,
            description=description,
            matched=(matched_income_id is not None or matched_expense_id is not None),
            matched_income_id=matched_income_id,
            matched_expense_id=matched_expense_id,
            notes=notes,
        )

        self.db.save_bank_transaction(transaction)

        # 更新账户余额
        self.update_account_balance(bank_type, abs(amount), is_income)

        return transaction

    def get_bank_transactions(
        self,
        bank_type: Optional[BankType] = None,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
    ) -> List[BankTransaction]:
        """
        获取银行交易记录列表

        Args:
            bank_type: 银行类型（可选，不指定则返回所有）
            start_date: 开始日期（可选）
            end_date: 结束日期（可选）

        Returns:
            List[BankTransaction]: 银行交易记录列表
        """
        transactions = self.db.list_bank_transactions(bank_type)

        # 按日期过滤
        if start_date or end_date:
            filtered_transactions = []
            for transaction in transactions:
                if start_date and transaction.transaction_date < start_date:
                    continue
                if end_date and transaction.transaction_date > end_date:
                    continue
                filtered_transactions.append(transaction)
            transactions = filtered_transactions

        return transactions

    def match_transaction_to_income(
        self, transaction_id: str, income_id: str
    ) -> Tuple[bool, str]:
        """
        将银行交易匹配到收入记录

        Args:
            transaction_id: 交易记录ID
            income_id: 收入记录ID

        Returns:
            Tuple[bool, str]: (是否成功, 消息)
        """
        transaction = self.db.get_bank_transaction(transaction_id)
        if not transaction:
            return False, f"交易记录不存在: {transaction_id}"

        income = self.db.get_income(income_id)
        if not income:
            return False, f"收入记录不存在: {income_id}"

        # 验证金额和银行类型是否匹配
        if transaction.amount != income.amount:
            return (
                False,
                f"金额不匹配：交易金额 {transaction.amount}，收入金额 {income.amount}",
            )

        if transaction.bank_type != income.bank_type:
            return (
                False,
                f"银行类型不匹配：交易银行 {transaction.bank_type.value}，收入银行 {income.bank_type.value}",
            )

        # 更新匹配信息
        transaction.matched = True
        transaction.matched_income_id = income_id
        self.db.save_bank_transaction(transaction)

        return True, "交易匹配成功"

    def match_transaction_to_expense(
        self, transaction_id: str, expense_id: str
    ) -> Tuple[bool, str]:
        """
        将银行交易匹配到支出记录

        Args:
            transaction_id: 交易记录ID
            expense_id: 支出记录ID

        Returns:
            Tuple[bool, str]: (是否成功, 消息)
        """
        transaction = self.db.get_bank_transaction(transaction_id)
        if not transaction:
            return False, f"交易记录不存在: {transaction_id}"

        expense = self.db.get_expense(expense_id)
        if not expense:
            return False, f"支出记录不存在: {expense_id}"

        # 验证金额和银行类型是否匹配
        if abs(transaction.amount) != expense.amount:
            return (
                False,
                f"金额不匹配：交易金额 {abs(transaction.amount)}，支出金额 {expense.amount}",
            )

        if transaction.bank_type != expense.bank_type:
            return (
                False,
                f"银行类型不匹配：交易银行 {transaction.bank_type.value}，支出银行 {expense.bank_type.value}",
            )

        # 更新匹配信息
        transaction.matched = True
        transaction.matched_expense_id = expense_id
        self.db.save_bank_transaction(transaction)

        return True, "交易匹配成功"

    def get_unmatched_transactions(
        self, bank_type: Optional[BankType] = None
    ) -> List[BankTransaction]:
        """
        获取未匹配的银行交易记录

        Args:
            bank_type: 银行类型（可选）

        Returns:
            List[BankTransaction]: 未匹配的交易记录列表
        """
        transactions = self.db.list_bank_transactions(bank_type)
        return [t for t in transactions if not t.matched]

    def get_bank_account_summary(self, bank_type: BankType) -> Dict:
        """
        获取银行账户汇总信息

        Args:
            bank_type: 银行类型

        Returns:
            Dict: 账户汇总信息
        """
        # 获取账户余额
        balance = self.get_account_balance(bank_type)

        # 获取交易记录
        transactions = self.db.list_bank_transactions(bank_type)

        # 统计收入和支出
        total_income = Decimal("0")
        total_expense = Decimal("0")
        matched_count = 0
        unmatched_count = 0

        for transaction in transactions:
            if transaction.amount > 0:
                total_income += transaction.amount
            else:
                total_expense += abs(transaction.amount)

            if transaction.matched:
                matched_count += 1
            else:
                unmatched_count += 1

        # 特殊标记
        special_notes = []
        if bank_type == BankType.G_BANK:
            special_notes.append("G银行用于有票据的正式交易")
        elif bank_type == BankType.N_BANK:
            special_notes.append("N银行作为现金等价物处理（与微信结合）")

        return {
            "bank_type": bank_type.value,
            "balance": balance,
            "total_income": total_income,
            "total_expense": total_expense,
            "net_flow": total_income - total_expense,
            "transaction_count": len(transactions),
            "matched_count": matched_count,
            "unmatched_count": unmatched_count,
            "special_notes": special_notes,
        }

    def reconcile_bank_accounts(self) -> Dict:
        """
        银行账户对账汇总

        Returns:
            Dict: 对账汇总信息
        """
        g_bank_summary = self.get_bank_account_summary(BankType.G_BANK)
        n_bank_summary = self.get_bank_account_summary(BankType.N_BANK)

        total_balance = g_bank_summary["balance"] + n_bank_summary["balance"]
        total_unmatched = (
            g_bank_summary["unmatched_count"] + n_bank_summary["unmatched_count"]
        )

        return {
            "g_bank": g_bank_summary,
            "n_bank": n_bank_summary,
            "total_balance": total_balance,
            "total_unmatched_transactions": total_unmatched,
            "reconciliation_status": "完成" if total_unmatched == 0 else "有未匹配交易",
        }

    # ==================== 实际发生制记账 ====================

    def record_accrual_income(
        self,
        customer_id: str,
        customer_name: str,
        amount: Decimal,
        bank_type: BankType,
        occurrence_date: date,
        payment_date: Optional[date] = None,
        has_invoice: bool = False,
        notes: str = "",
    ) -> Income:
        """
        按实际发生日期记录收入（实际发生制）

        Args:
            customer_id: 客户ID
            customer_name: 客户名称
            amount: 收入金额
            bank_type: 银行类型
            occurrence_date: 业务实际发生日期
            payment_date: 实际付款日期（可选，用于处理预收款）
            has_invoice: 是否有票据
            notes: 备注

        Returns:
            Income: 收入记录对象
        """
        # 使用实际发生日期作为收入日期
        income = Income(
            customer_id=customer_id,
            customer_name=customer_name,
            amount=amount,
            bank_type=bank_type,
            has_invoice=has_invoice,
            income_date=occurrence_date,  # 关键：使用业务实际发生日期
            notes=notes,
        )

        # 如果付款日期与发生日期不同，记录在备注中
        if payment_date and payment_date != occurrence_date:
            time_diff = (payment_date - occurrence_date).days
            if time_diff < 0:
                # 付款早于发生日期 → 预收款（提前收款）
                income.notes = (
                    f"{notes}; 预收款：提前{abs(time_diff)}天收款（付款日期：{payment_date.isoformat()}）"
                    if notes
                    else f"预收款：提前{abs(time_diff)}天收款（付款日期：{payment_date.isoformat()}）"
                )
            else:
                # 付款晚于发生日期 → 延迟收款
                income.notes = (
                    f"{notes}; 延迟收款：延后{time_diff}天收款（付款日期：{payment_date.isoformat()}）"
                    if notes
                    else f"延迟收款：延后{time_diff}天收款（付款日期：{payment_date.isoformat()}）"
                )

        self.db.save_income(income)
        return income

    def record_accrual_expense(
        self,
        expense_type: ExpenseType,
        amount: Decimal,
        bank_type: BankType,
        occurrence_date: date,
        payment_date: Optional[date] = None,
        supplier_id: Optional[str] = None,
        supplier_name: str = "",
        has_invoice: bool = False,
        related_order_id: Optional[str] = None,
        description: str = "",
        notes: str = "",
    ) -> Expense:
        """
        按实际发生日期记录支出（实际发生制）

        Args:
            expense_type: 支出类型
            amount: 支出金额
            bank_type: 银行类型
            occurrence_date: 业务实际发生日期
            payment_date: 实际付款日期（可选，用于处理预付款）
            supplier_id: 供应商ID
            supplier_name: 供应商名称
            has_invoice: 是否有票据
            related_order_id: 关联订单ID
            description: 描述
            notes: 备注

        Returns:
            Expense: 支出记录对象
        """
        # 使用实际发生日期作为支出日期
        expense = Expense(
            expense_type=expense_type,
            supplier_id=supplier_id,
            supplier_name=supplier_name,
            amount=amount,
            bank_type=bank_type,
            has_invoice=has_invoice,
            related_order_id=related_order_id,
            expense_date=occurrence_date,  # 关键：使用业务实际发生日期
            description=description,
            notes=notes,
        )

        # 如果付款日期与发生日期不同，记录在备注中
        if payment_date and payment_date != occurrence_date:
            time_diff = (payment_date - occurrence_date).days
            if time_diff < 0:
                expense.notes = (
                    f"{notes}; 预付款：提前{abs(time_diff)}天付款（付款日期：{payment_date.isoformat()}）"
                    if notes
                    else f"预付款：提前{abs(time_diff)}天付款（付款日期：{payment_date.isoformat()}）"
                )
            else:
                expense.notes = (
                    f"{notes}; 延迟付款：延后{time_diff}天付款（付款日期：{payment_date.isoformat()}）"
                    if notes
                    else f"延迟付款：延后{time_diff}天付款（付款日期：{payment_date.isoformat()}）"
                )

        self.db.save_expense(expense)
        return expense

    def match_income_to_expenses(
        self, income_id: str, expense_allocations: Dict[str, Decimal]
    ) -> Tuple[bool, str]:
        """
        灵活匹配收入到多个支出（支持多对多匹配）

        Args:
            income_id: 收入记录ID
            expense_allocations: 支出ID到分配金额的映射 {expense_id: amount}

        Returns:
            Tuple[bool, str]: (是否成功, 消息)
        """
        # 获取收入记录
        income = self.db.get_income(income_id)
        if not income:
            return False, f"收入记录不存在: {income_id}"

        # 验证分配金额总和
        total_allocated = sum(expense_allocations.values())
        if total_allocated > income.amount:
            return False, f"分配金额总和 {total_allocated} 超过收入金额 {income.amount}"

        # 验证每个支出记录存在
        for expense_id, allocated_amount in expense_allocations.items():
            expense = self.db.get_expense(expense_id)
            if not expense:
                return False, f"支出记录不存在: {expense_id}"

            if allocated_amount <= 0:
                return False, f"分配金额必须大于0: {allocated_amount}"

        # 更新收入记录的匹配信息
        if not income.notes:
            income.notes = ""

        match_info = f"匹配到{len(expense_allocations)}笔支出："
        for expense_id, allocated_amount in expense_allocations.items():
            expense = self.db.get_expense(expense_id)
            if not expense:
                continue  # Skip if expense no longer exists
            match_note = f"匹配收入 {income_id[:8]}: {allocated_amount}元"
            expense.notes = (
                f"{expense.notes}; {match_note}" if expense.notes else match_note
            )
            self.db.save_expense(expense)

        # 更新收入记录的匹配信息
        income.notes = f"{income.notes}; {match_info}" if income.notes else match_info
        self.db.save_income(income)

        return True, f"成功匹配收入到{len(expense_allocations)}笔支出"

    def match_expense_to_incomes(
        self, expense_id: str, income_allocations: Dict[str, Decimal]
    ) -> Tuple[bool, str]:
        """
        灵活匹配支出到多个收入（支持多对多匹配）

        Args:
            expense_id: 支出记录ID
            income_allocations: 收入ID到分配金额的映射 {income_id: amount}

        Returns:
            Tuple[bool, str]: (是否成功, 消息)
        """
        # 获取支出记录
        expense = self.db.get_expense(expense_id)
        if not expense:
            return False, f"支出记录不存在: {expense_id}"

        # 验证分配金额总和
        total_allocated = sum(income_allocations.values())
        if total_allocated > expense.amount:
            return (
                False,
                f"分配金额总和 {total_allocated} 超过支出金额 {expense.amount}",
            )

        # 验证每个收入记录存在
        for income_id, allocated_amount in income_allocations.items():
            income = self.db.get_income(income_id)
            if not income:
                return False, f"收入记录不存在: {income_id}"

            if allocated_amount <= 0:
                return False, f"分配金额必须大于0: {allocated_amount}"

        # 更新支出记录的匹配信息
        if not expense.notes:
            expense.notes = ""

        match_info = f"匹配到{len(income_allocations)}笔收入："
        for income_id, allocated_amount in income_allocations.items():
            income = self.db.get_income(income_id)
            if not income:
                continue  # Skip if income no longer exists
            match_info += (
                f" {income.customer_name}({income_id[:8]}): {allocated_amount}元;"
            )

        expense.notes = (
            f"{expense.notes}; {match_info}" if expense.notes else match_info
        )
        self.db.save_expense(expense)

        # 更新每个收入记录的匹配信息
        for income_id, allocated_amount in income_allocations.items():
            income = self.db.get_income(income_id)
            if not income:
                continue  # Skip if income no longer exists
            match_note = f"匹配支出 {expense_id[:8]}: {allocated_amount}元"
            income.notes = (
                f"{income.notes}; {match_note}" if income.notes else match_note
            )
            self.db.save_income(income)

        return True, f"成功匹配支出到{len(income_allocations)}笔收入"

    def get_prepayment_analysis(
        self, start_date: Optional[date] = None, end_date: Optional[date] = None
    ) -> Dict:
        """
        分析预收预付款情况

        Args:
            start_date: 开始日期（可选）
            end_date: 结束日期（可选）

        Returns:
            Dict: 预收预付款分析结果
        """
        # 获取所有收入和支出
        all_incomes = self.db.list_incomes()
        all_expenses = self.db.list_expenses()

        # 按日期过滤
        if start_date or end_date:
            if start_date:
                all_incomes = [i for i in all_incomes if i.income_date >= start_date]
                all_expenses = [e for e in all_expenses if e.expense_date >= start_date]
            if end_date:
                all_incomes = [i for i in all_incomes if i.income_date <= end_date]
                all_expenses = [e for e in all_expenses if e.expense_date <= end_date]

        # 识别预收款（notes中包含"预收款"）
        advance_receipts = []
        for income in all_incomes:
            if income.notes and "预收款" in income.notes:
                advance_receipts.append(
                    {
                        "id": income.id,
                        "customer": income.customer_name,
                        "amount": income.amount,
                        "occurrence_date": income.income_date,
                        "notes": income.notes,
                    }
                )

        # 识别预付款（notes中包含"预付款"）
        advance_payments = []
        for expense in all_expenses:
            if expense.notes and "预付款" in expense.notes:
                advance_payments.append(
                    {
                        "id": expense.id,
                        "supplier": expense.supplier_name,
                        "amount": expense.amount,
                        "occurrence_date": expense.expense_date,
                        "notes": expense.notes,
                    }
                )

        # 计算总额
        total_advance_receipts = sum(item["amount"] for item in advance_receipts)
        total_advance_payments = sum(item["amount"] for item in advance_payments)

        return {
            "advance_receipts": {
                "count": len(advance_receipts),
                "total_amount": total_advance_receipts,
                "details": advance_receipts,
            },
            "advance_payments": {
                "count": len(advance_payments),
                "total_amount": total_advance_payments,
                "details": advance_payments,
            },
            "net_advance": total_advance_receipts - total_advance_payments,
        }

    def get_accrual_period_summary(self, start_date: date, end_date: date) -> Dict:
        """
        获取会计期间的实际发生制汇总

        Args:
            start_date: 期间开始日期
            end_date: 期间结束日期

        Returns:
            Dict: 期间汇总信息
        """
        # 获取期间内的收入和支出（按实际发生日期）
        all_incomes = self.db.list_incomes()
        all_expenses = self.db.list_expenses()

        # 按实际发生日期过滤
        period_incomes = [
            i for i in all_incomes if start_date <= i.income_date <= end_date
        ]
        period_expenses = [
            e for e in all_expenses if start_date <= e.expense_date <= end_date
        ]

        # 计算总额
        total_income = sum(i.amount for i in period_incomes)
        total_expense = sum(e.amount for e in period_expenses)
        net_profit = total_income - total_expense

        # 按银行类型分类
        g_bank_income = sum(
            i.amount for i in period_incomes if i.bank_type == BankType.G_BANK
        )
        n_bank_income = sum(
            i.amount for i in period_incomes if i.bank_type == BankType.N_BANK
        )
        g_bank_expense = sum(
            e.amount for e in period_expenses if e.bank_type == BankType.G_BANK
        )
        n_bank_expense = sum(
            e.amount for e in period_expenses if e.bank_type == BankType.N_BANK
        )

        # 按支出类型分类
        expense_by_type = {}
        for expense in period_expenses:
            expense_type_name = expense.expense_type.value
            if expense_type_name not in expense_by_type:
                expense_by_type[expense_type_name] = Decimal("0")
            expense_by_type[expense_type_name] += expense.amount

        return {
            "period": {
                "start_date": start_date,
                "end_date": end_date,
                "days": (end_date - start_date).days + 1,
            },
            "income": {
                "total": total_income,
                "count": len(period_incomes),
                "g_bank": g_bank_income,
                "n_bank": n_bank_income,
            },
            "expense": {
                "total": total_expense,
                "count": len(period_expenses),
                "g_bank": g_bank_expense,
                "n_bank": n_bank_expense,
                "by_type": expense_by_type,
            },
            "net_profit": net_profit,
            "profit_margin": (net_profit / total_income * 100)
            if total_income > 0
            else Decimal("0"),
        }

    # ==================== 审计轨迹管理 ====================

    def log_operation(
        self,
        operation_type: str | OperationType,
        entity_type: str | EntityType,
        entity_id: str,
        entity_name: str = "",
        operator: str = "系统",
        operation_description: str = "",
        old_value: str = "",
        new_value: str = "",
        ip_address: str = "",
        notes: str = "",
    ) -> str:
        """
        记录操作审计日志

        Args:
            operation_type: 操作类型（创建、更新、删除等）
            entity_type: 实体类型（订单、收入、支出等）
            entity_id: 实体ID
            entity_name: 实体名称或描述
            operator: 操作人
            operation_description: 操作描述
            old_value: 旧值（JSON格式）
            new_value: 新值（JSON格式）
            ip_address: IP地址
            notes: 备注

        Returns:
            str: 审计日志ID
        """
        from ..models.business_models import AuditLog, OperationType, EntityType
        from datetime import datetime

        # 转换字符串为枚举（如果是字符串）
        if isinstance(operation_type, str):
            if operation_type in OperationType.__members__:
                op_type: OperationType = OperationType[operation_type]
            else:
                raise ValueError(f"无效的操作类型: {operation_type}")
        else:
            op_type = operation_type

        if isinstance(entity_type, str):
            if entity_type in EntityType.__members__:
                ent_type: EntityType = EntityType[entity_type]
            else:
                raise ValueError(f"无效的实体类型: {entity_type}")
        else:
            ent_type = entity_type

        # 创建审计日志
        audit_log = AuditLog(
            operation_type=op_type,
            entity_type=ent_type,
            entity_id=entity_id,
            entity_name=entity_name,
            operator=operator,
            operation_time=datetime.now(),
            operation_description=operation_description,
            old_value=old_value,
            new_value=new_value,
            ip_address=ip_address,
            notes=notes,
        )

        self.db.save_audit_log(audit_log)
        return audit_log.id

    def get_audit_logs(
        self,
        entity_type: str | None = None,
        entity_id: str | None = None,
        operator: str | None = None,
        start_time: date | None = None,
        end_time: date | None = None,
        limit: int = 100,
    ) -> list[dict[str, Any]]:
        """
        查询审计日志

        Args:
            entity_type: 实体类型（可选）
            entity_id: 实体ID（可选）
            operator: 操作人（可选）
            start_time: 开始时间（可选）
            end_time: 结束时间（可选）
            limit: 返回数量限制

        Returns:
            list[dict[str, Any]]: 审计日志列表
        """
        logs = self.db.list_audit_logs(
            entity_type=entity_type,
            entity_id=entity_id,
            operator=operator,
            start_time=start_time,
            end_time=end_time,
            limit=limit,
        )

        return [
            {
                "id": log.id,
                "operation_type": log.operation_type.value
                if hasattr(log.operation_type, "value")
                else log.operation_type,
                "entity_type": log.entity_type.value
                if hasattr(log.entity_type, "value")
                else log.entity_type,
                "entity_id": log.entity_id,
                "entity_name": log.entity_name,
                "operator": log.operator,
                "operation_time": log.operation_time,
                "operation_description": log.operation_description,
                "old_value": log.old_value,
                "new_value": log.new_value,
                "ip_address": log.ip_address,
                "notes": log.notes,
            }
            for log in logs
        ]

    def get_entity_audit_trail(self, entity_type: str, entity_id: str) -> List[Dict]:
        """
        获取特定实体的完整审计轨迹

        Args:
            entity_type: 实体类型
            entity_id: 实体ID

        Returns:
            List[Dict]: 审计轨迹列表，按时间倒序排列
        """
        return self.get_audit_logs(
            entity_type=entity_type, entity_id=entity_id, limit=1000
        )

    def get_operation_statistics(
        self, start_date: Optional[date] = None, end_date: Optional[date] = None
    ) -> Dict:
        """
        获取操作统计信息

        Args:
            start_date: 开始日期（可选）
            end_date: 结束日期（可选）

        Returns:
            Dict: 操作统计信息
        """
        logs = self.db.list_audit_logs(
            start_time=start_date, end_time=end_date, limit=10000
        )

        # 按操作类型统计
        operation_counts = {}
        entity_counts = {}
        operator_counts = {}

        for log in logs:
            op_type = (
                log.operation_type.value
                if hasattr(log.operation_type, "value")
                else str(log.operation_type)
            )
            entity_type = (
                log.entity_type.value
                if hasattr(log.entity_type, "value")
                else str(log.entity_type)
            )

            operation_counts[op_type] = operation_counts.get(op_type, 0) + 1
            entity_counts[entity_type] = entity_counts.get(entity_type, 0) + 1
            operator_counts[log.operator] = operator_counts.get(log.operator, 0) + 1

        return {
            "total_operations": len(logs),
            "by_operation_type": operation_counts,
            "by_entity_type": entity_counts,
            "by_operator": operator_counts,
            "period": {"start_date": start_date, "end_date": end_date},
        }

    # ==================== 会计期间管理 ====================

    def create_accounting_period(
        self, period_name: str, start_date: date, end_date: date, notes: str = ""
    ) -> Dict:
        """
        创建会计期间

        Args:
            period_name: 期间名称，如"2024年1月"
            start_date: 开始日期
            end_date: 结束日期
            notes: 备注

        Returns:
            Dict: 创建的会计期间信息
        """
        from ..models.business_models import AccountingPeriod
        from datetime import datetime

        # 验证日期范围
        if start_date > end_date:
            return {"error": "开始日期不能晚于结束日期"}

        # 检查是否与现有期间重叠
        existing_periods = self.db.list_accounting_periods()
        for period in existing_periods:
            if not (end_date < period.start_date or start_date > period.end_date):
                return {"error": f"与现有期间 {period.period_name} 重叠"}

        # 创建期间
        period = AccountingPeriod(
            period_name=period_name,
            start_date=start_date,
            end_date=end_date,
            status="开放",
            is_closed=False,
            notes=notes,
            created_at=datetime.now(),
            updated_at=datetime.now(),
        )

        self.db.save_accounting_period(period)

        # 记录审计日志
        self.log_operation(
            operation_type="CREATE",
            entity_type="ACCOUNTING_PERIOD",
            entity_id=period.id,
            entity_name=period_name,
            operation_description=f"创建会计期间：{period_name} ({start_date} 至 {end_date})",
        )

        return {
            "id": period.id,
            "period_name": period.period_name,
            "start_date": period.start_date,
            "end_date": period.end_date,
            "status": period.status,
            "message": "会计期间创建成功",
        }

    def adjust_accounting_period(
        self,
        period_id: str,
        new_start_date: Optional[date] = None,
        new_end_date: Optional[date] = None,
        new_period_name: Optional[str] = None,
        notes: str = "",
    ) -> Tuple[bool, str]:
        """
        调整会计期间（灵活调整）

        Args:
            period_id: 期间ID
            new_start_date: 新的开始日期（可选）
            new_end_date: 新的结束日期（可选）
            new_period_name: 新的期间名称（可选）
            notes: 调整原因备注

        Returns:
            Tuple[bool, str]: (是否成功, 消息)
        """
        from datetime import datetime
        import json

        # 获取期间
        period = self.db.get_accounting_period(period_id)
        if not period:
            return False, f"会计期间不存在: {period_id}"

        # 检查是否已关闭
        if period.is_closed:
            return False, f"会计期间 {period.period_name} 已关闭，不能调整"

        # 记录旧值
        old_values = {
            "period_name": period.period_name,
            "start_date": period.start_date.isoformat(),
            "end_date": period.end_date.isoformat(),
        }

        # 应用调整
        if new_start_date:
            period.start_date = new_start_date
        if new_end_date:
            period.end_date = new_end_date
        if new_period_name:
            period.period_name = new_period_name

        # 验证调整后的日期范围
        if period.start_date > period.end_date:
            return False, "调整后的开始日期不能晚于结束日期"

        # 检查是否与其他期间重叠
        existing_periods = self.db.list_accounting_periods()
        for other_period in existing_periods:
            if other_period.id == period_id:
                continue
            if not (
                period.end_date < other_period.start_date
                or period.start_date > other_period.end_date
            ):
                return False, f"调整后与期间 {other_period.period_name} 重叠"

        # 更新备注
        if notes:
            period.notes = (
                f"{period.notes}; 调整：{notes}" if period.notes else f"调整：{notes}"
            )

        period.updated_at = datetime.now()
        self.db.save_accounting_period(period)

        # 记录审计日志
        new_values = {
            "period_name": period.period_name,
            "start_date": period.start_date.isoformat(),
            "end_date": period.end_date.isoformat(),
        }

        self.log_operation(
            operation_type="ADJUST",
            entity_type="ACCOUNTING_PERIOD",
            entity_id=period.id,
            entity_name=period.period_name,
            operation_description=f"调整会计期间：{period.period_name}",
            old_value=json.dumps(old_values, ensure_ascii=False),
            new_value=json.dumps(new_values, ensure_ascii=False),
            notes=notes,
        )

        return True, f"会计期间 {period.period_name} 调整成功"

    def close_accounting_period(
        self, period_id: str, closed_by: str = "系统", notes: str = ""
    ) -> Tuple[bool, str]:
        """
        关闭会计期间

        Args:
            period_id: 期间ID
            closed_by: 关闭人
            notes: 备注

        Returns:
            Tuple[bool, str]: (是否成功, 消息)
        """
        from datetime import datetime

        # 获取期间
        period = self.db.get_accounting_period(period_id)
        if not period:
            return False, f"会计期间不存在: {period_id}"

        # 检查是否已关闭
        if period.is_closed:
            return False, f"会计期间 {period.period_name} 已经关闭"

        # 计算期间汇总数据
        period_summary = self.get_accrual_period_summary(
            period.start_date, period.end_date
        )

        # 更新期间数据
        period.total_income = period_summary["income"]["total"]
        period.total_expense = period_summary["expense"]["total"]
        period.net_profit = period_summary["net_profit"]
        period.is_closed = True
        period.status = "关闭"
        period.closed_by = closed_by
        period.closed_at = datetime.now()

        if notes:
            period.notes = (
                f"{period.notes}; 关闭：{notes}" if period.notes else f"关闭：{notes}"
            )

        period.updated_at = datetime.now()
        self.db.save_accounting_period(period)

        # 记录审计日志
        self.log_operation(
            operation_type="UPDATE",
            entity_type="ACCOUNTING_PERIOD",
            entity_id=period.id,
            entity_name=period.period_name,
            operation_description=f"关闭会计期间：{period.period_name}",
            new_value=f"收入: {period.total_income}, 支出: {period.total_expense}, 净利润: {period.net_profit}",
            notes=notes,
        )

        return True, f"会计期间 {period.period_name} 已关闭"

    def reopen_accounting_period(
        self, period_id: str, operator: str = "系统", notes: str = ""
    ) -> Tuple[bool, str]:
        """
        重新打开已关闭的会计期间

        Args:
            period_id: 期间ID
            operator: 操作人
            notes: 备注

        Returns:
            Tuple[bool, str]: (是否成功, 消息)
        """
        from datetime import datetime

        # 获取期间
        period = self.db.get_accounting_period(period_id)
        if not period:
            return False, f"会计期间不存在: {period_id}"

        # 检查是否已打开
        if not period.is_closed:
            return False, f"会计期间 {period.period_name} 已经是开放状态"

        # 重新打开
        period.is_closed = False
        period.status = "开放"

        if notes:
            period.notes = (
                f"{period.notes}; 重新打开：{notes}"
                if period.notes
                else f"重新打开：{notes}"
            )

        period.updated_at = datetime.now()
        self.db.save_accounting_period(period)

        # 记录审计日志
        self.log_operation(
            operation_type="UPDATE",
            entity_type="ACCOUNTING_PERIOD",
            entity_id=period.id,
            entity_name=period.period_name,
            operation_description=f"重新打开会计期间：{period.period_name}",
            notes=notes,
        )

        return True, f"会计期间 {period.period_name} 已重新打开"

    def get_accounting_period(self, period_id: str) -> Optional[Dict]:
        """
        获取会计期间详情

        Args:
            period_id: 期间ID

        Returns:
            Optional[Dict]: 期间详情，如果不存在则返回None
        """
        period = self.db.get_accounting_period(period_id)
        if not period:
            return None

        return {
            "id": period.id,
            "period_name": period.period_name,
            "start_date": period.start_date,
            "end_date": period.end_date,
            "status": period.status,
            "is_closed": period.is_closed,
            "total_income": period.total_income,
            "total_expense": period.total_expense,
            "net_profit": period.net_profit,
            "closed_by": period.closed_by,
            "closed_at": period.closed_at,
            "notes": period.notes,
            "created_at": period.created_at,
            "updated_at": period.updated_at,
        }

    def list_accounting_periods(self, include_closed: bool = True) -> List[Dict]:
        """
        列出所有会计期间

        Args:
            include_closed: 是否包含已关闭的期间

        Returns:
            List[Dict]: 期间列表
        """
        periods = self.db.list_accounting_periods()

        if not include_closed:
            periods = [p for p in periods if not p.is_closed]

        return [
            {
                "id": p.id,
                "period_name": p.period_name,
                "start_date": p.start_date,
                "end_date": p.end_date,
                "status": p.status,
                "is_closed": p.is_closed,
                "total_income": p.total_income,
                "total_expense": p.total_expense,
                "net_profit": p.net_profit,
            }
            for p in periods
        ]

    def get_current_accounting_period(
        self, reference_date: Optional[date] = None
    ) -> Optional[Dict]:
        """
        获取当前会计期间（包含指定日期的期间）

        Args:
            reference_date: 参考日期（默认为今天）

        Returns:
            Optional[Dict]: 当前期间，如果不存在则返回None
        """
        if reference_date is None:
            reference_date = date.today()

        periods = self.db.list_accounting_periods()

        for period in periods:
            if period.start_date <= reference_date <= period.end_date:
                return {
                    "id": period.id,
                    "period_name": period.period_name,
                    "start_date": period.start_date,
                    "end_date": period.end_date,
                    "status": period.status,
                    "is_closed": period.is_closed,
                }

        return None
