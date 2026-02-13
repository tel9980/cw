# 氧化加工厂工作流程优化系统 V1.8

## 项目简介

本系统是专为氧化加工厂小白会计设计的工作流程优化系统，整合了订单管理、收付款管理、对账、报表生成等核心业务流程，提供简化、高效的财务管理工作流。

## 技术栈

- Python 3.8+
- JSON 文件存储
- pytest + hypothesis (测试框架)
- Excel 导入导出

## 项目结构

```
oxidation_workflow_v18/
├── config/              # 配置管理
├── models/              # 数据模型
├── business/            # 业务逻辑层
│   ├── orders/         # 订单管理
│   ├── accounts/       # 账户管理
│   ├── reconciliation/ # 对账引擎
│   ├── expenses/       # 支出管理
│   └── reports/        # 报表生成
├── workflow/            # 工作流引擎
├── storage/             # 数据持久化
├── ui/                  # 用户界面
├── utils/               # 工具函数
├── tests/               # 测试
│   ├── unit/           # 单元测试
│   └── properties/     # 属性测试
└── data/                # 数据文件
```

## 快速开始

1. 安装依赖：`pip install -r requirements.txt`
2. 运行测试：`pytest`
3. 启动系统：`python main.py`

## 文档

详细文档请参考 `.kiro/specs/oxidation-factory-workflow-optimization/` 目录。
