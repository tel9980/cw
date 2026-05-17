@echo off
chcp 65001 >nul
echo ========================================
echo    V1.5 财务助手 - 一键安装程序
echo ========================================
echo.
echo 正在检查Python环境...
python --version >nul 2>&1
if errorlevel 1 (
    echo [错误] 未检测到Python！
    echo.
    echo 请先安装Python 3.9或更高版本
    echo 下载地址: https://www.python.org/downloads/
    echo.
    echo 安装时务必勾选 "Add Python to PATH"
    echo.
    pause
    exit /b 1
)

echo [成功] Python环境正常
echo.
echo 正在安装依赖包...
echo 这可能需要几分钟，请耐心等待...
echo.

pip install -r requirements.txt

if errorlevel 1 (
    echo.
    echo [错误] 安装失败！
    echo.
    echo 可能的原因：
    echo 1. 网络连接问题
    echo 2. pip版本过旧
    echo.
    echo 解决方案：
    echo 1. 检查网络连接
    echo 2. 升级pip: python -m pip install --upgrade pip
    echo 3. 重新运行此脚本
    echo.
    pause
    exit /b 1
)

echo.
echo ========================================
echo    安装完成！
echo ========================================
echo.
echo 接下来你可以：
echo.
echo 1. 双击 "启动_V1.5实战版.bat" 启动系统
echo 2. 双击 "运行_生成测试数据.bat" 生成测试数据
echo 3. 查看 "小白落地指南.md" 了解详细使用方法
echo.
echo 祝使用愉快！
echo.
pause
