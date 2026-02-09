# 需求文档：氧化加工厂财务助手系统优化

## 简介

本项目旨在优化现有的飞书财务助手系统，使其更好地适应氧化加工厂的业务特点。系统需要支持多样化的计价方式、灵活的往来对账、行业专用的费用分类，并为小白会计提供简单易用的操作界面。

## 术语表

- **系统 (System)**: 基于飞书多维表格的财务助手系统
- **往来单位 (Business_Partner)**: 客户或供应商
- **加工费 (Processing_Fee)**: 客户支付的来料氧化加工服务费用
- **外发加工 (Outsourced_Processing)**: 委托外部供应商进行的喷砂、拉丝、抛光等工序
- **对账 (Reconciliation)**: 将银行流水与业务往来进行匹配的过程
- **AI分类器 (AI_Classifier)**: 使用GLM-4模型自动分类交易的组件
- **多维表格 (Multidimensional_Table)**: 飞书提供的数据存储和展示工具
- **计价单位 (Pricing_Unit)**: 加工费计算的度量单位（件、条、只、个、米长、米重、平方）

## 需求

### 需求 1：支持氧化加工行业专用计价单位

**用户故事**：作为会计，我需要系统支持多种计价单位，以便准确记录不同类型的加工订单。

#### 验收标准

1. THE System SHALL 支持以下计价单位：件、条、只、个、米长、米重、平方
2. WHEN 创建加工订单记录时，THE System SHALL 允许用户选择适当的计价单位
3. WHEN 计算加工费时，THE System SHALL 根据选定的计价单位和数量自动计算总金额
4. THE System SHALL 在报表中按计价单位分类统计加工费收入

### 需求 2：优化往来对账逻辑

**用户故事**：作为会计，我需要灵活的对账功能，因为客户和供应商的付款经常不是一一对应的。

#### 验收标准

1. WHEN 客户多笔订单合并付款时，THE System SHALL 支持一笔银行流水关联多个订单
2. WHEN 客户分批支付一个订单时，THE System SHALL 支持多笔银行流水关联同一订单
3. WHEN 进行对账操作时，THE System SHALL 显示往来单位的未对账余额
4. WHEN 对账完成后，THE System SHALL 自动更新订单的已收款/已付款金额
5. THE System SHALL 支持手动调整对账关系
6. THE System SHALL 记录每次对账操作的历史记录

### 需求 3：预置氧化加工行业费用分类规则

**用户故事**：作为会计，我需要系统自动识别常见的费用类型，以减少手动分类的工作量。

#### 验收标准

1. THE AI_Classifier SHALL 预置氧化加工行业的费用分类规则
2. THE System SHALL 支持以下收入分类：加工费收入、其他收入
3. THE System SHALL 支持以下支出分类：原材料（三酸、片碱、亚钠、色粉、除油剂）、挂具、外发加工费（喷砂、拉丝、抛光）、房租、水电费、工资、日常费用、其他支出
4. WHEN 导入银行流水时，THE AI_Classifier SHALL 根据交易描述和往来单位自动分类
5. WHEN AI分类置信度低于阈值时，THE System SHALL 标记为待人工确认
6. THE System SHALL 允许用户修正AI分类结果并学习优化

### 需求 4：往来单位别名智能管理

**用户故事**：作为会计，我需要系统自动识别同一往来单位的不同名称，以便准确统计往来账。

#### 验收标准

1. THE System SHALL 支持为每个往来单位配置多个别名
2. WHEN 导入银行流水时，THE System SHALL 根据别名自动匹配往来单位
3. WHEN 发现新的潜在别名时，THE System SHALL 提示用户确认是否添加
4. THE System SHALL 支持批量导入往来单位及其别名
5. THE System SHALL 在往来单位管理界面显示所有别名

### 需求 5：生成行业专用财务报表

**用户故事**：作为会计，我需要查看氧化加工行业特定的财务报表，以便了解经营状况。

#### 验收标准

1. THE System SHALL 生成加工费收入明细表，按客户、计价单位、时间维度统计
2. THE System SHALL 生成外发加工成本统计表，按工序类型（喷砂、拉丝、抛光）和供应商统计
3. THE System SHALL 生成原材料消耗统计表，按材料类型（三酸、片碱、亚钠、色粉、除油剂）统计
4. THE System SHALL 生成往来单位对账表，显示应收应付余额
5. THE System SHALL 生成月度利润表，包含收入、成本、费用的汇总
6. WHEN 生成报表时，THE System SHALL 支持自定义时间范围
7. THE System SHALL 支持将报表导出为Excel格式

### 需求 6：简化日常操作流程

**用户故事**：作为小白会计，我需要简单易懂的操作流程，以便快速完成日常财务工作。

#### 验收标准

1. THE System SHALL 提供分步操作向导，引导用户完成常见任务
2. THE System SHALL 在关键操作点提供操作提示和帮助文档
3. WHEN 用户首次使用功能时，THE System SHALL 显示操作演示或教程
4. THE System SHALL 提供快捷操作入口，减少点击次数
5. THE System SHALL 使用简单易懂的术语，避免专业会计术语
6. THE System SHALL 在错误发生时提供明确的错误信息和解决建议

### 需求 7：提供示例数据和操作模板

**用户故事**：作为小白会计，我需要参考示例数据和模板，以便理解如何正确使用系统。

#### 验收标准

1. THE System SHALL 提供氧化加工厂的示例数据集，包含典型的收入和支出场景
2. THE System SHALL 提供订单录入模板，预填充常用字段
3. THE System SHALL 提供银行流水导入模板，说明各列的含义
4. THE System SHALL 提供往来单位信息模板，包含别名配置示例
5. WHEN 用户创建新记录时，THE System SHALL 提供"参考示例"功能
6. THE System SHALL 提供一键加载示例数据的功能，用于测试和学习

### 需求 8：优化银行账户管理

**用户故事**：作为会计，我需要区分不同银行账户的用途，以便更好地管理资金流。

#### 验收标准

1. THE System SHALL 支持配置多个银行账户
2. THE System SHALL 为每个账户设置属性：账户名称、银行名称、账户类型（对公/现金账户）、是否有票据
3. WHEN 导入银行流水时，THE System SHALL 自动识别所属账户
4. THE System SHALL 在报表中按账户分别统计收支
5. THE System SHALL 支持标记G银行账户为"有票据"，N银行和微信为"现金账户"
6. THE System SHALL 在对账时显示交易所属的银行账户

### 需求 9：自动备份和数据安全

**用户故事**：作为会计，我需要系统自动备份数据，以防止数据丢失。

#### 验收标准

1. THE System SHALL 每日自动备份多维表格数据
2. THE System SHALL 在关键操作（批量导入、批量删除）前自动创建备份点
3. THE System SHALL 保留最近30天的备份文件
4. THE System SHALL 支持手动触发备份
5. THE System SHALL 支持从备份恢复数据
6. WHEN 备份失败时，THE System SHALL 发送通知给管理员

### 需求 10：文件监听和自动导入

**用户故事**：作为会计，我希望将银行流水文件放到指定文件夹后自动导入，以减少手动操作。

#### 验收标准

1. THE System SHALL 监听指定文件夹中的新Excel文件
2. WHEN 检测到新文件时，THE System SHALL 自动解析并导入银行流水
3. WHEN 导入成功后，THE System SHALL 将文件移动到已处理文件夹
4. WHEN 导入失败时，THE System SHALL 将文件移动到错误文件夹并记录错误信息
5. THE System SHALL 支持配置监听文件夹路径
6. THE System SHALL 在导入过程中显示进度和结果摘要

### 需求 11：AI分类优化和学习

**用户故事**：作为会计，我希望AI分类越用越准确，减少人工修正的次数。

#### 验收标准

1. WHEN 用户修正AI分类结果时，THE System SHALL 记录修正信息
2. THE AI_Classifier SHALL 定期使用修正数据优化分类规则
3. THE System SHALL 显示AI分类的置信度分数
4. WHEN 置信度低于80%时，THE System SHALL 标记为待确认
5. THE System SHALL 提供分类准确率统计报表
6. THE System SHALL 支持手动触发AI模型重新训练

### 需求 12：数据验证和完整性检查

**用户故事**：作为会计，我需要系统帮我检查数据错误，以确保财务数据的准确性。

#### 验收标准

1. WHEN 导入数据时，THE System SHALL 验证必填字段的完整性
2. WHEN 导入数据时，THE System SHALL 验证金额字段的格式和合理性
3. WHEN 导入数据时，THE System SHALL 检测重复的银行流水记录
4. THE System SHALL 提供数据完整性检查功能，识别异常数据
5. WHEN 发现数据异常时，THE System SHALL 生成异常报告
6. THE System SHALL 支持批量修正常见的数据错误

## 非功能性需求

### 性能需求

1. THE System SHALL 在3秒内完成单次银行流水导入（100条记录以内）
2. THE System SHALL 在5秒内生成任意财务报表
3. THE System SHALL 支持至少10000条历史交易记录的查询和统计

### 可用性需求

1. THE System SHALL 提供中文界面
2. THE System SHALL 在移动端（飞书APP）正常显示和操作
3. THE System SHALL 提供在线帮助文档

### 兼容性需求

1. THE System SHALL 兼容飞书开放平台最新API版本
2. THE System SHALL 支持Excel 2007及以上版本的文件格式
3. THE System SHALL 在Python 3.8及以上版本运行

### 可维护性需求

1. THE System SHALL 使用模块化设计，便于功能扩展
2. THE System SHALL 提供详细的日志记录，便于问题排查
3. THE System SHALL 提供配置文件，避免硬编码
