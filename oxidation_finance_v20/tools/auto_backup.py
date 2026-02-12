#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
自动备份服务

功能：
- 每天自动备份数据库
- 保留最近30个备份
- 可设置为Windows定时任务

使用方法：
1. 手动运行: python auto_backup.py
2. 设置定时任务: 每天运行一次

设置Windows定时任务：
    schtasks /create /tn "财务系统备份" /tr "python auto_backup.py" /sc daily /st 18:00
"""

import sys
import io

# Windows编码支持
if sys.platform == "win32":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")

import sys
from pathlib import Path
from datetime import datetime, timedelta
import shutil
import sqlite3
import json


class AutoBackup:
    def __init__(self):
        base_dir = Path(__file__).resolve().parent.parent
        self.db_path = base_dir / "oxidation_finance_demo_ready.db"
        if not self.db_path.exists():
            self.db_path = base_dir / "oxidation_finance_demo.db"

        self.backup_dir = base_dir / "backups" / "auto"
        self.backup_dir.mkdir(parents=True, exist_ok=True)
        self.max_backups = 30  # 保留30个备份

    def create_backup(self):
        """创建自动备份"""
        if not self.db_path.exists():
            print(f"[ERROR] 数据库不存在: {self.db_path}")
            return False

        # 生成备份文件名
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_file = self.backup_dir / f"auto_backup_{timestamp}.db"

        try:
            # 复制数据库
            shutil.copy2(self.db_path, backup_file)

            # 记录备份信息
            meta = {
                "backup_file": str(backup_file),
                "backup_time": datetime.now().isoformat(),
                "db_size": self.db_path.stat().st_size,
                "type": "automatic",
            }

            meta_file = backup_file.with_suffix(".json")
            with open(meta_file, "w", encoding="utf-8") as f:
                json.dump(meta, f, ensure_ascii=False, indent=2)

            print(f"[OK] 自动备份已创建: {backup_file.name}")
            print(f"     文件大小: {meta['db_size'] / 1024:.1f} KB")

            # 清理旧备份
            self.cleanup_old_backups()

            return True

        except Exception as e:
            print(f"[ERROR] 备份失败: {e}")
            return False

    def cleanup_old_backups(self):
        """清理旧备份，只保留最近30个"""
        backups = sorted(
            self.backup_dir.glob("auto_backup_*.db"),
            key=lambda f: f.stat().st_mtime,
            reverse=True,
        )

        for old_backup in backups[self.max_backups :]:
            try:
                old_backup.unlink()
                # 同时删除元数据文件
                meta_file = old_backup.with_suffix(".json")
                if meta_file.exists():
                    meta_file.unlink()
                print(f"[INFO] 清理旧备份: {old_backup.name}")
            except Exception as e:
                print(f"[WARN] 清理失败: {e}")

    def get_backup_status(self):
        """获取备份状态"""
        backups = list(self.backup_dir.glob("auto_backup_*.db"))

        if not backups:
            return {"count": 0, "last_backup": None, "total_size": 0}

        # 按时间排序
        backups.sort(key=lambda f: f.stat().st_mtime, reverse=True)
        last_backup = backups[0]

        total_size = sum(b.stat().st_size for b in backups)

        return {
            "count": len(backups),
            "last_backup": datetime.fromtimestamp(last_backup.stat().st_mtime).strftime(
                "%Y-%m-%d %H:%M:%S"
            ),
            "last_file": last_backup.name,
            "total_size": total_size,
            "backups": [b.name for b in backups[:5]],  # 最近5个
        }

    def run(self):
        """运行自动备份"""
        print("\n" + "=" * 70)
        print("氧化加工厂财务系统 - 自动备份服务")
        print("=" * 70)
        print(f"\n数据库: {self.db_path}")
        print(f"备份目录: {self.backup_dir}")
        print(f"保留数量: 最近{self.max_backups}个")

        # 显示当前状态
        status = self.get_backup_status()
        print(f"\n当前状态:")
        print(f"  已有备份: {status['count']}个")
        if status["last_backup"]:
            print(f"  上次备份: {status['last_backup']}")
            print(f"  总大小: {status['total_size'] / 1024 / 1024:.2f} MB")

        print("\n" + "-" * 70)
        print("正在创建备份...")
        print("-" * 70)

        if self.create_backup():
            print("\n[OK] 备份完成!")
        else:
            print("\n[ERROR] 备份失败!")

        print("=" * 70 + "\n")


def setup_windows_task():
    """设置Windows定时任务"""
    print("\n" + "=" * 70)
    print("设置Windows定时任务")
    print("=" * 70)
    print("\n请复制以下命令，以管理员身份运行cmd执行:")
    print("\n" + "-" * 70)

    script_path = Path(__file__).resolve()
    python_path = sys.executable

    # 每天18:00运行
    cmd = f'''schtasks /create /tn "财务系统自动备份" /tr "\\"{python_path}\\" \\"{script_path}\\"" /sc daily /st 18:00 /f'''

    print(cmd)
    print("-" * 70)
    print("\n说明:")
    print("  - 任务名称: 财务系统自动备份")
    print("  - 执行时间: 每天18:00")
    print("  - 执行内容: 自动备份数据库")
    print("\n要删除任务，请运行:")
    print('  schtasks /delete /tn "财务系统自动备份" /f')
    print("=" * 70 + "\n")


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="自动备份服务")
    parser.add_argument("--setup", action="store_true", help="显示设置定时任务的命令")

    args = parser.parse_args()

    if args.setup:
        setup_windows_task()
    else:
        backup = AutoBackup()
        backup.run()
