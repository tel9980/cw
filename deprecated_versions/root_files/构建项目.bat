@echo off
chcp 65001 >nul
title 项目构建工具 - 氧化加工厂财务系统

:MAIN_MENU
cls
echo.
echo ================================================================
echo    氧化加工厂财务系统 V2.0 - 项目构建工具
echo ================================================================
echo.
echo 请选择操作：
echo.
echo    [1] 📦 构建发行版本      - 创建可发布的项目包
echo    [2] 🧪 运行所有测试      - 执行完整的测试套件
echo    [3] 📊 生成测试报告      - 创建详细的测试覆盖率报告
echo    [4] 📋 代码质量检查      - 运行代码静态分析
echo    [5] 🗃️  清理构建缓存     - 清除临时文件和缓存
echo    [6] 📤 打包为可执行文件  - 创建Windows可执行程序
echo.
echo    [0] 🚪 退出
echo.
echo ================================================================
echo.
set /p CHOICE=请输入选项 [0-6]:

if "%CHOICE%"=="1" goto BUILD_RELEASE
if "%CHOICE%"=="2" goto RUN_ALL_TESTS
if "%CHOICE%"=="3" goto GENERATE_COVERAGE
if "%CHOICE%"=="4" goto CODE_QUALITY_CHECK
if "%CHOICE%"=="5" goto CLEAN_CACHE
if "%CHOICE%"=="6" goto CREATE_EXE
if "%CHOICE%"=="0" goto EXIT

echo 无效选项，请重新选择
timeout /t 2 >nul
goto MAIN_MENU

:BUILD_RELEASE
echo.
echo 📦 正在构建发行版本...
echo.

REM 创建构建目录
if exist "dist" rd /s /q "dist"
mkdir "dist"
mkdir "dist\cwzs-v2.0"

REM 复制必要文件
echo 正在复制源代码...
xcopy /E /I /Y "oxidation_finance_v20" "dist\cwzs-v2.0\oxidation_finance_v20" >nul
xcopy /E /I /Y "docs" "dist\cwzs-v2.0\docs" >nul
xcopy /E /I /Y "requirements" "dist\cwzs-v2.0\requirements" >nul

REM 复制启动脚本
copy "启动系统.bat" "dist\cwzs-v2.0\" >nul
copy "启动Web.bat" "dist\cwzs-v2.0\" >nul
copy "安装依赖.bat" "dist\cwzs-v2.0\" >nul
copy "README.md" "dist\cwzs-v2.0\" >nul
copy ".env.example" "dist\cwzs-v2.0\" >nul

REM 创建版本文件
echo V2.0.0 > "dist\cwzs-v2.0\VERSION"
date /t >> "dist\cwzs-v2.0\VERSION"
time /t >> "dist\cwzs-v2.0\VERSION"

echo.
echo ✅ 发行版本构建完成！
echo 📁 位置: dist\cwzs-v2.0\
pause
goto MAIN_MENU

:RUN_ALL_TESTS
echo.
echo 🧪 正在运行所有测试...
echo.
cd oxidation_finance_v20
python -m pytest -v --tb=short
cd ..
pause
goto MAIN_MENU

:GENERATE_COVERAGE
echo.
echo 📊 正在生成测试覆盖率报告...
echo.
cd oxidation_finance_v20
python -m pytest --cov=oxidation_finance_v20 --cov-report=html --cov-report=term
cd ..
echo.
echo 📊 覆盖率报告已生成到: oxidation_finance_v20/htmlcov/index.html
pause
goto MAIN_MENU

:CODE_QUALITY_CHECK
echo.
echo 📋 正在进行代码质量检查...
echo.
echo 检查Python语法...
python -m py_compile oxidation_finance_v20/**/*.py
if errorlevel 1 (
    echo ❌ 语法检查发现错误
) else (
    echo ✅ 语法检查通过
)

echo.
echo 运行代码风格检查...
cd oxidation_finance_v20
ruff check .
cd ..

pause
goto MAIN_MENU

:CLEAN_CACHE
echo.
echo 🗃️ 正在清理构建缓存...
echo.

REM 清理Python缓存
for /d /r . %%d in (__pycache__) do @if exist "%%d" rd /s /q "%%d"
for /d /r . %%d in (*.pyc) do @if exist "%%d" del /q "%%d"
for /d /r . %%d in (*.pyo) do @if exist "%%d" del /q "%%d"

REM 清理测试缓存
if exist ".pytest_cache" rd /s /q ".pytest_cache"
if exist "oxidation_finance_v20\.pytest_cache" rd /s /q "oxidation_finance_v20\.pytest_cache"

REM 清理构建目录
if exist "build" rd /s /q "build"
if exist "dist" rd /s /q "dist"

echo ✅ 缓存清理完成！
pause
goto MAIN_MENU

:CREATE_EXE
echo.
echo 📤 正在创建Windows可执行文件...
echo.
echo 💡 注意：这需要安装 pyinstaller
echo 💡 安装命令：pip install pyinstaller
echo.
pause

REM 检查pyinstaller是否存在
python -c "import PyInstaller" >nul 2>&1
if errorlevel 1 (
    echo ❌ 未找到 PyInstaller，请先安装
    echo 💡 运行：pip install pyinstaller
    pause
    goto MAIN_MENU
)

REM 创建可执行文件
pyinstaller --onefile --windowed --name="CWZS-Finance" oxidation_finance_v20/web_app.py

echo.
echo ✅ 可执行文件创建完成！
echo 📁 位置: dist\CWZS-Finance.exe
pause
goto MAIN_MENU

:EXIT
echo.
echo 感谢使用项目构建工具！
echo.
pause
exit /b 0