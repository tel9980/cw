# 氧化加工厂财务管理系统 V2.4

专为小型氧化加工企业设计的财务管理解决方案，支持非一一对应收付款、权责发生制记账，以及双银行账户管理。

## 🚀 快速开始

### 方式一：一键初始化（推荐）

只需一条命令，自动完成所有初始化工作：

```bash
cd oxidation_finance_v20
python init.py
```

初始化脚本会自动完成以下工作：
- ✅ 检查Python环境
- ✅ 安装所需依赖包
- ✅ 生成完整的小企业模拟数据
- ✅ 验证系统配置
- ✅ 提供详细的使用说明

### 方式二：快速启动

如果已经初始化过，直接运行：

**Linux/Mac:**
```bash
./start.sh
```

**Windows:**
```cmd
start.bat
```

### 方式三：手动启动

```bash
# 1. 安装依赖
pip install -r requirements.txt
pip install flask

# 2. 生成演示数据（可选）
python examples/generate_small_business_demo.py

# 3. 启动Web应用
python web_app.py
```

然后访问：http://localhost:5000

## 项目结构

```
oxidation_finance_v20/
├── models/              # 数据模型
│   ├── __init__.py
│   ├── business_models.py      # 业务数据模型
│   └── accounting_models.py    # 会计数据模型
├── database/            # 数据库管理
│   ├── __init__.py
│   ├── schema.py       # 数据库表结构
│   └── db_manager.py   # 数据库管理器
├── business/            # 业务逻辑
│   ├── __init__.py
│   ├── finance_manager.py      # 财务管理
│   ├── order_manager.py        # 订单管理
│   ├── cost_calculation_engine.py  # 成本计算
│   ├── report_manager.py       # 报表生成
│   ├── voucher_manager.py      # 凭证管理
│   └── accountant_assistant.py # 小会计助手
├── examples/            # 示例和演示
│   ├── __init__.py
│   ├── generate_small_business_demo.py  # 小企业模拟数据生成
│   ├── generate_comprehensive_demo.py   # 综合演示数据
│   ├── demo_backup_restore.py
│   └── demo_data_import.py
├── templates/           # Web 模板
│   ├── base.html
│   ├── index.html
│   ├── orders.html
│   ├── order_form.html
│   ├── customers.html
│   ├── reports.html
│   ├── income_form.html
│   ├── expense_form.html
│   ├── assistant.html          # 小会计助手页面
│   ├── quick_income.html       # 快速记录收入
│   ├── quick_expense.html      # 快速记录支出
│   ├── api_docs.html
│   └── error.html
├── static/css/          # 静态资源
├── tools/               # 工具脚本
├── tests/               # 测试
│   ├── __init__.py
│   ├── conftest.py     # Pytest配置
│   └── test_*.py       # 各模块测试
├── config/              # 配置管理
├── utils/               # 工具函数
├── __init__.py
├── web_app.py          # Web 应用入口
├── pytest.ini          # Pytest配置文件
├── requirements.txt    # 依赖包
└── README.md           # 项目说明
```

## 核心功能

### 1. 数据模型
- **客户管理**: Customer
- **供应商管理**: Supplier
- **加工订单**: ProcessingOrder
- **收入记录**: Income
- **支出记录**: Expense
- **银行账户**: BankAccount
- **银行交易**: BankTransaction
- **会计凭证**: AccountingVoucher, VoucherLine
- **会计期间**: AccountingPeriod
- **委外加工**: OutsourcedProcessing

### 2. 计价方式
支持七种计价单位:
- 件 (PIECE)
- 条 (STRIP)
- 只 (UNIT)
- 个 (ITEM)
- 米 (METER)
- 公斤 (KILOGRAM)
- 平方米 (SQUARE_METER)

### 3. 加工工序
- 喷砂 (SANDBLASTING)
- 拉丝 (WIRE_DRAWING)
- 抛光 (POLISHING)
- 氧化 (OXIDATION)

### 4. 支出类型
- 房租、水电费
- 三酸（硫酸、硝酸、盐酸）
- 片碱、亚钠
- 色粉、除油剂
- 挂具
- 外发加工费
- 日常费用、工资

### 5. 银行账户
- **G银行**: 用于有票据的正式交易
- **N银行**: 与微信结合，用于现金交易

### 6. 会计系统
- 小企业会计准则
- 权责发生制
- 会计凭证自动生成
- 财务报表支持

### 7. 小会计助手
- 每日工作检查
- 快速记录收入/支出
- 智能提醒（月末、大额支出等）
- 未付款订单跟踪

## 安装依赖

```bash
pip install -r requirements.txt
pip install flask  # Web 应用需要
```

## 快速开始

### 1. 生成演示数据

```bash
cd oxidation_finance_v20
python examples/generate_small_business_demo.py
```

这会生成包含以下内容的演示数据：
- 4个核心客户
- 5个主要供应商
- 60+个加工订单
- 非一一对应的收付款记录
- G银行和N银行的交易
- 会计凭证和财务报表

### 2. 启动 Web 应用

```bash
python web_app.py
```

然后在浏览器中访问：
- http://localhost:5000 - 首页仪表盘
- http://localhost:5000/assistant - 小会计助手
- http://localhost:5000/orders - 订单管理
- http://localhost:5000/customers - 客户管理
- http://localhost:5000/reports - 报表中心

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

系统使用SQLite数据库存储所有数据，数据库文件默认为 `oxidation_finance.db`，演示数据使用 `oxidation_finance_demo_ready.db`。

### 数据库表
- customers: 客户信息
- suppliers: 供应商信息
- processing_orders: 加工订单
- incomes: 收入记录
- expenses: 支出记录
- bank_accounts: 银行账户
- bank_transactions: 银行交易记录
- outsourced_processing: 委外加工
- accounting_periods: 会计期间
- accounting_vouchers: 会计凭证
- voucher_lines: 凭证明细
- audit_logs: 审计日志

## 使用示例

### Python API 使用

```python
from decimal import Decimal
from datetime import date
from oxidation_finance_v20.database import DatabaseManager
from oxidation_finance_v20.models import Customer, ProcessingOrder, PricingUnit
from oxidation_finance_v20.business import FinanceManager

# 创建数据库管理器
with DatabaseManager("my_finance.db") as db:
    # 创建财务管理
    fm = FinanceManager(db)
    
    # 创建客户
    customer = Customer(
        name="优质客户有限公司",
        contact="张经理",
        phone="138****1234",
        credit_limit=Decimal("100000")
    )
    db.save_customer(customer)
    
    # 创建订单
    order = ProcessingOrder(
        order_no="OX202401001",
        customer_id=customer.id,
        customer_name=customer.name,
        item_description="铝型材6063",
        quantity=Decimal("100"),
        pricing_unit=PricingUnit.METER,
        unit_price=Decimal("5.50"),
        total_amount=Decimal("550.00")
    )
    db.save_order(order)
    
    # 记录收入（非一一对应）
    from oxidation_finance_v20.models import Income, BankType
    income = Income(
        customer_id=customer.id,
        customer_name=customer.name,
        amount=Decimal("10000.00"),
        bank_type=BankType.G_BANK,
        has_invoice=True,
        income_date=date.today()
    )
    fm.record_income(income)
    
    # 分配收入到订单
    fm.allocate_income_to_orders(income.id, [
        (order.id, Decimal("550.00"))
    ])
    
    # 查询订单
    orders = db.list_orders(customer_id=customer.id)
    for order in orders:
        print(f"订单号: {order.order_no}, 金额: {order.total_amount}")
```

## 开发状态

当前版本: 2.4.0

已完成:
- ✅ 项目结构搭建
- ✅ 核心数据模型定义
- ✅ SQLite数据库设计
- ✅ 数据库管理器实现
- ✅ 测试框架配置
- ✅ 基础单元测试
- ✅ 权责发生制会计
- ✅ 非一一对应收付款
- ✅ 小企业会计准则实现
- ✅ 会计凭证自动生成
- ✅ 小会计助手功能
- ✅ Web 应用界面
- ✅ 模拟数据生成

## 许可证

MIT License
