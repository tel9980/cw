#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
审计轨迹和会计期间管理测试
"""

import pytest
from decimal import Decimal
from datetime import date, datetime, timedelta
import json

from oxidation_finance_v20.business.finance_manager import FinanceManager
from oxidation_finance_v20.models.business_models import (
    BankType, ExpenseType, OperationType, EntityType
)


class TestAuditTrail:
    """审计轨迹测试"""
    
    def test_log_operation_basic(self, db_manager):
        """测试基本操作日志记录"""
        finance_mgr = FinanceManager(db_manager)
        
        # 记录一个操作
        log_id = finance_mgr.log_operation(
            operation_type="CREATE",
            entity_type="ORDER",
            entity_id="order-123",
            entity_name="测试订单",
            operator="张三",
            operation_description="创建新订单",
            notes="测试日志"
        )
        
        assert log_id is not None
        assert len(log_id) > 0
    
    def test_log_operation_with_values(self, db_manager):
        """测试记录操作前后值"""
        finance_mgr = FinanceManager(db_manager)
        
        old_data = {"amount": 1000, "status": "pending"}
        new_data = {"amount": 1500, "status": "completed"}
        
        log_id = finance_mgr.log_operation(
            operation_type="UPDATE",
            entity_type="ORDER",
            entity_id="order-456",
            entity_name="订单456",
            operator="李四",
            operation_description="更新订单金额和状态",
            old_value=json.dumps(old_data, ensure_ascii=False),
            new_value=json.dumps(new_data, ensure_ascii=False)
        )
        
        assert log_id is not None
        
        # 查询日志
        logs = finance_mgr.get_audit_logs(entity_id="order-456")
        assert len(logs) == 1
        assert logs[0]["entity_id"] == "order-456"
        assert logs[0]["operator"] == "李四"
    
    def test_get_entity_audit_trail(self, db_manager):
        """测试获取实体的完整审计轨迹"""
        finance_mgr = FinanceManager(db_manager)
        
        entity_id = "order-789"
        
        # 记录多个操作
        finance_mgr.log_operation(
            operation_type="CREATE",
            entity_type="ORDER",
            entity_id=entity_id,
            entity_name="订单789",
            operator="张三",
            operation_description="创建订单"
        )
        
        finance_mgr.log_operation(
            operation_type="UPDATE",
            entity_type="ORDER",
            entity_id=entity_id,
            entity_name="订单789",
            operator="李四",
            operation_description="更新订单"
        )
        
        finance_mgr.log_operation(
            operation_type="UPDATE",
            entity_type="ORDER",
            entity_id=entity_id,
            entity_name="订单789",
            operator="王五",
            operation_description="完成订单"
        )
        
        # 获取审计轨迹
        trail = finance_mgr.get_entity_audit_trail("ORDER", entity_id)
        
        assert len(trail) == 3
        # 应该按时间倒序排列
        assert trail[0]["operation_description"] == "完成订单"
        assert trail[1]["operation_description"] == "更新订单"
        assert trail[2]["operation_description"] == "创建订单"
    
    def test_get_audit_logs_by_operator(self, db_manager):
        """测试按操作人查询日志"""
        finance_mgr = FinanceManager(db_manager)
        
        # 记录不同操作人的日志
        finance_mgr.log_operation(
            operation_type="CREATE",
            entity_type="ORDER",
            entity_id="order-1",
            operator="张三",
            operation_description="张三的操作"
        )
        
        finance_mgr.log_operation(
            operation_type="CREATE",
            entity_type="ORDER",
            entity_id="order-2",
            operator="李四",
            operation_description="李四的操作"
        )
        
        finance_mgr.log_operation(
            operation_type="UPDATE",
            entity_type="ORDER",
            entity_id="order-3",
            operator="张三",
            operation_description="张三的另一个操作"
        )
        
        # 查询张三的操作
        logs = finance_mgr.get_audit_logs(operator="张三")
        assert len(logs) == 2
        assert all(log["operator"] == "张三" for log in logs)
    
    def test_get_audit_logs_by_time_range(self, db_manager):
        """测试按时间范围查询日志"""
        finance_mgr = FinanceManager(db_manager)
        
        today = date.today()
        yesterday = today - timedelta(days=1)
        
        # 记录日志（实际上都是今天的，但我们可以测试查询逻辑）
        finance_mgr.log_operation(
            operation_type="CREATE",
            entity_type="ORDER",
            entity_id="order-time-1",
            operation_description="今天的操作"
        )
        
        # 查询今天的日志
        logs = finance_mgr.get_audit_logs(start_time=today, end_time=today)
        assert len(logs) >= 1
        
        # 查询昨天的日志（应该为空）
        logs = finance_mgr.get_audit_logs(start_time=yesterday, end_time=yesterday)
        # 可能为空，取决于测试运行时间
    
    def test_get_operation_statistics(self, db_manager):
        """测试操作统计"""
        finance_mgr = FinanceManager(db_manager)
        
        # 记录多种操作
        finance_mgr.log_operation(
            operation_type="CREATE",
            entity_type="ORDER",
            entity_id="order-stat-1",
            operator="张三"
        )
        
        finance_mgr.log_operation(
            operation_type="CREATE",
            entity_type="INCOME",
            entity_id="income-stat-1",
            operator="张三"
        )
        
        finance_mgr.log_operation(
            operation_type="UPDATE",
            entity_type="ORDER",
            entity_id="order-stat-2",
            operator="李四"
        )
        
        # 获取统计
        stats = finance_mgr.get_operation_statistics()
        
        assert stats["total_operations"] >= 3
        assert "by_operation_type" in stats
        assert "by_entity_type" in stats
        assert "by_operator" in stats
        
        # 验证统计数据
        assert stats["by_operator"]["张三"] >= 2
        assert stats["by_operator"]["李四"] >= 1


class TestAccountingPeriod:
    """会计期间管理测试"""
    
    def test_create_accounting_period(self, db_manager):
        """测试创建会计期间"""
        finance_mgr = FinanceManager(db_manager)
        
        start_date = date(2024, 1, 1)
        end_date = date(2024, 1, 31)
        
        result = finance_mgr.create_accounting_period(
            period_name="2024年1月",
            start_date=start_date,
            end_date=end_date,
            notes="测试期间"
        )
        
        assert "error" not in result
        assert result["period_name"] == "2024年1月"
        assert result["status"] == "开放"
        assert "message" in result
        
        # 验证期间已创建
        period = finance_mgr.get_accounting_period(result["id"])
        assert period is not None
        assert period["period_name"] == "2024年1月"
        assert period["is_closed"] is False
    
    def test_create_overlapping_period_fails(self, db_manager):
        """测试创建重叠期间应该失败"""
        finance_mgr = FinanceManager(db_manager)
        
        # 创建第一个期间
        finance_mgr.create_accounting_period(
            period_name="2024年1月",
            start_date=date(2024, 1, 1),
            end_date=date(2024, 1, 31)
        )
        
        # 尝试创建重叠期间
        result = finance_mgr.create_accounting_period(
            period_name="2024年1月中旬",
            start_date=date(2024, 1, 15),
            end_date=date(2024, 1, 20)
        )
        
        assert "error" in result
        assert "重叠" in result["error"]
    
    def test_create_invalid_date_range_fails(self, db_manager):
        """测试创建无效日期范围应该失败"""
        finance_mgr = FinanceManager(db_manager)
        
        result = finance_mgr.create_accounting_period(
            period_name="无效期间",
            start_date=date(2024, 1, 31),
            end_date=date(2024, 1, 1)  # 结束日期早于开始日期
        )
        
        assert "error" in result
    
    def test_adjust_accounting_period(self, db_manager):
        """测试调整会计期间"""
        finance_mgr = FinanceManager(db_manager)
        
        # 创建期间
        result = finance_mgr.create_accounting_period(
            period_name="2024年2月",
            start_date=date(2024, 2, 1),
            end_date=date(2024, 2, 28)
        )
        period_id = result["id"]
        
        # 调整期间（延长到29天）
        success, message = finance_mgr.adjust_accounting_period(
            period_id=period_id,
            new_end_date=date(2024, 2, 29),
            notes="闰年调整"
        )
        
        assert success is True
        assert "成功" in message
        
        # 验证调整
        period = finance_mgr.get_accounting_period(period_id)
        assert period["end_date"] == date(2024, 2, 29)
        assert "闰年调整" in period["notes"]
    
    def test_adjust_closed_period_fails(self, db_manager):
        """测试调整已关闭期间应该失败"""
        finance_mgr = FinanceManager(db_manager)
        
        # 创建并关闭期间
        result = finance_mgr.create_accounting_period(
            period_name="2024年3月",
            start_date=date(2024, 3, 1),
            end_date=date(2024, 3, 31)
        )
        period_id = result["id"]
        
        finance_mgr.close_accounting_period(period_id, closed_by="测试")
        
        # 尝试调整已关闭的期间
        success, message = finance_mgr.adjust_accounting_period(
            period_id=period_id,
            new_end_date=date(2024, 3, 30)
        )
        
        assert success is False
        assert "已关闭" in message
    
    def test_close_accounting_period(self, db_manager, sample_customer, sample_supplier):
        """测试关闭会计期间"""
        finance_mgr = FinanceManager(db_manager)
        
        # 保存客户和供应商
        db_manager.save_customer(sample_customer)
        db_manager.save_supplier(sample_supplier)
        
        # 创建期间
        start_date = date(2024, 4, 1)
        end_date = date(2024, 4, 30)
        
        result = finance_mgr.create_accounting_period(
            period_name="2024年4月",
            start_date=start_date,
            end_date=end_date
        )
        period_id = result["id"]
        
        # 在期间内记录一些收入和支出
        finance_mgr.record_income(
            customer_id=sample_customer.id,
            customer_name=sample_customer.name,
            amount=Decimal("10000"),
            bank_type=BankType.G_BANK,
            income_date=date(2024, 4, 15)
        )
        
        finance_mgr.record_expense(
            expense_type=ExpenseType.RENT,
            amount=Decimal("3000"),
            bank_type=BankType.G_BANK,
            expense_date=date(2024, 4, 10)
        )
        
        # 关闭期间
        success, message = finance_mgr.close_accounting_period(
            period_id=period_id,
            closed_by="财务主管",
            notes="月度结账"
        )
        
        assert success is True
        assert "已关闭" in message
        
        # 验证期间已关闭并计算了汇总数据
        period = finance_mgr.get_accounting_period(period_id)
        assert period["is_closed"] is True
        assert period["status"] == "关闭"
        assert period["total_income"] == Decimal("10000")
        assert period["total_expense"] == Decimal("3000")
        assert period["net_profit"] == Decimal("7000")
        assert period["closed_by"] == "财务主管"
        assert period["closed_at"] is not None
    
    def test_close_already_closed_period_fails(self, db_manager):
        """测试关闭已关闭期间应该失败"""
        finance_mgr = FinanceManager(db_manager)
        
        # 创建并关闭期间
        result = finance_mgr.create_accounting_period(
            period_name="2024年5月",
            start_date=date(2024, 5, 1),
            end_date=date(2024, 5, 31)
        )
        period_id = result["id"]
        
        finance_mgr.close_accounting_period(period_id)
        
        # 尝试再次关闭
        success, message = finance_mgr.close_accounting_period(period_id)
        
        assert success is False
        assert "已经关闭" in message
    
    def test_reopen_accounting_period(self, db_manager):
        """测试重新打开会计期间"""
        finance_mgr = FinanceManager(db_manager)
        
        # 创建并关闭期间
        result = finance_mgr.create_accounting_period(
            period_name="2024年6月",
            start_date=date(2024, 6, 1),
            end_date=date(2024, 6, 30)
        )
        period_id = result["id"]
        
        finance_mgr.close_accounting_period(period_id)
        
        # 重新打开
        success, message = finance_mgr.reopen_accounting_period(
            period_id=period_id,
            operator="财务主管",
            notes="需要调整数据"
        )
        
        assert success is True
        assert "重新打开" in message
        
        # 验证期间已重新打开
        period = finance_mgr.get_accounting_period(period_id)
        assert period["is_closed"] is False
        assert period["status"] == "开放"
        assert "重新打开" in period["notes"]
    
    def test_reopen_open_period_fails(self, db_manager):
        """测试重新打开已打开期间应该失败"""
        finance_mgr = FinanceManager(db_manager)
        
        # 创建期间（不关闭）
        result = finance_mgr.create_accounting_period(
            period_name="2024年7月",
            start_date=date(2024, 7, 1),
            end_date=date(2024, 7, 31)
        )
        period_id = result["id"]
        
        # 尝试重新打开已打开的期间
        success, message = finance_mgr.reopen_accounting_period(period_id)
        
        assert success is False
        assert "开放状态" in message
    
    def test_list_accounting_periods(self, db_manager):
        """测试列出所有会计期间"""
        finance_mgr = FinanceManager(db_manager)
        
        # 创建多个期间
        finance_mgr.create_accounting_period(
            period_name="2024年8月",
            start_date=date(2024, 8, 1),
            end_date=date(2024, 8, 31)
        )
        
        result2 = finance_mgr.create_accounting_period(
            period_name="2024年9月",
            start_date=date(2024, 9, 1),
            end_date=date(2024, 9, 30)
        )
        
        # 关闭一个期间
        finance_mgr.close_accounting_period(result2["id"])
        
        # 列出所有期间
        all_periods = finance_mgr.list_accounting_periods(include_closed=True)
        assert len(all_periods) >= 2
        
        # 只列出开放期间
        open_periods = finance_mgr.list_accounting_periods(include_closed=False)
        assert len(open_periods) >= 1
        assert all(not p["is_closed"] for p in open_periods)
    
    def test_get_current_accounting_period(self, db_manager):
        """测试获取当前会计期间"""
        finance_mgr = FinanceManager(db_manager)
        
        # 创建包含今天的期间
        today = date.today()
        start_of_month = date(today.year, today.month, 1)
        
        # 计算月末
        if today.month == 12:
            end_of_month = date(today.year, 12, 31)
        else:
            next_month = date(today.year, today.month + 1, 1)
            end_of_month = next_month - timedelta(days=1)
        
        finance_mgr.create_accounting_period(
            period_name=f"{today.year}年{today.month}月",
            start_date=start_of_month,
            end_date=end_of_month
        )
        
        # 获取当前期间
        current_period = finance_mgr.get_current_accounting_period()
        
        assert current_period is not None
        assert current_period["start_date"] <= today <= current_period["end_date"]
    
    def test_get_current_period_with_reference_date(self, db_manager):
        """测试使用参考日期获取会计期间"""
        finance_mgr = FinanceManager(db_manager)
        
        # 创建特定期间
        finance_mgr.create_accounting_period(
            period_name="2024年10月",
            start_date=date(2024, 10, 1),
            end_date=date(2024, 10, 31)
        )
        
        # 使用参考日期查询
        period = finance_mgr.get_current_accounting_period(
            reference_date=date(2024, 10, 15)
        )
        
        assert period is not None
        assert period["period_name"] == "2024年10月"


class TestAuditTrailIntegration:
    """审计轨迹集成测试"""
    
    def test_period_operations_create_audit_logs(self, db_manager):
        """测试期间操作会创建审计日志"""
        finance_mgr = FinanceManager(db_manager)
        
        # 创建期间
        result = finance_mgr.create_accounting_period(
            period_name="2024年11月",
            start_date=date(2024, 11, 1),
            end_date=date(2024, 11, 30)
        )
        period_id = result["id"]
        
        # 调整期间
        finance_mgr.adjust_accounting_period(
            period_id=period_id,
            new_period_name="2024年11月（调整后）",
            notes="测试调整"
        )
        
        # 关闭期间
        finance_mgr.close_accounting_period(period_id, closed_by="测试人员")
        
        # 检查审计日志
        logs = finance_mgr.get_entity_audit_trail("ACCOUNTING_PERIOD", period_id)
        
        # 应该有至少3条日志：创建、调整、关闭
        assert len(logs) >= 3
        
        # 验证日志内容
        log_descriptions = [log["operation_description"] for log in logs]
        assert any("创建会计期间" in desc for desc in log_descriptions)
        assert any("调整会计期间" in desc for desc in log_descriptions)
        assert any("关闭会计期间" in desc for desc in log_descriptions)
    
    def test_audit_trail_preserves_history(self, db_manager):
        """测试审计轨迹保留完整历史"""
        finance_mgr = FinanceManager(db_manager)
        
        # 创建期间
        result = finance_mgr.create_accounting_period(
            period_name="2024年12月",
            start_date=date(2024, 12, 1),
            end_date=date(2024, 12, 31)
        )
        period_id = result["id"]
        
        # 多次调整
        for i in range(3):
            finance_mgr.adjust_accounting_period(
                period_id=period_id,
                notes=f"第{i+1}次调整"
            )
        
        # 获取审计轨迹
        logs = finance_mgr.get_entity_audit_trail("ACCOUNTING_PERIOD", period_id)
        
        # 应该有4条日志：1次创建 + 3次调整
        assert len(logs) >= 4
        
        # 验证所有调整都被记录
        adjustment_logs = [log for log in logs if "调整" in log["operation_description"]]
        assert len(adjustment_logs) == 3


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
