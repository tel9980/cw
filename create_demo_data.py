import pandas as pd
import os
import random
from datetime import datetime, timedelta

def create_demo_files():
    print("🚀 正在生成模拟测试数据...")
    
    # 1. 创建别名映射表 (Excel)
    # 场景：银行流水里全是 "G银行...", "网转...", "财付通..."，需要映射到标准公司名
    aliases_data = {
        "别名 (对方户名/摘要)": [
            "G银行-张三", 
            "财付通-李四餐饮", 
            "网转*王五技术服务", 
            "支付宝-滴滴出行", 
            "AWS-US-Bill"
        ],
        "标准单位名称": [
            "张三 (员工)", 
            "李四餐饮管理有限公司", 
            "王五科技工作室", 
            "滴滴出行", 
            "亚马逊云服务"
        ]
    }
    df_alias = pd.DataFrame(aliases_data)
    df_alias.to_excel("测试数据_别名导入模板.xlsx", index=False)
    print("✅ 已生成: 测试数据_别名导入模板.xlsx")

    # 2. 创建杂乱的银行流水/账单 (Excel)
    # 场景：包含需要清洗的摘要、需要匹配的别名、大额现金风险、重复录入
    
    # 生成日期
    today = datetime.now()
    dates = [(today - timedelta(days=i)).strftime("%Y-%m-%d") for i in range(5)]
    
    bank_data = [
        # 日期, 摘要, 收入, 支出, 对方户名
        [dates[0], "G银行-张三 报销款", 0, 5200, "张三"], # 风险：大额现金(如果被识别为现金) or 只是大额报销
        [dates[1], "财付通-李四餐饮 招待费", 0, 880, "李四餐饮"], # 应自动匹配别名
        [dates[2], "收货款", 20000, 0, "客户A"], 
        [dates[3], "网转*王五技术服务 开发费", 0, 5000, "王五"], # 应匹配别名
        [dates[4], "提现 / 手续费", 0, 10, "G银行"], # 干扰项
        [dates[0], "G银行-张三 报销款", 0, 5200, "张三"], # 风险：完全重复的记录
    ]
    
    df_bank = pd.DataFrame(bank_data, columns=["交易日期", "摘要", "收入金额", "支出金额", "对方户名"])
    df_bank.to_excel("测试数据_银行流水.xlsx", index=False)
    print("✅ 已生成: 测试数据_银行流水.xlsx")

    # 3. 创建标准凭证导出的预期结果 (仅作为示意，不生成文件，由代码生成)
    
    print("\n🎉 模拟数据准备完毕！")
    print("请使用 'test_logic.py' 来验证系统是否能正确处理这些数据。")

if __name__ == "__main__":
    create_demo_files()
