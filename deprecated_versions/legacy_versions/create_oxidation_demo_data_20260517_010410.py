# -*- coding: utf-8 -*-
"""
氧化加工厂示例数据生成器
为小白会计提供真实场景的示例数据，方便学习和测试
"""
import pandas as pd
from datetime import datetime, timedelta
import random
import os

# 确保输出目录存在
OUTPUT_DIR = "财务数据/示例数据"
os.makedirs(OUTPUT_DIR, exist_ok=True)

def generate_oxidation_demo_data():
    """生成氧化加工厂完整示例数据"""
    
    print("=" * 60)
    print("     氧化加工厂示例数据生成器")
    print("=" * 60)
    
    # 1. 生成往来单位数据
    print("\n📋 正在生成往来单位数据...")
    partners_data = generate_partners()
    partners_file = os.path.join(OUTPUT_DIR, "示例_往来单位.xlsx")
    partners_data.to_excel(partners_file, index=False, sheet_name="往来单位")
    print(f"✅ 已生成：{partners_file}")
    
    # 2. 生成加工订单数据
    print("\n📋 正在生成加工订单数据...")
    orders_data = generate_orders()
    orders_file = os.path.join(OUTPUT_DIR, "示例_加工订单.xlsx")
    orders_data.to_excel(orders_file, index=False, sheet_name="加工订单")
    print(f"✅ 已生成：{orders_file}")
    
    # 3. 生成银行流水数据（G银行-有票）
    print("\n📋 正在生成G银行流水数据...")
    g_bank_data = generate_g_bank_records(orders_data)
    g_bank_file = os.path.join(OUTPUT_DIR, "示例_G银行流水.xlsx")
    g_bank_data.to_excel(g_bank_file, index=False, sheet_name="日常台账表")
    print(f"✅ 已生成：{g_bank_file}")
    
    # 4. 生成银行流水数据（N银行/微信-现金）
    print("\n📋 正在生成N银行微信流水数据...")
    n_bank_data = generate_n_bank_records()
    n_bank_file = os.path.join(OUTPUT_DIR, "示例_N银行微信流水.xlsx")
    n_bank_data.to_excel(n_bank_file, index=False, sheet_name="日常台账表")
    print(f"✅ 已生成：{n_bank_file}")
    
    # 5. 生成综合示例文件
    print("\n📋 正在生成综合示例文件...")
    comprehensive_file = os.path.join(OUTPUT_DIR, "氧化加工厂完整示例数据.xlsx")
    with pd.ExcelWriter(comprehensive_file, engine='openpyxl') as writer:
        partners_data.to_excel(writer, sheet_name="往来单位", index=False)
        orders_data.to_excel(writer, sheet_name="加工订单", index=False)
        g_bank_data.to_excel(writer, sheet_name="G银行流水", index=False)
        n_bank_data.to_excel(writer, sheet_name="N银行微信流水", index=False)
    print(f"✅ 已生成：{comprehensive_file}")
    
    print("\n" + "=" * 60)
    print("✅ 所有示例数据生成完成！")
    print(f"📁 文件位置：{OUTPUT_DIR}")
    print("=" * 60)
    print("\n💡 使用说明：")
    print("1. 先导入【示例_往来单位.xlsx】建立客户供应商档案")
    print("2. 再导入【示例_加工订单.xlsx】建立订单记录")
    print("3. 最后导入银行流水进行对账练习")
    print("4. 或直接使用【氧化加工厂完整示例数据.xlsx】一次性查看所有数据")
    print("=" * 60)

def generate_partners():
    """生成往来单位数据"""
    partners = []
    
    # 客户数据（5个）
    customers = [
        {"单位名称": "华为技术有限公司", "单位类型": "客户", "别名列表": "华为\n华为科技\nHuawei", 
         "联系人": "张经理", "联系电话": "13800138001", "备注": "VIP客户，月结30天"},
        {"单位名称": "小米科技有限公司", "单位类型": "客户", "别名列表": "小米\n小米科技\nXiaomi",
         "联系人": "李总", "联系电话": "13800138002", "备注": "长期合作客户"},
        {"单位名称": "OPPO广东移动通信有限公司", "单位类型": "客户", "别名列表": "OPPO\nOPPO手机\n欧珀",
         "联系人": "王采购", "联系电话": "13800138003", "备注": "季度结算"},
        {"单位名称": "比亚迪汽车工业有限公司", "单位类型": "客户", "别名列表": "比亚迪\nBYD\n比亚迪汽车",
         "联系人": "赵主管", "联系电话": "13800138004", "备注": "汽车配件氧化"},
        {"单位名称": "格力电器股份有限公司", "单位类型": "客户", "别名列表": "格力\n格力电器\nGREE",
         "联系人": "刘经理", "联系电话": "13800138005", "备注": "空调配件加工"}
    ]
    
    # 供应商数据（8个）
    suppliers = [
        {"单位名称": "鑫达喷砂加工厂", "单位类型": "供应商", "别名列表": "鑫达喷砂\n鑫达厂",
         "联系人": "陈老板", "联系电话": "13900139001", "备注": "喷砂外发合作商"},
        {"单位名称": "华美拉丝加工厂", "单位类型": "供应商", "别名列表": "华美拉丝\n华美厂",
         "联系人": "林师傅", "联系电话": "13900139002", "备注": "拉丝外发合作商"},
        {"单位名称": "精工抛光加工厂", "单位类型": "供应商", "别名列表": "精工抛光\n精工厂",
         "联系人": "吴老板", "联系电话": "13900139003", "备注": "抛光外发合作商"},
        {"单位名称": "顺达化工原料有限公司", "单位类型": "供应商", "别名列表": "顺达化工\n顺达",
         "联系人": "周经理", "联系电话": "13900139004", "备注": "三酸、片碱供应商"},
        {"单位名称": "永兴化工贸易公司", "单位类型": "供应商", "别名列表": "永兴化工\n永兴",
         "联系人": "郑总", "联系电话": "13900139005", "备注": "亚钠、色粉供应商"},
        {"单位名称": "佳洁除油剂厂", "单位类型": "供应商", "别名列表": "佳洁\n佳洁除油剂",
         "联系人": "孙老板", "联系电话": "13900139006", "备注": "除油剂供应商"},
        {"单位名称": "鸿运挂具制造厂", "单位类型": "供应商", "别名列表": "鸿运挂具\n鸿运",
         "联系人": "马师傅", "联系电话": "13900139007", "备注": "挂具供应商"},
        {"单位名称": "万达工业园物业", "单位类型": "供应商", "别名列表": "万达物业\n工业园物业",
         "联系人": "物业中心", "联系电话": "0755-88888888", "备注": "厂房租赁"}
    ]
    
    # 既是客户又是供应商（2个）
    both = [
        {"单位名称": "京东办公用品专营店", "单位类型": "两者", "别名列表": "京东\n京东办公\nJD",
         "联系人": "客服", "联系电话": "400-606-5500", "备注": "采购办公用品，偶尔有小批量加工订单"},
        {"单位名称": "阿里巴巴五金批发", "单位类型": "两者", "别名列表": "阿里巴巴\n阿里\n1688",
         "联系人": "在线客服", "联系电话": "400-800-1688", "备注": "采购原材料，偶尔有加工需求"}
    ]
    
    partners = customers + suppliers + both
    return pd.DataFrame(partners)

def generate_orders():
    """生成加工订单数据"""
    orders = []
    base_date = datetime(2026, 2, 1)
    
    # 订单模板（10个典型订单）
    order_templates = [
        {"客户名称": "华为技术有限公司", "物品名称": "铝合金手机外壳", "计价单位": "件", 
         "数量": 1000, "单价": 2.5, "工序明细": "喷砂、氧化、封孔", "外发工序": "喷砂", "外发成本": 300},
        {"客户名称": "小米科技有限公司", "物品名称": "不锈钢装饰条", "计价单位": "米长",
         "数量": 500, "单价": 8.0, "工序明细": "拉丝、氧化", "外发工序": "拉丝", "外发成本": 400},
        {"客户名称": "OPPO广东移动通信有限公司", "物品名称": "铝合金中框", "计价单位": "件",
         "数量": 800, "单价": 3.2, "工序明细": "抛光、氧化、封孔", "外发工序": "抛光", "外发成本": 350},
        {"客户名称": "比亚迪汽车工业有限公司", "物品名称": "汽车铝型材", "计价单位": "米重",
         "数量": 200, "单价": 15.0, "工序明细": "氧化、封孔", "外发工序": "", "外发成本": 0},
        {"客户名称": "格力电器股份有限公司", "物品名称": "空调散热片", "计价单位": "平方",
         "数量": 50, "单价": 80.0, "工序明细": "氧化", "外发工序": "", "外发成本": 0},
        {"客户名称": "华为技术有限公司", "物品名称": "铝合金支架", "计价单位": "只",
         "数量": 5000, "单价": 0.8, "工序明细": "喷砂、氧化", "外发工序": "喷砂", "外发成本": 500},
        {"客户名称": "小米科技有限公司", "物品名称": "铝棒", "计价单位": "条",
         "数量": 300, "单价": 12.0, "工序明细": "氧化、封孔", "外发工序": "", "外发成本": 0},
        {"客户名称": "OPPO广东移动通信有限公司", "物品名称": "铝合金按键", "计价单位": "个",
         "数量": 10000, "单价": 0.5, "工序明细": "拉丝、氧化", "外发工序": "拉丝", "外发成本": 600},
        {"客户名称": "比亚迪汽车工业有限公司", "物品名称": "铝管", "计价单位": "米长",
         "数量": 1000, "单价": 6.5, "工序明细": "抛光、氧化", "外发工序": "抛光", "外发成本": 450},
        {"客户名称": "格力电器股份有限公司", "物品名称": "铝合金面板", "计价单位": "件",
         "数量": 1500, "单价": 4.0, "工序明细": "氧化、封孔", "外发工序": "", "外发成本": 0}
    ]
    
    for i, template in enumerate(order_templates, 1):
        order_date = base_date + timedelta(days=i-1)
        order_amount = template["数量"] * template["单价"]
        
        # 模拟不同的收款状态
        if i <= 3:
            paid_amount = order_amount  # 已全额收款
            status = "已结算"
        elif i <= 6:
            paid_amount = order_amount * 0.5  # 已收50%
            status = "已完工"
        else:
            paid_amount = 0  # 未收款
            status = "生产中"
        
        unpaid_amount = order_amount - paid_amount
        
        order = {
            "订单编号": f"PO2026020{i:02d}",
            "客户名称": template["客户名称"],
            "订单日期": order_date.strftime("%Y-%m-%d"),
            "物品名称": template["物品名称"],
            "计价单位": template["计价单位"],
            "数量": template["数量"],
            "单价": template["单价"],
            "订单金额": order_amount,
            "已收款金额": paid_amount,
            "未收款金额": unpaid_amount,
            "工序明细": template["工序明细"],
            "外发工序": template["外发工序"],
            "外发成本": template["外发成本"],
            "订单状态": status,
            "备注": f"第{i}批订单"
        }
        orders.append(order)
    
    return pd.DataFrame(orders)

def generate_g_bank_records(orders_df):
    """生成G银行流水（有票，对公账户）"""
    records = []
    base_date = datetime(2026, 2, 1)
    
    # 1. 客户付款（对应订单）
    # 前3个订单全额收款
    for i in range(3):
        order = orders_df.iloc[i]
        record_date = base_date + timedelta(days=i+2)
        records.append({
            "记账日期": record_date.strftime("%Y-%m-%d"),
            "业务类型": "收款",
            "费用归类": "加工费收入",
            "往来单位费用": order["客户名称"],
            "账面金额": order["订单金额"],
            "实际收付金额": order["订单金额"],
            "交易银行": "G银行基本户",
            "是否现金": "否",
            "是否有票": "有票",
            "备注": f"收{order['订单编号']}加工费"
        })
    
    # 订单4-6部分收款（50%）
    for i in range(3, 6):
        order = orders_df.iloc[i]
        record_date = base_date + timedelta(days=i+2)
        records.append({
            "记账日期": record_date.strftime("%Y-%m-%d"),
            "业务类型": "收款",
            "费用归类": "加工费收入",
            "往来单位费用": order["客户名称"],
            "账面金额": order["订单金额"] * 0.5,
            "实际收付金额": order["订单金额"] * 0.5,
            "交易银行": "G银行基本户",
            "是否现金": "否",
            "是否有票": "有票",
            "备注": f"收{order['订单编号']}加工费（预付50%）"
        })
    
    # 2. 供应商付款（原材料）
    supplier_payments = [
        {"日期": base_date + timedelta(days=3), "供应商": "顺达化工原料有限公司", 
         "金额": 5000, "分类": "原材料-三酸", "备注": "采购硫酸、硝酸"},
        {"日期": base_date + timedelta(days=5), "供应商": "永兴化工贸易公司",
         "金额": 3000, "分类": "原材料-亚钠", "备注": "采购亚硫酸钠"},
        {"日期": base_date + timedelta(days=7), "供应商": "顺达化工原料有限公司",
         "金额": 2000, "分类": "原材料-片碱", "备注": "采购片碱"},
    ]
    
    for payment in supplier_payments:
        records.append({
            "记账日期": payment["日期"].strftime("%Y-%m-%d"),
            "业务类型": "付款",
            "费用归类": payment["分类"],
            "往来单位费用": payment["供应商"],
            "账面金额": payment["金额"],
            "实际收付金额": payment["金额"],
            "交易银行": "G银行基本户",
            "是否现金": "否",
            "是否有票": "有票",
            "备注": payment["备注"]
        })
    
    # 3. 外发加工费
    outsource_payments = [
        {"日期": base_date + timedelta(days=4), "供应商": "鑫达喷砂加工厂",
         "金额": 800, "分类": "外发加工-喷砂", "备注": "订单PO001、PO006喷砂费"},
        {"日期": base_date + timedelta(days=6), "供应商": "华美拉丝加工厂",
         "金额": 1000, "分类": "外发加工-拉丝", "备注": "订单PO002、PO008拉丝费"},
        {"日期": base_date + timedelta(days=8), "供应商": "精工抛光加工厂",
         "金额": 800, "分类": "外发加工-抛光", "备注": "订单PO003、PO009抛光费"},
    ]
    
    for payment in outsource_payments:
        records.append({
            "记账日期": payment["日期"].strftime("%Y-%m-%d"),
            "业务类型": "付款",
            "费用归类": payment["分类"],
            "往来单位费用": payment["供应商"],
            "账面金额": payment["金额"],
            "实际收付金额": payment["金额"],
            "交易银行": "G银行基本户",
            "是否现金": "否",
            "是否有票": "有票",
            "备注": payment["备注"]
        })
    
    # 4. 固定支出
    fixed_expenses = [
        {"日期": base_date + timedelta(days=1), "单位": "万达工业园物业",
         "金额": 8000, "分类": "房租", "备注": "2月厂房租金"},
        {"日期": base_date + timedelta(days=10), "单位": "国家电网",
         "金额": 3500, "分类": "水电费", "备注": "1月电费"},
    ]
    
    for expense in fixed_expenses:
        records.append({
            "记账日期": expense["日期"].strftime("%Y-%m-%d"),
            "业务类型": "费用",
            "费用归类": expense["分类"],
            "往来单位费用": expense["单位"],
            "账面金额": expense["金额"],
            "实际收付金额": expense["金额"],
            "交易银行": "G银行基本户",
            "是否现金": "否",
            "是否有票": "有票",
            "备注": expense["备注"]
        })
    
    return pd.DataFrame(records)

def generate_n_bank_records():
    """生成N银行/微信流水（现金账户，无票）"""
    records = []
    base_date = datetime(2026, 2, 1)
    
    # 1. 小额现金收入
    cash_income = [
        {"日期": base_date + timedelta(days=2), "客户": "散户", "金额": 500,
         "分类": "加工费收入", "备注": "零星小件氧化", "银行": "微信"},
        {"日期": base_date + timedelta(days=5), "客户": "散户", "金额": 800,
         "分类": "加工费收入", "备注": "个人客户铝件氧化", "银行": "N银行（现金）"},
    ]
    
    for income in cash_income:
        records.append({
            "记账日期": income["日期"].strftime("%Y-%m-%d"),
            "业务类型": "收款",
            "费用归类": income["分类"],
            "往来单位费用": income["客户"],
            "账面金额": income["金额"],
            "实际收付金额": income["金额"],
            "交易银行": income["银行"],
            "是否现金": "是",
            "是否有票": "无票",
            "备注": income["备注"]
        })
    
    # 2. 日常小额支出
    daily_expenses = [
        {"日期": base_date + timedelta(days=1), "单位": "佳洁除油剂厂",
         "金额": 600, "分类": "原材料-除油剂", "备注": "采购除油剂", "银行": "微信"},
        {"日期": base_date + timedelta(days=3), "单位": "永兴化工贸易公司",
         "金额": 450, "分类": "原材料-色粉", "备注": "采购黑色色粉", "银行": "N银行（现金）"},
        {"日期": base_date + timedelta(days=4), "单位": "鸿运挂具制造厂",
         "金额": 800, "分类": "挂具", "备注": "采购挂具配件", "银行": "微信"},
        {"日期": base_date + timedelta(days=6), "单位": "京东办公用品专营店",
         "金额": 350, "分类": "日常费用", "备注": "采购办公用品", "银行": "微信"},
        {"日期": base_date + timedelta(days=7), "单位": "中国石化",
         "金额": 200, "分类": "差旅费-加油", "备注": "送货加油", "银行": "微信"},
        {"日期": base_date + timedelta(days=9), "单位": "美团外卖",
         "金额": 180, "分类": "业务招待费", "备注": "员工午餐", "银行": "微信"},
    ]
    
    for expense in daily_expenses:
        records.append({
            "记账日期": expense["日期"].strftime("%Y-%m-%d"),
            "业务类型": "付款",
            "费用归类": expense["分类"],
            "往来单位费用": expense["单位"],
            "账面金额": expense["金额"],
            "实际收付金额": expense["金额"],
            "交易银行": expense["银行"],
            "是否现金": "是",
            "是否有票": "无票",
            "备注": expense["备注"]
        })
    
    return pd.DataFrame(records)

if __name__ == "__main__":
    generate_oxidation_demo_data()
    print("\n按任意键退出...")
    input()
