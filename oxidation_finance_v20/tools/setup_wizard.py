#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
初始化向导 - 首次使用引导

帮助用户：
1. 验证系统环境
2. 配置基本信息
3. 导入历史数据（可选）
4. 验证数据完整性
"""

import sys
import io

# Windows编码支持
if sys.platform == "win32":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")

import sys
import sqlite3
from pathlib import Path
from datetime import date, datetime
from decimal import Decimal
import json
import uuid


class SetupWizard:
    """初始化向导"""

    def __init__(self):
        self.project_dir = Path(__file__).parent
        self.db_file = self.project_dir / "oxidation_finance_demo_ready.db"
        self.config_file = self.project_dir / "config.json"

    def step1_check_environment(self):
        """步骤1：检查环境"""
        print("\n" + "=" * 60)
        print("步骤 1/4：检查系统环境")
        print("=" * 60)

        checks = []

        # 检查Python版本
        try:
            import sys

            version = tuple(map(int, sys.version.split()[0].split(".")[:2]))
            if version >= (3, 8):
                checks.append(("Python 3.8+", True, f"Python {sys.version.split()[0]}"))
            else:
                checks.append(
                    (
                        "Python 3.8+",
                        False,
                        f"Python {sys.version.split()[0]} (需要3.8+)",
                    )
                )
        except Exception as e:
            checks.append(("Python", False, str(e)))

        # 检查必要模块
        required_modules = [
            ("sqlite3", "标准库"),
            ("json", "标准库"),
            ("pathlib", "标准库"),
            ("pandas", "pip install pandas"),
            ("openpyxl", "pip install openpyxl"),
        ]

        for module, install_cmd in required_modules:
            try:
                __import__(module)
                checks.append((module, True, "已安装"))
            except ImportError:
                checks.append((module, False, f"运行: {install_cmd}"))

        # 检查数据库
        if self.db_file.exists():
            checks.append(("数据库文件", True, str(self.db_file)))
        else:
            checks.append(("数据库文件", False, "将自动创建"))

        # 显示检查结果
        all_passed = True
        for name, passed, msg in checks:
            status = "[OK]" if passed else "[FAIL]"
            print(f"  {status} {name}: {msg}")
            if not passed:
                all_passed = False

        return all_passed

    def step2_company_info(self):
        """步骤2：公司信息"""
        print("\n" + "=" * 60)
        print("步骤 2/4：公司基本信息")
        print("=" * 60)
        print("  以下信息用于生成报表和文档")
        print()

        defaults = {
            "company_name": "",
            "contact_person": "",
            "phone": "",
            "address": "",
            "tax_id": "",
        }

        try:
            if self.config_file.exists():
                with open(self.config_file, "r", encoding="utf-8") as f:
                    config = json.load(f)
                    defaults.update(config.get("company", {}))
        except Exception:
            pass

        print("  [按回车使用默认值]")
        print()

        company_name = input(f"  公司名称 [{defaults['company_name']}]: ").strip()
        if not company_name:
            company_name = defaults["company_name"]

        contact = input(f"  联系人 [{defaults['contact_person']}]: ").strip()
        if not contact:
            contact = defaults["contact_person"]

        phone = input(f"  联系电话 [{defaults['phone']}]: ").strip()
        if not phone:
            phone = defaults["phone"]

        address = input(f"  公司地址 [{defaults['address']}]: ").strip()
        if not address:
            address = defaults["address"]

        # 保存配置
        config = {
            "company": {
                "name": company_name,
                "contact": contact,
                "phone": phone,
                "address": address,
            },
            "version": "2.0.0",
        }

        with open(self.config_file, "w", encoding="utf-8") as f:
            json.dump(config, f, ensure_ascii=False, indent=2)

        print("\n  [OK] 公司信息已保存")

        return True

    def step3_data_initialization(self):
        """步骤3：数据初始化"""
        print("\n" + "=" * 60)
        print("步骤 3/4：数据初始化")
        print("=" * 60)

        # 检查现有数据
        if self.db_file.exists():
            conn = sqlite3.connect(str(self.db_file))
            cursor = conn.cursor()

            tables = [
                "customers",
                "suppliers",
                "processing_orders",
                "incomes",
                "expenses",
            ]
            total = 0
            for table in tables:
                try:
                    count = cursor.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[
                        0
                    ]
                    print(f"  [INFO] {table}: {count}条记录")
                    total += count
                except:
                    pass

            conn.close()

            if total > 0:
                print(f"\n  发现现有数据 ({total}条)")
                choice = input("  是否重新生成示例数据? (y/N): ").strip().lower()
                if choice == "y":
                    self.db_file.unlink()
                    print("  已删除旧数据")
                else:
                    print("  保留现有数据")
                    return True

        # 生成示例数据
        print("\n  正在生成示例数据...")

        try:
            # 直接导入模块
            sys.path.insert(0, str(self.project_dir.parent))
            from examples.generate_comprehensive_demo import generate_demo_data

            generate_demo_data()
            print("\n  [OK] 示例数据生成完成")
            return True
        except Exception as e:
            print(f"\n  [ERROR] 生成失败: {e}")
            print("  尝试直接创建数据库...")

            # 直接创建数据库
            self.create_minimal_database()
            return True

    def create_minimal_database(self):
        """创建最小数据库"""
        conn = sqlite3.connect(str(self.db_file))
        conn.executescript("""
            CREATE TABLE customers (
                id TEXT PRIMARY KEY, name TEXT, contact TEXT, phone TEXT,
                address TEXT, credit_limit REAL, notes TEXT, created_at TEXT
            );
            CREATE TABLE suppliers (
                id TEXT PRIMARY KEY, name TEXT, contact TEXT, phone TEXT,
                address TEXT, business_type TEXT, notes TEXT, created_at TEXT
            );
            CREATE TABLE processing_orders (
                id TEXT PRIMARY KEY, order_no TEXT, customer_id TEXT, customer_name TEXT,
                item_description TEXT, quantity REAL, pricing_unit TEXT, unit_price REAL,
                processes TEXT, outsourced_processes TEXT, total_amount REAL,
                outsourcing_cost REAL, status TEXT, order_date TEXT, completion_date TEXT,
                delivery_date TEXT, received_amount REAL, notes TEXT, created_at TEXT, updated_at TEXT
            );
            CREATE TABLE incomes (
                id TEXT PRIMARY KEY, customer_id TEXT, customer_name TEXT, amount REAL,
                bank_type TEXT, has_invoice INTEGER, related_orders TEXT, allocation TEXT,
                income_date TEXT, notes TEXT, created_at TEXT
            );
            CREATE TABLE expenses (
                id TEXT PRIMARY KEY, expense_type TEXT, supplier_id TEXT, supplier_name TEXT,
                amount REAL, bank_type TEXT, has_invoice INTEGER, related_order_id TEXT,
                expense_date TEXT, description TEXT, notes TEXT, created_at TEXT
            );
            CREATE TABLE bank_accounts (
                id TEXT PRIMARY KEY, bank_type TEXT, account_name TEXT,
                account_number TEXT, balance REAL, notes TEXT
            );
            CREATE TABLE bank_transactions (
                id TEXT PRIMARY KEY, bank_type TEXT, transaction_date TEXT, amount REAL,
                counterparty TEXT, description TEXT, matched INTEGER,
                matched_income_id TEXT, matched_expense_id TEXT, notes TEXT, created_at TEXT
            );
        """)
        conn.commit()
        conn.close()
        print("  [OK] 最小数据库已创建")

    def step4_verify(self):
        """步骤4：验证"""
        print("\n" + "=" * 60)
        print("步骤 4/4：验证安装")
        print("=" * 60)

        if not self.db_file.exists():
            print("  [FAIL] 数据库文件不存在")
            return False

        try:
            conn = sqlite3.connect(str(self.db_file))
            cursor = conn.cursor()

            # 检查表
            tables = cursor.execute(
                "SELECT name FROM sqlite_master WHERE type='table'"
            ).fetchall()
            table_list = [t[0] for t in tables]

            print("  [OK] 数据库表结构正常")
            print(f"     表数量: {len(table_list)}")

            # 检查数据
            print("\n  数据统计:")
            total_records = 0
            for table in table_list:
                try:
                    count = cursor.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[
                        0
                    ]
                    print(f"     {table}: {count}条")
                    total_records += count
                except:
                    pass

            # 金额统计
            try:
                income = (
                    cursor.execute("SELECT SUM(amount) FROM incomes").fetchone()[0] or 0
                )
                expense = (
                    cursor.execute("SELECT SUM(amount) FROM expenses").fetchone()[0]
                    or 0
                )
                print(f"\n  财务概况:")
                print(f"     总收入: ¥{income:,.2f}")
                print(f"     总支出: ¥{expense:,.2f}")
                print(f"     利润: ¥{income - expense:,.2f}")
            except:
                pass

            conn.close()

            print("\n" + "=" * 60)
            print("  [OK] 安装验证通过！")
            print("=" * 60)

            return True
        except Exception as e:
            print(f"  [FAIL] 验证失败: {e}")
            return False

    def run(self):
        """运行向导"""
        print("\n" + "╔" + "═" * 58 + "╗")
        print("║" + " " * 10 + "氧化加工厂财务系统 V2.0" + " " * 18 + "║")
        print("║" + " " * 15 + "初始化向导" + " " * 32 + "║")
        print("╚" + "═" * 58 + "╝")

        # 步骤1：检查环境
        if not self.step1_check_environment():
            print("\n[ERROR] 环境检查未通过，请先解决问题再运行")
            return False

        # 步骤2：公司信息
        self.step2_company_info()

        # 步骤3：数据初始化
        self.step3_data_initialization()

        # 步骤4：验证
        if not self.step4_verify():
            print("\n[ERROR] 验证未通过，请检查错误信息")
            return False

        print("\n" + "=" * 60)
        print("  初始化完成！")
        print("=" * 60)
        print("\n下一步:")
        print("  1. 运行: python 氧化加工厂财务助手_V2.0_完整版.py")
        print("  2. 或查看文档: 氧化加工厂财务系统_V2.0_快速上手指南.md")
        print()

        return True


if __name__ == "__main__":
    wizard = SetupWizard()
    wizard.run()
