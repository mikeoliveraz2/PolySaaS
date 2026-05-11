# go.ps1 - PolySaaS Launcher: Pull -> App check -> (if OK) Commit/Push -> Services -> runserver -> (on exit) pip freeze + Backup
#
# Implementation: scripts\go\*.ps1 (dot-sourced).

$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass -Force -ErrorAction SilentlyContinue

$goDir = Join-Path $scriptDir "scripts\go"
. (Join-Path $goDir "Go-Env.ps1")
. (Join-Path $goDir "Go-DailyBackup.ps1")
. (Join-Path $goDir "Go-MorningSync.ps1")
. (Join-Path $goDir "Go-Services.ps1")
. (Join-Path $goDir "Go-SessionEnd.ps1")

# ── Pull first ─────────────────────────────────────────────────────────

Write-Host ""
Write-Host "── Pull ───────────────────────────────────────────────" -ForegroundColor Cyan
$unmergedPaths = Get-PolySaaSGitUnmergedPaths -RepoRoot $scriptDir
if ($unmergedPaths.Count -gt 0) {
    Write-Host "  SKIPPED - unresolved merge conflicts present" -ForegroundColor Yellow
    $unmergedPaths | ForEach-Object { Write-Host ('    U ' + $_) -ForegroundColor Yellow }
} else {
    Push-Location $scriptDir
    git pull origin main 2>&1
    if ($LASTEXITCODE -ne 0) {
        Write-Host "  Pull failed - resolve conflicts before continuing" -ForegroundColor Red
    } else {
        Write-Host "  Pull complete" -ForegroundColor Green
    }
    Pop-Location
}
Write-Host ""

# ── Virtual Environment (required for app check) ───────────────────────

if (-Not (Test-Path $venvActivate)) {
    Write-Host "VENV NOT FOUND" -ForegroundColor Red
    pause
    exit
}

# ── App load check: only if this passes do we backup and commit/push ───

Write-Host '── App check (runserver must load clean) ─────────────' -ForegroundColor Cyan
Push-Location $scriptDir
$checkOutput = & $venvPython manage.py check 2>&1
if ($checkOutput) {
    $checkOutput | ForEach-Object { Write-Host $_ }
}
$appLoadOk = ($LASTEXITCODE -eq 0)
Pop-Location
if ($appLoadOk) {
    if (Test-PolySaaSGitHasUnmergedFiles -RepoRoot $scriptDir) {
        Write-Host '  App loads OK - git sync skipped because merge conflicts unresolved' -ForegroundColor Yellow
    } else {
        Write-Host '  App loads OK - will commit/push now; backup runs when you exit runserver' -ForegroundColor Green
    }
} else {
    Write-Host "  App failed to load - skipping commit/push and backup" -ForegroundColor Yellow
}
Write-Host ""

if ($appLoadOk) {
    Invoke-MorningSync -ScriptRoot $scriptDir
}

# ── Blog Archive Refresh ─────────────────────────────────────────────────

$blogScript = Join-Path $scriptDir "wp_build_blog_page.py"
if (Test-Path $blogScript) {
    Write-Host "── Blog Archive Refresh ────────────────────────────" -ForegroundColor Cyan
    $blogOutput = & $venvPython $blogScript 2>&1
    if ($LASTEXITCODE -eq 0) {
        Write-Host "  Blog archive page refreshed with latest posts" -ForegroundColor Green
    } else {
        Write-Host '  Blog refresh skipped (network/API error; non-blocking)' -ForegroundColor DarkYellow
    }
    Write-Host ""
}

# ── Activate venv for services ─────────────────────────────────────────

. $venvActivate

Start-GoBackgroundServices -ScriptRoot $scriptDir -PythonExe $venvPython

Write-Host ""
Write-Host "========================================" -ForegroundColor Green
Write-Host "DJANGO          -> http://localhost:8000" -ForegroundColor Green
Write-Host 'MONITOR (app)   -> http://localhost:5000' -ForegroundColor Green
Write-Host "POLYSNIFFER     -> http://127.0.0.1:5002" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Green

# ── Run Django from the active Windsurf worktree (Cascade edits live there) ─
# When the worktree is merged back to main, set $worktreeRoot = $scriptDir.
$worktreeRoot = "C:\Users\PC\.windsurf\worktrees\PolySaaS\PolySaaS-a136a386"
$worktreeManage = Join-Path $worktreeRoot "manage.py"

if (Test-Path $worktreeManage) {
    Write-Host "RUNNING FROM WORKTREE: $worktreeRoot" -ForegroundColor Magenta
    Push-Location $worktreeRoot
    try {
        & $venvPython -u $worktreeManage runserver 0.0.0.0:8000
    } finally {
        Pop-Location
        Invoke-GoSessionEnd -ScriptRoot $scriptDir -PythonExe $venvPython
    }
} else {
    Write-Host "Worktree not found - running local manage.py" -ForegroundColor Yellow
    try {
        & $venvPython -u manage.py runserver 0.0.0.0:8000
    } finally {
        Invoke-GoSessionEnd -ScriptRoot $scriptDir -PythonExe $venvPython
    }
}