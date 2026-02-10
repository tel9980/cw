@echo off
chcp 65001 >nul
title 小会计 - 快速导入Excel数据

echo ========================================
echo    小会计 - 快速导入Excel数据
echo ========================================
echo.
echo 功能说明：
echo   - 导入交易记录（流水账）
echo   - 导入往来单位（客户供应商）
echo   - 导入银行流水（对账用）
echo.
echo 请准备好要导入的Excel文件
echo.
pause

echo.
echo 正在启动导入功能...
echo.

python run_cli.py

echo.
pause
