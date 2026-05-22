@echo off
chcp 65001 >nul
echo ==========================================
echo   🏭 氧化加工厂财务系统
echo ==========================================

REM 检查是否已初始化
if not exist "oxidation_finance_demo_ready.db" (
    echo.
    echo 📦 首次使用，正在初始化系统...
    python init.py
) else (
    echo.
    echo ✅ 系统已初始化，直接启动Web应用
    echo.
    echo 按 Ctrl+C 停止服务
    echo ==========================================
    echo.
    python web_app.py
)
