"""
ReconciliationAssistant Example Usage

This example demonstrates how to use the ReconciliationAssistant for:
1. Bank statement reconciliation
2. Customer statement generation
3. Supplier account reconciliation

The assistant provides a simple, unified interface for all reconciliation tasks.
"""

from datetime import date, datetime
from decimal import Decimal
from pathlib import Path
import tempfile

import pandas as pd

from small_accountant_v16.models.core_models import (
    TransactionRecord,
    TransactionType,
    TransactionStatus,
    Counterparty,
    CounterpartyType
)
from small_accountant_v16.reconciliation.reconciliation_assistant import (
    ReconciliationAssistant
)
from small_accountant_v16.reconciliation.bank_statement_matcher import MatchConfig
from small_accountant_v16.storage.transaction_storage import TransactionStorage
from small_accountant_v16.storage.counterparty_storage import CounterpartyStorage


def setup_demo_data():
    """设置演示数据"""
    print("=" * 60)
    print("设置演示数据...")
    print("=" * 60)
    
    # 创建临时目录
    temp_dir = tempfile.mkdtemp()
    
    # 初始化存储
    transaction_storage = TransactionStorage(temp_dir)
    counterparty_storage = CounterpartyStorage(temp_dir)
    
    # 添加往来单位
    customers = [
        Counterparty(
            id="C001",
            name="ABC科技公司",
            type=CounterpartyType.CUSTOMER,
            contact_person="张经理",
            phone="13800138000",
            email="zhang@abc.com",
            address="北京市朝阳区科技园",
            tax_id="110000000000001",
            created_at=datetime.now(),
            updated_at=datetime.now()
        ),
        Counterparty(
            id="C002",
            name="XYZ贸易公司",
            type=CounterpartyType.CUSTOMER,
            contact_person="李总",
            phone="13900139000",
            email="li@xyz.com",
            address="上海市浦东新区",
            tax_id="310000000000001",
            created_at=datetime.now(),
            updated_at=datetime.now()
        ),
    ]
    
    suppliers = [
        Counterparty(
            id="S001",
            name="优质原材料供应商",
            type=CounterpartyType.SUPPLIER,
            contact_person="王经理",
            phone="13700137000",
            email="wang@supplier.com",
            address="广州市天河区",
            tax_id="440000000000001",
            created_at=datetime.now(),
            updated_at=datetime.now()
        ),
    ]
    
    for customer in customers:
        counterparty_storage.add(customer)
        print(f"✓ 添加客户: {customer.name}")
    
    for supplier in suppliers:
        counterparty_storage.add(supplier)
        print(f"✓ 添加供应商: {supplier.name}")
    
    # 添加交易记录
    transactions = [
        # 客户收入
        TransactionRecord(
            id="T001",
            date=date(2024, 1, 15),
            type=TransactionType.INCOME,
            amount=Decimal("50000.00"),
            counterparty_id="C001",
            description="ABC科技公司",
            category="产品销售",
            status=TransactionStatus.COMPLETED,
            created_at=datetime.now(),
            updated_at=datetime.now()
        ),
        TransactionRecord(
            id="T002",
            date=date(2024, 1, 20),
            type=TransactionType.INCOME,
            amount=Decimal("30000.00"),
            counterparty_id="C002",
            description="XYZ贸易公司",
            category="产品销售",
            status=TransactionStatus.COMPLETED,
            created_at=datetime.now(),
            updated_at=datetime.now()
        ),
        TransactionRecord(
            id="T003",
            date=date(2024, 1, 25),
            type=TransactionType.INCOME,
            amount=Decimal("20000.00"),
            counterparty_id="C001",
            description="ABC科技公司",
            category="服务费",
            status=TransactionStatus.COMPLETED,
            created_at=datetime.now(),
            updated_at=datetime.now()
        ),
        # 供应商采购
        TransactionRecord(
            id="T004",
            date=date(2024, 1, 10),
            type=TransactionType.ORDER,
            amount=Decimal("15000.00"),
            counterparty_id="S001",
            description="优质原材料供应商",
            category="原材料采购",
            status=TransactionStatus.PENDING,
            created_at=datetime.now(),
            updated_at=datetime.now()
        ),
        TransactionRecord(
            id="T005",
            date=date(2024, 1, 12),
            type=TransactionType.EXPENSE,
            amount=Decimal("15000.00"),
            counterparty_id="S001",
            description="优质原材料供应商",
            category="原材料采购",
            status=TransactionStatus.COMPLETED,
            created_at=datetime.now(),
            updated_at=datetime.now()
        ),
        TransactionRecord(
            id="T006",
            date=date(2024, 1, 28),
            type=TransactionType.ORDER,
            amount=Decimal("8000.00"),
            counterparty_id="S001",
            description="优质原材料供应商",
            category="原材料采购",
            status=TransactionStatus.PENDING,
            created_at=datetime.now(),
            updated_at=datetime.now()
        ),
    ]
    
    for transaction in transactions:
        transaction_storage.add(transaction)
        print(f"✓ 添加交易: {transaction.description} - {transaction.amount}元")
    
    print()
    return temp_dir, transaction_storage, counterparty_storage


def create_sample_bank_statement(temp_dir):
    """创建示例银行流水文件"""
    print("=" * 60)
    print("创建示例银行流水文件...")
    print("=" * 60)
    
    file_path = Path(temp_dir) / "bank_statement_202401.xlsx"
    
    # 创建银行流水数据
    data = {
        '交易日期': [
            '2024-01-15',
            '2024-01-20',
            '2024-01-25',
            '2024-01-12',
            '2024-01-30'  # 这条记录在系统中不存在
        ],
        '往来单位': [
            'ABC科技公司',
            'XYZ贸易公司',
            'ABC科技公司',
            '优质原材料供应商',
            '其他公司'
        ],
        '金额': [
            50000.00,
            30000.00,
            20000.00,
            15000.00,
            5000.00
        ],
        '余额': [
            50000.00,
            80000.00,
            100000.00,
            85000.00,
            90000.00
        ],
        '摘要': [
            '产品销售收入',
            '产品销售收入',
            '服务费收入',
            '原材料采购付款',
            '其他支出'
        ]
    }
    
    df = pd.DataFrame(data)
    df.to_excel(file_path, index=False)
    
    print(f"✓ 银行流水文件已创建: {file_path}")
    print(f"  包含 {len(data['交易日期'])} 条银行流水记录")
    print()
    
    return str(file_path)


def demo_bank_reconciliation(assistant, bank_statement_file):
    """演示银行对账功能"""
    print("=" * 60)
    print("1. 银行对账演示")
    print("=" * 60)
    
    print("执行银行对账...")
    result = assistant.reconcile_bank_statement(bank_statement_file)
    
    print(f"\n对账结果:")
    print(f"  ✓ 匹配成功: {result.matched_count} 条")
    print(f"  ✗ 未匹配银行流水: {len(result.unmatched_bank_records)} 条")
    print(f"  ✗ 未匹配系统记录: {len(result.unmatched_system_records)} 条")
    print(f"  ⚠ 发现差异: {len(result.discrepancies)} 条")
    
    if result.discrepancies:
        print(f"\n差异详情:")
        for disc in result.discrepancies[:3]:  # 只显示前3条
            print(f"  - {disc.description}")
    
    print(f"\n✓ 差异报告已生成")
    print()


def demo_customer_statement(assistant):
    """演示客户对账单生成"""
    print("=" * 60)
    print("2. 客户对账单生成演示")
    print("=" * 60)
    
    print("为客户 ABC科技公司 生成对账单...")
    
    report_path = assistant.generate_customer_statement(
        customer_id="C001",
        start_date=date(2024, 1, 1),
        end_date=date(2024, 1, 31),
        opening_balance=Decimal("0.00")
    )
    
    print(f"✓ 客户对账单已生成: {Path(report_path).name}")
    print(f"  对账期间: 2024年1月1日 - 2024年1月31日")
    print(f"  客户名称: ABC科技公司")
    print(f"  对账单可直接发送给客户")
    print()


def demo_supplier_reconciliation(assistant):
    """演示供应商对账"""
    print("=" * 60)
    print("3. 供应商对账演示")
    print("=" * 60)
    
    print("对供应商 优质原材料供应商 进行对账...")
    
    result = assistant.reconcile_supplier_accounts(
        supplier_id="S001",
        start_date=date(2024, 1, 1),
        end_date=date(2024, 1, 31)
    )
    
    print(f"\n对账结果:")
    print(f"  ✓ 订单与付款匹配: {result.matched_count} 条")
    print(f"  ⚠ 未付款订单: {len(result.unmatched_bank_records)} 条")
    print(f"  ⚠ 未匹配订单的付款: {len(result.unmatched_system_records)} 条")
    
    if result.unmatched_bank_records:
        print(f"\n未付款订单详情:")
        for record in result.unmatched_bank_records:
            print(f"  - {record.transaction_date}: {record.description} - {record.amount}元")
    
    if result.discrepancies:
        print(f"\n✓ 供应商对账报告已生成")
    
    print()


def demo_advanced_features(assistant, temp_dir):
    """演示高级功能"""
    print("=" * 60)
    print("4. 高级功能演示")
    print("=" * 60)
    
    # 演示模糊匹配配置
    print("配置模糊匹配参数...")
    fuzzy_config = MatchConfig(
        amount_tolerance_percent=0.01,  # 1%金额容差
        date_tolerance_days=3,  # 3天日期容差
        enable_fuzzy_matching=True
    )
    
    fuzzy_assistant = ReconciliationAssistant(
        transaction_storage=assistant.transaction_storage,
        counterparty_storage=assistant.counterparty_storage,
        output_dir=temp_dir,
        match_config=fuzzy_config
    )
    
    print(f"  ✓ 金额容差: 1%")
    print(f"  ✓ 日期容差: 3天")
    print(f"  ✓ 启用模糊匹配")
    
    # 演示列名识别
    print(f"\n支持的银行流水列名格式:")
    print(f"  - 日期列: 日期、交易日期、时间、date、transaction_date")
    print(f"  - 金额列: 金额、交易金额、发生额、amount")
    print(f"  - 往来单位: 往来单位、对方户名、对方账户、counterparty")
    print(f"  - 描述列: 摘要、备注、说明、description")
    
    print(f"\n✓ 系统会自动识别Excel列名，无需严格模板")
    print()


def main():
    """主函数"""
    print("\n")
    print("╔" + "=" * 58 + "╗")
    print("║" + " " * 10 + "ReconciliationAssistant 使用演示" + " " * 15 + "║")
    print("║" + " " * 15 + "快速对账助手" + " " * 28 + "║")
    print("╚" + "=" * 58 + "╝")
    print()
    
    # 设置演示数据
    temp_dir, transaction_storage, counterparty_storage = setup_demo_data()
    
    # 创建银行流水文件
    bank_statement_file = create_sample_bank_statement(temp_dir)
    
    # 初始化对账助手
    print("=" * 60)
    print("初始化对账助手...")
    print("=" * 60)
    assistant = ReconciliationAssistant(
        transaction_storage=transaction_storage,
        counterparty_storage=counterparty_storage,
        output_dir=temp_dir
    )
    print("✓ 对账助手初始化完成")
    print()
    
    # 演示各项功能
    demo_bank_reconciliation(assistant, bank_statement_file)
    demo_customer_statement(assistant)
    demo_supplier_reconciliation(assistant)
    demo_advanced_features(assistant, temp_dir)
    
    # 总结
    print("=" * 60)
    print("演示完成！")
    print("=" * 60)
    print()
    print("ReconciliationAssistant 提供了三大核心功能：")
    print()
    print("1. 银行对账 (reconcile_bank_statement)")
    print("   - 自动导入银行流水Excel文件")
    print("   - 智能匹配系统交易记录")
    print("   - 识别并报告差异")
    print("   - 生成专业的差异报告")
    print()
    print("2. 客户对账单 (generate_customer_statement)")
    print("   - 生成指定期间的客户对账单")
    print("   - 包含期初余额、交易明细、期末余额")
    print("   - 格式专业，可直接发送给客户")
    print()
    print("3. 供应商对账 (reconcile_supplier_accounts)")
    print("   - 核对采购订单和付款记录")
    print("   - 识别未付款订单")
    print("   - 生成供应商对账报告")
    print()
    print("特点：")
    print("  ✓ 简单易用 - 不需要专业IT知识")
    print("  ✓ 自动化 - 自动匹配和识别差异")
    print("  ✓ 智能识别 - 支持多种Excel列名格式")
    print("  ✓ 模糊匹配 - 支持金额和日期容差")
    print("  ✓ 专业输出 - 生成格式化的Excel报表")
    print()
    print(f"所有报表已保存到: {temp_dir}")
    print()


if __name__ == "__main__":
    main()
