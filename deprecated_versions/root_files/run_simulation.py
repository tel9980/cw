
import os
import sys
import logging
from unittest.mock import MagicMock
import builtins
import time

# 1. Setup Environment
os.environ["FEISHU_APP_ID"] = "mock_app_id"
os.environ["FEISHU_APP_SECRET"] = "mock_app_secret"
os.environ["FEISHU_APP_TOKEN"] = "mock_app_token"
os.environ["ZHIPUAI_API_KEY"] = "mock_ai_key"

# 2. Generate Demo Data
import create_demo_data
create_demo_data.create_demo_files()

# 3. Import CW and patch
import CW
from mock_feishu import MockClient, MockDataStore

# Reset Mock Data
MockDataStore.reset()

# Patch init_clients
CW.init_clients = lambda: MockClient()
CW.APP_TOKEN = "mock_app_token"
CW.ZHIPUAI_API_KEY = "mock_ai_key"
# Mock ZhipuAI to avoid errors
CW.zhipu_client = MagicMock()
CW.zhipu_client.chat.completions.create.return_value.choices[0].message.content = "分类：办公费"

# Patch ZhipuAI class for functions that instantiate it locally (e.g. get_ai_insight)
CW.ZhipuAI = MagicMock()
CW.ZhipuAI.return_value.chat.completions.create.return_value.choices[0].message.content = "AI 诊断建议: 经营状况良好。"

# Patch input to automate interaction
original_input = builtins.input
input_queue = []

def mock_input(prompt=""):
    print(f"[Mock Input] Prompt: {prompt}")
    p_str = str(prompt)
    
    if input_queue:
        val = input_queue.pop(0)
        print(f"[Mock Input] Auto-typing: {val}")
        return val
    
    # Default fallbacks
    if "y/n" in p_str: return "n"
    if "请选择" in p_str: return "1"
    
    return "" 

builtins.input = mock_input

def run_simulation():
    print("\n🚀 Starting Full Simulation with Mock Data...\n")
    client = CW.init_clients()
    
    # Step 1: Initialize Tables
    print("\n--- Step 1: Initializing Mock Tables ---")
    CW.create_basic_info_table(client, CW.APP_TOKEN)
    CW.create_ledger_table(client, CW.APP_TOKEN)
    CW.create_partner_table(client, CW.APP_TOKEN)
    CW.create_invoice_table(client, CW.APP_TOKEN)
    CW.create_asset_table(client, CW.APP_TOKEN)
    
    # Fill Test Data (Partners)
    print("\n--- Step 1.1: Filling Test Data ---")
    CW.fill_test_data(client, CW.APP_TOKEN)

    # Step 2: Import Data (Bank Flow)
    print("\n--- Step 2: Importing Bank Flow (Mock) ---")
    # Queue inputs for import_from_excel
    # NOTE: import_from_excel with path does NOT use input()
    # input_queue.append("y") 
    # input_queue.append("y") 

    CW.import_from_excel(client, CW.APP_TOKEN, "测试数据_银行流水.xlsx")
    
    # Simulate "Archive" action (move file manually as script would do)
    if not os.path.exists("2_已处理归档"):
        os.makedirs("2_已处理归档")
    import shutil
    if os.path.exists("测试数据_银行流水.xlsx"):
        shutil.move("测试数据_银行流水.xlsx", os.path.join("2_已处理归档", "测试数据_银行流水.xlsx"))
        print("✅ Manually archived '测试数据_银行流水.xlsx'")
    
    # Debug: Check records
    tid = CW.get_table_id_by_name(client, CW.APP_TOKEN, "日常台账表")
    if tid:
        recs = CW.get_all_records(client, CW.APP_TOKEN, tid)
        print(f"\n[Debug] Ledger Records Count: {len(recs)}")
    
    # Step 4: One Click Daily Closing
    print("\n--- Step 4: Running One-Click Daily Closing ---")
    # Step 4 sees "测试数据_往来单位别名.xlsx"
    input_queue.append("3") # Skip this file
    
    # one_click_daily_closing calls auto_fix_missing_categories -> auto_categorize
    # This should trigger AI Cache save (if AI key is present, but we mocked it)
    
    CW.one_click_daily_closing(client, CW.APP_TOKEN)
    
    # Step 5: Generate Partner Statement (Optimized)
    print("\n--- Step 5: Generating Partner Statement ---")
    # Inputs:
    # 1. Partner name -> "京东" (Matches "京东办公用品")
    # 2. Filter date? -> "y"
    # 3. Start date -> "2026-01-01"
    # 4. End date -> "2026-12-31"
    input_queue.append("京东") 
    input_queue.append("y") 
    input_queue.append("2026-01-01") 
    input_queue.append("2026-12-31") 
    CW.generate_business_statement(client, CW.APP_TOKEN)
    
    # Step 5.5: Bank Reconciliation (Added)
    print("\n--- Step 5.5: Running Bank Reconciliation ---")
    # Scenario: 
    # - 1 matched record (already in system)
    # - 1 unmatched record (new)
    # Input: Confirm import of unmatched records -> "y"
    input_queue.append("y")
    CW.reconcile_bank_flow(client, CW.APP_TOKEN, "测试数据_待对账流水_G银行.xlsx")

    # Step 6: Year End Closing (Optimized)
    print("\n--- Step 6: Running Year-End Closing ---")
    
    # Ensure Mock AI is still active
    print(f"[Debug] CW.zhipu_client type: {type(CW.zhipu_client)}")
    if not isinstance(CW.zhipu_client, MagicMock):
        print("⚠️ CW.zhipu_client lost mock status! Re-mocking...")
        CW.zhipu_client = MagicMock()
        CW.zhipu_client.chat.completions.create.return_value.choices[0].message.content = "分类：办公费"
        
    # Inputs: 
    # 1. Year -> "2026"
    # 2. Confirm -> "y"
    # 3. Depreciation Confirm -> "y"
    input_queue.append("2026")
    input_queue.append("y")
    input_queue.append("y")
    CW.year_end_closing(client, CW.APP_TOKEN)
    
    print("\n✅ Simulation Completed Successfully!")

if __name__ == "__main__":
    run_simulation()
