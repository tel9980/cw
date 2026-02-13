"""
Reconciliation module for V1.7 Oxidation Factory Complete

This module provides bank statement reconciliation functionality,
including flexible matching for one-to-many and many-to-one scenarios,
and counterparty alias management.
"""

from small_accountant_v16.reconciliation.bank_statement_matcher import (
    BankStatementMatcher,
    MatchConfig,
    Match,
    MatchResult
)
from small_accountant_v16.reconciliation.reconciliation_report_generator import (
    ReconciliationReportGenerator,
    CustomerAccountData
)
from small_accountant_v16.reconciliation.reconciliation_assistant import ReconciliationAssistant
from oxidation_complete_v17.reconciliation.flexible_matcher import (
    FlexibleReconciliationMatcher,
    FlexibleMatch,
    FlexibleMatchType,
    ReconciliationHistory,
    CounterpartyBalance
)
from oxidation_complete_v17.reconciliation.alias_manager import (
    CounterpartyAliasManager,
    CounterpartyAlias,
    AliasMatchResult
)

__all__ = [
    'BankStatementMatcher',
    'MatchConfig',
    'Match',
    'MatchResult',
    'ReconciliationReportGenerator',
    'CustomerAccountData',
    'ReconciliationAssistant',
    'FlexibleReconciliationMatcher',
    'FlexibleMatch',
    'FlexibleMatchType',
    'ReconciliationHistory',
    'CounterpartyBalance',
    'CounterpartyAliasManager',
    'CounterpartyAlias',
    'AliasMatchResult',
]
