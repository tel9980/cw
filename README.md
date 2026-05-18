# 🏭 CWZS - 氧化加工厂财务系统 V2.3

> 企业级财务管理解决方案 - AI 辅助开发 | 符合小企业会计准则

**版本**: V2.3 | **状态**: ✅ 生产就绪

---

## ✨ V2.3 最新优化 - 小企业会计准则 (2026-05-17)

### 重大改进

| 改进项 | 描述 | 状态 |
|------|------|------|
| **会计科目体系** | 完整的小企业会计准则科目体系 | ✅ |
| **会计凭证管理** | 凭证创建、审核、记账、查询 | ✅ |
| **财务报表** | 自动生成资产负债表和利润表 | ✅ |
| **成本核算** | 针对氧化加工行业的成本计算 | ✅ |
| **数据库schema** | 新增凭证表和凭证明细表 | ✅ |

---

## ✨ V2.2 优化回顾

### 重大改进

| 改进项 | 描述 | 状态 |
|------|------|------|
| **项目结构整理** | 清理根目录，迁移35个历史文件到`deprecated_versions/` | ✅ |
| **性能监控中间件** | 添加请求性能监控，自动记录响应时间 | ✅ |
| **API文档页面** | 创建完整的API文档页面，包含性能统计 | ✅ |
| **独立HTML模板** | 创建完整的模板系统，便于维护 | ✅ |
| **响应式CSS** | 现代化渐变UI，完美支持移动端 | ✅ |
| **统一启动菜单** | 创建交互式启动菜单，简化操作 | ✅ |

---

## ✨ V2.1 优化回顾

| 改进项 | 描述 | 状态 |
|------|------|------|
| **项目结构整理** | 清理根目录，迁移35个历史文件到 `deprecated_versions/` | ✅ |
| **Web应用重构** | 使用业务层（OrderManager, FinanceManager）重构web_app.py | ✅ |
| **日志系统** | 集成结构化日志记录，支持错误追踪 | ✅ |
| **错误处理** | 全局错误处理，统一错误页面 | ✅ |
| **统一启动器** | 创建交互式启动菜单，简化操作 | ✅ |

---

## 🚀 快速开始

### 方式1：使用统一启动器（推荐）

```bash
# Windows
双击 启动.bat

# Linux/Mac
python scripts/launcher.py
```

### 方式2：直接启动Web界面

```bash
cd oxidation_finance_v20
python web_app.py
# 浏览器访问: http://localhost:5000
# API文档: http://localhost:5000/api-docs
```

### 方式3：命令行模式

```bash
cd oxidation_finance_v20

# 初始化系统
python tools/setup_wizard.py

# 生成示例数据
python examples/generate_comprehensive_demo.py

# 运行测试
pytest tests/ -v
```

---

## 📁 项目结构

```
oxidation_finance_v20/          # 主项目目录
├── __init__.py               # 包初始化文件
├── web_app.py                  # Web应用（V2.3，含性能监控和API文档）
├── models/                      # 数据模型层
│   ├── business_models.py      # 业务模型定义
│   └── accounting_models.py    # 会计模型（科目、凭证、报表）
├── database/                   # 数据库层
│   ├── schema.py             # 数据表结构 + 索引（含凭证表）
│   └── db_manager.py         # 数据库管理器
├── business/                   # 业务逻辑层
│   ├── order_manager.py      # 订单管理
│   ├── finance_manager.py    # 财务管理
│   ├── voucher_manager.py    # 会计凭证管理
│   ├── report_manager.py     # 财务报表生成
│   └── cost_calculation_engine.py  # 费用计算引擎
├── config/                      # 配置管理
│   └── config_manager.py      # 配置管理器
├── utils/                      # 工具函数
│   └── data_manager.py       # 数据管理器
├── tools/                       # 业务工具
│   ├── setup_wizard.py      # 系统设置向导
│   ├── quick_panel.py       # 快速操作面板
│   ├── backup_restore.py     # 备份恢复
│   └── import_excel.py      # Excel导入
├── tests/                       # 测试套件 (426+ 测试)
├── examples/                    # 示例和演示
├── templates/                  # HTML模板
│   ├── base.html            # 基础模板
│   ├── index.html           # 首页
│   ├── orders.html         # 订单列表
│   ├── order_form.html     # 新建订单表单
│   ├── income_form.html    # 收入表单
│   ├── expense_form.html  # 支出表单
│   ├── customers.html     # 客户列表
│   ├── reports.html       # 报表中心
│   ├── api_docs.html  # API文档
│   └── error.html         # 错误页面
├── static/                       # 静态资源
│   └── css/
│       └── style.css          # 响应式样式
└── requirements.txt           # 依赖包

deprecated_versions/             # 历史版本归档
├── legacy_versions/         # 旧版Python文件
├── business_docs/          # 历史文档
└── tests_backup/         # 旧测试备份

scripts/                        # 启动脚本
├── launcher.py               # 统一启动器
└── launcher_full_demo.py    # 演示数据生成器
```

---

## 🎯 核心功能

### 1. 订单管理
- ✅ 创建/编辑/删除订单
- ✅ 7种计价方式（件、条、只、个、米、公斤、平方米）
- ✅ 多工序支持（喷砂、拉丝、抛光、氧化）
- ✅ 委外加工管理
- ✅ 订单状态跟踪

### 2. 财务管理
- ✅ 收入/支出记录
- ✅ 银行账户管理（G银行/N银行）
- ✅ 收付款分配
- ✅ 自动对账

### 3. 报表分析
- ✅ 财务报表
- ✅ 月度统计
- ✅ 客户分析
- ✅ 支出分类统计

### 4. 性能监控（V2.2新增）
- ✅ 请求响应时间记录
- ✅ 慢请求警告（>500ms）
- ✅ API性能统计展示
- ✅ API文档页面

### 5. 会计核算（V2.3新增 - 小企业会计准则）
- ✅ 会计科目体系（完整的小企业准则科目）
- ✅ 会计凭证管理（创建、审核、记账、查询）
- ✅ 自动凭证生成（收入、支出、订单完工）
- ✅ 财务报表（资产负债表、利润表）
- ✅ 成本核算（针对氧化加工行业）
- ✅ 会计期间管理

### 6. 系统功能
- ✅ 审计日志（完整操作追踪）
- ✅ 自动备份
- ✅ 数据库索引优化
- ✅ 金额精度保护（TEXT存储）

---

## 📚 API文档

访问 `http://localhost:5000/api-docs` 查看完整的API文档。

### 主要API接口

| 接口 | 方法 | 说明 |
|------|------|
| `/api/search` | GET | 搜索客户和订单 |
| `/api/stats` | GET | 获取统计数据 |

### 性能监控

- 自动记录每个请求的响应时间
- 在API文档页面展示性能统计
- 慢请求（>500ms）自动警告

---

## 🧪 测试验证

### 运行全部测试

```bash
cd oxidation_finance_v20
pytest tests/ -v --tb=short
```

**预期输出**:
```
============================= test session starts ==============================
tests/test_database.py::TestDatabaseBasics::test_database_connection PASSED [ 10%]
tests/test_database.py::TestDatabaseBasics::test_customer_crud PASSED [ 20%]
...
======================= 10 passed, 17 warnings in 0.92s ========================
```

### 快速测试

```bash
# 数据库测试
python -m pytest tests/test_database.py -v

# 财务测试
python -m pytest tests/test_finance_manager.py -v

# 订单测试
python -m pytest tests/test_order_manager.py -v
```

---

## 📖 使用说明

### 初始化系统

```bash
cd oxidation_finance_v20
python tools/setup_wizard.py
```

### 生成示例数据

```bash
python examples/generate_comprehensive_demo.py
```

**输出示例**:
```
📊 数据统计：
   客户数量：5
   供应商数量：5
   订单数量：30
   收入记录：31
   支出记录：74
   银行交易：105

💰 财务概况：
   总收入：¥36,704.73
   总支出：¥203,712.08
   利润：¥-167,007.34
```

### 启动Web界面

```bash
cd oxidation_finance_v20
python web_app.py
```

访问 `http://localhost:5000` 查看财务仪表盘，
访问 `http://localhost:5000/api-docs` 查看API文档。

---

## 🔧 技术特性

### 已实现

- ✅ **审计日志全覆盖** - 所有核心操作自动记录
- ✅ **金额精度改进** - TEXT存储避免浮点问题
- ✅ **事务支持** - 原子性操作保障数据一致性
- ✅ **幂等性保护** - 重复操作自动识别
- ✅ **SQL注入防护** - 参数化查询 + 表名白名单
- ✅ **数据库索引** - 15+ 索引提升查询性能
- ✅ **结构化日志** - 完整的错误追踪
- ✅ **性能监控** - 请求响应时间记录（V2.2新增）
- ✅ **API文档** - 完整的API文档页面（V2.2新增）
- ✅ **类型安全** - Decimal/UUID/Optional规范使用

### 技术栈

- Python 3.8+
- SQLite 3
- Flask 2.0+
- pytest + Hypothesis
- Decimal 精确计算

---

## 🔄 版本历史

| 版本 | 日期 | 说明 |
|------|------|------|
| V2.3 | 2026-05-17 | 小企业会计准则、会计凭证、财务报表、成本核算 |
| V2.2 | 2026-05-17 | 性能监控、API文档、独立模板 |
| V2.1 | 2026-05-17 | 项目结构整理、Web重构、日志系统、启动器 |
| V2.0.1 | 2026-02-25 | 审计日志全覆盖、金额精度改进、事务支持 |
| V2.0 | 2026-02 | 初始版本 |

---

## 📞 支持

- 📚 查看文档：`oxidation_finance_v20/docs/
- 🐛 提交问题：GitHub Issues
- 📧 技术支持：查看 AGENTS.md

---

## ⚠️ 重要提示

1. **始终先读 `AGENTS.md` - 这是项目黑匣子
2. **运行测试** - 任何更改后必须运行测试
3. **更新记忆核心** - 重大变更后更新 `AGENTS.md`
4. **不要删除历史** - 旧版本移动到 `deprecated_versions/`

---

**最后更新**: 2026-05-17

**优化版本**: V2.2

**AI 助手**: Kimi (OpenCode)

---

💼 **氧化加工厂财务系统 V2.2 - 让财务管理更简单、更专业！
