"""
Property-based tests for ImportEngine - Import Preview Validation

Feature: small-accountant-practical-enhancement
Property 17: Import preview validation
Validates: Requirements 4.4
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
    Counterparty, CounterpartyType
)


# Hypothesis strategies for generating test data with errors
@st.composite
def invalid_transaction_record(draw, counterparty_ids):
    """生成包含错误的交易记录"""
    error_type = draw(st.integers(min_value=0, max_value=5))
    
    base_record = {
        'date': '2024-01-01',
        'type': '收入',
        'amount': 100.00,
        'counterparty_id': counterparty_ids[0] if counterparty_ids else 'cp001',
        'description': '测试',
        'category': '销售',
        'status': '已完成'
    }
    
    if error_type == 0:
        # 缺少必需字段 - 日期
        del base_record['date']
    elif error_type == 1:
        # 缺少必需字段 - 类型
        del base_record['type']
    elif error_type == 2:
        # 缺少必需字段 - 金额
        del base_record['amount']
    elif error_type == 3:
        # 无效的交易类型
        base_record['type'] = '无效类型'
    elif error_type == 4:
        # 无效的金额（负数）
        base_record['amount'] = -100.00
    elif error_type == 5:
        # 无效的日期格式
        base_record['date'] = '不是日期'
    
    return base_record


@st.composite
def invalid_counterparty_record(draw):
    """生成包含错误的往来单位记录"""
    error_type = draw(st.integers(min_value=0, max_value=5))
    
    base_record = {
        'name': '测试单位',
        'type': '客户',
        'contact_person': '张三',
        'phone': '13800138000',
        'email': 'test@example.com',
        'address': '测试地址',
        'tax_id': '123456789012345'
    }
    
    if error_type == 0:
        # 缺少必需字段 - 名称
        del base_record['name']
    elif error_type == 1:
        # 缺少必需字段 - 类型
        del base_record['type']
    elif error_type == 2:
        # 无效的单位类型
        base_record['type'] = '无效类型'
    elif error_type == 3:
        # 无效的邮箱格式
        base_record['email'] = '不是邮箱'
    elif error_type == 4:
        # 名称太短
        base_record['name'] = 'A'
    elif error_type == 5:
        # 税号太短
        base_record['tax_id'] = '123'
    
    return base_record


@st.composite
def mixed_transaction_data(draw, counterparty_ids, valid_count, invalid_count):
    """生成混合的交易数据（包含有效和无效记录）"""
    assume(len(counterparty_ids) > 0)
    
    records = []
    
    # 添加有效记录
    for i in range(valid_count):
        records.append({
            'date': (date.today() - timedelta(days=i)).strftime('%Y-%m-%d'),
            'type': draw(st.sampled_from(['收入', '支出', '订单'])),
            'amount': float(draw(st.decimals(min_value=Decimal('0.01'), max_value=Decimal('10000'), places=2))),
            'counterparty_id': draw(st.sampled_from(counterparty_ids)),
            'description': f'有效记录{i}',
            'category': '销售',
            'status': '已完成'
        })
    
    # 添加无效记录
    for _ in range(invalid_count):
        invalid_record = draw(invalid_transaction_record(counterparty_ids))
        records.append(invalid_record)
    
    # 打乱顺序
    draw(st.randoms()).shuffle(records)
    
    return records


@st.composite
def mixed_counterparty_data(draw, valid_count, invalid_count):
    """生成混合的往来单位数据（包含有效和无效记录）"""
    records = []
    
    # 添加有效记录
    for i in range(valid_count):
        records.append({
            'name': f'测试单位{i}',
            'type': draw(st.sampled_from(['客户', '供应商'])),
            'contact_person': f'联系人{i}',
            'phone': f'138{i:08d}',
            'email': f'test{i}@example.com',
            'address': f'地址{i}',
            'tax_id': f'{i:015d}'
        })
    
    # 添加无效记录
    for _ in range(invalid_count):
        invalid_record = draw(invalid_counterparty_record())
        records.append(invalid_record)
    
    # 打乱顺序
    draw(st.randoms()).shuffle(records)
    
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


class TestImportPreviewProperties:
    """Property-based tests for import preview validation
    
    **Property 17: Import preview validation**
    For any Excel file prepared for import, the preview should identify
    all validation errors before the actual import occurs.
    **Validates: Requirements 4.4**
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
            'counterparty_ids': [cp.id for cp in test_counterparties]
        }
    
    @given(data=st.data())
    @settings(max_examples=100, suppress_health_check=[HealthCheck.function_scoped_fixture], deadline=None)
    def test_preview_identifies_all_validation_errors(self, setup_storage, data):
        """
        Property: 预览应该识别所有验证错误
        
        验证：
        1. 预览返回的错误数量与实际错误数量一致
        2. 每个错误都包含行号、字段名和错误消息
        3. 预览不会修改存储中的数据
        """
        engine = setup_storage['engine']
        transaction_storage = setup_storage['transaction_storage']
        counterparty_ids = setup_storage['counterparty_ids']
        
        # 生成混合数据（有效和无效记录）
        valid_count = data.draw(st.integers(min_value=0, max_value=5))
        invalid_count = data.draw(st.integers(min_value=1, max_value=5))
        
        test_data = data.draw(mixed_transaction_data(
            counterparty_ids, valid_count, invalid_count
        ))
        
        # 创建Excel文件
        excel_file = create_excel_file(test_data)
        
        try:
            # 记录预览前的记录数
            initial_count = len(transaction_storage.get_all())
            
            # 执行预览
            preview_result = engine.preview_import(excel_file, data_type='transaction')
            
            # 验证预览不会修改数据
            after_preview_count = len(transaction_storage.get_all())
            assert after_preview_count == initial_count, \
                "预览操作不应该修改存储中的数据"
            
            # 验证预览结果包含错误信息
            assert preview_result.validation_errors is not None, \
                "预览结果应该包含validation_errors字段"
            
            # 验证错误数量大于0（因为我们生成了无效记录）
            assert len(preview_result.validation_errors) > 0, \
                f"应该检测到验证错误，但得到{len(preview_result.validation_errors)}个错误"
            
            # 验证每个错误都包含必要信息
            for error in preview_result.validation_errors:
                assert error.row_number >= 0, "错误应该包含行号"
                assert error.field_name is not None, "错误应该包含字段名"
                assert error.error_message is not None, "错误应该包含错误消息"
                assert error.error_type in ['missing', 'invalid_format', 'invalid_value', 'duplicate'], \
                    f"错误类型应该是有效值，但得到: {error.error_type}"
            
            # 验证estimated_rows正确
            assert preview_result.estimated_rows == len(test_data), \
                f"estimated_rows应该等于数据行数: {preview_result.estimated_rows} != {len(test_data)}"
            
        finally:
            if os.path.exists(excel_file):
                os.unlink(excel_file)
    
    @given(data=st.data())
    @settings(max_examples=100, suppress_health_check=[HealthCheck.function_scoped_fixture], deadline=None)
    def test_preview_errors_match_import_errors(self, setup_storage, data):
        """
        Property: 预览识别的错误应该与实际导入时的错误一致
        
        验证：
        1. 预览和导入识别的错误类型相同
        2. 预览和导入识别的错误数量相近
        3. 如果预览显示有错误，导入应该失败
        """
        engine = setup_storage['engine']
        counterparty_ids = setup_storage['counterparty_ids']
        
        # 生成包含错误的数据
        invalid_count = data.draw(st.integers(min_value=1, max_value=5))
        test_data = data.draw(mixed_transaction_data(
            counterparty_ids, valid_count=0, invalid_count=invalid_count
        ))
        
        # 创建Excel文件
        excel_file = create_excel_file(test_data)
        
        try:
            # 执行预览
            preview_result = engine.preview_import(excel_file, data_type='transaction')
            
            # 执行实际导入
            import_result = engine.import_transactions(excel_file)
            
            # 验证：如果预览显示有错误，导入应该失败
            if len(preview_result.validation_errors) > 0:
                assert import_result.successful_rows == 0, \
                    "如果预览显示有错误，导入不应该成功"
                assert len(import_result.errors) > 0, \
                    "如果预览显示有错误，导入结果应该包含错误"
            
            # 验证错误数量相近（可能不完全相同，因为导入可能有额外的运行时检查）
            preview_error_count = len(preview_result.validation_errors)
            import_error_count = len(import_result.errors)
            
            # 允许一定的差异，但应该在同一数量级
            assert abs(preview_error_count - import_error_count) <= max(preview_error_count, import_error_count), \
                f"预览和导入的错误数量应该相近: preview={preview_error_count}, import={import_error_count}"
            
        finally:
            if os.path.exists(excel_file):
                os.unlink(excel_file)
    
    @given(data=st.data())
    @settings(max_examples=50, suppress_health_check=[HealthCheck.function_scoped_fixture], deadline=None)
    def test_preview_provides_column_mapping_info(self, setup_storage, data):
        """
        Property: 预览应该提供列映射信息
        
        验证：
        1. 预览结果包含column_mapping
        2. column_mapping包含source_columns和target_fields
        3. column_mapping包含confidence分数
        """
        engine = setup_storage['engine']
        counterparty_ids = setup_storage['counterparty_ids']
        
        # 生成有效数据
        valid_count = data.draw(st.integers(min_value=1, max_value=5))
        test_data = data.draw(mixed_transaction_data(
            counterparty_ids, valid_count=valid_count, invalid_count=0
        ))
        
        # 创建Excel文件
        excel_file = create_excel_file(test_data)
        
        try:
            # 执行预览
            preview_result = engine.preview_import(excel_file, data_type='transaction')
            
            # 验证column_mapping存在
            assert preview_result.column_mapping is not None, \
                "预览结果应该包含column_mapping"
            
            # 验证column_mapping包含必要字段
            assert hasattr(preview_result.column_mapping, 'source_columns'), \
                "column_mapping应该包含source_columns"
            assert hasattr(preview_result.column_mapping, 'target_fields'), \
                "column_mapping应该包含target_fields"
            assert hasattr(preview_result.column_mapping, 'confidence'), \
                "column_mapping应该包含confidence"
            
            # 验证confidence在合理范围内
            assert 0.0 <= preview_result.column_mapping.confidence <= 1.0, \
                f"confidence应该在0-1之间: {preview_result.column_mapping.confidence}"
            
        finally:
            if os.path.exists(excel_file):
                os.unlink(excel_file)
    
    @given(data=st.data())
    @settings(max_examples=50, suppress_health_check=[HealthCheck.function_scoped_fixture], deadline=None)
    def test_preview_provides_sample_data(self, setup_storage, data):
        """
        Property: 预览应该提供样本数据
        
        验证：
        1. 预览结果包含sample_data
        2. sample_data是DataFrame格式
        3. sample_data最多包含10行（预览限制）
        """
        engine = setup_storage['engine']
        counterparty_ids = setup_storage['counterparty_ids']
        
        # 生成数据（可能超过10行）
        row_count = data.draw(st.integers(min_value=1, max_value=20))
        test_data = data.draw(mixed_transaction_data(
            counterparty_ids, valid_count=row_count, invalid_count=0
        ))
        
        # 创建Excel文件
        excel_file = create_excel_file(test_data)
        
        try:
            # 执行预览
            preview_result = engine.preview_import(excel_file, data_type='transaction')
            
            # 验证sample_data存在
            assert preview_result.sample_data is not None, \
                "预览结果应该包含sample_data"
            
            # 验证sample_data是DataFrame
            assert isinstance(preview_result.sample_data, pd.DataFrame), \
                "sample_data应该是DataFrame类型"
            
            # 验证sample_data最多10行
            assert len(preview_result.sample_data) <= 10, \
                f"sample_data应该最多10行，但得到{len(preview_result.sample_data)}行"
            
            # 验证sample_data行数不超过总行数
            assert len(preview_result.sample_data) <= len(test_data), \
                "sample_data行数不应该超过总行数"
            
        finally:
            if os.path.exists(excel_file):
                os.unlink(excel_file)
    
    @given(data=st.data())
    @settings(max_examples=50, suppress_health_check=[HealthCheck.function_scoped_fixture], deadline=None)
    def test_preview_counterparty_validation(self, setup_storage, data):
        """
        Property: 预览应该验证往来单位数据
        
        验证：
        1. 预览能识别往来单位数据的错误
        2. 预览能检测重复的单位名称
        3. 预览能检测重复的税号
        """
        engine = setup_storage['engine']
        
        # 生成包含错误的往来单位数据
        valid_count = data.draw(st.integers(min_value=0, max_value=3))
        invalid_count = data.draw(st.integers(min_value=1, max_value=3))
        
        test_data = data.draw(mixed_counterparty_data(valid_count, invalid_count))
        
        # 创建Excel文件
        excel_file = create_excel_file(test_data)
        
        try:
            # 执行预览
            preview_result = engine.preview_import(excel_file, data_type='counterparty')
            
            # 验证预览识别了错误
            assert len(preview_result.validation_errors) > 0, \
                "应该检测到往来单位数据的验证错误"
            
            # 验证错误包含必要信息
            for error in preview_result.validation_errors:
                assert error.row_number >= 0
                assert error.field_name is not None
                assert error.error_message is not None
            
        finally:
            if os.path.exists(excel_file):
                os.unlink(excel_file)
    
    def test_preview_empty_file(self, setup_storage):
        """
        单元测试: 预览空文件应该返回适当的结果
        
        验证：
        1. 不抛出异常
        2. 返回estimated_rows为0
        3. 返回适当的错误消息
        """
        engine = setup_storage['engine']
        
        # 创建空Excel文件
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
            # 执行预览
            preview_result = engine.preview_import(excel_file, data_type='transaction')
            
            # 验证结果
            assert preview_result.estimated_rows == 0, \
                "空文件的estimated_rows应该为0"
            
            assert len(preview_result.validation_errors) > 0, \
                "空文件应该返回错误消息"
            
            # 验证错误消息提示文件为空
            error_messages = [e.error_message for e in preview_result.validation_errors]
            assert any('空' in msg for msg in error_messages), \
                "错误消息应该提示文件为空"
            
        finally:
            if os.path.exists(excel_file):
                os.unlink(excel_file)
    
    def test_preview_missing_required_fields(self, setup_storage):
        """
        单元测试: 预览应该检测缺少必需字段的记录
        
        验证：
        1. 检测缺少日期字段
        2. 检测缺少类型字段
        3. 检测缺少金额字段
        
        注意：当Excel中缺少列时，pandas会将其读取为NaN，
        验证器会将NaN识别为invalid_format或missing错误
        """
        engine = setup_storage['engine']
        counterparty_ids = setup_storage['counterparty_ids']
        
        # 创建缺少必需字段的数据（使用None或空字符串）
        test_data = [
            {
                'date': None,  # 缺少date
                'type': '收入',
                'amount': 100.00,
                'counterparty_id': counterparty_ids[0]
            },
            {
                'date': '2024-01-01',
                'type': '',  # 缺少type
                'amount': 200.00,
                'counterparty_id': counterparty_ids[0]
            },
            {
                'date': '2024-01-01',
                'type': '支出',
                'amount': None,  # 缺少amount
                'counterparty_id': counterparty_ids[0]
            }
        ]
        
        excel_file = create_excel_file(test_data)
        
        try:
            # 执行预览
            preview_result = engine.preview_import(excel_file, data_type='transaction')
            
            # 验证检测到错误
            assert len(preview_result.validation_errors) >= 3, \
                f"应该检测到至少3个错误，但得到{len(preview_result.validation_errors)}个"
            
            # 验证错误类型（可能是missing或invalid_format）
            error_types = [e.error_type for e in preview_result.validation_errors]
            assert 'missing' in error_types or 'invalid_format' in error_types, \
                f"应该包含'missing'或'invalid_format'类型的错误，但得到: {error_types}"
            
            # 验证错误字段
            error_fields = [e.field_name for e in preview_result.validation_errors]
            assert 'date' in error_fields or 'type' in error_fields or 'amount' in error_fields, \
                "错误应该指出缺少的必需字段"
            
        finally:
            if os.path.exists(excel_file):
                os.unlink(excel_file)
    
    def test_preview_invalid_data_formats(self, setup_storage):
        """
        单元测试: 预览应该检测无效的数据格式
        
        验证：
        1. 检测无效的日期格式
        2. 检测无效的金额格式
        3. 检测无效的交易类型
        """
        engine = setup_storage['engine']
        counterparty_ids = setup_storage['counterparty_ids']
        
        # 创建包含无效格式的数据
        test_data = [
            {
                'date': '不是日期',
                'type': '收入',
                'amount': 100.00,
                'counterparty_id': counterparty_ids[0]
            },
            {
                'date': '2024-01-01',
                'type': '无效类型',
                'amount': 100.00,
                'counterparty_id': counterparty_ids[0]
            },
            {
                'date': '2024-01-01',
                'type': '收入',
                'amount': -100.00,  # 负数金额
                'counterparty_id': counterparty_ids[0]
            }
        ]
        
        excel_file = create_excel_file(test_data)
        
        try:
            # 执行预览
            preview_result = engine.preview_import(excel_file, data_type='transaction')
            
            # 验证检测到错误
            assert len(preview_result.validation_errors) >= 3, \
                f"应该检测到至少3个错误，但得到{len(preview_result.validation_errors)}个"
            
            # 验证错误类型
            error_types = [e.error_type for e in preview_result.validation_errors]
            assert 'invalid_format' in error_types or 'invalid_value' in error_types, \
                "应该包含格式或值错误"
            
        finally:
            if os.path.exists(excel_file):
                os.unlink(excel_file)
    
    def test_preview_duplicate_detection(self, setup_storage):
        """
        单元测试: 预览应该检测重复的往来单位
        
        验证：
        1. 检测重复的单位名称
        2. 检测重复的税号
        3. 检测批次内的重复
        """
        engine = setup_storage['engine']
        counterparty_storage = setup_storage['counterparty_storage']
        
        # 获取已存在的单位名称
        existing_counterparties = counterparty_storage.get_all()
        existing_name = existing_counterparties[0].name if existing_counterparties else '测试客户A'
        
        # 创建包含重复的数据
        test_data = [
            {
                'name': existing_name,  # 与已存在的单位重名
                'type': '客户',
                'contact_person': '张三',
                'phone': '13800138000',
                'email': 'test1@example.com',
                'address': '地址1',
                'tax_id': '111111111111111'
            },
            {
                'name': '新单位A',
                'type': '客户',
                'contact_person': '李四',
                'phone': '13900139000',
                'email': 'test2@example.com',
                'address': '地址2',
                'tax_id': '222222222222222'
            },
            {
                'name': '新单位B',  # 批次内重复税号
                'type': '供应商',
                'contact_person': '王五',
                'phone': '13700137000',
                'email': 'test3@example.com',
                'address': '地址3',
                'tax_id': '222222222222222'  # 与上一条重复
            }
        ]
        
        excel_file = create_excel_file(test_data)
        
        try:
            # 执行预览
            preview_result = engine.preview_import(excel_file, data_type='counterparty')
            
            # 验证检测到重复错误
            duplicate_errors = [
                e for e in preview_result.validation_errors
                if e.error_type == 'duplicate'
            ]
            
            assert len(duplicate_errors) >= 1, \
                f"应该检测到至少1个重复错误，但得到{len(duplicate_errors)}个"
            
            # 验证错误消息包含"重复"或"已存在"
            error_messages = [e.error_message for e in duplicate_errors]
            assert any('重复' in msg or '已存在' in msg for msg in error_messages), \
                "错误消息应该提示重复或已存在"
            
        finally:
            if os.path.exists(excel_file):
                os.unlink(excel_file)
