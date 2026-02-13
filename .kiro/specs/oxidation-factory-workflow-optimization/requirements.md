# Requirements Document

## Introduction

本文档定义了氧化加工厂小白会计工作流程优化系统的需求。该系统旨在帮助不具备专业会计背景的小会计人员高效完成日常会计工作，包括订单管理、收支记录、对账、报表生成等核心业务流程。

## Glossary

- **System**: 氧化加工厂会计工作流程优化系统
- **User**: 使用系统的小白会计人员
- **Processing_Order**: 氧化加工订单，包含客户来料的加工信息
- **Processing_Fee**: 氧化加工费用，可按件/条/只/个、米长、米重、平方计价
- **Outsourced_Processing**: 委外加工，指喷砂、拉丝、抛光等工序的外包
- **Payment_Record**: 付款记录，包括收款和付款
- **Bank_Account**: 银行账户，包括G银行（有票）、N银行（现金性质）、微信
- **Reconciliation**: 对账，匹配收付款与订单/供应商的关系
- **Expense_Category**: 支出类别，包括房租、水电费、三酸、片碱、亚钠、色粉、除油剂、挂具、外发加工费用、日常费用、工资
- **Financial_Report**: 财务报表，包括资产负债表、利润表、现金流量表等

## Requirements

### Requirement 1: 多样化加工费计价管理

**User Story:** 作为小白会计，我需要系统支持多种计价方式，以便准确记录不同类型的加工订单费用。

#### Acceptance Criteria

1. WHEN 创建加工订单时，THE System SHALL 支持按件/条/只/个计价方式
2. WHEN 创建加工订单时，THE System SHALL 支持按米长计价方式
3. WHEN 创建加工订单时，THE System SHALL 支持按米重计价方式
4. WHEN 创建加工订单时，THE System SHALL 支持按平方计价方式
5. WHEN 输入订单数量和单价时，THE System SHALL 自动计算总加工费
6. WHEN 订单包含多个计价项目时，THE System SHALL 正确汇总总费用

### Requirement 2: 灵活的收付款管理

**User Story:** 作为小白会计，我需要灵活记录收付款，因为客户付款和供应商付款不是一一对应的。

#### Acceptance Criteria

1. WHEN 记录客户付款时，THE System SHALL 允许一次付款关联多个订单
2. WHEN 记录客户付款时，THE System SHALL 允许一个订单分批收款
3. WHEN 记录供应商付款时，THE System SHALL 允许一次付款关联多个采购或外发加工
4. WHEN 记录供应商付款时，THE System SHALL 允许一个采购或外发加工分批付款
5. WHEN 存在未完全匹配的收付款时，THE System SHALL 显示待对账金额
6. THE System SHALL 支持手动调整收付款与订单的匹配关系

### Requirement 3: 多账户资金管理

**User Story:** 作为小白会计，我需要区分不同银行账户和支付方式，以便准确追踪资金流向。

#### Acceptance Criteria

1. THE System SHALL 支持G银行账户管理（标记为有票账户）
2. THE System SHALL 支持N银行账户管理（标记为现金性质账户）
3. THE System SHALL 支持微信账户管理（标记为现金性质账户）
4. WHEN 记录收付款时，THE System SHALL 要求选择资金账户
5. WHEN 查询账户余额时，THE System SHALL 显示各账户的实时余额
6. WHEN 生成报表时，THE System SHALL 区分有票和无票资金

### Requirement 4: 支出分类管理

**User Story:** 作为小白会计，我需要按类别记录各项支出，以便进行成本分析和报表生成。

#### Acceptance Criteria

1. THE System SHALL 支持预定义的支出类别：房租、水电费、三酸、片碱、亚钠、色粉、除油剂、挂具、外发加工费用、日常费用、工资
2. WHEN 记录支出时，THE System SHALL 要求选择支出类别
3. THE System SHALL 允许用户添加自定义支出类别
4. WHEN 查询支出时，THE System SHALL 支持按类别筛选
5. WHEN 生成报表时，THE System SHALL 按类别汇总支出金额

### Requirement 5: 委外加工流程管理

**User Story:** 作为小白会计，我需要追踪委外加工的费用和进度，以便准确核算成本。

#### Acceptance Criteria

1. WHEN 创建委外加工记录时，THE System SHALL 记录工序类型（喷砂、拉丝、抛光）
2. WHEN 创建委外加工记录时，THE System SHALL 记录供应商信息
3. WHEN 创建委外加工记录时，THE System SHALL 记录加工数量和费用
4. WHEN 委外加工完成时，THE System SHALL 允许记录实际费用
5. WHEN 关联订单时，THE System SHALL 将委外加工费用计入订单成本
6. THE System SHALL 显示委外加工的付款状态

### Requirement 6: 智能对账辅助

**User Story:** 作为小白会计，我需要系统帮助我完成对账工作，因为我不熟悉复杂的对账流程。

#### Acceptance Criteria

1. WHEN 导入银行流水时，THE System SHALL 自动识别收付款方向
2. WHEN 导入银行流水时，THE System SHALL 尝试自动匹配已有订单或供应商
3. WHEN 自动匹配成功时，THE System SHALL 标记为已对账
4. WHEN 自动匹配失败时，THE System SHALL 提示用户手动匹配
5. WHEN 手动匹配时，THE System SHALL 提供候选订单或供应商列表
6. THE System SHALL 显示未对账的收付款列表

### Requirement 7: 按实际发生记账

**User Story:** 作为小白会计，我需要按实际发生时间记账，以便准确反映财务状况。

#### Acceptance Criteria

1. WHEN 记录任何交易时，THE System SHALL 记录实际发生日期
2. WHEN 记录任何交易时，THE System SHALL 允许用户修改日期
3. WHEN 生成报表时，THE System SHALL 按实际发生日期统计
4. THE System SHALL 支持按日期范围查询交易记录
5. WHEN 跨月记账时，THE System SHALL 正确归属到对应月份

### Requirement 8: 模拟数据测试功能

**User Story:** 作为小白会计，我需要使用模拟数据练习操作，以便在正式使用前熟悉系统。

#### Acceptance Criteria

1. THE System SHALL 提供生成模拟数据的功能
2. WHEN 生成模拟数据时，THE System SHALL 创建典型的加工订单
3. WHEN 生成模拟数据时，THE System SHALL 创建典型的收付款记录
4. WHEN 生成模拟数据时，THE System SHALL 创建典型的支出记录
5. THE System SHALL 允许清除模拟数据
6. THE System SHALL 明确区分模拟数据和真实数据

### Requirement 9: 会计报表生成

**User Story:** 作为小白会计，我需要系统自动生成会计报表，以便完成月度和年度财务报告。

#### Acceptance Criteria

1. THE System SHALL 生成资产负债表
2. THE System SHALL 生成利润表
3. THE System SHALL 生成现金流量表
4. WHEN 生成报表时，THE System SHALL 支持选择报表期间
5. WHEN 生成报表时，THE System SHALL 自动计算各项财务指标
6. THE System SHALL 支持导出报表为Excel格式
7. THE System SHALL 支持打印报表

### Requirement 10: 依葫芦画瓢的操作指引

**User Story:** 作为小白会计，我需要清晰的操作指引，以便按照示例完成日常工作。

#### Acceptance Criteria

1. THE System SHALL 为每个主要功能提供操作指引
2. WHEN 用户首次使用功能时，THE System SHALL 显示操作提示
3. THE System SHALL 提供常见业务场景的操作示例
4. THE System SHALL 提供视频或图文教程链接
5. WHEN 用户操作错误时，THE System SHALL 提供纠正建议
6. THE System SHALL 提供快速参考卡片

### Requirement 11: 工作效率优化

**User Story:** 作为小白会计，我需要系统帮助我提高工作效率，以便快速完成日常任务。

#### Acceptance Criteria

1. THE System SHALL 提供快捷键支持
2. THE System SHALL 记住用户的常用选项
3. THE System SHALL 提供批量操作功能
4. WHEN 执行重复性任务时，THE System SHALL 提供模板功能
5. THE System SHALL 提供数据自动填充功能
6. THE System SHALL 显示任务完成进度

### Requirement 12: 数据导入导出

**User Story:** 作为小白会计，我需要方便地导入导出数据，以便与其他系统或工具协作。

#### Acceptance Criteria

1. THE System SHALL 支持从Excel导入订单数据
2. THE System SHALL 支持从Excel导入银行流水
3. THE System SHALL 支持从Excel导入支出记录
4. WHEN 导入数据时，THE System SHALL 验证数据格式
5. WHEN 导入数据时，THE System SHALL 显示导入结果摘要
6. THE System SHALL 支持导出所有数据为Excel格式
7. THE System SHALL 提供Excel模板下载

### Requirement 13: 数据安全与备份

**User Story:** 作为小白会计，我需要确保财务数据安全，以便避免数据丢失。

#### Acceptance Criteria

1. THE System SHALL 自动保存用户输入的数据
2. THE System SHALL 提供手动备份功能
3. THE System SHALL 提供自动备份功能
4. WHEN 执行备份时，THE System SHALL 显示备份进度
5. THE System SHALL 支持从备份恢复数据
6. THE System SHALL 记录数据修改历史
