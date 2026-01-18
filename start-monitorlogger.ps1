# start-monitorlogger.ps1 — Start Monitor Logger service only

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

Write-Host ""
Write-Host "========================================" -ForegroundColor Green
Write-Host "MONITOR LOGGER → http://localhost:5000" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Green