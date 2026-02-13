"""
Excel批量导入引擎模块

处理Excel文件的导入、预览、验证和撤销操作。
"""

from typing import List, Dict, Any, Optional
from dataclasses import dataclass
from datetime import datetime, date
from decimal import Decimal
import uuid
import openpyxl
import pandas as pd

from small_accountant_v16.models.core_models import (
    TransactionRecord, Counterparty, ImportResult,
    PreviewResult, TransactionType, CounterpartyType,
    TransactionStatus
)
from small_accountant_v16.storage.transaction_storage import TransactionStorage
from small_accountant_v16.storage.counterparty_storage import CounterpartyStorage
from small_accountant_v16.storage.import_history import ImportHistory
from small_accountant_v16.import_engine.column_recognizer import ExcelColumnRecognizer, ColumnMapping
from small_accountant_v16.import_engine.validator import ImportValidator, ValidationError


@dataclass
class ImportData:
    """导入数据"""
    import_id: str
    import_type: str  # 'transaction' or 'counterparty'
    imported_ids: List[str]
    import_date: datetime
    source_file: str


class ImportEngine:
    """Excel批量导入引擎
    
    提供Excel文件的智能导入功能，包括：
    - 列名识别和映射
    - 数据验证
    - 批量导入
    - 预览功能
    - 撤销导入
    """
    
    def __init__(
        self,
        transaction_storage: TransactionStorage,
        counterparty_storage: CounterpartyStorage,
        import_history: ImportHistory
    ):
        """初始化导入引擎
        
        Args:
            transaction_storage: 交易记录存储
            counterparty_storage: 往来单位存储
            import_history: 导入历史管理
        """
        self.transaction_storage = transaction_storage
        self.counterparty_storage = counterparty_storage
        self.import_history = import_history
        self.column_recognizer = ExcelColumnRecognizer()
        self.validator = ImportValidator()
    
    def preview_import(
        self,
        excel_file: str,
        data_type: str = 'transaction',
        sheet_name: Optional[str] = None
    ) -> PreviewResult:
        """预览导入数据
        
        Args:
            excel_file: Excel文件路径
            data_type: 数据类型，'transaction' 或 'counterparty'
            sheet_name: 工作表名称（可选，默认第一个）
            
        Returns:
            PreviewResult: 预览结果
        """
        try:
            # 读取Excel文件
            df = self._read_excel_file(excel_file, sheet_name)
            
            if df.empty:
                return PreviewResult(
                    column_mapping=ColumnMapping(
                        source_columns=[],
                        target_fields={},
                        confidence=0.0,
                        unmapped_columns=[],
                        missing_required_fields=[]
                    ),
                    sample_data=df,
                    validation_errors=[
                        ValidationError(
                            row_number=0,
                            field_name='file',
                            field_value=excel_file,
                            error_message='Excel文件为空或没有数据',
                            error_type='invalid_format'
                        )
                    ],
                    estimated_rows=0
                )
            
            # 识别列名
            column_names = df.columns.tolist()
            column_mapping = self.column_recognizer.recognize_columns(
                column_names, data_type
            )
            
            # 映射列名
            mapped_df = self._map_columns(df, column_mapping.target_fields)
            
            # 转换为字典列表
            data_records = mapped_df.to_dict('records')
            
            # 验证数据
            if data_type == 'transaction':
                existing_cp_ids = [
                    cp.id for cp in self.counterparty_storage.get_all()
                ]
                validation_errors = self.validator.validate_transaction_data(
                    data_records, existing_cp_ids
                )
            elif data_type == 'counterparty':
                existing_names = [
                    cp.name for cp in self.counterparty_storage.get_all()
                ]
                existing_tax_ids = [
                    cp.tax_id for cp in self.counterparty_storage.get_all()
                    if cp.tax_id
                ]
                validation_errors = self.validator.validate_counterparty_data(
                    data_records, existing_names, existing_tax_ids
                )
            else:
                raise ValueError(f"不支持的数据类型: {data_type}")
            
            # 返回预览结果（只显示前10行）
            sample_df = mapped_df.head(10)
            
            return PreviewResult(
                column_mapping=column_mapping,
                sample_data=sample_df,
                validation_errors=validation_errors,
                estimated_rows=len(df)
            )
            
        except Exception as e:
            # 返回错误预览结果
            return PreviewResult(
                column_mapping=ColumnMapping(
                    source_columns=[],
                    target_fields={},
                    confidence=0.0,
                    unmapped_columns=[],
                    missing_required_fields=[]
                ),
                sample_data=pd.DataFrame(),
                validation_errors=[
                    ValidationError(
                        row_number=0,
                        field_name='file',
                        field_value=excel_file,
                        error_message=f'读取Excel文件失败: {str(e)}',
                        error_type='invalid_format'
                    )
                ],
                estimated_rows=0
            )
    
    def import_transactions(
        self,
        excel_file: str,
        sheet_name: Optional[str] = None,
        skip_validation: bool = False
    ) -> ImportResult:
        """批量导入交易记录
        
        Args:
            excel_file: Excel文件路径
            sheet_name: 工作表名称（可选）
            skip_validation: 是否跳过验证（默认False）
            
        Returns:
            ImportResult: 导入结果
        """
        import_id = str(uuid.uuid4())
        imported_ids = []
        errors = []
        
        try:
            # 读取Excel文件
            df = self._read_excel_file(excel_file, sheet_name)
            
            if df.empty:
                return ImportResult(
                    import_id=import_id,
                    total_rows=0,
                    successful_rows=0,
                    failed_rows=0,
                    errors=[],
                    import_date=datetime.now(),
                    can_undo=False
                )
            
            # 识别和映射列名
            column_names = df.columns.tolist()
            column_mapping = self.column_recognizer.recognize_columns(
                column_names, 'transaction'
            )
            mapped_df = self._map_columns(df, column_mapping.target_fields)
            data_records = mapped_df.to_dict('records')
            
            # 验证数据（除非跳过）
            if not skip_validation:
                existing_cp_ids = [
                    cp.id for cp in self.counterparty_storage.get_all()
                ]
                validation_errors = self.validator.validate_transaction_data(
                    data_records, existing_cp_ids
                )
                
                if validation_errors:
                    return ImportResult(
                        import_id=import_id,
                        total_rows=len(data_records),
                        successful_rows=0,
                        failed_rows=len(data_records),
                        errors=validation_errors,
                        import_date=datetime.now(),
                        can_undo=False
                    )
            
            # 导入数据
            for row_num, record in enumerate(data_records, start=1):
                try:
                    transaction = self._create_transaction_from_record(record)
                    self.transaction_storage.add(transaction)
                    imported_ids.append(transaction.id)
                except Exception as e:
                    errors.append(ValidationError(
                        row_number=row_num,
                        field_name='record',
                        field_value=str(record),
                        error_message=f'导入失败: {str(e)}',
                        error_type='invalid_value'
                    ))
            
            # 记录导入历史
            if imported_ids:
                self.import_history.record_import(
                    import_id=import_id,
                    import_type='transaction',
                    imported_ids=imported_ids,
                    source_file=excel_file
                )
            
            return ImportResult(
                import_id=import_id,
                total_rows=len(data_records),
                successful_rows=len(imported_ids),
                failed_rows=len(errors),
                errors=errors,
                import_date=datetime.now(),
                can_undo=len(imported_ids) > 0
            )
            
        except Exception as e:
            return ImportResult(
                import_id=import_id,
                total_rows=0,
                successful_rows=0,
                failed_rows=0,
                errors=[
                    ValidationError(
                        row_number=0,
                        field_name='file',
                        field_value=excel_file,
                        error_message=f'导入失败: {str(e)}',
                        error_type='invalid_format'
                    )
                ],
                import_date=datetime.now(),
                can_undo=False
            )
    
    def import_counterparties(
        self,
        excel_file: str,
        sheet_name: Optional[str] = None,
        skip_validation: bool = False
    ) -> ImportResult:
        """批量导入往来单位
        
        Args:
            excel_file: Excel文件路径
            sheet_name: 工作表名称（可选）
            skip_validation: 是否跳过验证（默认False）
            
        Returns:
            ImportResult: 导入结果
        """
        import_id = str(uuid.uuid4())
        imported_ids = []
        errors = []
        
        try:
            # 读取Excel文件
            df = self._read_excel_file(excel_file, sheet_name)
            
            if df.empty:
                return ImportResult(
                    import_id=import_id,
                    total_rows=0,
                    successful_rows=0,
                    failed_rows=0,
                    errors=[],
                    import_date=datetime.now(),
                    can_undo=False
                )
            
            # 识别和映射列名
            column_names = df.columns.tolist()
            column_mapping = self.column_recognizer.recognize_columns(
                column_names, 'counterparty'
            )
            mapped_df = self._map_columns(df, column_mapping.target_fields)
            data_records = mapped_df.to_dict('records')
            
            # 验证数据（除非跳过）
            if not skip_validation:
                existing_names = [
                    cp.name for cp in self.counterparty_storage.get_all()
                ]
                existing_tax_ids = [
                    cp.tax_id for cp in self.counterparty_storage.get_all()
                    if cp.tax_id
                ]
                validation_errors = self.validator.validate_counterparty_data(
                    data_records, existing_names, existing_tax_ids
                )
                
                if validation_errors:
                    return ImportResult(
                        import_id=import_id,
                        total_rows=len(data_records),
                        successful_rows=0,
                        failed_rows=len(data_records),
                        errors=validation_errors,
                        import_date=datetime.now(),
                        can_undo=False
                    )
            
            # 导入数据
            for row_num, record in enumerate(data_records, start=1):
                try:
                    counterparty = self._create_counterparty_from_record(record)
                    self.counterparty_storage.add(counterparty)
                    imported_ids.append(counterparty.id)
                except Exception as e:
                    errors.append(ValidationError(
                        row_number=row_num,
                        field_name='record',
                        field_value=str(record),
                        error_message=f'导入失败: {str(e)}',
                        error_type='invalid_value'
                    ))
            
            # 记录导入历史
            if imported_ids:
                self.import_history.record_import(
                    import_id=import_id,
                    import_type='counterparty',
                    imported_ids=imported_ids,
                    source_file=excel_file
                )
            
            return ImportResult(
                import_id=import_id,
                total_rows=len(data_records),
                successful_rows=len(imported_ids),
                failed_rows=len(errors),
                errors=errors,
                import_date=datetime.now(),
                can_undo=len(imported_ids) > 0
            )
            
        except Exception as e:
            return ImportResult(
                import_id=import_id,
                total_rows=0,
                successful_rows=0,
                failed_rows=0,
                errors=[
                    ValidationError(
                        row_number=0,
                        field_name='file',
                        field_value=excel_file,
                        error_message=f'导入失败: {str(e)}',
                        error_type='invalid_format'
                    )
                ],
                import_date=datetime.now(),
                can_undo=False
            )
    
    def undo_import(self, import_id: str) -> bool:
        """撤销导入操作
        
        Args:
            import_id: 导入ID
            
        Returns:
            是否成功撤销
        """
        try:
            # 获取导入记录
            import_record = self.import_history.get_import_by_id(import_id)
            if not import_record:
                return False
            
            if import_record.get('undone', False):
                return False  # 已经撤销过
            
            # 删除导入的记录
            import_type = import_record['import_type']
            imported_ids = import_record['imported_ids']
            
            if import_type == 'transaction':
                for record_id in imported_ids:
                    try:
                        self.transaction_storage.delete(record_id)
                    except Exception:
                        pass  # 忽略已删除的记录
            elif import_type == 'counterparty':
                for record_id in imported_ids:
                    try:
                        self.counterparty_storage.delete(record_id)
                    except Exception:
                        pass  # 忽略已删除的记录
            
            # 标记为已撤销
            self.import_history.mark_as_undone(import_id)
            
            return True
            
        except Exception:
            return False
    
    def validate_import_data(
        self,
        data: List[Dict[str, Any]],
        data_type: str = 'transaction'
    ) -> List[ValidationError]:
        """验证导入数据
        
        Args:
            data: 数据列表
            data_type: 数据类型
            
        Returns:
            验证错误列表
        """
        if data_type == 'transaction':
            existing_cp_ids = [
                cp.id for cp in self.counterparty_storage.get_all()
            ]
            return self.validator.validate_transaction_data(data, existing_cp_ids)
        elif data_type == 'counterparty':
            existing_names = [
                cp.name for cp in self.counterparty_storage.get_all()
            ]
            existing_tax_ids = [
                cp.tax_id for cp in self.counterparty_storage.get_all()
                if cp.tax_id
            ]
            return self.validator.validate_counterparty_data(
                data, existing_names, existing_tax_ids
            )
        else:
            raise ValueError(f"不支持的数据类型: {data_type}")
    
    def _read_excel_file(
        self,
        excel_file: str,
        sheet_name: Optional[str] = None
    ) -> pd.DataFrame:
        """读取Excel文件
        
        Args:
            excel_file: Excel文件路径
            sheet_name: 工作表名称
            
        Returns:
            DataFrame
        """
        try:
            if sheet_name:
                df = pd.read_excel(excel_file, sheet_name=sheet_name)
            else:
                df = pd.read_excel(excel_file)
            
            # 删除完全空白的行
            df = df.dropna(how='all')
            
            return df
        except Exception as e:
            raise ValueError(f"读取Excel文件失败: {str(e)}")
    
    def _map_columns(
        self,
        df: pd.DataFrame,
        column_mapping: Dict[str, str]
    ) -> pd.DataFrame:
        """映射列名
        
        Args:
            df: 原始DataFrame
            column_mapping: 列映射字典（目标字段 -> 源列名）
            
        Returns:
            映射后的DataFrame
        """
        # 创建反向映射（源列名 -> 目标字段）
        reverse_mapping = {v: k for k, v in column_mapping.items()}
        
        # 重命名列
        mapped_df = df.rename(columns=reverse_mapping)
        
        # 只保留映射的列
        mapped_columns = list(column_mapping.keys())
        existing_columns = [col for col in mapped_columns if col in mapped_df.columns]
        
        return mapped_df[existing_columns]
    
    def _create_transaction_from_record(
        self,
        record: Dict[str, Any]
    ) -> TransactionRecord:
        """从记录创建交易对象
        
        Args:
            record: 记录字典
            
        Returns:
            TransactionRecord
        """
        # 解析日期
        trans_date = self._parse_date(record['date'])
        
        # 解析交易类型
        trans_type = self._parse_transaction_type(record['type'])
        
        # 解析金额
        amount = Decimal(str(record['amount']))
        
        # 解析状态
        status = TransactionStatus.COMPLETED
        if 'status' in record and record['status']:
            status = self._parse_transaction_status(record['status'])
        
        return TransactionRecord(
            id=str(uuid.uuid4()),
            date=trans_date,
            type=trans_type,
            amount=amount,
            counterparty_id=record.get('counterparty_id', ''),
            description=record.get('description', ''),
            category=record.get('category', ''),
            status=status,
            created_at=datetime.now(),
            updated_at=datetime.now()
        )
    
    def _create_counterparty_from_record(
        self,
        record: Dict[str, Any]
    ) -> Counterparty:
        """从记录创建往来单位对象
        
        Args:
            record: 记录字典
            
        Returns:
            Counterparty
        """
        # 解析单位类型
        cp_type = self._parse_counterparty_type(record['type'])
        
        return Counterparty(
            id=str(uuid.uuid4()),
            name=record['name'],
            type=cp_type,
            contact_person=record.get('contact_person', ''),
            phone=record.get('phone', ''),
            email=record.get('email', ''),
            address=record.get('address', ''),
            tax_id=record.get('tax_id', ''),
            created_at=datetime.now(),
            updated_at=datetime.now()
        )
    
    def _parse_date(self, value: Any) -> date:
        """解析日期"""
        if isinstance(value, date):
            return value
        if isinstance(value, datetime):
            return value.date()
        
        # 尝试解析字符串
        if isinstance(value, str):
            for fmt in ['%Y-%m-%d', '%Y/%m/%d', '%Y%m%d', '%d/%m/%Y', '%d-%m-%Y']:
                try:
                    return datetime.strptime(value, fmt).date()
                except ValueError:
                    continue
        
        raise ValueError(f"无法解析日期: {value}")
    
    def _parse_transaction_type(self, value: str) -> TransactionType:
        """解析交易类型"""
        value_lower = value.lower()
        
        if value_lower in ['income', '收入']:
            return TransactionType.INCOME
        elif value_lower in ['expense', '支出']:
            return TransactionType.EXPENSE
        elif value_lower in ['order', '订单']:
            return TransactionType.ORDER
        else:
            raise ValueError(f"无效的交易类型: {value}")
    
    def _parse_transaction_status(self, value: str) -> TransactionStatus:
        """解析交易状态"""
        value_lower = value.lower()
        
        if value_lower in ['pending', '待处理']:
            return TransactionStatus.PENDING
        elif value_lower in ['completed', '已完成']:
            return TransactionStatus.COMPLETED
        elif value_lower in ['cancelled', '已取消']:
            return TransactionStatus.CANCELLED
        else:
            return TransactionStatus.COMPLETED  # 默认值
    
    def _parse_counterparty_type(self, value: str) -> CounterpartyType:
        """解析往来单位类型"""
        value_lower = value.lower()
        
        if value_lower in ['customer', '客户']:
            return CounterpartyType.CUSTOMER
        elif value_lower in ['supplier', '供应商']:
            return CounterpartyType.SUPPLIER
        else:
            raise ValueError(f"无效的单位类型: {value}")
