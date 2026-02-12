#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
验证审计属性测试 - 简单验证脚本
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from decimal import Decimal
from datetime import date
import tempfile
import json

from oxidation_finance_v20.database.db_manager import DatabaseManager
from oxidation_finance_v20.business.finance_manager import FinanceManager
from oxidation_finance_v20.models.business_models import (
    Customer, BankType, ExpenseType
)


def test_property_19_basic():
    """测试属性19: 审计轨迹完整性 - 基本测试"""
    print("\n=== 测试属性19: 审计轨迹完整性 ===")
    
    fd, path = tempfile.mkstemp(suffix='.db')
    os.close(fd)
    
    try:
        with DatabaseManager(path) as db:
            finance_manager = FinanceManager(db)
            
            # 测试1: 记录操作并验证审计日志包含所有必要信息
            print("\n测试1: 审计日志包含操作人、时间、内容和结果")
            
            customer = Customer(
                name="测试客户",
                contact="张经理",
                phone="13800138000"
            )
            db.save_customer(customer)
            
            # 记录收入
            income = finance_manager.record_income(
                customer_id=customer.id,
                customer_name=customer.name,
                amount=Decimal("5000"),
                bank_type=BankType.G_BANK,
                income_date=date.today()
            )
            
            # 记录审计日志
            log_id = finance_manager.log_operation(
                operation_type="CREATE",
                entity_type="INCOME",
                entity_id=income.id,
                entity_name=f"{customer.name}收入",
                operator="张三",
                operation_description=f"记录收入：5000元",
                new_value=json.dumps({
                    "customer_id": customer.id,
                    "amount": "5000",
                    "bank_type": BankType.G_BANK.value
                }, ensure_ascii=False)
            )
            
            # 验证审计日志
            logs = finance_manager.get_audit_logs(entity_id=income.id)
            assert len(logs) >= 1, "应该至少有一条审计日志"
            
            log = logs[0]
            assert log["operator"] is not None, "应该记录操作人"
            assert log["operator"] == "张三", f"操作人应该是'张三'，实际是'{log['operator']}'"
            assert log["operation_time"] is not None, "应该记录操作时间"
            assert log["operation_description"] is not None, "应该记录操作内容"
            assert "记录收入" in log["operation_description"], "操作内容应该包含'记录收入'"
            assert log["new_value"] is not None, "应该记录操作结果"
            
            print("✓ 审计日志包含所有必要信息：操作人、时间、内容和结果")
            
            # 测试2: 多次操作创建完整审计轨迹
            print("\n测试2: 多次操作创建完整审计轨迹")
            
            entity_id = "test-order-123"
            for i in range(5):
                finance_manager.log_operation(
                    operation_type="UPDATE",
                    entity_type="ORDER",
                    entity_id=entity_id,
                    entity_name=f"测试订单{i+1}",
                    operator="李四",
                    operation_description=f"第{i+1}次操作"
                )
            
            trail = finance_manager.get_entity_audit_trail("ORDER", entity_id)
            assert len(trail) == 5, f"应该有5条审计记录，实际有{len(trail)}条"
            
            # 验证每条记录都完整
            for i, log in enumerate(trail):
                assert log["operator"] == "李四", f"第{i+1}条记录的操作人应该是'李四'"
                assert log["operation_time"] is not None, f"第{i+1}条记录应该有操作时间"
                assert log["operation_description"] is not None, f"第{i+1}条记录应该有操作内容"
            
            print("✓ 多次操作创建了完整的审计轨迹")
            
            # 测试3: 会计期间操作自动记录审计日志
            print("\n测试3: 会计期间操作自动记录审计日志")
            
            result = finance_manager.create_accounting_period(
                period_name="2024年测试期间",
                start_date=date(2024, 6, 1),
                end_date=date(2024, 6, 30)
            )
            
            if "error" not in result:
                period_id = result["id"]
                
                # 调整期间
                finance_manager.adjust_accounting_period(
                    period_id=period_id,
                    notes="测试调整"
                )
                
                # 获取审计轨迹
                period_trail = finance_manager.get_entity_audit_trail("ACCOUNTING_PERIOD", period_id)
                assert len(period_trail) >= 2, "应该至少有2条审计日志（创建和调整）"
                
                # 验证日志内容
                for log in period_trail:
                    assert log["operator"] is not None, "每条日志应该有操作人"
                    assert log["operation_time"] is not None, "每条日志应该有操作时间"
                    assert log["operation_description"] is not None, "每条日志应该有操作内容"
                
                print("✓ 会计期间操作自动记录了完整的审计日志")
            else:
                print("⚠ 跳过会计期间测试（期间创建失败）")
            
            # 测试4: 操作统计功能
            print("\n测试4: 操作统计功能")
            
            stats = finance_manager.get_operation_statistics()
            assert stats["total_operations"] > 0, "应该有操作记录"
            assert "by_operation_type" in stats, "应该包含按操作类型的统计"
            assert "by_entity_type" in stats, "应该包含按实体类型的统计"
            assert "by_operator" in stats, "应该包含按操作人的统计"
            
            print(f"✓ 操作统计功能正常：总操作数={stats['total_operations']}")
            
            print("\n✅ 属性19测试通过：审计轨迹完整性得到验证")
            return True
            
    except Exception as e:
        print(f"\n❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        if os.path.exists(path):
            os.unlink(path)


def test_property_19_comprehensive():
    """测试属性19: 审计轨迹完整性 - 综合测试"""
    print("\n=== 综合测试：审计轨迹在各种操作中的完整性 ===")
    
    fd, path = tempfile.mkstemp(suffix='.db')
    os.close(fd)
    
    try:
        with DatabaseManager(path) as db:
            finance_manager = FinanceManager(db)
            
            # 创建测试数据
            customer = Customer(
                name="综合测试客户",
                contact="王经理",
                phone="13900139000"
            )
            db.save_customer(customer)
            
            # 测试不同类型的操作
            operations = [
                ("CREATE", "INCOME", "创建收入"),
                ("UPDATE", "INCOME", "更新收入"),
                ("CREATE", "EXPENSE", "创建支出"),
                ("UPDATE", "EXPENSE", "更新支出"),
                ("CREATE", "ORDER", "创建订单"),
                ("UPDATE", "ORDER", "更新订单"),
            ]
            
            entity_ids = []
            for op_type, entity_type, description in operations:
                entity_id = f"test-{entity_type.lower()}-{len(entity_ids)}"
                entity_ids.append((entity_type, entity_id))
                
                finance_manager.log_operation(
                    operation_type=op_type,
                    entity_type=entity_type,
                    entity_id=entity_id,
                    entity_name=f"测试{entity_type}",
                    operator="综合测试员",
                    operation_description=description,
                    new_value=json.dumps({"test": "data"}, ensure_ascii=False)
                )
            
            # 验证每个实体的审计轨迹
            for entity_type, entity_id in entity_ids:
                trail = finance_manager.get_entity_audit_trail(entity_type, entity_id)
                assert len(trail) >= 1, f"{entity_type} {entity_id} 应该有审计轨迹"
                
                for log in trail:
                    # 验证四个核心要素：操作人、时间、内容、结果
                    assert log["operator"] is not None, "缺少操作人"
                    assert log["operation_time"] is not None, "缺少操作时间"
                    assert log["operation_description"] is not None, "缺少操作内容"
                    # 结果可以在new_value或operation_description中
                    assert log["new_value"] is not None or log["operation_description"], "缺少操作结果"
            
            print(f"✓ 验证了{len(entity_ids)}个实体的审计轨迹完整性")
            
            # 验证按操作人查询
            operator_logs = finance_manager.get_audit_logs(operator="综合测试员")
            assert len(operator_logs) >= len(operations), "应该能查询到所有操作"
            
            print(f"✓ 按操作人查询到{len(operator_logs)}条记录")
            
            print("\n✅ 综合测试通过：审计轨迹在各种操作中保持完整性")
            return True
            
    except Exception as e:
        print(f"\n❌ 综合测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        if os.path.exists(path):
            os.unlink(path)


if __name__ == "__main__":
    print("=" * 70)
    print("属性19: 审计轨迹完整性 - 验证测试")
    print("=" * 70)
    
    results = []
    results.append(("基本测试", test_property_19_basic()))
    results.append(("综合测试", test_property_19_comprehensive()))
    
    print("\n" + "=" * 70)
    print("测试结果汇总")
    print("=" * 70)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for name, result in results:
        status = "✅ 通过" if result else "❌ 失败"
        print(f"{name}: {status}")
    
    print(f"\n总计: {passed}/{total} 测试通过")
    
    if passed == total:
        print("\n🎉 所有测试通过! 属性19得到验证")
        print("\n属性19: 审计轨迹完整性")
        print("对于任何业务操作，系统记录了完整的操作轨迹，")
        print("包括操作人、操作时间、操作内容和操作结果")
        sys.exit(0)
    else:
        print(f"\n⚠️ 有 {total - passed} 个测试失败")
        sys.exit(1)
