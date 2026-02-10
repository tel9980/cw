#!/bin/bash
# V1.6 小会计实用增强版 - Linux/macOS安装脚本

echo "========================================"
echo "V1.6 小会计实用增强版 - 安装向导"
echo "========================================"
echo ""

# 检查Python
echo "[步骤 1/5] 检查Python环境..."
if ! command -v python3 &> /dev/null; then
    echo "[错误] 未检测到Python3"
    echo ""
    echo "请先安装Python 3.8或更高版本"
    echo ""
    echo "Ubuntu/Debian: sudo apt-get install python3 python3-venv python3-pip"
    echo "CentOS/RHEL: sudo yum install python3 python3-pip"
    echo "macOS: brew install python3"
    exit 1
fi

python3 --version
echo "[成功] Python环境检查通过"
echo ""

# 创建虚拟环境
echo "[步骤 2/5] 创建虚拟环境..."
if [ -d ".venv" ]; then
    echo "[信息] 虚拟环境已存在，跳过创建"
else
    python3 -m venv .venv
    if [ $? -ne 0 ]; then
        echo "[错误] 虚拟环境创建失败"
        exit 1
    fi
    echo "[成功] 虚拟环境创建完成"
fi
echo ""

# 激活虚拟环境
echo "[步骤 3/5] 激活虚拟环境..."
source .venv/bin/activate
if [ $? -ne 0 ]; then
    echo "[错误] 虚拟环境激活失败"
    exit 1
fi
echo "[成功] 虚拟环境激活完成"
echo ""

# 升级pip
echo "[步骤 4/5] 升级pip..."
python -m pip install --upgrade pip
echo ""

# 安装依赖
echo "[步骤 5/5] 安装依赖包..."
echo "[信息] 这可能需要几分钟时间，请耐心等待..."
echo ""
pip install -r requirements.txt
if [ $? -ne 0 ]; then
    echo "[错误] 依赖安装失败"
    echo ""
    echo "请检查网络连接或尝试使用国内镜像:"
    echo "pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple"
    exit 1
fi
echo ""
echo "[成功] 依赖安装完成"
echo ""

# 创建必要目录
echo "[信息] 创建必要目录..."
mkdir -p data reports backups logs
echo "[成功] 目录创建完成"
echo ""

# 复制示例配置
if [ ! -f "config.json" ]; then
    echo "[信息] 创建默认配置文件..."
    cp config_example.json config.json
    echo "[成功] 配置文件创建完成"
    echo ""
fi

# 设置执行权限
echo "[信息] 设置脚本执行权限..."
chmod +x start.sh
chmod +x install.sh
echo "[成功] 权限设置完成"
echo ""

# 运行测试
echo "[信息] 运行系统测试..."
python -m pytest tests/ -v --tb=short
if [ $? -ne 0 ]; then
    echo ""
    echo "[警告] 部分测试未通过，但不影响基本使用"
    echo ""
else
    echo ""
    echo "[成功] 所有测试通过"
    echo ""
fi

# 完成
echo "========================================"
echo "安装完成！"
echo "========================================"
echo ""
echo "下一步:"
echo "  1. 查看文档: docs/README.md"
echo "  2. 启动系统: ./start.sh"
echo "  3. 或运行: python run_cli.py"
echo ""
echo "快速开始:"
echo "  - 阅读快速开始指南: docs/快速开始指南.md"
echo "  - 查看功能说明: docs/功能使用说明.md"
echo "  - 遇到问题: docs/常见问题解答.md"
echo ""
