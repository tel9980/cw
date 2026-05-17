#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
项目结构整理脚本
将根目录的历史文件迁移到 deprecated_versions/ 目录
"""

import os
import shutil
from pathlib import Path
from datetime import datetime


def organize_project():
    """整理项目结构"""

    workspace = Path("/workspace")
    deprecated = workspace / "deprecated_versions"
    legacy_versions = deprecated / "legacy_versions"
    business_docs = deprecated / "business_docs"
    data_files = deprecated / "data_files"
    test_data = deprecated / "test_data"

    # 创建必要的目录
    for directory in [legacy_versions, business_docs, data_files, test_data]:
        directory.mkdir(parents=True, exist_ok=True)

    print("开始整理项目结构...")
    print("=" * 70)

    # 需要保留在根目录的文件/目录
    keep_list = [
        "oxidation_finance_v20",
        "deprecated_versions",
        "demo_data",
        "demo_data_v20",
        "backup",
        "collection_letters_demo",
        "2_已处理归档",
        "往来对账单",
        "日结报告",
        "scripts",
        ".git",
        ".gitignore",
        "requirements.txt",
        "README.md",
        "AGENTS.md",
        ".sisyphus",
        ".kiro",
    ]

    # 保留的文档文件
    keep_docs = [
        "README.md",
        "AGENTS.md",
        "氧化加工厂财务系统_V2.0_README.md",
        "氧化加工厂财务系统_V2.0_1页纸启动指南.md",
        "氧化加工厂财务系统_V2.0_快速上手指南.md",
        "氧化加工厂财务系统_V2.0_使用指南.md",
        "氧化加工厂财务系统_V2.0_完整使用手册.md",
    ]

    # 需要迁移的Python文件
    python_files_to_move = []

    for py_file in workspace.glob("*.py"):
        if py_file.name not in ["organize_project.py"]:
            python_files_to_move.append(py_file)

    # 需要迁移的Markdown文档
    md_files_to_move = []

    for md_file in workspace.glob("*.md"):
        if md_file.name not in keep_docs:
            md_files_to_move.append(md_file)

    # 需要迁移的文本文件
    txt_files_to_move = []

    for txt_file in workspace.glob("*.txt"):
        txt_files_to_move.append(txt_file)

    # 需要迁移的批处理文件
    bat_files_to_move = []

    for bat_file in workspace.glob("*.bat"):
        bat_files_to_move.append(bat_file)

    # 需要迁移的PowerShell文件
    ps1_files_to_move = []

    for ps1_file in workspace.glob("*.ps1"):
        ps1_files_to_move.append(ps1_file)

    # 迁移Python文件
    print(f"\n1. 迁移 Python 历史文件 ({len(python_files_to_move)} 个):")
    print("-" * 70)

    for py_file in python_files_to_move:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        dest = legacy_versions / f"{py_file.stem}_{timestamp}{py_file.suffix}"

        try:
            shutil.copy2(py_file, dest)
            py_file.unlink()  # 删除原文件
            print(f"  ✅ {py_file.name} -> {dest.name}")
        except Exception as e:
            print(f"  ❌ {py_file.name}: {e}")

    # 迁移Markdown文档
    print(f"\n2. 迁移 Markdown 文档 ({len(md_files_to_move)} 个):")
    print("-" * 70)

    for md_file in md_files_to_move:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        dest = business_docs / f"{md_file.stem}_{timestamp}{md_file.suffix}"

        try:
            shutil.copy2(md_file, dest)
            md_file.unlink()
            print(f"  ✅ {md_file.name} -> {dest.name}")
        except Exception as e:
            print(f"  ❌ {md_file.name}: {e}")

    # 迁移文本文件
    print(f"\n3. 迁移文本文件 ({len(txt_files_to_move)} 个):")
    print("-" * 70)

    for txt_file in txt_files_to_move:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        dest = legacy_versions / f"{txt_file.stem}_{timestamp}{txt_file.suffix}"

        try:
            shutil.copy2(txt_file, dest)
            txt_file.unlink()
            print(f"  ✅ {txt_file.name} -> {dest.name}")
        except Exception as e:
            print(f"  ❌ {txt_file.name}: {e}")

    # 迁移批处理文件
    print(f"\n4. 迁移批处理文件 ({len(bat_files_to_move)} 个):")
    print("-" * 70)

    for bat_file in bat_files_to_move:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        dest = legacy_versions / f"{bat_file.stem}_{timestamp}{bat_file.suffix}"

        try:
            shutil.copy2(bat_file, dest)
            bat_file.unlink()
            print(f"  ✅ {bat_file.name} -> {dest.name}")
        except Exception as e:
            print(f"  ❌ {bat_file.name}: {e}")

    # 迁移PowerShell文件
    print(f"\n5. 迁移 PowerShell 文件 ({len(ps1_files_to_move)} 个):")
    print("-" * 70)

    for ps1_file in ps1_files_to_move:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        dest = legacy_versions / f"{ps1_file.stem}_{timestamp}{ps1_file.suffix}"

        try:
            shutil.copy2(ps1_file, dest)
            ps1_file.unlink()
            print(f"  ✅ {ps1_file.name} -> {dest.name}")
        except Exception as e:
            print(f"  ❌ {ps1_file.name}: {e}")

    # 统计结果
    print("\n" + "=" * 70)
    print("项目结构整理完成！")
    print("=" * 70)
    print("\n迁移统计：")
    print(f"  - Python 文件: {len(python_files_to_move)} 个")
    print(f"  - Markdown 文档: {len(md_files_to_move)} 个")
    print(f"  - 文本文件: {len(txt_files_to_move)} 个")
    print(f"  - 批处理文件: {len(bat_files_to_move)} 个")
    print(f"  - PowerShell 文件: {len(ps1_files_to_move)} 个")

    print("\n保留在根目录的内容：")
    print("  - oxidation_finance_v20/ (主项目)")
    print("  - README.md, AGENTS.md")
    print("  - deprecated_versions/ (历史文件归档)")
    print("  - demo_data/, demo_data_v20/ (示例数据)")
    print("  - backup/ (备份)")
    print("  - scripts/ (启动脚本)")
    print("  - collection_letters_demo/ (催款函示例)")
    print("  - 2_已处理归档/ (归档数据)")
    print("  - 往来对账单/, 日结报告/ (业务数据)")

    print("\n归档位置：")
    print(f"  - {legacy_versions}")
    print(f"  - {business_docs}")
    print("\n" + "=" * 70)


if __name__ == "__main__":
    organize_project()
