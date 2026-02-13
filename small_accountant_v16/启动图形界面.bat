@echo off
chcp 65001 >nul
title 小企业会计助手 - 图形界面版

echo.
echo ========================================
echo   小企业会计助手 V1.6 - 图形界面版
echo ========================================
echo.
echo 🚀 正在启动图形界面...
echo ⚡ 特性: 高性能Excel处理 + 友好GUI界面
echo.

cd /d "%~dp0"

REM 检查Python是否安装
python --version >nul 2>&1
if errorlevel 1 (
    echo ❌ 错误: 未找到Python
    echo 💡 请先安装Python 3.7或更高版本
    echo 📥 下载地址: https://www.python.org/downloads/
    pause
    exit /b 1
)

REM 检查依赖包
echo 📦 检查依赖包...
python -c "import pandas, tkinter" >nul 2>&1
if errorlevel 1 (
    echo ⚠️  正在安装依赖包...
    pip install pandas openpyxl psutil
    if errorlevel 1 (
        echo ❌ 依赖包安装失败
        echo 💡 请手动运行: pip install pandas openpyxl psutil
        pause
        exit /b 1
    )
)

REM 启动程序
echo ✅ 启动图形界面...
python "启动图形界面.py"

if errorlevel 1 (
    echo.
    echo ❌ 程序运行出错
    echo 💡 请检查错误信息或联系技术支持
    pause
)

echo.
echo 👋 程序已退出
pause