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
import itertools
import pandas as pd
import tkinter as tk
from tkinter import filedialog
from concurrent.futures import ThreadPoolExecutor, as_completed
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
    OKBLUE = '\033[94m'
    CYAN = '\033[96m'
    GREEN = '\033[92m'
    OKGREEN = '\033[92m'
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
class SolutionFormatter(logging.Formatter):
    def format(self, record):
        if not hasattr(record, 'solution'):
            record.solution = "无"
        return super().format(record)

file_handler = logging.FileHandler(LOG_FILE, encoding="utf-8")
stream_handler = logging.StreamHandler()

# 使用自定义Formatter
formatter = SolutionFormatter("%(asctime)s - %(levelname)s - %(message)s - 解决方案：%(solution)s")
file_handler.setFormatter(formatter)
stream_handler.setFormatter(formatter)

logging.basicConfig(
    level=logging.INFO,
    handlers=[file_handler, stream_handler],
    force=True # Ensure we override any existing config
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

        # 导入基础信息表
        with pd.ExcelFile(excel_path) as excel_file:
            if "基础信息表" in excel_file.sheet_names:
                table_id = get_table_id_by_name(client, app_token, "基础信息表")
                if table_id:
                    df = pd.read_excel(excel_file, sheet_name="基础信息表").fillna("")
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

                desc = str(row.get("往来单位费用", ""))
                
                # 优化：解析别名
                resolved_desc = resolve_partner(desc)
                
                # 如果户名列无效，尝试从摘要列匹配别名
                if resolved_desc == desc:
                    memo = str(row.get("备注", ""))
                    memo_resolved = resolve_partner(memo)
                    if memo_resolved != memo:
                        resolved_desc = memo_resolved
                
                desc = resolved_desc
                if not desc or desc == "nan" or desc == "未知" or desc == "":
                    desc = "散户" # 默认

                # 尝试自动分类补全 (费用归类)
                category = str(row.get("费用归类", ""))
                if not category or category == "nan" or category == "未知" or category == "":
                    memo = str(row.get("备注", ""))
                    category = auto_categorize(memo, "其他", partner_name=desc)
                    
                fields = {
                    "记账日期": ts,
                    "凭证号": int(row.get("凭证号", 0)) if str(row.get("凭证号", "")).strip() != "" else 0,
                    "业务类型": r_type,
                    "费用归类": category,
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
        with pd.ExcelFile(file_path) as xl:
            # 优先读 '日常台账表'，否则读第一个 Sheet
            sheet_name = "日常台账表" if "日常台账表" in xl.sheet_names else xl.sheet_names[0]
            
            # 先读前 20 行来找表头
            df_preview = pd.read_excel(xl, sheet_name=sheet_name, header=None, nrows=20)
            
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
            df = pd.read_excel(xl, sheet_name=sheet_name, header=header_row_idx)
        
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
AI_CACHE_FILE = "ai_category_cache.json"
AI_CACHE_MAP = {}
AI_CACHE_LOADED = False

def load_ai_cache():
    """加载本地AI分类缓存"""
    global AI_CACHE_MAP, AI_CACHE_LOADED
    if os.path.exists(AI_CACHE_FILE):
        try:
            with open(AI_CACHE_FILE, "r", encoding="utf-8") as f:
                AI_CACHE_MAP = json.load(f)
            log.info(f"🧠 已加载 {len(AI_CACHE_MAP)} 条AI分类缓存", extra={"solution": "无"})
        except Exception as e:
            log.warning(f"⚠️ 加载AI缓存失败: {e}", extra={"solution": "无"})
            AI_CACHE_MAP = {}
    AI_CACHE_LOADED = True

def save_ai_cache():
    """保存AI分类缓存到本地"""
    try:
        with open(AI_CACHE_FILE, "w", encoding="utf-8") as f:
            json.dump(AI_CACHE_MAP, f, ensure_ascii=False, indent=2)
    except Exception as e:
        log.warning(f"⚠️ 保存AI缓存失败: {e}")

def load_history_knowledge(client, app_token):
    """从飞书加载最近的历史分类习惯 (智能记忆)"""
    global HISTORY_CATEGORY_MAP
    HISTORY_CATEGORY_MAP = {}
    
    # 同时加载AI缓存
    load_ai_cache()
    
    table_id = get_table_id_by_name(client, app_token, "日常台账表")
    if not table_id: return
    
    # 获取最近2000条记录
    log.info("🧠 正在学习历史分类习惯...", extra={"solution": "无"})
    records = get_all_records(client, app_token, table_id, field_names=["备注", "往来单位费用", "费用归类"])
    
    # 倒序遍历，越新的越优先
    for r in reversed(records):
        f = r.fields
        memo = str(f.get("备注") or "").strip()
        partner = str(f.get("往来单位费用") or "").strip()
        cat = str(f.get("费用归类") or "").strip()
        
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
    global AUTO_CATEGORY_RULES, HISTORY_CATEGORY_MAP, AI_CACHE_LOADED
    
    # 确保AI缓存已加载
    if not AI_CACHE_LOADED:
        load_ai_cache()
    
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
            
    # 2.3 [V9.5新特性] 匹配本地AI缓存 (Smart Cache)
    # 避免重复调用AI接口，节省Token并提升速度
    cache_key = f"{desc_str}|{str(partner_name).lower()}"
    if cache_key in AI_CACHE_MAP:
        # print(f"   🧠 命中本地AI缓存: {cache_key[:20]}... -> {AI_CACHE_MAP[cache_key]}")
        return AI_CACHE_MAP[cache_key]
            
    # 3. [V9.4新特性] 尝试 AI 智能推断
    # 只有当描述足够长(>2)或有明确往来单位时才调用，避免浪费 Token
    if (len(desc_str) > 2 or partner_name) and ZHIPUAI_API_KEY:
        ai_cat = ai_guess_category(description, partner_name)
        if ai_cat:
            print(f"   🧠 AI 智能推断: '{description}' -> [{ai_cat}]")
            # 更新缓存
            AI_CACHE_MAP[cache_key] = ai_cat
            save_ai_cache()
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

        # 尝试自动分类补全 (费用归类)
        category = str(r.get("费用归类", ""))
        if not category or category == "nan" or category == "未知" or category == "":
            category = auto_categorize(r.get("备注", ""), "其他", partner_name=r.get("往来单位费用", ""))

        fields = {
            "记账日期": ts,
            "凭证号": 0, # 默认为0
            "业务类型": r["业务类型"],
            "费用归类": category,
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

def generate_reconciliation_report(matched_count, unmatched_list, ledger_unmatched_list=None):
    """生成对账结果可视化报告 (包含双向差异)"""
    if ledger_unmatched_list is None: ledger_unmatched_list = []
    
    total_bank = matched_count + len(unmatched_list)
    total_ledger_issues = len(ledger_unmatched_list)
    
    if total_bank == 0 and total_ledger_issues == 0: return
    
    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <title>银行对账报告 - {datetime.now().strftime('%Y-%m-%d')}</title>
        <script src="https://cdn.jsdelivr.net/npm/echarts@5.4.3/dist/echarts.min.js"></script>
        <style>
            body {{ font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; background-color: #f4f6f9; margin: 0; padding: 20px; }}
            .container {{ max-width: 1200px; margin: 0 auto; background: white; padding: 30px; border-radius: 10px; box-shadow: 0 4px 6px rgba(0,0,0,0.1); }}
            h1 {{ color: #2c3e50; text-align: center; border-bottom: 2px solid #3498db; padding-bottom: 10px; }}
            .summary {{ display: flex; justify-content: space-around; margin: 30px 0; }}
            .card {{ text-align: center; padding: 20px; background: #f8f9fa; border-radius: 8px; width: 22%; }}
            .number {{ font-size: 24px; font-weight: bold; color: #2c3e50; }}
            .chart-row {{ display: flex; justify-content: space-between; height: 400px; margin: 20px 0; }}
            .chart-box {{ width: 48%; height: 100%; }}
            table {{ width: 100%; border-collapse: collapse; margin-top: 20px; font-size: 14px; }}
            th, td {{ border: 1px solid #ddd; padding: 12px; text-align: left; }}
            th {{ background-color: #3498db; color: white; }}
            tr:nth-child(even) {{ background-color: #f2f2f2; }}
            .badge {{ padding: 5px 10px; border-radius: 4px; font-size: 12px; }}
            .badge-danger {{ background-color: #e74c3c; color: white; }}
            .badge-warning {{ background-color: #f39c12; color: white; }}
            .section-title {{ margin-top: 40px; color: #2c3e50; border-left: 5px solid #3498db; padding-left: 10px; }}
        </style>
    </head>
    <body>
        <div class="container">
            <h1>🏦 银行对账报告</h1>
            <p style="text-align: center; color: #7f8c8d;">生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
            
            <div class="summary">
                <div class="card">
                    <div class="number" style="color: #3498db;">{total_bank}</div>
                    <div>银行流水总数</div>
                </div>
                <div class="card">
                    <div class="number" style="color: #27ae60;">{matched_count}</div>
                    <div>✅ 自动匹配成功</div>
                </div>
                <div class="card">
                    <div class="number" style="color: #e74c3c;">{len(unmatched_list)}</div>
                    <div>❌ 银行有而台账无</div>
                </div>
                <div class="card">
                    <div class="number" style="color: #f39c12;">{len(ledger_unmatched_list)}</div>
                    <div>❓ 台账有而银行无</div>
                </div>
            </div>

            <div class="chart-row">
                <div id="pie-chart" class="chart-box"></div>
                <div id="bar-chart" class="chart-box"></div>
            </div>

            <h3 class="section-title">❌ 异常类型一：银行流水有，但台账未记录 ({len(unmatched_list)}条)</h3>
            <p style="color: #7f8c8d; font-size: 14px;">👉 建议：检查是否漏记，可使用"待补录流水.xlsx"直接导入</p>
            <table>
                <thead>
                    <tr>
                        <th>日期</th>
                        <th>摘要</th>
                        <th>金额</th>
                        <th>对象</th>
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
                        <td>{item.get('费用归类')}</td>
                        <td><span class="badge badge-danger">{item.get('原因')}</span></td>
                    </tr>
        """
        
    html += f"""
                </tbody>
            </table>

            <h3 class="section-title">❓ 异常类型二：台账已记，但银行流水无 ({len(ledger_unmatched_list)}条)</h3>
            <p style="color: #7f8c8d; font-size: 14px;">👉 建议：检查是否多记、重复记账、日期偏差过大(>2天)或银行选错</p>
            <table>
                <thead>
                    <tr>
                        <th>日期</th>
                        <th>摘要</th>
                        <th>金额</th>
                        <th>往来对象</th>
                        <th>登记银行</th>
                        <th>原因</th>
                    </tr>
                </thead>
                <tbody>
    """

    for item in ledger_unmatched_list:
        html += f"""
                    <tr>
                        <td>{item.get('记账日期')}</td>
                        <td>{item.get('摘要')}</td>
                        <td>{item.get('金额')}</td>
                        <td>{item.get('往来')}</td>
                        <td>{item.get('交易银行')}</td>
                        <td><span class="badge badge-warning">{item.get('原因')}</span></td>
                    </tr>
        """

    html += f"""
                </tbody>
            </table>
            
            <script>
                var chartDom = document.getElementById('pie-chart');
                var myChart = echarts.init(chartDom);
                var option = {{
                    title: {{ text: '银行流水匹配情况', left: 'center' }},
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
                                {{ value: {len(unmatched_list)}, name: '银行未入账', itemStyle: {{ color: '#e74c3c' }} }}
                            ]
                        }}
                    ]
                }};
                myChart.setOption(option);
                
                var barDom = document.getElementById('bar-chart');
                var barChart = echarts.init(barDom);
                var barOption = {{
                    title: {{ text: '双向差异概览', left: 'center' }},
                    tooltip: {{ trigger: 'axis', axisPointer: {{ type: 'shadow' }} }},
                    grid: {{ left: '3%', right: '4%', bottom: '3%', containLabel: true }},
                    xAxis: [ {{ type: 'category', data: ['银行有台账无', '台账有银行无'], axisTick: {{ alignWithLabel: true }} }} ],
                    yAxis: [ {{ type: 'value' }} ],
                    series: [
                        {{
                            name: '笔数',
                            type: 'bar',
                            barWidth: '60%',
                            data: [
                                {{ value: {len(unmatched_list)}, itemStyle: {{ color: '#e74c3c' }} }},
                                {{ value: {len(ledger_unmatched_list)}, itemStyle: {{ color: '#f39c12' }} }}
                            ]
                        }}
                    ]
                }};
                barChart.setOption(barOption);
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
            category = auto_categorize(cleaned_memo, "其他", partner_name=cleaned_desc) 
            
            # 如果自动分类返回默认值，尝试单独匹配 cleaned_desc
            if category == "其他":
                 category = auto_categorize(cleaned_desc, "其他", partner_name=cleaned_desc)
            
            unmatched.append({
                "记账日期": b_date.strftime("%Y-%m-%d"),
                "凭证号": "",
                "业务类型": "付款" if b_amount < 0 else "收款",
                "费用归类": category,
                "往来单位费用": cleaned_desc,
                "实际收付金额": b_amount,
                "交易银行": bank_name,
                "是否现金": is_cash,
                "是否有票": default_ticket,
                "待补票标记": "否",
                "备注": f"流水导入: {memo}",
                "原因": "飞书无此金额或日期超2天"
            })
            
    # [新增] 反向对账：检查台账中有，但银行流水中没有的记录 (可能是多记、重复或日期错误)
    ledger_unmatched = []
    
    # 定义当前银行的关键词
    target_bank_keywords = []
    if bank_choice == "1":
        target_bank_keywords = ["G银行", "工行", "ICBC", "对公"]
    elif bank_choice == "2":
        target_bank_keywords = ["N银行", "微信", "现金", "私户"]
        
    for key, records_list in feishu_amount_map.items():
        for r in records_list:
            if not r["matched"]:
                # 检查该记录是否属于当前对账的银行
                r_bank = str(r["fields"].get("交易银行", "")).strip()
                
                # 如果台账里没写银行，默认不报错(避免误报)；或者如果用户希望严查，可以调整策略
                if not r_bank: continue
                
                is_target = False
                for k in target_bank_keywords:
                    if k in r_bank:
                        is_target = True
                        break
                        
                if is_target:
                    # 找到了属于该银行但未匹配流水的数据
                    f = r["fields"]
                    ledger_unmatched.append({
                        "记账日期": datetime.fromtimestamp(f.get("记账日期",0)/1000).strftime("%Y-%m-%d"),
                        "业务类型": f.get("业务类型",""),
                        "金额": f.get("实际收付金额",0),
                        "摘要": f.get("备注",""),
                        "往来": f.get("往来单位费用",""),
                        "交易银行": r_bank,
                        "原因": "台账有但流水无 (可能是多记、日期偏差大或金额不一致)"
                    })

    # 3. 输出结果
    msg = f"智能对账完成！\n✅ 自动匹配：{matched_count}笔\n❌ 银行流水未入账：{len(unmatched)}笔"
    if ledger_unmatched:
        msg += f"\n⚠️ 台账多余记录 (疑似错误)：{len(ledger_unmatched)}笔"
        
    log.info(msg, extra={"solution": "查看导出文件"})
    
    # 生成可视化报告
    generate_reconciliation_report(matched_count, unmatched, ledger_unmatched)

    # 导出 银行流水未入账
    if unmatched:
        res_df = pd.DataFrame(unmatched)
        # 确保列顺序符合导入要求
        cols = ["记账日期", "凭证号", "业务类型", "费用归类", "往来单位费用", "实际收付金额", 
                "交易银行", "是否现金", "是否有票", "待补票标记", "备注", "原因"]
        # 动态调整列，防止KeyError
        final_cols = [c for c in cols if c in res_df.columns]
        res_df = res_df[final_cols]
        
        res_path = f"待补录流水_{datetime.now().strftime('%Y%m%d%H%M%S')}.xlsx"
        res_df.to_excel(res_path, index=False, sheet_name="日常台账表") 
        log.info(f"📄 待补录清单已导出: {res_path}", extra={"solution": "检查后导入"})
        
    # 导出 台账多余记录
    if ledger_unmatched:
        l_df = pd.DataFrame(ledger_unmatched)
        l_path = f"台账异常记录_{datetime.now().strftime('%Y%m%d%H%M%S')}.xlsx"
        l_df.to_excel(l_path, index=False)
        log.warning(f"📄 发现台账异常记录 (流水中没有): {l_path}", extra={"solution": "请核对是否多记或日期错误"})

    if unmatched:
        # 新增：询问是否直接导入 (按实际发生)
        print(f"\n💡 发现 {len(unmatched)} 笔未匹配流水 (可能是新发生的收支)。")
        print("💡 小提示: 小企业通常付款/回款不一一对应，建议按'实际发生'直接导入。")
        import_choice = input("👉 是否直接将这些流水作为新账目导入飞书? (y/n) [推荐y]: ").strip().lower()
        if import_choice != 'n': 
            import_bank_records_to_feishu(client, app_token, unmatched)
            
    else:
        send_bot_message(f"{msg}\n🎉 账目完美平衡！", "reconcile")
        
    return True

# 往来对账 (导入外部账单核对)
@retry_on_failure(max_retries=2, delay=3)
def reconcile_partner_flow(client, app_token, partner_excel_path=None):
    log.info("🤝 开始往来对账流程...", extra={"solution": "无"})
    
    # 1. 获取外部账单文件
    if not partner_excel_path:
        partner_excel_path = select_file_interactively("*.xlsx", "请选择客户/供应商的对账单文件")
        
    if not partner_excel_path:
        log.warning("⚠️ 未选择文件，操作取消", extra={"solution": "无"})
        return False
        
    # 2. 读取外部账单
    try:
        df = read_excel_smart(partner_excel_path)
        if df.empty:
            log.error("❌ 文件为空或无法识别", extra={"solution": "检查文件内容"})
            return False
            
        # 尝试从文件名猜测往来单位
        filename = os.path.basename(partner_excel_path)
        guessed_partner = filename.split('.')[0].replace("对账单", "").replace("往来", "").strip()
        
        print(f"\n🏢 识别到的往来单位: {Color.BOLD}{guessed_partner}{Color.ENDC}")
        partner_name = input(f"👉 确认往来单位名称 (回车默认, 或输入新名称): ").strip()
        if not partner_name:
            partner_name = guessed_partner
            
        log.info(f"✅ 当前对账对象: {partner_name}", extra={"solution": "无"})
        
        # 识别关键列
        # 我们需要: 日期, 金额 (正负代表方向), 摘要
        # read_excel_smart 已经尽力标准化了 '记账日期', '实际收付金额', '摘要'
        if "记账日期" not in df.columns or "实际收付金额" not in df.columns:
            log.error("❌ 无法识别必要的列 (日期/金额)", extra={"solution": "请确保表头包含 '日期' 和 '金额' 相关字样"})
            return False
            
    except Exception as e:
        log.error(f"❌ 读取文件失败: {e}", extra={"solution": "检查文件格式"})
        return False

    # 3. 拉取系统内部数据 (按往来单位过滤)
    table_id = get_table_id_by_name(client, app_token, "日常台账表")
    if not table_id: return False
    
    # 构造日期范围过滤器 (为了性能)
    try:
        dates = pd.to_datetime(df["记账日期"])
        min_ts = int((dates.min() - timedelta(days=15)).timestamp() * 1000) # 放宽范围
        max_ts = int((dates.max() + timedelta(days=15)).timestamp() * 1000)
        
        # 组合过滤器: 日期范围 AND 往来单位包含
        # 注意: 飞书公式中字符串包含用 CurrentValue.[往来单位费用].contains("Name") ? 不, API filter syntax
        # 简单起见，先按日期拉取，内存过滤往来单位 (更稳健)
        filter_info = f'AND(CurrentValue.[记账日期]>={min_ts}, CurrentValue.[记账日期]<={max_ts})'
        
        log.info("📥 正在拉取系统内部账目...", extra={"solution": "无"})
        all_records = get_all_records(client, app_token, table_id, filter_info=filter_info)
        
        # 内存过滤往来单位 (支持模糊匹配)
        internal_records = []
        for r in all_records:
            f = r.fields
            p = str(f.get("往来单位费用", "")).strip()
            # 简单的包含关系检查
            if partner_name in p or p in partner_name:
                internal_records.append(r)
                
        log.info(f"✅ 系统内找到相关记录: {len(internal_records)} 条", extra={"solution": "无"})
        
    except Exception as e:
        log.error(f"❌ 数据拉取失败: {e}", extra={"solution": "检查网络"})
        return False
        
    # 4. 执行核心对账逻辑 (升级版: 模糊匹配 + 组合匹配)
    log.info("🔄 正在进行智能比对 (精准+模糊+组合)...", extra={"solution": "无"})
    
    # 构建内部数据池 (Flat List)
    internal_pool = []
    for i, r in enumerate(internal_records):
        f = r.fields
        try:
            amt = round(float(f.get("实际收付金额", 0)), 2)
            ts = f.get("记账日期", 0)
            date_obj = datetime.fromtimestamp(ts/1000)
            internal_pool.append({
                "record": r,
                "amount": amt,
                "date": date_obj,
                "matched": False,
                "match_type": None,
                "id": i
            })
        except:
            pass

    # 构建外部数据池
    external_pool = []
    for idx, row in df.iterrows():
        try:
            e_amt = round(float(row["实际收付金额"]), 2)
            e_date = pd.to_datetime(row["记账日期"])
            e_desc = str(row.get("摘要", "") or row.get("备注", ""))
            external_pool.append({
                "amount": e_amt,
                "date": e_date,
                "desc": e_desc,
                "matched": False,
                "match_type": None,
                "original_idx": idx
            })
        except:
            continue

    matched_count = 0
    fuzzy_count = 0
    combo_count = 0

    # --- Pass 1: 精准匹配 (金额一致 & 日期在容差内) ---
    for e_item in external_pool:
        if e_item['matched']: continue
        
        best_match = None
        min_day_diff = 999
        
        for i_item in internal_pool:
            if i_item['matched']: continue
            
            # 金额严格一致
            if abs(i_item['amount'] - e_item['amount']) < 0.01:
                day_diff = abs((i_item['date'] - e_item['date']).days)
                if day_diff <= TOLERANCE_DAYS:
                    if day_diff < min_day_diff:
                        min_day_diff = day_diff
                        best_match = i_item
        
        if best_match:
            e_item['matched'] = True
            e_item['match_type'] = "精准匹配"
            best_match['matched'] = True
            best_match['match_type'] = "精准匹配"
            matched_count += 1

    # --- Pass 2: 模糊金额匹配 (金额相差<=1元 & 日期在容差内) ---
    for e_item in external_pool:
        if e_item['matched']: continue
        
        best_match = None
        min_day_diff = 999
        
        for i_item in internal_pool:
            if i_item['matched']: continue
            
            diff = abs(i_item['amount'] - e_item['amount'])
            if 0.01 < diff <= 1.0: # 允许1元以内误差
                day_diff = abs((i_item['date'] - e_item['date']).days)
                if day_diff <= TOLERANCE_DAYS:
                    if day_diff < min_day_diff:
                        min_day_diff = day_diff
                        best_match = i_item
        
        if best_match:
            diff_val = best_match['amount'] - e_item['amount']
            e_item['matched'] = True
            e_item['match_type'] = f"模糊匹配 (差{diff_val:+.2f})"
            best_match['matched'] = True
            best_match['match_type'] = f"模糊匹配 (差{-diff_val:+.2f})"
            fuzzy_count += 1

    # --- Pass 3: 组合匹配 (1笔外部 vs 多笔内部) ---
    # 场景: 客户一次转账对应我们多笔发票/订单
    # 限制: 仅尝试未匹配的记录, 且组合数量限制在 2-3 笔以防性能问题
    
    # 筛选候选池 (仅保留日期接近的未匹配内部记录)
    for e_item in external_pool:
        if e_item['matched']: continue
        
        candidates = []
        for i_item in internal_pool:
            if not i_item['matched']:
                # 放宽日期限制给组合匹配
                day_diff = abs((i_item['date'] - e_item['date']).days)
                if day_diff <= TOLERANCE_DAYS + 5: 
                    candidates.append(i_item)
        
        if len(candidates) > 50: continue # 候选太多跳过组合尝试
        
        found_combo = False
        
        # 尝试 2 笔组合
        for i in range(len(candidates)):
            if found_combo: break
            for j in range(i+1, len(candidates)):
                s = candidates[i]['amount'] + candidates[j]['amount']
                if abs(s - e_item['amount']) < 0.05:
                    # 找到组合!
                    e_item['matched'] = True
                    e_item['match_type'] = "组合匹配 (2笔)"
                    candidates[i]['matched'] = True
                    candidates[i]['match_type'] = "组合成员"
                    candidates[j]['matched'] = True
                    candidates[j]['match_type'] = "组合成员"
                    combo_count += 1
                    found_combo = True
                    break
        
        # 尝试 3 笔组合 (仅当候选较少时)
        if not found_combo and len(candidates) < 20:
             for i in range(len(candidates)):
                if found_combo: break
                for j in range(i+1, len(candidates)):
                    for k in range(j+1, len(candidates)):
                        s = candidates[i]['amount'] + candidates[j]['amount'] + candidates[k]['amount']
                        if abs(s - e_item['amount']) < 0.05:
                            e_item['matched'] = True
                            e_item['match_type'] = "组合匹配 (3笔)"
                            candidates[i]['matched'] = True
                            candidates[i]['match_type'] = "组合成员"
                            candidates[j]['matched'] = True
                            candidates[j]['match_type'] = "组合成员"
                            candidates[k]['matched'] = True
                            candidates[k]['match_type'] = "组合成员"
                            combo_count += 1
                            found_combo = True
                            break

    # --- 结果汇总 ---
    internal_missing = [] # 漏记
    external_missing = [] # 多记
    
    for e_item in external_pool:
        if not e_item['matched']:
            internal_missing.append({
                "日期": e_item['date'].strftime("%Y-%m-%d"),
                "金额": e_item['amount'],
                "摘要": e_item['desc'],
                "原因": "我方缺失 (需补录)"
            })
            
    for i_item in internal_pool:
        if not i_item['matched']:
             f = i_item['record'].fields
             external_missing.append({
                "日期": i_item['date'].strftime("%Y-%m-%d"),
                "金额": i_item['amount'],
                "摘要": f.get("备注", "") or f.get("往来单位费用", ""),
                "原因": "我方多出 (对方无此记录)"
             })

    # 5. 输出结果
    total_ok = matched_count + fuzzy_count + combo_count
    print(f"\n{Color.HEADER}📊 对账结果摘要 ({partner_name}){Color.ENDC}")
    print(f"✅ 匹配成功: {total_ok} 笔 (精准: {matched_count}, 模糊: {fuzzy_count}, 组合: {combo_count})")
    print(f"❌ 我方缺失: {len(internal_missing)} 笔 (可能是漏记)")
    print(f"❓ 我方多出: {len(external_missing)} 笔 (可能是多记/对方漏记)")
    
    # 6. 生成差异报告 Excel
    if internal_missing or external_missing:
        report_data = []
        for item in internal_missing:
            item["类型"] = "漏记风险"
            report_data.append(item)
        for item in external_missing:
            item["类型"] = "多记风险"
            report_data.append(item)
            
        df_res = pd.DataFrame(report_data)
        out_file = f"往来对账差异_{partner_name}_{datetime.now().strftime('%Y%m%d')}.xlsx"
        
        # 简单美化 Excel (通过 pandas writer)
        try:
            with pd.ExcelWriter(out_file, engine='xlsxwriter') as writer:
                df_res.to_excel(writer, sheet_name='差异明细', index=False)
                workbook = writer.book
                worksheet = writer.sheets['差异明细']
                
                # 定义格式
                red_fmt = workbook.add_format({'font_color': '#9C0006', 'bg_color': '#FFC7CE'})
                yellow_fmt = workbook.add_format({'font_color': '#9C6500', 'bg_color': '#FFEB9C'})
                
                # 设置列宽
                worksheet.set_column('A:A', 12) # 日期
                worksheet.set_column('B:B', 12) # 金额
                worksheet.set_column('C:C', 30) # 摘要
                worksheet.set_column('D:D', 20) # 原因
                worksheet.set_column('E:E', 10) # 类型
                
                # 条件格式
                worksheet.conditional_format('E2:E1000', {'type': 'text',
                                                        'criteria': 'containing',
                                                        'value': '漏记',
                                                        'format': red_fmt})
                worksheet.conditional_format('E2:E1000', {'type': 'text',
                                                        'criteria': 'containing',
                                                        'value': '多记',
                                                        'format': yellow_fmt})
        except:
            # Fallback if xlsxwriter not available
            df_res.to_excel(out_file, index=False)
            
        log.info(f"📄 差异报告已生成: {out_file}", extra={"solution": "请打开Excel查看详情"})
        
        try:
            os.startfile(out_file)
        except:
            pass
            
        # 7. 交互式补录询问
        if internal_missing:
            print(f"\n🔧 发现 {len(internal_missing)} 笔漏记记录。")
            if input("👉 是否将这些记录自动补录到台账? (y/n): ").strip().lower() == 'y':
                # 转换格式适配 import_bank_records_to_feishu 或直接写入
                to_import = []
                for item in internal_missing:
                    # 构造导入所需的字典格式
                    # 需要: 记账日期, 实际收付金额, 往来单位费用, 业务类型, 费用归类
                    
                    # 简单推断业务类型
                    b_type = "付款" if item["金额"] < 0 else "收款"
                    
                    to_import.append({
                        "记账日期": item["日期"],
                        "实际收付金额": item["金额"],
                        "往来单位费用": partner_name,
                        "摘要": item["摘要"],
                        "业务类型": b_type,
                        "费用归类": "待确认", # 暂时设为待确认
                        "交易银行": "未指定",
                        "是否现金": "否",
                        "是否有票": "有票",
                        "备注": f"对账补录: {item['摘要']}"
                    })
                
                # 调用现有的导入逻辑
                batch_add_records(client, app_token, table_id, to_import)

    else:
        print(f"\n{Color.GREEN}🎉 完美匹配！双方账目一致。{Color.ENDC}")
        
    return True

def batch_add_records(client, app_token, table_id, data_list):
    """批量写入记录辅助函数"""
    records = []
    for item in data_list:
        fields = {
            "记账日期": int(pd.to_datetime(item["记账日期"]).timestamp() * 1000),
            "实际收付金额": float(item["实际收付金额"]),
            "往来单位费用": str(item["往来单位费用"]),
            "业务类型": str(item["业务类型"]),
            "费用归类": str(item["费用归类"]),
            "备注": str(item["备注"])
        }
        records.append(AppTableRecord.builder().fields(fields).build())
        
    # 分批写入
    batch_size = 100
    for i in range(0, len(records), batch_size):
        batch = records[i:i+batch_size]
        req = BatchCreateAppTableRecordRequest.builder() \
            .app_token(app_token) \
            .table_id(table_id) \
            .request_body(BatchCreateAppTableRecordRequestBody.builder().records(batch).build()) \
            .build()
            
        resp = client.bitable.v1.app_table_record.batch_create(req)
        if resp.success():
            log.info(f"✅ 已补录 {len(batch)} 条记录", extra={"solution": "无"})
        else:
            log.error(f"❌ 补录失败: {resp.msg}", extra={"solution": "检查权限"})

# 薪酬管理流程 (新)
def manage_salary_flow(client, app_token):
    """薪酬管理流程：导入工资表、生成凭证"""
    while True:
        print(f"\n{Color.HEADER}💰 薪酬管理 (工资/个税/社保){Color.ENDC}")
        print("1. 导入工资表 (Excel)")
        print("2. 查看薪酬列表 (最近10条)")
        print("3. 生成记账凭证 (同步到台账)")
        print("4. 个税计算器 (实用工具) [New]")
        print("0. 返回主菜单")
        
        choice = input(f"{Color.OKBLUE}请选择功能 (0-4): {Color.ENDC}").strip()
        
        if choice == '0': break

        if choice == '4':
            print(f"\n{Color.CYAN}🧮 2024 个人所得税计算器 (月度综合所得){Color.ENDC}")
            try:
                salary = float(input("请输入税前工资: ") or 0)
                social = float(input("请输入社保公积金扣除(个人部分): ") or 0)
                special = float(input("请输入专项附加扣除(如租金/养老等): ") or 0)
                threshold = 5000 # 起征点
                
                taxable = salary - social - special - threshold
                tax = 0
                if taxable <= 0:
                    tax = 0
                elif taxable <= 3000:
                    tax = taxable * 0.03
                elif taxable <= 12000:
                    tax = taxable * 0.1 - 210
                elif taxable <= 25000:
                    tax = taxable * 0.2 - 1410
                elif taxable <= 35000:
                    tax = taxable * 0.25 - 2660
                elif taxable <= 55000:
                    tax = taxable * 0.3 - 4410
                elif taxable <= 80000:
                    tax = taxable * 0.35 - 7160
                else:
                    tax = taxable * 0.45 - 15160
                
                net_salary = salary - social - max(0, tax)
                
                print(f"\n{Color.BOLD}计算结果:{Color.ENDC}")
                print(f"应纳税所得额: {max(0, taxable):.2f} 元")
                print(f"预计个税:     {Color.FAIL}{max(0, tax):.2f} 元{Color.ENDC}")
                print(f"税后实发:     {Color.GREEN}{net_salary:.2f} 元{Color.ENDC}")
                
            except ValueError:
                print("❌ 输入格式错误，请输入数字")
            
            input("\n按回车继续...")
            continue
        
        if choice == '1':
            file_path = input(f"{Color.OKBLUE}请输入工资表Excel路径 (直接回车扫描当前目录): {Color.ENDC}").strip()
            if not file_path:
                candidates = [f for f in os.listdir('.') if '工资' in f and f.endswith('.xlsx')]
                if candidates:
                    file_path = candidates[0]
                    print(f"🔍 自动找到: {file_path}")
                else:
                    print(f"{Color.WARNING}⚠️ 未找到工资表，请手动输入路径{Color.ENDC}")
                    continue
            
            if not os.path.exists(file_path):
                print(f"{Color.FAIL}❌ 文件不存在{Color.ENDC}")
                continue

            try:
                df = pd.read_excel(file_path)
                month_input = input(f"{Color.OKBLUE}请输入归属月份 (YYYY-MM): {Color.ENDC}").strip()
                
                table_id = get_table_id_by_name(client, app_token, "薪酬管理表")
                if not table_id:
                    print(f"{Color.FAIL}❌ 薪酬管理表不存在{Color.ENDC}")
                    continue

                records = []
                for _, row in df.iterrows():
                    fields = {
                        "月份": month_input,
                        "姓名": str(row.get('姓名', '')),
                        "部门": str(row.get('部门', '')),
                        "实发工资": float(row.get('实发工资', 0) or 0),
                        "状态": "已发放"
                    }
                    if '基本工资' in row: fields["基本工资"] = float(row.get('基本工资', 0) or 0)
                    if '绩效工资' in row: fields["绩效工资"] = float(row.get('绩效工资', 0) or 0)
                    if '社保个人' in row: fields["社保扣除"] = float(row.get('社保个人', 0) or 0)
                    if '个税' in row: fields["个税扣除"] = float(row.get('个税', 0) or 0)
                    
                    records.append(AppTableRecord.builder().fields(fields).build())

                # Batch Write
                batch_size = 100
                total_success = 0
                for i in range(0, len(records), batch_size):
                    batch = records[i:i+batch_size]
                    req = BatchCreateAppTableRecordRequest.builder() \
                        .app_token(app_token) \
                        .table_id(table_id) \
                        .request_body(BatchCreateAppTableRecordRequestBody.builder().records(batch).build()) \
                        .build()
                    
                    resp = client.bitable.v1.app_table_record.batch_create(req)
                    if resp.success():
                        total_success += len(batch)
                    else:
                        print(f"{Color.FAIL}❌ 部分写入失败: {resp.msg}{Color.ENDC}")
                
                print(f"{Color.OKGREEN}✅ 成功导入 {total_success} 条薪酬记录 ({month_input}){Color.ENDC}")
                
                # Ask to generate accounting vouchers
                if input(f"{Color.OKBLUE}是否生成记账凭证(写入日常台账)? (y/n): {Color.ENDC}").lower() == 'y':
                    total_net = df["实发工资"].sum()
                    ledger_id = get_table_id_by_name(client, app_token, "日常台账表")
                    
                    print(f"{Color.WARNING}⚠️ 注意: 将生成【实发工资】的支出记录。个税和社保请在缴纳时通过银行流水导入。{Color.ENDC}")
                    
                    record_fields = {
                        "记账日期": int(datetime.now().timestamp() * 1000),
                        "实际收付金额": float(total_net),
                        "业务类型": "费用",
                        "费用归类": "工资薪金",
                        "摘要": f"{month_input} 工资发放 (共{len(df)}人)",
                        "交易银行": "待确认",
                        "是否有票": "无票",
                        "备注": "自动生成自薪酬管理"
                    }
                    
                    rec = AppTableRecord.builder().fields(record_fields).build()
                    req_l = BatchCreateAppTableRecordRequest.builder().app_token(app_token).table_id(ledger_id).request_body(
                        BatchCreateAppTableRecordRequestBody.builder().records([rec]).build()).build()
                    resp_l = client.bitable.v1.app_table_record.batch_create(req_l)
                    if resp_l.success():
                         print(f"{Color.OKGREEN}✅ 已生成支出凭证: {total_net} 元{Color.ENDC}")
                    else:
                         print(f"{Color.FAIL}❌ 生成凭证失败: {resp_l.msg}{Color.ENDC}")

            except Exception as e:
                log.error(f"操作失败: {e}")
                print(f"{Color.FAIL}❌ 操作失败: {e}{Color.ENDC}")
                
        elif choice == '2':
             table_id = get_table_id_by_name(client, app_token, "薪酬管理表")
             if not table_id:
                 print(f"{Color.WARNING}⚠️ 薪酬表不存在{Color.ENDC}")
                 continue
             records = get_all_records(client, app_token, table_id) # Should limit? get_all_records gets all.
             # Assuming get_all_records is efficient enough for now or we just take last 10
             if not records:
                 print("📭 暂无记录")
             else:
                 print(f"\n{Color.UNDERLINE}最近 10 条薪酬记录:{Color.ENDC}")
                 # Sort by creation? The API returns in some order.
                 # Just show last 10
                 for r in records[-10:]:
                     f = r.fields
                     print(f"- {f.get('月份')} | {f.get('姓名')} | 实发: {f.get('实发工资')} | 状态: {f.get('状态')}")
             
        elif choice == '3':
            month_input = input(f"{Color.OKBLUE}请输入月份 (YYYY-MM): {Color.ENDC}").strip()
            if len(month_input) != 7 or '-' not in month_input:
                print(f"{Color.WARNING}⚠️ 格式错误，请使用 YYYY-MM 格式{Color.ENDC}")
                continue

            table_id = get_table_id_by_name(client, app_token, "薪酬管理表")
            if not table_id:
                print(f"{Color.FAIL}❌ 未找到薪酬管理表{Color.ENDC}")
                continue

            # 查询该月记录
            filter_str = f'CurrentValue.[月份]="{month_input}"'
            print(f"🔍 正在查询 {month_input} 的薪酬记录...")
            records = get_all_records(client, app_token, table_id, filter_info=filter_str)

            if not records:
                print(f"{Color.WARNING}📭 {month_input} 暂无薪酬记录{Color.ENDC}")
                continue

            # 统计金额
            total_net = 0.0
            person_count = 0
            details_summary = []

            for r in records:
                f = r.fields
                try:
                    net = float(f.get("实发工资", 0))
                except:
                    net = 0.0
                
                total_net += net
                person_count += 1
                if len(details_summary) < 3:
                    details_summary.append(f"{f.get('姓名', '未知')}")

            print(f"\n{Color.OKGREEN}📊 {month_input} 薪酬统计概览:{Color.ENDC}")
            print(f"--------------------------------")
            print(f"👥 发放人数: {person_count} 人 ({', '.join(details_summary)}...)")
            print(f"💰 实发总额: {total_net:,.2f} 元")
            print(f"--------------------------------")

            if input(f"{Color.OKBLUE}❓ 确认生成记账凭证(同步到日常台账)? (y/n): {Color.ENDC}").lower() == 'y':
                ledger_id = get_table_id_by_name(client, app_token, "日常台账表")
                if not ledger_id:
                    print(f"{Color.FAIL}❌ 未找到日常台账表{Color.ENDC}")
                    continue

                record_fields = {
                    "记账日期": int(datetime.now().timestamp() * 1000),
                    "实际收付金额": float(total_net),
                    "业务类型": "费用",
                    "费用归类": "工资薪金",
                    "摘要": f"{month_input} 工资发放 (共{person_count}人)",
                    "交易银行": "待确认", 
                    "是否有票": "无票",
                    "备注": f"薪酬模块自动生成 - {datetime.now().strftime('%Y-%m-%d %H:%M')}"
                }

                rec = AppTableRecord.builder().fields(record_fields).build()
                req = BatchCreateAppTableRecordRequest.builder() \
                    .app_token(app_token) \
                    .table_id(ledger_id) \
                    .request_body(BatchCreateAppTableRecordRequestBody.builder().records([rec]).build()) \
                    .build()
                
                resp = client.bitable.v1.app_table_record.batch_create(req)
                
                if resp.success():
                    print(f"{Color.OKGREEN}✅ 凭证生成成功！已写入日常台账。{Color.ENDC}")
                else:
                    print(f"{Color.FAIL}❌ 生成凭证失败: {resp.msg}{Color.ENDC}")

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
def calculate_tax(client, app_token, target_year=None):
    if target_year:
        log.info(f"🧮 开始 {target_year}年度 税务及风险分析...", extra={"solution": "无"})
        year = target_year
    else:
        log.info("🧮 开始税务及风险分析...", extra={"solution": "无"})
        year = datetime.now().year
        
    table_id = get_table_id_by_name(client, app_token, "日常台账表")
    if not table_id:
        return False
        
    # 优化：只获取指定年度数据
    start_ts = int(datetime(year, 1, 1).timestamp() * 1000)
    end_ts = int(datetime(year + 1, 1, 1).timestamp() * 1000)
    filter_str = f'AND(CurrentValue.[记账日期]>={start_ts}, CurrentValue.[记账日期]<{end_ts})'
    
    log.info(f"🔍 正在拉取 {year} 年度数据...", extra={"solution": "无"})
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
        cols = ["记账日期", "凭证号", "费用归类", "往来单位费用", "实际收付金额", "是否有票", "待补票标记", "备注", "操作人"]
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
def generate_html_report(client, app_token, target_year=None):
    if target_year:
        log.info(f"📊 正在生成 {target_year}年度 可视化报表...", extra={"solution": "无"})
        year = target_year
    else:
        log.info("📊 正在生成可视化报表...", extra={"solution": "无"})
        year = datetime.now().year

    table_id = get_table_id_by_name(client, app_token, "日常台账表")
    if not table_id:
        return False
        
    # 获取指定年度数据
    start_ts = int(datetime(year, 1, 1).timestamp() * 1000)
    end_ts = int(datetime(year + 1, 1, 1).timestamp() * 1000)
    filter_str = f'AND(CurrentValue.[记账日期]>={start_ts}, CurrentValue.[记账日期]<{end_ts})'
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
            <h1>📊 {year}年度财务经营分析</h1>
            
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
def export_to_excel(client, app_token, target_path=None):
    """全量备份：导出所有数据表到 Excel"""
    log.info("💾 开始全量云端数据备份...", extra={"solution": "无"})
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    if target_path:
        backup_path = os.path.join(target_path, f"飞书台账全量备份_{timestamp}.xlsx")
    else:
        backup_path = os.path.join(LOCAL_FOLDER, f"飞书台账全量备份_{timestamp}.xlsx")
    
    try:
        # 1. 获取所有数据表
        tables = []
        page_token = None
        while True:
            req = ListAppTableRequest.builder() \
                .app_token(app_token) \
                .page_size(20) \
                .page_token(page_token) \
                .build()
            resp = client.bitable.v1.app_table.list(req)
            if resp.success():
                if resp.data.items:
                    tables.extend(resp.data.items)
                if not resp.data.has_more:
                    break
                page_token = resp.data.page_token
            else:
                log.error(f"无法获取表格列表: {resp.msg}")
                break

        if not tables:
            return False

        # 2. [V9.5新特性] 并行获取数据 (Parallel Backup)
        table_data_map = {}
        
        def fetch_table_data(table):
            t_name = table.name
            t_id = table.table_id
            try:
                # print(f"   ⏳ [并行] 正在拉取: {t_name}...") # 减少刷屏
                records = get_all_records(client, app_token, t_id)
                clean_data = []
                if records:
                    for r in records:
                        row = r.fields.copy()
                        # 转换时间戳
                        for k, v in row.items():
                            if isinstance(v, int) and v > 1000000000000: # 简单判断毫秒时间戳
                                try:
                                    row[k] = datetime.fromtimestamp(v / 1000).strftime("%Y-%m-%d %H:%M:%S")
                                except:
                                    pass
                        clean_data.append(row)
                return t_name, pd.DataFrame(clean_data)
            except Exception as e:
                log.error(f"❌ 获取表 {t_name} 失败: {e}")
                return t_name, pd.DataFrame()

        log.info(f"🚀 启动并行备份，正在同时拉取 {len(tables)} 张表...", extra={"solution": "无"})
        with ThreadPoolExecutor(max_workers=5) as executor:
            future_to_table = {executor.submit(fetch_table_data, t): t for t in tables}
            for future in as_completed(future_to_table):
                t_name, df = future.result()
                table_data_map[t_name] = df
                print(f"   ✅ 已就绪: {t_name} ({len(df)} 条)")

        # 3. 写入 Excel
        log.info("💾 正在写入Excel文件...", extra={"solution": "无"})
        with pd.ExcelWriter(backup_path) as writer:
            for table in tables: # 保持原有顺序
                table_name = table.name
                if table_name in table_data_map:
                    df = table_data_map[table_name]
                    # Excel Sheet 名字不能超过31个字符
                    safe_name = table_name[:30]
                    # 处理重名Sheet (极其罕见)
                    if safe_name in writer.sheets:
                        safe_name = (table_name[:25] + "_1")
                    
                    df.to_excel(writer, sheet_name=safe_name, index=False)
                else:
                    pd.DataFrame().to_excel(writer, sheet_name=table_name[:30])

        log.info(f"✅ 全量备份成功: {backup_path}", extra={"solution": "妥善保管"})
        if not target_path: # 如果是手动触发，发送通知
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
                        AppTableFieldPropertyOption.builder().name("外发加工").build(),
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

# 创建薪酬表 (新)
@retry_on_failure(max_retries=2, delay=3)
def create_salary_table(client, app_token):
    existing_id = get_table_id_by_name(client, app_token, "薪酬管理表")
    if existing_id:
        log.info(f"⚠️ 薪酬管理表已存在 (ID: {existing_id})", extra={"solution": "无"})
        return True, existing_id

    req = CreateAppTableRequest.builder() \
        .app_token(app_token) \
        .request_body(CreateAppTableRequestBody.builder()
            .table(ReqTable.builder()
                .name("薪酬管理表")
                .fields([
                    AppTableCreateHeader.builder().field_name("月份").type(FT.TEXT).build(), # YYYY-MM
                    AppTableCreateHeader.builder().field_name("姓名").type(FT.TEXT).build(),
                    AppTableCreateHeader.builder().field_name("基本工资").type(FT.NUMBER).build(),
                    AppTableCreateHeader.builder().field_name("绩效奖金").type(FT.NUMBER).build(),
                    AppTableCreateHeader.builder().field_name("社保扣款(个人)").type(FT.NUMBER).build(),
                    AppTableCreateHeader.builder().field_name("公积金扣款(个人)").type(FT.NUMBER).build(),
                    AppTableCreateHeader.builder().field_name("个税").type(FT.NUMBER).build(),
                    AppTableCreateHeader.builder().field_name("实发工资").type(FT.NUMBER).build(),
                    AppTableCreateHeader.builder().field_name("公司社保承担").type(FT.NUMBER).build(),
                    AppTableCreateHeader.builder().field_name("公司公积金承担").type(FT.NUMBER).build(),
                    AppTableCreateHeader.builder().field_name("发放日期").type(FT.DATE).build(),
                    AppTableCreateHeader.builder().field_name("状态").type(FT.SELECT).property(AppTableFieldProperty.builder().options([
                        AppTableFieldPropertyOption.builder().name("草稿").build(),
                        AppTableFieldPropertyOption.builder().name("已发放").build()
                    ]).build()).build(),
                    AppTableCreateHeader.builder().field_name("备注").type(FT.TEXT).build()
                ])
                .build())
            .build()) \
        .build()
    
    resp = client.bitable.v1.app_table.create(req)
    if resp.success():
        log.info("✅ 薪酬管理表创建成功", extra={"solution": "无"})
        return True, resp.data.table_id
    else:
        log.error(f"❌ 薪酬管理表创建失败: {resp.msg}", extra={"solution": "检查权限"})
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
                    AppTableCreateHeader.builder().field_name("费用归类").type(FT.SELECT).property(AppTableFieldProperty.builder().options([
                        AppTableFieldPropertyOption.builder().name("办公费").build(),
                        AppTableFieldPropertyOption.builder().name("差旅费").build(),
                        AppTableFieldPropertyOption.builder().name("房租水电").build(),
                        AppTableFieldPropertyOption.builder().name("人力成本").build(),
                        AppTableFieldPropertyOption.builder().name("营销推广").build(),
                        AppTableFieldPropertyOption.builder().name("采购成本").build(),
                        AppTableFieldPropertyOption.builder().name("税费").build(),
                        AppTableFieldPropertyOption.builder().name("其他").build()
                    ]).build()).build(),
                    AppTableCreateHeader.builder().field_name("关联项目").type(FT.TEXT).build(),
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
def monthly_close(client, app_token, ym_input=None):
    log.info("📅 开始月度结账流程...", extra={"solution": "无"})
    
    # 确定结账月份 (默认上个月)
    today = datetime.now()
    last_month_date = today.replace(day=1) - timedelta(days=1)
    default_ym = last_month_date.strftime("%Y%m")
    
    if ym_input:
        ym_str = ym_input
    else:
        print(f"\n{Color.YELLOW}💡 默认结账月份为上个月 ({default_ym}){Color.ENDC}")
        ym_str = input(f"请输入结账月份 (格式 YYYYMM, 直接回车使用默认值): ").strip()
    
    target_year = None
    target_month = None
    
    if not ym_str:
        target_year = last_month_date.year
        target_month = last_month_date.month
    else:
        try:
            if len(ym_str) == 4:
                target_year = int(ym_str)
                target_month = None
                print(f"🎯 选定结账年度: {target_year}年 (生成年度报表)")
            elif len(ym_str) == 6:
                target_year = int(ym_str[:4])
                target_month = int(ym_str[4:])
                print(f"🎯 选定结账月份: {target_year}年{target_month}月")
            else:
                raise ValueError("Length mismatch")
        except:
            print(f"❌ 格式错误，将处理当前年度所有数据")
            target_year = today.year

    # 1. 自动修复缺失分类
    print("\n[1/5] 正在检查并修复缺失分类...")
    auto_fix_missing_categories(client, app_token, target_year)
    
    # 2. 导出备份
    print("\n[2/5] 正在执行全量备份...")
    backup_ok = export_to_excel(client, app_token)
    
    # 3. 生成报表
    print("\n[3/5] 正在生成分析报表...")
    report_ok = generate_html_report(client, app_token, target_year)
    
    if backup_ok and report_ok:
        # 生成Excel利润表
        generate_excel_pnl_report(client, app_token, target_year, target_month)
        
        # 4. 税务测算 (一键结转增强)
        print("\n[4/5] 正在进行税务风险测算及财务体检...")
        calculate_tax(client, app_token, target_year)
        financial_health_check(client, app_token, target_year)

        # 5. 导出标准凭证 (一键结转增强)
        print("\n[5/5] 正在导出标准财务凭证...")
        export_standard_voucher(client, app_token, target_year, target_month)
        
        if target_month:
            msg = f"📅 {target_year}年{target_month}月 月度结账完成！\n✅ 数据已备份\n✅ 报表已生成\n✅ 税务已测算\n✅ 凭证已导出\n💡 请务必将本地生成的 Excel 和 HTML 文件打包存档。"
        else:
            msg = f"🏆 {target_year}年度 年结完成！\n✅ 全年数据已备份\n✅ 年度报表已生成\n✅ 年度税务测算完成\n✅ 全年凭证已导出\n💡 请务必将本地生成的 Excel 和 HTML 文件打包存档。"
            
        log.info("✅ 结账流程结束", extra={"solution": "存档"})
        send_bot_message(msg, "accountant")
        return True
    else:
        log.error("❌ 结账部分失败", extra={"solution": "检查日志"})
        return False

def year_end_closing(client, app_token):
    """一键年结：调用月度结账逻辑，但锁定为年度模式"""
    print(f"\n{Color.HEADER}📅 启动年结流程 (Year-End Closing)...{Color.ENDC}")
    print(f"{Color.CYAN}此功能将生成全年的财务报表、税务测算及凭证导出。{Color.ENDC}")
    
    last_year = datetime.now().year - 1
    year_str = input(f"请输入结账年度 (默认: {last_year}): ").strip()
    if not year_str:
        year_str = str(last_year)
        
    # 再次确认
    confirm = input(f"❓ 确认对 {year_str} 年度进行年结吗? (y/n) [y]: ").strip().lower()
    if confirm == 'n':
        print("已取消。")
        return

    # 新增：年结前建议进行折旧计提
    print("-" * 30)
    dep_confirm = input(f"📉 是否先进行 {year_str}年12月 的固定资产折旧计提 (通常作为年度最后调整)? (y/n) [y]: ").strip().lower()
    if dep_confirm != 'n':
        calculate_depreciation(client, app_token, auto_run=True, target_year=int(year_str), target_month=12)

    # 复用 monthly_close 逻辑，它已经包含了年度处理的所有分支
    monthly_close(client, app_token, ym_input=year_str)

# 生成Excel利润表
def generate_excel_pnl_report(client, app_token, target_year=None, target_month=None):
    if target_year and target_month:
        log.info(f"📊 正在生成 {target_year}年{target_month}月 利润表(Excel)...", extra={"solution": "无"})
        filename_prefix = f"利润表_{target_year}{target_month:02d}"
    elif target_year:
        log.info(f"📊 正在生成 {target_year}年度 利润表(Excel)...", extra={"solution": "无"})
        filename_prefix = f"利润表_{target_year}"
    else:
        log.info("📊 正在生成标准利润表(Excel)...", extra={"solution": "无"})
        filename_prefix = f"利润表_{datetime.now().strftime('%Y%m')}"

    table_id = get_table_id_by_name(client, app_token, "日常台账表")
    if not table_id:
        return False

    # 构建过滤条件
    filter_str = None
    if target_year:
        try:
            if target_month:
                start_dt = datetime(target_year, target_month, 1)
                if target_month == 12:
                    end_dt = datetime(target_year + 1, 1, 1)
                else:
                    end_dt = datetime(target_year, target_month + 1, 1)
            else:
                start_dt = datetime(target_year, 1, 1)
                end_dt = datetime(target_year + 1, 1, 1)
            
            start_ts = int(start_dt.timestamp() * 1000)
            end_ts = int(end_dt.timestamp() * 1000)
            filter_str = f'AND(CurrentValue.[记账日期]>={start_ts}, CurrentValue.[记账日期]<{end_ts})'
        except Exception as e:
            log.error(f"日期计算错误: {e}")
            return False

    records = get_all_records(client, app_token, table_id, filter_info=filter_str)
    if not records:
        log.warning("⚠️ 该期间无数据，跳过生成利润表")
        return False
        
    data = []
    for r in records:
        fields = r.fields
        data.append({
            "记账日期": datetime.fromtimestamp(fields.get("记账日期", 0)/1000).strftime('%Y-%m-%d') if fields.get("记账日期") else "",
            "业务类型": fields.get("业务类型", ""),
            "往来单位费用": fields.get("往来单位费用", ""),
            "费用归类": fields.get("费用归类", "其他"),
            "实际收付金额": float(fields.get("实际收付金额", 0)),
            "是否有票": fields.get("是否有票", "无票")
        })
        
    df = pd.DataFrame(data)
    
    # 简单的利润表逻辑
    income = df[df["业务类型"] == "收款"]["实际收付金额"].sum()
    cost = df[df["业务类型"].isin(["付款", "费用"])]["实际收付金额"].sum()
    gross_profit = income - cost
    
    # 按费用分类汇总 (往来单位)
    partner_summary = pd.DataFrame()
    if not df[df["业务类型"].isin(["付款", "费用"])].empty:
        partner_summary = df[df["业务类型"].isin(["付款", "费用"])].groupby("往来单位费用")["实际收付金额"].sum().reset_index()
        partner_summary.columns = ["往来单位", "金额"]
        partner_summary = partner_summary.sort_values(by="金额", ascending=False)
    
    # 按费用分类汇总 (费用归类)
    category_summary = pd.DataFrame()
    if not df[df["业务类型"].isin(["付款", "费用"])].empty:
        category_summary = df[df["业务类型"].isin(["付款", "费用"])].groupby("费用归类")["实际收付金额"].sum().reset_index()
        category_summary.columns = ["费用科目", "金额"]
        category_summary = category_summary.sort_values(by="金额", ascending=False)
    
    # 月度趋势 (仅在年度报表时生成)
    monthly_trend = pd.DataFrame()
    if not target_month and not df.empty:
        try:
            # Extract month from date
            df['Month'] = df['记账日期'].apply(lambda x: x[:7] if x else '') # YYYY-MM
            expense_df = df[df["业务类型"].isin(["付款", "费用"])]
            if not expense_df.empty:
                monthly_trend = expense_df.pivot_table(
                    index='费用归类', 
                    columns='Month', 
                    values='实际收付金额', 
                    aggfunc='sum', 
                    fill_value=0
                )
                
                # 按总金额排序 (降序)
                # 计算每行的总和
                monthly_trend['Total'] = monthly_trend.sum(axis=1)
                # 排序
                monthly_trend = monthly_trend.sort_values(by='Total', ascending=False)
                # 移除 Total 列，避免写入 Excel 时重复
                monthly_trend = monthly_trend.drop(columns=['Total'])
                
                monthly_trend = monthly_trend.reset_index()
        except Exception as e:
            log.warning(f"生成月度趋势失败: {e}")

    # 写入Excel
    filename = f"{filename_prefix}.xlsx"
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
        
        # 费用明细页 (按科目)
        category_summary.to_excel(writer, sheet_name="费用明细(按科目)", index=False)
        
        # 费用明细页 (按单位)
        partner_summary.to_excel(writer, sheet_name="费用明细(按单位)", index=False)
        
        # 年度趋势页
        if not monthly_trend.empty:
             monthly_trend.to_excel(writer, sheet_name="年度费用趋势", index=False)

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
    
    # [V9.7] 利润率分析
    profit_margin = 0.0
    if month_income > 0:
        profit_margin = (net_cash / month_income) * 100
        
    margin_color = Color.OKGREEN if profit_margin >= 10 else (Color.WARNING if profit_margin >= 0 else Color.FAIL)
    margin_str = f"{margin_color}{profit_margin:+.1f}%{Color.ENDC}"

    # [新增] 终端显示 ASCII 图表
    chart_data = {
        "今日收入": today_income,
        "今日支出": today_cost,
        "本月收入": month_income,
        "本月支出": month_cost,
        "本月净利": net_cash  # Add Net Profit to chart
    }
    
    # [V9.4] 简单的趋势预测
    days_passed = now.day
    pred_msg = ""
    if days_passed >= 3: # 至少3天才预测
        avg_cost = month_cost / days_passed
        pred_total_cost = avg_cost * 30
        chart_data[f"预测月底支出"] = pred_total_cost
        pred_msg = f" (按当前趋势，月底预计支出: {pred_total_cost:,.0f})"
        
    draw_ascii_bar_chart(chart_data, title=f"今日经营简报 (利润率: {margin_str}){pred_msg}")
    
    if latest_txs:
        print(f"\n📝 今日明细 ({today_tx_count}笔):")
        for t in latest_txs[:5]:
            print(f"  - {t}")
        if len(latest_txs) > 5:
            print(f"  ... (还有 {len(latest_txs)-5} 笔)")
    else:
        print("\n💤 今日暂无收支记录")

    # [V9.7] 保存到仪表盘缓存
    try:
        cache_data = {
            "updated_at": now.strftime("%Y-%m-%d %H:%M"),
            "month": now.strftime("%Y-%m"),
            "income": month_income,
            "expense": month_cost,
            "net": net_cash
        }
        with open("dashboard_cache.json", "w", encoding="utf-8") as f:
            json.dump(cache_data, f)
    except:
        pass

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
                "费用归类": data.get('category'),
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
            "费用归类": data.get('category'),
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
        cat = f.get("费用归类", "")
        
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
        
        full_text = f"{date_str} {f.get('业务类型','')} {f.get('费用归类','')} {f.get('往来单位费用','')} {f.get('实际收付金额','')} {f.get('备注','')} {f.get('合同订单号','')}"
        
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

def manage_partners_flow(client, app_token):
    """往来单位综合管理：主数据(云端) + 别名(本地)"""
    global PARTNER_ALIASES
    
    while True:
        print(f"\n{Color.HEADER}🤝 往来单位管理 (客户/供应商/外发){Color.ENDC}")
        print("---------------------------------------")
        print("1. [云端] 查看往来单位列表 (最新20条)")
        print("2. [云端] 新增往来单位 (单个)")
        print("3. [本地] 管理名称别名 (用于对账)")
        print("0. 返回主菜单")
        
        choice = input(f"{Color.OKBLUE}请选择功能 (0-3): {Color.ENDC}").strip()
        
        if choice == '0':
            break
            
        elif choice == '1':
            table_id = get_table_id_by_name(client, app_token, "往来单位表")
            if not table_id:
                print(f"{Color.FAIL}❌ 往来单位表不存在{Color.ENDC}")
                continue
                
            records = get_all_records(client, app_token, table_id)
            if not records:
                print("📭 暂无往来单位数据")
            else:
                print(f"\n{Color.UNDERLINE}往来单位列表 (共 {len(records)} 个):{Color.ENDC}")
                print(f"{'单位名称':<20} | {'类型':<8} | {'联系人'}")
                print("-" * 50)
                # Show last 20
                for r in records[-20:]:
                    f = r.fields
                    print(f"{f.get('单位名称', '')[:18]:<20} | {f.get('类型', ''):<8} | {f.get('联系人', '')}")
                    
        elif choice == '2':
            print(f"\n{Color.CYAN}➕ 新增往来单位{Color.ENDC}")
            name = input("请输入单位名称: ").strip()
            if not name: continue
            
            p_type = input("请输入类型 (1.客户 2.供应商 3.外发加工 4.其他): ").strip()
            type_map = {'1': '客户', '2': '供应商', '3': '外发加工', '4': '其他'}
            type_str = type_map.get(p_type, '其他')
            
            contact = input("联系人 (选填): ").strip()
            phone = input("联系电话 (选填): ").strip()
            
            table_id = get_table_id_by_name(client, app_token, "往来单位表")
            if not table_id:
                create_partner_table(client, app_token)
                table_id = get_table_id_by_name(client, app_token, "往来单位表")
                
            fields = {
                "单位名称": name,
                "类型": type_str,
                "联系人": contact,
                "联系电话": phone,
                "备注": f"CLI添加 {datetime.now().strftime('%Y-%m-%d')}"
            }
            
            req = BatchCreateAppTableRecordRequest.builder() \
                .app_token(app_token) \
                .table_id(table_id) \
                .request_body(BatchCreateAppTableRecordRequestBody.builder().records([
                    AppTableRecord.builder().fields(fields).build()
                ]).build()) \
                .build()
                
            resp = client.bitable.v1.app_table_record.batch_create(req)
            if resp.success():
                print(f"{Color.OKGREEN}✅ 添加成功: {name} ({type_str}){Color.ENDC}")
            else:
                print(f"{Color.FAIL}❌ 添加失败: {resp.msg}{Color.ENDC}")

        elif choice == '3':
            manage_aliases() # Call existing function

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

def generate_partner_statement(client, app_token, start_date=None, end_date=None):
    """生成往来对账单 (支持日期筛选)"""
    log.info("📊 准备生成往来对账单...", extra={"solution": "请按提示操作"})
    
    table_id = get_table_id_by_name(client, app_token, "日常台账表")
    if not table_id: return
    
    # 1. 获取全量数据以计算余额
    print("正在拉取全量数据计算余额...")
    
    # 尝试使用全局缓存
    global GLOBAL_LEDGER_CACHE
    if GLOBAL_LEDGER_CACHE and len(GLOBAL_LEDGER_CACHE) > 0:
         print(f"⚡ 使用内存缓存 ({len(GLOBAL_LEDGER_CACHE)} 条)")
         records = GLOBAL_LEDGER_CACHE
    else:
         records = get_all_records(client, app_token, table_id, field_names=["往来单位费用", "实际收付金额", "业务类型"])
         # 顺便更新缓存（如果字段够用的话，不过这里只取了部分字段，更新全局缓存可能不安全，还是算了）
         # 或者我们可以拉取全部字段？为了速度，先只拉取部分。

    # 计算每个单位的余额
    partner_balances = {} # {partner: balance}
    
    for r in records:
        f = r.fields
        p = f.get("往来单位费用")
        if not p or p == "散户": continue
        
        amt = float(f.get("实际收付金额", 0))
        b_type = f.get("业务类型", "")
        
        if p not in partner_balances: partner_balances[p] = 0.0
        
        # 逻辑：正数=我方收，负数=我方付
        # 余额 = 我方应收 - 我方应付
        # 收款 -> 增加余额 (对方欠我/我收到钱) ? 不，这里通常指"未结清金额"
        # 让我们定义 Balance 为 "对方欠我方金额" (Receivable)
        # 收款: 余额减少 (对方还钱了) -> -amt
        # 付款: 余额增加 (我方付钱了?) -> Wait.
        
        # 让我们换个角度：Net Balance = Total In - Total Out
        # Net > 0: 我方净收 (我方赚了/对方付多了)
        # Net < 0: 我方净付 (我方亏了/对方还没付?)
        
        # 通常对账单：
        # 销售对账: 应收 = 销售额 - 已收款
        # 采购对账: 应付 = 采购额 - 已付款
        
        # 这里是混合流水。
        # 收款: +amt
        # 付款/费用: -amt (注意：费用通常是负数入库吗？在 ledger 里通常是正数，业务类型区分)
        
        # 假设 ledger 记录：
        # 业务类型="收款", 金额=1000  -> Total In += 1000
        # 业务类型="付款", 金额=200   -> Total Out += 200
        
        val = amt
        if b_type == "收款":
            partner_balances[p] += val
        elif b_type in ["付款", "费用"]:
            partner_balances[p] -= val
            
    # 排序：按余额绝对值从大到小
    sorted_partners = sorted(partner_balances.keys(), key=lambda x: abs(partner_balances[x]), reverse=True)
    
    print(f"\n👥 往来单位列表 (按余额排序):")
    print(f"{'序号':<5} | {'单位名称':<20} | {'当前净额 (收-付)':<15}")
    print("-" * 50)
    
    for i, p in enumerate(sorted_partners):
        bal = partner_balances[p]
        bal_str = f"{bal:,.2f}"
        if bal > 0: bal_str = f"+{bal_str}"
        
        # Color
        c = ""
        if bal > 0: c = Color.GREEN
        elif bal < 0: c = Color.FAIL
            
        print(f"{i+1:<5} | {p:<20} | {c}{bal_str:<15}{Color.ENDC}")
        
    # 2. 选择单位
    print("-" * 50)
    choice = input("请输入序号或直接输入单位名称 (输入 '0' 退出): ").strip()
    if choice == '0': return

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

    # 2.1 日期筛选
    start_ts = None
    end_ts = None
    date_desc = "全部历史"

    if start_date and end_date:
        try:
            s_dt = datetime.strptime(start_date, "%Y-%m-%d")
            e_dt = datetime.strptime(end_date, "%Y-%m-%d") + timedelta(days=1)
            start_ts = int(s_dt.timestamp() * 1000)
            end_ts = int(e_dt.timestamp() * 1000)
            date_desc = f"{start_date}至{end_date}"
        except:
            pass
    else:
        print("-" * 30)
        use_date = input("📅 是否筛选特定日期范围? (y/n) [n]: ").strip().lower()
        if use_date == 'y':
            s_in = input("   起始日期 (YYYY-MM-DD): ").strip()
            e_in = input("   结束日期 (YYYY-MM-DD): ").strip()
            if s_in and e_in:
                try:
                    s_dt = datetime.strptime(s_in, "%Y-%m-%d")
                    e_dt = datetime.strptime(e_in, "%Y-%m-%d") + timedelta(days=1)
                    start_ts = int(s_dt.timestamp() * 1000)
                    end_ts = int(e_dt.timestamp() * 1000)
                    date_desc = f"{s_in}至{e_in}"
                except:
                    print("❌ 日期格式错误，将导出全部数据")
    
    # 3. 获取该单位所有记录
    print(f"正在拉取 {target_partner} 的记录 ({date_desc})...")
    
    # 构建过滤器
    conditions = []
    # 1. 往来单位筛选
    conditions.append(f'CurrentValue.[往来单位费用]="{target_partner}"')
    # 2. 日期筛选
    if start_ts and end_ts:
        conditions.append(f'CurrentValue.[记账日期]>={start_ts}')
        conditions.append(f'CurrentValue.[记账日期]<{end_ts}')
    
    filter_cmd = "&&".join(conditions)
    if len(conditions) > 1:
        filter_cmd = f"AND({', '.join(conditions)})" # 飞书公式语法可能不支持 && 在 API 中直接用，通常是 AND(cond1, cond2)
        # 修正：飞书 API filter 通常支持 logic operator like "AND(CurrentValue.[Field]=val, ...)"
        # 之前的代码有用 && 吗？
        # Line 3764 used: f'CurrentValue.[记账日期]>={start_ts}&&CurrentValue.[记账日期]<{end_ts}&&CurrentValue.[费用归类]="折旧摊销"'
        # So && is supported? Let's check line 3764 in previous read.
        # Yes, line 3764: filter_cmd = f'CurrentValue.[记账日期]>={start_ts}&&CurrentValue.[记账日期]<{end_ts}&&CurrentValue.[费用归类]="折旧摊销"'
        # So I will use &&
    
    filter_cmd = "&&".join(conditions)

    all_records = get_all_records(client, app_token, table_id, filter_info=filter_cmd)
    
    partner_records = []
    total_in = 0.0
    total_out = 0.0
    
    for r in all_records:
        f = r.fields
        # 双重确认 (API 过滤可能有时候不完美，或者防止注入)
        p = str(f.get("往来单位费用", "")).strip()
        if p != target_partner:
            continue
            
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
        
    # --- 新增：控制台汇总输出 ---
    print(f"\n📊 {Color.HEADER}【{target_partner}】对账汇总{Color.ENDC}")
    print(f"📅 期间: {date_desc}")
    print("-" * 40)
    print(f"💰 累计收款 (我方收): {Color.GREEN}{total_in:,.2f}{Color.ENDC}")
    print(f"💸 累计付款 (我方付): {Color.FAIL}{total_out:,.2f}{Color.ENDC}")
    net = total_in - total_out
    net_color = Color.GREEN if net >= 0 else Color.FAIL
    print(f"⚖️  净额 (收-付):      {net_color}{net:,.2f}{Color.ENDC}")
    print("-" * 40)
    
    # --- 复制专用片段 ---
    print(f"\n📋 {Color.BOLD}>>> 请复制下方内容发送给客户/供应商 <<<{Color.ENDC}")
    print("----------------------------------------")
    print(f"【对账单】{target_partner}")
    print(f"统计期间：{date_desc}")
    print(f"累计收款：{total_in:,.2f}")
    print(f"累计付款：{total_out:,.2f}")
    print(f"当前净额：{net:,.2f} ({'我方应收' if net > 0 else '我方应付' if net < 0 else '已结清'})")
    print(f"明细附件：请查阅生成的 Excel/HTML 对账单")
    print("----------------------------------------")
    print(f"\n📝 共计 {len(partner_records)} 条记录")
    print("-" * 40)
    # ---------------------------

    # 4. 生成 Excel
    df = pd.DataFrame(partner_records)
    df = df.sort_values(by="日期")
    
    # 创建输出目录
    output_dir = "往来对账单"
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    timestamp_str = datetime.now().strftime('%Y%m%d_%H%M%S')
    filename_base = f"往来对账单_{target_partner}_{date_desc}_{timestamp_str}".replace(":", "").replace("/", "-")
    excel_path = os.path.join(output_dir, f"{filename_base}.xlsx")
    html_path = os.path.join(output_dir, f"{filename_base}.html")
    
    # --- Excel 生成 ---
    with pd.ExcelWriter(excel_path, engine='openpyxl') as writer:
        # 汇总页
        summary = [
            ["项目", "金额", "说明"],
            ["往来单位", target_partner, ""],
            ["统计期间", date_desc, ""],
            ["累计收款", total_in, "我方收到"],
            ["累计付款", total_out, "我方支付"],
            ["净额", total_in - total_out, "正数=我方净收，负数=我方净付"],
            ["生成时间", datetime.now().strftime('%Y-%m-%d %H:%M:%S'), ""]
        ]
        pd.DataFrame(summary).to_excel(writer, sheet_name="对账汇总", index=False, header=False)
        
        # 明细页
        df.to_excel(writer, sheet_name="流水明细", index=False)
        
    log.info(f"✅ Excel对账单已生成: {excel_path}")

    # --- HTML 生成 (可视化报表) ---
    print("📊 正在生成可视化HTML报表...")
    
    # 准备图表数据 (按日期累计净额)
    chart_labels = []
    chart_data = []
    running_balance = 0.0
    
    # 确保按日期排序
    sorted_records = sorted(partner_records, key=lambda x: x['日期'])
    
    for r in sorted_records:
        chart_labels.append(r['日期'])
        val = r['金额']
        if r['业务类型'] in ["付款", "费用"]:
            val = -val
        running_balance += val
        chart_data.append(round(running_balance, 2))
        
    # 简单的 JS 图表 (使用 Chart.js CDN，如果没有网则只显示表格)
    # 为了离线可用，我们也可以用 SVG，但 Chart.js 更好看。这里我们假设有网，或者回退。
    # 实际上，我们可以嵌入一个简单的 SVG 折线图生成逻辑，保证 100% 离线可用。
    # 这里我们用一个极简的 SVG 生成器。
    
    svg_points = ""
    if chart_data:
        max_val = max(max(chart_data), abs(min(chart_data)), 1)
        min_val = min(chart_data)
        width = 800
        height = 200
        # Normalize
        # Y axis: 0 is at height/2 if min < 0 < max? No, let's map min~max to height~0
        y_range = max_val - min_val if max_val != min_val else 1
        x_step = width / (len(chart_data) - 1) if len(chart_data) > 1 else width
        
        points = []
        for i, val in enumerate(chart_data):
            x = i * x_step
            # y: map val to height...0
            # val = min -> y = height
            # val = max -> y = 0
            y = height - ((val - min_val) / y_range * height)
            points.append(f"{x:.1f},{y:.1f}")
            
        # Optimization: If only one point, draw a flat line
        if len(chart_data) == 1:
            points.append(f"{width:.1f},{points[0].split(',')[1]}")
            
        svg_points = " ".join(points)
        
    # 生成 HTML 内容
    net_val = total_in - total_out
    net_cls = "income" if net_val >= 0 else "expense"
    
    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="utf-8">
        <title>往来对账单 - {target_partner}</title>
        <style>
            body {{ font-family: 'Segoe UI', sans-serif; background: #f5f7fa; color: #333; padding: 20px; }}
            .container {{ max-width: 900px; margin: 0 auto; background: white; padding: 40px; border-radius: 12px; box-shadow: 0 4px 20px rgba(0,0,0,0.05); }}
            .header {{ border-bottom: 2px solid #eee; padding-bottom: 20px; margin-bottom: 30px; display: flex; justify-content: space-between; align-items: center; }}
            .title h1 {{ margin: 0; font-size: 24px; color: #2c3e50; }}
            .title p {{ margin: 5px 0 0; color: #7f8c8d; font-size: 14px; }}
            .meta {{ text-align: right; color: #95a5a6; font-size: 13px; }}
            
            .cards {{ display: flex; gap: 20px; margin-bottom: 40px; }}
            .card {{ flex: 1; background: #f8f9fa; padding: 20px; border-radius: 8px; text-align: center; border: 1px solid #e9ecef; }}
            .card .val {{ font-size: 24px; font-weight: bold; margin-bottom: 5px; }}
            .card .lbl {{ font-size: 13px; color: #7f8c8d; }}
            .c-in {{ color: #27ae60; }}
            .c-out {{ color: #c0392b; }}
            .c-net {{ color: #2980b9; }}
            
            table {{ width: 100%; border-collapse: collapse; font-size: 14px; }}
            th {{ text-align: left; padding: 12px; background: #f8f9fa; color: #7f8c8d; border-bottom: 2px solid #eee; }}
            td {{ padding: 12px; border-bottom: 1px solid #f1f1f1; }}
            tr:hover {{ background: #fafafa; }}
            
            .chart-container {{ margin: 30px 0; padding: 20px; border: 1px solid #eee; border-radius: 8px; background: #fff; }}
            .chart-title {{ font-size: 14px; font-weight: bold; color: #34495e; margin-bottom: 15px; }}
            
            /* Tag styles */
            .tag {{ padding: 2px 8px; border-radius: 4px; font-size: 12px; }}
            .tag-in {{ background: #e8f5e9; color: #2e7d32; }}
            .tag-out {{ background: #ffebee; color: #c62828; }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <div class="title">
                    <h1>往来对账单</h1>
                    <p>单位: <strong>{target_partner}</strong></p>
                </div>
                <div class="meta">
                    期间: {date_desc}<br>
                    生成: {datetime.now().strftime('%Y-%m-%d %H:%M')}
                </div>
            </div>
            
            <div class="cards">
                <div class="card">
                    <div class="val c-in">+{total_in:,.2f}</div>
                    <div class="lbl">累计收款 (我方收)</div>
                </div>
                <div class="card">
                    <div class="val c-out">-{total_out:,.2f}</div>
                    <div class="lbl">累计付款 (我方付)</div>
                </div>
                <div class="card">
                    <div class="val {net_cls}">{net_val:+,.2f}</div>
                    <div class="lbl">净额 (收-付)</div>
                </div>
            </div>
            
            <div class="chart-container">
                <div class="chart-title">📈 累计净额走势 (Cumulative Net Balance)</div>
                <svg width="100%" height="200" viewBox="0 0 800 200" preserveAspectRatio="none">
                    <defs>
                        <linearGradient id="grad" x1="0%" y1="0%" x2="0%" y2="100%">
                            <stop offset="0%" style="stop-color:#3498db;stop-opacity:0.2" />
                            <stop offset="100%" style="stop-color:#3498db;stop-opacity:0" />
                        </linearGradient>
                    </defs>
                    <!-- Grid lines -->
                    <line x1="0" y1="100" x2="800" y2="100" stroke="#eee" stroke-width="1" />
                    <line x1="0" y1="0" x2="800" y2="0" stroke="#eee" stroke-width="1" />
                    <line x1="0" y1="200" x2="800" y2="200" stroke="#eee" stroke-width="1" />
                    
                    <!-- The Line -->
                    <polyline points="{svg_points}" fill="none" stroke="#3498db" stroke-width="2" />
                </svg>
                <div style="text-align: center; font-size: 12px; color: #999; margin-top: 5px;">
                    (起始: {chart_data[0] if chart_data else 0:.0f} &rarr; 结束: {chart_data[-1] if chart_data else 0:.0f})
                </div>
            </div>
            
            <h3>📄 交易明细</h3>
            <table>
                <thead>
                    <tr>
                        <th width="120">日期</th>
                        <th width="80">类型</th>
                        <th width="120">金额</th>
                        <th>摘要/备注</th>
                        <th width="80">凭证</th>
                    </tr>
                </thead>
                <tbody>
    """
    
    for r in sorted_records:
        type_cls = "tag-in" if r['业务类型'] == "收款" else "tag-out"
        amt_color = "#27ae60" if r['业务类型'] == "收款" else "#c0392b"
        prefix = "+" if r['业务类型'] == "收款" else "-"
        
        html_content += f"""
        <tr>
            <td>{r['日期']}</td>
            <td><span class="tag {type_cls}">{r['业务类型']}</span></td>
            <td style="color: {amt_color}; font-family: monospace; font-weight: bold;">{prefix}{r['金额']:,.2f}</td>
            <td>{r['备注']} <span style="color:#999; font-size:12px">({r['费用类型']})</span></td>
            <td>{r['是否有票']}</td>
        </tr>
        """
        
    html_content += """
                </tbody>
            </table>
            
            <div style="margin-top: 40px; text-align: center; color: #ccc; font-size: 12px; border-top: 1px solid #eee; padding-top: 20px;">
                Generated by Feishu Financial Assistant
            </div>
        </div>
    </body>
    </html>
    """
    
    with open(html_path, "w", encoding="utf-8") as f:
        f.write(html_content)
        
    log.info(f"✅ HTML对账单已生成: {html_path}", extra={"solution": "浏览器打开查看"})

    try:
        os.startfile(html_path)
    except:
        pass

    # --- 5. 生成微信发送模板 ---
    print("\n" + "="*40)
    print("✂️  微信/IM 发送模板 (请复制下方内容)")
    print("="*40)
    
    wx_template = f"""
【对账单】{target_partner}
📅 期间: {date_desc}
----------------
💰 我方收款: {total_in:,.2f}
💸 我方付款: {total_out:,.2f}
⚖️ 结余净额: {net:+,.2f} ({'我方净收' if net >=0 else '我方净付'})
----------------
详情请见附件对账单 (HTML/Excel)。
如有疑问请及时沟通，谢谢！
生成时间: {datetime.now().strftime('%m-%d %H:%M')}
    """
    print(wx_template.strip())
    print("="*40 + "\n")

# -------------------------------------------------------------------------
# 新增功能：固定资产折旧
# -------------------------------------------------------------------------

def calculate_depreciation(client, app_token, auto_run=False, target_year=None, target_month=None):
    """一键计提折旧 (生成折旧凭证)"""
    log.info("📉 正在计算固定资产折旧...", extra={"solution": "无"})
    
    asset_table_id = get_table_id_by_name(client, app_token, "固定资产表")
    ledger_table_id = get_table_id_by_name(client, app_token, "日常台账表")
    
    if not asset_table_id or not ledger_table_id:
        log.error("❌ 未找到表格，请先初始化", extra={"solution": "运行 --create-table"})
        return

    # 0. 确定计提月份
    now = datetime.now()
    if target_year and target_month:
        current_month_str = f"{target_year}-{target_month:02d}"
        start_dt = datetime(target_year, target_month, 1)
        if target_month == 12:
            end_dt = datetime(target_year + 1, 1, 1)
        else:
            end_dt = datetime(target_year, target_month + 1, 1)
    else:
        # 默认当前月份
        current_month_str = now.strftime('%Y-%m')
        start_dt = datetime(now.year, now.month, 1)
        if now.month == 12:
            end_dt = datetime(now.year + 1, 1, 1)
        else:
            end_dt = datetime(now.year, now.month + 1, 1)
    
    start_ts = int(start_dt.timestamp() * 1000)
    end_ts = int(end_dt.timestamp() * 1000)
    
    # 使用筛选器查询，避免拉取全部数据
    filter_cmd = f'CurrentValue.[记账日期]>={start_ts}&&CurrentValue.[记账日期]<{end_ts}&&CurrentValue.[费用归类]="折旧摊销"'
    
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
        # 优化：如果是补提旧月份，可能资产状态现在是'已报废'，但当时是'使用中'？
        # 暂时只支持对当前'使用中'的资产计提，或者假设资产状态维护得当
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
            
            # 记账日期设为该月最后一天 (或当前时间)
            # 如果是补提，设为该月最后一天中午12点
            entry_ts = int((end_dt - timedelta(hours=12)).timestamp() * 1000)
            
            depreciation_entries.append({
                "记账日期": entry_ts,
                "业务类型": "费用",
                "费用归类": "折旧摊销", # 自动归类
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
        send_bot_message(f"✅ 完成 {current_month_str} 折旧计提，总额: {total_depreciation}元", "accountant")
    else:
        print("❌ 已取消")

def export_standard_voucher(client, app_token, target_year=None, target_month=None):
    """导出标准凭证格式 (对接财务软件)"""
    if target_year and target_month:
        log.info(f"📑 正在生成 {target_year}年{target_month}月 标准凭证导出文件...", extra={"solution": "请稍候"})
        filename_prefix = f"标准凭证导出_{target_year}{target_month:02d}"
    else:
        log.info("📑 正在生成标准凭证导出文件...", extra={"solution": "请稍候"})
        filename_prefix = f"标准凭证导出_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

    table_id = get_table_id_by_name(client, app_token, "日常台账表")
    if not table_id: return
    
    # 构建过滤条件
    filter_str = None
    if target_year:
        try:
            if target_month:
                start_dt = datetime(target_year, target_month, 1)
                if target_month == 12:
                    end_dt = datetime(target_year + 1, 1, 1)
                else:
                    end_dt = datetime(target_year, target_month + 1, 1)
            else:
                start_dt = datetime(target_year, 1, 1)
                end_dt = datetime(target_year + 1, 1, 1)
            
            start_ts = int(start_dt.timestamp() * 1000)
            end_ts = int(end_dt.timestamp() * 1000)
            filter_str = f'AND(CurrentValue.[记账日期]>={start_ts}, CurrentValue.[记账日期]<{end_ts})'
        except Exception as e:
            log.error(f"日期计算错误: {e}")
            return
            
    # Get all records
    print("正在拉取凭证数据...")
    records = get_all_records(client, app_token, table_id, filter_info=filter_str)
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
        partner = f.get("往来单位费用", "")
        category = f.get("费用归类", "")

        # 如果备注为空，使用往来单位或费用类型作为摘要
        if not summary:
             summary = f"{partner} {category}".strip()
        
        # 借贷逻辑
        bank_acc = f.get("交易银行", "银行存款")
        
        # 优先使用费用归类作为科目，如果为空则使用往来单位
        # 对于费用类支出，通常科目为费用归类；对于往来款，科目为往来单位
        subject = category if category and category != "其他" and category != "nan" else partner
        if not subject or subject == "nan":
            subject = "暂无分类"
        
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
    
    filename = f"{filename_prefix}.xlsx"
    df.to_excel(filename, index=False)
    
    log.info(f"✅ 导出完成: {filename}", extra={"solution": "可直接导入金蝶/用友等财务软件"})
    try:
        os.startfile(filename)
    except:
        pass

# -------------------------------------------------------------------------
# 新增功能：交互式主菜单 (Python版)
# -------------------------------------------------------------------------

def backup_system_data(client=None, app_token=None):
    """备份系统关键配置和数据"""
    print(f"{Color.CYAN}💾 正在进行系统备份...{Color.ENDC}")
    
    backup_root = "backup"
    if not os.path.exists(backup_root):
        os.makedirs(backup_root)
        
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    target_dir = os.path.join(backup_root, timestamp)
    os.makedirs(target_dir)
    
    # 1. 备份配置文件
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
    
    # 2. 备份 Excel 文件 (如果存在)
    excel_files = [f for f in os.listdir('.') if f.endswith('.xlsx') and not f.startswith('~$')]
    for f in excel_files:
        try:
            shutil.copy(f, target_dir)
            print(f"  - 已备份: {f}")
        except:
            pass
            
    # 3. [新增] 备份云端数据 (如果提供了client)
    if client and app_token:
        print("  - 正在导出云端数据...")
        export_to_excel(client, app_token, target_path=target_dir)

    # 4. 压缩备份文件夹
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
        
def auto_fix_missing_categories(client, app_token, target_year=None):
    """自动修复缺失的费用归类"""
    if target_year:
        log.info(f"🔧 正在检查并修复 {target_year}年度 缺失的费用归类...", extra={"solution": "自动修复"})
        year = target_year
    else:
        log.info("🔧 正在检查并修复缺失的费用归类...", extra={"solution": "自动修复"})
        year = datetime.now().year
    
    # [V9.6优化] 确保加载历史知识和AI缓存
    if not HISTORY_CATEGORY_MAP or not AI_CACHE_MAP:
        load_history_knowledge(client, app_token)
        
    table_id = get_table_id_by_name(client, app_token, "日常台账表")
    if not table_id: return
    
    # 获取指定年度数据 (减少处理量)
    start_ts = int(datetime(year, 1, 1).timestamp() * 1000)
    end_ts = int(datetime(year + 1, 1, 1).timestamp() * 1000)
    filter_str = f'AND(CurrentValue.[记账日期]>={start_ts}, CurrentValue.[记账日期]<{end_ts})'
    
    records = get_all_records(client, app_token, table_id, filter_info=filter_str)
    
    updates = []
    
    for r in records:
        f = r.fields
        # 仅处理 费用/付款 类型
        if f.get("业务类型") not in ["费用", "付款"]:
            continue
            
        cat = f.get("费用归类", "")
        desc = f.get("备注", "")
        partner = f.get("往来单位费用", "")
        
        # 如果归类为空 或 为默认值 "其他"
        if not cat or cat in ["", "nan", "其他", "未知"]:
            # 尝试自动分类
            new_cat = auto_categorize(desc, "其他", partner_name=partner)
            
            # 如果自动分类找到了非默认值，且与原值不同
            if new_cat != "其他" and new_cat != cat:
                print(f"   🔧 自动修复: {partner} | {desc} -> {new_cat}")
                updates.append(AppTableRecord.builder().record_id(r.record_id).fields({"费用归类": new_cat}).build())
                
    if updates:
        print(f"   📋 发现 {len(updates)} 条记录待修复，正在批量更新...")
        # [V9.6优化] 批量更新 (Batch Update)
        batch_size = 100
        total_success = 0
        
        for i in range(0, len(updates), batch_size):
            batch = updates[i:i+batch_size]
            try:
                req = BatchUpdateAppTableRecordRequest.builder() \
                    .app_token(app_token) \
                    .table_id(table_id) \
                    .request_body(BatchUpdateAppTableRecordRequestBody.builder().records(batch).build()) \
                    .build()
                resp = client.bitable.v1.app_table_record.batch_update(req)
                if resp.success():
                    total_success += len(batch)
                    print(f"      ✅ 已更新批次 {i//batch_size + 1} ({len(batch)}条)")
                else:
                    log.error(f"❌ 批次更新失败: {resp.msg}")
            except Exception as e:
                log.error(f"❌ 批次更新异常: {e}")
                
        print(f"   ✅ 成功修复 {total_success} 条记录")
    else:
        print("   ✅ 费用归类数据完整，无需修复")

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

    # 1.6 自动修复缺失分类 (New)
    print(f"\n{Color.HEADER}🔧 检查并修复缺失分类...{Color.ENDC}")
    auto_fix_missing_categories(client, app_token)

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
    backup_system_data(client, app_token)

    # 6. 发送每日简报
    print(f"\n{Color.HEADER}📢 发送每日经营简报...{Color.ENDC}")
    daily_briefing(client, app_token)
    
    # 6. 生成日结报告 (HTML)
    print(f"\n{Color.HEADER}📊 生成每日结账报告...{Color.ENDC}")
    combined_log = []
    if summary:
        combined_log.append("【处理摘要】")
        combined_log.extend(summary)
    if daily_log:
        combined_log.append("\n【详细日志】")
        combined_log.extend(daily_log)
        
    report_file = generate_daily_html_report(client, app_token, summary_log=combined_log)
    
    if report_file:
        print(f"\n{Color.GREEN}========================================{Color.ENDC}")
        print(f"{Color.GREEN}🎉 日结完成！报告已生成: {report_file}{Color.ENDC}")
        print(f"{Color.GREEN}========================================{Color.ENDC}")
        try:
            os.startfile(report_file)
        except:
            pass
    else:
        log.error("生成报告失败")
    
    print(f"\n{Color.GREEN}✅ 一键流程全部完成！{Color.ENDC}")

# -------------------------------------------------------------------------
# 实用小工具
# -------------------------------------------------------------------------
def number_to_chinese(n):
    """
    人民币数字转大写 (简化版，支持万亿级别)
    """
    if not isinstance(n, (int, float)):
        try: n = float(n)
        except: return "输入无效"
        
    if n > 999999999999.99: return "金额过大"
    
    fractions = ['角', '分']
    digit = ['零', '壹', '贰', '叁', '肆', '伍', '陆', '柒', '捌', '玖']
    unit = [['元', '万', '亿'], ['', '拾', '佰', '仟']]
    
    n_str = "{:.2f}".format(n)
    left, right = n_str.split('.')
    
    # 小数部分
    res = []
    jiao = int(right[0])
    fen = int(right[1])
    
    if jiao > 0:
        res.append(digit[jiao] + fractions[0])
    elif fen > 0 and int(left) > 0:
        res.append("零")
        
    if fen > 0:
        res.append(digit[fen] + fractions[1])
            
    if not res:
        suffix = "整"
    else:
        suffix = ""
        
    if int(left) == 0:
        if not res: return "零元整"
        return "".join(res)
        
    # 整数部分
    s = ""
    left_str = str(int(left))
    length = len(left_str)
    
    for i in range(length):
        j = length - i - 1
        d = int(left_str[i])
        
        # 单位索引
        u_idx = j % 4
        # 大单位索引
        b_idx = j // 4
        
        if d != 0:
            s += digit[d] + unit[1][u_idx]
        else:
            # 处理零
            if s and s[-1] != digit[0]:
                s += digit[0]
                
        # 添加大单位
        if u_idx == 0:
            if s and s[-1] == digit[0]: s = s[:-1]
            if b_idx < len(unit[0]):
                s += unit[0][b_idx]
                
    # 修复多余的零
    s = s.replace("零万", "万").replace("零亿", "亿").replace("亿万", "亿").replace("零元", "元")
    
    return s + ("".join(res) or "整")

def get_dashboard_status():
    """获取仪表盘状态 (财务概览/待办/备份)"""
    status_lines = []
    
    # 0. 财务概览 (本月)
    try:
        if os.path.exists("dashboard_cache.json"):
            with open("dashboard_cache.json", "r", encoding="utf-8") as f:
                data = json.load(f)
                cur_month = datetime.now().strftime("%Y-%m")
                if data.get("month") == cur_month:
                    inc = data.get("income", 0)
                    exp = data.get("expense", 0)
                    net = data.get("net", 0)
                    
                    c_inc = Color.GREEN
                    c_exp = Color.FAIL
                    c_net = Color.OKBLUE if net >= 0 else Color.FAIL
                    
                    summary = f"{cur_month} 概览: {c_inc}+{inc:,.0f}{Color.ENDC} / {c_exp}-{exp:,.0f}{Color.ENDC} = {c_net}{net:+,.0f}{Color.ENDC}"
                    status_lines.append(summary)
    except:
        pass
    
    # 1. 检查待处理文件
    watch_dir = os.path.join(os.getcwd(), "待处理单据")
    pending_count = 0
    if os.path.exists(watch_dir):
        pending_files = [f for f in os.listdir(watch_dir) if f.lower().endswith(('.xlsx', '.xls', '.csv', '.jpg', '.png'))]
        pending_count = len(pending_files)
        
    if pending_count > 0:
        status_lines.append(f"{Color.FAIL}🔔 待处理单据: {pending_count} 个 (建议立即运行 '00'){Color.ENDC}")
    else:
        status_lines.append(f"{Color.OKGREEN}✅ 待处理单据: 无{Color.ENDC}")
        
    # 2. 检查最近备份
    backup_dir = os.path.join(os.getcwd(), "财务数据备份")
    last_backup = "无"
    if os.path.exists(backup_dir):
        try:
            # 检查子目录 (旧模式) 或 文件 (新模式)
            items = [os.path.join(backup_dir, d) for d in os.listdir(backup_dir)]
            valid_backups = [f for f in items if os.path.isdir(f) or f.lower().endswith(('.xlsx', '.zip'))]
            
            if valid_backups:
                latest = max(valid_backups, key=os.path.getmtime)
                last_time = datetime.fromtimestamp(os.path.getmtime(latest)).strftime("%m-%d %H:%M")
                last_backup = last_time
        except: pass
            
    status_lines.append(f"{Color.OKBLUE}💾 最近备份: {last_backup}{Color.ENDC}")
    
    return " | ".join(status_lines)

def manage_small_tools(client, app_token):
    while True:
        print(f"\n{Color.BOLD}🧰 会计实用工具箱{Color.ENDC}")
        print("  1. 🔢 金额转大写 (壹万贰仟...)")
        print("  2. 🧮 税额计算器 (含税/不含税互转)")
        print("  3. 📅 日期计算器 (账期推算)")
        print("  0. 返回主菜单")
        
        choice = input(f"👉 {Color.BOLD}请选择: {Color.ENDC}").strip()
        if choice == '0': break
        
        if choice == '1':
            print(f"\n{Color.UNDERLINE}🔢 金额转大写{Color.ENDC}")
            while True:
                s = input("请输入金额 (输入 0 返回): ").strip()
                if s == '0': break
                try:
                    val = float(s)
                    cn = number_to_chinese(val)
                    print(f"👉 大写: {Color.OKGREEN}{cn}{Color.ENDC}")
                    # 同时也显示复制提示
                    print(f"   (已生成，可直接选中复制)")
                except:
                    print("❌ 无效数字")
                    
        elif choice == '2':
            print(f"\n{Color.UNDERLINE}🧮 税额计算器{Color.ENDC}")
            print("💡 提示: 输入 '100' 代表不含税，输入 'h 113' 代表含税")
            while True:
                s = input("\n请输入金额 (0 返回): ").strip()
                if s == '0': break
                
                is_inclusive = False
                val = 0.0
                if s.lower().startswith('h') or s.startswith('含'):
                    is_inclusive = True
                    try: val = float(s.lstrip('h含 '))
                    except: pass
                else:
                    try: val = float(s)
                    except: pass
                    
                if val == 0: continue
                
                r_str = input("税率% [13]: ").strip()
                if not r_str: r_str = "13"
                try:
                    rate = float(r_str) / 100.0
                except:
                    print("❌ 税率无效")
                    continue
                
                if is_inclusive:
                    amt = val / (1 + rate)
                    tax = val - amt
                    print(f"📉 [含税 {val:,.2f}] (税率 {int(rate*100)}%)")
                    print(f"   ✅ 不含税金额: {Color.OKGREEN}{amt:,.2f}{Color.ENDC}")
                    print(f"   ✅ 税额:       {Color.OKGREEN}{tax:,.2f}{Color.ENDC}")
                else:
                    tax = val * rate
                    total = val + tax
                    print(f"📈 [不含税 {val:,.2f}] (税率 {int(rate*100)}%)")
                    print(f"   ✅ 税额:       {Color.OKGREEN}{tax:,.2f}{Color.ENDC}")
                    print(f"   ✅ 价税合计:   {Color.OKGREEN}{total:,.2f}{Color.ENDC}")

        elif choice == '3':
            print(f"\n{Color.UNDERLINE}📅 日期计算器{Color.ENDC}")
            print("💡 示例: 输入 '30' (30天后) 或 '-7' (7天前)")
            while True:
                s = input("\n请输入天数 (0 返回): ").strip()
                if s == '0': break
                
                try:
                    days = int(s)
                    target_date = datetime.now() + timedelta(days=days)
                    desc = "后" if days > 0 else "前"
                    print(f"👉 {abs(days)}天{desc}: {Color.OKGREEN}{target_date.strftime('%Y-%m-%d')} ({target_date.strftime('%A')}){Color.ENDC}")
                except:
                    print("❌ 无效天数")

def register_voucher(client, app_token):
    """手工录入凭证 (CLI Wizard)"""
    print(f"\n{Color.HEADER}📝 手工录入凭证 (Voucher Entry){Color.ENDC}")
    print("-----------------------------------------------")
    
    # 1. Date
    default_date = datetime.now().strftime("%Y-%m-%d")
    date_str = input(f"📅 日期 [默认 {default_date}]: ").strip()
    if not date_str: date_str = default_date
    try:
        ts = int(datetime.strptime(date_str, "%Y-%m-%d").timestamp() * 1000)
    except:
        print("❌ 日期格式错误")
        return

    # 2. Type
    print("\n请选择业务类型:")
    print("  1. 收款 (+)")
    print("  2. 付款 (-)")
    print("  3. 费用 (-)")
    t_map = {"1": "收款", "2": "付款", "3": "费用"}
    t_choice = input("👉 选择 (1-3): ").strip()
    if t_choice not in t_map: 
        print("❌ 无效选择")
        return
    biz_type = t_map[t_choice]

    # 3. Amount
    amt_str = input("\n💰 金额 (正数): ").strip()
    try:
        # Simple eval for basic math like "100+200"
        amount = float(eval(amt_str, {"__builtins__": None}, {}))
    except:
        print("❌ 金额错误")
        return
    
    # 4. Partner
    partner = input("\n👤 往来单位 (直接输入，留空为'散户'): ").strip()
    if not partner: partner = "散户"
    
    # 5. Category
    category = input("\n📂 费用归类 (如办公费/差旅费): ").strip()
    if not category: category = "未分类"
    
    # 6. Remarks
    remark = input("\n📝 备注摘要: ").strip()
    
    # 7. Invoice
    has_invoice = "无票"
    if input("\n🧾 是否有票? (y/n) [n]: ").strip().lower() == 'y':
        has_invoice = "有票"
        
    # Confirm
    print("\n--------------------------------")
    print(f"日期: {date_str}")
    print(f"类型: {biz_type}")
    print(f"单位: {partner}")
    print(f"科目: {category}")
    print(f"金额: {amount:,.2f}")
    print(f"备注: {remark}")
    print("--------------------------------")
    
    if input("确认保存? (y/n): ").strip().lower() != 'y': return
    
    # Save
    table_id = get_table_id_by_name(client, app_token, "日常台账表")
    if not table_id: return
    
    fields = {
        "记账日期": ts,
        "业务类型": biz_type,
        "费用归类": category,
        "往来单位费用": partner,
        "实际收付金额": amount,
        "备注": remark,
        "是否有票": has_invoice,
        "是否现金": "否"
    }
    
    try:
        req = CreateAppTableRecordRequest.builder() \
            .app_token(app_token) \
            .table_id(table_id) \
            .request_body(AppTableRecord.builder().fields(fields).build()) \
            .build()
            
        resp = client.bitable.v1.app_table_record.create(req)
        if resp.success():
            print(f"\n✅ {Color.GREEN}凭证保存成功！{Color.ENDC}")
        else:
            print(f"\n❌ 保存失败: {resp.msg}")
            
    except Exception as e:
        log.error(f"保存异常: {e}")

def interactive_menu():
    """Python版交互主菜单"""
    # 启用 Windows ANSI 支持 (如果是 Windows)
    if os.name == 'nt':
        os.system('color')
        
    while True:
        # 清屏 (兼容 Windows/Linux)
        os.system('cls' if os.name == 'nt' else 'clear')
        
        print(f"{Color.HEADER}===============================================")
        print(f"       🚀 飞书财务小助手 V9.7 - 旗舰版")
        print(f"==============================================={Color.ENDC}")
        
        # 显示仪表盘状态
        print(f"\n{get_dashboard_status()}")
        
        print(f"\n{Color.CYAN}📝 记账录入{Color.ENDC}")
        print("  00. 🚀 一键日结 (自动处理+税务+体检+备份) [推荐]")
        print("  1. 智能截图记账 (OCR + AI)")
        print("  2. 智能文本记账 (微信/自然语言)")
        print("  27. 凭证登记 (手工录入凭证) [新]")
        print("  3. 从 Excel 导入数据")
        
        print(f"\n{Color.CYAN}🏦 银行与对账{Color.ENDC}")
        print("  4. 银行流水对账 (自动勾兑)")
        print("  5. 生成往来对账单 (给客户/供应商)")
        print("  23. 往来对账 (导入外部账单核对) [新]")
        print("  24. 薪酬管理 (工资/个税/社保) [新]")
        print("  25. 发票管理 (进项/销项) [新]")
        print("  26. 加工费管理 (独立台账) [新]")
        print("  28. 会计实用工具箱 (大写/税额/日期) [新]")
        print("  6. 查找待补票记录")
        
        print(f"\n{Color.CYAN}📊 报表与分析{Color.ENDC}")
        print("  7. 生成可视化报表 (HTML)")
        print("  8. 每日经营简报 (老板看板)")
        print("  9. 财务体检 (风险扫描)")
        print("  10. 智能查数助手 (AI 问答)")
        print("  21. 生成年度报表 (可视化) [新]")
        
        print(f"\n{Color.CYAN}⚙️ 结账与设置{Color.ENDC}")
        print("  11. 月度结账 (归档/利润表)")
        print("  22. 一键年结 (全流程) [新]")
        print("  12. 计提固定资产折旧 [新]")
        print("  13. 税务统计")
        print("  14. 往来单位与别名管理 [新]")
        print("  15. 系统设置 (税率/AI Key)")
        print("  16. 导出标准凭证 (财务软件用) [新]")
        print("  17. 智能学习分类规则 (越用越聪明) [新]")
        print("  18. 万能查账 (金额/日期/关键词) [新]")
        print("  19. 导出云端数据到 Excel [备份]")
        print("  20. 启动文件夹监听模式 (支持Excel/图片) [新]")

        print(f"\n{Color.CYAN}🧰 实用工具{Color.ENDC}")
        print("  28. 会计常用工具箱 (大写/税额) [新]")
        
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
        elif choice == '27': register_voucher(client, APP_TOKEN)
        elif choice == '3': 
             import_from_excel(client, APP_TOKEN, None)
             
        elif choice == '4': 
             reconcile_bank_flow(client, APP_TOKEN, None)
             
        elif choice == '5': generate_partner_statement(client, APP_TOKEN)
        elif choice == '23': reconcile_partner_flow(client, APP_TOKEN, None)
        elif choice == '24': manage_salary_flow(client, APP_TOKEN)
        elif choice == '25': manage_invoice_flow(client, APP_TOKEN)
        elif choice == '26': manage_processing_fee_flow(client, APP_TOKEN)
        elif choice == '28': manage_small_tools(client, APP_TOKEN)
        elif choice == '6': export_missing_tickets(client, APP_TOKEN)
        
        elif choice == '7': generate_html_report(client, APP_TOKEN)
        elif choice == '8': daily_briefing(client, APP_TOKEN)
        elif choice == '9': financial_health_check(client, APP_TOKEN)
        elif choice == '10': ai_data_query(client, APP_TOKEN)
        
        elif choice == '11': monthly_close(client, APP_TOKEN)
        elif choice == '22': year_end_closing(client, APP_TOKEN)
        elif choice == '12': calculate_depreciation(client, APP_TOKEN)
        elif choice == '13': calculate_tax(client, APP_TOKEN)
        elif choice == '14': manage_partners_flow(client, APP_TOKEN)
        elif choice == '15': settings_menu()
        elif choice == '16': export_standard_voucher(client, APP_TOKEN)
        elif choice == '17': learn_category_rules(client, APP_TOKEN)
        elif choice == '18': quick_search_ledger(client, APP_TOKEN)
        elif choice == '19': export_to_excel(client, APP_TOKEN)
        elif choice == '20': monitor_folder_mode(client, APP_TOKEN)
        elif choice == '21': generate_annual_report(client, APP_TOKEN)
        
        elif choice == '97': 
             print(f"{Color.WARNING}⚠️  警告: 初始化将创建新表格。{Color.ENDC}")
             if input("确认初始化吗? (y/n): ").strip().lower() == 'y':
                 create_basic_info_table(client, APP_TOKEN)
                 create_ledger_table(client, APP_TOKEN)
                 create_partner_table(client, APP_TOKEN)
                 create_invoice_table(client, APP_TOKEN)
                 create_asset_table(client, APP_TOKEN)
                 create_salary_table(client, APP_TOKEN)
                 create_processing_fee_table(client, APP_TOKEN)
                 print(f"{Color.GREEN}✅ 初始化完成！{Color.ENDC}")
             
        elif choice == '99': show_cloud_urls(client, APP_TOKEN)
        
        else:
            print(f"{Color.FAIL}❌ 无效选项{Color.ENDC}")
            
        input("\n✅ 操作完成，按回车返回主菜单...")

def create_processing_fee_table(client, app_token):
    """创建加工费明细表"""
    table_id = get_table_id_by_name(client, app_token, "加工费明细表")
    if table_id:
        log.info("✅ 加工费明细表已存在", extra={"solution": "无需创建"})
        return table_id

    log.info("🔨 正在创建加工费明细表...", extra={"solution": "请稍候"})
    
    req = CreateAppTableRequest.builder() \
        .app_token(app_token) \
        .request_body(CreateAppTableRequestBody.builder()
            .table(AppTableCreateHeader.builder()
                .name("加工费明细表")
                .fields([
                    AppTableField.builder().field_name("日期").type(FT.DATE).build(),
                    AppTableField.builder().field_name("往来单位").type(FT.TEXT).build(),
                    AppTableField.builder().field_name("品名").type(FT.TEXT).build(),
                    AppTableField.builder().field_name("规格").type(FT.TEXT).build(),
                    AppTableField.builder().field_name("类型").type(FT.SELECT).property(
                        AppTableFieldProperty.builder().options([
                            AppTableFieldPropertyOption.builder().name("支出-外协加工").build(),
                            AppTableFieldPropertyOption.builder().name("收入-加工服务").build()
                        ]).build()
                    ).build(),
                    AppTableField.builder().field_name("计价方式").type(FT.SELECT).property(
                        AppTableFieldProperty.builder().options([
                            AppTableFieldPropertyOption.builder().name("按件/个").build(),
                            AppTableFieldPropertyOption.builder().name("按米长").build(),
                            AppTableFieldPropertyOption.builder().name("按重量").build(),
                            AppTableFieldPropertyOption.builder().name("按平方").build()
                        ]).build()
                    ).build(),
                    AppTableField.builder().field_name("数量").type(FT.NUMBER).build(),
                    AppTableField.builder().field_name("单位").type(FT.TEXT).build(),
                    AppTableField.builder().field_name("单价").type(FT.NUMBER).property(
                        AppTableFieldProperty.builder().formatter("0.000").build() # 单价保留3位小数
                    ).build(),
                    AppTableField.builder().field_name("总金额").type(FT.NUMBER).property(
                        AppTableFieldProperty.builder().formatter("0.00").build()
                    ).build(),
                    AppTableField.builder().field_name("备注").type(FT.TEXT).build()
                ])
                .build())
            .build()) \
        .build()

    resp = client.bitable.v1.app_table.create(req)
    if resp.success():
        log.info("✅ 加工费明细表创建成功", extra={"solution": "无"})
        return resp.data.table_id
    else:
        log.error(f"❌ 创建失败: {resp.msg}", extra={"solution": "检查权限"})
        return None

def create_processing_price_table(client, app_token):
    """创建加工费价目表 (Price List)"""
    table_id = get_table_id_by_name(client, app_token, "加工费价目表")
    if table_id: return table_id

    log.info("🔨 正在创建加工费价目表...", extra={"solution": "请稍候"})
    
    req = CreateAppTableRequest.builder() \
        .app_token(app_token) \
        .request_body(CreateAppTableRequestBody.builder()
            .table(AppTableCreateHeader.builder()
                .name("加工费价目表")
                .fields([
                    AppTableField.builder().field_name("品名").type(FT.TEXT).build(),
                    AppTableField.builder().field_name("规格").type(FT.TEXT).build(),
                    AppTableField.builder().field_name("单位").type(FT.TEXT).build(),
                    AppTableField.builder().field_name("单价").type(FT.NUMBER).property(
                        AppTableFieldProperty.builder().formatter("0.000").build()
                    ).build(),
                    AppTableField.builder().field_name("备注").type(FT.TEXT).build()
                ])
                .build())
            .build()) \
        .build()

    resp = client.bitable.v1.app_table.create(req)
    if resp.success():
        log.info("✅ 加工费价目表创建成功", extra={"solution": "无"})
        return resp.data.table_id
    else:
        log.error(f"❌ 创建价目表失败: {resp.msg}", extra={"solution": "检查权限"})
        return None

def manage_price_list(client, app_token):
    """维护加工费价目表"""
    table_id = create_processing_price_table(client, app_token)
    if not table_id: return

    while True:
        print(f"\n{Color.CYAN}📋 加工费价目表管理{Color.ENDC}")
        print("1. 查看/搜索价目")
        print("2. 新增单价 (逐条)")
        print("3. 修改/删除单价")
        print("4. Excel 批量导入 (高效)")
        print("0. 返回")
        
        choice = input("👉 请选择: ").strip()
        
        if choice == '0': break
        
        if choice == '1':
            records = get_all_records(client, app_token, table_id)
            if not records:
                print("📭 暂无价目")
            else:
                print(f"\n{'品名':<15} | {'规格':<15} | {'单位':<6} | {'单价':<8} | {'备注'}")
                print("-" * 70)
                filter_kw = input("🔍 搜索关键词 (回车显示全部): ").strip()
                count = 0
                for r in records:
                    f = r.fields
                    if filter_kw and (filter_kw not in f.get('品名','') and filter_kw not in f.get('规格','')):
                        continue
                    print(f"{f.get('品名',''):<15} | {f.get('规格',''):<15} | {f.get('单位',''):<6} | {f.get('单价',0):<8} | {f.get('备注','')}")
                    count += 1
                print(f"共找到 {count} 条记录")
        
        elif choice == '2':
            print("\n➕ 新增价目")
            name = input("品名 (如: 铝型材/螺丝): ").strip()
            spec = input("规格 (如: 黑色氧化/周长20cm): ").strip()
            unit = input("单位 (如: 米, kg, 件): ").strip()
            try:
                price = float(input("单价 (元): ").strip())
            except:
                print("❌ 单价无效")
                continue
            remark = input("备注 (选填): ").strip()
            
            fields = {
                "品名": name,
                "规格": spec,
                "单位": unit,
                "单价": price,
                "备注": remark
            }
            
            req = CreateAppTableRecordRequest.builder() \
                .app_token(app_token) \
                .table_id(table_id) \
                .request_body(AppTableRecord.builder().fields(fields).build()) \
                .build()
                
            if client.bitable.v1.app_table_record.create(req).success():
                print("✅ 价目已保存")
            else:
                print("❌ 保存失败")

        elif choice == '3':
            # 修改/删除
            print("\n🛠️ 修改/删除单价")
            kw = input("🔍 请输入品名/规格关键词搜索: ").strip()
            if not kw: continue
            
            records = get_all_records(client, app_token, table_id)
            candidates = []
            for r in records:
                f = r.fields
                if kw in f.get('品名','') or kw in f.get('规格',''):
                    candidates.append(r)
            
            if not candidates:
                print("❌ 未找到相关记录")
                continue
                
            print(f"\n{'序号':<4} | {'品名':<15} | {'规格':<15} | {'单价':<8}")
            for i, r in enumerate(candidates):
                f = r.fields
                print(f"{i+1:<4} | {f.get('品名',''):<15} | {f.get('规格',''):<15} | {f.get('单价',0):<8}")
                
            sel = input("\n👉 请输入序号 (0取消): ").strip()
            if not sel or sel == '0': continue
            
            try:
                idx = int(sel) - 1
                if 0 <= idx < len(candidates):
                    target = candidates[idx]
                    print(f"\n已选中: {target.fields.get('品名')} {target.fields.get('规格')} (当前单价: {target.fields.get('单价')})")
                    action = input("👉 请选择操作: 1.修改单价  2.删除记录  0.取消: ").strip()
                    
                    if action == '1':
                        new_price = float(input("请输入新单价: ").strip())
                        
                        req = UpdateAppTableRecordRequest.builder() \
                            .app_token(app_token) \
                            .table_id(table_id) \
                            .record_id(target.record_id) \
                            .request_body(AppTableRecord.builder().fields({"单价": new_price}).build()) \
                            .build()
                            
                        if client.bitable.v1.app_table_record.update(req).success():
                            print("✅ 修改成功")
                        else:
                            print("❌ 修改失败")
                            
                    elif action == '2':
                        if input("⚠️ 确认删除吗? (y/n): ").lower() == 'y':
                            req = DeleteAppTableRecordRequest.builder() \
                                .app_token(app_token) \
                                .table_id(table_id) \
                                .record_id(target.record_id) \
                                .build()
                            if client.bitable.v1.app_table_record.delete(req).success():
                                print("✅ 删除成功")
                            else:
                                print("❌ 删除失败")
            except Exception as e:
                print(f"❌ 操作错误: {e}")

        elif choice == '4':
            # Excel 导入
            print(f"\n{Color.OKBLUE}📂 Excel 批量导入价目表{Color.ENDC}")
            print("请准备 Excel 文件，包含以下列: [品名, 规格, 单位, 单价, 备注(选填)]")
            path = input("请输入文件路径 (直接回车扫描当前目录): ").strip()
            
            if not path:
                cands = [f for f in os.listdir('.') if '价目' in f and f.endswith('.xlsx')]
                if cands:
                    path = cands[0]
                    print(f"🔍 自动找到: {path}")
                else:
                    print("❌ 未找到文件")
                    continue
                    
            if not os.path.exists(path):
                print("❌ 文件不存在")
                continue
                
            try:
                df = pd.read_excel(path)
                required = ['品名', '规格', '单位', '单价']
                if not all(c in df.columns for c in required):
                    print(f"❌ 缺少必要列: {required}")
                    continue
                
                print(f"📄 读取到 {len(df)} 条记录，正在导入...")
                
                # 获取现有记录以进行排重/更新 (可选，这里简化为追加模式，或者先查后插)
                # 为了效率，暂用追加模式，用户需自行管理重复
                # 高级版：构建 map (name+spec -> record_id) 进行 upsert
                
                existing_map = {}
                print("🔄 正在同步现有数据以支持更新...")
                all_recs = get_all_records(client, app_token, table_id)
                if all_recs:
                    for r in all_recs:
                        key = f"{r.fields.get('品名')}_{r.fields.get('规格')}"
                        existing_map[key] = r.record_id
                
                batch_add = []
                update_count = 0
                
                for _, row in df.iterrows():
                    name = str(row['品名']).strip()
                    spec = str(row['规格']).strip()
                    key = f"{name}_{spec}"
                    
                    fields = {
                        "品名": name,
                        "规格": spec,
                        "单位": str(row['单位']).strip(),
                        "单价": float(row['单价']),
                        "备注": str(row.get('备注', ''))
                    }
                    
                    if key in existing_map:
                        # Update
                        rid = existing_map[key]
                        req = UpdateAppTableRecordRequest.builder() \
                            .app_token(app_token) \
                            .table_id(table_id) \
                            .record_id(rid) \
                            .request_body(AppTableRecord.builder().fields(fields).build()) \
                            .build()
                        client.bitable.v1.app_table_record.update(req)
                        update_count += 1
                        print(f"   🔄 更新: {name} {spec}")
                    else:
                        # Add
                        batch_add.append(AppTableRecord.builder().fields(fields).build())
                
                # Execute Batch Add
                if batch_add:
                    batch_size = 100
                    for i in range(0, len(batch_add), batch_size):
                        batch = batch_add[i:i+batch_size]
                        req = BatchCreateAppTableRecordRequest.builder() \
                            .app_token(app_token) \
                            .table_id(table_id) \
                            .request_body(BatchCreateAppTableRecordRequestBody.builder().records(batch).build()) \
                            .build()
                        client.bitable.v1.app_table_record.batch_create(req)
                        
                print(f"✅ 导入完成! 新增 {len(batch_add)} 条, 更新 {update_count} 条")
                
            except Exception as e:
                print(f"❌ 导入出错: {e}")


def ensure_processing_fee_fields(client, app_token, table_id):
    """确保加工费明细表包含 '品名' 和 '规格' 字段 (Migration)"""
    try:
        fields = client.bitable.v1.app_table_field.list(
            ListAppTableFieldRequest.builder().app_token(app_token).table_id(table_id).build()
        ).data.items
        
        field_names = [f.field_name for f in fields]
        
        if "品名" not in field_names:
            print("🔨 正在升级表结构: 添加 '品名'...")
            client.bitable.v1.app_table_field.create(
                CreateAppTableFieldRequest.builder().app_token(app_token).table_id(table_id)
                .request_body(AppTableField.builder().field_name("品名").type(FT.TEXT).build()).build()
            )
            
        if "规格" not in field_names:
            print("🔨 正在升级表结构: 添加 '规格'...")
            client.bitable.v1.app_table_field.create(
                CreateAppTableFieldRequest.builder().app_token(app_token).table_id(table_id)
                .request_body(AppTableField.builder().field_name("规格").type(FT.TEXT).build()).build()
            )
    except Exception as e:
        print(f"⚠️ 检查表结构失败: {e}")

def manage_processing_fee_flow(client, app_token):
    """加工费管理 (Menu 26)"""
    print(f"\n{Color.CYAN}🔧 加工费管理{Color.ENDC}")
    print("-----------------------------------")
    print("1. 登记加工费")
    print("2. 导出加工费明细 (Excel)")
    print("3. 维护价目表 (Price List)")
    print("0. 返回")
    
    choice = input("\n👉 请选择 (0-3): ").strip()
    
    if choice == '0': return
    
    if choice == '3':
        manage_price_list(client, app_token)
        return

    table_id = create_processing_fee_table(client, app_token) # 确保表存在
    if not table_id: return
    
    # 确保字段存在 (Migration)
    ensure_processing_fee_fields(client, app_token, table_id)
    
    if choice == '2':
        # 导出逻辑
        records = get_all_records(client, app_token, table_id)
        if not records:
            print("❌ 暂无数据")
            return
            
        data = []
        for r in records:
            f = r.fields
            ts = f.get("日期", 0)
            d_str = datetime.fromtimestamp(ts/1000).strftime("%Y-%m-%d") if ts else "-"
            data.append({
                "日期": d_str,
                "往来单位": f.get("往来单位", ""),
                "品名": f.get("品名", ""),
                "规格": f.get("规格", ""),
                "类型": f.get("类型", ""),
                "计价方式": f.get("计价方式", ""),
                "数量": f.get("数量", 0),
                "单位": f.get("单位", ""),
                "单价": f.get("单价", 0),
                "总金额": f.get("总金额", 0),
                "备注": f.get("备注", "")
            })
        
        df = pd.DataFrame(data)
        fname = f"加工费明细_{datetime.now().strftime('%Y%m%d%H%M')}.xlsx"
        df.to_excel(fname, index=False)
        print(f"✅ 已导出: {fname}")
        try: os.startfile(fname)
        except: pass
        return

    if choice == '1':
        # 登记逻辑
        # 预加载价目表以支持智能学习
        print("🔄 正在加载价目表以支持智能学习...")
        pt_id = create_processing_price_table(client, app_token)
        price_list_map = {} # (name, spec) -> record
        if pt_id:
            p_recs = get_all_records(client, app_token, pt_id)
            if p_recs:
                for r in p_recs:
                    key = (r.fields.get('品名', '').strip(), r.fields.get('规格', '').strip())
                    price_list_map[key] = r
        
        # 记忆变量，用于批量录入时的默认值
        last_date = datetime.now().strftime('%Y-%m-%d')
        last_partner = ""
        last_type_choice = "1"
        
        # 批次累计变量
        batch_total_amount = 0.0
        batch_count = 0
        batch_mode = False

        while True:
            # 显示批次累计信息
            if batch_count > 0:
                print(f"\n{Color.HEADER}📊 当前批次累计: {batch_total_amount:,.2f} 元 (共 {batch_count} 笔){Color.ENDC}")
            
            # 定义类型映射
            type_map = {'1': '支出-外协加工', '2': '收入-加工服务'}
            
            if batch_mode:
                print(f"\n{Color.OKBLUE}🔒 批量录入模式 (输入 0 退出当前模式){Color.ENDC}")
                print(f"   📅 {last_date} | 🏢 {last_partner} | 🔖 {type_map.get(last_type_choice)}")
                date_str = last_date
                partner = last_partner
                p_type = type_map.get(last_type_choice, "支出-外协加工")
            else:
                print(f"\n{Color.BOLD}📝 新增加工费记录 (输入 0 退出){Color.ENDC}")
                
                # 日期
                date_str = input(f"日期 (默认 {last_date}): ").strip()
                if date_str == '0': break
                if not date_str: date_str = last_date
                else: last_date = date_str
                
                # 往来单位
                p_prompt = f"往来单位 (默认 '{last_partner}'): " if last_partner else "往来单位: "
                partner = input(p_prompt).strip()
                if not partner and last_partner:
                    partner = last_partner
                
                if not partner: 
                    print("❌ 必须输入单位")
                    continue
                last_partner = partner
                    
                # 类型
                def_type_name = type_map.get(last_type_choice, "支出-外协加工")
                print(f"类型: 1. 支出-外协加工  2. 收入-加工服务 (默认 {last_type_choice}.{def_type_name})")
                t_choice = input("👉 请选择 (1/2): ").strip()
                if not t_choice: t_choice = last_type_choice
                else: last_type_choice = t_choice
                
                p_type = type_map.get(t_choice, "支出-外协加工")
                
                # 询问是否进入批量模式
                if input("⚡ 是否锁定表头进入批量极速模式? (y/n) [n]: ").strip().lower() == 'y':
                    batch_mode = True
                    print(f"{Color.OKGREEN}✅ 已进入批量模式，输入 '0' 可退出{Color.ENDC}")
            
            # 统一录入/搜索逻辑
            selected_record = None
            price = 0.0
            calc_remark = ""
            product_name = ""
            product_spec = ""
            
            print(f"\n{Color.CYAN}🔍 品名录入 (支持关键词搜索，输入 0 返回):{Color.ENDC}")
            p_input = input("👉 品名/关键词: ").strip()
            
            if p_input == '0':
                if batch_mode:
                    batch_mode = False
                    print("🔓 已退出批量模式")
                    continue
                else:
                    break
            
            if not p_input:
                print("❌ 品名不能为空")
                continue

            # 智能搜索
            matches = []
            if price_list_map:
                for r in price_list_map.values():
                    # 简单匹配: 输入包含在品名或规格中，或者品名包含输入
                    p_val = r.fields.get('品名', '')
                    s_val = r.fields.get('规格', '')
                    if p_input in p_val or p_input in s_val:
                        matches.append(r)
            
            # 显示匹配项
            if matches:
                print(f"💡 找到 {len(matches)} 个匹配项:")
                # 按匹配度排序 (完全匹配优先)
                matches.sort(key=lambda x: 0 if x.fields.get('品名') == p_input else 1)
                
                for i, m in enumerate(matches[:5]): # 最多显示5个
                    f = m.fields
                    print(f"   {i+1}. {f.get('品名')} {f.get('规格')} @ {f.get('单价')}元/{f.get('单位')}")
                
                sel = input("👉 选择序号 (回车跳过，直接使用输入值): ").strip()
                if sel.isdigit() and 0 < int(sel) <= len(matches):
                    selected_record = matches[int(sel)-1]
                    print(f"✅ 已选择: {selected_record.fields.get('品名')}")
                else:
                    product_name = p_input # 用户坚持使用输入值
            else:
                product_name = p_input

            if selected_record:
                # 自动推断模式
                f = selected_record.fields
                product_name = f.get('品名', '')
                product_spec = f.get('规格', '')
                unit = f.get('单位', '件')
                
                if unit in ['米', 'm']: m_choice = '2'
                elif unit in ['kg', 'kg', '公斤']: m_choice = '3'
                elif unit in ['平方', 'm²', 'm2']: m_choice = '4'
                else: m_choice = '1'
                
                base_unit = unit
                price = float(f.get('单价', 0))
                calc_remark = f"[价目] {product_name} {product_spec}"
                
                try:
                    qty_str = input(f"数量 ({base_unit}) [支持算式]: ").strip()
                    if '*' in qty_str or '+' in qty_str:
                        try:
                            qty = float(eval(qty_str, {"__builtins__": None}, {}))
                            print(f"   🧮 计算结果: {qty}")
                        except:
                            print("❌ 算式无效")
                            continue
                    else:
                        qty = float(qty_str)
                except:
                    print("❌ 数量无效")
                    continue
            else:
                # 手动模式 - 询问品名/规格 (Smart Learning Key)
                # product_name 已经在上面赋值了
                product_spec = input("规格 (Spec): ").strip()
                
                # 计价方式
                print("计价方式:")
                print("1. 按件/个 (Quantity)")
                print("2. 按米长 (Length)")
                print("3. 按重量 (Weight)")
                print("4. 按平方 (Area)")
                
                m_choice = input("👉 请选择 (1-4): ").strip()
                modes = {'1': '按件/个', '2': '按米长', '3': '按重量', '4': '按平方'}
                mode_name = modes.get(m_choice, '按件/个')
                
                units = {'1': '件', '2': '米', '3': 'kg', '4': 'm²'}
                base_unit = units.get(m_choice, '单位')
                
                # 数量
                try:
                    qty_str = input(f"数量 ({base_unit}) [支持算式]: ").strip()
                    if '*' in qty_str or '+' in qty_str:
                        try:
                            qty = float(eval(qty_str, {"__builtins__": None}, {}))
                            print(f"   🧮 计算结果: {qty}")
                        except:
                            print("❌ 算式无效")
                            continue
                    else:
                        qty = float(qty_str)
                except:
                    print("❌ 数量无效")
                    continue
                
                # 单价计算器/转换器
                if m_choice in ['2', '3']:
                    print(f"\n{Color.CYAN}🧮 单价助手: {Color.ENDC}")
                    print("   A. 通过【米重/线密度】转换 (g/m)")
                    print("   B. 通过【规格/周长】按比例折算")
                    print("   C. 跳过")
                    
                    helper_choice = input("   👉 请选择 (A/B/C) [默认C]: ").strip().upper()
                    
                    if helper_choice == 'A':
                        try:
                            gram_weight = float(input("   请输入米重/线密度 (克/米, g/m): ").strip())
                            
                            if m_choice == '2': # 按米计价
                                kg_price = float(input("   请输入公斤价 (元/kg): ").strip())
                                price = kg_price * (gram_weight / 1000)
                                print(f"   ✅ 计算结果: {kg_price}元/kg * ({gram_weight}g/1000) = {price:.4f} 元/米")
                                calc_remark = f"[米重折算] {gram_weight}g/m, 基价{kg_price}元/kg"
                                
                            elif m_choice == '3': # 按重量计价
                                meter_price = float(input("   请输入米价 (元/米): ").strip())
                                if gram_weight > 0:
                                    price = meter_price / (gram_weight / 1000)
                                    print(f"   ✅ 计算结果: {meter_price}元/米 / ({gram_weight}g/1000) = {price:.4f} 元/kg")
                                    calc_remark = f"[米重折算] {gram_weight}g/m, 基价{meter_price}元/米"
                                
                            if input(f"   👉 是否使用计算出的单价 {price:.4f}? (y/n): ").strip().lower() != 'y':
                                price = 0.0 # 重置
                                calc_remark = ""
                                
                        except Exception as e:
                            print(f"   ❌ 计算出错: {e}")
                    
                    elif helper_choice == 'B':
                        try:
                            base_width = float(input("   请输入基准规格/周长 [默认1.0]: ").strip() or 1.0)
                            base_price = float(input(f"   请输入基准单价 (元/{base_unit}): ").strip())
                            actual_width = float(input("   请输入实际规格/周长: ").strip())
                            
                            if base_width > 0:
                                price = base_price * (actual_width / base_width)
                                print(f"   ✅ 计算结果: {base_price}元 * ({actual_width}/{base_width}) = {price:.4f} 元/{base_unit}")
                                calc_remark = f"[规格折算] 基准{base_width}@{base_price}元 -> {actual_width}"
                                
                            if input(f"   👉 是否使用计算出的单价 {price:.4f}? (y/n): ").strip().lower() != 'y':
                                price = 0.0
                                calc_remark = ""
                        except Exception as e:
                            print(f"   ❌ 计算出错: {e}")
            
            # 如果没有计算或未采用计算结果
            if price == 0.0:
                try:
                    price = float(input(f"单价 (元/{base_unit}): ").strip())
                except:
                    print("❌ 单价无效")
                    continue
            
            total = round(qty * price, 2)
            
            # 重新获取 mode_name 如果是从价目表选择的 (因为 mode_name 之前可能没设置)
            modes = {'1': '按件/个', '2': '按米长', '3': '按重量', '4': '按平方'}
            mode_name = modes.get(m_choice, '按件/个')

            print(f"💰 总金额: {total:,.2f} 元")
            
            r_prompt = f"备注 (默认 '{calc_remark}'): " if calc_remark else "备注: "
            remark = input(r_prompt).strip()
            if not remark and calc_remark:
                remark = calc_remark
            elif remark and calc_remark:
                remark = f"{calc_remark} {remark}"
            
            # 确认保存
            print(f"\n即将保存: [{date_str}] {partner} - {product_name} {product_spec} - {mode_name} {qty}{base_unit} * {price} = {total}")
            if input("确认保存? (y/n): ").strip().lower() == 'y':
                fields = {
                    "日期": int(pd.to_datetime(date_str).timestamp() * 1000),
                    "往来单位": partner,
                    "品名": product_name,
                    "规格": product_spec,
                    "类型": p_type,
                    "计价方式": mode_name,
                    "数量": qty,
                    "单位": base_unit,
                    "单价": price,
                    "总金额": total,
                    "备注": remark
                }
                
                req = CreateAppTableRecordRequest.builder() \
                    .app_token(app_token) \
                    .table_id(table_id) \
                    .request_body(AppTableRecord.builder().fields(fields).build()) \
                    .build()
                    
                resp = client.bitable.v1.app_table_record.create(req)
                if resp.success():
                    print("✅ 保存成功！")
                    batch_total_amount += total
                    batch_count += 1
                    
                    # --- 智能学习逻辑 (Smart Learning) ---
                    if product_name:
                        key = (product_name, product_spec)
                        existing_rec = price_list_map.get(key)
                        
                        if existing_rec:
                            # 存在，检查价格差异
                            old_price = float(existing_rec.fields.get('单价', 0))
                            if abs(old_price - price) > 0.0001:
                                print(f"\n{Color.WARNING}💡 价格变动提醒: 价目表单价为 {old_price}，本次录入 {price}{Color.ENDC}")
                                if input("   👉 是否更新价目表? (y/n) [n]: ").strip().lower() == 'y':
                                    req = UpdateAppTableRecordRequest.builder() \
                                        .app_token(app_token) \
                                        .table_id(pt_id) \
                                        .record_id(existing_rec.record_id) \
                                        .request_body(AppTableRecord.builder().fields({"单价": price}).build()) \
                                        .build()
                                    if client.bitable.v1.app_table_record.update(req).success():
                                        print("   ✅ 价目表已更新")
                                        # Update local cache
                                        existing_rec.fields['单价'] = price
                                        price_list_map[key] = existing_rec
                        else:
                            # 不存在，提示新增
                            print(f"\n{Color.OKGREEN}💡 发现新项目: {product_name} {product_spec} @ {price}{Color.ENDC}")
                            if input("   👉 是否添加到价目表? (y/n) [y]: ").strip().lower() != 'n':
                                fields = {
                                    "品名": product_name,
                                    "规格": product_spec,
                                    "单位": base_unit,
                                    "单价": price,
                                    "备注": "自动学习"
                                }
                                req = CreateAppTableRecordRequest.builder() \
                                    .app_token(app_token) \
                                    .table_id(pt_id) \
                                    .request_body(AppTableRecord.builder().fields(fields).build()) \
                                    .build()
                                resp = client.bitable.v1.app_table_record.create(req)
                                if resp.success():
                                    print("   ✅ 已添加到价目表")
                                    # Update local cache
                                    price_list_map[key] = resp.data.record

                else:
                    print(f"❌ 保存失败: {resp.msg}")



# 发票管理流程 (新)
def manage_invoice_flow(client, app_token):
    """发票管理：录入销项/进项，查看统计"""
    while True:
        print(f"\n{Color.HEADER}🧾 发票管理 (进项/销项){Color.ENDC}")
        print("---------------------------------------")
        print("1. [销项] 登记已开发票 (给客户)")
        print("2. [进项] 登记收到发票 (供应商)")
        print("3. 查看最近发票记录 (20条)")
        print("4. 发票统计 (本月/本年)")
        print("0. 返回主菜单")
        
        choice = input(f"{Color.OKBLUE}请选择功能 (0-4): {Color.ENDC}").strip()
        
        if choice == '0': break
        
        table_id = get_table_id_by_name(client, app_token, "发票管理表")
        if not table_id:
            create_invoice_table(client, app_token)
            table_id = get_table_id_by_name(client, app_token, "发票管理表")
            
        if choice in ['1', '2']:
            is_sales = (choice == '1')
            type_prefix = "销项" if is_sales else "进项"
            
            # 批量模式状态
            batch_mode = False
            b_code = ""
            b_date = ""
            b_type = ""
            b_target = ""
            
            while True:
                print(f"\n{Color.BOLD}➕ 登记{type_prefix}发票{Color.ENDC}")
                if batch_mode:
                    print(f"{Color.OKBLUE}🔒 批量锁定模式 (输入 0 退出当前模式){Color.ENDC}")
                    print(f"   📅 {b_date} | 🏷️ {b_type} | 🏢 {b_target} | 🔢 代码:{b_code}")
                    inv_code = b_code
                    inv_date = b_date
                    inv_type = b_type
                    target = b_target
                else:
                    print("   (输入 0 返回上级菜单)")

                # 1. 发票号码
                inv_no = input("发票号码: ").strip()
                if inv_no == '0':
                    if batch_mode:
                        batch_mode = False
                        print("🔓 已退出批量锁定模式")
                        continue
                    break
                
                if not batch_mode:
                    inv_code = input("发票代码 (选填): ").strip()
                    inv_date = input("开票日期 (YYYY-MM-DD, 回车默认今天): ").strip()
                    if not inv_date: inv_date = datetime.now().strftime("%Y-%m-%d")
                    
                    print(f"发票类型: 1.专票  2.普票")
                    t_choice = input("请选择 (1/2): ").strip()
                    inv_type = f"{type_prefix}{'专票' if t_choice=='1' else '普票'}"
                    
                    target = input(f"{'购买方' if is_sales else '销售方'}名称: ").strip()

                # 金额处理
                amount = 0.0
                tax = 0.0
                auto_calculated = False

                while True:
                    print(f"💰 金额录入 (输入 'h 113' 可按含税价自动拆分，默认税率13%/1%/3%)")
                    amt_input = input("   不含税金额: ").strip()
                    
                    # 检查是否为含税模式
                    if amt_input.lower().startswith('h') or amt_input.startswith('含'):
                        try:
                            # 解析含税总额
                            total_inc = float(amt_input[1:].strip())
                            
                            # 询问税率
                            rate_str = input("   请输入税率% (默认 1, 输入 13/6/3/1): ").strip()
                            if not rate_str: rate_str = "1" # 普票常见1%，专票常见13%
                            rate = float(rate_str) / 100.0
                            
                            amount = total_inc / (1 + rate)
                            tax = total_inc - amount
                            amount = round(amount, 2)
                            tax = round(tax, 2)
                            
                            print(f"   ✨ 自动拆分: 不含税 {amount} + 税额 {tax} = 总额 {total_inc}")
                            auto_calculated = True
                            break
                        except:
                            print("❌ 格式错误，请使用 'h 113'")
                            continue

                    try:
                        amount = float(amt_input or 0)
                        break
                    except:
                        print("❌ 金额无效")
                
                try:
                    if not auto_calculated:
                        # 简易税额计算辅助
                        tax_input = input("税额 (直接回车可按税率估算): ").strip()
                        if not tax_input and amount > 0:
                             pass
                        tax = float(tax_input or 0)
                    
                    total = amount + tax
                    print(f"💰 价税合计: {total:,.2f}")
                except:
                    print("❌ 金额输入错误")
                    continue
                
                remark = f"手动录入 {datetime.now().strftime('%Y-%m-%d %H:%M')}"
                    
                fields = {
                    "发票号码": inv_no,
                    "发票代码": inv_code,
                    "开票日期": int(pd.to_datetime(inv_date).timestamp() * 1000),
                    "类型": inv_type,
                    "购买方/销售方": target,
                    "不含税金额": amount,
                    "税额": tax,
                    "价税合计": total,
                    "状态": "正常",
                    "备注": remark
                }
                
                req = BatchCreateAppTableRecordRequest.builder().app_token(app_token).table_id(table_id).request_body(
                    BatchCreateAppTableRecordRequestBody.builder().records([AppTableRecord.builder().fields(fields).build()]).build()).build()
                
                if client.bitable.v1.app_table_record.batch_create(req).success():
                    print(f"{Color.OKGREEN}✅ {type_prefix}发票已登记: {inv_no}{Color.ENDC}")
                    
                    # 询问进入批量模式
                    if not batch_mode:
                        if input("⚡ 是否锁定表头(代码/日期/类型/对方)进入批量模式? (y/n) [n]: ").strip().lower() == 'y':
                            batch_mode = True
                            b_code = inv_code
                            b_date = inv_date
                            b_type = inv_type
                            b_target = target
                            print(f"{Color.OKGREEN}✅ 已进入批量模式，接下来只需输入号码和金额{Color.ENDC}")
                else:
                    print("❌ 登记失败")
                
        elif choice == '3':
            records = get_all_records(client, app_token, table_id)
            if not records:
                print("📭 暂无发票记录")
            else:
                print(f"\n{Color.UNDERLINE}最近 20 条发票记录:{Color.ENDC}")
                print(f"{'日期':<12} | {'类型':<8} | {'号码':<10} | {'金额':<10} | {'对方名称'}")
                print("-" * 60)
                records.sort(key=lambda x: x.fields.get("开票日期", 0))
                for r in records[-20:]:
                    f = r.fields
                    ts = f.get("开票日期", 0)
                    d_str = datetime.fromtimestamp(ts/1000).strftime("%Y-%m-%d") if ts else "-"
                    print(f"{d_str:<12} | {f.get('类型',''):<8} | {f.get('发票号码',''):<10} | {f.get('价税合计',0):<10.2f} | {f.get('购买方/销售方','')}")

        elif choice == '4':
            # 简单统计
            records = get_all_records(client, app_token, table_id)
            input_tax = 0.0
            output_tax = 0.0
            cur_month = datetime.now().strftime("%Y-%m")
            m_in = 0.0
            m_out = 0.0
            
            for r in records:
                f = r.fields
                tax = float(f.get("税额", 0))
                itype = f.get("类型", "")
                ts = f.get("开票日期", 0)
                d_str = datetime.fromtimestamp(ts/1000).strftime("%Y-%m") if ts else ""
                
                if "进项" in itype:
                    input_tax += tax
                    if d_str == cur_month: m_in += tax
                elif "销项" in itype:
                    output_tax += tax
                    if d_str == cur_month: m_out += tax
                    
            print(f"\n📊 发票统计摘要")
            print(f"本月 ({cur_month}): 进项税 {m_in:,.2f} | 销项税 {m_out:,.2f} | 差额 {m_out - m_in:,.2f}")
            print(f"累计历史: 进项税 {input_tax:,.2f} | 销项税 {output_tax:,.2f}")
            input("\n按回车继续...")

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

def financial_health_check(client, app_token, target_year=None):
    """一键财务体检：扫描税务风险和数据异常 (生成HTML报告)"""
    if target_year:
        log.info(f"🏥 正在进行 {target_year}年度 财务体检...", extra={"solution": "全面扫描中"})
        year = target_year
    else:
        log.info("🏥 正在进行财务体检...", extra={"solution": "全面扫描中"})
        year = datetime.now().year
    
    table_id = get_table_id_by_name(client, app_token, "日常台账表")
    if not table_id:
        log.error("❌ 找不到日常台账表", extra={"solution": "请先初始化表格"})
        return

    # 优化：只获取指定年度数据
    start_ts = int(datetime(year, 1, 1).timestamp() * 1000)
    end_ts = int(datetime(year + 1, 1, 1).timestamp() * 1000)
    filter_str = f'AND(CurrentValue.[记账日期]>={start_ts}, CurrentValue.[记账日期]<{end_ts})'

    records = get_all_records(client, app_token, table_id, filter_info=filter_str)
    
    risks = []
    stats = {
        "total_count": len(records),
        "cash_txns": 0,
        "no_ticket_amt": 0.0,
        "large_cash": 0,
        "total_income": 0.0,
        "total_expense": 0.0
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
        expense_type = f.get("费用归类", "")
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
        
        # 统计收支
        if biz_type == "收入":
            stats["total_income"] += amt
        elif biz_type in ["支出", "费用"]:
            stats["total_expense"] += amt
        
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

        # 规则 5: 费用归类缺失 (Daily Closing Validation)
        if biz_type == "费用" and (not expense_type or expense_type in ["", "nan", "未知"]):
            msg = f"⚠️ [数据完善] 费用归类缺失: {amt}元 ({remark})"
            risks.append(msg)
            risk_details.append({"date": date_str, "type": "归类缺失", "amt": amt, "desc": "请补充费用归类", "level": "中"})
            print(msg)

    # 规则 4: 本月折旧未计提
    current_month_str = datetime.now().strftime('%Y-%m')
    check_depreciation = False
    
    # 仅当检查当前年份时，才检查本月折旧
    if year == datetime.now().year:
        check_depreciation = True
        
    has_depreciation = False
    if check_depreciation:
        for r in records:
            f = r.fields
            # 检查是否为本月记录且费用归类为折旧摊销
            r_date = f.get("记账日期", 0)
            try:
                r_month = datetime.fromtimestamp(r_date/1000).strftime('%Y-%m')
            except:
                r_month = ""
                
            if r_month == current_month_str and f.get("费用归类") == "折旧摊销":
                has_depreciation = True
                break
            
        if not has_depreciation:
            msg = f"⚠️ [合规风险] 本月尚未计提固定资产折旧 ({current_month_str})"
            risks.append(msg)
            risk_details.append({"date": datetime.now().strftime("%Y-%m-%d"), "type": "折旧缺失", "amt": 0, "desc": "本月未计提折旧", "level": "中"})
            print(msg)

    # -------------------------------------------------------------------------
    # 新增：加工费明细表体检
    # -------------------------------------------------------------------------
    pf_table_id = get_table_id_by_name(client, app_token, "加工费明细表")
    if pf_table_id:
        log.info("🏥 正在扫描加工费明细表...", extra={"solution": "无"})
        # 针对 "日期" 字段的过滤器
        pf_filter = f'AND(CurrentValue.[日期]>={start_ts}, CurrentValue.[日期]<{end_ts})'
        try:
            pf_records = get_all_records(client, app_token, pf_table_id, filter_info=pf_filter)
            
            for r in pf_records:
                f = r.fields
                date_ts = f.get("日期", 0)
                try:
                    d_str = datetime.fromtimestamp(date_ts/1000).strftime("%Y-%m-%d")
                except:
                    d_str = "未知"
                
                # Check 1: 有数量无金额
                total = float(f.get("总金额", 0))
                qty = float(f.get("数量", 0))
                price = float(f.get("单价", 0))
                
                if qty != 0 and total == 0:
                     msg = f"⚠️ [加工费异常] 有数量无金额: {d_str} {f.get('往来单位','')}"
                     risks.append(msg)
                     risk_details.append({"date": d_str, "type": "加工费异常", "amt": 0, "desc": "有数量无金额", "level": "高"})
                     print(msg)
                
                # Check 2: 单价为0 (提醒)
                if qty != 0 and price == 0:
                     msg = f"ℹ️ [数据提醒] 加工费单价为0: {d_str} {f.get('往来单位','')}"
                     print(msg)

                # Check 3: 往来单位缺失
                if not f.get("往来单位"):
                     msg = f"⚠️ [数据缺失] 加工费未指定往来单位: {d_str}"
                     risks.append(msg)
                     risk_details.append({"date": d_str, "type": "数据缺失", "amt": total, "desc": "未指定往来单位", "level": "中"})
                     print(msg)
        except Exception as e:
            log.warning(f"⚠️ 扫描加工费表失败: {e}")

    # 规则 6: 经营风险预警 (New)
    income = stats["total_income"]
    expense = stats["total_expense"]
    
    if income > 0:
        margin = (income - expense) / income
        if margin < 0:
             msg = f"⚠️ [经营风险] 当前处于亏损状态 (净利润率: {margin*100:.1f}%)"
             risks.append(msg)
             risk_details.append({"date": datetime.now().strftime("%Y-%m-%d"), "type": "亏损预警", "amt": income-expense, "desc": "支出大于收入", "level": "高"})
             print(msg)
        elif margin < 0.1:
             msg = f"⚠️ [经营风险] 利润率过低 ({margin*100:.1f}%)"
             print(msg)
    elif expense > 0 and income == 0:
         msg = f"⚠️ [经营风险] 本期暂无收入"
         risks.append(msg)
         risk_details.append({"date": datetime.now().strftime("%Y-%m-%d"), "type": "亏损预警", "amt": -expense, "desc": "只有支出无收入", "level": "高"})
         print(msg)

    print("-" * 40)
    print(f"扫描完成。共 {len(records)} 条记录。")
    print(f"本期收入: {stats['total_income']:.2f} 元")
    print(f"本期支出: {stats['total_expense']:.2f} 元")
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

def generate_daily_html_report(client, app_token, summary_log=None):
    """生成每日结账 HTML 报告"""
    log.info("📊 正在生成今日结账报告...", extra={"solution": "无"})
    
    table_id = get_table_id_by_name(client, app_token, "日常台账表")
    if not table_id: return None
    
    # 1. 获取今日数据
    now = datetime.now()
    today_start = datetime(now.year, now.month, now.day)
    start_ts = int(today_start.timestamp() * 1000)
    filter_str = f'CurrentValue.[记账日期]>={start_ts}'
    
    records = get_all_records(client, app_token, table_id, filter_info=filter_str)
    
    today_income = 0.0
    today_expense = 0.0
    tx_count = len(records)
    details = []
    
    for r in records:
        f = r.fields
        amt = float(f.get("实际收付金额", 0))
        b_type = f.get("业务类型", "")
        desc = f.get("备注") or f.get("往来单位费用", "")
        
        if b_type == "收款":
            today_income += amt
        elif b_type in ["付款", "费用"]:
            today_expense += amt
            
        details.append({
            "type": b_type,
            "amt": amt,
            "desc": desc,
            "partner": f.get("往来单位费用", "-")
        })
        
    # 2. 待办事项 (检查文件夹)
    pending_files = []
    watch_dir = "待处理单据"
    if os.path.exists(watch_dir):
        pending_files = [f for f in os.listdir(watch_dir) if not f.startswith("~$") and f.lower().endswith(('.xlsx', '.png', '.jpg'))]
        
    # 3. 待补票据 (简单查询)
    missing_count = 0
    # 这里为了速度，暂时不全量查，只看传入的 summary_log 是否有提及
    
    # 生成 HTML
    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="utf-8">
        <title>每日结账报告 - {now.strftime('%Y-%m-%d')}</title>
        <style>
            body {{ font-family: 'Segoe UI', sans-serif; background: #f0f2f5; padding: 20px; }}
            .container {{ max-width: 800px; margin: 0 auto; background: white; padding: 30px; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }}
            h1 {{ color: #1a1a1a; border-bottom: 3px solid #3498db; padding-bottom: 10px; }}
            .summary-box {{ display: flex; gap: 20px; margin: 20px 0; }}
            .card {{ flex: 1; background: #f8f9fa; padding: 15px; border-radius: 8px; text-align: center; border: 1px solid #e9ecef; }}
            .num {{ font-size: 24px; font-weight: bold; color: #2c3e50; }}
            .label {{ color: #7f8c8d; font-size: 14px; }}
            .income {{ color: #27ae60; }}
            .expense {{ color: #c0392b; }}
            
            h3 {{ margin-top: 30px; color: #34495e; border-left: 5px solid #3498db; padding-left: 10px; }}
            table {{ width: 100%; border-collapse: collapse; margin-top: 10px; }}
            th, td {{ padding: 10px; text-align: left; border-bottom: 1px solid #eee; }}
            th {{ background: #f8f9fa; color: #7f8c8d; }}
            
            .log-box {{ background: #2c3e50; color: #ecf0f1; padding: 15px; border-radius: 5px; font-family: monospace; max-height: 200px; overflow-y: auto; }}
            .pending-alert {{ background: #fff3cd; color: #856404; padding: 10px; border-radius: 5px; margin-top: 10px; }}
        </style>
    </head>
    <body>
        <div class="container">
            <h1>📅 每日结账报告 <small style="font-size: 16px; color: #7f8c8d">{now.strftime('%Y-%m-%d %H:%M')}</small></h1>
            
            <div class="summary-box">
                <div class="card">
                    <div class="num income">+{today_income:,.2f}</div>
                    <div class="label">今日收款</div>
                </div>
                <div class="card">
                    <div class="num expense">-{today_expense:,.2f}</div>
                    <div class="label">今日支出</div>
                </div>
                <div class="card">
                    <div class="num">{tx_count}</div>
                    <div class="label">业务笔数</div>
                </div>
                <div class="card">
                    <div class="num" style="color: #2980b9">{today_income - today_expense:,.2f}</div>
                    <div class="label">今日净现金流</div>
                </div>
            </div>
            
            <h3>📝 今日业务明细</h3>
            """
            
    if details:
        html += "<table><thead><tr><th>类型</th><th>金额</th><th>对象</th><th>摘要</th></tr></thead><tbody>"
        for d in details:
            color = "green" if d['type'] == "收款" else "red"
            html += f"<tr><td><span style='color:{color}'>{d['type']}</span></td><td>{d['amt']:,.2f}</td><td>{d['partner']}</td><td>{d['desc']}</td></tr>"
        html += "</tbody></table>"
    else:
        html += "<p style='color:#999; text-align:center'>今日暂无收支记录</p>"
        
    if pending_files:
        html += f"""
        <h3>🔔 待办提醒</h3>
        <div class="pending-alert">
            <strong>发现 {len(pending_files)} 个待处理文件:</strong><br>
            {', '.join(pending_files[:5])} {'...' if len(pending_files)>5 else ''}
        </div>
        """
        
    if summary_log:
        html += """
        <h3>⚙️ 系统处理日志</h3>
        <div class="log-box">
        """
        for line in summary_log:
            html += f"<div>{line}</div>"
        html += "</div>"
        
    html += """
        </div>
    </body>
    </html>
    """
    
    report_dir = "日结报告"
    if not os.path.exists(report_dir): os.makedirs(report_dir)
    filename = f"{report_dir}/日结_{now.strftime('%Y%m%d')}.html"
    
    with open(filename, "w", encoding="utf-8") as f:
        f.write(html)
        
    log.info(f"📄 日结报告已生成: {filename}")
    return filename

def generate_annual_report(client, app_token, year=None):
    """生成年度财务报表"""
    if not year:
        year = datetime.now().year
    
    log.info(f"📊 正在生成 {year} 年度报表...", extra={"solution": "无"})
    
    table_id = get_table_id_by_name(client, app_token, "日常台账表")
    if not table_id: return False
    
    # 获取全年数据
    records = get_all_records(client, app_token, table_id)
    
    monthly_data = {m: {"income": 0.0, "expense": 0.0, "count": 0} for m in range(1, 13)}
    category_summary = {} # {category: amount}
    
    total_income = 0.0
    total_expense = 0.0
    
    for r in records:
        f = r.fields
        ts = f.get("记账日期", 0)
        if not ts: continue
        
        dt = datetime.fromtimestamp(ts / 1000)
        if dt.year != year: continue
        
        amt = float(f.get("实际收付金额", 0))
        b_type = f.get("业务类型", "")
        cat = f.get("费用归类", "未分类")
        
        monthly_data[dt.month]["count"] += 1
        
        if b_type == "收款":
            monthly_data[dt.month]["income"] += amt
            total_income += amt
        elif b_type in ["付款", "费用"]:
            monthly_data[dt.month]["expense"] += amt
            total_expense += amt
            
            # 统计费用分类
            if cat not in category_summary: category_summary[cat] = 0.0
            category_summary[cat] += amt

    # 生成 HTML
    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="utf-8">
        <title>{year} 年度财务报表</title>
        <style>
            body {{ font-family: 'Segoe UI', sans-serif; background: #f0f2f5; padding: 20px; }}
            .container {{ max-width: 1000px; margin: 0 auto; background: white; padding: 40px; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }}
            h1 {{ color: #2c3e50; text-align: center; border-bottom: 2px solid #3498db; padding-bottom: 20px; }}
            .summary-cards {{ display: flex; gap: 20px; margin: 30px 0; }}
            .card {{ flex: 1; background: #f8f9fa; padding: 20px; border-radius: 8px; text-align: center; box-shadow: 0 1px 3px rgba(0,0,0,0.05); }}
            .num {{ font-size: 28px; font-weight: bold; margin: 10px 0; }}
            .income {{ color: #27ae60; }}
            .expense {{ color: #c0392b; }}
            .profit {{ color: #2980b9; }}
            
            table {{ width: 100%; border-collapse: collapse; margin-top: 20px; }}
            th, td {{ padding: 12px; text-align: center; border-bottom: 1px solid #eee; }}
            th {{ background: #34495e; color: white; }}
            tr:nth-child(even) {{ background: #f9f9f9; }}
            
            .chart-box {{ height: 300px; margin-top: 40px; border: 1px solid #eee; padding: 10px; }}
            h2 {{ color: #34495e; margin-top: 40px; border-left: 5px solid #3498db; padding-left: 10px; }}
        </style>
    </head>
    <body>
        <div class="container">
            <h1>📅 {year} 年度财务报表</h1>
            
            <div class="summary-cards">
                <div class="card">
                    <div class="label">全年总收入</div>
                    <div class="num income">¥{total_income:,.2f}</div>
                </div>
                <div class="card">
                    <div class="label">全年总支出</div>
                    <div class="num expense">¥{total_expense:,.2f}</div>
                </div>
                <div class="card">
                    <div class="label">全年净利润</div>
                    <div class="num profit">¥{total_income - total_expense:,.2f}</div>
                </div>
            </div>
            
            <h2>📈 月度收支明细</h2>
            <table>
                <thead>
                    <tr>
                        <th>月份</th>
                        <th>收入</th>
                        <th>支出</th>
                        <th>结余</th>
                        <th>笔数</th>
                    </tr>
                </thead>
                <tbody>
    """
    
    for m in range(1, 13):
        d = monthly_data[m]
        balance = d["income"] - d["expense"]
        color = "#27ae60" if balance >= 0 else "#c0392b"
        html += f"""
        <tr>
            <td>{m}月</td>
            <td style="color:#27ae60">+{d['income']:,.2f}</td>
            <td style="color:#c0392b">-{d['expense']:,.2f}</td>
            <td style="font-weight:bold; color:{color}">{balance:,.2f}</td>
            <td>{d['count']}</td>
        </tr>
        """
        
    html += """
                </tbody>
            </table>
            
            <h2>📊 费用支出分布</h2>
            <table>
                <thead>
                    <tr>
                        <th>费用类型</th>
                        <th>金额</th>
                        <th>占比</th>
                    </tr>
                </thead>
                <tbody>
    """
    
    sorted_cats = sorted(category_summary.items(), key=lambda x: x[1], reverse=True)
    for cat, amt in sorted_cats:
        percent = (amt / total_expense * 100) if total_expense > 0 else 0
        html += f"""
        <tr>
            <td>{cat}</td>
            <td>{amt:,.2f}</td>
            <td>{percent:.1f}%</td>
        </tr>
        """
        
    html += """
                </tbody>
            </table>
            
            <p style="margin-top: 40px; color: #7f8c8d; text-align: center; font-size: 12px;">生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} | Powered by 飞书财务小助手</p>
        </div>
    </body>
    </html>
    """
    
    report_dir = "年度报告"
    if not os.path.exists(report_dir): os.makedirs(report_dir)
    filename = f"{report_dir}/{year}年度报表_{datetime.now().strftime('%Y%m%d')}.html"
    
    with open(filename, "w", encoding="utf-8") as f:
        f.write(html)
        
    log.info(f"✅ 年度报表已生成: {filename}")
    os.startfile(filename) # 自动打开
    return True

# 全局台账缓存 (用于快速查账)
GLOBAL_LEDGER_CACHE = None

def quick_search_ledger(client, app_token):
    """快速查账 (优化版：支持金额、日期、关键词智能搜索)"""
    global GLOBAL_LEDGER_CACHE
    
    print(f"\n{Color.HEADER}🔍 万能查账助手{Color.ENDC}")
    print(f"{Color.CYAN}提示：支持输入 金额(100)、日期(2024-01)、关键词(京东){Color.ENDC}")
    
    table_id = get_table_id_by_name(client, app_token, "日常台账表")
    if not table_id: return
    
    # 首次加载或刷新
    if GLOBAL_LEDGER_CACHE is None:
        print("⏳ 正在拉取全量台账数据 (首次加载)...")
        GLOBAL_LEDGER_CACHE = get_all_records(client, app_token, table_id)
        print(f"✅ 已缓存 {len(GLOBAL_LEDGER_CACHE)} 条记录")
    else:
        print(f"⚡ 使用本地缓存 ({len(GLOBAL_LEDGER_CACHE)} 条) - 输入 'reload' 强制刷新")
    
    import re

    while True:
        print("-" * 30)
        query = input("👉 请输入查询内容 (q:退出, reload:刷新): ").strip()
        
        if not query: continue
        if query.lower() == 'q': break
        
        if query.lower() == 'reload':
            print("🔄 正在刷新数据...")
            GLOBAL_LEDGER_CACHE = get_all_records(client, app_token, table_id)
            print(f"✅ 刷新完成: {len(GLOBAL_LEDGER_CACHE)} 条")
            continue
            
        matches = []
        total_income = 0.0
        total_expense = 0.0
        
        # 智能解析查询意图
        target_amt = None
        target_month = None
        target_date = None
        is_fuzzy_text = True
        
        # 1. 尝试解析为金额
        try:
            target_amt = float(query)
            # 即使解析为金额，如果它是整数，也可能是文本的一部分（如单号），所以不完全禁用文本搜索
            # 但为了精准，如果用户输入的是 100.00，那肯定是金额。如果是 2024，可能是年份。
            # 策略：如果匹配到金额，就加入；同时如果文本匹配，也加入。
        except:
            pass
            
        # 2. 尝试解析为日期 (YYYY-MM 或 YYYY-MM-DD)
        if re.match(r"^\d{4}-\d{2}$", query):
            target_month = query
            is_fuzzy_text = False # 明确是月份搜索
        elif re.match(r"^\d{4}-\d{2}-\d{2}$", query):
            target_date = query
            is_fuzzy_text = False # 明确是日期搜索

        print(f"🔎 正在搜索: {query} ...")
        
        for r in GLOBAL_LEDGER_CACHE:
            f = r.fields
            
            # 提取关键字段
            ts = f.get("记账日期", 0)
            date_str = datetime.fromtimestamp(ts/1000).strftime("%Y-%m-%d") if ts else ""
            r_amt = float(f.get("实际收付金额", 0))
            desc = f.get("备注", "")
            partner = f.get("往来单位费用", "")
            cat = f.get("费用归类", "")
            b_type = f.get("业务类型", "")
            
            # 构建全文本索引 (用于模糊搜)
            full_text = f"{date_str} {r_amt} {desc} {partner} {b_type} {cat}".lower()
            
            matched = False
            
            # 逻辑 A: 金额匹配 (绝对值误差 0.01)
            if target_amt is not None:
                if abs(abs(r_amt) - abs(target_amt)) < 0.01:
                    matched = True
            
            # 逻辑 B: 日期匹配
            if target_month and date_str.startswith(target_month):
                matched = True
            if target_date and date_str == target_date:
                matched = True
                    
            # 逻辑 C: 文本匹配 (只要关键词在任意字段中)
            if query.lower() in full_text:
                matched = True
            
            if matched:
                matches.append(r.fields) # Store fields directly
                if b_type == "收款":
                    total_income += r_amt
                elif b_type in ["付款", "费用"]:
                    total_expense += r_amt

        if matches:
            print(f"\n✅ 找到 {len(matches)} 条记录:")
            print(f"{'日期':<12} | {'类型':<6} | {'金额':<10} | {'往来单位/备注'}")
            print("-" * 65)
            
            # 按日期排序
            matches.sort(key=lambda x: x.get("记账日期", 0), reverse=True)
            
            limit = 20
            for m in matches[:limit]:
                ts = m.get("记账日期", 0)
                d_str = datetime.fromtimestamp(ts/1000).strftime("%Y-%m-%d") if ts else "-"
                amt = float(m.get("实际收付金额", 0))
                b_type = m.get("业务类型", "")
                desc = f"{m.get('往来单位费用', '')} {m.get('备注', '')}".replace('\n', ' ')
                
                # Color
                amt_str = f"{amt:,.2f}"
                row_str = f"{d_str:<12} | {b_type:<6} | {amt_str:<10} | {desc[:30]}"
                if b_type == "收款":
                    print(f"{Color.GREEN}{row_str}{Color.ENDC}")
                else:
                    print(row_str)
                
            if len(matches) > limit:
                print(f"... (还有 {len(matches)-limit} 条，建议导出)")
                
            print("-" * 65)
            net = total_income - total_expense
            print(f"💰 统计结果: 收入 {total_income:,.2f} | 支出 {total_expense:,.2f} | 净额 {net:,.2f}")
            
            # 导出选项
            opt = input("👉 导出结果? (x=Excel / h=HTML报表 / n=取消) [n]: ").strip().lower()
            
            if opt == 'x':
                try:
                    df = pd.DataFrame(matches)
                    # 简单清洗列
                    cols = ["记账日期", "业务类型", "费用归类", "实际收付金额", "往来单位费用", "备注"]
                    # 确保列存在
                    exist_cols = [c for c in cols if c in df.columns]
                    df = df[exist_cols]
                    # 格式化日期
                    if "记账日期" in df.columns:
                        df["记账日期"] = df["记账日期"].apply(lambda x: datetime.fromtimestamp(x/1000).strftime("%Y-%m-%d") if x else "")
                    
                    fname = f"查询结果_{query.replace(':','-')}_{datetime.now().strftime('%H%M%S')}.xlsx"
                    df.to_excel(fname, index=False)
                    print(f"✅ 已导出: {fname}")
                    os.startfile(fname) # Windows only
                except Exception as e:
                    print(f"❌ 导出失败: {e}")

            elif opt == 'h':
                try:
                    # 准备数据
                    # 1. 支出分类统计
                    cat_stats = {}
                    for m in matches:
                        if m.get("业务类型") in ["付款", "费用"]:
                            c = m.get("费用归类", "未分类")
                            if not c: c = "未分类"
                            amt = float(m.get("实际收付金额", 0))
                            cat_stats[c] = cat_stats.get(c, 0) + amt
                    
                    sorted_cats = sorted(cat_stats.items(), key=lambda x: x[1], reverse=True)[:10] # Top 10
                    
                    # 生成 SVG 柱状图
                    chart_html = ""
                    if sorted_cats:
                        max_val = sorted_cats[0][1] if sorted_cats else 1
                        svg_height = len(sorted_cats) * 40 + 20
                        svg_bars = ""
                        for idx, (k, v) in enumerate(sorted_cats):
                            y = idx * 40
                            w = (v / max_val) * 500
                            color = "#e74c3c"
                            svg_bars += f"""
                            <g transform="translate(0, {y})">
                                <text x="0" y="20" font-size="12" fill="#555">{k}</text>
                                <rect x="100" y="5" width="{w}" height="20" fill="{color}" rx="3" opacity="0.8"/>
                                <text x="{100 + w + 10}" y="20" font-size="12" fill="#333">{v:,.2f}</text>
                            </g>
                            """
                        
                        chart_html = f"""
                        <div class="chart-container">
                            <div class="chart-title">💸 支出分类 TOP10</div>
                            <svg width="100%" height="{svg_height}" viewBox="0 0 800 {svg_height}">
                                <g transform="translate(20, 10)">
                                    {svg_bars}
                                </g>
                            </svg>
                        </div>
                        """
                    
                    # 生成 HTML
                    html = f"""
                    <!DOCTYPE html>
                    <html>
                    <head>
                        <meta charset="utf-8">
                        <title>查账报告 - {query}</title>
                        <style>
                            body {{ font-family: 'Segoe UI', sans-serif; background: #f5f7fa; color: #333; padding: 20px; }}
                            .container {{ max-width: 900px; margin: 0 auto; background: white; padding: 40px; border-radius: 12px; box-shadow: 0 4px 20px rgba(0,0,0,0.05); }}
                            .header {{ border-bottom: 2px solid #eee; padding-bottom: 20px; margin-bottom: 30px; }}
                            .title h1 {{ margin: 0; font-size: 24px; color: #2c3e50; }}
                            .cards {{ display: flex; gap: 20px; margin-bottom: 40px; }}
                            .card {{ flex: 1; background: #f8f9fa; padding: 20px; border-radius: 8px; text-align: center; border: 1px solid #e9ecef; }}
                            .card .val {{ font-size: 24px; font-weight: bold; margin-bottom: 5px; }}
                            .card .lbl {{ font-size: 13px; color: #7f8c8d; }}
                            .c-in {{ color: #27ae60; }}
                            .c-out {{ color: #c0392b; }}
                            .c-net {{ color: #2980b9; }}
                            
                            table {{ width: 100%; border-collapse: collapse; font-size: 14px; }}
                            th {{ text-align: left; padding: 12px; background: #f8f9fa; color: #7f8c8d; border-bottom: 2px solid #eee; }}
                            td {{ padding: 12px; border-bottom: 1px solid #f1f1f1; }}
                            tr:hover {{ background: #fafafa; }}
                            
                            .chart-container {{ margin: 30px 0; padding: 20px; border: 1px solid #eee; border-radius: 8px; background: #fff; }}
                            .chart-title {{ font-size: 14px; font-weight: bold; color: #34495e; margin-bottom: 15px; }}
                        </style>
                    </head>
                    <body>
                        <div class="container">
                            <div class="header">
                                <div class="title">
                                    <h1>🔎 查账报告: {query}</h1>
                                    <p style="color:#999; font-size:12px; margin-top:5px">生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M')}</p>
                                </div>
                            </div>
                            
                            <div class="cards">
                                <div class="card">
                                    <div class="val c-in">+{total_income:,.2f}</div>
                                    <div class="lbl">总收入</div>
                                </div>
                                <div class="card">
                                    <div class="val c-out">-{total_expense:,.2f}</div>
                                    <div class="lbl">总支出</div>
                                </div>
                                <div class="card">
                                    <div class="val c-net">{net:+,.2f}</div>
                                    <div class="lbl">净额</div>
                                </div>
                                <div class="card">
                                    <div class="val">{len(matches)}</div>
                                    <div class="lbl">记录数</div>
                                </div>
                            </div>
                            
                            {chart_html}
                            
                            <h3>📝 详细记录</h3>
                            <table>
                                <thead>
                                    <tr>
                                        <th>日期</th>
                                        <th>类型</th>
                                        <th>费用归类</th>
                                        <th>往来/备注</th>
                                        <th style="text-align:right">金额</th>
                                    </tr>
                                </thead>
                                <tbody>
                    """
                    
                    for m in matches:
                        ts = m.get("记账日期", 0)
                        d_str = datetime.fromtimestamp(ts/1000).strftime("%Y-%m-%d") if ts else "-"
                        b_type = m.get("业务类型", "")
                        cat = m.get("费用归类", "")
                        desc = f"{m.get('往来单位费用', '')} {m.get('备注', '')}"
                        amt = float(m.get("实际收付金额", 0))
                        
                        color = "#333"
                        if b_type == "收款": color = "#27ae60"
                        elif b_type in ["付款", "费用"]: color = "#c0392b"
                        
                        html += f"""
                        <tr>
                            <td>{d_str}</td>
                            <td><span style="padding:2px 6px; border-radius:4px; font-size:12px; background:{'#e8f5e9' if b_type=='收款' else '#ffebee'}; color:{color}">{b_type}</span></td>
                            <td>{cat}</td>
                            <td>{desc}</td>
                            <td style="text-align:right; font-weight:bold; color:{color}">{amt:,.2f}</td>
                        </tr>
                        """
                        
                    html += """
                                </tbody>
                            </table>
                        </div>
                    </body>
                    </html>
                    """
                    
                    report_dir = "查询报告"
                    if not os.path.exists(report_dir): os.makedirs(report_dir)
                    fname = f"{report_dir}/查账_{query.replace(':','-')}_{datetime.now().strftime('%Y%m%d%H%M%S')}.html"
                    
                    with open(fname, "w", encoding="utf-8") as f:
                        f.write(html)
                        
                    print(f"✅ 报表已生成: {fname}")
                    try:
                        os.startfile(os.path.abspath(fname))
                    except:
                        pass
                    
                except Exception as e:
                    print(f"❌ 生成报表失败: {e}")
                    import traceback
                    traceback.print_exc()
                    
        else:
            print("❌ 未找到相关记录")

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
    parser.add_argument("--reconcile-partner", type=str, nargs='?', const="", help="[新] 往来对账（Excel路径）")
    parser.add_argument("--salary", action="store_true", help="[新] 薪酬管理")
    parser.add_argument("--invoice", action="store_true", help="[新] 发票管理")
    parser.add_argument("--processing-fee", action="store_true", help="[新] 加工费管理")
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
        create_salary_table(client, APP_TOKEN) # 新增
        create_processing_fee_table(client, APP_TOKEN) # 新增
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
        manage_partners_flow(client, APP_TOKEN)

    if args.show_urls:
        show_cloud_urls(client, APP_TOKEN)

    if args.export_excel:
        export_to_excel(client, APP_TOKEN)

    if args.reconcile_partner:
        reconcile_partner_flow(client, APP_TOKEN, args.reconcile_partner)

    if args.salary:
        manage_salary_flow(client, APP_TOKEN)

    if args.invoice:
        manage_invoice_flow(client, APP_TOKEN)

    if args.processing_fee:
        manage_processing_fee_flow(client, APP_TOKEN)

if __name__ == "__main__":
    main()
