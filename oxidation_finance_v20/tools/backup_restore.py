#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
备份恢复工具 - 自动/手动备份和恢复

功能：
- 自动备份（保留最近10个版本）
- 手动备份
- 一键恢复
- 查看备份历史
"""

import sys
import io

# Windows编码支持
if sys.platform == "win32":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")

import sys
import shutil
import sqlite3
from pathlib import Path
from datetime import datetime
import json
import argparse


class BackupManager:
    def __init__(self, db_name="oxidation_finance_demo_ready.db"):
        self.db_name = db_name
        self.db_path = Path(__file__).parent / db_name
        self.backup_dir = Path(__file__).parent / "backups"
        self.max_backups = 10

    def ensure_backup_dir(self):
        """确保备份目录存在"""
        self.backup_dir.mkdir(exist_ok=True)
        (self.backup_dir / "auto").mkdir(exist_ok=True)
        (self.backup_dir / "manual").mkdir(exist_ok=True)

    def get_backup_filename(self, backup_type="manual"):
        """生成备份文件名"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        suffix = "auto" if backup_type == "auto" else "manual"
        return f"{self.db_name}_{timestamp}_{suffix}.db"

    def create_backup(self, backup_type="manual", description=""):
        """创建备份"""
        if not self.db_path.exists():
            print(f"[ERROR] 数据库不存在: {self.db_path}")
            return None

        self.ensure_backup_dir()

        backup_file = (
            self.backup_dir / backup_type / self.get_backup_filename(backup_type)
        )

        try:
            # 复制数据库文件
            shutil.copy2(self.db_path, backup_file)

            # 写入元数据
            meta_file = backup_file.with_suffix(".json")
            meta = {
                "backup_file": str(backup_file),
                "backup_type": backup_type,
                "backup_time": datetime.now().isoformat(),
                "description": description,
                "db_size": self.db_path.stat().st_size,
            }
            with open(meta_file, "w", encoding="utf-8") as f:
                json.dump(meta, f, ensure_ascii=False, indent=2)

            print(f"[OK] 备份已创建: {backup_file.name}")

            # 清理旧备份
            self.cleanup_old_backups(backup_type)

            return str(backup_file)
        except Exception as e:
            print(f"[ERROR] 备份失败: {e}")
            return None

    def cleanup_old_backups(self, backup_type="manual"):
        """清理旧备份"""
        backup_folder = self.backup_dir / backup_type
        if not backup_folder.exists():
            return

        backups = list(backup_folder.glob("*.db"))
        backups.sort(key=lambda f: f.stat().st_mtime, reverse=True)

        for old in backups[self.max_backups :]:
            try:
                old.unlink()
                # 同时删除元数据
                meta_file = old.with_suffix(".json")
                if meta_file.exists():
                    meta_file.unlink()
            except Exception as e:
                print(f"[WARN] 删除旧备份失败: {e}")

    def list_backups(self):
        """列出所有备份"""
        self.ensure_backup_dir()

        print("\n" + "=" * 60)
        print("备份历史")
        print("=" * 60)

        total_backups = 0

        for backup_type in ["manual", "auto"]:
            folder = self.backup_dir / backup_type
            if not folder.exists():
                continue

            backups = list(folder.glob("*.db"))
            if not backups:
                continue

            backups.sort(key=lambda f: f.stat().st_mtime, reverse=True)

            print(f"\n[{backup_type.upper()} BACKUPS]")
            print("-" * 60)

            for i, backup in enumerate(backups, 1):
                meta_file = backup.with_suffix(".json")
                if meta_file.exists():
                    try:
                        with open(meta_file, "r", encoding="utf-8") as f:
                            meta = json.load(f)
                        time = meta["backup_time"][:16].replace("T", " ")
                        size = meta["db_size"] / 1024
                        desc = meta.get("description", "")
                        print(f"  {i}. {backup.name}")
                        print(f"     时间: {time} | 大小: {size:.1f} KB")
                        if desc:
                            print(f"     说明: {desc}")
                    except Exception:
                        print(f"  {i}. {backup.name} [元数据损坏]")
                else:
                    print(f"  {i}. {backup.name}")
                total_backups += 1

        print("\n" + "=" * 60)
        print(f"共 {total_backups} 个备份")

    def restore_backup(self, backup_index=None, backup_file=None):
        """恢复备份"""
        self.ensure_backup_dir()

        if backup_file and Path(backup_file).exists():
            restore_from = Path(backup_file)
        elif backup_index:
            # 列出所有备份并按序号选择
            all_backups = []
            for backup_type in ["manual", "auto"]:
                folder = self.backup_dir / backup_type
                if folder.exists():
                    for f in folder.glob("*.db"):
                        all_backups.append(f)

            all_backups.sort(key=lambda f: f.stat().st_mtime, reverse=True)

            if backup_index < 1 or backup_index > len(all_backups):
                print(f"[ERROR] 无效的备份序号: {backup_index}")
                return False

            restore_from = all_backups[backup_index - 1]
        else:
            print("[ERROR] 请指定要恢复的备份（--index 或 --file）")
            return False

        try:
            # 备份当前数据库（如果存在）
            if self.db_path.exists():
                self.create_backup("auto", "恢复前自动备份")

            # 恢复
            shutil.copy2(restore_from, self.db_path)

            print(f"[OK] 已恢复到: {restore_from.name}")
            return True
        except Exception as e:
            print(f"[ERROR] 恢复失败: {e}")
            return False

    def auto_backup(self):
        """自动备份（定时任务调用）"""
        return self.create_backup("auto", "自动备份")

    def verify_backup(self, backup_file=None):
        """验证备份完整性"""
        if backup_file is None:
            backup_file = self.db_path

        file = Path(backup_file)
        if not file.exists():
            print(f"[ERROR] 文件不存在: {backup_file}")
            return False

        try:
            # 尝试连接数据库
            conn = sqlite3.connect(str(file))
            cursor = conn.cursor()

            # 检查表是否存在
            tables = cursor.execute(
                "SELECT name FROM sqlite_master WHERE type='table'"
            ).fetchall()
            table_list = [t[0] for t in tables]

            required_tables = [
                "customers",
                "suppliers",
                "processing_orders",
                "incomes",
                "expenses",
                "bank_accounts",
                "bank_transactions",
            ]

            missing = [t for t in required_tables if t not in table_list]

            if missing:
                print(f"[ERROR] 备份不完整，缺少表: {missing}")
                return False

            # 检查数据
            total_records = 0
            # 允许的表名列表（白名单）
            allowed_tables = {
                "customers",
                "suppliers",
                "processing_orders",
                "incomes",
                "expenses",
                "bank_accounts",
                "bank_transactions",
                "outsourced_processing",
                "audit_logs",
                "accounting_periods",
            }
            for table in table_list:
                if table not in allowed_tables:
                    continue
                count = cursor.execute(
                    "SELECT COUNT(*) FROM {}".format(table)
                ).fetchone()[0]
                total_records += count

            print(f"[OK] 备份验证通过")
            print(f"     文件: {file.name}")
            print(f"     大小: {file.stat().st_size / 1024:.1f} KB")
            print(f"     表数: {len(table_list)}")
            print(f"     记录: {total_records}")

            conn.close()
            return True
        except Exception as e:
            print(f"[ERROR] 验证失败: {e}")
            return False


def main():
    parser = argparse.ArgumentParser(
        description="氧化加工厂财务系统 V2.0 - 备份恢复工具",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
    python backup_restore.py --create                    # 手动备份
    python backup_restore.py --list                      # 查看备份历史
    python backup_restore.py --restore --index 1        # 恢复到最新备份
    python backup_restore.py --verify                   # 验证当前数据库
    python backup_restore.py --auto                      # 自动备份（脚本定时调用）
        """,
    )

    parser.add_argument("--create", action="store_true", help="创建手动备份")
    parser.add_argument("--list", action="store_true", help="列出所有备份")
    parser.add_argument("--restore", action="store_true", help="恢复备份")
    parser.add_argument("--index", type=int, help="备份序号（与--restore一起使用）")
    parser.add_argument("--file", type=str, help="备份文件路径（与--restore一起使用）")
    parser.add_argument("--verify", action="store_true", help="验证备份完整性")
    parser.add_argument("--auto", action="store_true", help="自动备份")

    args = parser.parse_args()

    manager = BackupManager()

    if args.create:
        desc = input("备份说明（可选）: ").strip()
        manager.create_backup("manual", desc)
    elif args.list:
        manager.list_backups()
    elif args.restore:
        manager.restore_backup(args.index, args.file)
    elif args.verify:
        manager.verify_backup()
    elif args.auto:
        manager.auto_backup()
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
