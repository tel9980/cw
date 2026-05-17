@echo off
chcp 65001 >nul
title 氧化加工厂财务系统 V2.0 - 小白会计专版

echo.
echo ========================================
echo   氧化加工厂财务系统 V2.0
echo   小白会计专版 - 开箱即用
echo ========================================
echo.
echo 🎯 专为氧化加工厂设计
echo ⚡ 支持7种计价方式
echo 💰 灵活的收付款管理
echo 📊 自动生成财务报表
echo.

cd /d "%~dp0"

REM 检查Python是否安装
python --version >nul 2>&1
if errorlevel 1 (
    echo ❌ 错误: 未找到Python
    echo 💡 请先安装Python 3.7或更高版本
    echo 📥 下载地址: https://www.python.org/downloads/
    pause
    exit /b 1
)

echo 📦 检查依赖包...
python -c "import json, pathlib" >nul 2>&1
if errorlevel 1 (
    echo ❌ 缺少必要的Python模块
    pause
    exit /b 1
)

REM 检查是否已有示例数据
if not exist "demo_data_v20\oxidation_factory_demo_data.json" (
    echo.
    echo 📊 首次使用，正在生成示例数据...
    echo 💡 这些数据可以帮助您快速了解系统
    echo.
    python "生成氧化加工厂示例数据_V2.0.py"
    if errorlevel 1 (
        echo.
        echo ❌ 示例数据生成失败
        echo 💡 请检查错误信息
        pause
        exit /b 1
    )
    echo.
    echo ✅ 示例数据生成完成！
    echo.
    pause
)

echo.
echo ========================================
echo   系统功能说明
echo ========================================
echo.
echo 📋 订单管理
echo    - 支持7种计价方式（件、条、只、个、米、公斤、平方米）
echo    - 自动处理委外加工（喷砂、拉丝、抛光）
echo    - 智能计算订单利润
echo.
echo 💰 收付款管理
echo    - 灵活分配：一笔收款可对应多个订单
echo    - 预收款管理：先收款，后分配
echo    - 双银行管理：G银行（有票）+ N银行（现金）
echo.
echo 📊 财务报表
echo    - 自动生成利润表、资产负债表、现金流量表
echo    - 业务分析报告
echo    - 应收应付管理
echo.
echo 🎓 小白友好
echo    - 完整示例数据，照着做就行
echo    - 详细操作说明
echo    - 常见问题解答
echo.
echo ========================================
echo.

echo 📖 使用提示：
echo    1. 首次使用建议先查看示例数据
echo    2. 详细使用说明请查看：氧化加工厂财务系统_V2.0_使用指南.md
echo    3. 示例数据位置：demo_data_v20\oxidation_factory_demo_data.json
echo.

echo 🚀 准备启动系统...
echo.
echo ⚠️  注意：完整GUI版本正在开发中
echo 💡 当前版本：示例数据已生成，可以查看和学习
echo.

choice /C YN /M "是否查看示例数据文件"
if errorlevel 2 goto end
if errorlevel 1 goto show_data

:show_data
echo.
echo 📂 打开示例数据文件...
start "" "demo_data_v20\oxidation_factory_demo_data.json"
echo.
echo ✅ 已打开示例数据文件
echo 💡 您可以用记事本或其他文本编辑器查看
echo.

:end
echo.
echo ========================================
echo   快速开始指南
echo ========================================
echo.
echo 第一步：查看示例数据
echo    - 打开 demo_data_v20\oxidation_factory_demo_data.json
echo    - 了解订单、收入、支出的数据结构
echo.
echo 第二步：阅读使用文档
echo    - 打开 氧化加工厂财务系统_V2.0_使用指南.md
echo    - 学习各种业务场景的操作方法
echo.
echo 第三步：理解业务流程
echo    - 查看 氧化加工厂财务系统_V2.0_完成总结.md
echo    - 了解系统的核心功能和业务逻辑
echo.
echo 第四步：等待完整版本
echo    - GUI界面正在开发中
echo    - 完成后可以直接使用图形界面操作
echo.
echo ========================================
echo.

choice /C YN /M "是否打开使用指南"
if errorlevel 2 goto final
if errorlevel 1 goto show_guide

:show_guide
echo.
echo 📖 打开使用指南...
start "" "氧化加工厂财务系统_V2.0_使用指南.md"
echo.
echo ✅ 已打开使用指南
echo.

:final
echo.
echo 👋 感谢使用氧化加工厂财务系统 V2.0！
echo.
echo 💡 提示：
echo    - 示例数据可以随时重新生成
echo    - 运行：python 生成氧化加工厂示例数据_V2.0.py
echo.
echo 📞 如有问题，请查看文档或联系技术支持
echo.
pause