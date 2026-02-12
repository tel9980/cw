#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
氧化加工厂财务系统 V2.0 - 业务模型
专为小白会计设计的简单易用模型
"""

from dataclasses import dataclass, field
from datetime import date, datetime
from decimal import Decimal
from enum import Enum
from typing import List, Optional, Dict
import uuid


class PricingUnit(Enum):
    """计价单位"""
    PIECE = "件"      # 按件计价
    STRIP = "条"      # 按条计价
    UNIT = "只"       # 按只计价
    ITEM = "个"       # 按个计价
    METER = "米"      # 按米长计价
    KILOGRAM = "公斤"  # 按米重(公斤)计价
    SQUARE_METER = "平方米"  # 按平方米计价


class ProcessType(Enum):
    """加工工序类型"""
    SANDBLASTING = "喷砂"
    WIRE_DRAWING = "拉丝"
    POLISHING = "抛光"
    OXIDATION = "氧化"  # 最后工序


class OrderStatus(Enum):
    """订单状态"""
    PENDING = "待加工"
    IN_PROGRESS = "加工中"
    OUTSOURCED = "委外中"
    COMPLETED = "已完工"
    DELIVERED = "已交付"
    PAID = "已收款"


class ExpenseType(Enum):
    """支出类型"""
    RENT = "房租"
    UTILITIES = "水电费"
    ACID_THREE = "三酸"  # 硫酸、硝酸、盐酸
    CAUSTIC_SODA = "片碱"
    SODIUM_SULFITE = "亚钠"
    COLOR_POWDER = "色粉"
    DEGREASER = "除油剂"
    FIXTURES = "挂具"
    OUTSOURCING = "外发加工费"
    DAILY_EXPENSE = "日常费用"
    SALARY = "工资"
    OTHER = "其他"


class BankType(Enum):
    """银行类型"""
    G_BANK = "G银行"  # 有票据的正式交易
    N_BANK = "N银行"  # 现金等价物(与微信结合)


@dataclass
class Customer:
    """客户信息"""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    name: str = ""
    contact: str = ""
    phone: str = ""
    address: str = ""
    credit_limit: Decimal = Decimal("0")  # 信用额度
    notes: str = ""
    created_at: datetime = field(default_factory=datetime.now)


@dataclass
class Supplier:
    """供应商信息"""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    name: str = ""
    contact: str = ""
    phone: str = ""
    address: str = ""
    business_type: str = ""  # 业务类型：原料供应商、委外加工商等
    notes: str = ""
    created_at: datetime = field(default_factory=datetime.now)


@dataclass
class ProcessingOrder:
    """加工订单"""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    order_no: str = ""  # 订单编号
    customer_id: str = ""
    customer_name: str = ""
    
    # 物品信息
    item_description: str = ""  # 物品描述
    quantity: Decimal = Decimal("0")  # 数量
    pricing_unit: PricingUnit = PricingUnit.PIECE  # 计价单位
    unit_price: Decimal = Decimal("0")  # 单价
    
    # 工序信息
    processes: List[ProcessType] = field(default_factory=list)  # 需要的工序
    outsourced_processes: List[str] = field(default_factory=list)  # 委外工序
    
    # 费用信息
    total_amount: Decimal = Decimal("0")  # 总加工费
    outsourcing_cost: Decimal = Decimal("0")  # 委外成本
    
    # 状态信息
    status: OrderStatus = OrderStatus.PENDING
    order_date: date = field(default_factory=date.today)
    completion_date: Optional[date] = None
    delivery_date: Optional[date] = None
    
    # 收款信息
    received_amount: Decimal = Decimal("0")  # 已收金额
    
    notes: str = ""
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)


@dataclass
class Income:
    """收入记录"""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    customer_id: str = ""
    customer_name: str = ""
    
    amount: Decimal = Decimal("0")
    bank_type: BankType = BankType.G_BANK
    has_invoice: bool = False  # 是否有票据
    
    # 关联订单（可能对应多个订单）
    related_orders: List[str] = field(default_factory=list)
    allocation: Dict[str, Decimal] = field(default_factory=dict)  # 订单ID -> 分配金额
    
    income_date: date = field(default_factory=date.today)
    notes: str = ""
    created_at: datetime = field(default_factory=datetime.now)


@dataclass
class Expense:
    """支出记录"""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    expense_type: ExpenseType = ExpenseType.OTHER
    supplier_id: Optional[str] = None
    supplier_name: str = ""
    
    amount: Decimal = Decimal("0")
    bank_type: BankType = BankType.G_BANK
    has_invoice: bool = False
    
    # 关联订单（委外加工费用）
    related_order_id: Optional[str] = None
    
    expense_date: date = field(default_factory=date.today)
    description: str = ""
    notes: str = ""
    created_at: datetime = field(default_factory=datetime.now)


@dataclass
class BankAccount:
    """银行账户"""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))

    bank_type: BankType = BankType.G_BANK
    account_name: str = ""
    account_number: str = ""
    balance: Decimal = Decimal("0")
    notes: str = ""


@dataclass
class BankTransaction:
    """银行交易记录"""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    bank_type: BankType = BankType.G_BANK
    transaction_date: date = field(default_factory=date.today)
    
    amount: Decimal = Decimal("0")  # 正数为收入，负数为支出
    counterparty: str = ""  # 交易对手
    description: str = ""
    
    # 匹配信息
    matched: bool = False
    matched_income_id: Optional[str] = None
    matched_expense_id: Optional[str] = None
    
    notes: str = ""
    created_at: datetime = field(default_factory=datetime.now)


@dataclass
class OutsourcedProcessing:
    """委外加工记录"""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    order_id: str = ""  # 关联的订单ID
    supplier_id: str = ""  # 供应商ID
    supplier_name: str = ""  # 供应商名称
    
    # 工序信息
    process_type: ProcessType = ProcessType.SANDBLASTING  # 委外工序类型
    process_description: str = ""  # 工序描述
    
    # 数量和费用
    quantity: Decimal = Decimal("0")  # 数量
    unit_price: Decimal = Decimal("0")  # 单价
    total_cost: Decimal = Decimal("0")  # 总成本
    
    # 付款信息
    paid_amount: Decimal = Decimal("0")  # 已付金额
    
    # 日期信息
    process_date: date = field(default_factory=date.today)  # 加工日期
    
    notes: str = ""
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    
    def get_unpaid_amount(self) -> Decimal:
        """获取未付金额"""
        return self.total_cost - self.paid_amount
    
    def is_fully_paid(self) -> bool:
        """是否已全额付款"""
        return self.paid_amount >= self.total_cost
    
    def get_payment_status(self) -> str:
        """获取付款状态"""
        if self.paid_amount == Decimal("0"):
            return "未付款"
        elif self.is_fully_paid():
            return "已付清"
        else:
            return "部分付款"


# 用于小白会计的简化说明
PRICING_UNIT_EXAMPLES = {
    PricingUnit.PIECE: "例如：螺丝、螺母等小零件",
    PricingUnit.STRIP: "例如：铝条、钢条等长条形物品",
    PricingUnit.UNIT: "例如：把手、拉手等单个物品",
    PricingUnit.ITEM: "例如：配件、组件等",
    PricingUnit.METER: "例如：铝型材、管材等按长度计价",
    PricingUnit.KILOGRAM: "例如：板材、型材等按重量计价",
    PricingUnit.SQUARE_METER: "例如：铝板、钢板等按面积计价"
}

EXPENSE_TYPE_EXAMPLES = {
    ExpenseType.RENT: "每月固定的厂房租金",
    ExpenseType.UTILITIES: "水费、电费等公用事业费用",
    ExpenseType.ACID_THREE: "硫酸、硝酸、盐酸等氧化用酸",
    ExpenseType.CAUSTIC_SODA: "氢氧化钠，用于除油和中和",
    ExpenseType.SODIUM_SULFITE: "亚硫酸钠，用于氧化处理",
    ExpenseType.COLOR_POWDER: "氧化着色用的色粉",
    ExpenseType.DEGREASER: "除油剂，前处理用",
    ExpenseType.FIXTURES: "挂具、夹具等工装",
    ExpenseType.OUTSOURCING: "委外加工的费用",
    ExpenseType.DAILY_EXPENSE: "办公用品、维修等日常开支",
    ExpenseType.SALARY: "员工工资",
    ExpenseType.OTHER: "其他未分类的支出"
}

PROCESS_TYPE_EXAMPLES = {
    ProcessType.SANDBLASTING: "用砂粒喷射表面，去除氧化层和杂质",
    ProcessType.WIRE_DRAWING: "用砂带或砂轮拉出丝纹效果",
    ProcessType.POLISHING: "用抛光轮打磨至光亮",
    ProcessType.OXIDATION: "最后工序，在酸液中形成氧化膜"
}


class OperationType(Enum):
    """操作类型"""
    CREATE = "创建"
    UPDATE = "更新"
    DELETE = "删除"
    ALLOCATE = "分配"
    MATCH = "匹配"
    ADJUST = "调整"


class EntityType(Enum):
    """实体类型"""
    ORDER = "订单"
    INCOME = "收入"
    EXPENSE = "支出"
    CUSTOMER = "客户"
    SUPPLIER = "供应商"
    BANK_ACCOUNT = "银行账户"
    BANK_TRANSACTION = "银行交易"
    OUTSOURCED_PROCESSING = "委外加工"
    ACCOUNTING_PERIOD = "会计期间"


@dataclass
class AuditLog:
    """审计日志"""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    operation_type: OperationType = OperationType.CREATE
    entity_type: EntityType = EntityType.ORDER
    entity_id: str = ""  # 被操作实体的ID
    entity_name: str = ""  # 被操作实体的名称或描述
    
    operator: str = "系统"  # 操作人
    operation_time: datetime = field(default_factory=datetime.now)
    
    # 操作详情
    operation_description: str = ""  # 操作描述
    old_value: str = ""  # 旧值（JSON格式）
    new_value: str = ""  # 新值（JSON格式）
    
    # 额外信息
    ip_address: str = ""  # IP地址
    notes: str = ""


@dataclass
class AccountingPeriod:
    """会计期间"""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    period_name: str = ""  # 期间名称，如"2024年1月"
    start_date: date = field(default_factory=date.today)
    end_date: date = field(default_factory=date.today)
    
    status: str = "开放"  # 开放、关闭
    is_closed: bool = False  # 是否已关闭
    
    # 期间汇总数据
    total_income: Decimal = Decimal("0")
    total_expense: Decimal = Decimal("0")
    net_profit: Decimal = Decimal("0")
    
    # 关闭信息
    closed_by: str = ""  # 关闭人
    closed_at: Optional[datetime] = None  # 关闭时间
    
    notes: str = ""
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)