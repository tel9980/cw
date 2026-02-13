# 项目结构说明

## 目录结构

```
oxidation_workflow_v18/
│
├── config/                          # 配置管理模块
│   ├── __init__.py
│   └── config_manager.py           # 配置管理器（已实现）
│
├── models/                          # 数据模型
│   └── __init__.py
│   # 后续任务：
│   # ├── core_models.py            # 核心数据模型
│   # ├── enums.py                  # 枚举类型
│   # └── validators.py             # 数据验证器
│
├── business/                        # 业务逻辑层
│   ├── __init__.py
│   ├── orders/                     # 订单管理
│   │   └── __init__.py
│   │   # 后续任务：
│   │   # ├── order_manager.py     # 订单管理器
│   │   # └── pricing_calculator.py # 计价计算器
│   │
│   ├── accounts/                   # 账户管理
│   │   └── __init__.py
│   │   # 后续任务：
│   │   # ├── account_manager.py   # 账户管理器
│   │   # └── transaction_manager.py # 交易管理器
│   │
│   ├── reconciliation/             # 对账引擎
│   │   └── __init__.py
│   │   # 后续任务：
│   │   # ├── matcher.py           # 对账匹配器
│   │   # └── suggestion_engine.py # 建议引擎
│   │
│   ├── expenses/                   # 支出管理
│   │   └── __init__.py
│   │   # 后续任务：
│   │   # ├── expense_classifier.py # 支出分类器
│   │   # └── expense_manager.py   # 支出管理器
│   │
│   └── reports/                    # 报表生成
│       └── __init__.py
│       # 后续任务：
│       # ├── report_generator.py  # 报表生成器
│       # └── chart_generator.py   # 图表生成器
│
├── workflow/                        # 工作流引擎
│   └── __init__.py
│   # 后续任务：
│   # ├── workflow_engine.py       # 工作流引擎
│   # ├── workflow_templates.py    # 工作流模板
│   # └── smart_dashboard.py       # 智能工作台
│
├── storage/                         # 数据持久化层
│   └── __init__.py
│   # 后续任务：
│   # ├── base_storage.py          # 基础存储类
│   # ├── json_storage.py          # JSON存储实现
│   # └── backup_manager.py        # 备份管理器
│
├── ui/                              # 用户界面
│   └── __init__.py
│   # 后续任务：
│   # ├── cli.py                   # 命令行界面
│   # ├── menu.py                  # 菜单系统
│   # └── forms.py                 # 表单输入
│
├── utils/                           # 工具函数
│   └── __init__.py
│   # 后续任务：
│   # ├── date_utils.py            # 日期工具
│   # ├── validation.py            # 验证工具
│   # └── formatters.py            # 格式化工具
│
├── tests/                           # 测试套件
│   ├── __init__.py
│   ├── conftest.py                 # Pytest配置（已实现）
│   ├── unit/                       # 单元测试
│   │   ├── __init__.py
│   │   └── test_config_manager.py # 配置管理器测试（已实现）
│   │
│   └── properties/                 # 属性测试
│       └── __init__.py
│       # 后续任务：
│       # ├── test_order_properties.py
│       # ├── test_account_properties.py
│       # └── test_reconciliation_properties.py
│
├── data/                            # 数据文件（运行时创建）
├── backups/                         # 备份文件（运行时创建）
├── logs/                            # 日志文件（运行时创建）
│
├── __init__.py                      # 包初始化（已实现）
├── main.py                          # 主入口（已实现）
├── requirements.txt                 # 依赖列表（已实现）
├── pytest.ini                       # Pytest配置（已实现）
├── .env.example                     # 环境变量示例（已实现）
├── .gitignore                       # Git忽略文件（已实现）
├── README.md                        # 项目说明（已实现）
├── SETUP.md                         # 安装指南（已实现）
├── PROJECT_STRUCTURE.md             # 本文件（已实现）
├── 启动系统.bat                     # Windows启动脚本（已实现）
└── 运行测试.bat                     # Windows测试脚本（已实现）
```

## 模块说明

### 已实现模块

#### config/ - 配置管理
- **config_manager.py**: 完整的配置管理系统
  - 支持JSON配置文件
  - 支持环境变量覆盖
  - 用户偏好管理
  - 工作流自定义配置
  - 支出类别管理

#### tests/ - 测试框架
- **conftest.py**: Pytest共享fixtures
- **unit/test_config_manager.py**: 配置管理器的11个单元测试

### 待实现模块（后续任务）

#### models/ - 数据模型（任务2）
- 订单模型（ProcessingOrder）
- 银行账户模型（BankAccount）
- 对账匹配模型（ReconciliationMatch）
- 交易记录模型（TransactionRecord）
- 委外加工模型（OutsourcedProcessing）

#### business/ - 业务逻辑（任务4-13）
- 订单管理器（任务4）
- 委外加工管理器（任务5）
- 银行账户管理器（任务6）
- 支出分类器（任务8）
- 对账引擎（任务9）
- 报表生成器（任务12）
- 数据导入导出引擎（任务13）

#### workflow/ - 工作流引擎（任务14-16）
- 工作流引擎核心
- 工作流模板
- 智能工作台

#### storage/ - 数据持久化（任务19）
- JSON存储实现
- 备份管理器
- 审计日志

#### ui/ - 用户界面（任务21-22）
- CLI命令行界面
- 菜单系统
- 表单输入
- 错误处理

## 设计原则

### 1. 模块化设计
- 每个模块职责单一
- 模块间低耦合
- 接口清晰明确

### 2. 可测试性
- 单元测试覆盖核心功能
- 属性测试验证通用性质
- 集成测试验证端到端流程

### 3. 可扩展性
- 支持自定义配置
- 支持插件式扩展
- 支持用户自定义

### 4. 用户友好
- 简化的操作流程
- 清晰的错误提示
- 完善的帮助文档

## 开发进度

### ✅ 已完成（任务1）
- [x] 项目目录结构
- [x] Python环境配置
- [x] 测试框架设置（pytest + hypothesis）
- [x] 配置文件管理模块
- [x] 基础文档

### 🔄 进行中
- 无

### 📋 待开始
- [ ] 任务2：核心数据模型整合
- [ ] 任务3：数据模型验证检查点
- [ ] 任务4-25：后续开发任务

## 技术栈

- **语言**: Python 3.8+
- **数据存储**: JSON文件
- **测试框架**: pytest + hypothesis
- **数据验证**: pydantic
- **Excel处理**: openpyxl
- **日期处理**: python-dateutil

## 代码规范

### Python代码风格
- 遵循 PEP 8 规范
- 使用类型注解
- 编写文档字符串（docstrings）
- 函数和类命名清晰明确

### 测试规范
- 单元测试使用 `@pytest.mark.unit` 标记
- 属性测试使用 `@pytest.mark.property` 标记
- 测试函数命名：`test_<功能描述>`
- 每个测试应该独立且可重复

### 文档规范
- 所有公共API必须有文档字符串
- 复杂逻辑需要注释说明
- 保持README和文档同步更新

## 下一步

完成任务1后，下一步是：
1. 实施任务2：整合核心数据模型
2. 编写数据模型的属性测试
3. 进行数据模型验证检查点（任务3）
