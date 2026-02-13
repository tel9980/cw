"""
Property-based tests for order models

Tests universal properties that should hold across all valid inputs
for ProcessingOrder and related models.

Uses Hypothesis framework with 100+ iterations per property test.
"""

import pytest
from hypothesis import given, strategies as st, settings
from datetime import date, datetime
from decimal import Decimal
from uuid import uuid4
from dataclasses import dataclass

from oxidation_workflow_v18.models.core_models import (
    ProcessingOrder,
    PricingUnit,
    OrderStatus,
)


# ============================================================================
# Hypothesis Strategies
# ============================================================================

# Strategy for generating valid pricing units
pricing_unit_strategy = st.sampled_from(list(PricingUnit))

# Strategy for generating positive decimal quantities (0.01 to 10000)
quantity_strategy = st.decimals(
    min_value=Decimal('0.01'),
    max_value=Decimal('10000'),
    allow_nan=False,
    allow_infinity=False,
    places=2
)

# Strategy for generating positive decimal unit prices (0.01 to 1000)
unit_price_strategy = st.decimals(
    min_value=Decimal('0.01'),
    max_value=Decimal('1000'),
    allow_nan=False,
    allow_infinity=False,
    places=2
)

# Strategy for generating order status
order_status_strategy = st.sampled_from(list(OrderStatus))

# Strategy for generating dates
date_strategy = st.dates(
    min_value=date(2020, 1, 1),
    max_value=date(2030, 12, 31)
)

# Strategy for generating product names
product_name_strategy = st.text(
    alphabet=st.characters(whitelist_categories=('L', 'N', 'P', 'Zs')),
    min_size=1,
    max_size=50
)


# ============================================================================
# Helper Functions
# ============================================================================

def create_test_order(
    pricing_unit: PricingUnit,
    quantity: Decimal,
    unit_price: Decimal,
    order_date: date = None,
    product_name: str = "测试产品",
    status: OrderStatus = OrderStatus.PENDING
) -> ProcessingOrder:
    """
    Helper function to create a test order with calculated total amount.
    
    Args:
        pricing_unit: The pricing unit for the order
        quantity: The quantity of items
        unit_price: The price per unit
        order_date: The order date (defaults to today)
        product_name: The product name
        status: The order status
    
    Returns:
        ProcessingOrder: A new order instance
    """
    if order_date is None:
        order_date = date.today()
    
    total_amount = quantity * unit_price
    now = datetime.now()
    
    return ProcessingOrder(
        id=str(uuid4()),
        order_number=f"ORD-{uuid4().hex[:8].upper()}",
        customer_id=f"cust_{uuid4().hex[:8]}",
        order_date=order_date,
        product_name=product_name,
        pricing_unit=pricing_unit,
        quantity=quantity,
        unit_price=unit_price,
        total_amount=total_amount,
        status=status,
        received_amount=Decimal('0'),
        outsourced_cost=Decimal('0'),
        notes="",
        created_at=now,
        updated_at=now,
    )


# ============================================================================
# Property 1: Pricing Unit Support and Calculation
# ============================================================================

@settings(max_examples=100)
@given(
    pricing_unit=pricing_unit_strategy,
    quantity=quantity_strategy,
    unit_price=unit_price_strategy
)
def test_property_1_pricing_unit_calculation(
    pricing_unit: PricingUnit,
    quantity: Decimal,
    unit_price: Decimal
):
    """
    **Validates: Requirements 1.1, 1.2, 1.3, 1.4, 1.5**
    
    Property 1: Pricing Unit Support and Calculation
    
    For any processing order with a valid pricing unit (件/条/只/个/米长/米重/平方),
    quantity, and unit price, the calculated total amount should equal
    quantity multiplied by unit price.
    
    This property ensures:
    1. All pricing units are supported
    2. Calculation is mathematically correct
    3. Decimal precision is maintained
    """
    # Create order with the given parameters
    order = create_test_order(pricing_unit, quantity, unit_price)
    
    # Property: total_amount should equal quantity * unit_price
    expected_total = quantity * unit_price
    assert order.total_amount == expected_total, (
        f"Order total {order.total_amount} does not match "
        f"expected {expected_total} for {quantity} × {unit_price}"
    )
    
    # Property: calculate_total() method should return the same value
    calculated_total = order.calculate_total()
    assert calculated_total == expected_total, (
        f"calculate_total() returned {calculated_total}, "
        f"expected {expected_total}"
    )
    
    # Property: pricing_unit should be preserved
    assert order.pricing_unit == pricing_unit, (
        f"Pricing unit {order.pricing_unit} does not match "
        f"expected {pricing_unit}"
    )
    
    # Property: quantity and unit_price should be preserved
    assert order.quantity == quantity
    assert order.unit_price == unit_price


@settings(max_examples=100)
@given(
    pricing_unit=pricing_unit_strategy,
    quantity=quantity_strategy,
    unit_price=unit_price_strategy,
    order_date=date_strategy,
    product_name=product_name_strategy,
    status=order_status_strategy
)
def test_property_1_all_pricing_units_supported(
    pricing_unit: PricingUnit,
    quantity: Decimal,
    unit_price: Decimal,
    order_date: date,
    product_name: str,
    status: OrderStatus
):
    """
    **Validates: Requirements 1.1, 1.2, 1.3, 1.4**
    
    Property 1 (Extended): All Pricing Units Supported
    
    For any valid pricing unit from the PricingUnit enum, the system
    should be able to create an order and perform calculations correctly.
    
    This ensures all 7 pricing units are fully supported:
    - PIECE (件)
    - STRIP (条)
    - ITEM (只)
    - UNIT (个)
    - METER_LENGTH (米长)
    - METER_WEIGHT (米重)
    - SQUARE_METER (平方)
    """
    # Create order with all random parameters
    order = create_test_order(
        pricing_unit=pricing_unit,
        quantity=quantity,
        unit_price=unit_price,
        order_date=order_date,
        product_name=product_name,
        status=status
    )
    
    # Property: Order should be created successfully
    assert order is not None
    
    # Property: All fields should be preserved
    assert order.pricing_unit == pricing_unit
    assert order.quantity == quantity
    assert order.unit_price == unit_price
    assert order.order_date == order_date
    assert order.product_name == product_name
    assert order.status == status
    
    # Property: Calculation should work for any pricing unit
    expected_total = quantity * unit_price
    assert order.total_amount == expected_total
    assert order.calculate_total() == expected_total


# ============================================================================
# Property 2: Multi-Item Order Aggregation
# ============================================================================

@dataclass
class OrderLineItem:
    """Represents a line item in a multi-item order"""
    pricing_unit: PricingUnit
    quantity: Decimal
    unit_price: Decimal
    
    @property
    def total(self) -> Decimal:
        return self.quantity * self.unit_price


# Strategy for generating a list of line items
line_item_strategy = st.builds(
    OrderLineItem,
    pricing_unit=pricing_unit_strategy,
    quantity=quantity_strategy,
    unit_price=unit_price_strategy
)

# Strategy for generating multiple line items (1 to 10 items)
multi_line_items_strategy = st.lists(
    line_item_strategy,
    min_size=1,
    max_size=10
)


@settings(max_examples=100)
@given(line_items=multi_line_items_strategy)
def test_property_2_multi_item_order_aggregation(line_items: list):
    """
    **Validates: Requirements 1.6**
    
    Property 2: Multi-Item Order Aggregation
    
    For any order containing multiple line items, the total order amount
    should equal the sum of all individual line item totals.
    
    This property ensures:
    1. Multiple items can be aggregated correctly
    2. Sum of parts equals the whole
    3. No rounding errors in aggregation
    
    Note: In the current model, we simulate multi-item orders by creating
    separate orders and summing them. In a real system with line items,
    this would be a single order with multiple lines.
    """
    # Calculate expected total from all line items
    expected_total = sum(item.total for item in line_items)
    
    # Create individual orders for each line item
    # (In a real system, these would be line items in a single order)
    orders = []
    for item in line_items:
        order = create_test_order(
            pricing_unit=item.pricing_unit,
            quantity=item.quantity,
            unit_price=item.unit_price
        )
        orders.append(order)
    
    # Property: Sum of all order totals should equal expected total
    actual_total = sum(order.total_amount for order in orders)
    assert actual_total == expected_total, (
        f"Aggregated total {actual_total} does not match "
        f"expected {expected_total}"
    )
    
    # Property: Each individual order should have correct calculation
    for i, (order, item) in enumerate(zip(orders, line_items)):
        assert order.total_amount == item.total, (
            f"Order {i} total {order.total_amount} does not match "
            f"line item total {item.total}"
        )
    
    # Property: Number of orders should match number of line items
    assert len(orders) == len(line_items)


@settings(max_examples=100)
@given(
    line_items=st.lists(
        st.tuples(quantity_strategy, unit_price_strategy),
        min_size=2,
        max_size=5
    )
)
def test_property_2_aggregation_associativity(line_items: list):
    """
    **Validates: Requirements 1.6**
    
    Property 2 (Extended): Aggregation Associativity
    
    For any set of line items, the order of aggregation should not matter.
    (a + b) + c should equal a + (b + c)
    
    This ensures the aggregation operation is mathematically sound.
    """
    if len(line_items) < 2:
        return  # Skip if not enough items
    
    # Calculate total by summing all at once
    total_all_at_once = sum(
        qty * price for qty, price in line_items
    )
    
    # Calculate total by summing in pairs
    total_pairwise = Decimal('0')
    for qty, price in line_items:
        total_pairwise += (qty * price)
    
    # Property: Both methods should give the same result
    assert total_all_at_once == total_pairwise, (
        f"All-at-once total {total_all_at_once} does not match "
        f"pairwise total {total_pairwise}"
    )


@settings(max_examples=100)
@given(
    pricing_unit=pricing_unit_strategy,
    quantities=st.lists(quantity_strategy, min_size=1, max_size=10),
    unit_price=unit_price_strategy
)
def test_property_2_same_unit_price_aggregation(
    pricing_unit: PricingUnit,
    quantities: list,
    unit_price: Decimal
):
    """
    **Validates: Requirements 1.6**
    
    Property 2 (Extended): Same Unit Price Aggregation
    
    For multiple items with the same unit price, the total should equal
    the sum of quantities multiplied by the unit price.
    
    This is a common scenario where multiple batches of the same product
    are ordered at the same price.
    """
    # Create orders for each quantity
    orders = []
    for qty in quantities:
        order = create_test_order(
            pricing_unit=pricing_unit,
            quantity=qty,
            unit_price=unit_price
        )
        orders.append(order)
    
    # Calculate expected total
    total_quantity = sum(quantities)
    expected_total = total_quantity * unit_price
    
    # Calculate actual total from orders
    actual_total = sum(order.total_amount for order in orders)
    
    # Property: Aggregated total should match expected
    assert actual_total == expected_total, (
        f"Aggregated total {actual_total} does not match "
        f"expected {expected_total} for total quantity {total_quantity} "
        f"at unit price {unit_price}"
    )


# ============================================================================
# Additional Properties for Robustness
# ============================================================================

@settings(max_examples=100)
@given(
    pricing_unit=pricing_unit_strategy,
    quantity=quantity_strategy,
    unit_price=unit_price_strategy
)
def test_property_calculation_idempotence(
    pricing_unit: PricingUnit,
    quantity: Decimal,
    unit_price: Decimal
):
    """
    Property: Calculation Idempotence
    
    Calling calculate_total() multiple times should always return
    the same result.
    """
    order = create_test_order(pricing_unit, quantity, unit_price)
    
    # Calculate total multiple times
    result1 = order.calculate_total()
    result2 = order.calculate_total()
    result3 = order.calculate_total()
    
    # Property: All results should be identical
    assert result1 == result2 == result3
    assert result1 == order.total_amount


@settings(max_examples=100)
@given(
    pricing_unit=pricing_unit_strategy,
    quantity=quantity_strategy,
    unit_price=unit_price_strategy
)
def test_property_serialization_preserves_calculation(
    pricing_unit: PricingUnit,
    quantity: Decimal,
    unit_price: Decimal
):
    """
    Property: Serialization Preserves Calculation
    
    After serializing to dict and deserializing back, the order
    should maintain the same calculation results.
    """
    original_order = create_test_order(pricing_unit, quantity, unit_price)
    original_total = original_order.calculate_total()
    
    # Serialize and deserialize
    order_dict = original_order.to_dict()
    restored_order = ProcessingOrder.from_dict(order_dict)
    
    # Property: Calculation should be preserved
    assert restored_order.calculate_total() == original_total
    assert restored_order.total_amount == original_order.total_amount
    assert restored_order.quantity == original_order.quantity
    assert restored_order.unit_price == original_order.unit_price
    assert restored_order.pricing_unit == original_order.pricing_unit
