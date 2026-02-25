#!/usr/bin/env bash
set -euo pipefail

# Launcher script to run the latest完整版 demo data entry
ROOT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
export PYTHONPATH="$ROOT_DIR"

python3 "$ROOT_DIR/scripts/launcher_full_demo.py"
