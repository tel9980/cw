# 安装和设置指南

## 系统要求

- Python 3.8 或更高版本
- pip (Python 包管理器)

## 安装步骤

### 1. 创建虚拟环境（推荐）

```bash
# Windows
python -m venv venv
venv\Scripts\activate

# Linux/Mac
python3 -m venv venv
source venv/bin/activate
```

### 2. 安装依赖

```bash
pip install -r requirements.txt
```

### 3. 配置环境

复制环境配置示例文件：

```bash
# Windows
copy .env.example .env

# Linux/Mac
cp .env.example .env
```

根据需要编辑 `.env` 文件。

### 4. 运行测试

验证安装是否成功：

```bash
pytest
```

### 5. 启动系统

```bash
python main.py
```

## 配置说明

系统配置存储在 `config.json` 文件中，首次运行时会自动创建默认配置。

### 配置项说明

**存储配置 (storage)**:
- `data_path`: 数据文件存储路径（默认：./data）
- `backup_path`: 备份文件存储路径（默认：./backups）
- `log_path`: 日志文件存储路径（默认：./logs）

**备份配置 (backup)**:
- `auto_backup_enabled`: 是否启用自动备份（默认：true）
- `auto_backup_interval_hours`: 自动备份间隔（小时）（默认：24）
- `max_backup_count`: 最大备份文件数量（默认：30）
- `backup_on_exit`: 退出时是否备份（默认：true）

**系统配置 (system)**:
- `demo_mode`: 演示模式（默认：false）
- `log_level`: 日志级别（默认：INFO）
- `auto_save_enabled`: 自动保存（默认：true）
- `language`: 界面语言（默认：zh_CN）

**用户偏好 (user_preferences)**:
- `default_pricing_unit`: 默认计价单位（默认：件）
- `default_bank_account`: 默认银行账户（默认：null）
- `show_tips`: 显示操作提示（默认：true）
- `remember_last_values`: 记住上次输入值（默认：true）
- `custom_expense_categories`: 自定义支出类别（默认：[]）
- `workflow_customizations`: 工作流自定义配置（默认：{}）

## 环境变量

可以通过环境变量覆盖配置文件中的设置：

- `DATA_PATH`: 数据路径
- `BACKUP_PATH`: 备份路径
- `LOG_PATH`: 日志路径
- `AUTO_BACKUP_ENABLED`: 自动备份开关（true/false）
- `AUTO_BACKUP_INTERVAL_HOURS`: 自动备份间隔
- `DEMO_MODE`: 演示模式（true/false）
- `LOG_LEVEL`: 日志级别（DEBUG/INFO/WARNING/ERROR）

## 目录结构

安装完成后，系统会自动创建以下目录：

```
oxidation_workflow_v18/
├── data/           # 数据文件
├── backups/        # 备份文件
└── logs/           # 日志文件
```

## 故障排除

### 问题：导入模块失败

确保已激活虚拟环境并安装了所有依赖：

```bash
pip install -r requirements.txt
```

### 问题：测试失败

检查 Python 版本是否满足要求（3.8+）：

```bash
python --version
```

### 问题：权限错误

确保对数据、备份和日志目录有写入权限。

## 下一步

安装完成后，请参考以下文档：

- 用户手册：`docs/用户手册.md`（后续任务中创建）
- API 文档：`docs/API文档.md`（后续任务中创建）
- 开发指南：`docs/开发指南.md`（后续任务中创建）
