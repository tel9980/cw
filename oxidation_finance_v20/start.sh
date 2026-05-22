#!/bin/bash
# 氧化加工厂财务系统 - 快速启动脚本

echo "=========================================="
echo "  🏭 氧化加工厂财务系统"
echo "=========================================="

# 检查是否已初始化
if [ ! -f "oxidation_finance_demo_ready.db" ]; then
    echo ""
    echo "📦 首次使用，正在初始化系统..."
    python3 init.py
else
    echo ""
    echo "✅ 系统已初始化，直接启动Web应用"
    echo ""
    echo "按 Ctrl+C 停止服务"
    echo "=========================================="
    echo ""
    python3 web_app.py
fi
