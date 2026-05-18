# go.ps1 - PolySaaS Launcher: Pull -> App check -> (if OK) Commit/Push -> Services -> runserver -> (on exit) pip freeze + Backup
#
# Implementation: scripts\go\*.ps1 (dot-sourced). Validate syntax: scripts\Parse-Ps1File.ps1 -Path scripts\go\Go-Services.ps1

$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass -Force -ErrorAction SilentlyContinue

$goDir = Join-Path $scriptDir "scripts\go"
. (Join-Path $goDir "Go-Env.ps1")
. (Join-Path $goDir "Go-DailyBackup.ps1")
. (Join-Path $goDir "Go-MorningSync.ps1")
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

# ── AI Peers Enable (non-blocking) ─────────────────────────────────────

$enableAiPeers = ($env:GO_ENABLE_AI_PEERS -ne '0')
if ($enableAiPeers) {
    Write-Host "── AI Peers Enable ───────────────────────────────" -ForegroundColor Cyan

    if (-not $env:MATTERMOST_URL -or -not $env:MATTERMOST_ADMIN_TOKEN) {
        Write-Host "  Skipped: MATTERMOST_URL or MATTERMOST_ADMIN_TOKEN not set" -ForegroundColor DarkYellow
    } else {
        $mmTeam = if ($env:MATTERMOST_TEAM) { $env:MATTERMOST_TEAM } else { 'PolySaaS Online LLC' }
        $callbackBase = if ($env:AIASPEERS_BASE_URL) { $env:AIASPEERS_BASE_URL } elseif ($env:POLYSAAS_CORE_BASE_URL) { $env:POLYSAAS_CORE_BASE_URL } else { '' }

        Push-Location $scriptDir
        try {
            Write-Host "  Ensuring bots are members of configured tenant teams..." -ForegroundColor Gray
            & $venvPython manage.py add_bots_to_all_tenants 2>&1 | ForEach-Object { Write-Host "    $_" }
            if ($LASTEXITCODE -eq 0) {
                Write-Host "  Bot team membership sync complete" -ForegroundColor Green
            } else {
                Write-Host "  Bot team membership sync had warnings/errors (non-blocking)" -ForegroundColor DarkYellow
            }

            $webhookArgs = @(
                'manage.py',
                'create_ai_peers_outgoing_webhook',
                '--team', $mmTeam,
                '--channel-name', 'town-square'
            )
            if ($callbackBase) {
                $webhookArgs += @('--callback-url', $callbackBase)
            }

            Write-Host "  Ensuring outgoing webhook for team '$mmTeam'..." -ForegroundColor Gray
            & $venvPython @webhookArgs 2>&1 | ForEach-Object { Write-Host "    $_" }
            if ($LASTEXITCODE -eq 0) {
                Write-Host "  Outgoing webhook ready" -ForegroundColor Green
            } else {
                Write-Host "  Outgoing webhook setup had warnings/errors (non-blocking)" -ForegroundColor DarkYellow
            }
        } finally {
            Pop-Location
        }
    }

    Write-Host ""
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
Write-Host 'MONITOR (app)   -> http://localhost:5000' -ForegroundColor Green
Write-Host "POLYSNIFFER     -> http://127.0.0.1:5002" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Green

# Hard-coded worktree path — Django runs from the active Windsurf worktree
# regardless of where this go.ps1 is invoked from. Comment out / change when
# the worktree is merged back to main checkout.
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
    Write-Host "Worktree not found at $worktreeRoot - falling back to local manage.py" -ForegroundColor Yellow
    try {
        & $venvPython -u manage.py runserver 0.0.0.0:8000
    } finally {
        Invoke-GoSessionEnd -ScriptRoot $scriptDir -PythonExe $venvPython
    }
}
