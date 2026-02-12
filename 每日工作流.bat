@echo off
echo.
echo ================================================================
echo    氧化加工厂财务系统 V2.0 - 每日工作流
echo ================================================================
echo.
echo [推荐每日工作流程]
echo.
echo ===== 早上（3分钟）================================================
echo.
echo 1. 启动Web版
echo    双击: 启动_Web版.bat
echo    浏览器访问: http://localhost:5000
echo.
echo 2. 查看今日概览
echo    - 查看今日收支
echo    - 查看待办订单
echo    - 查看未收款提醒
echo.
echo ===== 白天（工作中）===============================================
echo.
echo 3. 录入新订单
echo    点击: [+ 新建订单]
echo    填写: 客户、物品、数量、单价
echo    系统自动计算金额
echo.
echo 4. 录入收入
echo    点击: [+ 录入收入]
echo    选择: G银行（有票）或 N银行（现金）
echo.
echo 5. 录入支出
echo    点击: [+ 录入支出]
echo    选择: 支出类型、填写金额
echo.
echo ===== 晚上（2分钟）================================================
echo.
echo 6. 查看当日汇总
echo    Web版首页已显示今日数据
echo.
echo 7. 数据备份（自动）
echo    python oxidation_finance_v20/tools/auto_backup.py
echo.
echo ===== 月末（10分钟）===============================================
echo.
echo 8. 生成报表
echo    python oxidation_finance_v20/tools/report_exporter.py --all
echo.
echo 9. 打印报表
echo    python oxidation_finance_v20/tools/print_optimizer.py
echo.
echo 10. 数据检查
echo    python oxidation_finance_v20/tools/data_quality_check.py
echo.
echo ================================================================
echo.
echo 按任意键打开Web版...
echo.
pause >nul

start 启动_Web版.bat
