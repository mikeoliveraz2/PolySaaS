#!/usr/bin/env pwsh
<#
.SYNOPSIS
Run the PolySaaS Django development server in the WIP worktree.

.DESCRIPTION
Activates the virtual environment, navigates to the worktree, and starts
the Django development server on 0.0.0.0:8000 with auto-reload enabled.
#>

param(
    [int]$Port = 8000
)

# Kill any existing Python processes on this port
$existing = Get-Process python -ErrorAction SilentlyContinue | Where-Object {
    # Try to find processes that might be using this port
    $_ | Get-NetTCPConnection -ErrorAction SilentlyContinue | Where-Object { $_.LocalPort -eq $Port }
}

if ($existing) {
    Write-Host "Killing existing Python processes on port $Port..."
    $existing | Stop-Process -Force -ErrorAction SilentlyContinue
    Start-Sleep -Seconds 2
}

# Set location
$wip = "F:\PolySaaS-worktrees\wip"
Set-Location $wip

# Activate venv
Write-Host "Activating virtual environment..."
$venvActivate = "F:\PolySaaS\venv\Scripts\Activate.ps1"
if (Test-Path $venvActivate) {
    & $venvActivate
} else {
    Write-Error "Virtual environment not found at $venvActivate"
    exit 1
}

# Start server
Write-Host "Starting Django development server on 0.0.0.0:$Port..."
Write-Host "Press Ctrl+C to stop."
python manage.py runserver "0.0.0.0:$Port"
