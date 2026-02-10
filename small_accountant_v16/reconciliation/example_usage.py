"""
Example usage of BankStatementMatcher

This script demonstrates how to use the BankStatementMatcher to reconcile
bank statements with system transaction records.
"""

from datetime import date, datetime
from decimal import Decimal

import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from models.core_models import (
    BankRecord,
    TransactionRecord,
    TransactionType,
    TransactionStatus,
    DiscrepancyType
)
from reconciliation.bank_statement_matcher import (
    BankStatementMatcher,
    MatchConfig
)


def example_exact_matching():
    """示例：精确匹配"""
    print("=" * 60)
    print("示例1：精确匹配")
    print("=" * 60)
    
    # 创建银行流水记录
    bank_records = [
        BankRecord(
            id="B001",
            transaction_date=date(2024, 1, 15),
            description="收款",
            amount=Decimal("10000.00"),
            balance=Decimal("50000.00"),
            transaction_type="CREDIT",
            counterparty="北京ABC科技有限公司"
        ),
        BankRecord(
            id="B002",
            transaction_date=date(2024, 1, 16),
            description="付款",
            amount=Decimal("5000.00"),
            balance=Decimal("45000.00"),
            transaction_type="DEBIT",
            counterparty="上海XYZ供应商"
        )
    ]
    
    # 创建系统交易记录
    system_records = [
        TransactionRecord(
            id="S001",
            date=date(2024, 1, 15),
            type=TransactionType.INCOME,
            amount=Decimal("10000.00"),
            counterparty_id="C001",
            description="北京ABC科技有限公司",
            category="销售收入",
            status=TransactionStatus.COMPLETED,
            created_at=datetime.now(),
            updated_at=datetime.now()
        ),
        TransactionRecord(
            id="S002",
            date=date(2024, 1, 16),
            type=TransactionType.EXPENSE,
            amount=Decimal("5000.00"),
            counterparty_id="S001",
            description="上海XYZ供应商",
            category="采购支出",
            status=TransactionStatus.COMPLETED,
            created_at=datetime.now(),
            updated_at=datetime.now()
        )
    ]
    
    # 使用默认配置进行匹配
    matcher = BankStatementMatcher()
    result = matcher.match_transactions(bank_records, system_records)
    
    print(f"\n匹配结果：")
    print(f"  总银行记录数：{result.total_bank_records}")
    print(f"  总系统记录数：{result.total_system_records}")
    print(f"  成功匹配数：{result.matched_count}")
    print(f"  匹配率：{result.match_rate * 100:.1f}%")
    print(f"  未匹配银行记录：{len(result.unmatched_bank_records)}")
    print(f"  未匹配系统记录：{len(result.unmatched_system_records)}")
    
    for i, match in enumerate(result.matches, 1):
        print(f"\n  匹配 {i}:")
        print(f"    银行记录：{match.bank_record.id} - {match.bank_record.counterparty} - {match.bank_record.amount}")
        print(f"    系统记录：{match.system_record.id} - {match.system_record.description} - {match.system_record.amount}")
        print(f"    匹配类型：{match.match_type}")
        print(f"    置信度：{match.confidence * 100:.1f}%")


def example_fuzzy_matching_with_amount_tolerance():
    """示例：带金额容差的模糊匹配"""
    print("\n" + "=" * 60)
    print("示例2：带金额容差的模糊匹配")
    print("=" * 60)
    
    # 银行流水金额为 10000.00
    bank_records = [
        BankRecord(
            id="B001",
            transaction_date=date(2024, 1, 15),
            description="收款",
            amount=Decimal("10000.00"),
            balance=Decimal("50000.00"),
            transaction_type="CREDIT",
            counterparty="ABC公司"
        )
    ]
    
    # 系统记录金额为 10050.00（差50元，0.5%差异）
    system_records = [
        TransactionRecord(
            id="S001",
            date=date(2024, 1, 15),
            type=TransactionType.INCOME,
            amount=Decimal("10050.00"),
            counterparty_id="C001",
            description="ABC公司",
            category="销售收入",
            status=TransactionStatus.COMPLETED,
            created_at=datetime.now(),
            updated_at=datetime.now()
        )
    ]
    
    # 配置1%的金额容差
    config = MatchConfig(
        amount_tolerance_percent=0.01,  # 1%容差
        enable_fuzzy_matching=True
    )
    matcher = BankStatementMatcher(config)
    result = matcher.match_transactions(bank_records, system_records)
    
    print(f"\n配置：金额容差 1%")
    print(f"匹配结果：{result.matched_count} 条匹配")
    
    if result.matches:
        match = result.matches[0]
        print(f"\n匹配详情：")
        print(f"  银行金额：{match.bank_record.amount}")
        print(f"  系统金额：{match.system_record.amount}")
        print(f"  差额：{abs(match.bank_record.amount - match.system_record.amount)}")
        print(f"  匹配类型：{match.match_type}")
        print(f"  置信度：{match.confidence * 100:.1f}%")
    
    # 识别差异
    discrepancies = matcher.identify_discrepancies(result)
    print(f"\n差异数量：{len(discrepancies)}")
    for disc in discrepancies:
        print(f"  差异类型：{disc.type.value}")
        print(f"  差异金额：{disc.difference_amount}")
        print(f"  描述：{disc.description}")


def example_fuzzy_matching_with_date_tolerance():
    """示例：带日期容差的模糊匹配"""
    print("\n" + "=" * 60)
    print("示例3：带日期容差的模糊匹配")
    print("=" * 60)
    
    # 银行流水日期为 1月15日
    bank_records = [
        BankRecord(
            id="B001",
            transaction_date=date(2024, 1, 15),
            description="收款",
            amount=Decimal("10000.00"),
            balance=Decimal("50000.00"),
            transaction_type="CREDIT",
            counterparty="ABC公司"
        )
    ]
    
    # 系统记录日期为 1月17日（相差2天）
    system_records = [
        TransactionRecord(
            id="S001",
            date=date(2024, 1, 17),
            type=TransactionType.INCOME,
            amount=Decimal("10000.00"),
            counterparty_id="C001",
            description="ABC公司",
            category="销售收入",
            status=TransactionStatus.COMPLETED,
            created_at=datetime.now(),
            updated_at=datetime.now()
        )
    ]
    
    # 配置3天的日期容差
    config = MatchConfig(
        date_tolerance_days=3,
        enable_fuzzy_matching=True
    )
    matcher = BankStatementMatcher(config)
    result = matcher.match_transactions(bank_records, system_records)
    
    print(f"\n配置：日期容差 3 天")
    print(f"匹配结果：{result.matched_count} 条匹配")
    
    if result.matches:
        match = result.matches[0]
        print(f"\n匹配详情：")
        print(f"  银行日期：{match.bank_record.transaction_date}")
        print(f"  系统日期：{match.system_record.date}")
        print(f"  日期差：{abs((match.bank_record.transaction_date - match.system_record.date).days)} 天")
        print(f"  匹配类型：{match.match_type}")
        print(f"  置信度：{match.confidence * 100:.1f}%")


def example_discrepancy_identification():
    """示例：差异识别"""
    print("\n" + "=" * 60)
    print("示例4：差异识别")
    print("=" * 60)
    
    # 3条银行流水
    bank_records = [
        BankRecord(
            id="B001",
            transaction_date=date(2024, 1, 15),
            description="收款",
            amount=Decimal("10000.00"),
            balance=Decimal("50000.00"),
            transaction_type="CREDIT",
            counterparty="ABC公司"
        ),
        BankRecord(
            id="B002",
            transaction_date=date(2024, 1, 16),
            description="收款",
            amount=Decimal("5000.00"),
            balance=Decimal("55000.00"),
            transaction_type="CREDIT",
            counterparty="DEF公司"
        ),
        BankRecord(
            id="B003",
            transaction_date=date(2024, 1, 17),
            description="付款",
            amount=Decimal("3000.00"),
            balance=Decimal("52000.00"),
            transaction_type="DEBIT",
            counterparty="GHI供应商"
        )
    ]
    
    # 2条系统记录（缺少一条）
    system_records = [
        TransactionRecord(
            id="S001",
            date=date(2024, 1, 15),
            type=TransactionType.INCOME,
            amount=Decimal("10000.00"),
            counterparty_id="C001",
            description="ABC公司",
            category="销售收入",
            status=TransactionStatus.COMPLETED,
            created_at=datetime.now(),
            updated_at=datetime.now()
        ),
        TransactionRecord(
            id="S002",
            date=date(2024, 1, 18),  # 日期不同
            type=TransactionType.EXPENSE,
            amount=Decimal("2000.00"),  # 金额不同
            counterparty_id="S001",
            description="JKL供应商",  # 名称不同
            category="采购支出",
            status=TransactionStatus.COMPLETED,
            created_at=datetime.now(),
            updated_at=datetime.now()
        )
    ]
    
    matcher = BankStatementMatcher()
    result = matcher.match_transactions(bank_records, system_records)
    discrepancies = matcher.identify_discrepancies(result)
    
    print(f"\n匹配统计：")
    print(f"  成功匹配：{result.matched_count} 条")
    print(f"  未匹配银行记录：{len(result.unmatched_bank_records)} 条")
    print(f"  未匹配系统记录：{len(result.unmatched_system_records)} 条")
    
    print(f"\n差异详情（共 {len(discrepancies)} 条）：")
    for i, disc in enumerate(discrepancies, 1):
        print(f"\n  差异 {i}:")
        print(f"    ID: {disc.id}")
        print(f"    类型: {disc.type.value}")
        print(f"    差异金额: {disc.difference_amount}")
        print(f"    描述: {disc.description}")


def example_comprehensive_reconciliation():
    """示例：综合对账场景"""
    print("\n" + "=" * 60)
    print("示例5：综合对账场景")
    print("=" * 60)
    
    # 模拟一个月的银行流水
    bank_records = [
        BankRecord(
            id="B001",
            transaction_date=date(2024, 1, 5),
            description="收款",
            amount=Decimal("50000.00"),
            balance=Decimal("150000.00"),
            transaction_type="CREDIT",
            counterparty="客户A"
        ),
        BankRecord(
            id="B002",
            transaction_date=date(2024, 1, 10),
            description="付款",
            amount=Decimal("20000.00"),
            balance=Decimal("130000.00"),
            transaction_type="DEBIT",
            counterparty="供应商B"
        ),
        BankRecord(
            id="B003",
            transaction_date=date(2024, 1, 15),
            description="收款",
            amount=Decimal("30000.00"),
            balance=Decimal("160000.00"),
            transaction_type="CREDIT",
            counterparty="客户C"
        ),
        BankRecord(
            id="B004",
            transaction_date=date(2024, 1, 20),
            description="付款",
            amount=Decimal("15000.00"),
            balance=Decimal("145000.00"),
            transaction_type="DEBIT",
            counterparty="供应商D"
        ),
        BankRecord(
            id="B005",
            transaction_date=date(2024, 1, 25),
            description="收款",
            amount=Decimal("25000.00"),
            balance=Decimal("170000.00"),
            transaction_type="CREDIT",
            counterparty="客户E"
        )
    ]
    
    # 模拟系统交易记录（有些记录有差异）
    system_records = [
        TransactionRecord(
            id="S001",
            date=date(2024, 1, 5),
            type=TransactionType.INCOME,
            amount=Decimal("50000.00"),
            counterparty_id="C001",
            description="客户A",
            category="销售收入",
            status=TransactionStatus.COMPLETED,
            created_at=datetime.now(),
            updated_at=datetime.now()
        ),
        TransactionRecord(
            id="S002",
            date=date(2024, 1, 11),  # 日期差1天
            type=TransactionType.EXPENSE,
            amount=Decimal("20000.00"),
            counterparty_id="S001",
            description="供应商B",
            category="采购支出",
            status=TransactionStatus.COMPLETED,
            created_at=datetime.now(),
            updated_at=datetime.now()
        ),
        TransactionRecord(
            id="S003",
            date=date(2024, 1, 15),
            type=TransactionType.INCOME,
            amount=Decimal("30500.00"),  # 金额差500元
            counterparty_id="C002",
            description="客户C",
            category="销售收入",
            status=TransactionStatus.COMPLETED,
            created_at=datetime.now(),
            updated_at=datetime.now()
        ),
        # 缺少 B004 对应的记录
        TransactionRecord(
            id="S005",
            date=date(2024, 1, 25),
            type=TransactionType.INCOME,
            amount=Decimal("25000.00"),
            counterparty_id="C003",
            description="客户E",
            category="销售收入",
            status=TransactionStatus.COMPLETED,
            created_at=datetime.now(),
            updated_at=datetime.now()
        )
    ]
    
    # 使用灵活的配置进行对账
    config = MatchConfig(
        amount_tolerance_percent=0.02,  # 2%金额容差
        date_tolerance_days=2,  # 2天日期容差
        enable_fuzzy_matching=True
    )
    matcher = BankStatementMatcher(config)
    result = matcher.match_transactions(bank_records, system_records)
    discrepancies = matcher.identify_discrepancies(result)
    
    print(f"\n对账统计：")
    print(f"  银行流水总数：{result.total_bank_records}")
    print(f"  系统记录总数：{result.total_system_records}")
    print(f"  成功匹配：{result.matched_count} 条")
    print(f"  匹配率：{result.match_rate * 100:.1f}%")
    
    print(f"\n匹配详情：")
    for i, match in enumerate(result.matches, 1):
        print(f"  {i}. {match.bank_record.id} <-> {match.system_record.id}")
        print(f"     类型: {match.match_type}, 置信度: {match.confidence * 100:.1f}%")
    
    print(f"\n差异汇总（共 {len(discrepancies)} 条）：")
    amount_diff_count = sum(1 for d in discrepancies if d.type == DiscrepancyType.AMOUNT_DIFF)
    missing_system_count = sum(1 for d in discrepancies if d.type == DiscrepancyType.MISSING_SYSTEM)
    missing_bank_count = sum(1 for d in discrepancies if d.type == DiscrepancyType.MISSING_BANK)
    
    print(f"  金额差异：{amount_diff_count} 条")
    print(f"  系统记录缺失：{missing_system_count} 条")
    print(f"  银行流水缺失：{missing_bank_count} 条")
    
    print(f"\n差异详情：")
    for disc in discrepancies:
        print(f"  - {disc.id}: {disc.type.value}")
        print(f"    {disc.description}")


if __name__ == "__main__":
    # 运行所有示例
    example_exact_matching()
    example_fuzzy_matching_with_amount_tolerance()
    example_fuzzy_matching_with_date_tolerance()
    example_discrepancy_identification()
    example_comprehensive_reconciliation()
    
    print("\n" + "=" * 60)
    print("所有示例运行完成！")
    print("=" * 60)
