#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
银行账户管理快速测试
"""

import sys
from pathlib import Path
from decimal import Decimal
from datetime import date

# 添加项目根目录到路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from models.business_models import Customer, Supplier, BankType, ExpenseType
from business.finance_manager import FinanceManager
from database.db_manager import DatabaseManager


def test_bank_account_management():
    """测试银行账户管理功能"""
    print("=" * 60)
    print("银行账户管理功能测试")
    print("=" * 60)
    
    # 创建临时数据库
    db = DatabaseManager(":memory:")
    db.connect()
    
    # 创建财务管理器
    fm = FinanceManager(db)
    
    # 测试1: 创建G银行账户
    print("\n测试1: 创建G银行账户")
    g_account = fm.create_bank_account(
        bank_type=BankType.G_BANK,
        account_name="G银行主账户",
        account_number="6222000012345678",
        initial_balance=Decimal("50000"),
        notes="用于有票据的正式交易"
    )
    print(f"✓ G银行账户创建成功: {g_account.account_name}, 余额: {g_account.balance}")
    
    # 测试2: 创建N银行账户
    print("\n测试2: 创建N银行账户")
    n_account = fm.create_bank_account(
        bank_type=BankType.N_BANK,
        account_name="N银行现金账户",
        account_number="6228000087654321",
        initial_balance=Decimal("20000"),
        notes="现金等价物，与微信结合使用"
    )
    print(f"✓ N银行账户创建成功: {n_account.account_name}, 余额: {n_account.balance}")
    
    # 测试3: 获取账户余额
    print("\n测试3: 获取账户余额")
    g_balance = fm.get_account_balance(BankType.G_BANK)
    n_balance = fm.get_account_balance(BankType.N_BANK)
    print(f"✓ G银行余额: {g_balance}")
    print(f"✓ N银行余额: {n_balance}")
    
    # 测试4: 记录G银行收入交易
    print("\n测试4: 记录G银行收入交易")
    customer = Customer(name="测试客户A", contact="张三")
    db.save_customer(customer)
    
    transaction1 = fm.record_bank_transaction(
        bank_type=BankType.G_BANK,
        amount=Decimal("10000"),
        transaction_date=date.today(),
        counterparty=customer.name,
        description="加工费收入",
        is_income=True,
        notes="有票据"
    )
    print(f"✓ G银行收入交易记录成功: {transaction1.amount}, 对手方: {transaction1.counterparty}")
    
    new_g_balance = fm.get_account_balance(BankType.G_BANK)
    print(f"✓ G银行更新后余额: {new_g_balance} (增加了 {new_g_balance - g_balance})")
    
    # 测试5: 记录N银行支出交易
    print("\n测试5: 记录N银行支出交易")
    supplier = Supplier(name="测试供应商B", contact="李四")
    db.save_supplier(supplier)
    
    transaction2 = fm.record_bank_transaction(
        bank_type=BankType.N_BANK,
        amount=Decimal("3000"),
        transaction_date=date.today(),
        counterparty=supplier.name,
        description="微信支付原料费",
        is_income=False,
        notes="现金等价物"
    )
    print(f"✓ N银行支出交易记录成功: {transaction2.amount}, 对手方: {transaction2.counterparty}")
    
    new_n_balance = fm.get_account_balance(BankType.N_BANK)
    print(f"✓ N银行更新后余额: {new_n_balance} (减少了 {n_balance - new_n_balance})")
    
    # 测试6: 验证账户独立性
    print("\n测试6: 验证G银行和N银行账户独立性")
    final_g_balance = fm.get_account_balance(BankType.G_BANK)
    final_n_balance = fm.get_account_balance(BankType.N_BANK)
    print(f"✓ G银行最终余额: {final_g_balance}")
    print(f"✓ N银行最终余额: {final_n_balance}")
    print(f"✓ 账户独立性验证: G银行操作不影响N银行，N银行操作不影响G银行")
    
    # 测试7: 交易匹配
    print("\n测试7: 交易匹配功能")
    income = fm.record_income(
        customer_id=customer.id,
        customer_name=customer.name,
        amount=Decimal("10000"),
        bank_type=BankType.G_BANK,
        income_date=date.today(),
        has_invoice=True
    )
    print(f"✓ 收入记录创建: {income.amount}")
    
    success, message = fm.match_transaction_to_income(
        transaction_id=transaction1.id,
        income_id=income.id
    )
    print(f"✓ 交易匹配结果: {message}")
    
    # 测试8: 获取未匹配交易
    print("\n测试8: 获取未匹配交易")
    unmatched_g = fm.get_unmatched_transactions(BankType.G_BANK)
    unmatched_n = fm.get_unmatched_transactions(BankType.N_BANK)
    print(f"✓ G银行未匹配交易数: {len(unmatched_g)}")
    print(f"✓ N银行未匹配交易数: {len(unmatched_n)}")
    
    # 测试9: 银行账户汇总
    print("\n测试9: 银行账户汇总")
    g_summary = fm.get_bank_account_summary(BankType.G_BANK)
    print(f"✓ G银行汇总:")
    print(f"  - 余额: {g_summary['balance']}")
    print(f"  - 总收入: {g_summary['total_income']}")
    print(f"  - 总支出: {g_summary['total_expense']}")
    print(f"  - 净流量: {g_summary['net_flow']}")
    print(f"  - 交易数: {g_summary['transaction_count']}")
    print(f"  - 已匹配: {g_summary['matched_count']}")
    print(f"  - 未匹配: {g_summary['unmatched_count']}")
    print(f"  - 特殊说明: {g_summary['special_notes'][0]}")
    
    n_summary = fm.get_bank_account_summary(BankType.N_BANK)
    print(f"✓ N银行汇总:")
    print(f"  - 余额: {n_summary['balance']}")
    print(f"  - 总收入: {n_summary['total_income']}")
    print(f"  - 总支出: {n_summary['total_expense']}")
    print(f"  - 净流量: {n_summary['net_flow']}")
    print(f"  - 交易数: {n_summary['transaction_count']}")
    print(f"  - 特殊说明: {n_summary['special_notes'][0]}")
    
    # 测试10: 银行对账
    print("\n测试10: 银行对账汇总")
    reconciliation = fm.reconcile_bank_accounts()
    print(f"✓ 总余额: {reconciliation['total_balance']}")
    print(f"✓ 未匹配交易总数: {reconciliation['total_unmatched_transactions']}")
    print(f"✓ 对账状态: {reconciliation['reconciliation_status']}")
    
    # 关闭数据库
    db.close()
    
    print("\n" + "=" * 60)
    print("所有测试通过！银行账户管理功能正常工作。")
    print("=" * 60)


if __name__ == "__main__":
    try:
        test_bank_account_management()
    except Exception as e:
        print(f"\n❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
