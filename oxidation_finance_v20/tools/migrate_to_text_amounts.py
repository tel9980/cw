#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Migration: convert money-related REAL columns to TEXT to preserve precision.

This is a best-effort migration tool for SQLite to migrate existing data
from REAL/REAL-like types to TEXT for monetary fields.
"""

import sqlite3
import re
from pathlib import Path

DB_PATHS = [
    Path("oxidation_finance.db"),
    Path("oxidation_finance_v20/oxidation_finance_demo_ready.db"),
    Path("oxidation_finance_v20/oxidation_finance_demo.db"),
]

MONEY_COLUMNS = {
    # table: [money_columns]
    "customers": ["credit_limit"],
    "processing_orders": ["quantity", "unit_price", "total_amount", "outsourcing_cost", "received_amount"],
    "incomes": ["amount"],
    "expenses": ["amount"],
    "bank_accounts": ["balance"],
    "bank_transactions": ["amount"],
    "outsourced_processing": ["quantity", "unit_price", "total_cost", "paid_amount"],
    "accounting_periods": ["total_income", "total_expense", "net_profit"],
}

def migrate(db_path: Path):
    if not db_path.exists():
        print(f"DB not found: {db_path}")
        # 如果数据库不存在，尝试创建一个空的数据库，并应用当前模型的TEXT字段结构
        try:
            db_path.parent.mkdir(parents=True, exist_ok=True)
            conn = sqlite3.connect(str(db_path))
            # 使用当前 schema 创建表（TEXT 字段已在 schema.py 中定义）
            # Local import to avoid import-time cycles in some environments
            try:
                from oxidation_finance_v20.database.schema import create_tables
            except Exception:
                from database.schema import create_tables  # fallback for relative import scenarios
            create_tables(conn)
            conn.commit()
            conn.close()
            print(f"[Migrate] Created new DB with TEXT money columns: {db_path}")
            return True
        except Exception as e:
            print(f"[Migrate] Failed to create DB: {e}")
            return False

    print(f"[Migrate] Migrating: {db_path}")
    conn = sqlite3.connect(str(db_path))
    cur = conn.cursor()

    tables = [t[0] for t in cur.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()]

    for table in tables:
        if table not in MONEY_COLUMNS:
            continue
        money_cols = MONEY_COLUMNS[table]
        # Retrieve current column names
        cols = cur.execute(f"PRAGMA table_info({table})").fetchall()
        col_names = [c[1] for c in cols]
        # Build SELECT expressions: cast money columns to TEXT
        select_expr = []
        for c in col_names:
            if c in money_cols:
                select_expr.append(f"CAST({c} AS TEXT) AS {c}")
            else:
                select_expr.append(c)
        select_cols = ", ".join(select_expr)
        # Create new table with the transformed columns (no data yet)
        new_table = f"{table}_new"
        cur.execute(f"CREATE TABLE {new_table} AS SELECT {select_cols} FROM {table} LIMIT 0")
        # Copy data with conversion for money columns
        cur.execute(f"INSERT INTO {new_table} ({', '.join(col_names)}) SELECT {select_cols} FROM {table}")
        # Replace old table with new
        cur.execute(f"DROP TABLE {table}")
        cur.execute(f"ALTER TABLE {new_table} RENAME TO {table}")
        conn.commit()
        print(f"  - Migrated table: {table}")

    conn.close()
    print("[Migrate] Finished")
    return True

if __name__ == '__main__':
    # Try both preset DB paths
    for p in DB_PATHS:
        migrate(p)
