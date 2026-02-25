#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Money field migration: convert money columns to TEXT storage.

This script migrates money-related columns in the database to TEXT to avoid
floating-point precision issues. It performs a safe, table-by-table migration
by creating a new table with TEXT money columns, copying data with casts, and
replacing the old table.
"""

import sqlite3
from pathlib import Path
from typing import Iterable

from oxidation_finance_v20.tools.migrate_to_text_amounts import MONEY_COLUMNS


def migrate_one_db(db_path: Path) -> None:
    if not db_path.exists():
        print(f"DB not found: {db_path}")
        return
    print(f"[Migrate] Migrating: {db_path}")
    conn = sqlite3.connect(str(db_path))
    cur = conn.cursor()

    # Tables to migrate based on MONEY_COLUMNS
    tables = [t for t in MONEY_COLUMNS.keys() if True]

    for table in tables:
        money_cols = MONEY_COLUMNS[table]
        # 1) read current columns
        cols_info = cur.execute(f"PRAGMA table_info({table})").fetchall()
        col_names = [c[1] for c in cols_info]
        # 2) create new table with TEXT money cols
        row = cur.execute("SELECT sql FROM sqlite_master WHERE type='table' AND name=?", (table,)).fetchone()
        if not row:
            continue
        create_sql = row[0]
        new_create = create_sql
        for col in money_cols:
            new_create = new_create.replace(f"{col} REAL", f"{col} TEXT")
            new_create = new_create.replace(f"{col} NUMERIC", f"{col} TEXT")
        new_table = f"{table}_money_text"
        cur.execute(new_create.replace(table, new_table, 1))
        # 3) copy data with casts for money cols
        select_expr = []
        for c in col_names:
            if c in money_cols:
                select_expr.append(f"CAST({c} AS TEXT) AS {c}")
            else:
                select_expr.append(c)
        select_cols = ", ".join(select_expr)
        insert_cols = ", ".join(col_names)
        cur.execute(f"INSERT INTO {new_table} ({insert_cols}) SELECT {select_cols} FROM {table}")
        # 4) swap tables
        cur.execute(f"DROP TABLE {table}")
        cur.execute(f"ALTER TABLE {new_table} RENAME TO {table}")
        conn.commit()
        print(f"  - Migrated table: {table}")

    conn.close()
    print(f"[Migrate] Finished: {db_path}")


def main():
    # Expose MONEY_COLUMNS via a simple alias for import convenience
    dbs = [Path("oxidation_finance.db"), Path("oxidation_finance_v20/oxidation_finance_demo_ready.db"), Path("oxidation_finance_v20/oxidation_finance_demo.db")]
    for db in dbs:
        migrate_one_db(db)


if __name__ == '__main__':
    main()
