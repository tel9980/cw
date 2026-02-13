#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Utility for centralized CWZS configuration
 - Centralizes database path resolution
 - Allows overriding via CWZS_DB_PATH env var
"""

from __future__ import annotations

import os
from pathlib import Path


def get_db_path() -> str:
    """Return the canonical database path for CWZS oxidation finance v2.0.
    Priority:
      1) CWZS_DB_PATH env var
      2) oxidation_finance_v20/oxidation_finance.db in repo
    """
    env_path = os.environ.get("CWZS_DB_PATH")
    if env_path:
        return env_path
    root = Path(__file__).resolve().parents[1]  # .../oxidation_finance_v20
    db_path = root / "oxidation_finance.db"
    return str(db_path)
