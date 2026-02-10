# Implementation Plan: V1.6 Small Accountant Practical Enhancement

## Overview

本实施计划将V1.6小会计实用增强版分解为可执行的编码任务。系统包含4个核心模块：智能报表生成器、智能提醒系统、快速对账助手和Excel批量导入增强。实施采用增量方式，每个模块独立开发并测试，最后集成为完整系统。

技术栈：Python 3.8+, openpyxl, pandas, matplotlib, Hypothesis (property testing)

## Tasks

- [x] 1. 项目结构和核心数据模型
  - 创建项目目录结构
  - 实现核心数据模型（TransactionRecord, Counterparty, Reminder等）
  - 设置测试框架（pytest + Hypothesis）
  - 创建配置管理模块
  - _Requirements: 5.1, 5.4_

- [x] 1.1 为数据模型编写单元测试
  - 测试数据模型的创建、验证和序列化
  - _Requirements: 5.1_

- [x] 2. 数据存储层实现
  - [x] 2.1 实现本地数据存储（使用JSON或SQLite）
    - 实现TransactionStorage类（交易记录存储）
    - 实现CounterpartyStorage类（往来单位存储）
    - 实现ReminderStorage类（提醒事项存储）
    - 实现ImportHistory类（导入历史管理）
    - _Requirements: 5.4_
  
  - [x] 2.2 为存储层编写单元测试
    - 测试CRUD操作
    - 测试数据持久化和加载
    - _Requirements: 5.4_

- [-] 3. Excel批量导入增强模块
  - [x] 3.1 实现ExcelColumnRecognizer（列识别器）
    - 实现智能列名识别算法
    - 实现列映射建议功能
    - 支持常见列名变体（如"日期"、"时间"、"交易日期"等）
    - _Requirements: 4.1, 4.6_
  
  - [ ] 3.2 为列识别器编写属性测试
    - **Property 14: Column recognition accuracy**
    - **Validates: Requirements 4.1**
  
  - [x] 3.3 实现ImportValidator（导入验证器）
    - 实现交易数据验证逻辑
    - 实现往来单位数据验证逻辑
    - 生成详细的验证错误报告
    - _Requirements: 4.4_
  
  - [x] 3.4 为导入验证器编写单元测试
    - 测试各种验证规则
    - 测试错误消息生成
    - _Requirements: 4.4_
  
  - [x] 3.5 实现ImportEngine核心功能
    - 实现preview_import()（预览导入）
    - 实现import_transactions()（导入交易记录）
    - 实现import_counterparties()（导入往来单位）
    - 实现undo_import()（撤销导入）
    - _Requirements: 4.2, 4.3, 4.4, 4.5_
  
  - [ ] 3.6 为导入引擎编写属性测试
    - **Property 15: Transaction import completeness**
    - **Validates: Requirements 4.2**
  
  - [ ] 3.7 为导入引擎编写属性测试
    - **Property 16: Counterparty import completeness**
    - **Validates: Requirements 4.3**
  
  - [ ] 3.8 为导入引擎编写属性测试
    - **Property 17: Import preview validation**
    - **Validates: Requirements 4.4**
  
  - [ ] 3.9 为导入引擎编写属性测试
    - **Property 18: Import undo round-trip**
    - **Validates: Requirements 4.5**

- [x] 4. Checkpoint - 验证导入模块
  - 确保所有导入相关测试通过
  - 手动测试Excel导入功能
  - 如有问题请询问用户

- [ ] 5. 智能报表生成器模块
  - [x] 5.1 实现ReportTemplate（报表模板管理）
    - 创建管理报表模板（收支对比、利润趋势、客户排名）
    - 创建税务报表模板（增值税、所得税申报表）
    - 创建银行贷款报表模板（资产负债表、利润表、现金流量表）
    - 实现模板加载和应用逻辑
    - _Requirements: 1.1, 1.2, 1.3, 1.5_
  
  - [-] 5.2 实现ChartGenerator（图表生成器）
    - 实现create_revenue_comparison_chart()（收支对比图）
    - 实现create_profit_trend_chart()（利润趋势图）
    - 实现create_customer_ranking_chart()（客户排名图）
    - 使用matplotlib生成图表并嵌入Excel
    - _Requirements: 1.1, 1.4_
  
  - [x] 5.3 为图表生成器编写单元测试
    - 测试各类图表生成
    - 测试图表数据正确性
    - _Requirements: 1.1, 1.4_
  
  - [x] 5.4 实现ReportGenerator核心功能
    - 实现generate_management_report()（管理报表）
    - 实现generate_tax_report()（税务报表）
    - 实现generate_bank_loan_report()（银行贷款报表）
    - 集成模板和图表生成
    - _Requirements: 1.1, 1.2, 1.3_
  
  - [ ] 5.5 为报表生成器编写属性测试
    - **Property 1: Management report completeness**
    - **Validates: Requirements 1.1**
  
  - [ ] 5.6 为报表生成器编写属性测试
    - **Property 2: Tax report structure**
    - **Validates: Requirements 1.2**
  
  - [ ] 5.7 为报表生成器编写属性测试
    - **Property 3: Bank loan report completeness**
    - **Validates: Requirements 1.3**
  
  - [ ] 5.8 为报表生成器编写属性测试
    - **Property 4: Excel output format consistency**
    - **Validates: Requirements 1.4, 1.6**

- [x] 6. Checkpoint - 验证报表生成模块
  - 确保所有报表生成测试通过
  - 手动测试生成的Excel报表格式
  - 如有问题请询问用户

- [ ] 7. 快速对账助手模块
  - [x] 7.1 实现BankStatementMatcher（银行流水匹配器）
    - 实现match_transactions()（匹配交易记录）
    - 实现identify_discrepancies()（识别差异）
    - 支持模糊匹配（金额、日期容差）
    - _Requirements: 3.1_
  
  - [ ] 7.2 为银行流水匹配器编写属性测试
    - **Property 11: Bank reconciliation matching and discrepancy detection**
    - **Validates: Requirements 3.1, 3.4**
  
  - [x] 7.3 实现ReconciliationReportGenerator（对账报告生成器）
    - 实现generate_discrepancy_report()（差异报告）
    - 实现generate_customer_statement_excel()（客户对账单）
    - 格式化Excel输出
    - _Requirements: 3.2, 3.4_
  
  - [ ] 7.4 为对账报告生成器编写属性测试
    - **Property 12: Customer statement generation**
    - **Validates: Requirements 3.2**
  
  - [x] 7.5 实现ReconciliationAssistant核心功能
    - 实现reconcile_bank_statement()（银行对账）
    - 实现generate_customer_statement()（客户对账单）
    - 实现reconcile_supplier_accounts()（供应商对账）
    - 集成匹配器和报告生成器
    - _Requirements: 3.1, 3.2, 3.3_
  
  - [ ] 7.6 为对账助手编写属性测试
    - **Property 13: Supplier reconciliation verification**
    - **Validates: Requirements 3.3**

- [x] 8. Checkpoint - 验证对账模块
  - 确保所有对账测试通过
  - 手动测试银行对账和客户对账功能
  - 如有问题请询问用户

- [ ] 9. 智能提醒系统模块
  - [x] 9.1 实现NotificationService（通知服务）
    - 实现send_desktop_notification()（桌面通知）
    - 实现send_wechat_notification()（企业微信通知）
    - 处理通知发送失败和重试逻辑
    - _Requirements: 2.5, 5.3_
  
  - [x] 9.2 为通知服务编写单元测试
    - 测试桌面通知
    - 测试企业微信webhook调用
    - 测试重试逻辑
    - _Requirements: 2.5_
  
  - [x] 9.3 实现CollectionLetterGenerator（催款函生成器）
    - 实现generate_collection_letter()（生成催款函）
    - 创建催款函模板（30天、60天、90天）
    - _Requirements: 2.3_
  
  - [x] 9.4 为催款函生成器编写单元测试
    - 测试不同逾期天数的催款函
    - 测试催款函内容正确性
    - _Requirements: 2.3_
  
  - [x] 9.5 实现ReminderSystem核心功能
    - 实现check_tax_reminders()（税务提醒检查）
    - 实现check_payable_reminders()（应付账款提醒）
    - 实现check_receivable_reminders()（应收账款提醒）
    - 实现check_cashflow_warnings()（现金流预警）
    - 实现send_reminder()（发送提醒）
    - _Requirements: 2.1, 2.2, 2.3, 2.4, 2.5_
  
  - [ ] 9.6 为提醒系统编写属性测试
    - **Property 5: Tax reminder timing**
    - **Validates: Requirements 2.1**
  
  - [ ] 9.7 为提醒系统编写属性测试
    - **Property 6: Payable reminder timing**
    - **Validates: Requirements 2.2**
  
  - [ ] 9.8 为提醒系统编写属性测试
    - **Property 7: Receivable overdue alerts**
    - **Validates: Requirements 2.3**
  
  - [ ] 9.9 为提醒系统编写属性测试
    - **Property 8: Cash flow warning prediction**
    - **Validates: Requirements 2.4**
  
  - [ ] 9.10 为提醒系统编写属性测试
    - **Property 9: Multi-channel notification delivery**
    - **Validates: Requirements 2.5**
  
  - [x] 9.11 实现ReminderScheduler（提醒调度器）
    - 实现schedule_reminder()（安排提醒）
    - 实现run_scheduled_checks()（运行定时检查）
    - 支持配置提醒时间和通知渠道
    - _Requirements: 2.6_
  
  - [ ] 9.12 为提醒调度器编写属性测试
    - **Property 10: Reminder configuration respect**
    - **Validates: Requirements 2.6**

- [x] 10. Checkpoint - 验证提醒系统模块
  - 确保所有提醒系统测试通过
  - 手动测试桌面通知和企业微信通知
  - 如有问题请询问用户

- [ ] 11. 用户界面层实现
  - [x] 11.1 实现命令行界面（CLI）
    - 创建主菜单（报表生成、提醒管理、对账、导入）
    - 实现各功能模块的CLI交互
    - 提供简单易懂的中文提示
    - _Requirements: 5.5_
  
  - [ ] 11.2 为CLI编写集成测试
    - 测试端到端工作流
    - 测试用户交互流程
    - _Requirements: 5.5_

- [ ] 12. 系统集成和错误处理
  - [x] 12.1 实现统一错误处理
    - 实现用户友好的中文错误消息
    - 实现错误日志记录
    - 实现优雅降级逻辑
    - _Requirements: 5.5_
  
  - [x] 12.2 实现配置管理
    - 实现系统配置加载和保存
    - 实现企业微信webhook配置
    - 实现提醒时间配置
    - _Requirements: 2.6, 5.3_
  
  - [x] 12.3 编写端到端集成测试
    - 测试完整工作流（导入→生成报表→发送提醒）
    - 测试错误处理和恢复
    - _Requirements: 5.4, 5.5_

- [ ] 13. 文档和部署准备
  - [x] 13.1 创建用户文档
    - 编写快速开始指南
    - 编写功能使用说明
    - 编写常见问题解答
    - _Requirements: 5.5_
  
  - [x] 13.2 创建部署脚本
    - 创建依赖安装脚本（requirements.txt）
    - 创建启动脚本
    - 创建示例配置文件
    - _Requirements: 5.1, 5.4_
  
  - [x] 13.3 创建示例数据
    - 生成示例交易记录
    - 生成示例往来单位
    - 生成示例Excel导入文件
    - _Requirements: 5.5_

- [ ] 14. Final Checkpoint - 最终验证
  - 运行所有测试（单元测试 + 属性测试）
  - 手动测试所有核心功能
  - 验证用户文档完整性
  - 确认系统满足1-2周实施周期要求
  - 如有问题请询问用户

## Notes

- 所有任务都是必需的，包括完整的测试覆盖
- 每个任务都引用了具体的需求条款，确保可追溯性
- Checkpoint任务确保增量验证，及早发现问题
- 属性测试使用Hypothesis库，每个测试至少运行100次迭代
- 单元测试聚焦于具体示例和边界情况
- 所有用户界面和错误消息使用简单中文，适合非技术背景用户
