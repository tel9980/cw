"""
导入数据验证器模块

验证导入的交易记录和往来单位数据。
"""

from typing import List, Dict, Any, Optional
from dataclasses import dataclass
from datetime import datetime, date
from decimal import Decimal, InvalidOperation
import re


@dataclass
class ValidationError:
    """验证错误"""
    row_number: int
    field_name: str
    field_value: Any
    error_message: str
    error_type: str  # 'missing', 'invalid_format', 'invalid_value', 'duplicate'


class ImportValidator:
    """导入数据验证器
    
    验证交易记录和往来单位数据的完整性和正确性。
    """
    
    # 交易类型有效值
    VALID_TRANSACTION_TYPES = ['income', 'expense', 'order', '收入', '支出', '订单']
    
    # 往来单位类型有效值
    VALID_COUNTERPARTY_TYPES = ['customer', 'supplier', '客户', '供应商']
    
    # 交易状态有效值
    VALID_TRANSACTION_STATUSES = [
        'pending', 'completed', 'cancelled', '待处理', '已完成', '已取消'
    ]
    
    def __init__(self):
        """初始化验证器"""
        pass
    
    def validate_transaction_data(
        self,
        data: List[Dict[str, Any]],
        existing_counterparty_ids: Optional[List[str]] = None
    ) -> List[ValidationError]:
        """验证交易记录数据
        
        Args:
            data: 交易记录数据列表
            existing_counterparty_ids: 已存在的往来单位ID列表（用于验证外键）
            
        Returns:
            验证错误列表
        """
        errors = []
        existing_counterparty_ids = existing_counterparty_ids or []
        
        for row_num, record in enumerate(data, start=1):
            # 验证必需字段
            errors.extend(self._validate_required_fields(
                record, row_num, ['date', 'type', 'amount']
            ))
            
            # 验证日期字段
            if 'date' in record:
                errors.extend(self._validate_date_field(
                    record['date'], row_num, 'date'
                ))
            
            # 验证交易类型
            if 'type' in record:
                errors.extend(self._validate_transaction_type(
                    record['type'], row_num
                ))
            
            # 验证金额
            if 'amount' in record:
                errors.extend(self._validate_amount(
                    record['amount'], row_num
                ))
            
            # 验证往来单位ID（如果提供）
            if 'counterparty_id' in record and record['counterparty_id']:
                if existing_counterparty_ids:
                    errors.extend(self._validate_counterparty_reference(
                        record['counterparty_id'],
                        row_num,
                        existing_counterparty_ids
                    ))
            
            # 验证状态（如果提供）
            if 'status' in record and record['status']:
                errors.extend(self._validate_transaction_status(
                    record['status'], row_num
                ))
            
            # 验证描述长度
            if 'description' in record and record['description']:
                errors.extend(self._validate_string_length(
                    record['description'], row_num, 'description', max_length=500
                ))
            
            # 验证分类长度
            if 'category' in record and record['category']:
                errors.extend(self._validate_string_length(
                    record['category'], row_num, 'category', max_length=100
                ))
        
        return errors
    
    def validate_counterparty_data(
        self,
        data: List[Dict[str, Any]],
        existing_names: Optional[List[str]] = None,
        existing_tax_ids: Optional[List[str]] = None
    ) -> List[ValidationError]:
        """验证往来单位数据
        
        Args:
            data: 往来单位数据列表
            existing_names: 已存在的单位名称列表（用于检测重复）
            existing_tax_ids: 已存在的税号列表（用于检测重复）
            
        Returns:
            验证错误列表
        """
        errors = []
        existing_names = existing_names or []
        existing_tax_ids = existing_tax_ids or []
        
        # 用于检测批次内重复
        batch_names = set()
        batch_tax_ids = set()
        
        for row_num, record in enumerate(data, start=1):
            # 验证必需字段
            errors.extend(self._validate_required_fields(
                record, row_num, ['name', 'type']
            ))
            
            # 验证单位名称
            if 'name' in record:
                name = record['name']
                errors.extend(self._validate_string_length(
                    name, row_num, 'name', min_length=2, max_length=200
                ))
                
                # 检测重复名称
                if name in existing_names:
                    errors.append(ValidationError(
                        row_number=row_num,
                        field_name='name',
                        field_value=name,
                        error_message=f"单位名称已存在: {name}",
                        error_type='duplicate'
                    ))
                elif name in batch_names:
                    errors.append(ValidationError(
                        row_number=row_num,
                        field_name='name',
                        field_value=name,
                        error_message=f"批次内单位名称重复: {name}",
                        error_type='duplicate'
                    ))
                else:
                    batch_names.add(name)
            
            # 验证单位类型
            if 'type' in record:
                errors.extend(self._validate_counterparty_type(
                    record['type'], row_num
                ))
            
            # 验证联系人
            if 'contact_person' in record and record['contact_person']:
                errors.extend(self._validate_string_length(
                    record['contact_person'], row_num, 'contact_person', max_length=50
                ))
            
            # 验证电话
            if 'phone' in record and record['phone']:
                errors.extend(self._validate_phone(
                    record['phone'], row_num
                ))
            
            # 验证邮箱
            if 'email' in record and record['email']:
                errors.extend(self._validate_email(
                    record['email'], row_num
                ))
            
            # 验证地址
            if 'address' in record and record['address']:
                errors.extend(self._validate_string_length(
                    record['address'], row_num, 'address', max_length=300
                ))
            
            # 验证税号
            if 'tax_id' in record and record['tax_id']:
                tax_id = record['tax_id']
                errors.extend(self._validate_tax_id(
                    tax_id, row_num
                ))
                
                # 检测重复税号
                if tax_id in existing_tax_ids:
                    errors.append(ValidationError(
                        row_number=row_num,
                        field_name='tax_id',
                        field_value=tax_id,
                        error_message=f"税号已存在: {tax_id}",
                        error_type='duplicate'
                    ))
                elif tax_id in batch_tax_ids:
                    errors.append(ValidationError(
                        row_number=row_num,
                        field_name='tax_id',
                        field_value=tax_id,
                        error_message=f"批次内税号重复: {tax_id}",
                        error_type='duplicate'
                    ))
                else:
                    batch_tax_ids.add(tax_id)
        
        return errors
    
    def _validate_required_fields(
        self,
        record: Dict[str, Any],
        row_num: int,
        required_fields: List[str]
    ) -> List[ValidationError]:
        """验证必需字段"""
        errors = []
        for field in required_fields:
            if field not in record or record[field] is None or record[field] == '':
                errors.append(ValidationError(
                    row_number=row_num,
                    field_name=field,
                    field_value=None,
                    error_message=f"必需字段缺失: {field}",
                    error_type='missing'
                ))
        return errors
    
    def _validate_date_field(
        self,
        value: Any,
        row_num: int,
        field_name: str
    ) -> List[ValidationError]:
        """验证日期字段"""
        errors = []
        
        # 如果已经是date对象，直接返回
        if isinstance(value, (date, datetime)):
            return errors
        
        # 尝试解析字符串日期
        if isinstance(value, str):
            try:
                # 尝试多种日期格式
                for fmt in ['%Y-%m-%d', '%Y/%m/%d', '%Y%m%d', '%d/%m/%Y', '%d-%m-%Y']:
                    try:
                        datetime.strptime(value, fmt)
                        return errors
                    except ValueError:
                        continue
                
                # 所有格式都失败
                errors.append(ValidationError(
                    row_number=row_num,
                    field_name=field_name,
                    field_value=value,
                    error_message=f"日期格式无效: {value}，支持格式: YYYY-MM-DD, YYYY/MM/DD等",
                    error_type='invalid_format'
                ))
            except Exception as e:
                errors.append(ValidationError(
                    row_number=row_num,
                    field_name=field_name,
                    field_value=value,
                    error_message=f"日期解析失败: {str(e)}",
                    error_type='invalid_format'
                ))
        else:
            errors.append(ValidationError(
                row_number=row_num,
                field_name=field_name,
                field_value=value,
                error_message=f"日期类型无效: {type(value).__name__}",
                error_type='invalid_format'
            ))
        
        return errors
    
    def _validate_transaction_type(
        self,
        value: Any,
        row_num: int
    ) -> List[ValidationError]:
        """验证交易类型"""
        errors = []
        
        if not isinstance(value, str):
            errors.append(ValidationError(
                row_number=row_num,
                field_name='type',
                field_value=value,
                error_message=f"交易类型必须是字符串",
                error_type='invalid_format'
            ))
            return errors
        
        if value.lower() not in [t.lower() for t in self.VALID_TRANSACTION_TYPES]:
            errors.append(ValidationError(
                row_number=row_num,
                field_name='type',
                field_value=value,
                error_message=f"无效的交易类型: {value}，有效值: {', '.join(self.VALID_TRANSACTION_TYPES[:3])}",
                error_type='invalid_value'
            ))
        
        return errors
    
    def _validate_amount(
        self,
        value: Any,
        row_num: int
    ) -> List[ValidationError]:
        """验证金额"""
        errors = []
        
        try:
            amount = Decimal(str(value))
            if amount <= 0:
                errors.append(ValidationError(
                    row_number=row_num,
                    field_name='amount',
                    field_value=value,
                    error_message=f"金额必须大于0: {value}",
                    error_type='invalid_value'
                ))
        except (InvalidOperation, ValueError, TypeError):
            errors.append(ValidationError(
                row_number=row_num,
                field_name='amount',
                field_value=value,
                error_message=f"金额格式无效: {value}",
                error_type='invalid_format'
            ))
        
        return errors
    
    def _validate_counterparty_reference(
        self,
        value: Any,
        row_num: int,
        existing_ids: List[str]
    ) -> List[ValidationError]:
        """验证往来单位引用"""
        errors = []
        
        if not isinstance(value, str):
            errors.append(ValidationError(
                row_number=row_num,
                field_name='counterparty_id',
                field_value=value,
                error_message=f"往来单位ID必须是字符串",
                error_type='invalid_format'
            ))
            return errors
        
        if value not in existing_ids:
            errors.append(ValidationError(
                row_number=row_num,
                field_name='counterparty_id',
                field_value=value,
                error_message=f"往来单位不存在: {value}",
                error_type='invalid_value'
            ))
        
        return errors
    
    def _validate_transaction_status(
        self,
        value: Any,
        row_num: int
    ) -> List[ValidationError]:
        """验证交易状态"""
        errors = []
        
        if not isinstance(value, str):
            errors.append(ValidationError(
                row_number=row_num,
                field_name='status',
                field_value=value,
                error_message=f"状态必须是字符串",
                error_type='invalid_format'
            ))
            return errors
        
        if value.lower() not in [s.lower() for s in self.VALID_TRANSACTION_STATUSES]:
            errors.append(ValidationError(
                row_number=row_num,
                field_name='status',
                field_value=value,
                error_message=f"无效的状态: {value}，有效值: {', '.join(self.VALID_TRANSACTION_STATUSES[:3])}",
                error_type='invalid_value'
            ))
        
        return errors
    
    def _validate_counterparty_type(
        self,
        value: Any,
        row_num: int
    ) -> List[ValidationError]:
        """验证往来单位类型"""
        errors = []
        
        if not isinstance(value, str):
            errors.append(ValidationError(
                row_number=row_num,
                field_name='type',
                field_value=value,
                error_message=f"单位类型必须是字符串",
                error_type='invalid_format'
            ))
            return errors
        
        if value.lower() not in [t.lower() for t in self.VALID_COUNTERPARTY_TYPES]:
            errors.append(ValidationError(
                row_number=row_num,
                field_name='type',
                field_value=value,
                error_message=f"无效的单位类型: {value}，有效值: {', '.join(self.VALID_COUNTERPARTY_TYPES[:2])}",
                error_type='invalid_value'
            ))
        
        return errors
    
    def _validate_string_length(
        self,
        value: Any,
        row_num: int,
        field_name: str,
        min_length: int = 0,
        max_length: int = 1000
    ) -> List[ValidationError]:
        """验证字符串长度"""
        errors = []
        
        if not isinstance(value, str):
            errors.append(ValidationError(
                row_number=row_num,
                field_name=field_name,
                field_value=value,
                error_message=f"{field_name}必须是字符串",
                error_type='invalid_format'
            ))
            return errors
        
        length = len(value)
        if length < min_length:
            errors.append(ValidationError(
                row_number=row_num,
                field_name=field_name,
                field_value=value,
                error_message=f"{field_name}长度不能少于{min_length}个字符",
                error_type='invalid_value'
            ))
        
        if length > max_length:
            errors.append(ValidationError(
                row_number=row_num,
                field_name=field_name,
                field_value=value,
                error_message=f"{field_name}长度不能超过{max_length}个字符",
                error_type='invalid_value'
            ))
        
        return errors
    
    def _validate_phone(
        self,
        value: Any,
        row_num: int
    ) -> List[ValidationError]:
        """验证电话号码"""
        errors = []
        
        if not isinstance(value, str):
            value = str(value)
        
        # 移除常见分隔符
        phone = re.sub(r'[\s\-()]', '', value)
        
        # 验证格式（支持手机和固话）
        if not re.match(r'^1[3-9]\d{9}$|^0\d{2,3}-?\d{7,8}$|^\d{7,11}$', phone):
            errors.append(ValidationError(
                row_number=row_num,
                field_name='phone',
                field_value=value,
                error_message=f"电话号码格式无效: {value}",
                error_type='invalid_format'
            ))
        
        return errors
    
    def _validate_email(
        self,
        value: Any,
        row_num: int
    ) -> List[ValidationError]:
        """验证邮箱地址"""
        errors = []
        
        if not isinstance(value, str):
            errors.append(ValidationError(
                row_number=row_num,
                field_name='email',
                field_value=value,
                error_message=f"邮箱必须是字符串",
                error_type='invalid_format'
            ))
            return errors
        
        # 简单的邮箱格式验证
        email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        if not re.match(email_pattern, value):
            errors.append(ValidationError(
                row_number=row_num,
                field_name='email',
                field_value=value,
                error_message=f"邮箱格式无效: {value}",
                error_type='invalid_format'
            ))
        
        return errors
    
    def _validate_tax_id(
        self,
        value: Any,
        row_num: int
    ) -> List[ValidationError]:
        """验证税号"""
        errors = []
        
        if not isinstance(value, str):
            value = str(value)
        
        # 移除空格和分隔符
        tax_id = re.sub(r'[\s\-]', '', value)
        
        # 验证长度（15位或18位统一社会信用代码）
        if len(tax_id) not in [15, 18, 20]:
            errors.append(ValidationError(
                row_number=row_num,
                field_name='tax_id',
                field_value=value,
                error_message=f"税号长度无效: {value}（应为15位或18位）",
                error_type='invalid_format'
            ))
        
        return errors
