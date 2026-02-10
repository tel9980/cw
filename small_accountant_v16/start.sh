#!/bin/bash
# V1.6 小会计实用增强版 - Linux/macOS启动脚本

echo "========================================"
echo "V1.6 小会计实用增强版"
echo "========================================"
echo ""

# 检查Python是否安装
if ! command -v python3 &> /dev/null; then
    echo "[错误] 未检测到Python3，请先安装Python 3.8或更高版本"
    exit 1
fi

echo "[信息] Python版本:"
python3 --version
echo ""

# 检查虚拟环境
if [ ! -d ".venv" ]; then
    echo "[信息] 首次运行，正在创建虚拟环境..."
    python3 -m venv .venv
    if [ $? -ne 0 ]; then
        echo "[错误] 虚拟环境创建失败"
        exit 1
    fi
    echo "[成功] 虚拟环境创建完成"
    echo ""
fi

# 激活虚拟环境
echo "[信息] 激活虚拟环境..."
source .venv/bin/activate
if [ $? -ne 0 ]; then
    echo "[错误] 虚拟环境激活失败"
    exit 1
fi

# 检查依赖是否安装
python -c "import openpyxl" &> /dev/null
if [ $? -ne 0 ]; then
    echo "[信息] 首次运行，正在安装依赖..."
    pip install -r requirements.txt
    if [ $? -ne 0 ]; then
        echo "[错误] 依赖安装失败"
        exit 1
    fi
    echo "[成功] 依赖安装完成"
    echo ""
fi

# 启动系统
echo "[信息] 启动系统..."
echo ""
python run_cli.py

# 检查退出状态
if [ $? -ne 0 ]; then
    echo ""
    echo "[错误] 系统运行出错"
    exit 1
fi
