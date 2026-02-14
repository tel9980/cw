@echo off
chcp 65001 >nul
title 依赖安装器 - 氧化加工厂财务系统

:MAIN_MENU
cls
echo.
echo ================================================================
echo    氧化加工厂财务系统 V2.0 - 依赖安装器
echo ================================================================
echo.
echo 请选择安装类型：
echo.
echo    [1] 📦 安装生产环境依赖    - 仅安装运行所需的基本包
echo    [2] 🛠️  安装开发环境依赖    - 安装所有开发和测试工具
echo    [3] 🔄 升级所有依赖包      - 升级到最新版本
echo    [4] 📋 查看已安装包        - 列出当前环境的包
echo.
echo    [0] 🚪 退出
echo.
echo ================================================================
echo.
set /p CHOICE=请输入选项 [0-4]:

if "%CHOICE%"=="1" goto INSTALL_PROD
if "%CHOICE%"=="2" goto INSTALL_DEV
if "%CHOICE%"=="3" goto UPGRADE_PACKAGES
if "%CHOICE%"=="4" goto LIST_PACKAGES
if "%CHOICE%"=="0" goto EXIT

echo 无效选项，请重新选择
timeout /t 2 >nul
goto MAIN_MENU

:INSTALL_PROD
echo.
echo 📦 正在安装生产环境依赖...
echo.
pip install -r requirements\requirements.txt
if errorlevel 1 (
    echo.
    echo ❌ 安装失败！请检查网络连接或Python环境
    echo 💡 建议：尝试升级pip - python -m pip install --upgrade pip
) else (
    echo.
    echo ✅ 生产环境依赖安装完成！
)
pause
goto MAIN_MENU

:INSTALL_DEV
echo.
echo 🛠️ 正在安装开发环境依赖...
echo.
pip install -r requirements\requirements-dev.txt
if errorlevel 1 (
    echo.
    echo ❌ 安装失败！请检查网络连接或Python环境
    echo 💡 建议：尝试升级pip - python -m pip install --upgrade pip
) else (
    echo.
    echo ✅ 开发环境依赖安装完成！
)
pause
goto MAIN_MENU

:UPGRADE_PACKAGES
echo.
echo 🔄 正在升级所有依赖包...
echo.
pip install --upgrade -r requirements\requirements.txt
if errorlevel 1 (
    echo.
    echo ❌ 升级失败！
) else (
    echo.
    echo ✅ 依赖包升级完成！
)
pause
goto MAIN_MENU

:LIST_PACKAGES
echo.
echo 📋 已安装的Python包：
echo.
pip list
echo.
echo 按任意键返回...
pause >nul
goto MAIN_MENU

:EXIT
echo.
echo 感谢使用依赖安装器！
echo.
pause
exit /b 0