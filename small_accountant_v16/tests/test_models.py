"""
Unit tests for core data models

Tests data model creation, validation, and serialization.
"""

import pytest
from datetime import date, datetime
from decimal import Decimal

from small_accountant_v16.models import (
    TransactionRecord,
    Counterparty,
    Reminder,
    BankRecord,
    ReconciliationResult,
    Discrepancy,
    ReportResult,
    ImportResult,
    PreviewResult,
    ColumnMapping,
    DateRange,
    ImportError,
    ValidationError,
    TransactionType,
    CounterpartyType,
    ReminderType,
    ReportType,
    NotificationChannel,
    TransactionStatus,
    ReminderStatus,
    Priority,
    DiscrepancyType,
)


@pytest.mark.unit
class TestTransactionRecord:
    """测试交易记录模型"""
    
    def test_create_transaction_record(self, sample_transaction):
        """测试创建交易记录"""
        assert sample_transaction.id == "T001"
        assert sample_transaction.date == date(2024, 1, 15)
        assert sample_transaction.type == TransactionType.INCOME
        assert sample_transaction.amount == Decimal("10000.00")
        assert sample_transaction.counterparty_id == "C001"
        assert sample_transaction.description == "销售收入"
        assert sample_transaction.category == "销售"
        assert sample_transaction.status == TransactionStatus.COMPLETED
    
    def test_transaction_to_dict(self, sample_transaction):
        """测试交易记录转换为字典"""
        data = sample_transaction.to_dict()
        assert data["id"] == "T001"
        assert data["date"] == "2024-01-15"
        assert data["type"] == "income"
        assert data["amount"] == "10000.00"
        assert data["status"] == "completed"
    
    def test_transaction_from_dict(self, sample_transaction):
        """测试从字典创建交易记录"""
        data = sample_transaction.to_dict()
        restored = TransactionRecord.from_dict(data)
        
        assert restored.id == sample_transaction.id
        assert restored.date == sample_transaction.date
        assert restored.type == sample_transaction.type
        assert restored.amount == sample_transaction.amount
        assert restored.counterparty_id == sample_transaction.counterparty_id
        assert restored.description == sample_transaction.description
        assert restored.category == sample_transaction.category
        assert restored.status == sample_transaction.status
    
    def test_transaction_round_trip(self, sample_transaction):
        """测试交易记录序列化和反序列化的往返"""
        data = sample_transaction.to_dict()
        restored = TransactionRecord.from_dict(data)
        assert restored.to_dict() == data


@pytest.mark.unit
class TestCounterparty:
    """测试往来单位模型"""
    
    def test_create_counterparty(self, sample_counterparty):
        """测试创建往来单位"""
        assert sample_counterparty.id == "C001"
        assert sample_counterparty.name == "测试客户有限公司"
        assert sample_counterparty.type == CounterpartyType.CUSTOMER
        assert sample_counterparty.contact_person == "张三"
        assert sample_counterparty.phone == "13800138000"
        assert sample_counterparty.email == "zhangsan@example.com"
        assert sample_counterparty.tax_id == "91110000000000000X"
    
    def test_counterparty_to_dict(self, sample_counterparty):
        """测试往来单位转换为字典"""
        data = sample_counterparty.to_dict()
        assert data["id"] == "C001"
        assert data["name"] == "测试客户有限公司"
        assert data["type"] == "customer"
        assert data["phone"] == "13800138000"
    
    def test_counterparty_from_dict(self, sample_counterparty):
        """测试从字典创建往来单位"""
        data = sample_counterparty.to_dict()
        restored = Counterparty.from_dict(data)
        
        assert restored.id == sample_counterparty.id
        assert restored.name == sample_counterparty.name
        assert restored.type == sample_counterparty.type
        assert restored.contact_person == sample_counterparty.contact_person
        assert restored.phone == sample_counterparty.phone
        assert restored.email == sample_counterparty.email
        assert restored.tax_id == sample_counterparty.tax_id
    
    def test_counterparty_round_trip(self, sample_counterparty):
        """测试往来单位序列化和反序列化的往返"""
        data = sample_counterparty.to_dict()
        restored = Counterparty.from_dict(data)
        assert restored.to_dict() == data


@pytest.mark.unit
class TestReminder:
    """测试提醒模型"""
    
    def test_create_reminder(self, sample_reminder):
        """测试创建提醒"""
        assert sample_reminder.id == "R001"
        assert sample_reminder.type == ReminderType.TAX
        assert sample_reminder.title == "增值税申报提醒"
        assert sample_reminder.due_date == date(2024, 1, 15)
        assert sample_reminder.priority == Priority.HIGH
        assert sample_reminder.status == ReminderStatus.PENDING
        assert NotificationChannel.DESKTOP in sample_reminder.notification_channels
        assert NotificationChannel.WECHAT in sample_reminder.notification_channels
    
    def test_reminder_to_dict(self, sample_reminder):
        """测试提醒转换为字典"""
        data = sample_reminder.to_dict()
        assert data["id"] == "R001"
        assert data["type"] == "tax"
        assert data["priority"] == "high"
        assert data["status"] == "pending"
        assert "desktop" in data["notification_channels"]
        assert "wechat" in data["notification_channels"]
    
    def test_reminder_from_dict(self, sample_reminder):
        """测试从字典创建提醒"""
        data = sample_reminder.to_dict()
        restored = Reminder.from_dict(data)
        
        assert restored.id == sample_reminder.id
        assert restored.type == sample_reminder.type
        assert restored.title == sample_reminder.title
        assert restored.due_date == sample_reminder.due_date
        assert restored.priority == sample_reminder.priority
        assert restored.status == sample_reminder.status
        assert len(restored.notification_channels) == len(sample_reminder.notification_channels)
    
    def test_reminder_round_trip(self, sample_reminder):
        """测试提醒序列化和反序列化的往返"""
        data = sample_reminder.to_dict()
        restored = Reminder.from_dict(data)
        assert restored.to_dict() == data


@pytest.mark.unit
class TestBankRecord:
    """测试银行流水模型"""
    
    def test_create_bank_record(self, sample_bank_record):
        """测试创建银行流水"""
        assert sample_bank_record.id == "B001"
        assert sample_bank_record.transaction_date == date(2024, 1, 15)
        assert sample_bank_record.description == "收款-测试客户有限公司"
        assert sample_bank_record.amount == Decimal("10000.00")
        assert sample_bank_record.balance == Decimal("50000.00")
        assert sample_bank_record.transaction_type == "CREDIT"
        assert sample_bank_record.counterparty == "测试客户有限公司"
    
    def test_bank_record_to_dict(self, sample_bank_record):
        """测试银行流水转换为字典"""
        data = sample_bank_record.to_dict()
        assert data["id"] == "B001"
        assert data["transaction_date"] == "2024-01-15"
        assert data["amount"] == "10000.00"
        assert data["balance"] == "50000.00"
        assert data["transaction_type"] == "CREDIT"
    
    def test_bank_record_from_dict(self, sample_bank_record):
        """测试从字典创建银行流水"""
        data = sample_bank_record.to_dict()
        restored = BankRecord.from_dict(data)
        
        assert restored.id == sample_bank_record.id
        assert restored.transaction_date == sample_bank_record.transaction_date
        assert restored.description == sample_bank_record.description
        assert restored.amount == sample_bank_record.amount
        assert restored.balance == sample_bank_record.balance
        assert restored.transaction_type == sample_bank_record.transaction_type
        assert restored.counterparty == sample_bank_record.counterparty
    
    def test_bank_record_round_trip(self, sample_bank_record):
        """测试银行流水序列化和反序列化的往返"""
        data = sample_bank_record.to_dict()
        restored = BankRecord.from_dict(data)
        assert restored.to_dict() == data


@pytest.mark.unit
class TestDiscrepancy:
    """测试差异记录模型"""
    
    def test_create_discrepancy_with_both_records(self, sample_bank_record, sample_transaction):
        """测试创建包含两条记录的差异"""
        discrepancy = Discrepancy(
            id="D001",
            type=DiscrepancyType.AMOUNT_DIFF,
            bank_record=sample_bank_record,
            system_record=sample_transaction,
            difference_amount=Decimal("0.00"),
            description="金额一致但描述不同",
        )
        
        assert discrepancy.id == "D001"
        assert discrepancy.type == DiscrepancyType.AMOUNT_DIFF
        assert discrepancy.bank_record is not None
        assert discrepancy.system_record is not None
        assert discrepancy.difference_amount == Decimal("0.00")
    
    def test_create_discrepancy_missing_bank(self, sample_transaction):
        """测试创建缺失银行流水的差异"""
        discrepancy = Discrepancy(
            id="D002",
            type=DiscrepancyType.MISSING_BANK,
            bank_record=None,
            system_record=sample_transaction,
            difference_amount=sample_transaction.amount,
            description="系统有记录但银行流水缺失",
        )
        
        assert discrepancy.bank_record is None
        assert discrepancy.system_record is not None
        assert discrepancy.type == DiscrepancyType.MISSING_BANK
    
    def test_create_discrepancy_missing_system(self, sample_bank_record):
        """测试创建缺失系统记录的差异"""
        discrepancy = Discrepancy(
            id="D003",
            type=DiscrepancyType.MISSING_SYSTEM,
            bank_record=sample_bank_record,
            system_record=None,
            difference_amount=sample_bank_record.amount,
            description="银行有流水但系统记录缺失",
        )
        
        assert discrepancy.bank_record is not None
        assert discrepancy.system_record is None
        assert discrepancy.type == DiscrepancyType.MISSING_SYSTEM
    
    def test_discrepancy_to_dict(self, sample_bank_record, sample_transaction):
        """测试差异记录转换为字典"""
        discrepancy = Discrepancy(
            id="D001",
            type=DiscrepancyType.AMOUNT_DIFF,
            bank_record=sample_bank_record,
            system_record=sample_transaction,
            difference_amount=Decimal("0.00"),
            description="测试差异",
        )
        
        data = discrepancy.to_dict()
        assert data["id"] == "D001"
        assert data["type"] == "amount_diff"
        assert data["bank_record"] is not None
        assert data["system_record"] is not None
        assert data["difference_amount"] == "0.00"


@pytest.mark.unit
class TestReconciliationResult:
    """测试对账结果模型"""
    
    def test_create_reconciliation_result(self):
        """测试创建对账结果"""
        result = ReconciliationResult(
            matched_count=10,
            unmatched_bank_records=[],
            unmatched_system_records=[],
            discrepancies=[],
            reconciliation_date=datetime(2024, 1, 15, 10, 0, 0),
        )
        
        assert result.matched_count == 10
        assert len(result.unmatched_bank_records) == 0
        assert len(result.unmatched_system_records) == 0
        assert len(result.discrepancies) == 0
    
    def test_reconciliation_result_to_dict(self, sample_bank_record, sample_transaction):
        """测试对账结果转换为字典"""
        result = ReconciliationResult(
            matched_count=1,
            unmatched_bank_records=[sample_bank_record],
            unmatched_system_records=[sample_transaction],
            discrepancies=[],
            reconciliation_date=datetime(2024, 1, 15, 10, 0, 0),
        )
        
        data = result.to_dict()
        assert data["matched_count"] == 1
        assert len(data["unmatched_bank_records"]) == 1
        assert len(data["unmatched_system_records"]) == 1
        assert data["reconciliation_date"] == "2024-01-15T10:00:00"


@pytest.mark.unit
class TestReportResult:
    """测试报表结果模型"""
    
    def test_create_report_result_success(self):
        """测试创建成功的报表结果"""
        result = ReportResult(
            report_type=ReportType.MANAGEMENT,
            file_path="/reports/management_2024.xlsx",
            generation_date=datetime(2024, 1, 15, 10, 0, 0),
            data_period=DateRange(date(2024, 1, 1), date(2024, 1, 31)),
            success=True,
        )
        
        assert result.report_type == ReportType.MANAGEMENT
        assert result.file_path == "/reports/management_2024.xlsx"
        assert result.success is True
        assert result.error_message is None
    
    def test_create_report_result_failure(self):
        """测试创建失败的报表结果"""
        result = ReportResult(
            report_type=ReportType.TAX_VAT,
            file_path="",
            generation_date=datetime(2024, 1, 15, 10, 0, 0),
            data_period=DateRange(date(2024, 1, 1), date(2024, 1, 31)),
            success=False,
            error_message="数据不足，无法生成报表",
        )
        
        assert result.success is False
        assert result.error_message == "数据不足，无法生成报表"
    
    def test_report_result_to_dict(self):
        """测试报表结果转换为字典"""
        result = ReportResult(
            report_type=ReportType.BANK_LOAN,
            file_path="/reports/bank_loan.xlsx",
            generation_date=datetime(2024, 1, 15, 10, 0, 0),
            data_period=DateRange(date(2024, 1, 1), date(2024, 12, 31)),
            success=True,
        )
        
        data = result.to_dict()
        assert data["report_type"] == "bank_loan"
        assert data["file_path"] == "/reports/bank_loan.xlsx"
        assert data["success"] is True
        assert data["data_period"]["start_date"] == "2024-01-01"
        assert data["data_period"]["end_date"] == "2024-12-31"


@pytest.mark.unit
class TestImportResult:
    """测试导入结果模型"""
    
    def test_create_import_result_success(self):
        """测试创建成功的导入结果"""
        result = ImportResult(
            import_id="IMP001",
            total_rows=100,
            successful_rows=100,
            failed_rows=0,
            errors=[],
            import_date=datetime(2024, 1, 15, 10, 0, 0),
            can_undo=True,
        )
        
        assert result.import_id == "IMP001"
        assert result.total_rows == 100
        assert result.successful_rows == 100
        assert result.failed_rows == 0
        assert len(result.errors) == 0
        assert result.can_undo is True
    
    def test_create_import_result_with_errors(self):
        """测试创建包含错误的导入结果"""
        errors = [
            ImportError(row_number=5, field="amount", error_message="金额格式错误"),
            ImportError(row_number=10, field="date", error_message="日期格式错误"),
        ]
        
        result = ImportResult(
            import_id="IMP002",
            total_rows=100,
            successful_rows=98,
            failed_rows=2,
            errors=errors,
            import_date=datetime(2024, 1, 15, 10, 0, 0),
            can_undo=True,
        )
        
        assert result.total_rows == 100
        assert result.successful_rows == 98
        assert result.failed_rows == 2
        assert len(result.errors) == 2
        assert result.errors[0].row_number == 5
        assert result.errors[1].row_number == 10
    
    def test_import_result_to_dict(self):
        """测试导入结果转换为字典"""
        result = ImportResult(
            import_id="IMP001",
            total_rows=50,
            successful_rows=50,
            failed_rows=0,
            errors=[],
            import_date=datetime(2024, 1, 15, 10, 0, 0),
            can_undo=True,
        )
        
        data = result.to_dict()
        assert data["import_id"] == "IMP001"
        assert data["total_rows"] == 50
        assert data["successful_rows"] == 50
        assert data["can_undo"] is True


@pytest.mark.unit
class TestColumnMapping:
    """测试列映射模型"""
    
    def test_create_column_mapping(self):
        """测试创建列映射"""
        mapping = ColumnMapping(
            source_columns=["日期", "金额", "描述"],
            target_fields={"日期": "date", "金额": "amount", "描述": "description"},
            confidence=0.95,
        )
        
        assert len(mapping.source_columns) == 3
        assert mapping.target_fields["日期"] == "date"
        assert mapping.target_fields["金额"] == "amount"
        assert mapping.confidence == 0.95
    
    def test_column_mapping_to_dict(self):
        """测试列映射转换为字典"""
        mapping = ColumnMapping(
            source_columns=["交易日期", "交易金额"],
            target_fields={"交易日期": "date", "交易金额": "amount"},
            confidence=0.85,
        )
        
        data = mapping.to_dict()
        assert data["source_columns"] == ["交易日期", "交易金额"]
        assert data["target_fields"]["交易日期"] == "date"
        assert data["confidence"] == 0.85


@pytest.mark.unit
class TestPreviewResult:
    """测试预览结果模型"""
    
    def test_create_preview_result(self):
        """测试创建预览结果"""
        mapping = ColumnMapping(
            source_columns=["日期", "金额"],
            target_fields={"日期": "date", "金额": "amount"},
            confidence=0.9,
        )
        
        sample_data = [
            {"日期": "2024-01-15", "金额": "10000.00"},
            {"日期": "2024-01-16", "金额": "20000.00"},
        ]
        
        result = PreviewResult(
            column_mapping=mapping,
            sample_data=sample_data,
            validation_errors=[],
            estimated_rows=100,
        )
        
        assert result.column_mapping.confidence == 0.9
        assert len(result.sample_data) == 2
        assert result.estimated_rows == 100
        assert len(result.validation_errors) == 0
    
    def test_preview_result_with_errors(self):
        """测试创建包含验证错误的预览结果"""
        mapping = ColumnMapping(
            source_columns=["日期", "金额"],
            target_fields={"日期": "date", "金额": "amount"},
            confidence=0.9,
        )
        
        errors = [
            ValidationError(
                row_number=5,
                field_name="金额",
                field_value="abc",
                error_message="金额必须是数字",
                error_type="invalid_format"
            ),
        ]
        
        result = PreviewResult(
            column_mapping=mapping,
            sample_data=[],
            validation_errors=errors,
            estimated_rows=100,
        )
        
        assert len(result.validation_errors) == 1
        assert result.validation_errors[0].row_number == 5
        assert result.validation_errors[0].field_name == "金额"
    
    def test_preview_result_to_dict(self):
        """测试预览结果转换为字典"""
        mapping = ColumnMapping(
            source_columns=["日期"],
            target_fields={"日期": "date"},
            confidence=1.0,
        )
        
        result = PreviewResult(
            column_mapping=mapping,
            sample_data=[{"日期": "2024-01-15"}],
            validation_errors=[],
            estimated_rows=50,
        )
        
        data = result.to_dict()
        assert data["estimated_rows"] == 50
        assert len(data["sample_data"]) == 1
        assert data["column_mapping"]["confidence"] == 1.0
