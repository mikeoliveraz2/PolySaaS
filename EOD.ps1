# EOD.ps1 - PolySaaS End of Day: Stop services -> Freeze/Backup -> Encrypt+Commit+Push
#
# Mirror of go.ps1 (morning start):
#   go.ps1:  Pull -> Decrypt .env -> App check -> Morning sync -> Start services -> runserver -> (exit) pip freeze
#   EOD.ps1: Stop services -> pip freeze -> daily zip backup -> Evening sync (encrypt+commit+push, no pull)
#
# Run after you stop work (Ctrl+C runserver, or let EOD stop port 8000).
#
# Implementation: scripts\eod\*.ps1 + scripts\go\*.ps1 (shared). Validate:
#   scripts\Parse-Ps1File.ps1 -Path scripts\eod\Eod-Services.ps1

$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass -Force -ErrorAction SilentlyContinue

$goDir = Join-Path $scriptDir "scripts\go"
$eodDir = Join-Path $scriptDir "scripts\eod"
. (Join-Path $goDir "Go-Env.ps1")
. (Join-Path $goDir "Go-EnvSync.ps1")
. (Join-Path $goDir "Go-DailyBackup.ps1")
. (Join-Path $goDir "Go-SessionEnd.ps1")
. (Join-Path $eodDir "Eod-Services.ps1")
. (Join-Path $eodDir "Eod-EveningSync.ps1")

Write-Host ""
Write-Host "========================================" -ForegroundColor Magenta
Write-Host "  PolySaaS End of Day (EOD)" -ForegroundColor Magenta
Write-Host "========================================" -ForegroundColor Magenta
Write-Host ""

# -- Stop services (opposite of Start-GoBackgroundServices + runserver) --

Stop-GoBackgroundServices -ScriptRoot $scriptDir

# -- Virtual Environment (required for pip freeze) --

if (-Not (Test-Path $venvActivate)) {
    Write-Host "VENV NOT FOUND" -ForegroundColor Red
    pause
    exit 1
}

# ── Pip freeze (requirements.txt) ──────────────────────────────────────

Write-Host "── Pip Freeze ────────────────────────────────────" -ForegroundColor Cyan
Invoke-GoSessionEnd -ScriptRoot $scriptDir -PythonExe $venvPython

# ── Daily zip backup ───────────────────────────────────────────────────

Write-Host "── Daily Backup ──────────────────────────────────" -ForegroundColor Cyan
Invoke-DailyBackup -ScriptRoot $scriptDir
Write-Host ""

# ── Evening sync: encrypt .env, commit, push (no pull — opposite of morning) ─

Invoke-EveningSync -ScriptRoot $scriptDir

Write-Host "========================================" -ForegroundColor Magenta
Write-Host "  End of day complete" -ForegroundColor Magenta
Write-Host "  Next session: .\go.ps1" -ForegroundColor Magenta
Write-Host "========================================" -ForegroundColor Magenta
Write-Host ""
