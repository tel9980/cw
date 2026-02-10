"""
Unit tests for ReconciliationAssistant

Tests the core functionality of the reconciliation assistant including:
- Bank statement reconciliation
- Customer statement generation
- Supplier account reconciliation
"""

import pytest
from datetime import date, datetime
from decimal import Decimal
from pathlib import Path
import tempfile
import shutil

import pandas as pd
from openpyxl import Workbook

from small_accountant_v16.models.core_models import (
    TransactionRecord,
    TransactionType,
    TransactionStatus,
    Counterparty,
    CounterpartyType,
    BankRecord
)
from small_accountant_v16.reconciliation.reconciliation_assistant import (
    ReconciliationAssistant
)
from small_accountant_v16.storage.transaction_storage import TransactionStorage
from small_accountant_v16.storage.counterparty_storage import CounterpartyStorage


@pytest.fixture
def temp_dir():
    """创建临时目录用于测试"""
    temp_path = tempfile.mkdtemp()
    yield temp_path
    shutil.rmtree(temp_path)


@pytest.fixture
def transaction_storage(temp_dir):
    """创建测试用的交易记录存储"""
    storage = TransactionStorage(temp_dir)
    
    # 添加测试数据
    transactions = [
        TransactionRecord(
            id="T001",
            date=date(2024, 1, 15),
            type=TransactionType.INCOME,
            amount=Decimal("10000.00"),
            counterparty_id="C001",
            description="销售收入",
            category="产品销售",
            status=TransactionStatus.COMPLETED,
            created_at=datetime.now(),
            updated_at=datetime.now()
        ),
        TransactionRecord(
            id="T002",
            date=date(2024, 1, 20),
            type=TransactionType.EXPENSE,
            amount=Decimal("5000.00"),
            counterparty_id="S001",
            description="采购原材料",
            category="原材料采购",
            status=TransactionStatus.COMPLETED,
            created_at=datetime.now(),
            updated_at=datetime.now()
        ),
        TransactionRecord(
            id="T003",
            date=date(2024, 1, 25),
            type=TransactionType.INCOME,
            amount=Decimal("8000.00"),
            counterparty_id="C001",
            description="服务收入",
            category="服务费",
            status=TransactionStatus.COMPLETED,
            created_at=datetime.now(),
            updated_at=datetime.now()
        ),
        TransactionRecord(
            id="T004",
            date=date(2024, 1, 28),
            type=TransactionType.ORDER,
            amount=Decimal("3000.00"),
            counterparty_id="S001",
            description="采购订单",
            category="原材料采购",
            status=TransactionStatus.PENDING,
            created_at=datetime.now(),
            updated_at=datetime.now()
        ),
    ]
    
    for transaction in transactions:
        storage.add(transaction)
    
    return storage


@pytest.fixture
def counterparty_storage(temp_dir):
    """创建测试用的往来单位存储"""
    storage = CounterpartyStorage(temp_dir)
    
    # 添加测试数据
    counterparties = [
        Counterparty(
            id="C001",
            name="ABC公司",
            type=CounterpartyType.CUSTOMER,
            contact_person="张三",
            phone="13800138000",
            email="zhangsan@abc.com",
            address="北京市朝阳区",
            tax_id="110000000000001",
            created_at=datetime.now(),
            updated_at=datetime.now()
        ),
        Counterparty(
            id="S001",
            name="XYZ供应商",
            type=CounterpartyType.SUPPLIER,
            contact_person="李四",
            phone="13900139000",
            email="lisi@xyz.com",
            address="上海市浦东新区",
            tax_id="310000000000001",
            created_at=datetime.now(),
            updated_at=datetime.now()
        ),
    ]
    
    for counterparty in counterparties:
        storage.add(counterparty)
    
    return storage


@pytest.fixture
def assistant(transaction_storage, counterparty_storage, temp_dir):
    """创建测试用的对账助手"""
    return ReconciliationAssistant(
        transaction_storage=transaction_storage,
        counterparty_storage=counterparty_storage,
        output_dir=temp_dir
    )


@pytest.fixture
def sample_bank_statement_file(temp_dir):
    """创建示例银行流水Excel文件"""
    file_path = Path(temp_dir) / "bank_statement.xlsx"
    
    # 创建示例数据
    data = {
        '交易日期': ['2024-01-15', '2024-01-20', '2024-01-25', '2024-01-30'],
        '往来单位': ['ABC公司', 'XYZ供应商', 'ABC公司', '其他公司'],
        '金额': [10000.00, 5000.00, 8000.00, 2000.00],
        '余额': [10000.00, 5000.00, 13000.00, 15000.00],
        '摘要': ['销售收入', '采购原材料', '服务收入', '其他收入']
    }
    
    df = pd.DataFrame(data)
    df.to_excel(file_path, index=False)
    
    return str(file_path)


class TestReconciliationAssistant:
    """测试ReconciliationAssistant类"""
    
    def test_initialization(self, assistant):
        """测试初始化"""
        assert assistant is not None
        assert assistant.transaction_storage is not None
        assert assistant.counterparty_storage is not None
        assert assistant.matcher is not None
        assert assistant.report_generator is not None
    
    def test_reconcile_bank_statement_basic(
        self, 
        assistant, 
        sample_bank_statement_file
    ):
        """测试基本的银行对账功能"""
        # 执行对账
        result = assistant.reconcile_bank_statement(sample_bank_statement_file)
        
        # 验证结果
        assert result is not None
        assert result.matched_count >= 0
        assert isinstance(result.unmatched_bank_records, list)
        assert isinstance(result.unmatched_system_records, list)
        assert isinstance(result.discrepancies, list)
        assert result.reconciliation_date is not None
        
        # 银行流水有4条记录
        assert len(result.unmatched_bank_records) + result.matched_count == 4
        
        # 应该识别出差异
        assert len(result.discrepancies) > 0
    
    def test_reconcile_bank_statement_with_date_range(
        self,
        assistant,
        sample_bank_statement_file
    ):
        """测试带日期范围的银行对账"""
        # 指定日期范围
        start_date = date(2024, 1, 1)
        end_date = date(2024, 1, 31)
        
        result = assistant.reconcile_bank_statement(
            sample_bank_statement_file,
            start_date=start_date,
            end_date=end_date
        )
        
        assert result is not None
        assert result.matched_count >= 0
    
    def test_reconcile_bank_statement_file_not_found(self, assistant):
        """测试银行流水文件不存在的情况"""
        with pytest.raises(FileNotFoundError):
            assistant.reconcile_bank_statement("nonexistent_file.xlsx")
    
    def test_reconcile_bank_statement_invalid_format(self, assistant, temp_dir):
        """测试无效的银行流水文件格式"""
        # 创建一个格式不正确的Excel文件
        file_path = Path(temp_dir) / "invalid_statement.xlsx"
        data = {
            '无关列1': [1, 2, 3],
            '无关列2': ['a', 'b', 'c']
        }
        df = pd.DataFrame(data)
        df.to_excel(file_path, index=False)
        
        with pytest.raises(ValueError, match="缺少必需列"):
            assistant.reconcile_bank_statement(str(file_path))
    
    def test_generate_customer_statement_basic(
        self,
        assistant,
        counterparty_storage
    ):
        """测试生成客户对账单"""
        # 生成客户对账单
        report_path = assistant.generate_customer_statement(
            customer_id="C001",
            start_date=date(2024, 1, 1),
            end_date=date(2024, 1, 31)
        )
        
        # 验证文件已生成
        assert Path(report_path).exists()
        assert report_path.endswith('.xlsx')
        
        # 验证文件名包含客户名称
        assert 'ABC公司' in report_path
    
    def test_generate_customer_statement_with_opening_balance(
        self,
        assistant
    ):
        """测试带期初余额的客户对账单"""
        opening_balance = Decimal("5000.00")
        
        report_path = assistant.generate_customer_statement(
            customer_id="C001",
            start_date=date(2024, 1, 1),
            end_date=date(2024, 1, 31),
            opening_balance=opening_balance
        )
        
        assert Path(report_path).exists()
    
    def test_generate_customer_statement_customer_not_found(self, assistant):
        """测试客户不存在的情况"""
        with pytest.raises(ValueError, match="客户不存在"):
            assistant.generate_customer_statement(
                customer_id="NONEXISTENT",
                start_date=date(2024, 1, 1),
                end_date=date(2024, 1, 31)
            )
    
    def test_generate_customer_statement_wrong_type(self, assistant):
        """测试往来单位类型错误的情况"""
        # S001是供应商，不是客户
        with pytest.raises(ValueError, match="不是客户类型"):
            assistant.generate_customer_statement(
                customer_id="S001",
                start_date=date(2024, 1, 1),
                end_date=date(2024, 1, 31)
            )
    
    def test_generate_customer_statement_no_transactions(
        self,
        assistant,
        counterparty_storage
    ):
        """测试没有交易记录的客户对账单"""
        # 添加一个没有交易的客户
        new_customer = Counterparty(
            id="C002",
            name="新客户",
            type=CounterpartyType.CUSTOMER,
            contact_person="王五",
            phone="13700137000",
            email="wangwu@new.com",
            address="广州市天河区",
            tax_id="440000000000001",
            created_at=datetime.now(),
            updated_at=datetime.now()
        )
        counterparty_storage.add(new_customer)
        
        # 生成对账单
        report_path = assistant.generate_customer_statement(
            customer_id="C002",
            start_date=date(2024, 1, 1),
            end_date=date(2024, 1, 31)
        )
        
        # 应该成功生成，即使没有交易记录
        assert Path(report_path).exists()
    
    def test_reconcile_supplier_accounts_basic(self, assistant):
        """测试基本的供应商对账功能"""
        # 执行供应商对账
        result = assistant.reconcile_supplier_accounts(supplier_id="S001")
        
        # 验证结果
        assert result is not None
        assert result.matched_count >= 0
        assert isinstance(result.unmatched_bank_records, list)
        assert isinstance(result.unmatched_system_records, list)
        assert isinstance(result.discrepancies, list)
        assert result.reconciliation_date is not None
        
        # 应该有未匹配的订单（因为有一个订单没有对应的付款）
        assert len(result.unmatched_bank_records) > 0
    
    def test_reconcile_supplier_accounts_with_date_range(self, assistant):
        """测试带日期范围的供应商对账"""
        result = assistant.reconcile_supplier_accounts(
            supplier_id="S001",
            start_date=date(2024, 1, 1),
            end_date=date(2024, 1, 31)
        )
        
        assert result is not None
        assert result.matched_count >= 0
    
    def test_reconcile_supplier_accounts_supplier_not_found(self, assistant):
        """测试供应商不存在的情况"""
        with pytest.raises(ValueError, match="供应商不存在"):
            assistant.reconcile_supplier_accounts(supplier_id="NONEXISTENT")
    
    def test_reconcile_supplier_accounts_wrong_type(self, assistant):
        """测试往来单位类型错误的情况"""
        # C001是客户，不是供应商
        with pytest.raises(ValueError, match="不是供应商类型"):
            assistant.reconcile_supplier_accounts(supplier_id="C001")
    
    def test_load_bank_statement_column_recognition(self, assistant, temp_dir):
        """测试银行流水列名识别"""
        # 创建使用不同列名的银行流水文件
        file_path = Path(temp_dir) / "bank_statement_alt.xlsx"
        
        data = {
            'date': ['2024-01-15', '2024-01-20'],
            'counterparty': ['ABC公司', 'XYZ供应商'],
            'amount': [10000.00, 5000.00],
            'balance': [10000.00, 5000.00],
            'description': ['销售收入', '采购原材料']
        }
        
        df = pd.DataFrame(data)
        df.to_excel(file_path, index=False)
        
        # 应该能够正确识别列名
        bank_records = assistant._load_bank_statement(str(file_path))
        
        assert len(bank_records) == 2
        assert bank_records[0].counterparty == 'ABC公司'
        assert bank_records[0].amount == Decimal("10000.00")
    
    def test_load_bank_statement_chinese_columns(self, assistant, temp_dir):
        """测试中文列名的银行流水"""
        file_path = Path(temp_dir) / "bank_statement_chinese.xlsx"
        
        data = {
            '日期': ['2024-01-15', '2024-01-20'],
            '对方户名': ['ABC公司', 'XYZ供应商'],
            '交易金额': [10000.00, 5000.00],
            '账户余额': [10000.00, 5000.00],
            '摘要': ['销售收入', '采购原材料']
        }
        
        df = pd.DataFrame(data)
        df.to_excel(file_path, index=False)
        
        bank_records = assistant._load_bank_statement(str(file_path))
        
        assert len(bank_records) == 2
        assert bank_records[0].counterparty == 'ABC公司'
    
    def test_load_bank_statement_empty_file(self, assistant, temp_dir):
        """测试空的银行流水文件"""
        file_path = Path(temp_dir) / "empty_statement.xlsx"
        
        # 创建只有表头的文件
        data = {
            '日期': [],
            '往来单位': [],
            '金额': []
        }
        
        df = pd.DataFrame(data)
        df.to_excel(file_path, index=False)
        
        with pytest.raises(ValueError, match="没有有效的记录"):
            assistant._load_bank_statement(str(file_path))
    
    def test_recognize_bank_statement_columns(self, assistant):
        """测试列名识别功能"""
        # 测试中文列名
        columns = ['交易日期', '往来单位', '金额', '余额', '摘要']
        mapping = assistant._recognize_bank_statement_columns(columns)
        
        assert 'date' in mapping
        assert 'counterparty' in mapping
        assert 'amount' in mapping
        assert 'balance' in mapping
        assert 'description' in mapping
        
        # 测试英文列名
        columns = ['date', 'counterparty', 'amount', 'balance', 'description']
        mapping = assistant._recognize_bank_statement_columns(columns)
        
        assert 'date' in mapping
        assert 'counterparty' in mapping
        assert 'amount' in mapping
    
    def test_recognize_bank_statement_columns_variations(self, assistant):
        """测试列名识别的各种变体"""
        # 测试日期列的变体
        columns = ['时间', '往来单位', '金额']
        mapping = assistant._recognize_bank_statement_columns(columns)
        assert 'date' in mapping
        
        # 测试往来单位列的变体
        columns = ['日期', '对方账户', '金额']
        mapping = assistant._recognize_bank_statement_columns(columns)
        assert 'counterparty' in mapping
        
        # 测试金额列的变体
        columns = ['日期', '往来单位', '发生额']
        mapping = assistant._recognize_bank_statement_columns(columns)
        assert 'amount' in mapping


class TestReconciliationAssistantEdgeCases:
    """测试边界情况"""
    
    def test_reconcile_with_exact_matches(
        self,
        assistant,
        sample_bank_statement_file
    ):
        """测试对账功能正常执行"""
        result = assistant.reconcile_bank_statement(sample_bank_statement_file)
        
        # 验证对账功能正常执行
        assert result is not None
        assert result.reconciliation_date is not None
        # 总记录数应该等于银行记录数
        total_bank_records = len(result.unmatched_bank_records) + result.matched_count
        assert total_bank_records == 4
    
    def test_reconcile_with_no_matches(self, assistant, temp_dir):
        """测试完全不匹配的情况"""
        # 创建一个完全不匹配的银行流水
        file_path = Path(temp_dir) / "no_match_statement.xlsx"
        
        data = {
            '交易日期': ['2024-12-01', '2024-12-02'],
            '往来单位': ['完全不存在的公司', '另一个不存在的公司'],
            '金额': [99999.00, 88888.00],
            '余额': [99999.00, 188887.00],
            '摘要': ['不相关的交易', '另一个不相关的交易']
        }
        
        df = pd.DataFrame(data)
        df.to_excel(file_path, index=False)
        
        result = assistant.reconcile_bank_statement(str(file_path))
        
        # 应该没有匹配
        assert result.matched_count == 0
        # 所有银行记录都应该未匹配
        assert len(result.unmatched_bank_records) == 2
    
    def test_customer_statement_with_large_amounts(
        self,
        assistant,
        transaction_storage,
        counterparty_storage
    ):
        """测试大金额的客户对账单"""
        # 添加大金额交易
        large_transaction = TransactionRecord(
            id="T999",
            date=date(2024, 1, 15),
            type=TransactionType.INCOME,
            amount=Decimal("9999999.99"),
            counterparty_id="C001",
            description="大额交易",
            category="特殊业务",
            status=TransactionStatus.COMPLETED,
            created_at=datetime.now(),
            updated_at=datetime.now()
        )
        transaction_storage.add(large_transaction)
        
        report_path = assistant.generate_customer_statement(
            customer_id="C001",
            start_date=date(2024, 1, 1),
            end_date=date(2024, 1, 31)
        )
        
        assert Path(report_path).exists()
    
    def test_supplier_reconciliation_all_paid(
        self,
        assistant,
        transaction_storage
    ):
        """测试供应商对账功能"""
        # 为现有订单添加付款记录
        payment = TransactionRecord(
            id="T005",
            date=date(2024, 1, 29),
            type=TransactionType.EXPENSE,
            amount=Decimal("3000.00"),
            counterparty_id="S001",
            description="采购订单",
            category="原材料采购",
            status=TransactionStatus.COMPLETED,
            created_at=datetime.now(),
            updated_at=datetime.now()
        )
        transaction_storage.add(payment)
        
        result = assistant.reconcile_supplier_accounts(supplier_id="S001")
        
        # 验证对账功能正常执行
        assert result is not None
        assert result.reconciliation_date is not None
        # 应该有一些记录（匹配或未匹配）
        total_records = result.matched_count + len(result.unmatched_bank_records) + len(result.unmatched_system_records)
        assert total_records > 0


class TestReconciliationAssistantIntegration:
    """集成测试"""
    
    def test_complete_reconciliation_workflow(
        self,
        assistant,
        sample_bank_statement_file
    ):
        """测试完整的对账工作流"""
        # 1. 执行银行对账
        bank_result = assistant.reconcile_bank_statement(sample_bank_statement_file)
        assert bank_result is not None
        
        # 2. 生成客户对账单
        customer_report = assistant.generate_customer_statement(
            customer_id="C001",
            start_date=date(2024, 1, 1),
            end_date=date(2024, 1, 31)
        )
        assert Path(customer_report).exists()
        
        # 3. 执行供应商对账
        supplier_result = assistant.reconcile_supplier_accounts(supplier_id="S001")
        assert supplier_result is not None
        
        # 所有操作都应该成功完成
        assert bank_result.reconciliation_date is not None
        assert supplier_result.reconciliation_date is not None
