# start-sniffer.ps1 — Start PolySniffer service only

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

# POLYSNIFFER — root folder
Start-IfNotRunning -Port 5001 -Name "PolySniffer" -ScriptBlock "cd '$scriptDir'; & '$venvActivate'; python polysniffer_simple.py"

Write-Host ""
Write-Host "========================================" -ForegroundColor Green
Write-Host "POLYSNIFFER → http://127.0.0.1:5001" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Green