# 配置管理模块

## 概述

配置管理模块提供了系统配置和基础数据的管理功能，包括客户信息、供应商信息、计价方式、工序类型、会计科目和报表格式的配置管理。

## 主要功能

### 1. 客户管理
- 添加、更新、删除客户信息
- 查询单个客户或列出所有客户
- 支持客户信用额度管理

### 2. 供应商管理
- 添加、更新、删除供应商信息
- 查询单个供应商或列出所有供应商
- 支持供应商业务类型分类

### 3. 计价方式配置
- 管理系统支持的计价方式
- 默认支持7种计价方式：件、条、只、个、米、公斤、平方米
- 支持添加自定义计价方式

### 4. 工序类型配置
- 管理加工工序类型
- 默认支持4种工序：喷砂、拉丝、抛光、氧化
- 支持自定义工序顺序

### 5. 会计科目配置
- 管理会计科目结构
- 支持资产、负债、权益、收入、费用等科目类别
- 支持添加自定义会计科目

### 6. 报表格式配置
- 管理报表格式定义
- 支持资产负债表、利润表、现金流量表等
- 支持自定义报表格式

### 7. 配置导出导入
- 支持将所有配置导出到指定目录
- 支持从指定目录导入配置
- 便于配置备份和迁移

## 使用示例

### 基本使用

```python
from config.config_manager import ConfigManager
from models.business_models import Customer, Supplier
from decimal import Decimal

# 创建配置管理器
config_manager = ConfigManager("database.db", "config_data")

# 添加客户
customer = Customer(
    name="测试客户",
    contact="张三",
    phone="13800138000",
    credit_limit=Decimal("10000")
)
config_manager.add_customer(customer)

# 获取客户
retrieved = config_manager.get_customer(customer.id)
print(f"客户名称: {retrieved.name}")

# 列出所有客户
customers = config_manager.list_customers()
for c in customers:
    print(f"- {c.name}")
```

### 配置管理

```python
# 获取计价方式
pricing_methods = config_manager.get_pricing_methods()
for method in pricing_methods:
    print(f"{method['name']}: {method['description']}")

# 添加自定义计价方式
config_manager.add_pricing_method(
    "CUSTOM", "自定义单位", "自定义计价方式"
)

# 获取工序类型
process_types = config_manager.get_process_types()
for ptype in process_types:
    print(f"{ptype['order']}. {ptype['name']}")

# 添加自定义工序
config_manager.add_process_type(
    "COATING", "喷涂", "表面喷涂工序", 5
)
```

### 会计科目管理

```python
# 获取会计科目结构
account_structure = config_manager.get_account_structure()
assets = account_structure["assets"]
for account in assets:
    print(f"{account['code']} {account['name']}")

# 添加会计科目
config_manager.add_account(
    "assets", "1403", "原材料", "流动资产"
)

# 更新会计科目
config_manager.update_account(
    "assets", "1403", "原材料库存", "流动资产"
)
```

### 配置导出导入

```python
# 导出所有配置
config_manager.export_all_configs("backup_configs")

# 导入配置
config_manager.import_all_configs("backup_configs")
```

## 配置文件结构

配置管理器使用JSON文件存储配置信息，默认存储在 `config_data/` 目录下：

```
config_data/
├── pricing_methods.json      # 计价方式配置
├── process_types.json         # 工序类型配置
├── account_structure.json     # 会计科目配置
└── report_formats.json        # 报表格式配置
```

### pricing_methods.json 示例

```json
{
  "pricing_methods": [
    {
      "code": "PIECE",
      "name": "件",
      "description": "按件计价，例如：螺丝、螺母等小零件"
    },
    {
      "code": "METER",
      "name": "米",
      "description": "按米长计价，例如：铝型材、管材等"
    }
  ]
}
```

### process_types.json 示例

```json
{
  "process_types": [
    {
      "code": "SANDBLASTING",
      "name": "喷砂",
      "description": "用砂粒喷射表面，去除氧化层和杂质",
      "order": 1
    },
    {
      "code": "OXIDATION",
      "name": "氧化",
      "description": "最后工序，在酸液中形成氧化膜",
      "order": 4
    }
  ]
}
```

## API 参考

### ConfigManager 类

#### 构造函数

```python
ConfigManager(db_path: str, config_dir: Optional[str] = None)
```

- `db_path`: 数据库文件路径
- `config_dir`: 配置文件目录，默认为 `config_data/`

#### 客户管理方法

- `add_customer(customer: Customer) -> bool`: 添加客户
- `update_customer(customer: Customer) -> bool`: 更新客户
- `delete_customer(customer_id: str) -> bool`: 删除客户
- `get_customer(customer_id: str) -> Optional[Customer]`: 获取客户
- `list_customers() -> List[Customer]`: 列出所有客户

#### 供应商管理方法

- `add_supplier(supplier: Supplier) -> bool`: 添加供应商
- `update_supplier(supplier: Supplier) -> bool`: 更新供应商
- `delete_supplier(supplier_id: str) -> bool`: 删除供应商
- `get_supplier(supplier_id: str) -> Optional[Supplier]`: 获取供应商
- `list_suppliers() -> List[Supplier]`: 列出所有供应商

#### 计价方式配置方法

- `get_pricing_methods() -> List[Dict[str, str]]`: 获取所有计价方式
- `add_pricing_method(code: str, name: str, description: str) -> bool`: 添加计价方式
- `update_pricing_method(code: str, name: str, description: str) -> bool`: 更新计价方式
- `delete_pricing_method(code: str) -> bool`: 删除计价方式

#### 工序类型配置方法

- `get_process_types() -> List[Dict[str, Any]]`: 获取所有工序类型
- `add_process_type(code: str, name: str, description: str, order: int) -> bool`: 添加工序类型
- `update_process_type(code: str, name: str, description: str, order: int) -> bool`: 更新工序类型
- `delete_process_type(code: str) -> bool`: 删除工序类型

#### 会计科目配置方法

- `get_account_structure() -> Dict[str, List[Dict[str, str]]]`: 获取会计科目结构
- `add_account(category: str, code: str, name: str, account_category: str) -> bool`: 添加会计科目
- `update_account(category: str, code: str, name: str, account_category: str) -> bool`: 更新会计科目
- `delete_account(category: str, code: str) -> bool`: 删除会计科目

#### 报表格式配置方法

- `get_report_formats() -> Dict[str, Dict[str, Any]]`: 获取所有报表格式
- `update_report_format(report_type: str, name: str, sections: List[str], format_type: str) -> bool`: 更新报表格式
- `get_report_format(report_type: str) -> Optional[Dict[str, Any]]`: 获取指定报表格式

#### 配置导出导入方法

- `export_all_configs(export_path: str) -> bool`: 导出所有配置
- `import_all_configs(import_path: str) -> bool`: 导入所有配置

## 注意事项

1. **数据库连接**: ConfigManager 会为每个操作创建新的数据库连接，操作完成后自动关闭
2. **配置文件**: 配置文件使用 UTF-8 编码的 JSON 格式，可以手动编辑
3. **默认配置**: 首次创建 ConfigManager 时会自动生成默认配置文件
4. **错误处理**: 所有方法都包含错误处理，失败时返回 False 并打印错误信息
5. **数据验证**: 添加重复数据时会返回 False，不会覆盖现有数据

## 测试

运行单元测试：

```bash
python -m pytest tests/test_config_manager.py -v
```

运行快速测试：

```bash
python test_config_quick.py
```

运行演示示例：

```bash
python examples/demo_config_manager.py
```

## 相关文档

- [业务模型文档](../models/business_models.py)
- [数据库模式文档](../database/schema.py)
- [项目结构文档](../PROJECT_STRUCTURE.md)
