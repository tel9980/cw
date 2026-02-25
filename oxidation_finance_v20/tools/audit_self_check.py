#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Audit self-check: quick end-to-end test of审计日志覆盖。

Note: This script is meant for local validation and should not be run on
production databases without proper backups.
"""

import uuid
from datetime import date, datetime
from decimal import Decimal

from oxidation_finance_v20.database.db_manager import DatabaseManager
from oxidation_finance_v20.business.order_manager import OrderManager
from oxidation_finance_v20.business.finance_manager import FinanceManager
from oxidation_finance_v20.models import Customer, PricingUnit, ProcessType, BankType, OrderStatus


def main():
    # Use an in-memory DB for quick test
    dbm = DatabaseManager(":memory:")
    dbm.connect()

    om = OrderManager(dbm)
    fm = FinanceManager(dbm)

    # 1. Create a customer
    c = Customer(
        id=str(uuid.uuid4()),
        name="Audit Test 客户",
        credit_limit=Decimal("1000.00"),
        created_at=datetime.now(),
    )
    dbm.save_customer(c)

    # 2. Create an order
    o = om.create_order(
        customer_id=c.id,
        customer_name=c.name,
        item_description="测试产品",
        quantity=Decimal("10"),
        pricing_unit=PricingUnit.PIECE,
        unit_price=Decimal("10.00"),
        processes=[ProcessType.SANDBLASTING],
        order_date=date.today(),
        outsourced_processes=None,
        notes="审计自检与创建测试"
    )

    # 3. Create income and allocate to the order
    inc = fm.record_income(
        customer_id=c.id,
        customer_name=c.name,
        amount=Decimal("100.00"),
        bank_type=BankType.G_BANK,
        income_date=date.today(),
        has_invoice=True,
        notes="审计自检收入"
    )

    allocations = {o.id: Decimal("100.00")}
    ok, msg = fm.allocate_payment_to_orders(inc.id, allocations)
    print("Allocation result:", ok, msg)

    # 4. Audit logs count
    cur = dbm.conn.cursor()
    cur.execute("SELECT COUNT(*) FROM audit_logs")
    total_logs = cur.fetchone()[0]
    print("Audit log count:", total_logs)

    # 5. Print a summary of last audit entry
    cur.execute("SELECT * FROM audit_logs ORDER BY operation_time DESC LIMIT 1")
    last = cur.fetchone()
    print("Last audit:", dict(last) if last else None)

if __name__ == '__main__':
    main()
