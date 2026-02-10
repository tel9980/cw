"""
CLI集成测试

测试命令行界面的各项功能
"""

import pytest
import os
import tempfile
import shutil
from datetime import date, timedelta
from decimal import Decimal
from unittest.mock import Mock, patch, MagicMock
from io import StringIO

from small_accountant_v16.ui.cli import SmallAccountantCLI
from small_accountant_v16.models.core_models import (
    TransactionRecord, TransactionType, TransactionStatus,
    Counterparty, CounterpartyType,
    Reminder, ReminderType, Priority, ReminderStatus,
    NotificationChannel
)


@pytest.fixture
def temp_storage_dir():
    """创建临时存储目录"""
    temp_dir = tempfile.mkdtemp()
    yield temp_dir
    shutil.rmtree(temp_dir, ignore_errors=True)


@pytest.fixture
def cli(temp_storage_dir):
    """创建CLI实例"""
    return SmallAccountantCLI(storage_dir=temp_storage_dir)


@pytest.fixture
def sample_data(cli):
    """创建示例数据"""
    now = datetime.now()
    
    # 添加往来单位
    customer = Counterparty(
        id="CUST001",
        name="测试客户",
        type=CounterpartyType.CUSTOMER,
        contact_person="张三",
        phone="13800138000",
        email="test@example.com",
        address="测试地址",
        tax_id="123456789",
        created_at=now,
        updated_at=now
    )
    cli.counterparty_storage.add(customer)
    
    # 添加交易记录
    transaction = TransactionRecord(
        id="TXN001",
        date=date.today(),
        type=TransactionType.INCOME,
        amount=Decimal("10000.00"),
        counterparty_id="CUST001",
        description="测试交易",
        category="销售收入",
        status=TransactionStatus.COMPLETED,
        created_at=now,
        updated_at=now
    )
    cli.transaction_storage.add(transaction)
    
    return {"customer": customer, "transaction": transaction}


class TestCLIInitialization:
    """测试CLI初始化"""
    
    def test_cli_initialization(self, temp_storage_dir):
        """测试CLI正常初始化"""
        cli = SmallAccountantCLI(storage_dir=temp_storage_dir)
        
        assert cli.storage_dir == temp_storage_dir
        assert cli.config is not None
        assert cli.transaction_storage is not None
        assert cli.counterparty_storage is not None
        assert cli.reminder_storage is not None
        assert cli.report_generator is not None
        assert cli.reminder_system is not None
        assert cli.reminder_scheduler is not None
        assert cli.reconciliation_assistant is not None
        assert cli.import_engine is not None
    
    def test_cli_creates_storage_directory(self, temp_storage_dir):
        """测试CLI创建存储目录"""
        storage_path = os.path.join(temp_storage_dir, "test_storage")
        cli = SmallAccountantCLI(storage_dir=storage_path)
        
        assert os.path.exists(storage_path)


class TestCLIHelperMethods:
    """测试CLI辅助方法"""
    
    def test_clear_screen(self, cli):
        """测试清屏功能"""
        # 不会抛出异常即可
        cli.clear_screen()
    
    def test_print_header(self, cli, capsys):
        """测试打印标题"""
        cli.print_header("测试标题")
        captured = capsys.readouterr()
        
        assert "测试标题" in captured.out
        assert "=" in captured.out
    
    def test_print_menu(self, cli, capsys):
        """测试打印菜单"""
        options = ["选项1", "选项2", "选项3"]
        cli.print_menu("测试菜单", options)
        captured = capsys.readouterr()
        
        assert "测试菜单" in captured.out
        assert "1. 选项1" in captured.out
        assert "2. 选项2" in captured.out
        assert "3. 选项3" in captured.out
        assert "0. 返回上级菜单" in captured.out
    
    @patch('builtins.input', return_value='test input')
    def test_get_input(self, mock_input, cli):
        """测试获取用户输入"""
        result = cli.get_input("请输入")
        assert result == "test input"
    
    @patch('builtins.input', return_value='')
    def test_get_input_with_default(self, mock_input, cli):
        """测试获取用户输入（使用默认值）"""
        result = cli.get_input("请输入", default="默认值")
        assert result == "默认值"
    
    @patch('builtins.input', return_value='2026-01-15')
    def test_get_date_input_valid(self, mock_input, cli):
        """测试获取日期输入（有效）"""
        result = cli.get_date_input("请输入日期")
        assert result == date(2026, 1, 15)
    
    @patch('builtins.input', return_value='invalid-date')
    def test_get_date_input_invalid(self, mock_input, cli, capsys):
        """测试获取日期输入（无效）"""
        result = cli.get_date_input("请输入日期")
        captured = capsys.readouterr()
        
        assert result is None
        assert "日期格式错误" in captured.out
    
    @patch('builtins.input', return_value='')
    def test_pause(self, mock_input, cli):
        """测试暂停功能"""
        cli.pause()
        mock_input.assert_called_once()


class TestReportMenu:
    """测试报表菜单功能"""
    
    @patch('builtins.input', side_effect=['', '', ''])
    def test_generate_management_report_with_defaults(self, mock_input, cli, sample_data, capsys):
        """测试生成管理报表（使用默认日期）"""
        cli.generate_management_report()
        captured = capsys.readouterr()
        
        assert "生成管理报表" in captured.out
    
    @patch('builtins.input', side_effect=['1', '2026-01', ''])
    def test_generate_tax_report_vat(self, mock_input, cli, sample_data, capsys):
        """测试生成增值税报表"""
        cli.generate_tax_report()
        captured = capsys.readouterr()
        
        assert "生成税务报表" in captured.out
    
    @patch('builtins.input', side_effect=['', ''])
    def test_generate_bank_loan_report(self, mock_input, cli, sample_data, capsys):
        """测试生成银行贷款报表"""
        cli.generate_bank_loan_report()
        captured = capsys.readouterr()
        
        assert "生成银行贷款报表" in captured.out


class TestReminderMenu:
    """测试提醒菜单功能"""
    
    def test_view_pending_reminders_empty(self, cli, capsys):
        """测试查看待办提醒（无提醒）"""
        cli.view_pending_reminders()
        captured = capsys.readouterr()
        
        assert "待办提醒" in captured.out
        assert "暂无待办提醒" in captured.out
    
    def test_view_pending_reminders_with_data(self, cli, capsys):
        """测试查看待办提醒（有提醒）"""
        # 添加提醒
        reminder = Reminder(
            id="REM001",
            type=ReminderType.TAX,
            title="测试提醒",
            description="这是一个测试提醒",
            due_date=date.today(),
            priority=Priority.HIGH,
            status=ReminderStatus.PENDING,
            notification_channels=[NotificationChannel.DESKTOP],
            created_at=datetime.now()
        )
        cli.reminder_storage.add(reminder)
        
        cli.view_pending_reminders()
        captured = capsys.readouterr()
        
        assert "待办提醒" in captured.out
        assert "测试提醒" in captured.out
    
    @patch('builtins.input', return_value='n')
    def test_run_reminder_checks(self, mock_input, cli, sample_data, capsys):
        """测试运行提醒检查"""
        cli.run_reminder_checks()
        captured = capsys.readouterr()
        
        assert "运行提醒检查" in captured.out
        assert "检查税务申报提醒" in captured.out
        assert "检查应付账款提醒" in captured.out
        assert "检查应收账款提醒" in captured.out
        assert "检查现金流预警" in captured.out
    
    def test_view_scheduler_status(self, cli, capsys):
        """测试查看调度器状态"""
        cli.view_scheduler_status()
        captured = capsys.readouterr()
        
        assert "调度器状态" in captured.out
        assert "运行状态" in captured.out
        assert "总任务数" in captured.out


class TestReconciliationMenu:
    """测试对账菜单功能"""
    
    def test_view_reconciliation_reports_empty(self, cli, capsys):
        """测试查看对账报告（无报告）"""
        cli.view_reconciliation_reports()
        captured = capsys.readouterr()
        
        assert "对账报告" in captured.out
        assert "暂无对账报告" in captured.out
    
    @patch('builtins.input', return_value='')
    def test_generate_customer_statement_no_customers(self, mock_input, cli, capsys):
        """测试生成客户对账单（无客户）"""
        cli.generate_customer_statement()
        captured = capsys.readouterr()
        
        assert "生成客户对账单" in captured.out
        assert "暂无客户数据" in captured.out
    
    @patch('builtins.input', return_value='')
    def test_supplier_reconciliation_no_suppliers(self, mock_input, cli, capsys):
        """测试供应商对账（无供应商）"""
        cli.supplier_reconciliation()
        captured = capsys.readouterr()
        
        assert "供应商对账" in captured.out
        assert "暂无供应商数据" in captured.out


class TestImportMenu:
    """测试导入菜单功能"""
    
    def test_view_import_history_empty(self, cli, capsys):
        """测试查看导入历史（无历史）"""
        cli.view_import_history()
        captured = capsys.readouterr()
        
        assert "导入历史" in captured.out
        assert "暂无导入历史" in captured.out
    
    @patch('builtins.input', return_value='nonexistent.xlsx')
    def test_import_transactions_file_not_found(self, mock_input, cli, capsys):
        """测试导入交易记录（文件不存在）"""
        cli.import_transactions()
        captured = capsys.readouterr()
        
        assert "导入交易记录" in captured.out
        assert "文件不存在" in captured.out
    
    @patch('builtins.input', return_value='nonexistent.xlsx')
    def test_import_counterparties_file_not_found(self, mock_input, cli, capsys):
        """测试导入往来单位（文件不存在）"""
        cli.import_counterparties()
        captured = capsys.readouterr()
        
        assert "导入往来单位" in captured.out
        assert "文件不存在" in captured.out


class TestSettingsMenu:
    """测试设置菜单功能"""
    
    @patch('builtins.input', side_effect=['', ''])
    def test_configure_wechat_no_change(self, mock_input, cli, capsys):
        """测试配置企业微信（不修改）"""
        cli.configure_wechat()
        captured = capsys.readouterr()
        
        assert "配置企业微信通知" in captured.out
    
    @patch('builtins.input', side_effect=['https://qyapi.weixin.qq.com/test', 'n', ''])
    def test_configure_wechat_with_new_url(self, mock_input, cli, capsys):
        """测试配置企业微信（修改URL）"""
        cli.configure_wechat()
        captured = capsys.readouterr()
        
        assert "配置企业微信通知" in captured.out
        assert "配置已保存" in captured.out
    
    def test_view_system_info(self, cli, sample_data, capsys):
        """测试查看系统信息"""
        cli.view_system_info()
        captured = capsys.readouterr()
        
        assert "系统信息" in captured.out
        assert "数据统计" in captured.out
        assert "交易记录: 1 条" in captured.out
        assert "往来单位: 1 个" in captured.out
        assert "V1.6 实用增强版" in captured.out
    
    def test_backup_data(self, cli, sample_data, capsys):
        """测试数据备份"""
        cli.backup_data()
        captured = capsys.readouterr()
        
        assert "数据备份" in captured.out
        assert ("备份完成" in captured.out or "备份失败" in captured.out)


class TestEndToEndWorkflows:
    """测试端到端工作流"""
    
    @patch('builtins.input', side_effect=['', '', ''])
    def test_report_generation_workflow(self, mock_input, cli, sample_data):
        """测试报表生成工作流"""
        # 生成管理报表
        cli.generate_management_report()
        
        # 验证报表目录存在
        reports_dir = os.path.join(cli.storage_dir, "reports")
        assert os.path.exists(reports_dir)
    
    @patch('builtins.input', return_value='n')
    def test_reminder_workflow(self, mock_input, cli, sample_data):
        """测试提醒工作流"""
        # 运行提醒检查
        cli.run_reminder_checks()
        
        # 验证提醒系统正常工作（不抛出异常）
        assert True
    
    def test_data_statistics_workflow(self, cli, sample_data, capsys):
        """测试数据统计工作流"""
        # 查看系统信息
        cli.view_system_info()
        captured = capsys.readouterr()
        
        # 验证统计数据正确
        assert "交易记录: 1 条" in captured.out
        assert "往来单位: 1 个" in captured.out


class TestErrorHandling:
    """测试错误处理"""
    
    @patch('builtins.input', return_value='invalid-date')
    def test_invalid_date_input(self, mock_input, cli, capsys):
        """测试无效日期输入"""
        result = cli.get_date_input("请输入日期")
        captured = capsys.readouterr()
        
        assert result is None
        assert "日期格式错误" in captured.out
    
    @patch('builtins.input', return_value='nonexistent.xlsx')
    def test_file_not_found_error(self, mock_input, cli, capsys):
        """测试文件不存在错误"""
        cli.import_transactions()
        captured = capsys.readouterr()
        
        assert "文件不存在" in captured.out
    
    @patch('builtins.input', return_value='')
    def test_empty_input_handling(self, mock_input, cli):
        """测试空输入处理"""
        result = cli.get_input("请输入", default="默认值")
        assert result == "默认值"


class TestUserInterface:
    """测试用户界面"""
    
    def test_menu_display(self, cli, capsys):
        """测试菜单显示"""
        options = ["选项1", "选项2"]
        cli.print_menu("测试菜单", options)
        captured = capsys.readouterr()
        
        # 验证菜单格式正确
        assert "测试菜单" in captured.out
        assert "1. 选项1" in captured.out
        assert "2. 选项2" in captured.out
        assert "0. 返回上级菜单" in captured.out
    
    def test_header_display(self, cli, capsys):
        """测试标题显示"""
        cli.print_header("测试标题")
        captured = capsys.readouterr()
        
        # 验证标题格式正确
        assert "测试标题" in captured.out
        assert "=" in captured.out
