# Design Document: V1.6 Small Accountant Practical Enhancement

## Overview

V1.6 Small Accountant Practical Enhancement是一个专为小企业会计人员设计的实用财务管理增强系统。系统采用模块化架构，包含4个核心功能模块：智能报表生成器、智能提醒系统、快速对账助手和Excel批量导入增强。

系统设计原则：
- **简单易用**：界面直观，操作简单，不需要专业IT知识
- **本地运行**：所有核心功能本地执行，不依赖云服务
- **快速落地**：使用成熟的Python库，避免复杂技术
- **高投入产出比**：聚焦核心痛点，快速见效

技术栈：
- Python 3.8+
- openpyxl（Excel读写）
- pandas（数据处理）
- matplotlib（图表生成）
- 企业微信webhook（通知）

## Architecture

系统采用分层架构：

```
┌─────────────────────────────────────────────────────────┐
│                    User Interface Layer                 │
│  (Simple CLI/GUI for Small Accountants)                │
└─────────────────────────────────────────────────────────┘
                          │
┌─────────────────────────────────────────────────────────┐
│                   Application Layer                      │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐ │
│  │   Report     │  │   Reminder   │  │Reconciliation│ │
│  │  Generator   │  │    System    │  │  Assistant   │ │
│  └──────────────┘  └──────────────┘  └──────────────┘ │
│  ┌──────────────┐                                      │
│  │    Import    │                                      │
│  │    Engine    │                                      │
│  └──────────────┘                                      │
└─────────────────────────────────────────────────────────┘
                          │
┌─────────────────────────────────────────────────────────┐
│                     Data Layer                           │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐ │
│  │ Transaction  │  │  Reminder    │  │ Counterparty │ │
│  │   Storage    │  │   Storage    │  │   Storage    │ │
│  └──────────────┘  └──────────────┘  └──────────────┘ │
└─────────────────────────────────────────────────────────┘
                          │
┌─────────────────────────────────────────────────────────┐
│                  External Services                       │
│  ┌──────────────┐  ┌──────────────┐                   │
│  │   WeChat     │  │    Local     │                   │
│  │   Webhook    │  │  File System │                   │
│  └──────────────┘  └──────────────┘                   │
└─────────────────────────────────────────────────────────┘
```

### 架构说明

1. **User Interface Layer**: 提供简单的命令行或图形界面，适合非技术背景用户
2. **Application Layer**: 包含4个核心功能模块，每个模块独立实现
3. **Data Layer**: 本地数据存储，使用JSON或SQLite
4. **External Services**: 最小化外部依赖，仅包含企业微信通知和本地文件系统

## Components and Interfaces

### 1. Report Generator（报表生成器）

**职责**：生成各类财务报表，包括管理报表、税务报表和银行贷款报表。

**核心类**：

```python
class ReportGenerator:
    """智能报表生成器"""
    
    def generate_management_report(
        self, 
        start_date: date, 
        end_date: date
    ) -> ReportResult:
        """生成管理报表（收支对比、利润趋势、客户排名）"""
        pass
    
    def generate_tax_report(
        self, 
        report_type: TaxReportType,
        period: str
    ) -> ReportResult:
        """生成税务报表（增值税、所得税申报表）"""
        pass
    
    def generate_bank_loan_report(
        self, 
        report_date: date
    ) -> ReportResult:
        """生成银行贷款报表（资产负债表、利润表、现金流量表）"""
        pass

class ReportTemplate:
    """报表模板管理"""
    
    def load_template(self, template_name: str) -> Template:
        """加载预定义报表模板"""
        pass
    
    def apply_template(
        self, 
        template: Template, 
        data: DataFrame
    ) -> Workbook:
        """应用模板生成Excel报表"""
        pass

class ChartGenerator:
    """图表生成器"""
    
    def create_revenue_comparison_chart(
        self, 
        data: DataFrame
    ) -> Figure:
        """创建收支对比图"""
        pass
    
    def create_profit_trend_chart(
        self, 
        data: DataFrame
    ) -> Figure:
        """创建利润趋势图"""
        pass
    
    def create_customer_ranking_chart(
        self, 
        data: DataFrame
    ) -> Figure:
        """创建客户排名图"""
        pass
```

**接口说明**：
- `generate_management_report()`: 生成给老板看的管理报表
- `generate_tax_report()`: 生成税务申报表
- `generate_bank_loan_report()`: 生成银行贷款所需报表
- 所有报表输出为Excel格式，包含图表和格式化

### 2. Reminder System（提醒系统）

**职责**：管理各类提醒事项，包括税务申报、应付应收账款和现金流预警。

**核心类**：

```python
class ReminderSystem:
    """智能提醒系统"""
    
    def check_tax_reminders(self) -> List[Reminder]:
        """检查税务申报提醒"""
        pass
    
    def check_payable_reminders(self) -> List[Reminder]:
        """检查应付账款提醒"""
        pass
    
    def check_receivable_reminders(self) -> List[Reminder]:
        """检查应收账款提醒"""
        pass
    
    def check_cashflow_warnings(self) -> List[Reminder]:
        """检查现金流预警"""
        pass
    
    def send_reminder(self, reminder: Reminder) -> bool:
        """发送提醒（桌面+微信）"""
        pass

class ReminderScheduler:
    """提醒调度器"""
    
    def schedule_reminder(
        self, 
        reminder: Reminder, 
        schedule: Schedule
    ) -> None:
        """安排提醒任务"""
        pass
    
    def run_scheduled_checks(self) -> None:
        """运行定时检查"""
        pass

class NotificationService:
    """通知服务"""
    
    def send_desktop_notification(self, message: str) -> bool:
        """发送桌面通知"""
        pass
    
    def send_wechat_notification(
        self, 
        webhook_url: str, 
        message: str
    ) -> bool:
        """发送企业微信通知"""
        pass

class CollectionLetterGenerator:
    """催款函生成器"""
    
    def generate_collection_letter(
        self, 
        customer: Counterparty,
        overdue_days: int,
        amount: Decimal
    ) -> str:
        """生成催款函"""
        pass
```

**接口说明**：
- `check_*_reminders()`: 检查各类提醒事项
- `send_reminder()`: 发送提醒通知
- 支持桌面弹窗和企业微信webhook通知
- 自动生成催款函

### 3. Reconciliation Assistant（对账助手）

**职责**：快速完成银行对账、客户对账和供应商对账。

**核心类**：

```python
class ReconciliationAssistant:
    """快速对账助手"""
    
    def reconcile_bank_statement(
        self, 
        bank_statement_file: str
    ) -> ReconciliationResult:
        """银行对账"""
        pass
    
    def generate_customer_statement(
        self, 
        customer_id: str,
        start_date: date,
        end_date: date
    ) -> Workbook:
        """生成客户对账单"""
        pass
    
    def reconcile_supplier_accounts(
        self, 
        supplier_id: str
    ) -> ReconciliationResult:
        """供应商对账"""
        pass

class BankStatementMatcher:
    """银行流水匹配器"""
    
    def match_transactions(
        self, 
        bank_records: List[BankRecord],
        system_records: List[TransactionRecord]
    ) -> MatchResult:
        """匹配银行流水和系统记录"""
        pass
    
    def identify_discrepancies(
        self, 
        match_result: MatchResult
    ) -> List[Discrepancy]:
        """识别差异"""
        pass

class ReconciliationReportGenerator:
    """对账报告生成器"""
    
    def generate_discrepancy_report(
        self, 
        discrepancies: List[Discrepancy]
    ) -> Workbook:
        """生成差异报告"""
        pass
    
    def generate_customer_statement_excel(
        self, 
        customer_data: CustomerAccountData
    ) -> Workbook:
        """生成客户对账单Excel"""
        pass
```

**接口说明**：
- `reconcile_bank_statement()`: 导入银行流水并自动匹配
- `generate_customer_statement()`: 生成客户对账单
- `reconcile_supplier_accounts()`: 核对供应商账目
- 自动标记差异并生成差异报告

### 4. Import Engine（导入引擎）

**职责**：智能识别Excel格式并批量导入数据。

**核心类**：

```python
class ImportEngine:
    """Excel批量导入增强引擎"""
    
    def import_transactions(
        self, 
        excel_file: str
    ) -> ImportResult:
        """批量导入交易记录"""
        pass
    
    def import_counterparties(
        self, 
        excel_file: str
    ) -> ImportResult:
        """批量导入往来单位"""
        pass
    
    def preview_import(
        self, 
        excel_file: str
    ) -> PreviewResult:
        """预览导入数据"""
        pass
    
    def validate_import_data(
        self, 
        data: DataFrame
    ) -> ValidationResult:
        """验证导入数据"""
        pass
    
    def undo_import(self, import_id: str) -> bool:
        """撤销导入"""
        pass

class ExcelColumnRecognizer:
    """Excel列识别器"""
    
    def recognize_columns(
        self, 
        excel_file: str
    ) -> ColumnMapping:
        """智能识别Excel列名"""
        pass
    
    def suggest_mapping(
        self, 
        detected_columns: List[str]
    ) -> ColumnMapping:
        """建议列映射"""
        pass

class ImportValidator:
    """导入验证器"""
    
    def validate_transaction_data(
        self, 
        data: DataFrame
    ) -> List[ValidationError]:
        """验证交易数据"""
        pass
    
    def validate_counterparty_data(
        self, 
        data: DataFrame
    ) -> List[ValidationError]:
        """验证往来单位数据"""
        pass

class ImportHistory:
    """导入历史管理"""
    
    def record_import(
        self, 
        import_data: ImportData
    ) -> str:
        """记录导入操作"""
        pass
    
    def get_import_history(self) -> List[ImportRecord]:
        """获取导入历史"""
        pass
    
    def rollback_import(self, import_id: str) -> bool:
        """回滚导入"""
        pass
```

**接口说明**：
- `import_transactions()`: 批量导入交易记录
- `import_counterparties()`: 批量导入往来单位
- `preview_import()`: 导入前预览和验证
- `undo_import()`: 支持撤销导入操作
- 智能识别Excel列名，不需要严格模板

## Data Models

### 核心数据模型

```python
@dataclass
class TransactionRecord:
    """交易记录"""
    id: str
    date: date
    type: TransactionType  # INCOME, EXPENSE, ORDER
    amount: Decimal
    counterparty_id: str
    description: str
    category: str
    status: TransactionStatus
    created_at: datetime
    updated_at: datetime

@dataclass
class Counterparty:
    """往来单位（客户/供应商）"""
    id: str
    name: str
    type: CounterpartyType  # CUSTOMER, SUPPLIER
    contact_person: str
    phone: str
    email: str
    address: str
    tax_id: str
    created_at: datetime
    updated_at: datetime

@dataclass
class Reminder:
    """提醒事项"""
    id: str
    type: ReminderType  # TAX, PAYABLE, RECEIVABLE, CASHFLOW
    title: str
    description: str
    due_date: date
    priority: Priority  # HIGH, MEDIUM, LOW
    status: ReminderStatus  # PENDING, SENT, COMPLETED
    notification_channels: List[NotificationChannel]
    created_at: datetime

@dataclass
class BankRecord:
    """银行流水记录"""
    id: str
    transaction_date: date
    description: str
    amount: Decimal
    balance: Decimal
    transaction_type: str  # DEBIT, CREDIT
    counterparty: str

@dataclass
class ReconciliationResult:
    """对账结果"""
    matched_count: int
    unmatched_bank_records: List[BankRecord]
    unmatched_system_records: List[TransactionRecord]
    discrepancies: List[Discrepancy]
    reconciliation_date: datetime

@dataclass
class Discrepancy:
    """差异记录"""
    id: str
    type: DiscrepancyType  # AMOUNT_DIFF, MISSING_BANK, MISSING_SYSTEM
    bank_record: Optional[BankRecord]
    system_record: Optional[TransactionRecord]
    difference_amount: Decimal
    description: str

@dataclass
class ReportResult:
    """报表生成结果"""
    report_type: ReportType
    file_path: str
    generation_date: datetime
    data_period: DateRange
    success: bool
    error_message: Optional[str]

@dataclass
class ImportResult:
    """导入结果"""
    import_id: str
    total_rows: int
    successful_rows: int
    failed_rows: int
    errors: List[ImportError]
    import_date: datetime
    can_undo: bool

@dataclass
class PreviewResult:
    """导入预览结果"""
    column_mapping: ColumnMapping
    sample_data: DataFrame
    validation_errors: List[ValidationError]
    estimated_rows: int

@dataclass
class ColumnMapping:
    """列映射"""
    source_columns: List[str]
    target_fields: Dict[str, str]
    confidence: float  # 识别置信度
```

### 枚举类型

```python
class TransactionType(Enum):
    INCOME = "income"
    EXPENSE = "expense"
    ORDER = "order"

class CounterpartyType(Enum):
    CUSTOMER = "customer"
    SUPPLIER = "supplier"

class ReminderType(Enum):
    TAX = "tax"
    PAYABLE = "payable"
    RECEIVABLE = "receivable"
    CASHFLOW = "cashflow"

class ReportType(Enum):
    MANAGEMENT = "management"
    TAX_VAT = "tax_vat"
    TAX_INCOME = "tax_income"
    BANK_LOAN = "bank_loan"

class NotificationChannel(Enum):
    DESKTOP = "desktop"
    WECHAT = "wechat"
```


## Correctness Properties

*A property is a characteristic or behavior that should hold true across all valid executions of a system—essentially, a formal statement about what the system should do. Properties serve as the bridge between human-readable specifications and machine-verifiable correctness guarantees.*

### Report Generator Properties

**Property 1: Management report completeness**
*For any* valid date range and transaction data, when generating a management report, the output Excel file should contain revenue comparison charts, profit trend charts, and customer ranking reports.
**Validates: Requirements 1.1**

**Property 2: Tax report structure**
*For any* valid tax period and transaction data, when generating a tax report, the output should contain the correct tax form structure (VAT or income tax declaration form) with all required fields populated.
**Validates: Requirements 1.2**

**Property 3: Bank loan report completeness**
*For any* valid report date and transaction data, when generating a bank loan report, the output should contain all three required financial statements: balance sheet, income statement, and cash flow statement.
**Validates: Requirements 1.3**

**Property 4: Excel output format consistency**
*For any* report type, the generated output should be a valid Excel file with embedded charts and proper formatting.
**Validates: Requirements 1.4, 1.6**

### Reminder System Properties

**Property 5: Tax reminder timing**
*For any* tax filing deadline, the system should generate reminders at exactly 7 days, 3 days, 1 day, and 0 days before the deadline.
**Validates: Requirements 2.1**

**Property 6: Payable reminder timing**
*For any* accounts payable record with a due date, the system should send a reminder before the due date.
**Validates: Requirements 2.2**

**Property 7: Receivable overdue alerts**
*For any* accounts receivable record, when it becomes overdue by 30, 60, or 90 days, the system should send an alert and generate a collection letter.
**Validates: Requirements 2.3**

**Property 8: Cash flow warning prediction**
*For any* set of transaction data, when predicted cash flow for the next 7 days is insufficient, the system should send a cash flow warning.
**Validates: Requirements 2.4**

**Property 9: Multi-channel notification delivery**
*For any* reminder, when sent, the system should deliver notifications through both desktop and WeChat channels (if configured).
**Validates: Requirements 2.5**

**Property 10: Reminder configuration respect**
*For any* configured reminder settings (timing and channels), the system should respect those settings when sending reminders.
**Validates: Requirements 2.6**

### Reconciliation Assistant Properties

**Property 11: Bank reconciliation matching and discrepancy detection**
*For any* bank statement Excel file and system transaction records, the reconciliation process should correctly match identical transactions and identify all discrepancies (unmatched records and amount differences).
**Validates: Requirements 3.1, 3.4**

**Property 12: Customer statement generation**
*For any* customer and date range, the generated customer reconciliation statement should be a valid Excel file containing all transactions for that customer within the specified period.
**Validates: Requirements 3.2**

**Property 13: Supplier reconciliation verification**
*For any* supplier, the reconciliation process should correctly match purchase orders with payment records and identify any unmatched items.
**Validates: Requirements 3.3**

### Import Engine Properties

**Property 14: Column recognition accuracy**
*For any* Excel file with common column naming patterns, the system should correctly identify and map columns to target fields with reasonable confidence.
**Validates: Requirements 4.1**

**Property 15: Transaction import completeness**
*For any* valid Excel file containing transaction data (revenue, expenses, orders), all valid rows should be successfully imported as Transaction_Records.
**Validates: Requirements 4.2**

**Property 16: Counterparty import completeness**
*For any* valid Excel file containing counterparty data (customers, suppliers), all valid rows should be successfully imported as Counterparty records.
**Validates: Requirements 4.3**

**Property 17: Import preview validation**
*For any* Excel file prepared for import, the preview should identify all validation errors before the actual import occurs.
**Validates: Requirements 4.4**

**Property 18: Import undo round-trip**
*For any* completed import operation, performing an undo should restore the system to its state before the import (round-trip property).
**Validates: Requirements 4.5**

## Error Handling

### Report Generation Errors

1. **Missing Data**: If insufficient data exists for a report period, return a clear error message indicating the missing data requirements
2. **Invalid Date Range**: If the date range is invalid (end before start), reject the request with a descriptive error
3. **Template Loading Failure**: If a report template cannot be loaded, fall back to a basic template or return an error
4. **Chart Generation Failure**: If chart generation fails, generate the report without charts and log a warning

### Reminder System Errors

1. **Notification Delivery Failure**: If desktop or WeChat notification fails, log the error and retry up to 3 times
2. **Invalid Reminder Configuration**: If reminder configuration is invalid, use default settings and notify the user
3. **Date Calculation Errors**: If date calculations fail (e.g., invalid due dates), log the error and skip that reminder
4. **Collection Letter Generation Failure**: If collection letter generation fails, send a basic alert without the letter

### Reconciliation Errors

1. **Invalid Excel Format**: If the uploaded Excel file is corrupted or invalid, return a clear error message with format requirements
2. **Column Recognition Failure**: If columns cannot be recognized, prompt the user to manually map columns
3. **Matching Algorithm Failure**: If matching fails due to data issues, return partial results with error details
4. **Report Generation Failure**: If discrepancy report generation fails, return raw discrepancy data

### Import Engine Errors

1. **File Reading Errors**: If Excel file cannot be read, return a clear error with file format requirements
2. **Validation Errors**: If data validation fails, return all validation errors in the preview for user correction
3. **Duplicate Detection**: If duplicate records are detected, prompt the user to choose how to handle them (skip, update, or import as new)
4. **Undo Failure**: If undo operation fails (e.g., data has been modified), return an error and prevent partial rollback
5. **Transaction Errors**: If import fails mid-process, rollback all changes to maintain data consistency

### General Error Handling Principles

1. **User-Friendly Messages**: All error messages should be in simple Chinese, avoiding technical jargon
2. **Actionable Guidance**: Error messages should include suggestions for how to fix the problem
3. **Graceful Degradation**: When possible, provide partial functionality rather than complete failure
4. **Error Logging**: All errors should be logged with sufficient detail for troubleshooting
5. **Data Integrity**: Never leave the system in an inconsistent state; use transactions where appropriate

## Testing Strategy

### Dual Testing Approach

The system will use both unit tests and property-based tests to ensure comprehensive coverage:

- **Unit tests**: Verify specific examples, edge cases, and error conditions
- **Property tests**: Verify universal properties across all inputs using randomized testing

Both testing approaches are complementary and necessary. Unit tests catch concrete bugs and validate specific scenarios, while property tests verify general correctness across a wide range of inputs.

### Property-Based Testing Configuration

**Library**: We will use **Hypothesis** for Python property-based testing.

**Configuration**:
- Minimum 100 iterations per property test (due to randomization)
- Each property test must reference its design document property
- Tag format: `# Feature: small-accountant-practical-enhancement, Property {number}: {property_text}`

**Property Test Coverage**:
- Each of the 18 correctness properties will be implemented as a separate property-based test
- Property tests will use Hypothesis strategies to generate random but valid test data
- Tests will verify that properties hold across all generated inputs

### Unit Testing Strategy

**Unit Test Focus**:
- Specific examples that demonstrate correct behavior (e.g., generating a report for a known dataset)
- Edge cases (e.g., empty data, single transaction, boundary dates)
- Error conditions (e.g., invalid Excel files, missing columns, corrupted data)
- Integration points between components (e.g., report generator calling chart generator)

**Unit Test Balance**:
- Avoid writing too many unit tests for scenarios already covered by property tests
- Focus unit tests on concrete examples and edge cases that are hard to express as properties
- Use unit tests to validate error handling and user-facing messages

### Test Data Generation

**For Property Tests**:
- Use Hypothesis strategies to generate random transaction records, counterparties, dates, and amounts
- Generate random but valid Excel files with varying column arrangements
- Generate random bank statements with matching and non-matching transactions

**For Unit Tests**:
- Create fixture data representing typical small business scenarios
- Include edge cases like empty datasets, single records, and boundary conditions
- Create invalid data to test error handling

### Testing Priorities

1. **Critical Path**: Report generation, reconciliation matching, import operations
2. **Data Integrity**: Import undo, transaction consistency, reconciliation accuracy
3. **User Experience**: Error messages, notification delivery, preview functionality
4. **Edge Cases**: Empty data, invalid formats, boundary dates

### Integration Testing

- Test end-to-end workflows (e.g., import data → generate report → send reminder)
- Test external integrations (WeChat webhook, Excel file I/O)
- Test with realistic data volumes (100-1000 transactions)

### Performance Testing

- Verify report generation completes within 10 seconds for typical datasets (1 year of data)
- Verify import operations handle up to 10,000 rows without memory issues
- Verify reconciliation completes within 30 seconds for typical bank statements (1 month)

### Manual Testing Checklist

Since the target users are non-technical small accountants, manual testing should verify:
- [ ] All error messages are in simple Chinese and easy to understand
- [ ] Excel output files open correctly in Microsoft Excel and WPS Office
- [ ] Desktop notifications appear correctly on Windows
- [ ] WeChat notifications are received in enterprise WeChat
- [ ] Generated reports are readable and professionally formatted
- [ ] Import preview interface is intuitive and easy to use
