# CWZS - 氧化加工厂财务系统 V2.0

> 🏭 企业级财务管理解决方案 - AI 辅助开发
> 
> **版本**: V2.0.1 | **状态**: ✅ 生产就绪

---

## ✨ V2.0.1 最新优化 (2026-02-25)

### 新增功能

| 功能 | 描述 | 状态 |
|------|------|------|
| **审计日志全覆盖** | 所有核心写操作(CREATE/UPDATE/DELETE/ALLOCATE)自动记录审计日志 | ✅ |
| **金额精度改进** | 金额字段改为TEXT存储，避免浮点精度问题 | ✅ |
| **事务支持** | 新增事务上下文管理器，支持原子性操作 | ✅ |
| **幂等性保护** | 支出/银行交易/委外加工增加重复性检查 | ✅ |
| **启动器优化** | 自动定位入口脚本，解决中文/空格文件名问题 | ✅ |

---

## 🚀 快速开始

### 1. 初始化系统

```bash
cd oxidation_finance_v20
python tools/setup_wizard.py
```

### 2. 生成示例数据

```bash
./scripts/run_full_demo.sh
```

或

```bash
python scripts/launcher_full_demo.py
```

### 3. 启动Web界面

```bash
cd oxidation_finance_v20
python web_app.py
# 浏览器访问: http://localhost:5000
```

---

## 🧪 测试验证

### 审计覆盖自检

```bash
export PYTHONPATH=/app/workspace/cw
python3 -m oxidation_finance_v20.tools.audit_self_check
```

**预期输出**:
```
Allocation result: True 付款分配成功
Audit log count: 7
Last audit: {...}
```

### 金额字段迁移

```bash
# 备份数据库
cp oxidation_finance.db oxidation_finance.db.bak

# 执行迁移
export PYTHONPATH=/app/workspace/cw
python3 oxidation_finance_v20/tools/migrate_to_text_amounts.py
```

---

## 📁 项目结构

```
CWZS/
├── oxidation_finance_v20/          # 氧化加工厂财务系统 V2.0 (主版本)
│   ├── business/                   # 业务逻辑层
│   ├── database/                    # 数据库管理
│   ├── models/                     # 数据模型
│   ├── tools/                      # 命令行工具
│   │   ├── audit_self_check.py     # 审计自检
│   │   ├── migrate_to_text_amounts.py  # 金额迁移
│   │   └── setup_wizard.py         # 初始化向导
│   ├── examples/                   # 示例数据
│   └── web_app.py                  # Web界面
├── scripts/                         # 启动脚本
│   ├── launcher_full_demo.py        # 自动启动器
│   └── run_full_demo.sh            # 一键启动
├── deprecated_versions/             # 已归档旧版本
├── AGENTS.md                       # AI开发指南
└── README.md                        # 本文档
```

---

## 🔧 核心模块

### 数据库层 (database/)

| 模块 | 功能 |
|------|------|
| `db_manager.py` | 数据库CRUD + 审计日志 + 事务管理 |
| `schema.py` | 数据表结构定义 |

### 业务层 (business/)

| 模块 | 功能 |
|------|------|
| `order_manager.py` | 订单管理 + 审计日志 |
| `finance_manager.py` | 财务管理 + 收入分配 + 审计日志 |

### 工具层 (tools/)

| 工具 | 功能 |
|------|------|
| `audit_self_check.py` | 审计覆盖自检 |
| `migrate_to_text_amounts.py` | 金额字段TEXT迁移 |
| `setup_wizard.py` | 系统初始化向导 |
| `quick_panel.py` | 快速操作面板 |

---

## 📊 技术特性

### 已实现

- ✅ 审计日志端到端覆盖
- ✅ 金额精度改进 (TEXT存储)
- ✅ 事务支持 (原子性操作)
- ✅ 幂等性保护
- ✅ SQL注入防护
- ✅ 完整类型注解
- ✅ 启动器优化

### 技术栈

- Python 3.8+ / SQLite / Flask
- pytest 测试框架
- Decimal 精确计算

---

## 📖 使用指南

### 初始化向导

```bash
cd oxidation_finance_v20
python tools/setup_wizard.py
```

### 生成示例数据

```bash
./scripts/run_full_demo.sh
```

输出示例:
```
📊 数据统计：
   客户数量: 5
   供应商数量: 5
   订单数量: 30
   收入记录: 31
   支出记录: 74
   银行交易: 105

💰 财务概况：
   总收入: ¥36,704.73
   总支出: ¥203,712.08
   利润: ¥-167,007.34
```

### 审计自检

```bash
export PYTHONPATH=/app/workspace/cw
python3 -m oxidation_finance_v20.tools.audit_self_check
```

---

## 🔄 版本历史

| 版本 | 日期 | 说明 |
|------|------|------|
| V2.0.1 | 2026-02-25 | 审计日志全覆盖、金额精度改进、事务支持、幂等性保护 |
| V2.0 | 2026-02 | 初始版本 |

---

## 🤝 AI 协作开发

本项目采用 AI 辅助开发模式，遵循以下规范：

1. **需求分析** - AI 协助梳理业务需求
2. **代码生成** - AI 辅助编写核心逻辑
3. **测试验证** - AI 辅助生成测试用例
4. **文档维护** - AI 协助维护文档

详见 `AGENTS.md` 了解 AI 助手开发规范。

---

## 📄 提交规范

使用 [Conventional Commits](https://www.conventionalcommits.org/) 格式：

```
type(scope): brief description

Detailed explanation if needed (wrap at 72 chars)
```

**Types**:
- `feat:` 新功能
- `fix:` Bug修复
- `docs:` 文档
- `test:` 测试
- `refactor:` 重构
- `chore:` 维护

---

## ⚠️ 重要规则

1. **始终先读 `AGENTS.md`** - 这是项目黑匣子
2. **运行测试** - 任何更改后必须运行测试
3. **更新记忆核心** - 重大变更后更新 `AGENTS.md`
4. **不要删除历史** - 旧版本移动到 `deprecated_versions/`

---

## 📞 支持

- GitHub Issues: [提交问题](https://github.com/tel9980/cw/issues)
- 查看文档：`oxidation_finance_v20/docs/`

---

**最后更新**: 2026-02-25

**AI 助手**: Kimi (OpenCode)

---

💼 **氧化加工厂财务系统 V2.0** - 让财务管理变简单
