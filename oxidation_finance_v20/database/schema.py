#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
数据库表结构定义
"""

import sqlite3
from pathlib import Path


def create_tables(conn: sqlite3.Connection):
    """创建所有数据库表"""
    cursor = conn.cursor()

    # 1. 客户表
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS customers (
            id TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            contact TEXT,
            phone TEXT,
            address TEXT,
            credit_limit TEXT DEFAULT '0',
            notes TEXT,
            created_at TEXT NOT NULL
        )
    """)

    # 2. 供应商表
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS suppliers (
            id TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            contact TEXT,
            phone TEXT,
            address TEXT,
            business_type TEXT,
            notes TEXT,
            created_at TEXT NOT NULL
        )
    """)

    # 3. 加工订单表
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS processing_orders (
            id TEXT PRIMARY KEY,
            order_no TEXT UNIQUE NOT NULL,
            customer_id TEXT NOT NULL,
            customer_name TEXT NOT NULL,
            item_description TEXT NOT NULL,
            quantity TEXT NOT NULL,
            pricing_unit TEXT NOT NULL,
            unit_price TEXT NOT NULL,
            processes TEXT NOT NULL,
            outsourced_processes TEXT,
            total_amount TEXT NOT NULL,
            outsourcing_cost TEXT DEFAULT '0',
            status TEXT NOT NULL,
            order_date TEXT NOT NULL,
            completion_date TEXT,
            delivery_date TEXT,
            received_amount TEXT DEFAULT '0',
            notes TEXT,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL,
            FOREIGN KEY (customer_id) REFERENCES customers(id)
        )
    """)

    # 4. 收入记录表
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS incomes (
            id TEXT PRIMARY KEY,
            customer_id TEXT NOT NULL,
            customer_name TEXT NOT NULL,
            amount TEXT NOT NULL,
            bank_type TEXT NOT NULL,
            has_invoice INTEGER DEFAULT 0,
            related_orders TEXT,
            allocation TEXT,
            income_date TEXT NOT NULL,
            notes TEXT,
            created_at TEXT NOT NULL,
            FOREIGN KEY (customer_id) REFERENCES customers(id)
        )
    """)

    # 5. 支出记录表
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS expenses (
            id TEXT PRIMARY KEY,
            expense_type TEXT NOT NULL,
            supplier_id TEXT,
            supplier_name TEXT,
            amount TEXT NOT NULL,
            bank_type TEXT NOT NULL,
            has_invoice INTEGER DEFAULT 0,
            related_order_id TEXT,
            expense_date TEXT NOT NULL,
            description TEXT,
            notes TEXT,
            created_at TEXT NOT NULL,
            FOREIGN KEY (supplier_id) REFERENCES suppliers(id),
            FOREIGN KEY (related_order_id) REFERENCES processing_orders(id)
        )
    """)

    # 6. 银行账户表
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS bank_accounts (
            id TEXT PRIMARY KEY,
            bank_type TEXT NOT NULL,
            account_name TEXT NOT NULL,
            account_number TEXT,
            balance TEXT DEFAULT '0',
            notes TEXT
        )
    """)

    # 7. 银行交易记录表
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS bank_transactions (
            id TEXT PRIMARY KEY,
            bank_type TEXT NOT NULL,
            transaction_date TEXT NOT NULL,
            amount TEXT NOT NULL,
            counterparty TEXT,
            description TEXT,
            matched INTEGER DEFAULT 0,
            matched_income_id TEXT,
            matched_expense_id TEXT,
            notes TEXT,
            created_at TEXT NOT NULL,
            FOREIGN KEY (matched_income_id) REFERENCES incomes(id),
            FOREIGN KEY (matched_expense_id) REFERENCES expenses(id)
        )
    """)

    # 8. 委外加工记录表
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS outsourced_processing (
            id TEXT PRIMARY KEY,
            order_id TEXT NOT NULL,
            supplier_id TEXT NOT NULL,
            supplier_name TEXT NOT NULL,
            process_type TEXT NOT NULL,
            process_description TEXT,
            quantity TEXT NOT NULL,
            unit_price TEXT NOT NULL,
            total_cost TEXT NOT NULL,
            paid_amount TEXT DEFAULT '0',
            process_date TEXT NOT NULL,
            notes TEXT,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL,
            FOREIGN KEY (order_id) REFERENCES processing_orders(id),
            FOREIGN KEY (supplier_id) REFERENCES suppliers(id)
        )
    """)

    # 9. 审计日志表
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS audit_logs (
            id TEXT PRIMARY KEY,
            operation_type TEXT NOT NULL,
            entity_type TEXT NOT NULL,
            entity_id TEXT NOT NULL,
            entity_name TEXT,
            operator TEXT NOT NULL,
            operation_time TEXT NOT NULL,
            operation_description TEXT,
            old_value TEXT,
            new_value TEXT,
            ip_address TEXT,
            notes TEXT
        )
    """)

    # 10. 会计期间表
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS accounting_periods (
            id TEXT PRIMARY KEY,
            period_name TEXT NOT NULL,
            start_date TEXT NOT NULL,
            end_date TEXT NOT NULL,
            status TEXT NOT NULL,
            is_closed INTEGER DEFAULT 0,
            total_income TEXT DEFAULT '0',
            total_expense TEXT DEFAULT '0',
            net_profit TEXT DEFAULT '0',
            closed_by TEXT,
            closed_at TEXT,
            notes TEXT,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL
        )
    """)
    
    # 11. 会计凭证表
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS accounting_vouchers (
            id TEXT PRIMARY KEY,
            voucher_no TEXT NOT NULL,
            voucher_date TEXT NOT NULL,
            accounting_period TEXT NOT NULL,
            summary TEXT NOT NULL,
            total_debit TEXT NOT NULL,
            total_credit TEXT NOT NULL,
            created_by TEXT NOT NULL,
            reviewed_by TEXT,
            posted_by TEXT,
            reviewed_at TEXT,
            posted_at TEXT,
            status TEXT NOT NULL DEFAULT '草稿',
            source_type TEXT,
            source_id TEXT,
            notes TEXT,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL,
            UNIQUE(voucher_no)
        )
    """)
    
    # 12. 凭证明细表
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS voucher_lines (
            id TEXT PRIMARY KEY,
            voucher_id TEXT NOT NULL,
            account_code TEXT NOT NULL,
            account_name TEXT NOT NULL,
            debit TEXT NOT NULL DEFAULT '0',
            credit TEXT NOT NULL DEFAULT '0',
            summary TEXT,
            related_entity_type TEXT,
            related_entity_id TEXT,
            FOREIGN KEY (voucher_id) REFERENCES accounting_vouchers(id)
        )
    """)

    # 创建索引以提高查询性能
    cursor.execute(
        "CREATE INDEX IF NOT EXISTS idx_orders_customer ON processing_orders(customer_id)"
    )
    cursor.execute(
        "CREATE INDEX IF NOT EXISTS idx_orders_date ON processing_orders(order_date)"
    )
    cursor.execute(
        "CREATE INDEX IF NOT EXISTS idx_orders_status ON processing_orders(status)"
    )
    cursor.execute(
        "CREATE INDEX IF NOT EXISTS idx_incomes_customer ON incomes(customer_id)"
    )
    cursor.execute(
        "CREATE INDEX IF NOT EXISTS idx_incomes_date ON incomes(income_date)"
    )
    cursor.execute(
        "CREATE INDEX IF NOT EXISTS idx_expenses_supplier ON expenses(supplier_id)"
    )
    cursor.execute(
        "CREATE INDEX IF NOT EXISTS idx_expenses_date ON expenses(expense_date)"
    )
    cursor.execute(
        "CREATE INDEX IF NOT EXISTS idx_expenses_type ON expenses(expense_type)"
    )
    cursor.execute(
        "CREATE INDEX IF NOT EXISTS idx_transactions_date ON bank_transactions(transaction_date)"
    )
    cursor.execute(
        "CREATE INDEX IF NOT EXISTS idx_transactions_bank ON bank_transactions(bank_type)"
    )
    cursor.execute(
        "CREATE INDEX IF NOT EXISTS idx_outsourced_order ON outsourced_processing(order_id)"
    )
    cursor.execute(
        "CREATE INDEX IF NOT EXISTS idx_outsourced_supplier ON outsourced_processing(supplier_id)"
    )
    cursor.execute(
        "CREATE INDEX IF NOT EXISTS idx_outsourced_date ON outsourced_processing(process_date)"
    )
    cursor.execute(
        "CREATE INDEX IF NOT EXISTS idx_audit_entity ON audit_logs(entity_type, entity_id)"
    )
    cursor.execute(
        "CREATE INDEX IF NOT EXISTS idx_audit_time ON audit_logs(operation_time)"
    )
    cursor.execute(
        "CREATE INDEX IF NOT EXISTS idx_audit_operator ON audit_logs(operator)"
    )
    cursor.execute(
        "CREATE INDEX IF NOT EXISTS idx_period_dates ON accounting_periods(start_date, end_date)"
    )
    cursor.execute(
        "CREATE INDEX IF NOT EXISTS idx_period_status ON accounting_periods(status)"
    )
    # 会计凭证相关索引
    cursor.execute(
        "CREATE INDEX IF NOT EXISTS idx_voucher_period ON accounting_vouchers(accounting_period)"
    )
    cursor.execute(
        "CREATE INDEX IF NOT EXISTS idx_voucher_date ON accounting_vouchers(voucher_date)"
    )
    cursor.execute(
        "CREATE INDEX IF NOT EXISTS idx_voucher_status ON accounting_vouchers(status)"
    )
    cursor.execute(
        "CREATE INDEX IF NOT EXISTS idx_voucher_no ON accounting_vouchers(voucher_no)"
    )
    cursor.execute(
        "CREATE INDEX IF NOT EXISTS idx_voucher_source ON accounting_vouchers(source_type, source_id)"
    )
    cursor.execute(
        "CREATE INDEX IF NOT EXISTS idx_voucher_line_voucher ON voucher_lines(voucher_id)"
    )
    cursor.execute(
        "CREATE INDEX IF NOT EXISTS idx_voucher_line_account ON voucher_lines(account_code)"
    )

    # 13. 会计科目表（核心骨架）
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS chart_of_accounts (
            id TEXT PRIMARY KEY,
            code TEXT NOT NULL UNIQUE,
            name TEXT NOT NULL,
            account_type TEXT NOT NULL,
            parent_id TEXT,
            level INTEGER DEFAULT 1,
            balance_direction TEXT DEFAULT '借',
            is_active INTEGER DEFAULT 1,
            is_controlled INTEGER DEFAULT 0,
            aux_customer INTEGER DEFAULT 0,
            aux_supplier INTEGER DEFAULT 0,
            aux_department INTEGER DEFAULT 0,
            aux_project INTEGER DEFAULT 0,
            aux_employee INTEGER DEFAULT 0,
            sort_order INTEGER DEFAULT 0,
            notes TEXT,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL,
            FOREIGN KEY (parent_id) REFERENCES chart_of_accounts(id)
        )
    """)

    # 14. 科目余额表（按期间汇总）
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS account_balances (
            id TEXT PRIMARY KEY,
            account_code TEXT NOT NULL,
            period_id TEXT NOT NULL,
            opening_balance REAL DEFAULT 0,
            debit_amount REAL DEFAULT 0,
            credit_amount REAL DEFAULT 0,
            closing_balance REAL DEFAULT 0,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL,
            UNIQUE(account_code, period_id),
            FOREIGN KEY (account_code) REFERENCES chart_of_accounts(code)
        )
    """)

    # 15. 部门表（辅助核算）
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS departments (
            id TEXT PRIMARY KEY,
            code TEXT UNIQUE NOT NULL,
            name TEXT NOT NULL,
            manager TEXT,
            is_active INTEGER DEFAULT 1,
            sort_order INTEGER DEFAULT 0,
            notes TEXT,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL
        )
    """)

    # 16. 项目表（辅助核算）
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS projects (
            id TEXT PRIMARY KEY,
            code TEXT UNIQUE NOT NULL,
            name TEXT NOT NULL,
            status TEXT DEFAULT '进行中',
            start_date TEXT,
            end_date TEXT,
            budget REAL DEFAULT 0,
            manager TEXT,
            notes TEXT,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL
        )
    """)

    # 17. 系统参数表
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS system_settings (
            key TEXT PRIMARY KEY,
            value TEXT NOT NULL,
            description TEXT,
            updated_at TEXT NOT NULL
        )
    """)

    # 新增表的索引
    cursor.execute(
        "CREATE INDEX IF NOT EXISTS idx_accounts_type ON chart_of_accounts(account_type)"
    )
    cursor.execute(
        "CREATE INDEX IF NOT EXISTS idx_accounts_parent ON chart_of_accounts(parent_id)"
    )
    cursor.execute(
        "CREATE INDEX IF NOT EXISTS idx_accounts_code ON chart_of_accounts(code)"
    )
    cursor.execute(
        "CREATE INDEX IF NOT EXISTS idx_balance_period ON account_balances(period_id)"
    )
    cursor.execute(
        "CREATE INDEX IF NOT EXISTS idx_balance_account ON account_balances(account_code)"
    )

    conn.commit()


def drop_tables(conn: sqlite3.Connection):
    """删除所有数据库表（用于测试）"""
    cursor = conn.cursor()

    allowed_tables = {
        "accounting_periods",
        "audit_logs",
        "bank_transactions",
        "outsourced_processing",
        "expenses",
        "incomes",
        "processing_orders",
        "suppliers",
        "customers",
        "bank_accounts",
        "accounting_vouchers",
        "voucher_lines",
        "chart_of_accounts",
        "account_balances",
        "departments",
        "projects",
    }

    tables = [
        "account_balances",
        "chart_of_accounts",
        "departments",
        "projects",
        "voucher_lines",
        "accounting_vouchers",
        "accounting_periods",
        "audit_logs",
        "bank_transactions",
        "outsourced_processing",
        "expenses",
        "incomes",
        "processing_orders",
        "suppliers",
        "customers",
        "bank_accounts",
    ]

    for table in tables:
        if table not in allowed_tables:
            raise ValueError(f"Invalid table name: {table}")
        cursor.execute(f"DROP TABLE IF EXISTS {table}")

    conn.commit()
