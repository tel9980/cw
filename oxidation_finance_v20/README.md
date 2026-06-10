# 氧化加工厂财务管理系统 V3.1

专为小型氧化加工企业设计的全功能财务管理解决方案，覆盖完整会计循环（科目→凭证→账簿→报表→结账），支持银行对账、固定资产折旧、应收应付账龄分析、客户对账单、财务比率分析、部门项目损益、发票管理、出纳日记账、登录认证、用户权限管理、数据备份恢复等企业级功能。

## 快速开始

### 方式一：一键初始化（推荐）

```bash
cd oxidation_finance_v20
python init.py
```

初始化脚本会自动完成：Python环境检查、依赖安装、演示数据生成、系统配置验证。

### 方式二：手动启动

```bash
# 1. 安装依赖
pip install -r requirements.txt
pip install flask

# 2. 生成演示数据
python examples/generate_small_business_demo.py

# 3. 启动应用
python web_app.py
```

浏览器访问：http://localhost:5000

### 默认管理员账号

- 用户名：`admin`
- 密码：`admin123`

## 项目结构

```
oxidation_finance_v20/
├── models/                  # 数据模型
│   ├── business_models.py   # 业务数据模型
│   └── accounting_models.py # 会计数据模型
├── database/                # 数据库管理
│   ├── schema.py            # 数据库表结构（20+张表）
│   └── db_manager.py        # 数据库管理器
├── business/                # 业务逻辑
│   ├── finance_manager.py           # 财务管理
│   ├── order_manager.py             # 订单管理
│   ├── cost_calculation_engine.py   # 成本计算
│   ├── report_manager.py            # 报表生成
│   ├── voucher_manager.py           # 凭证管理
│   └── accountant_assistant.py      # 小会计助手
├── routes/                  # 路由模块（Flask Blueprint）
│   ├── __init__.py
│   ├── helpers.py           # 数据库连接、统计工具
│   ├── main_routes.py       # 主页、订单、客户路由
│   ├── finance_routes.py    # 收入、支出、报表、银行对账路由
│   ├── accounting_routes.py # 会计核心路由（科目/凭证/账簿/资产/结账等）
│   └── assistant_routes.py  # 小会计助手、API
├── templates/               # Web 模板（33个页面）
│   ├── base.html            # 基础模板
│   ├── index.html           # 首页仪表盘
│   ├── login.html           # 登录页
│   ├── orders.html          # 订单列表
│   ├── order_form.html      # 订单表单
│   ├── customers.html       # 客户管理
│   ├── reports.html         # 报表中心
│   ├── income_form.html     # 收入录入
│   ├── expense_form.html    # 支出录入
│   ├── quick_income.html    # 快速收入
│   ├── quick_expense.html   # 快速支出
│   ├── assistant.html       # 小会计助手
│   ├── api_docs.html        # API文档
│   ├── error.html           # 错误页
│   ├── chart_of_accounts.html    # 会计科目
│   ├── opening_balances.html     # 期初余额
│   ├── vouchers.html             # 会计凭证列表
│   ├── voucher_detail.html       # 凭证详情
│   ├── voucher_templates.html    # 凭证模板
│   ├── accounting_books.html     # 会计账簿（含现金流量表、账龄分析）
│   ├── fixed_assets.html         # 固定资产管理
│   ├── bank_reconciliation.html  # 银行对账
│   ├── multi_column_ledger.html  # 多栏式明细账
│   ├── audit_log.html            # 审计日志
│   ├── cash_journal.html         # 出纳日记账
│   ├── check_close.html          # 结账前检查
│   ├── data_backup.html          # 数据备份恢复
│   ├── user_management.html      # 用户管理
│   ├── batch_import.html         # 批量导入
│   ├── customer_statement.html   # 客户/供应商对账单
│   ├── financial_ratios.html     # 财务比率分析
│   ├── department_pl.html        # 部门损益表
│   ├── project_pl.html           # 项目损益与预算
│   ├── invoice_management.html   # 发票管理
│   └── system_settings.html      # 系统设置
├── examples/                # 示例和演示数据生成
├── tests/                   # 测试
├── config/                  # 配置管理
├── utils/                   # 工具函数
├── tools/                   # 工具脚本
├── backups/                 # 数据备份目录
├── web_app.py               # Web 应用入口
├── init.py                  # 一键初始化脚本
├── requirements.txt         # 依赖包
└── README.md
```

## 核心功能

### 1. 业务管理
- **客户管理**：客户档案、信用额度、交易统计
- **供应商管理**：供应商档案、业务类型、合作记录
- **加工订单**：全生命周期管理（待加工→加工中→已完工→已交付）
- **收入记录**：支持G银行/N银行双账户、非一一对应收付款
- **支出记录**：9种支出分类（三酸、片碱、亚钠、色粉、除油剂、挂具、外发加工费、日常费用、工资、房租、水电费）
- **委外加工**：外发工序管理、成本核算

### 2. 计价方式
支持七种计价单位：件、条、只、个、米、公斤、平方米

### 3. 加工工序
喷砂、拉丝、抛光、氧化（可自定义组合）

### 4. 银行管理
- **G银行**：有票据的正式交易
- **N银行**：与微信结合，用于现金交易
- **银行对账**：导入银行流水、自动匹配、勾稽确认

### 5. 会计系统（完整会计循环）
- 小企业会计准则、权责发生制
- **会计科目**：树形科目体系，支持辅助核算（客户/供应商/部门/项目/员工）
- **期初余额**：科目期初数据管理
- **会计凭证**：制作/审核/记账/冲销，支持批量审核、批量记账、凭证复制
- **凭证模板**：预设分录模板，快速生成常用凭证
- **会计账簿**：
  - 总分类账
  - 明细分类账
  - 科目余额表
  - 辅助核算余额表（按客户/供应商/部门/项目/员工）
  - 多栏式明细账（费用分类/增值税分类）
  - 试算平衡表
  - 现金流量表
  - 应收/应付账龄分析（0-30/31-60/61-90/90+天）
- **财务报表**：资产负债表、利润表、现金流量表
- **期末结账**：结账前检查（5项校验）、执行结账、取消结账回滚

### 6. 固定资产管理
- 固定资产卡片（编号/名称/类别/部门/位置）
- 直线法折旧自动计算
- 累计折旧跟踪、净值计算
- 资产处置（报废/出售）

### 7. 出纳管理
- **现金日记账**：按日期序时记录，实时计算余额
- **银行存款日记账**：分账户查询，流水式余额
- 筛选（现金/银行切换、期间、账户）、CSV导出

### 8. 数据管理
- **数据备份**：一键备份数据库到本地，含备注说明
- **数据恢复**：上传备份文件恢复，危险操作区确认提示
- **备份历史**：文件名、大小、时间列表

### 9. 用户权限管理
- 用户CRUD（管理员账号不可删除）
- 角色管理：管理员、会计、出纳
- SHA-256 密码哈希存储
- 默认管理员：admin / admin123

### 10. 批量导入
- CSV 批量导入客户、供应商、会计科目
- 格式示例提示

### 11. 审计追踪
- 操作日志记录（操作类型、实体、操作人、时间、新旧值）
- 分页查询、支持检索

### 12. 小会计助手
- 每日工作检查提醒
- 快速记录收入/支出
- 智能提醒（月末结账、大额支出）
- 未付款订单跟踪
- 全局搜索 API
- 统计数据 API

### 13. 首页仪表盘
- 4 KPI 卡片（本月收入/支出/利润、当前资产负债率）
- 6 项辅助统计（应收账款、应付账款、银行余额等）
- Canvas 趋势图（月度收支柱状图 + 利润折线图）
- 待办提醒、8 个快捷操作入口
- 支出 Top5（带进度条）、最近交易、最近订单

### 14. 客户/供应商对账单
- 按期对账：选择客户/供应商+日期范围
- 逐笔明细（订单/收款/费用，日期、摘要、金额、余额）
- 期初余额→本期发生→期末余额
- 打印优化、CSV 导出

### 15. 财务比率分析
- 盈利能力：毛利率、净利率、ROE、ROA
- 偿债能力：流动比率、资产负债率、利息保障倍数
- 运营能力：应收账款周转率/周转天数、总资产周转率
- 杜邦分析框架（ROE = 净利率 × 周转率 × 权益乘数）
- 环比/同比对比表（收入/支出/利润较上月、较去年同期）

### 16. 部门/项目损益
- 部门损益表：按部门汇总收入、成本、费用、利润
- 项目损益表：预算vs实际对比，差异分析
- 预算管理：设置/调整项目预算，进度条可视化
- 超预算预警（颜色标记）

### 17. 发票管理
- 发票录入（号码/类型/对方单位/金额/税率/税额）
- 销项/进项分类管理
- 发票汇总：销项税额 - 进项税额 = 应纳税额
- 发票列表及删除

### 18. 登录认证
- 登录页（用户名/密码/默认管理员提示）
- Session 会话管理
- 全局认证拦截中间件
- 导航栏显示当前用户+角色标签+退出按钮

## 路由总览（49个端点）

### main_routes - 主页/业务
| 路由 | 说明 |
|------|------|
| `GET/POST /login` | 用户登录 |
| `GET /logout` | 退出登录 |
| `GET /` | 首页仪表盘 |
| `GET /orders` | 订单列表 |
| `GET/POST /order/new` | 新建订单 |
| `GET/POST /order/edit/<id>` | 编辑订单 |
| `GET /order/delete/<id>` | 删除订单 |
| `GET /customers` | 客户管理 |

### finance_routes - 财务/报表
| 路由 | 说明 |
|------|------|
| `GET/POST /income/new` | 录入收入 |
| `GET/POST /income/edit/<id>` | 编辑收入 |
| `GET/POST /expense/new` | 录入支出 |
| `GET/POST /expense/edit/<id>` | 编辑支出 |
| `GET/POST /quick-income` | 快速收入 |
| `GET/POST /quick-expense` | 快速支出 |
| `GET /reports` | 报表中心 |
| `GET/POST /bank-reconciliation` | 银行对账 |

### accounting_routes - 会计核心
| 路由 | 说明 |
|------|------|
| `GET/POST /chart-of-accounts` | 会计科目管理 |
| `POST /chart-of-accounts/delete` | 删除科目 |
| `POST /chart-of-accounts/department` | 添加部门 |
| `POST /chart-of-accounts/project` | 添加项目 |
| `GET/POST /chart-of-accounts/opening-balances` | 期初余额 |
| `GET/POST /vouchers` | 凭证列表/新增 |
| `GET /vouchers/<id>` | 凭证详情 |
| `GET /accounting-books` | 会计账簿（总账/明细账/余额表/现金流量表/账龄分析） |
| `GET/POST /system-settings` | 系统设置 |
| `POST /period-close` | 期末结账 |
| `GET /export/vouchers` | 导出凭证 CSV |
| `GET /export/balance` | 导出余额表 CSV |
| `GET /export/trial-balance` | 导出试算平衡表 CSV |
| `GET/POST /fixed-assets` | 固定资产管理 |
| `POST /depreciate-fixed-assets` | 执行折旧 |
| `GET/POST /voucher-templates` | 凭证模板管理 |
| `POST /batch-vouchers` | 批量审核/记账 |
| `POST /copy-voucher/<id>` | 复制凭证 |
| `GET /multi-column-ledger` | 多栏式明细账 |
| `GET /audit-log` | 审计日志 |
| `GET /cash-journal` | 出纳日记账 |
| `GET /export/statement` | 导出日记账 CSV |
| `GET/POST /check-before-close` | 结账前检查 |
| `GET/POST /data-backup` | 数据备份恢复 |
| `GET/POST /user-management` | 用户管理 |
| `GET/POST /batch-import` | 批量导入 |
| `GET /customer-statement` | 客户对账单 |
| `GET /supplier-statement` | 供应商对账单 |
| `GET /financial-ratios` | 财务比率分析 |
| `GET /department-pl` | 部门损益表 |
| `GET/POST /project-pl` | 项目损益与预算 |
| `GET/POST /invoices` | 发票管理 |

### assistant_routes - 助手/API
| 路由 | 说明 |
|------|------|
| `GET/POST /assistant` | 小会计助手 |
| `GET /api/search` | 全局搜索 |
| `GET /api/stats` | 统计数据 |
| `GET /api-docs` | API 文档 |

## 数据库表结构（21+2张表）

### 业务表
| 表名 | 说明 |
|------|------|
| `customers` | 客户信息 |
| `suppliers` | 供应商信息 |
| `processing_orders` | 加工订单 |
| `incomes` | 收入记录 |
| `expenses` | 支出记录 |
| `bank_accounts` | 银行账户 |
| `bank_transactions` | 银行交易流水 |
| `outsourced_processing` | 委外加工记录 |

### 会计表
| 表名 | 说明 |
|------|------|
| `chart_of_accounts` | 会计科目（树形结构） |
| `account_balances` | 科目余额（按期间） |
| `accounting_periods` | 会计期间 |
| `accounting_vouchers` | 会计凭证 |
| `voucher_lines` | 凭证明细 |
| `departments` | 部门（辅助核算） |
| `projects` | 项目（辅助核算） |

### 管理表
| 表名 | 说明 |
|------|------|
| `fixed_assets` | 固定资产卡片 |
| `bank_reconciliations` | 银行勾稽记录 |
| `voucher_templates` | 凭证模板 |
| `system_settings` | 系统参数 |
| `audit_logs` | 审计操作日志 |
| `invoices` | 发票记录 |

### 运行时表（动态创建）
| 表名 | 说明 |
|------|------|
| `users` | 系统用户（SHA-256密码） |
| `login_sessions` | 登录会话 |

## 运行测试

```bash
# 运行所有测试
pytest

# 运行特定测试文件
pytest tests/test_finance_manager.py

# 运行测试并显示覆盖率
pytest --cov=oxidation_finance_v20

# 运行特定标记的测试
pytest -m unit
pytest -m database
```

## 数据库

系统使用SQLite数据库，默认文件 `oxidation_finance.db`，演示数据使用 `oxidation_finance_demo_ready.db`。

## 开发状态

当前版本：**3.1.0**

已完成功能：

- 核心数据模型与SQLite数据库设计
- 权责发生制会计体系
- 完整会计循环（科目→凭证→账簿→报表→结账）
- 非一一对应收付款管理
- 银行对账（导入/自动匹配/勾稽）
- 固定资产管理与直线法折旧
- 应收应付账龄分析（4个账龄段）
- 多栏式明细账（费用/增值税维度）
- 现金流量表（经营/投资/筹资三段式）
- 凭证模板与批量操作
- 出纳日记账（现金/银行+流水余额）
- 结账前检查（5项校验+回滚）
- 数据备份与恢复
- 登录认证与会话管理
- 用户权限管理（SHA-256密码、管理员/会计/出纳角色）
- 客户/供应商对账单（期初→本期→期末+逐笔明细）
- 财务比率分析（盈利/偿债/运营+杜邦框架+环比同比）
- 部门损益表 + 项目损益与预算对比
- 发票管理（销项/进项+税额汇总）
- CSV批量导入
- 审计操作日志
- 首页可视化仪表盘（Canvas图表）
- 小会计助手智能提醒
- Web 全功能界面（33个页面、49个路由端点）

## 许可证

MIT License