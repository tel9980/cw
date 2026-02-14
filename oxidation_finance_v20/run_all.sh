#!/usr/bin/env bash
set -euo pipefail
ROOT=$(cd "$(dirname "$0")" && pwd)
cd "$ROOT"

echo "=== 1) 更新分支 ==="
git switch feat/reports-dashboard
git pull --rebase

echo "=== 2) 安装依赖 ==="
pip install -r oxidation_finance_v20/requirements.txt

echo "=== 3) 运行测试 ==="
pytest
if [ $? -ne 0 ]; then
  echo "Tests failed. Exit."
  exit 1
fi

echo "=== 4) 生成演示数据 ==="
python oxidation_finance_v20/examples/generate_advanced_demo.py
python oxidation_finance_v20/examples/generate_extended_demo.py

echo "=== 5) 启动 Web 服务（后台） ==="
python oxidation_finance_v20/web_app.py &
WEB_PID=$!
sleep 6

echo "=== 6) 验证接口 ==="
urls=(
  "http://localhost:5000/api/reports/summary"
  "http://localhost:5000/api/reports/monthly"
  "http://localhost:5000/api/reports/top-customers"
  "http://localhost:5000/api/reports/expense-by-type"
)
for u in "${urls[@]}"; do
  if curl -sf "$u" > /dev/null; then
    echo "OK: $u"
  else
    echo "WARN: unable to fetch $u"
  fi
done

echo "=== 7) 导出与快速查看 ==="
python oxidation_finance_v20/tools/report_exporter.py --all
python oxidation_finance_v20/reports/cli.py

echo "=== 8) PR 提示 ==="
echo "Push 分支并创建 PR："
echo "  git push -u origin feat/reports-dashboard"
echo "  gh pr create --title 'feat(reports): dashboard view and advanced demo data scaffolding' --body '<PR BODY>'"
echo "若本地没有 gh，请在网页端创建 PR"

echo "完成。若需要，我可以继续在你允许的前提下自动化 PR 创建流程。"
