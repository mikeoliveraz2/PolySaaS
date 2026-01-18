# go.ps1 — FINAL: MONITOR LOGGER 100% GUARANTEED

$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$venvActivate = Join-Path $scriptDir "venv\Scripts\Activate.ps1"

if (-Not (Test-Path $venvActivate)) {
    Write-Host "VENV NOT FOUND" -ForegroundColor Red
    pause
    exit
}

& $venvActivate

function Start-IfNotRunning {
    param([int]$Port, [string]$ScriptBlock, [string]$Name)
    $listener = Get-NetTCPConnection -State Listen -LocalPort $Port -ErrorAction SilentlyContinue
    if ($listener) {
        Write-Host "$Name already running on port $Port → SKIPPING" -ForegroundColor Green
    } else {
        Write-Host "Starting $Name on port $Port..." -ForegroundColor Yellow
        Start-Process powershell -ArgumentList "-NoExit", "-Command", $ScriptBlock
    }
}

# MONITOR LOGGER — CORRECT FOLDER NAME: pass_through_service
$monitorFolder = Join-Path $scriptDir "pass_through_service"
Start-IfNotRunning -Port 5000 -Name "Monitor Logger" -ScriptBlock "cd '$monitorFolder'; & '$venvActivate'; python app.py"

# POLYSNIFFER — root
Start-IfNotRunning -Port 5002 -Name "PolySniffer" -ScriptBlock "cd '$scriptDir'; & '$venvActivate'; python polysniffer_simple.py"

# POLYSYSMON — placeholder Docker container (Tomcat)
$polysysmonFolder = Join-Path $scriptDir "placeholders\polysysmon"
if (-Not (Get-NetTCPConnection -State Listen -LocalPort 9001 -ErrorAction SilentlyContinue)) {
    Write-Host "Starting PolySysMon (Tomcat Docker) on port 9001..." -ForegroundColor Yellow
    Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd '$polysysmonFolder'; docker build -t polysysmon-demo .; docker run -d -p 9001:8080 polysysmon-demo"
} else {
    Write-Host "PolySysMon already running on port 9001 → SKIPPING" -ForegroundColor Green
}

Write-Host ""
Write-Host "========================================" -ForegroundColor Green
Write-Host "DJANGO     → http://localhost:8000" -ForegroundColor Green
Write-Host "MONITOR    → http://localhost:5000" -ForegroundColor Green
Write-Host "POLYSNIFFER → http://127.0.0.1:5002" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Green

python -u manage.py runserver