"""
Property-based tests for ImportEngine - Import Undo Round-trip

Feature: small-accountant-practical-enhancement
Property 18: Import undo round-trip
Validates: Requirements 4.5
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
    Counterparty, CounterpartyType, TransactionRecord
)


# Hypothesis strategies for generating test data
@st.composite
def valid_transaction_record(draw, counterparty_ids):
    """生成有效的交易记录"""
    assume(len(counterparty_ids) > 0)
    
    return {
        'date': (date.today() - timedelta(days=draw(st.integers(min_value=0, max_value=365)))).strftime('%Y-%m-%d'),
        'type': draw(st.sampled_from(['收入', '支出', '订单'])),
        'amount': float(draw(st.decimals(min_value=Decimal('0.01'), max_value=Decimal('10000'), places=2))),
        'counterparty_id': draw(st.sampled_from(counterparty_ids)),
        'description': draw(st.text(min_size=1, max_size=50, alphabet=st.characters(whitelist_categories=('L', 'N')))),
        'category': draw(st.sampled_from(['销售', '采购', '费用', '其他'])),
        'status': draw(st.sampled_from(['已完成', '待处理']))
    }


@st.composite
def valid_counterparty_record(draw):
    """生成有效的往来单位记录"""
    idx = draw(st.integers(min_value=1, max_value=9999))
    
    # 生成有效的税号（15位数字）
    tax_id_base = draw(st.integers(min_value=100000000000000, max_value=999999999999999))
    
    return {
        'name': f'测试单位{idx}',
        'type': draw(st.sampled_from(['客户', '供应商'])),
        'contact_person': f'联系人{idx}',
        'phone': f'138{idx:08d}',
        'email': f'test{idx}@example.com',
        'address': f'地址{idx}',
        'tax_id': str(tax_id_base)
    }


@st.composite
def transaction_batch(draw, counterparty_ids, min_size=1, max_size=10):
    """生成一批交易记录"""
    assume(len(counterparty_ids) > 0)
    
    size = draw(st.integers(min_value=min_size, max_value=max_size))
    return [draw(valid_transaction_record(counterparty_ids)) for _ in range(size)]


@st.composite
def counterparty_batch(draw, min_size=1, max_size=10):
    """生成一批往来单位记录"""
    size = draw(st.integers(min_value=min_size, max_value=max_size))
    
    # 生成唯一的索引列表
    indices = draw(st.lists(
        st.integers(min_value=1, max_value=99999),
        min_size=size,
        max_size=size,
        unique=True
    ))
    
    records = []
    for idx in indices:
        # 生成有效的税号（15位数字）
        tax_id_base = 100000000000000 + idx
        
        record = {
            'name': f'测试单位{idx}',
            'type': draw(st.sampled_from(['客户', '供应商'])),
            'contact_person': f'联系人{idx}',
            'phone': f'138{idx:08d}',
            'email': f'test{idx}@example.com',
            'address': f'地址{idx}',
            'tax_id': str(tax_id_base)
        }
        records.append(record)
    
    return records


def create_excel_file(data, column_names=None):
    """创建临时Excel文件"""
    if column_names is None:
        # 根据数据类型自动判断列名
        if data and 'amount' in data[0]:
            # 交易记录
            column_names = {
                'date': '日期',
                'type': '类型',
                'amount': '金额',
                'counterparty_id': '往来单位',
                'description': '描述',
                'category': '分类',
                'status': '状态'
            }
        else:
            # 往来单位
            column_names = {
                'name': '名称',
                'type': '类型',
                'contact_person': '联系人',
                'phone': '电话',
                'email': '邮箱',
                'address': '地址',
                'tax_id': '税号'
            }
    
    # 转换为DataFrame
    df = pd.DataFrame(data)
    
    # 重命名列（只重命名存在的列）
    rename_dict = {k: v for k, v in column_names.items() if k in df.columns}
    df = df.rename(columns=rename_dict)
    
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


class TestImportUndoProperties:
    """Property-based tests for import undo round-trip
    
    **Property 18: Import undo round-trip**
    For any completed import operation, performing an undo should restore
    the system to its state before the import (round-trip property).
    **Validates: Requirements 4.5**
    """
    
    @pytest.fixture(autouse=True)
    def setup_storage(self, tmp_path):
        """设置存储层 - 每个测试都使用独立的临时目录"""
        import uuid
        test_dir = tmp_path / str(uuid.uuid4())
        test_dir.mkdir()
        
        transaction_storage = TransactionStorage(str(test_dir / 'transactions.json'))
        counterparty_storage = CounterpartyStorage(str(test_dir / 'counterparties.json'))
        import_history = ImportHistory(str(test_dir / 'import_history.json'))
        
        # 创建测试往来单位
        test_counterparties = [
            Counterparty(
                id='cp001',
                name='测试客户A',
                type=CounterpartyType.CUSTOMER,
                contact_person='张三',
                phone='13800138000',
                email='test@example.com',
                address='测试地址',
                tax_id='123456789012345',
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
                tax_id='987654321098765',
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
    def test_transaction_import_undo_round_trip(self, setup_storage, data):
        """
        Property: 交易记录导入撤销往返属性
        
        验证：
        1. 导入前后的记录数量变化正确
        2. 撤销后记录数量恢复到导入前
        3. 撤销后的记录ID集合与导入前相同
        4. 导入历史正确记录了导入和撤销操作
        """
        engine = setup_storage['engine']
        transaction_storage = setup_storage['transaction_storage']
        import_history = setup_storage['import_history']
        counterparty_ids = setup_storage['counterparty_ids']
        
        # 生成测试数据
        test_data = data.draw(transaction_batch(counterparty_ids, min_size=1, max_size=10))
        
        # 记录导入前的状态
        initial_transactions = transaction_storage.get_all()
        initial_count = len(initial_transactions)
        initial_ids = {t.id for t in initial_transactions}
        
        # 创建Excel文件并导入
        excel_file = create_excel_file(test_data)
        
        try:
            # 执行导入
            import_result = engine.import_transactions(excel_file)
            
            # 验证导入成功
            assert import_result.successful_rows > 0, \
                "导入应该成功"
            assert import_result.can_undo, \
                "导入应该可以撤销"
            
            # 验证导入后的状态
            after_import_transactions = transaction_storage.get_all()
            after_import_count = len(after_import_transactions)
            after_import_ids = {t.id for t in after_import_transactions}
            
            # 验证记录数量增加
            assert after_import_count == initial_count + import_result.successful_rows, \
                f"导入后记录数应该增加{import_result.successful_rows}条，" \
                f"但从{initial_count}变为{after_import_count}"
            
            # 验证新增的记录ID
            new_ids = after_import_ids - initial_ids
            assert len(new_ids) == import_result.successful_rows, \
                f"新增的记录ID数量应该等于成功导入的行数"
            
            # 验证导入历史记录
            import_record = import_history.get_import_by_id(import_result.import_id)
            assert import_record is not None, \
                "导入历史应该记录导入操作"
            assert import_record['import_type'] == 'transaction', \
                "导入类型应该是transaction"
            assert len(import_record['imported_ids']) == import_result.successful_rows, \
                "导入历史应该记录所有导入的记录ID"
            
            # 执行撤销
            undo_success = engine.undo_import(import_result.import_id)
            assert undo_success, \
                "撤销操作应该成功"
            
            # 验证撤销后的状态
            after_undo_transactions = transaction_storage.get_all()
            after_undo_count = len(after_undo_transactions)
            after_undo_ids = {t.id for t in after_undo_transactions}
            
            # 验证记录数量恢复
            assert after_undo_count == initial_count, \
                f"撤销后记录数应该恢复到{initial_count}，但实际为{after_undo_count}"
            
            # 验证记录ID集合恢复
            assert after_undo_ids == initial_ids, \
                "撤销后的记录ID集合应该与导入前相同"
            
            # 验证导入历史标记为已撤销
            import_record_after_undo = import_history.get_import_by_id(import_result.import_id)
            assert import_record_after_undo['undone'] == True, \
                "导入历史应该标记为已撤销"
            assert import_record_after_undo['can_undo'] == False, \
                "已撤销的导入不应该再次可撤销"
            
        finally:
            if os.path.exists(excel_file):
                os.unlink(excel_file)
    
    @given(data=st.data())
    @settings(max_examples=100, suppress_health_check=[HealthCheck.function_scoped_fixture], deadline=None)
    def test_counterparty_import_undo_round_trip(self, setup_storage, data):
        """
        Property: 往来单位导入撤销往返属性
        
        验证：
        1. 导入前后的记录数量变化正确
        2. 撤销后记录数量恢复到导入前
        3. 撤销后的记录ID集合与导入前相同
        4. 往来单位的详细信息在撤销后完全恢复
        """
        engine = setup_storage['engine']
        counterparty_storage = setup_storage['counterparty_storage']
        import_history = setup_storage['import_history']
        
        # 生成测试数据
        test_data = data.draw(counterparty_batch(min_size=1, max_size=10))
        
        # 记录导入前的状态
        initial_counterparties = counterparty_storage.get_all()
        initial_count = len(initial_counterparties)
        initial_ids = {cp.id for cp in initial_counterparties}
        initial_names = {cp.name for cp in initial_counterparties}
        
        # 创建Excel文件并导入
        excel_file = create_excel_file(test_data)
        
        try:
            # 执行导入
            import_result = engine.import_counterparties(excel_file)
            
            # 验证导入成功
            assert import_result.successful_rows > 0, \
                "导入应该成功"
            assert import_result.can_undo, \
                "导入应该可以撤销"
            
            # 验证导入后的状态
            after_import_counterparties = counterparty_storage.get_all()
            after_import_count = len(after_import_counterparties)
            after_import_ids = {cp.id for cp in after_import_counterparties}
            after_import_names = {cp.name for cp in after_import_counterparties}
            
            # 验证记录数量增加
            assert after_import_count == initial_count + import_result.successful_rows, \
                f"导入后记录数应该增加{import_result.successful_rows}条"
            
            # 验证新增的记录
            new_ids = after_import_ids - initial_ids
            assert len(new_ids) == import_result.successful_rows, \
                "新增的记录ID数量应该等于成功导入的行数"
            
            # 验证新增的名称
            new_names = after_import_names - initial_names
            assert len(new_names) == import_result.successful_rows, \
                "新增的单位名称数量应该等于成功导入的行数"
            
            # 执行撤销
            undo_success = engine.undo_import(import_result.import_id)
            assert undo_success, \
                "撤销操作应该成功"
            
            # 验证撤销后的状态
            after_undo_counterparties = counterparty_storage.get_all()
            after_undo_count = len(after_undo_counterparties)
            after_undo_ids = {cp.id for cp in after_undo_counterparties}
            after_undo_names = {cp.name for cp in after_undo_counterparties}
            
            # 验证记录数量恢复
            assert after_undo_count == initial_count, \
                f"撤销后记录数应该恢复到{initial_count}，但实际为{after_undo_count}"
            
            # 验证记录ID集合恢复
            assert after_undo_ids == initial_ids, \
                "撤销后的记录ID集合应该与导入前相同"
            
            # 验证单位名称集合恢复
            assert after_undo_names == initial_names, \
                "撤销后的单位名称集合应该与导入前相同"
            
        finally:
            if os.path.exists(excel_file):
                os.unlink(excel_file)
    
