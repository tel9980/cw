"""
Property-based tests for ImportEngine - Counterparty Import

Feature: small-accountant-practical-enhancement
Property 16: Counterparty import completeness
Validates: Requirements 4.3
"""

import pytest
import os
import tempfile
from datetime import datetime
from hypothesis import given, strategies as st, settings, assume
from hypothesis import HealthCheck
import pandas as pd

from small_accountant_v16.import_engine.import_engine import ImportEngine
from small_accountant_v16.storage.transaction_storage import TransactionStorage
from small_accountant_v16.storage.counterparty_storage import CounterpartyStorage
from small_accountant_v16.storage.import_history import ImportHistory
from small_accountant_v16.models.core_models import CounterpartyType


# Hypothesis strategies for generating test data
@st.composite
def valid_counterparty_type(draw):
    """生成有效的往来单位类型"""
    return draw(st.sampled_from(['客户', '供应商', 'customer', 'supplier']))


@st.composite
def valid_phone_number(draw):
    """生成有效的电话号码"""
    # 生成中国手机号或固定电话
    phone_type = draw(st.integers(min_value=0, max_value=1))
    if phone_type == 0:
        # 手机号: 13x, 14x, 15x, 16x, 17x, 18x, 19x
        prefix = draw(st.sampled_from(['13', '14', '15', '16', '17', '18', '19']))
        suffix = draw(st.integers(min_value=0, max_value=99999999))
        return f"{prefix}{suffix:08d}"
    else:
        # 固定电话: 区号-号码
        area_code = draw(st.integers(min_value=10, max_value=999))
        number = draw(st.integers(min_value=1000000, max_value=99999999))
        return f"{area_code:03d}-{number}"


@st.composite
def valid_email(draw):
    """生成有效的邮箱地址"""
    # 生成简单的邮箱地址
    username_length = draw(st.integers(min_value=3, max_value=15))
    username = ''.join(draw(st.lists(
        st.sampled_from('abcdefghijklmnopqrstuvwxyz0123456789'),
        min_size=username_length,
        max_size=username_length
    )))
    domain = draw(st.sampled_from(['example.com', 'test.com', 'company.com', 'mail.com']))
    return f"{username}@{domain}"


@st.composite
def valid_tax_id(draw):
    """生成有效的税号"""
    # 生成15位或18位数字税号
    length = draw(st.sampled_from([15, 18]))
    # 确保第一位不是0（避免被解析为八进制）
    first_digit = draw(st.integers(min_value=1, max_value=9))
    rest_digits = ''.join(str(draw(st.integers(min_value=0, max_value=9))) for _ in range(length - 1))
    return str(first_digit) + rest_digits


@st.composite
def safe_chinese_text(draw, min_size=1, max_size=50):
    """生成安全的中文文本"""
    # 使用常见汉字范围
    text_length = draw(st.integers(min_value=min_size, max_value=max_size))
    chars = []
    for _ in range(text_length):
        char = draw(st.sampled_from([
            '公', '司', '有', '限', '责', '任', '股', '份', '集', '团',
            '科', '技', '贸', '易', '商', '业', '工', '厂', '店', '行',
            '中', '国', '北', '京', '上', '海', '广', '州', '深', '圳',
            '一', '二', '三', '四', '五', '六', '七', '八', '九', '十',
            'A', 'B', 'C', 'D', 'E', 'F', 'G', 'H', 'I', 'J'
        ]))
        chars.append(char)
    return ''.join(chars)


@st.composite
def valid_counterparty_record(draw):
    """生成有效的往来单位记录"""
    return {
        'name': draw(safe_chinese_text(min_size=2, max_size=30)),
        'type': draw(valid_counterparty_type()),
        'contact_person': draw(safe_chinese_text(min_size=2, max_size=10)),
        'phone': draw(valid_phone_number()),
        'email': draw(valid_email()),
        'address': draw(safe_chinese_text(min_size=5, max_size=50)),
        'tax_id': draw(valid_tax_id())
    }


@st.composite
def counterparty_excel_data(draw, min_rows=1, max_rows=50):
    """生成往来单位Excel数据"""
    num_rows = draw(st.integers(min_value=min_rows, max_value=max_rows))
    
    records = []
    used_names = set()
    used_tax_ids = set()
    
    for _ in range(num_rows):
        # 生成唯一的记录
        max_attempts = 10
        for attempt in range(max_attempts):
            record = draw(valid_counterparty_record())
            # 确保名称和税号唯一
            if record['name'] not in used_names and record['tax_id'] not in used_tax_ids:
                used_names.add(record['name'])
                used_tax_ids.add(record['tax_id'])
                records.append(record)
                break
        else:
            # 如果无法生成唯一记录，使用后缀
            record = draw(valid_counterparty_record())
            record['name'] = f"{record['name']}{len(records)}"
            record['tax_id'] = f"{record['tax_id']}{len(records)}"
            records.append(record)
    
    return records


def create_counterparty_excel_file(data, column_names=None):
    """创建往来单位临时Excel文件"""
    if column_names is None:
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


class TestCounterpartyImportProperties:
    """Property-based tests for counterparty import
    
    **Property 16: Counterparty import completeness**
    For any valid Excel file containing counterparty data (customers, suppliers),
    all valid rows should be successfully imported as Counterparty records.
    **Validates: Requirements 4.3**
    """
    
    @pytest.fixture
    def setup_storage(self, tmp_path):
        """设置存储层 - 每个测试都使用独立的临时目录"""
        import uuid
        test_dir = tmp_path / str(uuid.uuid4())
        test_dir.mkdir()
        
        transaction_storage = TransactionStorage(str(test_dir / 'transactions.json'))
        counterparty_storage = CounterpartyStorage(str(test_dir / 'counterparties.json'))
        import_history = ImportHistory(str(test_dir / 'import_history.json'))
        
        engine = ImportEngine(
            transaction_storage,
            counterparty_storage,
            import_history
        )
        
        # 清空存储，确保每个测试都从空白状态开始
        for cp in counterparty_storage.get_all():
            counterparty_storage.delete(cp.id)
        
        return {
            'engine': engine,
            'transaction_storage': transaction_storage,
            'counterparty_storage': counterparty_storage,
            'import_history': import_history
        }
    
    @given(data=st.data())
    @settings(max_examples=100, suppress_health_check=[HealthCheck.function_scoped_fixture], deadline=None)
    def test_all_valid_counterparties_are_imported(self, setup_storage, data):
        """
        Property: 所有有效的往来单位都应该被成功导入
        
        验证：
        1. 导入结果中successful_rows等于输入的有效行数
        2. 导入后存储中的记录数等于导入的记录数
        3. 导入的记录可以被检索
        """
        engine = setup_storage['engine']
        counterparty_storage = setup_storage['counterparty_storage']
        
        # 清空存储，确保每次测试都从空白状态开始
        for cp in counterparty_storage.get_all():
            counterparty_storage.delete(cp.id)
        
        # 生成测试数据
        excel_data = data.draw(counterparty_excel_data(min_rows=1, max_rows=20))
        
        # 创建Excel文件
        excel_file = create_counterparty_excel_file(excel_data)
        
        try:
            # 记录导入前的记录数
            initial_count = len(counterparty_storage.get_all())
            
            # 执行导入
            result = engine.import_counterparties(excel_file)
            
            # 验证导入结果
            assert result.total_rows == len(excel_data), \
                f"总行数应该等于输入数据行数: {result.total_rows} != {len(excel_data)}"
            
            assert result.successful_rows == len(excel_data), \
                f"成功导入行数应该等于输入数据行数: {result.successful_rows} != {len(excel_data)}, errors: {result.errors}"
            
            assert result.failed_rows == 0, \
                f"失败行数应该为0: {result.failed_rows}"
            
            assert len(result.errors) == 0, \
                f"不应该有错误: {result.errors}"
            
            # 验证存储中的记录数
            final_count = len(counterparty_storage.get_all())
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
    def test_imported_counterparties_match_source_data(self, setup_storage, data):
        """
        Property: 导入的往来单位应该与源数据匹配
        
        验证：
        1. 导入的记录数量正确
        2. 导入的记录字段值与源数据一致
        3. 名称、类型等关键字段正确转换
        """
        engine = setup_storage['engine']
        counterparty_storage = setup_storage['counterparty_storage']
        
        # 清空存储
        for cp in counterparty_storage.get_all():
            counterparty_storage.delete(cp.id)
        
        # 生成测试数据
        excel_data = data.draw(counterparty_excel_data(min_rows=1, max_rows=10))
        
        # 创建Excel文件
        excel_file = create_counterparty_excel_file(excel_data)
        
        try:
            # 执行导入
            result = engine.import_counterparties(excel_file)
            
            # 获取所有导入的记录
            all_counterparties = counterparty_storage.get_all()
            
            # 验证导入的记录数量
            assert len(all_counterparties) >= len(excel_data), \
                "导入后的记录数应该至少等于源数据行数"
            
            # 验证名称都被导入
            imported_names = [cp.name for cp in all_counterparties[-len(excel_data):]]
            source_names = [record['name'] for record in excel_data]
            
            for source_name in source_names:
                assert source_name in imported_names, \
                    f"源数据中的名称 {source_name} 应该被导入"
            
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
        3. 变体列名可以导入
        """
        engine = setup_storage['engine']
        counterparty_storage = setup_storage['counterparty_storage']
        
        # 清空存储
        for cp in counterparty_storage.get_all():
            counterparty_storage.delete(cp.id)
        
        # 生成测试数据
        excel_data = data.draw(counterparty_excel_data(min_rows=1, max_rows=10))
        
        # 随机选择列名格式
        column_format = data.draw(st.integers(min_value=0, max_value=2))
        
        if column_format == 0:
            # 中文列名
            column_names = {
                'name': '名称',
                'type': '类型',
                'contact_person': '联系人',
                'phone': '电话',
                'email': '邮箱',
                'address': '地址',
                'tax_id': '税号'
            }
        elif column_format == 1:
            # 英文列名
            column_names = {
                'name': 'name',
                'type': 'type',
                'contact_person': 'contact_person',
                'phone': 'phone',
                'email': 'email',
                'address': 'address',
                'tax_id': 'tax_id'
            }
        else:
            # 变体列名
            column_names = {
                'name': '单位名称',
                'type': '单位类型',
                'contact_person': '联系人姓名',
                'phone': '联系电话',
                'email': '电子邮箱',
                'address': '单位地址',
                'tax_id': '纳税人识别号'
            }
        
        # 创建Excel文件
        excel_file = create_counterparty_excel_file(excel_data, column_names)
        
        try:
            # 执行导入
            result = engine.import_counterparties(excel_file)
            
            # 验证导入成功
            assert result.successful_rows == len(excel_data), \
                f"使用列名格式{column_format}时，应该成功导入所有记录，errors: {result.errors}"
            
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
        counterparty_storage = setup_storage['counterparty_storage']
        
        # 清空存储
        for cp in counterparty_storage.get_all():
            counterparty_storage.delete(cp.id)
        
        # 生成测试数据
        excel_data = data.draw(counterparty_excel_data(min_rows=1, max_rows=10))
        
        # 创建Excel文件
        excel_file = create_counterparty_excel_file(excel_data)
        
        try:
            # 执行导入
            result = engine.import_counterparties(excel_file)
            
            # 验证import_id
            assert result.import_id is not None, "import_id不应该为空"
            assert len(result.import_id) > 0, "import_id应该是非空字符串"
            
            # 只有成功导入时才会记录历史
            if result.successful_rows > 0:
                # 验证可以查询导入历史
                import_record = import_history.get_import_by_id(result.import_id)
                assert import_record is not None, "应该能通过import_id查询到导入记录"
                
                # 验证导入历史包含正确信息
                assert import_record['import_type'] == 'counterparty'
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
            result = engine.import_counterparties(excel_file)
            
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
        counterparty_storage = setup_storage['counterparty_storage']
        
        # 清空存储
        for cp in counterparty_storage.get_all():
            counterparty_storage.delete(cp.id)
        
        # 生成测试数据
        excel_data = data.draw(counterparty_excel_data(min_rows=1, max_rows=5))
        
        # 创建Excel文件
        excel_file = create_counterparty_excel_file(excel_data)
        
        try:
            from datetime import timedelta
            
            # 记录导入前的时间
            before_import = datetime.now()
            
            # 执行导入
            result = engine.import_counterparties(excel_file)
            
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
    
    @given(data=st.data())
    @settings(max_examples=50, suppress_health_check=[HealthCheck.function_scoped_fixture], deadline=None)
    def test_both_customer_and_supplier_types_imported(self, setup_storage, data):
        """
        Property: 客户和供应商两种类型都应该能被正确导入
        
        验证：
        1. 客户类型可以导入
        2. 供应商类型可以导入
        3. 类型字段正确转换
        """
        engine = setup_storage['engine']
        counterparty_storage = setup_storage['counterparty_storage']
        
        # 清空存储
        for cp in counterparty_storage.get_all():
            counterparty_storage.delete(cp.id)
        
        # 生成包含两种类型的测试数据
        num_records = data.draw(st.integers(min_value=2, max_value=10))
        excel_data = []
        
        for i in range(num_records):
            record = data.draw(valid_counterparty_record())
            # 确保唯一性
            record['name'] = f"{record['name']}{i}"
            record['tax_id'] = f"{record['tax_id']}{i}"
            # 交替设置类型
            record['type'] = '客户' if i % 2 == 0 else '供应商'
            excel_data.append(record)
        
        # 创建Excel文件
        excel_file = create_counterparty_excel_file(excel_data)
        
        try:
            # 执行导入
            result = engine.import_counterparties(excel_file)
            
            # 验证导入成功
            assert result.successful_rows == len(excel_data), \
                f"应该成功导入所有记录，errors: {result.errors}"
            
            # 验证导入的记录类型
            counterparties = counterparty_storage.get_all()
            types = [cp.type for cp in counterparties[-len(excel_data):]]
            
            assert CounterpartyType.CUSTOMER in types, "应该包含客户类型"
            assert CounterpartyType.SUPPLIER in types, "应该包含供应商类型"
            
        finally:
            if os.path.exists(excel_file):
                os.unlink(excel_file)
    
    def test_standard_counterparty_fields_are_imported_correctly(self, setup_storage):
        """
        单元测试: 标准往来单位字段应该被正确导入
        
        验证所有必需和可选字段都能正确导入
        """
        engine = setup_storage['engine']
        counterparty_storage = setup_storage['counterparty_storage']
        
        # 创建包含完整字段的测试数据
        test_data = [
            {
                'name': '测试客户公司',
                'type': '客户',
                'contact_person': '张三',
                'phone': '13800138000',
                'email': 'zhangsan@test.com',
                'address': '北京市朝阳区测试路123号',
                'tax_id': '123456789012345'
            },
            {
                'name': '测试供应商公司',
                'type': '供应商',
                'contact_person': '李四',
                'phone': '010-12345678',
                'email': 'lisi@supplier.com',
                'address': '上海市浦东新区供应商大道456号',
                'tax_id': '987654321098765'
            }
        ]
        
        excel_file = create_counterparty_excel_file(test_data)
        
        try:
            result = engine.import_counterparties(excel_file)
            
            assert result.successful_rows == 2, "应该成功导入2条记录"
            
            # 验证导入的记录字段
            counterparties = counterparty_storage.get_all()
            
            # 验证第一条记录（客户）
            customer = next((cp for cp in counterparties if cp.name == '测试客户公司'), None)
            assert customer is not None, "应该找到客户记录"
            assert customer.type == CounterpartyType.CUSTOMER
            assert customer.contact_person == '张三'
            assert customer.phone == '13800138000'
            assert customer.email == 'zhangsan@test.com'
            assert customer.tax_id == '123456789012345'
            
            # 验证第二条记录（供应商）
            supplier = next((cp for cp in counterparties if cp.name == '测试供应商公司'), None)
            assert supplier is not None, "应该找到供应商记录"
            assert supplier.type == CounterpartyType.SUPPLIER
            assert supplier.contact_person == '李四'
            assert supplier.phone == '010-12345678'
            assert supplier.email == 'lisi@supplier.com'
            assert supplier.tax_id == '987654321098765'
            
        finally:
            if os.path.exists(excel_file):
                os.unlink(excel_file)
    
    def test_minimal_required_fields_import(self, setup_storage):
        """
        单元测试: 只包含必需字段的记录应该能成功导入
        
        验证只有名称和类型的记录可以导入
        """
        engine = setup_storage['engine']
        counterparty_storage = setup_storage['counterparty_storage']
        
        # 创建只包含必需字段的测试数据（使用None而不是空字符串）
        test_data = [
            {
                'name': '最小客户',
                'type': '客户',
                'contact_person': None,
                'phone': None,
                'email': None,
                'address': None,
                'tax_id': None
            }
        ]
        
        # 创建DataFrame并处理None值
        df = pd.DataFrame(test_data)
        # 只保留必需字段
        df = df[['name', 'type']]
        
        # 创建临时文件
        temp_file = tempfile.NamedTemporaryFile(
            mode='w',
            suffix='.xlsx',
            delete=False
        )
        temp_file.close()
        
        # 写入Excel
        df.to_excel(temp_file.name, index=False)
        excel_file = temp_file.name
        
        try:
            result = engine.import_counterparties(excel_file)
            
            assert result.successful_rows == 1, f"应该成功导入1条记录，但是: {result.errors}"
            
            # 验证导入的记录
            counterparties = counterparty_storage.get_all()
            minimal_cp = next((cp for cp in counterparties if cp.name == '最小客户'), None)
            assert minimal_cp is not None, "应该找到最小客户记录"
            assert minimal_cp.type == CounterpartyType.CUSTOMER
            
        finally:
            if os.path.exists(excel_file):
                os.unlink(excel_file)
