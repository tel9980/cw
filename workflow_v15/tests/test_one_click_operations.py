# -*- coding: utf-8 -*-
"""
Unit Tests for One-Click Operations Manager
一键操作管理器的单元测试
"""

import pytest
import json
import tempfile
import shutil
from pathlib import Path
from datetime import datetime
from unittest.mock import Mock, MagicMock, patch

from workflow_v15.core.one_click_operations import (
    OneClickOperationManager,
    OperationError,
    ValidationError
)
from workflow_v15.core.context_engine import ContextEngine
from workflow_v15.core.workflow_engine import WorkflowEngine
from workflow_v15.core.progressive_disclosure import ProgressiveDisclosureManager
from workflow_v15.models.context_models import SmartDefault, Alternative


class TestOneClickOperationManager:
    """测试一键操作管理器"""
    
    @pytest.fixture
    def temp_storage(self):
        """创建临时存储目录"""
        temp_dir = tempfile.mkdtemp()
        yield temp_dir
        shutil.rmtree(temp_dir)
    
    @pytest.fixture
    def mock_context_engine(self):
        """创建模拟的上下文引擎"""
        engine = Mock(spec=ContextEngine)
        
        # 模拟generate_smart_defaults方法
        def mock_generate_defaults(transaction_type, context):
            return {
                'date': SmartDefault(
                    field_name='date',
                    suggested_value='2024-01-15',
                    confidence=1.0,
                    reasoning='当前日期',
                    source='business_rules'
                ),
                'category': SmartDefault(
                    field_name='category',
                    suggested_value='销售收入',
                    confidence=0.8,
                    reasoning='最常用类别',
                    alternatives=[
                        Alternative(value='服务收入', confidence=0.6, reasoning='次常用')
                    ],
                    source='user_pattern'
                )
            }
        
        engine.generate_smart_defaults = Mock(side_effect=mock_generate_defaults)
        engine._get_user_patterns = Mock(return_value=Mock(function_usage_count={}))
        engine.record_transaction = Mock()
        
        return engine
    
    @pytest.fixture
    def mock_workflow_engine(self):
        """创建模拟的工作流引擎"""
        return Mock(spec=WorkflowEngine)
    
    @pytest.fixture
    def mock_progressive_disclosure(self):
        """创建模拟的渐进式披露管理器"""
        return Mock(spec=ProgressiveDisclosureManager)
    
    @pytest.fixture
    def manager(
        self,
        temp_storage,
        mock_context_engine,
        mock_workflow_engine,
        mock_progressive_disclosure
    ):
        """创建一键操作管理器实例"""
        return OneClickOperationManager(
            context_engine=mock_context_engine,
            workflow_engine=mock_workflow_engine,
            progressive_disclosure_manager=mock_progressive_disclosure,
            storage_path=temp_storage
        )
    
    def test_initialization(self, manager):
        """测试初始化"""
        assert manager is not None
        assert len(manager.operation_templates) > 0
        assert 'income_entry' in manager.operation_templates
        assert 'expense_entry' in manager.operation_templates
        assert len(manager.validators) > 0
        assert len(manager.calculators) > 0
        assert len(manager.savers) > 0
    
    def test_income_entry_template(self, manager):
        """测试收入录入模板"""
        template = manager.operation_templates['income_entry']
        
        assert template['template_id'] == 'income_entry'
        assert template['name'] == '收入录入'
        assert template['transaction_type'] == 'income'
        assert 'date' in template['required_fields']
        assert 'amount' in template['required_fields']
        assert 'customer_id' in template['required_fields']
    
    def test_expense_entry_template(self, manager):
        """测试支出录入模板"""
        template = manager.operation_templates['expense_entry']
        
        assert template['template_id'] == 'expense_entry'
        assert template['name'] == '支出录入'
        assert template['transaction_type'] == 'expense'
        assert 'date' in template['required_fields']
        assert 'amount' in template['required_fields']
        assert 'vendor_id' in template['required_fields']
    
    def test_apply_smart_defaults(self, manager, mock_context_engine):
        """测试应用智能默认值 (Requirement 3.1)"""
        template = manager.operation_templates['income_entry']
        user_id = 'test_user'
        data = {
            'amount': 1000.0,
            'customer_id': 'CUST001'
        }
        context = {}
        
        enriched_data = manager._apply_smart_defaults(
            template, user_id, data, context
        )
        
        # 验证应用了模板默认值
        assert enriched_data['payment_method'] == '银行转账'
        
        # 验证应用了智能默认值
        assert enriched_data['date'] == '2024-01-15'
        assert enriched_data['category'] == '销售收入'
        
        # 验证记录了智能默认值的元数据
        assert '_smart_default_date' in enriched_data
        assert enriched_data['_smart_default_date']['confidence'] == 1.0
        
        # 验证调用了ContextEngine
        mock_context_engine.generate_smart_defaults.assert_called_once()
    
    def test_validate_operation_data_success(self, manager):
        """测试数据验证成功"""
        template = manager.operation_templates['income_entry']
        data = {
            'date': '2024-01-15',
            'amount': 1000.0,
            'customer_id': 'CUST001',
            'category': '销售收入'
        }
        
        result = manager._validate_operation_data(template, data)
        
        assert result['valid'] is True
        assert len(result['errors']) == 0
    
    def test_validate_operation_data_missing_required_field(self, manager):
        """测试缺少必填字段"""
        template = manager.operation_templates['income_entry']
        data = {
            'date': '2024-01-15',
            'amount': 1000.0
            # 缺少 customer_id 和 category
        }
        
        result = manager._validate_operation_data(template, data)
        
        assert result['valid'] is False
        assert len(result['errors']) == 2
        assert any('customer_id' in error for error in result['errors'])
        assert any('category' in error for error in result['errors'])
    
    def test_validate_amount(self, manager):
        """测试金额验证"""
        rules = {'min': 0.01, 'type': 'float'}
        
        # 有效金额
        manager._validate_amount(100.0, rules)
        manager._validate_amount('100.0', rules)
        
        # 无效金额 - 小于最小值
        with pytest.raises(ValidationError, match="金额不能小于"):
            manager._validate_amount(0.0, rules)
        
        # 无效金额 - 非数字
        with pytest.raises(ValidationError, match="金额必须是有效的数字"):
            manager._validate_amount('abc', rules)
    
    def test_validate_date(self, manager):
        """测试日期验证"""
        rules = {'type': 'date', 'max': 'today'}
        
        # 有效日期
        manager._validate_date('2024-01-15', rules)
        
        # 无效日期格式
        with pytest.raises(ValidationError, match="日期格式"):
            manager._validate_date('15-01-2024', rules)
        
        # 未来日期（如果规则限制为今天）
        future_date = '2099-12-31'
        with pytest.raises(ValidationError, match="日期不能晚于今天"):
            manager._validate_date(future_date, rules)
    
    def test_validate_list(self, manager):
        """测试列表验证"""
        rules = {'type': 'list', 'min_length': 1}
        
        # 有效列表
        manager._validate_list([1, 2, 3], rules)
        
        # 无效 - 不是列表
        with pytest.raises(ValidationError, match="必须是列表类型"):
            manager._validate_list('not a list', rules)
        
        # 无效 - 长度不足
        with pytest.raises(ValidationError, match="列表长度不能少于"):
            manager._validate_list([], rules)
    
    def test_perform_calculations_income(self, manager):
        """测试收入计算"""
        template = manager.operation_templates['income_entry']
        data = {
            'amount': 1000.0,
            'tax_rate': 0.13
        }
        
        calculated_data = manager._perform_calculations(template, data)
        
        assert 'tax_amount' in calculated_data
        assert calculated_data['tax_amount'] == 130.0
        assert 'total_amount' in calculated_data
        assert calculated_data['total_amount'] == 1130.0
    
    def test_perform_calculations_batch(self, manager):
        """测试批量操作计算"""
        template = manager.operation_templates['batch_collection']
        data = {
            'items': [
                {'amount': 100.0},
                {'amount': 200.0},
                {'amount': 300.0}
            ]
        }
        
        calculated_data = manager._perform_calculations(template, data)
        
        assert calculated_data['total_amount'] == 600.0
        assert calculated_data['item_count'] == 3
    
    def test_calculate_balance(self, manager):
        """测试余额计算"""
        transactions = [
            {'type': 'income', 'amount': 1000.0},
            {'type': 'expense', 'amount': 300.0},
            {'type': 'income', 'amount': 500.0},
            {'type': 'expense', 'amount': 200.0}
        ]
        
        balance = manager._calculate_balance(transactions)
        
        assert balance == 1000.0  # 1000 - 300 + 500 - 200
    
    def test_execute_one_click_operation_success(self, manager, mock_context_engine):
        """测试一键操作成功执行 (Requirements 3.1, 3.3)"""
        user_id = 'test_user'
        data = {
            'amount': 1000.0,
            'customer_id': 'CUST001',
            'date': '2024-01-15',
            'category': '销售收入'
        }
        
        result = manager.execute_one_click_operation(
            'income_entry', user_id, data
        )
        
        assert result['success'] is True
        assert 'operation_id' in result
        assert result['template_id'] == 'income_entry'
        assert 'execution_time' in result
        
        # 验证记录了操作历史
        assert user_id in manager.operation_history
        assert len(manager.operation_history[user_id]) > 0
        
        # 验证调用了ContextEngine记录交易
        mock_context_engine.record_transaction.assert_called()
    
    def test_execute_one_click_operation_validation_error(self, manager):
        """测试一键操作验证失败"""
        user_id = 'test_user'
        data = {
            'amount': 1000.0
            # 缺少必填字段
        }
        
        result = manager.execute_one_click_operation(
            'income_entry', user_id, data
        )
        
        assert result['success'] is False
        assert result['error_type'] == 'validation'
        assert '验证失败' in result['message']
    
    def test_execute_one_click_operation_invalid_template(self, manager):
        """测试无效模板"""
        user_id = 'test_user'
        data = {}
        
        result = manager.execute_one_click_operation(
            'invalid_template', user_id, data
        )
        
        assert result['success'] is False
        assert result['error_type'] == 'operation'
    
    def test_execute_batch_operation_success(self, manager, mock_context_engine):
        """测试批量操作成功 (Requirement 3.2)"""
        user_id = 'test_user'
        items = [
            {
                'amount': 100.0,
                'customer_id': 'CUST001',
                'date': '2024-01-15',
                'category': '销售收入'
            },
            {
                'amount': 200.0,
                'customer_id': 'CUST002',
                'date': '2024-01-15',
                'category': '销售收入'
            },
            {
                'amount': 300.0,
                'customer_id': 'CUST003',
                'date': '2024-01-15',
                'category': '销售收入'
            }
        ]
        
        result = manager.execute_batch_operation(
            'income_entry', user_id, items
        )
        
        assert result['success'] is True
        assert result['total_items'] == 3
        assert result['successful'] == 3
        assert result['failed'] == 0
        assert len(result['results']) == 3
        assert 'execution_time' in result
    
    def test_execute_batch_operation_partial_failure(self, manager, mock_context_engine):
        """测试批量操作部分失败"""
        user_id = 'test_user'
        items = [
            {
                'amount': 100.0,
                'customer_id': 'CUST001',
                'date': '2024-01-15',
                'category': '销售收入'
            },
            {
                'amount': 200.0
                # 缺少必填字段 - 会失败
            },
            {
                'amount': 300.0,
                'customer_id': 'CUST003',
                'date': '2024-01-15',
                'category': '销售收入'
            }
        ]
        
        result = manager.execute_batch_operation(
            'income_entry', user_id, items
        )
        
        assert result['success'] is False
        assert result['total_items'] == 3
        assert result['successful'] == 2
        assert result['failed'] == 1
        assert len(result['errors']) == 1
    
    def test_rollback_operation(self, manager):
        """测试操作回滚"""
        user_id = 'test_user'
        
        # 先执行一个操作
        data = {
            'amount': 1000.0,
            'customer_id': 'CUST001',
            'date': '2024-01-15',
            'category': '销售收入'
        }
        
        result = manager.execute_one_click_operation(
            'income_entry', user_id, data
        )
        
        assert result['success'] is True
        operation_id = result['operation_id']
        
        # 回滚操作
        rollback_result = manager.rollback_operation(operation_id, user_id)
        
        assert rollback_result['success'] is True
        assert rollback_result['operation_id'] == operation_id
    
    def test_rollback_nonexistent_operation(self, manager):
        """测试回滚不存在的操作"""
        user_id = 'test_user'
        operation_id = 'nonexistent_id'
        
        result = manager.rollback_operation(operation_id, user_id)
        
        assert result['success'] is False
        assert 'not found' in result['error']
    
    def test_get_operation_templates(self, manager, mock_context_engine):
        """测试获取操作模板"""
        user_id = 'test_user'
        
        templates = manager.get_operation_templates(user_id)
        
        assert len(templates) > 0
        assert all('template_id' in t for t in templates)
        assert all('name' in t for t in templates)
        assert all('description' in t for t in templates)
    
    def test_get_frequent_operations(self, manager):
        """测试获取常用操作 (Requirement 3.5)"""
        user_id = 'test_user'
        
        # 执行多次操作以建立历史
        for _ in range(3):
            manager.execute_one_click_operation(
                'income_entry',
                user_id,
                {
                    'amount': 1000.0,
                    'customer_id': 'CUST001',
                    'date': '2024-01-15',
                    'category': '销售收入'
                }
            )
        
        for _ in range(2):
            manager.execute_one_click_operation(
                'expense_entry',
                user_id,
                {
                    'amount': 500.0,
                    'vendor_id': 'VEND001',
                    'date': '2024-01-15',
                    'category': '采购成本'
                }
            )
        
        frequent_ops = manager.get_frequent_operations(user_id, top_n=5)
        
        assert len(frequent_ops) > 0
        # 收入录入应该是最常用的（3次）
        assert frequent_ops[0]['template_id'] == 'income_entry'
        assert frequent_ops[0]['usage_count'] == 3
        # 支出录入应该是第二常用的（2次）
        assert frequent_ops[1]['template_id'] == 'expense_entry'
        assert frequent_ops[1]['usage_count'] == 2
    
    def test_save_income_transaction(self, manager, temp_storage, mock_context_engine):
        """测试保存收入交易"""
        user_id = 'test_user'
        data = {
            'amount': 1000.0,
            'customer_id': 'CUST001',
            'date': '2024-01-15',
            'category': '销售收入'
        }
        
        result = manager._save_income_transaction(data, user_id)
        
        assert result['saved'] is True
        assert 'transaction_id' in result
        assert 'file_path' in result
        
        # 验证文件已创建
        file_path = Path(result['file_path'])
        assert file_path.exists()
        
        # 验证文件内容
        with open(file_path, 'r', encoding='utf-8') as f:
            saved_data = json.load(f)
        
        assert saved_data['user_id'] == user_id
        assert saved_data['type'] == 'income'
        assert saved_data['data']['amount'] == 1000.0
        
        # 验证调用了ContextEngine记录交易
        mock_context_engine.record_transaction.assert_called_with(
            user_id, 'income', data
        )
    
    def test_save_expense_transaction(self, manager, temp_storage, mock_context_engine):
        """测试保存支出交易"""
        user_id = 'test_user'
        data = {
            'amount': 500.0,
            'vendor_id': 'VEND001',
            'date': '2024-01-15',
            'category': '采购成本'
        }
        
        result = manager._save_expense_transaction(data, user_id)
        
        assert result['saved'] is True
        assert 'transaction_id' in result
        
        # 验证文件已创建
        file_path = Path(result['file_path'])
        assert file_path.exists()
        
        # 验证文件内容
        with open(file_path, 'r', encoding='utf-8') as f:
            saved_data = json.load(f)
        
        assert saved_data['type'] == 'expense'
        assert saved_data['data']['amount'] == 500.0
    
    def test_operation_history_persistence(self, manager, temp_storage):
        """测试操作历史持久化"""
        user_id = 'test_user'
        
        # 执行操作
        result = manager.execute_one_click_operation(
            'income_entry',
            user_id,
            {
                'amount': 1000.0,
                'customer_id': 'CUST001',
                'date': '2024-01-15',
                'category': '销售收入'
            }
        )
        
        assert result['success'] is True
        
        # 验证历史文件已创建
        history_file = Path(temp_storage) / f"history_{user_id}.json"
        assert history_file.exists()
        
        # 验证历史内容
        with open(history_file, 'r', encoding='utf-8') as f:
            history = json.load(f)
        
        assert len(history) > 0
        assert history[0]['template_id'] == 'income_entry'
        assert 'operation_id' in history[0]
        assert 'timestamp' in history[0]
    
    def test_atomic_operation_rollback_on_error(self, manager):
        """测试原子操作在错误时的行为"""
        user_id = 'test_user'
        
        # 提供无效数据（金额为负）
        data = {
            'amount': -100.0,  # 无效金额
            'customer_id': 'CUST001',
            'date': '2024-01-15',
            'category': '销售收入'
        }
        
        result = manager.execute_one_click_operation(
            'income_entry', user_id, data
        )
        
        # 操作应该失败
        assert result['success'] is False
        
        # 验证没有创建任何文件（原子性）
        storage_path = Path(manager.storage_path)
        income_files = list(storage_path.glob('income_*.json'))
        assert len(income_files) == 0
    
    def test_concurrent_batch_operations(self, manager, mock_context_engine):
        """测试并发批量操作"""
        user_id = 'test_user'
        
        # 创建两个批量操作
        items1 = [
            {
                'amount': 100.0,
                'customer_id': 'CUST001',
                'date': '2024-01-15',
                'category': '销售收入'
            }
        ]
        
        items2 = [
            {
                'amount': 200.0,
                'vendor_id': 'VEND001',
                'date': '2024-01-15',
                'category': '采购成本'
            }
        ]
        
        result1 = manager.execute_batch_operation('income_entry', user_id, items1)
        result2 = manager.execute_batch_operation('expense_entry', user_id, items2)
        
        assert result1['success'] is True
        assert result2['success'] is True
        assert result1['batch_id'] != result2['batch_id']


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
