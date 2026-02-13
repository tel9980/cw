#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Report exporter: dumps reports into JSON file for quick sharing."""

from __future__ import annotations

import argparse
import json
import os
from datetime import datetime
from pathlib import Path

from oxidation_finance_v20.database.db_manager import DatabaseManager
from oxidation_finance_v20.reports.report_manager import ReportManager
from oxidation_finance_v20.utils.config import get_db_path


def main():
    parser = argparse.ArgumentParser(description="Export reports to JSON file.")
    parser.add_argument(
        "--all", action="store_true", help="Export all reports (summary + details)"
    )
    parser.add_argument(
        "--out", type=str, default=None, help="Output file path (optional)"
    )
    args = parser.parse_args()

    db_path = str(get_db_path())
    if not Path(db_path).exists():
        print(f"[ERROR] 数据库不存在: {db_path}")
        return 2

    target = Path(args.out) if args.out else None
    with DatabaseManager(db_path) as db:
        rm = ReportManager(db)
        data = rm.generate_all_reports()
        # 只要是 JSON 序列化都可以处理；若有 Decimal，使用自定义序列化
        json_str = json.dumps(
            data,
            default=lambda o: float(o) if isinstance(o, (int, float)) else str(o),
            ensure_ascii=False,
            indent=2,
        )
        if target:
            target.parent.mkdir(parents=True, exist_ok=True)
            with open(target, "w", encoding="utf-8") as f:
                f.write(json_str)
            print(f"Exported reports to {target}")
        else:
            print(json_str)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
