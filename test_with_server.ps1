# PowerShell script: activate venv, start server, run TDD test - all in one
$venvPath = ".\.venv\Scripts\Activate.ps1"
if (Test-Path $venvPath) {
    Write-Host "Activating virtual environment..." -ForegroundColor Green
    . $venvPath
    Write-Host "OK: Virtual environment activated" -ForegroundColor Green

    Write-Host "Loading .env..." -ForegroundColor Cyan
    if (Test-Path ".env") {
        Get-Content .env | ForEach-Object {
            if ($_ -match '=') {
                $parts = $_ -split '=', 2
                Set-Item -Path "env:$($parts[0])" -Value $parts[1]
            }
        }
    } else {
        $env:DJANGO_SECRET_KEY = "dev-secret-key"
        $env:DOSE_DB_PASSWORD = "dosedbpass"
    }
    Write-Host "OK: Environment loaded" -ForegroundColor Green

    Write-Host "Starting server in background..." -ForegroundColor Cyan
    $serverProcess = Start-Process -FilePath "python" -ArgumentList "manage.py runserver" -PassThru -NoNewWindow
    Write-Host "OK: Server PID $($serverProcess.Id)" -ForegroundColor Green

    Write-Host "Waiting 3 seconds for server startup..." -ForegroundColor Yellow
    Start-Sleep -Seconds 3

    Write-Host "Running TDD test..." -ForegroundColor Cyan
    python test_odoo_tdd.py
    $testResult = $LASTEXITCODE

    Write-Host "Stopping server..." -ForegroundColor Yellow
    Stop-Process -Id $serverProcess.Id -Force -ErrorAction SilentlyContinue

    Write-Host "OK: Test exit code $testResult" -ForegroundColor Green
    exit $testResult
} else {
    Write-Host "ERROR: venv not found" -ForegroundColor Red
    exit 1
}
