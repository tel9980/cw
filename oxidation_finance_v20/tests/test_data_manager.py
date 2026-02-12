#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
数据管理器单元测试
"""

import pytest
import pandas as pd
from pathlib import Path
from datetime import date, datetime
from decimal import Decimal
import tempfile
import os

from oxidation_finance_v20.utils.data_manager import DataManager, DataValidationError
from oxidation_finance_v20.models.business_models import (
    BankType, Customer, Supplier
)
from oxidation_finance_v20.database.db_manager import DatabaseManager


@pytest.fixture
def db_manager():
    """创建测试数据库管理器"""
    with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as f:
        db_path = f.name
    
    db = DatabaseManager(db_path)
    db.connect()
    
    yield db
    
    db.close()
    if os.path.exists(db_path):
        os.unlink(db_path)


@pytest.fixture
def data_manager(db_manager):
    """创建数据管理器"""
    return DataManager(db_manager)


@pytest.fixture
def sample_customers(db_manager):
    """创建示例客户数据"""
    customers = [
        Customer(name="张三公司", contact="张三", phone="13800138000"),
        Customer(name="李四工厂", contact="李四", phone="13900139000"),
        Customer(name="王五贸易", contact="王五", phone="13700137000")
    ]
    for customer in customers:
        db_manager.save_customer(customer)
    return customers


@pytest.fixture
def sample_suppliers(db_manager):
    """创建示例供应商数据"""
    suppliers = [
        Supplier(name="化工原料供应商", contact="赵六", business_type="原料供应"),
        Supplier(name="喷砂加工厂", contact="钱七", business_type="委外加工"),
        Supplier(name="电力公司", contact="孙八", business_type="公用事业")
    ]
    for supplier in suppliers:
        db_manager.save_supplier(supplier)
    return suppliers


@pytest.fixture
def sample_excel_file():
    """创建示例Excel文件"""
    with tempfile.NamedTemporaryFile(suffix='.xlsx', delete=False) as f:
        excel_path = f.name
    
    # 创建示例数据
    data = {
        "交易日期": [
            "2024-01-15",
            "2024-01-16",
            "2024-01-17",
            "2024-01-18"
        ],
        "金额": [
            5000.00,
            -2000.00,
            3500.50,
            -1200.00
        ],
        "交易对手": [
            "张三公司",
            "化工原料供应商",
            "李四工厂",
            "电力公司"
        ],
        "摘要": [
            "收到货款",
            "采购原料",
            "收到加工费",
            "支付电费"
        ]
    }
    
    df = pd.DataFrame(data)
    df.to_excel(excel_path, index=False)
    
    yield excel_path
    
    if os.path.exists(excel_path):
        os.unlink(excel_path)


class TestDataManagerBasic:
    """数据管理器基础功能测试"""
    
    def test_init(self, data_manager):
        """测试初始化"""
        assert data_manager is not None
        assert data_manager.db is not None
        assert data_manager.validation_errors == []
    
    def test_import_bank_statement_success(
        self, data_manager, sample_excel_file, sample_customers, sample_suppliers
    ):
        """测试成功导入银行流水"""
        count, errors = data_manager.import_bank_statement(
            sample_excel_file,
            BankType.G_BANK
        )
        
        assert count == 4
        assert len(errors) == 0
        
        # 验证数据已保存到数据库
        transactions = data_manager.db.list_bank_transactions(BankType.G_BANK)
        assert len(transactions) == 4
    
    def test_import_bank_statement_with_counterparty_matching(
        self, data_manager, sample_excel_file, sample_customers, sample_suppliers
    ):
        """测试导入时自动匹配交易对手"""
        count, errors = data_manager.import_bank_statement(
            sample_excel_file,
            BankType.G_BANK
        )
        
        transactions = data_manager.db.list_bank_transactions(BankType.G_BANK)
        
        # 验证交易对手已正确匹配
        counterparties = [t.counterparty for t in transactions]
        assert "张三公司" in counterparties
        assert "化工原料供应商" in counterparties
        assert "李四工厂" in counterparties
    
    def test_import_bank_statement_file_not_found(self, data_manager):
        """测试文件不存在的情况"""
        with pytest.raises(DataValidationError, match="无法读取Excel文件"):
            data_manager.import_bank_statement(
                "nonexistent_file.xlsx",
                BankType.G_BANK
            )
    
    def test_import_bank_statement_missing_columns(self, data_manager):
        """测试缺少必需列的情况"""
        with tempfile.NamedTemporaryFile(suffix='.xlsx', delete=False) as f:
            excel_path = f.name
        
        try:
            # 创建缺少必需列的Excel
            data = {"其他列": [1, 2, 3]}
            df = pd.DataFrame(data)
            df.to_excel(excel_path, index=False)
            
            with pytest.raises(DataValidationError, match="缺少必需列"):
                data_manager.import_bank_statement(
                    excel_path,
                    BankType.G_BANK
                )
        finally:
            if os.path.exists(excel_path):
                os.unlink(excel_path)


class TestDataValidation:
    """数据验证功能测试"""
    
    def test_validate_import_data_success(self, data_manager, sample_excel_file):
        """测试验证成功的情况"""
        is_valid, errors = data_manager.validate_import_data(sample_excel_file)
        
        assert is_valid is True
        assert len(errors) == 0
    
    def test_validate_import_data_file_not_found(self, data_manager):
        """测试文件不存在"""
        is_valid, errors = data_manager.validate_import_data("nonexistent.xlsx")
        
        assert is_valid is False
        assert len(errors) > 0
        assert "文件不存在" in errors[0]
    
    def test_validate_import_data_empty_file(self, data_manager):
        """测试空文件"""
        with tempfile.NamedTemporaryFile(suffix='.xlsx', delete=False) as f:
            excel_path = f.name
        
        try:
            # 创建空Excel
            df = pd.DataFrame()
            df.to_excel(excel_path, index=False)
            
            is_valid, errors = data_manager.validate_import_data(excel_path)
            
            assert is_valid is False
            assert any("为空" in error for error in errors)
        finally:
            if os.path.exists(excel_path):
                os.unlink(excel_path)
    
    def test_validate_import_data_missing_required_columns(self, data_manager):
        """测试缺少必需列"""
        with tempfile.NamedTemporaryFile(suffix='.xlsx', delete=False) as f:
            excel_path = f.name
        
        try:
            data = {"其他列": [1, 2, 3]}
            df = pd.DataFrame(data)
            df.to_excel(excel_path, index=False)
            
            is_valid, errors = data_manager.validate_import_data(excel_path)
            
            assert is_valid is False
            assert any("缺少必需列" in error for error in errors)
        finally:
            if os.path.exists(excel_path):
                os.unlink(excel_path)
    
    def test_validate_import_data_null_values(self, data_manager):
        """测试空值检测"""
        with tempfile.NamedTemporaryFile(suffix='.xlsx', delete=False) as f:
            excel_path = f.name
        
        try:
            data = {
                "交易日期": ["2024-01-15", None, "2024-01-17"],
                "金额": [1000, 2000, None]
            }
            df = pd.DataFrame(data)
            df.to_excel(excel_path, index=False)
            
            is_valid, errors = data_manager.validate_import_data(excel_path)
            
            assert is_valid is False
            assert any("日期为空" in error for error in errors)
            assert any("金额为空" in error for error in errors)
        finally:
            if os.path.exists(excel_path):
                os.unlink(excel_path)
    
    def test_validate_import_data_invalid_amount_format(self, data_manager):
        """测试无效金额格式"""
        with tempfile.NamedTemporaryFile(suffix='.xlsx', delete=False) as f:
            excel_path = f.name
        
        try:
            data = {
                "交易日期": ["2024-01-15", "2024-01-16"],
                "金额": [1000, "无效金额"]
            }
            df = pd.DataFrame(data)
            df.to_excel(excel_path, index=False)
            
            is_valid, errors = data_manager.validate_import_data(excel_path)
            
            assert is_valid is False
            assert any("金额格式不正确" in error for error in errors)
        finally:
            if os.path.exists(excel_path):
                os.unlink(excel_path)


class TestDateParsing:
    """日期解析测试"""
    
    def test_parse_date_datetime(self, data_manager):
        """测试解析datetime对象"""
        dt = datetime(2024, 1, 15, 10, 30, 0)
        result = data_manager._parse_date(dt, 0)
        
        assert result == date(2024, 1, 15)
    
    def test_parse_date_string_formats(self, data_manager):
        """测试解析多种字符串日期格式"""
        test_cases = [
            ("2024-01-15", date(2024, 1, 15)),
            ("2024/01/15", date(2024, 1, 15)),
            ("2024年01月15日", date(2024, 1, 15)),
            ("2024.01.15", date(2024, 1, 15))
        ]
        
        for date_str, expected in test_cases:
            result = data_manager._parse_date(date_str, 0)
            assert result == expected
    
    def test_parse_date_null(self, data_manager):
        """测试解析空值"""
        result = data_manager._parse_date(None, 0)
        
        assert result is None
        assert len(data_manager.validation_errors) > 0
    
    def test_parse_date_invalid_format(self, data_manager):
        """测试解析无效格式"""
        result = data_manager._parse_date("invalid-date", 0)
        
        assert result is None
        assert len(data_manager.validation_errors) > 0


class TestAmountParsing:
    """金额解析测试"""
    
    def test_parse_amount_number(self, data_manager):
        """测试解析数字"""
        result = data_manager._parse_amount(1234.56, 0)
        
        assert result == Decimal("1234.56")
    
    def test_parse_amount_string_with_comma(self, data_manager):
        """测试解析带逗号的字符串"""
        result = data_manager._parse_amount("1,234.56", 0)
        
        assert result == Decimal("1234.56")
    
    def test_parse_amount_string_with_currency(self, data_manager):
        """测试解析带货币符号的字符串"""
        test_cases = [
            "¥1234.56",
            "$1234.56",
            "￥1234.56"
        ]
        
        for amount_str in test_cases:
            result = data_manager._parse_amount(amount_str, 0)
            assert result == Decimal("1234.56")
    
    def test_parse_amount_negative(self, data_manager):
        """测试解析负数"""
        result = data_manager._parse_amount(-1234.56, 0)
        
        assert result == Decimal("-1234.56")
    
    def test_parse_amount_null(self, data_manager):
        """测试解析空值"""
        result = data_manager._parse_amount(None, 0)
        
        assert result is None
        assert len(data_manager.validation_errors) > 0
    
    def test_parse_amount_out_of_range(self, data_manager):
        """测试超出范围的金额"""
        result = data_manager._parse_amount(9999999999.99, 0)
        
        assert result is None
        assert len(data_manager.validation_errors) > 0


class TestCounterpartyMatching:
    """交易对手匹配测试"""
    
    def test_match_counterparty_exact_customer(
        self, data_manager, sample_customers, sample_suppliers
    ):
        """测试精确匹配客户"""
        result = data_manager._match_counterparty(
            "张三公司",
            sample_customers,
            sample_suppliers
        )
        
        assert result == "张三公司"
    
    def test_match_counterparty_exact_supplier(
        self, data_manager, sample_customers, sample_suppliers
    ):
        """测试精确匹配供应商"""
        result = data_manager._match_counterparty(
            "化工原料供应商",
            sample_customers,
            sample_suppliers
        )
        
        assert result == "化工原料供应商"
    
    def test_match_counterparty_fuzzy_customer(
        self, data_manager, sample_customers, sample_suppliers
    ):
        """测试模糊匹配客户"""
        result = data_manager._match_counterparty(
            "张三公司有限责任公司",
            sample_customers,
            sample_suppliers
        )
        
        assert result == "张三公司"
    
    def test_match_counterparty_fuzzy_supplier(
        self, data_manager, sample_customers, sample_suppliers
    ):
        """测试模糊匹配供应商"""
        result = data_manager._match_counterparty(
            "某某化工原料供应商",
            sample_customers,
            sample_suppliers
        )
        
        assert result == "化工原料供应商"
    
    def test_match_counterparty_no_match(
        self, data_manager, sample_customers, sample_suppliers
    ):
        """测试无匹配的情况"""
        result = data_manager._match_counterparty(
            "未知公司",
            sample_customers,
            sample_suppliers
        )
        
        assert result == "未知公司"
    
    def test_match_counterparty_empty(
        self, data_manager, sample_customers, sample_suppliers
    ):
        """测试空交易对手"""
        result = data_manager._match_counterparty(
            "",
            sample_customers,
            sample_suppliers
        )
        
        assert result == ""


class TestImportSummary:
    """导入摘要测试"""
    
    def test_get_import_summary_success(self, data_manager, sample_excel_file):
        """测试获取导入摘要"""
        summary = data_manager.get_import_summary(sample_excel_file)
        
        assert "total_rows" in summary
        assert summary["total_rows"] == 4
        assert "columns" in summary
        assert "交易日期" in summary["columns"]
        assert "金额" in summary["columns"]
        assert summary["has_required_columns"] is True
    
    def test_get_import_summary_with_stats(self, data_manager, sample_excel_file):
        """测试摘要包含统计信息"""
        summary = data_manager.get_import_summary(sample_excel_file)
        
        assert "date_range" in summary
        assert "amount_stats" in summary
        assert "min" in summary["amount_stats"]
        assert "max" in summary["amount_stats"]
        assert "sum" in summary["amount_stats"]
        assert "count" in summary["amount_stats"]
    
    def test_get_import_summary_file_not_found(self, data_manager):
        """测试文件不存在"""
        summary = data_manager.get_import_summary("nonexistent.xlsx")
        
        assert "error" in summary


class TestEdgeCases:
    """边界情况测试"""
    
    def test_import_large_file(self, data_manager, db_manager):
        """测试导入大文件"""
        with tempfile.NamedTemporaryFile(suffix='.xlsx', delete=False) as f:
            excel_path = f.name
        
        try:
            # 创建包含100条记录的文件
            data = {
                "交易日期": [f"2024-01-{i%28+1:02d}" for i in range(100)],
                "金额": [1000.0 + i for i in range(100)],
                "交易对手": [f"客户{i}" for i in range(100)],
                "摘要": [f"交易{i}" for i in range(100)]
            }
            df = pd.DataFrame(data)
            df.to_excel(excel_path, index=False)
            
            count, errors = data_manager.import_bank_statement(
                excel_path,
                BankType.G_BANK
            )
            
            assert count == 100
            assert len(errors) == 0
        finally:
            if os.path.exists(excel_path):
                os.unlink(excel_path)
    
    def test_import_with_special_characters(self, data_manager, db_manager):
        """测试包含特殊字符的数据"""
        with tempfile.NamedTemporaryFile(suffix='.xlsx', delete=False) as f:
            excel_path = f.name
        
        try:
            data = {
                "交易日期": ["2024-01-15"],
                "金额": [1000.0],
                "交易对手": ["公司名称（特殊）& Co."],
                "摘要": ["备注：包含特殊字符 @#$%"]
            }
            df = pd.DataFrame(data)
            df.to_excel(excel_path, index=False)
            
            count, errors = data_manager.import_bank_statement(
                excel_path,
                BankType.G_BANK
            )
            
            assert count == 1
            assert len(errors) == 0
        finally:
            if os.path.exists(excel_path):
                os.unlink(excel_path)
    
    def test_import_with_mixed_data_types(self, data_manager, db_manager):
        """测试混合数据类型"""
        with tempfile.NamedTemporaryFile(suffix='.xlsx', delete=False) as f:
            excel_path = f.name
        
        try:
            data = {
                "交易日期": [
                    datetime(2024, 1, 15),
                    "2024-01-16",
                    "2024/01/17"
                ],
                "金额": [
                    1000,
                    "2,000.50",
                    "¥3000"
                ],
                "交易对手": ["客户A", "客户B", "客户C"],
                "摘要": ["备注1", "备注2", "备注3"]
            }
            df = pd.DataFrame(data)
            df.to_excel(excel_path, index=False)
            
            count, errors = data_manager.import_bank_statement(
                excel_path,
                BankType.G_BANK
            )
            
            assert count == 3
        finally:
            if os.path.exists(excel_path):
                os.unlink(excel_path)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
