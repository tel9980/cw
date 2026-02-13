"""
Example usage of ReconciliationReportGenerator

This script demonstrates how to use the ReconciliationReportGenerator to create
professional Excel reports for bank reconciliation discrepancies and customer statements.
"""

from datetime import date, datetime
from decimal import Decimal
from pathlib import Path

import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from small_accountant_v16.models.core_models import (
    BankRecord,
    TransactionRecord,
    TransactionType,
    TransactionStatus,
    Discrepancy,
    DiscrepancyType,
    Counterparty,
    CounterpartyType
)
from small_accountant_v16.reconciliation.bank_statement_matcher import (
    BankStatementMatcher,
    MatchConfig
)
from small_accountant_v16.reconciliation.reconciliation_report_generator import (
    ReconciliationReportGenerator,
    CustomerAccountData
)


def example_generate_discrepancy_report():
    """示例：生成差异报告"""
    print("=" * 60)
    print("示例1：生成银行对账差异报告")
    print("=" * 60)
    
    # 准备银行流水数据
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
            description="收款",
            amount=Decimal("5000.00"),
            balance=Decimal("55000.00"),
            transaction_type="CREDIT",
            counterparty="上海XYZ贸易公司"
        ),
        BankRecord(
            id="B003",
            transaction_date=date(2024, 1, 17),
            description="付款",
            amount=Decimal("3000.00"),
            balance=Decimal("52000.00"),
            transaction_type="DEBIT",
            counterparty="深圳DEF供应商"
        )
    ]
    
    # 准备系统交易记录
    system_records = [
        TransactionRecord(
            id="S001",
            date=date(2024, 1, 15),
            type=TransactionType.INCOME,
            amount=Decimal("10050.00"),  # 金额有差异
            counterparty_id="C001",
            description="北京ABC科技有限公司",
            category="销售收入",
            status=TransactionStatus.COMPLETED,
            created_at=datetime.now(),
            updated_at=datetime.now()
        ),
        # 缺少 B002 对应的记录
        TransactionRecord(
            id="S003",
            date=date(2024, 1, 17),
            type=TransactionType.EXPENSE,
            amount=Decimal("3000.00"),
            counterparty_id="S001",
            description="深圳DEF供应商",
            category="采购支出",
            status=TransactionStatus.COMPLETED,
            created_at=datetime.now(),
            updated_at=datetime.now()
        ),
        TransactionRecord(
            id="S004",
            date=date(2024, 1, 18),
            type=TransactionType.INCOME,
            amount=Decimal("8000.00"),
            counterparty_id="C002",
            description="广州GHI客户",
            category="销售收入",
            status=TransactionStatus.COMPLETED,
            created_at=datetime.now(),
            updated_at=datetime.now()
        )
    ]
    
    # 步骤1：使用BankStatementMatcher进行对账
    print("\n步骤1：执行银行对账...")
    config = MatchConfig(
        amount_tolerance_percent=0.01,  # 1%金额容差
        date_tolerance_days=2,
        enable_fuzzy_matching=True
    )
    matcher = BankStatementMatcher(config)
    match_result = matcher.match_transactions(bank_records, system_records)
    
    print(f"  匹配结果：{match_result.matched_count} 条匹配")
    print(f"  未匹配银行记录：{len(match_result.unmatched_bank_records)} 条")
    print(f"  未匹配系统记录：{len(match_result.unmatched_system_records)} 条")
    
    # 步骤2：识别差异
    print("\n步骤2：识别差异...")
    discrepancies = matcher.identify_discrepancies(match_result)
    print(f"  发现差异：{len(discrepancies)} 条")
    
    for disc in discrepancies:
        print(f"    - {disc.id}: {disc.type.value} - {disc.difference_amount}")
    
    # 步骤3：生成差异报告Excel
    print("\n步骤3：生成差异报告Excel...")
    output_dir = Path("output/reconciliation_reports")
    generator = ReconciliationReportGenerator(output_dir=str(output_dir))
    
    filepath = generator.save_discrepancy_report(
        discrepancies,
        filename="银行对账差异报告_示例.xlsx"
    )
    
    print(f"  ✓ 差异报告已生成：{filepath}")
    print(f"  报告包含：")
    print(f"    - 差异明细表（含金额、日期、往来单位等）")
    print(f"    - 差异类型统计")
    print(f"    - 专业格式化（颜色标记、边框、对齐）")


def example_generate_customer_statement():
    """示例：生成客户对账单"""
    print("\n" + "=" * 60)
    print("示例2：生成客户对账单")
    print("=" * 60)
    
    # 准备客户信息
    customer = Counterparty(
        id="C001",
        name="北京ABC科技有限公司",
        type=CounterpartyType.CUSTOMER,
        contact_person="张经理",
        phone="13800138000",
        email="zhang@abc.com",
        address="北京市朝阳区建国路88号",
        tax_id="91110000XXXXXXXX",
        created_at=datetime.now(),
        updated_at=datetime.now()
    )
    
    # 准备交易记录
    transactions = [
        TransactionRecord(
            id="T001",
            date=date(2024, 1, 5),
            type=TransactionType.INCOME,
            amount=Decimal("50000.00"),
            counterparty_id="C001",
            description="销售产品A",
            category="产品销售",
            status=TransactionStatus.COMPLETED,
            created_at=datetime.now(),
            updated_at=datetime.now()
        ),
        TransactionRecord(
            id="T002",
            date=date(2024, 1, 12),
            type=TransactionType.INCOME,
            amount=Decimal("30000.00"),
            counterparty_id="C001",
            description="销售产品B",
            category="产品销售",
            status=TransactionStatus.COMPLETED,
            created_at=datetime.now(),
            updated_at=datetime.now()
        ),
        TransactionRecord(
            id="T003",
            date=date(2024, 1, 18),
            type=TransactionType.EXPENSE,
            amount=Decimal("5000.00"),
            counterparty_id="C001",
            description="产品退货",
            category="销售退款",
            status=TransactionStatus.COMPLETED,
            created_at=datetime.now(),
            updated_at=datetime.now()
        ),
        TransactionRecord(
            id="T004",
            date=date(2024, 1, 25),
            type=TransactionType.INCOME,
            amount=Decimal("20000.00"),
            counterparty_id="C001",
            description="销售服务",
            category="服务收入",
            status=TransactionStatus.COMPLETED,
            created_at=datetime.now(),
            updated_at=datetime.now()
        )
    ]
    
    # 准备客户对账数据
    customer_data = CustomerAccountData(
        customer=customer,
        transactions=transactions,
        start_date=date(2024, 1, 1),
        end_date=date(2024, 1, 31),
        opening_balance=Decimal("0.00"),
        closing_balance=Decimal("95000.00")  # 50000 + 30000 - 5000 + 20000
    )
    
    print(f"\n客户信息：")
    print(f"  名称：{customer.name}")
    print(f"  编号：{customer.id}")
    print(f"  联系人：{customer.contact_person}")
    print(f"  对账期间：{customer_data.start_date} 至 {customer_data.end_date}")
    
    print(f"\n交易统计：")
    total_income = sum(t.amount for t in transactions if t.type == TransactionType.INCOME)
    total_expense = sum(t.amount for t in transactions if t.type == TransactionType.EXPENSE)
    print(f"  交易笔数：{len(transactions)} 笔")
    print(f"  总收入：¥{total_income:,.2f}")
    print(f"  总支出：¥{total_expense:,.2f}")
    print(f"  期末余额：¥{customer_data.closing_balance:,.2f}")
    
    # 生成客户对账单Excel
    print(f"\n生成客户对账单Excel...")
    output_dir = Path("output/reconciliation_reports")
    generator = ReconciliationReportGenerator(output_dir=str(output_dir))
    
    filepath = generator.save_customer_statement(customer_data)
    
    print(f"  ✓ 客户对账单已生成：{filepath}")
    print(f"  对账单包含：")
    print(f"    - 客户基本信息（名称、联系人、电话等）")
    print(f"    - 对账期间和生成日期")
    print(f"    - 期初余额")
    print(f"    - 交易明细（日期、类型、摘要、收入、支出、余额）")
    print(f"    - 期末余额")
    print(f"    - 汇总统计（笔数、总收入、总支出）")
    print(f"    - 客户签字确认栏")
    print(f"  可直接发送给客户进行对账确认！")


def example_comprehensive_workflow():
    """示例：完整的对账工作流"""
    print("\n" + "=" * 60)
    print("示例3：完整的对账工作流")
    print("=" * 60)
    
    print("\n场景：月末对账，需要完成以下工作：")
    print("  1. 导入银行流水")
    print("  2. 与系统记录进行对账")
    print("  3. 生成差异报告供内部审核")
    print("  4. 生成客户对账单发送给客户")
    
    # 模拟数据
    bank_records = [
        BankRecord(
            id="B001",
            transaction_date=date(2024, 1, 10),
            description="收款",
            amount=Decimal("100000.00"),
            balance=Decimal("200000.00"),
            transaction_type="CREDIT",
            counterparty="客户A"
        ),
        BankRecord(
            id="B002",
            transaction_date=date(2024, 1, 15),
            description="收款",
            amount=Decimal("50000.00"),
            balance=Decimal("250000.00"),
            transaction_type="CREDIT",
            counterparty="客户B"
        )
    ]
    
    system_records = [
        TransactionRecord(
            id="S001",
            date=date(2024, 1, 10),
            type=TransactionType.INCOME,
            amount=Decimal("100000.00"),
            counterparty_id="C001",
            description="客户A",
            category="销售收入",
            status=TransactionStatus.COMPLETED,
            created_at=datetime.now(),
            updated_at=datetime.now()
        ),
        TransactionRecord(
            id="S002",
            date=date(2024, 1, 15),
            type=TransactionType.INCOME,
            amount=Decimal("50000.00"),
            counterparty_id="C002",
            description="客户B",
            category="销售收入",
            status=TransactionStatus.COMPLETED,
            created_at=datetime.now(),
            updated_at=datetime.now()
        )
    ]
    
    print("\n步骤1：执行银行对账...")
    matcher = BankStatementMatcher()
    match_result = matcher.match_transactions(bank_records, system_records)
    print(f"  ✓ 对账完成：匹配率 {match_result.match_rate * 100:.1f}%")
    
    print("\n步骤2：生成差异报告...")
    discrepancies = matcher.identify_discrepancies(match_result)
    output_dir = Path("output/reconciliation_reports")
    generator = ReconciliationReportGenerator(output_dir=str(output_dir))
    
    if discrepancies:
        disc_filepath = generator.save_discrepancy_report(discrepancies)
        print(f"  ✓ 差异报告已生成：{disc_filepath}")
    else:
        print(f"  ✓ 无差异，对账完全匹配！")
    
    print("\n步骤3：生成客户对账单...")
    # 为每个客户生成对账单
    customers = [
        Counterparty(
            id="C001",
            name="客户A",
            type=CounterpartyType.CUSTOMER,
            contact_person="李经理",
            phone="13900139000",
            email="li@customer-a.com",
            address="北京市",
            tax_id="91110000XXXXXXXX",
            created_at=datetime.now(),
            updated_at=datetime.now()
        )
    ]
    
    for customer in customers:
        # 筛选该客户的交易记录
        customer_transactions = [
            t for t in system_records if t.counterparty_id == customer.id
        ]
        
        if customer_transactions:
            customer_data = CustomerAccountData(
                customer=customer,
                transactions=customer_transactions,
                start_date=date(2024, 1, 1),
                end_date=date(2024, 1, 31),
                opening_balance=Decimal("0.00"),
                closing_balance=sum(t.amount for t in customer_transactions)
            )
            
            stmt_filepath = generator.save_customer_statement(customer_data)
            print(f"  ✓ {customer.name} 对账单已生成：{stmt_filepath}")
    
    print("\n✓ 月末对账工作完成！")
    print(f"  所有报告保存在：{output_dir}")


if __name__ == "__main__":
    # 运行所有示例
    example_generate_discrepancy_report()
    example_generate_customer_statement()
    example_comprehensive_workflow()
    
    print("\n" + "=" * 60)
    print("所有示例运行完成！")
    print("=" * 60)
    print("\n提示：")
    print("  - 生成的Excel文件保存在 output/reconciliation_reports/ 目录")
    print("  - 可以用Microsoft Excel或WPS Office打开查看")
    print("  - 差异报告用于内部审核")
    print("  - 客户对账单可直接发送给客户确认")
