# CWZS 氧化加工厂财务系统 - 依赖管理

## 项目依赖包

### 核心依赖
```
# Web框架
flask>=2.3.0
flask-login>=0.6.0

# 数据处理
pandas>=2.0.0
openpyxl>=3.1.2
python-dateutil>=2.8.2

# 数据库
sqlite3  # Python标准库

# 配置管理
python-dotenv>=1.0.0

# 工具库
requests>=2.31.0
Pillow>=10.0.0
```

### 开发依赖
```
# 测试框架
pytest>=7.4.0
pytest-cov>=4.1.0
hypothesis>=6.82.0

# 代码质量
ruff>=0.1.0
black>=23.0.0
mypy>=1.5.0
```

### 可选依赖
```
# 飞书集成
lark-oapi>=3.0.0

# AI功能
zhipuai>=2.0.0
```

## 安装说明

### 安装生产环境依赖
```bash
pip install -r requirements.txt
```

### 安装开发环境依赖
```bash
pip install -r requirements-dev.txt
```

### 一键安装脚本
双击根目录的 `安装依赖.bat` 文件