# 数据导入功能使用说明

## 概述

DataManager 类提供了强大的Excel数据导入功能，专门用于导入银行流水数据。该功能包括：

- ✓ 支持Excel格式的银行流水导入
- ✓ 自动识别和匹配交易对手（基于历史客户和供应商数据）
- ✓ 全面的数据验证和完整性检查
- ✓ 灵活的日期和金额格式解析
- ✓ 详细的错误报告和导入摘要

## 快速开始

### 1. 基本导入

```python
from utils.data_manager import DataManager
from models.business_models import BankType
from database.db_manager import DatabaseManager

# 初始化
db = DatabaseManager("finance.db")
db.connect()
data_manager = DataManager(db)

# 导入银行流水
count, errors = data_manager.import_bank_statement(
    file_path="bank_statement.xlsx",
    bank_type=BankType.G_BANK
)

print(f"成功导入 {count} 条记录")
if errors:
    print(f"发现 {len(errors)} 个错误")
```

### 2. 数据验证

在导入前验证数据：

```python
# 验证数据完整性
is_valid, errors = data_manager.validate_import_data("bank_statement.xlsx")

if is_valid:
    print("数据验证通过，可以导入")
else:
    print("数据验证失败:")
    for error in errors:
        print(f"  - {error}")
```

### 3. 获取导入摘要

查看文件信息：

```python
summary = data_manager.get_import_summary("bank_statement.xlsx")

print(f"总行数: {summary['total_rows']}")
print(f"日期范围: {summary['date_range']}")
print(f"金额统计: {summary['amount_stats']}")
```

## Excel文件格式要求

### 必需列

- **交易日期**: 交易发生的日期
- **金额**: 交易金额（正数表示收入，负数表示支出）

### 可选列

- **交易对手**: 交易对方的名称（用于自动匹配）
- **摘要**: 交易的描述或备注

### 示例格式

| 交易日期 | 金额 | 交易对手 | 摘要 |
|---------|------|---------|------|
| 2024-01-15 | 5000.00 | 张三公司 | 收到货款 |
| 2024-01-16 | -2000.00 | 化工供应商 | 采购原料 |
| 2024-01-17 | 3500.50 | 李四工厂 | 收到加工费 |

## 支持的数据格式

### 日期格式

系统自动识别以下日期格式：

- `2024-01-15` (ISO格式)
- `2024/01/15` (斜杠分隔)
- `2024年01月15日` (中文格式)
- `2024.01.15` (点分隔)

### 金额格式

系统自动处理以下金额格式：

- `1234.56` (标准数字)
- `1,234.56` (带千位分隔符)
- `¥1234.56` (带人民币符号)
- `$1234.56` (带美元符号)
- `-1234.56` (负数表示支出)

## 交易对手自动匹配

### 匹配规则

DataManager 使用智能匹配算法自动识别交易对手：

1. **精确匹配**: 首先尝试与客户/供应商名称精确匹配
2. **模糊匹配**: 如果精确匹配失败，使用包含关系进行模糊匹配
3. **保留原值**: 如果无法匹配，保留原始交易对手名称

### 匹配示例

假设系统中有客户"张三公司"：

- `张三公司` → 精确匹配 → `张三公司`
- `张三公司有限责任公司` → 模糊匹配 → `张三公司`
- `某某张三公司` → 模糊匹配 → `张三公司`
- `未知公司` → 无匹配 → `未知公司`

## 数据验证规则

### 完整性检查

- ✓ 检查必需列是否存在
- ✓ 检查是否有空值
- ✓ 检查文件是否为空

### 格式检查

- ✓ 验证日期格式是否正确
- ✓ 验证金额格式是否正确
- ✓ 验证金额是否在合理范围内（不超过999,999,999.99）

### 错误报告

所有验证错误都会详细报告，包括：

- 错误所在的行号
- 错误的具体描述
- 错误的数据值

## 高级用法

### 自定义列名

如果Excel文件使用不同的列名：

```python
count, errors = data_manager.import_bank_statement(
    file_path="bank_statement.xlsx",
    bank_type=BankType.G_BANK,
    date_column="日期",           # 自定义日期列名
    amount_column="交易金额",      # 自定义金额列名
    counterparty_column="对方",   # 自定义交易对手列名
    description_column="备注"     # 自定义摘要列名
)
```

### 批量导入

导入多个文件：

```python
files = ["statement_jan.xlsx", "statement_feb.xlsx", "statement_mar.xlsx"]

total_count = 0
all_errors = []

for file in files:
    count, errors = data_manager.import_bank_statement(file, BankType.G_BANK)
    total_count += count
    all_errors.extend(errors)

print(f"总共导入 {total_count} 条记录")
print(f"总共 {len(all_errors)} 个错误")
```

### 导入前预览

在实际导入前查看数据：

```python
# 1. 验证数据
is_valid, errors = data_manager.validate_import_data("bank_statement.xlsx")

# 2. 获取摘要
summary = data_manager.get_import_summary("bank_statement.xlsx")

# 3. 确认后导入
if is_valid and summary['total_rows'] > 0:
    count, errors = data_manager.import_bank_statement(
        "bank_statement.xlsx",
        BankType.G_BANK
    )
```

## 错误处理

### 常见错误及解决方案

#### 1. 文件不存在

```
错误: 无法读取Excel文件: [Errno 2] No such file or directory
解决: 检查文件路径是否正确
```

#### 2. 缺少必需列

```
错误: 缺少必需列: 交易日期, 金额
解决: 确保Excel文件包含必需的列，或使用自定义列名参数
```

#### 3. 日期格式错误

```
错误: 第3行: 日期解析错误 - 无法解析日期格式: 2024/13/45
解决: 检查日期数据是否正确，使用支持的日期格式
```

#### 4. 金额格式错误

```
错误: 第5行: 金额解析错误 - invalid literal for Decimal
解决: 检查金额数据是否为有效数字
```

## 性能优化

### 大文件导入

对于包含大量记录的文件：

1. 系统会批量处理数据
2. 使用事务确保数据一致性
3. 提供进度反馈

### 内存管理

- 使用pandas的分块读取功能处理超大文件
- 及时释放不需要的数据
- 避免重复加载相同数据

## 示例代码

完整的导入示例请参考：

- `examples/demo_data_import.py` - 完整的导入演示
- `examples/sample_bank_statement.py` - 创建示例Excel文件
- `tests/test_data_manager.py` - 单元测试示例

## 最佳实践

1. **导入前验证**: 始终先验证数据再导入
2. **查看摘要**: 使用get_import_summary了解数据概况
3. **处理错误**: 检查并处理导入过程中的错误
4. **维护主数据**: 保持客户和供应商数据的准确性以提高匹配率
5. **备份数据**: 导入前备份数据库
6. **测试导入**: 先在测试环境中验证导入流程

## 技术细节

### 依赖包

- `pandas>=2.0.0` - 数据处理
- `openpyxl>=3.1.2` - Excel文件读写

### 数据库表

导入的数据保存到 `bank_transactions` 表：

```sql
CREATE TABLE bank_transactions (
    id TEXT PRIMARY KEY,
    bank_type TEXT NOT NULL,
    transaction_date TEXT NOT NULL,
    amount REAL NOT NULL,
    counterparty TEXT,
    description TEXT,
    matched INTEGER DEFAULT 0,
    matched_income_id TEXT,
    matched_expense_id TEXT,
    notes TEXT,
    created_at TEXT NOT NULL
)
```

## 常见问题

**Q: 可以导入CSV文件吗？**
A: 目前只支持Excel格式(.xlsx)，但可以轻松扩展支持CSV。

**Q: 如何处理重复数据？**
A: 系统会导入所有数据，不会自动去重。建议在导入前清理重复数据。

**Q: 交易对手匹配不准确怎么办？**
A: 可以在导入后手动调整，或者完善客户/供应商主数据。

**Q: 可以撤销导入吗？**
A: 目前不支持自动撤销，建议导入前备份数据库。

## 支持

如有问题或建议，请查看：

- 单元测试: `tests/test_data_manager.py`
- 演示代码: `examples/demo_data_import.py`
- 项目文档: `README.md`
