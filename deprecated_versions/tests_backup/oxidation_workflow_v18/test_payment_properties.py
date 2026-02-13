"""
Property-based tests for payment matching persistence

Tests universal properties that should hold across all valid inputs
for payment-order matching and persistence.

Uses Hypothesis framework with 100+ iterations per property test.
"""

import pytest
from hypothesis import given, strategies as st, settings, assume
from datetime import date, datetime
from decimal import Decimal
from uuid import uuid4
import tempfile
import shutil

from oxidation_workflow_v18.models.core_models import (
    ProcessingOrder,
    OrderStatus,
    PricingUnit,
    TransactionType,
    TransactionStatus
)
from oxidation_workflow_v18.business.order_manager import ProcessingOrderManager
from oxidation_workflow_v18.business.payment_manager import PaymentManager


# ============================================================================
# Hypothesis Strategies
# ============================================================================

# Strategy for generating positive decimal amounts (0.01 to 10000)
amount_strategy = st.decimals(
    min_value=Decimal('0.01'),
    max_value=Decimal('10000'),
    allow_nan=False,
    allow_infinity=False,
    places=2
)

# Strategy for generating small amounts (0.01 to 5000)
small_amount_strategy = st.decimals(
    min_value=Decimal('0.01'),
    max_value=Decimal('5000'),
    allow_nan=False,
    allow_infinity=False,
    places=2
)

# Strategy for generating dates
date_strategy = st.dates(
    min_value=date(2024, 1, 1),
    max_value=date(2024, 12, 31)
)


# ============================================================================
# Helper Functions
# ============================================================================

def create_temp_managers():
    """
    Create temporary payment and order managers for testing.
    
    Returns:
        tuple: (temp_dir, order_manager, payment_manager)
    """
    temp_dir = tempfile.mkdtemp()
    order_manager = ProcessingOrderManager(data_dir=temp_dir)
    payment_manager = PaymentManager(data_dir=temp_dir, order_manager=order_manager)
    return temp_dir, order_manager, payment_manager


def cleanup_temp_dir(temp_dir: str):
    """Clean up temporary directory"""
    try:
        shutil.rmtree(temp_dir)
    except Exception:
        pass


def create_test_order(
    order_manager: ProcessingOrderManager,
    amount: Decimal,
    order_date: date = None
) -> ProcessingOrder:
    """
    Helper function to create a test order.
    
    Args:
        order_manager: The order manager instance
        amount: The order amount
        order_date: The order date (defaults to today)
    
    Returns:
        ProcessingOrder: A new order instance
    """
    if order_date is None:
        order_date = date.today()
    
    order_number = f"ORD-{uuid4().hex[:8].upper()}"
    customer_id = f"cust_{uuid4().hex[:8]}"
    
    return order_manager.create_order(
        order_number=order_number,
        customer_id=customer_id,
        order_date=order_date,
        product_name="测试产品",
        pricing_unit=PricingUnit.PIECE,
        quantity=Decimal("1"),
        unit_price=amount
    )


# ============================================================================
# Property 6: Payment Matching Persistence
# ============================================================================

@settings(max_examples=100)
@given(
    payment_amount=amount_strategy,
    order_amount=amount_strategy,
    payment_date=date_strategy
)
def test_property_6_simple_payment_matching_persistence(
    payment_amount: Decimal,
    order_amount: Decimal,
    payment_date: date
):
    """
    **Validates: Requirements 2.6**
    
    Property 6: Payment Matching Persistence (Simple Case)
    
    For any manual adjustment to payment-order matching, the new matching
    relationship should be persisted and retrievable.
    
    This property ensures:
    1. Payment-order matching is saved to persistent storage
    2. Matching can be retrieved after saving
    3. Matching survives manager restart (new instance)
    4. All matching details are preserved
    """
    temp_dir, order_manager, payment_manager = create_temp_managers()
    
    try:
        # Create an order
        order = create_test_order(order_manager, order_amount, payment_date)
        
        # Record a payment with allocation to the order
        allocated_amount = min(payment_amount, order_amount)
        
        payment, success = payment_manager.record_payment(
            payment_date=payment_date,
            amount=payment_amount,
            customer_id=order.customer_id,
            bank_account_id=f"bank_{uuid4().hex[:8]}",
            description="测试付款",
            order_allocations={order.id: allocated_amount}
        )
        
        assert success is True, "Payment recording should succeed"
        
        # Property 1: Payment should be retrievable immediately
        retrieved_payment = payment_manager.get_payment(payment.id)
        assert retrieved_payment is not None, "Payment should be retrievable"
        assert retrieved_payment.id == payment.id
        assert retrieved_payment.amount == payment_amount
        
        # Property 2: Payment-order matching should be retrievable
        payment_orders = payment_manager.get_payment_orders(payment.id)
        assert len(payment_orders) == 1, "Should have one order allocation"
        assert payment_orders[0][0] == order.id
        assert payment_orders[0][1] == allocated_amount
        
        # Property 3: Order should show the payment
        order_payments = payment_manager.get_order_payments(order.id)
        assert len(order_payments) == 1, "Order should have one payment"
        assert order_payments[0][0].id == payment.id
        assert order_payments[0][1] == allocated_amount
        
        # Property 4: Order received amount should be updated
        updated_order = order_manager.get_order(order.id)
        assert updated_order.received_amount == allocated_amount
        
        # Property 5: Matching should persist across manager restart
        # Create new manager instances (simulating restart)
        new_order_manager = ProcessingOrderManager(data_dir=temp_dir)
        new_payment_manager = PaymentManager(
            data_dir=temp_dir,
            order_manager=new_order_manager
        )
        
        # Retrieve payment from new manager
        persisted_payment = new_payment_manager.get_payment(payment.id)
        assert persisted_payment is not None, "Payment should persist"
        assert persisted_payment.amount == payment_amount
        
        # Retrieve matching from new manager
        persisted_payment_orders = new_payment_manager.get_payment_orders(payment.id)
        assert len(persisted_payment_orders) == 1, "Matching should persist"
        assert persisted_payment_orders[0][0] == order.id
        assert persisted_payment_orders[0][1] == allocated_amount
        
        # Retrieve order payments from new manager
        persisted_order_payments = new_payment_manager.get_order_payments(order.id)
        assert len(persisted_order_payments) == 1, "Order payments should persist"
        assert persisted_order_payments[0][0].id == payment.id
        assert persisted_order_payments[0][1] == allocated_amount
        
        # Retrieve order from new manager
        persisted_order = new_order_manager.get_order(order.id)
        assert persisted_order.received_amount == allocated_amount
        
    finally:
        cleanup_temp_dir(temp_dir)


@settings(max_examples=100)
@given(
    payment_amount=amount_strategy,
    order_amounts=st.lists(small_amount_strategy, min_size=2, max_size=5),
    payment_date=date_strategy
)
def test_property_6_one_to_many_matching_persistence(
    payment_amount: Decimal,
    order_amounts: list,
    payment_date: date
):
    """
    **Validates: Requirements 2.6**
    
    Property 6 (Extended): One-to-Many Matching Persistence
    
    When a single payment is matched to multiple orders, all matching
    relationships should be persisted and retrievable.
    """
    temp_dir, order_manager, payment_manager = create_temp_managers()
    
    try:
        # Normalize order amounts to not exceed payment amount
        total_orders = sum(order_amounts)
        assume(total_orders > Decimal('0'))
        
        normalized_amounts = [
            (amount / total_orders) * payment_amount
            for amount in order_amounts
        ]
        
        # Ensure we don't exceed payment amount due to rounding
        total_allocated = sum(normalized_amounts)
        if total_allocated > payment_amount:
            normalized_amounts[-1] -= (total_allocated - payment_amount)
        
        # Create orders
        orders = []
        order_allocations = {}
        for amount in normalized_amounts:
            order = create_test_order(order_manager, amount, payment_date)
            orders.append(order)
            order_allocations[order.id] = amount
        
        # Record payment with multiple order allocations
        payment, success = payment_manager.record_payment(
            payment_date=payment_date,
            amount=payment_amount,
            customer_id=orders[0].customer_id,
            bank_account_id=f"bank_{uuid4().hex[:8]}",
            description="一对多付款",
            order_allocations=order_allocations
        )
        
        assert success is True
        
        # Property 1: All matching relationships should be retrievable
        payment_orders = payment_manager.get_payment_orders(payment.id)
        assert len(payment_orders) == len(orders), (
            f"Should have {len(orders)} order allocations"
        )
        
        # Property 2: Each order should show the payment
        for order in orders:
            order_payments = payment_manager.get_order_payments(order.id)
            assert len(order_payments) == 1
            assert order_payments[0][0].id == payment.id
        
        # Property 3: All matching should persist across restart
        new_order_manager = ProcessingOrderManager(data_dir=temp_dir)
        new_payment_manager = PaymentManager(
            data_dir=temp_dir,
            order_manager=new_order_manager
        )
        
        persisted_payment_orders = new_payment_manager.get_payment_orders(payment.id)
        assert len(persisted_payment_orders) == len(orders), (
            "All matching relationships should persist"
        )
        
        # Verify each allocation persisted correctly
        for order_id, allocated_amount in order_allocations.items():
            found = False
            for persisted_order_id, persisted_amount in persisted_payment_orders:
                if persisted_order_id == order_id:
                    assert persisted_amount == allocated_amount, (
                        f"Allocated amount should persist correctly"
                    )
                    found = True
                    break
            assert found, f"Order {order_id} allocation should persist"
        
    finally:
        cleanup_temp_dir(temp_dir)


@settings(max_examples=100)
@given(
    payment_amounts=st.lists(small_amount_strategy, min_size=2, max_size=5),
    order_amount=amount_strategy,
    payment_date=date_strategy
)
def test_property_6_many_to_one_matching_persistence(
    payment_amounts: list,
    order_amount: Decimal,
    payment_date: date
):
    """
    **Validates: Requirements 2.6**
    
    Property 6 (Extended): Many-to-One Matching Persistence
    
    When multiple payments are matched to a single order, all matching
    relationships should be persisted and retrievable.
    """
    temp_dir, order_manager, payment_manager = create_temp_managers()
    
    try:
        # Normalize payment amounts to not exceed order amount
        total_payments = sum(payment_amounts)
        assume(total_payments > Decimal('0'))
        
        normalized_payments = [
            (amount / total_payments) * order_amount
            for amount in payment_amounts
        ]
        
        # Create a single order
        order = create_test_order(order_manager, order_amount, payment_date)
        
        # Record multiple payments for the order
        payments = []
        for i, payment_amount in enumerate(normalized_payments):
            payment, success = payment_manager.record_payment(
                payment_date=payment_date,
                amount=payment_amount,
                customer_id=order.customer_id,
                bank_account_id=f"bank_{uuid4().hex[:8]}",
                description=f"多对一付款 {i+1}",
                order_allocations={order.id: payment_amount}
            )
            assert success is True
            payments.append(payment)
        
        # Property 1: Order should show all payments
        order_payments = payment_manager.get_order_payments(order.id)
        assert len(order_payments) == len(payments), (
            f"Order should have {len(payments)} payments"
        )
        
        # Property 2: Each payment should show the order
        for payment in payments:
            payment_orders = payment_manager.get_payment_orders(payment.id)
            assert len(payment_orders) == 1
            assert payment_orders[0][0] == order.id
        
        # Property 3: Total received should equal sum of payments
        total_received = payment_manager.get_order_total_received(order.id)
        expected_total = sum(normalized_payments)
        assert abs(total_received - expected_total) < Decimal('0.01')
        
        # Property 4: All matching should persist across restart
        new_order_manager = ProcessingOrderManager(data_dir=temp_dir)
        new_payment_manager = PaymentManager(
            data_dir=temp_dir,
            order_manager=new_order_manager
        )
        
        persisted_order_payments = new_payment_manager.get_order_payments(order.id)
        assert len(persisted_order_payments) == len(payments), (
            "All payment relationships should persist"
        )
        
        # Verify each payment persisted correctly
        persisted_payment_ids = {p[0].id for p in persisted_order_payments}
        original_payment_ids = {p.id for p in payments}
        assert persisted_payment_ids == original_payment_ids, (
            "All payment IDs should persist"
        )
        
        # Verify total received persisted
        persisted_total = new_payment_manager.get_order_total_received(order.id)
        assert abs(persisted_total - expected_total) < Decimal('0.01')
        
    finally:
        cleanup_temp_dir(temp_dir)


@settings(max_examples=100)
@given(
    initial_amount=small_amount_strategy,
    additional_amount=small_amount_strategy,
    payment_date=date_strategy
)
def test_property_6_incremental_allocation_persistence(
    initial_amount: Decimal,
    additional_amount: Decimal,
    payment_date: date
):
    """
    **Validates: Requirements 2.6**
    
    Property 6 (Extended): Incremental Allocation Persistence
    
    When payment allocations are adjusted incrementally (first allocate
    some amount, then allocate more), all adjustments should be persisted.
    """
    temp_dir, order_manager, payment_manager = create_temp_managers()
    
    try:
        total_payment = initial_amount + additional_amount
        
        # Create two orders
        order1 = create_test_order(order_manager, initial_amount, payment_date)
        order2 = create_test_order(order_manager, additional_amount, payment_date)
        
        # Record payment without initial allocation
        payment, success = payment_manager.record_payment(
            payment_date=payment_date,
            amount=total_payment,
            customer_id=order1.customer_id,
            bank_account_id=f"bank_{uuid4().hex[:8]}",
            description="增量分配付款"
        )
        
        assert success is True
        
        # Property 1: Initial state - no allocations
        payment_orders = payment_manager.get_payment_orders(payment.id)
        assert len(payment_orders) == 0
        
        # First allocation to order1
        success = payment_manager.allocate_payment_to_orders(
            payment.id,
            {order1.id: initial_amount}
        )
        assert success is True
        
        # Property 2: First allocation should persist
        new_payment_manager1 = PaymentManager(
            data_dir=temp_dir,
            order_manager=ProcessingOrderManager(data_dir=temp_dir)
        )
        
        persisted_orders1 = new_payment_manager1.get_payment_orders(payment.id)
        assert len(persisted_orders1) == 1
        assert persisted_orders1[0][0] == order1.id
        assert persisted_orders1[0][1] == initial_amount
        
        # Second allocation to order2
        success = payment_manager.allocate_payment_to_orders(
            payment.id,
            {order2.id: additional_amount}
        )
        assert success is True
        
        # Property 3: Both allocations should persist
        new_payment_manager2 = PaymentManager(
            data_dir=temp_dir,
            order_manager=ProcessingOrderManager(data_dir=temp_dir)
        )
        
        persisted_orders2 = new_payment_manager2.get_payment_orders(payment.id)
        assert len(persisted_orders2) == 2, "Both allocations should persist"
        
        # Verify both allocations
        allocation_dict = {oid: amt for oid, amt in persisted_orders2}
        assert order1.id in allocation_dict
        assert order2.id in allocation_dict
        assert allocation_dict[order1.id] == initial_amount
        assert allocation_dict[order2.id] == additional_amount
        
    finally:
        cleanup_temp_dir(temp_dir)


@settings(max_examples=100)
@given(
    payment_amount=amount_strategy,
    order_amount=amount_strategy,
    payment_date=date_strategy
)
def test_property_6_unallocated_amount_persistence(
    payment_amount: Decimal,
    order_amount: Decimal,
    payment_date: date
):
    """
    **Validates: Requirements 2.6**
    
    Property 6 (Extended): Unallocated Amount Persistence
    
    When a payment is partially allocated, the unallocated amount
    calculation should be consistent after persistence.
    """
    temp_dir, order_manager, payment_manager = create_temp_managers()
    
    try:
        # Ensure payment is larger than order
        if payment_amount <= order_amount:
            payment_amount = order_amount + Decimal('100')
        
        # Create order
        order = create_test_order(order_manager, order_amount, payment_date)
        
        # Record payment with partial allocation
        allocated_amount = order_amount
        
        payment, success = payment_manager.record_payment(
            payment_date=payment_date,
            amount=payment_amount,
            customer_id=order.customer_id,
            bank_account_id=f"bank_{uuid4().hex[:8]}",
            description="部分分配付款",
            order_allocations={order.id: allocated_amount}
        )
        
        assert success is True
        
        # Property 1: Unallocated amount should be correct
        unallocated = payment_manager.get_payment_unallocated_amount(payment.id)
        expected_unallocated = payment_amount - allocated_amount
        assert unallocated == expected_unallocated
        
        # Property 2: Unallocated amount should persist
        new_payment_manager = PaymentManager(
            data_dir=temp_dir,
            order_manager=ProcessingOrderManager(data_dir=temp_dir)
        )
        
        persisted_unallocated = new_payment_manager.get_payment_unallocated_amount(
            payment.id
        )
        assert persisted_unallocated == expected_unallocated, (
            "Unallocated amount should persist correctly"
        )
        
        # Property 3: Payment should appear in unallocated list
        unallocated_payments = new_payment_manager.get_unallocated_payments()
        payment_ids = [p.id for p in unallocated_payments]
        assert payment.id in payment_ids, (
            "Partially allocated payment should appear in unallocated list"
        )
        
    finally:
        cleanup_temp_dir(temp_dir)


@settings(max_examples=100)
@given(
    payment_amounts=st.lists(small_amount_strategy, min_size=2, max_size=4),
    order_amounts=st.lists(small_amount_strategy, min_size=2, max_size=4),
    payment_date=date_strategy
)
def test_property_6_complex_matching_persistence(
    payment_amounts: list,
    order_amounts: list,
    payment_date: date
):
    """
    **Validates: Requirements 2.6**
    
    Property 6 (Extended): Complex Matching Persistence
    
    For complex scenarios with multiple payments and orders, all matching
    relationships should be persisted correctly.
    """
    temp_dir, order_manager, payment_manager = create_temp_managers()
    
    try:
        # Create orders
        orders = []
        for amount in order_amounts:
            order = create_test_order(order_manager, amount, payment_date)
            orders.append(order)
        
        # Create payments with various allocations
        payments = []
        for i, payment_amount in enumerate(payment_amounts):
            # Allocate to one or more orders
            order_allocations = {}
            
            if i < len(orders):
                # Allocate to corresponding order
                allocated = min(payment_amount, order_amounts[i])
                order_allocations[orders[i].id] = allocated
            
            payment, success = payment_manager.record_payment(
                payment_date=payment_date,
                amount=payment_amount,
                customer_id=orders[0].customer_id,
                bank_account_id=f"bank_{uuid4().hex[:8]}",
                description=f"复杂匹配付款 {i+1}",
                order_allocations=order_allocations
            )
            
            assert success is True
            payments.append(payment)
        
        # Collect all matching relationships before restart
        original_matches = {}
        for payment in payments:
            original_matches[payment.id] = payment_manager.get_payment_orders(payment.id)
        
        original_order_payments = {}
        for order in orders:
            original_order_payments[order.id] = payment_manager.get_order_payments(order.id)
        
        # Property: All matching relationships should persist
        new_order_manager = ProcessingOrderManager(data_dir=temp_dir)
        new_payment_manager = PaymentManager(
            data_dir=temp_dir,
            order_manager=new_order_manager
        )
        
        # Verify payment-to-order matches persisted
        for payment_id, original_orders in original_matches.items():
            persisted_orders = new_payment_manager.get_payment_orders(payment_id)
            assert len(persisted_orders) == len(original_orders), (
                f"Payment {payment_id} should have same number of order matches"
            )
            
            # Convert to sets for comparison
            original_set = {(oid, amt) for oid, amt in original_orders}
            persisted_set = {(oid, amt) for oid, amt in persisted_orders}
            assert original_set == persisted_set, (
                "Payment-to-order matches should be identical after persistence"
            )
        
        # Verify order-to-payment matches persisted
        for order_id, original_payments in original_order_payments.items():
            persisted_payments = new_payment_manager.get_order_payments(order_id)
            assert len(persisted_payments) == len(original_payments), (
                f"Order {order_id} should have same number of payment matches"
            )
            
            # Compare payment IDs and amounts
            original_set = {(p.id, amt) for p, amt in original_payments}
            persisted_set = {(p.id, amt) for p, amt in persisted_payments}
            assert original_set == persisted_set, (
                "Order-to-payment matches should be identical after persistence"
            )
        
    finally:
        cleanup_temp_dir(temp_dir)
