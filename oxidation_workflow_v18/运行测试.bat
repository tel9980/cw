@echo off
chcp 65001 >nul
echo ============================================================
echo 运行测试套件
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

REM Run tests
python -m pytest tests/ -v

echo.
echo 测试完成！
pause
