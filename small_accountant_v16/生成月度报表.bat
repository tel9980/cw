@echo off
chcp 65001 >nul
echo.
echo ========================================
echo   小会计 - 一键生成月度报表
echo ========================================
echo.
echo 正在生成上个月的所有报表...
echo.

python quick_monthly_report.py

echo.
echo 按任意键退出...
pause >nul
