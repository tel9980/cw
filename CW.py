# -*- coding: utf-8 -*-
"""
飞书财务小助手V8.8 全场景自动化终极版
✅ 新增：自动对账+税务统计+批量导入导出+异常自愈
✅ 集成：你的Bot + Wiki + 台账
✅ 适配：lark-oapi V2 SDK
"""
import os
import sys
import json
import time
import shutil
import logging
import requests
import pandas as pd
import tkinter as tk
from tkinter import filedialog
import base64
from io import BytesIO
from PIL import Image, ImageGrab
from datetime import datetime, timedelta
from dotenv import load_dotenv

# Lark OAPI V2 Imports
import lark_oapi as lark
from lark_oapi.api.bitable.v1 import *
from lark_oapi.api.bitable.v1.model import *

# ZhipuAI Import
from zhipuai import ZhipuAI

class Color:
    HEADER = '\033[95m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    GREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'

# Compatibility constants for Field Types
class FT:
    TEXT = 1
    NUMBER = 2
    SELECT = 3
    MULTI_SELECT = 4
    DATE = 5
    CHECKBOX = 7
    USER = 11
    PHONE = 13
    URL = 15
    ATTACHMENT = 17
    LINK = 18
    LOOKUP = 19
    FORMULA = 20
    DUPLEX_LINK = 21
    LOCATION = 22
    GROUP_CHAT = 23
    CREATED_TIME = 1001
    MODIFIED_TIME = 1002
    CREATED_USER = 1003
    MODIFIED_USER = 1004

# 加载环境变量
load_dotenv()

# -------------------------------------------------------------------------
# 新增功能：启动引导向导
# -------------------------------------------------------------------------
def setup_wizard():
    """新手引导配置向导"""
    if os.path.exists(".env"):
        # 检查关键变量是否存在
        with open(".env", "r", encoding="utf-8") as f:
            content = f.read()
        if "FEISHU_APP_ID" in content and "FEISHU_APP_SECRET" in content and "FEISHU_APP_TOKEN" in content:
            return # 配置已存在，跳过

    print(f"{Color.HEADER}===============================================")
    print(f"       👋 欢迎使用飞书财务小助手！(初次设置)")
    print(f"==============================================={Color.ENDC}")
    print(f"{Color.CYAN}检测到您是第一次运行或配置文件缺失。{Color.ENDC}")
    print("请按照提示输入飞书开放平台的 App ID 和 Secret。")
    print("如果您还没有这些信息，请先去 open.feishu.cn 创建企业自建应用。")
    print("-" * 50)
    
    app_id = input(f"👉 请输入 {Color.BOLD}App ID{Color.ENDC} (cli_...): ").strip()
    app_secret = input(f"👉 请输入 {Color.BOLD}App Secret{Color.ENDC}: ").strip()
    app_token = input(f"👉 请输入 {Color.BOLD}App Token{Color.ENDC} (多维表格的base_token): ").strip()
    
    if not app_id or not app_secret or not app_token:
        print(f"{Color.FAIL}❌ 输入不完整，无法继续。{Color.ENDC}")
        sys.exit(1)
        
    # 写入 .env
    with open(".env", "w", encoding="utf-8") as f:
        f.write(f"FEISHU_APP_ID={app_id}\n")
        f.write(f"FEISHU_APP_SECRET={app_secret}\n")
        f.write(f"FEISHU_APP_TOKEN={app_token}\n")
        f.write("VAT_RATE=3\n")
        f.write("TOLERANCE_DAYS=2\n")
        
    print(f"\n{Color.GREEN}✅ 配置已保存！正在启动...{Color.ENDC}\n")
    # 重新加载
    load_dotenv()
    global APP_ID, APP_SECRET, APP_TOKEN
    APP_ID = os.getenv("FEISHU_APP_ID")
    APP_SECRET = os.getenv("FEISHU_APP_SECRET")
    APP_TOKEN = os.getenv("FEISHU_APP_TOKEN")

# 辅助：交互式文件选择
def select_file_interactively(pattern="*.xlsx", prompt="请选择文件"):
    """列出当前目录下匹配的文件供用户选择 (优先尝试 GUI)"""
    # 尝试使用 GUI 选择文件
    try:
        import tkinter as tk
        from tkinter import filedialog
        
        print(f"\n📂 正在打开文件选择窗口...")
        root = tk.Tk()
        root.withdraw() # 隐藏主窗口
        root.attributes('-topmost', True) # 置顶
        
        file_path = filedialog.askopenfilename(
            title=prompt,
            filetypes=[("Excel files", "*.xlsx"), ("All files", "*.*")],
            initialdir=os.getcwd()
        )
        root.destroy()
        
        if file_path:
            # 转换为相对路径以保持显示整洁 (如果是在当前目录下)
            try:
                rel_path = os.path.relpath(file_path, os.getcwd())
                if not rel_path.startswith(".."):
                    return rel_path
                return file_path
            except:
                return file_path
        else:
            print("   (用户取消了选择)")
            # 如果用户取消，回退到列表模式？或者直接返回None
            # 让我们回退到列表模式，以防万一GUI不好用
    except Exception as e:
        print(f"⚠️ GUI 启动失败 ({e})，切换回列表模式。")

    import glob
    files = [f for f in glob.glob(pattern) if not f.startswith("~$")]
    
    if not files:
        return None
        
    print(f"\n📂 {prompt} (列表模式):")
    for i, f in enumerate(files):
        print(f"  {i+1}. {f}")
    print(f"  0. 手动输入路径")
    
    while True:
        choice = input(f"👉 请选择 (1-{len(files)}, 0): ").strip()
        if choice == '0':
            return None
        if choice.isdigit():
            idx = int(choice) - 1
            if 0 <= idx < len(files):
                return files[idx]
        print(f"{Color.FAIL}❌ 无效选择{Color.ENDC}")

# 辅助：选择文件
def select_file(title="请选择Excel文件"):
    root = tk.Tk()
    root.withdraw() # 隐藏主窗口
    root.attributes('-topmost', True) # 置顶
    file_path = filedialog.askopenfilename(
        title=title,
        filetypes=[("Excel files", "*.xlsx;*.xls")]
    )
    root.destroy()
    return file_path

# -------------------------- 核心配置 --------------------------
LOG_FILE = f"feishu_table_log_{datetime.now().strftime('%Y%m%d')}.log"
TEST_PRODUCT_COUNT = 10
TEST_LEDGER_COUNT = 5
# TABLE_NAME 在此处意为 Base Name (应用名称)
BASE_NAME = "飞书财务台账-2026"
BOT_WEBHOOK = os.getenv("BOT_WEBHOOK", "")
WIKI_LINK = os.getenv("WIKI_LINK", "")
WIKI_EXCEPTION = f"{WIKI_LINK}# 异常排查" if WIKI_LINK else "请联系管理员"
WIKI_TAX = f"{WIKI_LINK}# 税务申报" if WIKI_LINK else "请联系管理员"
LOCAL_FOLDER = "财务数据备份"
os.makedirs(LOCAL_FOLDER, exist_ok=True)

# 业务配置
VAT_RATE = float(os.getenv("VAT_RATE", 3))
TOLERANCE_DAYS = int(os.getenv("TOLERANCE_DAYS", 2))
# -------------------------------------------------------------------------

# 初始化日志
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s - 解决方案：%(solution)s",
    handlers=[logging.FileHandler(LOG_FILE, encoding="utf-8"), logging.StreamHandler()]
)
logger = logging.getLogger(__name__)

class SolutionLogAdapter(logging.LoggerAdapter):
    def process(self, msg, kwargs):
        kwargs["extra"] = {"solution": self.extra.get("solution", "无")}
        return msg, kwargs
log = SolutionLogAdapter(logger, {"solution": "无"})

# 加载环境变量 (已在上方加载)
APP_ID = os.getenv("FEISHU_APP_ID")
APP_SECRET = os.getenv("FEISHU_APP_SECRET")
APP_TOKEN = os.getenv("FEISHU_APP_TOKEN") # Base Token
USER_ID = os.getenv("FEISHU_USER_ID", "")
BOSS_ID = os.getenv("BOSS_FEISHU_ID", "")
ZHIPUAI_API_KEY = os.getenv("ZHIPUAI_API_KEY", "")

# 初始化 GLM-4 客户端
zhipu_client = None
if ZHIPUAI_API_KEY:
    try:
        zhipu_client = ZhipuAI(api_key=ZHIPUAI_API_KEY)
        # log.info("🧠 GLM-4 AI 模型已加载", extra={"solution": "无"}) # Avoid logging too early if log not setup, but log is setup at line 95
    except Exception as e:
        pass

# 税务配置
TAX_CONFIG = {
    "is_small": os.getenv("IS_SMALL", "true").lower() == "true",
    "vat_rate": float(os.getenv("VAT_RATE", 3)),
    "corporate_tax_rate": float(os.getenv("CORP_TAX_RATE", 25)),
    "surtax_rates": {"city": 7, "education": 3, "local_education": 2}
}
RECONCILE_THRESHOLD = float(os.getenv("RECONCILE_THRESHOLD", 0.01))

def ai_guess_category(description, partner):
    """使用 AI 猜测交易分类"""
    if not zhipu_client: return None
    
    try:
        # 构造提示词
        prompt = f"""
你是一名资深会计。请根据交易描述判断费用类型。
交易对象: {partner}
交易摘要: {description}
可选分类: [差旅费-交通, 差旅费-住宿, 差旅费-加油, 业务招待费, 办公费, 房租物业, 水电费, 快递费, 营销推广费, 技术服务费, 采购款, 员工工资, 社保公积金, 税费]
如果不确定，请根据经验推断最可能的分类。
只返回分类名称，不要其他废话。
"""
        resp = zhipu_client.chat.completions.create(
            model="glm-4-flash",
            messages=[{"role": "user", "content": prompt}]
        )
        category = resp.choices[0].message.content.strip()
        # 简单清洗
        category = category.replace("分类：", "").replace("。", "").strip()
        return category
    except Exception as e:
        # print(f"AI error: {e}")
        return None

# 重试装饰器
def retry_on_failure(max_retries=3, delay=3):
    def decorator(func):
        def wrapper(*args, **kwargs):
            retries = 0
            while retries < max_retries:
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    retries += 1
                    log.error(f"❌ 函数{func.__name__}执行失败（第{retries}次重试）：{str(e)}",
                              extra={"solution": f"等待{delay}秒后重试"})
                    time.sleep(delay)
            log.error(f"❌ 函数{func.__name__}重试{max_retries}次失败",
                      extra={"solution": f"查看Wiki：{WIKI_EXCEPTION}"})
            return False
        return wrapper
    return decorator

# 发送Bot消息 (支持卡片)
def send_bot_message(content, msg_type="text", card_data=None):
    if not BOT_WEBHOOK:
        log.warning("⚠️ 未配置Bot Webhook，跳过消息推送", extra={"solution": "在.env配置BOT_WEBHOOK"})
        return

    headers = {"Content-Type": "application/json"}
    
    if msg_type == "interactive" and card_data:
        payload = {
            "msg_type": "interactive",
            "card": card_data
        }
    else:
        # 默认文本消息
        payload = {
            "msg_type": "text",
            "content": {"text": content}
        }
        
    try:
        resp = requests.post(BOT_WEBHOOK, json=payload, headers=headers)
        if resp.status_code == 200:
            resp_json = resp.json()
            if resp_json.get("code") == 0:
                log.info("✅ Bot推送成功", extra={"solution": "无"})
                return True
            else:
                log.error(f"❌ Bot推送失败：{resp_json.get('msg')}", extra={"solution": "检查Bot配置"})
                return False
        else:
            log.error(f"❌ Bot网络错误：{resp.status_code}", extra={"solution": "检查网络"})
            return False
    except Exception as e:
        log.error(f"❌ Bot推送异常：{str(e)}", extra={"solution": "检查网络"})
        return False

# 初始化客户端
@retry_on_failure(max_retries=3, delay=3)
def init_clients():
    if not APP_ID or not APP_SECRET:
        log.error("❌ 未配置 APP_ID 或 APP_SECRET", extra={"solution": "请在 .env 文件中配置"})
        return None
        
    client = lark.Client.builder() \
        .app_id(APP_ID) \
        .app_secret(APP_SECRET) \
        .build()
    log.info("✅ 飞书客户端初始化成功", extra={"solution": "无"})
    send_bot_message("飞书财务小助手V8.8已启动 (Lark OAPI V2)", "accountant")
    return client

# 辅助：根据表名获取TableID
def get_table_id_by_name(client, app_token, table_name):
    req = ListAppTableRequest.builder() \
        .app_token(app_token) \
        .page_size(50) \
        .build()
    resp = client.bitable.v1.app_table.list(req)
    if not resp.success():
        log.error(f"❌ 获取表格列表失败: {resp.msg}", extra={"solution": "检查App Token"})
        return None
        
    if resp.data and resp.data.items:
        for table in resp.data.items:
            if table.name == table_name:
                return table.table_id
    return None

# 批量导入Excel
@retry_on_failure(max_retries=2, delay=3)
def import_from_excel(client, app_token, excel_path=None):
    try:
        # 如果没有指定路径，尝试交互式选择或弹窗
        if not excel_path:
            # 优先尝试交互式选择
            excel_path = select_file_interactively("*.xlsx", "请选择要导入的数据文件")
            
            # 如果还是没有，回退到弹窗
            if not excel_path:
                log.info("📂 请选择导入数据的Excel文件...", extra={"solution": "弹窗选择"})
                excel_path = select_file("请选择要导入的Excel文件")
                
            if not excel_path:
                log.warning("⚠️ 未选择文件，操作取消", extra={"solution": "无"})
                return False

        excel_file = pd.ExcelFile(excel_path)
        
        # 导入基础信息表
        if "基础信息表" in excel_file.sheet_names:
            table_id = get_table_id_by_name(client, app_token, "基础信息表")
            if table_id:
                df = pd.read_excel(excel_path, sheet_name="基础信息表").fillna("")
                records = []
                for _, row in df.iterrows():
                    fields = {
                        "产品名称": str(row["产品名称"]),
                        "单位成本": float(row["单位成本"]) if row["单位成本"] != "" else 0,
                        "备注": str(row.get("备注", ""))
                    }
                    records.append(AppTableRecord.builder().fields(fields).build())
                
                # 分批写入 (API限制每次100条)
                batch_size = 100
                for i in range(0, len(records), batch_size):
                    batch = records[i:i+batch_size]
                    req = BatchCreateAppTableRecordRequest.builder() \
                        .app_token(app_token) \
                        .table_id(table_id) \
                        .request_body(BatchCreateAppTableRecordRequestBody.builder().records(batch).build()) \
                        .build()
                    resp = client.bitable.v1.app_table_record.batch_create(req)
                    if not resp.success():
                        log.error(f"❌ 基础信息表部分导入失败: {resp.msg}", extra={"solution": "检查数据格式"})
                log.info(f"✅ 基础信息表导入完成: {len(records)}条", extra={"solution": "无"})
            else:
                log.error("❌ 未找到'基础信息表'", extra={"solution": "请先创建表格"})

        # 导入日常台账表 (优化：支持任意Sheet名，智能识别表头)
        table_id = get_table_id_by_name(client, app_token, "日常台账表")
        if table_id:
            # 1. 智能读取Excel数据
            df = read_excel_smart(excel_path).fillna("")
            if df.empty:
                 log.info("⚠️ Excel中没有有效数据", extra={"solution": "请检查文件内容"})
                 return True

            # 2. 智能银行识别 (基于文件名)
            filename = os.path.basename(excel_path).upper()
            default_bank = "N银行（现金）"
            default_is_cash = "是"
            default_has_ticket = "无票"
            
            if "微信" in filename or "WECHAT" in filename:
                default_bank = "微信"
                default_is_cash = "是"
                default_has_ticket = "无票"
            elif "支付宝" in filename or "ALIPAY" in filename:
                default_bank = "支付宝"
                default_is_cash = "是"
                default_has_ticket = "无票"
            elif "工商" in filename or "ICBC" in filename:
                default_bank = "工商银行"
                default_is_cash = "否"
                default_has_ticket = "有票"
            elif "G银行" in filename:
                default_bank = "G银行基本户"
                default_is_cash = "否"
                default_has_ticket = "有票"

            log.info(f"🤖 智能识别默认银行: {default_bank}", extra={"solution": "如需修改请重命名文件"})

            # 3. 获取日期范围用于过滤查询 (优化)
            min_ts = None
            max_ts = None
            valid_dates = []
            for idx, row in df.iterrows():
                try:
                    dt = pd.to_datetime(row["记账日期"])
                    ts = int(dt.timestamp() * 1000)
                    valid_dates.append(ts)
                except:
                    pass
            
            filter_cmd = None
            if valid_dates:
                min_ts = min(valid_dates) - 24*3600*1000 # 放宽1天
                max_ts = max(valid_dates) + 24*3600*1000
                filter_cmd = f'CurrentValue.[记账日期]>={min_ts}&&CurrentValue.[记账日期]<={max_ts}'
                log.info(f"📅 启用日期范围过滤: {pd.to_datetime(min_ts, unit='ms').date()} 至 {pd.to_datetime(max_ts, unit='ms').date()}", extra={"solution": "无"})

            # 4. 获取现有记录 (仅获取必要字段 + 日期过滤)
            log.info("🔍 正在拉取现有数据进行去重检查...", extra={"solution": "无"})
            required_fields = ["记账日期", "实际收付金额", "业务类型", "备注"]
            existing_records = get_all_records(client, app_token, table_id, filter_info=filter_cmd, field_names=required_fields)
            
            existing_hashes = set()
            for r in existing_records:
                f = r.fields
                d = f.get("记账日期", 0)
                a = round(float(f.get("实际收付金额", 0)), 2)
                t = f.get("业务类型", "")
                m = str(f.get("备注", ""))[:10]
                existing_hashes.add(f"{d}_{a}_{t}_{m}")
            
            log.info(f"✅ 已索引 {len(existing_hashes)} 条现有记录", extra={"solution": "无"})

            records = []
            skipped_count = 0
            
            for _, row in df.iterrows():
                # 预处理数据以生成Hash
                try:
                    r_date_str = str(row["记账日期"])
                    if not r_date_str: continue
                    
                    # 处理日期格式
                    if isinstance(row["记账日期"], (int, float)):
                        ts = int(pd.to_datetime(row["记账日期"]).timestamp() * 1000)
                    else:
                        ts = int(pd.to_datetime(row["记账日期"]).timestamp() * 1000)
                        
                    r_amt = round(float(row["实际收付金额"]), 2)
                    r_type = str(row["业务类型"])
                    r_memo = str(row.get("备注", ""))[:10]
                    
                    # 查重
                    row_hash = f"{ts}_{r_amt}_{r_type}_{r_memo}"
                    if row_hash in existing_hashes:
                        skipped_count += 1
                        continue
                        
                except Exception as e:
                    log.warning(f"⚠️ 数据行解析失败跳过: {e}", extra={"solution": "检查日期/金额格式"})
                    continue

                desc = str(row["往来单位费用"])
                
                # 优化：解析别名
                # 1. 先尝试从户名列匹配
                resolved_desc = resolve_partner(desc)
                
                # 2. 如果户名列没匹配到 (结果没变) 或者 户名列无效，尝试从摘要列匹配
                # 注意：只有当摘要里包含明确的别名时才替换
                if resolved_desc == desc:
                    memo = str(row.get("备注", ""))
                    memo_resolved = resolve_partner(memo)
                    if memo_resolved != memo:
                        # 摘要里包含别名，使用匹配到的标准名称
                        resolved_desc = memo_resolved
                
                desc = resolved_desc
                
                # 尝试自动分类补全
                if not desc or desc == "nan" or desc == "未知" or desc == "":
                    memo = str(row.get("备注", ""))
                    desc = auto_categorize(memo, "未知")
                    
                fields = {
                    "记账日期": ts,
                    "凭证号": int(row["凭证号"]) if row["凭证号"] != "" else 0,
                    "业务类型": r_type,
                    "往来单位费用": desc,
                    "账面金额": float(row.get("账面金额", 0)),
                    "实际收付金额": r_amt,
                    "交易银行": str(row.get("交易银行", "")) or default_bank,
                    "是否现金": str(row.get("是否现金", "")) or default_is_cash,
                    "发票流水单号": str(row.get("发票流水单号", "")),
                    "是否有票": str(row.get("是否有票", "")) or default_has_ticket,
                    "待补票标记": str(row.get("待补票标记", "无")),
                    "有票成本": float(row.get("有票成本", 0)),
                    "无票成本": float(row.get("无票成本", 0)),
                    "本次实际利润": float(row.get("本次实际利润", 0)),
                    "手工式分录": str(row.get("手工式分录", "")),
                    "操作人": str(row.get("操作人", USER_ID)),
                    "合同订单号": str(row.get("合同订单号", "")),
                    "备注": str(row.get("备注", ""))
                }
                    
                records.append(AppTableRecord.builder().fields(fields).build())
            
            if skipped_count > 0:
                log.info(f"⏭️ 已自动跳过 {skipped_count} 条重复记录", extra={"solution": "无"})
            
            if not records:
                log.info("✅ 没有新数据需要导入", extra={"solution": "无"})
                return True

            batch_size = 100
            for i in range(0, len(records), batch_size):
                batch = records[i:i+batch_size]
                req = BatchCreateAppTableRecordRequest.builder() \
                    .app_token(app_token) \
                    .table_id(table_id) \
                    .request_body(BatchCreateAppTableRecordRequestBody.builder().records(batch).build()) \
                    .build()
                resp = client.bitable.v1.app_table_record.batch_create(req)
                if not resp.success():
                     log.error(f"❌ 日常台账表部分导入失败: {resp.msg}", extra={"solution": "检查数据"})
            log.info(f"✅ 日常台账表导入完成: {len(records)}条", extra={"solution": "无"})
        else:
             log.error("❌ 未找到'日常台账表'", extra={"solution": "请先创建表格"})
                 
        return True
    except Exception as e:
        log.error(f"❌ Excel导入异常：{str(e)}", extra={"solution": "检查文件"})
        return False

# 辅助：获取所有记录 (支持过滤和字段选择)
def get_all_records(client, app_token, table_id, filter_info=None, field_names=None):
    records = []
    page_token = None
    while True:
        builder = ListAppTableRecordRequest.builder() \
            .app_token(app_token) \
            .table_id(table_id) \
            .page_size(100)
        
        if filter_info:
            builder.filter(filter_info)
            
        if field_names:
            builder.field_names(field_names)
            
        if page_token:
            builder.page_token(page_token)
            
        req = builder.build()
        resp = client.bitable.v1.app_table_record.list(req)
        if not resp.success():
            log.error(f"❌ 获取记录失败: {resp.msg}", extra={"solution": "检查网络或Token"})
            break
        if resp.data.items:
            records.extend(resp.data.items)
        if not resp.data.has_more:
            break
        page_token = resp.data.page_token
    return records

# 自动分类规则 (关键词 -> 往来单位/费用类型)
def load_category_rules():
    default_rules = {
        "电费": "水电费",
        "水费": "水电费",
        "燃气": "水电费",
        "中石化": "差旅费-加油",
        "中石油": "差旅费-加油",
        "滴滴": "差旅费-交通",
        "铁路": "差旅费-交通",
        "航空": "差旅费-交通",
        "餐饮": "业务招待费",
        "酒店": "差旅费-住宿",
        "住宿": "差旅费-住宿",
        "工资": "工资薪金",
        "社保": "社保公积金",
        "公积金": "社保公积金",
        "税": "税费",
        "利息": "财务费用-利息",
        "手续费": "财务费用-手续费",
        "租金": "房租",
        "物业": "物业费",
        "推广": "市场推广费",
        "广告": "市场推广费",
        "阿里云": "技术服务费",
        "腾讯云": "技术服务费",
        "采购": "原材料采购",
        "货款": "原材料采购",
        "微信提现": "现金互转"
    }
    
    if os.path.exists("category_rules.json"):
        try:
            with open("category_rules.json", "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            log.warning(f"⚠️ 规则文件读取失败: {e}，使用默认规则")
            return default_rules
    else:
        # 创建默认文件方便用户修改
        try:
            with open("category_rules.json", "w", encoding="utf-8") as f:
                json.dump(default_rules, f, ensure_ascii=False, indent=4)
        except:
            pass
        return default_rules

AUTO_CATEGORY_RULES = load_category_rules()

def load_partner_aliases():
    """加载往来单位别名映射"""
    default_aliases = {}
    if os.path.exists("partner_aliases.json"):
        try:
            with open("partner_aliases.json", "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            log.warning(f"⚠️ 别名文件读取失败: {e}")
            return default_aliases
    return default_aliases

PARTNER_ALIASES = load_partner_aliases()

def resolve_partner(name):
    """解析往来单位别名 (支持模糊匹配)"""
    if not name: return ""
    name = str(name).strip()
    
    # 1. 优先完全匹配
    if name in PARTNER_ALIASES:
        return PARTNER_ALIASES[name]
        
    # 2. 模糊匹配 (按别名长度倒序，优先匹配更长的别名)
    # 例如：规则 "张三"->A, "张三丰"->B. 输入 "张三丰转账".
    # 应该匹配 "张三丰" 而不是 "张三".
    sorted_aliases = sorted(PARTNER_ALIASES.keys(), key=len, reverse=True)
    
    for alias in sorted_aliases:
        if alias in name:
            # log.info(f"💡 触发别名匹配: '{alias}' in '{name}' -> '{PARTNER_ALIASES[alias]}'")
            return PARTNER_ALIASES[alias]
            
    return name

def clean_description(text):
    """清洗摘要，移除无用前缀"""
    if not text: return ""
    text = str(text).strip()
    # 常见银行摘要垃圾词 (按长度倒序排列，优先匹配长的)
    garbage = [
        "PAYMENT TO", "TRANSFER FROM", "REMITTANCE", 
        "跨行转账", "网银转账", "银企直联", "手机转账", "批量转账",
        "付款给", "收到", "支付", "转账", "汇款", "网转", "电汇", "回单", "记账",
        "用途:", "摘要:", "附言:", "备注:", "说明:",
        "工资:", "报销:", "代发:",
        "用途：", "摘要：", "附言：", "备注：", "说明：",
        "工资：", "报销：", "代发："
    ]
    # 排序：长的在前面，防止误伤
    garbage.sort(key=len, reverse=True)
    
    clean_text = text
    # 循环去除前缀，直到没有匹配项
    while True:
        original = clean_text
        for g in garbage:
            if clean_text.upper().startswith(g):
                clean_text = clean_text[len(g):].strip()
        if clean_text == original:
            break
            
    return clean_text

def read_excel_smart(file_path):
    """
    智能读取 Excel：
    1. 自动寻找表头行 (包含 '日期', '金额' 等关键词)
    2. 自动重命名列为标准字段
    3. 返回标准化的 DataFrame
    """
    try:
        xl = pd.ExcelFile(file_path)
        # 优先读 '日常台账表'，否则读第一个 Sheet
        sheet_name = "日常台账表" if "日常台账表" in xl.sheet_names else xl.sheet_names[0]
        
        # 先读前 20 行来找表头
        df_preview = pd.read_excel(file_path, sheet_name=sheet_name, header=None, nrows=20)
        
        header_row_idx = -1
        column_map = {}
        
        # 关键词映射表 (可能的列名 -> 标准列名)
        keyword_map = {
            "日期": "记账日期", "时间": "记账日期", "交易日": "记账日期",
            "金额": "实际收付金额", "发生额": "实际收付金额", "收支金额": "实际收付金额",
            "摘要": "备注", "说明": "备注", "用途": "备注", "商品": "备注", "附言": "备注",
            "对方": "往来单位费用", "户名": "往来单位费用", "单位": "往来单位费用", "收/支": "业务类型",
            "借贷": "业务类型", "收付": "业务类型"
        }
        
        # 扫描寻找表头
        for idx, row in df_preview.iterrows():
            row_str = " ".join([str(x) for x in row.values])
            if "日期" in row_str and ("金额" in row_str or "发生额" in row_str):
                header_row_idx = idx
                # 构建列映射
                for col_idx, val in enumerate(row.values):
                    val_str = str(val).strip()
                    for k, v in keyword_map.items():
                        if k in val_str:
                            column_map[val_str] = v # 记录原始列名 -> 标准列名
                            break 
                break
                
        if header_row_idx == -1:
            # 没找到明显表头，假设第一行就是
            header_row_idx = 0
            log.warning("⚠️ 未找到明显的表头行，尝试默认第一行读取", extra={"solution": "请检查Excel格式"})
            
        # 重新读取数据
        df = pd.read_excel(file_path, sheet_name=sheet_name, header=header_row_idx)
        
        # 重命名列
        df.rename(columns=column_map, inplace=True)
        
        # 再次检查关键列是否存在，如果不存在尝试根据位置猜测
        # 假设：如果不包含标准列名，尝试猜：第一列是日期，最后一列是金额？(风险较大，暂不激进)
        
        return df
        
    except Exception as e:
        log.error(f"❌ 智能读取Excel失败: {e}", extra={"solution": "文件可能损坏"})
        return pd.DataFrame()

# 智能分类：历史记忆库
HISTORY_CATEGORY_MAP = {}

def load_history_knowledge(client, app_token):
    """从飞书加载最近的历史分类习惯 (智能记忆)"""
    global HISTORY_CATEGORY_MAP
    HISTORY_CATEGORY_MAP = {}
    
    table_id = get_table_id_by_name(client, app_token, "日常台账表")
    if not table_id: return
    
    # 获取最近2000条记录
    log.info("🧠 正在学习历史分类习惯...", extra={"solution": "无"})
    records = get_all_records(client, app_token, table_id, field_names=["备注", "往来单位费用", "费用类型"])
    
    # 倒序遍历，越新的越优先
    for r in reversed(records):
        f = r.fields
        memo = str(f.get("备注") or "").strip()
        partner = str(f.get("往来单位费用") or "").strip()
        cat = str(f.get("费用类型") or "").strip()
        
        if not cat: continue
        
        # 1. 记住 "摘要关键词" -> "分类" (取前10个字作为特征)
        if memo and len(memo) > 1:
            key = memo[:10].lower()
            if key not in HISTORY_CATEGORY_MAP:
                HISTORY_CATEGORY_MAP[key] = cat
                
        # 2. 记住 "往来单位" -> "分类"
        if partner and partner not in ["散户", ""]:
            # 往来单位优先级低一点，加上前缀区分
            p_key = f"PARTNER:{partner}"
            if p_key not in HISTORY_CATEGORY_MAP:
                HISTORY_CATEGORY_MAP[p_key] = cat
                
    log.info(f"✅ 已学习 {len(HISTORY_CATEGORY_MAP)} 条历史分类规则", extra={"solution": "无"})

def auto_categorize(description, default_val, partner_name=None):
    if not description and not partner_name:
        return default_val
    
    # 重新加载规则，支持热修改
    global AUTO_CATEGORY_RULES, HISTORY_CATEGORY_MAP
    
    desc_str = str(description).lower()
    
    # 1. 优先匹配明确的【规则库】 (category_rules.json)
    for key, value in AUTO_CATEGORY_RULES.items():
        if key.lower() in desc_str:
            return value
            
    # 2. 其次匹配【历史记忆】 (History Knowledge)
    # 2.1 匹配摘要前缀
    if desc_str:
        key = desc_str[:10]
        if key in HISTORY_CATEGORY_MAP:
            return HISTORY_CATEGORY_MAP[key]
            
    # 2.2 匹配往来单位
    if partner_name:
        p_key = f"PARTNER:{partner_name}"
        if p_key in HISTORY_CATEGORY_MAP:
            return HISTORY_CATEGORY_MAP[p_key]
            
    # 3. [V9.4新特性] 尝试 AI 智能推断
    # 只有当描述足够长(>2)或有明确往来单位时才调用，避免浪费 Token
    if (len(desc_str) > 2 or partner_name) and ZHIPUAI_API_KEY:
        ai_cat = ai_guess_category(description, partner_name)
        if ai_cat:
            print(f"   🧠 AI 智能推断: '{description}' -> [{ai_cat}]")
            return ai_cat
            
    return default_val

# 导入未匹配流水到飞书
def import_bank_records_to_feishu(client, app_token, records_list):
    """
    将未匹配的银行流水直接导入飞书台账
    """
    if not records_list:
        return
        
    table_id = get_table_id_by_name(client, app_token, "日常台账表")
    if not table_id:
        log.error("❌ 找不到日常台账表，无法导入", extra={"solution": "请先初始化表格"})
        return

    log.info(f"🚀 正在批量导入 {len(records_list)} 条流水...", extra={"solution": "无"})
    
    # 导入未匹配流水到飞书
    # 自动识别逻辑：G银行默认有票，N银行/微信默认现金
    
    feishu_records = []
    for r in records_list:
        # 解析日期字符串 "YYYY-MM-DD" -> timestamp
        try:
            dt = datetime.strptime(r["记账日期"], "%Y-%m-%d")
            ts = int(dt.timestamp() * 1000)
        except:
            ts = int(datetime.now().timestamp() * 1000)

        # 绝对值处理
        amt = abs(float(r["实际收付金额"]))
        
        # 智能判断默认值
        txn_bank = r.get("交易银行", "G银行基本户")
        is_cash = "否"
        has_ticket = "无票"
        
        if "G银行" in txn_bank:
            has_ticket = "有票"
            is_cash = "否"
        elif "N银行" in txn_bank or "微信" in txn_bank or "现金" in txn_bank:
            is_cash = "是"
            has_ticket = "无票" # 现金通常默认无票，除非明确指定

        # 如果原记录已有值，则优先使用
        if r.get("是否有票"): has_ticket = r.get("是否有票")
        if r.get("是否现金"): is_cash = r.get("是否现金")

        fields = {
            "记账日期": ts,
            "凭证号": 0, # 默认为0
            "业务类型": r["业务类型"],
            "往来单位费用": r["往来单位费用"],
            "账面金额": amt, # 默认账面=实际 (按实际发生)
            "实际收付金额": amt,
            "交易银行": txn_bank,
            "是否现金": is_cash,
            "是否有票": has_ticket,
            "待补票标记": "否",
            "备注": r["备注"]
        }
        feishu_records.append(AppTableRecord.builder().fields(fields).build())
    
    # 分批提交 (每次100条)
    batch_size = 100
    success_count = 0
    for i in range(0, len(feishu_records), batch_size):
        batch = feishu_records[i:i+batch_size]
        req = BatchCreateAppTableRecordRequest.builder() \
            .app_token(app_token) \
            .table_id(table_id) \
            .request_body(BatchCreateAppTableRecordRequestBody.builder().records(batch).build()) \
            .build()
        
        resp = client.bitable.v1.app_table_record.batch_create(req)
        if resp.success():
            success_count += len(batch)
            log.info(f"✅ 第 {i//batch_size + 1} 批导入成功 ({len(batch)}条)")
        else:
            log.error(f"❌ 第 {i//batch_size + 1} 批导入失败: {resp.msg}")
            
    if success_count > 0:
        send_bot_message(f"✅ 已自动导入 {success_count} 条银行流水到台账！", "reconcile")
        print(f"✅ 成功导入 {success_count} 条记录。")

def generate_reconciliation_report(matched_count, unmatched_list):
    """生成对账结果可视化报告"""
    total = matched_count + len(unmatched_list)
    if total == 0: return
    
    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <title>银行对账报告 - {datetime.now().strftime('%Y-%m-%d')}</title>
        <script src="https://cdn.jsdelivr.net/npm/echarts@5.4.3/dist/echarts.min.js"></script>
        <style>
            body {{ font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; background-color: #f4f6f9; margin: 0; padding: 20px; }}
            .container {{ max-width: 1000px; margin: 0 auto; background: white; padding: 30px; border-radius: 10px; box-shadow: 0 4px 6px rgba(0,0,0,0.1); }}
            h1 {{ color: #2c3e50; text-align: center; border-bottom: 2px solid #3498db; padding-bottom: 10px; }}
            .summary {{ display: flex; justify-content: space-around; margin: 30px 0; }}
            .card {{ text-align: center; padding: 20px; background: #f8f9fa; border-radius: 8px; width: 30%; }}
            .number {{ font-size: 24px; font-weight: bold; color: #2c3e50; }}
            .chart-box {{ height: 400px; margin: 20px 0; }}
            table {{ width: 100%; border-collapse: collapse; margin-top: 20px; }}
            th, td {{ border: 1px solid #ddd; padding: 12px; text-align: left; }}
            th {{ background-color: #3498db; color: white; }}
            tr:nth-child(even) {{ background-color: #f2f2f2; }}
            .badge {{ padding: 5px 10px; border-radius: 4px; font-size: 12px; }}
            .badge-danger {{ background-color: #e74c3c; color: white; }}
        </style>
    </head>
    <body>
        <div class="container">
            <h1>🏦 银行对账报告</h1>
            <p style="text-align: center; color: #7f8c8d;">生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
            
            <div class="summary">
                <div class="card">
                    <div class="number" style="color: #3498db;">{total}</div>
                    <div>总流水数</div>
                </div>
                <div class="card">
                    <div class="number" style="color: #27ae60;">{matched_count}</div>
                    <div>自动匹配成功</div>
                </div>
                <div class="card">
                    <div class="number" style="color: #e74c3c;">{len(unmatched_list)}</div>
                    <div>待处理异常</div>
                </div>
            </div>

            <div id="pie-chart" class="chart-box"></div>

            <h3>📋 待处理异常清单 ({len(unmatched_list)}条)</h3>
            <table>
                <thead>
                    <tr>
                        <th>日期</th>
                        <th>摘要</th>
                        <th>金额</th>
                        <th>建议分类</th>
                        <th>原因</th>
                    </tr>
                </thead>
                <tbody>
    """
    
    for item in unmatched_list:
        html += f"""
                    <tr>
                        <td>{item.get('记账日期')}</td>
                        <td>{item.get('备注')}</td>
                        <td>{item.get('实际收付金额')}</td>
                        <td>{item.get('往来单位费用')}</td>
                        <td><span class="badge badge-danger">{item.get('原因')}</span></td>
                    </tr>
        """
        
    html += f"""
                </tbody>
            </table>
            
            <script>
                var chartDom = document.getElementById('pie-chart');
                var myChart = echarts.init(chartDom);
                var option = {{
                    title: {{ text: '对账匹配率', left: 'center' }},
                    tooltip: {{ trigger: 'item' }},
                    legend: {{ orient: 'vertical', left: 'left' }},
                    series: [
                        {{
                            name: '匹配结果',
                            type: 'pie',
                            radius: ['40%', '70%'],
                            avoidLabelOverlap: false,
                            itemStyle: {{
                                borderRadius: 10,
                                borderColor: '#fff',
                                borderWidth: 2
                            }},
                            label: {{
                                show: false,
                                position: 'center'
                            }},
                            emphasis: {{
                                label: {{
                                    show: true,
                                    fontSize: 20,
                                    fontWeight: 'bold'
                                }}
                            }},
                            labelLine: {{ show: false }},
                            data: [
                                {{ value: {matched_count}, name: '匹配成功', itemStyle: {{ color: '#27ae60' }} }},
                                {{ value: {len(unmatched_list)}, name: '未匹配异常', itemStyle: {{ color: '#e74c3c' }} }}
                            ]
                        }}
                    ]
                }};
                option && myChart.setOption(option);
            </script>
        </div>
    </body>
    </html>
    """
    
    report_dir = "财务数据备份"
    if not os.path.exists(report_dir):
        os.makedirs(report_dir)
        
    filename = f"{report_dir}/对账报告_{datetime.now().strftime('%Y%m%d%H%M%S')}.html"
    with open(filename, "w", encoding="utf-8") as f:
        f.write(html)
        
    log.info(f"📊 对账可视化报告已生成: {filename}", extra={"solution": "浏览器打开查看"})
    try:
        os.startfile(filename)
    except:
        pass

# 银行流水对账 (智能模糊匹配 + 性能优化)
@retry_on_failure(max_retries=2, delay=3)
def reconcile_bank_flow(client, app_token, bank_excel_path):
    log.info("📊 开始智能对账...", extra={"solution": "无"})
    
    # 1. 先读取银行流水 (为了获取日期范围，减少飞书数据拉取量)
    try:
        if not bank_excel_path:
            # 优先尝试交互式选择
            bank_excel_path = select_file_interactively("*.xlsx", "请选择银行流水Excel文件")
            
            # 如果还是没有，回退到弹窗
            if not bank_excel_path:
                log.info("📂 请选择银行流水Excel文件...", extra={"solution": "弹窗选择"})
                bank_excel_path = select_file("请选择银行流水Excel文件")

            if not bank_excel_path:
                log.warning("⚠️ 未选择文件，操作取消", extra={"solution": "无"})
                return False

        # 智能识别银行类型 (基于文件名)
        bank_choice = "1" # Default G Bank
        base_name = os.path.basename(bank_excel_path).upper()
        
        if any(k in base_name for k in ["微信", "N银行", "现金", "WECHAT", "ALIPAY", "支付宝"]):
            log.info(f"🤖 检测到文件名包含关键信息，自动识别为【N银行/微信（现金）】模式", extra={"solution": "无需操作"})
            bank_choice = "2"
        elif any(k in base_name for k in ["G银行", "工商", "ICBC", "对公"]):
             log.info(f"🤖 检测到文件名包含关键信息，自动识别为【G银行（对公）】模式", extra={"solution": "无需操作"})
             bank_choice = "1"
        else:
            # 交互式选择银行类型
            print("\n🏦 请选择当前对账的银行类型：")
            print("1. G银行 (对公账户 - 默认有票)")
            print("2. N银行/微信 (现金/私户 - 默认现金)")
            user_input = input(f"请输入数字 (1/2) [默认{bank_choice}]: ").strip()
            if user_input:
                bank_choice = user_input
        
        bank_name = "G银行基本户"
        default_ticket = "有票"
        is_cash = "否"
        
        if bank_choice == "2":
            bank_name = "N银行/微信（现金）"
            default_ticket = "无票"
            is_cash = "是"
        log.info(f"✅ 当前设定: {bank_name}", extra={"solution": "无"})

        # 使用智能读取
        df = read_excel_smart(bank_excel_path)
        if df.empty:
            return False

        # 标准列名
        date_col = "记账日期"
        amount_col = "实际收付金额"
        
        if date_col not in df.columns or amount_col not in df.columns:
            log.error(f"❌ 银行流水Excel缺少必要的列 (需包含 日期/金额 关键词)", extra={"solution": "修改表头或使用智能模式"})
            log.info(f"当前识别到的列: {df.columns.tolist()}", extra={"solution": "无"})
            return False

        # 获取日期范围用于过滤
        try:
            dates = pd.to_datetime(df[date_col])
            min_date = dates.min()
            max_date = dates.max()
            # 扩大范围前后各7天，防止容差漏掉
            filter_start_ts = int((min_date - timedelta(days=7)).timestamp() * 1000)
            filter_end_ts = int((max_date + timedelta(days=7)).timestamp() * 1000)
            log.info(f"📅 提取流水日期范围: {min_date.date()} 至 {max_date.date()}", extra={"solution": "无"})
        except Exception as e:
            log.warning(f"⚠️ 日期解析失败，将拉取全量数据: {e}", extra={"solution": "检查日期格式"})
            filter_start_ts = None
            filter_end_ts = None

    except Exception as e:
        log.error(f"❌ 读取Excel失败: {str(e)}", extra={"solution": "检查文件是否被占用"})
        return False

    # 2. 读取飞书台账 (带过滤器)
    table_id = get_table_id_by_name(client, app_token, "日常台账表")
    if not table_id:
        log.error("❌ 未找到'日常台账表'", extra={"solution": "先创建表格"})
        return False
        
    filter_info = None
    if filter_start_ts and filter_end_ts:
        # 构造组合过滤器
        filter_info = f'AND(CurrentValue.[记账日期]>={filter_start_ts}, CurrentValue.[记账日期]<={filter_end_ts})'
        log.info("🚀 启用云端数据过滤，仅拉取相关日期记录", extra={"solution": "性能优化"})

    feishu_records = get_all_records(client, app_token, table_id, filter_info=filter_info)
    log.info(f"📥 拉取到 {len(feishu_records)} 条相关记录", extra={"solution": "无"})
    
    # 构建飞书数据索引: Amount -> List of Records
    feishu_amount_map = {}
    for record in feishu_records:
        fields = record['fields']
        try:
            # 修正：字段名应为 '实际收付金额'
            f_amount = float(fields.get('实际收付金额', 0))
            f_date = pd.to_datetime(fields.get('记账日期', 0), unit='ms')
            
            key = round(f_amount, 2)
            if key not in feishu_amount_map:
                feishu_amount_map[key] = []
            
            feishu_amount_map[key].append({
                "record_id": record['record_id'],
                "date": f_date,
                "fields": fields,
                "matched": False
            })
        except:
            continue

            
    unmatched = []
    matched_count = 0
    
    # 容差设置
    # TOLERANCE_DAYS = 2 # Moved to global config
    
    # 加载历史分类知识
    load_history_knowledge(client, app_token)

    for idx, row in df.iterrows():
        try:
            b_date = pd.to_datetime(row[date_col])
            b_amount = float(row[amount_col])
            b_amount_key = round(b_amount, 2)
        except:
            continue 
        
        # 查找匹配
        candidates = feishu_amount_map.get(b_amount_key, [])
        match_found = False
        
        for cand in candidates:
            if cand["matched"]:
                continue # 已经被其他流水匹配过了
            
            # 检查日期差
            delta = abs((cand["date"] - b_date).days)
            if delta <= TOLERANCE_DAYS:
                cand["matched"] = True
                match_found = True
                matched_count += 1
                break
        
        if not match_found:
            # 构造符合导入格式的数据
            raw_desc = str(row.get("对方户名", str(row.get("对方账号", row.get("摘要", "未知")))))
            memo = str(row.get('摘要', ''))
            
            # 优化：清洗摘要
            cleaned_memo = clean_description(memo)
            cleaned_desc = clean_description(raw_desc)
            
            # 优化：解析别名 (张三 -> A客户)
            cleaned_desc = resolve_partner(cleaned_desc)

            # 尝试自动分类 (使用历史记忆)
            # 逻辑：
            # 1. 如果有明确规则匹配 cleaned_memo -> 用规则
            # 2. 如果 cleaned_memo 在历史中出现过 -> 用历史
            # 3. 如果 cleaned_desc 在历史中出现过 -> 用历史
            category = auto_categorize(cleaned_memo, cleaned_desc, partner_name=cleaned_desc) 
            
            # 如果自动分类还是等于 对方户名 (说明没匹配到)，尝试单独匹配 cleaned_desc
            if category == cleaned_desc:
                 category = auto_categorize(cleaned_desc, cleaned_desc, partner_name=cleaned_desc)
            
            unmatched.append({
                "记账日期": b_date.strftime("%Y-%m-%d"),
                "凭证号": "",
                "业务类型": "付款" if b_amount < 0 else "收款",
                "往来单位费用": category,
                "实际收付金额": b_amount,
                "交易银行": bank_name,
                "是否现金": is_cash,
                "是否有票": default_ticket,
                "待补票标记": "否",
                "备注": f"流水导入: {memo}",
                "原因": "飞书无此金额或日期超2天"
            })
            
    # 3. 输出结果
    msg = f"智能对账完成！\n✅ 自动匹配：{matched_count}笔\n❌ 异常/漏记：{len(unmatched)}笔"
    log.info(msg, extra={"solution": "查看未匹配详情"})
    
    # 生成可视化报告
    generate_reconciliation_report(matched_count, unmatched)

    if unmatched:
        res_df = pd.DataFrame(unmatched)
        # 确保列顺序符合导入要求
        cols = ["记账日期", "凭证号", "业务类型", "往来单位费用", "实际收付金额", 
                "交易银行", "是否现金", "是否有票", "待补票标记", "备注", "原因"]
        # 动态调整列，防止KeyError
        final_cols = [c for c in cols if c in res_df.columns]
        res_df = res_df[final_cols]
        
        res_path = f"待补录流水_{datetime.now().strftime('%Y%m%d%H%M%S')}.xlsx"
        res_df.to_excel(res_path, index=False, sheet_name="日常台账表") # Sheet名设为日常台账表方便直接导入
        log.info(f"📄 待补录清单已导出: {res_path}", extra={"solution": "直接使用'从Excel导入'功能导入此文件"})
        send_bot_message(f"{msg}\n📄 待补录清单: {res_path}\n💡 该文件已按导入格式整理，可直接导入系统。", "reconcile")

        # 新增：询问是否直接导入 (按实际发生)
        print(f"\n💡 发现 {len(unmatched)} 笔未匹配流水 (可能是新发生的收支)。")
        print("💡 小提示: 小企业通常付款/回款不一一对应，建议按'实际发生'直接导入。")
        import_choice = input("👉 是否直接将这些流水作为新账目导入飞书? (y/n) [推荐y]: ").strip().lower()
        if import_choice != 'n': 
            import_bank_records_to_feishu(client, app_token, unmatched)
            
    else:
        send_bot_message(f"{msg}\n🎉 账目完美平衡！", "reconcile")
        
    return True

# AI 财务诊断 (GLM-4-Flash)
def get_ai_insight(data_context):
    if not ZHIPUAI_API_KEY:
        log.info("🤖 AI 未配置，跳过智能分析", extra={"solution": "在.env配置 ZHIPUAI_API_KEY"})
        return ""
        
    log.info("🧠 正在进行AI财务诊断 (GLM-4-Flash)...", extra={"solution": "无"})
    try:
        client = ZhipuAI(api_key=ZHIPUAI_API_KEY)
        
        prompt = f"""
        你是一位经验丰富的CFO（首席财务官）。请根据以下小企业本月财务数据，给出一段简练、专业的经营评价，并提出1条具体的改进建议。
        
        【财务数据】
        - 有票收入：{data_context['income']}
        - 总支出：{data_context['cost']} (其中无票支出：{data_context['no_ticket_cost']})
        - 账面利润：{data_context['profit']} (利润率：{data_context['margin']}%)
        - 预计税负：{data_context['tax']}
        - 风险提示：{data_context['risk_msg']}
        
        【要求】
        1. 语气专业、客观，但也通俗易懂（给老板看）。
        2. 重点关注利润率、合规风险（无票占比）。
        3. 100字以内。
        4. 不要用Markdown格式，直接输出纯文本。
        """
        
        response = client.chat.completions.create(
            model="glm-4-flash",
            messages=[
                {"role": "user", "content": prompt}
            ],
            stream=False
        )
        insight = response.choices[0].message.content.strip()
        log.info("✅ AI诊断完成", extra={"solution": "无"})
        return f"\n🤖 [AI 财务诊断]\n{insight}"
        
    except Exception as e:
        log.error(f"❌ AI分析失败: {str(e)}", extra={"solution": "检查API Key或网络"})
        return ""

# 税务统计 (含风险预警)
@retry_on_failure(max_retries=2, delay=3)
def calculate_tax(client, app_token):
    log.info("🧮 开始税务及风险分析...", extra={"solution": "无"})
    table_id = get_table_id_by_name(client, app_token, "日常台账表")
    if not table_id:
        return False
        
    # 优化：只获取本年度数据，减少数据量
    current_year = datetime.now().year
    start_ts = int(datetime(current_year, 1, 1).timestamp() * 1000)
    filter_str = f'CurrentValue.[记账日期]>={start_ts}'
    
    log.info(f"🔍 正在拉取 {current_year} 年度数据...", extra={"solution": "无"})
    records = get_all_records(client, app_token, table_id, filter_info=filter_str)
    
    total_income_ticket = 0.0 # 有票收入
    total_cost_ticket = 0.0   # 有票成本
    total_cost_no_ticket = 0.0 # 无票成本 (总)
    
    # 细分风险统计
    g_bank_no_ticket = 0.0   # G银行(对公)无票支出 -> 高风险
    n_bank_flow = 0.0        # N银行(私户)流水总额 -> 私户避税风险
    
    for r in records:
        fields = r.fields
        has_ticket = fields.get("是否有票") == "有票"
        bank = str(fields.get("交易银行", ""))
        is_g_bank = "G银行" in bank or "对公" in bank
        is_n_bank = "N银行" in bank or "现金" in bank or "私户" in bank
        
        biz_type = fields.get("业务类型")
        amount = float(fields.get("实际收付金额", 0))
        
        if biz_type == "收款":
            if has_ticket:
                total_income_ticket += amount
            if is_n_bank:
                n_bank_flow += amount
        elif biz_type == "付款" or biz_type == "费用":
            if has_ticket:
                total_cost_ticket += amount
            else:
                total_cost_no_ticket += amount
                if is_g_bank:
                    g_bank_no_ticket += amount
            
            if is_n_bank:
                n_bank_flow += abs(amount)
                
    # 计算
    vat_rate = VAT_RATE / 100.0
    estimated_vat = (total_income_ticket / (1 + vat_rate)) * vat_rate
    
    profit = total_income_ticket - total_cost_ticket
    corp_tax = max(0, profit * (TAX_CONFIG["corporate_tax_rate"] / 100.0))
    
    # 风险分析
    total_cost = total_cost_ticket + total_cost_no_ticket
    no_ticket_ratio = (total_cost_no_ticket / total_cost * 100) if total_cost > 0 else 0
    profit_margin = (profit / total_income_ticket * 100) if total_income_ticket > 0 else 0
    
    risk_msg = ""
    if g_bank_no_ticket > 0:
        risk_msg += f"\n⚠️ [严重风险] G银行(对公)存在无票支出: {g_bank_no_ticket:,.2f} (必须补票)"
    if no_ticket_ratio > 30:
        risk_msg += f"\n⚠️ [经营风险] 无票支出整体占比 {no_ticket_ratio:.1f}%"
    if n_bank_flow > 500000: # 假设阈值
        risk_msg += f"\n⚠️ [私户风险] N银行(私户)流水过大: {n_bank_flow:,.2f}"
        
    if profit_margin < 5 and total_income_ticket > 0:
        risk_msg += f"\n⚠️ [异常] 账面利润率仅 {profit_margin:.1f}% (易被稽查)"
    
    # AI 分析
    ai_context = {
        "income": f"{total_income_ticket:,.2f}",
        "cost": f"{total_cost:,.2f}",
        "no_ticket_cost": f"{total_cost_no_ticket:,.2f}",
        "profit": f"{profit:,.2f}",
        "margin": f"{profit_margin:.1f}",
        "tax": f"{estimated_vat + corp_tax:,.2f}",
        "risk_msg": risk_msg.replace("\n", "; ")
    }
    ai_insight = get_ai_insight(ai_context)
    
    msg = (
        f"📊 财务经营月报 (费率: {VAT_RATE}%)\n"
        f"------------------------\n"
        f"💰 有票收入: {total_income_ticket:,.2f}\n"
        f"💸 有票成本: {total_cost_ticket:,.2f}\n"
        f"🚫 无票支出: {total_cost_no_ticket:,.2f} (含G银行: {g_bank_no_ticket:,.2f})\n"
        f"------------------------\n"
        f"🧾 预计增值税: {estimated_vat:,.2f}\n"
        f"🏦 预计所得税: {corp_tax:,.2f}\n"
        f"📈 账面利润率: {profit_margin:.1f}%\n"
        f"------------------------{risk_msg}\n"
        f"{ai_insight}\n"
        f"------------------------\n"
        f"💡 仅供参考，具体以申报为准"
    )
    log.info("✅ 税务统计完成", extra={"solution": "无"})
    print(msg) # 保持原有打印
    return msg
    
    # 构造卡片
    header_color = "green" if profit_margin >= 5 else "red"
    
    elements = [
        {
            "tag": "div",
            "fields": [
                {"is_short": True, "text": {"tag": "lark_md", "content": f"**有票收入**\n¥ {total_income_ticket:,.2f}"}},
                {"is_short": True, "text": {"tag": "lark_md", "content": f"**有票成本**\n¥ {total_cost_ticket:,.2f}"}},
                {"is_short": True, "text": {"tag": "lark_md", "content": f"**预计增值税**\n¥ {estimated_vat:,.2f}"}},
                {"is_short": True, "text": {"tag": "lark_md", "content": f"**预计所得税**\n¥ {corp_tax:,.2f}"}}
            ]
        },
        {"tag": "hr"},
        {
            "tag": "div",
            "text": {
                "tag": "lark_md", 
                "content": f"📈 **利润率**: {profit_margin:.1f}% | 🚫 **无票占比**: {no_ticket_ratio:.1f}%\n{risk_msg}"
            }
        }
    ]
    
    if ai_insight:
        elements.append({
            "tag": "div",
            "text": {"tag": "lark_md", "content": f"**🤖 AI CFO 观点**:\n{ai_insight.replace('🤖 [AI 财务诊断]', '').strip()}"}
        })
        
    elements.append({
        "tag": "action",
        "actions": [
            {
                "tag": "button",
                "text": {"tag": "plain_text", "content": "查看税务指南"},
                "url": WIKI_TAX,
                "type": "default"
            }
        ]
    })
    
    card = {
        "header": {
            "title": {"tag": "plain_text", "content": "📊 财务月度经营分析"},
            "template": header_color
        },
        "elements": elements
    }
    
    send_bot_message("税务分析报告", "interactive", card)
    return True

# 导出待补票清单 (新功能)
@retry_on_failure(max_retries=2, delay=3)
def export_missing_tickets(client, app_token, silent=False):
    log.info("🔍 正在查找待补票记录...", extra={"solution": "无"})
    table_id = get_table_id_by_name(client, app_token, "日常台账表")
    if not table_id:
        return 0
        
    records = get_all_records(client, app_token, table_id)
    missing_list = []
    
    for r in records:
        fields = r.fields
        # 条件: (无票 OR 待补票标记=是) AND (业务类型=付款/费用)
        is_expense = fields.get("业务类型") in ["付款", "费用"]
        no_ticket = fields.get("是否有票") == "无票"
        pending = "是" in str(fields.get("待补票标记", ""))
        
        if is_expense and (no_ticket or pending):
            row = fields.copy()
            # 注入 record_id 以便后续更新
            row['record_id'] = r.record_id
            
            # 日期格式化
            if isinstance(row.get("记账日期"), int):
                row["记账日期"] = datetime.fromtimestamp(row["记账日期"] / 1000).strftime("%Y-%m-%d")
            missing_list.append(row)
            
    if missing_list:
        df = pd.DataFrame(missing_list)
        # 整理列顺序
        cols = ["记账日期", "凭证号", "往来单位费用", "实际收付金额", "是否有票", "待补票标记", "备注", "操作人"]
        # 只保留存在的列
        final_cols = [c for c in cols if c in df.columns]
        df = df[final_cols]
        
        filename = f"待补票清单_{datetime.now().strftime('%Y%m%d')}.xlsx"
        file_path = os.path.join(LOCAL_FOLDER, filename)
        df.to_excel(file_path, index=False)
        
        msg = f"已生成待补票清单: {len(missing_list)}条"
        log.info(f"✅ {msg}", extra={"solution": "发送给业务员补票"})
        if not silent:
            send_bot_message(f"📢 {msg}\n📄 文件位置: {file_path}", "alert")
        
        # 询问是否进入交互式补录模式 (仅在非静默模式下)
        if not silent:
            print(f"\n💡 发现 {len(missing_list)} 笔待补票记录。")
            if input("👉 是否现在开始【交互式补录】(逐条确认收到发票)? (y/n): ").strip().lower() == 'y':
                resolve_missing_tickets(client, app_token, missing_list, table_id)
            
    else:
        log.info("✅ 没有发现待补票记录", extra={"solution": "无"})
        if not silent:
            send_bot_message("👏 只有完美的账单！目前没有待补票记录。", "alert")
            
    return len(missing_list)

def resolve_missing_tickets(client, app_token, missing_list, table_id):
    """交互式补录发票状态"""
    print(f"\n🎫 启动交互式补票模式 ({len(missing_list)}条待处理)...")
    print("-----------------------------------")
    print("说明: 按 'y' 标记为【有票】，按 'n' 或回车跳过，按 'q' 退出。")
    print("-----------------------------------")
    
    count = 0
    for row in missing_list:
        # 显示记录详情
        date_str = row.get("记账日期", "未知日期")
        partner = row.get("往来单位费用", "未知")
        amount = row.get("实际收付金额", 0)
        memo = row.get("备注", "")
        
        print(f"\n📝 [{count+1}/{len(missing_list)}] {date_str} | {partner} | {amount}元 | {memo}")
        choice = input("👉 是否已收到发票? (y/n/q): ").strip().lower()
        
        if choice == 'q':
            break
            
        if choice == 'y':
            # 更新记录
            record_id = row.get("record_id") # 需要确保 get_all_records 返回了 record_id
            if not record_id:
                # 尝试通过原始对象获取 (如果 row 是 dict，可能没有 record_id，除非 get_all_records 特殊处理)
                # 这里假设 get_all_records 返回的 record 对象包含 record_id，但我们之前转换为了 dict
                # 这是一个潜在 bug，我们需要检查 get_all_records 的实现或 missing_list 的构造
                # 修正: 在 export_missing_tickets 中构造 missing_list 时，应该包含 record_id
                print("❌ 无法获取记录ID，跳过")
                continue
                
            try:
                # 更新字段: 是否有票=有票, 待补票标记=""
                fields = {"是否有票": "有票", "待补票标记": ""}
                
                req = UpdateAppTableRecordRequest.builder() \
                    .app_token(app_token) \
                    .table_id(table_id) \
                    .record_id(record_id) \
                    .app_table_record(AppTableRecord.builder().fields(fields).build()) \
                    .build()
                    
                resp = client.bitable.v1.app_table_record.update(req)
                if resp.success():
                    print("✅ 已更新为 [有票]")
                    count += 1
                else:
                    print(f"❌ 更新失败: {resp.msg}")
            except Exception as e:
                print(f"❌ 错误: {e}")
                
    print(f"\n🎉 补录完成！共更新 {count} 条记录。")


# 生成HTML可视化报表
@retry_on_failure(max_retries=2, delay=3)
def generate_html_report(client, app_token):
    log.info("📊 正在生成可视化报表...", extra={"solution": "无"})
    table_id = get_table_id_by_name(client, app_token, "日常台账表")
    if not table_id:
        return False
        
    # 获取本年度数据
    current_year = datetime.now().year
    start_ts = int(datetime(current_year, 1, 1).timestamp() * 1000)
    filter_str = f'CurrentValue.[记账日期]>={start_ts}'
    records = get_all_records(client, app_token, table_id, filter_info=filter_str)
    
    # 数据处理
    monthly_data = {} # month -> {income, expense, profit}
    
    for r in records:
        fields = r.fields
        r_date = fields.get("记账日期")
        if not r_date: continue
        
        if isinstance(r_date, int):
            date_obj = datetime.fromtimestamp(r_date / 1000)
        else:
            try:
                date_obj = datetime.strptime(str(r_date).split(" ")[0], "%Y-%m-%d")
            except: continue
            
        month_key = date_obj.strftime("%Y-%m")
        if month_key not in monthly_data:
            monthly_data[month_key] = {"income": 0, "expense": 0}
            
        amount = float(fields.get("实际收付金额", 0))
        biz_type = fields.get("业务类型")
        
        if biz_type == "收款":
            monthly_data[month_key]["income"] += amount
        elif biz_type == "付款" or biz_type == "费用":
            monthly_data[month_key]["expense"] += amount
            
    # 生成HTML
    months = sorted(monthly_data.keys())
    incomes = [round(monthly_data[m]["income"], 2) for m in months]
    expenses = [round(monthly_data[m]["expense"], 2) for m in months]
    profits = [round(monthly_data[m]["income"] - monthly_data[m]["expense"], 2) for m in months]
    
    # 风险/合规数据
    total_cost = sum(expenses)
    total_cost_ticket = 0
    total_cost_no_ticket = 0
    
    for r in records:
        fields = r.fields
        biz_type = fields.get("业务类型")
        if biz_type in ["付款", "费用"]:
            amount = float(fields.get("实际收付金额", 0))
            if fields.get("是否有票") == "有票":
                total_cost_ticket += amount
            else:
                total_cost_no_ticket += amount
                
    compliance_data = [
        {"value": round(total_cost_ticket, 2), "name": "有票成本 (合规)"},
        {"value": round(total_cost_no_ticket, 2), "name": "无票成本 (风险)"}
    ]
    
    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="utf-8">
        <title>财务经营分析仪表盘</title>
        <script src="https://cdn.jsdelivr.net/npm/echarts@5.4.3/dist/echarts.min.js"></script>
        <style>
            body {{ font-family: 'Segoe UI', sans-serif; background: #f5f6fa; padding: 20px; }}
            .container {{ max-width: 1200px; margin: 0 auto; }}
            .card {{ background: white; border-radius: 8px; padding: 20px; margin-bottom: 20px; box-shadow: 0 2px 5px rgba(0,0,0,0.05); }}
            h1 {{ color: #2c3e50; text-align: center; }}
            .summary {{ display: flex; justify-content: space-around; margin-bottom: 20px; }}
            .stat-box {{ text-align: center; padding: 15px; background: #fff; border-radius: 8px; flex: 1; margin: 0 10px; box-shadow: 0 2px 5px rgba(0,0,0,0.05); }}
            .stat-value {{ font-size: 24px; font-weight: bold; color: #3498db; }}
            .stat-label {{ color: #7f8c8d; font-size: 14px; }}
            #main-chart {{ width: 100%; height: 500px; }}
            #pie-chart {{ width: 100%; height: 400px; }}
            .row {{ display: flex; gap: 20px; }}
            .col-8 {{ flex: 2; }}
            .col-4 {{ flex: 1; }}
        </style>
    </head>
    <body>
        <div class="container">
            <h1>📊 {current_year}年度财务经营分析</h1>
            
            <div class="summary">
                <div class="stat-box">
                    <div class="stat-value">¥ {sum(incomes):,.2f}</div>
                    <div class="stat-label">年度总收入</div>
                </div>
                <div class="stat-box">
                    <div class="stat-value" style="color: #e74c3c">¥ {sum(expenses):,.2f}</div>
                    <div class="stat-label">年度总支出</div>
                </div>
                <div class="stat-box">
                    <div class="stat-value" style="color: #27ae60">¥ {sum(profits):,.2f}</div>
                    <div class="stat-label">年度净利润</div>
                </div>
            </div>
            
            <div class="row">
                <div class="card col-8">
                    <div id="main-chart"></div>
                </div>
                <div class="card col-4">
                    <div id="pie-chart"></div>
                </div>
            </div>
            
            <script>
                var chartDom = document.getElementById('main-chart');
                var myChart = echarts.init(chartDom);
                var option;

                option = {{
                    title: {{ text: '月度收支趋势图' }},
                    tooltip: {{ trigger: 'axis' }},
                    legend: {{ data: ['收入', '支出', '利润'] }},
                    grid: {{ left: '3%', right: '4%', bottom: '3%', containLabel: true }},
                    xAxis: {{ type: 'category', boundaryGap: false, data: {months} }},
                    yAxis: {{ type: 'value' }},
                    series: [
                        {{ name: '收入', type: 'line', stack: 'Total', areaStyle: {{}}, data: {incomes}, itemStyle: {{ color: '#3498db' }} }},
                        {{ name: '支出', type: 'line', stack: 'Total', areaStyle: {{}}, data: {expenses}, itemStyle: {{ color: '#e74c3c' }} }},
                        {{ name: '利润', type: 'bar', data: {profits}, itemStyle: {{ color: '#27ae60' }} }}
                    ]
                }};
                option && myChart.setOption(option);
                
                // 饼图
                var pieDom = document.getElementById('pie-chart');
                var pieChart = echarts.init(pieDom);
                var pieOption = {{
                    title: {{ text: '成本合规性分析', subtext: '有票 vs 无票', left: 'center' }},
                    tooltip: {{ trigger: 'item' }},
                    legend: {{ orient: 'vertical', left: 'left' }},
                    series: [
                        {{
                            name: '成本构成',
                            type: 'pie',
                            radius: '50%',
                            data: {compliance_data},
                            emphasis: {{
                                itemStyle: {{
                                    shadowBlur: 10,
                                    shadowOffsetX: 0,
                                    shadowColor: 'rgba(0, 0, 0, 0.5)'
                                }}
                            }},
                            itemStyle: {{
                                color: function(params) {{
                                    var colorList = ['#27ae60', '#e74c3c'];
                                    return colorList[params.dataIndex];
                                }}
                            }}
                        }}
                    ]
                }};
                pieOption && pieChart.setOption(pieOption);
            </script>
        </div>
    </body>
    </html>
    """
    
    filename = f"财务分析报表_{datetime.now().strftime('%Y%m%d')}.html"
    filepath = os.path.join(LOCAL_FOLDER, filename)
    with open(filepath, "w", encoding="utf-8") as f:
        f.write(html_content)
        
    log.info(f"✅ 报表已生成: {filepath}", extra={"solution": "双击打开HTML文件"})
    # 尝试自动打开
    try:
        os.startfile(filepath)
    except:
        pass
        
    return True

# 导出备份
@retry_on_failure(max_retries=2, delay=3)
def export_to_excel(client, app_token):
    log.info("💾 开始全量备份...", extra={"solution": "无"})
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_path = os.path.join(LOCAL_FOLDER, f"飞书台账备份_{timestamp}.xlsx")
    
    try:
        with pd.ExcelWriter(backup_path) as writer:
            # 备份基础信息
            table_id = get_table_id_by_name(client, app_token, "基础信息表")
            if table_id:
                records = get_all_records(client, app_token, table_id)
                data = [r.fields for r in records]
                pd.DataFrame(data).to_excel(writer, sheet_name="基础信息表", index=False)
                
            # 备份日常台账
            table_id = get_table_id_by_name(client, app_token, "日常台账表")
            if table_id:
                records = get_all_records(client, app_token, table_id)
                # 处理字段中的特殊类型 (如日期timestamp转字符串)
                clean_data = []
                for r in records:
                    row = r.fields.copy()
                    if isinstance(row.get("记账日期"), int):
                        row["记账日期"] = datetime.fromtimestamp(row["记账日期"] / 1000).strftime("%Y-%m-%d")
                    clean_data.append(row)
                    
                pd.DataFrame(clean_data).to_excel(writer, sheet_name="日常台账表", index=False)
                
        log.info(f"✅ 备份成功: {backup_path}", extra={"solution": "妥善保管"})
        send_bot_message(f"✅ 数据已备份至本地:\n{backup_path}", "accountant")
        return True
    except Exception as e:
        log.error(f"❌ 备份失败: {str(e)}", extra={"solution": "检查磁盘空间"})
        return False

# 创建基础信息表
@retry_on_failure(max_retries=2, delay=3)
def create_basic_info_table(client, app_token):
    # 先检查是否存在
    existing_id = get_table_id_by_name(client, app_token, "基础信息表")
    if existing_id:
        log.info(f"⚠️ 基础信息表已存在 (ID: {existing_id})", extra={"solution": "无"})
        return True, existing_id

    req = CreateAppTableRequest.builder() \
        .app_token(app_token) \
        .request_body(CreateAppTableRequestBody.builder()
            .table(ReqTable.builder()
                .name("基础信息表")
                .fields([
                    AppTableCreateHeader.builder().field_name("产品名称").type(FT.TEXT).build(),
                    AppTableCreateHeader.builder().field_name("单位成本").type(FT.NUMBER).build(), # Number format can be set later or via property
                    AppTableCreateHeader.builder().field_name("备注").type(FT.TEXT).build(),
                    # "最后更新时间" is usually a system field, but we can add a Date field
                    AppTableCreateHeader.builder().field_name("最后更新时间").type(FT.DATE).build() 
                ])
                .build())
            .build()) \
        .build()
    
    resp = client.bitable.v1.app_table.create(req)
    if resp.success():
        log.info("✅ 基础信息表创建成功", extra={"solution": "无"})
        return True, resp.data.table_id
    else:
        log.error(f"❌ 基础信息表创建失败: {resp.msg}", extra={"solution": "检查权限"})
        return False, None

# 创建往来单位表 (新)
@retry_on_failure(max_retries=2, delay=3)
def create_partner_table(client, app_token):
    existing_id = get_table_id_by_name(client, app_token, "往来单位表")
    if existing_id:
        log.info(f"⚠️ 往来单位表已存在 (ID: {existing_id})", extra={"solution": "无"})
        return True, existing_id

    req = CreateAppTableRequest.builder() \
        .app_token(app_token) \
        .request_body(CreateAppTableRequestBody.builder()
            .table(ReqTable.builder()
                .name("往来单位表")
                .fields([
                    AppTableCreateHeader.builder().field_name("单位名称").type(FT.TEXT).build(),
                    AppTableCreateHeader.builder().field_name("类型").type(FT.SELECT).property(AppTableFieldProperty.builder().options([
                        AppTableFieldPropertyOption.builder().name("客户").build(),
                        AppTableFieldPropertyOption.builder().name("供应商").build(),
                        AppTableFieldPropertyOption.builder().name("其他").build()
                    ]).build()).build(),
                    AppTableCreateHeader.builder().field_name("纳税人识别号").type(FT.TEXT).build(),
                    AppTableCreateHeader.builder().field_name("开户行及账号").type(FT.TEXT).build(),
                    AppTableCreateHeader.builder().field_name("地址及电话").type(FT.TEXT).build(),
                    AppTableCreateHeader.builder().field_name("联系人").type(FT.TEXT).build(),
                    AppTableCreateHeader.builder().field_name("联系电话").type(FT.TEXT).build(),
                    AppTableCreateHeader.builder().field_name("备注").type(FT.TEXT).build()
                ])
                .build())
            .build()) \
        .build()
    
    resp = client.bitable.v1.app_table.create(req)
    if resp.success():
        log.info("✅ 往来单位表创建成功", extra={"solution": "无"})
        return True, resp.data.table_id
    else:
        log.error(f"❌ 往来单位表创建失败: {resp.msg}", extra={"solution": "检查权限"})
        return False, None

# 创建发票管理表 (新)
@retry_on_failure(max_retries=2, delay=3)
def create_invoice_table(client, app_token):
    existing_id = get_table_id_by_name(client, app_token, "发票管理表")
    if existing_id:
        log.info(f"⚠️ 发票管理表已存在 (ID: {existing_id})", extra={"solution": "无"})
        return True, existing_id

    req = CreateAppTableRequest.builder() \
        .app_token(app_token) \
        .request_body(CreateAppTableRequestBody.builder()
            .table(ReqTable.builder()
                .name("发票管理表")
                .fields([
                    AppTableCreateHeader.builder().field_name("发票号码").type(FT.TEXT).build(),
                    AppTableCreateHeader.builder().field_name("发票代码").type(FT.TEXT).build(),
                    AppTableCreateHeader.builder().field_name("开票日期").type(FT.DATE).build(),
                    AppTableCreateHeader.builder().field_name("类型").type(FT.SELECT).property(AppTableFieldProperty.builder().options([
                        AppTableFieldPropertyOption.builder().name("进项专票").build(),
                        AppTableFieldPropertyOption.builder().name("进项普票").build(),
                        AppTableFieldPropertyOption.builder().name("销项专票").build(),
                        AppTableFieldPropertyOption.builder().name("销项普票").build()
                    ]).build()).build(),
                    AppTableCreateHeader.builder().field_name("购买方/销售方").type(FT.TEXT).build(),
                    AppTableCreateHeader.builder().field_name("不含税金额").type(FT.NUMBER).build(),
                    AppTableCreateHeader.builder().field_name("税额").type(FT.NUMBER).build(),
                    AppTableCreateHeader.builder().field_name("价税合计").type(FT.NUMBER).build(),
                    AppTableCreateHeader.builder().field_name("状态").type(FT.SELECT).property(AppTableFieldProperty.builder().options([
                        AppTableFieldPropertyOption.builder().name("正常").build(),
                        AppTableFieldPropertyOption.builder().name("作废").build(),
                        AppTableFieldPropertyOption.builder().name("红冲").build()
                    ]).build()).build(),
                    AppTableCreateHeader.builder().field_name("电子发票文件").type(FT.ATTACHMENT).build(),
                    AppTableCreateHeader.builder().field_name("备注").type(FT.TEXT).build()
                ])
                .build())
            .build()) \
        .build()
    
    resp = client.bitable.v1.app_table.create(req)
    if resp.success():
        log.info("✅ 发票管理表创建成功", extra={"solution": "无"})
        return True, resp.data.table_id
    else:
        log.error(f"❌ 发票管理表创建失败: {resp.msg}", extra={"solution": "检查权限"})
        return False, None

# 创建固定资产表 (新)
@retry_on_failure(max_retries=2, delay=3)
def create_asset_table(client, app_token):
    existing_id = get_table_id_by_name(client, app_token, "固定资产表")
    if existing_id:
        log.info(f"⚠️ 固定资产表已存在 (ID: {existing_id})", extra={"solution": "无"})
        return True, existing_id

    req = CreateAppTableRequest.builder() \
        .app_token(app_token) \
        .request_body(CreateAppTableRequestBody.builder()
            .table(ReqTable.builder()
                .name("固定资产表")
                .fields([
                    AppTableCreateHeader.builder().field_name("资产名称").type(FT.TEXT).build(),
                    AppTableCreateHeader.builder().field_name("类别").type(FT.SELECT).property(AppTableFieldProperty.builder().options([
                        AppTableFieldPropertyOption.builder().name("电子设备").build(),
                        AppTableFieldPropertyOption.builder().name("办公家具").build(),
                        AppTableFieldPropertyOption.builder().name("交通工具").build(),
                        AppTableFieldPropertyOption.builder().name("其他").build()
                    ]).build()).build(),
                    AppTableCreateHeader.builder().field_name("购买日期").type(FT.DATE).build(),
                    AppTableCreateHeader.builder().field_name("原值").type(FT.NUMBER).build(),
                    AppTableCreateHeader.builder().field_name("残值率(%)").type(FT.NUMBER).build(), # New
                    AppTableCreateHeader.builder().field_name("使用年限(年)").type(FT.NUMBER).build(),
                    AppTableCreateHeader.builder().field_name("存放地点").type(FT.TEXT).build(),
                    AppTableCreateHeader.builder().field_name("保管人").type(FT.TEXT).build(),
                    AppTableCreateHeader.builder().field_name("状态").type(FT.SELECT).property(AppTableFieldProperty.builder().options([
                        AppTableFieldPropertyOption.builder().name("使用中").build(),
                        AppTableFieldPropertyOption.builder().name("闲置").build(),
                        AppTableFieldPropertyOption.builder().name("报废").build()
                    ]).build()).build(),
                    AppTableCreateHeader.builder().field_name("备注").type(FT.TEXT).build()
                ])
                .build())
            .build()) \
        .build()
    
    resp = client.bitable.v1.app_table.create(req)
    if resp.success():
        log.info("✅ 固定资产表创建成功", extra={"solution": "无"})
        return True, resp.data.table_id
    else:
        log.error(f"❌ 固定资产表创建失败: {resp.msg}", extra={"solution": "检查权限"})
        return False, None

# 创建日常台账表
@retry_on_failure(max_retries=2, delay=3)
def create_ledger_table(client, app_token):
    existing_id = get_table_id_by_name(client, app_token, "日常台账表")
    if existing_id:
        log.info(f"⚠️ 日常台账表已存在 (ID: {existing_id})", extra={"solution": "无"})
        return True, existing_id

    req = CreateAppTableRequest.builder() \
        .app_token(app_token) \
        .request_body(CreateAppTableRequestBody.builder()
            .table(ReqTable.builder()
                .name("日常台账表")
                .fields([
                    AppTableCreateHeader.builder().field_name("记账日期").type(FT.DATE).build(),
                    AppTableCreateHeader.builder().field_name("凭证号").type(FT.NUMBER).build(),
                    AppTableCreateHeader.builder().field_name("业务类型").type(FT.SELECT).property(AppTableFieldProperty.builder().options([
                        AppTableFieldPropertyOption.builder().name("收款").build(),
                        AppTableFieldPropertyOption.builder().name("付款").build(),
                        AppTableFieldPropertyOption.builder().name("费用").build()
                    ]).build()).build(),
                    AppTableCreateHeader.builder().field_name("往来单位费用").type(FT.TEXT).build(),
                    AppTableCreateHeader.builder().field_name("账面金额").type(FT.NUMBER).build(),
                    AppTableCreateHeader.builder().field_name("实际收付金额").type(FT.NUMBER).build(),
                    AppTableCreateHeader.builder().field_name("交易银行").type(FT.SELECT).property(AppTableFieldProperty.builder().options([
                         AppTableFieldPropertyOption.builder().name("G银行基本户").build(),
                         AppTableFieldPropertyOption.builder().name("N银行/微信（现金）").build()
                    ]).build()).build(),
                    AppTableCreateHeader.builder().field_name("是否现金").type(FT.SELECT).property(AppTableFieldProperty.builder().options([ # Use Select for Yes/No
                         AppTableFieldPropertyOption.builder().name("是").build(),
                         AppTableFieldPropertyOption.builder().name("否").build()
                    ]).build()).build(),
                    AppTableCreateHeader.builder().field_name("发票流水单号").type(FT.TEXT).build(),
                    AppTableCreateHeader.builder().field_name("是否有票").type(FT.SELECT).property(AppTableFieldProperty.builder().options([
                         AppTableFieldPropertyOption.builder().name("有票").build(),
                         AppTableFieldPropertyOption.builder().name("无票").build()
                    ]).build()).build(),
                    AppTableCreateHeader.builder().field_name("待补票标记").type(FT.SELECT).property(AppTableFieldProperty.builder().options([
                         AppTableFieldPropertyOption.builder().name("是（大额无票）").build(),
                         AppTableFieldPropertyOption.builder().name("无").build()
                    ]).build()).build(),
                    AppTableCreateHeader.builder().field_name("有票成本").type(FT.NUMBER).build(),
                    AppTableCreateHeader.builder().field_name("无票成本").type(FT.NUMBER).build(),
                    AppTableCreateHeader.builder().field_name("本次实际利润").type(FT.NUMBER).build(),
                    AppTableCreateHeader.builder().field_name("手工式分录").type(FT.TEXT).build(),
                    AppTableCreateHeader.builder().field_name("操作人").type(FT.TEXT).build(),
                    AppTableCreateHeader.builder().field_name("合同订单号").type(FT.TEXT).build(),
                    AppTableCreateHeader.builder().field_name("备注").type(FT.TEXT).build()
                ])
                .build())
            .build()) \
        .build()
    
    resp = client.bitable.v1.app_table.create(req)
    if resp.success():
        log.info("✅ 日常台账表创建成功", extra={"solution": "无"})
        return True, resp.data.table_id
    else:
        log.error(f"❌ 日常台账表创建失败: {resp.msg}", extra={"solution": "检查权限"})
        return False, None

# 填充测试数据
def fill_test_data(client, app_token):
    log.info("🚀 正在填充高质量演示数据...", extra={"solution": "请稍候"})
    
    # 1. 填充往来单位表 (先填充这个，方便后面引用)
    table_id = get_table_id_by_name(client, app_token, "往来单位表")
    if table_id:
        records = []
        sample_partners = [
            {"name": "杭州阿里云计算有限公司", "type": "供应商", "tax_id": "913301066739887754", "remark": "云服务器费用"},
            {"name": "滴滴出行科技有限公司", "type": "供应商", "tax_id": "91120116340983320T", "remark": "员工差旅"},
            {"name": "上海xx贸易有限公司", "type": "客户", "tax_id": "91310115MA1H888888", "remark": "核心大客户"},
            {"name": "京东办公用品", "type": "供应商", "tax_id": "91110105MA00C7XE48", "remark": "办公耗材"},
            {"name": "中国移动通信", "type": "供应商", "tax_id": "911100007109250324", "remark": "电话宽带"}
        ]
        for p in sample_partners:
            fields = {
                "单位名称": p["name"],
                "类型": p["type"],
                "纳税人识别号": p["tax_id"],
                "备注": p["remark"]
            }
            records.append(AppTableRecord.builder().fields(fields).build())
        
        req = BatchCreateAppTableRecordRequest.builder() \
            .app_token(app_token) \
            .table_id(table_id) \
            .request_body(BatchCreateAppTableRecordRequestBody.builder().records(records).build()) \
            .build()
        client.bitable.v1.app_table_record.batch_create(req)
        log.info("✅ 往来单位表：已写入 5 条标准数据")

    # 2. 填充基础信息表
    table_id = get_table_id_by_name(client, app_token, "基础信息表")
    if table_id:
        records = []
        products = [
            {"name": "咨询服务费", "cost": 0},
            {"name": "标准SaaS订阅", "cost": 2000},
            {"name": "高级定制开发", "cost": 15000}
        ]
        for p in products:
            fields = {
                "产品名称": p["name"],
                "单位成本": p["cost"],
                "备注": "演示产品"
            }
            records.append(AppTableRecord.builder().fields(fields).build())
        
        req = BatchCreateAppTableRecordRequest.builder() \
            .app_token(app_token) \
            .table_id(table_id) \
            .request_body(BatchCreateAppTableRecordRequestBody.builder().records(records).build()) \
            .build()
        client.bitable.v1.app_table_record.batch_create(req)
        log.info("✅ 基础信息表：已写入 3 条产品数据")

    # 3. 填充日常台账表 (生成本月真实流水的台账)
    table_id = get_table_id_by_name(client, app_token, "日常台账表")
    if table_id:
        records = []
        now = datetime.now()
        # 生成几笔典型交易
        txs = [
            {"day": 1, "type": "收款", "name": "上海xx贸易有限公司", "amt": 50000.0, "bank": "G银行基本户", "ticket": "有票", "cash": "否", "remark": "Q1服务费首款"},
            {"day": 5, "type": "付款", "name": "杭州阿里云计算有限公司", "amt": 2500.0, "bank": "G银行基本户", "ticket": "有票", "cash": "否", "remark": "1月云资源费"},
            {"day": 8, "type": "费用", "name": "滴滴出行科技有限公司", "amt": 356.5, "bank": "G银行基本户", "ticket": "有票", "cash": "否", "remark": "销售部拜访客户打车"},
            {"day": 10, "type": "费用", "name": "京东办公用品", "amt": 899.0, "bank": "G银行基本户", "ticket": "有票", "cash": "否", "remark": "采购A4纸和墨盒"},
            {"day": 12, "type": "收款", "name": "上海xx贸易有限公司", "amt": 30000.0, "bank": "G银行基本户", "ticket": "有票", "cash": "否", "remark": "Q1服务费尾款"},
            {"day": 15, "type": "费用", "name": "中国移动通信", "amt": 199.0, "bank": "G银行基本户", "ticket": "有票", "cash": "否", "remark": "公司宽带费"},
            {"day": 20, "type": "付款", "name": "房租物业", "amt": 12000.0, "bank": "N银行/微信（现金）", "ticket": "无票", "cash": "是", "remark": "临时仓库租金(房东个人)"},
            {"day": 22, "type": "费用", "name": "顺丰快递", "amt": 56.0, "bank": "N银行/微信（现金）", "ticket": "无票", "cash": "是", "remark": "寄送合同快递费(微信支付)"}
        ]
        
        for tx in txs:
            # 构造日期
            tx_date = datetime(now.year, now.month, tx["day"])
            ts = int(tx_date.timestamp() * 1000)
            
            fields = {
                "记账日期": ts,
                "凭证号": int(tx_date.strftime("%Y%m%d")) + hash(tx["name"]) % 100,
                "业务类型": tx["type"],
                "往来单位费用": tx["name"],
                "账面金额": tx["amt"],
                "实际收付金额": tx["amt"],
                "交易银行": tx["bank"],
                "是否现金": tx["cash"],
                "是否有票": tx["ticket"],
                "待补票标记": "是（大额无票）" if tx["ticket"] == "无票" and tx["amt"] > 1000 else "无",
                "操作人": "自动初始化",
                "备注": tx["remark"]
            }
            records.append(AppTableRecord.builder().fields(fields).build())
        
        req = BatchCreateAppTableRecordRequest.builder() \
            .app_token(app_token) \
            .table_id(table_id) \
            .request_body(BatchCreateAppTableRecordRequestBody.builder().records(records).build()) \
            .build()
        client.bitable.v1.app_table_record.batch_create(req)
        log.info(f"✅ 日常台账表：已写入 {len(records)} 条演示流水")

    # 4. 填充发票管理表
    table_id = get_table_id_by_name(client, app_token, "发票管理表")
    if table_id:
        records = []
        fields = {
            "发票号码": "88888888",
            "发票代码": "031001800104",
            "开票日期": int(datetime.now().timestamp() * 1000),
            "类型": "进项专票",
            "购买方/销售方": "杭州阿里云计算有限公司",
            "价税合计": 2500.0,
            "不含税金额": 2358.49,
            "税额": 141.51,
            "状态": "正常",
            "备注": "对应1月云资源费"
        }
        records.append(AppTableRecord.builder().fields(fields).build())
        
        req = BatchCreateAppTableRecordRequest.builder() \
            .app_token(app_token) \
            .table_id(table_id) \
            .request_body(BatchCreateAppTableRecordRequestBody.builder().records(records).build()) \
            .build()
        client.bitable.v1.app_table_record.batch_create(req)
        log.info("✅ 发票管理表：已写入演示发票")

    # 5. 填充固定资产表
    table_id = get_table_id_by_name(client, app_token, "固定资产表")
    if table_id:
        records = []
        assets = [
            {"name": "MacBook Pro M3", "type": "电子设备", "val": 14999, "user": "老板"},
            {"name": "佳能打印机", "type": "电子设备", "val": 2500, "user": "行政"},
            {"name": "人体工学椅", "type": "办公家具", "val": 800, "user": "全体"}
        ]
        for a in assets:
            fields = {
                "资产名称": a["name"],
                "类别": a["type"],
                "购买日期": int((datetime.now() - timedelta(days=30)).timestamp() * 1000),
                "原值": a["val"],
                "使用年限(年)": 3,
                "存放地点": "公司总部",
                "保管人": a["user"],
                "状态": "使用中",
                "备注": "初始资产"
            }
            records.append(AppTableRecord.builder().fields(fields).build())
        
        req = BatchCreateAppTableRecordRequest.builder() \
            .app_token(app_token) \
            .table_id(table_id) \
            .request_body(BatchCreateAppTableRecordRequestBody.builder().records(records).build()) \
            .build()
        client.bitable.v1.app_table_record.batch_create(req)
        log.info("✅ 固定资产表：已写入演示资产")

# 月度结账
@retry_on_failure(max_retries=2, delay=3)
def monthly_close(client, app_token):
    log.info("📅 开始月度结账流程...", extra={"solution": "无"})
    
    # 1. 导出备份
    print("\n[1/2] 正在执行全量备份...")
    backup_ok = export_to_excel(client, app_token)
    
    # 2. 生成报表
    print("\n[2/2] 正在生成分析报表...")
    report_ok = generate_html_report(client, app_token)
    
    if backup_ok and report_ok:
        # 新增：生成Excel利润表
        generate_excel_pnl_report(client, app_token)
        
        msg = f"📅 月度结账完成！\n✅ 数据已备份\n✅ 报表已生成\n💡 请务必将本地生成的 Excel 和 HTML 文件打包存档。"
        log.info("✅ 月度结账流程结束", extra={"solution": "存档"})
        send_bot_message(msg, "accountant")
        return True
    else:
        log.error("❌ 月度结账部分失败", extra={"solution": "检查日志"})
        return False

# 生成Excel利润表
def generate_excel_pnl_report(client, app_token):
    log.info("📊 正在生成标准利润表(Excel)...", extra={"solution": "无"})
    table_id = get_table_id_by_name(client, app_token, "日常台账表")
    if not table_id:
        return False

    records = get_all_records(client, app_token, table_id)
    if not records:
        return False
        
    data = []
    for r in records:
        fields = r.fields
        data.append({
            "记账日期": datetime.fromtimestamp(fields.get("记账日期", 0)/1000).strftime('%Y-%m-%d') if fields.get("记账日期") else "",
            "业务类型": fields.get("业务类型", ""),
            "往来单位费用": fields.get("往来单位费用", ""),
            "实际收付金额": float(fields.get("实际收付金额", 0)),
            "是否有票": fields.get("是否有票", "无票")
        })
        
    df = pd.DataFrame(data)
    
    # 简单的利润表逻辑
    income = df[df["业务类型"] == "收款"]["实际收付金额"].sum()
    cost = df[df["业务类型"].isin(["付款", "费用"])]["实际收付金额"].sum()
    gross_profit = income - cost
    
    # 按费用分类汇总
    expense_summary = df[df["业务类型"].isin(["付款", "费用"])].groupby("往来单位费用")["实际收付金额"].sum().reset_index()
    expense_summary.columns = ["项目", "金额"]
    expense_summary = expense_summary.sort_values(by="金额", ascending=False)
    
    # 写入Excel
    filename = f"利润表_{datetime.now().strftime('%Y%m')}.xlsx"
    with pd.ExcelWriter(filename, engine='openpyxl') as writer:
        # 概览页
        summary_data = [
            ["项目", "金额", "备注"],
            ["营业收入", income, "所有收款汇总"],
            ["营业成本/费用", cost, "所有付款/费用汇总"],
            ["净利润", gross_profit, "收入 - 成本"],
            ["", "", ""],
            ["利润率", f"{(gross_profit/income*100):.2f}%" if income > 0 else "0%", ""]
        ]
        pd.DataFrame(summary_data).to_excel(writer, sheet_name="利润表概览", index=False, header=False)
        
        # 费用明细页
        expense_summary.to_excel(writer, sheet_name="费用明细", index=False)
        
        # 原始数据页
        df.to_excel(writer, sheet_name="流水底稿", index=False)
        
    log.info(f"✅ 利润表已生成: {filename}", extra={"solution": "无"})
    return True

def setup_auto_task():
    """设置 Windows 计划任务 (每天18:00自动运行)"""
    print(f"\n⏰ 正在配置每日自动运行任务...")
    
    # 1. 创建自动运行脚本
    cwd = os.getcwd()
    python_exe = sys.executable
    script_path = os.path.join(cwd, "CW.py")
    
    bat_content = f"""@echo off
cd /d "{cwd}"
"{python_exe}" "{script_path}" --auto-run >> auto_run.log 2>&1
"""
    bat_file = os.path.join(cwd, "run_daily_task.bat")
    with open(bat_file, "w", encoding="utf-8") as f:
        f.write(bat_content)
        
    print(f"✅ 已创建执行脚本: {bat_file}")
    
    # 2. 调用 schtasks 创建任务
    # 任务名: FeishuFinanceAuto
    # 触发: 每天 18:00
    cmd = f'schtasks /create /sc daily /tn "FeishuFinanceAuto" /tr "{bat_file}" /st 18:00 /f'
    
    print(f"👉 正在向 Windows 注册任务 (可能需要管理员权限)...")
    print(f"   执行命令: {cmd}")
    
    try:
        ret = os.system(cmd)
        if ret == 0:
            print(f"{Color.GREEN}✅ 成功！系统将在每天 18:00 自动帮您处理账务。{Color.ENDC}")
            print("   (记得电脑那时候要开机哦)")
        else:
            print(f"{Color.FAIL}❌ 创建失败。请尝试以管理员身份运行 run.bat 再试一次。{Color.ENDC}")
    except Exception as e:
        print(f"❌ 发生错误: {e}")

def restore_from_backup():
    """从备份恢复数据"""
    backup_root = "backup"
    if not os.path.exists(backup_root):
        print("❌ 没有找到备份文件夹 (backup)")
        return
        
    # 列出备份目录
    dirs = [d for d in os.listdir(backup_root) if os.path.isdir(os.path.join(backup_root, d))]
    dirs.sort(reverse=True) # 最新在通过
    
    if not dirs:
        print("❌ 没有找到任何备份记录")
        return
        
    print(f"\n💾 [系统恢复] 请选择要恢复的备份点:")
    for i, d in enumerate(dirs[:10]):
        print(f"   {i+1}. {d}")
        
    choice = input("\n👉 请输入序号 (慎重! 会覆盖当前配置): ").strip()
    if not choice.isdigit(): return
    
    idx = int(choice) - 1
    if 0 <= idx < len(dirs):
        target = dirs[idx]
        src_path = os.path.join(backup_root, target)
        
        print(f"{Color.WARNING}⚠️  警告: 将从 {target} 恢复文件。当前目录下的同名文件将被覆盖！{Color.ENDC}")
        if input("确认继续吗? (输入 'yes' 确认): ").strip().lower() != "yes":
            return
            
        print("⏳ 正在恢复...")
        import shutil
        
        # 恢复文件
        for f in os.listdir(src_path):
            full_src = os.path.join(src_path, f)
            if os.path.isfile(full_src) and not f.endswith(".zip"):
                try:
                    shutil.copy(full_src, ".")
                    print(f"   - 已恢复: {f}")
                except Exception as e:
                    print(f"   ❌ 失败: {f} ({e})")
                    
        print(f"{Color.GREEN}✅ 恢复完成！请重启程序。{Color.ENDC}")
        sys.exit(0)

# 每日简报 (老板看板)
@retry_on_failure(max_retries=2, delay=3)
def draw_ascii_bar_chart(data, title="统计图表"):
    """在终端绘制简单的ASCII柱状图"""
    if not data: return
    
    print(f"\n📊 {title}")
    print("-" * 50)
    
    # 过滤掉 0 值，除非全是 0
    valid_data = {k: v for k, v in data.items() if v > 0}
    if not valid_data and any(v > 0 for v in data.values()):
        pass # 只有部分是0
    elif not valid_data:
        valid_data = data # 全是0
        
    if not valid_data:
        print("   (暂无数据)")
        print("-" * 50)
        return

    max_val = max(valid_data.values())
    if max_val == 0: max_val = 1
    
    max_len = 25 # 柱子最大长度
    
    for label, value in data.items():
        bar_len = int((value / max_val) * max_len)
        bar = "█" * bar_len
        # 使用 ANSI 颜色让它更好看
        color = Color.GREEN if "收入" in label else (Color.FAIL if "支出" in label else Color.CYAN)
        print(f"{label:<12} | {color}{bar:<25}{Color.ENDC} {value:,.2f}")
    print("-" * 50)

def daily_briefing(client, app_token):
    log.info("📅 正在生成每日经营简报...", extra={"solution": "无"})
    table_id = get_table_id_by_name(client, app_token, "日常台账表")
    if not table_id: return False

    # 获取本月数据
    now = datetime.now()
    start_of_month = datetime(now.year, now.month, 1)
    start_ts = int(start_of_month.timestamp() * 1000)
    filter_info = f'CurrentValue.[记账日期]>={start_ts}'
    
    records = get_all_records(client, app_token, table_id, filter_info=filter_info)
    
    today_str = now.strftime("%Y-%m-%d")
    
    today_income = 0.0
    today_cost = 0.0
    month_income = 0.0
    month_cost = 0.0
    
    today_tx_count = 0
    latest_txs = []
    
    for r in records:
        fields = r.fields
        # 日期处理
        ts = fields.get("记账日期", 0)
        try:
            r_date = datetime.fromtimestamp(ts/1000)
            r_date_str = r_date.strftime("%Y-%m-%d")
        except:
            continue
            
        amt = float(fields.get("实际收付金额", 0))
        biz_type = fields.get("业务类型", "")
        desc = fields.get("往来单位费用", "未知")
        
        # 本月累计
        if biz_type == "收款":
            month_income += amt
        elif biz_type in ["付款", "费用"]:
            month_cost += amt
            
        # 今日统计
        if r_date_str == today_str:
            today_tx_count += 1
            if biz_type == "收款":
                today_income += amt
            elif biz_type in ["付款", "费用"]:
                today_cost += amt
                
            # 收集今日明细
            latest_txs.append(f"{biz_type}: {desc} ({amt:,.2f})")

    # 构造飞书卡片
    net_cash = month_income - month_cost

    # [新增] 终端显示 ASCII 图表
    chart_data = {
        "今日收入": today_income,
        "今日支出": today_cost,
        "本月收入": month_income,
        "本月支出": month_cost
    }
    
    # [V9.4] 简单的趋势预测
    days_passed = now.day
    pred_msg = ""
    if days_passed >= 3: # 至少3天才预测
        avg_cost = month_cost / days_passed
        pred_total_cost = avg_cost * 30
        chart_data[f"预测月底支出"] = pred_total_cost
        pred_msg = f" (按当前趋势，月底预计支出: {pred_total_cost:,.0f})"
        
    draw_ascii_bar_chart(chart_data, title=f"今日经营简报{pred_msg}")
    
    if latest_txs:
        print(f"\n📝 今日明细 ({today_tx_count}笔):")
        for t in latest_txs[:5]:
            print(f"  - {t}")
        if len(latest_txs) > 5:
            print(f"  ... (还有 {len(latest_txs)-5} 笔)")
    else:
        print("\n💤 今日暂无收支记录")

    # [V9.4] 检查待处理单据
    watch_dir = os.path.join(os.getcwd(), "待处理单据")
    if os.path.exists(watch_dir):
        pending_files = [f for f in os.listdir(watch_dir) if f.lower().endswith(('.xlsx', '.xls'))]
        if pending_files:
            print(f"\n🔔 【待办提醒】 发现 {len(pending_files)} 个待处理文件在 '{watch_dir}'")
            for pf in pending_files[:3]:
                print(f"   - {pf}")
            if len(pending_files) > 3:
                print(f"   ... 等 {len(pending_files)} 个文件")
            print("   💡 建议运行菜单 [20] 启动自动监听，或手动导入")
    
    elements = [
        {
            "tag": "div",
            "fields": [
                {"is_short": True, "text": {"tag": "lark_md", "content": f"**今日收入**\n¥ {today_income:,.2f}"}},
                {"is_short": True, "text": {"tag": "lark_md", "content": f"**今日支出**\n¥ {today_cost:,.2f}"}},
                {"is_short": True, "text": {"tag": "lark_md", "content": f"**本月累计收入**\n¥ {month_income:,.2f}"}},
                {"is_short": True, "text": {"tag": "lark_md", "content": f"**本月累计支出**\n¥ {month_cost:,.2f}"}}
            ]
        },
        {"tag": "hr"},
        {
             "tag": "div",
             "text": {"tag": "lark_md", "content": f"💰 **本月净现金流**: ¥ {net_cash:,.2f}"}
        }
    ]
    
    # 如果今天有交易，列出前5笔
    if latest_txs:
        tx_list = "\n".join([f"- {t}" for t in latest_txs[:5]])
        if len(latest_txs) > 5:
            tx_list += f"\n... (还有 {len(latest_txs)-5} 笔)"
            
        elements.append({
            "tag": "div",
            "text": {"tag": "lark_md", "content": f"**📝 今日交易明细 ({today_tx_count}笔)**:\n{tx_list}"}
        })
    else:
        elements.append({
            "tag": "div",
            "text": {"tag": "lark_md", "content": "💤 今日暂无收支记录"}
        })
        
    # AI 点评 (如果有Key)
    if ZHIPUAI_API_KEY and today_tx_count > 0:
        try:
            client_ai = ZhipuAI(api_key=ZHIPUAI_API_KEY)
            prompt = f"今日公司收入{today_income}，支出{today_cost}。请用一句话给老板汇报，语气积极。"
            resp = client_ai.chat.completions.create(model="glm-4-flash", messages=[{"role": "user", "content": prompt}])
            ai_msg = resp.choices[0].message.content.strip()
            print(f"\n🤖 AI汇报: {ai_msg}") # 终端也显示
            elements.append({
                "tag": "note",
                "elements": [{"tag": "plain_text", "content": f"🤖 AI汇报: {ai_msg}"}]
            })
        except:
            pass

    card = {
        "header": {
            "title": {"tag": "plain_text", "content": f"📅 每日经营简报 ({today_str})"},
            "template": "blue"
        },
        "elements": elements
    }
    
    send_bot_message("每日简报", "interactive", card)
    log.info("✅ 每日简报已推送", extra={"solution": "查看飞书"})
    return True

# 显示数据后台链接
def show_cloud_urls(client, app_token):
    print("\n🌐 飞书云端数据后台 (请复制链接在浏览器打开):")
    print(f"🔗 多维表格主页: https://feishu.cn/base/{app_token}")
    
    tables = ["日常台账表", "往来单位表", "基础信息表", "发票管理表", "固定资产表"]
    for t in tables:
        tid = get_table_id_by_name(client, app_token, t)
        if tid:
            print(f"   📂 {t}: https://feishu.cn/base/{app_token}?table={tid}")
            
    print("\n💡 提示:")
    print("1. 往来单位、产品信息、银行账户等**基础档案**，请直接在网页端修改。")
    print("2. 自动分类规则，请修改本地的 category_rules.json 文件。")
    print("3. 税率、容差等参数，请使用 [8. 系统设置] 修改。")
    
    # 尝试自动打开
    try:
        import webbrowser
        print("\n🚀 正在尝试自动打开浏览器...")
        webbrowser.open(f"https://feishu.cn/base/{app_token}")
    except:
        pass

# -------------------------------------------------------------------------
# 新增功能：AI 查数助手 & 财务体检
# -------------------------------------------------------------------------

def ai_data_query(client, app_token):
    """AI 查数助手：允许用户用自然语言查询财务数据"""
    if not zhipu_client:
        log.error("❌ 未配置 GLM-4 API Key，无法使用 AI 功能", extra={"solution": "请在 .env 文件中配置 ZHIPU_API_KEY"})
        return

    print("\n🤖 AI 财务助手已启动 (输入 'q' 退出)")
    print("你可以问：'上个月餐饮费多少？' 或 '最近一笔大额支出是什么？'")
    
    # 获取最近的数据作为上下文 (为了节省 token，只取最近 50 条)
    table_id = get_table_id_by_name(client, app_token, "日常台账表")
    if not table_id:
        log.error("❌ 找不到日常台账表", extra={"solution": "请先初始化表格"})
        return

    records = get_all_records(client, app_token, table_id)
    # 简单的上下文构建
    context_data = []
    # 排序：最新的在后
    records_sorted = sorted(records, key=lambda r: r.fields.get("记账日期", 0))
    
    for r in records_sorted[-50:]: # 取最后50条
        f = r.fields
        # 转换时间戳
        date_str = "未知日期"
        if isinstance(f.get("记账日期"), int):
            date_str = datetime.fromtimestamp(f["记账日期"] / 1000).strftime("%Y-%m-%d")
        
        context_data.append(f"{date_str} | {f.get('业务类型')} | {f.get('往来单位费用')} | {f.get('实际收付金额')} | {f.get('备注') or ''}")
    
    data_context = "\n".join(context_data)
    
    while True:
        user_input = input("\n🗣️ 请提问: ").strip()
        if user_input.lower() in ['q', 'quit', 'exit']:
            break
            
        if not user_input:
            continue
            
        try:
            log.info("🤔 AI 正在思考...", extra={"solution": "请稍候"})
            response = zhipu_client.chat.completions.create(
                model="glm-4-flash",
                messages=[
                    {"role": "system", "content": f"你是一名专业的财务助理。以下是最近的财务流水数据（格式：日期|类型|对象|金额|备注）：\n\n{data_context}\n\n请根据以上数据回答用户的问题。如果数据中没有答案，请如实告知。金额单位为元。"},
                    {"role": "user", "content": user_input}
                ],
                stream=False
            )
            answer = response.choices[0].message.content
            print(f"\n🤖 AI 回答:\n{answer}")
        except Exception as e:
            log.error(f"AI 响应失败: {e}")

def check_duplicate(client, app_token, table_id, amount, date_str, partner, summary):
    """检查是否存在重复记录 (最近7天，金额相同，摘要相似)"""
    try:
        # 获取最近记录
        records = get_all_records(client, app_token, table_id, field_names=["记账日期", "实际收付金额", "备注", "往来单位费用"])
        
        target_date = datetime.strptime(date_str, "%Y-%m-%d")
        target_amount = float(amount)
        
        for r in records:
            f = r.fields
            try:
                r_date = datetime.fromtimestamp(f.get("记账日期", 0) / 1000)
                r_amount = float(f.get("实际收付金额", 0))
                r_partner = str(f.get("往来单位费用", ""))
                r_summary = str(f.get("备注", ""))
                
                # 规则1: 金额必须完全相同
                if abs(r_amount - target_amount) > 0.01:
                    continue
                    
                # 规则2: 日期在前后3天内
                if abs((r_date - target_date).days) > 3:
                    continue
                    
                # 规则3: 往来单位或摘要高度相似
                if partner and partner in r_partner:
                    return True, f"发现相似记录: {r_date.strftime('%Y-%m-%d')} {r_amount} {r_summary}"
                if summary and summary[:5] in r_summary:
                    return True, f"发现相似记录: {r_date.strftime('%Y-%m-%d')} {r_amount} {r_summary}"
                    
            except:
                continue
                
        return False, ""
    except Exception as e:
        log.warning(f"查重失败: {e}")
        return False, ""

def smart_text_entry(client, app_token):
    """智能文本录入：将自然语言/微信消息解析为记账记录"""
    if not zhipu_client:
        log.error("❌ 未配置 GLM-4 API Key，无法使用 AI 功能", extra={"solution": "请在 .env 文件中配置 ZHIPU_API_KEY"})
        return

    table_id = get_table_id_by_name(client, app_token, "日常台账表")
    if not table_id:
        log.error("❌ 找不到日常台账表", extra={"solution": "请先初始化表格"})
        return

    print("\n📝 智能文本记账助手")
    print("-----------------------------------")
    print("👉 请直接粘贴微信/支付宝的文本，或者老板在群里发的消息。")
    print("例如：")
    print("  - '今天收到张三货款5000元'")
    print("  - '支付阿里云服务器续费 1200元'")
    print("  - '微信支付打车费 56元'")
    print("-----------------------------------")
    
    import json
    
    # 预加载历史知识，用于优化AI结果
    load_history_knowledge(client, app_token)

    while True:
        text = input("\n⌨️ 请输入/粘贴文本 (输入 'q' 退出): ").strip()
        if text.lower() in ['q', 'quit', 'exit']:
            break
        if not text:
            continue
            
        log.info("🧠 AI 正在解析...", extra={"solution": "请稍候"})
        
        try:
            # 1. AI 解析
            prompt = f"""
            你是一个专业的会计助手。请从以下文本中提取财务记账所需的关键信息，并以 JSON 格式返回。
            文本："{text}"
            
            JSON 字段要求：
            - date: 记账日期 (格式 YYYY-MM-DD)。如果文本中没有明确日期，默认为今天({datetime.now().strftime('%Y-%m-%d')})。
            - amount: 金额 (数字，保留2位小数)。
            - type: 业务类型 (只能是 "收款" 或 "付款" 或 "费用")。如果是支出但有票，优先选"费用"；如果是纯支出无票，选"付款"。如果无法判断，默认为"费用"。
            - category: 费用类型/资金账户 (例如：主营业务收入, 办公费, 差旅费, 技术服务费, 预收账款, 预付账款)。请根据内容猜测。
            - partner: 往来单位/对象 (例如：张三, 阿里云, 滴滴)。如果没提到，留空。
            - summary: 备注/摘要 (尽量保留原意，去除无关废话)。
            - is_cash: 是否现金/私户 (true/false)。如果提到"微信"、"支付宝"、"现金"，则为 true，否则 false。
            - has_ticket: 是否有票 (有票/无票)。如果是现金/私户，默认为"无票"，否则"有票"。
            
            只返回纯 JSON 字符串，不要包含 Markdown 格式。
            """
            
            response = zhipu_client.chat.completions.create(
                model="glm-4-flash",
                messages=[
                    {"role": "user", "content": prompt}
                ],
                stream=False
            )
            
            content = response.choices[0].message.content.replace("```json", "").replace("```", "").strip()
            data = json.loads(content)
            
            # 优化1：解析别名
            if data.get('partner'):
                data['partner'] = resolve_partner(data['partner'])

            # 优化2：利用历史知识修正分类
            # 如果 AI 猜的分类不在常用列表中，或者我们有更明确的规则
            history_cat = auto_categorize(data.get('summary'), data.get('category'), partner_name=data.get('partner'))
            if history_cat != data.get('category'):
                log.info(f"💡 根据历史习惯，将 '{data.get('category')}' 修正为 '{history_cat}'")
                data['category'] = history_cat

            # 查重检测
            is_dup, dup_msg = check_duplicate(client, app_token, table_id, data.get('amount'), data.get('date'), data.get('partner'), data.get('summary'))
            if is_dup:
                print(f"\n⚠️  警告: {dup_msg}")
                print("    (可能重复录入！)")
            
            # 3. 交互式确认与修改 (复用逻辑)
            while True:
                print("\n🤖 AI 解析结果 (请核对):")
                print(f"  1. 📅 日期: {data.get('date')}")
                print(f"  2. 💰 金额: {data.get('amount')}")
                print(f"  3. 🏷️ 类型: {data.get('type')}")
                print(f"  4. 📂 分类: {data.get('category')}")
                print(f"  5. 👤 对象: {data.get('partner')}")
                print(f"  6. 📝 摘要: {data.get('summary')}")
                print(f"  7. 🏦 账户: {'现金/私户' if data.get('is_cash') else '对公账户'}")
                print(f"  8. 🧾 发票: {data.get('has_ticket')}")
                
                action = input("\n👉 输入 'y' 确认录入，输入数字(1-8)修改对应项，输入 'n' 取消: ").strip().lower()
                
                if action == 'y':
                    break
                elif action == 'n':
                    print("❌ 已取消")
                    return
                elif action.isdigit():
                    idx = int(action)
                    if idx == 1:
                        val = input(f"请输入新日期 ({data.get('date')}): ").strip()
                        if val: data['date'] = val
                    elif idx == 2:
                        val = input(f"请输入新金额 ({data.get('amount')}): ").strip()
                        if val: data['amount'] = val
                    elif idx == 3:
                        val = input(f"请输入新类型 ({data.get('type')}): ").strip()
                        if val: data['type'] = val
                    elif idx == 4:
                        val = input(f"请输入新分类 ({data.get('category')}): ").strip()
                        if val: data['category'] = val
                    elif idx == 5:
                        val = input(f"请输入新对象 ({data.get('partner')}): ").strip()
                        if val: data['partner'] = val
                    elif idx == 6:
                        val = input(f"请输入新摘要 ({data.get('summary')}): ").strip()
                        if val: data['summary'] = val
                    elif idx == 7:
                        data['is_cash'] = not data.get('is_cash') # 切换
                    elif idx == 8:
                        curr = data.get('has_ticket')
                        data['has_ticket'] = "无票" if curr == "有票" else "有票" # 切换
                else:
                    print("❌ 无效指令")

            # 4. 构造 Record 并上传
            fields = {
                "记账日期": int(datetime.strptime(data.get('date'), "%Y-%m-%d").timestamp() * 1000),
                "业务类型": data.get('type'),
                "费用类型": data.get('category'),
                "往来单位费用": data.get('partner') or "散户",
                "实际收付金额": float(data.get('amount')),
                "备注": data.get('summary'),
                "是否现金": "是" if data.get('is_cash') else "否",
                "是否有票": data.get('has_ticket')
            }
            
            req = CreateAppTableRecordRequest.builder() \
                .app_token(app_token) \
                .table_id(table_id) \
                .app_table_record(AppTableRecord.builder().fields(fields).build()) \
                .build()
            
            resp = client.bitable.v1.app_table_record.create(req)
            if resp.success():
                print("✅ 录入成功！")
                send_bot_message(f"✅ AI 文本录入成功: {data.get('summary')} - {data.get('amount')}元", "accountant")
            else:
                log.error(f"❌ 录入失败: {resp.msg}")

        except Exception as e:
            log.error(f"处理失败: {e}", extra={"solution": "请重试"})

def smart_image_entry(client, app_token, file_path=None, auto_confirm=False):
    """智能截图记账：OCR识别+AI解析"""
    if not zhipu_client:
        log.error("❌ 未配置 GLM-4 API Key", extra={"solution": "请在 .env 文件中配置 ZHIPU_API_KEY"})
        return

    table_id = get_table_id_by_name(client, app_token, "日常台账表")
    if not table_id: return

    # 预加载历史知识
    load_history_knowledge(client, app_token)

    image = None
    if file_path:
        # 自动模式：直接使用传入的文件路径
        try:
            image = Image.open(file_path)
            print(f"✅ 已加载图片: {os.path.basename(file_path)}")
        except Exception as e:
            log.error(f"无法打开图片: {e}")
            return
    else:
        # 交互模式：从剪贴板或对话框获取
        print("\n📸 智能截图记账助手")
        print("-----------------------------------")
        print("👉 请先将【微信/支付宝截图】或【银行回单截图】复制到剪贴板。")
        print("   (或者按回车键选择本地图片文件)")
        print("-----------------------------------")
        
        input("📋 复制好图片后，请按回车继续... (输入 q 退出)")
        
        try:
            # 1. 获取图片
            image = ImageGrab.grabclipboard()
            
            # Windows上抓取的文件列表可能不是Image对象
            if isinstance(image, list):
                 # 用户复制了文件，不是图片内容
                 if len(image) > 0:
                     try:
                         image = Image.open(image[0])
                     except:
                         image = None

            if isinstance(image, Image.Image):
                print("✅ 已从剪贴板获取图片")
            else:
                print("⚠️ 剪贴板中没有图片，请选择文件...")
                # 隐藏主窗口
                root = tk.Tk()
                root.withdraw()
                root.attributes('-topmost', True) # 确保弹窗在最前
                
                file_path_dialog = filedialog.askopenfilename(
                    title="选择图片文件",
                    filetypes=[("Images", "*.png;*.jpg;*.jpeg;*.bmp;*.webp")]
                )
                root.destroy()
                
                if not file_path_dialog:
                    print("❌ 未选择文件")
                    return
                try:
                    image = Image.open(file_path_dialog)
                    print(f"✅ 已加载图片: {os.path.basename(file_path_dialog)}")
                except Exception as e:
                    log.error(f"无法打开图片: {e}")
                    return
        except Exception as e:
            log.error(f"获取图片失败: {e}")
            return

    try:

        # 2. 转 base64
        # 压缩图片以避免超出token限制或传输过慢
        image.thumbnail((1024, 1024)) 
        
        buffered = BytesIO()
        image.save(buffered, format="PNG") # 统一转PNG
        img_base64 = base64.b64encode(buffered.getvalue()).decode('utf-8')
        
        log.info("👀 AI 正在“看”图并提取数据...", extra={"solution": "请稍候"})
        
        response = zhipu_client.chat.completions.create(
            model="glm-4v-flash",
            messages=[
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": """
                            请分析这张财务单据/聊天截图，提取记账所需的关键信息，并以 JSON 格式返回。
                            
                            JSON 字段要求：
                            - date: 交易日期 (格式 YYYY-MM-DD)。如果图中没有年份，默认为2026年。如果完全没日期，默认为今天。
                            - amount: 金额 (数字，保留2位小数)。
                            - type: 业务类型 (收款/付款/费用)。
                            - category: 费用类型/资金账户 (例如：主营业务收入, 办公费, 差旅费, 技术服务费, 预收账款, 预付账款)。请根据内容猜测。
                            - partner: 往来单位/对象。
                            - summary: 备注/摘要 (简要描述交易内容)。
                            - is_cash: 是否现金/私户 (true/false)。微信/支付宝/私卡截图通常为 true。
                            - has_ticket: 是否有票 (有票/无票)。截图通常默认为"无票"，除非是发票截图。
                            
                            只返回纯 JSON 字符串，不要包含 Markdown 格式。
                            """
                        },
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": img_base64
                            }
                        }
                    ]
                }
            ]
        )
        
        import json
        content = response.choices[0].message.content.replace("```json", "").replace("```", "").strip()
        data = json.loads(content)
        
        # 优化：解析别名
        if data.get('partner'):
            data['partner'] = resolve_partner(data['partner'])

        # 优化：利用历史知识修正分类
        history_cat = auto_categorize(data.get('summary'), data.get('category'), partner_name=data.get('partner'))
        if history_cat != data.get('category'):
            log.info(f"💡 根据历史习惯，将 '{data.get('category')}' 修正为 '{history_cat}'")
            data['category'] = history_cat

        # 查重检测
        is_dup, dup_msg = check_duplicate(client, app_token, table_id, data.get('amount'), data.get('date'), data.get('partner'), data.get('summary'))
        if is_dup:
            print(f"\n⚠️  警告: {dup_msg}")
            print("    (可能重复录入！)")

        # 3. 交互式确认与修改
        while True:
            print("\n🤖 AI 解析结果 (请核对):")
            print(f"  1. 📅 日期: {data.get('date')}")
            print(f"  2. 💰 金额: {data.get('amount')}")
            print(f"  3. 🏷️ 类型: {data.get('type')}")
            print(f"  4. 📂 分类: {data.get('category')}")
            print(f"  5. 👤 对象: {data.get('partner')}")
            print(f"  6. 📝 摘要: {data.get('summary')}")
            print(f"  7. 🏦 账户: {'现金/私户' if data.get('is_cash') else '对公账户'}")
            print(f"  8. 🧾 发票: {data.get('has_ticket')}")
            
            if auto_confirm:
                print("✅ 自动确认模式：直接录入")
                action = 'y'
            else:
                action = input("\n👉 输入 'y' 确认录入，输入数字(1-8)修改对应项，输入 'n' 取消: ").strip().lower()
            
            if action == 'y':
                break
            elif action == 'n':
                print("❌ 已取消")
                return
            elif action.isdigit():
                idx = int(action)
                if idx == 1:
                    val = input(f"请输入新日期 ({data.get('date')}): ").strip()
                    if val: data['date'] = val
                elif idx == 2:
                    val = input(f"请输入新金额 ({data.get('amount')}): ").strip()
                    if val: data['amount'] = val
                elif idx == 3:
                    val = input(f"请输入新类型 ({data.get('type')}): ").strip()
                    if val: data['type'] = val
                elif idx == 4:
                    val = input(f"请输入新分类 ({data.get('category')}): ").strip()
                    if val: data['category'] = val
                elif idx == 5:
                    val = input(f"请输入新对象 ({data.get('partner')}): ").strip()
                    if val: data['partner'] = val
                elif idx == 6:
                    val = input(f"请输入新摘要 ({data.get('summary')}): ").strip()
                    if val: data['summary'] = val
                elif idx == 7:
                    data['is_cash'] = not data.get('is_cash') # 切换
                elif idx == 8:
                    curr = data.get('has_ticket')
                    data['has_ticket'] = "无票" if curr == "有票" else "有票" # 切换
            else:
                print("❌ 无效指令")

        # 4. 构造 Record 并上传
        fields = {
            "记账日期": int(datetime.strptime(data.get('date'), "%Y-%m-%d").timestamp() * 1000),
            "业务类型": data.get('type'),
            "费用类型": data.get('category'),
            "往来单位费用": data.get('partner') or "散户",
            "实际收付金额": float(data.get('amount')),
            "备注": data.get('summary'),
            "是否现金": "是" if data.get('is_cash') else "否",
            "是否有票": data.get('has_ticket')
        }
        
        req = CreateAppTableRecordRequest.builder() \
            .app_token(app_token) \
            .table_id(table_id) \
            .app_table_record(AppTableRecord.builder().fields(fields).build()) \
            .build()
        
        resp = client.bitable.v1.app_table_record.create(req)
        if resp.success():
            print("✅ 录入成功！")
            send_bot_message(f"✅ AI 截图录入成功: {data.get('summary')} - {data.get('amount')}元", "accountant")
        else:
            log.error(f"❌ 录入失败: {resp.msg}")

    except Exception as e:
        log.error(f"处理失败: {e}", extra={"solution": "请重试"})

def learn_category_rules(client, app_token):
    """智能学习：从历史数据中挖掘分类规则"""
    log.info("🧠 正在分析历史数据以优化分类规则...", extra={"solution": "无"})
    
    table_id = get_table_id_by_name(client, app_token, "日常台账表")
    if not table_id:
        return

    records = get_all_records(client, app_token, table_id)
    
    from collections import Counter
    
    # 现有规则
    global AUTO_CATEGORY_RULES
    existing_rules = AUTO_CATEGORY_RULES
    
    # 候选池
    candidates = []
    
    for r in records:
        f = r.fields
        desc = str(f.get("备注", "")).strip()
        cat = f.get("费用类型", "")
        
        if not desc or not cat:
            continue
            
        # 简单清洗：如果全是数字（如订单号），跳过
        if desc.isdigit(): continue
        
        # 检查是否已被规则覆盖
        is_covered = False
        for k, v in existing_rules.items():
            if k in desc:
                is_covered = True
                break
        
        if not is_covered:
            candidates.append((desc, cat))
            
    # 统计频率
    counts = Counter(candidates)
    
    # 筛选出高频项 (出现 >= 2 次)
    print("\n🔍 发现以下潜在的分类规则 (基于您的历史习惯):")
    print(f"{'关键词 (摘要)':<30} | {'建议分类':<15} | {'出现次数'}")
    print("-" * 60)
    
    index = 1
    suggested_map = {}
    
    for (desc, cat), count in counts.most_common(20): # 只看前20个高频
        if count >= 2:
            # 简单启发式：截取前10个字作为关键词
            keyword = desc[:10]
            print(f"{index}. {keyword:<27} -> {cat:<15} ({count}次)")
            suggested_map[index] = (keyword, cat)
            index += 1
            
    if not suggested_map:
        print("✅ 当前没有发现明显的新规则 (现有规则已覆盖大部分场景)")
        return
        
    print("-" * 60)
    print("👉 输入序号添加规则 (例如 '1,3,5')，输入 'all' 全部添加，直接回车跳过")
    choice = input("您的选择: ").strip().lower()
    
    to_add = []
    if choice == 'all':
        to_add = list(suggested_map.values())
    elif choice:
        try:
            indices = [int(x.strip()) for x in choice.replace("，", ",").split(",") if x.strip()]
            for i in indices:
                if i in suggested_map:
                    to_add.append(suggested_map[i])
        except:
            pass
            
    if to_add:
        # 更新规则文件
        import json
        try:
            with open("category_rules.json", "r", encoding="utf-8") as f:
                rules = json.load(f)
        except:
            rules = {}
            
        count = 0
        for k, v in to_add:
            rules[k] = v
            AUTO_CATEGORY_RULES[k] = v # 更新内存
            count += 1
            
        with open("category_rules.json", "w", encoding="utf-8") as f:
            json.dump(rules, f, ensure_ascii=False, indent=4)
            
        print(f"✅ 已成功添加 {count} 条新规则！下次记账更智能。")
    else:
        print("未添加任何规则。")

def quick_search_records(client, app_token):
    """快速查账功能"""
    print("\n🔍 快速查账助手")
    print("-----------------------------------")
    keyword = input("👉 请输入关键词 (日期/金额/对象/摘要): ").strip()
    if not keyword: return

    table_id = get_table_id_by_name(client, app_token, "日常台账表")
    if not table_id: return

    print("正在搜索...")
    records = get_all_records(client, app_token, table_id)
    
    found = []
    total_in = 0.0
    total_out = 0.0
    
    for r in records:
        f = r.fields
        # 将所有字段拼接成字符串进行搜索
        date_ts = f.get("记账日期", 0)
        date_str = datetime.fromtimestamp(date_ts/1000).strftime('%Y-%m-%d') if date_ts else ""
        
        full_text = f"{date_str} {f.get('业务类型','')} {f.get('费用类型','')} {f.get('往来单位费用','')} {f.get('实际收付金额','')} {f.get('备注','')} {f.get('合同订单号','')}"
        
        if keyword in full_text:
            found.append(r)
            amt = float(f.get("实际收付金额", 0))
            if f.get("业务类型") == "收款":
                total_in += amt
            elif f.get("业务类型") in ["付款", "费用"]:
                total_out += amt
                
    if not found:
        print(f"❌ 未找到包含 '{keyword}' 的记录")
        return
        
    print(f"\n✅ 找到 {len(found)} 条记录:")
    print("-" * 60)
    print(f"{'日期':<12} | {'类型':<6} | {'对象':<15} | {'金额':<10} | {'摘要'}")
    print("-" * 60)
    
    # 按日期倒序
    found.sort(key=lambda x: x.fields.get("记账日期", 0), reverse=True)
    
    for r in found[:20]: # 最多显示20条
        f = r.fields
        date_ts = f.get("记账日期", 0)
        date_str = datetime.fromtimestamp(date_ts/1000).strftime('%Y-%m-%d') if date_ts else ""
        
        # 截断过长字符串
        partner = str(f.get("往来单位费用", ""))[:14]
        memo = str(f.get("备注", ""))[:20]
        
        print(f"{date_str:<12} | {f.get('业务类型',''):<6} | {partner:<15} | {f.get('实际收付金额',0):<10} | {memo}")
        
    if len(found) > 20:
        print(f"... (还有 {len(found)-20} 条未显示)")
        
    print("-" * 60)
    print(f"💰 统计结果: 收款 {total_in:,.2f} | 支出 {total_out:,.2f} | 净额 {total_in - total_out:,.2f}")
    
    # 导出选项
    if input("\n👉 是否导出搜索结果到 Excel? (y/n): ").strip().lower() == 'y':
        data = []
        for r in found:
            f = r.fields
            f['记账日期'] = datetime.fromtimestamp(f.get('记账日期', 0)/1000).strftime('%Y-%m-%d') if f.get('记账日期') else ""
            data.append(f)
            
        filename = f"查账结果_{keyword}_{datetime.now().strftime('%Y%m%d%H%M%S')}.xlsx"
        pd.DataFrame(data).to_excel(filename, index=False)
        print(f"✅ 已导出: {filename}")
        try: os.startfile(filename)
        except: pass

def manage_aliases():
    """管理往来单位别名 (增删改查)"""
    global PARTNER_ALIASES
    
    while True:
        print("\n📇 往来单位别名管理")
        print("-------------------")
        print("1. 查看当前别名")
        print("2. 添加新别名")
        print("3. 删除别名")
        print("4. 批量导入别名 (文本粘贴) [新]")
        print("5. 批量导入别名 (Excel文件) [新]")
        print("0. 返回主菜单")
        print("-------------------")
        
        choice = input("请选择 (0-5): ").strip()
        
        if choice == '0':
            break
            
        elif choice == '1':
            print(f"\n📋 当前映射规则 ({len(PARTNER_ALIASES)}条):")
            print(f"{'别名 (对方户名)':<20} -> {'标准名称 (系统)'}")
            print("-" * 50)
            if not PARTNER_ALIASES:
                print("(暂无别名)")
            else:
                for k, v in PARTNER_ALIASES.items():
                    print(f"{k:<25} -> {v}")
            input("\n按回车继续...")
            
        elif choice == '2':
            print("\n➕ 添加新别名")
            print("例如: 银行流水显示'张三'，实际是'A客户公司'")
            alias = input("请输入别名 (对方户名/微信名): ").strip()
            if not alias: continue
            
            real_name = input(f"请输入 '{alias}' 对应的标准单位名称: ").strip()
            if not real_name: continue
            
            PARTNER_ALIASES[alias] = real_name
            
            # 保存
            try:
                with open("partner_aliases.json", "w", encoding="utf-8") as f:
                    json.dump(PARTNER_ALIASES, f, ensure_ascii=False, indent=4)
                print(f"✅ 已添加: {alias} -> {real_name}")
            except Exception as e:
                log.error(f"保存失败: {e}")
                
        elif choice == '3':
            alias = input("请输入要删除的别名: ").strip()
            if alias in PARTNER_ALIASES:
                del PARTNER_ALIASES[alias]
                # 保存
                try:
                    with open("partner_aliases.json", "w", encoding="utf-8") as f:
                        json.dump(PARTNER_ALIASES, f, ensure_ascii=False, indent=4)
                    print(f"✅ 已删除: {alias}")
                except Exception as e:
                    log.error(f"保存失败: {e}")
            else:
                print("❌ 找不到该别名")
                
        elif choice == '4':
            print("\n📥 批量导入别名 (文本粘贴)")
            print("格式：别名 -> 标准名称 (每行一条)")
            print("例如：")
            print("张三 -> A公司")
            print("李四 -> B公司")
            print("-------------------")
            print("请粘贴内容，然后按 Ctrl+Z (Windows) 或 Ctrl+D (Linux/Mac) 结束输入，或者输入 'END' 结束：")
            
            lines = []
            while True:
                try:
                    line = input()
                    if line.strip().upper() == 'END':
                        break
                    lines.append(line)
                except EOFError:
                    break
            
            count = 0
            for line in lines:
                if "->" in line:
                    parts = line.split("->")
                    if len(parts) == 2:
                        alias = parts[0].strip()
                        real = parts[1].strip()
                        if alias and real:
                            PARTNER_ALIASES[alias] = real
                            count += 1
            
            if count > 0:
                # Save
                try:
                    with open("partner_aliases.json", "w", encoding="utf-8") as f:
                        json.dump(PARTNER_ALIASES, f, ensure_ascii=False, indent=4)
                    print(f"✅ 成功导入 {count} 条别名！")
                except Exception as e:
                    log.error(f"保存失败: {e}")
            else:
                print("⚠️ 未识别到有效数据")

        elif choice == '5':
            print("\n📥 批量导入别名 (Excel文件)")
            print("请准备一个Excel文件，包含两列：【别名】和【标准名称】")
            print("如果没有表头，默认第一列是别名，第二列是标准名称。")
            
            excel_path = select_file_interactively("*.xlsx", "请选择别名映射表")
            if not excel_path:
                print("❌ 未选择文件")
                continue
                
            try:
                df = pd.read_excel(excel_path)
                if df.shape[1] < 2:
                    print("❌ 文件列数不足，至少需要两列")
                    continue
                    
                count = 0
                # 尝试寻找标准列名
                alias_col = None
                real_col = None
                
                for col in df.columns:
                    col_str = str(col)
                    if "别名" in col_str or "户名" in col_str:
                        alias_col = col
                    if "标准" in col_str or "全称" in col_str or "单位" in col_str:
                        real_col = col
                        
                # 如果找不到，就用前两列
                if not alias_col: alias_col = df.columns[0]
                if not real_col: real_col = df.columns[1]
                
                print(f"ℹ️ 使用列: 【{alias_col}】 -> 【{real_col}】")
                
                for _, row in df.iterrows():
                    a = str(row[alias_col]).strip()
                    r = str(row[real_col]).strip()
                    if a and r and a != "nan" and r != "nan":
                        PARTNER_ALIASES[a] = r
                        count += 1
                        
                if count > 0:
                     # Save
                    with open("partner_aliases.json", "w", encoding="utf-8") as f:
                        json.dump(PARTNER_ALIASES, f, ensure_ascii=False, indent=4)
                    print(f"✅ 成功导入 {count} 条别名！")
                else:
                    print("⚠️ 未找到有效数据")
                    
            except Exception as e:
                log.error(f"导入失败: {e}")

def generate_partner_statement(client, app_token):
    """生成往来对账单"""
    log.info("📊 准备生成往来对账单...", extra={"solution": "请按提示操作"})
    
    table_id = get_table_id_by_name(client, app_token, "日常台账表")
    if not table_id: return
    
    # 1. 获取所有往来单位
    print("正在获取往来单位列表...")
    records = get_all_records(client, app_token, table_id, field_names=["往来单位费用"])
    partners = set()
    for r in records:
        p = r.fields.get("往来单位费用")
        if p and p != "散户":
            partners.add(p)
            
    sorted_partners = sorted(list(partners))
    
    print("\n👥 往来单位列表:")
    for i, p in enumerate(sorted_partners):
        print(f"{i+1}. {p}")
        
    # 2. 选择单位
    print("-" * 30)
    choice = input("请输入序号或直接输入单位名称: ").strip()
    target_partner = ""
    
    if choice.isdigit() and 1 <= int(choice) <= len(sorted_partners):
        target_partner = sorted_partners[int(choice)-1]
    else:
        # 模糊匹配
        matches = [p for p in sorted_partners if choice in p]
        if len(matches) == 1:
            target_partner = matches[0]
        elif len(matches) > 1:
            print(f"❌ 找到多个匹配: {matches}，请更精确一点")
            return
        elif choice in sorted_partners: # 精确匹配
            target_partner = choice
        else:
            print("❌ 未找到该单位")
            return
            
    print(f"✅ 已选择: 【{target_partner}】")
    
    # 3. 获取该单位所有记录
    print(f"正在拉取 {target_partner} 的所有往来记录...")
    all_records = get_all_records(client, app_token, table_id)
    
    partner_records = []
    total_in = 0.0
    total_out = 0.0
    
    for r in all_records:
        f = r.fields
        p = str(f.get("往来单位费用", "")).strip()
        
        if p == target_partner:
            date_ts = f.get("记账日期", 0)
            date_str = datetime.fromtimestamp(date_ts/1000).strftime('%Y-%m-%d') if date_ts else ""
            
            amt = float(f.get("实际收付金额", 0))
            b_type = f.get("业务类型", "")
            
            row = {
                "日期": date_str,
                "业务类型": b_type,
                "费用类型": f.get("费用类型", ""),
                "金额": amt,
                "备注": f.get("备注", ""),
                "是否有票": f.get("是否有票", "无票")
            }
            partner_records.append(row)
            
            if b_type == "收款":
                total_in += amt
            elif b_type in ["付款", "费用"]:
                total_out += amt

    if not partner_records:
        print("⚠️ 未找到任何记录")
        return
        
    # 4. 生成 Excel
    df = pd.DataFrame(partner_records)
    df = df.sort_values(by="日期")
    
    filename = f"往来对账单_{target_partner}_{datetime.now().strftime('%Y%m%d')}.xlsx"
    
    with pd.ExcelWriter(filename, engine='openpyxl') as writer:
        # 汇总页
        summary = [
            ["项目", "金额", "说明"],
            ["往来单位", target_partner, ""],
            ["累计收款", total_in, "我方收到"],
            ["累计付款", total_out, "我方支付"],
            ["净额", total_in - total_out, "正数=我方净收，负数=我方净付"],
            ["生成时间", datetime.now().strftime('%Y-%m-%d %H:%M:%S'), ""]
        ]
        pd.DataFrame(summary).to_excel(writer, sheet_name="对账汇总", index=False, header=False)
        
        # 明细页
        df.to_excel(writer, sheet_name="流水明细", index=False)
        
    log.info(f"✅ 对账单已生成: {filename}", extra={"solution": "请发给对方确认"})
    try:
        os.startfile(filename)
    except:
        pass

# -------------------------------------------------------------------------
# 新增功能：固定资产折旧
# -------------------------------------------------------------------------

def calculate_depreciation(client, app_token, auto_run=False):
    """一键计提折旧 (生成折旧凭证)"""
    log.info("📉 正在计算固定资产折旧...", extra={"solution": "无"})
    
    asset_table_id = get_table_id_by_name(client, app_token, "固定资产表")
    ledger_table_id = get_table_id_by_name(client, app_token, "日常台账表")
    
    if not asset_table_id or not ledger_table_id:
        log.error("❌ 未找到表格，请先初始化", extra={"solution": "运行 --create-table"})
        return

    # 0. 检查本月是否已计提
    current_month_str = datetime.now().strftime('%Y-%m')
    
    # 简易检查：检查是否存在备注包含 "折旧计提" 且日期为本月的记录
    now = datetime.now()
    start_dt = datetime(now.year, now.month, 1)
    if now.month == 12:
        end_dt = datetime(now.year + 1, 1, 1)
    else:
        end_dt = datetime(now.year, now.month + 1, 1)
    
    start_ts = int(start_dt.timestamp() * 1000)
    end_ts = int(end_dt.timestamp() * 1000)
    
    # 使用筛选器查询，避免拉取全部数据
    filter_cmd = f'CurrentValue.[记账日期]>={start_ts}&&CurrentValue.[记账日期]<{end_ts}&&CurrentValue.[费用类型]="折旧摊销"'
    
    existing_deps = get_all_records(client, app_token, ledger_table_id, filter_info=filter_cmd)
    if existing_deps:
        print(f"{Color.WARNING}⚠️ 检测到本月 ({current_month_str}) 已有 {len(existing_deps)} 条折旧记录！{Color.ENDC}")
        if not auto_run:
            if input("❓ 是否继续计提 (可能导致重复)? (y/n) [n]: ").strip().lower() != 'y':
                return
        else:
            log.info("⚠️ 自动模式下跳过重复计提", extra={"solution": "手动强制执行"})
            return

    # 1. 获取所有使用中的资产
    assets = get_all_records(client, app_token, asset_table_id)
    
    depreciation_entries = []
    total_depreciation = 0.0
    
    if not auto_run:
        print(f"\n📋 资产折旧预览 ({current_month_str}):")
        print("-" * 60)
        print(f"{'资产名称':<20} | {'原值':<10} | {'残值%':<5} | {'月折旧额':<10}")
        print("-" * 60)
    
    for asset in assets:
        f = asset.fields
        status = f.get("状态", "")
        if status != "使用中":
            continue
            
        name = f.get("资产名称", "未知资产")
        original_val = float(f.get("原值", 0))
        years = float(f.get("使用年限(年)", 3)) # 默认3年
        
        if years <= 0: continue
        
        # 简单直线法：月折旧 = 原值 * (1 - 残值率) / (年限 * 12)
        # 尝试获取残值率，默认 0%
        salvage_rate = 0.0
        if "残值率(%)" in f:
            try:
                salvage_rate = float(f["残值率(%)"]) / 100.0
            except:
                salvage_rate = 0.0
        
        monthly_dep = (original_val * (1 - salvage_rate)) / (years * 12)
        monthly_dep = round(monthly_dep, 2)
        
        if monthly_dep > 0:
            if not auto_run:
                print(f"{name:<20} | {original_val:<10.2f} | {salvage_rate*100:<5.0f}% | {monthly_dep:<10.2f}")
            
            depreciation_entries.append({
                "记账日期": int(datetime.now().timestamp() * 1000),
                "业务类型": "费用",
                "费用类型": "折旧摊销", # 自动归类
                "往来单位费用": "内部计提",
                "实际收付金额": monthly_dep, 
                "备注": f"{current_month_str} 折旧计提 - {name}",
                "是否现金": "否", 
                "是否有票": "无票",
                "待补票标记": "无"
            })
            total_depreciation += monthly_dep
            
    if not auto_run:
        print("-" * 60)
        print(f"💰 本月折旧总额: {total_depreciation:.2f}")
    
    if total_depreciation == 0:
        if not auto_run: print("⚠️ 没有需要折旧的资产。")
        return
        
    confirm = 'y'
    if not auto_run:
        confirm = input("\n❓ 确认生成以上折旧凭证吗？(y/n): ").strip().lower()
        
    if confirm == 'y':
        # 批量写入
        batch_size = 100
        for i in range(0, len(depreciation_entries), batch_size):
            batch = depreciation_entries[i:i+batch_size]
            
            # Convert dicts to AppTableRecord
            record_objects = [AppTableRecord.builder().fields(entry).build() for entry in batch]
            
            req = BatchCreateAppTableRecordRequest.builder() \
                .app_token(app_token) \
                .table_id(ledger_table_id) \
                .request_body(BatchCreateAppTableRecordRequestBody.builder().records(record_objects).build()) \
                .build()
            resp = client.bitable.v1.app_table_record.batch_create(req)
            if not resp.success():
                log.error(f"❌ 折旧凭证写入失败: {resp.msg}", extra={"solution": "检查网络"})
            
        print("✅ 折旧凭证已生成！")
        send_bot_message(f"✅ 完成本月折旧计提，总额: {total_depreciation}元", "accountant")
    else:
        print("❌ 已取消")

def export_standard_voucher(client, app_token):
    """导出标准凭证格式 (对接财务软件)"""
    log.info("📑 正在生成标准凭证导出文件...", extra={"solution": "请稍候"})
    
    table_id = get_table_id_by_name(client, app_token, "日常台账表")
    if not table_id: return
    
    # Get all records
    print("正在拉取所有凭证数据...")
    records = get_all_records(client, app_token, table_id)
    if not records:
        print("⚠️ 无数据")
        return

    # Sort records by date first
    records.sort(key=lambda r: r.fields.get("记账日期", 0))

    voucher_rows = []
    
    # Voucher Numbering
    current_month = ""
    month_seq = 0
    
    for r in records:
        f = r.fields
        date_ts = f.get("记账日期", 0)
        if not date_ts: continue
        
        dt = datetime.fromtimestamp(date_ts/1000)
        date_str = dt.strftime('%Y-%m-%d')
        month_str = dt.strftime('%Y%m')
        
        # Reset sequence for new month
        if month_str != current_month:
            current_month = month_str
            month_seq = 0
        
        month_seq += 1
        voucher_id = f"{month_str}-{month_seq:04d}" # e.g. 202310-0001
        
        amt = float(f.get("实际收付金额", 0))
        if amt == 0: continue
        
        b_type = f.get("业务类型", "")
        summary = f.get("备注", "")
        # 如果备注为空，使用往来单位或费用类型作为摘要
        if not summary:
             summary = f.get("往来单位费用", "")
        
        # 借贷逻辑
        bank_acc = f.get("交易银行", "银行存款")
        subject = f.get("往来单位费用", "暂无分类")
        
        # 简单会计分录逻辑
        if b_type == "收款":
            # 借：银行 (Asset Increase)
            voucher_rows.append({
                "日期": date_str,
                "凭证号": voucher_id,
                "摘要": summary,
                "科目名称": bank_acc, # 借方
                "借方金额": amt,
                "贷方金额": 0
            })
            # 贷：收入/往来 (Revenue/Liability Increase)
            voucher_rows.append({
                "日期": date_str,
                "凭证号": voucher_id,
                "摘要": summary,
                "科目名称": subject, # 贷方
                "借方金额": 0,
                "贷方金额": amt
            })
        elif b_type in ["付款", "费用"]:
            # 借：费用/往来 (Expense Increase)
            voucher_rows.append({
                "日期": date_str,
                "凭证号": voucher_id,
                "摘要": summary,
                "科目名称": subject, # 借方
                "借方金额": amt,
                "贷方金额": 0
            })
            # 贷：银行 (Asset Decrease)
            voucher_rows.append({
                "日期": date_str,
                "凭证号": voucher_id,
                "摘要": summary,
                "科目名称": bank_acc, # 贷方
                "借方金额": 0,
                "贷方金额": amt
            })
            
    if not voucher_rows:
        print("⚠️ 没有生成任何凭证分录")
        return

    df = pd.DataFrame(voucher_rows)
    # 按日期排序
    df = df.sort_values(by="日期")
    
    filename = f"标准凭证导出_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
    df.to_excel(filename, index=False)
    
    log.info(f"✅ 导出完成: {filename}", extra={"solution": "可直接导入金蝶/用友等财务软件"})
    try:
        os.startfile(filename)
    except:
        pass

# -------------------------------------------------------------------------
# 新增功能：交互式主菜单 (Python版)
# -------------------------------------------------------------------------

def backup_system_data():
    """备份系统关键配置和数据"""
    print(f"{Color.CYAN}💾 正在进行系统备份...{Color.ENDC}")
    
    backup_root = "backup"
    if not os.path.exists(backup_root):
        os.makedirs(backup_root)
        
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    target_dir = os.path.join(backup_root, timestamp)
    os.makedirs(target_dir)
    
    # 备份配置文件
    files_to_backup = [
        "partner_aliases.json",
        "category_rules.json",
        ".env",
        "run.bat",
        "使用手册_小白必读.txt"
    ]
    
    for f in files_to_backup:
        if os.path.exists(f):
            try:
                shutil.copy(f, target_dir)
                print(f"  - 已备份: {f}")
            except Exception as e:
                print(f"{Color.FAIL}  - 备份失败 {f}: {e}{Color.ENDC}")
    
    # 尝试备份 Excel 文件 (如果存在)
    excel_files = [f for f in os.listdir('.') if f.endswith('.xlsx') and not f.startswith('~$')]
    for f in excel_files:
        try:
            shutil.copy(f, target_dir)
            print(f"  - 已备份: {f}")
        except:
            pass
            
    # 压缩备份文件夹 (新增)
    try:
        shutil.make_archive(target_dir, 'zip', target_dir)
        print(f"📦 已创建压缩包: {target_dir}.zip")
    except Exception as e:
        print(f"⚠️ 压缩失败: {e}")

    print(f"{Color.GREEN}✅ 备份完成！保存路径: {target_dir}{Color.ENDC}")

def move_to_archive(filename):
    """归档文件"""
    target_dir = "2_已处理归档"
    if not os.path.exists(target_dir):
        os.makedirs(target_dir)
    try:
        basename = os.path.basename(filename)
        shutil.move(filename, os.path.join(target_dir, basename))
        print(f"   ✅ 文件已归档至 {target_dir}")
    except Exception as e:
        print(f"   ❌ 归档失败: {e}")

def send_notification(title, message):
    """发送 Windows 桌面通知 (使用 PowerShell)"""
    if os.name != 'nt': return
    
    try:
        # PowerShell 脚本: 加载 Windows.Forms 和 Drawing，使用 NotifyIcon
        ps_script = f"""
        [void] [System.Reflection.Assembly]::LoadWithPartialName("System.Windows.Forms")
        [void] [System.Reflection.Assembly]::LoadWithPartialName("System.Drawing")
        $notify = New-Object System.Windows.Forms.NotifyIcon
        $notify.Icon = [System.Drawing.SystemIcons]::Information
        $notify.Visible = $True
        $notify.ShowBalloonTip(0, "{title}", "{message}", [System.Windows.Forms.ToolTipIcon]::Info)
        Start-Sleep -s 3
        $notify.Dispose()
        """
        # 转换命令以避免引号问题
        cmd = ["powershell", "-Command", ps_script]
        # 异步执行，不阻塞
        import subprocess
        subprocess.Popen(cmd, shell=True)
    except Exception as e:
        print(f"⚠️ 通知发送失败: {e}")

def move_to_error(filename, error_msg=""):
    """移动到错误文件夹"""
    target_dir = "待处理单据/处理失败"
    if not os.path.exists(target_dir):
        os.makedirs(target_dir)
    try:
        basename = os.path.basename(filename)
        shutil.move(filename, os.path.join(target_dir, basename))
        print(f"   ❌ 文件已移至 {target_dir}")
        # 写个错误日志
        with open(os.path.join(target_dir, f"{basename}.log"), "w", encoding="utf-8") as f:
            f.write(f"Error Time: {datetime.now()}\n")
            f.write(f"Error: {error_msg}\n")
    except Exception as e:
        print(f"   ❌ 移动失败: {e}")

def monitor_folder_mode(client, app_token):
    """自动监听文件夹模式"""
    watch_dir = "待处理单据"
    watch_dir_abs = os.path.abspath(watch_dir)
    if not os.path.exists(watch_dir):
        os.makedirs(watch_dir)
        
    print(f"\n{Color.HEADER}📡 已启动【文件夹监听模式】 (挂机中...){Color.ENDC}")
    print(f"📂 监听目录: {watch_dir_abs}")
    print(f"💡 说明: 请将 Excel 银行流水/账单放入该文件夹，系统将自动识别并处理。")
    print(f"🔔 处理结果将通过桌面通知反馈。")
    print(f"🛑 按 Ctrl+C 停止监听并返回菜单。\n")
    
    send_notification("飞书财务助手", "挂机模式已启动，正在监听文件夹...")
    
    print("👀 正在等待新文件...")
    
    try:
        while True:
            # 扫描文件
            if os.path.exists(watch_dir):
                files = [f for f in os.listdir(watch_dir) if f.lower().endswith(('.xlsx', '.xls', '.png', '.jpg', '.jpeg', '.bmp')) and not f.startswith('~$')]
                
                if files:
                    print(f"\n⚡ 发现 {len(files)} 个新文件！开始处理...")
                    for filename in files:
                        full_path = os.path.join(watch_dir, filename)
                        
                        # 等待文件写入完成 (简单等待)
                        time.sleep(2)
                        
                        print(f"▶️ 正在处理: {filename}")
                        try:
                            # 图片处理
                            if filename.lower().endswith(('.png', '.jpg', '.jpeg', '.bmp')):
                                print(f"   📸 识别为图片，启动 AI 记账...")
                                smart_image_entry(client, app_token, file_path=full_path, auto_confirm=True)
                                msg = f"图片 {filename} AI 记账完成！"
                            else:
                                # Excel 处理
                                # 默认作为数据导入
                                is_bank_flow = False
                                if "流水" in filename or "对账" in filename or "bank" in filename.lower():
                                    is_bank_flow = True
                                    
                                if is_bank_flow:
                                    print(f"   🏦 识别为银行流水，启动对账模式...")
                                    reconcile_bank_flow(client, app_token, full_path)
                                    msg = f"银行流水 {filename} 对账完成！"
                                else:
                                    print(f"   📥 识别为业务数据，启动导入模式...")
                                    import_from_excel(client, app_token, excel_path=full_path)
                                    msg = f"业务数据 {filename} 导入成功！"
                                
                            # 归档
                            move_to_archive(full_path)
                            send_notification("处理成功", msg)
                            
                        except Exception as e:
                             print(f"❌ 处理出错: {e}")
                             send_notification("处理失败", f"文件 {filename} 处理出错，已移至失败文件夹。")
                             move_to_error(full_path, str(e))
                             
                    print("\n👀 处理完毕，继续等待新文件...")
                
            time.sleep(5)
    except KeyboardInterrupt:
        print("\n🛑 停止监听。")
        return

def one_click_daily_closing(client, app_token):
    """一键日结：自动处理单据 -> 计提折旧 -> 税务测算 -> 缺票检查 -> 结账报告 -> 备份"""
    print(f"\n{Color.HEADER}🚀 启动一键日结流程 (Daily Closing)...{Color.ENDC}")
    
    summary = []
    daily_log = [] # 报告详情
    
    # 1. 扫描当前目录下的 Excel 和 图片 文件
    import glob
    excel_files = [f for f in glob.glob("*.xlsx") if not f.startswith("~$") and not f.startswith("待补录") and not f.startswith("往来对账单") and not f.startswith("日结报告")]
    image_files = [f for f in glob.glob("*.*") if f.lower().endswith(('.png', '.jpg', '.jpeg', '.bmp'))]
    
    all_files = excel_files + image_files
    
    if not all_files:
        print(f"{Color.WARNING}⚠️  当前目录下没有找到待处理文件。{Color.ENDC}")
        summary.append("❌ 未发现新文件")
    else:
        print(f"📂 发现 {len(all_files)} 个待处理文件，开始处理...")
        for f in all_files:
            print(f"\n📄 正在处理文件: {Color.BOLD}{f}{Color.ENDC}")
            
            # 图片处理
            if f.lower().endswith(('.png', '.jpg', '.jpeg', '.bmp')):
                print(f"   📸 识别为图片，建议进行 AI 记账")
                if input("   ❓ 是否处理此图片? (y/n) [y]: ").strip().lower() != 'n':
                    smart_image_entry(client, app_token, file_path=f, auto_confirm=True)
                    summary.append(f"✅ 图片记账: {f}")
                    if input("   ❓ 是否归档? (y/n) [y]: ").strip().lower() != 'n':
                        move_to_archive(f)
                else:
                    summary.append(f"⏩ 跳过图片: {f}")
                continue

            # Excel 处理 (保留原有逻辑)
            # 智能判断建议
            suggestion = "3" # 默认跳过
            f_lower = f.lower()
            if "流水" in f or "对账单" in f or "bank" in f_lower:
                suggestion = "2" # 银行对账
                action_str = "银行对账"
            elif "账单" in f or "import" in f_lower or "数据" in f:
                suggestion = "1" # 数据导入
                action_str = "数据导入"
            else:
                suggestion = "3"
                action_str = "跳过"
            
            print(f"   建议操作: {Color.CYAN}{action_str}{Color.ENDC}")
            print("   1. 作为【业务数据】导入 (Upload)")
            print("   2. 作为【银行流水】对账 (Compare)")
            print("   3. 跳过")
            
            choice = input(f"👉 请选择 (1/2/3) [默认{suggestion}]: ").strip()
            if not choice: choice = suggestion
            
            if choice == '1':
                import_from_excel(client, app_token, f)
                summary.append(f"✅ 导入: {f}")
                if input("   ❓ 是否将文件移入 '2_已处理归档' 文件夹? (y/n) [y]: ").strip().lower() != 'n':
                    move_to_archive(f)
            elif choice == '2':
                reconcile_bank_flow(client, app_token, f)
                summary.append(f"✅ 对账: {f}")
                if input("   ❓ 是否将文件移入 '2_已处理归档' 文件夹? (y/n) [y]: ").strip().lower() != 'n':
                    move_to_archive(f)
            else:
                print("   ⏩ 已跳过")
                summary.append(f"⏩ 跳过: {f}")

    # 1.5 自动计提折旧
    print(f"\n{Color.HEADER}📉 检查固定资产折旧...{Color.ENDC}")
    calculate_depreciation(client, app_token, auto_run=True)

    # 2. 税务测算 (New)
    print(f"\n{Color.HEADER}🧮 正在进行税务测算...{Color.ENDC}")
    tax_msg = calculate_tax(client, app_token)
    daily_log.append("\n【税务风险测算】\n" + str(tax_msg))

    # 3. 缺票检查 (New)
    print(f"\n{Color.HEADER}🎫 正在检查待补票据...{Color.ENDC}")
    missing_count = export_missing_tickets(client, app_token, silent=True)
    if missing_count > 0:
        summary.append(f"⚠️ 发现 {missing_count} 笔待补票记录")
        daily_log.append(f"\n【待补票据】\n发现 {missing_count} 笔支出未收发票，请及时催收！")
    else:
        summary.append("✅ 票据状态良好")
        daily_log.append("\n【待补票据】\n目前没有待补票记录，非常棒！")

    # 4. 财务体检
    print(f"\n{Color.HEADER}🏥 开始财务健康体检...{Color.ENDC}")
    financial_health_check(client, app_token)
    
    # 5. 系统备份
    print(f"\n{Color.HEADER}💾 开始系统自动备份...{Color.ENDC}")
    backup_system_data()
    
    # 6. 生成日结报告
    report_file = f"日结报告_{datetime.now().strftime('%Y%m%d')}.txt"
    try:
        with open(report_file, "w", encoding="utf-8") as f:
            f.write(f"=== 飞书财务助手日结报告 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} ===\n\n")
            f.write("【今日工作事项】\n")
            if not summary:
                f.write("无处理事项\n")
            for s in summary:
                f.write(f"- {s}\n")
            f.write("\n")
            f.write("\n".join(daily_log))
            f.write("\n\n(本报告由飞书财务助手自动生成)")
            
        print(f"\n{Color.GREEN}========================================{Color.ENDC}")
        print(f"{Color.GREEN}🎉 日结完成！报告已生成: {report_file}{Color.ENDC}")
        print(f"{Color.GREEN}========================================{Color.ENDC}")
        os.startfile(report_file)
    except Exception as e:
        log.error(f"生成报告失败: {e}")
    
    print(f"\n{Color.GREEN}✅ 一键流程全部完成！{Color.ENDC}")

def interactive_menu():
    """Python版交互主菜单"""
    # 启用 Windows ANSI 支持 (如果是 Windows)
    if os.name == 'nt':
        os.system('color')
        
    while True:
        # 清屏 (兼容 Windows/Linux)
        os.system('cls' if os.name == 'nt' else 'clear')
        
        print(f"{Color.HEADER}===============================================")
        print(f"       🚀 飞书财务小助手 V9.6 - 旗舰版")
        print(f"==============================================={Color.ENDC}")
        
        print(f"\n{Color.CYAN}📝 记账录入{Color.ENDC}")
        print("  00. 🚀 一键日结 (自动处理+税务+体检+备份) [推荐]")
        print("  1. 智能截图记账 (OCR + AI)")
        print("  2. 智能文本记账 (微信/自然语言)")
        print("  3. 从 Excel 导入数据")
        
        print(f"\n{Color.CYAN}🏦 银行与对账{Color.ENDC}")
        print("  4. 银行流水对账 (自动勾兑)")
        print("  5. 生成往来对账单 (给客户/供应商)")
        print("  6. 查找待补票记录")
        
        print(f"\n{Color.CYAN}📊 报表与分析{Color.ENDC}")
        print("  7. 生成可视化报表 (HTML)")
        print("  8. 每日经营简报 (老板看板)")
        print("  9. 财务体检 (风险扫描)")
        print("  10. 智能查数助手 (AI 问答)")
        
        print(f"\n{Color.CYAN}⚙️ 结账与设置{Color.ENDC}")
        print("  11. 月度结账 (归档/利润表)")
        print("  12. 计提固定资产折旧 [新]")
        print("  13. 税务统计")
        print("  14. 往来单位别名管理")
        print("  15. 系统设置 (税率/AI Key)")
        print("  16. 导出标准凭证 (财务软件用) [新]")
        print("  17. 智能学习分类规则 (越用越聪明) [新]")
        print("  18. 快速查账 (关键词搜索) [新]")
        print("  19. 导出云端数据到 Excel [备份]")
        print("  20. 启动文件夹监听模式 (支持Excel/图片) [新]")
        
        print(f"\n{Color.CYAN}🛠️ 系统工具{Color.ENDC}")
        print("  95. 设置每日自动运行 (Windows任务) [新]")
        print("  96. 从备份恢复数据 [新]")
        print("  97. 初始化飞书表格 (首次)")
        print("  98. 备份系统数据 (配置+Excel)")
        print("  99. 显示云端后台链接")
        print("  0. 退出")
        print(f"{Color.HEADER}==============================================={Color.ENDC}")
        
        choice = input(f"\n👉 {Color.BOLD}请选择功能 (输入数字): {Color.ENDC}").strip()
        
        # 处理选择
        if choice == '0':
            print("👋 再见！")
            sys.exit(0)
        
        # [无需联网的功能优先处理]
        if choice == '95': 
            setup_auto_task()
            input("\n✅ 操作完成，按回车返回...")
            continue
        elif choice == '96': 
            restore_from_backup()
            input("\n✅ 操作完成，按回车返回...")
            continue
        elif choice == '98': 
            backup_system_data()
            input("\n✅ 操作完成，按回车返回...")
            continue
            
        # 懒加载 client，避免启动太慢
        global client, APP_TOKEN
        if 'client' not in globals() or not client:
             print(f"{Color.WARNING}🔄 正在连接飞书云端...{Color.ENDC}")
             client = init_clients()
             if not client: 
                 input(f"{Color.FAIL}❌ 初始化失败，按回车退出...{Color.ENDC}")
                 sys.exit(1)
                 
        if choice == '00': one_click_daily_closing(client, APP_TOKEN)
        elif choice == '1': smart_image_entry(client, APP_TOKEN)
        elif choice == '2': smart_text_entry(client, APP_TOKEN)
        elif choice == '3': 
             import_from_excel(client, APP_TOKEN, None)
             
        elif choice == '4': 
             reconcile_bank_flow(client, APP_TOKEN, None)
             
        elif choice == '5': generate_partner_statement(client, APP_TOKEN)
        elif choice == '6': export_missing_tickets(client, APP_TOKEN)
        
        elif choice == '7': generate_html_report(client, APP_TOKEN)
        elif choice == '8': daily_briefing(client, APP_TOKEN)
        elif choice == '9': financial_health_check(client, APP_TOKEN)
        elif choice == '10': ai_data_query(client, APP_TOKEN)
        
        elif choice == '11': monthly_close(client, APP_TOKEN)
        elif choice == '12': calculate_depreciation(client, APP_TOKEN)
        elif choice == '13': calculate_tax(client, APP_TOKEN)
        elif choice == '14': manage_aliases()
        elif choice == '15': settings_menu()
        elif choice == '16': export_standard_voucher(client, APP_TOKEN)
        elif choice == '17': learn_category_rules(client, APP_TOKEN)
        elif choice == '18': quick_search_records(client, APP_TOKEN)
        elif choice == '19': export_to_excel(client, APP_TOKEN)
        elif choice == '20': monitor_folder_mode(client, APP_TOKEN)
        
        elif choice == '97': 
             print(f"{Color.WARNING}⚠️  警告: 初始化将创建新表格。{Color.ENDC}")
             if input("确认初始化吗? (y/n): ").strip().lower() == 'y':
                 create_basic_info_table(client, APP_TOKEN)
                 create_ledger_table(client, APP_TOKEN)
                 create_partner_table(client, APP_TOKEN)
                 create_invoice_table(client, APP_TOKEN)
                 create_asset_table(client, APP_TOKEN)
                 print(f"{Color.GREEN}✅ 初始化完成！{Color.ENDC}")
             
        elif choice == '99': show_cloud_urls(client, APP_TOKEN)
        
        else:
            print(f"{Color.FAIL}❌ 无效选项{Color.ENDC}")
            
        input("\n✅ 操作完成，按回车返回主菜单...")

# 菜单：设置
def settings_menu():
    """系统设置菜单"""
    global TAX_RATE, ZHIPU_API_KEY
    
    while True:
        print(f"\n{Color.CYAN}⚙️ 系统设置{Color.ENDC}")
        print(f"  1. 设置税率 (当前: {TAX_RATE}%)")
        print(f"  2. 设置智谱AI Key (当前: {ZHIPU_API_KEY[:6]}******)")
        print("  0. 返回")
        
        choice = input("请选择: ").strip()
        
        if choice == '0':
            break
        elif choice == '1':
            try:
                new_rate = float(input("请输入新税率 (例如 1, 3, 6, 13): "))
                TAX_RATE = new_rate
                # Update .env
                update_env_key("TAX_RATE", str(TAX_RATE))
                print("✅ 税率已更新")
            except:
                print("❌ 输入无效")
        elif choice == '2':
            key = input("请输入新的 API Key: ").strip()
            if key:
                ZHIPU_API_KEY = key
                update_env_key("ZHIPU_API_KEY", key)
                print("✅ Key 已更新")
        else:
            print("❌ 无效选项")

def update_env_key(key, value):
    """更新 .env 文件"""
    lines = []
    if os.path.exists(".env"):
        try:
            with open(".env", "r", encoding="utf-8") as f:
                lines = f.readlines()
        except:
            pass
            
    new_lines = []
    found = False
    for line in lines:
        if line.strip().startswith(f"{key}="):
            new_lines.append(f"{key}={value}\n")
            found = True
        else:
            new_lines.append(line)
            
    if not found:
        if new_lines and not new_lines[-1].endswith('\n'):
             new_lines.append('\n')
        new_lines.append(f"{key}={value}\n")
        
    try:
        with open(".env", "w", encoding="utf-8") as f:
            f.writelines(new_lines)
    except Exception as e:
        print(f"❌ 保存配置失败: {e}")

def financial_health_check(client, app_token):
    """一键财务体检：扫描税务风险和数据异常 (生成HTML报告)"""
    log.info("🏥 正在进行财务体检...", extra={"solution": "全面扫描中"})
    
    table_id = get_table_id_by_name(client, app_token, "日常台账表")
    if not table_id:
        log.error("❌ 找不到日常台账表", extra={"solution": "请先初始化表格"})
        return

    records = get_all_records(client, app_token, table_id)
    
    risks = []
    stats = {
        "total_count": len(records),
        "cash_txns": 0,
        "no_ticket_amt": 0.0,
        "large_cash": 0
    }
    
    print("\n📋 体检报告")
    print("-" * 40)
    
    # 风险详情列表 (用于生成报告)
    risk_details = []
    seen_txns = {} # 用于查重 (key: date_amt_partner)
    
    # [新增] 可修复的异常
    duplicate_ids = [] # 待删除的重复记录ID
    has_depreciation = False # 本月是否有折旧

    for r in records:
        f = r.fields
        amt = float(f.get("实际收付金额", 0))
        is_cash = f.get("是否现金", "否") == "是"
        has_ticket = f.get("是否有票", "有票") == "无票"
        biz_type = f.get("业务类型", "")
        expense_type = f.get("费用类型", "")
        remark = f.get("备注") or ""
        partner = f.get("往来单位费用") or ""
        date_ts = f.get("记账日期", 0)
        try:
            date_str = datetime.fromtimestamp(date_ts/1000).strftime("%Y-%m-%d")
        except:
            date_str = "未知日期"
            
        # 检查是否已计提折旧
        if "折旧" in expense_type:
            has_depreciation = True
        
        # 统计
        if is_cash: stats["cash_txns"] += 1
        if has_ticket and biz_type in ["付款", "费用"]: stats["no_ticket_amt"] += amt
        
        # 规则 0: 重复录入检测 (新增)
        # 简单指纹: 日期 + 金额 + 对象 (忽略时分秒)
        # 注意: 只有非零金额才查重
        if amt != 0:
            dup_key = f"{date_str}_{amt}_{partner}"
            if dup_key in seen_txns:
                msg = f"⚠️ [重复风险] 疑似重复录入: {date_str} {amt}元 - {partner}"
                risks.append(msg)
                risk_details.append({"date": date_str, "type": "重复录入", "amt": amt, "desc": f"与已有记录重复: {partner}", "level": "高"})
                print(msg)
                
                # 收集重复记录ID (假设是后录入的为重复)
                rid = getattr(r, "record_id", None)
                if rid:
                    duplicate_ids.append(rid)
            else:
                seen_txns[dup_key] = True

        # 规则 1: 大额现金支付 (>5000)
        if is_cash and amt > 5000 and biz_type in ["付款", "费用"]:
            msg = f"⚠️ [高风险] 大额现金支出: {amt}元 ({remark})"
            risks.append(msg)
            risk_details.append({"date": date_str, "type": "大额现金", "amt": amt, "desc": remark, "level": "高"})
            print(msg)
            stats["large_cash"] += 1
            
        # 规则 2: 大额无票费用 (>1000)
        if has_ticket and amt > 1000 and biz_type == "费用":
            msg = f"⚠️ [税务风险] 大额无票费用: {amt}元 ({remark})"
            risks.append(msg)
            risk_details.append({"date": date_str, "type": "大额无票", "amt": amt, "desc": remark, "level": "中"})
            print(msg)
            
        # 规则 3: 摘要缺失
        if len(remark) < 2:
            print(f"ℹ️ [数据规范] 摘要过短或缺失: {amt}元")
            risk_details.append({"date": date_str, "type": "摘要缺失", "amt": amt, "desc": "摘要为空或过短", "level": "低"})

    # 规则 4: 本月折旧未计提
    current_month_str = datetime.now().strftime('%Y-%m')
    has_depreciation = False
    for r in records:
        f = r.fields
        # 检查是否为本月记录且费用类型为折旧摊销
        r_date = f.get("记账日期", 0)
        try:
            r_month = datetime.fromtimestamp(r_date/1000).strftime('%Y-%m')
        except:
            r_month = ""
            
        if r_month == current_month_str and f.get("费用类型") == "折旧摊销":
            has_depreciation = True
            break
            
    if not has_depreciation:
        msg = f"⚠️ [合规风险] 本月尚未计提固定资产折旧 ({current_month_str})"
        risks.append(msg)
        risk_details.append({"date": datetime.now().strftime("%Y-%m-%d"), "type": "折旧缺失", "amt": 0, "desc": "本月未计提折旧", "level": "中"})
        print(msg)

    print("-" * 40)
    print(f"扫描完成。共 {len(records)} 条记录。")
    print(f"大额现金笔数: {stats['large_cash']}")
    print(f"无票金额总计: {stats['no_ticket_amt']:.2f} 元")
    
    ai_advice = "暂无建议"
    
    # 如果有 AI，生成建议
    if zhipu_client and risks:
        try:
            log.info("🤖 AI 正在生成整改建议...", extra={"solution": "请稍候"})
            risk_text = "\n".join(risks[:10]) # 限制长度
            response = zhipu_client.chat.completions.create(
                model="glm-4-flash",
                messages=[
                    {"role": "system", "content": "你是一名资深税务会计。用户进行了一次财务体检，发现了以下风险点。请给出简短、专业的整改建议（3条以内，用HTML列表格式输出）。"},
                    {"role": "user", "content": risk_text}
                ]
            )
            ai_advice = response.choices[0].message.content
            print(f"\n💡 AI 建议生成完毕")
        except:
            pass
            
    # 生成 HTML 报告
    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <title>财务体检报告 - {datetime.now().strftime('%Y-%m-%d')}</title>
        <style>
            body {{ font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; background-color: #f4f6f9; margin: 0; padding: 20px; }}
            .container {{ max-width: 900px; margin: 0 auto; background: white; padding: 40px; border-radius: 10px; box-shadow: 0 4px 6px rgba(0,0,0,0.1); }}
            h1 {{ color: #2c3e50; border-bottom: 2px solid #e74c3c; padding-bottom: 10px; }}
            .stats {{ display: flex; justify-content: space-between; margin-bottom: 30px; }}
            .stat-box {{ background: #f8f9fa; padding: 20px; border-radius: 8px; text-align: center; width: 30%; }}
            .stat-val {{ font-size: 24px; font-weight: bold; color: #e74c3c; }}
            .risk-table {{ width: 100%; border-collapse: collapse; margin-top: 20px; }}
            th, td {{ border: 1px solid #ddd; padding: 12px; text-align: left; }}
            th {{ background-color: #e74c3c; color: white; }}
            tr:nth-child(even) {{ background-color: #f2f2f2; }}
            .tag {{ padding: 4px 8px; border-radius: 4px; color: white; font-size: 12px; }}
            .tag-high {{ background-color: #c0392b; }}
            .tag-mid {{ background-color: #e67e22; }}
            .tag-low {{ background-color: #f1c40f; color: #333; }}
            .ai-box {{ background-color: #e8f6f3; padding: 20px; border-left: 5px solid #1abc9c; margin-top: 30px; border-radius: 4px; }}
        </style>
    </head>
    <body>
        <div class="container">
            <h1>🏥 财务健康体检报告</h1>
            <p>生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
            
            <div class="stats">
                <div class="stat-box">
                    <div class="stat-val">{stats['large_cash']}</div>
                    <div>大额现金笔数 (>5k)</div>
                </div>
                <div class="stat-box">
                    <div class="stat-val">{stats['no_ticket_amt']:,.2f}</div>
                    <div>无票支出总额</div>
                </div>
                <div class="stat-box">
                    <div class="stat-val">{len(risk_details)}</div>
                    <div>发现风险点总数</div>
                </div>
            </div>

            <div class="ai-box">
                <h3>🤖 AI 整改建议</h3>
                {ai_advice}
            </div>

            <h3>⚠️ 风险详情清单</h3>
            <table class="risk-table">
                <thead>
                    <tr>
                        <th>风险等级</th>
                        <th>日期</th>
                        <th>类型</th>
                        <th>金额</th>
                        <th>说明</th>
                    </tr>
                </thead>
                <tbody>
    """
    
    for r in risk_details:
        tag_cls = "tag-low"
        if r['level'] == "高": tag_cls = "tag-high"
        elif r['level'] == "中": tag_cls = "tag-mid"
        
        html += f"""
        <tr>
            <td><span class="tag {tag_cls}">{r['level']}</span></td>
            <td>{r['date']}</td>
            <td>{r['type']}</td>
            <td>{r['amt']:,.2f}</td>
            <td>{r['desc']}</td>
        </tr>
        """
        
    html += """
                </tbody>
            </table>
        </div>
    </body>
    </html>
    """
    
    report_dir = "财务数据备份"
    if not os.path.exists(report_dir): os.makedirs(report_dir)
    filename = f"{report_dir}/体检报告_{datetime.now().strftime('%Y%m%d%H%M%S')}.html"
    
    with open(filename, "w", encoding="utf-8") as f:
        f.write(html)
        
    log.info(f"📄 体检报告已生成: {filename}", extra={"solution": "浏览器打开查看"})
    try:
        os.startfile(filename)
    except:
        pass
    
    # [新增] 交互式修复逻辑
    if duplicate_ids:
        print(f"\n🔧 [一键修复] 发现 {len(duplicate_ids)} 条重复记录。")
        if input("👉 是否立即删除这些重复项? (y/n): ").strip().lower() == 'y':
            print("🗑️ 正在删除重复记录...")
            try:
                # 批量删除
                req = BatchDeleteAppTableRecordRequest.builder() \
                    .app_token(app_token) \
                    .table_id(table_id) \
                    .request_body(BatchDeleteAppTableRecordRequestBody.builder().records(duplicate_ids).build()) \
                    .build()
                
                resp = client.bitable.v1.app_table_record.batch_delete(req)
                if resp.success():
                    print(f"✅ 已成功删除 {len(duplicate_ids)} 条重复记录！")
                else:
                    print(f"❌ 删除失败: {resp.msg}")
            except Exception as e:
                print(f"❌ 删除出错: {e}")
                
    if not has_depreciation and datetime.now().day > 20:
        print(f"\n🔧 [一键修复] 本月尚未计提折旧 (通常月底计提)。")
        if input("👉 是否立即运行折旧计算? (y/n): ").strip().lower() == 'y':
            calculate_depreciation(client, app_token)

    return True

# 菜单：设置
def settings_menu():
    print("\n⚙️  系统设置 (修改后自动保存到 .env)")
    print("-----------------------------------")
    print(f"1. 增值税率 (当前: {VAT_RATE}%)")
    print(f"2. 对账容差天数 (当前: {TOLERANCE_DAYS}天)")
    print(f"3. 智谱AI Key (当前: {ZHIPUAI_API_KEY[:8]}...)" if ZHIPUAI_API_KEY else "3. 智谱AI Key (当前: 未配置)")
    print("0. 返回主菜单")
    
    choice = input("\n请选择要修改的项 (0-3): ").strip()
    
    if choice == "1":
        val = input("请输入新的税率 (例如 3): ").strip()
        if val.isdigit():
            update_env("VAT_RATE", val)
            print("✅ 税率已更新")
        else:
            print("❌ 输入无效")
            
    elif choice == "2":
        val = input("请输入新的容差天数 (例如 2): ").strip()
        if val.isdigit():
            update_env("TOLERANCE_DAYS", val)
            print("✅ 容差天数已更新")
        else:
            print("❌ 输入无效")
            
    elif choice == "3":
        val = input("请输入智谱AI API Key: ").strip()
        if val:
            update_env("ZHIPUAI_API_KEY", val)
            print("✅ API Key 已更新")
    
    elif choice == "0":
        return

def update_env(key, value):
    # 读取现有内容
    lines = []
    if os.path.exists(".env"):
        with open(".env", "r", encoding="utf-8") as f:
            lines = f.readlines()
            
    # 更新或添加
    found = False
    new_lines = []
    for line in lines:
        if line.startswith(f"{key}="):
            new_lines.append(f"{key}={value}\n")
            found = True
        else:
            new_lines.append(line)
            
    if not found:
        new_lines.append(f"\n{key}={value}\n")
        
    with open(".env", "w", encoding="utf-8") as f:
        f.writelines(new_lines)
        
    # 重新加载变量 (简单方式: 告诉用户重启，或者尝试热加载)
    # 这里我们只做简单的全局变量更新，为了生效最好重启，但部分变量可以热更新
    global VAT_RATE, TOLERANCE_DAYS, ZHIPUAI_API_KEY
    if key == "VAT_RATE":
        VAT_RATE = float(value)
    elif key == "TOLERANCE_DAYS":
        TOLERANCE_DAYS = int(value)
    elif key == "ZHIPUAI_API_KEY":
        ZHIPUAI_API_KEY = value

# 主函数
def main():
    global ZHIPUAI_API_KEY
    import argparse
    parser = argparse.ArgumentParser(description="飞书财务小助手V8.8 (Lark OAPI V2)")
    parser.add_argument("--create-table", action="store_true", help="创建台账表格+填充测试数据")
    parser.add_argument("--import-excel", type=str, nargs='?', const="", help="从Excel导入数据（路径）")
    parser.add_argument("--export-excel", action="store_true", help="导出台账数据")
    parser.add_argument("--reconcile", type=str, nargs='?', const="", help="银行流水对账（Excel路径）")
    parser.add_argument("--calculate-tax", action="store_true", help="统计税务数据")
    parser.add_argument("--find-missing-ticket", action="store_true", help="查找待补票记录")
    parser.add_argument("--generate-report", action="store_true", help="生成HTML可视化报表")
    parser.add_argument("--monthly-close", action="store_true", help="一键月度结账")
    parser.add_argument("--daily-briefing", action="store_true", help="发送每日经营简报")
    parser.add_argument("--health-check", action="store_true", help="[新] 一键财务体检")
    parser.add_argument("--ai-chat", action="store_true", help="[新] AI 查数助手")
    parser.add_argument("--smart-entry", action="store_true", help="[新] 智能文本录入")
    parser.add_argument("--smart-image", action="store_true", help="[新] 智能截图记账")
    parser.add_argument("--learn-rules", action="store_true", help="[新] 智能学习分类规则")
    parser.add_argument("--partner-statement", action="store_true", help="[新] 生成往来对账单")
    parser.add_argument("--manage-aliases", action="store_true", help="[新] 管理往来单位别名")
    parser.add_argument("--show-urls", action="store_true", help="显示云端后台链接")
    parser.add_argument("--settings", action="store_true", help="进入设置菜单")
    parser.add_argument("--menu", action="store_true", help="进入交互式主菜单")
    parser.add_argument("--auto-run", action="store_true", help="[新] 自动运行每日任务(无交互)")
    args = parser.parse_args()

    # 如果没有参数，默认进入交互式菜单
    import sys
    if len(sys.argv) == 1:
        interactive_menu()
        return

    if args.auto_run:
        log.info("🤖 自动运行模式启动...")
        client = init_clients()
        if client:
            one_click_daily_closing(client, APP_TOKEN)
        return

    if args.menu:
        interactive_menu()
        return
        
    if args.settings:
        settings_menu()
        return

    client = init_clients()
    if not client:
        return

    # 自动引导配置
    if not APP_TOKEN:
        print("\n⚠️  检测到未配置 FEISHU_APP_TOKEN (Base Token)")
        token = input("请输入您的飞书多维表格 Token (通常在URL中): ").strip()
        if token:
            with open(".env", "a", encoding="utf-8") as f:
                f.write(f"\nFEISHU_APP_TOKEN={token}")
            log.info("✅ 配置已保存，请重新运行程序", extra={"solution": "重启"})
            return
        else:
            log.error("❌ 未配置 Token，程序退出", extra={"solution": "请在 .env 中配置"})
            return

    if args.create_table:
        # Create Tables
        log.info("🛠️ 正在初始化飞书多维表格结构...")
        create_basic_info_table(client, APP_TOKEN)
        create_ledger_table(client, APP_TOKEN)
        create_partner_table(client, APP_TOKEN) # 新增
        create_invoice_table(client, APP_TOKEN) # 新增
        create_asset_table(client, APP_TOKEN) # 新增
        print("✅ 所有表格初始化完成！")
        fill_test_data(client, APP_TOKEN)
        send_bot_message(f"✅ 表格初始化完成！Base: {APP_TOKEN}", "accountant")

    if args.import_excel is not None:
        import_from_excel(client, APP_TOKEN, args.import_excel)
        
    if args.reconcile is not None:
        reconcile_bank_flow(client, APP_TOKEN, args.reconcile)
        
    if args.calculate_tax:
        # 如果是新功能，检查API KEY
        if not ZHIPUAI_API_KEY:
            print("\n💡 提示：您尚未配置 ZHIPUAI_API_KEY，无法使用 AI 财务诊断。")
            key = input("请输入智谱AI Key (按回车跳过): ").strip()
            if key:
                with open(".env", "a", encoding="utf-8") as f:
                    f.write(f"\nZHIPUAI_API_KEY={key}")
                # 重新加载
                ZHIPUAI_API_KEY = key
                log.info("✅ AI Key 已保存", extra={"solution": "无"})
        calculate_tax(client, APP_TOKEN)
        
    if args.find_missing_ticket:
        export_missing_tickets(client, APP_TOKEN)
        
    if args.generate_report:
        generate_html_report(client, APP_TOKEN)
        
    if args.monthly_close:
        monthly_close(client, APP_TOKEN)
        
    if args.daily_briefing:
        daily_briefing(client, APP_TOKEN)

    if args.health_check:
        financial_health_check(client, APP_TOKEN)

    if args.ai_chat:
        ai_data_query(client, APP_TOKEN)

    if args.smart_entry:
        smart_text_entry(client, APP_TOKEN)

    if args.smart_image:
        smart_image_entry(client, APP_TOKEN)

    if args.learn_rules:
        learn_category_rules(client, APP_TOKEN)

    if args.partner_statement:
        generate_partner_statement(client, APP_TOKEN)

    if args.manage_aliases:
        manage_aliases()

    if args.show_urls:
        show_cloud_urls(client, APP_TOKEN)

    if args.export_excel:
        export_to_excel(client, APP_TOKEN)

if __name__ == "__main__":
    main()
