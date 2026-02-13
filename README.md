# CWZS - 我的 AI 协作项目

> 🏭 氧化加工厂财务系统 V2.0 + 小会计财务管理系统
> 
> **AI 辅助开发的企业级财务管理解决方案**

---

## 🤖 AI 协作配置

**本地 AI 中转站**: `http://127.0.0.1:7861/v1`

本项目使用本地 AI 中转站进行智能化开发辅助，支持多种 AI 模型接入。

### 🤝 AI 协作开发规范

本项目采用 **AI 辅助开发模式**，遵循以下工作流程：

#### 1. 需求分析
- AI 协助梳理业务需求
- 生成任务清单和工作计划

#### 2. 代码生成
- AI 辅助编写核心逻辑
- 遵循 `AGENTS.md` 中的编码规范
- 所有代码必须通过类型检查

#### 3. 测试验证
- AI 辅助生成测试用例
- 运行 `pytest` 确保 100% 测试通过
- 使用 property-based tests 验证边缘情况

#### 4. 代码审查
- AI 执行自我审查（通过 oracle 代理）
- 检查安全漏洞（SQL注入、类型错误）
- 验证代码符合项目规范

#### 5. 文档维护
- AI 协助维护文档
- 更新 `AGENTS.md` 记忆核心
- 提交清晰规范的 commit message

### 📋 提交规范

使用 [Conventional Commits](https://www.conventionalcommits.org/) 格式：

```
type(scope): brief description

Detailed explanation if needed (wrap at 72 chars)
```

**Types**:
- `feat:` 新功能
- `fix:`  bug修复
- `docs:` 文档
- `test:` 测试
- `refactor:` 重构
- `chore:` 维护

**Example**:
```
feat(database): add customer credit limit validation

- Add credit_limit field to Customer model
- Implement validation in order creation
- Add unit tests for credit checks

Fixes #123
```

### ⚠️ 重要规则

1. **始终先读 `AGENTS.md`** - 这是项目黑匣子
2. **运行测试** - 任何更改后必须运行 `pytest`
3. **更新记忆核心** - 重大变更后更新 `AGENTS.md`
4. **不要删除历史** - 旧版本移动到 `deprecated_versions/` 而非删除

### 🔄 开发工作流

```bash
# 1. 阅读项目状态
cat AGENTS.md

# 2. 运行测试检查当前状态
cd oxidation_finance_v20
pytest

# 3. 开发 / 修复
# ... 编写代码 ...

# 4. 验证测试通过
pytest tests/test_database.py

# 5. 提交 (AI 或 人工)
git add .
git commit -m "feat(scope): description"
```

---

## 🚀 快速开始 - 氧化加工厂专版

### 方法1: 主菜单启动 (推荐)

```bash
双击: 启动_主菜单.bat
```

### 方法2: Web界面

```bash
双击: 启动_Web版.bat
# 浏览器访问: http://localhost:5000
# 默认登录: admin / admin123
```

### 方法3: 命令行

```bash
cd oxidation_finance_v20
python tools/quick_panel.py  # 今日概览
```

---

## 📁 项目结构

```
CWZS/
├── 🏭 oxidation_finance_v20/    # 氧化加工厂财务系统 V2.0 (主版本)
├── 📦 deprecated_versions/       # 已弃用的旧版本 (归档)
│   ├── small_accountant_v16/    # 小会计财务管理系统 V1.6
│   ├── oxidation_factory/       # 氧化加工厂 V1.x
│   ├── oxidation_workflow_v18/  # 工作流 V1.8
│   ├── oxidation_complete_v17/  # 完整版 V1.7
│   └── workflow_v15/            # 工作流 V1.5
├── 📄 AGENTS.md                  # AI助手开发指南 (必读!)
└── 📊 财务报表/                  # 生成的报表目录
```

---

## ✨ 氧化加工厂财务系统 V2.0 功能

| 模块 | 功能 |
|------|------|
| **订单管理** | CRUD + 5种状态追踪 |
| **收入管理** | G银行(有票) / N银行(微信) |
| **支出管理** | 12种支出类型 |
| **客户管理** | 信用额度、联系方式 |
| **报表** | 月度统计、客户排名 |
| **权限** | 4角色 × 22权限 |

### 技术栈

- Python 3.8+ / SQLite / Flask
- 35个单元测试全部通过

---

## 📦 版本说明

### 🏭 氧化加工厂专版 V2.0 (主推)

**位置**: `oxidation_finance_v20/`

**核心功能**:
- ✅ Web界面 + CLI工具
- ✅ 用户权限系统
- ✅ 操作日志审计
- ✅ 9个命令行工具
- ✅ 服务层架构
- ✅ SQL注入防护
- ✅ 完整类型注解

**快速开始**:
```bash
cd oxidation_finance_v20
python web_app.py  # 启动Web服务
```

### 📦 旧版本 (已归档)

旧版本已移动到 `deprecated_versions/` 目录，仅供历史参考：

- **小会计通用版 V1.6**: `deprecated_versions/small_accountant_v16/`
- **氧化加工厂 V1.x**: `deprecated_versions/oxidation_factory/`
- **工作流 V1.8**: `deprecated_versions/oxidation_workflow_v18/`
- **完整版 V1.7**: `deprecated_versions/oxidation_complete_v17/`
- **工作流 V1.5**: `deprecated_versions/workflow_v15/`

> **注意**: 这些版本已不再维护，建议使用 V2.0。

## 🚀 5分钟快速上手

### 1. 安装系统

```bash
# 克隆项目
git clone https://github.com/tel9980/cw.git
cd cw

# 进入V1.6目录
cd small_accountant_v16

# 安装（Windows）
install.bat

# 安装（Linux/Mac）
chmod +x install.sh
./install.sh
```

### 2. 启动系统

```bash
# Windows
start.bat

# Linux/Mac
./start.sh
```

### 3. 导入示例数据

```bash
# 生成示例数据
python examples/generate_sample_data.py

# 然后在系统中导入Excel文件
```

## 📊 主要功能

### 1. 智能报表 📈

一键生成专业财务报表：
- 管理报表：收支对比、利润趋势、客户排名
- 税务报表：增值税、所得税申报表
- 银行报表：资产负债表、利润表、现金流量表

### 2. 智能提醒 🔔

永不错过重要事项：
- 税务申报截止日期提醒
- 应付账款到期提醒
- 应收账款逾期催收（自动生成催款函）
- 现金流预警

### 3. 快速对账 🔄

轻松完成对账工作：
- 银行流水自动匹配
- 一键生成客户对账单
- 供应商对账核对

### 4. Excel导入 📥

快速导入历史数据：
- 智能识别Excel列名
- 导入前数据验证
- 支持撤销错误导入

## 💡 使用场景

### 小微企业
- 日常收支记录
- 月度财务报表
- 税务申报准备

### 个体工商户
- 简单记账
- 客户对账
- 收款提醒

### 初创公司
- 财务数据管理
- 银行贷款材料
- 投资人报表

## 📖 文档导航

- [V1.6 快速开始](small_accountant_v16/docs/快速开始指南.md)
- [V1.6 功能说明](small_accountant_v16/docs/功能使用说明.md)
- [V1.6 常见问题](small_accountant_v16/docs/常见问题解答.md)
- [V1.5 工作流文档](workflow_v15/README.md)
- [氧化厂文档](oxidation_factory/README.md)

## 🔧 系统要求

- Python 3.8+
- Windows/Linux/macOS
- 100MB 磁盘空间
- 2GB 内存（推荐）

## 📈 数据量支持

- **V1.6**: < 10,000条交易记录（JSON存储）
- **未来版本**: 支持SQLite，可处理更大数据量

## 🛡️ 数据安全

- 本地存储，数据完全掌控
- 自动配置备份（保留10个版本）
- 支持手动数据备份
- 导入撤销功能

## 🎓 学习资源

### 新手入门
1. [小白落地指南](小白落地指南.md)
2. [图解教程](图解教程_3步上手.txt)
3. [快速开始](快速开始_看这里.txt)

### 进阶使用
1. [V1.6 功能详解](small_accountant_v16/docs/功能使用说明.md)
2. [常见问题解答](small_accountant_v16/docs/常见问题解答.md)

## 🔄 版本历史

- **V1.6** (2026-02) - 实用增强版，完整功能
- **V1.5** (2026-01) - 工作流优化版
- **V1.4** (2025-12) - 增强版
- **V1.3** (2025-11) - 全能版
- **V1.2** (2025-10) - 优化版
- **V1.1** (2025-09) - 初始版本

## 🤝 贡献

欢迎提交问题和建议！

## 📄 许可证

本项目仅供学习和内部使用

## 📞 支持

- 查看文档：`small_accountant_v16/docs/`
- 查看日志：`small_accountant_v16/logs/`
- GitHub Issues: [提交问题](https://github.com/tel9980/cw/issues)

## ⚡ 快速命令

```bash
# V1.6 系统
cd small_accountant_v16
python run_cli.py              # 启动系统
python run_cli.py --status     # 查看状态
python run_cli.py --verify     # 验证数据
python run_cli.py --debug      # 调试模式

# 生成示例数据
python examples/generate_sample_data.py

# 运行测试
python -m pytest tests/ -v
```

## 🎉 开始使用

```bash
cd small_accountant_v16
install.bat  # 或 ./install.sh
start.bat    # 或 ./start.sh
```

**祝您使用愉快！** 💼

## 🤝 AI 协作开发

本项目采用 AI 辅助开发模式：

1. **需求分析** - AI 协助梳理业务需求
2. **代码生成** - AI 辅助编写核心逻辑
3. **测试验证** - AI 辅助生成测试用例
4. **文档维护** - AI 协助维护文档

详见 `AGENTS.md` 了解 AI 助手开发规范。

---

**最后更新**: 2026-02-13

**AI 助手**: Kimi (OpenCode)

---

**小会计** - 让财务管理变简单
