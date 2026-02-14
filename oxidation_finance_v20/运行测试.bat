@echo off
chcp 65001 >nul
title 测试运行器 - 氧化加工厂财务系统

:MAIN_MENU
cls
echo.
echo ================================================================
echo    氧化加工厂财务系统 V2.0 - 测试运行器
echo ================================================================
echo.
echo 请选择要运行的测试类型：
echo.
echo    [1] 🧪 全部测试          - 运行所有377个测试用例
echo    [2] 🧪 数据库测试        - 测试数据库相关功能
echo    [3] 🧪 订单管理测试      - 测试订单相关功能
echo    [4] 🧪 用户权限测试      - 测试用户和权限系统
echo    [5] 🧪 Web API测试       - 测试Web接口
echo    [6] 🧪 属性测试          - 运行属性验证测试
echo    [7] 🧪 快速冒烟测试      - 快速验证核心功能
echo.
echo    [0] 🚪 退出
echo.
echo ================================================================
echo.
set /p CHOICE=请输入选项 [0-7]:

if "%CHOICE%"=="1" goto ALL_TESTS
if "%CHOICE%"=="2" goto DATABASE_TESTS
if "%CHOICE%"=="3" goto ORDER_TESTS
if "%CHOICE%"=="4" goto USER_TESTS
if "%CHOICE%"=="5" goto WEB_TESTS
if "%CHOICE%"=="6" goto PROPERTY_TESTS
if "%CHOICE%"=="7" goto SMOKE_TESTS
if "%CHOICE%"=="0" goto EXIT

echo 无效选项，请重新选择
timeout /t 2 >nul
goto MAIN_MENU

:ALL_TESTS
echo.
echo 🧪 运行全部测试...
echo.
python -m pytest -v --tb=short
pause
goto MAIN_MENU

:DATABASE_TESTS
echo.
echo 🧪 运行数据库测试...
echo.
python -m pytest tests/test_database.py -v --tb=short
pause
goto MAIN_MENU

:ORDER_TESTS
echo.
echo 🧪 运行订单管理测试...
echo.
python -m pytest tests/test_order_manager.py tests/test_order_properties.py -v --tb=short
pause
goto MAIN_MENU

:USER_TESTS
echo.
echo 🧪 运行用户权限测试...
echo.
python -m pytest tests/test_user_manager.py -v --tb=short
pause
goto MAIN_MENU

:WEB_TESTS
echo.
echo 🧪 运行Web API测试...
echo.
python -m pytest tests/test_web_api.py -v --tb=short
pause
goto MAIN_MENU

:PROPERTY_TESTS
echo.
echo 🧪 运行属性测试...
echo.
python -m pytest tests/*properties*.py -v --tb=short
pause
goto MAIN_MENU

:SMOKE_TESTS
echo.
echo 🧪 运行快速冒烟测试...
echo.
python quick_test.py
pause
goto MAIN_MENU

:EXIT
echo.
echo 感谢使用测试运行器！
echo.
pause
exit /b 0