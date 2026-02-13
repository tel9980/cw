"""
Property-based tests for ExcelColumnRecognizer

Feature: small-accountant-practical-enhancement
Property 14: Column recognition accuracy
Validates: Requirements 4.1
"""

import pytest
from hypothesis import given, strategies as st, settings, assume, HealthCheck
from small_accountant_v16.import_engine.column_recognizer import (
    ExcelColumnRecognizer,
    ColumnMapping,
)


# Hypothesis strategies for generating column names
@st.composite
def transaction_column_names(draw):
    """生成交易记录相关的列名变体"""
    # 定义各字段的可能列名
    date_variants = ['日期', '时间', '交易日期', '发生日期', '业务日期', 'date', 'Date', 'DATE', 'time']
    type_variants = ['类型', '交易类型', '业务类型', '收支类型', 'type', 'Type', 'TYPE']
    amount_variants = ['金额', '交易金额', '发生额', '数额', 'amount', 'Amount', 'AMOUNT', 'money']
    counterparty_variants = ['往来单位', '客户', '供应商', '对方', 'counterparty', 'customer', 'supplier']
    description_variants = ['描述', '说明', '备注', '摘要', 'description', 'note', 'memo']
    category_variants = ['分类', '类别', '科目', 'category', 'class']
    status_variants = ['状态', 'status', 'state']
    
    # 随机选择是否包含每个字段
    columns = []
    
    # 必需字段：date, type, amount
    if draw(st.booleans()):
        columns.append(draw(st.sampled_from(date_variants)))
    if draw(st.booleans()):
        columns.append(draw(st.sampled_from(type_variants)))
    if draw(st.booleans()):
        columns.append(draw(st.sampled_from(amount_variants)))
    
    # 可选字段
    if draw(st.booleans()):
        columns.append(draw(st.sampled_from(counterparty_variants)))
    if draw(st.booleans()):
        columns.append(draw(st.sampled_from(description_variants)))
    if draw(st.booleans()):
        columns.append(draw(st.sampled_from(category_variants)))
    if draw(st.booleans()):
        columns.append(draw(st.sampled_from(status_variants)))
    
    # 添加一些随机的无关列
    num_random = draw(st.integers(min_value=0, max_value=3))
    for _ in range(num_random):
        columns.append(draw(st.text(min_size=1, max_size=20)))
    
    # 确保至少有一列
    if not columns:
        columns.append(draw(st.sampled_from(date_variants)))
    
    return columns


@st.composite
def counterparty_column_names(draw):
    """生成往来单位相关的列名变体"""
    name_variants = ['名称', '单位名称', '公司名称', '客户名称', 'name', 'Name', 'company']
    type_variants = ['类型', '单位类型', '往来类型', 'type', 'Type']
    contact_variants = ['联系人', '负责人', '经办人', 'contact', 'contact_person']
    phone_variants = ['电话', '联系电话', '手机', 'phone', 'tel', 'mobile']
    email_variants = ['邮箱', '电子邮箱', 'email', 'e-mail']
    address_variants = ['地址', '联系地址', '公司地址', 'address', 'addr']
    tax_id_variants = ['税号', '纳税人识别号', '统一社会信用代码', 'tax_id', 'tax_number']
    
    columns = []
    
    # 必需字段：name, type
    if draw(st.booleans()):
        columns.append(draw(st.sampled_from(name_variants)))
    if draw(st.booleans()):
        columns.append(draw(st.sampled_from(type_variants)))
    
    # 可选字段
    if draw(st.booleans()):
        columns.append(draw(st.sampled_from(contact_variants)))
    if draw(st.booleans()):
        columns.append(draw(st.sampled_from(phone_variants)))
    if draw(st.booleans()):
        columns.append(draw(st.sampled_from(email_variants)))
    if draw(st.booleans()):
        columns.append(draw(st.sampled_from(address_variants)))
    if draw(st.booleans()):
        columns.append(draw(st.sampled_from(tax_id_variants)))
    
    # 添加一些随机的无关列
    num_random = draw(st.integers(min_value=0, max_value=3))
    for _ in range(num_random):
        columns.append(draw(st.text(min_size=1, max_size=20)))
    
    # 确保至少有一列
    if not columns:
        columns.append(draw(st.sampled_from(name_variants)))
    
    return columns


class TestColumnRecognizerProperties:
    """Property-based tests for column recognizer
    
    **Property 14: Column recognition accuracy**
    For any Excel file with common column naming patterns, the system should 
    correctly identify and map columns to target fields with reasonable confidence.
    **Validates: Requirements 4.1**
    """
    
    @given(column_names=transaction_column_names())
    @settings(max_examples=100, suppress_health_check=[HealthCheck.too_slow])
    def test_transaction_column_recognition_returns_valid_mapping(self, column_names):
        """
        Property: 对于任何交易记录列名列表，识别器应返回有效的列映射结果
        
        验证：
        1. 返回的ColumnMapping对象结构完整
        2. source_columns与输入一致
        3. confidence在0-1之间
        4. 所有映射的列都存在于输入列名中
        """
        recognizer = ExcelColumnRecognizer()
        result = recognizer.recognize_columns(column_names, data_type='transaction')
        
        # 验证返回类型
        assert isinstance(result, ColumnMapping)
        
        # 验证source_columns与输入一致
        assert set(result.source_columns) == set(column_names)
        
        # 验证置信度在有效范围内
        assert 0.0 <= result.confidence <= 1.0
        
        # 验证所有映射的列都存在于输入中
        for field, column in result.target_fields.items():
            assert column in column_names, f"映射的列 {column} 不在输入列名中"
        
        # 验证未映射列都存在于输入中
        for column in result.unmapped_columns:
            assert column in column_names, f"未映射列 {column} 不在输入列名中"
        
        # 验证没有重复映射（一个列不能映射到多个字段）
        mapped_columns = list(result.target_fields.values())
        assert len(mapped_columns) == len(set(mapped_columns)), "存在重复映射的列"
    
    @given(column_names=counterparty_column_names())
    @settings(max_examples=100)
    def test_counterparty_column_recognition_returns_valid_mapping(self, column_names):
        """
        Property: 对于任何往来单位列名列表，识别器应返回有效的列映射结果
        
        验证：
        1. 返回的ColumnMapping对象结构完整
        2. source_columns与输入一致
        3. confidence在0-1之间
        4. 所有映射的列都存在于输入列名中
        """
        recognizer = ExcelColumnRecognizer()
        result = recognizer.recognize_columns(column_names, data_type='counterparty')
        
        # 验证返回类型
        assert isinstance(result, ColumnMapping)
        
        # 验证source_columns与输入一致
        assert set(result.source_columns) == set(column_names)
        
        # 验证置信度在有效范围内
        assert 0.0 <= result.confidence <= 1.0
        
        # 验证所有映射的列都存在于输入中
        for field, column in result.target_fields.items():
            assert column in column_names
        
        # 验证未映射列都存在于输入中
        for column in result.unmapped_columns:
            assert column in column_names
        
        # 验证没有重复映射
        mapped_columns = list(result.target_fields.values())
        assert len(mapped_columns) == len(set(mapped_columns))
    
    @given(column_names=transaction_column_names())
    @settings(max_examples=100)
    def test_recognized_fields_match_known_patterns(self, column_names):
        """
        Property: 识别出的字段应该匹配已知的模式
        
        验证：
        1. 识别出的字段名应该是系统定义的有效字段
        2. 对于标准列名（如"日期"、"金额"），应该能正确识别
        """
        recognizer = ExcelColumnRecognizer()
        result = recognizer.recognize_columns(column_names, data_type='transaction')
        
        # 验证所有识别出的字段都是有效的交易记录字段
        valid_fields = set(recognizer.TRANSACTION_FIELD_PATTERNS.keys())
        for field in result.target_fields.keys():
            assert field in valid_fields, f"识别出的字段 {field} 不是有效的交易记录字段"
        
        # 如果输入包含标准列名，应该能识别出来
        standard_mappings = {
            '日期': 'date',
            '金额': 'amount',
            '类型': 'type',
            '往来单位': 'counterparty_id',
            '描述': 'description',
        }
        
        for column in column_names:
            if column in standard_mappings:
                expected_field = standard_mappings[column]
                assert expected_field in result.target_fields, \
                    f"标准列名 {column} 应该被识别为 {expected_field}"
    
    @given(column_names=transaction_column_names())
    @settings(max_examples=100)
    def test_missing_required_fields_are_identified(self, column_names):
        """
        Property: 缺失的必需字段应该被正确识别
        
        验证：
        1. 如果必需字段（date, type, amount）未被识别，应该出现在missing_required_fields中
        2. 如果必需字段被识别，不应该出现在missing_required_fields中
        """
        recognizer = ExcelColumnRecognizer()
        result = recognizer.recognize_columns(column_names, data_type='transaction')
        
        required_fields = {'date', 'type', 'amount'}
        
        for field in required_fields:
            if field in result.target_fields:
                # 如果字段被识别，不应该在缺失列表中
                assert field not in result.missing_required_fields, \
                    f"字段 {field} 已被识别，不应该在缺失列表中"
            else:
                # 如果字段未被识别，应该在缺失列表中
                assert field in result.missing_required_fields, \
                    f"字段 {field} 未被识别，应该在缺失列表中"
    
    @given(column_names=transaction_column_names())
    @settings(max_examples=100)
    def test_mapped_and_unmapped_columns_are_disjoint(self, column_names):
        """
        Property: 已映射列和未映射列应该是互斥的
        
        验证：
        1. 已映射列和未映射列的交集为空
        2. 已映射列和未映射列的并集等于所有输入列
        """
        recognizer = ExcelColumnRecognizer()
        result = recognizer.recognize_columns(column_names, data_type='transaction')
        
        mapped_columns = set(result.target_fields.values())
        unmapped_columns = set(result.unmapped_columns)
        all_columns = set(column_names)
        
        # 已映射和未映射应该互斥
        assert mapped_columns.isdisjoint(unmapped_columns), \
            "已映射列和未映射列不应该有交集"
        
        # 并集应该等于所有列
        assert mapped_columns.union(unmapped_columns) == all_columns, \
            "已映射列和未映射列的并集应该等于所有输入列"
    
    @given(column_names=transaction_column_names())
    @settings(max_examples=100)
    def test_confidence_reflects_recognition_quality(self, column_names):
        """
        Property: 置信度应该反映识别质量
        
        验证：
        1. 如果所有必需字段都被识别，置信度应该较高（>0.5）
        2. 如果没有字段被识别，置信度应该为0
        3. 如果部分字段被识别，置信度应该在0-1之间
        """
        recognizer = ExcelColumnRecognizer()
        result = recognizer.recognize_columns(column_names, data_type='transaction')
        
        if len(result.target_fields) == 0:
            # 没有字段被识别，置信度应该为0
            assert result.confidence == 0.0, "没有字段被识别时，置信度应该为0"
        elif len(result.missing_required_fields) == 0:
            # 所有必需字段都被识别，置信度应该较高
            assert result.confidence > 0.5, \
                "所有必需字段都被识别时，置信度应该大于0.5"
        else:
            # 部分字段被识别，置信度应该在合理范围内
            assert 0.0 <= result.confidence <= 1.0
    
    @given(
        column_names=transaction_column_names(),
        data_type=st.sampled_from(['transaction', 'counterparty'])
    )
    @settings(max_examples=100)
    def test_suggest_mapping_returns_valid_suggestions(self, column_names, data_type):
        """
        Property: suggest_mapping应该返回有效的建议
        
        验证：
        1. 返回的建议字典的键是有效的字段名
        2. 建议的列名都存在于输入列名中
        3. 每个字段最多建议3个候选列
        """
        recognizer = ExcelColumnRecognizer()
        suggestions = recognizer.suggest_mapping(column_names, data_type=data_type)
        
        # 确定有效字段集合
        if data_type == 'transaction':
            valid_fields = set(recognizer.TRANSACTION_FIELD_PATTERNS.keys())
        else:
            valid_fields = set(recognizer.COUNTERPARTY_FIELD_PATTERNS.keys())
        
        # 验证建议字典的键是有效字段
        for field in suggestions.keys():
            assert field in valid_fields, f"建议的字段 {field} 不是有效字段"
        
        # 验证建议的列名都存在于输入中
        for field, candidates in suggestions.items():
            assert len(candidates) <= 3, f"字段 {field} 的候选列超过3个"
            for candidate in candidates:
                assert candidate in column_names, \
                    f"建议的列 {candidate} 不在输入列名中"
    
    @given(column_names=st.lists(
        st.text(min_size=1, max_size=20),
        min_size=1,
        max_size=10,
        unique=True
    ))
    @settings(max_examples=100)
    def test_handles_arbitrary_column_names_gracefully(self, column_names):
        """
        Property: 对于任意列名，识别器应该优雅处理而不崩溃
        
        验证：
        1. 不应该抛出异常
        2. 返回有效的ColumnMapping对象
        3. 即使无法识别任何字段，也应该返回合理的结果
        """
        recognizer = ExcelColumnRecognizer()
        
        # 应该不抛出异常
        try:
            result = recognizer.recognize_columns(column_names, data_type='transaction')
            
            # 验证返回有效对象
            assert isinstance(result, ColumnMapping)
            assert result.source_columns == column_names
            assert 0.0 <= result.confidence <= 1.0
            
        except Exception as e:
            pytest.fail(f"识别器在处理任意列名时抛出异常: {e}")
    
    def test_standard_chinese_columns_are_recognized_with_high_confidence(self):
        """
        Property: 标准中文列名应该被高置信度识别
        
        这是一个具体的单元测试，验证常见的中文列名能被正确识别
        """
        recognizer = ExcelColumnRecognizer()
        
        # 标准中文交易记录列名
        standard_columns = ['日期', '类型', '金额', '往来单位', '描述', '分类']
        result = recognizer.recognize_columns(standard_columns, data_type='transaction')
        
        # 应该识别出所有必需字段
        assert 'date' in result.target_fields
        assert 'type' in result.target_fields
        assert 'amount' in result.target_fields
        
        # 置信度应该很高
        assert result.confidence > 0.8, f"标准列名的置信度应该>0.8，实际为{result.confidence}"
        
        # 不应该有缺失的必需字段
        assert len(result.missing_required_fields) == 0
    
    def test_standard_english_columns_are_recognized_with_high_confidence(self):
        """
        Property: 标准英文列名应该被高置信度识别
        """
        recognizer = ExcelColumnRecognizer()
        
        # 标准英文交易记录列名
        standard_columns = ['date', 'type', 'amount', 'counterparty', 'description', 'category']
        result = recognizer.recognize_columns(standard_columns, data_type='transaction')
        
        # 应该识别出所有必需字段
        assert 'date' in result.target_fields
        assert 'type' in result.target_fields
        assert 'amount' in result.target_fields
        
        # 置信度应该很高
        assert result.confidence > 0.8
        
        # 不应该有缺失的必需字段
        assert len(result.missing_required_fields) == 0
    
    def test_mixed_case_columns_are_recognized(self):
        """
        Property: 大小写混合的列名应该被正确识别
        """
        recognizer = ExcelColumnRecognizer()
        
        # 大小写混合的列名
        mixed_columns = ['Date', 'TYPE', 'Amount', 'Counterparty', 'Description']
        result = recognizer.recognize_columns(mixed_columns, data_type='transaction')
        
        # 应该识别出必需字段
        assert 'date' in result.target_fields
        assert 'type' in result.target_fields
        assert 'amount' in result.target_fields
    
    def test_columns_with_spaces_are_handled(self):
        """
        Property: 包含空格的列名应该被正确处理
        """
        recognizer = ExcelColumnRecognizer()
        
        # 包含空格的列名
        spaced_columns = [' 日期 ', ' 类型 ', ' 金额 ', ' 往来单位 ']
        result = recognizer.recognize_columns(spaced_columns, data_type='transaction')
        
        # 应该能识别出字段（因为会进行标准化处理）
        assert len(result.target_fields) > 0
