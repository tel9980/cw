# 🏭 氧化加工厂财务系统 V2.0 + 小会计财务管理系统

---

## 🚀 快速开始 - 氧化加工厂专版

### 方法1: 主菜单启动 (推荐)

```bash
双击: 启动_主菜单.bat
```

### 方法2: Web界面

```bash
双击: 启动_Web版.bat
# 浏览器访问: http://localhost:5000
# 默认登录: admin / admin123
```

### 方法3: 命令行

```bash
cd oxidation_finance_v20
python tools/quick_panel.py  # 今日概览
```

---

## ✨ 氧化加工厂财务系统 V2.0 功能

| 模块 | 功能 |
|------|------|
| **订单管理** | CRUD + 5种状态追踪 |
| **收入管理** | G银行(有票) / N银行(微信) |
| **支出管理** | 12种支出类型 |
| **客户管理** | 信用额度、联系方式 |
| **报表** | 月度统计、客户排名 |
| **权限** | 4角色 × 22权限 |

### 技术栈

- Python 3.8+ / SQLite / Flask
- 35个单元测试全部通过

---

## 📦 版本说明

### 🏭 氧化加工厂专版 V2.0 (推荐)

**位置**: `oxidation_finance_v20/`

**核心功能**:
- ✅ Web界面 + CLI工具
- ✅ 用户权限系统
- ✅ 操作日志审计
- ✅ 9个命令行工具

**快速开始**:
```bash
cd oxidation_finance_v20
python web_app.py  # 启动Web服务
```

### 小会计通用版 V1.6

**位置**: `small_accountant_v16/`

**适合**: 小微企业日常财务管理

**适合**: 加工制造行业

**特色功能**:
- 订单管理
- 加工流程追踪
- 成本核算

## 🚀 5分钟快速上手

### 1. 安装系统

```bash
# 克隆项目
git clone https://github.com/tel9980/cw.git
cd cw

# 进入V1.6目录
cd small_accountant_v16

# 安装（Windows）
install.bat

# 安装（Linux/Mac）
chmod +x install.sh
./install.sh
```

### 2. 启动系统

```bash
# Windows
start.bat

# Linux/Mac
./start.sh
```

### 3. 导入示例数据

```bash
# 生成示例数据
python examples/generate_sample_data.py

# 然后在系统中导入Excel文件
```

## 📊 主要功能

### 1. 智能报表 📈

一键生成专业财务报表：
- 管理报表：收支对比、利润趋势、客户排名
- 税务报表：增值税、所得税申报表
- 银行报表：资产负债表、利润表、现金流量表

### 2. 智能提醒 🔔

永不错过重要事项：
- 税务申报截止日期提醒
- 应付账款到期提醒
- 应收账款逾期催收（自动生成催款函）
- 现金流预警

### 3. 快速对账 🔄

轻松完成对账工作：
- 银行流水自动匹配
- 一键生成客户对账单
- 供应商对账核对

### 4. Excel导入 📥

快速导入历史数据：
- 智能识别Excel列名
- 导入前数据验证
- 支持撤销错误导入

## 💡 使用场景

### 小微企业
- 日常收支记录
- 月度财务报表
- 税务申报准备

### 个体工商户
- 简单记账
- 客户对账
- 收款提醒

### 初创公司
- 财务数据管理
- 银行贷款材料
- 投资人报表

## 📖 文档导航

- [V1.6 快速开始](small_accountant_v16/docs/快速开始指南.md)
- [V1.6 功能说明](small_accountant_v16/docs/功能使用说明.md)
- [V1.6 常见问题](small_accountant_v16/docs/常见问题解答.md)
- [V1.5 工作流文档](workflow_v15/README.md)
- [氧化厂文档](oxidation_factory/README.md)

## 🔧 系统要求

- Python 3.8+
- Windows/Linux/macOS
- 100MB 磁盘空间
- 2GB 内存（推荐）

## 📈 数据量支持

- **V1.6**: < 10,000条交易记录（JSON存储）
- **未来版本**: 支持SQLite，可处理更大数据量

## 🛡️ 数据安全

- 本地存储，数据完全掌控
- 自动配置备份（保留10个版本）
- 支持手动数据备份
- 导入撤销功能

## 🎓 学习资源

### 新手入门
1. [小白落地指南](小白落地指南.md)
2. [图解教程](图解教程_3步上手.txt)
3. [快速开始](快速开始_看这里.txt)

### 进阶使用
1. [V1.6 功能详解](small_accountant_v16/docs/功能使用说明.md)
2. [常见问题解答](small_accountant_v16/docs/常见问题解答.md)

## 🔄 版本历史

- **V1.6** (2026-02) - 实用增强版，完整功能
- **V1.5** (2026-01) - 工作流优化版
- **V1.4** (2025-12) - 增强版
- **V1.3** (2025-11) - 全能版
- **V1.2** (2025-10) - 优化版
- **V1.1** (2025-09) - 初始版本

## 🤝 贡献

欢迎提交问题和建议！

## 📄 许可证

本项目仅供学习和内部使用

## 📞 支持

- 查看文档：`small_accountant_v16/docs/`
- 查看日志：`small_accountant_v16/logs/`
- GitHub Issues: [提交问题](https://github.com/tel9980/cw/issues)

## ⚡ 快速命令

```bash
# V1.6 系统
cd small_accountant_v16
python run_cli.py              # 启动系统
python run_cli.py --status     # 查看状态
python run_cli.py --verify     # 验证数据
python run_cli.py --debug      # 调试模式

# 生成示例数据
python examples/generate_sample_data.py

# 运行测试
python -m pytest tests/ -v
```

## 🎉 开始使用

```bash
cd small_accountant_v16
install.bat  # 或 ./install.sh
start.bat    # 或 ./start.sh
```

**祝您使用愉快！** 💼

---

**小会计** - 让财务管理变简单
