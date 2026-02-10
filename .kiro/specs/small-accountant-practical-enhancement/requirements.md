# Requirements Document

## Introduction

V1.6 Small Accountant Practical Enhancement（小会计实用增强版）是一个专为小企业（10-50人）和非专业IT背景的会计人员设计的财务管理增强系统。系统聚焦于4个核心功能，解决小会计日常工作中最痛的问题：报表生成、提醒管理、对账核对和数据导入。系统采用简单技术栈，本地运行，快速落地，投入产出比高。

## Glossary

- **System**: V1.6 Small Accountant Practical Enhancement System
- **Report_Generator**: 智能报表生成器模块
- **Reminder_System**: 智能提醒系统模块
- **Reconciliation_Assistant**: 快速对账助手模块
- **Import_Engine**: Excel批量导入增强模块
- **Small_Accountant**: 非专业IT背景的会计人员用户
- **Transaction_Record**: 交易记录（收入、支出、订单等）
- **Bank_Statement**: 银行流水记录
- **Reconciliation_Report**: 对账报告
- **Tax_Report**: 税务报表
- **Management_Report**: 管理报表（给老板看的报表）
- **Reminder**: 提醒事项
- **Excel_File**: Excel格式的数据文件
- **WeChat_Webhook**: 企业微信webhook通知接口
- **Counterparty**: 往来单位（客户或供应商）

## Requirements

### Requirement 1: 智能报表生成器

**User Story:** As a Small_Accountant, I want to generate various reports with one click, so that I can quickly provide reports to my boss, tax authorities, and banks without needing professional knowledge.

#### Acceptance Criteria

1. WHEN a Small_Accountant requests a management report, THE Report_Generator SHALL generate revenue comparison charts, profit trend charts, and customer ranking reports
2. WHEN a Small_Accountant requests a tax report, THE Report_Generator SHALL generate VAT declaration forms and income tax declaration forms
3. WHEN a Small_Accountant requests a bank loan report, THE Report_Generator SHALL generate balance sheets, income statements, and cash flow statements
4. WHEN generating any report, THE Report_Generator SHALL output formatted Excel files with charts
5. WHEN generating reports, THE Report_Generator SHALL use predefined templates that do not require professional accounting knowledge to understand
6. THE Report_Generator SHALL support exporting reports in Excel format with embedded charts and formatting

### Requirement 2: 智能提醒系统

**User Story:** As a Small_Accountant, I want to receive timely reminders for important tasks, so that I can avoid penalties from missed tax filings and losses from overdue payments or receivables.

#### Acceptance Criteria

1. WHEN a tax filing deadline approaches, THE Reminder_System SHALL send reminders 7 days, 3 days, 1 day, and on the day before the deadline
2. WHEN an accounts payable payment is due, THE Reminder_System SHALL send a reminder before the due date
3. WHEN accounts receivable are overdue by 30, 60, or 90 days, THE Reminder_System SHALL send alerts and generate collection letters
4. WHEN cash flow is predicted to be insufficient in the next 7 days, THE Reminder_System SHALL send a cash flow warning
5. WHEN sending reminders, THE Reminder_System SHALL display desktop notifications and send WeChat notifications via WeChat_Webhook
6. THE Reminder_System SHALL allow Small_Accountants to configure reminder timing and notification channels

### Requirement 3: 快速对账助手

**User Story:** As a Small_Accountant, I want to quickly reconcile bank statements and customer accounts, so that I can reduce errors and save time on monthly reconciliation tasks.

#### Acceptance Criteria

1. WHEN a Small_Accountant imports a Bank_Statement Excel file, THE Reconciliation_Assistant SHALL automatically match it with system Transaction_Records and mark discrepancies
2. WHEN a Small_Accountant requests a customer reconciliation, THE Reconciliation_Assistant SHALL generate a customer reconciliation statement in Excel format that can be sent directly to the customer
3. WHEN a Small_Accountant requests a supplier reconciliation, THE Reconciliation_Assistant SHALL automatically verify purchase orders against payment records
4. WHEN reconciliation is complete, THE Reconciliation_Assistant SHALL generate a discrepancy report with detailed differences for review
5. THE Reconciliation_Assistant SHALL provide a simple interface that does not require complex algorithms or technical knowledge to operate

### Requirement 4: Excel批量导入增强

**User Story:** As a Small_Accountant, I want to batch import historical data from Excel files, so that I can avoid slow manual entry and quickly migrate existing data into the system.

#### Acceptance Criteria

1. WHEN a Small_Accountant uploads an Excel_File, THE Import_Engine SHALL intelligently recognize column names and data structure
2. WHEN importing transaction data, THE Import_Engine SHALL support batch import of Transaction_Records including revenue, expenses, and orders
3. WHEN importing counterparty data, THE Import_Engine SHALL support batch import of Counterparty information including customers and suppliers
4. WHEN preparing to import data, THE Import_Engine SHALL provide a preview and validation interface where errors can be corrected before import
5. WHEN data has been imported, THE Import_Engine SHALL support undo operations to reverse the import if errors are discovered
6. THE Import_Engine SHALL support common Excel formats without requiring strict template adherence

### Requirement 5: 系统技术约束

**User Story:** As a Small_Accountant with limited IT resources, I want the system to use simple, reliable technology, so that it can be easily maintained and run locally without complex dependencies.

#### Acceptance Criteria

1. THE System SHALL use Python standard library and common libraries including openpyxl, pandas, and matplotlib
2. THE System SHALL NOT require AI, OCR, voice recognition, or other complex technologies
3. THE System SHALL NOT require third-party APIs except for WeChat_Webhook
4. THE System SHALL run entirely locally without requiring cloud services or internet connectivity for core functions
5. THE System SHALL maintain simple, maintainable code that can be understood and modified by developers with basic Python knowledge
6. THE System SHALL complete implementation within 1-2 weeks with an expected ROI of 1:15
