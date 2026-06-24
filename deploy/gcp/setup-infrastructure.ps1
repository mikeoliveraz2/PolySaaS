# Phase 1 — GCP infrastructure setup (PowerShell wrapper for Windows desktop)
# Usage:
#   Copy-Item deploy\gcp\config.env.example deploy\gcp\config.env
#   # Edit config.env
#   .\deploy\gcp\setup-infrastructure.ps1

$ErrorActionPreference = "Stop"
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$Config = Join-Path $ScriptDir "config.env"

if (-not (Test-Path $Config)) {
    Write-Error "Missing $Config — copy config.env.example first."
}

Write-Host "[gcp-setup] Running bash setup script via WSL or Git Bash..."
$bash = Get-Command bash -ErrorAction SilentlyContinue
if (-not $bash) {
    Write-Error "bash not found. Install Git for Windows or run gcloud commands from deploy/gcp/setup-infrastructure.sh on a Linux shell."
}

Push-Location (Split-Path -Parent (Split-Path -Parent $ScriptDir))
try {
    & bash "$ScriptDir/setup-infrastructure.sh"
} finally {
    Pop-Location
}
