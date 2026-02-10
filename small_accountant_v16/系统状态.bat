@echo off
chcp 65001 >nul
title 小会计 - 系统状态

echo ========================================
echo    小会计 - 系统状态检查
echo ========================================
echo.

python run_cli.py --status

echo.
pause
