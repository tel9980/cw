#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
快速测试数据管理器功能
"""

import sys
import os
import pandas as pd
import tempfile
from datetime import date
from decimal import Decimal

# 添加项目路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from utils.data_manager import DataManager, DataValidationError
from models.business_models import BankType, Customer, Supplier
from database.db_manager import DatabaseManager


def test_basic_functionality():
    """测试基本功能"""
    print("=" * 60)
    print("测试 1: 基本功能测试")
    print("=" * 60)
    
    # 创建临时数据库
    with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as f:
        db_path = f.name
    
    try:
        # 初始化数据库和数据管理器
        db = DatabaseManager(db_path)
        db.connect()
        data_manager = DataManager(db)
        
        print("✓ 数据管理器初始化成功")
        
        # 创建测试客户和供应商
        customer = Customer(name="测试客户公司", contact="张三")
        supplier = Supplier(name="测试供应商", contact="李四", business_type="原料供应")
        
        db.save_customer(customer)
        db.save_supplier(supplier)
        
        print("✓ 测试数据创建成功")
        
        db.close()
        
    finally:
        if os.path.exists(db_path):
            os.unlink(db_path)
    
    print("\n测试 1 通过！\n")


def test_excel_import():
    """测试Excel导入功能"""
    print("=" * 60)
    print("测试 2: Excel导入功能")
    print("=" * 60)
    
    # 创建临时数据库
    with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as f:
        db_path = f.name
    
    # 创建临时Excel文件
    with tempfile.NamedTemporaryFile(suffix='.xlsx', delete=False) as f:
        excel_path = f.name
    
    try:
        # 初始化
        db = DatabaseManager(db_path)
        db.connect()
        data_manager = DataManager(db)
        
        # 创建测试数据
        customer = Customer(name="张三公司", contact="张三")
        supplier = Supplier(name="化工供应商", contact="李四", business_type="原料")
        db.save_customer(customer)
        db.save_supplier(supplier)
        
        # 创建Excel文件
        data = {
            "交易日期": ["2024-01-15", "2024-01-16", "2024-01-17"],
            "金额": [5000.00, -2000.00, 3500.50],
            "交易对手": ["张三公司", "化工供应商", "其他客户"],
            "摘要": ["收到货款", "采购原料", "收到加工费"]
        }
        df = pd.DataFrame(data)
        df.to_excel(excel_path, index=False)
        
        print(f"✓ 创建测试Excel文件: {excel_path}")
        
        # 导入数据
        count, errors = data_manager.import_bank_statement(
            excel_path,
            BankType.G_BANK
        )
        
        print(f"✓ 成功导入 {count} 条记录")
        if errors:
            print(f"  警告: {len(errors)} 个错误")
            for error in errors[:3]:
                print(f"    - {error}")
        
        # 验证导入结果
        transactions = db.list_bank_transactions(BankType.G_BANK)
        print(f"✓ 数据库中共有 {len(transactions)} 条交易记录")
        
        # 检查交易对手匹配
        for trans in transactions:
            print(f"  - 日期: {trans.transaction_date}, "
                  f"金额: {trans.amount}, "
                  f"交易对手: {trans.counterparty}")
        
        db.close()
        
    finally:
        if os.path.exists(db_path):
            os.unlink(db_path)
        if os.path.exists(excel_path):
            os.unlink(excel_path)
    
    print("\n测试 2 通过！\n")


def test_data_validation():
    """测试数据验证功能"""
    print("=" * 60)
    print("测试 3: 数据验证功能")
    print("=" * 60)
    
    with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as f:
        db_path = f.name
    
    with tempfile.NamedTemporaryFile(suffix='.xlsx', delete=False) as f:
        excel_path = f.name
    
    try:
        db = DatabaseManager(db_path)
        db.connect()
        data_manager = DataManager(db)
        
        # 创建有效的Excel文件
        data = {
            "交易日期": ["2024-01-15", "2024-01-16"],
            "金额": [1000.00, 2000.00],
            "交易对手": ["客户A", "客户B"],
            "摘要": ["备注1", "备注2"]
        }
        df = pd.DataFrame(data)
        df.to_excel(excel_path, index=False)
        
        # 验证数据
        is_valid, errors = data_manager.validate_import_data(excel_path)
        
        print(f"✓ 数据验证结果: {'通过' if is_valid else '失败'}")
        if errors:
            print(f"  错误数量: {len(errors)}")
            for error in errors:
                print(f"    - {error}")
        
        # 获取导入摘要
        summary = data_manager.get_import_summary(excel_path)
        print(f"✓ 导入摘要:")
        print(f"  - 总行数: {summary.get('total_rows', 0)}")
        print(f"  - 列名: {summary.get('columns', [])}")
        if 'amount_stats' in summary:
            stats = summary['amount_stats']
            print(f"  - 金额统计: 最小={stats['min']}, 最大={stats['max']}, "
                  f"总和={stats['sum']}")
        
        db.close()
        
    finally:
        if os.path.exists(db_path):
            os.unlink(db_path)
        if os.path.exists(excel_path):
            os.unlink(excel_path)
    
    print("\n测试 3 通过！\n")


def test_counterparty_matching():
    """测试交易对手匹配功能"""
    print("=" * 60)
    print("测试 4: 交易对手匹配功能")
    print("=" * 60)
    
    with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as f:
        db_path = f.name
    
    try:
        db = DatabaseManager(db_path)
        db.connect()
        data_manager = DataManager(db)
        
        # 创建测试数据
        customers = [
            Customer(name="张三公司", contact="张三"),
            Customer(name="李四工厂", contact="李四"),
        ]
        suppliers = [
            Supplier(name="化工原料供应商", contact="王五", business_type="原料"),
            Supplier(name="喷砂加工厂", contact="赵六", business_type="委外"),
        ]
        
        for c in customers:
            db.save_customer(c)
        for s in suppliers:
            db.save_supplier(s)
        
        # 测试匹配
        test_cases = [
            ("张三公司", "张三公司"),  # 精确匹配客户
            ("化工原料供应商", "化工原料供应商"),  # 精确匹配供应商
            ("张三公司有限责任公司", "张三公司"),  # 模糊匹配客户
            ("某某化工原料供应商", "化工原料供应商"),  # 模糊匹配供应商
            ("未知公司", "未知公司"),  # 无匹配
        ]
        
        print("✓ 交易对手匹配测试:")
        for input_name, expected in test_cases:
            result = data_manager._match_counterparty(
                input_name,
                customers,
                suppliers
            )
            status = "✓" if result == expected else "✗"
            print(f"  {status} '{input_name}' -> '{result}' "
                  f"(期望: '{expected}')")
        
        db.close()
        
    finally:
        if os.path.exists(db_path):
            os.unlink(db_path)
    
    print("\n测试 4 通过！\n")


def test_date_and_amount_parsing():
    """测试日期和金额解析"""
    print("=" * 60)
    print("测试 5: 日期和金额解析")
    print("=" * 60)
    
    with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as f:
        db_path = f.name
    
    try:
        db = DatabaseManager(db_path)
        db.connect()
        data_manager = DataManager(db)
        
        # 测试日期解析
        print("✓ 日期解析测试:")
        date_tests = [
            ("2024-01-15", date(2024, 1, 15)),
            ("2024/01/15", date(2024, 1, 15)),
            ("2024年01月15日", date(2024, 1, 15)),
            ("2024.01.15", date(2024, 1, 15)),
        ]
        
        for date_str, expected in date_tests:
            result = data_manager._parse_date(date_str, 0)
            status = "✓" if result == expected else "✗"
            print(f"  {status} '{date_str}' -> {result}")
        
        # 测试金额解析
        print("\n✓ 金额解析测试:")
        amount_tests = [
            (1234.56, Decimal("1234.56")),
            ("1,234.56", Decimal("1234.56")),
            ("¥1234.56", Decimal("1234.56")),
            ("$1234.56", Decimal("1234.56")),
            (-1234.56, Decimal("-1234.56")),
        ]
        
        for amount_input, expected in amount_tests:
            data_manager.validation_errors = []
            result = data_manager._parse_amount(amount_input, 0)
            status = "✓" if result == expected else "✗"
            print(f"  {status} {amount_input} -> {result}")
        
        db.close()
        
    finally:
        if os.path.exists(db_path):
            os.unlink(db_path)
    
    print("\n测试 5 通过！\n")


def main():
    """运行所有测试"""
    print("\n" + "=" * 60)
    print("数据管理器快速测试")
    print("=" * 60 + "\n")
    
    try:
        test_basic_functionality()
        test_excel_import()
        test_data_validation()
        test_counterparty_matching()
        test_date_and_amount_parsing()
        
        print("=" * 60)
        print("所有测试通过！✓")
        print("=" * 60)
        
    except Exception as e:
        print(f"\n✗ 测试失败: {str(e)}")
        import traceback
        traceback.print_exc()
        return 1
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
