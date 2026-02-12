@echo off
chcp 65001 >nul
echo.
echo ================================================================
echo    氧化加工厂财务系统 V2.0 - Web版启动器
echo ================================================================
echo.

REM 检查Python
python --version >nul 2>&1
if errorlevel 1 (
    echo [错误] 未找到Python，请先安装Python 3.8+
    pause
    exit /b 1
)

REM 检查Flask
python -c "import flask" >nul 2>&1
if errorlevel 1 (
    echo [提示] 正在安装Flask...
    pip install flask
)

echo.
echo 正在启动Web服务...
echo.
echo 启动后请打开浏览器访问: http://localhost:5000
echo.
echo 按 Ctrl+C 停止服务
echo.
echo ================================================================
echo.

REM 获取脚本所在目录
set "SCRIPT_DIR=%~dp0"
cd /d "%SCRIPT_DIR%oxidation_finance_v20"
python web_app.py
