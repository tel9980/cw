@echo off
chcp 65001 >nul
title 氧化加工厂财务助手 V1.0

echo.
echo ========================================================================
echo              氧化加工厂财务助手 V1.0
echo ========================================================================
echo.
echo 正在启动系统...
echo.

REM 检查Python环境
python --version >nul 2>&1
if errorlevel 1 (
    echo ❌ 未检测到Python环境
    echo 💡 请先安装Python 3.8或更高版本
    echo.
    pause
    exit /b 1
)

REM 检查虚拟环境
if exist ".venv\Scripts\activate.bat" (
    echo ✅ 检测到虚拟环境，正在激活...
    call .venv\Scripts\activate.bat
) else (
    echo ⚠️ 未检测到虚拟环境，使用系统Python
)

REM 启动程序
python "氧化加工厂财务助手.py"

REM 如果程序异常退出，暂停以查看错误信息
if errorlevel 1 (
    echo.
    echo ❌ 程序异常退出
    pause
)
