# runwt.ps1 — Run Django from the wip worktree only (no pull, no morning sync, no EOD).
#
# Use go.ps1 for full morning start (pull, decrypt .env, morning sync, background services).
# Use runwt.ps1 when the worktree is ready and you only need runserver again.
#
# Requires: venv on main checkout, .worktree-path (or default worktree path with manage.py).

$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass -Force -ErrorAction SilentlyContinue

. (Join-Path $scriptDir "scripts\go\Go-Env.ps1")
. (Join-Path $scriptDir "scripts\go\Go-EnvSync.ps1")
. (Join-Path $scriptDir "scripts\go\Go-Worktree.ps1")
. (Join-Path $scriptDir "scripts\eod\Eod-Services.ps1")

Write-Host "── Stop stale Django on port 8000 ──────────────────" -ForegroundColor Cyan
Stop-ListenerOnPort -Port 8000 -Name "Django runserver (stale)"
Write-Host ""

if (-Not (Test-Path $venvActivate)) {
    Write-Host "VENV NOT FOUND at $venvActivate" -ForegroundColor Red
    Write-Host "Run from main checkout after go.ps1 has created the venv, or create venv first." -ForegroundColor Yellow
    exit 1
}

$worktreeRoot = Get-PolySaaSWorktreeRoot -RepoRoot $scriptDir
if (-not $worktreeRoot) {
    Write-Host "No worktree found." -ForegroundColor Red
    Write-Host "  Set .worktree-path in repo root, or see documentation/WORKTREE_SETUP.md" -ForegroundColor Yellow
    exit 1
}

Write-Host ""
Write-Host "── Env (main checkout -> worktree) ─────────────────" -ForegroundColor Cyan
Unprotect-PolySaaSEnv -RepoRoot $scriptDir | Out-Null
Sync-PolySaaSWorktreeEnv -RepoRoot $scriptDir -WorktreeRoot $worktreeRoot
Write-Host ""

Write-Host "========================================" -ForegroundColor Green
Write-Host "DJANGO (worktree) -> http://localhost:8000" -ForegroundColor Green
Write-Host "  $worktreeRoot" -ForegroundColor Magenta
Write-Host "========================================" -ForegroundColor Green
Write-Host ""

Push-Location $worktreeRoot
try {
    & $venvPython -u manage.py runserver 0.0.0.0:8000
} finally {
    Pop-Location
}
