#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
旧版本文件整理脚本
将根目录的旧版本 .py 和 .bat 文件移动到 deprecated_versions/
"""

import os
import shutil
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent
DEPRECATED_DIR = PROJECT_ROOT / "deprecated_versions" / "legacy_files"

OLD_VERSION_PATTERNS = [
    "_V1.0",
    "_V1.1",
    "_V1.2",
    "_V1.3",
    "_V1.4",
    "_V1.5",
    "_V1.6",
    "_V1.7",
    "_V1.8",
    "_V1.9",
    "_小白专版",
    "_实战版",
    "_增强版",
    "_优化版",
    "_全能版",
    "_完整版",
    "氧化加工厂财务助手_",
    "氧化加工厂版_",
    "启动_",
    "小白专版_",
    "全能版_",
]

OLD_SCRIPT_PATTERNS = [
    "run_",
    "verify_",
    "test_v",
    "test_standalone",
    "test_optimized",
    "test_logic",
    "create_demo",
    "create_oxidation",
    "create_test",
    "simulate_",
    "_create_",
    "test_runner_",
]

EXTENSIONS = [".py", ".bat", ".txt", ".md"]


def should_move(filename: str) -> bool:
    """检查文件是否应该被移动"""
    name = Path(filename).stem
    ext = Path(filename).suffix
    
    if ext not in EXTENSIONS:
        return False
    
    for pattern in OLD_VERSION_PATTERNS:
        if pattern in name:
            return True
    
    for pattern in OLD_SCRIPT_PATTERNS:
        if name.startswith(pattern):
            return True
    
    return False


def get_destination_dir(filename: str) -> Path:
    """根据文件类型确定目标目录"""
    ext = Path(filename).suffix
    
    if ext == ".py":
        return DEPRECATED_DIR / "python_scripts"
    elif ext == ".bat":
        return DEPRECATED_DIR / "batch_files"
    elif ext == ".txt":
        return DEPRECATED_DIR / "text_docs"
    else:
        return DEPRECATED_DIR / "other"


def main():
    print("=" * 60)
    print("旧版本文件整理脚本")
    print("=" * 60)
    
    DEPRECATED_DIR.mkdir(parents=True, exist_ok=True)
    
    for subdir in ["python_scripts", "batch_files", "text_docs", "other"]:
        (DEPRECATED_DIR / subdir).mkdir(exist_ok=True)
    
    files_to_move = []
    
    for item in PROJECT_ROOT.iterdir():
        if item.is_file() and item.name not in ["AGENTS.md", "README.md"]:
            if should_move(item.name):
                files_to_move.append(item)
    
    if not files_to_move:
        print("\n没有找到需要移动的旧版本文件。")
        return
    
    print(f"\n找到 {len(files_to_move)} 个需要移动的文件:\n")
    
    for f in files_to_move:
        print(f"  - {f.name}")
    
    print("\n" + "-" * 60)
    confirm = input("确认移动这些文件到 deprecated_versions/legacy_files/ ? (y/n): ").strip().lower()
    
    if confirm != "y":
        print("\n操作已取消。")
        return
    
    moved_count = 0
    for src_file in files_to_move:
        dest_dir = get_destination_dir(src_file.name)
        dest_file = dest_dir / src_file.name
        
        counter = 1
        while dest_file.exists():
            stem = src_file.stem
            ext = src_file.suffix
            dest_file = dest_dir / f"{stem}_{counter}{ext}"
            counter += 1
        
        shutil.move(str(src_file), str(dest_file))
        print(f"  ✓ {src_file.name} -> {dest_dir.name}/")
        moved_count += 1
    
    print("\n" + "=" * 60)
    print(f"完成！已移动 {moved_count} 个文件到 deprecated_versions/legacy_files/")
    print("=" * 60)


if __name__ == "__main__":
    main()
