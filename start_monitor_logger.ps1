# Start Monitor Logger (Flask) service manually
# Run this if go.ps1 doesn't start Flask properly

Write-Host "Starting Monitor Logger service..." -ForegroundColor Green
Write-Host "This service will run on http://localhost:5000" -ForegroundColor Yellow
Write-Host ""
Write-Host "Press Ctrl+C to stop the service" -ForegroundColor Cyan
Write-Host ""

# Activate venv if it exists
$venvPath = ".\venv\Scripts\Activate.ps1"
if (Test-Path $venvPath) {
    Write-Host "Activating virtual environment..." -ForegroundColor Cyan
    . $venvPath
}

# Change to pass_through_service directory
cd pass_through_service

# Start Flask service
Write-Host "Starting Flask service..." -ForegroundColor Green
python app.py

