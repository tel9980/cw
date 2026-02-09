@echo off
chcp 65001 >nul
title 氧化加工厂财务助手 V1.1 - 优化版

echo.
echo ═══════════════════════════════════════════════════════════════════
echo     氧化加工厂财务助手 V1.1 - 优化版
echo ═══════════════════════════════════════════════════════════════════
echo.
echo 💡 V1.1 新功能：
echo   ✅ 订单自动保存到本地（无需飞书）
echo   ✅ 查看订单列表和详情
echo   ✅ 搜索订单（按客户、状态、日期）
echo   ✅ 订单统计分析
echo   ✅ 导出订单到Excel
echo.
echo ═══════════════════════════════════════════════════════════════════
echo.

REM 检查虚拟环境
if exist ".venv\Scripts\activate.bat" (
    echo 🔧 激活虚拟环境...
    call .venv\Scripts\activate.bat
) else (
    echo ⚠️  未找到虚拟环境，使用系统Python
)

echo.
echo 🚀 启动程序...
echo.

python 氧化加工厂财务助手_优化版.py

pause
