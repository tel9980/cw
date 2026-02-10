# V1.6 小会计实用增强版

专为小微企业设计的财务管理系统，提供智能报表生成、智能提醒、快速对账和Excel批量导入功能。

## 快速开始

### Windows用户

```batch
# 1. 安装系统
install.bat

# 2. 启动系统
start.bat
```

### Linux/macOS用户

```bash
# 1. 设置执行权限
chmod +x install.sh start.sh

# 2. 安装系统
./install.sh

# 3. 启动系统
./start.sh
```

## 系统要求

- Python 3.8 或更高版本
- 100MB 可用磁盘空间
- 2GB 内存（推荐）

## 主要功能

### 1. 智能报表生成 📊

一键生成专业财务报表：
- **管理报表**：收支对比、利润趋势、客户排名
- **税务报表**：增值税、所得税申报表
- **银行贷款报表**：资产负债表、利润表、现金流量表

### 2. 智能提醒系统 🔔

永不错过重要事项：
- **税务提醒**：增值税、所得税申报截止日期
- **应付账款提醒**：供应商付款到期提醒
- **应收账款提醒**：客户逾期账款催收（自动生成催款函）
- **现金流预警**：资金短缺提前预警

### 3. 快速对账助手 🔄

轻松完成银行对账：
- **银行流水对账**：自动匹配交易记录
- **客户对账单**：一键生成客户对账单
- **供应商对账**：核对应付账款

### 4. Excel批量导入 📥

快速导入历史数据：
- **智能列识别**：自动识别Excel列名
- **数据验证**：导入前验证数据完整性
- **导入预览**：查看导入结果再确认
- **撤销功能**：支持撤销错误导入

## 目录结构

```
small_accountant_v16/
├── config/              # 配置管理
├── models/              # 数据模型
├── storage/             # 数据存储
├── import_engine/       # 导入引擎
├── reports/             # 报表生成
├── reminders/           # 提醒系统
├── reconciliation/      # 对账助手
├── ui/                  # 用户界面
├── core/                # 核心功能
├── tests/               # 测试代码
├── docs/                # 用户文档
├── data/                # 数据文件（运行时创建）
├── reports/             # 生成的报表（运行时创建）
├── backups/             # 配置备份（运行时创建）
├── logs/                # 系统日志（运行时创建）
├── requirements.txt     # Python依赖
├── config_example.json  # 示例配置文件
├── run_cli.py           # 启动脚本
├── install.bat          # Windows安装脚本
├── install.sh           # Linux/macOS安装脚本
├── start.bat            # Windows启动脚本
└── start.sh             # Linux/macOS启动脚本
```

## 使用文档

详细文档请查看 `docs/` 目录：

- **[快速开始指南](docs/快速开始指南.md)** - 5分钟快速上手
- **[功能使用说明](docs/功能使用说明.md)** - 详细功能说明
- **[常见问题解答](docs/常见问题解答.md)** - FAQ和问题解决
- **[日常使用指南](日常使用指南.md)** - 小会计系统日常使用流程
- **[小企业会计工作全清单](小企业会计工作全清单.md)** - 小企业所有财务工作清单

## 命令行选项

```bash
# 启动CLI界面
python run_cli.py

# 查看系统状态
python run_cli.py --status

# 验证数据完整性
python run_cli.py --verify

# 启用调试模式
python run_cli.py --debug

# 显示帮助信息
python run_cli.py --help
```

## 配置文件

首次运行会自动创建 `config.json` 配置文件。

主要配置项：

```json
{
  "storage": {
    "data_dir": "data",
    "report_output_dir": "reports",
    "backup_dir": "backups"
  },
  "reminder": {
    "tax_reminder_days": [10, 7, 5, 3, 1, 0],
    "enable_desktop_notification": true,
    "enable_wechat_notification": false
  },
  "wechat": {
    "enabled": false,
    "webhook_url": "YOUR_WEBHOOK_URL"
  }
}
```

详细配置说明请参考 `config_example.json`。

## 企业微信通知配置

1. 登录企业微信管理后台
2. 创建群机器人
3. 复制Webhook URL
4. 在系统配置中启用企业微信通知并填入URL

## 运行测试

```bash
# 运行所有测试
python -m pytest tests/ -v

# 运行特定测试
python -m pytest tests/test_integration.py -v

# 查看测试覆盖率
python -m pytest tests/ --cov=small_accountant_v16 --cov-report=html
```

## 数据备份

系统会自动备份配置文件，保留最近10个备份。

手动备份数据：

```bash
# Windows
xcopy /E /I data backups\data_backup_%date:~0,4%%date:~5,2%%date:~8,2%

# Linux/macOS
cp -r data backups/data_backup_$(date +%Y%m%d)
```

## 故障排除

### 问题：Python未找到

**Windows**：
- 下载并安装Python：https://www.python.org/downloads/
- 安装时勾选 "Add Python to PATH"

**Linux/macOS**：
```bash
# Ubuntu/Debian
sudo apt-get install python3 python3-venv python3-pip

# macOS
brew install python3
```

### 问题：依赖安装失败

尝试使用国内镜像：

```bash
pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple
```

### 问题：桌面通知不显示

安装plyer库：

```bash
pip install plyer
```

检查系统通知权限设置。

### 更多问题

查看 [常见问题解答](docs/常见问题解答.md)

## 技术栈

- **Python 3.8+** - 编程语言
- **openpyxl** - Excel文件处理
- **pandas** - 数据分析
- **matplotlib** - 图表生成
- **pytest** - 测试框架
- **Hypothesis** - 属性测试

## 版本信息

**当前版本**：V1.6 实用增强版

**主要特性**：
- ✅ 智能报表生成（管理/税务/银行贷款）
- ✅ 智能提醒系统（税务/应收应付/现金流）
- ✅ 快速对账助手（银行/客户/供应商）
- ✅ Excel批量导入（智能识别/验证/撤销）
- ✅ 统一错误处理（中文提示/日志记录）
- ✅ 配置管理（备份/恢复/导入导出）

## 许可证

本项目仅供学习和内部使用。

## 联系方式

如有问题或建议，请查看文档或联系技术支持。

---

**祝您使用愉快！** 🎉
