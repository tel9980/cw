"""
Unit tests for BankStatementMatcher

Tests the bank statement matching functionality including exact matching,
fuzzy matching, and discrepancy identification.
"""

import pytest
from datetime import date, datetime, timedelta
from decimal import Decimal

from small_accountant_v16.models.core_models import (
    BankRecord,
    TransactionRecord,
    TransactionType,
    TransactionStatus,
    DiscrepancyType
)
from small_accountant_v16.reconciliation.bank_statement_matcher import (
    BankStatementMatcher,
    MatchConfig,
    Match,
    MatchResult
)


class TestBankStatementMatcherExactMatch:
    """测试精确匹配功能"""
    
    def test_exact_match_identical_records(self):
        """测试完全相同的记录能够精确匹配"""
        # 准备测试数据
        bank_record = BankRecord(
            id="B001",
            transaction_date=date(2024, 1, 15),
            description="收款",
            amount=Decimal("1000.00"),
            balance=Decimal("5000.00"),
            transaction_type="CREDIT",
            counterparty="ABC公司"
        )
        
        system_record = TransactionRecord(
            id="S001",
            date=date(2024, 1, 15),
            type=TransactionType.INCOME,
            amount=Decimal("1000.00"),
            counterparty_id="C001",
            description="ABC公司",
            category="销售收入",
            status=TransactionStatus.COMPLETED,
            created_at=datetime.now(),
            updated_at=datetime.now()
        )
        
        matcher = BankStatementMatcher()
        result = matcher.match_transactions([bank_record], [system_record])
        
        # 验证匹配结果
        assert result.matched_count == 1
        assert len(result.matches) == 1
        assert result.matches[0].match_type == 'exact'
        assert result.matches[0].confidence == 1.0
        assert len(result.unmatched_bank_records) == 0
        assert len(result.unmatched_system_records) == 0
    
    def test_exact_match_counterparty_substring(self):
        """测试往来单位名称包含关系的精确匹配"""
        bank_record = BankRecord(
            id="B001",
            transaction_date=date(2024, 1, 15),
            description="收款",
            amount=Decimal("1000.00"),
            balance=Decimal("5000.00"),
            transaction_type="CREDIT",
            counterparty="ABC"
        )
        
        system_record = TransactionRecord(
            id="S001",
            date=date(2024, 1, 15),
            type=TransactionType.INCOME,
            amount=Decimal("1000.00"),
            counterparty_id="C001",
            description="ABC公司有限责任公司",
            category="销售收入",
            status=TransactionStatus.COMPLETED,
            created_at=datetime.now(),
            updated_at=datetime.now()
        )
        
        matcher = BankStatementMatcher()
        result = matcher.match_transactions([bank_record], [system_record])
        
        assert result.matched_count == 1
        assert result.matches[0].match_type == 'exact'
    
    def test_no_match_different_amounts(self):
        """测试金额不同时无法精确匹配"""
        bank_record = BankRecord(
            id="B001",
            transaction_date=date(2024, 1, 15),
            description="收款",
            amount=Decimal("1000.00"),
            balance=Decimal("5000.00"),
            transaction_type="CREDIT",
            counterparty="ABC公司"
        )
        
        system_record = TransactionRecord(
            id="S001",
            date=date(2024, 1, 15),
            type=TransactionType.INCOME,
            amount=Decimal("1001.00"),  # 金额不同
            counterparty_id="C001",
            description="ABC公司",
            category="销售收入",
            status=TransactionStatus.COMPLETED,
            created_at=datetime.now(),
            updated_at=datetime.now()
        )
        
        matcher = BankStatementMatcher(MatchConfig(enable_fuzzy_matching=False))
        result = matcher.match_transactions([bank_record], [system_record])
        
        assert result.matched_count == 0
        assert len(result.unmatched_bank_records) == 1
        assert len(result.unmatched_system_records) == 1
    
    def test_no_match_different_dates(self):
        """测试日期不同时无法精确匹配"""
        bank_record = BankRecord(
            id="B001",
            transaction_date=date(2024, 1, 15),
            description="收款",
            amount=Decimal("1000.00"),
            balance=Decimal("5000.00"),
            transaction_type="CREDIT",
            counterparty="ABC公司"
        )
        
        system_record = TransactionRecord(
            id="S001",
            date=date(2024, 1, 16),  # 日期不同
            type=TransactionType.INCOME,
            amount=Decimal("1000.00"),
            counterparty_id="C001",
            description="ABC公司",
            category="销售收入",
            status=TransactionStatus.COMPLETED,
            created_at=datetime.now(),
            updated_at=datetime.now()
        )
        
        matcher = BankStatementMatcher(MatchConfig(enable_fuzzy_matching=False))
        result = matcher.match_transactions([bank_record], [system_record])
        
        assert result.matched_count == 0


class TestBankStatementMatcherFuzzyMatch:
    """测试模糊匹配功能"""
    
    def test_fuzzy_match_with_amount_tolerance(self):
        """测试金额容差的模糊匹配"""
        bank_record = BankRecord(
            id="B001",
            transaction_date=date(2024, 1, 15),
            description="收款",
            amount=Decimal("1000.00"),
            balance=Decimal("5000.00"),
            transaction_type="CREDIT",
            counterparty="ABC公司"
        )
        
        system_record = TransactionRecord(
            id="S001",
            date=date(2024, 1, 15),
            type=TransactionType.INCOME,
            amount=Decimal("1005.00"),  # 金额有5元差异
            counterparty_id="C001",
            description="ABC公司",
            category="销售收入",
            status=TransactionStatus.COMPLETED,
            created_at=datetime.now(),
            updated_at=datetime.now()
        )
        
        # 配置1%的金额容差
        config = MatchConfig(
            amount_tolerance_percent=0.01,
            enable_fuzzy_matching=True
        )
        matcher = BankStatementMatcher(config)
        result = matcher.match_transactions([bank_record], [system_record])
        
        assert result.matched_count == 1
        assert result.matches[0].match_type == 'fuzzy'
        assert result.matches[0].confidence > 0.7
    
    def test_fuzzy_match_with_date_tolerance(self):
        """测试日期容差的模糊匹配"""
        bank_record = BankRecord(
            id="B001",
            transaction_date=date(2024, 1, 15),
            description="收款",
            amount=Decimal("1000.00"),
            balance=Decimal("5000.00"),
            transaction_type="CREDIT",
            counterparty="ABC公司"
        )
        
        system_record = TransactionRecord(
            id="S001",
            date=date(2024, 1, 17),  # 日期相差2天
            type=TransactionType.INCOME,
            amount=Decimal("1000.00"),
            counterparty_id="C001",
            description="ABC公司",
            category="销售收入",
            status=TransactionStatus.COMPLETED,
            created_at=datetime.now(),
            updated_at=datetime.now()
        )
        
        # 配置3天的日期容差
        config = MatchConfig(
            date_tolerance_days=3,
            enable_fuzzy_matching=True
        )
        matcher = BankStatementMatcher(config)
        result = matcher.match_transactions([bank_record], [system_record])
        
        assert result.matched_count == 1
        assert result.matches[0].match_type == 'fuzzy'
    
    def test_fuzzy_match_with_similar_counterparty(self):
        """测试相似往来单位名称的模糊匹配"""
        bank_record = BankRecord(
            id="B001",
            transaction_date=date(2024, 1, 15),
            description="收款",
            amount=Decimal("1000.00"),
            balance=Decimal("5000.00"),
            transaction_type="CREDIT",
            counterparty="北京ABC科技有限公司"
        )
        
        system_record = TransactionRecord(
            id="S001",
            date=date(2024, 1, 15),
            type=TransactionType.INCOME,
            amount=Decimal("1000.00"),
            counterparty_id="C001",
            description="北京ABC科技公司",  # 名称略有不同
            category="销售收入",
            status=TransactionStatus.COMPLETED,
            created_at=datetime.now(),
            updated_at=datetime.now()
        )
        
        config = MatchConfig(
            counterparty_similarity_threshold=0.7,
            enable_fuzzy_matching=True
        )
        matcher = BankStatementMatcher(config)
        result = matcher.match_transactions([bank_record], [system_record])
        
        assert result.matched_count == 1
        assert result.matches[0].match_type in ['exact', 'fuzzy']
    
    def test_fuzzy_match_disabled(self):
        """测试禁用模糊匹配时只进行精确匹配"""
        bank_record = BankRecord(
            id="B001",
            transaction_date=date(2024, 1, 15),
            description="收款",
            amount=Decimal("1000.00"),
            balance=Decimal("5000.00"),
            transaction_type="CREDIT",
            counterparty="ABC公司"
        )
        
        system_record = TransactionRecord(
            id="S001",
            date=date(2024, 1, 17),  # 日期不同
            type=TransactionType.INCOME,
            amount=Decimal("1000.00"),
            counterparty_id="C001",
            description="ABC公司",
            category="销售收入",
            status=TransactionStatus.COMPLETED,
            created_at=datetime.now(),
            updated_at=datetime.now()
        )
        
        config = MatchConfig(enable_fuzzy_matching=False)
        matcher = BankStatementMatcher(config)
        result = matcher.match_transactions([bank_record], [system_record])
        
        assert result.matched_count == 0
    
    def test_fuzzy_match_selects_best_match(self):
        """测试模糊匹配选择最佳匹配"""
        bank_record = BankRecord(
            id="B001",
            transaction_date=date(2024, 1, 15),
            description="收款",
            amount=Decimal("1000.00"),
            balance=Decimal("5000.00"),
            transaction_type="CREDIT",
            counterparty="ABC公司"
        )
        
        # 两个可能的匹配，一个更接近
        system_record1 = TransactionRecord(
            id="S001",
            date=date(2024, 1, 17),  # 相差2天
            type=TransactionType.INCOME,
            amount=Decimal("1000.00"),
            counterparty_id="C001",
            description="ABC公司",
            category="销售收入",
            status=TransactionStatus.COMPLETED,
            created_at=datetime.now(),
            updated_at=datetime.now()
        )
        
        system_record2 = TransactionRecord(
            id="S002",
            date=date(2024, 1, 16),  # 相差1天，更接近
            type=TransactionType.INCOME,
            amount=Decimal("1000.00"),
            counterparty_id="C001",
            description="ABC公司",
            category="销售收入",
            status=TransactionStatus.COMPLETED,
            created_at=datetime.now(),
            updated_at=datetime.now()
        )
        
        config = MatchConfig(
            date_tolerance_days=3,
            enable_fuzzy_matching=True
        )
        matcher = BankStatementMatcher(config)
        result = matcher.match_transactions(
            [bank_record],
            [system_record1, system_record2]
        )
        
        assert result.matched_count == 1
        # 应该匹配日期更接近的记录
        assert result.matches[0].system_record.id == "S002"


class TestBankStatementMatcherDiscrepancies:
    """测试差异识别功能"""
    
    def test_identify_amount_discrepancy(self):
        """测试识别金额差异"""
        bank_record = BankRecord(
            id="B001",
            transaction_date=date(2024, 1, 15),
            description="收款",
            amount=Decimal("1000.00"),
            balance=Decimal("5000.00"),
            transaction_type="CREDIT",
            counterparty="ABC公司"
        )
        
        system_record = TransactionRecord(
            id="S001",
            date=date(2024, 1, 15),
            type=TransactionType.INCOME,
            amount=Decimal("1010.00"),  # 金额有差异
            counterparty_id="C001",
            description="ABC公司",
            category="销售收入",
            status=TransactionStatus.COMPLETED,
            created_at=datetime.now(),
            updated_at=datetime.now()
        )
        
        config = MatchConfig(
            amount_tolerance_percent=0.02,  # 2%容差，允许匹配
            enable_fuzzy_matching=True
        )
        matcher = BankStatementMatcher(config)
        match_result = matcher.match_transactions([bank_record], [system_record])
        discrepancies = matcher.identify_discrepancies(match_result)
        
        # 应该有一个金额差异
        amount_discrepancies = [
            d for d in discrepancies if d.type == DiscrepancyType.AMOUNT_DIFF
        ]
        assert len(amount_discrepancies) == 1
        assert amount_discrepancies[0].difference_amount == Decimal("10.00")
    
    def test_identify_missing_system_record(self):
        """测试识别系统记录缺失"""
        bank_record = BankRecord(
            id="B001",
            transaction_date=date(2024, 1, 15),
            description="收款",
            amount=Decimal("1000.00"),
            balance=Decimal("5000.00"),
            transaction_type="CREDIT",
            counterparty="ABC公司"
        )
        
        matcher = BankStatementMatcher()
        match_result = matcher.match_transactions([bank_record], [])
        discrepancies = matcher.identify_discrepancies(match_result)
        
        # 应该有一个系统记录缺失的差异
        missing_system = [
            d for d in discrepancies if d.type == DiscrepancyType.MISSING_SYSTEM
        ]
        assert len(missing_system) == 1
        assert missing_system[0].bank_record.id == "B001"
        assert missing_system[0].system_record is None
    
    def test_identify_missing_bank_record(self):
        """测试识别银行流水缺失"""
        system_record = TransactionRecord(
            id="S001",
            date=date(2024, 1, 15),
            type=TransactionType.INCOME,
            amount=Decimal("1000.00"),
            counterparty_id="C001",
            description="ABC公司",
            category="销售收入",
            status=TransactionStatus.COMPLETED,
            created_at=datetime.now(),
            updated_at=datetime.now()
        )
        
        matcher = BankStatementMatcher()
        match_result = matcher.match_transactions([], [system_record])
        discrepancies = matcher.identify_discrepancies(match_result)
        
        # 应该有一个银行流水缺失的差异
        missing_bank = [
            d for d in discrepancies if d.type == DiscrepancyType.MISSING_BANK
        ]
        assert len(missing_bank) == 1
        assert missing_bank[0].system_record.id == "S001"
        assert missing_bank[0].bank_record is None
    
    def test_no_discrepancies_for_exact_matches(self):
        """测试精确匹配不产生差异"""
        bank_record = BankRecord(
            id="B001",
            transaction_date=date(2024, 1, 15),
            description="收款",
            amount=Decimal("1000.00"),
            balance=Decimal("5000.00"),
            transaction_type="CREDIT",
            counterparty="ABC公司"
        )
        
        system_record = TransactionRecord(
            id="S001",
            date=date(2024, 1, 15),
            type=TransactionType.INCOME,
            amount=Decimal("1000.00"),
            counterparty_id="C001",
            description="ABC公司",
            category="销售收入",
            status=TransactionStatus.COMPLETED,
            created_at=datetime.now(),
            updated_at=datetime.now()
        )
        
        matcher = BankStatementMatcher()
        match_result = matcher.match_transactions([bank_record], [system_record])
        discrepancies = matcher.identify_discrepancies(match_result)
        
        # 精确匹配不应该产生差异
        assert len(discrepancies) == 0


class TestBankStatementMatcherEdgeCases:
    """测试边界情况"""
    
    def test_empty_bank_records(self):
        """测试空银行流水列表"""
        system_record = TransactionRecord(
            id="S001",
            date=date(2024, 1, 15),
            type=TransactionType.INCOME,
            amount=Decimal("1000.00"),
            counterparty_id="C001",
            description="ABC公司",
            category="销售收入",
            status=TransactionStatus.COMPLETED,
            created_at=datetime.now(),
            updated_at=datetime.now()
        )
        
        matcher = BankStatementMatcher()
        result = matcher.match_transactions([], [system_record])
        
        assert result.matched_count == 0
        assert result.total_bank_records == 0
        assert result.total_system_records == 1
        assert len(result.unmatched_system_records) == 1
    
    def test_empty_system_records(self):
        """测试空系统记录列表"""
        bank_record = BankRecord(
            id="B001",
            transaction_date=date(2024, 1, 15),
            description="收款",
            amount=Decimal("1000.00"),
            balance=Decimal("5000.00"),
            transaction_type="CREDIT",
            counterparty="ABC公司"
        )
        
        matcher = BankStatementMatcher()
        result = matcher.match_transactions([bank_record], [])
        
        assert result.matched_count == 0
        assert result.total_bank_records == 1
        assert result.total_system_records == 0
        assert len(result.unmatched_bank_records) == 1
    
    def test_both_empty(self):
        """测试两个列表都为空"""
        matcher = BankStatementMatcher()
        result = matcher.match_transactions([], [])
        
        assert result.matched_count == 0
        assert result.total_bank_records == 0
        assert result.total_system_records == 0
        assert result.match_rate == 0.0
    
    def test_multiple_records_matching(self):
        """测试多条记录的匹配"""
        bank_records = [
            BankRecord(
                id=f"B{i:03d}",
                transaction_date=date(2024, 1, i+1),
                description="收款",
                amount=Decimal(f"{(i+1)*1000}.00"),
                balance=Decimal("5000.00"),
                transaction_type="CREDIT",
                counterparty=f"客户{i+1}"
            )
            for i in range(5)
        ]
        
        system_records = [
            TransactionRecord(
                id=f"S{i:03d}",
                date=date(2024, 1, i+1),
                type=TransactionType.INCOME,
                amount=Decimal(f"{(i+1)*1000}.00"),
                counterparty_id=f"C{i:03d}",
                description=f"客户{i+1}",
                category="销售收入",
                status=TransactionStatus.COMPLETED,
                created_at=datetime.now(),
                updated_at=datetime.now()
            )
            for i in range(5)
        ]
        
        matcher = BankStatementMatcher()
        result = matcher.match_transactions(bank_records, system_records)
        
        assert result.matched_count == 5
        assert len(result.unmatched_bank_records) == 0
        assert len(result.unmatched_system_records) == 0
        assert result.match_rate == 1.0
    
    def test_match_rate_calculation(self):
        """测试匹配率计算"""
        bank_records = [
            BankRecord(
                id="B001",
                transaction_date=date(2024, 1, 15),
                description="收款",
                amount=Decimal("1000.00"),
                balance=Decimal("5000.00"),
                transaction_type="CREDIT",
                counterparty="ABC公司"
            ),
            BankRecord(
                id="B002",
                transaction_date=date(2024, 1, 16),
                description="收款",
                amount=Decimal("2000.00"),
                balance=Decimal("7000.00"),
                transaction_type="CREDIT",
                counterparty="XYZ公司"
            )
        ]
        
        system_records = [
            TransactionRecord(
                id="S001",
                date=date(2024, 1, 15),
                type=TransactionType.INCOME,
                amount=Decimal("1000.00"),
                counterparty_id="C001",
                description="ABC公司",
                category="销售收入",
                status=TransactionStatus.COMPLETED,
                created_at=datetime.now(),
                updated_at=datetime.now()
            )
        ]
        
        matcher = BankStatementMatcher()
        result = matcher.match_transactions(bank_records, system_records)
        
        # 2条银行记录，1条匹配，匹配率应该是50%
        assert result.matched_count == 1
        assert result.match_rate == 0.5


class TestMatchConfig:
    """测试匹配配置"""
    
    def test_default_config(self):
        """测试默认配置"""
        config = MatchConfig()
        
        assert config.amount_tolerance_percent == 0.0
        assert config.amount_tolerance_absolute == Decimal("0.00")
        assert config.date_tolerance_days == 0
        assert config.counterparty_similarity_threshold == 0.8
        assert config.enable_fuzzy_matching is True
    
    def test_custom_config(self):
        """测试自定义配置"""
        config = MatchConfig(
            amount_tolerance_percent=0.05,
            amount_tolerance_absolute=Decimal("10.00"),
            date_tolerance_days=5,
            counterparty_similarity_threshold=0.7,
            enable_fuzzy_matching=False
        )
        
        assert config.amount_tolerance_percent == 0.05
        assert config.amount_tolerance_absolute == Decimal("10.00")
        assert config.date_tolerance_days == 5
        assert config.counterparty_similarity_threshold == 0.7
        assert config.enable_fuzzy_matching is False
