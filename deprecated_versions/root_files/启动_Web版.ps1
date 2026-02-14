# 氧化加工厂财务系统 V2.0 - Web版启动器
# UTF-8编码

$ErrorActionPreference = "Stop"

Write-Host ""
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host "   氧化加工厂财务系统 V2.0 - Web版启动器" -ForegroundColor Green
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host ""

# 检查Python
try {
    $pythonVersion = python --version 2>&1
    Write-Host "[OK] Python found: $pythonVersion"
} catch {
    Write-Host "[ERROR] 未找到Python，请先安装Python 3.8+" -ForegroundColor Red
    Write-Host "   下载地址: https://www.python.org/downloads/" -ForegroundColor Yellow
    pause
    exit 1
}

# 检查Flask
try {
    python -c "import flask" 2>&1 | Out-Null
    Write-Host "[OK] Flask 已安装"
} catch {
    Write-Host "[INFO] 正在安装Flask..." -ForegroundColor Yellow
    pip install flask
    if ($LASTEXITCODE -eq 0) {
        Write-Host "[OK] Flask 安装成功"
    } else {
        Write-Host "[ERROR] Flask 安装失败" -ForegroundColor Red
        pause
        exit 1
    }
}

Write-Host ""
Write-Host "正在启动Web服务..." -ForegroundColor Yellow
Write-Host ""
Write-Host "请打开浏览器访问: http://localhost:5000" -ForegroundColor Green
Write-Host ""
Write-Host "按 Ctrl+C 停止服务" -ForegroundColor Gray
Write-Host ""
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host ""

# 启动Web服务
$scriptPath = Split-Path -Parent $MyInvocation.MyCommand.Path
$webAppPath = Join-Path $scriptPath "oxidation_finance_v20\web_app.py"

try {
    python $webAppPath
} catch {
    Write-Host "[ERROR] 启动失败: $_" -ForegroundColor Red
    pause
}
