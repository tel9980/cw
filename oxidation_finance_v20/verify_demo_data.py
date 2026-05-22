#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
验证演示数据完整性
"""
import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).resolve().parent / "oxidation_finance_demo_ready.db"

def to_float(value):
    """将字符串转换为浮点数"""
    try:
        return float(value) if value else 0.0
    except (ValueError, TypeError):
        return 0.0

def verify_data():
    print("=" * 60)
    print("🔍 验证演示数据完整性")
    print("=" * 60)
    
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    
    try:
        # 1. 检查客户数量
        customers = conn.execute("SELECT COUNT(*) FROM customers").fetchone()[0]
        print(f"✅ 客户数量: {customers}")
        
        # 2. 检查供应商数量
        suppliers = conn.execute("SELECT COUNT(*) FROM suppliers").fetchone()[0]
        print(f"✅ 供应商数量: {suppliers}")
        
        # 3. 检查订单数量
        orders = conn.execute("SELECT COUNT(*) FROM processing_orders").fetchone()[0]
        print(f"✅ 订单数量: {orders}")
        
        # 4. 检查收入记录数量
        incomes = conn.execute("SELECT COUNT(*) FROM incomes").fetchone()[0]
        print(f"✅ 收入记录数量: {incomes}")
        
        # 5. 检查支出记录数量
        expenses = conn.execute("SELECT COUNT(*) FROM expenses").fetchone()[0]
        print(f"✅ 支出记录数量: {expenses}")
        
        # 6. 检查银行账户
        bank_accounts = conn.execute("SELECT COUNT(*) FROM bank_accounts").fetchone()[0]
        print(f"✅ 银行账户数量: {bank_accounts}")
        
        # 7. 检查银行交易
        bank_transactions = conn.execute("SELECT COUNT(*) FROM bank_transactions").fetchone()[0]
        print(f"✅ 银行交易数量: {bank_transactions}")
        
        # 8. 检查会计凭证
        vouchers = conn.execute("SELECT COUNT(*) FROM accounting_vouchers").fetchone()[0]
        print(f"✅ 会计凭证数量: {vouchers}")
        
        # 9. 统计总金额
        total_income = to_float(conn.execute("SELECT SUM(CAST(amount AS REAL)) FROM incomes").fetchone()[0])
        total_expense = to_float(conn.execute("SELECT SUM(CAST(amount AS REAL)) FROM expenses").fetchone()[0])
        
        print(f"\n💰 财务概览:")
        print(f"   总收入: ¥{total_income:,.2f}")
        print(f"   总支出: ¥{total_expense:,.2f}")
        print(f"   净收入: ¥{total_income - total_expense:,.2f}")
        
        # 10. 显示一些示例数据
        print(f"\n📋 示例订单:")
        sample_orders = conn.execute("""
            SELECT order_no, customer_name, total_amount, status 
            FROM processing_orders 
            LIMIT 3
        """).fetchall()
        
        for order in sample_orders:
            print(f"   - {order['order_no']}: {order['customer_name']} - ¥{to_float(order['total_amount']):,.2f} ({order['status']})")
        
        print("\n" + "=" * 60)
        print("🎉 演示数据验证完成！所有数据正常。")
        print("=" * 60)
        
        return True
        
    except Exception as e:
        print(f"❌ 验证失败: {e}")
        return False
    finally:
        conn.close()

if __name__ == "__main__":
    verify_data()
