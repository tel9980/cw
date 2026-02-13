#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Advanced demo data generator for oxidation finance v2.0.
Creates multiple customers, orders with varied pricing units, incomes
and expenses, and simple income/expense allocations to orders.
"""

from __future__ import annotations

import uuid
from datetime import datetime, date
from pathlib import Path
from decimal import Decimal
import json

from oxidation_finance_v20.database.db_manager import DatabaseManager
from oxidation_finance_v20.utils.config import get_db_path


def main():
    # Resolve DB path (prefer existing demo DBs or fall back to a new one)
    possible = [
        Path("oxidation_finance_demo_ready.db"),
        Path("oxidation_finance_demo.db"),
        Path("oxidation_finance.db"),
    ]
    db_path = None
    for p in possible:
        if p.exists():
            db_path = str(p)
            break
    if db_path is None:
        db_path = str(get_db_path())

    with DatabaseManager(db_path) as db:
        conn = db.conn
        # Create two customers
        customers = [
            {"name": "Alpha Co", "contact": "李经理", "phone": "13800000001"},
            {"name": "Beta Tech", "contact": "王小姐", "phone": "13900000002"},
        ]
        customer_ids = []
        for c in customers:
            cid = str(uuid.uuid4())
            conn.execute(
                "INSERT OR REPLACE INTO customers (id, name, contact, phone, address, credit_limit, notes, created_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                (
                    cid,
                    c["name"],
                    c["contact"],
                    c["phone"],
                    "",
                    float(100000),
                    "demo",
                    datetime.now().isoformat(),
                ),
            )
            customer_ids.append(cid)

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

        # Create 3 orders with diverse pricing units
        o1 = save_order(
            "OX-ADV-001",
            customer_ids[0],
            customers[0]["name"],
            "铝型材6063",
            20,
            "METER",
            8.5,
        )
        o2 = save_order(
            "OX-ADV-002",
            customer_ids[1],
            customers[1]["name"],
            "铝板AIS",
            120,
            "PIECE",
            1.25,
        )
        o3 = save_order(
            "OX-ADV-003",
            customer_ids[0],
            customers[0]["name"],
            "棒材P",
            50,
            "METER",
            2.0,
        )

        # Records of incomes and expenses to be allocated
        inc_id = str(uuid.uuid4())
        conn.execute(
            "INSERT OR REPLACE INTO incomes (id, customer_name, amount, bank_type, income_date, notes, created_at) VALUES (?, ?, ?, ?, ?, ?, ?)",
            (
                inc_id,
                customers[0]["name"],
                200.0,
                "G_BANK",
                date.today().isoformat(),
                "demo income",
                datetime.now().isoformat(),
            ),
        )
        exp1_id = str(uuid.uuid4())
        conn.execute(
            "INSERT OR REPLACE INTO expenses (id, expense_type, supplier_name, amount, bank_type, expense_date, description, created_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
            (
                exp1_id,
                "房租",
                "Landlord",
                80.0,
                "BANK",
                date.today().isoformat(),
                "demo rent",
                datetime.now().isoformat(),
            ),
        )
        conn.commit()

        # Allocate income/expense to orders using a fresh RM instance
        with DatabaseManager(db_path) as db2:
            report = __import__(
                "oxidation_finance_v20.reports.report_manager",
                fromlist=["ReportManager"],
            ).ReportManager(db2)
            report.allocate_income(inc_id, o1, 100.0)
            report.allocate_income(inc_id, o3, 60.0)
            report.allocate_expense(exp1_id, o1, 30.0)

        print("Advanced demo data generated with allocations:")
        print(f"Orders: {o1}, {o2}, {o3}")


if __name__ == "__main__":
    main()
