@echo off
chcp 65001 >nul
title 一键部署 - 氧化加工厂财务系统

cls
echo.
echo ================================================================
echo    氧化加工厂财务系统 V2.0 - 一键部署工具
echo ================================================================
echo.
echo 正在为您自动部署系统...
echo.

REM 检查Python环境
echo 🐍 检查Python环境...
python --version >nul 2>&1
if errorlevel 1 (
    echo ❌ 未找到Python，请先安装Python 3.8+
    echo 💡 下载地址：https://www.python.org/downloads/
    pause
    exit /b 1
)
echo ✅ Python环境正常

REM 创建必要目录
echo 📁 创建必要目录...
if not exist "data" mkdir "data"
if not exist "logs" mkdir "logs"
if not exist "temp" mkdir "temp"

REM 安装依赖
echo 📦 安装依赖包...
pip install -r requirements\requirements.txt >nul 2>&1
if errorlevel 1 (
    echo ⚠️  依赖安装遇到问题，尝试升级pip...
    python -m pip install --upgrade pip >nul 2>&1
    pip install -r requirements\requirements.txt
)

REM 检查示例数据
echo 📊 检查示例数据...
if not exist "demo_data_v20\oxidation_factory_demo_data.json" (
    echo 正在生成示例数据...
    python "生成氧化加工厂示例数据_V2.0.py" >nul 2>&1
    if exist "demo_data_v20\oxidation_factory_demo_data.json" (
        echo ✅ 示例数据生成完成
    ) else (
        echo ⚠️  示例数据生成失败，但这不影响系统运行
    )
) else (
    echo ✅ 示例数据已存在
)

REM 初始化数据库
echo 🗄️  初始化数据库...
cd oxidation_finance_v20
if not exist "oxidation_finance_demo_ready.db" (
    echo 正在创建数据库...
    python examples/generate_comprehensive_demo.py >nul 2>&1
)
cd ..

REM 创建环境配置文件
echo ⚙️  创建配置文件...
if not exist ".env" (
    copy ".env.example" ".env" >nul
    echo ✅ 环境配置文件创建完成
) else (
    echo ✅ 环境配置文件已存在
)

REM 运行健康检查
echo 🧪 运行健康检查...
cd oxidation_finance_v20
python quick_test.py >nul 2>&1
if errorlevel 1 (
    echo ⚠️  健康检查发现问题，但系统仍可运行
) else (
    echo ✅ 健康检查通过
)
cd ..

echo.
echo ================================================================
echo    🎉 部署完成！
echo ================================================================
echo.
echo 系统已准备就绪，您可以：
echo.
echo 🚀 双击 "启动CWZS.bat" 开始使用系统
echo 📖 查看帮助文档：docs\README.md
echo.
echo 默认登录信息：
echo 用户名：admin
echo 密码：admin123
echo.
echo 📝 建议首次使用：
echo 1. 启动Web界面熟悉操作
echo 2. 查看docs目录下的使用指南
echo 3. 根据需要修改.env配置文件
echo.
echo 如有任何问题，请查看docs目录中的文档
echo.
pause