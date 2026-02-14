#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Extended demo data generator for deeper coverage (count, units, allocations).
This script adds gamma client and several orders with varied pricing units,
plus a couple of income/expense events and simple allocations to demonstrate
the distribution of revenue and costs across orders."""

from __future__ import annotations

import uuid
from datetime import datetime, date
from decimal import Decimal
import json
from oxidation_finance_v20.database.db_manager import DatabaseManager
from oxidation_finance_v20.utils.config import get_db_path


def main():
    db_path = str(get_db_path())
    with DatabaseManager(db_path) as db:
        conn = db.conn
        # Ensure Gamma Labs customer exists
        gamma_id = str(uuid.uuid4())
        conn.execute(
            "INSERT OR IGNORE INTO customers (id, name, contact, phone, address, credit_limit, notes, created_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
            (
                gamma_id,
                "Gamma Labs",
                "",
                "",
                "",
                float(100000),
                "extended demo",
                datetime.now().isoformat(),
            ),
        )
        conn.commit()

        def save_order(
            order_no,
            customer_id,
            customer_name,
            item,
            quantity,
            pricing_unit,
            unit_price,
            status="待加工",
        ):
            oid = str(uuid.uuid4())
            total_amount = Decimal(str(quantity)) * Decimal(str(unit_price))
            conn.execute(
                "INSERT OR REPLACE INTO processing_orders (id, order_no, customer_id, customer_name, item_description, quantity, pricing_unit, unit_price, total_amount, processes, outsourced_processes, status, order_date, created_at, updated_at, received_amount) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                (
                    oid,
                    order_no,
                    customer_id,
                    customer_name,
                    item,
                    float(quantity),
                    pricing_unit,
                    float(unit_price),
                    float(total_amount),
                    json.dumps(["OXIDATION"]),
                    json.dumps([]),
                    status,
                    date.today().isoformat(),
                    datetime.now().isoformat(),
                    datetime.now().isoformat(),
                    0.0,
                ),
            )
            return oid

        # Create several orders with diverse pricing units
        o4 = save_order("OX-EXT-004", gamma_id, "Gamma Labs", "铝带", 50, "STRIP", 0.4)
        o5 = save_order("OX-EXT-005", gamma_id, "Gamma Labs", "铝箔", 30, "PIECE", 6.0)
        o6 = save_order(
            "OX-EXT-006", gamma_id, "Gamma Labs", "型材长", 120, "METER", 0.05
        )

        # New income and expenses to be allocated
        inc3_id = str(uuid.uuid4())
        conn.execute(
            "INSERT OR REPLACE INTO incomes (id, customer_name, amount, bank_type, income_date, notes, created_at) VALUES (?, ?, ?, ?, ?, ?, ?)",
            (
                inc3_id,
                "Gamma Labs",
                420.0,
                "G_BANK",
                date.today().isoformat(),
                "extended demo income 3",
                datetime.now().isoformat(),
            ),
        )
        exp3_id = str(uuid.uuid4())
        conn.execute(
            "INSERT OR REPLACE INTO expenses (id, expense_type, supplier_name, amount, bank_type, expense_date, description, created_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
            (
                exp3_id,
                "UTILITIES",
                "Utility Co",
                60.0,
                "BANK",
                date.today().isoformat(),
                "extended demo utilities 3",
                datetime.now().isoformat(),
            ),
        )
        conn.commit()

        # Use a fresh ReportManager to apply allocations
        with DatabaseManager(db_path) as db_alloc:
            report = __import__(
                "oxidation_finance_v20.reports.report_manager",
                fromlist=["ReportManager"],
            ).ReportManager(db_alloc)
            report.allocate_income(inc3_id, o4, 200.0)
            report.allocate_income(inc3_id, o5, 120.0)
            report.allocate_expense(exp3_id, o6, 60.0)

    print("Extended demo data (gamma scope) created.")


if __name__ == "__main__":
    main()
