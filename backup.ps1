# backup.ps1 — Run daily source backup only (same logic as go.ps1 Invoke-DailyBackup)
$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path

$backupRoot = "D:\backups"
$today = Get-Date -Format "yyyy-MM-dd"
$timestamp = Get-Date -Format "yyyy-MM-dd_HHmmss"

if (-Not (Test-Path $backupRoot)) {
    New-Item -ItemType Directory -Path $backupRoot -Force | Out-Null
    Write-Host "Created backup directory: $backupRoot" -ForegroundColor Cyan
}

$existingToday = Get-ChildItem -Path $backupRoot -Filter "polysaas-backup-${today}*.zip" -ErrorAction SilentlyContinue
if ($existingToday) {
    Write-Host "Backup already exists for $today -> SKIPPING" -ForegroundColor Green
    Write-Host "  $($existingToday[0].Name)" -ForegroundColor DarkGray
    exit 0
}

$zipName = "polysaas-backup-${timestamp}.zip"
$zipPath = Join-Path $backupRoot $zipName

Write-Host "Creating daily source backup..." -ForegroundColor Yellow

$excludeDirs = @(
    'venv', '.venv', 'node_modules', '.git', '__pycache__', '*.pyc',
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
    exit 1
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
