@echo off
chcp 65001 >nul
title 小会计 - 数据备份

echo ========================================
echo    小会计 - 数据备份
echo ========================================
echo.

REM 生成备份文件夹名称（格式：备份_20260210_143025）
set backup_name=备份_%date:~0,4%%date:~5,2%%date:~8,2%_%time:~0,2%%time:~3,2%%time:~6,2%
set backup_name=%backup_name: =0%

echo 正在备份数据...
echo 备份位置: %backup_name%
echo.

REM 创建备份文件夹
if not exist "%backup_name%" mkdir "%backup_name%"

REM 备份数据文件
if exist "data" (
    echo [1/3] 备份数据文件...
    xcopy /E /I /Q data "%backup_name%\data" >nul
    echo       ✓ 数据文件备份完成
) else (
    echo       ⚠ 数据文件夹不存在
)

REM 备份报表文件
if exist "reports" (
    echo [2/3] 备份报表文件...
    xcopy /E /I /Q reports "%backup_name%\reports" >nul
    echo       ✓ 报表文件备份完成
) else (
    echo       ⚠ 报表文件夹不存在
)

REM 备份配置文件
if exist "config.json" (
    echo [3/3] 备份配置文件...
    copy /Y config.json "%backup_name%\config.json" >nul
    echo       ✓ 配置文件备份完成
) else (
    echo       ⚠ 配置文件不存在
)

echo.
echo ========================================
echo ✅ 备份完成！
echo ========================================
echo.
echo 备份位置: %backup_name%
echo.
echo 💡 建议：
echo   - 将备份文件夹复制到U盘
echo   - 或上传到网盘（百度网盘/阿里云盘）
echo   - 定期清理旧备份（保留最近3个月）
echo.
pause
