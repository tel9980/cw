#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Launcher: automatically run the latest完整版 demo data script.

This script searches the repository root for Python entrypoints that look
like a完整版 demo launcher (containing '完整版' and/or 'V2.0') and runs
the most recently modified one. If none is found, it exits with an informative
message.
"""

import os
import sys
import subprocess
from pathlib import Path

def find_entry_script(root: Path) -> Path:
    candidates = []
    for p in root.rglob("*.py"):
        name = p.name
        if ("完整版" in name) or ("V2.0" in name):
            candidates.append(p)
    if not candidates:
        return None
    # choose most recently modified
    candidates.sort(key=lambda x: x.stat().st_mtime, reverse=True)
    return candidates[0]

def main():
    root = Path(__file__).resolve().parents[1]
    entry = find_entry_script(root)
    if entry is None:
        print("[Launcher] 未找到入口脚本，未包含 '完整版' 或 'V2.0' 的 Python 文件。")
        sys.exit(1)
    print(f"[Launcher] 运行入口: {entry}")
    # 运行入口
    cmd = [sys.executable, str(entry)]
    env = os.environ.copy()
    env["PYTHONPATH"] = str(root)
    proc = subprocess.Popen(cmd, cwd=str(root), env=env, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
    # 逐行输出
    try:
        for line in proc.stdout:
            print(line.rstrip())
    finally:
        proc.wait()
    sys.exit(proc.returncode)

if __name__ == '__main__':
    main()
