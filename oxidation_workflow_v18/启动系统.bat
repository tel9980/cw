@echo off
chcp 65001 >nul
echo ============================================================
echo 氧化加工厂工作流程优化系统 V1.8
echo ============================================================
echo.

REM Check if virtual environment exists
if not exist "..\venv\Scripts\activate.bat" (
    echo 错误：未找到虚拟环境
    echo 请先运行安装脚本或手动创建虚拟环境
    pause
    exit /b 1
)

REM Activate virtual environment
call ..\venv\Scripts\activate.bat

REM Run the application
python main.py

pause
