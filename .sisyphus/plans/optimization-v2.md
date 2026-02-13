# oxidation_finance_v20 优化计划

## 目标
优化氧化加工厂财务系统，修复问题并提升代码质量

## 待办事项

### 高优先级

- [ ] 1. 修复 setup_wizard.py 中的裸异常捕获 (3处)
  - 第193行: `except:` → `except Exception:`
  - 第319行: `except:` → `except Exception:`
  - 第335行: `except:` → `except Exception:`

- [ ] 2. 修复 smart_calculator.py 中的裸异常捕获 (1处)
  - 第338行: `except:` → `except Exception:`

- [ ] 3. 修复 quick_panel.py 中的裸异常捕获 (1处)
  - 第270行: `except:` → `except Exception:`

- [ ] 4. 修复 data_quality_check.py 中的裸异常捕获 (1处)
  - 第246行: `except:` → `except Exception:`

- [ ] 5. 修复 backup_restore.py 中的异常处理 (1处)
  - 第143行: `except Exception:` 已正确，保持

### 中优先级

- [ ] 6. 添加统一日志模块
  - 创建 `oxidation_finance_v20/utils/logger.py`
  - 配置日志格式和级别

- [ ] 7. 修复 web_app.py 数据库连接泄漏
  - 使用上下文管理器或确保连接关闭

### 测试验证

- [ ] 8. 运行核心测试确认无回归
  - `pytest tests/test_database.py tests/test_user_manager.py tests/test_order_manager.py`

- [ ] 9. 提交更改到 GitHub

## 验收标准
- 所有裸异常捕获已修复
- 核心测试 100% 通过
- 代码可正常启动运行
