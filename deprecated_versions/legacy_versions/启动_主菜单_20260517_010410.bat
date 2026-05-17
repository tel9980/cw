@echo off
chcp 65001 >nul
setlocal

REM 颜色定义
set "COLOR_TITLE=0A"
set "COLOR_OPTION=0F"
set "COLOR_HIGHLIGHT=0E"
set "COLOR_ERROR=0C"

title 氧化加工厂财务系统 V2.0 - 主菜单

:MAIN_MENU
cls
echo.
echo ============================================================================
echo.
echo    ██████╗  █████╗ ██████╗  █████╗ ██╗     ██╗     ███████╗██╗
echo    ██╔══██╗██╔══██╗██╔══██╗██╔══██╗██║     ██║     ██╔════╝██║
echo    ██████╔╝███████║██████╔╝███████║██║     ██║     █████╗  ██║
echo    ██╔═══╝ ██╔══██║██╔══██╗██╔══██║██║     ██║     ██╔══╝  ██║
echo    ██║      ██║  ██║██║  ██║██║  ██║███████╗███████╗███████╗███████╗
echo    ╚═╝      ╚═╝  ╚═╝╚═╝  ╚═╝╚═╝  ╚═╝╚══════╝╚══════╝╚══════╝╚══════╝
echo.
echo ============================================================================
echo.
echo                        氧化加工厂财务系统 V2.0
echo.
echo ============================================================================
echo.
echo    [1] 启动 Web界面      - 浏览器访问 http://localhost:5000
echo    [2] 今日概览         - 查看今日统计数据
echo    [3] 智能提醒         - 待加工/未收款提醒
echo    [4] 数据备份         - 备份数据库
echo    [5] 数据恢复         - 从备份恢复
echo    [6] 数据质量检查     - 检查数据完整性
echo    [7] 系统设置向导     - 初始化配置
echo.
echo    [0] 退出系统
echo.
echo ============================================================================
echo.
set /p MENU_CHOICE=请输入选项 [0-7]:
echo.

if "%MENU_CHOICE%"=="1" goto WEB
if "%MENU_CHOICE%"=="2" goto PANEL
if "%MENU_CHOICE%"=="3" goto REMINDER
if "%MENU_CHOICE%"=="4" goto BACKUP
if "%MENU_CHOICE%"=="5" goto RESTORE
if "%MENU_CHOICE%"=="6" goto CHECK
if "%MENU_CHOICE%"=="7" goto SETUP
if "%MENU_CHOICE%"=="0" goto EXIT

echo [ERROR] 无效选项，请重新选择
pause
goto MAIN_MENU

:WEB
echo [INFO] 正在启动Web服务...
cd oxidation_finance_v20
python web_app.py
goto MAIN_MENU

:PANEL
echo [INFO] 正在打开今日概览...
cd oxidation_finance_v20
python tools/quick_panel.py
pause
goto MAIN_MENU

:REMINDER
echo [INFO] 正在生成智能提醒...
cd oxidation_finance_v20
python tools/reminder_system.py
pause
goto MAIN_MENU

:BACKUP
echo [INFO] 正在备份数据...
cd oxidation_finance_v20
python tools/backup_restore.py --create
pause
goto MAIN_MENU

:RESTORE
echo [INFO] 可用备份:
cd oxidation_finance_v20
python tools/backup_restore.py --list
echo.
set /p BACKUP_NUM=请输入要恢复的备份序号:
python tools/backup_restore.py --restore --index %BACKUP_NUM%
pause
goto MAIN_MENU

:CHECK
echo [INFO] 正在进行数据质量检查...
cd oxidation_finance_v20
python tools/data_quality_check.py
pause
goto MAIN_MENU

:SETUP
echo [INFO] 正在启动系统设置向导...
cd oxidation_finance_v20
python tools/setup_wizard.py
pause
goto MAIN_MENU

:EXIT
echo.
echo [INFO] 感谢使用氧化加工厂财务系统 V2.0
echo.
pause
exit /b 0
