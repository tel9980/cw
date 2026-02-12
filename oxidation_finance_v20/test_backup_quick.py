#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
快速测试备份恢复功能
"""

import sys
import tempfile
import shutil
from pathlib import Path
from datetime import date
from decimal import Decimal

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent))

from database.db_manager import DatabaseManager
from utils.data_manager import DataManager
from models.business_models import (
    Customer, Supplier, ProcessingOrder, Income, Expense,
    BankAccount, PricingUnit, ProcessType, OrderStatus,
    ExpenseType, BankType
)


def test_backup_restore():
    """测试备份和恢复功能"""
    print("=" * 60)
    print("测试备份和恢复功能")
    print("=" * 60)
    
    # 创建临时目录
    temp_dir = tempfile.mkdtemp()
    print(f"\n临时目录: {temp_dir}")
    
    try:
        # 1. 创建数据库和数据管理器
        db_path = Path(temp_dir) / "test.db"
        db = DatabaseManager(str(db_path))
        db.connect()
        data_manager = DataManager(db)
        
        print("\n✓ 数据库创建成功")
        
        # 2. 创建测试数据
        print("\n创建测试数据...")
        
        customer = Customer(
            name="测试客户",
            contact="张三",
            phone="13800138000",
            address="测试地址",
            credit_limit=Decimal("100000")
        )
        db.save_customer(customer)
        print(f"  ✓ 客户: {customer.name}")
        
        supplier = Supplier(
            name="测试供应商",
            contact="李四",
            phone="13900139000",
            business_type="喷砂"
        )
        db.save_supplier(supplier)
        print(f"  ✓ 供应商: {supplier.name}")
        
        order = ProcessingOrder(
            order_no="TEST001",
            customer_id=customer.id,
            customer_name=customer.name,
            item_description="测试产品",
            quantity=Decimal("100"),
            pricing_unit=PricingUnit.PER_PIECE,
            unit_price=Decimal("10.50"),
            processes=[ProcessType.SANDBLASTING, ProcessType.OXIDATION],
            total_amount=Decimal("1050.00"),
            status=OrderStatus.IN_PROGRESS,
            order_date=date.today()
        )
        db.save_order(order)
        print(f"  ✓ 订单: {order.order_no}, 金额: {order.total_amount}")
        
        income = Income(
            customer_id=customer.id,
            customer_name=customer.name,
            amount=Decimal("500.00"),
            bank_type=BankType.G_BANK,
            has_invoice=True,
            related_orders=[order.id],
            allocation={order.id: Decimal("500.00")},
            income_date=date.today()
        )
        db.save_income(income)
        print(f"  ✓ 收入: {income.amount}")
        
        expense = Expense(
            expense_type=ExpenseType.ACIDS,
            supplier_id=supplier.id,
            supplier_name=supplier.name,
            amount=Decimal("200.00"),
            bank_type=BankType.N_BANK,
            has_invoice=False,
            expense_date=date.today(),
            description="购买硫酸"
        )
        db.save_expense(expense)
        print(f"  ✓ 支出: {expense.amount}")
        
        account = BankAccount(
            bank_type=BankType.G_BANK,
            account_name="G银行账户",
            account_number="6222000012345678",
            balance=Decimal("50000.00")
        )
        db.save_bank_account(account)
        print(f"  ✓ 银行账户: {account.account_name}, 余额: {account.balance}")
        
        # 3. 执行备份
        print("\n" + "=" * 60)
        print("执行数据备份...")
        print("=" * 60)
        
        backup_dir = Path(temp_dir) / "backups"
        success, backup_file, backup_info = data_manager.backup_system_data(
            backup_dir=str(backup_dir),
            include_config=True
        )
        
        if success:
            print(f"\n✓ 备份成功!")
            print(f"  备份文件: {backup_file}")
            print(f"  备份时间: {backup_info['backup_time']}")
            print(f"  总记录数: {backup_info['total_records']}")
            print(f"  客户数: {backup_info['customers_count']}")
            print(f"  供应商数: {backup_info['suppliers_count']}")
            print(f"  订单数: {backup_info['processing_orders_count']}")
            print(f"  收入记录数: {backup_info['incomes_count']}")
            print(f"  支出记录数: {backup_info['expenses_count']}")
            print(f"  银行账户数: {backup_info['bank_accounts_count']}")
            print(f"  数据库大小: {backup_info['database_size']} 字节")
            print(f"  备份大小: {backup_info['backup_size']} 字节")
            print(f"  包含配置: {backup_info['config_included']}")
        else:
            print(f"\n✗ 备份失败: {backup_info}")
            return False
        
        # 4. 修改数据
        print("\n" + "=" * 60)
        print("修改数据...")
        print("=" * 60)
        
        new_customer = Customer(
            name="新客户",
            contact="王五",
            phone="13700137000"
        )
        db.save_customer(new_customer)
        print(f"  ✓ 添加新客户: {new_customer.name}")
        
        customers_before = db.list_customers()
        print(f"  当前客户总数: {len(customers_before)}")
        
        # 5. 执行恢复
        print("\n" + "=" * 60)
        print("执行数据恢复...")
        print("=" * 60)
        
        success, messages = data_manager.restore_system_data(
            backup_file=backup_file,
            restore_config=True,
            validate_before_restore=True
        )
        
        if success:
            print(f"\n✓ 恢复成功!")
            for msg in messages:
                print(f"  • {msg}")
        else:
            print(f"\n✗ 恢复失败:")
            for msg in messages:
                print(f"  • {msg}")
            return False
        
        # 6. 验证恢复结果
        print("\n" + "=" * 60)
        print("验证恢复结果...")
        print("=" * 60)
        
        customers_after = db.list_customers()
        print(f"  恢复后客户总数: {len(customers_after)}")
        
        # 验证原始客户存在
        restored_customer = db.get_customer(customer.id)
        if restored_customer and restored_customer.name == "测试客户":
            print(f"  ✓ 原始客户已恢复: {restored_customer.name}")
        else:
            print(f"  ✗ 原始客户恢复失败")
            return False
        
        # 验证新客户不存在（已回滚）
        new_customer_check = db.get_customer(new_customer.id)
        if new_customer_check is None:
            print(f"  ✓ 新添加的客户已回滚")
        else:
            print(f"  ✗ 新客户未回滚")
        
        # 验证订单
        restored_order = db.get_order(order.id)
        if restored_order and restored_order.order_no == "TEST001":
            print(f"  ✓ 订单已恢复: {restored_order.order_no}")
        else:
            print(f"  ✗ 订单恢复失败")
            return False
        
        # 验证收入
        restored_income = db.get_income(income.id)
        if restored_income and restored_income.amount == Decimal("500.00"):
            print(f"  ✓ 收入已恢复: {restored_income.amount}")
        else:
            print(f"  ✗ 收入恢复失败")
            return False
        
        # 7. 测试列出备份
        print("\n" + "=" * 60)
        print("列出所有备份...")
        print("=" * 60)
        
        backups = data_manager.list_backups(backup_dir=str(backup_dir))
        print(f"  找到 {len(backups)} 个备份:")
        for i, backup in enumerate(backups, 1):
            print(f"  {i}. {backup['backup_name']}")
            print(f"     时间: {backup['backup_time']}")
            print(f"     大小: {backup['backup_size']} 字节")
            print(f"     包含配置: {backup['has_config']}")
        
        # 8. 测试数据完整性验证
        print("\n" + "=" * 60)
        print("验证数据库完整性...")
        print("=" * 60)
        
        is_ok, errors = data_manager._verify_database_integrity()
        if is_ok:
            print("  ✓ 数据库完整性检查通过")
        else:
            print(f"  ✗ 数据库完整性检查失败:")
            for err in errors:
                print(f"    • {err}")
        
        # 关闭数据库
        db.close()
        
        print("\n" + "=" * 60)
        print("✓ 所有测试通过!")
        print("=" * 60)
        
        return True
        
    except Exception as e:
        print(f"\n✗ 测试失败: {str(e)}")
        import traceback
        traceback.print_exc()
        return False
        
    finally:
        # 清理临时目录
        try:
            shutil.rmtree(temp_dir, ignore_errors=True)
            print(f"\n临时目录已清理: {temp_dir}")
        except:
            pass


if __name__ == "__main__":
    success = test_backup_restore()
    sys.exit(0 if success else 1)
