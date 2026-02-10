"""
导入验证器单元测试
"""

import pytest
from datetime import date, datetime
from decimal import Decimal

from small_accountant_v16.import_engine.validator import ImportValidator, ValidationError


class TestImportValidator:
    """导入验证器测试类"""
    
    @pytest.fixture
    def validator(self):
        """创建验证器实例"""
        return ImportValidator()
    
    # ==================== 交易记录验证测试 ====================
    
    def test_validate_valid_transaction_data(self, validator):
        """测试验证有效的交易记录数据"""
        data = [
            {
                'date': '2024-01-15',
                'type': 'income',
                'amount': '1000.50',
                'counterparty_id': 'CP001',
                'description': '销售收入',
                'category': '主营业务收入',
                'status': 'completed'
            }
        ]
        
        errors = validator.validate_transaction_data(
            data, existing_counterparty_ids=['CP001']
        )
        
        assert len(errors) == 0
    
    def test_validate_transaction_missing_required_fields(self, validator):
        """测试缺失必需字段"""
        data = [
            {'type': 'income'},  # 缺少date和amount
            {'date': '2024-01-15'},  # 缺少type和amount
            {'amount': '1000'}  # 缺少date和type
        ]
        
        errors = validator.validate_transaction_data(data)
        
        # 应该有6个错误（每条记录缺2个字段）
        assert len(errors) == 6
        assert all(e.error_type == 'missing' for e in errors)
    
    def test_validate_transaction_invalid_date_format(self, validator):
        """测试无效的日期格式"""
        data = [
            {
                'date': 'invalid-date',
                'type': 'income',
                'amount': '1000'
            },
            {
                'date': '2024/13/45',  # 无效日期
                'type': 'income',
                'amount': '1000'
            }
        ]
        
        errors = validator.validate_transaction_data(data)
        
        date_errors = [e for e in errors if e.field_name == 'date']
        assert len(date_errors) == 2
        assert all(e.error_type == 'invalid_format' for e in date_errors)
    
    def test_validate_transaction_valid_date_formats(self, validator):
        """测试支持的日期格式"""
        data = [
            {'date': '2024-01-15', 'type': 'income', 'amount': '1000'},
            {'date': '2024/01/15', 'type': 'income', 'amount': '1000'},
            {'date': '20240115', 'type': 'income', 'amount': '1000'},
            {'date': date(2024, 1, 15), 'type': 'income', 'amount': '1000'},
        ]
        
        errors = validator.validate_transaction_data(data)
        
        date_errors = [e for e in errors if e.field_name == 'date']
        assert len(date_errors) == 0
    
    def test_validate_transaction_invalid_type(self, validator):
        """测试无效的交易类型"""
        data = [
            {
                'date': '2024-01-15',
                'type': 'invalid_type',
                'amount': '1000'
            }
        ]
        
        errors = validator.validate_transaction_data(data)
        
        type_errors = [e for e in errors if e.field_name == 'type']
        assert len(type_errors) == 1
        assert type_errors[0].error_type == 'invalid_value'
        assert 'invalid_type' in type_errors[0].error_message
    
    def test_validate_transaction_valid_types(self, validator):
        """测试有效的交易类型（包括中英文）"""
        data = [
            {'date': '2024-01-15', 'type': 'income', 'amount': '1000'},
            {'date': '2024-01-15', 'type': 'expense', 'amount': '1000'},
            {'date': '2024-01-15', 'type': 'order', 'amount': '1000'},
            {'date': '2024-01-15', 'type': '收入', 'amount': '1000'},
            {'date': '2024-01-15', 'type': '支出', 'amount': '1000'},
            {'date': '2024-01-15', 'type': '订单', 'amount': '1000'},
        ]
        
        errors = validator.validate_transaction_data(data)
        
        type_errors = [e for e in errors if e.field_name == 'type']
        assert len(type_errors) == 0
    
    def test_validate_transaction_invalid_amount(self, validator):
        """测试无效的金额"""
        data = [
            {'date': '2024-01-15', 'type': 'income', 'amount': 'invalid'},
            {'date': '2024-01-15', 'type': 'income', 'amount': '-100'},
            {'date': '2024-01-15', 'type': 'income', 'amount': '0'},
            {'date': '2024-01-15', 'type': 'income', 'amount': None},
        ]
        
        errors = validator.validate_transaction_data(data)
        
        amount_errors = [e for e in errors if e.field_name == 'amount']
        # 第一个和第四个是格式错误，第二个和第三个是值错误
        assert len(amount_errors) >= 3
    
    def test_validate_transaction_valid_amounts(self, validator):
        """测试有效的金额格式"""
        data = [
            {'date': '2024-01-15', 'type': 'income', 'amount': '1000'},
            {'date': '2024-01-15', 'type': 'income', 'amount': '1000.50'},
            {'date': '2024-01-15', 'type': 'income', 'amount': 1000},
            {'date': '2024-01-15', 'type': 'income', 'amount': 1000.50},
            {'date': '2024-01-15', 'type': 'income', 'amount': Decimal('1000.50')},
        ]
        
        errors = validator.validate_transaction_data(data)
        
        amount_errors = [e for e in errors if e.field_name == 'amount']
        assert len(amount_errors) == 0
    
    def test_validate_transaction_invalid_counterparty_reference(self, validator):
        """测试无效的往来单位引用"""
        data = [
            {
                'date': '2024-01-15',
                'type': 'income',
                'amount': '1000',
                'counterparty_id': 'NONEXISTENT'
            }
        ]
        
        errors = validator.validate_transaction_data(
            data, existing_counterparty_ids=['CP001', 'CP002']
        )
        
        cp_errors = [e for e in errors if e.field_name == 'counterparty_id']
        assert len(cp_errors) == 1
        assert cp_errors[0].error_type == 'invalid_value'
    
    def test_validate_transaction_invalid_status(self, validator):
        """测试无效的交易状态"""
        data = [
            {
                'date': '2024-01-15',
                'type': 'income',
                'amount': '1000',
                'status': 'invalid_status'
            }
        ]
        
        errors = validator.validate_transaction_data(data)
        
        status_errors = [e for e in errors if e.field_name == 'status']
        assert len(status_errors) == 1
        assert status_errors[0].error_type == 'invalid_value'
    
    def test_validate_transaction_string_length(self, validator):
        """测试字符串长度验证"""
        data = [
            {
                'date': '2024-01-15',
                'type': 'income',
                'amount': '1000',
                'description': 'x' * 501,  # 超过500字符
                'category': 'y' * 101  # 超过100字符
            }
        ]
        
        errors = validator.validate_transaction_data(data)
        
        length_errors = [
            e for e in errors
            if e.field_name in ['description', 'category']
        ]
        assert len(length_errors) == 2
    
    # ==================== 往来单位验证测试 ====================
    
    def test_validate_valid_counterparty_data(self, validator):
        """测试验证有效的往来单位数据"""
        data = [
            {
                'name': '测试客户有限公司',
                'type': 'customer',
                'contact_person': '张三',
                'phone': '13800138000',
                'email': 'test@example.com',
                'address': '北京市朝阳区测试路123号',
                'tax_id': '91110000000000000X'
            }
        ]
        
        errors = validator.validate_counterparty_data(data)
        
        assert len(errors) == 0
    
    def test_validate_counterparty_missing_required_fields(self, validator):
        """测试缺失必需字段"""
        data = [
            {'type': 'customer'},  # 缺少name
            {'name': '测试公司'},  # 缺少type
            {}  # 缺少name和type
        ]
        
        errors = validator.validate_counterparty_data(data)
        
        # 应该有4个错误
        assert len(errors) == 4
        assert all(e.error_type == 'missing' for e in errors)
    
    def test_validate_counterparty_invalid_type(self, validator):
        """测试无效的单位类型"""
        data = [
            {
                'name': '测试公司',
                'type': 'invalid_type'
            }
        ]
        
        errors = validator.validate_counterparty_data(data)
        
        type_errors = [e for e in errors if e.field_name == 'type']
        assert len(type_errors) == 1
        assert type_errors[0].error_type == 'invalid_value'
    
    def test_validate_counterparty_valid_types(self, validator):
        """测试有效的单位类型（包括中英文）"""
        data = [
            {'name': '客户1', 'type': 'customer'},
            {'name': '客户2', 'type': 'supplier'},
            {'name': '客户3', 'type': '客户'},
            {'name': '客户4', 'type': '供应商'},
        ]
        
        errors = validator.validate_counterparty_data(data)
        
        type_errors = [e for e in errors if e.field_name == 'type']
        assert len(type_errors) == 0
    
    def test_validate_counterparty_name_length(self, validator):
        """测试单位名称长度"""
        data = [
            {'name': 'A', 'type': 'customer'},  # 太短
            {'name': 'x' * 201, 'type': 'customer'},  # 太长
        ]
        
        errors = validator.validate_counterparty_data(data)
        
        name_errors = [e for e in errors if e.field_name == 'name']
        assert len(name_errors) == 2
    
    def test_validate_counterparty_duplicate_name(self, validator):
        """测试重复的单位名称"""
        data = [
            {'name': '测试公司', 'type': 'customer'},
            {'name': '测试公司', 'type': 'customer'},  # 批次内重复
        ]
        
        errors = validator.validate_counterparty_data(
            data, existing_names=['已存在公司']
        )
        
        duplicate_errors = [
            e for e in errors
            if e.error_type == 'duplicate' and e.field_name == 'name'
        ]
        assert len(duplicate_errors) == 1
        assert '批次内' in duplicate_errors[0].error_message
    
    def test_validate_counterparty_existing_name(self, validator):
        """测试已存在的单位名称"""
        data = [
            {'name': '已存在公司', 'type': 'customer'}
        ]
        
        errors = validator.validate_counterparty_data(
            data, existing_names=['已存在公司']
        )
        
        duplicate_errors = [
            e for e in errors
            if e.error_type == 'duplicate' and e.field_name == 'name'
        ]
        assert len(duplicate_errors) == 1
        assert '已存在' in duplicate_errors[0].error_message
    
    def test_validate_counterparty_invalid_phone(self, validator):
        """测试无效的电话号码"""
        data = [
            {'name': '测试公司', 'type': 'customer', 'phone': '123'},
            {'name': '测试公司2', 'type': 'customer', 'phone': 'invalid'},
        ]
        
        errors = validator.validate_counterparty_data(data)
        
        phone_errors = [e for e in errors if e.field_name == 'phone']
        assert len(phone_errors) == 2
    
    def test_validate_counterparty_valid_phones(self, validator):
        """测试有效的电话号码"""
        data = [
            {'name': '公司1', 'type': 'customer', 'phone': '13800138000'},
            {'name': '公司2', 'type': 'customer', 'phone': '010-12345678'},
            {'name': '公司3', 'type': 'customer', 'phone': '0755-87654321'},
        ]
        
        errors = validator.validate_counterparty_data(data)
        
        phone_errors = [e for e in errors if e.field_name == 'phone']
        assert len(phone_errors) == 0
    
    def test_validate_counterparty_invalid_email(self, validator):
        """测试无效的邮箱地址"""
        data = [
            {'name': '测试公司', 'type': 'customer', 'email': 'invalid'},
            {'name': '测试公司2', 'type': 'customer', 'email': 'test@'},
            {'name': '测试公司3', 'type': 'customer', 'email': '@example.com'},
        ]
        
        errors = validator.validate_counterparty_data(data)
        
        email_errors = [e for e in errors if e.field_name == 'email']
        assert len(email_errors) == 3
    
    def test_validate_counterparty_valid_emails(self, validator):
        """测试有效的邮箱地址"""
        data = [
            {'name': '公司1', 'type': 'customer', 'email': 'test@example.com'},
            {'name': '公司2', 'type': 'customer', 'email': 'user.name@company.co.cn'},
        ]
        
        errors = validator.validate_counterparty_data(data)
        
        email_errors = [e for e in errors if e.field_name == 'email']
        assert len(email_errors) == 0
    
    def test_validate_counterparty_invalid_tax_id(self, validator):
        """测试无效的税号"""
        data = [
            {'name': '测试公司', 'type': 'customer', 'tax_id': '123'},  # 太短
            {'name': '测试公司2', 'type': 'customer', 'tax_id': '12345'},  # 太短
        ]
        
        errors = validator.validate_counterparty_data(data)
        
        tax_errors = [e for e in errors if e.field_name == 'tax_id']
        assert len(tax_errors) == 2
    
    def test_validate_counterparty_valid_tax_ids(self, validator):
        """测试有效的税号"""
        data = [
            {'name': '公司1', 'type': 'customer', 'tax_id': '123456789012345'},  # 15位
            {'name': '公司2', 'type': 'customer', 'tax_id': '91110000000000000X'},  # 18位
        ]
        
        errors = validator.validate_counterparty_data(data)
        
        tax_errors = [e for e in errors if e.field_name == 'tax_id']
        assert len(tax_errors) == 0
    
    def test_validate_counterparty_duplicate_tax_id(self, validator):
        """测试重复的税号"""
        data = [
            {'name': '公司1', 'type': 'customer', 'tax_id': '91110000000000000X'},
            {'name': '公司2', 'type': 'customer', 'tax_id': '91110000000000000X'},  # 批次内重复
        ]
        
        errors = validator.validate_counterparty_data(
            data, existing_tax_ids=['91110000000000000Y']
        )
        
        duplicate_errors = [
            e for e in errors
            if e.error_type == 'duplicate' and e.field_name == 'tax_id'
        ]
        assert len(duplicate_errors) == 1
        assert '批次内' in duplicate_errors[0].error_message
    
    def test_validate_counterparty_existing_tax_id(self, validator):
        """测试已存在的税号"""
        data = [
            {'name': '测试公司', 'type': 'customer', 'tax_id': '91110000000000000X'}
        ]
        
        errors = validator.validate_counterparty_data(
            data, existing_tax_ids=['91110000000000000X']
        )
        
        duplicate_errors = [
            e for e in errors
            if e.error_type == 'duplicate' and e.field_name == 'tax_id'
        ]
        assert len(duplicate_errors) == 1
        assert '已存在' in duplicate_errors[0].error_message
    
    # ==================== 综合测试 ====================
    
    def test_validate_multiple_errors_per_record(self, validator):
        """测试单条记录多个错误"""
        data = [
            {
                'date': 'invalid',
                'type': 'invalid',
                'amount': '-100',
                'status': 'invalid'
            }
        ]
        
        errors = validator.validate_transaction_data(data)
        
        # 应该有多个错误
        assert len(errors) >= 4
        assert len(set(e.field_name for e in errors)) >= 4
    
    def test_validation_error_structure(self, validator):
        """测试验证错误的结构"""
        data = [
            {'type': 'income', 'amount': '1000'}  # 缺少date
        ]
        
        errors = validator.validate_transaction_data(data)
        
        assert len(errors) > 0
        error = errors[0]
        assert hasattr(error, 'row_number')
        assert hasattr(error, 'field_name')
        assert hasattr(error, 'field_value')
        assert hasattr(error, 'error_message')
        assert hasattr(error, 'error_type')
        assert error.row_number == 1
        assert isinstance(error.error_message, str)
        assert len(error.error_message) > 0
