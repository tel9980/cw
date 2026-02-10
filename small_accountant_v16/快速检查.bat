@echo off
chcp 65001 >nul
title 小会计 - 快速检查

echo ========================================
echo    小会计 - 快速检查
echo ========================================
echo.
echo 正在检查系统状态...
echo.

python quick_check.py

echo.
pause
