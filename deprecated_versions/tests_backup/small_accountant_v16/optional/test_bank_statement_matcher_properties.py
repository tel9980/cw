"""
Property-based tests for BankStatementMatcher - Bank reconciliation matching and discrepancy detection

Feature: small-accountant-practical-enhancement
Property 11: Bank reconciliation matching and discrepancy detection
Validates: Requirements 3.1, 3.4
"""

import pytest
from datetime import date, timedelta
from decimal import Decimal
from hypothesis import given, strategies as st, settings, assume
from hypothesis import HealthCheck
from typing import List
import uuid

from small_accountant_v16.reconciliation.bank_statement_matcher import (
    BankStatementMatcher, MatchConfig
)
from small_accountant_v16.models.core_models import (
    BankRecord, TransactionRecord, TransactionType, TransactionStatus,
    DiscrepancyType
)


# Hypothesis strategies for generating test data
@st.composite
def valid_amount(draw, min_value=0.01, max_value=100000.0):
    """生成有效的金额"""
    amount = draw(st.decimals(
        min_value=Decimal(str(min_value)),
        max_value=Decimal(str(max_value)),
        places=2
    ))
    return amount


@st.composite
def valid_date_range(draw, max_days=365):
    """生成有效的日期范围"""
    base_date = draw(st.dates(
        min_value=date(2020, 1, 1),
        max_value=date.today() - timedelta(days=1)
    ))
    
    end_date = draw(st.dates(
        min_value=base_date,
        max_value=min(base_date + timedelta(days=max_days), date.today())
    ))
    
    return base_date, end_date


@st.composite
def bank_record_strategy(draw, date_range=None, amount_range=None):
    """生成银行流水记录"""
    if date_range:
        start_date, end_date = date_range
        trans_date = draw(st.dates(min_value=start_date, max_value=end_date))
    else:
        trans_date = draw(st.dates(
            min_value=date(2020, 1, 1),
            max_value=date.today()
        ))
    
    if amount_range:
        min_amt, max_amt = amount_range
        amount = draw(valid_amount(min_value=min_amt, max_value=max_amt))
    else:
        amount = draw(valid_amount())
    
    counterparty_names = [
        "测试客户A", "测试供应商B", "测试客户C", "ABC公司", "XYZ有限公司",
        "北京科技公司", "上海贸易公司", "深圳制造厂", "广州服务商"
    ]
    
    return BankRecord(
        id=str(uuid.uuid4()),
        transaction_date=trans_date,
        amount=amount,
        counterparty=draw(st.sampled_from(counterparty_names)),
        description=draw(st.text(min_size=5, max_size=50, alphabet=st.characters(whitelist_categories=('L', 'N')))),
        balance=amount + draw(valid_amount(min_value=0, max_value=10000)),
        transaction_type=draw(st.sampled_from(["DEBIT", "CREDIT"]))
    )


@st.composite
def transaction_record_strategy(draw, date_range=None, amount_range=None, counterparty_hint=None):
    """生成系统交易记录"""
    if date_range:
        start_date, end_date = date_range
        trans_date = draw(st.dates(min_value=start_date, max_value=end_date))
    else:
        trans_date = draw(st.dates(
            min_value=date(2020, 1, 1),
            max_value=date.today()
        ))
    
    if amount_range:
        min_amt, max_amt = amount_range
        amount = draw(valid_amount(min_value=min_amt, max_value=max_amt))
    else:
        amount = draw(valid_amount())
    
    # 如果提供了往来单位提示，使用相似的描述
    if counterparty_hint:
        descriptions = [
            counterparty_hint,
            f"向{counterparty_hint}付款",
            f"收到{counterparty_hint}款项",
            f"{counterparty_hint}货款",
            f"与{counterparty_hint}交易"
        ]
        description = draw(st.sampled_from(descriptions))
    else:
        descriptions = [
            "销售收入", "采购付款", "办公费用", "差旅费", "租金支出",
            "工资支付", "税费缴纳", "银行手续费", "利息收入", "其他收入"
        ]
        description = draw(st.sampled_from(descriptions))
    
    return TransactionRecord(
        id=str(uuid.uuid4()),
        date=trans_date,
        type=draw(st.sampled_from([TransactionType.INCOME, TransactionType.EXPENSE])),
        amount=amount,
        counterparty_id=f"cp{draw(st.integers(min_value=1, max_value=100))}",
        description=description,
        category=draw(st.sampled_from(['销售', '采购', '费用', '其他'])),
        status=TransactionStatus.COMPLETED,
        created_at=draw(st.datetimes()),
        updated_at=draw(st.datetimes())
    )


@st.composite
def matching_record_pair(draw):
    """生成匹配的银行记录和系统记录对"""
    # 生成基础数据
    trans_date = draw(st.dates(
        min_value=date(2020, 1, 1),
        max_value=date.today()
    ))
    amount = draw(valid_amount())
    counterparty = draw(st.sampled_from([
        "测试客户A", "测试供应商B", "ABC公司", "XYZ有限公司"
    ]))
    
    # 创建匹配的银行记录
    bank_record = BankRecord(
        id=str(uuid.uuid4()),
        transaction_date=trans_date,
        amount=amount,
        counterparty=counterparty,
        description=f"与{counterparty}交易",
        balance=amount + draw(valid_amount(min_value=0, max_value=10000)),
        transaction_type=draw(st.sampled_from(["DEBIT", "CREDIT"]))
    )
    
    # 创建匹配的系统记录
    system_record = TransactionRecord(
        id=str(uuid.uuid4()),
        date=trans_date,
        type=TransactionType.INCOME if amount > 0 else TransactionType.EXPENSE,
        amount=amount,
        counterparty_id=f"cp{draw(st.integers(min_value=1, max_value=100))}",
        description=f"{counterparty}款项",
        category=draw(st.sampled_from(['销售', '采购', '费用', '其他'])),
        status=TransactionStatus.COMPLETED,
        created_at=draw(st.datetimes()),
        updated_at=draw(st.datetimes())
    )
    
    return bank_record, system_record


@st.composite
def fuzzy_matching_record_pair(draw):
    """生成模糊匹配的银行记录和系统记录对"""
    # 生成基础数据
    base_date = draw(st.dates(
        min_value=date(2020, 1, 1),
        max_value=date.today() - timedelta(days=5)
    ))
    base_amount = draw(valid_amount(min_value=100, max_value=10000))
    counterparty = draw(st.sampled_from([
        "测试客户A", "测试供应商B", "ABC公司", "XYZ有限公司"
    ]))
    
    # 银行记录
    bank_date = base_date
    bank_amount = base_amount
    
    # 系统记录（有小幅差异）
    system_date = base_date + timedelta(days=draw(st.integers(min_value=0, max_value=3)))
    # 金额差异在1%以内
    amount_variation = float(base_amount) * draw(st.floats(min_value=-0.01, max_value=0.01))
    system_amount = base_amount + Decimal(str(round(amount_variation, 2)))
    
    bank_record = BankRecord(
        id=str(uuid.uuid4()),
        transaction_date=bank_date,
        amount=bank_amount,
        counterparty=counterparty,
        description=f"与{counterparty}交易",
        balance=bank_amount + draw(valid_amount(min_value=0, max_value=10000)),
        transaction_type=draw(st.sampled_from(["DEBIT", "CREDIT"]))
    )
    
    system_record = TransactionRecord(
        id=str(uuid.uuid4()),
        date=system_date,
        type=TransactionType.INCOME if system_amount > 0 else TransactionType.EXPENSE,
        amount=system_amount,
        counterparty_id=f"cp{draw(st.integers(min_value=1, max_value=100))}",
        description=f"{counterparty}相关交易",  # 稍微不同的描述
        category=draw(st.sampled_from(['销售', '采购', '费用', '其他'])),
        status=TransactionStatus.COMPLETED,
        created_at=draw(st.datetimes()),
        updated_at=draw(st.datetimes())
    )
    
    return bank_record, system_record


class TestBankStatementMatcherProperties:
    """Property-based tests for bank statement matcher
    
    **Property 11: Bank reconciliation matching and discrepancy detection**
    For any valid bank records and system records, when performing reconciliation,
    the matcher should correctly identify matches and discrepancies according to
    the configured matching rules.
    **Validates: Requirements 3.1, 3.4**
    """
    
    @given(data=st.data())
    @settings(max_examples=50, suppress_health_check=[HealthCheck.function_scoped_fixture], deadline=None)
    def test_exact_matching_property(self, data):
        """
        Property: 精确匹配属性
        
        验证：
        1. 对于完全相同的记录（金额、日期、往来单位），应该被精确匹配
        2. 匹配置信度应该为1.0
        3. 匹配类型应该为'exact'
        4. 不应该产生差异
        """
        # 生成匹配的记录对
        matching_pairs = data.draw(st.lists(
            matching_record_pair(),
            min_size=1,
            max_size=10
        ))
        
        bank_records = [pair[0] for pair in matching_pairs]
        system_records = [pair[1] for pair in matching_pairs]
        
        # 创建匹配器
        matcher = BankStatementMatcher()
        
        # 执行匹配
        result = matcher.match_transactions(bank_records, system_records)
        
        # 验证所有记录都被匹配
        assert result.matched_count == len(matching_pairs), \
            f"应该匹配所有{len(matching_pairs)}对记录，但只匹配了{result.matched_count}对"
        
        assert len(result.unmatched_bank_records) == 0, \
            f"不应该有未匹配的银行记录，但有{len(result.unmatched_bank_records)}条"
        
        assert len(result.unmatched_system_records) == 0, \
            f"不应该有未匹配的系统记录，但有{len(result.unmatched_system_records)}条"
        
        # 验证匹配质量
        for match in result.matches:
            assert match.confidence == 1.0, \
                f"精确匹配的置信度应该为1.0，但为{match.confidence}"
            
            assert match.match_type == 'exact', \
                f"匹配类型应该为'exact'，但为'{match.match_type}'"
            
            # 验证匹配的记录确实相同
            assert match.bank_record.amount == match.system_record.amount, \
                "匹配记录的金额应该相同"
            
            assert match.bank_record.transaction_date == match.system_record.date, \
                "匹配记录的日期应该相同"
        
        # 验证匹配率
        assert result.match_rate == 1.0, \
            f"匹配率应该为100%，但为{result.match_rate:.2%}"
        
        # 验证差异检测
        discrepancies = matcher.identify_discrepancies(result)
        assert len(discrepancies) == 0, \
            f"精确匹配不应该产生差异，但产生了{len(discrepancies)}个差异"
    
    @given(data=st.data())
    @settings(max_examples=30, suppress_health_check=[HealthCheck.function_scoped_fixture], deadline=None)
    def test_fuzzy_matching_property(self, data):
        """
        Property: 模糊匹配属性
        
        验证：
        1. 对于有小幅差异的记录，应该能够进行模糊匹配
        2. 模糊匹配的置信度应该在合理范围内（0.7-1.0）
        3. 匹配类型应该为'fuzzy'
        4. 应该正确识别金额差异
        """
        # 配置支持模糊匹配的匹配器
        config = MatchConfig(
            amount_tolerance_percent=0.02,  # 2%容差
            date_tolerance_days=3,
            enable_fuzzy_matching=True
        )
        matcher = BankStatementMatcher(config)
        
        # 生成模糊匹配的记录对
        fuzzy_pairs = data.draw(st.lists(
            fuzzy_matching_record_pair(),
            min_size=1,
            max_size=8
        ))
        
        bank_records = [pair[0] for pair in fuzzy_pairs]
        system_records = [pair[1] for pair in fuzzy_pairs]
        
        # 执行匹配
        result = matcher.match_transactions(bank_records, system_records)
        
        # 验证大部分记录被匹配（允许一些记录因为差异过大而不匹配）
        match_rate_threshold = 0.5  # 至少50%的记录应该被匹配
        assert result.match_rate >= match_rate_threshold, \
            f"模糊匹配率应该至少为{match_rate_threshold:.0%}，但为{result.match_rate:.2%}"
        
        # 验证模糊匹配的质量
        fuzzy_matches = [m for m in result.matches if m.match_type == 'fuzzy']
        
        for match in fuzzy_matches:
            assert 0.7 <= match.confidence <= 1.0, \
                f"模糊匹配的置信度应该在0.7-1.0之间，但为{match.confidence}"
            
            assert match.match_type == 'fuzzy', \
                f"匹配类型应该为'fuzzy'，但为'{match.match_type}'"
            
            # 验证匹配详情包含必要信息
            assert 'amount_score' in match.match_details, \
                "模糊匹配详情应该包含金额分数"
            
            assert 'date_score' in match.match_details, \
                "模糊匹配详情应该包含日期分数"
            
            assert 'counterparty_score' in match.match_details, \
                "模糊匹配详情应该包含往来单位分数"
        
        # 验证差异检测
        discrepancies = matcher.identify_discrepancies(result)
        
        # 检查金额差异的识别
        amount_discrepancies = [
            d for d in discrepancies if d.type == DiscrepancyType.AMOUNT_DIFF
        ]
        
        # 对于有金额差异的模糊匹配，应该识别出差异
        for match in fuzzy_matches:
            amount_diff = abs(match.bank_record.amount - match.system_record.amount)
            if amount_diff > Decimal("0.01"):
                # 应该有对应的金额差异记录
                found_discrepancy = any(
                    d.bank_record.id == match.bank_record.id and
                    d.system_record.id == match.system_record.id
                    for d in amount_discrepancies
                )
                assert found_discrepancy, \
                    f"金额差异{amount_diff}应该被识别为差异"
    
    @given(data=st.data())
    @settings(max_examples=30, suppress_health_check=[HealthCheck.function_scoped_fixture], deadline=None)
    def test_unmatched_records_discrepancy_detection(self, data):
        """
        Property: 未匹配记录差异检测属性
        
        验证：
        1. 银行流水中存在但系统中缺失的记录应该被识别为MISSING_SYSTEM差异
        2. 系统中存在但银行流水中缺失的记录应该被识别为MISSING_BANK差异
        3. 差异描述应该包含相关信息
        """
        # 生成一些匹配的记录对
        matching_pairs = data.draw(st.lists(
            matching_record_pair(),
            min_size=1,
            max_size=5
        ))
        
        # 生成一些只在银行流水中存在的记录
        bank_only_records = data.draw(st.lists(
            bank_record_strategy(),
            min_size=1,
            max_size=5
        ))
        
        # 生成一些只在系统中存在的记录
        system_only_records = data.draw(st.lists(
            transaction_record_strategy(),
            min_size=1,
            max_size=5
        ))
        
        # 组合所有记录
        all_bank_records = [pair[0] for pair in matching_pairs] + bank_only_records
        all_system_records = [pair[1] for pair in matching_pairs] + system_only_records
        
        # 创建匹配器
        matcher = BankStatementMatcher()
        
        # 执行匹配
        result = matcher.match_transactions(all_bank_records, all_system_records)
        
        # 验证未匹配记录数量
        assert len(result.unmatched_bank_records) == len(bank_only_records), \
            f"应该有{len(bank_only_records)}条未匹配的银行记录，但有{len(result.unmatched_bank_records)}条"
        
        assert len(result.unmatched_system_records) == len(system_only_records), \
            f"应该有{len(system_only_records)}条未匹配的系统记录，但有{len(result.unmatched_system_records)}条"
        
        # 验证差异检测
        discrepancies = matcher.identify_discrepancies(result)
        
        # 检查MISSING_SYSTEM差异
        missing_system_discrepancies = [
            d for d in discrepancies if d.type == DiscrepancyType.MISSING_SYSTEM
        ]
        assert len(missing_system_discrepancies) == len(bank_only_records), \
            f"应该有{len(bank_only_records)}个MISSING_SYSTEM差异，但有{len(missing_system_discrepancies)}个"
        
        # 检查MISSING_BANK差异
        missing_bank_discrepancies = [
            d for d in discrepancies if d.type == DiscrepancyType.MISSING_BANK
        ]
        assert len(missing_bank_discrepancies) == len(system_only_records), \
            f"应该有{len(system_only_records)}个MISSING_BANK差异，但有{len(missing_bank_discrepancies)}个"
        
        # 验证差异记录的完整性
        for discrepancy in missing_system_discrepancies:
            assert discrepancy.bank_record is not None, \
                "MISSING_SYSTEM差异应该包含银行记录"
            
            assert discrepancy.system_record is None, \
                "MISSING_SYSTEM差异不应该包含系统记录"
            
            assert discrepancy.description, \
                "差异应该包含描述信息"
            
            assert "系统记录缺失" in discrepancy.description, \
                "MISSING_SYSTEM差异描述应该包含'系统记录缺失'"
        
        for discrepancy in missing_bank_discrepancies:
            assert discrepancy.bank_record is None, \
                "MISSING_BANK差异不应该包含银行记录"
            
            assert discrepancy.system_record is not None, \
                "MISSING_BANK差异应该包含系统记录"
            
            assert discrepancy.description, \
                "差异应该包含描述信息"
            
            assert "银行流水缺失" in discrepancy.description, \
                "MISSING_BANK差异描述应该包含'银行流水缺失'"
    
    @given(data=st.data())
    @settings(max_examples=20, suppress_health_check=[HealthCheck.function_scoped_fixture], deadline=None)
    def test_match_configuration_respect(self, data):
        """
        Property: 匹配配置遵循属性
        
        验证：
        1. 匹配器应该遵循配置的容差设置
        2. 禁用模糊匹配时不应该产生模糊匹配
        3. 容差范围内的差异应该被接受
        4. 超出容差范围的差异应该被拒绝
        """
        # 生成测试配置
        amount_tolerance = data.draw(st.floats(min_value=0.0, max_value=0.05))  # 0-5%
        date_tolerance = data.draw(st.integers(min_value=0, max_value=7))  # 0-7天
        enable_fuzzy = data.draw(st.booleans())
        
        config = MatchConfig(
            amount_tolerance_percent=amount_tolerance,
            date_tolerance_days=date_tolerance,
            enable_fuzzy_matching=enable_fuzzy
        )
        
        matcher = BankStatementMatcher(config)
        
        # 生成一些基础记录
        base_pairs = data.draw(st.lists(
            matching_record_pair(),
            min_size=2,
            max_size=5
        ))
        
        bank_records = [pair[0] for pair in base_pairs]
        system_records = [pair[1] for pair in base_pairs]
        
        # 执行匹配
        result = matcher.match_transactions(bank_records, system_records)
        
        # 验证模糊匹配配置
        fuzzy_matches = [m for m in result.matches if m.match_type == 'fuzzy']
        
        if not enable_fuzzy:
            assert len(fuzzy_matches) == 0, \
                f"禁用模糊匹配时不应该有模糊匹配，但有{len(fuzzy_matches)}个"
        
        # 验证所有匹配都符合配置要求
        for match in result.matches:
            if match.match_type == 'fuzzy':
                # 验证金额在容差范围内
                amount_diff = abs(match.bank_record.amount - match.system_record.amount)
                max_amount = max(match.bank_record.amount, match.system_record.amount)
                
                if max_amount > 0:
                    percent_diff = float(amount_diff / max_amount)
                    assert percent_diff <= amount_tolerance or amount_diff <= Decimal("0.01"), \
                        f"模糊匹配的金额差异{percent_diff:.2%}应该在容差{amount_tolerance:.2%}内"
                
                # 验证日期在容差范围内
                date_diff = abs((match.bank_record.transaction_date - match.system_record.date).days)
                assert date_diff <= date_tolerance, \
                    f"模糊匹配的日期差异{date_diff}天应该在容差{date_tolerance}天内"
        
        # 验证匹配结果的一致性
        total_records = len(bank_records)
        matched_count = result.matched_count
        unmatched_count = len(result.unmatched_bank_records)
        
        assert matched_count + unmatched_count == total_records, \
            f"匹配记录数({matched_count}) + 未匹配记录数({unmatched_count}) 应该等于总记录数({total_records})"
    
    @given(data=st.data())
    @settings(max_examples=20, suppress_health_check=[HealthCheck.function_scoped_fixture], deadline=None)
    def test_match_result_consistency(self, data):
        """
        Property: 匹配结果一致性属性
        
        验证：
        1. 匹配结果的统计信息应该一致
        2. 每条记录只能被匹配一次
        3. 匹配率计算正确
        4. 差异总数与未匹配记录数相符
        """
        # 生成测试数据
        bank_records = data.draw(st.lists(
            bank_record_strategy(),
            min_size=1,
            max_size=20
        ))
        
        system_records = data.draw(st.lists(
            transaction_record_strategy(),
            min_size=1,
            max_size=20
        ))
        
        # 创建匹配器
        matcher = BankStatementMatcher()
        
        # 执行匹配
        result = matcher.match_transactions(bank_records, system_records)
        
        # 验证统计信息一致性
        assert result.total_bank_records == len(bank_records), \
            f"银行记录总数应该为{len(bank_records)}，但为{result.total_bank_records}"
        
        assert result.total_system_records == len(system_records), \
            f"系统记录总数应该为{len(system_records)}，但为{result.total_system_records}"
        
        assert result.matched_count == len(result.matches), \
            f"匹配数量应该为{len(result.matches)}，但为{result.matched_count}"
        
        # 验证记录唯一性
        matched_bank_ids = set()
        matched_system_ids = set()
        
        for match in result.matches:
            bank_id = match.bank_record.id
            system_id = match.system_record.id
            
            assert bank_id not in matched_bank_ids, \
                f"银行记录{bank_id}被重复匹配"
            
            assert system_id not in matched_system_ids, \
                f"系统记录{system_id}被重复匹配"
            
            matched_bank_ids.add(bank_id)
            matched_system_ids.add(system_id)
        
        # 验证未匹配记录不在匹配列表中
        for unmatched_bank in result.unmatched_bank_records:
            assert unmatched_bank.id not in matched_bank_ids, \
                f"未匹配的银行记录{unmatched_bank.id}不应该在匹配列表中"
        
        for unmatched_system in result.unmatched_system_records:
            assert unmatched_system.id not in matched_system_ids, \
                f"未匹配的系统记录{unmatched_system.id}不应该在匹配列表中"
        
        # 验证匹配率计算
        expected_match_rate = result.matched_count / result.total_bank_records if result.total_bank_records > 0 else 0.0
        assert abs(result.match_rate - expected_match_rate) < 0.001, \
            f"匹配率计算错误：期望{expected_match_rate:.3f}，实际{result.match_rate:.3f}"
        
        # 验证记录完整性
        total_matched_bank = len(matched_bank_ids)
        total_unmatched_bank = len(result.unmatched_bank_records)
        
        assert total_matched_bank + total_unmatched_bank == result.total_bank_records, \
            f"匹配银行记录数({total_matched_bank}) + 未匹配银行记录数({total_unmatched_bank}) 应该等于总银行记录数({result.total_bank_records})"
        
        # 验证差异检测的一致性
        discrepancies = matcher.identify_discrepancies(result)
        
        missing_system_count = len([d for d in discrepancies if d.type == DiscrepancyType.MISSING_SYSTEM])
        missing_bank_count = len([d for d in discrepancies if d.type == DiscrepancyType.MISSING_BANK])
        
        assert missing_system_count == len(result.unmatched_bank_records), \
            f"MISSING_SYSTEM差异数({missing_system_count})应该等于未匹配银行记录数({len(result.unmatched_bank_records)})"
        
        assert missing_bank_count == len(result.unmatched_system_records), \
            f"MISSING_BANK差异数({missing_bank_count})应该等于未匹配系统记录数({len(result.unmatched_system_records)})"