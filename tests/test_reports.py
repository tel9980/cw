import os
import json
import tempfile
import sqlite3
from datetime import datetime

import pytest

from oxidation_finance_v20.database.db_manager import DatabaseManager
from oxidation_finance_v20.reports.report_manager import ReportManager


def setup_test_db(path: str):
    # Create a minimal schema compatible with ReportManager usage
    conn = sqlite3.connect(path)
    conn.execute(
        "CREATE TABLE customers (id TEXT PRIMARY KEY, name TEXT, created_at TEXT)"
    )
    conn.execute(
        "CREATE TABLE processing_orders (id TEXT PRIMARY KEY, order_no TEXT, customer_id TEXT, customer_name TEXT, item_description TEXT, quantity REAL, pricing_unit TEXT, unit_price REAL, total_amount REAL, processes TEXT, status TEXT, order_date TEXT, created_at TEXT, updated_at TEXT, received_amount REAL DEFAULT 0)"
    )
    conn.execute(
        "CREATE TABLE incomes (id TEXT PRIMARY KEY, customer_name TEXT, amount REAL, bank_type TEXT, income_date TEXT, notes TEXT, created_at TEXT)"
    )
    conn.execute(
        "CREATE TABLE expenses (id TEXT PRIMARY KEY, expense_type TEXT, supplier_name TEXT, amount REAL, bank_type TEXT, expense_date TEXT, description TEXT, created_at TEXT)"
    )
    conn.commit()
    # Ensure allocation tables exist for later tests
    conn.execute(
        """CREATE TABLE IF NOT EXISTS income_allocations (
            income_id TEXT,
            order_id TEXT,
            amount REAL,
            PRIMARY KEY (income_id, order_id)
        )"""
    )
    conn.execute(
        """CREATE TABLE IF NOT EXISTS expense_allocations (
            expense_id TEXT,
            order_id TEXT,
            amount REAL,
            PRIMARY KEY (expense_id, order_id)
        )"""
    )
    conn.commit()
    return conn


@pytest.fixture
def temp_db_path():
    fd, path = tempfile.mkstemp(suffix=".db")
    os.close(fd)
    yield path
    try:
        os.remove(path)
    except FileNotFoundError:
        pass


def test_report_manager_basic(temp_db_path):
    # Setup a small dataset
    conn = setup_test_db(temp_db_path)
    now = datetime.now().isoformat()
    # Insert sample customer and order
    conn.execute(
        "INSERT INTO customers (id, name, created_at) VALUES (?, ?, ?)",
        ("c1", "Alpha Co", now),
    )
    conn.execute(
        "INSERT INTO processing_orders (id, order_no, customer_id, customer_name, item_description, quantity, pricing_unit, unit_price, total_amount, processes, status, order_date, created_at, updated_at, received_amount) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
        (
            "o1",
            "OX-TEST-001",
            "c1",
            "Alpha Co",
            "Aluminum rods",
            10,
            "METER",
            5.0,
            50.0,
            "氧化",
            "已完工",
            "2025-01-15",
            now,
            now,
            50.0,
        ),
    )
    # Insert income and expense
    conn.execute(
        "INSERT INTO incomes (id, customer_name, amount, bank_type, income_date, notes, created_at) VALUES (?, ?, ?, ?, ?, ?, ?)",
        ("inc1", "Alpha Co", 60.0, "G_BANK", "2025-01-15", "note", now),
    )
    conn.execute(
        "INSERT INTO expenses (id, expense_type, supplier_name, amount, bank_type, expense_date, description, created_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
        ("exp1", "RENT", "Landlord", 20.0, "BANK", "2025-01-10", "monthly rent", now),
    )
    conn.commit()
    conn.close()

    # Bind DB through manager
    with DatabaseManager(temp_db_path) as db:
        rm = ReportManager(db)
        summary = rm.get_summary()
        assert "total_income" in summary and "total_expense" in summary
        monthly = rm.get_monthly_stats()
        assert isinstance(monthly, list)
        top = rm.get_top_customers()
        assert isinstance(top, list)
        by_type = rm.get_expense_by_type()
        assert isinstance(by_type, list)
        all_reports = rm.generate_all_reports()
        assert "summary" in all_reports and "monthly" in all_reports

        # Allocation: assign income/expense to the order and verify profit calculation
        rm.allocate_income("inc1", "o1", 50.0)
        rm.allocate_expense("exp1", "o1", 10.0)
        profit_info = rm.get_order_profit("o1")
        assert profit_info["order_id"] == "o1"
        assert profit_info["income_allocated"] == 50.0
        assert profit_info["expense_allocated"] == 10.0
        assert profit_info["profit"] == 40.0
