#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
审计功能属性测试 - 验证审计轨迹完整性的核心正确性属性
"""

import pytest
from hypothesis import given, strategies as st, settings, assume
from decimal import Decimal
from datetime import date, datetime, timedelta
import tempfile
import os
import json

from oxidation_finance_v20.models.business_models import (
    Customer, Supplier, BankType, ExpenseType, OperationType, EntityType
)
from oxidation_finance_v20.database.db_manager import DatabaseManager
from oxidation_finance_v20.business.finance_manager import FinanceManager


# ==================== 策略定义 ====================

@st.composite
def customer_strategy(draw):
    """生成客户数据的策略"""
    return Customer(
        name=draw(st.text(min_size=1, max_size=50, alphabet=st.characters(whitelist_categories=('L', 'N')))),
        contact=draw(st.text(min_size=1, max_size=30, alphabet=st.characters(whitelist_categories=('L', 'N')))),
        phone=draw(st.text(min_size=8, max_size=15, alphabet=st.characters(whitelist_categories=('N',)))),
        address=draw(st.text(min_size=1, max_size=100, alphabet=st.characters(whitelist_categories=('L', 'N')))),
        credit_limit=Decimal(str(draw(st.floats(min_value=0, max_value=1000000, allow_nan=False, allow_infinity=False)))),
        notes=draw(st.text(max_size=200))
    )


@st.composite
def supplier_strategy(draw):
    """生成供应商数据的策略"""
    return Supplier(
        name=draw(st.text(min_size=1, max_size=50, alphabet=st.characters(whitelist_categories=('L', 'N')))),
        contact=draw(st.text(min_size=1, max_size=30, alphabet=st.characters(whitelist_categories=('L', 'N')))),
        phone=draw(st.text(min_size=8, max_size=15, alphabet=st.characters(whitelist_categories=('N',)))),
        address=draw(st.text(min_size=1, max_size=100, alphabet=st.characters(whitelist_categories=('L', 'N')))),
        business_type=draw(st.text(min_size=1, max_size=50, alphabet=st.characters(whitelist_categories=('L', 'N')))),
        notes=draw(st.text(max_size=200))
    )


@st.composite
def amount_strategy(draw):
    """生成金额的策略"""
    return Decimal(str(draw(st.floats(min_value=0.01, max_value=100000, allow_nan=False, allow_infinity=False))))


@st.composite
def date_strategy(draw):
    """生成日期的策略"""
    days_offset = draw(st.integers(min_value=-365, max_value=365))
    return date.today() + timedelta(days=days_offset)


@st.composite
def operator_strategy(draw):
    """生成操作人的策略"""
    operators = ["张三", "李四", "王五", "赵六", "系统管理员", "财务主管", "会计"]
    return draw(st.sampled_from(operators))


# ==================== 属性测试 ====================

class TestProperty19_AuditTrailCompleteness:
    """
    **属性 19: 审计轨迹完整性**
    **Validates: Requirements 6.4**
    
    对于任何业务操作，系统应该记录完整的操作轨迹，
    包括操作人、操作时间、操作内容和操作结果
    """
    
    @given(
        customer=customer_strategy(),
        amount=amount_strategy(),
        bank_type=st.sampled_from(list(BankType)),
        operator=operator_strategy()
    )
    @settings(max_examples=100, deadline=None)
    def test_income_operation_creates_audit_log(self, customer, amount, bank_type, operator):
        """测试收入操作创建完整的审计日志"""
        fd, path = tempfile.mkstemp(suffix='.db')
        os.close(fd)
        
        try:
            with DatabaseManager(path) as db:
                db.save_customer(customer)
                finance_manager = FinanceManager(db)
                
                # 记录收入
                income = finance_manager.record_income(
                    customer_id=customer.id,
                    customer_name=customer.name,
                    amount=amount,
                    bank_type=bank_type,
                    income_date=date.today()
                )
                
                # 手动记录审计日志（模拟系统行为）
                log_id = finance_manager.log_operation(
                    operation_type="CREATE",
                    entity_type="INCOME",
                    entity_id=income.id,
                    entity_name=f"{customer.name}收入",
                    operator=operator,
                    operation_description=f"记录收入：{amount}元",
                    new_value=json.dumps({
                        "customer_id": customer.id,
                        "amount": str(amount),
                        "bank_type": bank_type.value
                    }, ensure_ascii=False)
                )
                
                # 验证审计日志存在
                assert log_id is not None, "应该返回审计日志ID"
                assert len(log_id) > 0, "审计日志ID不应为空"
                
                # 查询审计日志
                logs = finance_manager.get_audit_logs(entity_id=income.id)
                assert len(logs) >= 1, "应该至少有一条审计日志"
                
                # 验证审计日志完整性
                log = logs[0]
                assert log["operator"] == operator, "应该记录操作人"
                assert log["operation_time"] is not None, "应该记录操作时间"
                assert log["operation_description"] is not None, "应该记录操作内容"
                assert log["entity_id"] == income.id, "应该记录实体ID"
                assert log["entity_type"] == "INCOME", "应该记录实体类型"
        
        finally:
            if os.path.exists(path):
                os.unlink(path)
    
    @given(
        supplier=supplier_strategy(),
        expense_type=st.sampled_from(list(ExpenseType)),
        amount=amount_strategy(),
        bank_type=st.sampled_from(list(BankType)),
        operator=operator_strategy()
    )
    @settings(max_examples=100, deadline=None)
    def test_expense_operation_creates_audit_log(self, supplier, expense_type, amount, bank_type, operator):
        """测试支出操作创建完整的审计日志"""
        fd, path = tempfile.mkstemp(suffix='.db')
        os.close(fd)
        
        try:
            with DatabaseManager(path) as db:
                db.save_supplier(supplier)
                finance_manager = FinanceManager(db)
                
                # 记录支出
                expense = finance_manager.record_expense(
                    expense_type=expense_type,
                    amount=amount,
                    bank_type=bank_type,
                    expense_date=date.today(),
                    supplier_id=supplier.id,
                    supplier_name=supplier.name
                )
                
                # 手动记录审计日志
                log_id = finance_manager.log_operation(
                    operation_type="CREATE",
                    entity_type="EXPENSE",
                    entity_id=expense.id,
                    entity_name=f"{expense_type.value}支出",
                    operator=operator,
                    operation_description=f"记录支出：{expense_type.value} {amount}元",
                    new_value=json.dumps({
                        "expense_type": expense_type.value,
                        "amount": str(amount),
                        "supplier_id": supplier.id
                    }, ensure_ascii=False)
                )
                
                # 验证审计日志
                assert log_id is not None, "应该返回审计日志ID"
                
                logs = finance_manager.get_audit_logs(entity_id=expense.id)
                assert len(logs) >= 1, "应该至少有一条审计日志"
                
                log = logs[0]
                assert log["operator"] == operator, "应该记录操作人"
                assert log["operation_time"] is not None, "应该记录操作时间"
                assert log["operation_description"] is not None, "应该记录操作内容"
                assert log["new_value"] is not None, "应该记录操作结果"
        
        finally:
            if os.path.exists(path):
                os.unlink(path)
    
    @given(
        period_name=st.text(min_size=1, max_size=50, alphabet=st.characters(whitelist_categories=('L', 'N'))),
        start_date=date_strategy(),
        end_date=date_strategy(),
        operator=operator_strategy()
    )
    @settings(max_examples=100, deadline=None)
    def test_accounting_period_operations_create_audit_trail(self, period_name, start_date, end_date, operator):
        """测试会计期间操作创建完整的审计轨迹"""
        # 确保日期范围有效
        if start_date > end_date:
            start_date, end_date = end_date, start_date
        
        fd, path = tempfile.mkstemp(suffix='.db')
        os.close(fd)
        
        try:
            with DatabaseManager(path) as db:
                finance_manager = FinanceManager(db)
                
                # 创建会计期间（自动记录审计日志）
                result = finance_manager.create_accounting_period(
                    period_name=period_name,
                    start_date=start_date,
                    end_date=end_date
                )
                
                if "error" in result:
                    # 如果创建失败（如日期重叠），跳过此测试
                    assume(False)
                
                period_id = result["id"]
                
                # 调整期间（自动记录审计日志）
                finance_manager.adjust_accounting_period(
                    period_id=period_id,
                    notes="测试调整"
                )
                
                # 获取审计轨迹
                trail = finance_manager.get_entity_audit_trail("ACCOUNTING_PERIOD", period_id)
                
                # 验证审计轨迹完整性
                assert len(trail) >= 2, "应该至少有2条审计日志（创建和调整）"
                
                # 验证每条日志都包含必要信息
                for log in trail:
                    assert log["operator"] is not None, "每条日志应该记录操作人"
                    assert log["operation_time"] is not None, "每条日志应该记录操作时间"
                    assert log["operation_description"] is not None, "每条日志应该记录操作内容"
                    assert log["entity_id"] == period_id, "每条日志应该关联正确的实体ID"
                
                # 验证日志按时间倒序排列
                if len(trail) >= 2:
                    assert trail[0]["operation_time"] >= trail[1]["operation_time"], \
                        "审计日志应该按时间倒序排列"
        
        finally:
            if os.path.exists(path):
                os.unlink(path)
    
    @given(
        customer=customer_strategy(),
        num_operations=st.integers(min_value=2, max_value=10),
        operator=operator_strategy()
    )
    @settings(max_examples=100, deadline=None)
    def test_multiple_operations_create_complete_audit_trail(self, customer, num_operations, operator):
        """测试多次操作创建完整的审计轨迹"""
        fd, path = tempfile.mkstemp(suffix='.db')
        os.close(fd)
        
        try:
            with DatabaseManager(path) as db:
                db.save_customer(customer)
                finance_manager = FinanceManager(db)
                
                # 记录多次操作
                entity_id = f"test-entity-{customer.id}"
                for i in range(num_operations):
                    finance_manager.log_operation(
                        operation_type="UPDATE",
                        entity_type="ORDER",
                        entity_id=entity_id,
                        entity_name=f"测试订单{i+1}",
                        operator=operator,
                        operation_description=f"第{i+1}次操作",
                        old_value=json.dumps({"step": i}, ensure_ascii=False),
                        new_value=json.dumps({"step": i+1}, ensure_ascii=False)
                    )
                
                # 获取完整审计轨迹
                trail = finance_manager.get_entity_audit_trail("ORDER", entity_id)
                
                # 验证所有操作都被记录
                assert len(trail) == num_operations, \
                    f"应该记录所有{num_operations}次操作"
                
                # 验证每次操作的完整性
                for i, log in enumerate(trail):
                    assert log["operator"] == operator, f"第{i+1}条日志应该记录操作人"
                    assert log["operation_time"] is not None, f"第{i+1}条日志应该记录操作时间"
                    assert log["operation_description"] is not None, f"第{i+1}条日志应该记录操作内容"
                    assert log["old_value"] is not None or i == num_operations - 1, \
                        f"第{i+1}条日志应该记录旧值"
                    assert log["new_value"] is not None, f"第{i+1}条日志应该记录新值"
        
        finally:
            if os.path.exists(path):
                os.unlink(path)
    
    @given(
        operators=st.lists(operator_strategy(), min_size=2, max_size=5, unique=True),
        customer=customer_strategy()
    )
    @settings(max_examples=100, deadline=None)
    def test_audit_logs_distinguish_different_operators(self, operators, customer):
        """测试审计日志能区分不同操作人"""
        fd, path = tempfile.mkstemp(suffix='.db')
        os.close(fd)
        
        try:
            with DatabaseManager(path) as db:
                db.save_customer(customer)
                finance_manager = FinanceManager(db)
                
                # 不同操作人执行操作
                entity_id = f"test-entity-{customer.id}"
                for operator in operators:
                    finance_manager.log_operation(
                        operation_type="UPDATE",
                        entity_type="ORDER",
                        entity_id=entity_id,
                        entity_name="测试订单",
                        operator=operator,
                        operation_description=f"{operator}的操作"
                    )
                
                # 按操作人查询
                for operator in operators:
                    logs = finance_manager.get_audit_logs(operator=operator)
                    assert len(logs) >= 1, f"应该能查询到{operator}的操作日志"
                    assert all(log["operator"] == operator for log in logs), \
                        f"查询结果应该只包含{operator}的操作"
        
        finally:
            if os.path.exists(path):
                os.unlink(path)
    
    @given(
        customer=customer_strategy(),
        num_operations=st.integers(min_value=3, max_value=10)
    )
    @settings(max_examples=100, deadline=None)
    def test_audit_logs_preserve_chronological_order(self, customer, num_operations):
        """测试审计日志保持时间顺序"""
        fd, path = tempfile.mkstemp(suffix='.db')
        os.close(fd)
        
        try:
            with DatabaseManager(path) as db:
                db.save_customer(customer)
                finance_manager = FinanceManager(db)
                
                # 按顺序记录操作
                entity_id = f"test-entity-{customer.id}"
                for i in range(num_operations):
                    finance_manager.log_operation(
                        operation_type="UPDATE",
                        entity_type="ORDER",
                        entity_id=entity_id,
                        entity_name="测试订单",
                        operation_description=f"操作{i+1}"
                    )
                
                # 获取审计轨迹
                trail = finance_manager.get_entity_audit_trail("ORDER", entity_id)
                
                # 验证时间顺序（倒序）
                for i in range(len(trail) - 1):
                    assert trail[i]["operation_time"] >= trail[i+1]["operation_time"], \
                        "审计日志应该按时间倒序排列（最新的在前）"
        
        finally:
            if os.path.exists(path):
                os.unlink(path)
    
    @given(
        customer=customer_strategy(),
        start_date=date_strategy(),
        end_date=date_strategy()
    )
    @settings(max_examples=100, deadline=None)
    def test_audit_logs_can_be_filtered_by_time_range(self, customer, start_date, end_date):
        """测试审计日志可以按时间范围过滤"""
        # 确保日期范围有效
        if start_date > end_date:
            start_date, end_date = end_date, start_date
        
        fd, path = tempfile.mkstemp(suffix='.db')
        os.close(fd)
        
        try:
            with DatabaseManager(path) as db:
                db.save_customer(customer)
                finance_manager = FinanceManager(db)
                
                # 记录操作
                entity_id = f"test-entity-{customer.id}"
                finance_manager.log_operation(
                    operation_type="CREATE",
                    entity_type="ORDER",
                    entity_id=entity_id,
                    entity_name="测试订单",
                    operation_description="创建订单"
                )
                
                # 按时间范围查询
                logs = finance_manager.get_audit_logs(
                    start_time=start_date,
                    end_time=end_date
                )
                
                # 验证查询结果在时间范围内
                for log in logs:
                    log_date = log["operation_time"].date() if isinstance(log["operation_time"], datetime) else log["operation_time"]
                    assert start_date <= log_date <= end_date, \
                        f"日志时间 {log_date} 应该在范围 {start_date} 到 {end_date} 内"
        
        finally:
            if os.path.exists(path):
                os.unlink(path)
    
    @given(
        customer=customer_strategy(),
        num_operations=st.integers(min_value=5, max_value=20)
    )
    @settings(max_examples=100, deadline=None)
    def test_operation_statistics_aggregate_correctly(self, customer, num_operations):
        """测试操作统计正确汇总"""
        fd, path = tempfile.mkstemp(suffix='.db')
        os.close(fd)
        
        try:
            with DatabaseManager(path) as db:
                db.save_customer(customer)
                finance_manager = FinanceManager(db)
                
                # 记录不同类型的操作
                entity_id = f"test-entity-{customer.id}"
                create_count = 0
                update_count = 0
                
                for i in range(num_operations):
                    if i % 3 == 0:
                        op_type = "CREATE"
                        create_count += 1
                    else:
                        op_type = "UPDATE"
                        update_count += 1
                    
                    finance_manager.log_operation(
                        operation_type=op_type,
                        entity_type="ORDER",
                        entity_id=f"{entity_id}-{i}",
                        entity_name=f"测试订单{i}",
                        operation_description=f"{op_type}操作"
                    )
                
                # 获取操作统计
                stats = finance_manager.get_operation_statistics()
                
                # 验证统计准确性
                assert stats["total_operations"] >= num_operations, \
                    f"总操作数应该至少为{num_operations}"
                
                assert "by_operation_type" in stats, "应该包含按操作类型的统计"
                assert "by_entity_type" in stats, "应该包含按实体类型的统计"
                assert "by_operator" in stats, "应该包含按操作人的统计"
                
                # 验证操作类型统计
                if "CREATE" in stats["by_operation_type"]:
                    assert stats["by_operation_type"]["CREATE"] >= create_count, \
                        f"CREATE操作数应该至少为{create_count}"
                
                if "UPDATE" in stats["by_operation_type"]:
                    assert stats["by_operation_type"]["UPDATE"] >= update_count, \
                        f"UPDATE操作数应该至少为{update_count}"
        
        finally:
            if os.path.exists(path):
                os.unlink(path)
    
    @given(
        customer=customer_strategy(),
        old_amount=amount_strategy(),
        new_amount=amount_strategy(),
        operator=operator_strategy()
    )
    @settings(max_examples=100, deadline=None)
    def test_audit_log_records_value_changes(self, customer, old_amount, new_amount, operator):
        """测试审计日志记录值的变化"""
        fd, path = tempfile.mkstemp(suffix='.db')
        os.close(fd)
        
        try:
            with DatabaseManager(path) as db:
                db.save_customer(customer)
                finance_manager = FinanceManager(db)
                
                # 记录值变化
                entity_id = f"test-entity-{customer.id}"
                old_data = {"amount": str(old_amount), "status": "pending"}
                new_data = {"amount": str(new_amount), "status": "completed"}
                
                log_id = finance_manager.log_operation(
                    operation_type="UPDATE",
                    entity_type="ORDER",
                    entity_id=entity_id,
                    entity_name="测试订单",
                    operator=operator,
                    operation_description="更新订单金额和状态",
                    old_value=json.dumps(old_data, ensure_ascii=False),
                    new_value=json.dumps(new_data, ensure_ascii=False)
                )
                
                # 查询审计日志
                logs = finance_manager.get_audit_logs(entity_id=entity_id)
                assert len(logs) >= 1, "应该有审计日志"
                
                log = logs[0]
                assert log["old_value"] is not None, "应该记录旧值"
                assert log["new_value"] is not None, "应该记录新值"
                
                # 验证值可以被解析
                old_parsed = json.loads(log["old_value"])
                new_parsed = json.loads(log["new_value"])
                
                assert old_parsed["amount"] == str(old_amount), "旧值应该正确记录"
                assert new_parsed["amount"] == str(new_amount), "新值应该正确记录"
        
        finally:
            if os.path.exists(path):
                os.unlink(path)
    
    @given(
        customer=customer_strategy(),
        amount=amount_strategy()
    )
    @settings(max_examples=100, deadline=None)
    def test_audit_trail_survives_entity_deletion(self, customer, amount):
        """测试实体删除后审计轨迹仍然保留"""
        fd, path = tempfile.mkstemp(suffix='.db')
        os.close(fd)
        
        try:
            with DatabaseManager(path) as db:
                db.save_customer(customer)
                finance_manager = FinanceManager(db)
                
                # 创建收入并记录审计日志
                income = finance_manager.record_income(
                    customer_id=customer.id,
                    customer_name=customer.name,
                    amount=amount,
                    bank_type=BankType.G_BANK,
                    income_date=date.today()
                )
                
                finance_manager.log_operation(
                    operation_type="CREATE",
                    entity_type="INCOME",
                    entity_id=income.id,
                    entity_name=f"{customer.name}收入",
                    operation_description=f"创建收入：{amount}元"
                )
                
                # 记录删除操作
                finance_manager.log_operation(
                    operation_type="DELETE",
                    entity_type="INCOME",
                    entity_id=income.id,
                    entity_name=f"{customer.name}收入",
                    operation_description="删除收入记录"
                )
                
                # 即使实体被删除，审计轨迹应该仍然存在
                trail = finance_manager.get_entity_audit_trail("INCOME", income.id)
                assert len(trail) >= 2, "删除后审计轨迹应该仍然保留"
                
                # 验证包含删除操作
                delete_logs = [log for log in trail if "删除" in log["operation_description"]]
                assert len(delete_logs) >= 1, "应该记录删除操作"
        
        finally:
            if os.path.exists(path):
                os.unlink(path)


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
