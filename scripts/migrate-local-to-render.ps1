param(
    [Parameter(Mandatory = $true)]
    [string]$RenderDatabaseUrl,

    [string]$PythonPath = "d:\PolySaaS\.venv\Scripts\python.exe",
    [string]$ProjectRoot = "d:\PolySaaS",
    [string]$SettingsModule = "mysite.settings_render",
    [string]$BackupDir = "d:\PolySaaS\db_backups",

    [switch]$BackupOnly,
    [switch]$SkipFlush,
    [switch]$Yes
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

function Invoke-Manage {
    param(
        [Parameter(Mandatory = $true)]
        [string[]]$Args,

        [string]$DatabaseUrl,
        [string]$OutputFile
    )

    if ([string]::IsNullOrWhiteSpace($DatabaseUrl)) {
        Remove-Item Env:DATABASE_URL -ErrorAction SilentlyContinue
    }
    else {
        $env:DATABASE_URL = $DatabaseUrl
    }

    $env:DJANGO_SETTINGS_MODULE = $SettingsModule

    Push-Location $ProjectRoot
    try {
        if ([string]::IsNullOrWhiteSpace($OutputFile)) {
            & $PythonPath manage.py @Args
        }
        else {
            & $PythonPath manage.py @Args 1> $OutputFile
        }
    }
    finally {
        Pop-Location
    }
}

if (-not (Test-Path $PythonPath)) {
    throw "Python executable not found: $PythonPath"
}

if (-not (Test-Path $ProjectRoot)) {
    throw "Project root not found: $ProjectRoot"
}

if (-not (Test-Path $BackupDir)) {
    New-Item -ItemType Directory -Path $BackupDir | Out-Null
}

$timestamp = Get-Date -Format "yyyyMMdd_HHmmss"
$remoteBackup = Join-Path $BackupDir "render_remote_backup_$timestamp.json"
$localBackup = Join-Path $BackupDir "local_backup_$timestamp.json"

$dumpArgs = @(
    "dumpdata",
    "--natural-foreign",
    "--natural-primary",
    "--exclude", "auth.permission",
    "--exclude", "contenttypes",
    "--exclude", "admin.logentry",
    "--exclude", "sessions.session",
    "--indent", "2"
)

Write-Host "Step 1/5: Backing up Render database to $remoteBackup" -ForegroundColor Cyan
Invoke-Manage -Args $dumpArgs -DatabaseUrl $RenderDatabaseUrl -OutputFile $remoteBackup

Write-Host "Step 2/5: Backing up local database to $localBackup" -ForegroundColor Cyan
Invoke-Manage -Args $dumpArgs -DatabaseUrl "" -OutputFile $localBackup

if ($BackupOnly) {
    Write-Host "Backup-only mode complete." -ForegroundColor Green
    Write-Host "Render backup: $remoteBackup"
    Write-Host "Local backup:   $localBackup"
    exit 0
}

if (-not $Yes) {
    Write-Host ""
    Write-Host "About to import LOCAL data into RENDER database." -ForegroundColor Yellow
    Write-Host "This will replace current Render data."
    $confirm = Read-Host "Type IMPORT to continue"
    if ($confirm -ne "IMPORT") {
        Write-Host "Cancelled. Backups were still created." -ForegroundColor Yellow
        exit 0
    }
}

if (-not $SkipFlush) {
    Write-Host "Step 3/5: Flushing Render database" -ForegroundColor Cyan
    Invoke-Manage -Args @("flush", "--no-input") -DatabaseUrl $RenderDatabaseUrl
}
else {
    Write-Host "Step 3/5: Skip flush enabled" -ForegroundColor Yellow
}

Write-Host "Step 4/5: Loading local backup into Render" -ForegroundColor Cyan
Invoke-Manage -Args @("loaddata", $localBackup) -DatabaseUrl $RenderDatabaseUrl

Write-Host "Step 5/5: Running bootstrap_auth and verification" -ForegroundColor Cyan
Invoke-Manage -Args @("bootstrap_auth") -DatabaseUrl $RenderDatabaseUrl

$verifyScript = "from django.contrib.auth import get_user_model; from dose.models import Instruction; U=get_user_model(); print('users=', U.objects.count(), 'instructions=', Instruction.objects.count())"
Invoke-Manage -Args @("shell", "-c", $verifyScript) -DatabaseUrl $RenderDatabaseUrl

Write-Host ""
Write-Host "Migration complete." -ForegroundColor Green
Write-Host "Render backup file: $remoteBackup"
Write-Host "Local backup file:   $localBackup"
Write-Host ""
Write-Host "Rollback commands:" -ForegroundColor Yellow
Write-Host "`$env:DATABASE_URL = '$RenderDatabaseUrl'"
Write-Host "& '$PythonPath' manage.py flush --no-input"
Write-Host "& '$PythonPath' manage.py loaddata '$remoteBackup'"
Write-Host "& '$PythonPath' manage.py bootstrap_auth"
