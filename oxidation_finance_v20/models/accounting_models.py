#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
氧化加工厂财务系统 V2.3 - 会计模型
符合小企业会计准则的会计科目、凭证、报表模型
"""

from dataclasses import dataclass, field
from datetime import date, datetime
from decimal import Decimal
from enum import Enum
from typing import List, Optional, Dict
import uuid


class AccountType(Enum):
    """账户类型"""
    ASSET = "资产类"
    LIABILITY = "负债类"
    EQUITY = "所有者权益类"
    COST = "成本类"
    REVENUE = "损益类（收入）"
    EXPENSE = "损益类（费用）"


class AccountCode(Enum):
    """小企业会计准则会计科目"""
    # 资产类（1开头）
    CASH_IN_HAND = ("1001", "库存现金", AccountType.ASSET)
    BANK_DEPOSIT = ("1002", "银行存款", AccountType.ASSET)
    OTHER_CURRENT_ASSETS = ("1111", "其他流动资产", AccountType.ASSET)
    ACCOUNTS_RECEIVABLE = ("1122", "应收账款", AccountType.ASSET)
    PREPAYMENTS = ("1123", "预付款项", AccountType.ASSET)
    RAW_MATERIALS = ("1403", "原材料", AccountType.ASSET)
    INVENTORY_GOODS = ("1405", "库存商品", AccountType.ASSET)
    FIXED_ASSETS = ("1601", "固定资产", AccountType.ASSET)
    ACCUMULATED_DEPRECIATION = ("1602", "累计折旧", AccountType.ASSET)
    
    # 负债类（2开头）
    SHORT_TERM_LOAN = ("2001", "短期借款", AccountType.LIABILITY)
    ACCOUNTS_PAYABLE = ("2202", "应付账款", AccountType.LIABILITY)
    TAXES_PAYABLE = ("2221", "应交税费", AccountType.LIABILITY)
    WAGES_PAYABLE = ("2211", "应付职工薪酬", AccountType.LIABILITY)
    
    # 所有者权益类（3开头）
    PAID_IN_CAPITAL = ("3001", "实收资本", AccountType.EQUITY)
    CAPITAL_RESERVE = ("3002", "资本公积", AccountType.EQUITY)
    SURPLUS_RESERVE = ("3101", "盈余公积", AccountType.EQUITY)
    CURRENT_PROFIT = ("3103", "本年利润", AccountType.EQUITY)
    UNDISTRIBUTED_PROFIT = ("3104", "利润分配", AccountType.EQUITY)
    
    # 成本类（5开头）
    PRODUCTION_COSTS = ("5001", "生产成本", AccountType.COST)
    MANUFACTURING_EXPENSES = ("5101", "制造费用", AccountType.COST)
    
    # 损益类-收入（6开头）
    MAIN_BUSINESS_INCOME = ("6001", "主营业务收入", AccountType.REVENUE)
    OTHER_BUSINESS_INCOME = ("6051", "其他业务收入", AccountType.REVENUE)
    NON_OPERATING_INCOME = ("6301", "营业外收入", AccountType.REVENUE)
    
    # 损益类-费用（6开头）
    MAIN_BUSINESS_COST = ("6401", "主营业务成本", AccountType.EXPENSE)
    OTHER_BUSINESS_COST = ("6402", "其他业务成本", AccountType.EXPENSE)
    TAXES_AND_SURCHARGES = ("6403", "税金及附加", AccountType.EXPENSE)
    SALES_EXPENSES = ("6601", "销售费用", AccountType.EXPENSE)
    ADMINISTRATIVE_EXPENSES = ("6602", "管理费用", AccountType.EXPENSE)
    FINANCIAL_EXPENSES = ("6603", "财务费用", AccountType.EXPENSE)
    NON_OPERATING_EXPENSES = ("6711", "营业外支出", AccountType.EXPENSE)
    INCOME_TAX_EXPENSES = ("6801", "所得税费用", AccountType.EXPENSE)
    
    def __init__(self, code: str, name: str, account_type: AccountType):
        self.code = code
        self.display_name = name
        self.account_type = account_type
    
    @property
    def full_name(self) -> str:
        """获取科目全名"""
        return f"{self.code}-{self.display_name}"


@dataclass
class Account:
    """会计科目"""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    account_code: AccountCode = AccountCode.CASH_IN_HAND
    account_name: str = ""
    account_type: AccountType = AccountType.ASSET
    parent_id: Optional[str] = None  # 上级科目ID
    level: int = 1  # 科目级别
    balance: Decimal = Decimal("0")  # 余额
    is_active: bool = True
    created_at: datetime = field(default_factory=datetime.now)


@dataclass
class VoucherLine:
    """凭证明细"""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    voucher_id: str = ""
    account_code: str = ""  # 科目编码
    account_name: str = ""  # 科目名称
    debit: Decimal = Decimal("0")  # 借方金额
    credit: Decimal = Decimal("0")  # 贷方金额
    summary: str = ""  # 摘要
    related_entity_type: Optional[str] = None  # 关联实体类型（订单、客户等）
    related_entity_id: Optional[str] = None  # 关联实体ID


class VoucherStatus(Enum):
    """凭证状态"""
    DRAFT = "草稿"
    REVIEWED = "已审核"
    POSTED = "已记账"


@dataclass
class AccountingVoucher:
    """会计凭证（记账凭证）"""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    voucher_no: str = ""  # 凭证编号
    voucher_date: date = field(default_factory=date.today)  # 凭证日期
    accounting_period: str = ""  # 会计期间（如：2024-01）
    lines: List[VoucherLine] = field(default_factory=list)
    summary: str = ""  # 摘要
    total_debit: Decimal = Decimal("0")  # 借方合计
    total_credit: Decimal = Decimal("0")  # 贷方合计
    created_by: str = ""  # 制单人
    reviewed_by: Optional[str] = None  # 审核人
    posted_by: Optional[str] = None  # 记账人
    reviewed_at: Optional[datetime] = None  # 审核时间
    posted_at: Optional[datetime] = None  # 记账时间
    status: VoucherStatus = VoucherStatus.DRAFT
    source_type: Optional[str] = None  # 来源类型（订单、收入、支出等）
    source_id: Optional[str] = None  # 来源ID
    notes: str = ""
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    
    def validate_balance(self) -> bool:
        """验证借贷平衡"""
        total_debit = sum(line.debit for line in self.lines)
        total_credit = sum(line.credit for line in self.lines)
        return total_debit == total_credit
    
    def calculate_totals(self):
        """计算借贷方合计"""
        self.total_debit = sum(line.debit for line in self.lines)
        self.total_credit = sum(line.credit for line in self.lines)


@dataclass
class ProductionCostItem:
    """生产成本项目（针对氧化加工行业）"""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    order_id: str = ""
    order_no: str = ""
    
    # 成本明细
    material_cost: Decimal = Decimal("0")  # 原材料消耗（三酸、片碱、色粉等）
    labor_cost: Decimal = Decimal("0")  # 人工成本
    manufacturing_expense: Decimal = Decimal("0")  # 制造费用分摊
    outsourcing_cost: Decimal = Decimal("0")  # 委外加工成本
    
    # 成本日期
    cost_date: date = field(default_factory=date.today)
    
    # 状态
    is_allocated: bool = False  # 是否已分配到订单
    created_at: datetime = field(default_factory=datetime.now)
    
    @property
    def total_cost(self) -> Decimal:
        """计算总成本"""
        return (
            self.material_cost +
            self.labor_cost +
            self.manufacturing_expense +
            self.outsourcing_cost
        )


@dataclass
class BalanceSheetItem:
    """资产负债表项目"""
    item_name: str
    line_order: int
    current_amount: Decimal
    previous_amount: Optional[Decimal] = None


@dataclass
class IncomeStatementItem:
    """利润表项目"""
    item_name: str
    line_order: int
    current_amount: Decimal
    previous_amount: Optional[Decimal] = None


@dataclass
class BalanceSheet:
    """资产负债表"""
    period: str
    assets: List[BalanceSheetItem]
    liabilities: List[BalanceSheetItem]
    equity: List[BalanceSheetItem]
    total_assets: Decimal
    total_liabilities: Decimal
    total_equity: Decimal
    created_at: datetime = field(default_factory=datetime.now)


@dataclass
class IncomeStatement:
    """利润表"""
    period: str
    items: List[IncomeStatementItem]
    total_revenue: Decimal
    total_cost: Decimal
    gross_profit: Decimal
    operating_expenses: Decimal
    operating_profit: Decimal
    net_profit: Decimal
    created_at: datetime = field(default_factory=datetime.now)
