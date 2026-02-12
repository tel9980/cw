# 氧化加工厂财务管理系统 V2.0

专为小型氧化加工企业设计的财务管理解决方案

## 项目结构

```
oxidation_finance_v20/
├── models/              # 数据模型
│   ├── __init__.py
│   └── business_models.py
├── database/            # 数据库管理
│   ├── __init__.py
│   ├── schema.py       # 数据库表结构
│   └── db_manager.py   # 数据库管理器
├── business/            # 业务逻辑
│   └── __init__.py
├── reports/             # 报表生成
│   └── __init__.py
├── config/              # 配置管理
│   └── __init__.py
├── utils/               # 工具函数
│   └── __init__.py
├── tests/               # 测试
│   ├── __init__.py
│   ├── conftest.py     # Pytest配置
│   └── test_database.py
├── __init__.py
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
- G银行: 用于有票据的正式交易
- N银行: 与微信结合，用于现金交易

## 安装依赖

```bash
pip install -r requirements.txt
```

## 运行测试

```bash
# 运行所有测试
pytest

# 运行特定测试文件
pytest tests/test_database.py

# 运行测试并显示覆盖率
pytest --cov=oxidation_finance_v20

# 运行特定标记的测试
pytest -m unit
pytest -m database
```

## 数据库

系统使用SQLite数据库存储所有数据，数据库文件默认为 `oxidation_finance.db`。

### 数据库表
- customers: 客户信息
- suppliers: 供应商信息
- processing_orders: 加工订单
- incomes: 收入记录
- expenses: 支出记录
- bank_accounts: 银行账户
- bank_transactions: 银行交易记录

## 使用示例

```python
from oxidation_finance_v20.database import DatabaseManager
from oxidation_finance_v20.models import Customer, ProcessingOrder, PricingUnit

# 创建数据库管理器
with DatabaseManager("my_finance.db") as db:
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
    
    # 查询订单
    orders = db.list_orders(customer_id=customer.id)
    for order in orders:
        print(f"订单号: {order.order_no}, 金额: {order.total_amount}")
```

## 开发状态

当前版本: 2.0.0

已完成:
- ✅ 项目结构搭建
- ✅ 核心数据模型定义
- ✅ SQLite数据库设计
- ✅ 数据库管理器实现
- ✅ 测试框架配置
- ✅ 基础单元测试

进行中:
- 🔄 业务逻辑实现
- 🔄 报表生成功能
- 🔄 用户界面开发

## 许可证

MIT License
