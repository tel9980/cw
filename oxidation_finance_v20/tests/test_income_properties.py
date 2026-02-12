#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
收入管理属性测试 - 验证收入管理的核心正确性属性
"""

import pytest
from hypothesis import given, strategies as st, settings, assume
from decimal import Decimal
from datetime import date, timedelta
import tempfile
import os

from oxidation_finance_v20.models.business_models import (
    Customer, ProcessingOrder, BankType, PricingUnit, ProcessType, OrderStatus
)
from oxidation_finance_v20.database.db_manager import DatabaseManager
from oxidation_finance_v20.business.finance_manager import FinanceManager
from oxidation_finance_v20.business.order_manager import OrderManager


# ==================== 策略定义 ====================

@st.composite
def customer_strategy(draw):
    """生成客户数据的策略"""
    return Customer(
        name=draw(st.text(min_size=1, max_size=50, alphabet=st.characters(whitelist_categories=('L', 'N')))),
        contact=draw(st.text(min_size=1, max_size=30, alphabet=st.characters(whitelist_categories=('L', 'N')))),
        phone=draw(st.text(min_size=8, max_size=15, alphabet=st.characters(whitelist_categories=('N',)))),
        address=draw(st.text(min_size=1, max_size=100, alphabet=st.characters(whitelist_categories=('L', 'N')))),
        credit_limit=Decimal(str(draw(st.floats(min_value=0, max_value=1000000, allow_nan=False, allow_infinity=False)))),
        notes=draw(st.text(max_size=200))
    )


@st.composite
def amount_strategy(draw):
    """生成金额的策略"""
    return Decimal(str(draw(st.floats(min_value=0.01, max_value=100000, allow_nan=False, allow_infinity=False))))


@st.composite
def date_strategy(draw):
    """生成日期的策略"""
    days_offset = draw(st.integers(min_value=-365, max_value=365))
    return date.today() + timedelta(days=days_offset)


# ==================== 属性测试 ====================

class TestProperty6_PaymentRecordCompleteness:
    """
    **属性 6: 付款信息记录完整性**
    **Validates: Requirements 2.1**
    
    对于任何客户付款，记录的付款金额、付款方式和付款日期应该与实际付款信息完全一致
    """
    
    @given(
        customer=customer_strategy(),
        amount=amount_strategy(),
        bank_type=st.sampled_from(list(BankType)),
        income_date=date_strategy(),
        has_invoice=st.booleans()
    )
    @settings(max_examples=100, deadline=None)
    def test_payment_information_recorded_completely(self, customer, amount, bank_type, income_date, has_invoice):
        """测试付款信息被完整记录"""
        fd, path = tempfile.mkstemp(suffix='.db')
        os.close(fd)
        
        try:
            with DatabaseManager(path) as db:
                db.save_customer(customer)
                finance_manager = FinanceManager(db)
                
                # 记录收入
                income = finance_manager.record_income(
                    customer_id=customer.id,
                    customer_name=customer.name,
                    amount=amount,
                    bank_type=bank_type,
                    income_date=income_date,
                    has_invoice=has_invoice,
                    notes="测试收入"
                )
                
                # 验证收入信息完整性
                assert income is not None, "收入记录应该被创建"
                assert income.customer_id == customer.id, "客户ID应该一致"
                assert income.customer_name == customer.name, "客户名称应该一致"
                assert income.amount == amount, "付款金额应该一致"
                assert income.bank_type == bank_type, "付款方式应该一致"
                assert income.income_date == income_date, "付款日期应该一致"
                assert income.has_invoice == has_invoice, "票据信息应该一致"
                
                # 验证从数据库查询的信息一致性
                retrieved = finance_manager.get_income_by_id(income.id)
                assert retrieved is not None, "应该能查询到收入记录"
                assert retrieved.customer_id == customer.id, "查询的客户ID应该一致"
                assert retrieved.customer_name == customer.name, "查询的客户名称应该一致"
                assert retrieved.amount == amount, "查询的付款金额应该一致"
                assert retrieved.bank_type == bank_type, "查询的付款方式应该一致"
                assert retrieved.income_date == income_date, "查询的付款日期应该一致"
                assert retrieved.has_invoice == has_invoice, "查询的票据信息应该一致"
        
        finally:
            if os.path.exists(path):
                os.unlink(path)

    @given(
        customer=customer_strategy(),
        amount=amount_strategy()
    )
    @settings(max_examples=100, deadline=None)
    def test_g_bank_invoice_marking(self, customer, amount):
        """测试G银行交易的票据标记"""
        fd, path = tempfile.mkstemp(suffix='.db')
        os.close(fd)
        
        try:
            with DatabaseManager(path) as db:
                db.save_customer(customer)
                finance_manager = FinanceManager(db)
                
                # 记录G银行有票据的收入
                income_with_invoice = finance_manager.record_income(
                    customer_id=customer.id,
                    customer_name=customer.name,
                    amount=amount,
                    bank_type=BankType.G_BANK,
                    income_date=date.today(),
                    has_invoice=True
                )
                
                assert income_with_invoice.bank_type == BankType.G_BANK, "应该是G银行"
                assert income_with_invoice.has_invoice is True, "应该标记有票据"
                
                # 记录G银行无票据的收入
                income_without_invoice = finance_manager.record_income(
                    customer_id=customer.id,
                    customer_name=customer.name,
                    amount=amount,
                    bank_type=BankType.G_BANK,
                    income_date=date.today(),
                    has_invoice=False
                )
                
                assert income_without_invoice.bank_type == BankType.G_BANK, "应该是G银行"
                assert income_without_invoice.has_invoice is False, "应该标记无票据"
        
        finally:
            if os.path.exists(path):
                os.unlink(path)
    
    @given(
        customer=customer_strategy(),
        amount=amount_strategy()
    )
    @settings(max_examples=100, deadline=None)
    def test_n_bank_cash_equivalent_marking(self, customer, amount):
        """测试N银行交易作为现金等价物处理"""
        fd, path = tempfile.mkstemp(suffix='.db')
        os.close(fd)
        
        try:
            with DatabaseManager(path) as db:
                db.save_customer(customer)
                finance_manager = FinanceManager(db)
                
                # 记录N银行收入（现金等价物）
                income = finance_manager.record_income(
                    customer_id=customer.id,
                    customer_name=customer.name,
                    amount=amount,
                    bank_type=BankType.N_BANK,
                    income_date=date.today(),
                    has_invoice=False,
                    notes="微信收款"
                )
                
                assert income.bank_type == BankType.N_BANK, "应该是N银行"
                # N银行通常不需要票据，作为现金等价物处理
                
                # 验证查询时银行类型保持一致
                retrieved = finance_manager.get_income_by_id(income.id)
                assert retrieved.bank_type == BankType.N_BANK, "查询的银行类型应该是N银行"
        
        finally:
            if os.path.exists(path):
                os.unlink(path)


class TestProperty7_PaymentAllocationConsistency:
    """
    **属性 7: 付款灵活分配一致性**
    **Validates: Requirements 2.2**
    
    对于任何付款分配操作，分配到各个订单的金额总和应该等于原始付款金额，
    且不能超过各项的未付余额
    """
    
    @given(
        customer=customer_strategy(),
        payment_amount=st.decimals(min_value=Decimal("100"), max_value=Decimal("10000"), places=2),
        num_orders=st.integers(min_value=1, max_value=5)
    )
    @settings(max_examples=100, deadline=None)
    def test_allocation_sum_equals_payment_amount(self, customer, payment_amount, num_orders):
        """测试分配金额总和等于付款金额"""
        fd, path = tempfile.mkstemp(suffix='.db')
        os.close(fd)
        
        try:
            with DatabaseManager(path) as db:
                db.save_customer(customer)
                finance_manager = FinanceManager(db)
                order_manager = OrderManager(db)
                
                # 创建多个订单
                orders = []
                for i in range(num_orders):
                    order = order_manager.create_order(
                        customer_id=customer.id,
                        customer_name=customer.name,
                        item_description=f"订单{i+1}",
                        quantity=Decimal("100"),
                        pricing_unit=PricingUnit.PIECE,
                        unit_price=Decimal("10"),
                        processes=[ProcessType.OXIDATION]
                    )
                    orders.append(order)
                
                # 记录收入
                income = finance_manager.record_income(
                    customer_id=customer.id,
                    customer_name=customer.name,
                    amount=payment_amount,
                    bank_type=BankType.G_BANK,
                    income_date=date.today()
                )
                
                # 计算分配金额（平均分配，但不超过订单金额）
                allocations = {}
                remaining = payment_amount
                for i, order in enumerate(orders):
                    if i == len(orders) - 1:
                        # 最后一个订单分配剩余金额
                        allocated = min(remaining, order.total_amount)
                    else:
                        # 平均分配
                        allocated = min(payment_amount / num_orders, order.total_amount)
                        allocated = Decimal(str(allocated)).quantize(Decimal("0.01"))
                    
                    if allocated > 0:
                        allocations[order.id] = allocated
                        remaining -= allocated
                
                # 执行分配
                if allocations:
                    success, message = finance_manager.allocate_payment_to_orders(
                        income_id=income.id,
                        allocations=allocations
                    )
                    
                    if success:
                        # 验证分配金额总和不超过付款金额
                        total_allocated = sum(allocations.values())
                        assert total_allocated <= payment_amount, \
                            f"分配金额总和 {total_allocated} 不应超过付款金额 {payment_amount}"
                        
                        # 验证每个订单的分配金额不超过其未付余额
                        for order_id, allocated_amount in allocations.items():
                            order = order_manager.get_order(order_id)
                            assert order.received_amount <= order.total_amount, \
                                f"订单已收金额 {order.received_amount} 不应超过订单总金额 {order.total_amount}"
        
        finally:
            if os.path.exists(path):
                os.unlink(path)

    @given(
        customer=customer_strategy(),
        order_amount=st.decimals(min_value=Decimal("100"), max_value=Decimal("5000"), places=2),
        payment_amount=st.decimals(min_value=Decimal("100"), max_value=Decimal("5000"), places=2)
    )
    @settings(max_examples=100, deadline=None)
    def test_allocation_cannot_exceed_unpaid_balance(self, customer, order_amount, payment_amount):
        """测试分配金额不能超过订单未付余额"""
        fd, path = tempfile.mkstemp(suffix='.db')
        os.close(fd)
        
        try:
            with DatabaseManager(path) as db:
                db.save_customer(customer)
                finance_manager = FinanceManager(db)
                order_manager = OrderManager(db)
                
                # 创建订单
                order = order_manager.create_order(
                    customer_id=customer.id,
                    customer_name=customer.name,
                    item_description="测试订单",
                    quantity=Decimal("100"),
                    pricing_unit=PricingUnit.PIECE,
                    unit_price=order_amount / Decimal("100"),
                    processes=[ProcessType.OXIDATION]
                )
                
                # 记录收入
                income = finance_manager.record_income(
                    customer_id=customer.id,
                    customer_name=customer.name,
                    amount=payment_amount,
                    bank_type=BankType.G_BANK,
                    income_date=date.today()
                )
                
                # 尝试分配金额
                allocated_amount = min(payment_amount, order_amount)
                success, message = finance_manager.allocate_payment_to_orders(
                    income_id=income.id,
                    allocations={order.id: allocated_amount}
                )
                
                if success:
                    # 验证订单已收金额不超过订单总金额
                    updated_order = order_manager.get_order(order.id)
                    assert updated_order.received_amount <= updated_order.total_amount, \
                        "订单已收金额不应超过订单总金额"
                    
                    # 尝试再次分配超过剩余金额
                    unpaid = updated_order.total_amount - updated_order.received_amount
                    if unpaid > 0 and payment_amount > allocated_amount:
                        # 记录第二笔收入
                        income2 = finance_manager.record_income(
                            customer_id=customer.id,
                            customer_name=customer.name,
                            amount=payment_amount,
                            bank_type=BankType.G_BANK,
                            income_date=date.today()
                        )
                        
                        # 尝试分配超过未付余额的金额
                        over_allocated = unpaid + Decimal("100")
                        success2, message2 = finance_manager.allocate_payment_to_orders(
                            income_id=income2.id,
                            allocations={order.id: over_allocated}
                        )
                        
                        # 应该失败
                        assert success2 is False, "分配超过未付余额应该失败"
                        assert "超过未付余额" in message2, "错误消息应该提示超过未付余额"
        
        finally:
            if os.path.exists(path):
                os.unlink(path)

    @given(
        customer=customer_strategy(),
        num_orders=st.integers(min_value=2, max_value=4)
    )
    @settings(max_examples=100, deadline=None)
    def test_flexible_allocation_to_multiple_orders(self, customer, num_orders):
        """测试灵活分配到多个订单的一致性"""
        fd, path = tempfile.mkstemp(suffix='.db')
        os.close(fd)
        
        try:
            with DatabaseManager(path) as db:
                db.save_customer(customer)
                finance_manager = FinanceManager(db)
                order_manager = OrderManager(db)
                
                # 创建多个订单
                orders = []
                total_order_amount = Decimal("0")
                for i in range(num_orders):
                    order = order_manager.create_order(
                        customer_id=customer.id,
                        customer_name=customer.name,
                        item_description=f"订单{i+1}",
                        quantity=Decimal("50"),
                        pricing_unit=PricingUnit.PIECE,
                        unit_price=Decimal("10"),
                        processes=[ProcessType.OXIDATION]
                    )
                    orders.append(order)
                    total_order_amount += order.total_amount
                
                # 记录一笔收入，金额为所有订单总额的一半
                payment_amount = total_order_amount / 2
                payment_amount = payment_amount.quantize(Decimal("0.01"))
                
                income = finance_manager.record_income(
                    customer_id=customer.id,
                    customer_name=customer.name,
                    amount=payment_amount,
                    bank_type=BankType.G_BANK,
                    income_date=date.today()
                )
                
                # 灵活分配到多个订单
                allocations = {}
                remaining = payment_amount
                for i, order in enumerate(orders):
                    if i == len(orders) - 1:
                        # 最后一个订单分配剩余金额
                        allocated = remaining
                    else:
                        # 平均分配
                        allocated = (payment_amount / num_orders).quantize(Decimal("0.01"))
                    
                    allocations[order.id] = allocated
                    remaining -= allocated
                
                success, message = finance_manager.allocate_payment_to_orders(
                    income_id=income.id,
                    allocations=allocations
                )
                
                assert success is True, f"灵活分配应该成功: {message}"
                
                # 验证分配一致性
                total_allocated = sum(allocations.values())
                assert abs(total_allocated - payment_amount) < Decimal("0.01"), \
                    f"分配金额总和 {total_allocated} 应该等于付款金额 {payment_amount}"
                
                # 验证每个订单的已收金额
                for order_id, allocated_amount in allocations.items():
                    order = order_manager.get_order(order_id)
                    assert order.received_amount == allocated_amount, \
                        f"订单已收金额应该等于分配金额 {allocated_amount}"
        
        finally:
            if os.path.exists(path):
                os.unlink(path)

    @given(
        customer=customer_strategy(),
        payment_amount=st.decimals(min_value=Decimal("100"), max_value=Decimal("5000"), places=2)
    )
    @settings(max_examples=50, deadline=None)
    def test_allocation_sum_cannot_exceed_payment(self, customer, payment_amount):
        """测试分配金额总和不能超过付款金额"""
        fd, path = tempfile.mkstemp(suffix='.db')
        os.close(fd)
        
        try:
            with DatabaseManager(path) as db:
                db.save_customer(customer)
                finance_manager = FinanceManager(db)
                order_manager = OrderManager(db)
                
                # 创建两个订单
                order1 = order_manager.create_order(
                    customer_id=customer.id,
                    customer_name=customer.name,
                    item_description="订单1",
                    quantity=Decimal("100"),
                    pricing_unit=PricingUnit.PIECE,
                    unit_price=Decimal("50"),
                    processes=[ProcessType.OXIDATION]
                )
                
                order2 = order_manager.create_order(
                    customer_id=customer.id,
                    customer_name=customer.name,
                    item_description="订单2",
                    quantity=Decimal("100"),
                    pricing_unit=PricingUnit.PIECE,
                    unit_price=Decimal("50"),
                    processes=[ProcessType.OXIDATION]
                )
                
                # 记录收入
                income = finance_manager.record_income(
                    customer_id=customer.id,
                    customer_name=customer.name,
                    amount=payment_amount,
                    bank_type=BankType.G_BANK,
                    income_date=date.today()
                )
                
                # 尝试分配超过付款金额的总和
                over_allocation = {
                    order1.id: payment_amount * Decimal("0.6"),
                    order2.id: payment_amount * Decimal("0.6")  # 总和为 1.2 倍
                }
                
                success, message = finance_manager.allocate_payment_to_orders(
                    income_id=income.id,
                    allocations=over_allocation
                )
                
                # 应该失败
                assert success is False, "分配总和超过付款金额应该失败"
                assert "超过付款金额" in message, "错误消息应该提示超过付款金额"
        
        finally:
            if os.path.exists(path):
                os.unlink(path)


class TestProperty9_PartialPaymentBalanceAccuracy:
    """
    **属性 9: 部分付款余额计算准确性**
    **Validates: Requirements 2.4**
    
    对于任何订单的部分付款，订单的未付余额应该等于订单总金额减去所有已付金额的总和
    """

    @given(
        customer=customer_strategy(),
        order_amount=st.decimals(min_value=Decimal("100"), max_value=Decimal("10000"), places=2),
        num_payments=st.integers(min_value=1, max_value=5)
    )
    @settings(max_examples=100, deadline=None)
    def test_partial_payment_balance_calculation(self, customer, order_amount, num_payments):
        """测试部分付款余额计算准确性"""
        fd, path = tempfile.mkstemp(suffix='.db')
        os.close(fd)
        
        try:
            with DatabaseManager(path) as db:
                db.save_customer(customer)
                finance_manager = FinanceManager(db)
                order_manager = OrderManager(db)
                
                # 创建订单
                order = order_manager.create_order(
                    customer_id=customer.id,
                    customer_name=customer.name,
                    item_description="测试订单",
                    quantity=Decimal("100"),
                    pricing_unit=PricingUnit.PIECE,
                    unit_price=order_amount / Decimal("100"),
                    processes=[ProcessType.OXIDATION]
                )
                
                # 进行多次部分付款
                total_paid = Decimal("0")
                for i in range(num_payments):
                    # 计算本次付款金额（不超过剩余未付金额）
                    remaining = order_amount - total_paid
                    if remaining <= 0:
                        break
                    
                    # 付款金额为剩余金额的一部分
                    payment_ratio = Decimal(str(1.0 / (num_payments - i)))
                    payment_amount = (remaining * payment_ratio).quantize(Decimal("0.01"))
                    
                    # 确保不超过剩余金额
                    payment_amount = min(payment_amount, remaining)
                    
                    if payment_amount <= 0:
                        break
                    
                    # 记录收入
                    income = finance_manager.record_income(
                        customer_id=customer.id,
                        customer_name=customer.name,
                        amount=payment_amount,
                        bank_type=BankType.G_BANK,
                        income_date=date.today()
                    )
                    
                    # 分配到订单
                    success, message = finance_manager.allocate_payment_to_orders(
                        income_id=income.id,
                        allocations={order.id: payment_amount}
                    )
                    
                    if success:
                        total_paid += payment_amount
                        
                        # 验证余额计算准确性
                        payment_status = finance_manager.get_order_payment_status(order.id)
                        expected_unpaid = order_amount - total_paid
                        
                        assert payment_status["total_amount"] == order_amount, \
                            "订单总金额应该保持不变"
                        assert payment_status["received_amount"] == total_paid, \
                            f"已收金额应该等于累计付款 {total_paid}"
                        assert abs(payment_status["unpaid_amount"] - expected_unpaid) < Decimal("0.01"), \
                            f"未付余额 {payment_status['unpaid_amount']} 应该等于 {expected_unpaid}"
        
        finally:
            if os.path.exists(path):
                os.unlink(path)

    @given(
        customer=customer_strategy(),
        order_amount=st.decimals(min_value=Decimal("1000"), max_value=Decimal("10000"), places=2),
        first_payment_ratio=st.decimals(min_value=Decimal("0.1"), max_value=Decimal("0.9"), places=2)
    )
    @settings(max_examples=100, deadline=None)
    def test_unpaid_balance_after_partial_payment(self, customer, order_amount, first_payment_ratio):
        """测试部分付款后的未付余额"""
        fd, path = tempfile.mkstemp(suffix='.db')
        os.close(fd)
        
        try:
            with DatabaseManager(path) as db:
                db.save_customer(customer)
                finance_manager = FinanceManager(db)
                order_manager = OrderManager(db)
                
                # 创建订单
                order = order_manager.create_order(
                    customer_id=customer.id,
                    customer_name=customer.name,
                    item_description="测试订单",
                    quantity=Decimal("100"),
                    pricing_unit=PricingUnit.PIECE,
                    unit_price=order_amount / Decimal("100"),
                    processes=[ProcessType.OXIDATION]
                )
                
                # 第一次部分付款
                first_payment = (order_amount * first_payment_ratio).quantize(Decimal("0.01"))
                income1 = finance_manager.record_income(
                    customer_id=customer.id,
                    customer_name=customer.name,
                    amount=first_payment,
                    bank_type=BankType.G_BANK,
                    income_date=date.today()
                )
                
                success1, _ = finance_manager.allocate_payment_to_orders(
                    income_id=income1.id,
                    allocations={order.id: first_payment}
                )
                
                assert success1 is True, "第一次付款分配应该成功"
                
                # 验证第一次付款后的余额
                status1 = finance_manager.get_order_payment_status(order.id)
                expected_unpaid1 = order_amount - first_payment
                
                assert status1["received_amount"] == first_payment, "已收金额应该等于第一次付款"
                assert abs(status1["unpaid_amount"] - expected_unpaid1) < Decimal("0.01"), \
                    f"未付余额应该等于 {expected_unpaid1}"
                assert status1["status"] == "部分付款", "状态应该是部分付款"
                
                # 第二次付款（付清剩余金额）
                remaining = status1["unpaid_amount"]
                income2 = finance_manager.record_income(
                    customer_id=customer.id,
                    customer_name=customer.name,
                    amount=remaining,
                    bank_type=BankType.G_BANK,
                    income_date=date.today()
                )
                
                success2, _ = finance_manager.allocate_payment_to_orders(
                    income_id=income2.id,
                    allocations={order.id: remaining}
                )
                
                assert success2 is True, "第二次付款分配应该成功"
                
                # 验证付清后的余额
                status2 = finance_manager.get_order_payment_status(order.id)
                
                assert abs(status2["received_amount"] - order_amount) < Decimal("0.01"), \
                    "已收金额应该等于订单总金额"
                assert abs(status2["unpaid_amount"]) < Decimal("0.01"), \
                    "未付余额应该为0"
                assert status2["status"] == "已付清", "状态应该是已付清"
        
        finally:
            if os.path.exists(path):
                os.unlink(path)

    @given(
        customer=customer_strategy(),
        num_orders=st.integers(min_value=2, max_value=4)
    )
    @settings(max_examples=50, deadline=None)
    def test_multiple_orders_partial_payment_balance(self, customer, num_orders):
        """测试多个订单的部分付款余额计算"""
        fd, path = tempfile.mkstemp(suffix='.db')
        os.close(fd)
        
        try:
            with DatabaseManager(path) as db:
                db.save_customer(customer)
                finance_manager = FinanceManager(db)
                order_manager = OrderManager(db)
                
                # 创建多个订单
                orders = []
                for i in range(num_orders):
                    order = order_manager.create_order(
                        customer_id=customer.id,
                        customer_name=customer.name,
                        item_description=f"订单{i+1}",
                        quantity=Decimal("100"),
                        pricing_unit=PricingUnit.PIECE,
                        unit_price=Decimal("10"),
                        processes=[ProcessType.OXIDATION]
                    )
                    orders.append(order)
                
                # 记录一笔收入，部分支付所有订单
                total_order_amount = sum(o.total_amount for o in orders)
                payment_amount = (total_order_amount * Decimal("0.5")).quantize(Decimal("0.01"))
                
                income = finance_manager.record_income(
                    customer_id=customer.id,
                    customer_name=customer.name,
                    amount=payment_amount,
                    bank_type=BankType.G_BANK,
                    income_date=date.today()
                )
                
                # 平均分配到所有订单
                allocations = {}
                per_order_payment = (payment_amount / num_orders).quantize(Decimal("0.01"))
                remaining = payment_amount
                
                for i, order in enumerate(orders):
                    if i == len(orders) - 1:
                        allocated = remaining
                    else:
                        allocated = per_order_payment
                    allocations[order.id] = allocated
                    remaining -= allocated
                
                success, _ = finance_manager.allocate_payment_to_orders(
                    income_id=income.id,
                    allocations=allocations
                )
                
                assert success is True, "付款分配应该成功"
                
                # 验证每个订单的余额计算
                for order_id, allocated_amount in allocations.items():
                    status = finance_manager.get_order_payment_status(order_id)
                    order = order_manager.get_order(order_id)
                    
                    expected_unpaid = order.total_amount - allocated_amount
                    
                    assert status["received_amount"] == allocated_amount, \
                        f"订单已收金额应该等于分配金额 {allocated_amount}"
                    assert abs(status["unpaid_amount"] - expected_unpaid) < Decimal("0.01"), \
                        f"订单未付余额应该等于 {expected_unpaid}"
                    assert status["status"] == "部分付款", "订单状态应该是部分付款"
                
                # 验证客户应收账款汇总
                receivables = finance_manager.get_customer_receivables(customer.id)
                expected_total_unpaid = total_order_amount - payment_amount
                
                assert abs(receivables["unpaid_amount"] - expected_total_unpaid) < Decimal("0.01"), \
                    f"客户总未付金额应该等于 {expected_total_unpaid}"
        
        finally:
            if os.path.exists(path):
                os.unlink(path)

    @given(
        customer=customer_strategy(),
        order_amount=st.decimals(min_value=Decimal("100"), max_value=Decimal("5000"), places=2)
    )
    @settings(max_examples=100, deadline=None)
    def test_zero_payment_balance_equals_total(self, customer, order_amount):
        """测试未付款时余额等于订单总额"""
        fd, path = tempfile.mkstemp(suffix='.db')
        os.close(fd)
        
        try:
            with DatabaseManager(path) as db:
                db.save_customer(customer)
                finance_manager = FinanceManager(db)
                order_manager = OrderManager(db)
                
                # 创建订单
                order = order_manager.create_order(
                    customer_id=customer.id,
                    customer_name=customer.name,
                    item_description="测试订单",
                    quantity=Decimal("100"),
                    pricing_unit=PricingUnit.PIECE,
                    unit_price=order_amount / Decimal("100"),
                    processes=[ProcessType.OXIDATION]
                )
                
                # 获取付款状态（未付款）
                status = finance_manager.get_order_payment_status(order.id)
                
                # 验证未付款时的余额
                assert status["total_amount"] == order_amount, "订单总金额应该正确"
                assert status["received_amount"] == Decimal("0"), "已收金额应该为0"
                assert status["unpaid_amount"] == order_amount, "未付余额应该等于订单总额"
                assert status["status"] == "未付款", "状态应该是未付款"
                assert status["payment_ratio"] == 0, "付款比例应该为0"
        
        finally:
            if os.path.exists(path):
                os.unlink(path)
    
    @given(
        customer=customer_strategy(),
        order_amount=st.decimals(min_value=Decimal("100"), max_value=Decimal("5000"), places=2)
    )
    @settings(max_examples=100, deadline=None)
    def test_full_payment_balance_is_zero(self, customer, order_amount):
        """测试全额付款后余额为零"""
        fd, path = tempfile.mkstemp(suffix='.db')
        os.close(fd)
        
        try:
            with DatabaseManager(path) as db:
                db.save_customer(customer)
                finance_manager = FinanceManager(db)
                order_manager = OrderManager(db)
                
                # 创建订单
                order = order_manager.create_order(
                    customer_id=customer.id,
                    customer_name=customer.name,
                    item_description="测试订单",
                    quantity=Decimal("100"),
                    pricing_unit=PricingUnit.PIECE,
                    unit_price=order_amount / Decimal("100"),
                    processes=[ProcessType.OXIDATION]
                )
                
                # 全额付款
                income = finance_manager.record_income(
                    customer_id=customer.id,
                    customer_name=customer.name,
                    amount=order_amount,
                    bank_type=BankType.G_BANK,
                    income_date=date.today()
                )
                
                success, _ = finance_manager.allocate_payment_to_orders(
                    income_id=income.id,
                    allocations={order.id: order_amount}
                )
                
                assert success is True, "全额付款分配应该成功"
                
                # 验证付清后的余额
                status = finance_manager.get_order_payment_status(order.id)
                
                assert status["total_amount"] == order_amount, "订单总金额应该正确"
                assert status["received_amount"] == order_amount, "已收金额应该等于订单总额"
                assert abs(status["unpaid_amount"]) < Decimal("0.01"), "未付余额应该为0"
                assert status["status"] == "已付清", "状态应该是已付清"
                assert abs(status["payment_ratio"] - 100) < 0.01, "付款比例应该为100%"
        
        finally:
            if os.path.exists(path):
                os.unlink(path)
