#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tests for lightweight transaction context manager on DatabaseManager"""

import uuid
from datetime import datetime
import pytest

from oxidation_finance_v20.database.db_manager import DatabaseManager


def test_transaction_commits_on_success():
    db = DatabaseManager(":memory:")
    db.connect()
    # Use a transaction to insert a customer record
    customer_id = str(uuid.uuid4())
    with db.transaction():
        db.conn.execute(
            "INSERT INTO customers (id, name, contact, phone, address, credit_limit, notes, created_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
            (customer_id, "TxTest", "", "", "", "0", "", datetime.utcnow().isoformat())
        )
    # Verify the row exists after the transaction
    row = db.conn.execute("SELECT id FROM customers WHERE id = ?", (customer_id,)).fetchone()
    assert row is not None and row[0] == customer_id
    db.close()


def test_transaction_rolls_back_on_exception():
    db = DatabaseManager(":memory:")
    db.connect()
    # Start a transaction, insert one row, then raise to trigger rollback
    id_before = str(uuid.uuid4())
    with pytest.raises(ValueError):
        with db.transaction():
            db.conn.execute(
                "INSERT INTO customers (id, name, contact, phone, address, credit_limit, notes, created_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                (id_before, "TxRollback", "", "", "", "0", "", datetime.utcnow().isoformat())
            )
            # Force an error to trigger rollback
            raise ValueError("force rollback for test")
    # Ensure no row was committed due to rollback
    row = db.conn.execute("SELECT id FROM customers WHERE id = ?", (id_before,)).fetchone()
    assert row is None
    db.close()
