#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
快速测试Hypothesis是否工作
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from hypothesis import given, strategies as st, settings
from decimal import Decimal
import tempfile

from oxidation_finance_v20.database.db_manager import DatabaseManager
from oxidation_finance_v20.business.finance_manager import FinanceManager
from oxidation_finance_v20.models.business_models import Customer, BankType

@given(
    amount=st.decimals(min_value=Decimal("1"), max_value=Decimal("10000"), places=2)
)
@settings(max_examples=10, deadline=None)
def test_simple_audit_log(amount):
    """简单测试：审计日志记录"""
    fd, path = tempfile.mkstemp(suffix='.db')
    os.close(fd)
    
    try:
        with DatabaseManager(path) as db:
            finance_manager = FinanceManager(db)
            
            # 记录操作
            log_id = finance_manager.log_operation(
                operation_type="CREATE",
                entity_type="TEST",
                entity_id="test-123",
                operator="测试员",
                operation_description=f"测试金额: {amount}"
            )
            
            # 验证
            assert log_id is not None
            assert len(log_id) > 0
            
            # 查询
            logs = finance_manager.get_audit_logs(entity_id="test-123")
            assert len(logs) >= 1
            assert logs[0]["operator"] == "测试员"
    
    finally:
        if os.path.exists(path):
            os.unlink(path)

if __name__ == "__main__":
    print("运行Hypothesis快速测试...")
    try:
        test_simple_audit_log()
        print("✅ Hypothesis测试通过!")
        sys.exit(0)
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
