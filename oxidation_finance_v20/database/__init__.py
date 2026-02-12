#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
数据库模块
"""

# Lazy imports to avoid circular dependency issues
__all__ = ['DatabaseManager', 'create_tables', 'drop_tables']

def __getattr__(name):
    if name == 'DatabaseManager':
        from .db_manager import DatabaseManager
        return DatabaseManager
    elif name == 'create_tables':
        from .schema import create_tables
        return create_tables
    elif name == 'drop_tables':
        from .schema import drop_tables
        return drop_tables
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
