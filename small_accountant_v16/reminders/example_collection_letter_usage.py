"""
Example usage of CollectionLetterGenerator

Demonstrates how to generate collection letters for overdue receivables
using three different templates:
- First Reminder (30 days overdue)
- Second Notice (60 days overdue)
- Final Warning (90 days overdue)
"""

from datetime import date, timedelta
from decimal import Decimal
from pathlib import Path

from small_accountant_v16.models.core_models import Counterparty, CounterpartyType
from small_accountant_v16.reminders.collection_letter_generator import (
    CollectionLetterGenerator,
    LetterTemplate
)


def create_sample_customers():
    """Create sample customers for demonstration"""
    from datetime import datetime
    
    customers = [
        Counterparty(
            id="CUST001",
            name="优质客户有限公司",
            type=CounterpartyType.CUSTOMER,
            contact_person="李总",
            phone="021-87654321",
            email="lizong@youzhikehu.com",
            address="上海市浦东新区客户路456号",
            tax_id="91310000123456789X",
            created_at=datetime.now(),
            updated_at=datetime.now()
        ),
        Counterparty(
            id="CUST002",
            name="长期合作伙伴公司",
            type=CounterpartyType.CUSTOMER,
            contact_person="王经理",
            phone="010-12345678",
            email="wangjingli@partner.com",
            address="北京市朝阳区合作路789号",
            tax_id="91110000987654321Y",
            created_at=datetime.now(),
            updated_at=datetime.now()
        ),
        Counterparty(
            id="CUST003",
            name="新兴科技股份有限公司",
            type=CounterpartyType.CUSTOMER,
            contact_person="张总监",
            phone="0755-88888888",
            email="zhangzj@xinxing.com",
            address="深圳市南山区科技园路321号",
            tax_id="91440300555555555Z",
            created_at=datetime.now(),
            updated_at=datetime.now()
        )
    ]
    
    return customers


def example_1_first_reminder():
    """
    Example 1: Generate a first reminder letter (30 days overdue)
    
    This is a polite reminder for customers who are slightly overdue.
    """
    print("\n" + "="*70)
    print("示例 1: 生成首次提醒催款函（逾期30天）")
    print("="*70)
    
    # Initialize generator with company information
    generator = CollectionLetterGenerator(
        company_name="示例科技有限公司",
        company_address="北京市海淀区中关村大街1号",
        company_phone="010-88888888",
        company_contact="财务部 - 陈经理",
        output_dir="collection_letters_demo"
    )
    
    # Get sample customer
    customers = create_sample_customers()
    customer = customers[0]
    
    # Generate first reminder letter
    overdue_days = 35
    amount = Decimal("50000.00")
    invoice_numbers = ["INV-2024-001", "INV-2024-002"]
    due_date = date.today() - timedelta(days=overdue_days)
    
    print(f"\n客户信息:")
    print(f"  名称: {customer.name}")
    print(f"  联系人: {customer.contact_person}")
    print(f"  电话: {customer.phone}")
    
    print(f"\n欠款信息:")
    print(f"  逾期天数: {overdue_days} 天")
    print(f"  欠款金额: ¥{amount:,.2f}")
    print(f"  发票号: {', '.join(invoice_numbers)}")
    print(f"  原到期日: {due_date.strftime('%Y年%m月%d日')}")
    
    # Generate letter
    filepath = generator.generate_collection_letter(
        customer=customer,
        overdue_days=overdue_days,
        amount=amount,
        invoice_numbers=invoice_numbers,
        due_date=due_date,
        template_type=LetterTemplate.FIRST_REMINDER
    )
    
    print(f"\n✓ 催款函已生成: {filepath}")
    print(f"  模板类型: 首次提醒（礼貌温和）")
    print(f"  文件大小: {Path(filepath).stat().st_size / 1024:.1f} KB")


def example_2_second_notice():
    """
    Example 2: Generate a second notice letter (60 days overdue)
    
    This is a firmer notice for customers who haven't responded to the first reminder.
    """
    print("\n" + "="*70)
    print("示例 2: 生成二次催收通知函（逾期60天）")
    print("="*70)
    
    # Initialize generator
    generator = CollectionLetterGenerator(
        company_name="示例科技有限公司",
        company_address="北京市海淀区中关村大街1号",
        company_phone="010-88888888",
        company_contact="财务部 - 陈经理",
        output_dir="collection_letters_demo"
    )
    
    # Get sample customer
    customers = create_sample_customers()
    customer = customers[1]
    
    # Generate second notice letter
    overdue_days = 68
    amount = Decimal("125000.50")
    invoice_numbers = ["INV-2024-003", "INV-2024-004", "INV-2024-005"]
    due_date = date.today() - timedelta(days=overdue_days)
    
    print(f"\n客户信息:")
    print(f"  名称: {customer.name}")
    print(f"  联系人: {customer.contact_person}")
    print(f"  电话: {customer.phone}")
    
    print(f"\n欠款信息:")
    print(f"  逾期天数: {overdue_days} 天")
    print(f"  欠款金额: ¥{amount:,.2f}")
    print(f"  发票号: {', '.join(invoice_numbers)}")
    print(f"  原到期日: {due_date.strftime('%Y年%m月%d日')}")
    
    # Generate letter
    filepath = generator.generate_collection_letter(
        customer=customer,
        overdue_days=overdue_days,
        amount=amount,
        invoice_numbers=invoice_numbers,
        due_date=due_date,
        template_type=LetterTemplate.SECOND_NOTICE
    )
    
    print(f"\n✓ 催款函已生成: {filepath}")
    print(f"  模板类型: 二次催收（语气更坚定）")
    print(f"  文件大小: {Path(filepath).stat().st_size / 1024:.1f} KB")
    print(f"  要求付款期限: 7个工作日内")


def example_3_final_warning():
    """
    Example 3: Generate a final warning letter (90+ days overdue)
    
    This is a firm final warning before legal action.
    """
    print("\n" + "="*70)
    print("示例 3: 生成最后催款通知函（逾期90天以上）")
    print("="*70)
    
    # Initialize generator
    generator = CollectionLetterGenerator(
        company_name="示例科技有限公司",
        company_address="北京市海淀区中关村大街1号",
        company_phone="010-88888888",
        company_contact="财务部 - 陈经理",
        output_dir="collection_letters_demo"
    )
    
    # Get sample customer
    customers = create_sample_customers()
    customer = customers[2]
    
    # Generate final warning letter
    overdue_days = 105
    amount = Decimal("280000.00")
    invoice_numbers = ["INV-2024-006", "INV-2024-007"]
    due_date = date.today() - timedelta(days=overdue_days)
    
    print(f"\n客户信息:")
    print(f"  名称: {customer.name}")
    print(f"  联系人: {customer.contact_person}")
    print(f"  电话: {customer.phone}")
    
    print(f"\n欠款信息:")
    print(f"  逾期天数: {overdue_days} 天 ⚠️")
    print(f"  欠款金额: ¥{amount:,.2f}")
    print(f"  发票号: {', '.join(invoice_numbers)}")
    print(f"  原到期日: {due_date.strftime('%Y年%m月%d日')}")
    
    # Generate letter
    filepath = generator.generate_collection_letter(
        customer=customer,
        overdue_days=overdue_days,
        amount=amount,
        invoice_numbers=invoice_numbers,
        due_date=due_date,
        template_type=LetterTemplate.FINAL_WARNING
    )
    
    print(f"\n✓ 催款函已生成: {filepath}")
    print(f"  模板类型: 最后通知（严肃警告）")
    print(f"  文件大小: {Path(filepath).stat().st_size / 1024:.1f} KB")
    print(f"  要求付款期限: 3个工作日内")
    print(f"  警告: 将采取法律行动 ⚠️")


def example_4_auto_template_selection():
    """
    Example 4: Automatic template selection based on overdue days
    
    The generator can automatically select the appropriate template
    based on how many days the payment is overdue.
    """
    print("\n" + "="*70)
    print("示例 4: 自动选择催款函模板")
    print("="*70)
    
    # Initialize generator
    generator = CollectionLetterGenerator(
        company_name="示例科技有限公司",
        company_address="北京市海淀区中关村大街1号",
        company_phone="010-88888888",
        company_contact="财务部 - 陈经理",
        output_dir="collection_letters_demo"
    )
    
    # Get sample customer
    customers = create_sample_customers()
    customer = customers[0]
    
    # Test different overdue periods
    test_cases = [
        (32, Decimal("10000.00"), "自动选择 -> 首次提醒"),
        (65, Decimal("20000.00"), "自动选择 -> 二次催收"),
        (95, Decimal("30000.00"), "自动选择 -> 最后通知")
    ]
    
    print("\n根据逾期天数自动选择模板:")
    print("-" * 70)
    
    for overdue_days, amount, description in test_cases:
        # Don't specify template_type - let it auto-select
        filepath = generator.generate_collection_letter(
            customer=customer,
            overdue_days=overdue_days,
            amount=amount,
            invoice_numbers=[f"INV-AUTO-{overdue_days}"]
        )
        
        print(f"\n逾期 {overdue_days} 天 -> {description}")
        print(f"  生成文件: {Path(filepath).name}")


def example_5_minimal_information():
    """
    Example 5: Generate letter with minimal information
    
    Demonstrates that the generator works even without optional information
    like invoice numbers and due dates.
    """
    print("\n" + "="*70)
    print("示例 5: 使用最少信息生成催款函")
    print("="*70)
    
    # Initialize generator with minimal company info
    generator = CollectionLetterGenerator(
        company_name="简单公司",
        output_dir="collection_letters_demo"
    )
    
    # Get sample customer
    customers = create_sample_customers()
    customer = customers[0]
    
    print(f"\n仅提供必需信息:")
    print(f"  客户: {customer.name}")
    print(f"  逾期天数: 45")
    print(f"  金额: ¥15,000.00")
    print(f"  发票号: 无")
    print(f"  到期日: 无")
    
    # Generate letter with minimal info
    filepath = generator.generate_collection_letter(
        customer=customer,
        overdue_days=45,
        amount=Decimal("15000.00")
        # No invoice_numbers, no due_date
    )
    
    print(f"\n✓ 催款函已生成: {filepath}")
    print(f"  说明: 即使没有发票号和到期日，催款函仍然可以正常生成")


def example_6_batch_generation():
    """
    Example 6: Batch generate letters for multiple customers
    
    Demonstrates how to generate collection letters for multiple
    overdue customers in a batch process.
    """
    print("\n" + "="*70)
    print("示例 6: 批量生成催款函")
    print("="*70)
    
    # Initialize generator
    generator = CollectionLetterGenerator(
        company_name="示例科技有限公司",
        company_address="北京市海淀区中关村大街1号",
        company_phone="010-88888888",
        company_contact="财务部 - 陈经理",
        output_dir="collection_letters_demo"
    )
    
    # Get all sample customers
    customers = create_sample_customers()
    
    # Simulate overdue receivables data
    overdue_receivables = [
        {
            "customer": customers[0],
            "overdue_days": 35,
            "amount": Decimal("50000.00"),
            "invoices": ["INV-2024-001"]
        },
        {
            "customer": customers[1],
            "overdue_days": 68,
            "amount": Decimal("125000.50"),
            "invoices": ["INV-2024-003", "INV-2024-004"]
        },
        {
            "customer": customers[2],
            "overdue_days": 105,
            "amount": Decimal("280000.00"),
            "invoices": ["INV-2024-006"]
        }
    ]
    
    print(f"\n批量处理 {len(overdue_receivables)} 个逾期客户:")
    print("-" * 70)
    
    generated_files = []
    total_amount = Decimal("0")
    
    for i, receivable in enumerate(overdue_receivables, 1):
        customer = receivable["customer"]
        overdue_days = receivable["overdue_days"]
        amount = receivable["amount"]
        invoices = receivable["invoices"]
        
        print(f"\n{i}. {customer.name}")
        print(f"   逾期: {overdue_days}天 | 金额: ¥{amount:,.2f}")
        
        filepath = generator.generate_collection_letter(
            customer=customer,
            overdue_days=overdue_days,
            amount=amount,
            invoice_numbers=invoices,
            due_date=date.today() - timedelta(days=overdue_days)
        )
        
        generated_files.append(filepath)
        total_amount += amount
        
        print(f"   ✓ 已生成: {Path(filepath).name}")
    
    print("\n" + "="*70)
    print(f"批量生成完成:")
    print(f"  生成文件数: {len(generated_files)}")
    print(f"  总欠款金额: ¥{total_amount:,.2f}")
    print(f"  输出目录: {generator.output_dir}")


def main():
    """Run all examples"""
    print("\n" + "="*70)
    print("催款函生成器 - 使用示例")
    print("="*70)
    print("\n本示例演示如何使用CollectionLetterGenerator生成专业的催款函")
    print("支持三种模板：首次提醒、二次催收、最后通知")
    
    try:
        # Run all examples
        example_1_first_reminder()
        example_2_second_notice()
        example_3_final_warning()
        example_4_auto_template_selection()
        example_5_minimal_information()
        example_6_batch_generation()
        
        print("\n" + "="*70)
        print("所有示例运行完成！")
        print("="*70)
        print(f"\n生成的催款函保存在: collection_letters_demo/")
        print("请使用Microsoft Word或WPS Office打开查看")
        
    except ImportError as e:
        print(f"\n❌ 错误: {e}")
        print("请确保已安装python-docx库: pip install python-docx")
    except Exception as e:
        print(f"\n❌ 发生错误: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
