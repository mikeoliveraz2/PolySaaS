# go.ps1 - PolySaaS Launcher: Pull -> Railway Docker stack -> App check -> (if OK) Commit/Push -> Services -> runserver -> (on exit) pip freeze + Backup
# Skip internal stack: $env:POLYSAAS_SKIP_RAILWAY_DOCKER = '1'
# Faster go when Docker stack is already up: $env:POLYSAAS_SKIP_RAILWAY_DOCKER = '1' (still runs app check + services + runserver)
#
# Implementation: scripts\go\*.ps1 (dot-sourced). Validate syntax: scripts\Parse-Ps1File.ps1 -Path scripts\go\Go-RailwayDocker.ps1

$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass -Force -ErrorAction SilentlyContinue

$goDir = Join-Path $scriptDir "scripts\go"
. (Join-Path $goDir "Go-Env.ps1")
. (Join-Path $goDir "Go-DailyBackup.ps1")
. (Join-Path $goDir "Go-MorningSync.ps1")
. (Join-Path $goDir "Go-RailwayDocker.ps1")
. (Join-Path $goDir "Go-Services.ps1")
. (Join-Path $goDir "Go-SessionEnd.ps1")

# ── Pull first (so documentation/collaboration/README and notes are current) ─

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

# ── Railway Docker stack (before app check - Django expects Postgres on 5433) ─

Write-Host ""
Write-Host '── Railway Docker stack (internal services) ───────────' -ForegroundColor Cyan
if ($env:POLYSAAS_SKIP_RAILWAY_DOCKER -eq '1') {
    Write-Host "  SKIPPED - POLYSAAS_SKIP_RAILWAY_DOCKER=1" -ForegroundColor DarkYellow
    Write-Host ""
} else {
    Invoke-RailwayDockerStack -RootDir $scriptDir
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
        Write-Host '  App loads OK - git sync skipped because merge conflicts are unresolved; backup runs when you exit runserver' -ForegroundColor Yellow
    } else {
        Write-Host '  App loads OK - will commit/push now; backup runs when you exit runserver' -ForegroundColor Green
    }
} else {
    Write-Host "  App failed to load - skipping commit/push and backup" -ForegroundColor Yellow
    Write-Host "  Fix errors above, run 'pip freeze > requirements.txt' when clean, then .\go again" -ForegroundColor Yellow
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

# ── Virtual Environment (activate for services) ─────────────────────────

. $venvActivate

Start-GoBackgroundServices -ScriptRoot $scriptDir -PythonExe $venvPython

Write-Host ""
Write-Host "========================================" -ForegroundColor Green
Write-Host "DJANGO          -> http://localhost:8000" -ForegroundColor Green
Write-Host 'POSTGRES (stack)-> localhost:5433  (dosedbadmin / DOSE_DB_PASSWORD)' -ForegroundColor Green
Write-Host 'RABBITMQ        -> amqp://localhost:5672  (mgmt http://localhost:15672)' -ForegroundColor Green
Write-Host "ELASTICSEARCH   -> http://localhost:9200" -ForegroundColor Green
Write-Host "GRAFANA         -> http://localhost:3000" -ForegroundColor Green
Write-Host "MONITORLOGGER   -> http://localhost:5080" -ForegroundColor Green
Write-Host 'MONITOR (app)   -> http://localhost:5000' -ForegroundColor Green
Write-Host "POLYSNIFFER     -> http://127.0.0.1:5002" -ForegroundColor Green
Write-Host "LIFERAY CE      -> http://localhost:8181" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Green

try {
    & $venvPython -u manage.py runserver 0.0.0.0:8000
} finally {
    Invoke-GoSessionEnd -ScriptRoot $scriptDir -PythonExe $venvPython
}
