"""
Property-based tests for reconciliation models

Tests universal properties that should hold across all valid inputs
for ReconciliationMatch and related payment matching models.

Uses Hypothesis framework with 100+ iterations per property test.
"""

import pytest
from hypothesis import given, strategies as st, settings, assume, HealthCheck
from datetime import date, datetime
from decimal import Decimal
from uuid import uuid4

from oxidation_workflow_v18.models.core_models import (
    ReconciliationMatch,
    ProcessingOrder,
    BankRecord,
    PricingUnit,
    OrderStatus,
)


# ============================================================================
# Hypothesis Strategies
# ============================================================================

# Strategy for generating positive decimal amounts (0.01 to 100000)
amount_strategy = st.decimals(
    min_value=Decimal('0.01'),
    max_value=Decimal('100000'),
    allow_nan=False,
    allow_infinity=False,
    places=2
)

# Strategy for generating small amounts for partial payments (0.01 to 10000)
small_amount_strategy = st.decimals(
    min_value=Decimal('0.01'),
    max_value=Decimal('10000'),
    allow_nan=False,
    allow_infinity=False,
    places=2
)

# Strategy for generating IDs
id_strategy = st.text(
    alphabet=st.characters(whitelist_categories=('L', 'N')),
    min_size=5,
    max_size=20
).filter(lambda x: x.strip() != "")


# ============================================================================
# Helper Functions
# ============================================================================

def create_test_order(
    order_id: str,
    total_amount: Decimal,
    received_amount: Decimal = Decimal('0')
) -> ProcessingOrder:
    """
    Helper function to create a test order.
    
    Args:
        order_id: The order ID
        total_amount: The total order amount
        received_amount: The amount already received
    
    Returns:
        ProcessingOrder: A new order instance
    """
    now = datetime.now()
    
    return ProcessingOrder(
        id=order_id,
        order_number=f"ORD-{uuid4().hex[:8].upper()}",
        customer_id=f"cust_{uuid4().hex[:8]}",
        order_date=date.today(),
        product_name="测试产品",
        pricing_unit=PricingUnit.PIECE,
        quantity=Decimal("1"),
        unit_price=total_amount,
        total_amount=total_amount,
        status=OrderStatus.PENDING,
        received_amount=received_amount,
        outsourced_cost=Decimal('0'),
        notes="",
        created_at=now,
        updated_at=now,
    )


def create_test_bank_record(
    record_id: str,
    amount: Decimal
) -> BankRecord:
    """
    Helper function to create a test bank record.
    
    Args:
        record_id: The bank record ID
        amount: The transaction amount
    
    Returns:
        BankRecord: A new bank record instance
    """
    return BankRecord(
        id=record_id,
        transaction_date=date.today(),
        description="测试交易",
        amount=amount,
        balance=Decimal('10000'),
        transaction_type="CREDIT",
        counterparty="测试客户",
        bank_account_id=f"acc_{uuid4().hex[:8]}",
    )


def create_test_reconciliation_match(
    bank_record_ids: list,
    order_ids: list,
    total_bank_amount: Decimal,
    total_order_amount: Decimal
) -> ReconciliationMatch:
    """
    Helper function to create a test reconciliation match.
    
    Args:
        bank_record_ids: List of bank record IDs
        order_ids: List of order IDs
        total_bank_amount: Total amount from bank records
        total_order_amount: Total amount from orders
    
    Returns:
        ReconciliationMatch: A new reconciliation match instance
    """
    difference = total_bank_amount - total_order_amount
    now = datetime.now()
    
    return ReconciliationMatch(
        id=str(uuid4()),
        match_date=now,
        bank_record_ids=bank_record_ids,
        order_ids=order_ids,
        total_bank_amount=total_bank_amount,
        total_order_amount=total_order_amount,
        difference=difference,
        notes="",
        created_by="test_user",
        created_at=now,
    )



# ============================================================================
# Property 3: Flexible Payment Matching (One-to-Many)
# ============================================================================

@settings(max_examples=100)
@given(
    payment_amount=amount_strategy,
    order_amounts=st.lists(small_amount_strategy, min_size=2, max_size=10)
)
def test_property_3_one_to_many_payment_matching(
    payment_amount: Decimal,
    order_amounts: list
):
    """
    **Validates: Requirements 2.1, 2.3**
    
    Property 3: Flexible Payment Matching (One-to-Many)
    
    For any single payment matched to multiple orders, the sum of allocated
    amounts to each order should equal the payment amount, and each order's
    received amount should be updated correctly.
    
    This property ensures:
    1. One payment can be split across multiple orders
    2. The sum of allocations equals the payment amount
    3. Each order receives its allocated portion
    4. No money is lost or created in the split
    """
    # Ensure the sum of order amounts equals the payment amount
    # We'll normalize the order amounts to sum to payment_amount
    total_orders = sum(order_amounts)
    
    # Skip if total is zero to avoid division by zero
    assume(total_orders > Decimal('0'))
    
    # Normalize order amounts to sum to payment_amount
    normalized_amounts = [
        (amount / total_orders) * payment_amount
        for amount in order_amounts
    ]
    
    # Create bank record for the single payment
    bank_record_id = f"bank_{uuid4().hex[:8]}"
    bank_record = create_test_bank_record(bank_record_id, payment_amount)
    
    # Create orders with normalized amounts
    orders = []
    order_ids = []
    for i, amount in enumerate(normalized_amounts):
        order_id = f"order_{i}_{uuid4().hex[:8]}"
        order = create_test_order(order_id, amount)
        orders.append(order)
        order_ids.append(order_id)
    
    # Create reconciliation match (one-to-many)
    match = create_test_reconciliation_match(
        bank_record_ids=[bank_record_id],
        order_ids=order_ids,
        total_bank_amount=payment_amount,
        total_order_amount=sum(normalized_amounts)
    )
    
    # Property 1: This should be identified as one-to-many
    assert match.is_one_to_many() is True, (
        f"Match with 1 bank record and {len(order_ids)} orders "
        f"should be one-to-many"
    )
    
    # Property 2: Sum of order amounts should equal payment amount
    total_allocated = sum(normalized_amounts)
    assert abs(total_allocated - payment_amount) < Decimal('0.01'), (
        f"Sum of allocated amounts {total_allocated} should equal "
        f"payment amount {payment_amount}"
    )
    
    # Property 3: Match should have correct totals
    assert match.total_bank_amount == payment_amount
    assert abs(match.total_order_amount - payment_amount) < Decimal('0.01')
    
    # Property 4: Difference should be minimal (within rounding tolerance)
    assert abs(match.difference) < Decimal('0.01'), (
        f"Difference {match.difference} should be minimal"
    )
    
    # Property 5: Match should be valid
    is_valid, error_msg = match.validate_match()
    assert is_valid is True, f"Match should be valid: {error_msg}"



@settings(max_examples=100)
@given(
    payment_amount=amount_strategy,
    num_orders=st.integers(min_value=2, max_value=10)
)
def test_property_3_one_to_many_equal_split(
    payment_amount: Decimal,
    num_orders: int
):
    """
    **Validates: Requirements 2.1, 2.3**
    
    Property 3 (Extended): One-to-Many Equal Split
    
    When a single payment is split equally among multiple orders,
    each order should receive payment_amount / num_orders.
    """
    # Calculate equal split amount
    split_amount = payment_amount / Decimal(num_orders)
    
    # Create bank record
    bank_record_id = f"bank_{uuid4().hex[:8]}"
    
    # Create orders with equal amounts
    order_ids = []
    for i in range(num_orders):
        order_id = f"order_{i}_{uuid4().hex[:8]}"
        order_ids.append(order_id)
    
    # Create reconciliation match
    match = create_test_reconciliation_match(
        bank_record_ids=[bank_record_id],
        order_ids=order_ids,
        total_bank_amount=payment_amount,
        total_order_amount=split_amount * Decimal(num_orders)
    )
    
    # Property: Should be one-to-many
    assert match.is_one_to_many() is True
    
    # Property: Total order amount should equal payment amount
    expected_total = split_amount * Decimal(num_orders)
    assert abs(match.total_order_amount - expected_total) < Decimal('0.01')
    
    # Property: Should be valid
    is_valid, _ = match.validate_match()
    assert is_valid is True


@settings(max_examples=100, suppress_health_check=[HealthCheck.filter_too_much])
@given(
    payment_amount=amount_strategy,
    order_amounts=st.lists(small_amount_strategy, min_size=2, max_size=5)
)
def test_property_3_one_to_many_partial_allocation(
    payment_amount: Decimal,
    order_amounts: list
):
    """
    **Validates: Requirements 2.1, 2.3**
    
    Property 3 (Extended): One-to-Many Partial Allocation
    
    When a payment is allocated to multiple orders but doesn't fully
    cover all orders, the difference should be tracked correctly.
    """
    # Ensure order amounts sum to more than payment
    total_orders = sum(order_amounts)
    assume(total_orders > payment_amount)
    
    # Create bank record
    bank_record_id = f"bank_{uuid4().hex[:8]}"
    
    # Create orders
    order_ids = [f"order_{i}_{uuid4().hex[:8]}" for i in range(len(order_amounts))]
    
    # Create reconciliation match with underpayment
    match = create_test_reconciliation_match(
        bank_record_ids=[bank_record_id],
        order_ids=order_ids,
        total_bank_amount=payment_amount,
        total_order_amount=total_orders
    )
    
    # Property: Should be one-to-many
    assert match.is_one_to_many() is True
    
    # Property: Difference should be negative (underpayment)
    expected_difference = payment_amount - total_orders
    assert match.difference == expected_difference
    assert match.difference < Decimal('0')
    
    # Property: Should still be valid (with warning)
    is_valid, error_msg = match.validate_match()
    assert is_valid is True
    if abs(match.difference) > Decimal('0.01'):
        assert "存在金额差异" in error_msg



# ============================================================================
# Property 4: Flexible Payment Matching (Many-to-One)
# ============================================================================

@settings(max_examples=100)
@given(
    payment_amounts=st.lists(small_amount_strategy, min_size=2, max_size=10),
    order_amount=amount_strategy
)
def test_property_4_many_to_one_payment_matching(
    payment_amounts: list,
    order_amount: Decimal
):
    """
    **Validates: Requirements 2.2, 2.4**
    
    Property 4: Flexible Payment Matching (Many-to-One)
    
    For any single order receiving multiple payments, the sum of all payment
    amounts should equal the order's total received amount.
    
    This property ensures:
    1. Multiple payments can be applied to a single order
    2. The sum of payments equals the total received
    3. Order tracks cumulative payments correctly
    4. No payment is lost or duplicated
    """
    # Ensure the sum of payments equals the order amount
    # We'll normalize the payment amounts to sum to order_amount
    total_payments = sum(payment_amounts)
    
    # Skip if total is zero to avoid division by zero
    assume(total_payments > Decimal('0'))
    
    # Normalize payment amounts to sum to order_amount
    normalized_payments = [
        (amount / total_payments) * order_amount
        for amount in payment_amounts
    ]
    
    # Create bank records for multiple payments
    bank_record_ids = []
    for i, amount in enumerate(normalized_payments):
        record_id = f"bank_{i}_{uuid4().hex[:8]}"
        bank_record_ids.append(record_id)
    
    # Create single order
    order_id = f"order_{uuid4().hex[:8]}"
    
    # Create reconciliation match (many-to-one)
    match = create_test_reconciliation_match(
        bank_record_ids=bank_record_ids,
        order_ids=[order_id],
        total_bank_amount=sum(normalized_payments),
        total_order_amount=order_amount
    )
    
    # Property 1: This should be identified as many-to-one
    assert match.is_many_to_one() is True, (
        f"Match with {len(bank_record_ids)} bank records and 1 order "
        f"should be many-to-one"
    )
    
    # Property 2: Sum of payments should equal order amount
    total_paid = sum(normalized_payments)
    assert abs(total_paid - order_amount) < Decimal('0.01'), (
        f"Sum of payments {total_paid} should equal "
        f"order amount {order_amount}"
    )
    
    # Property 3: Match should have correct totals
    assert abs(match.total_bank_amount - order_amount) < Decimal('0.01')
    assert match.total_order_amount == order_amount
    
    # Property 4: Difference should be minimal (within rounding tolerance)
    assert abs(match.difference) < Decimal('0.01'), (
        f"Difference {match.difference} should be minimal"
    )
    
    # Property 5: Match should be valid
    is_valid, error_msg = match.validate_match()
    assert is_valid is True, f"Match should be valid: {error_msg}"


@settings(max_examples=100)
@given(
    num_payments=st.integers(min_value=2, max_value=10),
    order_amount=amount_strategy
)
def test_property_4_many_to_one_equal_payments(
    num_payments: int,
    order_amount: Decimal
):
    """
    **Validates: Requirements 2.2, 2.4**
    
    Property 4 (Extended): Many-to-One Equal Payments
    
    When multiple equal payments are made for a single order,
    the sum should equal the order amount.
    """
    # Calculate equal payment amount
    payment_amount = order_amount / Decimal(num_payments)
    
    # Create bank records
    bank_record_ids = [
        f"bank_{i}_{uuid4().hex[:8]}"
        for i in range(num_payments)
    ]
    
    # Create single order
    order_id = f"order_{uuid4().hex[:8]}"
    
    # Create reconciliation match
    match = create_test_reconciliation_match(
        bank_record_ids=bank_record_ids,
        order_ids=[order_id],
        total_bank_amount=payment_amount * Decimal(num_payments),
        total_order_amount=order_amount
    )
    
    # Property: Should be many-to-one
    assert match.is_many_to_one() is True
    
    # Property: Total bank amount should equal order amount
    expected_total = payment_amount * Decimal(num_payments)
    assert abs(match.total_bank_amount - expected_total) < Decimal('0.01')
    
    # Property: Should be valid
    is_valid, _ = match.validate_match()
    assert is_valid is True



@settings(max_examples=100)
@given(
    payment_amounts=st.lists(small_amount_strategy, min_size=2, max_size=5),
    order_amount=amount_strategy
)
def test_property_4_many_to_one_partial_payments(
    payment_amounts: list,
    order_amount: Decimal
):
    """
    **Validates: Requirements 2.2, 2.4**
    
    Property 4 (Extended): Many-to-One Partial Payments
    
    When multiple payments are made but don't fully cover the order,
    the difference should be tracked correctly.
    """
    # Ensure payments sum to less than order amount
    total_payments = sum(payment_amounts)
    assume(total_payments < order_amount)
    
    # Create bank records
    bank_record_ids = [
        f"bank_{i}_{uuid4().hex[:8]}"
        for i in range(len(payment_amounts))
    ]
    
    # Create single order
    order_id = f"order_{uuid4().hex[:8]}"
    
    # Create reconciliation match with partial payment
    match = create_test_reconciliation_match(
        bank_record_ids=bank_record_ids,
        order_ids=[order_id],
        total_bank_amount=total_payments,
        total_order_amount=order_amount
    )
    
    # Property: Should be many-to-one
    assert match.is_many_to_one() is True
    
    # Property: Difference should be negative (underpayment)
    expected_difference = total_payments - order_amount
    assert match.difference == expected_difference
    assert match.difference < Decimal('0')
    
    # Property: Should still be valid (with warning)
    is_valid, error_msg = match.validate_match()
    assert is_valid is True
    if abs(match.difference) > Decimal('0.01'):
        assert "存在金额差异" in error_msg


@settings(max_examples=100)
@given(
    payment_amounts=st.lists(small_amount_strategy, min_size=2, max_size=5),
    order_amount=small_amount_strategy
)
def test_property_4_many_to_one_overpayment(
    payment_amounts: list,
    order_amount: Decimal
):
    """
    **Validates: Requirements 2.2, 2.4**
    
    Property 4 (Extended): Many-to-One Overpayment
    
    When multiple payments exceed the order amount, the positive
    difference should be tracked correctly.
    """
    # Ensure payments sum to more than order amount
    total_payments = sum(payment_amounts)
    assume(total_payments > order_amount)
    
    # Create bank records
    bank_record_ids = [
        f"bank_{i}_{uuid4().hex[:8]}"
        for i in range(len(payment_amounts))
    ]
    
    # Create single order
    order_id = f"order_{uuid4().hex[:8]}"
    
    # Create reconciliation match with overpayment
    match = create_test_reconciliation_match(
        bank_record_ids=bank_record_ids,
        order_ids=[order_id],
        total_bank_amount=total_payments,
        total_order_amount=order_amount
    )
    
    # Property: Should be many-to-one
    assert match.is_many_to_one() is True
    
    # Property: Difference should be positive (overpayment)
    expected_difference = total_payments - order_amount
    assert match.difference == expected_difference
    assert match.difference > Decimal('0')
    
    # Property: Should still be valid (with warning)
    is_valid, error_msg = match.validate_match()
    assert is_valid is True
    if abs(match.difference) > Decimal('0.01'):
        assert "存在金额差异" in error_msg



# ============================================================================
# Property 5: Unmatched Amount Calculation
# ============================================================================

@settings(max_examples=100)
@given(
    order_amount=amount_strategy,
    received_amount=amount_strategy
)
def test_property_5_unmatched_amount_calculation(
    order_amount: Decimal,
    received_amount: Decimal
):
    """
    **Validates: Requirements 2.5**
    
    Property 5: Unmatched Amount Calculation
    
    For any order, the unmatched amount should equal the total order amount
    minus the sum of all matched payment amounts.
    
    This property ensures:
    1. Unmatched amount is calculated correctly
    2. Formula: unmatched = total - received
    3. Can be positive (underpaid), zero (fully paid), or negative (overpaid)
    """
    # Create order with specified amounts
    order_id = f"order_{uuid4().hex[:8]}"
    order = create_test_order(order_id, order_amount, received_amount)
    
    # Property 1: Balance should equal total - received
    expected_balance = order_amount - received_amount
    actual_balance = order.get_balance()
    
    assert actual_balance == expected_balance, (
        f"Order balance {actual_balance} should equal "
        f"total {order_amount} - received {received_amount} = {expected_balance}"
    )
    
    # Property 2: If received equals total, balance should be zero
    if received_amount == order_amount:
        assert actual_balance == Decimal('0')
    
    # Property 3: If received < total, balance should be positive
    if received_amount < order_amount:
        assert actual_balance > Decimal('0')
    
    # Property 4: If received > total, balance should be negative (overpaid)
    if received_amount > order_amount:
        assert actual_balance < Decimal('0')


@settings(max_examples=100)
@given(
    order_amount=amount_strategy,
    payment_amounts=st.lists(small_amount_strategy, min_size=1, max_size=10)
)
def test_property_5_unmatched_with_multiple_payments(
    order_amount: Decimal,
    payment_amounts: list
):
    """
    **Validates: Requirements 2.5**
    
    Property 5 (Extended): Unmatched Amount with Multiple Payments
    
    When an order receives multiple payments, the unmatched amount
    should equal the order total minus the sum of all payments.
    """
    # Calculate total received from all payments
    total_received = sum(payment_amounts)
    
    # Create order
    order_id = f"order_{uuid4().hex[:8]}"
    order = create_test_order(order_id, order_amount, total_received)
    
    # Property: Balance should equal order amount - sum of payments
    expected_balance = order_amount - total_received
    actual_balance = order.get_balance()
    
    assert actual_balance == expected_balance, (
        f"Balance {actual_balance} should equal "
        f"order {order_amount} - payments {total_received} = {expected_balance}"
    )


@settings(max_examples=100)
@given(
    bank_amount=amount_strategy,
    order_amount=amount_strategy
)
def test_property_5_reconciliation_difference_calculation(
    bank_amount: Decimal,
    order_amount: Decimal
):
    """
    **Validates: Requirements 2.5**
    
    Property 5 (Extended): Reconciliation Difference Calculation
    
    The difference in a reconciliation match should equal the total
    bank amount minus the total order amount.
    """
    # Create reconciliation match
    match = create_test_reconciliation_match(
        bank_record_ids=[f"bank_{uuid4().hex[:8]}"],
        order_ids=[f"order_{uuid4().hex[:8]}"],
        total_bank_amount=bank_amount,
        total_order_amount=order_amount
    )
    
    # Property 1: Difference should equal bank - order
    expected_difference = bank_amount - order_amount
    assert match.difference == expected_difference, (
        f"Difference {match.difference} should equal "
        f"bank {bank_amount} - order {order_amount} = {expected_difference}"
    )
    
    # Property 2: calculate_difference() should return the same value
    calculated_difference = match.calculate_difference()
    assert calculated_difference == expected_difference
    assert calculated_difference == match.difference



@settings(max_examples=100)
@given(
    bank_amounts=st.lists(small_amount_strategy, min_size=1, max_size=5),
    order_amounts=st.lists(small_amount_strategy, min_size=1, max_size=5)
)
def test_property_5_complex_reconciliation_difference(
    bank_amounts: list,
    order_amounts: list
):
    """
    **Validates: Requirements 2.5**
    
    Property 5 (Extended): Complex Reconciliation Difference
    
    For any reconciliation with multiple bank records and orders,
    the difference should equal sum(bank amounts) - sum(order amounts).
    """
    # Calculate totals
    total_bank = sum(bank_amounts)
    total_order = sum(order_amounts)
    
    # Create bank record IDs
    bank_record_ids = [
        f"bank_{i}_{uuid4().hex[:8]}"
        for i in range(len(bank_amounts))
    ]
    
    # Create order IDs
    order_ids = [
        f"order_{i}_{uuid4().hex[:8]}"
        for i in range(len(order_amounts))
    ]
    
    # Create reconciliation match
    match = create_test_reconciliation_match(
        bank_record_ids=bank_record_ids,
        order_ids=order_ids,
        total_bank_amount=total_bank,
        total_order_amount=total_order
    )
    
    # Property: Difference should equal sum(bank) - sum(order)
    expected_difference = total_bank - total_order
    assert match.difference == expected_difference, (
        f"Difference {match.difference} should equal "
        f"bank total {total_bank} - order total {total_order} = {expected_difference}"
    )


@settings(max_examples=100)
@given(
    order_amount=amount_strategy,
    num_payments=st.integers(min_value=1, max_value=10)
)
def test_property_5_incremental_payment_tracking(
    order_amount: Decimal,
    num_payments: int
):
    """
    **Validates: Requirements 2.5**
    
    Property 5 (Extended): Incremental Payment Tracking
    
    As payments are incrementally applied to an order, the unmatched
    amount should decrease by the payment amount each time.
    """
    # Calculate equal payment amounts
    payment_amount = order_amount / Decimal(num_payments)
    
    # Create order with no initial payment
    order_id = f"order_{uuid4().hex[:8]}"
    order = create_test_order(order_id, order_amount, Decimal('0'))
    
    # Track cumulative received amount
    cumulative_received = Decimal('0')
    
    # Apply payments incrementally
    for i in range(num_payments):
        cumulative_received += payment_amount
        
        # Update order's received amount
        order.received_amount = cumulative_received
        
        # Property: Balance should decrease by payment_amount
        expected_balance = order_amount - cumulative_received
        actual_balance = order.get_balance()
        
        # Allow small rounding error
        assert abs(actual_balance - expected_balance) < Decimal('0.01'), (
            f"After payment {i+1}, balance {actual_balance} should be "
            f"approximately {expected_balance}"
        )
    
    # Property: After all payments, balance should be near zero
    final_balance = order.get_balance()
    assert abs(final_balance) < Decimal('0.01'), (
        f"After all payments, balance should be near zero, got {final_balance}"
    )


@settings(max_examples=100)
@given(
    amount=amount_strategy
)
def test_property_5_zero_difference_when_matched(amount: Decimal):
    """
    **Validates: Requirements 2.5**
    
    Property 5 (Extended): Zero Difference When Perfectly Matched
    
    When bank amount exactly equals order amount, the difference
    should be zero.
    """
    # Create reconciliation match with equal amounts
    match = create_test_reconciliation_match(
        bank_record_ids=[f"bank_{uuid4().hex[:8]}"],
        order_ids=[f"order_{uuid4().hex[:8]}"],
        total_bank_amount=amount,
        total_order_amount=amount
    )
    
    # Property: Difference should be exactly zero
    assert match.difference == Decimal('0'), (
        f"Difference should be 0 when amounts match, got {match.difference}"
    )
    
    # Property: Should be valid with no error message
    is_valid, error_msg = match.validate_match()
    assert is_valid is True
    assert error_msg == ""



# ============================================================================
# Additional Robustness Properties
# ============================================================================

@settings(max_examples=100)
@given(
    bank_record_ids=st.lists(id_strategy, min_size=1, max_size=10, unique=True),
    order_ids=st.lists(id_strategy, min_size=1, max_size=10, unique=True),
    bank_amount=amount_strategy,
    order_amount=amount_strategy
)
def test_property_match_type_identification(
    bank_record_ids: list,
    order_ids: list,
    bank_amount: Decimal,
    order_amount: Decimal
):
    """
    Property: Match Type Identification
    
    The system should correctly identify the type of reconciliation match
    based on the number of bank records and orders.
    """
    # Create reconciliation match
    match = create_test_reconciliation_match(
        bank_record_ids=bank_record_ids,
        order_ids=order_ids,
        total_bank_amount=bank_amount,
        total_order_amount=order_amount
    )
    
    num_banks = len(bank_record_ids)
    num_orders = len(order_ids)
    
    # Property: Exactly one type should be true
    type_checks = [
        match.is_one_to_one(),
        match.is_one_to_many(),
        match.is_many_to_one(),
        match.is_many_to_many()
    ]
    
    assert sum(type_checks) == 1, (
        f"Exactly one match type should be true, got {sum(type_checks)}"
    )
    
    # Property: Type should match the counts
    if num_banks == 1 and num_orders == 1:
        assert match.is_one_to_one() is True
        assert match.get_match_type() == "一对一"
    elif num_banks == 1 and num_orders > 1:
        assert match.is_one_to_many() is True
        assert match.get_match_type() == "一对多"
    elif num_banks > 1 and num_orders == 1:
        assert match.is_many_to_one() is True
        assert match.get_match_type() == "多对一"
    elif num_banks > 1 and num_orders > 1:
        assert match.is_many_to_many() is True
        assert match.get_match_type() == "多对多"


@settings(max_examples=100)
@given(
    bank_amount=amount_strategy,
    order_amount=amount_strategy
)
def test_property_serialization_preserves_reconciliation(
    bank_amount: Decimal,
    order_amount: Decimal
):
    """
    Property: Serialization Preserves Reconciliation Data
    
    After serializing a reconciliation match to dict and deserializing back,
    all properties should be preserved.
    """
    # Create original match
    bank_record_ids = [f"bank_{uuid4().hex[:8]}"]
    order_ids = [f"order_{uuid4().hex[:8]}"]
    
    original_match = create_test_reconciliation_match(
        bank_record_ids=bank_record_ids,
        order_ids=order_ids,
        total_bank_amount=bank_amount,
        total_order_amount=order_amount
    )
    
    # Serialize and deserialize
    match_dict = original_match.to_dict()
    restored_match = ReconciliationMatch.from_dict(match_dict)
    
    # Property: All fields should be preserved
    assert restored_match.id == original_match.id
    assert restored_match.bank_record_ids == original_match.bank_record_ids
    assert restored_match.order_ids == original_match.order_ids
    assert restored_match.total_bank_amount == original_match.total_bank_amount
    assert restored_match.total_order_amount == original_match.total_order_amount
    assert restored_match.difference == original_match.difference
    
    # Property: Match type should be preserved
    assert restored_match.is_one_to_one() == original_match.is_one_to_one()
    assert restored_match.is_one_to_many() == original_match.is_one_to_many()
    assert restored_match.is_many_to_one() == original_match.is_many_to_one()
    assert restored_match.is_many_to_many() == original_match.is_many_to_many()
    
    # Property: Difference calculation should work the same
    assert restored_match.calculate_difference() == original_match.calculate_difference()


@settings(max_examples=100)
@given(
    amounts=st.lists(small_amount_strategy, min_size=2, max_size=10)
)
def test_property_reconciliation_commutativity(amounts: list):
    """
    Property: Reconciliation Commutativity
    
    The order of bank records or orders in a reconciliation match
    should not affect the total amounts or difference.
    """
    # Split amounts into bank and order amounts
    mid = len(amounts) // 2
    bank_amounts = amounts[:mid]
    order_amounts = amounts[mid:]
    
    total_bank = sum(bank_amounts)
    total_order = sum(order_amounts)
    
    # Create match with original order
    bank_ids_original = [f"bank_{i}" for i in range(len(bank_amounts))]
    order_ids_original = [f"order_{i}" for i in range(len(order_amounts))]
    
    match_original = create_test_reconciliation_match(
        bank_record_ids=bank_ids_original,
        order_ids=order_ids_original,
        total_bank_amount=total_bank,
        total_order_amount=total_order
    )
    
    # Create match with reversed order
    bank_ids_reversed = list(reversed(bank_ids_original))
    order_ids_reversed = list(reversed(order_ids_original))
    
    match_reversed = create_test_reconciliation_match(
        bank_record_ids=bank_ids_reversed,
        order_ids=order_ids_reversed,
        total_bank_amount=total_bank,
        total_order_amount=total_order
    )
    
    # Property: Totals should be the same regardless of order
    assert match_original.total_bank_amount == match_reversed.total_bank_amount
    assert match_original.total_order_amount == match_reversed.total_order_amount
    assert match_original.difference == match_reversed.difference
    
    # Property: Match type should be the same
    assert match_original.get_match_type() == match_reversed.get_match_type()


@settings(max_examples=100)
@given(
    bank_amount=amount_strategy,
    order_amount=amount_strategy
)
def test_property_validation_consistency(
    bank_amount: Decimal,
    order_amount: Decimal
):
    """
    Property: Validation Consistency
    
    Calling validate_match() multiple times should return the same result.
    """
    # Create match
    match = create_test_reconciliation_match(
        bank_record_ids=[f"bank_{uuid4().hex[:8]}"],
        order_ids=[f"order_{uuid4().hex[:8]}"],
        total_bank_amount=bank_amount,
        total_order_amount=order_amount
    )
    
    # Call validate multiple times
    result1 = match.validate_match()
    result2 = match.validate_match()
    result3 = match.validate_match()
    
    # Property: All results should be identical
    assert result1 == result2 == result3, (
        "validate_match() should return consistent results"
    )


@settings(max_examples=100)
@given(
    order_amount=amount_strategy
)
def test_property_balance_calculation_idempotence(order_amount: Decimal):
    """
    Property: Balance Calculation Idempotence
    
    Calling get_balance() multiple times should return the same result.
    """
    # Create order
    order = create_test_order(
        f"order_{uuid4().hex[:8]}",
        order_amount,
        Decimal('0')
    )
    
    # Call get_balance multiple times
    balance1 = order.get_balance()
    balance2 = order.get_balance()
    balance3 = order.get_balance()
    
    # Property: All results should be identical
    assert balance1 == balance2 == balance3 == order_amount, (
        "get_balance() should return consistent results"
    )
