"""
Property-based tests for account models

Tests universal properties that should hold across all valid inputs
for BankAccount and related transaction models.

Uses Hypothesis framework with 100+ iterations per property test.
"""

import pytest
from hypothesis import given, strategies as st, settings, assume
from datetime import date, datetime
from decimal import Decimal
from uuid import uuid4

from oxidation_workflow_v18.models.core_models import (
    BankAccount,
    TransactionRecord,
    AccountType,
    TransactionType,
    TransactionStatus,
)


# ============================================================================
# Hypothesis Strategies
# ============================================================================

# Strategy for generating account types
account_type_strategy = st.sampled_from(list(AccountType))

# Strategy for generating positive decimal amounts (0.01 to 100000)
amount_strategy = st.decimals(
    min_value=Decimal('0.01'),
    max_value=Decimal('100000'),
    allow_nan=False,
    allow_infinity=False,
    places=2
)

# Strategy for generating transaction types
transaction_type_strategy = st.sampled_from(list(TransactionType))

# Strategy for generating dates
date_strategy = st.dates(
    min_value=date(2020, 1, 1),
    max_value=date(2030, 12, 31)
)

# Strategy for generating account names
account_name_strategy = st.sampled_from(['G银行', 'N银行', '微信'])

# Strategy for generating boolean values
boolean_strategy = st.booleans()


# ============================================================================
# Helper Functions
# ============================================================================

def create_test_account(
    name: str = "测试账户",
    account_type: AccountType = AccountType.BUSINESS,
    has_invoice: bool = True,
    initial_balance: Decimal = Decimal('0')
) -> BankAccount:
    """
    Helper function to create a test bank account.
    
    Args:
        name: The account name
        account_type: The account type (BUSINESS or CASH)
        has_invoice: Whether the account has invoice capability
        initial_balance: The initial balance
    
    Returns:
        BankAccount: A new account instance
    """
    now = datetime.now()
    
    return BankAccount(
        id=str(uuid4()),
        name=name,
        account_number=f"ACC-{uuid4().hex[:10].upper()}",
        account_type=account_type,
        has_invoice=has_invoice,
        balance=initial_balance,
        description=f"{name} - {account_type.value}",
        created_at=now,
        updated_at=now,
    )


def create_test_transaction(
    account_id: str,
    transaction_type: TransactionType,
    amount: Decimal,
    transaction_date: date = None
) -> TransactionRecord:
    """
    Helper function to create a test transaction record.
    
    Args:
        account_id: The bank account ID
        transaction_type: INCOME or EXPENSE
        amount: The transaction amount
        transaction_date: The transaction date (defaults to today)
    
    Returns:
        TransactionRecord: A new transaction instance
    """
    if transaction_date is None:
        transaction_date = date.today()
    
    now = datetime.now()
    
    return TransactionRecord(
        id=str(uuid4()),
        date=transaction_date,
        type=transaction_type,
        amount=amount,
        counterparty_id=f"party_{uuid4().hex[:8]}",
        description=f"{transaction_type.value} transaction",
        category="测试类别",
        status=TransactionStatus.COMPLETED,
        created_at=now,
        updated_at=now,
        bank_account_id=account_id,
    )


# ============================================================================
# Property 8: Account Balance Calculation
# ============================================================================

@settings(max_examples=100)
@given(
    account_type=account_type_strategy,
    has_invoice=boolean_strategy,
    income_amounts=st.lists(amount_strategy, min_size=0, max_size=10),
    expense_amounts=st.lists(amount_strategy, min_size=0, max_size=10)
)
def test_property_8_account_balance_calculation(
    account_type: AccountType,
    has_invoice: bool,
    income_amounts: list,
    expense_amounts: list
):
    """
    **Validates: Requirement 3.5**
    
    Property 8: Account Balance Calculation
    
    For any bank account, the balance should equal the sum of all credit
    transactions (income) minus the sum of all debit transactions (expense)
    for that account.
    
    This property ensures:
    1. Balance calculation is mathematically correct
    2. Income increases balance
    3. Expenses decrease balance
    4. Multiple transactions are aggregated correctly
    """
    # Create test account with zero initial balance
    account = create_test_account(
        account_type=account_type,
        has_invoice=has_invoice,
        initial_balance=Decimal('0')
    )
    
    # Create income transactions
    income_transactions = [
        create_test_transaction(
            account_id=account.id,
            transaction_type=TransactionType.INCOME,
            amount=amount
        )
        for amount in income_amounts
    ]
    
    # Create expense transactions
    expense_transactions = [
        create_test_transaction(
            account_id=account.id,
            transaction_type=TransactionType.EXPENSE,
            amount=amount
        )
        for amount in expense_amounts
    ]
    
    # Combine all transactions
    all_transactions = income_transactions + expense_transactions
    
    # Calculate expected balance
    total_income = sum(income_amounts) if income_amounts else Decimal('0')
    total_expense = sum(expense_amounts) if expense_amounts else Decimal('0')
    expected_balance = total_income - total_expense
    
    # Property: calculate_balance_from_transactions should return expected balance
    calculated_balance = account.calculate_balance_from_transactions(all_transactions)
    
    assert calculated_balance == expected_balance, (
        f"Calculated balance {calculated_balance} does not match "
        f"expected {expected_balance} "
        f"(income: {total_income}, expense: {total_expense})"
    )


@settings(max_examples=100)
@given(
    initial_balance=amount_strategy,
    transactions=st.lists(
        st.tuples(
            st.booleans(),  # is_credit
            amount_strategy  # amount
        ),
        min_size=1,
        max_size=20
    )
)
def test_property_8_update_balance_sequential(
    initial_balance: Decimal,
    transactions: list
):
    """
    **Validates: Requirement 3.5**
    
    Property 8 (Extended): Sequential Balance Updates
    
    For any sequence of balance updates (credits and debits), the final
    balance should equal the initial balance plus all credits minus all debits.
    
    This ensures the update_balance method works correctly for sequential
    operations.
    """
    # Create account with initial balance
    account = create_test_account(initial_balance=initial_balance)
    
    # Track expected balance
    expected_balance = initial_balance
    
    # Apply each transaction sequentially
    for is_credit, amount in transactions:
        account.update_balance(amount, is_credit)
        
        # Update expected balance
        if is_credit:
            expected_balance += amount
        else:
            expected_balance -= amount
    
    # Property: Final balance should match expected
    assert account.balance == expected_balance, (
        f"Final balance {account.balance} does not match "
        f"expected {expected_balance} after {len(transactions)} transactions"
    )


@settings(max_examples=100)
@given(
    account_type=account_type_strategy,
    has_invoice=boolean_strategy,
    transactions=st.lists(
        st.tuples(
            transaction_type_strategy,
            amount_strategy,
            date_strategy
        ),
        min_size=1,
        max_size=15
    )
)
def test_property_8_balance_calculation_with_dates(
    account_type: AccountType,
    has_invoice: bool,
    transactions: list
):
    """
    **Validates: Requirement 3.5**
    
    Property 8 (Extended): Balance Calculation with Dates
    
    The balance calculation should be independent of transaction dates.
    All transactions for an account should be included regardless of when
    they occurred.
    """
    # Create test account
    account = create_test_account(
        account_type=account_type,
        has_invoice=has_invoice
    )
    
    # Create transaction records
    transaction_records = [
        create_test_transaction(
            account_id=account.id,
            transaction_type=trans_type,
            amount=amount,
            transaction_date=trans_date
        )
        for trans_type, amount, trans_date in transactions
    ]
    
    # Calculate expected balance
    total_income = sum(
        amount for trans_type, amount, _ in transactions
        if trans_type == TransactionType.INCOME
    )
    total_expense = sum(
        amount for trans_type, amount, _ in transactions
        if trans_type == TransactionType.EXPENSE
    )
    expected_balance = total_income - total_expense
    
    # Property: Calculated balance should match expected
    calculated_balance = account.calculate_balance_from_transactions(transaction_records)
    
    assert calculated_balance == expected_balance, (
        f"Calculated balance {calculated_balance} does not match "
        f"expected {expected_balance}"
    )


@settings(max_examples=100)
@given(
    account1_transactions=st.lists(amount_strategy, min_size=1, max_size=10),
    account2_transactions=st.lists(amount_strategy, min_size=1, max_size=10)
)
def test_property_8_balance_isolation_between_accounts(
    account1_transactions: list,
    account2_transactions: list
):
    """
    **Validates: Requirement 3.5**
    
    Property 8 (Extended): Balance Isolation Between Accounts
    
    Each account's balance calculation should only include transactions
    for that specific account. Transactions from other accounts should
    not affect the balance.
    """
    # Create two separate accounts
    account1 = create_test_account(name="账户1")
    account2 = create_test_account(name="账户2")
    
    # Create transactions for account 1 (all income)
    account1_records = [
        create_test_transaction(
            account_id=account1.id,
            transaction_type=TransactionType.INCOME,
            amount=amount
        )
        for amount in account1_transactions
    ]
    
    # Create transactions for account 2 (all income)
    account2_records = [
        create_test_transaction(
            account_id=account2.id,
            transaction_type=TransactionType.INCOME,
            amount=amount
        )
        for amount in account2_transactions
    ]
    
    # Combine all transactions (simulating a shared transaction list)
    all_transactions = account1_records + account2_records
    
    # Calculate expected balances
    expected_balance1 = sum(account1_transactions)
    expected_balance2 = sum(account2_transactions)
    
    # Property: Each account should only see its own transactions
    calculated_balance1 = account1.calculate_balance_from_transactions(all_transactions)
    calculated_balance2 = account2.calculate_balance_from_transactions(all_transactions)
    
    assert calculated_balance1 == expected_balance1, (
        f"Account 1 balance {calculated_balance1} does not match "
        f"expected {expected_balance1}"
    )
    
    assert calculated_balance2 == expected_balance2, (
        f"Account 2 balance {calculated_balance2} does not match "
        f"expected {expected_balance2}"
    )
    
    # Property: Balances should be independent
    assert calculated_balance1 != calculated_balance2 or (
        sum(account1_transactions) == sum(account2_transactions)
    ), "Balances should only be equal if transaction sums are equal"


@settings(max_examples=100)
@given(
    initial_balance=amount_strategy,
    credit_amount=amount_strategy,
    debit_amount=amount_strategy
)
def test_property_8_balance_update_reversibility(
    initial_balance: Decimal,
    credit_amount: Decimal,
    debit_amount: Decimal
):
    """
    **Validates: Requirement 3.5**
    
    Property 8 (Extended): Balance Update Reversibility
    
    If we credit an amount and then debit the same amount, the balance
    should return to its original value (and vice versa).
    """
    # Create account with initial balance
    account = create_test_account(initial_balance=initial_balance)
    
    # Store original balance
    original_balance = account.balance
    
    # Credit then debit the same amount
    account.update_balance(credit_amount, is_credit=True)
    account.update_balance(credit_amount, is_credit=False)
    
    # Property: Balance should return to original
    assert account.balance == original_balance, (
        f"Balance {account.balance} did not return to original {original_balance} "
        f"after credit and debit of {credit_amount}"
    )
    
    # Reset to original
    account.balance = original_balance
    
    # Debit then credit the same amount
    account.update_balance(debit_amount, is_credit=False)
    account.update_balance(debit_amount, is_credit=True)
    
    # Property: Balance should return to original
    assert account.balance == original_balance, (
        f"Balance {account.balance} did not return to original {original_balance} "
        f"after debit and credit of {debit_amount}"
    )


@settings(max_examples=100)
@given(
    amounts=st.lists(amount_strategy, min_size=2, max_size=10)
)
def test_property_8_balance_calculation_commutativity(amounts: list):
    """
    **Validates: Requirement 3.5**
    
    Property 8 (Extended): Balance Calculation Commutativity
    
    The order of transactions in the list should not affect the final
    calculated balance. Balance calculation should be commutative.
    """
    # Create account
    account = create_test_account()
    
    # Create transactions in original order (all income)
    transactions_original = [
        create_test_transaction(
            account_id=account.id,
            transaction_type=TransactionType.INCOME,
            amount=amount
        )
        for amount in amounts
    ]
    
    # Create transactions in reversed order
    transactions_reversed = [
        create_test_transaction(
            account_id=account.id,
            transaction_type=TransactionType.INCOME,
            amount=amount
        )
        for amount in reversed(amounts)
    ]
    
    # Calculate balances
    balance_original = account.calculate_balance_from_transactions(transactions_original)
    balance_reversed = account.calculate_balance_from_transactions(transactions_reversed)
    
    # Property: Both should give the same result
    assert balance_original == balance_reversed, (
        f"Balance from original order {balance_original} does not match "
        f"balance from reversed order {balance_reversed}"
    )
    
    # Property: Both should equal the sum of amounts
    expected_balance = sum(amounts)
    assert balance_original == expected_balance
    assert balance_reversed == expected_balance


@settings(max_examples=100)
@given(
    account_type=account_type_strategy,
    has_invoice=boolean_strategy
)
def test_property_8_empty_transactions_zero_balance(
    account_type: AccountType,
    has_invoice: bool
):
    """
    **Validates: Requirement 3.5**
    
    Property 8 (Extended): Empty Transactions List
    
    For any account with no transactions, the calculated balance should be zero.
    """
    # Create account
    account = create_test_account(
        account_type=account_type,
        has_invoice=has_invoice
    )
    
    # Empty transaction list
    transactions = []
    
    # Property: Balance should be zero
    calculated_balance = account.calculate_balance_from_transactions(transactions)
    
    assert calculated_balance == Decimal('0'), (
        f"Balance for empty transactions should be 0, got {calculated_balance}"
    )


@settings(max_examples=100)
@given(
    initial_balance=amount_strategy,
    amount=amount_strategy
)
def test_property_8_update_balance_return_value(
    initial_balance: Decimal,
    amount: Decimal
):
    """
    **Validates: Requirement 3.5**
    
    Property 8 (Extended): Update Balance Return Value
    
    The update_balance method should return the new balance after the update.
    """
    # Create account
    account = create_test_account(initial_balance=initial_balance)
    
    # Update balance (credit)
    returned_balance = account.update_balance(amount, is_credit=True)
    
    # Property: Returned balance should match account balance
    assert returned_balance == account.balance, (
        f"Returned balance {returned_balance} does not match "
        f"account balance {account.balance}"
    )
    
    # Property: Returned balance should be correct
    expected_balance = initial_balance + amount
    assert returned_balance == expected_balance, (
        f"Returned balance {returned_balance} does not match "
        f"expected {expected_balance}"
    )


# ============================================================================
# Additional Robustness Properties
# ============================================================================

@settings(max_examples=100)
@given(
    account_type=account_type_strategy,
    has_invoice=boolean_strategy,
    transactions=st.lists(
        st.tuples(transaction_type_strategy, amount_strategy),
        min_size=1,
        max_size=10
    )
)
def test_property_serialization_preserves_balance_calculation(
    account_type: AccountType,
    has_invoice: bool,
    transactions: list
):
    """
    Property: Serialization Preserves Balance Calculation
    
    After serializing an account to dict and deserializing back,
    the balance calculation should remain correct.
    """
    # Create account
    original_account = create_test_account(
        account_type=account_type,
        has_invoice=has_invoice
    )
    
    # Create transactions
    transaction_records = [
        create_test_transaction(
            account_id=original_account.id,
            transaction_type=trans_type,
            amount=amount
        )
        for trans_type, amount in transactions
    ]
    
    # Calculate balance with original account
    original_balance = original_account.calculate_balance_from_transactions(transaction_records)
    
    # Serialize and deserialize
    account_dict = original_account.to_dict()
    restored_account = BankAccount.from_dict(account_dict)
    
    # Update transaction records to use restored account ID
    for trans in transaction_records:
        trans.bank_account_id = restored_account.id
    
    # Calculate balance with restored account
    restored_balance = restored_account.calculate_balance_from_transactions(transaction_records)
    
    # Property: Balance calculation should be preserved
    assert restored_balance == original_balance, (
        f"Restored balance {restored_balance} does not match "
        f"original balance {original_balance}"
    )


@settings(max_examples=100)
@given(
    amounts=st.lists(amount_strategy, min_size=1, max_size=10)
)
def test_property_balance_calculation_precision(amounts: list):
    """
    Property: Balance Calculation Precision
    
    Balance calculations should maintain decimal precision without
    rounding errors, even with many transactions.
    """
    # Create account
    account = create_test_account()
    
    # Create income transactions
    transactions = [
        create_test_transaction(
            account_id=account.id,
            transaction_type=TransactionType.INCOME,
            amount=amount
        )
        for amount in amounts
    ]
    
    # Calculate balance
    calculated_balance = account.calculate_balance_from_transactions(transactions)
    
    # Calculate expected using Python's Decimal for precision
    expected_balance = sum(amounts, Decimal('0'))
    
    # Property: Should match exactly (no rounding errors)
    assert calculated_balance == expected_balance, (
        f"Calculated balance {calculated_balance} does not match "
        f"expected {expected_balance} - precision error detected"
    )
