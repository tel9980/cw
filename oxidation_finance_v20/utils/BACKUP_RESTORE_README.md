# 数据备份和恢复功能说明

## 概述

数据备份和恢复功能为氧化加工厂财务系统提供完整的数据保护机制。该功能支持系统数据的完整备份、验证和恢复，确保数据安全和业务连续性。

## 主要功能

### 1. 数据备份 (backup_system_data)

完整备份系统数据库和配置参数。

**功能特点:**
- 完整的SQLite数据库备份
- 系统配置参数导出
- 备份统计信息收集
- 自动生成带时间戳的备份文件
- 备份元数据记录

**使用方法:**

```python
from utils.data_manager import DataManager
from database.db_manager import DatabaseManager

# 初始化
db = DatabaseManager("oxidation_finance.db")
db.connect()
data_manager = DataManager(db)

# 执行备份
success, backup_file, backup_info = data_manager.backup_system_data(
    backup_dir="backups",      # 备份目录
    include_config=True        # 是否包含配置
)

if success:
    print(f"备份成功: {backup_file}")
    print(f"总记录数: {backup_info['total_records']}")
else:
    print(f"备份失败: {backup_info}")
```

**备份内容:**
- 所有数据库表数据
  - 客户信息 (customers)
  - 供应商信息 (suppliers)
  - 加工订单 (processing_orders)
  - 收入记录 (incomes)
  - 支出记录 (expenses)
  - 银行账户 (bank_accounts)
  - 银行交易 (bank_transactions)
  - 委外加工 (outsourced_processing)
  - 审计日志 (audit_logs)
  - 会计期间 (accounting_periods)
- 系统配置参数（可选）
  - 客户列表配置
  - 供应商列表配置
  - 银行账户配置

**备份文件:**
- `backup_YYYYMMDD_HHMMSS.db` - 数据库备份文件
- `backup_YYYYMMDD_HHMMSS_config.json` - 配置文件（可选）
- `backup_YYYYMMDD_HHMMSS_metadata.json` - 备份元数据

### 2. 数据恢复 (restore_system_data)

从备份文件恢复系统数据。

**功能特点:**
- 备份文件验证
- 安全备份机制（恢复前自动备份当前数据）
- 数据完整性检查
- 配置参数恢复
- 详细的恢复日志

**使用方法:**

```python
# 执行恢复
success, messages = data_manager.restore_system_data(
    backup_file="backups/backup_20240101_120000.db",
    restore_config=True,              # 是否恢复配置
    validate_before_restore=True      # 恢复前验证
)

if success:
    print("恢复成功!")
    for msg in messages:
        print(f"  • {msg}")
else:
    print("恢复失败:")
    for msg in messages:
        print(f"  • {msg}")
```

**恢复流程:**
1. 验证备份文件存在性和有效性
2. 创建当前数据库的安全备份
3. 关闭当前数据库连接
4. 恢复数据库文件
5. 重新建立数据库连接
6. 验证恢复后的数据完整性
7. 恢复系统配置参数（可选）

**安全机制:**
- 恢复前自动创建安全备份
- 如果恢复失败，自动还原到恢复前状态
- 完整的错误处理和回滚机制

### 3. 列出备份 (list_backups)

查看所有可用的备份文件。

**使用方法:**

```python
backups = data_manager.list_backups(backup_dir="backups")

for backup in backups:
    print(f"备份名称: {backup['backup_name']}")
    print(f"备份时间: {backup['backup_time']}")
    print(f"备份大小: {backup['backup_size']} 字节")
    print(f"包含配置: {backup['has_config']}")
    if 'total_records' in backup:
        print(f"记录总数: {backup['total_records']}")
```

### 4. 备份验证 (validate_backup_file)

验证备份文件的完整性和有效性。

**验证内容:**
- 文件大小检查
- SQLite数据库格式验证
- 数据库完整性检查
- 必需表存在性验证

**使用方法:**

```python
is_valid, errors = data_manager._validate_backup_file(backup_file)

if is_valid:
    print("备份文件验证通过")
else:
    print("备份文件验证失败:")
    for err in errors:
        print(f"  • {err}")
```

### 5. 数据完整性验证 (verify_database_integrity)

验证数据库的完整性和一致性。

**验证内容:**
- SQLite完整性检查
- 外键约束检查
- 数据一致性检查
- 孤立记录检查

**使用方法:**

```python
is_ok, errors = data_manager._verify_database_integrity()

if is_ok:
    print("数据库完整性检查通过")
else:
    print("发现完整性问题:")
    for err in errors:
        print(f"  • {err}")
```

## 使用场景

### 场景 1: 定期备份

建议每天或每周进行定期备份，确保数据安全。

```python
# 每日备份脚本
import schedule
import time

def daily_backup():
    db = DatabaseManager("oxidation_finance.db")
    db.connect()
    data_manager = DataManager(db)
    
    success, backup_file, _ = data_manager.backup_system_data(
        backup_dir="backups/daily",
        include_config=True
    )
    
    if success:
        print(f"每日备份完成: {backup_file}")
    
    db.close()

# 每天凌晨2点执行备份
schedule.every().day.at("02:00").do(daily_backup)

while True:
    schedule.run_pending()
    time.sleep(60)
```

### 场景 2: 重要操作前备份

在执行重要操作（如批量删除、数据导入）前进行备份。

```python
# 重要操作前备份
db = DatabaseManager("oxidation_finance.db")
db.connect()
data_manager = DataManager(db)

# 备份
print("执行重要操作前备份...")
success, backup_file, _ = data_manager.backup_system_data(
    backup_dir="backups/before_operation"
)

if success:
    print(f"备份完成: {backup_file}")
    
    # 执行重要操作
    try:
        # ... 执行批量操作 ...
        print("操作完成")
    except Exception as e:
        print(f"操作失败，恢复备份: {e}")
        data_manager.restore_system_data(backup_file)

db.close()
```

### 场景 3: 数据迁移

将数据从一个系统迁移到另一个系统。

```python
# 源系统备份
source_db = DatabaseManager("source.db")
source_db.connect()
source_manager = DataManager(source_db)

success, backup_file, _ = source_manager.backup_system_data(
    backup_dir="migration",
    include_config=True
)
source_db.close()

# 目标系统恢复
target_db = DatabaseManager("target.db")
target_db.connect()
target_manager = DataManager(target_db)

success, messages = target_manager.restore_system_data(
    backup_file=backup_file,
    restore_config=True
)
target_db.close()

if success:
    print("数据迁移成功")
```

### 场景 4: 灾难恢复

系统故障后从备份恢复数据。

```python
# 灾难恢复
db = DatabaseManager("oxidation_finance.db")
db.connect()
data_manager = DataManager(db)

# 列出所有备份
backups = data_manager.list_backups("backups")

# 选择最新的备份
if backups:
    latest_backup = backups[0]
    print(f"使用最新备份: {latest_backup['backup_name']}")
    
    # 恢复数据
    success, messages = data_manager.restore_system_data(
        backup_file=latest_backup['backup_file'],
        restore_config=True,
        validate_before_restore=True
    )
    
    if success:
        print("系统恢复成功")
        for msg in messages:
            print(f"  • {msg}")

db.close()
```

## 最佳实践

### 1. 备份策略

- **频率**: 每天至少备份一次
- **保留**: 保留最近30天的每日备份
- **月度**: 每月保留一个月度备份
- **年度**: 每年保留一个年度备份

### 2. 备份存储

- 将备份文件存储在不同的物理位置
- 使用云存储服务进行异地备份
- 定期验证备份文件的可用性

### 3. 恢复测试

- 定期测试备份恢复流程
- 在测试环境中验证备份的完整性
- 记录恢复时间和步骤

### 4. 安全性

- 加密敏感的备份文件
- 限制备份文件的访问权限
- 记录所有备份和恢复操作

## 注意事项

1. **数据一致性**: 备份时确保没有正在进行的事务
2. **磁盘空间**: 确保有足够的磁盘空间存储备份
3. **权限**: 确保有读写备份目录的权限
4. **恢复影响**: 恢复操作会覆盖当前数据，请谨慎操作
5. **测试环境**: 建议先在测试环境中验证恢复流程

## 错误处理

常见错误及解决方法:

### 错误 1: 备份文件为空
```
原因: 数据库文件不存在或无法访问
解决: 检查数据库文件路径和权限
```

### 错误 2: 恢复验证失败
```
原因: 备份文件损坏或格式不正确
解决: 使用其他备份文件或重新创建备份
```

### 错误 3: 磁盘空间不足
```
原因: 备份目录所在磁盘空间不足
解决: 清理旧备份或使用其他存储位置
```

### 错误 4: 数据库锁定
```
原因: 数据库正在被其他进程使用
解决: 关闭所有数据库连接后再执行操作
```

## 技术细节

### 备份格式

备份使用SQLite的内置备份API，确保数据的完整性和一致性。

### 配置格式

配置文件使用JSON格式，包含:
- 版本信息
- 导出时间
- 客户列表
- 供应商列表
- 银行账户配置

### 元数据格式

元数据文件包含:
- 备份时间
- 备份文件路径
- 数据库大小
- 备份大小
- 各表记录数统计
- 配置文件信息

## 示例代码

完整的示例代码请参考:
- `examples/demo_backup_restore.py` - 备份恢复演示
- `tests/test_backup_restore.py` - 单元测试
- `test_backup_quick.py` - 快速测试

## 相关文档

- [数据导入导出说明](DATA_IMPORT_README.md)
- [数据库管理说明](../database/README.md)
- [系统使用指南](../README.md)
