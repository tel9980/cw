# Design Document: 氧化加工厂工作流程优化系统

## Overview

本设计文档描述了氧化加工厂小白会计工作流程优化系统的技术设计。该系统基于现有的 `oxidation_complete_v17` 和 `small_accountant_v16` 代码库，通过整合和优化现有功能，为非专业会计人员提供简化、高效的财务管理工作流。

系统核心目标：
- 简化复杂的会计操作流程
- 提供智能化的工作流引导
- 支持氧化加工行业特有的业务场景
- 降低小白会计的学习成本和操作难度

技术栈：Python 3.8+, JSON存储, Excel导入导出

## Architecture

系统采用模块化架构，主要包含以下层次：

```
┌─────────────────────────────────────────────────────────┐
│                    用户界面层 (UI Layer)                  │
│  - CLI交互界面                                            │
│  - 工作流向导                                             │
│  - 智能提示系统                                           │
└─────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────┐
│                 工作流引擎层 (Workflow Layer)             │
│  - 工作流模板管理                                         │
│  - 步骤执行引擎                                           │
│  - 上下文感知推荐                                         │
│  - 用户自定义配置                                         │
└─────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────┐
│                  业务逻辑层 (Business Layer)              │
│  - 订单管理  - 收付款管理  - 对账引擎                     │
│  - 账户管理  - 支出分类    - 报表生成                     │
│  - 委外加工  - 数据导入导出                               │
└─────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────┐
│                   数据持久层 (Data Layer)                 │
│  - JSON文件存储                                           │
│  - 数据备份恢复                                           │
│  - 审计日志                                               │
└─────────────────────────────────────────────────────────┘
```

### 关键设计原则

1. **渐进式披露 (Progressive Disclosure)**: 根据用户经验水平动态调整界面复杂度
2. **上下文感知 (Context Awareness)**: 基于当前状态和历史行为提供智能建议
3. **容错设计 (Error Prevention)**: 通过验证和提示减少用户错误
4. **可恢复性 (Recoverability)**: 支持撤销、备份和数据恢复


## Components and Interfaces

### 1. 工作流引擎 (Workflow Engine)

基于 `oxidation_complete_v17/workflow/workflow_engine.py` 的 `OxidationWorkflowEngine`。

**职责**:
- 管理工作流模板（早晨准备、订单处理、交易录入、报表生成、日终处理）
- 执行工作流步骤并跟踪进度
- 提供下一步操作建议
- 支持用户自定义工作流配置

**核心接口**:
```python
class OxidationWorkflowEngine:
    def start_workflow(workflow_type: str, context: Dict, user_id: str) -> WorkflowSession
    def execute_step(session_id: str, step_data: Dict) -> StepResult
    def get_next_suggestions(session_id: str) -> List[WorkflowAction]
    def skip_current_step(session_id: str) -> StepResult
    def save_workflow_customization(user_id: str, template_id: str, customizations: Dict) -> bool
```

### 2. 订单管理器 (Processing Order Manager)

基于 `oxidation_complete_v17/industry/processing_order_manager.py`。

**职责**:
- 创建和管理加工订单
- 支持多种计价单位（件、条、只、个、米长、米重、平方）
- 计算订单总额和利润
- 跟踪收款状态

**核心接口**:
```python
class ProcessingOrderManager:
    def create_order(order_data: Dict) -> ProcessingOrder
    def update_order(order_id: str, updates: Dict) -> ProcessingOrder
    def record_payment(order_id: str, payment_amount: Decimal, account_id: str) -> bool
    def get_order_balance(order_id: str) -> Decimal
    def list_orders(filters: Dict) -> List[ProcessingOrder]
```

### 3. 灵活对账引擎 (Flexible Reconciliation Engine)

基于 `oxidation_complete_v17/reconciliation/flexible_matcher.py`。

**职责**:
- 支持一对多、多对一的收付款匹配
- 自动匹配银行流水与订单/供应商
- 管理未对账项目
- 提供手动匹配建议

**核心接口**:
```python
class FlexibleMatcher:
    def auto_match_transactions(bank_records: List[BankRecord]) -> List[ReconciliationMatch]
    def manual_match(bank_record_ids: List[str], order_ids: List[str]) -> ReconciliationMatch
    def get_unmatched_items() -> Tuple[List[BankRecord], List[ProcessingOrder]]
    def suggest_matches(bank_record: BankRecord) -> List[Tuple[ProcessingOrder, float]]
```

### 4. 银行账户管理器 (Bank Account Manager)

基于 `oxidation_complete_v17/storage/bank_account_manager.py`。

**职责**:
- 管理多个银行账户（G银行、N银行、微信）
- 区分有票/无票账户
- 计算实时余额
- 跟踪资金流向

**核心接口**:
```python
class BankAccountManager:
    def create_account(account_data: Dict) -> BankAccount
    def get_account_balance(account_id: str) -> Decimal
    def list_accounts(account_type: Optional[AccountType] = None) -> List[BankAccount]
    def record_transaction(account_id: str, amount: Decimal, transaction_type: str) -> bool
```


### 5. 委外加工管理器 (Outsourced Processing Manager)

基于 `oxidation_complete_v17/industry/outsourced_processing_manager.py`。

**职责**:
- 管理委外加工记录（喷砂、拉丝、抛光）
- 关联订单和供应商
- 计算委外成本
- 跟踪付款状态

**核心接口**:
```python
class OutsourcedProcessingManager:
    def create_outsourced_processing(data: Dict) -> OutsourcedProcessing
    def update_actual_cost(processing_id: str, actual_cost: Decimal) -> bool
    def get_order_outsourced_cost(order_id: str) -> Decimal
    def list_by_supplier(supplier_id: str) -> List[OutsourcedProcessing]
```

### 6. 支出分类器 (Expense Classifier)

基于 `oxidation_complete_v17/industry/industry_classifier.py`。

**职责**:
- 自动分类支出（房租、水电费、原材料、工资等）
- 支持自定义类别
- 提供分类建议

**核心接口**:
```python
class ExpenseClassifier:
    def classify_expense(description: str, amount: Decimal) -> Tuple[str, float]
    def add_custom_category(category_name: str, keywords: List[str]) -> bool
    def get_all_categories() -> List[str]
```

### 7. 报表生成器 (Report Generator)

基于 `oxidation_complete_v17/reports/industry_report_generator.py`。

**职责**:
- 生成资产负债表、利润表、现金流量表
- 生成行业专用报表（加工费收入明细、外发成本统计、原材料消耗）
- 支持Excel导出
- 生成可视化图表

**核心接口**:
```python
class IndustryReportGenerator:
    def generate_balance_sheet(date_range: DateRange) -> ReportResult
    def generate_income_statement(date_range: DateRange) -> ReportResult
    def generate_cash_flow(date_range: DateRange) -> ReportResult
    def generate_processing_income_report(date_range: DateRange) -> ReportResult
    def generate_outsourced_cost_report(date_range: DateRange) -> ReportResult
```

### 8. 数据导入导出引擎 (Import/Export Engine)

基于 `small_accountant_v16/import_engine/import_engine.py`。

**职责**:
- 从Excel导入订单、银行流水、支出记录
- 智能识别列映射
- 数据验证
- 导出所有数据为Excel

**核心接口**:
```python
class ImportEngine:
    def import_from_excel(file_path: str, data_type: str) -> ImportResult
    def preview_import(file_path: str) -> PreviewResult
    def export_to_excel(data_type: str, output_path: str) -> bool
    def download_template(data_type: str) -> str
```

### 9. 智能工作台 (Smart Dashboard)

基于 `oxidation_complete_v17/workflow/smart_dashboard.py`。

**职责**:
- 显示今日优先任务
- 展示关键财务指标
- 提供快速操作入口
- 显示提醒和预警

**核心接口**:
```python
class SmartDashboard:
    def get_daily_summary(user_id: str, date: date) -> DashboardData
    def get_priority_tasks(user_id: str) -> List[Task]
    def get_key_metrics(date_range: DateRange) -> Dict[str, Any]
```

### 10. 模拟数据生成器 (Demo Data Generator)

**职责**:
- 生成典型的加工订单
- 生成收付款记录
- 生成支出记录
- 清除模拟数据
- 标记模拟数据

**核心接口**:
```python
class DemoDataGenerator:
    def generate_demo_orders(count: int) -> List[ProcessingOrder]
    def generate_demo_payments(count: int) -> List[TransactionRecord]
    def generate_demo_expenses(count: int) -> List[TransactionRecord]
    def clear_demo_data() -> bool
    def is_demo_data(record_id: str) -> bool
```


## Data Models

系统使用 `oxidation_complete_v17/models/core_models.py` 中定义的数据模型。

### 核心数据模型

**ProcessingOrder (加工订单)**:
```python
@dataclass
class ProcessingOrder:
    id: str
    order_number: str
    customer_id: str
    order_date: date
    product_name: str
    pricing_unit: PricingUnit  # 件/条/只/个/米长/米重/平方
    quantity: Decimal
    unit_price: Decimal
    total_amount: Decimal
    status: OrderStatus
    received_amount: Decimal
    outsourced_cost: Decimal
    notes: str
    created_at: datetime
    updated_at: datetime
```

**OutsourcedProcessing (委外加工)**:
```python
@dataclass
class OutsourcedProcessing:
    id: str
    order_id: str
    supplier_id: str
    process_type: ProcessType  # 喷砂/拉丝/抛光
    process_date: date
    quantity: Decimal
    unit_price: Decimal
    total_cost: Decimal
    notes: str
    created_at: datetime
    updated_at: datetime
```

**BankAccount (银行账户)**:
```python
@dataclass
class BankAccount:
    id: str
    name: str  # G银行/N银行/微信
    account_number: str
    account_type: AccountType  # business/cash
    has_invoice: bool  # 是否有票据
    balance: Decimal
    description: str
    created_at: datetime
    updated_at: datetime
```

**ReconciliationMatch (对账匹配)**:
```python
@dataclass
class ReconciliationMatch:
    id: str
    match_date: datetime
    bank_record_ids: List[str]  # 支持多笔
    order_ids: List[str]  # 支持多笔
    total_bank_amount: Decimal
    total_order_amount: Decimal
    difference: Decimal
    notes: str
    created_by: str
    created_at: datetime
```

**TransactionRecord (交易记录)**:
```python
@dataclass
class TransactionRecord:
    id: str
    date: date
    type: TransactionType  # income/expense
    amount: Decimal
    counterparty_id: str
    description: str
    category: str  # 支出类别
    status: TransactionStatus
    pricing_unit: Optional[PricingUnit]
    quantity: Optional[Decimal]
    unit_price: Optional[Decimal]
    bank_account_id: Optional[str]
    created_at: datetime
    updated_at: datetime
```

### 工作流数据模型

**WorkflowSession (工作流会话)**:
```python
@dataclass
class WorkflowSession:
    session_id: str
    user_id: str
    workflow_type: WorkflowType
    template_id: str
    current_step: int
    steps: List[WorkflowStep]
    step_data: Dict[str, Any]
    context: Dict[str, Any]
    is_active: bool
    completed_steps: List[str]
    customizations: Dict[str, Any]
```

**WorkflowStep (工作流步骤)**:
```python
@dataclass
class WorkflowStep:
    step_id: str
    name: str
    description: str
    function_codes: List[str]
    estimated_duration: int  # 秒
    required: bool = True
    status: StepStatus = StepStatus.PENDING
    metadata: Dict[str, Any] = field(default_factory=dict)
```


## Correctness Properties

*A property is a characteristic or behavior that should hold true across all valid executions of a system—essentially, a formal statement about what the system should do. Properties serve as the bridge between human-readable specifications and machine-verifiable correctness guarantees.*

### Property Reflection

After analyzing all acceptance criteria, the following properties were identified. Redundant properties have been consolidated:

- Requirements 1.1-1.4 (different pricing units) → Combined into Property 1 (all pricing units)
- Requirements 2.1-2.4 (flexible payment matching) → Combined into Property 2 (flexible matching)
- Requirements 3.1-3.3 (different account types) → Covered by examples, not properties
- Requirements 5.1-5.3 (outsourced processing fields) → Combined into Property 8
- Requirements 8.1-8.5 (demo data generation) → Covered by examples, not properties
- Requirements 9.1-9.3 (different report types) → Covered by examples, not properties
- Requirements 12.1-12.3 (different import types) → Covered by examples, not properties

### Core Properties

**Property 1: Pricing Unit Support and Calculation**

*For any* processing order with a valid pricing unit (件/条/只/个/米长/米重/平方), quantity, and unit price, the calculated total amount should equal quantity multiplied by unit price.

**Validates: Requirements 1.1, 1.2, 1.3, 1.4, 1.5**

**Property 2: Multi-Item Order Aggregation**

*For any* order containing multiple line items, the total order amount should equal the sum of all individual line item totals.

**Validates: Requirements 1.6**

**Property 3: Flexible Payment Matching (One-to-Many)**

*For any* single payment matched to multiple orders, the sum of allocated amounts to each order should equal the payment amount, and each order's received amount should be updated correctly.

**Validates: Requirements 2.1, 2.3**

**Property 4: Flexible Payment Matching (Many-to-One)**

*For any* single order receiving multiple payments, the sum of all payment amounts should equal the order's total received amount.

**Validates: Requirements 2.2, 2.4**

**Property 5: Unmatched Amount Calculation**

*For any* order, the unmatched amount should equal the total order amount minus the sum of all matched payment amounts.

**Validates: Requirements 2.5**

**Property 6: Payment Matching Persistence**

*For any* manual adjustment to payment-order matching, the new matching relationship should be persisted and retrievable.

**Validates: Requirements 2.6**

**Property 7: Payment Account Requirement**

*For any* payment or receipt transaction, it must have an associated bank account ID.

**Validates: Requirements 3.4**

**Property 8: Account Balance Calculation**

*For any* bank account, the balance should equal the sum of all credit transactions minus the sum of all debit transactions for that account.

**Validates: Requirements 3.5**

**Property 9: Invoice Classification in Reports**

*For any* financial report, transactions should be correctly categorized by whether they used accounts with invoices (has_invoice=true) or without invoices (has_invoice=false).

**Validates: Requirements 3.6**

**Property 10: Expense Category Requirement**

*For any* expense transaction, it must have a valid category assigned.

**Validates: Requirements 4.2**

**Property 11: Custom Category Creation**

*For any* custom expense category created by a user, it should be persisted and available for use in subsequent expense transactions.

**Validates: Requirements 4.3**

**Property 12: Expense Category Filtering**

*For any* expense query with a category filter, all returned results should have the specified category, and no expenses with other categories should be included.

**Validates: Requirements 4.4**

**Property 13: Expense Category Aggregation**

*For any* expense report, the sum of all category subtotals should equal the total expenses for the period.

**Validates: Requirements 4.5**


**Property 14: Outsourced Processing Record Completeness**

*For any* outsourced processing record, it must include process type, supplier ID, quantity, and cost information.

**Validates: Requirements 5.1, 5.2, 5.3**

**Property 15: Outsourced Processing Cost Update**

*For any* outsourced processing record, the actual cost should be updatable, and the updated value should be persisted.

**Validates: Requirements 5.4**

**Property 16: Order Cost Aggregation**

*For any* processing order, the total outsourced cost should equal the sum of all associated outsourced processing costs.

**Validates: Requirements 5.5**

**Property 17: Outsourced Processing Payment Status**

*For any* outsourced processing record, the payment status should accurately reflect whether full payment has been made based on matched payment records.

**Validates: Requirements 5.6**

**Property 18: Bank Statement Direction Recognition**

*For any* imported bank statement record, the system should correctly identify whether it is a credit (income) or debit (expense) transaction.

**Validates: Requirements 6.1**

**Property 19: Auto-Matching Accuracy**

*For any* bank statement record that matches an existing order or supplier with high confidence (>95%), the system should automatically create a reconciliation match.

**Validates: Requirements 6.2, 6.3**

**Property 20: Unmatched Transaction Tracking**

*For any* bank statement record that cannot be auto-matched, it should appear in the unmatched transactions list.

**Validates: Requirements 6.4, 6.6**

**Property 21: Manual Matching Suggestions**

*For any* unmatched bank statement record, the system should provide a list of candidate orders or suppliers based on amount and counterparty name similarity.

**Validates: Requirements 6.5**

**Property 22: Transaction Date Recording**

*For any* transaction (order, payment, expense), it must have a date field that records when the transaction actually occurred.

**Validates: Requirements 7.1**

**Property 23: Transaction Date Editability**

*For any* transaction, the date should be editable by the user, and the updated date should be persisted.

**Validates: Requirements 7.2**

**Property 24: Report Date-Based Aggregation**

*For any* financial report generated for a specific date range, only transactions with dates within that range should be included in the calculations.

**Validates: Requirements 7.3, 7.4**

**Property 25: Cross-Month Transaction Attribution**

*For any* transaction dated in a specific month, it should be attributed to that month's financial period regardless of when it was entered into the system.

**Validates: Requirements 7.5**

**Property 26: Demo Data Flagging**

*For any* record created as demo data, it should have a flag or marker that distinguishes it from real production data.

**Validates: Requirements 8.6**

**Property 27: Report Period Selection**

*For any* financial report, the user should be able to specify a date range, and the report should only include data from that period.

**Validates: Requirements 9.4**

**Property 28: Financial Indicator Calculation**

*For any* financial report, calculated indicators (e.g., profit margin, current ratio) should follow standard accounting formulas and be mathematically correct.

**Validates: Requirements 9.5**

**Property 29: User Preference Persistence**

*For any* user preference or frequently-used option, it should be saved and automatically applied in future sessions.

**Validates: Requirements 11.2**

**Property 30: Template Reusability**

*For any* template created for a repetitive task, it should be saveable and reusable for creating similar records with pre-filled data.

**Validates: Requirements 11.4**

**Property 31: Auto-Fill Functionality**

*For any* form field with auto-fill enabled, the system should suggest values based on historical data or context.

**Validates: Requirements 11.5**

**Property 32: Import Data Validation**

*For any* data import operation, records with invalid formats or missing required fields should be rejected with descriptive error messages.

**Validates: Requirements 12.4**

**Property 33: Auto-Save Functionality**

*For any* user input in a form, the data should be automatically persisted to prevent data loss.

**Validates: Requirements 13.1**

**Property 34: Backup and Restore Integrity**

*For any* backup created and subsequently restored, the restored data should be identical to the original data at the time of backup.

**Validates: Requirements 13.5**

**Property 35: Audit Trail Completeness**

*For any* data modification operation, an audit log entry should be created recording what was changed, when, and by whom.

**Validates: Requirements 13.6**


## Error Handling

### 错误分类

系统采用分层错误处理策略：

**1. 输入验证错误 (Validation Errors)**
- 必填字段缺失
- 数据格式不正确（日期、金额、数量）
- 数值超出合理范围
- 处理方式：在数据输入时立即提示，阻止无效数据进入系统

**2. 业务逻辑错误 (Business Logic Errors)**
- 订单金额与收款金额不匹配
- 账户余额不足
- 重复的订单编号
- 处理方式：提供清晰的错误消息和纠正建议

**3. 数据一致性错误 (Data Consistency Errors)**
- 引用的客户/供应商不存在
- 关联的订单已被删除
- 对账匹配的金额不平衡
- 处理方式：事务性操作，失败时回滚

**4. 系统错误 (System Errors)**
- 文件读写失败
- 数据解析错误
- 内存不足
- 处理方式：记录详细日志，提供用户友好的错误消息，尝试自动恢复

### 错误恢复机制

**自动保存**: 每次数据修改后自动保存，防止数据丢失

**撤销功能**: 支持撤销最近的操作（基于审计日志）

**数据备份**: 定期自动备份，支持手动备份和恢复

**导入预览**: 导入数据前先预览和验证，避免批量错误

### 用户友好的错误提示

所有错误消息应该：
- 使用简单易懂的语言（避免技术术语）
- 明确指出问题所在
- 提供具体的解决建议
- 提供相关帮助文档链接

示例：
```
❌ 错误：订单金额计算不正确
📝 问题：数量 (100) × 单价 (5.5) = 550，但您输入的总金额是 500
💡 建议：请检查数量或单价是否正确，或点击"自动计算"按钮
```

## Testing Strategy

系统采用双重测试策略，结合单元测试和基于属性的测试（Property-Based Testing）。

### 单元测试 (Unit Tests)

单元测试用于验证：
- 具体的业务场景示例
- 边界条件和特殊情况
- 错误处理逻辑
- 集成点

**测试框架**: pytest

**覆盖范围**:
- 每个核心业务组件
- 关键的数据转换函数
- 错误处理路径

### 基于属性的测试 (Property-Based Tests)

基于属性的测试用于验证：
- 通用的正确性属性（如本文档中定义的35个属性）
- 跨多种输入的系统行为
- 数据不变量

**测试框架**: Hypothesis (Python)

**配置**:
- 每个属性测试至少运行 100 次迭代
- 使用随机生成的测试数据
- 每个测试必须标注对应的设计属性

**标注格式**:
```python
# Feature: oxidation-factory-workflow-optimization, Property 1: Pricing Unit Support and Calculation
@given(
    pricing_unit=st.sampled_from(list(PricingUnit)),
    quantity=st.decimals(min_value=Decimal('0.01'), max_value=Decimal('10000')),
    unit_price=st.decimals(min_value=Decimal('0.01'), max_value=Decimal('1000'))
)
def test_order_total_calculation(pricing_unit, quantity, unit_price):
    order = create_order(pricing_unit, quantity, unit_price)
    assert order.total_amount == quantity * unit_price
```

### 测试优先级

**高优先级** (必须测试):
- 财务计算（订单金额、账户余额、报表数据）
- 数据持久化和恢复
- 对账匹配逻辑

**中优先级** (应该测试):
- 工作流引擎
- 数据导入导出
- 自动分类

**低优先级** (可选测试):
- UI交互
- 提示和建议
- 演示数据生成

### 集成测试

端到端工作流测试：
1. 早晨准备工作流：查看工作台 → 检查超期款项 → 查看待处理订单
2. 订单处理工作流：创建订单 → 记录外发加工 → 记录收款 → 更新状态
3. 对账工作流：导入银行流水 → 自动匹配 → 手动匹配 → 生成报告
4. 报表生成工作流：选择期间 → 生成报表 → 导出Excel

### 测试数据管理

- 使用独立的测试数据目录
- 每个测试用例使用隔离的数据
- 测试后自动清理
- 提供标准的测试数据集（包含各种业务场景）

