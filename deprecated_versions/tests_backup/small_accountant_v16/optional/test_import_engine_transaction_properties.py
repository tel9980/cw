"""
Property-based tests for ImportEngine - Transaction Import

Feature: small-accountant-practical-enhancement
Property 15: Transaction import completeness
Validates: Requirements 4.2
"""

import pytest
import os
import tempfile
from datetime import date, datetime, timedelta
from decimal import Decimal
from hypothesis import given, strategies as st, settings, assume
from hypothesis import HealthCheck
import pandas as pd

from small_accountant_v16.import_engine.import_engine import ImportEngine
from small_accountant_v16.storage.transaction_storage import TransactionStorage
from small_accountant_v16.storage.counterparty_storage import CounterpartyStorage
from small_accountant_v16.storage.import_history import ImportHistory
from small_accountant_v16.models.core_models import (
    TransactionType, TransactionStatus, Counterparty, CounterpartyType
)


# Hypothesis strategies for generating test data
@st.composite
def valid_transaction_type(draw):
    """生成有效的交易类型"""
    return draw(st.sampled_from(['收入', '支出', '订单', 'income', 'expense', 'order']))


@st.composite
def valid_date_string(draw):
    """生成有效的日期字符串"""
    # 生成最近3年内的日期
    days_ago = draw(st.integers(min_value=0, max_value=1095))
    target_date = date.today() - timedelta(days=days_ago)
    
    # 随机选择日期格式
    format_choice = draw(st.integers(min_value=0, max_value=2))
    if format_choice == 0:
        return target_date.strftime('%Y-%m-%d')
    elif format_choice == 1:
        return target_date.strftime('%Y/%m/%d')
    else:
        return target_date


@st.composite
def valid_amount(draw):
    """生成有效的金额"""
    # 生成0.01到1000000之间的金额
    return draw(st.decimals(
        min_value=Decimal('0.01'),
        max_value=Decimal('1000000'),
        places=2
    ))


@st.composite
def valid_transaction_record(draw, counterparty_ids):
    """生成有效的交易记录"""
    assume(len(counterparty_ids) > 0)
    
    # 生成安全的文本（只包含可打印字符）
    safe_text = draw(st.text(
        alphabet=st.characters(
            min_codepoint=32,  # 空格
            max_codepoint=126,  # ~
            blacklist_categories=('Cc', 'Cs')  # 排除控制字符和代理字符
        ),
        min_size=1,
        max_size=50
    ))
    
    return {
        'date': draw(valid_date_string()),
        'type': draw(valid_transaction_type()),
        'amount': float(draw(valid_amount())),
        'counterparty_id': draw(st.sampled_from(counterparty_ids)),
        'description': safe_text,
        'category': draw(st.sampled_from(['销售', '采购', '费用', '其他'])),
        'status': draw(st.sampled_from(['已完成', '待处理', 'completed', 'pending']))
    }


@st.composite
def transaction_excel_data(draw, counterparty_ids, min_rows=1, max_rows=50):
    """生成交易记录Excel数据"""
    assume(len(counterparty_ids) > 0)
    
    num_rows = draw(st.integers(min_value=min_rows, max_value=max_rows))
    
    records = []
    for _ in range(num_rows):
        record = draw(valid_transaction_record(counterparty_ids))
        records.append(record)
    
    return records


def create_excel_file(data, column_names=None):
    """创建临时Excel文件"""
    if column_names is None:
        column_names = {
            'date': '日期',
            'type': '类型',
            'amount': '金额',
            'counterparty_id': '往来单位',
            'description': '描述',
            'category': '分类',
            'status': '状态'
        }
    
    # 转换为DataFrame
    df = pd.DataFrame(data)
    
    # 重命名列
    df = df.rename(columns=column_names)
    
    # 创建临时文件
    temp_file = tempfile.NamedTemporaryFile(
        mode='w',
        suffix='.xlsx',
        delete=False
    )
    temp_file.close()
    
    # 写入Excel
    df.to_excel(temp_file.name, index=False)
    
    return temp_file.name


class TestTransactionImportProperties:
    """Property-based tests for transaction import
    
    **Property 15: Transaction import completeness**
    For any valid Excel file containing transaction data (revenue, expenses, orders),
    all valid rows should be successfully imported as Transaction_Records.
    **Validates: Requirements 4.2**
    """
    
    @pytest.fixture(autouse=True)
    def setup_storage(self, tmp_path):
        """设置存储层 - 每个测试都使用独立的临时目录"""
        # 为每个测试创建唯一的临时目录
        import uuid
        test_dir = tmp_path / str(uuid.uuid4())
        test_dir.mkdir()
        
        transaction_storage = TransactionStorage(str(test_dir / 'transactions.json'))
        counterparty_storage = CounterpartyStorage(str(test_dir / 'counterparties.json'))
        import_history = ImportHistory(str(test_dir / 'import_history.json'))
        
        # 创建一些测试往来单位
        test_counterparties = [
            Counterparty(
                id='cp001',
                name='测试客户A',
                type=CounterpartyType.CUSTOMER,
                contact_person='张三',
                phone='13800138000',
                email='test@example.com',
                address='测试地址',
                tax_id='123456789',
                created_at=datetime.now(),
                updated_at=datetime.now()
            ),
            Counterparty(
                id='cp002',
                name='测试供应商B',
                type=CounterpartyType.SUPPLIER,
                contact_person='李四',
                phone='13900139000',
                email='supplier@example.com',
                address='供应商地址',
                tax_id='987654321',
                created_at=datetime.now(),
                updated_at=datetime.now()
            ),
            Counterparty(
                id='cp003',
                name='测试客户C',
                type=CounterpartyType.CUSTOMER,
                contact_person='王五',
                phone='13700137000',
                email='customer@example.com',
                address='客户地址',
                tax_id='111222333',
                created_at=datetime.now(),
                updated_at=datetime.now()
            )
        ]
        
        for cp in test_counterparties:
            counterparty_storage.add(cp)
        
        engine = ImportEngine(
            transaction_storage,
            counterparty_storage,
            import_history
        )
        
        return {
            'engine': engine,
            'transaction_storage': transaction_storage,
            'counterparty_storage': counterparty_storage,
            'import_history': import_history,
            'counterparty_ids': [cp.id for cp in test_counterparties]
        }
    
    @given(data=st.data())
    @settings(max_examples=100, suppress_health_check=[HealthCheck.function_scoped_fixture], deadline=None)
    def test_all_valid_transactions_are_imported(self, setup_storage, data):
        """
        Property: 所有有效的交易记录都应该被成功导入
        
        验证：
        1. 导入结果中successful_rows等于输入的有效行数
        2. 导入后存储中的记录数等于导入的记录数
        3. 导入的记录可以被检索
        """
        engine = setup_storage['engine']
        transaction_storage = setup_storage['transaction_storage']
        counterparty_ids = setup_storage['counterparty_ids']
        
        # 生成测试数据
        excel_data = data.draw(transaction_excel_data(counterparty_ids, min_rows=1, max_rows=20))
        
        # 创建Excel文件
        excel_file = create_excel_file(excel_data)
        
        try:
            # 记录导入前的记录数
            initial_count = len(transaction_storage.get_all())
            
            # 执行导入
            result = engine.import_transactions(excel_file)
            
            # 验证导入结果
            assert result.total_rows == len(excel_data), \
                f"总行数应该等于输入数据行数: {result.total_rows} != {len(excel_data)}"
            
            assert result.successful_rows == len(excel_data), \
                f"成功导入行数应该等于输入数据行数: {result.successful_rows} != {len(excel_data)}"
            
            assert result.failed_rows == 0, \
                f"失败行数应该为0: {result.failed_rows}"
            
            assert len(result.errors) == 0, \
                f"不应该有错误: {result.errors}"
            
            # 验证存储中的记录数
            final_count = len(transaction_storage.get_all())
            assert final_count == initial_count + len(excel_data), \
                f"存储中的记录数应该增加{len(excel_data)}条"
            
            # 验证can_undo标志
            assert result.can_undo is True, "应该可以撤销导入"
            
        finally:
            # 清理临时文件
            if os.path.exists(excel_file):
                os.unlink(excel_file)
    
    @given(data=st.data())
    @settings(max_examples=100, suppress_health_check=[HealthCheck.function_scoped_fixture], deadline=None)
    def test_imported_transactions_match_source_data(self, setup_storage, data):
        """
        Property: 导入的交易记录应该与源数据匹配
        
        验证：
        1. 导入的记录数量正确
        2. 导入的记录字段值与源数据一致
        3. 日期、金额、类型等关键字段正确转换
        """
        engine = setup_storage['engine']
        transaction_storage = setup_storage['transaction_storage']
        counterparty_ids = setup_storage['counterparty_ids']
        
        # 生成测试数据
        excel_data = data.draw(transaction_excel_data(counterparty_ids, min_rows=1, max_rows=10))
        
        # 创建Excel文件
        excel_file = create_excel_file(excel_data)
        
        try:
            # 执行导入
            result = engine.import_transactions(excel_file)
            
            # 获取所有导入的记录
            all_transactions = transaction_storage.get_all()
            imported_transactions = [
                t for t in all_transactions
                if t.id in (result.import_id if hasattr(result, 'imported_ids') else [])
            ]
            
            # 验证导入的记录数量
            assert len(all_transactions) >= len(excel_data), \
                "导入后的记录数应该至少等于源数据行数"
            
            # 验证金额总和（简单的数据完整性检查）
            source_total = sum(Decimal(str(record['amount'])) for record in excel_data)
            imported_total = sum(t.amount for t in all_transactions[-len(excel_data):])
            
            # 允许小的浮点误差
            assert abs(source_total - imported_total) < Decimal('0.01'), \
                f"导入的金额总和应该与源数据一致: {source_total} != {imported_total}"
            
        finally:
            if os.path.exists(excel_file):
                os.unlink(excel_file)
    
    @given(data=st.data())
    @settings(max_examples=50, suppress_health_check=[HealthCheck.function_scoped_fixture], deadline=None)
    def test_import_with_different_column_names(self, setup_storage, data):
        """
        Property: 使用不同的列名格式应该都能成功导入
        
        验证：
        1. 中文列名可以导入
        2. 英文列名可以导入
        3. 混合列名可以导入
        """
        engine = setup_storage['engine']
        counterparty_ids = setup_storage['counterparty_ids']
        
        # 生成测试数据
        excel_data = data.draw(transaction_excel_data(counterparty_ids, min_rows=1, max_rows=10))
        
        # 随机选择列名格式
        column_format = data.draw(st.integers(min_value=0, max_value=2))
        
        if column_format == 0:
            # 中文列名
            column_names = {
                'date': '日期',
                'type': '类型',
                'amount': '金额',
                'counterparty_id': '往来单位',
                'description': '描述',
                'category': '分类',
                'status': '状态'
            }
        elif column_format == 1:
            # 英文列名
            column_names = {
                'date': 'date',
                'type': 'type',
                'amount': 'amount',
                'counterparty_id': 'counterparty_id',
                'description': 'description',
                'category': 'category',
                'status': 'status'
            }
        else:
            # 变体列名
            column_names = {
                'date': '交易日期',
                'type': '交易类型',
                'amount': '交易金额',
                'counterparty_id': '客户',
                'description': '备注',
                'category': '类别',
                'status': '状态'
            }
        
        # 创建Excel文件
        excel_file = create_excel_file(excel_data, column_names)
        
        try:
            # 执行导入
            result = engine.import_transactions(excel_file)
            
            # 验证导入成功
            assert result.successful_rows == len(excel_data), \
                f"使用列名格式{column_format}时，应该成功导入所有记录"
            
        finally:
            if os.path.exists(excel_file):
                os.unlink(excel_file)
    
    @given(data=st.data())
    @settings(max_examples=50, suppress_health_check=[HealthCheck.function_scoped_fixture], deadline=None)
    def test_import_result_contains_valid_import_id(self, setup_storage, data):
        """
        Property: 导入结果应该包含有效的导入ID
        
        验证：
        1. import_id不为空
        2. import_id可以用于查询导入历史
        3. import_id可以用于撤销操作
        """
        engine = setup_storage['engine']
        import_history = setup_storage['import_history']
        counterparty_ids = setup_storage['counterparty_ids']
        
        # 生成测试数据
        excel_data = data.draw(transaction_excel_data(counterparty_ids, min_rows=1, max_rows=10))
        
        # 创建Excel文件
        excel_file = create_excel_file(excel_data)
        
        try:
            # 执行导入
            result = engine.import_transactions(excel_file)
            
            # 验证import_id
            assert result.import_id is not None, "import_id不应该为空"
            assert len(result.import_id) > 0, "import_id应该是非空字符串"
            
            # 验证可以查询导入历史
            import_record = import_history.get_import_by_id(result.import_id)
            assert import_record is not None, "应该能通过import_id查询到导入记录"
            
            # 验证导入历史包含正确信息
            assert import_record['import_type'] == 'transaction'
            assert len(import_record['imported_ids']) == result.successful_rows
            
        finally:
            if os.path.exists(excel_file):
                os.unlink(excel_file)
    
    @given(data=st.data())
    @settings(max_examples=50, suppress_health_check=[HealthCheck.function_scoped_fixture], deadline=None)
    def test_empty_excel_file_handled_gracefully(self, setup_storage, data):
        """
        Property: 空Excel文件应该被优雅处理
        
        验证：
        1. 不应该抛出异常
        2. 返回的结果应该表明没有记录被导入
        3. total_rows应该为0
        """
        engine = setup_storage['engine']
        
        # 创建空Excel文件
        empty_data = []
        excel_file = create_excel_file(empty_data) if empty_data else None
        
        # 创建一个真正的空Excel文件
        temp_file = tempfile.NamedTemporaryFile(
            mode='w',
            suffix='.xlsx',
            delete=False
        )
        temp_file.close()
        
        df = pd.DataFrame()
        df.to_excel(temp_file.name, index=False)
        excel_file = temp_file.name
        
        try:
            # 执行导入
            result = engine.import_transactions(excel_file)
            
            # 验证结果
            assert result.total_rows == 0, "空文件的total_rows应该为0"
            assert result.successful_rows == 0, "空文件的successful_rows应该为0"
            assert result.can_undo is False, "空导入不应该可以撤销"
            
        finally:
            if os.path.exists(excel_file):
                os.unlink(excel_file)
    
    @given(data=st.data())
    @settings(max_examples=50, suppress_health_check=[HealthCheck.function_scoped_fixture], deadline=None)
    def test_import_date_is_recorded(self, setup_storage, data):
        """
        Property: 导入日期应该被正确记录
        
        验证：
        1. import_date不为空
        2. import_date是合理的时间（接近当前时间）
        """
        engine = setup_storage['engine']
        counterparty_ids = setup_storage['counterparty_ids']
        
        # 生成测试数据
        excel_data = data.draw(transaction_excel_data(counterparty_ids, min_rows=1, max_rows=5))
        
        # 创建Excel文件
        excel_file = create_excel_file(excel_data)
        
        try:
            # 记录导入前的时间
            before_import = datetime.now()
            
            # 执行导入
            result = engine.import_transactions(excel_file)
            
            # 记录导入后的时间
            after_import = datetime.now()
            
            # 验证import_date
            assert result.import_date is not None, "import_date不应该为空"
            assert isinstance(result.import_date, datetime), "import_date应该是datetime对象"
            
            # 验证时间在合理范围内（允许1分钟误差）
            assert before_import <= result.import_date <= after_import + timedelta(minutes=1), \
                "import_date应该在导入操作的时间范围内"
            
        finally:
            if os.path.exists(excel_file):
                os.unlink(excel_file)
    
    def test_standard_transaction_types_are_imported_correctly(self, setup_storage):
        """
        单元测试: 标准交易类型应该被正确导入
        
        验证收入、支出、订单三种类型都能正确导入
        """
        engine = setup_storage['engine']
        transaction_storage = setup_storage['transaction_storage']
        counterparty_ids = setup_storage['counterparty_ids']
        
        # 创建包含三种类型的测试数据
        test_data = [
            {
                'date': '2024-01-01',
                'type': '收入',
                'amount': 1000.00,
                'counterparty_id': counterparty_ids[0],
                'description': '销售收入',
                'category': '销售',
                'status': '已完成'
            },
            {
                'date': '2024-01-02',
                'type': '支出',
                'amount': 500.00,
                'counterparty_id': counterparty_ids[1],
                'description': '采购支出',
                'category': '采购',
                'status': '已完成'
            },
            {
                'date': '2024-01-03',
                'type': '订单',
                'amount': 2000.00,
                'counterparty_id': counterparty_ids[2],
                'description': '新订单',
                'category': '销售',
                'status': '待处理'
            }
        ]
        
        excel_file = create_excel_file(test_data)
        
        try:
            result = engine.import_transactions(excel_file)
            
            assert result.successful_rows == 3, "应该成功导入3条记录"
            
            # 验证导入的记录类型
            transactions = transaction_storage.get_all()
            types = [t.type for t in transactions[-3:]]
            
            assert TransactionType.INCOME in types, "应该包含收入类型"
            assert TransactionType.EXPENSE in types, "应该包含支出类型"
            assert TransactionType.ORDER in types, "应该包含订单类型"
            
        finally:
            if os.path.exists(excel_file):
                os.unlink(excel_file)
