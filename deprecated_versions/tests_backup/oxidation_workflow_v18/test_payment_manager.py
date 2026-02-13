"""
Unit tests for PaymentManager

Tests payment recording with flexible payment-to-order matching:
- One payment linked to multiple orders (one-to-many)
- One order receiving multiple payments (many-to-one)
- Payment allocation and tracking

Requirements: 2.1, 2.2
"""

import pytest
import os
import tempfile
import shutil
from datetime import date, datetime
from decimal import Decimal

from oxidation_workflow_v18.models.core_models import (
    ProcessingOrder,
    OrderStatus,
    PricingUnit,
    TransactionType,
    TransactionStatus
)
from oxidation_workflow_v18.business.order_manager import ProcessingOrderManager
from oxidation_workflow_v18.business.payment_manager import PaymentManager


@pytest.fixture
def temp_data_dir():
    """创建临时数据目录"""
    temp_dir = tempfile.mkdtemp()
    yield temp_dir
    # 清理
    shutil.rmtree(temp_dir)


@pytest.fixture
def order_manager(temp_data_dir):
    """创建订单管理器实例"""
    return ProcessingOrderManager(data_dir=temp_data_dir)


@pytest.fixture
def payment_manager(temp_data_dir, order_manager):
    """创建付款管理器实例"""
    return PaymentManager(data_dir=temp_data_dir, order_manager=order_manager)


@pytest.fixture
def sample_orders(order_manager):
    """创建示例订单"""
    orders = []
    
    # 订单1: 1000元
    order1 = order_manager.create_order(
        "ORD001", "CUST001", date(2024, 1, 10),
        "产品A", PricingUnit.PIECE, Decimal("100"), Decimal("10")
    )
    orders.append(order1)
    
    # 订单2: 2000元
    order2 = order_manager.create_order(
        "ORD002", "CUST001", date(2024, 1, 15),
        "产品B", PricingUnit.PIECE, Decimal("200"), Decimal("10")
    )
    orders.append(order2)
    
    # 订单3: 1500元
    order3 = order_manager.create_order(
        "ORD003", "CUST002", date(2024, 1, 20),
        "产品C", PricingUnit.PIECE, Decimal("150"), Decimal("10")
    )
    orders.append(order3)
    
    return orders


class TestBasicPaymentRecording:
    """测试基本付款记录功能"""
    
    def test_record_simple_payment_without_allocation(self, payment_manager):
        """测试记录简单付款（不分配到订单）"""
        payment, success = payment_manager.record_payment(
            payment_date=date(2024, 1, 15),
            amount=Decimal("1000"),
            customer_id="CUST001",
            bank_account_id="BANK001",
            description="客户付款"
        )
        
        assert success is True
        assert payment.amount == Decimal("1000")
        assert payment.type == TransactionType.INCOME
        assert payment.status == TransactionStatus.COMPLETED
        assert payment.counterparty_id == "CUST001"
        assert payment.bank_account_id == "BANK001"
    
    def test_record_payment_with_single_order(self, payment_manager, sample_orders):
        """测试记录付款并分配到单个订单"""
        order = sample_orders[0]
        
        payment, success = payment_manager.record_payment(
            payment_date=date(2024, 1, 16),
            amount=Decimal("500"),
            customer_id="CUST001",
            bank_account_id="BANK001",
            order_allocations={order.id: Decimal("500")}
        )
        
        assert success is True
        assert payment.amount == Decimal("500")
        
        # 验证订单已收款金额更新
        updated_order = payment_manager.order_manager.get_order(order.id)
        assert updated_order.received_amount == Decimal("500")
    
    def test_payment_persistence(self, temp_data_dir, order_manager, sample_orders):
        """测试付款数据持久化"""
        manager1 = PaymentManager(data_dir=temp_data_dir, order_manager=order_manager)
        
        payment, _ = manager1.record_payment(
            payment_date=date(2024, 1, 15),
            amount=Decimal("1000"),
            customer_id="CUST001",
            bank_account_id="BANK001"
        )
        
        # 创建新的管理器实例，应该能加载之前保存的付款
        manager2 = PaymentManager(data_dir=temp_data_dir, order_manager=order_manager)
        loaded_payment = manager2.get_payment(payment.id)
        
        assert loaded_payment is not None
        assert loaded_payment.amount == Decimal("1000")


class TestOneToManyPayment:
    """测试一对多付款（一次付款关联多个订单）- Requirements 2.1"""
    
    def test_record_payment_to_multiple_orders(self, payment_manager, sample_orders):
        """测试一次付款分配到多个订单"""
        order1, order2 = sample_orders[0], sample_orders[1]
        
        # 一次付款3000元，分配到两个订单
        payment, success = payment_manager.record_payment(
            payment_date=date(2024, 1, 20),
            amount=Decimal("3000"),
            customer_id="CUST001",
            bank_account_id="BANK001",
            order_allocations={
                order1.id: Decimal("1000"),  # 订单1全额
                order2.id: Decimal("2000")   # 订单2全额
            }
        )
        
        assert success is True
        
        # 验证付款分配
        orders = payment_manager.get_payment_orders(payment.id)
        assert len(orders) == 2
        assert (order1.id, Decimal("1000")) in orders
        assert (order2.id, Decimal("2000")) in orders
        
        # 验证订单已收款金额
        updated_order1 = payment_manager.order_manager.get_order(order1.id)
        updated_order2 = payment_manager.order_manager.get_order(order2.id)
        assert updated_order1.received_amount == Decimal("1000")
        assert updated_order2.received_amount == Decimal("2000")
    
    def test_partial_allocation_to_multiple_orders(self, payment_manager, sample_orders):
        """测试部分付款分配到多个订单"""
        order1, order2 = sample_orders[0], sample_orders[1]
        
        # 一次付款2500元，部分分配到两个订单
        payment, success = payment_manager.record_payment(
            payment_date=date(2024, 1, 20),
            amount=Decimal("2500"),
            customer_id="CUST001",
            bank_account_id="BANK001",
            order_allocations={
                order1.id: Decimal("1000"),  # 订单1全额
                order2.id: Decimal("1000")   # 订单2部分
            }
        )
        
        assert success is True
        
        # 验证未分配金额
        unallocated = payment_manager.get_payment_unallocated_amount(payment.id)
        assert unallocated == Decimal("500")
    
    def test_allocate_existing_payment_to_orders(self, payment_manager, sample_orders):
        """测试将已有付款分配到订单"""
        order1, order2 = sample_orders[0], sample_orders[1]
        
        # 先记录未分配的付款
        payment, _ = payment_manager.record_payment(
            payment_date=date(2024, 1, 20),
            amount=Decimal("3000"),
            customer_id="CUST001",
            bank_account_id="BANK001"
        )
        
        # 后续分配到订单
        success = payment_manager.allocate_payment_to_orders(
            payment.id,
            {
                order1.id: Decimal("1000"),
                order2.id: Decimal("1500")
            }
        )
        
        assert success is True
        
        # 验证分配
        orders = payment_manager.get_payment_orders(payment.id)
        assert len(orders) == 2
        
        # 验证未分配金额
        unallocated = payment_manager.get_payment_unallocated_amount(payment.id)
        assert unallocated == Decimal("500")
    
    def test_over_allocation_raises_error(self, payment_manager, sample_orders):
        """测试超额分配抛出错误"""
        order1, order2 = sample_orders[0], sample_orders[1]
        
        # 尝试分配超过付款金额
        with pytest.raises(ValueError, match="超过付款金额"):
            payment_manager.record_payment(
                payment_date=date(2024, 1, 20),
                amount=Decimal("2000"),
                customer_id="CUST001",
                bank_account_id="BANK001",
                order_allocations={
                    order1.id: Decimal("1500"),
                    order2.id: Decimal("1000")  # 总计2500 > 2000
                }
            )


class TestManyToOnePayment:
    """测试多对一付款（一个订单分批收款）- Requirements 2.2"""
    
    def test_multiple_payments_to_single_order(self, payment_manager, sample_orders):
        """测试一个订单接收多笔付款"""
        order = sample_orders[0]  # 订单金额1000元
        
        # 第一笔付款300元
        payment1, _ = payment_manager.record_payment(
            payment_date=date(2024, 1, 15),
            amount=Decimal("300"),
            customer_id="CUST001",
            bank_account_id="BANK001",
            order_allocations={order.id: Decimal("300")}
        )
        
        # 第二笔付款400元
        payment2, _ = payment_manager.record_payment(
            payment_date=date(2024, 1, 20),
            amount=Decimal("400"),
            customer_id="CUST001",
            bank_account_id="BANK001",
            order_allocations={order.id: Decimal("400")}
        )
        
        # 第三笔付款300元
        payment3, _ = payment_manager.record_payment(
            payment_date=date(2024, 1, 25),
            amount=Decimal("300"),
            customer_id="CUST001",
            bank_account_id="BANK001",
            order_allocations={order.id: Decimal("300")}
        )
        
        # 验证订单收到3笔付款
        payments = payment_manager.get_order_payments(order.id)
        assert len(payments) == 3
        
        # 验证付款按日期排序
        assert payments[0][0].id == payment1.id
        assert payments[1][0].id == payment2.id
        assert payments[2][0].id == payment3.id
        
        # 验证分配金额
        assert payments[0][1] == Decimal("300")
        assert payments[1][1] == Decimal("400")
        assert payments[2][1] == Decimal("300")
        
        # 验证订单总收款
        total_received = payment_manager.get_order_total_received(order.id)
        assert total_received == Decimal("1000")
        
        # 验证订单已收款金额更新
        updated_order = payment_manager.order_manager.get_order(order.id)
        assert updated_order.received_amount == Decimal("1000")
    
    def test_partial_payments_to_order(self, payment_manager, sample_orders):
        """测试订单部分收款"""
        order = sample_orders[1]  # 订单金额2000元
        
        # 第一笔付款800元
        payment_manager.record_payment(
            payment_date=date(2024, 1, 15),
            amount=Decimal("800"),
            customer_id="CUST001",
            bank_account_id="BANK001",
            order_allocations={order.id: Decimal("800")}
        )
        
        # 第二笔付款600元
        payment_manager.record_payment(
            payment_date=date(2024, 1, 20),
            amount=Decimal("600"),
            customer_id="CUST001",
            bank_account_id="BANK001",
            order_allocations={order.id: Decimal("600")}
        )
        
        # 验证订单部分收款
        total_received = payment_manager.get_order_total_received(order.id)
        assert total_received == Decimal("1400")
        
        # 验证订单余额
        updated_order = payment_manager.order_manager.get_order(order.id)
        balance = updated_order.get_balance()
        assert balance == Decimal("600")  # 2000 - 1400


class TestPaymentQueries:
    """测试付款查询功能"""
    
    def test_get_unallocated_payments(self, payment_manager, sample_orders):
        """测试获取未完全分配的付款"""
        order = sample_orders[0]
        
        # 完全分配的付款
        payment_manager.record_payment(
            payment_date=date(2024, 1, 15),
            amount=Decimal("1000"),
            customer_id="CUST001",
            bank_account_id="BANK001",
            order_allocations={order.id: Decimal("1000")}
        )
        
        # 部分分配的付款
        payment_manager.record_payment(
            payment_date=date(2024, 1, 20),
            amount=Decimal("2000"),
            customer_id="CUST001",
            bank_account_id="BANK001",
            order_allocations={order.id: Decimal("500")}
        )
        
        # 未分配的付款
        payment_manager.record_payment(
            payment_date=date(2024, 1, 25),
            amount=Decimal("1500"),
            customer_id="CUST001",
            bank_account_id="BANK001"
        )
        
        # 获取未完全分配的付款
        unallocated = payment_manager.get_unallocated_payments()
        assert len(unallocated) == 2
        
        # 验证按日期降序排序
        assert unallocated[0].date > unallocated[1].date
    
    def test_get_payments_by_customer(self, payment_manager, sample_orders):
        """测试按客户查询付款"""
        # 客户1的付款
        payment_manager.record_payment(
            payment_date=date(2024, 1, 15),
            amount=Decimal("1000"),
            customer_id="CUST001",
            bank_account_id="BANK001"
        )
        payment_manager.record_payment(
            payment_date=date(2024, 1, 20),
            amount=Decimal("2000"),
            customer_id="CUST001",
            bank_account_id="BANK001"
        )
        
        # 客户2的付款
        payment_manager.record_payment(
            payment_date=date(2024, 1, 18),
            amount=Decimal("1500"),
            customer_id="CUST002",
            bank_account_id="BANK001"
        )
        
        # 查询客户1的付款
        cust1_payments = payment_manager.get_payments_by_customer("CUST001")
        assert len(cust1_payments) == 2
        assert all(p.counterparty_id == "CUST001" for p in cust1_payments)
        
        # 查询客户2的付款
        cust2_payments = payment_manager.get_payments_by_customer("CUST002")
        assert len(cust2_payments) == 1
        assert cust2_payments[0].counterparty_id == "CUST002"
    
    def test_get_payments_by_date_range(self, payment_manager):
        """测试按日期范围查询付款"""
        payment_manager.record_payment(
            payment_date=date(2024, 1, 10),
            amount=Decimal("1000"),
            customer_id="CUST001",
            bank_account_id="BANK001"
        )
        payment_manager.record_payment(
            payment_date=date(2024, 1, 20),
            amount=Decimal("2000"),
            customer_id="CUST001",
            bank_account_id="BANK001"
        )
        payment_manager.record_payment(
            payment_date=date(2024, 2, 5),
            amount=Decimal("1500"),
            customer_id="CUST001",
            bank_account_id="BANK001"
        )
        
        # 查询1月份的付款
        jan_payments = payment_manager.get_payments_by_date_range(
            date(2024, 1, 1),
            date(2024, 1, 31)
        )
        assert len(jan_payments) == 2
        assert all(date(2024, 1, 1) <= p.date <= date(2024, 1, 31) for p in jan_payments)


class TestComplexScenarios:
    """测试复杂场景"""
    
    def test_mixed_payment_scenarios(self, payment_manager, sample_orders):
        """测试混合付款场景（一对多和多对一同时存在）"""
        order1, order2, order3 = sample_orders
        
        # 场景1: 一笔付款分配到两个订单（一对多）
        payment1, _ = payment_manager.record_payment(
            payment_date=date(2024, 1, 15),
            amount=Decimal("3000"),
            customer_id="CUST001",
            bank_account_id="BANK001",
            order_allocations={
                order1.id: Decimal("1000"),
                order2.id: Decimal("2000")
            }
        )
        
        # 场景2: 订单3接收多笔付款（多对一）
        payment2, _ = payment_manager.record_payment(
            payment_date=date(2024, 1, 20),
            amount=Decimal("800"),
            customer_id="CUST002",
            bank_account_id="BANK001",
            order_allocations={order3.id: Decimal("800")}
        )
        
        payment3, _ = payment_manager.record_payment(
            payment_date=date(2024, 1, 25),
            amount=Decimal("700"),
            customer_id="CUST002",
            bank_account_id="BANK001",
            order_allocations={order3.id: Decimal("700")}
        )
        
        # 验证订单1和订单2的付款（一对多）
        order1_payments = payment_manager.get_order_payments(order1.id)
        order2_payments = payment_manager.get_order_payments(order2.id)
        assert len(order1_payments) == 1
        assert len(order2_payments) == 1
        assert order1_payments[0][0].id == payment1.id
        assert order2_payments[0][0].id == payment1.id
        
        # 验证订单3的付款（多对一）
        order3_payments = payment_manager.get_order_payments(order3.id)
        assert len(order3_payments) == 2
        assert order3_payments[0][0].id == payment2.id
        assert order3_payments[1][0].id == payment3.id
        
        # 验证订单收款金额
        assert payment_manager.get_order_total_received(order1.id) == Decimal("1000")
        assert payment_manager.get_order_total_received(order2.id) == Decimal("2000")
        assert payment_manager.get_order_total_received(order3.id) == Decimal("1500")
    
    def test_incremental_allocation(self, payment_manager, sample_orders):
        """测试增量分配（先记录付款，后续多次分配）"""
        order1, order2 = sample_orders[0], sample_orders[1]
        
        # 记录大额付款
        payment, _ = payment_manager.record_payment(
            payment_date=date(2024, 1, 15),
            amount=Decimal("5000"),
            customer_id="CUST001",
            bank_account_id="BANK001"
        )
        
        # 第一次分配
        payment_manager.allocate_payment_to_orders(
            payment.id,
            {order1.id: Decimal("1000")}
        )
        assert payment_manager.get_payment_unallocated_amount(payment.id) == Decimal("4000")
        
        # 第二次分配
        payment_manager.allocate_payment_to_orders(
            payment.id,
            {order2.id: Decimal("2000")}
        )
        assert payment_manager.get_payment_unallocated_amount(payment.id) == Decimal("2000")
        
        # 第三次分配（部分到订单2）
        payment_manager.allocate_payment_to_orders(
            payment.id,
            {order2.id: Decimal("1500")}
        )
        assert payment_manager.get_payment_unallocated_amount(payment.id) == Decimal("500")
        
        # 验证最终分配
        assert payment_manager.get_order_total_received(order1.id) == Decimal("1000")
        assert payment_manager.get_order_total_received(order2.id) == Decimal("3500")


class TestEdgeCases:
    """测试边界情况"""
    
    def test_zero_amount_allocation(self, payment_manager, sample_orders):
        """测试零金额分配（应该被忽略）"""
        order = sample_orders[0]
        
        payment, _ = payment_manager.record_payment(
            payment_date=date(2024, 1, 15),
            amount=Decimal("1000"),
            customer_id="CUST001",
            bank_account_id="BANK001",
            order_allocations={
                order.id: Decimal("0")  # 零金额
            }
        )
        
        # 零金额分配应该被忽略
        orders = payment_manager.get_payment_orders(payment.id)
        assert len(orders) == 0
        
        # 订单不应该有收款记录
        order_payments = payment_manager.get_order_payments(order.id)
        assert len(order_payments) == 0
    
    def test_get_nonexistent_payment(self, payment_manager):
        """测试获取不存在的付款"""
        payment = payment_manager.get_payment("INVALID_ID")
        assert payment is None
    
    def test_allocate_nonexistent_payment(self, payment_manager, sample_orders):
        """测试分配不存在的付款"""
        order = sample_orders[0]
        
        success = payment_manager.allocate_payment_to_orders(
            "INVALID_ID",
            {order.id: Decimal("100")}
        )
        assert success is False
    
    def test_empty_order_allocations(self, payment_manager):
        """测试空订单分配"""
        payment, success = payment_manager.record_payment(
            payment_date=date(2024, 1, 15),
            amount=Decimal("1000"),
            customer_id="CUST001",
            bank_account_id="BANK001",
            order_allocations={}  # 空字典
        )
        
        assert success is True
        # 应该没有分配记录
        orders = payment_manager.get_payment_orders(payment.id)
        assert len(orders) == 0
