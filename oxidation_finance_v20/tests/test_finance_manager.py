#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
财务管理器单元测试
"""

import pytest
from decimal import Decimal
from datetime import date, timedelta
from ..models.business_models import (
    Customer, ProcessingOrder, Income, Expense,
    PricingUnit, ProcessType, OrderStatus, BankType, ExpenseType
)
from ..business.finance_manager import FinanceManager
from ..database.db_manager import DatabaseManager


@pytest.fixture
def db_manager(tmp_path):
    """创建临时数据库管理器"""
    db_path = tmp_path / "test_finance.db"
    db = DatabaseManager(str(db_path))
    db.connect()
    yield db
    db.close()


@pytest.fixture
def finance_manager(db_manager):
    """创建财务管理器"""
    return FinanceManager(db_manager)


@pytest.fixture
def sample_customer(db_manager):
    """创建示例客户"""
    customer = Customer(
        name="测试客户",
        contact="张三",
        phone="13800138000",
        address="测试地址",
        credit_limit=Decimal("100000")
    )
    db_manager.save_customer(customer)
    return customer


@pytest.fixture
def sample_order(db_manager, sample_customer):
    """创建示例订单"""
    order = ProcessingOrder(
        order_no="ORD-2024-001",
        customer_id=sample_customer.id,
        customer_name=sample_customer.name,
        item_description="铝型材氧化",
        quantity=Decimal("100"),
        pricing_unit=PricingUnit.PIECE,
        unit_price=Decimal("10.5"),
        processes=[ProcessType.SANDBLASTING, ProcessType.OXIDATION],
        total_amount=Decimal("1050"),
        status=OrderStatus.COMPLETED,
        order_date=date.today()
    )
    db_manager.save_order(order)
    return order


class TestIncomeManagement:
    """收入管理测试"""
    
    def test_record_income_basic(self, finance_manager, sample_customer):
        """测试基本收入记录"""
        income = finance_manager.record_income(
            customer_id=sample_customer.id,
            customer_name=sample_customer.name,
            amount=Decimal("5000"),
            bank_type=BankType.G_BANK,
            income_date=date.today(),
            has_invoice=True,
            notes="测试收入"
        )
        
        assert income.customer_id == sample_customer.id
        assert income.amount == Decimal("5000")
        assert income.bank_type == BankType.G_BANK
        assert income.has_invoice is True
        
        # 验证可以从数据库读取
        retrieved = finance_manager.get_income_by_id(income.id)
        assert retrieved is not None
        assert retrieved.amount == Decimal("5000")
    
    def test_record_income_n_bank(self, finance_manager, sample_customer):
        """测试N银行收入记录（现金等价物）"""
        income = finance_manager.record_income(
            customer_id=sample_customer.id,
            customer_name=sample_customer.name,
            amount=Decimal("3000"),
            bank_type=BankType.N_BANK,
            income_date=date.today(),
            has_invoice=False,
            notes="微信收款"
        )
        
        assert income.bank_type == BankType.N_BANK
        assert income.has_invoice is False
    
    def test_allocate_payment_to_single_order(self, finance_manager, sample_customer, sample_order):
        """测试将付款分配到单个订单"""
        # 记录收入
        income = finance_manager.record_income(
            customer_id=sample_customer.id,
            customer_name=sample_customer.name,
            amount=Decimal("1050"),
            bank_type=BankType.G_BANK,
            income_date=date.today()
        )
        
        # 分配到订单
        success, message = finance_manager.allocate_payment_to_orders(
            income_id=income.id,
            allocations={sample_order.id: Decimal("1050")}
        )
        
        assert success is True
        assert "成功" in message
        
        # 验证订单已收金额更新
        payment_status = finance_manager.get_order_payment_status(sample_order.id)
        assert payment_status["received_amount"] == Decimal("1050")
        assert payment_status["status"] == "已付清"
    
    def test_allocate_payment_to_multiple_orders(self, finance_manager, db_manager, sample_customer):
        """测试将付款分配到多个订单"""
        # 创建两个订单
        order1 = ProcessingOrder(
            order_no="ORD-2024-002",
            customer_id=sample_customer.id,
            customer_name=sample_customer.name,
            item_description="订单1",
            quantity=Decimal("50"),
            pricing_unit=PricingUnit.PIECE,
            unit_price=Decimal("10"),
            total_amount=Decimal("500"),
            status=OrderStatus.COMPLETED
        )
        db_manager.save_order(order1)
        
        order2 = ProcessingOrder(
            order_no="ORD-2024-003",
            customer_id=sample_customer.id,
            customer_name=sample_customer.name,
            item_description="订单2",
            quantity=Decimal("30"),
            pricing_unit=PricingUnit.PIECE,
            unit_price=Decimal("20"),
            total_amount=Decimal("600"),
            status=OrderStatus.COMPLETED
        )
        db_manager.save_order(order2)
        
        # 记录收入
        income = finance_manager.record_income(
            customer_id=sample_customer.id,
            customer_name=sample_customer.name,
            amount=Decimal("1100"),
            bank_type=BankType.G_BANK,
            income_date=date.today()
        )
        
        # 分配到两个订单
        success, message = finance_manager.allocate_payment_to_orders(
            income_id=income.id,
            allocations={
                order1.id: Decimal("500"),
                order2.id: Decimal("600")
            }
        )
        
        assert success is True
        
        # 验证两个订单都已付清
        status1 = finance_manager.get_order_payment_status(order1.id)
        status2 = finance_manager.get_order_payment_status(order2.id)
        assert status1["status"] == "已付清"
        assert status2["status"] == "已付清"
    
    def test_allocate_payment_partial(self, finance_manager, sample_customer, sample_order):
        """测试部分付款"""
        # 记录部分付款
        income = finance_manager.record_income(
            customer_id=sample_customer.id,
            customer_name=sample_customer.name,
            amount=Decimal("500"),
            bank_type=BankType.G_BANK,
            income_date=date.today()
        )
        
        # 分配到订单
        success, message = finance_manager.allocate_payment_to_orders(
            income_id=income.id,
            allocations={sample_order.id: Decimal("500")}
        )
        
        assert success is True
        
        # 验证订单状态为部分付款
        payment_status = finance_manager.get_order_payment_status(sample_order.id)
        assert payment_status["received_amount"] == Decimal("500")
        assert payment_status["unpaid_amount"] == Decimal("550")
        assert payment_status["status"] == "部分付款"
        assert abs(float(payment_status["payment_ratio"]) - 47.62) < 0.01  # 500/1050 * 100
    
    def test_allocate_payment_exceeds_order_amount(self, finance_manager, sample_customer, sample_order):
        """测试分配金额超过订单金额"""
        income = finance_manager.record_income(
            customer_id=sample_customer.id,
            customer_name=sample_customer.name,
            amount=Decimal("2000"),
            bank_type=BankType.G_BANK,
            income_date=date.today()
        )
        
        # 尝试分配超过订单金额
        success, message = finance_manager.allocate_payment_to_orders(
            income_id=income.id,
            allocations={sample_order.id: Decimal("2000")}
        )
        
        assert success is False
        assert "超过未付余额" in message
    
    def test_allocate_payment_exceeds_income_amount(self, finance_manager, sample_customer, sample_order):
        """测试分配金额总和超过收入金额"""
        income = finance_manager.record_income(
            customer_id=sample_customer.id,
            customer_name=sample_customer.name,
            amount=Decimal("500"),
            bank_type=BankType.G_BANK,
            income_date=date.today()
        )
        
        # 尝试分配超过收入金额
        success, message = finance_manager.allocate_payment_to_orders(
            income_id=income.id,
            allocations={sample_order.id: Decimal("600")}
        )
        
        assert success is False
        assert "超过付款金额" in message
    
    def test_get_customer_incomes(self, finance_manager, sample_customer):
        """测试查询客户收入记录"""
        # 记录多笔收入
        finance_manager.record_income(
            customer_id=sample_customer.id,
            customer_name=sample_customer.name,
            amount=Decimal("1000"),
            bank_type=BankType.G_BANK,
            income_date=date.today()
        )
        
        finance_manager.record_income(
            customer_id=sample_customer.id,
            customer_name=sample_customer.name,
            amount=Decimal("2000"),
            bank_type=BankType.N_BANK,
            income_date=date.today()
        )
        
        incomes = finance_manager.get_customer_incomes(sample_customer.id)
        assert len(incomes) == 2
        assert sum(i.amount for i in incomes) == Decimal("3000")
    
    def test_get_customer_receivables(self, finance_manager, db_manager, sample_customer):
        """测试获取客户应收账款汇总"""
        # 创建多个订单，部分付款
        order1 = ProcessingOrder(
            order_no="ORD-2024-004",
            customer_id=sample_customer.id,
            customer_name=sample_customer.name,
            item_description="订单1",
            quantity=Decimal("100"),
            pricing_unit=PricingUnit.PIECE,
            unit_price=Decimal("10"),
            total_amount=Decimal("1000"),
            received_amount=Decimal("500"),
            status=OrderStatus.COMPLETED
        )
        db_manager.save_order(order1)
        
        order2 = ProcessingOrder(
            order_no="ORD-2024-005",
            customer_id=sample_customer.id,
            customer_name=sample_customer.name,
            item_description="订单2",
            quantity=Decimal("50"),
            pricing_unit=PricingUnit.PIECE,
            unit_price=Decimal("20"),
            total_amount=Decimal("1000"),
            received_amount=Decimal("1000"),
            status=OrderStatus.COMPLETED
        )
        db_manager.save_order(order2)
        
        receivables = finance_manager.get_customer_receivables(sample_customer.id)
        
        assert receivables["total_amount"] == Decimal("2000")
        assert receivables["received_amount"] == Decimal("1500")
        assert receivables["unpaid_amount"] == Decimal("500")
        assert len(receivables["unpaid_orders"]) == 1
        assert receivables["unpaid_orders"][0]["order_no"] == "ORD-2024-004"


class TestExpenseManagement:
    """支出管理测试"""
    
    def test_record_expense_basic(self, finance_manager, db_manager):
        """测试基本支出记录"""
        # 创建供应商
        from ..models.business_models import Supplier
        supplier = Supplier(
            name="测试供应商",
            contact="李四",
            phone="13900139000",
            business_type="原料供应商"
        )
        db_manager.save_supplier(supplier)
        
        expense = finance_manager.record_expense(
            expense_type=ExpenseType.ACID_THREE,
            amount=Decimal("3000"),
            bank_type=BankType.G_BANK,
            expense_date=date.today(),
            supplier_id=supplier.id,
            supplier_name=supplier.name,
            has_invoice=True,
            description="采购硫酸",
            notes="测试支出"
        )
        
        assert expense.expense_type == ExpenseType.ACID_THREE
        assert expense.amount == Decimal("3000")
        assert expense.supplier_id == supplier.id
        assert expense.has_invoice is True
    
    def test_record_expense_without_supplier(self, finance_manager):
        """测试不关联供应商的支出"""
        expense = finance_manager.record_expense(
            expense_type=ExpenseType.RENT,
            amount=Decimal("5000"),
            bank_type=BankType.G_BANK,
            expense_date=date.today(),
            description="厂房租金",
            notes="月租"
        )
        
        assert expense.expense_type == ExpenseType.RENT
        assert expense.supplier_id is None
    
    def test_record_outsourcing_expense(self, finance_manager, db_manager, sample_customer):
        """测试委外加工费用"""
        # 创建订单
        order = ProcessingOrder(
            order_no="ORD-2024-006",
            customer_id=sample_customer.id,
            customer_name=sample_customer.name,
            item_description="需要委外的订单",
            quantity=Decimal("100"),
            pricing_unit=PricingUnit.PIECE,
            unit_price=Decimal("15"),
            total_amount=Decimal("1500"),
            status=OrderStatus.OUTSOURCED
        )
        db_manager.save_order(order)
        
        # 记录委外费用
        expense = finance_manager.record_expense(
            expense_type=ExpenseType.OUTSOURCING,
            amount=Decimal("800"),
            bank_type=BankType.G_BANK,
            expense_date=date.today(),
            supplier_name="委外供应商",
            related_order_id=order.id,
            description="喷砂委外加工"
        )
        
        assert expense.expense_type == ExpenseType.OUTSOURCING
        assert expense.related_order_id == order.id
    
    def test_get_supplier_expenses(self, finance_manager, db_manager):
        """测试查询供应商支出"""
        from ..models.business_models import Supplier
        supplier = Supplier(
            name="测试供应商2",
            contact="王五",
            business_type="原料供应商"
        )
        db_manager.save_supplier(supplier)
        
        # 记录多笔支出
        finance_manager.record_expense(
            expense_type=ExpenseType.ACID_THREE,
            amount=Decimal("1000"),
            bank_type=BankType.G_BANK,
            expense_date=date.today(),
            supplier_id=supplier.id,
            supplier_name=supplier.name
        )
        
        finance_manager.record_expense(
            expense_type=ExpenseType.CAUSTIC_SODA,
            amount=Decimal("500"),
            bank_type=BankType.G_BANK,
            expense_date=date.today(),
            supplier_id=supplier.id,
            supplier_name=supplier.name
        )
        
        expenses = finance_manager.get_supplier_expenses(supplier.id)
        assert len(expenses) == 2
        assert sum(e.amount for e in expenses) == Decimal("1500")
    
    def test_get_expenses_by_type(self, finance_manager):
        """测试按类型查询支出"""
        # 记录不同类型的支出
        finance_manager.record_expense(
            expense_type=ExpenseType.UTILITIES,
            amount=Decimal("800"),
            bank_type=BankType.G_BANK,
            expense_date=date.today(),
            description="电费"
        )
        
        finance_manager.record_expense(
            expense_type=ExpenseType.UTILITIES,
            amount=Decimal("300"),
            bank_type=BankType.G_BANK,
            expense_date=date.today(),
            description="水费"
        )
        
        finance_manager.record_expense(
            expense_type=ExpenseType.RENT,
            amount=Decimal("5000"),
            bank_type=BankType.G_BANK,
            expense_date=date.today(),
            description="租金"
        )
        
        utilities = finance_manager.get_expenses_by_type(ExpenseType.UTILITIES)
        assert len(utilities) == 2
        assert sum(e.amount for e in utilities) == Decimal("1100")
        
        rent = finance_manager.get_expenses_by_type(ExpenseType.RENT)
        assert len(rent) == 1
        assert rent[0].amount == Decimal("5000")
    
    def test_allocate_payment_to_expenses(self, finance_manager, db_manager):
        """测试将付款分配到多个支出"""
        from ..models.business_models import Supplier
        supplier = Supplier(
            name="原料供应商",
            contact="赵六",
            business_type="原料供应商"
        )
        db_manager.save_supplier(supplier)
        
        # 记录多笔支出
        expense1 = finance_manager.record_expense(
            expense_type=ExpenseType.ACID_THREE,
            amount=Decimal("2000"),
            bank_type=BankType.G_BANK,
            expense_date=date.today(),
            supplier_id=supplier.id,
            supplier_name=supplier.name,
            description="硫酸采购"
        )
        
        expense2 = finance_manager.record_expense(
            expense_type=ExpenseType.CAUSTIC_SODA,
            amount=Decimal("1500"),
            bank_type=BankType.G_BANK,
            expense_date=date.today(),
            supplier_id=supplier.id,
            supplier_name=supplier.name,
            description="片碱采购"
        )
        
        # 分配付款
        success, message = finance_manager.allocate_payment_to_expenses(
            payment_amount=Decimal("3500"),
            allocations={
                expense1.id: Decimal("2000"),
                expense2.id: Decimal("1500")
            },
            bank_type=BankType.G_BANK,
            payment_date=date.today(),
            notes="批量付款"
        )
        
        assert success is True
        assert "成功" in message
    
    def test_allocate_payment_exceeds_amount(self, finance_manager, db_manager):
        """测试分配金额超过付款金额"""
        from ..models.business_models import Supplier
        supplier = Supplier(name="测试供应商")
        db_manager.save_supplier(supplier)
        
        expense = finance_manager.record_expense(
            expense_type=ExpenseType.ACID_THREE,
            amount=Decimal("2000"),
            bank_type=BankType.G_BANK,
            expense_date=date.today(),
            supplier_id=supplier.id,
            supplier_name=supplier.name
        )
        
        # 尝试分配超过付款金额
        success, message = finance_manager.allocate_payment_to_expenses(
            payment_amount=Decimal("1000"),
            allocations={expense.id: Decimal("2000")},
            bank_type=BankType.G_BANK,
            payment_date=date.today()
        )
        
        assert success is False
        assert "超过付款金额" in message
    
    def test_get_supplier_payables(self, finance_manager, db_manager):
        """测试获取供应商应付账款"""
        from ..models.business_models import Supplier
        supplier = Supplier(
            name="化工供应商",
            contact="孙七",
            business_type="原料供应商"
        )
        db_manager.save_supplier(supplier)
        
        # 记录多笔支出
        finance_manager.record_expense(
            expense_type=ExpenseType.ACID_THREE,
            amount=Decimal("3000"),
            bank_type=BankType.G_BANK,
            expense_date=date.today(),
            supplier_id=supplier.id,
            supplier_name=supplier.name,
            description="硫酸"
        )
        
        finance_manager.record_expense(
            expense_type=ExpenseType.COLOR_POWDER,
            amount=Decimal("800"),
            bank_type=BankType.G_BANK,
            expense_date=date.today(),
            supplier_id=supplier.id,
            supplier_name=supplier.name,
            description="色粉"
        )
        
        payables = finance_manager.get_supplier_payables(supplier.id)
        
        assert payables["total_amount"] == Decimal("3800")
        assert payables["expense_count"] == 2
        assert len(payables["expense_details"]) == 2
    
    def test_get_expense_summary_by_type(self, finance_manager):
        """测试按类型汇总支出"""
        today = date.today()
        
        # 记录不同类型的支出
        finance_manager.record_expense(
            expense_type=ExpenseType.RENT,
            amount=Decimal("5000"),
            bank_type=BankType.G_BANK,
            expense_date=today,
            description="租金"
        )
        
        finance_manager.record_expense(
            expense_type=ExpenseType.UTILITIES,
            amount=Decimal("800"),
            bank_type=BankType.G_BANK,
            expense_date=today,
            description="电费"
        )
        
        finance_manager.record_expense(
            expense_type=ExpenseType.UTILITIES,
            amount=Decimal("300"),
            bank_type=BankType.G_BANK,
            expense_date=today,
            description="水费"
        )
        
        finance_manager.record_expense(
            expense_type=ExpenseType.ACID_THREE,
            amount=Decimal("2000"),
            bank_type=BankType.G_BANK,
            expense_date=today,
            description="硫酸"
        )
        
        summary = finance_manager.get_expense_summary_by_type()
        
        assert summary["房租"] == Decimal("5000")
        assert summary["水电费"] == Decimal("1100")
        assert summary["三酸"] == Decimal("2000")
    
    def test_get_expense_summary_with_date_filter(self, finance_manager):
        """测试按日期过滤的支出汇总"""
        today = date.today()
        yesterday = today - timedelta(days=1)
        
        # 记录不同日期的支出
        finance_manager.record_expense(
            expense_type=ExpenseType.RENT,
            amount=Decimal("5000"),
            bank_type=BankType.G_BANK,
            expense_date=yesterday,
            description="上月租金"
        )
        
        finance_manager.record_expense(
            expense_type=ExpenseType.RENT,
            amount=Decimal("5000"),
            bank_type=BankType.G_BANK,
            expense_date=today,
            description="本月租金"
        )
        
        # 只查询今天的支出
        summary = finance_manager.get_expense_summary_by_type(
            start_date=today,
            end_date=today
        )
        
        assert summary["房租"] == Decimal("5000")
    
    def test_get_professional_materials_expenses(self, finance_manager, db_manager):
        """测试获取专业原料支出汇总"""
        from ..models.business_models import Supplier
        supplier = Supplier(name="化工供应商")
        db_manager.save_supplier(supplier)
        
        today = date.today()
        
        # 记录各种专业原料支出
        finance_manager.record_expense(
            expense_type=ExpenseType.ACID_THREE,
            amount=Decimal("3000"),
            bank_type=BankType.G_BANK,
            expense_date=today,
            supplier_id=supplier.id,
            supplier_name=supplier.name,
            description="硫酸"
        )
        
        finance_manager.record_expense(
            expense_type=ExpenseType.CAUSTIC_SODA,
            amount=Decimal("1500"),
            bank_type=BankType.G_BANK,
            expense_date=today,
            supplier_id=supplier.id,
            supplier_name=supplier.name,
            description="片碱"
        )
        
        finance_manager.record_expense(
            expense_type=ExpenseType.COLOR_POWDER,
            amount=Decimal("800"),
            bank_type=BankType.G_BANK,
            expense_date=today,
            supplier_id=supplier.id,
            supplier_name=supplier.name,
            description="色粉"
        )
        
        finance_manager.record_expense(
            expense_type=ExpenseType.DEGREASER,
            amount=Decimal("600"),
            bank_type=BankType.G_BANK,
            expense_date=today,
            supplier_id=supplier.id,
            supplier_name=supplier.name,
            description="除油剂"
        )
        
        # 记录非专业原料支出（不应包含在结果中）
        finance_manager.record_expense(
            expense_type=ExpenseType.RENT,
            amount=Decimal("5000"),
            bank_type=BankType.G_BANK,
            expense_date=today,
            description="租金"
        )
        
        materials = finance_manager.get_professional_materials_expenses()
        
        assert materials["total_amount"] == Decimal("5900")
        assert "三酸" in materials["materials"]
        assert "片碱" in materials["materials"]
        assert "色粉" in materials["materials"]
        assert "除油剂" in materials["materials"]
        assert materials["materials"]["三酸"]["amount"] == Decimal("3000")
        assert materials["materials"]["片碱"]["amount"] == Decimal("1500")
        
        # 验证租金不在专业原料中
        assert "房租" not in materials["materials"]
    
    def test_professional_materials_with_date_filter(self, finance_manager, db_manager):
        """测试按日期过滤的专业原料支出"""
        from ..models.business_models import Supplier
        supplier = Supplier(name="化工供应商")
        db_manager.save_supplier(supplier)
        
        today = date.today()
        yesterday = today - timedelta(days=1)
        
        # 记录不同日期的支出
        finance_manager.record_expense(
            expense_type=ExpenseType.ACID_THREE,
            amount=Decimal("2000"),
            bank_type=BankType.G_BANK,
            expense_date=yesterday,
            supplier_id=supplier.id,
            supplier_name=supplier.name,
            description="昨天的硫酸"
        )
        
        finance_manager.record_expense(
            expense_type=ExpenseType.ACID_THREE,
            amount=Decimal("3000"),
            bank_type=BankType.G_BANK,
            expense_date=today,
            supplier_id=supplier.id,
            supplier_name=supplier.name,
            description="今天的硫酸"
        )
        
        # 只查询今天的
        materials = finance_manager.get_professional_materials_expenses(
            start_date=today,
            end_date=today
        )
        
        assert materials["total_amount"] == Decimal("3000")
        assert materials["materials"]["三酸"]["count"] == 1
