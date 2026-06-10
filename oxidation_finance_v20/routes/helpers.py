#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""共享辅助函数和数据库连接"""

import sqlite3
from pathlib import Path
from collections import defaultdict

# 数据库路径
DB_PATH = Path(__file__).resolve().parent.parent / "oxidation_finance_demo_ready.db"
if not DB_PATH.exists():
    DB_PATH = Path(__file__).resolve().parent.parent / "oxidation_finance_demo.db"

# 性能统计
request_stats = defaultdict(list)


def get_db():
    """获取数据库连接"""
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    return conn


def to_float(value):
    """辅助函数：将字符串转换为浮点数"""
    try:
        return float(value) if value else 0.0
    except (ValueError, TypeError):
        return 0.0


def convert_row_to_dict(row):
    """将 SQLite Row 转换为字典，并转换金额字段"""
    if not row:
        return None
    data = dict(row)
    amount_fields = ['total_amount', 'received_amount', 'amount', 'outsourcing_cost', 'unit_price', 'quantity']
    for field in amount_fields:
        if field in data:
            data[field] = to_float(data[field])
    return data


def convert_rows_to_dicts(rows):
    """将多行转换为字典列表"""
    return [convert_row_to_dict(row) for row in rows]


def auto_gen_voucher(conn, source_type, source_id, lines_data, period, summary, created_by="系统自动"):
    """自动生成会计凭证

    Args:
        conn: 数据库连接
        source_type: 来源类型 (INCOME/EXPENSE/ORDER)
        source_id: 来源ID
        lines_data: 分录列表 [{'code': str, 'debit': float, 'credit': float}]
        period: 会计期间 'YYYY-MM'
        summary: 凭证摘要
        created_by: 制单人

    Returns:
        (voucher_no, voucher_id) 或 (None, None)
    """
    import uuid
    from datetime import datetime

    cursor = conn.cursor()
    cursor.execute(
        "SELECT COUNT(*) FROM accounting_vouchers WHERE accounting_period=?",
        (period,)
    )
    seq = cursor.fetchone()[0] + 1
    voucher_no = f"{period}-{seq:03d}"
    voucher_id = str(uuid.uuid4())

    total_debit = sum(l['debit'] for l in lines_data)
    total_credit = sum(l['credit'] for l in lines_data)

    if abs(total_debit - total_credit) > 0.01:
        return None, None

    now = datetime.now().isoformat()
    cursor.execute(
        """INSERT INTO accounting_vouchers
           (id, voucher_no, voucher_date, accounting_period, summary,
            total_debit, total_credit, created_by, status, source_type, source_id,
            created_at, updated_at)
           VALUES (?, ?, date('now'), ?, ?, ?, ?, ?, '草稿', ?, ?, ?, ?)""",
        (voucher_id, voucher_no, period, summary,
         f"{total_debit:.2f}", f"{total_credit:.2f}", created_by,
         source_type, source_id, now, now)
    )

    for line in lines_data:
        acc = cursor.execute(
            "SELECT name FROM chart_of_accounts WHERE code=?",
            (line['code'],)
        ).fetchone()
        acc_name = acc['name'] if acc else line['code']

        cursor.execute(
            """INSERT INTO voucher_lines
               (id, voucher_id, account_code, account_name, debit, credit, summary)
               VALUES (?, ?, ?, ?, ?, ?, ?)""",
            (str(uuid.uuid4()), voucher_id, line['code'], acc_name,
             f"{line['debit']:.2f}", f"{line['credit']:.2f}", summary)
        )

    conn.commit()
    return voucher_no, voucher_id