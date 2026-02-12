#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
简单的测试运行器 - 用于验证审计和期间管理功能
"""

import sys
import os

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from decimal import Decimal
from datetime import date, timedelta
import tempfile

from oxidation_finance_v20.database.db_manager import DatabaseManager
from oxidation_finance_v20.business.finance_manager import FinanceManager
from oxidation_finance_v20.models.business_models import (
    Customer, Supplier, BankType, ExpenseType
)


def test_audit_trail():
    """测试审计轨迹功能"""
    print("\n=== 测试审计轨迹功能 ===")
    
    # 创建临时数据库
    fd, db_path = tempfile.mkstemp(suffix='.db')
    os.close(fd)
    
    try:
        db = DatabaseManager(db_path)
        db.connect()
        finance_mgr = FinanceManager(db)
        
        # 测试1: 记录操作日志
        print("\n测试1: 记录操作日志")
        log_id = finance_mgr.log_operation(
            operation_type="CREATE",
            entity_type="ORDER",
            entity_id="order-123",
            entity_name="测试订单",
            operator="张三",
            operation_description="创建新订单"
        )
        print(f"✓ 日志ID: {log_id}")
        
        # 测试2: 查询日志
        print("\n测试2: 查询日志")
        logs = finance_mgr.get_audit_logs(entity_id="order-123")
        assert len(logs) == 1
        assert logs[0]["operator"] == "张三"
        print(f"✓ 查询到 {len(logs)} 条日志")
        
        # 测试3: 获取实体审计轨迹
        print("\n测试3: 获取实体审计轨迹")
        entity_id = "order-789"
        for i in range(3):
            finance_mgr.log_operation(
                operation_type="UPDATE",
                entity_type="ORDER",
                entity_id=entity_id,
                operator=f"操作人{i+1}",
                operation_description=f"操作{i+1}"
            )
        
        trail = finance_mgr.get_entity_audit_trail("ORDER", entity_id)
        assert len(trail) == 3
        print(f"✓ 获取到 {len(trail)} 条审计轨迹")
        
        # 测试4: 操作统计
        print("\n测试4: 操作统计")
        stats = finance_mgr.get_operation_statistics()
        print(f"✓ 总操作数: {stats['total_operations']}")
        print(f"✓ 按操作类型: {stats['by_operation_type']}")
        print(f"✓ 按实体类型: {stats['by_entity_type']}")
        
        db.close()
        print("\n✅ 审计轨迹功能测试通过!")
        return True
        
    except Exception as e:
        print(f"\n❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        if os.path.exists(db_path):
            os.unlink(db_path)


def test_accounting_period():
    """测试会计期间管理功能"""
    print("\n=== 测试会计期间管理功能 ===")
    
    # 创建临时数据库
    fd, db_path = tempfile.mkstemp(suffix='.db')
    os.close(fd)
    
    try:
        db = DatabaseManager(db_path)
        db.connect()
        finance_mgr = FinanceManager(db)
        
        # 创建测试数据
        customer = Customer(
            name="测试客户",
            contact="张经理",
            phone="138****1234"
        )
        db.save_customer(customer)
        
        # 测试1: 创建会计期间
        print("\n测试1: 创建会计期间")
        result = finance_mgr.create_accounting_period(
            period_name="2024年1月",
            start_date=date(2024, 1, 1),
            end_date=date(2024, 1, 31)
        )
        assert "error" not in result
        period_id = result["id"]
        print(f"✓ 创建期间: {result['period_name']}")
        
        # 测试2: 调整会计期间
        print("\n测试2: 调整会计期间")
        success, message = finance_mgr.adjust_accounting_period(
            period_id=period_id,
            new_period_name="2024年1月（调整后）",
            notes="测试调整"
        )
        assert success is True
        print(f"✓ {message}")
        
        # 测试3: 在期间内记录收入和支出
        print("\n测试3: 在期间内记录收入和支出")
        finance_mgr.record_income(
            customer_id=customer.id,
            customer_name=customer.name,
            amount=Decimal("10000"),
            bank_type=BankType.G_BANK,
            income_date=date(2024, 1, 15)
        )
        
        finance_mgr.record_expense(
            expense_type=ExpenseType.RENT,
            amount=Decimal("3000"),
            bank_type=BankType.G_BANK,
            expense_date=date(2024, 1, 10)
        )
        print("✓ 记录收入和支出")
        
        # 测试4: 关闭会计期间
        print("\n测试4: 关闭会计期间")
        success, message = finance_mgr.close_accounting_period(
            period_id=period_id,
            closed_by="测试人员"
        )
        assert success is True
        print(f"✓ {message}")
        
        # 验证期间数据
        period = finance_mgr.get_accounting_period(period_id)
        assert period["is_closed"] is True
        assert period["total_income"] == Decimal("10000")
        assert period["total_expense"] == Decimal("3000")
        assert period["net_profit"] == Decimal("7000")
        print(f"✓ 期间汇总: 收入={period['total_income']}, 支出={period['total_expense']}, 净利润={period['net_profit']}")
        
        # 测试5: 重新打开期间
        print("\n测试5: 重新打开期间")
        success, message = finance_mgr.reopen_accounting_period(
            period_id=period_id,
            operator="测试人员",
            notes="需要调整"
        )
        assert success is True
        print(f"✓ {message}")
        
        # 测试6: 列出所有期间
        print("\n测试6: 列出所有期间")
        periods = finance_mgr.list_accounting_periods()
        print(f"✓ 共有 {len(periods)} 个会计期间")
        
        # 测试7: 获取当前期间
        print("\n测试7: 获取当前期间")
        current = finance_mgr.get_current_accounting_period(
            reference_date=date(2024, 1, 15)
        )
        assert current is not None
        print(f"✓ 当前期间: {current['period_name']}")
        
        # 测试8: 验证审计日志
        print("\n测试8: 验证审计日志")
        logs = finance_mgr.get_entity_audit_trail("ACCOUNTING_PERIOD", period_id)
        print(f"✓ 期间操作产生了 {len(logs)} 条审计日志")
        for log in logs:
            print(f"  - {log['operation_description']}")
        
        db.close()
        print("\n✅ 会计期间管理功能测试通过!")
        return True
        
    except Exception as e:
        print(f"\n❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        if os.path.exists(db_path):
            os.unlink(db_path)


def test_period_validation():
    """测试会计期间验证功能"""
    print("\n=== 测试会计期间验证功能 ===")
    
    # 创建临时数据库
    fd, db_path = tempfile.mkstemp(suffix='.db')
    os.close(fd)
    
    try:
        db = DatabaseManager(db_path)
        db.connect()
        finance_mgr = FinanceManager(db)
        
        # 测试1: 创建重叠期间应该失败
        print("\n测试1: 创建重叠期间应该失败")
        finance_mgr.create_accounting_period(
            period_name="2024年2月",
            start_date=date(2024, 2, 1),
            end_date=date(2024, 2, 29)
        )
        
        result = finance_mgr.create_accounting_period(
            period_name="2024年2月中旬",
            start_date=date(2024, 2, 15),
            end_date=date(2024, 2, 20)
        )
        assert "error" in result
        assert "重叠" in result["error"]
        print("✓ 正确拒绝重叠期间")
        
        # 测试2: 无效日期范围应该失败
        print("\n测试2: 无效日期范围应该失败")
        result = finance_mgr.create_accounting_period(
            period_name="无效期间",
            start_date=date(2024, 3, 31),
            end_date=date(2024, 3, 1)
        )
        assert "error" in result
        print("✓ 正确拒绝无效日期范围")
        
        # 测试3: 调整已关闭期间应该失败
        print("\n测试3: 调整已关闭期间应该失败")
        result = finance_mgr.create_accounting_period(
            period_name="2024年4月",
            start_date=date(2024, 4, 1),
            end_date=date(2024, 4, 30)
        )
        period_id = result["id"]
        finance_mgr.close_accounting_period(period_id)
        
        success, message = finance_mgr.adjust_accounting_period(
            period_id=period_id,
            new_end_date=date(2024, 4, 29)
        )
        assert success is False
        assert "已关闭" in message
        print("✓ 正确拒绝调整已关闭期间")
        
        db.close()
        print("\n✅ 会计期间验证功能测试通过!")
        return True
        
    except Exception as e:
        print(f"\n❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        if os.path.exists(db_path):
            os.unlink(db_path)


if __name__ == "__main__":
    print("=" * 60)
    print("审计轨迹和会计期间管理功能测试")
    print("=" * 60)
    
    results = []
    
    # 运行所有测试
    results.append(("审计轨迹功能", test_audit_trail()))
    results.append(("会计期间管理功能", test_accounting_period()))
    results.append(("会计期间验证功能", test_period_validation()))
    
    # 汇总结果
    print("\n" + "=" * 60)
    print("测试结果汇总")
    print("=" * 60)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for name, result in results:
        status = "✅ 通过" if result else "❌ 失败"
        print(f"{name}: {status}")
    
    print(f"\n总计: {passed}/{total} 测试通过")
    
    if passed == total:
        print("\n🎉 所有测试通过!")
        sys.exit(0)
    else:
        print(f"\n⚠️  有 {total - passed} 个测试失败")
        sys.exit(1)
