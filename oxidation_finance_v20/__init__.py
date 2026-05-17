# 氧化加工厂财务系统 V2.1
# 包初始化文件

__version__ = "2.1"
__author__ = "氧化加工厂"
__description__ = "氧化加工厂财务管理系统"

# 导出主要模块
from .models.business_models import (
    Customer,
    Supplier,
    ProcessingOrder,
    Income,
    Expense,
    BankAccount,
    BankTransaction,
    OutsourcedProcessing,
    AccountingPeriod,
    AuditLog,
    PricingUnit,
    ProcessType,
    OrderStatus,
    ExpenseType,
    BankType,
)

__all__ = [
    "Customer",
    "Supplier",
    "ProcessingOrder",
    "Income",
    "Expense",
    "BankAccount",
    "BankTransaction",
    "OutsourcedProcessing",
    "AccountingPeriod",
    "AuditLog",
    "PricingUnit",
    "ProcessType",
    "OrderStatus",
    "ExpenseType",
    "BankType",
]
