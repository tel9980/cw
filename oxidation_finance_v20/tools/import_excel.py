#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
数据导入工具 - Excel批量导入

支持导入：
- 客户数据
- 订单数据
- 收入数据
- 支出数据
- 银行流水

使用方法：
    python import_excel.py --template customers    # 生成客户导入模板
    python import_excel.py --import customers.xlsx  # 导入客户数据
"""

import sys
import io

# Windows编码支持
if sys.platform == "win32":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")

import sys
import argparse
import pandas as pd
from pathlib import Path
from datetime import date, datetime
from decimal import Decimal
import json
import uuid
import sqlite3

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent))


def create_template(template_type: str):
    """生成导入模板"""

    templates = {
        "customers": {
            "columns": ["名称", "联系人", "电话", "地址", "信用额度", "备注"],
            "example": [
                ["新客户A", "张经理", "13800138001", "深圳市", "50000", "月结客户"],
                ["新客户B", "李老板", "13900139002", "东莞市", "30000", "现金客户"],
            ],
            "description": "客户导入模板",
        },
        "orders": {
            "columns": [
                "订单编号",
                "客户名称",
                "物品描述",
                "数量",
                "计价单位",
                "单价",
                "工序1",
                "工序2",
                "工序3",
                "委外工序",
                "订单日期",
                "备注",
            ],
            "example": [
                [
                    "OX202402001",
                    "优质客户有限公司",
                    "铝型材6063氧化",
                    "100",
                    "米",
                    "5.00",
                    "喷砂",
                    "氧化",
                    "",
                    "喷砂",
                    "2024-02-01",
                    "常规订单",
                ],
                [
                    "OX202402002",
                    "新兴科技股份有限公司",
                    "不锈钢螺丝氧化",
                    "5000",
                    "件",
                    "0.10",
                    "抛光",
                    "氧化",
                    "",
                    "",
                    "2024-02-02",
                    "小零件",
                ],
            ],
            "description": "订单导入模板",
        },
        "incomes": {
            "columns": ["客户名称", "金额", "银行类型", "是否有票", "收入日期", "备注"],
            "example": [
                [
                    "优质客户有限公司",
                    "5000",
                    "G银行",
                    "是",
                    "2024-02-01",
                    "订单OX202401001收款",
                ],
                [
                    "新兴科技股份有限公司",
                    "3000",
                    "N银行",
                    "否",
                    "2024-02-02",
                    "微信收款",
                ],
            ],
            "description": "收入导入模板",
        },
        "expenses": {
            "columns": [
                "支出类型",
                "供应商/说明",
                "金额",
                "银行类型",
                "是否有票",
                "支出日期",
                "关联订单号",
                "备注",
            ],
            "example": [
                [
                    "房租",
                    "工业园物业管理",
                    "8500",
                    "G银行",
                    "是",
                    "2024-02-01",
                    "",
                    "2月房租",
                ],
                [
                    "三酸",
                    "化工原料公司",
                    "5000",
                    "G银行",
                    "是",
                    "2024-02-05",
                    "",
                    "硫酸硝酸盐酸",
                ],
                [
                    "委外加工",
                    "喷砂加工厂",
                    "1000",
                    "G银行",
                    "是",
                    "2024-02-06",
                    "OX202401001",
                    "订单委外费",
                ],
            ],
            "description": "支出导入模板",
        },
        "bank": {
            "columns": ["交易日期", "金额", "交易对手", "摘要"],
            "example": [
                ["2024-02-01", "5000", "优质客户有限公司", "收到货款"],
                ["2024-02-02", "-2000", "化工原料公司", "采购三酸"],
                ["2024-02-03", "3000", "新兴科技股份有限公司", "收到加工费"],
            ],
            "description": "银行流水导入模板",
        },
    }

    if template_type not in templates:
        print(f"[ERROR] 未知的模板类型: {template_type}")
        print(f"可用类型: {', '.join(templates.keys())}")
        return

    t = templates[template_type]
    df = pd.DataFrame(t["example"], columns=t["columns"])

    output_file = Path(f"import_template_{template_type}.xlsx")
    df.to_excel(output_file, index=False, sheet_name=template_type)

    print(f"[OK] 导入模板已生成: {output_file}")
    print(f"     类型: {t['description']}")
    print(f"     列: {', '.join(t['columns'])}")


def import_data(file_path: str, data_type: str):
    """导入数据"""

    file = Path(file_path)
    if not file.exists():
        print(f"[ERROR] 文件不存在: {file_path}")
        return

    # 读取Excel
    try:
        df = pd.read_excel(file_path)
    except Exception as e:
        print(f"[ERROR] 读取Excel失败: {e}")
        return

    # 连接数据库
    db_path = Path(__file__).parent / "oxidation_finance_demo_ready.db"
    if not db_path.exists():
        db_path = Path(__file__).parent.parent / "oxidation_finance_demo.db"

    conn = sqlite3.connect(str(db_path))
    cursor = conn.cursor()

    count = 0

    if data_type == "customers":
        for _, row in df.iterrows():
            try:
                cursor.execute(
                    """
                    INSERT INTO customers (id, name, contact, phone, address, credit_limit, notes, created_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                    (
                        str(uuid.uuid4()),
                        str(row["名称"]),
                        str(row.get("联系人", "")),
                        str(row.get("电话", "")),
                        str(row.get("地址", "")),
                        Decimal(str(row.get("信用额度", 0))),
                        str(row.get("备注", "")),
                        datetime.now().isoformat(),
                    ),
                )
                count += 1
            except Exception as e:
                print(f"[WARN] 导入行失败: {e}")

    elif data_type == "orders":
        # 先获取客户ID映射
        cursor.execute("SELECT name, id FROM customers")
        customer_map = {row[0]: row[1] for row in cursor.fetchall()}

        process_map = {
            "喷砂": "喷砂",
            "sandblast": "喷砂",
            "SANDBLASTING": "喷砂",
            "拉丝": "拉丝",
            "wire": "拉丝",
            "WIRE_DRAWING": "拉丝",
            "抛光": "抛光",
            "polish": "抛光",
            "POLISHING": "抛光",
            "氧化": "氧化",
            "oxidation": "氧化",
            "OXIDATION": "氧化",
        }

        unit_map = {
            "件": "件",
            "PIECE": "件",
            "条": "条",
            "STRIP": "条",
            "只": "只",
            "UNIT": "只",
            "个": "个",
            "ITEM": "个",
            "米": "米",
            "METER": "米",
            "公斤": "公斤",
            "KILOGRAM": "公斤",
            "平方米": "平方米",
            "SQUARE_METER": "平方米",
        }

        for _, row in df.iterrows():
            try:
                # 处理工序
                processes = []
                for col in ["工序1", "工序2", "工序3"]:
                    val = row.get(col) if col in row.index else None
                    if val is not None and str(val).strip():
                        p = process_map.get(str(val), str(val))
                        processes.append(p)

                # 处理委外工序
                outsourced = []
                val = row.get("委外工序") if "委外工序" in row.index else None
                if val is not None:
                    for p in str(val).split(","):
                        p = p.strip()
                        if p:
                            outsourced.append(process_map.get(p, p))

                # 计算总价
                quantity = Decimal(str(row["数量"]))
                unit_price = Decimal(str(row["单价"]))
                total = quantity * unit_price

                cursor.execute(
                    """
                    INSERT INTO processing_orders 
                    (id, order_no, customer_id, customer_name, item_description, quantity,
                     pricing_unit, unit_price, processes, outsourced_processes, total_amount,
                     status, order_date, received_amount, notes, created_at, updated_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                    (
                        str(uuid.uuid4()),
                        str(row["订单编号"]),
                        customer_map.get(str(row["客户名称"]), ""),
                        str(row["客户名称"]),
                        str(row["物品描述"]),
                        quantity,
                        unit_map.get(
                            str(row.get("计价单位", "件")),
                            str(row.get("计价单位", "件")),
                        ),
                        unit_price,
                        ",".join(processes),
                        ",".join(outsourced),
                        total,
                        "待加工",
                        str(row.get("订单日期", date.today())),
                        Decimal("0"),
                        str(row.get("备注", "")),
                        datetime.now().isoformat(),
                        datetime.now().isoformat(),
                    ),
                )
                count += 1
            except Exception as e:
                print(f"[WARN] 导入行失败: {e}")

    elif data_type == "incomes":
        for _, row in df.iterrows():
            try:
                bank_type = "G银行" if "G" in str(row.get("银行类型", "G")) else "N银行"
                has_invoice = 1 if "是" in str(row.get("是否有票", "否")) else 0

                cursor.execute(
                    """
                    INSERT INTO incomes 
                    (id, customer_id, customer_name, amount, bank_type, has_invoice,
                     related_orders, allocation, income_date, notes, created_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                    (
                        str(uuid.uuid4()),
                        "",  # 可后续关联
                        str(row["客户名称"]),
                        Decimal(str(row["金额"])),
                        bank_type,
                        has_invoice,
                        "[]",
                        "{}",
                        str(row.get("收入日期", date.today())),
                        str(row.get("备注", "")),
                        datetime.now().isoformat(),
                    ),
                )
                count += 1
            except Exception as e:
                print(f"[WARN] 导入行失败: {e}")

    elif data_type == "expenses":
        type_map = {
            "房租": "房租",
            "RENT": "房租",
            "水电": "水电费",
            "UTILITIES": "水电费",
            "三酸": "三酸",
            "ACID": "三酸",
            "片碱": "片碱",
            "CAUSTIC": "片碱",
            "亚钠": "亚钠",
            "SULFITE": "亚钠",
            "色粉": "色粉",
            "COLOR": "色粉",
            "除油": "除油剂",
            "DEGREASER": "除油剂",
            "挂具": "挂具",
            "FIXTURES": "挂具",
            "委外": "外发加工费",
            "OUTSOURCING": "外发加工费",
            "日常": "日常费用",
            "DAILY": "日常费用",
            "工资": "工资",
            "SALARY": "工资",
            "其他": "其他",
            "OTHER": "其他",
        }

        for _, row in df.iterrows():
            try:
                expense_type = type_map.get(str(row.get("支出类型", "其他")), "其他")
                bank_type = "G银行" if "G" in str(row.get("银行类型", "G")) else "N银行"
                has_invoice = 1 if "是" in str(row.get("是否有票", "否")) else 0

                cursor.execute(
                    """
                    INSERT INTO expenses 
                    (id, expense_type, supplier_name, amount, bank_type, has_invoice,
                     related_order_id, expense_date, description, notes, created_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                    (
                        str(uuid.uuid4()),
                        expense_type,
                        str(row.get("供应商/说明", "")),
                        Decimal(str(row["金额"])),
                        bank_type,
                        has_invoice,
                        str(row.get("关联订单号", "")) or None,
                        str(row.get("支出日期", date.today())),
                        str(row.get("备注", "")),
                        "",
                        datetime.now().isoformat(),
                    ),
                )
                count += 1
            except Exception as e:
                print(f"[WARN] 导入行失败: {e}")

    conn.commit()
    conn.close()

    print(f"[OK] 成功导入 {count} 条{data_type}数据")


def show_stats():
    """显示数据库统计"""
    db_path = Path(__file__).parent / "oxidation_finance_demo_ready.db"
    if not db_path.exists():
        db_path = Path(__file__).parent.parent / "oxidation_finance_demo.db"

    if not db_path.exists():
        print("[ERROR] 数据库不存在")
        return

    conn = sqlite3.connect(str(db_path))

    stats = {
        "客户": "SELECT COUNT(*) FROM customers",
        "供应商": "SELECT COUNT(*) FROM suppliers",
        "订单": "SELECT COUNT(*) FROM processing_orders",
        "收入": "SELECT COUNT(*) FROM incomes",
        "支出": "SELECT COUNT(*) FROM expenses",
        "银行交易": "SELECT COUNT(*) FROM bank_transactions",
    }

    print("\n数据库统计：")
    print("-" * 30)
    for name, sql in stats.items():
        count = conn.execute(sql).fetchone()[0]
        print(f"  {name}: {count}")

    # 总金额
    income_total = conn.execute("SELECT SUM(amount) FROM incomes").fetchone()[0] or 0
    expense_total = conn.execute("SELECT SUM(amount) FROM expenses").fetchone()[0] or 0
    print("-" * 30)
    print(f"  总收入: ¥{income_total:,.2f}")
    print(f"  总支出: ¥{expense_total:,.2f}")
    print(f"  利润: ¥{income_total - expense_total:,.2f}")

    conn.close()


def main():
    parser = argparse.ArgumentParser(
        description="氧化加工厂财务系统 V2.0 - 数据导入工具",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
    python import_excel.py --template customers   # 生成客户导入模板
    python import_excel.py --template orders      # 生成订单导入模板
    python import_excel.py --import customers.xlsx  # 导入客户数据
    python import_excel.py --stats               # 显示数据库统计
        """,
    )

    parser.add_argument(
        "--template",
        choices=["customers", "orders", "incomes", "expenses", "bank"],
        help="生成导入模板",
    )
    parser.add_argument("--import", dest="import_file", help="导入Excel文件")
    parser.add_argument(
        "--type",
        choices=["customers", "orders", "incomes", "expenses"],
        help="指定导入数据类型（与--import一起使用）",
    )
    parser.add_argument("--stats", action="store_true", help="显示数据库统计")

    args = parser.parse_args()

    if args.template:
        create_template(args.template)
    elif args.import_file:
        if not args.type:
            print("[ERROR] 必须指定--type参数")
            return
        import_data(args.import_file, args.type)
    elif args.stats:
        show_stats()
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
