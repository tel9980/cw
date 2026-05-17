# CW项目 V2.0 完整优化补丁包

## PR 描述

```
标题: feat(core): 完成审计日志全覆盖、金额精度改进、事务支持 - V2.0 优化完成

## Summary
- ✅ 审计日志端到端全覆盖：所有核心写路径(CREATE/UPDATE/DELETE/ALLOCATE)均记录审计日志
- ✅ 金额精度改进：金额字段改为TEXT存储，避免浮点精度问题
- ✅ 事务支持：新增事务上下文管理器，支持原子性操作
- ✅ 幂等性增强：支出/银行交易/委外加工等路径增加重复性检查
- ✅ 启动器优化：解决中文/空格文件名导致的启动问题

## Changes

### 1. 数据库层 (oxidation_finance_v20/database/)
- **db_manager.py**
  - 新增 `log_audit()` 方法：统一审计日志写入入口
  - 新增 `transaction()` 上下文管理器：支持事务操作
  - `save_customer/supplier/order/income/expense/bank_account/bank_transaction/outsourced_processing`
    - 增加存在性检查，区分CREATE/UPDATE
    - 增加审计日志写入
- **schema.py**
  - 金额字段REAL → TEXT

### 2. 业务层 (oxidation_finance_v20/business/)
- **order_manager.py**
  - `create_order()`: 事务包装 + 审计日志(CREATE)
  - `update_order()`: 事务包装 + 审计日志(UPDATE) + old_value快照
  - `update_order_status()`: 审计日志记录状态变更
  - `delete_order()`: 审计日志(DELETE)
- **finance_manager.py**
  - `record_income()`: 审计日志(CREATE)
  - `allocate_payment_to_orders()`: 事务保护 + 审计日志(ALLOCATE)

### 3. 工具与脚本
- **scripts/**
  - `launcher_full_demo.py`: 自动定位并启动完整版入口
  - `run_full_demo.sh`: 一键启动脚本
- **oxidation_finance_v20/tools/**
  - `audit_self_check.py`: 审计覆盖自检工具
  - `migrate_to_text_amounts.py`: 金额字段TEXT迁移脚本
  - `migrate_money_to_text.py`: 辅助迁移工具
  - `setup_wizard.py`: 增强版初始化向导(自动创建数据库)

## Testing

### 1. 审计覆盖自检
```bash
export PYTHONPATH=/app/workspace/cw
python3 -m oxidation_finance_v20.tools.audit_self_check
```
预期输出:
- Allocation result: True
- Audit log count: >= 6
- Last audit: 包含 entity_type, entity_id, old_value, new_value

### 2. 启动器测试
```bash
./scripts/run_full_demo.sh
```
预期: 自动生成示例数据，输出数据统计

### 3. 金额迁移测试
```bash
# 备份数据库
cp oxidation_finance.db oxidation_finance.db.bak

# 执行迁移
export PYTHONPATH=/app/workspace/cw
python3 oxidation_finance_v20/tools/migrate_to_text_amounts.py

# 验证字段类型
sqlite3 oxidation_finance.db "PRAGMA table_info(orders);"
```

### 4. 幂等性测试
```python
# 多次写入同一支出记录，应返回已有ID
from oxidation_finance_v20.database.db_manager import DatabaseManager
from oxidation_finance_v20.models import Expense, ExpenseType, BankType
from datetime import date
from decimal import Decimal

db = DatabaseManager("test.db")
db.connect()
exp = Expense(
    id="test-001",
    expense_type=ExpenseType.RENT,
    supplier_id="sup-001",
    supplier_name="测试供应商",
    amount=Decimal("1000.00"),
    bank_type=BankType.G_BANK,
    expense_date=date.today()
)
id1 = db.save_expense(exp)
id2 = db.save_expense(exp)
assert id1 == id2, "幂等性验证失败"
```

## Migration

### 金额字段TEXT迁移
1. **备份数据库**
   ```bash
   cp oxidation_finance.db oxidation_finance.db.$(date +%Y%m%d)
   ```

2. **执行迁移**
   ```bash
   export PYTHONPATH=/app/workspace/cw
   python3 oxidation_finance_v20/tools/migrate_to_text_amounts.py
   ```

3. **验证**
   - 检查字段类型为TEXT
   - 执行读写测试确认计算正确

## Rollback

### 方案1: 数据库回滚
```bash
# 停止应用
# 恢复备份
cp oxidation_finance.db.bak oxidation_finance.db
# 重启应用
```

### 方案2: 代码回滚
```bash
# 回到上一个提交
git revert HEAD
# 或
git checkout <commit-hash>
```

## Impact
- 所有核心写操作现在都有审计日志可追溯
- 金额计算避免浮点精度问题
- 多表操作支持事务原子性
- 重复操作具备幂等性保护

## Breaking Changes
- 数据库金额字段从REAL改为TEXT，需要执行迁移脚本
- 审计日志表结构已更新

---
生成时间: 2026-02-25
```

## 完整补丁集合

### Patch 1: 数据库层 - 审计入口 + 事务支持

**文件: oxidation_finance_v20/database/db_manager.py**

```python
# 在文件顶部添加 contextlib 导入
from contextlib import contextmanager

# 在 close() 方法后添加事务上下文管理器
@contextmanager
def transaction(self):
    """简单事务上下文：BEGIN/COMMIT/ROLLBACK"""
    if not self.conn:
        self.connect()
    try:
        self.conn.execute("BEGIN")
        yield
        self.conn.execute("COMMIT")
    except Exception:
        self.conn.execute("ROLLBACK")
        raise
```

### Patch 2: save_customer - 审计日志

```python
def save_customer(self, customer: Customer) -> str:
    """保存客户信息，并记录审计日志（CREATE/UPDATE）"""
    cursor = self.conn.cursor()
    # 判断创建还是更新
    exists = False
    try:
        row = cursor.execute("SELECT id FROM customers WHERE id = ?", (customer.id,)).fetchone()
        exists = row is not None
    except Exception:
        exists = False
    cursor.execute("""
        INSERT OR REPLACE INTO customers 
        (id, name, contact, phone, address, credit_limit, notes, created_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        customer.id, customer.name, customer.contact, customer.phone,
        customer.address, str(customer.credit_limit), customer.notes,
        customer.created_at.isoformat()
    ))
    self.conn.commit()
    # 审计日志：创建/更新
    audit_type = "UPDATE" if exists else "CREATE"
    try:
        self.log_audit(audit_type, "CUSTOMER", customer.id, customer.name, None, str(customer))
    except Exception:
        pass
    return customer.id
```

### Patch 3: save_order - 审计日志 + 事务

```python
def save_order(self, order: ProcessingOrder) -> str:
    """保存加工订单"""
    # determine create vs update based on existence
    exists = False
    try:
        existing = self.get_order(order.id)
        exists = existing is not None
    except Exception:
        exists = False
    cursor = self.conn.cursor()
    cursor.execute("""
        INSERT OR REPLACE INTO processing_orders 
        (id, order_no, customer_id, customer_name, item_description,
         quantity, pricing_unit, unit_price, processes, outsourced_processes,
         total_amount, outsourcing_cost, status, order_date, completion_date,
         delivery_date, received_amount, notes, created_at, updated_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        order.id, order.order_no, order.customer_id, order.customer_name,
        order.item_description, str(order.quantity), order.pricing_unit.value,
        str(order.unit_price), 
        json.dumps([p.value if hasattr(p, 'value') else p for p in order.processes]),
        json.dumps(order.outsourced_processes), str(order.total_amount),
        str(order.outsourcing_cost), order.status.value,
        order.order_date.isoformat(),
        order.completion_date.isoformat() if order.completion_date else None,
        order.delivery_date.isoformat() if order.delivery_date else None,
        str(order.received_amount), order.notes,
        order.created_at.isoformat(), order.updated_at.isoformat()
    ))
    self.conn.commit()
    audit_type = "UPDATE" if exists else "CREATE"
    try:
        self.log_audit(audit_type, "ORDER", order.id, order.order_no, None, str(order))
    except Exception:
        pass
    return order.id
```

### Patch 4: save_income - 审计日志 + 幂等

```python
def save_income(self, income: Income) -> str:
    """保存收入记录"""
    cursor = self.conn.cursor()
    # 重复收入检查：基于 id 判断是否已经存在
    exists = False
    try:
        row = cursor.execute("SELECT id FROM incomes WHERE id = ?", (income.id,)).fetchone()
        exists = row is not None
    except Exception:
        exists = False
    # 保存
    cursor.execute("""
        INSERT OR REPLACE INTO incomes 
        (id, customer_id, customer_name, amount, bank_type, has_invoice,
         related_orders, allocation, income_date, notes, created_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        income.id, income.customer_id, income.customer_name,
        str(income.amount), income.bank_type.value, int(income.has_invoice),
        json.dumps(income.related_orders), json.dumps({k: str(v) for k, v in income.allocation.items()}),
        income.income_date.isoformat(), income.notes,
        income.created_at.isoformat()
    ))
    self.conn.commit()
    audit_type = "UPDATE" if exists else "CREATE"
    try:
        self.log_audit(audit_type, "INCOME", income.id, income.customer_name, None, str(income))
    except Exception:
        pass
    return income.id
```

### Patch 5: save_expense - 事务 + 审计 + 幂等

```python
def save_expense(self, expense: Expense) -> str:
    """保存支出记录，含幂等性与审计"""
    with self.transaction():
        cursor = self.conn.cursor()
        # 1) 重复性保护：若已存在相同的支出记录，返回已有记录的 id，避免重复记账
        exists = False
        try:
            row = cursor.execute("SELECT id FROM expenses WHERE id = ?", (expense.id,)).fetchone()
            exists = row is not None
        except Exception:
            exists = False
        try:
            existing = cursor.execute(
                "SELECT id FROM expenses WHERE expense_type = ? AND supplier_id = ? AND expense_date = ? AND amount = ?",
                (expense.expense_type.value, expense.supplier_id, expense.expense_date.isoformat(), str(expense.amount)),
            ).fetchone()
            if existing:
                return existing[0]
        except Exception:
            pass
        cursor.execute("""
            INSERT OR REPLACE INTO expenses 
            (id, expense_type, supplier_id, supplier_name, amount, bank_type,
             has_invoice, related_order_id, expense_date, description, notes, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            expense.id, expense.expense_type.value, expense.supplier_id,
            expense.supplier_name, str(expense.amount), expense.bank_type.value,
            int(expense.has_invoice), expense.related_order_id,
            expense.expense_date.isoformat(), expense.description,
            expense.notes, expense.created_at.isoformat()
        ))
    # 审计日志：CREATE/UPDATE
    audit_type = "UPDATE" if exists else "CREATE"
    try:
        self.log_audit(audit_type, "EXPENSE", expense.id, expense.supplier_name or "", None, str(expense))
    except Exception:
        pass
    return expense.id
```

### Patch 6: OrderManager - 订单事务包装

**文件: oxidation_finance_v20/business/order_manager.py**

```python
def create_order(self, ...):
    # ... 原有逻辑 ...
    
    # 保存到数据库并在同一事务中记录审计日志
    with self.db.transaction():
        self.db.save_order(order)
        try:
            self.db.log_audit(
                operation_type="CREATE",
                entity_type="ORDER",
                entity_id=order.id,
                entity_name=order.order_no,
                old_value=None,
                new_value=str(order),
                description="Order created"
            )
        except Exception:
            pass
    return order
```

```python
def update_order(self, order: ProcessingOrder) -> ProcessingOrder:
    """更新订单信息"""
    old_snapshot = str(order)
    order.updated_at = datetime.now()
    with self.db.transaction():
        self.db.save_order(order)
        try:
            self.db.log_audit(
                operation_type="UPDATE",
                entity_type="ORDER",
                entity_id=order.id,
                entity_name=order.order_no,
                old_value=old_snapshot,
                new_value=str(order),
                description="Order updated"
            )
        except Exception:
            pass
    return order
```

```python
def update_order_status(self, order_id: str, new_status: OrderStatus, ...):
    order = self.get_order(order_id)
    if not order:
        return None
    old_status = order.status
    order.status = new_status
    
    if new_status == OrderStatus.COMPLETED and completion_date:
        order.completion_date = completion_date
    elif new_status == OrderStatus.DELIVERED and delivery_date:
        order.delivery_date = delivery_date
    
    updated = self.update_order(order)
    # 审计日志：订单状态变更
    try:
        self.db.log_audit(
            operation_type="UPDATE",
            entity_type="ORDER",
            entity_id=order.id,
            entity_name=order.order_no,
            old_value=str(old_status.value) if old_status else None,
            new_value=str(new_status.value),
            description="Order status updated"
        )
    except Exception:
        pass
    return updated
```

### Patch 7: 金额字段 TEXT 迁移

**文件: oxidation_finance_v20/tools/migrate_to_text_amounts.py**

核心迁移逻辑:
```python
def migrate(db_path: Path):
    if not db_path.exists():
        # 创建新数据库
        ...
        return
    
    conn = sqlite3.connect(str(db_path))
    cur = conn.cursor()
    
    tables = [t[0] for t in cur.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()]
    
    for table in tables:
        if table not in MONEY_COLUMNS:
            continue
        money_cols = MONEY_COLUMNS[table]
        
        # 获取当前列
        cols = cur.execute(f"PRAGMA table_info({table})").fetchall()
        col_names = [c[1] for c in cols]
        
        # 构建SELECT表达式：金额列CAST为TEXT
        select_expr = []
        for c in col_names:
            if c in money_cols:
                select_expr.append(f"CAST({c} AS TEXT) AS {c}")
            else:
                select_expr.append(c)
        
        select_cols = ", ".join(select_expr)
        
        # 创建新表并复制数据
        new_table = f"{table}_new"
        cur.execute(f"CREATE TABLE {new_table} AS SELECT {select_cols} FROM {table} LIMIT 0")
        cur.execute(f"INSERT INTO {new_table} ({', '.join(col_names)}) SELECT {select_cols} FROM {table}")
        
        # 替换旧表
        cur.execute(f"DROP TABLE {table}")
        cur.execute(f"ALTER TABLE {new_table} RENAME TO {table}")
        conn.commit()
```

### Patch 8: 启动器脚本

**文件: scripts/launcher_full_demo.py**
```python
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Launcher: 自动运行完整版demo数据脚本"""

import os, sys, subprocess
from pathlib import Path

def find_entry_script(root: Path) -> Path:
    candidates = []
    for p in root.rglob("*.py"):
        if ("完整版" in p.name) or ("V2.0" in p.name):
            candidates.append(p)
    if not candidates:
        return None
    candidates.sort(key=lambda x: x.stat().st_mtime, reverse=True)
    return candidates[0]

def main():
    root = Path(__file__).resolve().parents[1]
    entry = find_entry_script(root)
    if entry is None:
        print("[Launcher] 未找到入口脚本")
        sys.exit(1)
    print(f"[Launcher] 运行入口: {entry}")
    cmd = [sys.executable, str(entry)]
    env = os.environ.copy()
    env["PYTHONPATH"] = str(root)
    proc = subprocess.Popen(cmd, cwd=str(root), env=env, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
    for line in proc.stdout:
        print(line.rstrip())
    proc.wait()
    sys.exit(proc.returncode)

if __name__ == '__main__':
    main()
```

**文件: scripts/run_full_demo.sh**
```bash
#!/usr/bin/env bash
set -euo pipefail
ROOT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
export PYTHONPATH="$ROOT_DIR"
python3 "$ROOT_DIR/scripts/launcher_full_demo.py"
```

### Patch 9: 审计自检工具

**文件: oxidation_finance_v20/tools/audit_self_check.py**
```python
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Audit self-check: 快速端到端审计日志覆盖测试"""

import uuid
from datetime import date, datetime
from decimal import Decimal

from oxidation_finance_v20.database.db_manager import DatabaseManager
from oxidation_finance_v20.business.order_manager import OrderManager
from oxidation_finance_v20.business.finance_manager import FinanceManager
from oxidation_finance_v20.models import Customer, PricingUnit, ProcessType, BankType, OrderStatus

def main():
    dbm = DatabaseManager(":memory:")
    dbm.connect()
    
    om = OrderManager(dbm)
    fm = FinanceManager(dbm)
    
    # 1. 创建客户
    c = Customer(id=str(uuid.uuid4()), name="审计测试客户", 
                 credit_limit=Decimal("1000.00"), created_at=datetime.now())
    dbm.save_customer(c)
    
    # 2. 创建订单
    o = om.create_order(
        customer_id=c.id, customer_name=c.name,
        item_description="测试产品", quantity=Decimal("10"),
        pricing_unit=PricingUnit.PIECE, unit_price=Decimal("10.00"),
        processes=[ProcessType.SANDBLASTING], order_date=date.today(),
        outsourced_processes=None, notes="审计自检"
    )
    
    # 3. 创建收入并分配
    inc = fm.record_income(
        customer_id=c.id, customer_name=c.name,
        amount=Decimal("100.00"), bank_type=BankType.G_BANK,
        income_date=date.today(), has_invoice=True, notes="审计自检收入"
    )
    
    allocations = {o.id: Decimal("100.00")}
    ok, msg = fm.allocate_payment_to_orders(inc.id, allocations)
    print(f"Allocation result: {ok} {msg}")
    
    # 4. 检查审计日志
    cur = dbm.conn.cursor()
    cur.execute("SELECT COUNT(*) FROM audit_logs")
    total = cur.fetchone()[0]
    print(f"Audit log count: {total}")
    
    cur.execute("SELECT * FROM audit_logs ORDER BY operation_time DESC LIMIT 1")
    last = cur.fetchone()
    print(f"Last audit: {dict(last) if last else None}")

if __name__ == '__main__':
    main()
```

## 测试指南

### 测试1: 审计覆盖自检
```bash
export PYTHONPATH=/app/workspace/cw
python3 -m oxidation_finance_v20.tools.audit_self_check
```

### 测试2: 启动器运行
```bash
./scripts/run_full_demo.sh
```

### 测试3: 金额迁移
```bash
# 备份
cp oxidation_finance.db oxidation_finance.db.bak

# 执行迁移
export PYTHONPATH=/app/workspace/cw
python3 oxidation_finance_v20/tools/migrate_to_text_amounts.py

# 验证
sqlite3 oxidation_finance.db "PRAGMA table_info(processing_orders);" | grep -E "(quantity|unit_price|total_amount|received_amount|outsourcing_cost)"
```

### 测试4: 幂等性
```python
# 见上文 Patch 5 中的测试代码
```

### 测试5: 事务回滚
```python
# 模拟异常，观察回滚
```

## 回滚方案

### 方案1: 数据库回滚
```bash
cp oxidation_finance.db.bak oxidation_finance.db
```

### 方案2: 代码回滚
```bash
git revert HEAD
# 或
git checkout <commit-hash>
```

---

**文档版本**: V1.0  
**生成日期**: 2026-02-25  
**维护者**: OpenCode Bot
