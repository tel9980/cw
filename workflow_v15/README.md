# V1.5 Small Accountant Workflow Optimization

## 概述

V1.5 小会计工作流优化模块是在现有 V1.4 增强版基础上构建的智能工作流系统，专为小企业会计设计。

## 核心特性

### 1. 工作流引擎 (WorkflowEngine)
- 编排多步骤财务流程
- 维护工作流状态
- 提供智能的下一步建议
- 支持工作流自定义

### 2. 上下文引擎 (ContextEngine)
- 分析用户行为模式
- 预测下一步操作
- 生成智能默认值
- 从用户纠正中学习

### 3. 渐进式披露管理器 (ProgressiveDisclosureManager)
- 限制主要操作数量（最多5个）
- 根据使用频率调整菜单
- 提供上下文帮助
- 隐藏高级功能直到需要时

### 4. 自动化层 (AutomationLayer)
- 检测重复任务模式
- 创建自动化规则
- 执行自动化任务
- 管理定期任务

## 模块结构

```
workflow_v15/
├── __init__.py              # 模块入口
├── README.md                # 本文件
├── core/                    # 核心引擎
│   ├── __init__.py
│   ├── workflow_engine.py   # 工作流引擎
│   ├── context_engine.py    # 上下文引擎
│   ├── progressive_disclosure.py  # 渐进式披露管理器
│   └── automation_layer.py  # 自动化层
├── models/                  # 数据模型
│   ├── __init__.py
│   ├── workflow_models.py   # 工作流相关模型
│   ├── context_models.py    # 上下文相关模型
│   └── automation_models.py # 自动化相关模型
└── tests/                   # 测试
    ├── __init__.py
    ├── conftest.py          # 测试配置
    └── test_setup.py        # 基础测试

## 快速开始

### 安装依赖

```bash
pip install -r requirements.txt
```

### 基本使用

```python
from workflow_v15 import WorkflowEngine, ContextEngine

# 创建工作流引擎
engine = WorkflowEngine()

# 启动早晨工作流
session = engine.start_workflow(
    workflow_type="morning_setup",
    context={"user_id": "user_001"}
)

# 执行步骤
result = engine.execute_step(
    session_id=session.session_id,
    step_data={"action": "review_tasks"}
)

# 获取下一步建议
suggestions = engine.get_next_suggestions(session.session_id)
```

### 上下文分析

```python
from workflow_v15 import ContextEngine

# 创建上下文引擎
context_engine = ContextEngine()

# 分析当前上下文
analysis = context_engine.analyze_current_context(user_id="user_001")

# 生成智能默认值
defaults = context_engine.generate_smart_defaults(
    transaction_type="income",
    context={"customer": "客户A"}
)

# 获取个性化仪表板
dashboard = context_engine.get_personalized_dashboard(user_id="user_001")
```

## 测试

运行所有测试：

```bash
pytest workflow_v15/tests/ -v
```

运行特定测试：

```bash
pytest workflow_v15/tests/test_setup.py -v
```

## 与 V1.4 的兼容性

V1.5 模块设计为与现有 V1.4 代码完全兼容：

- V1.5 组件可以独立使用
- 不影响现有 V1.4 功能
- 可以逐步迁移到 V1.5 工作流
- 共享相同的数据存储

## 开发指南

### 添加新的工作流模板

```python
from workflow_v15.models.workflow_models import WorkflowTemplate, WorkflowStep, WorkflowType

template = WorkflowTemplate(
    template_id="custom_workflow_v1",
    name="自定义工作流",
    description="描述",
    workflow_type=WorkflowType.CUSTOM,
    steps=[
        WorkflowStep(
            step_id="step1",
            name="步骤1",
            description="步骤描述",
            function_codes=["1", "2"]
        )
    ]
)

engine.templates[template.template_id] = template
```

### 扩展上下文分析

继承 `ContextEngine` 类并重写相关方法：

```python
class CustomContextEngine(ContextEngine):
    def _generate_priorities(self, user_patterns, time_context, pending_tasks):
        # 自定义优先级生成逻辑
        priorities = super()._generate_priorities(user_patterns, time_context, pending_tasks)
        # 添加自定义优先级
        return priorities
```

## 配置

### Hypothesis 测试配置

在 `tests/conftest.py` 中配置：

- `default`: 100次迭代（默认）
- `ci`: 1000次迭代（CI环境）
- `dev`: 10次迭代（开发环境）

## 性能考虑

- 工作流会话自动保存到磁盘
- 用户模式缓存在内存中
- 活动历史限制在最近24小时
- 建议操作最多返回5个

## 未来计划

- [ ] 机器学习模型集成
- [ ] 移动端界面适配
- [ ] 离线模式支持
- [ ] 高级自动化规则
- [ ] 多用户协作功能

## 许可证

与主项目相同

## 贡献

欢迎提交问题和拉取请求！
