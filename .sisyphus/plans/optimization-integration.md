# oxidation_finance_v20 增量优化计划

## 目标
基于现有项目架构，修复关键问题，提升可用性，保持小白会计工作流不变。

---

## 📋 优化任务清单

### 优先级 1：紧急修复（确保能用）

#### Task 1.1: 修复演示数据生成器

**文件**: `examples/generate_comprehensive_demo.py`  
**问题**: 第20行路径设置错误，导致模块导入失败  
```python
# 当前（错误）
sys.path.insert(0, str(Path(__file__).parent))

# 改为（正确）
sys.path.insert(0, str(Path(__file__).parent.parent))
```

**验证命令**:
```bash
cd oxidation_finance_v20
python examples/generate_comprehensive_demo.py
```

**预期输出**:
```
============================================================
氧化加工厂财务系统 V2.0 - 示例数据生成器
============================================================
[OK] 正在生成客户数据...
  已生成 6 个客户
[OK] 正在生成供应商数据...
  已生成 6 个供应商
...
```

---

#### Task 1.2: 增强 quick_panel 容错性

**文件**: `tools/quick_panel.py` (第28-43行)  
**问题**: 如果数据库不存在，直接崩溃，提示不友好  
**优化**: 捕获 `FileNotFoundError`，友好引导用户

```python
def __init__(self):
    base_dir = Path(__file__).resolve().parent.parent
    self.db_path = base_dir / "oxidation_finance_demo_ready.db"
    if not self.db_path.exists():
        alt_db = Path(__file__).parent / "oxidation_finance_demo_ready.db"
        if alt_db.exists():
            self.db_path = alt_db
        else:
            demo_db = base_dir / "oxidation_finance_demo.db"
            if demo_db.exists():
                self.db_path = demo_db
            else:
                print("[ERROR] 未找到数据库文件！")
                print("请先运行示例数据生成器:")
                print("  python examples/generate_comprehensive_demo.py")
                raise FileNotFoundError("数据库不存在")
```

**验证**:
```bash
# 删除数据库后运行
python tools/quick_panel.py
# 应看到友好提示而非崩溃
```

---

### 优先级 2：功能补全（按需选择）

#### Task 2.1: 恢复报表模块（可选）

**问题**: `tests/test_report_manager.py` 抛出 `ModuleNotFoundError: No module named 'oxidation_finance_v20.reports'`

**来源**: 旧版本 `deprecated_versions/small_accountant_v16/reports/` 有完整实现

**方案**:
1. 复制 `deprecated_versions/small_accountant_v16/reports/` 到 `oxidation_finance_v20/reports/`
2. 调整导入路径（从 `small_accountant_v16.reports` 改为 `oxidation_finance_v20.reports`）
3. 如有必要，更新依赖注入

**风险**: 旧版本架构可能不完全兼容当前服务层

**验证**:
```bash
cd oxidation_finance_v20
pytest tests/test_report_manager.py -v
```

**如果不需要报表功能**: 跳过此任务，后续删除相关测试

---

### 优先级 3：工具脚本统一（可选）

#### Task 3.1: 创建统一配置模块

**目标**: 避免每个工具重复写数据库路径查找逻辑

**创建**: `oxidation_finance_v20/utils/config.py`

```python
from pathlib import Path

def get_database_path() -> Path:
    """统一获取数据库路径"""
    base_dir = Path(__file__).resolve().parent.parent
    candidates = [
        base_dir / "oxidation_finance_demo_ready.db",
        base_dir / "oxidation_finance_demo.db"
    ]
    for path in candidates:
        if path.exists():
            return path
    raise FileNotFoundError(
        "未找到数据库文件\n"
        "请先运行: python examples/generate_comprehensive_demo.py"
    )
```

**修改工具**:
- `tools/quick_panel.py`
- `tools/setup_wizard.py`
- 其他需要数据库访问的工具

**影响**: 减少重复代码，统一路径管理

---

### 优先级 4：测试验证

#### Task 4.1: 运行核心测试套件

```bash
cd oxidation_finance_v20
pytest tests/test_database.py tests/test_order_manager.py tests/test_user_manager.py tests/test_accrual_accounting.py -v
```

**预期**: 51+ 测试全部通过

#### Task 4.2: 检查其他测试模块

```bash
pytest tests/ --co -q  # 列出所有测试
# 针对因模块缺失而失败的测试（test_report, test_excel等），决定：
# - 恢复对应模块，或
# - 暂时跳过（用 -k 筛选）
```

---

### 优先级 5：提交与推送

#### Task 5.1: 提交更改

```bash
git add oxidation_finance_v20/
git commit -m "fix(demo): generate_comprehensive_demo.py import path

- Fix sys.path to parent.parent for proper module import
- Enhance quick_panel error message for missing database
- Add utils/config.py (optional) for shared config

Closes #<issue-number>"
```

#### Task 5.2: 推送到远程

```bash
git push origin master
```

---

## ✅ 验收标准

1. ✅ `python examples/generate_comprehensive_demo.py` 运行无报错
2. ✅ 生成的数据库包含充足数据（6客户、6供应商、45订单、52收入、95支出）
3. ✅ `python tools/quick_panel.py` 能显示今日概览（有数据时）或友好提示（无数据时）
4. ✅ 核心测试通过率 100%
5. ✅ 所有原始问题（裸异常、SQL注入）保持修复状态
6. ✅ 代码风格符合 AGENTS.md 规范

---

## ⚠️ 执行约束

- **不改变现有 API**: 所有工具命令行接口保持不变
- **不引入新依赖**: 仅使用已存在的库（sqlite3, pathlib, decimal, etc.）
- **保持简单**: 避免添加复杂框架或配置
- **小白友好**: 错误信息清晰，步骤明确

---

## 📊 预估工作量

| 任务 | 预估时间 | 复杂度 |
|------|----------|--------|
| Task 1.1 (路径修复) | 2分钟 | 极低 |
| Task 1.2 (友好提示) | 5分钟 | 低 |
| Task 2.1 (报表恢复) | 30分钟 | 中 |
| Task 3.1 (统一配置) | 15分钟 | 低 |
| Task 4 (测试) | 10分钟 | 低 |
| **总计** | **60分钟** | **中低** |

---

**准备就绪，请启动执行！**
