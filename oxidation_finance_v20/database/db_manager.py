#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
数据库管理器
"""

import sqlite3
import json
from pathlib import Path
from typing import Optional, List, Dict, Any
from datetime import datetime
from decimal import Decimal

from ..models.business_models import (
    Customer, Supplier, ProcessingOrder, Income, Expense,
    BankAccount, BankTransaction, OutsourcedProcessing,
    PricingUnit, ProcessType, OrderStatus, ExpenseType, BankType
)
from .schema import create_tables, drop_tables


class DatabaseManager:
    """数据库管理器 - 负责所有数据库操作"""
    
    def __init__(self, db_path: str = "oxidation_finance.db"):
        """初始化数据库管理器"""
        self.db_path = db_path
        self.conn: Optional[sqlite3.Connection] = None
    
    def connect(self):
        """连接到数据库"""
        self.conn = sqlite3.connect(self.db_path)
        self.conn.row_factory = sqlite3.Row  # 使用字典式访问
        create_tables(self.conn)
    
    def close(self):
        """关闭数据库连接"""
        if self.conn:
            self.conn.close()
            self.conn = None
    
    def __enter__(self):
        """上下文管理器入口"""
        self.connect()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """上下文管理器出口"""
        self.close()
    
    # ==================== 客户管理 ====================
    
    def save_customer(self, customer: Customer) -> str:
        """保存客户信息"""
        cursor = self.conn.cursor()
        cursor.execute("""
            INSERT OR REPLACE INTO customers 
            (id, name, contact, phone, address, credit_limit, notes, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            customer.id, customer.name, customer.contact, customer.phone,
            customer.address, float(customer.credit_limit), customer.notes,
            customer.created_at.isoformat()
        ))
        self.conn.commit()
        return customer.id
    
    def get_customer(self, customer_id: str) -> Optional[Customer]:
        """获取客户信息"""
        cursor = self.conn.cursor()
        cursor.execute("SELECT * FROM customers WHERE id = ?", (customer_id,))
        row = cursor.fetchone()
        
        if row:
            return Customer(
                id=row['id'],
                name=row['name'],
                contact=row['contact'],
                phone=row['phone'],
                address=row['address'],
                credit_limit=Decimal(str(row['credit_limit'])),
                notes=row['notes'],
                created_at=datetime.fromisoformat(row['created_at'])
            )
        return None
    
    def list_customers(self) -> List[Customer]:
        """获取所有客户"""
        cursor = self.conn.cursor()
        cursor.execute("SELECT * FROM customers ORDER BY name")
        rows = cursor.fetchall()
        
        return [
            Customer(
                id=row['id'],
                name=row['name'],
                contact=row['contact'],
                phone=row['phone'],
                address=row['address'],
                credit_limit=Decimal(str(row['credit_limit'])),
                notes=row['notes'],
                created_at=datetime.fromisoformat(row['created_at'])
            )
            for row in rows
        ]
    
    # ==================== 供应商管理 ====================
    
    def save_supplier(self, supplier: Supplier) -> str:
        """保存供应商信息"""
        cursor = self.conn.cursor()
        cursor.execute("""
            INSERT OR REPLACE INTO suppliers 
            (id, name, contact, phone, address, business_type, notes, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            supplier.id, supplier.name, supplier.contact, supplier.phone,
            supplier.address, supplier.business_type, supplier.notes,
            supplier.created_at.isoformat()
        ))
        self.conn.commit()
        return supplier.id
    
    def get_supplier(self, supplier_id: str) -> Optional[Supplier]:
        """获取供应商信息"""
        cursor = self.conn.cursor()
        cursor.execute("SELECT * FROM suppliers WHERE id = ?", (supplier_id,))
        row = cursor.fetchone()
        
        if row:
            return Supplier(
                id=row['id'],
                name=row['name'],
                contact=row['contact'],
                phone=row['phone'],
                address=row['address'],
                business_type=row['business_type'],
                notes=row['notes'],
                created_at=datetime.fromisoformat(row['created_at'])
            )
        return None
    
    def list_suppliers(self) -> List[Supplier]:
        """获取所有供应商"""
        cursor = self.conn.cursor()
        cursor.execute("SELECT * FROM suppliers ORDER BY name")
        rows = cursor.fetchall()
        
        return [
            Supplier(
                id=row['id'],
                name=row['name'],
                contact=row['contact'],
                phone=row['phone'],
                address=row['address'],
                business_type=row['business_type'],
                notes=row['notes'],
                created_at=datetime.fromisoformat(row['created_at'])
            )
            for row in rows
        ]
    
    # ==================== 订单管理 ====================
    
    def save_order(self, order: ProcessingOrder) -> str:
        """保存加工订单"""
        cursor = self.conn.cursor()
        cursor.execute("""
            INSERT OR REPLACE INTO processing_orders 
            (id, order_no, customer_id, customer_name, item_description,
             quantity, pricing_unit, unit_price, processes, outsourced_processes,
             total_amount, outsourcing_cost, status, order_date, completion_date,
             delivery_date, received_amount, notes, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            order.id, order.order_no, order.customer_id, order.customer_name,
            order.item_description, float(order.quantity), order.pricing_unit.value,
            float(order.unit_price), 
            json.dumps([p.value if hasattr(p, 'value') else p for p in order.processes]),
            json.dumps(order.outsourced_processes), float(order.total_amount),
            float(order.outsourcing_cost), order.status.value,
            order.order_date.isoformat(),
            order.completion_date.isoformat() if order.completion_date else None,
            order.delivery_date.isoformat() if order.delivery_date else None,
            float(order.received_amount), order.notes,
            order.created_at.isoformat(), order.updated_at.isoformat()
        ))
        self.conn.commit()
        return order.id
    
    def get_order(self, order_id: str) -> Optional[ProcessingOrder]:
        """获取订单信息"""
        cursor = self.conn.cursor()
        cursor.execute("SELECT * FROM processing_orders WHERE id = ?", (order_id,))
        row = cursor.fetchone()
        
        if row:
            return self._row_to_order(row)
        return None
    
    def list_orders(self, customer_id: Optional[str] = None, 
                   status: Optional[OrderStatus] = None) -> List[ProcessingOrder]:
        """获取订单列表"""
        cursor = self.conn.cursor()
        
        query = "SELECT * FROM processing_orders WHERE 1=1"
        params = []
        
        if customer_id:
            query += " AND customer_id = ?"
            params.append(customer_id)
        
        if status:
            query += " AND status = ?"
            params.append(status.value)
        
        query += " ORDER BY order_date DESC"
        
        cursor.execute(query, params)
        rows = cursor.fetchall()
        
        return [self._row_to_order(row) for row in rows]
    
    def _row_to_order(self, row) -> ProcessingOrder:
        """将数据库行转换为订单对象"""
        from datetime import date
        
        return ProcessingOrder(
            id=row['id'],
            order_no=row['order_no'],
            customer_id=row['customer_id'],
            customer_name=row['customer_name'],
            item_description=row['item_description'],
            quantity=Decimal(str(row['quantity'])),
            pricing_unit=PricingUnit(row['pricing_unit']),
            unit_price=Decimal(str(row['unit_price'])),
            processes=[ProcessType(p) for p in json.loads(row['processes'])],
            outsourced_processes=json.loads(row['outsourced_processes']) if row['outsourced_processes'] else [],
            total_amount=Decimal(str(row['total_amount'])),
            outsourcing_cost=Decimal(str(row['outsourcing_cost'])),
            status=OrderStatus(row['status']),
            order_date=date.fromisoformat(row['order_date']),
            completion_date=date.fromisoformat(row['completion_date']) if row['completion_date'] else None,
            delivery_date=date.fromisoformat(row['delivery_date']) if row['delivery_date'] else None,
            received_amount=Decimal(str(row['received_amount'])),
            notes=row['notes'],
            created_at=datetime.fromisoformat(row['created_at']),
            updated_at=datetime.fromisoformat(row['updated_at'])
        )
    
    # ==================== 收入管理 ====================
    
    def save_income(self, income: Income) -> str:
        """保存收入记录"""
        cursor = self.conn.cursor()
        cursor.execute("""
            INSERT OR REPLACE INTO incomes 
            (id, customer_id, customer_name, amount, bank_type, has_invoice,
             related_orders, allocation, income_date, notes, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            income.id, income.customer_id, income.customer_name,
            float(income.amount), income.bank_type.value, int(income.has_invoice),
            json.dumps(income.related_orders), json.dumps({k: float(v) for k, v in income.allocation.items()}),
            income.income_date.isoformat(), income.notes,
            income.created_at.isoformat()
        ))
        self.conn.commit()
        return income.id
    
    def get_income(self, income_id: str) -> Optional[Income]:
        """获取收入记录"""
        cursor = self.conn.cursor()
        cursor.execute("SELECT * FROM incomes WHERE id = ?", (income_id,))
        row = cursor.fetchone()
        
        if row:
            return self._row_to_income(row)
        return None
    
    def list_incomes(self, customer_id: Optional[str] = None) -> List[Income]:
        """获取收入列表"""
        cursor = self.conn.cursor()
        
        if customer_id:
            cursor.execute("SELECT * FROM incomes WHERE customer_id = ? ORDER BY income_date DESC", (customer_id,))
        else:
            cursor.execute("SELECT * FROM incomes ORDER BY income_date DESC")
        
        rows = cursor.fetchall()
        return [self._row_to_income(row) for row in rows]
    
    def _row_to_income(self, row) -> Income:
        """将数据库行转换为收入对象"""
        from datetime import date
        
        allocation_data = json.loads(row['allocation']) if row['allocation'] else {}
        
        return Income(
            id=row['id'],
            customer_id=row['customer_id'],
            customer_name=row['customer_name'],
            amount=Decimal(str(row['amount'])),
            bank_type=BankType(row['bank_type']),
            has_invoice=bool(row['has_invoice']),
            related_orders=json.loads(row['related_orders']) if row['related_orders'] else [],
            allocation={k: Decimal(str(v)) for k, v in allocation_data.items()},
            income_date=date.fromisoformat(row['income_date']),
            notes=row['notes'],
            created_at=datetime.fromisoformat(row['created_at'])
        )
    
    # ==================== 支出管理 ====================
    
    def save_expense(self, expense: Expense) -> str:
        """保存支出记录"""
        cursor = self.conn.cursor()
        cursor.execute("""
            INSERT OR REPLACE INTO expenses 
            (id, expense_type, supplier_id, supplier_name, amount, bank_type,
             has_invoice, related_order_id, expense_date, description, notes, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            expense.id, expense.expense_type.value, expense.supplier_id,
            expense.supplier_name, float(expense.amount), expense.bank_type.value,
            int(expense.has_invoice), expense.related_order_id,
            expense.expense_date.isoformat(), expense.description,
            expense.notes, expense.created_at.isoformat()
        ))
        self.conn.commit()
        return expense.id
    
    def get_expense(self, expense_id: str) -> Optional[Expense]:
        """获取支出记录"""
        cursor = self.conn.cursor()
        cursor.execute("SELECT * FROM expenses WHERE id = ?", (expense_id,))
        row = cursor.fetchone()
        
        if row:
            return self._row_to_expense(row)
        return None
    
    def list_expenses(self, supplier_id: Optional[str] = None,
                     expense_type: Optional[ExpenseType] = None) -> List[Expense]:
        """获取支出列表"""
        cursor = self.conn.cursor()
        
        query = "SELECT * FROM expenses WHERE 1=1"
        params = []
        
        if supplier_id:
            query += " AND supplier_id = ?"
            params.append(supplier_id)
        
        if expense_type:
            query += " AND expense_type = ?"
            params.append(expense_type.value)
        
        query += " ORDER BY expense_date DESC"
        
        cursor.execute(query, params)
        rows = cursor.fetchall()
        
        return [self._row_to_expense(row) for row in rows]
    
    def _row_to_expense(self, row) -> Expense:
        """将数据库行转换为支出对象"""
        from datetime import date
        
        return Expense(
            id=row['id'],
            expense_type=ExpenseType(row['expense_type']),
            supplier_id=row['supplier_id'],
            supplier_name=row['supplier_name'],
            amount=Decimal(str(row['amount'])),
            bank_type=BankType(row['bank_type']),
            has_invoice=bool(row['has_invoice']),
            related_order_id=row['related_order_id'],
            expense_date=date.fromisoformat(row['expense_date']),
            description=row['description'],
            notes=row['notes'],
            created_at=datetime.fromisoformat(row['created_at'])
        )
    
    # ==================== 银行账户管理 ====================
    
    def save_bank_account(self, account: BankAccount) -> str:
        """保存银行账户"""
        cursor = self.conn.cursor()
        cursor.execute("""
            INSERT OR REPLACE INTO bank_accounts 
            (id, bank_type, account_name, account_number, balance, notes)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (
            account.id, account.bank_type.value, account.account_name,
            account.account_number, float(account.balance), account.notes
        ))
        self.conn.commit()
        return account.id
    
    def get_bank_account(self, account_id: str) -> Optional[BankAccount]:
        """获取银行账户"""
        cursor = self.conn.cursor()
        cursor.execute("SELECT * FROM bank_accounts WHERE id = ?", (account_id,))
        row = cursor.fetchone()
        
        if row:
            return BankAccount(
                id=row['id'],
                bank_type=BankType(row['bank_type']),
                account_name=row['account_name'],
                account_number=row['account_number'],
                balance=Decimal(str(row['balance'])),
                notes=row['notes']
            )
        return None
    
    def list_bank_accounts(self) -> List[BankAccount]:
        """获取所有银行账户"""
        cursor = self.conn.cursor()
        cursor.execute("SELECT * FROM bank_accounts")
        rows = cursor.fetchall()
        
        return [
            BankAccount(
                id=row['id'],
                bank_type=BankType(row['bank_type']),
                account_name=row['account_name'],
                account_number=row['account_number'],
                balance=Decimal(str(row['balance'])),
                notes=row['notes']
            )
            for row in rows
        ]
    
    # ==================== 银行交易管理 ====================
    
    def save_bank_transaction(self, transaction: BankTransaction) -> str:
        """保存银行交易记录"""
        cursor = self.conn.cursor()
        cursor.execute("""
            INSERT OR REPLACE INTO bank_transactions 
            (id, bank_type, transaction_date, amount, counterparty, description,
             matched, matched_income_id, matched_expense_id, notes, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            transaction.id, transaction.bank_type.value,
            transaction.transaction_date.isoformat(), float(transaction.amount),
            transaction.counterparty, transaction.description, int(transaction.matched),
            transaction.matched_income_id, transaction.matched_expense_id,
            transaction.notes, transaction.created_at.isoformat()
        ))
        self.conn.commit()
        return transaction.id
    
    def get_bank_transaction(self, transaction_id: str) -> Optional[BankTransaction]:
        """获取银行交易记录"""
        cursor = self.conn.cursor()
        cursor.execute("SELECT * FROM bank_transactions WHERE id = ?", (transaction_id,))
        row = cursor.fetchone()
        
        if row:
            return self._row_to_transaction(row)
        return None
    
    def list_bank_transactions(self, bank_type: Optional[BankType] = None) -> List[BankTransaction]:
        """获取银行交易列表"""
        cursor = self.conn.cursor()
        
        if bank_type:
            cursor.execute("SELECT * FROM bank_transactions WHERE bank_type = ? ORDER BY transaction_date DESC", 
                         (bank_type.value,))
        else:
            cursor.execute("SELECT * FROM bank_transactions ORDER BY transaction_date DESC")
        
        rows = cursor.fetchall()
        return [self._row_to_transaction(row) for row in rows]
    
    def _row_to_transaction(self, row) -> BankTransaction:
        """将数据库行转换为交易对象"""
        from datetime import date
        
        return BankTransaction(
            id=row['id'],
            bank_type=BankType(row['bank_type']),
            transaction_date=date.fromisoformat(row['transaction_date']),
            amount=Decimal(str(row['amount'])),
            counterparty=row['counterparty'],
            description=row['description'],
            matched=bool(row['matched']),
            matched_income_id=row['matched_income_id'],
            matched_expense_id=row['matched_expense_id'],
            notes=row['notes'],
            created_at=datetime.fromisoformat(row['created_at'])
        )

    # ==================== 委外加工管理 ====================
    
    def save_outsourced_processing(self, processing: OutsourcedProcessing) -> str:
        """保存委外加工记录"""
        cursor = self.conn.cursor()
        cursor.execute("""
            INSERT OR REPLACE INTO outsourced_processing 
            (id, order_id, supplier_id, supplier_name, process_type, process_description,
             quantity, unit_price, total_cost, paid_amount, process_date, notes, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            processing.id, processing.order_id, processing.supplier_id, processing.supplier_name,
            processing.process_type.value if hasattr(processing.process_type, 'value') else processing.process_type,
            processing.process_description,
            float(processing.quantity), float(processing.unit_price), float(processing.total_cost),
            float(processing.paid_amount), processing.process_date.isoformat(),
            processing.notes, processing.created_at.isoformat(), processing.updated_at.isoformat()
        ))
        self.conn.commit()
        return processing.id
    
    def get_outsourced_processing(self, processing_id: str) -> Optional[OutsourcedProcessing]:
        """获取委外加工记录"""
        cursor = self.conn.cursor()
        cursor.execute("SELECT * FROM outsourced_processing WHERE id = ?", (processing_id,))
        row = cursor.fetchone()
        
        if row:
            return self._row_to_outsourced_processing(row)
        return None
    
    def list_outsourced_processing(self, order_id: Optional[str] = None,
                                   supplier_id: Optional[str] = None) -> List[OutsourcedProcessing]:
        """获取委外加工列表"""
        cursor = self.conn.cursor()
        
        query = "SELECT * FROM outsourced_processing WHERE 1=1"
        params = []
        
        if order_id:
            query += " AND order_id = ?"
            params.append(order_id)
        
        if supplier_id:
            query += " AND supplier_id = ?"
            params.append(supplier_id)
        
        query += " ORDER BY process_date DESC"
        
        cursor.execute(query, params)
        rows = cursor.fetchall()
        
        return [self._row_to_outsourced_processing(row) for row in rows]
    
    def _row_to_outsourced_processing(self, row) -> OutsourcedProcessing:
        """将数据库行转换为委外加工对象"""
        from datetime import date
        
        return OutsourcedProcessing(
            id=row['id'],
            order_id=row['order_id'],
            supplier_id=row['supplier_id'],
            supplier_name=row['supplier_name'],
            process_type=ProcessType(row['process_type']),
            process_description=row['process_description'] or "",
            quantity=Decimal(str(row['quantity'])),
            unit_price=Decimal(str(row['unit_price'])),
            total_cost=Decimal(str(row['total_cost'])),
            paid_amount=Decimal(str(row['paid_amount'])),
            process_date=date.fromisoformat(row['process_date']),
            notes=row['notes'] or "",
            created_at=datetime.fromisoformat(row['created_at']),
            updated_at=datetime.fromisoformat(row['updated_at'])
        )

    # ==================== 审计日志管理 ====================
    
    def save_audit_log(self, audit_log) -> str:
        """保存审计日志"""
        from ..models.business_models import OperationType, EntityType
        
        cursor = self.conn.cursor()
        cursor.execute("""
            INSERT INTO audit_logs 
            (id, operation_type, entity_type, entity_id, entity_name, operator,
             operation_time, operation_description, old_value, new_value, ip_address, notes)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            audit_log.id,
            audit_log.operation_type.value if hasattr(audit_log.operation_type, 'value') else str(audit_log.operation_type),
            audit_log.entity_type.value if hasattr(audit_log.entity_type, 'value') else str(audit_log.entity_type),
            audit_log.entity_id,
            audit_log.entity_name,
            audit_log.operator,
            audit_log.operation_time.isoformat(),
            audit_log.operation_description,
            audit_log.old_value,
            audit_log.new_value,
            audit_log.ip_address,
            audit_log.notes
        ))
        self.conn.commit()
        return audit_log.id
    
    def list_audit_logs(
        self,
        entity_type: Optional[str] = None,
        entity_id: Optional[str] = None,
        operator: Optional[str] = None,
        start_time: Optional[Any] = None,
        end_time: Optional[Any] = None,
        limit: int = 100
    ) -> List:
        """查询审计日志"""
        from ..models.business_models import AuditLog, OperationType, EntityType
        from datetime import date
        
        cursor = self.conn.cursor()
        
        query = "SELECT * FROM audit_logs WHERE 1=1"
        params = []
        
        if entity_type:
            query += " AND entity_type = ?"
            params.append(entity_type)
        
        if entity_id:
            query += " AND entity_id = ?"
            params.append(entity_id)
        
        if operator:
            query += " AND operator = ?"
            params.append(operator)
        
        if start_time:
            if isinstance(start_time, date):
                start_time = datetime.combine(start_time, datetime.min.time())
            query += " AND operation_time >= ?"
            params.append(start_time.isoformat())
        
        if end_time:
            if isinstance(end_time, date):
                end_time = datetime.combine(end_time, datetime.max.time())
            query += " AND operation_time <= ?"
            params.append(end_time.isoformat())
        
        query += " ORDER BY operation_time DESC LIMIT ?"
        params.append(limit)
        
        cursor.execute(query, params)
        rows = cursor.fetchall()
        
        logs = []
        for row in rows:
            try:
                op_type = OperationType(row['operation_type'])
            except (ValueError, KeyError):
                op_type = row['operation_type']
            
            try:
                ent_type = EntityType(row['entity_type'])
            except (ValueError, KeyError):
                ent_type = row['entity_type']
            
            logs.append(AuditLog(
                id=row['id'],
                operation_type=op_type,
                entity_type=ent_type,
                entity_id=row['entity_id'],
                entity_name=row['entity_name'] or "",
                operator=row['operator'],
                operation_time=datetime.fromisoformat(row['operation_time']),
                operation_description=row['operation_description'] or "",
                old_value=row['old_value'] or "",
                new_value=row['new_value'] or "",
                ip_address=row['ip_address'] or "",
                notes=row['notes'] or ""
            ))
        
        return logs
    
    # ==================== 会计期间管理 ====================
    
    def save_accounting_period(self, period) -> str:
        """保存会计期间"""
        cursor = self.conn.cursor()
        cursor.execute("""
            INSERT OR REPLACE INTO accounting_periods 
            (id, period_name, start_date, end_date, status, is_closed,
             total_income, total_expense, net_profit, closed_by, closed_at,
             notes, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            period.id,
            period.period_name,
            period.start_date.isoformat(),
            period.end_date.isoformat(),
            period.status,
            1 if period.is_closed else 0,
            float(period.total_income),
            float(period.total_expense),
            float(period.net_profit),
            period.closed_by or "",
            period.closed_at.isoformat() if period.closed_at else None,
            period.notes,
            period.created_at.isoformat(),
            period.updated_at.isoformat()
        ))
        self.conn.commit()
        return period.id
    
    def get_accounting_period(self, period_id: str) -> Optional[Any]:
        """获取会计期间"""
        from ..models.business_models import AccountingPeriod
        from datetime import date
        
        cursor = self.conn.cursor()
        cursor.execute("SELECT * FROM accounting_periods WHERE id = ?", (period_id,))
        row = cursor.fetchone()
        
        if row:
            return AccountingPeriod(
                id=row['id'],
                period_name=row['period_name'],
                start_date=date.fromisoformat(row['start_date']),
                end_date=date.fromisoformat(row['end_date']),
                status=row['status'],
                is_closed=bool(row['is_closed']),
                total_income=Decimal(str(row['total_income'])),
                total_expense=Decimal(str(row['total_expense'])),
                net_profit=Decimal(str(row['net_profit'])),
                closed_by=row['closed_by'] or "",
                closed_at=datetime.fromisoformat(row['closed_at']) if row['closed_at'] else None,
                notes=row['notes'] or "",
                created_at=datetime.fromisoformat(row['created_at']),
                updated_at=datetime.fromisoformat(row['updated_at'])
            )
        return None
    
    def list_accounting_periods(self) -> List:
        """获取所有会计期间"""
        from ..models.business_models import AccountingPeriod
        from datetime import date
        
        cursor = self.conn.cursor()
        cursor.execute("SELECT * FROM accounting_periods ORDER BY start_date DESC")
        rows = cursor.fetchall()
        
        periods = []
        for row in rows:
            periods.append(AccountingPeriod(
                id=row['id'],
                period_name=row['period_name'],
                start_date=date.fromisoformat(row['start_date']),
                end_date=date.fromisoformat(row['end_date']),
                status=row['status'],
                is_closed=bool(row['is_closed']),
                total_income=Decimal(str(row['total_income'])),
                total_expense=Decimal(str(row['total_expense'])),
                net_profit=Decimal(str(row['net_profit'])),
                closed_by=row['closed_by'] or "",
                closed_at=datetime.fromisoformat(row['closed_at']) if row['closed_at'] else None,
                notes=row['notes'] or "",
                created_at=datetime.fromisoformat(row['created_at']),
                updated_at=datetime.fromisoformat(row['updated_at'])
            ))
        
        return periods
