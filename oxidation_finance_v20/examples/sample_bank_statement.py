#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
创建示例银行流水Excel文件
"""

import pandas as pd
from pathlib import Path

def create_sample_bank_statement():
    """创建示例银行流水Excel文件"""
    
    # 示例数据
    data = {
        "交易日期": [
            "2024-01-15",
            "2024-01-16",
            "2024-01-17",
            "2024-01-18",
            "2024-01-19",
            "2024-01-20",
            "2024-01-21",
            "2024-01-22"
        ],
        "金额": [
            5000.00,      # 收入
            -2000.00,     # 支出
            3500.50,      # 收入
            -1200.00,     # 支出
            8000.00,      # 收入
            -500.00,      # 支出
            4200.00,      # 收入
            -3000.00      # 支出
        ],
        "交易对手": [
            "张三公司",
            "化工原料供应商",
            "李四工厂",
            "电力公司",
            "王五贸易",
            "喷砂加工厂",
            "赵六企业",
            "水务公司"
        ],
        "摘要": [
            "收到货款-订单001",
            "采购硫酸、硝酸",
            "收到加工费-订单002",
            "支付电费",
            "收到货款-订单003",
            "委外喷砂加工费",
            "收到加工费-订单004",
            "支付水费"
        ]
    }
    
    # 创建DataFrame
    df = pd.DataFrame(data)
    
    # 保存为Excel
    output_dir = Path(__file__).parent
    output_file = output_dir / "sample_bank_statement.xlsx"
    
    df.to_excel(output_file, index=False, sheet_name="银行流水")
    
    print(f"✓ 示例银行流水文件已创建: {output_file}")
    print(f"  - 共 {len(df)} 条记录")
    print(f"  - 日期范围: {df['交易日期'].min()} 至 {df['交易日期'].max()}")
    print(f"  - 总收入: {df[df['金额'] > 0]['金额'].sum():.2f}")
    print(f"  - 总支出: {abs(df[df['金额'] < 0]['金额'].sum()):.2f}")
    
    return output_file


if __name__ == "__main__":
    create_sample_bank_statement()
