# go.ps1 — PolySaaS Launcher with Daily Source Backup

$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$venvActivate = Join-Path $scriptDir "venv\Scripts\Activate.ps1"

# ── Daily Source Backup ──────────────────────────────────────────────

function Invoke-DailyBackup {
    $backupRoot = "E:\backups"
    $today = Get-Date -Format "yyyy-MM-dd"
    $timestamp = Get-Date -Format "yyyy-MM-dd_HHmmss"

    if (-Not (Test-Path $backupRoot)) {
        New-Item -ItemType Directory -Path $backupRoot -Force | Out-Null
        Write-Host "Created backup directory: $backupRoot" -ForegroundColor Cyan
    }

    $existingToday = Get-ChildItem -Path $backupRoot -Filter "polysaas-backup-${today}*.zip" -ErrorAction SilentlyContinue
    if ($existingToday) {
        Write-Host "Backup already exists for $today → SKIPPING" -ForegroundColor Green
        Write-Host "  $($existingToday[0].Name)" -ForegroundColor DarkGray
        return
    }

    $zipName = "polysaas-backup-${timestamp}.zip"
    $zipPath = Join-Path $backupRoot $zipName

    Write-Host "Creating daily source backup..." -ForegroundColor Yellow

    $excludeDirs = @(
        'venv', 'node_modules', '.git', '__pycache__', '*.pyc',
        'media', 'large_files_backup', 'var', '.mypy_cache',
        '.pytest_cache', '*.egg-info'
    )

    $sourceFiles = Get-ChildItem -Path $scriptDir -Recurse -File -ErrorAction SilentlyContinue | Where-Object {
        $relPath = $_.FullName.Substring($scriptDir.Length + 1)
        $dominated = $false
        foreach ($ex in $excludeDirs) {
            if ($ex.StartsWith('*')) {
                if ($_.Name -like $ex -or $relPath -like "*\$ex*") { $dominated = $true; break }
            } else {
                if ($relPath -like "$ex\*" -or $relPath -like "*\$ex\*") { $dominated = $true; break }
            }
        }
        -not $dominated
    }

    $count = ($sourceFiles | Measure-Object).Count
    if ($count -eq 0) {
        Write-Host "No source files found to backup." -ForegroundColor Red
        return
    }

    Write-Host "  Backing up $count source files..." -ForegroundColor Cyan

    $tempStaging = Join-Path $env:TEMP "polysaas-backup-staging"
    if (Test-Path $tempStaging) { Remove-Item $tempStaging -Recurse -Force }
    New-Item -ItemType Directory -Path $tempStaging -Force | Out-Null

    foreach ($file in $sourceFiles) {
        $relPath = $file.FullName.Substring($scriptDir.Length + 1)
        $destPath = Join-Path $tempStaging $relPath
        $destDir = Split-Path $destPath -Parent
        if (-Not (Test-Path $destDir)) {
            New-Item -ItemType Directory -Path $destDir -Force | Out-Null
        }
        Copy-Item $file.FullName -Destination $destPath -Force
    }

    Compress-Archive -Path "$tempStaging\*" -DestinationPath $zipPath -Force
    Remove-Item $tempStaging -Recurse -Force

    $sizeMB = [math]::Round((Get-Item $zipPath).Length / 1MB, 2)
    Write-Host "  Backup complete: $zipName ($sizeMB MB)" -ForegroundColor Green
}

Invoke-DailyBackup

# ── Morning Documentation Commit & Push ──────────────────────────────

function Invoke-MorningSync {
    Write-Host ""
    Write-Host "── Morning Sync ──────────────────────────────────" -ForegroundColor Cyan

    Push-Location $scriptDir

    $gitStatus = git status --porcelain 2>&1
    if (-Not $gitStatus) {
        Write-Host "  Working tree clean — nothing to commit" -ForegroundColor Green
        Pop-Location
        return
    }

    $changedCount = ($gitStatus | Measure-Object).Count
    Write-Host "  Found $changedCount uncommitted change(s)" -ForegroundColor Yellow

    $docChanges = $gitStatus | Where-Object { $_ -match "documentation/" -or $_ -match "coordination/" -or $_ -match "\.cursor/rules/" -or $_ -match "\.md$" }
    $codeChanges = $gitStatus | Where-Object { $_ -notmatch "documentation/" -and $_ -notmatch "coordination/" -and $_ -notmatch "\.cursor/rules/" -and $_ -notmatch "\.md$" }

    if ($docChanges) {
        Write-Host "  Staging documentation/coordination files..." -ForegroundColor Cyan
        git add documentation/ 2>$null
        git add coordination/ 2>$null
        git add .cursor/rules/ 2>$null
        git add *.md 2>$null
    }

    if ($codeChanges) {
        Write-Host "  Code changes detected — staging all for morning commit" -ForegroundColor Yellow
        git add -A
    }

    $staged = git diff --cached --name-only 2>&1
    if (-Not $staged) {
        Write-Host "  Nothing staged — skipping commit" -ForegroundColor Green
        Pop-Location
        return
    }

    $today = Get-Date -Format "yyyy-MM-dd"
    $stagedCount = ($staged | Measure-Object).Count
    git commit -m "Morning sync $today — $stagedCount file(s) from previous session"

    if ($LASTEXITCODE -eq 0) {
        Write-Host "  Committed. Pushing to origin..." -ForegroundColor Cyan
        git push origin main
        if ($LASTEXITCODE -eq 0) {
            Write-Host "  Pushed to origin/main" -ForegroundColor Green
        } else {
            Write-Host "  Push failed — run 'git push origin main' manually" -ForegroundColor Red
        }
    } else {
        Write-Host "  Commit failed — check git status manually" -ForegroundColor Red
    }

    Write-Host "──────────────────────────────────────────────────" -ForegroundColor Cyan
    Write-Host ""

    Pop-Location
}

Invoke-MorningSync

# ── Virtual Environment ──────────────────────────────────────────────

if (-Not (Test-Path $venvActivate)) {
    Write-Host "VENV NOT FOUND" -ForegroundColor Red
    pause
    exit
}

& $venvActivate

# ── Service Launcher ─────────────────────────────────────────────────

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

# MONITOR LOGGER — pass_through_service
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

# LIFERAY CE — Docker container on port 8181
if (-Not (Get-NetTCPConnection -State Listen -LocalPort 8181 -ErrorAction SilentlyContinue)) {
    $liferayCompose = Join-Path $scriptDir "docker-compose.liferay.yml"
    if (Test-Path $liferayCompose) {
        Write-Host "Starting Liferay CE on port 8181..." -ForegroundColor Yellow
        Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd '$scriptDir'; docker compose -f docker-compose.liferay.yml up"
    } else {
        Write-Host "Liferay compose file not found → SKIPPING" -ForegroundColor DarkYellow
    }
} else {
    Write-Host "Liferay CE already running on port 8181 → SKIPPING" -ForegroundColor Green
}

Write-Host ""
Write-Host "========================================" -ForegroundColor Green
Write-Host "DJANGO      → http://localhost:8000" -ForegroundColor Green
Write-Host "MONITOR     → http://localhost:5000" -ForegroundColor Green
Write-Host "POLYSNIFFER → http://127.0.0.1:5002" -ForegroundColor Green
Write-Host "LIFERAY CE  → http://localhost:8181" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Green

python -u manage.py runserver
