@echo off
REM 设置UTF-8编码
chcp 65001 >nul
set PYTHONIOENCODING=utf-8
set PYTHONUTF8=1

echo.
echo ================================================================
echo    氧化加工厂财务系统 V2.0 - Web版启动器
echo ================================================================
echo.

REM 检查Python
python --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Please install Python 3.8+ first
    pause
    exit /b 1
)

REM 检查Flask
python -c "import flask" >nul 2>&1
if errorlevel 1 (
    echo [INFO] Installing Flask...
    pip install flask
)

echo.
echo Starting Web Service...
echo.
echo Please open browser: http://localhost:5000
echo.
echo Press Ctrl+C to stop
echo.
echo ================================================================
echo.

REM 切换到程序目录并启动
cd /d "%~dp0oxidation_finance_v20"
python web_app.py

pause