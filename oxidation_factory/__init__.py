# -*- coding: utf-8 -*-
"""
氧化加工厂财务助手模块
专为氧化加工行业定制的财务管理功能
"""

__version__ = "1.0.0"
__author__ = "Kiro AI"
__description__ = "氧化加工厂财务助手系统"

# 导入核心模块
from .config import OxidationConfig, get_config, reload_config
from .order_manager import Order, OrderManager
from .table_init import TableInitializer, init_oxidation_tables
from .local_storage import LocalStorage, get_storage

__all__ = [
    'OxidationConfig',
    'get_config',
    'reload_config',
    'Order',
    'OrderManager',
    'TableInitializer',
    'init_oxidation_tables',
    'LocalStorage',
    'get_storage',
]
