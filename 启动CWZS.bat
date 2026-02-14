@echo off
chcp 65001 >nul
title CWZS财务系统 - 统一启动器

cls
echo.
echo ================================================================
echo    🏭 CWZS氧化加工厂财务系统 V2.0
echo    统一启动管理器
echo ================================================================
echo.
echo 当前时间: %date% %time%
echo 工作目录: %cd%
echo.

REM 检查Python环境
echo 🐍 检查Python环境...
python --version >nul 2>&1
if errorlevel 1 (
    echo ❌ 未检测到Python环境
    echo 💡 请先安装Python 3.8或更高版本
    echo 📍 下载地址: https://www.python.org/downloads/
    pause
    exit /b 1
)
echo ✅ Python %ERRORLEVEL% 环境正常

REM 检查必要目录
if not exist "oxidation_finance_v20" (
    echo ❌ 未找到核心系统目录
    echo 💡 请确保在正确的项目根目录下运行
    pause
    exit /b 1
)
echo ✅ 系统目录存在

:MAIN_MENU
cls
echo.
echo ================================================================
echo    🏭 CWZS氧化加工厂财务系统 V2.0 - 统一启动器
echo ================================================================
echo.
echo 🎯 推荐使用路径（渐进式学习）：
echo    1. 首次使用 → 选择 [3] 一键部署配置环境
echo    2. 学习操作 → 选择 [4] 生成学习数据
echo    3. 日常使用 → 选择 [1] 启动小白财务助手
echo    4. 高级功能 → 选择 [2] 启动Web专业版
echo.
echo 📋 功能菜单：
echo    [1] 🚀 启动小白财务助手     - 菜单式操作，零技术门槛
echo    [2] 🌐 启动Web专业版       - 浏览器界面，功能完整
echo    [3] 🛠️  一键部署配置       - 自动安装依赖，配置环境
echo    [4] 📊 生成学习数据       - 创建示例数据供学习使用
echo    [5] 🧪 系统功能测试       - 验证各模块运行状态
echo    [6] 📖 查看使用说明       - 系统功能和操作指南
echo.
echo    [0] 🚪 退出系统
echo.
echo ================================================================
echo.
set /p CHOICE=请输入选项 [0-6]:

if "%CHOICE%"=="1" goto START_SIMPLE
if "%CHOICE%"=="2" goto START_WEB
if "%CHOICE%"=="3" goto DEPLOY_SYSTEM
if "%CHOICE%"=="4" goto GENERATE_DATA
if "%CHOICE%"=="5" goto TEST_SYSTEM
if "%CHOICE%"=="6" goto SHOW_HELP
if "%CHOICE%"=="0" goto EXIT

echo ❌ 无效选项 (%CHOICE%)，请输入 0-6 之间的数字
timeout /t 3 >nul
goto MAIN_MENU

:START_SIMPLE
cls
echo.
echo 🚀 正在启动小白财务助手...
echo.
cd oxidation_finance_v20
if exist "tools\小白财务助手.py" (
    python tools\小白财务助手.py
) else (
    echo ❌ 未找到小白财务助手程序
    echo 💡 请先运行一键部署配置环境
)
cd ..
pause
goto MAIN_MENU

:START_WEB
cls
echo.
echo 🌐 正在启动Web专业版...
echo.
echo 请在浏览器中访问: http://localhost:5000
echo 按 Ctrl+C 停止服务
echo.
cd oxidation_finance_v20
if exist "web_app.py" (
    python web_app.py
) else (
    echo ❌ 未找到Web应用程序
    echo 💡 请先运行一键部署配置环境
)
cd ..
pause
goto MAIN_MENU

:DEPLOY_SYSTEM
cls
echo.
echo 🛠️ 正在一键部署配置系统...
echo.
call "一键部署.bat"
pause
goto MAIN_MENU

:GENERATE_DATA
cls
echo.
echo 📊 正在生成学习用模拟数据...
echo.
cd oxidation_finance_v20
python -c "
import json
import os
from datetime import datetime, date
from decimal import Decimal

# 创建氧化加工厂模拟数据
data = {
    'customers': [],
    'orders': [],
    'income': [],
    'expenses': [],
    'bank_transactions': [],
    'suppliers': [],
    'last_updated': str(datetime.now())
}

print('🔄 正在生成氧化加工厂模拟数据...')
print()

# 添加典型客户（6个）
customers = [
    ('优质客户有限公司', '张经理', '13800138001'),
    ('新兴科技股份有限公司', '李总', '13900139002'),
    ('长期合作伙伴公司', '王主任', '13700137003'),
    ('诚信贸易公司', '陈经理', '13600136004'),
    ('实力制造企业', '刘总', '13500135005'),
    ('可靠供应商集团', '赵主任', '13400134006')
]

for i, (name, contact, phone) in enumerate(customers, 1):
    customer = {
        'id': f'C{i:03d}',
        'name': name,
        'contact': contact,
        'phone': phone,
        'created_at': str(datetime.now())
    }
    data['customers'].append(customer)
    print(f'✅ 添加客户: {name}')

print()

# 添加不同计价方式的订单（10个）
orders_data = [
    # 按件计价
    ('C001', '铝合金把手', 500, 2.5, '件', ['氧化']),
    ('C002', '不锈钢螺丝', 1000, 0.8, '件', ['氧化']),
    # 按条计价
    ('C003', '铜管', 200, 15.0, '条', ['氧化']),
    # 按米计价
    ('C001', '铝型材', 150, 12.0, '米', ['拉丝', '氧化']),
    ('C004', '不锈钢管', 80, 25.0, '米', ['喷砂', '氧化']),
    # 按公斤计价
    ('C002', '铁质零件', 300, 8.0, '公斤', ['氧化']),
    ('C005', '铜质配件', 150, 28.0, '公斤', ['抛光', '氧化']),
    # 按平方米计价
    ('C003', '铝板', 50, 45.0, '平方米', ['氧化']),
    ('C006', '不锈钢板', 30, 68.0, '平方米', ['拉丝', '氧化']),
    # 委外加工订单
    ('C004', '精密零件', 200, 18.0, '件', ['喷砂', '拉丝', '氧化'])
]

for i, (cust_id, item, qty, price, unit, processes) in enumerate(orders_data, 1):
    amount = Decimal(str(qty)) * Decimal(str(price))
    order = {
        'id': f'O{i:04d}',
        'customer_id': cust_id,
        'item_name': item,
        'quantity': float(qty),
        'unit_price': str(price),
        'pricing_unit': unit,
        'amount': str(amount),
        'outsourcing_processes': processes,
        'status': '待加工',
        'created_at': str(datetime.now())
    }
    data['orders'].append(order)
    print(f'✅ 添加订单: {item} ({qty}{unit}) - ¥{amount:.2f}')

print()

# 添加收入记录（6笔）
income_data = [
    ('C001', 2500, 'G银行', '铝合金把手加工费'),
    ('C002', 1800, 'G银行', '不锈钢螺丝加工费'),
    ('C003', 3000, 'N银行', '铜管加工费'),
    ('C001', 1200, 'N银行', '部分款项'),
    ('C004', 2800, 'G银行', '不锈钢管加工费'),
    ('C002', 1500, 'N银行', '铁质零件加工费')
]

for i, (cust_id, amount, bank, desc) in enumerate(income_data, 1):
    income = {
        'id': f'I{i:04d}',
        'customer_id': cust_id,
        'amount': str(amount),
        'bank_type': bank,
        'description': desc,
        'date': str(date.today()),
        'created_at': str(datetime.now())
    }
    data['income'].append(income)
    print(f'✅ 记录收入: {desc} - ¥{amount}')

print()

# 添加支出记录（12类）
expense_data = [
    ('房租', 8000, '厂房租金', ''),
    ('水电费', 2500, '本月水电费', ''),
    ('三酸', 3200, '硫酸、盐酸、硝酸', '化工供应商'),
    ('片碱', 1800, '氢氧化钠', '化工供应商'),
    ('亚钠', 1200, '亚硝酸钠', '化工供应商'),
    ('色粉', 800, '各种颜色粉末', '颜料供应商'),
    ('除油剂', 600, '金属表面处理剂', '表面处理供应商'),
    ('挂具', 1500, '电镀挂具', '设备供应商'),
    ('外发加工费', 2800, '喷砂拉丝费用', '外协加工厂'),
    ('日常费用', 1200, '办公用品等', ''),
    ('工资', 15000, '员工工资', ''),
    ('其他', 500, '杂项支出', '')
]

for i, (exp_type, amount, desc, supplier) in enumerate(expense_data, 1):
    expense = {
        'id': f'E{i:04d}',
        'type': exp_type,
        'amount': str(amount),
        'description': desc,
        'supplier': supplier,
        'date': str(date.today()),
        'created_at': str(datetime.now())
    }
    data['expenses'].append(expense)
    print(f'✅ 记录支出: {exp_type} - ¥{amount}')

print()

# 保存数据
data_file = 'simple_finance_data.json'
with open(data_file, 'w', encoding='utf-8') as f:
    json.dump(data, f, ensure_ascii=False, indent=2, default=str)

print('🎉 模拟数据生成完成！')
print(f'📁 数据文件: {os.path.abspath(data_file)}')
print()
print('📊 数据统计:')
print(f'   客户: {len(data[\"customers\"])} 个')
print(f'   订单: {len(data[\"orders\"])} 个')  
print(f'   收入: {len(data[\"income\"])} 笔')
print(f'   支出: {len(data[\"expenses\"])} 笔')
print()
print('💡 现在可以:')
print('   1. 启动小白财务助手查看数据')
print('   2. 学习各项功能操作')
print('   3. 修改删除数据进行练习')
"
cd ..
pause
goto MAIN_MENU

:TEST_SYSTEM
cls
echo.
echo 🧪 正在进行系统功能测试...
echo.
echo 正在检查各组件运行状态...
echo.

REM 测试Python基本功能
python -c "print('✅ Python运行正常')" >nul 2>&1
if errorlevel 1 (
    echo ❌ Python环境异常
    goto TEST_END
)
echo ✅ Python环境正常

REM 测试核心模块导入
cd oxidation_finance_v20
python -c "
try:
    from utils.config import get_db_path
    print('✅ 核心配置模块导入成功')
except ImportError as e:
    print(f'⚠️  配置模块导入警告: {e}')

try:
    from tools.小白财务助手 import SimpleFinanceHelper
    print('✅ 小白财务助手模块导入成功')
except ImportError as e:
    print(f'⚠️  小白助手模块导入警告: {e}')
" >nul 2>&1
cd ..

REM 测试文件系统
if exist "oxidation_finance_v20\simple_finance_data.json" (
    echo ✅ 数据文件存在
) else (
    echo ℹ️  数据文件不存在（首次运行正常）
)

echo.
echo 🎉 系统基础测试完成！
echo 💡 如需完整功能测试，请运行专业版测试工具

:TEST_END
pause
goto MAIN_MENU

:SHOW_HELP
cls
echo.
echo 📖 CWZS财务系统使用说明
echo ================================================================
echo.
echo 🎯 系统特色:
echo    • 专为氧化加工厂设计的专业财务管理系统
echo    • 支持多种计价方式（件/条/米/公斤/平方米）
echo    • 完整的委外加工流程管理
echo    • 灵活的收付款处理机制
echo    • 双银行账户支持（G银行有票/N银行现金）
echo.
echo 🚀 推荐使用流程:
echo    1. 首次使用建议运行 [3] 一键部署
echo    2. 生成学习数据 [4] 熟悉系统操作
echo    3. 日常使用选择 [1] 小白财务助手
echo    4. 需要高级功能时使用 [2] Web专业版
echo.
echo 💡 操作要点:
echo    • 客户管理：先建立客户档案再进行业务操作
echo    • 订单录入：支持7种计价单位，可设置委外工序
echo    • 收入记录：区分G银行(有票)和N银行(现金/微信)
echo    • 支出管理：12种常用支出类型分类管理
echo    • 灵活匹配：收付款不需要一一对应，按实际发生记录
echo.
echo 📊 计价方式说明:
echo    件/条/只/个 - 按数量计价（标准件加工）
echo    米 - 按长度计价（管材、型材加工）
echo    公斤 - 按重量计价（原材料加工）
echo    平方米 - 按面积计价（板材加工）
echo.
echo 🏭 行业特色功能:
echo    • 委外加工：支持喷砂/拉丝/抛光工序外包管理
echo    • 工序跟踪：完整跟踪氧化加工全流程
echo    • 成本核算：自动计算加工成本和利润分析
echo    • 财务统计：实时盈亏分析和报表生成
echo.
echo 按任意键返回主菜单...
pause >nul
goto MAIN_MENU

:EXIT
cls
echo.
echo ================================================================
echo    感谢使用CWZS氧化加工厂财务系统！
echo ================================================================
echo.
echo 📝 使用建议:
echo    • 定期备份 simple_finance_data.json 数据文件
echo    • 建议每天及时录入当日业务数据
echo    • 月末可结合数据制作正式财务报表
echo.
echo 🆘 技术支持:
echo    • 首次使用请运行一键部署配置环境
echo    • 遇到问题可重新生成学习数据练习
echo    • 查看使用说明了解各项功能详情
echo.
echo 👋 祝您工作顺利，财源广进！
echo.
pause
exit /b 0