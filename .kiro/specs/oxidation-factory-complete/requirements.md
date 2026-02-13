# 需求文档：V1.7 氧化加工厂智能财务助手完整版

## 简介

V1.7 氧化加工厂智能财务助手完整版是一个专为小型氧化加工厂设计的全功能财务管理系统。系统整合了行业特色功能、智能工作流优化和实用核心功能,为非专业IT背景的小白会计提供简单易用、高效智能的财务管理解决方案。

本系统基于V1.5工作流优化版和V1.6实用增强版的成功经验,针对氧化加工厂的业务特点进行深度定制,实现了行业功能与智能化的完美结合。

## 术语表

- **System**: V1.7 氧化加工厂智能财务助手完整版
- **Small_Accountant**: 非专业IT背景的小白会计用户
- **Processing_Order**: 加工订单,记录客户来料加工的详细信息
- **Pricing_Unit**: 计价单位(件、条、只、个、米长、米重、平方)
- **Outsourced_Processing**: 外发加工(喷砂、拉丝、抛光等工序)
- **Business_Partner**: 往来单位(客户或供应商)
- **Bank_Account**: 银行账户(G银行有票、N银行/微信现金账户)
- **Reconciliation**: 对账,支持一对多、多对一的灵活匹配
- **Smart_Dashboard**: 智能工作台,显示今日优先任务
- **Workflow_Engine**: 工作流引擎,组织日常工作流程
- **Report_Generator**: 智能报表生成器
- **Reminder_System**: 智能提醒系统
- **Import_Engine**: Excel批量导入引擎
- **Industry_Classifier**: 行业费用分类器

## 核心需求

### 需求组 A: 氧化加工厂行业特色功能

#### 需求 A1: 多种计价单位支持

**用户故事**: 作为小白会计,我需要系统支持氧化加工行业的多种计价方式,以便准确记录不同类型的加工订单。

**验收标准**:
1. THE System SHALL 支持以下计价单位:件、条、只、个、米长、米重、平方
2. WHEN 创建加工订单时,THE System SHALL 允许选择计价单位并自动计算总金额
3. THE System SHALL 在报表中按计价单位分类统计收入
4. THE System SHALL 提供计价单位的示例数据和使用说明

#### 需求 A2: 外发加工管理

**用户故事**: 作为小白会计,我需要记录和管理外发加工费用,以便准确核算成本。

**验收标准**:
1. THE System SHALL 支持记录外发加工工序:喷砂、拉丝、抛光
2. THE System SHALL 关联外发加工费用到对应的加工订单
3. THE System SHALL 生成外发加工成本统计报表
4. THE System SHALL 按工序类型和供应商统计外发成本

#### 需求 A3: 行业专用费用分类

**用户故事**: 作为小白会计,我需要系统自动识别氧化加工行业的常见费用,减少手动分类工作。

**验收标准**:
1. THE System SHALL 预置氧化加工行业费用分类规则
2. THE System SHALL 支持收入分类:加工费收入、其他收入
3. THE System SHALL 支持支出分类:
   - 原材料:三酸、片碱、亚钠、色粉、除油剂
   - 挂具
   - 外发加工费:喷砂、拉丝、抛光
   - 房租、水电费、工资、日常费用、其他支出
4. WHEN 导入银行流水时,THE System SHALL 自动分类并标记低置信度项目

#### 需求 A4: 灵活对账功能

**用户故事**: 作为小白会计,我需要灵活的对账功能,因为客户和供应商的付款经常不是一一对应的。

**验收标准**:
1. THE System SHALL 支持一笔银行流水关联多个订单(客户合并付款)
2. THE System SHALL 支持多笔银行流水关联一个订单(客户分批付款)
3. THE System SHALL 显示往来单位的未对账余额
4. THE System SHALL 自动更新订单的已收款/已付款金额
5. THE System SHALL 记录对账历史并支持撤销操作

#### 需求 A5: 银行账户分类管理

**用户故事**: 作为小白会计,我需要区分不同银行账户的用途,以便更好地管理资金流。

**验收标准**:
1. THE System SHALL 支持配置多个银行账户
2. THE System SHALL 标记G银行账户为"有票据"
3. THE System SHALL 标记N银行和微信为"现金账户"
4. THE System SHALL 在报表中按账户分别统计收支
5. THE System SHALL 在对账时显示交易所属的银行账户

### 需求组 B: 智能工作流和自动化

#### 需求 B1: 智能工作台

**用户故事**: 作为小白会计,我希望每天打开系统就能看到今天要做的事情,不用自己去找。

**验收标准**:
1. WHEN 用户早上启动系统,THE System SHALL 显示今日优先任务和待办事项
2. THE System SHALL 显示超期未收款提醒
3. THE System SHALL 显示即将到期的税务申报
4. THE System SHALL 显示现金流预警(如有)
5. THE System SHALL 提供快捷操作入口

#### 需求 B2: 日常工作流程

**用户故事**: 作为小白会计,我希望系统能引导我完成日常工作,不用记住复杂的操作步骤。

**验收标准**:
1. THE System SHALL 提供预定义工作流:早晨准备、交易录入、日终汇总
2. WHEN 完成一个步骤,THE System SHALL 自动建议下一步操作
3. THE System SHALL 在工作流中集成相关功能
4. THE System SHALL 记住用户的自定义工作流偏好

#### 需求 B3: 一键操作

**用户故事**: 作为小白会计,我希望常用操作能一键完成,不要点很多次。

**验收标准**:
1. THE System SHALL 提供一键录入常见交易类型
2. THE System SHALL 支持批量处理相似项目
3. THE System SHALL 自动完成验证、计算和保存
4. THE System SHALL 提供用户最常用的10个操作快捷方式

#### 需求 B4: 智能学习和建议

**用户故事**: 作为小白会计,我希望系统能记住我的习惯,越用越顺手。

**验收标准**:
1. THE System SHALL 根据历史记录智能建议交易信息
2. THE System SHALL 学习用户的修正并改进未来建议
3. THE System SHALL 识别重复模式并建议自动化
4. THE System SHALL 根据使用频率调整菜单优先级

### 需求组 C: 实用核心功能

#### 需求 C1: 智能报表生成

**用户故事**: 作为小白会计,我需要一键生成各种报表,给老板、税务局和银行看。

**验收标准**:
1. THE System SHALL 生成管理报表:收支对比图、利润趋势图、客户排名
2. THE System SHALL 生成税务报表:增值税申报表、所得税申报表
3. THE System SHALL 生成银行贷款报表:资产负债表、利润表、现金流量表
4. THE System SHALL 生成氧化加工行业专用报表:
   - 加工费收入明细表(按客户、计价单位、时间)
   - 外发加工成本统计表(按工序类型和供应商)
   - 原材料消耗统计表(按材料类型)
5. THE System SHALL 输出格式化的Excel文件,包含图表
6. THE System SHALL 使用简单易懂的模板,不需要专业会计知识

#### 需求 C2: 智能提醒系统

**用户故事**: 作为小白会计,我需要及时提醒,避免忘记重要事项造成损失。

**验收标准**:
1. THE System SHALL 在税务申报截止日前7天、3天、1天、当天发送提醒
2. THE System SHALL 在应付账款到期前发送提醒
3. THE System SHALL 在应收账款逾期30天、60天、90天发送提醒并生成催款函
4. THE System SHALL 在预测现金流不足时发送预警
5. THE System SHALL 支持桌面通知和企业微信通知
6. THE System SHALL 允许配置提醒时间和通知渠道

#### 需求 C3: 快速对账助手

**用户故事**: 作为小白会计,我需要快速完成银行对账和客户对账,减少错误和时间。

**验收标准**:
1. WHEN 导入银行流水Excel,THE System SHALL 自动匹配系统记录并标记差异
2. THE System SHALL 生成客户对账单Excel,可直接发给客户
3. THE System SHALL 自动核对采购订单与付款记录
4. THE System SHALL 生成差异报告,详细列出不匹配项
5. THE System SHALL 提供简单界面,不需要复杂算法知识

#### 需求 C4: Excel批量导入增强

**用户故事**: 作为小白会计,我需要批量导入历史数据,避免慢慢手工录入。

**验收标准**:
1. THE System SHALL 智能识别Excel列名和数据结构
2. THE System SHALL 支持批量导入交易记录(收入、支出、订单)
3. THE System SHALL 支持批量导入往来单位(客户、供应商)
4. THE System SHALL 提供预览和验证界面,导入前可修正错误
5. THE System SHALL 支持撤销导入操作
6. THE System SHALL 支持常见Excel格式,不要求严格模板

### 需求组 D: 小白友好设计

#### 需求 D1: 简化操作界面

**用户故事**: 作为小白会计,我需要简单易懂的界面,不要太多专业术语。

**验收标准**:
1. THE System SHALL 使用简单中文术语,避免专业会计术语
2. THE System SHALL 每次最多显示5个主要选项
3. THE System SHALL 提供分步操作向导
4. THE System SHALL 在关键操作点提供帮助提示
5. THE System SHALL 提供清晰的错误信息和解决建议

#### 需求 D2: 示例数据和模板

**用户故事**: 作为小白会计,我需要参考示例,照着做就能学会。

**验收标准**:
1. THE System SHALL 提供氧化加工厂的完整示例数据集
2. THE System SHALL 提供订单录入模板
3. THE System SHALL 提供银行流水导入模板
4. THE System SHALL 提供往来单位信息模板
5. THE System SHALL 支持一键加载示例数据用于学习
6. THE System SHALL 提供"参考示例"功能

#### 需求 D3: 操作教程和帮助

**用户故事**: 作为小白会计,我需要详细的使用说明,遇到问题能快速找到答案。

**验收标准**:
1. THE System SHALL 提供快速开始指南
2. THE System SHALL 提供功能使用说明
3. THE System SHALL 提供常见问题解答
4. THE System SHALL 在首次使用时显示操作演示
5. THE System SHALL 提供视频教程链接(如有)

### 需求组 E: 数据安全和性能

#### 需求 E1: 自动备份

**用户故事**: 作为小白会计,我需要系统自动备份数据,防止数据丢失。

**验收标准**:
1. THE System SHALL 每日自动备份数据
2. THE System SHALL 在关键操作前自动创建备份点
3. THE System SHALL 保留最近30天的备份文件
4. THE System SHALL 支持手动触发备份
5. THE System SHALL 支持从备份恢复数据

#### 需求 E2: 性能要求

**用户故事**: 作为小白会计,我需要系统响应快速,不要等太久。

**验收标准**:
1. THE System SHALL 在200毫秒内响应常用操作
2. THE System SHALL 在3秒内完成银行流水导入(100条以内)
3. THE System SHALL 在5秒内生成任意报表
4. THE System SHALL 支持至少10000条历史交易记录
5. THE System SHALL 支持至少1000个往来单位

#### 需求 E3: 数据验证

**用户故事**: 作为小白会计,我需要系统帮我检查数据错误,确保准确性。

**验收标准**:
1. THE System SHALL 验证必填字段完整性
2. THE System SHALL 验证金额格式和合理性
3. THE System SHALL 检测重复的银行流水记录
4. THE System SHALL 识别异常数据并生成报告
5. THE System SHALL 支持批量修正常见错误

## 非功能性需求

### 技术约束

1. THE System SHALL 使用Python 3.8+标准库和常用库(openpyxl, pandas, matplotlib)
2. THE System SHALL 本地运行,核心功能不依赖互联网
3. THE System SHALL 仅使用企业微信webhook作为外部API
4. THE System SHALL 保持代码简单可维护
5. THE System SHALL 支持Windows操作系统

### 可用性

1. THE System SHALL 提供中文界面
2. THE System SHALL 提供命令行界面(CLI)
3. THE System SHALL 在移动端(飞书APP)正常显示(如使用飞书)
4. THE System SHALL 提供在线帮助文档

### 可维护性

1. THE System SHALL 使用模块化设计
2. THE System SHALL 提供详细的日志记录
3. THE System SHALL 使用配置文件,避免硬编码
4. THE System SHALL 提供清晰的代码文档

## 实施目标

- **开发周期**: 2-3周
- **投入产出比**: 1:15
- **目标用户**: 小型氧化加工厂的非专业IT背景会计
- **核心价值**: 简单易用、行业专用、智能高效
