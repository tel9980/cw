# run_all.ps1
# 一键执行：分支保持、测试、演示数据、看板、导出到 PR
$root = Split-Path -Parent $MyInvocation.MyCommand.Definition
Set-Location $root

Write-Host "==== 1) Checkout/update branch ===="
git switch feat/reports-dashboard
git pull --rebase

Write-Host "==== 2) Install dependencies ===="
python -m pip install -r oxidation_finance_v20/requirements.txt

Write-Host "==== 3) Run tests (regression) ===="
pytest
if ($LASTEXITCODE -ne 0) {
  Write-Error "Tests failed. Stop."
  exit 1
}

Write-Host "==== 4) Generate demo data ===="
python oxidation_finance_v20/examples/generate_advanced_demo.py
python oxidation_finance_v20/examples/generate_extended_demo.py

Write-Host "==== 5) Start web service (background) ===="
$proc = Start-Process -FilePath python -ArgumentList "oxidation_finance_v20/web_app.py" -WorkingDirectory $root -NoNewWindow -PassThru
Start-Sleep -Seconds 6

Write-Host "==== 6) Validate endpoints ===="
$urls = @(
  "http://localhost:5000/api/reports/summary",
  "http://localhost:5000/api/reports/monthly",
  "http://localhost:5000/api/reports/top-customers",
  "http://localhost:5000/api/reports/expense-by-type"
)

foreach ($u in $urls) {
  try {
    $resp = Invoke-WebRequest -Uri $u -UseBasicParsing
    Write-Host "OK: $u [Status=$($resp.StatusCode)]"
  } catch {
    Write-Warning "WARN: could not fetch $u"
  }
}

Write-Host "==== 7) Export & quick view ===="
python oxidation_finance_v20/tools/report_exporter.py --all
python oxidation_finance_v20/reports/cli.py

Write-Host "==== 8) PR guidance ===="
Write-Host "To create PR:"
Write-Host "  git push -u origin feat/reports-dashboard"
Write-Host "  gh pr create --title 'feat(reports): dashboard view and advanced demo data scaffolding' --body '<PR BODY>'"
Write-Host "If gh is unavailable, create PR via GitHub web UI and paste PR BODY."

Write-Host "Done. If you want, I can automate PR creation given your ok."
