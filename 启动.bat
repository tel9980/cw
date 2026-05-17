@echo off
chcp 65001 > nul
title 氧化加工厂财务系统 V2.0

echo.
echo ========================================
echo   氧化加工厂财务系统 V2.0
echo ========================================
echo.
echo 正在启动...
echo.

cd /d "%~dp0"
python scripts\launcher.py

if errorlevel 1 (
    echo.
    echo 启动失败，请确保已安装 Python 3.8+
    pause
)
