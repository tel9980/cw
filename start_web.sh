#!/bin/bash
# Oxidation Finance System V2.0 - Web Launcher

echo "============================================================"
echo "   Oxidation Finance System V2.0 - Web Launcher"
echo "============================================================"
echo ""

# Check Python
if ! command -v python &> /dev/null; then
    echo "[ERROR] Python not found. Please install Python 3.8+"
    exit 1
fi

echo "[OK] Python found: $(python --version 2>&1)"

# Check Flask
if ! python -c "import flask" &> /dev/null; then
    echo "[INFO] Installing Flask..."
    pip install flask
fi

echo ""
echo "[INFO] Starting Web Service..."
echo ""
echo "Please open browser: http://localhost:5000"
echo ""
echo "Press Ctrl+C to stop"
echo "============================================================"
echo ""

cd oxidation_finance_v20
python web_app.py
