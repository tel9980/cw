import sys
import os
import pandas as pd
import json
from datetime import datetime

# 模拟 Lark Client
class MockClient:
    pass

# 拦截 CW.py 的实际执行，只导入函数
# 我们需要 mock 一些全局变量，因为 CW.py 可能会在导入时初始化
import builtins

# 临时修改 path 以便导入
sys.path.append(os.getcwd())

print("🚀 开始逻辑验证测试...")

try:
    import CW
    print("✅ CW 模块导入成功")
except Exception as e:
    print(f"❌ CW 模块导入失败: {e}")
    sys.exit(1)

def test_alias_import():
    print("\n[测试 1] 批量导入别名...")
    # 模拟用户输入文件路径
    # 我们直接调用内部逻辑，或者 mock input
    # 这里我们手动读取 excel 并更新 CW.PARTNER_ALIASES
    
    excel_path = "测试数据_别名导入模板.xlsx"
    if not os.path.exists(excel_path):
        print("❌ 测试文件不存在")
        return

    df = pd.read_excel(excel_path)
    count = 0
    for _, row in df.iterrows():
        a = str(row.iloc[0]).strip()
        r = str(row.iloc[1]).strip()
        CW.PARTNER_ALIASES[a] = r
        count += 1
    
    print(f"✅ 模拟导入了 {count} 条别名规则")
    # 验证是否生效
    test_key = "G银行-张三"
    if test_key in CW.PARTNER_ALIASES:
        print(f"   验证通过: '{test_key}' -> '{CW.PARTNER_ALIASES[test_key]}'")
    else:
        print(f"   ❌ 验证失败: 未找到 '{test_key}'")

def test_data_processing_and_health_check():
    print("\n[测试 2] 数据读取、清洗与体检逻辑...")
    
    excel_path = "测试数据_银行流水.xlsx"
    # 使用 CW.read_excel_smart 读取
    # 注意：read_excel_smart 需要 interactive selection, 这里我们绕过它，直接测试核心逻辑
    # 实际上 read_excel_smart 内部主要是 pd.read_excel 和列名标准化
    
    df = pd.read_excel(excel_path)
    print(f"📄 读取到 {len(df)} 条原始数据")
    
    # 模拟处理流程 (参考 CW.import_from_excel 的逻辑)
    processed_records = []
    
    for idx, row in df.iterrows():
        # 模拟字段映射
        date_val = row["交易日期"]
        summary = str(row["摘要"])
        income = float(row["收入金额"])
        expense = float(row["支出金额"])
        partner_raw = str(row["对方户名"])
        
        amount = income if income > 0 else expense
        biz_type = "收款" if income > 0 else "付款"
        
        # 1. 清洗摘要 (Clean Description)
        cleaned_summary = CW.clean_description(summary)
        
        # 2. 别名匹配 (使用 CW.resolve_partner)
        # 先查户名
        final_partner = CW.resolve_partner(partner_raw)
        
        # 如果没变，查摘要
        if final_partner == partner_raw:
             memo_partner = CW.resolve_partner(summary)
             if memo_partner != summary:
                 final_partner = memo_partner
        
        # 3. 构造 Mock Record 对象用于体检
        # Mock class for Bitable Record
        class MockRecord:
            def __init__(self, fields):
                self.fields = fields
        
        fields = {
            "记账日期": int(datetime.strptime(date_val, "%Y-%m-%d").timestamp() * 1000),
            "业务类型": biz_type,
            "费用归类": "测试费用", # 简化
            "往来单位费用": final_partner,
            "实际收付金额": amount,
            "备注": cleaned_summary,
            "是否现金": "否", # 默认
            "是否有票": "无票"
        }
        
        # 特殊逻辑：如果是 "张三"，标记为现金 (模拟规则)
        if "张三" in final_partner:
            fields["是否现金"] = "是"
            
        processed_records.append(MockRecord(fields))
        
        print(f"   Row {idx+1}: {summary[:10]}... -> 伙伴:[{final_partner}] 金额:[{amount}]")

    print("\n[测试 3] 运行财务体检逻辑 (Mock)...")
    
    # 复制 CW.financial_health_check 的核心检查逻辑
    # 直接调用有点难，因为它是打印到控制台的。我们把 CW.py 里的逻辑 copy 过来一点点或者直接调用
    # 为了方便，我们直接调用 CW.financial_health_check，但是我们需要 mock client 和 get_all_records
    
    # Mock get_all_records
    original_get_all_records = CW.get_all_records
    CW.get_all_records = lambda c, t, tid: processed_records
    CW.get_table_id_by_name = lambda c, t, n: "mock_table_id"
    
    # Mock Zhipu client to avoid errors
    CW.zhipu_client = None 
    
    print("--- 体检报告输出开始 ---")
    CW.financial_health_check(None, None)
    print("--- 体检报告输出结束 ---")
    
    # 恢复
    CW.get_all_records = original_get_all_records

if __name__ == "__main__":
    test_alias_import()
    test_data_processing_and_health_check()
