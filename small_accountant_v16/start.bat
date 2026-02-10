@echo off
REM V1.6 小会计实用增强版 - Windows启动脚本

echo ========================================
echo V1.6 小会计实用增强版
echo ========================================
echo.

REM 检查Python是否安装
python --version >nul 2>&1
if errorlevel 1 (
    echo [错误] 未检测到Python，请先安装Python 3.8或更高版本
    echo 下载地址: https://www.python.org/downloads/
    pause
    exit /b 1
)

echo [信息] Python版本:
python --version
echo.

REM 检查虚拟环境
if not exist ".venv" (
    echo [信息] 首次运行，正在创建虚拟环境...
    python -m venv .venv
    if errorlevel 1 (
        echo [错误] 虚拟环境创建失败
        pause
        exit /b 1
    )
    echo [成功] 虚拟环境创建完成
    echo.
)

REM 激活虚拟环境
echo [信息] 激活虚拟环境...
call .venv\Scripts\activate.bat
if errorlevel 1 (
    echo [错误] 虚拟环境激活失败
    pause
    exit /b 1
)

REM 检查依赖是否安装
python -c "import openpyxl" >nul 2>&1
if errorlevel 1 (
    echo [信息] 首次运行，正在安装依赖...
    pip install -r requirements.txt
    if errorlevel 1 (
        echo [错误] 依赖安装失败
        pause
        exit /b 1
    )
    echo [成功] 依赖安装完成
    echo.
)

REM 启动系统
echo [信息] 启动系统...
echo.
python run_cli.py

REM 退出时暂停
if errorlevel 1 (
    echo.
    echo [错误] 系统运行出错
    pause
)
