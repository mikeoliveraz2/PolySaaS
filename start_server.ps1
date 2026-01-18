# DoseV3 Server Start Script (PowerShell)
# Get the script directory (workspace root)
$scriptPath = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $scriptPath

# Activate virtual environment
if (Test-Path "venv\Scripts\Activate.ps1") {
    & "venv\Scripts\Activate.ps1"
    Write-Host "Starting Django development server..."
    python manage.py runserver 0.0.0.0:8000
} else {
    Write-Host "Error: Virtual environment not found at venv\Scripts\Activate.ps1" -ForegroundColor Red
    Write-Host "Please ensure the virtual environment is set up." -ForegroundColor Yellow
    exit 1
}