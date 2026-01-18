# PowerShell script to activate virtual environment and run TDD test
#
# USE THIS FOR: Testing Odoo login flow with TDD approach
# - Activates venv (same as go.ps1)
# - Loads .env variables
# - Runs test_odoo_tdd.py
# - Full test output visible in terminal
#
# Example: .\test_tdd.ps1
#

$venvPath = ".\.venv\Scripts\Activate.ps1"
if (Test-Path $venvPath) {
    Write-Host "Activating virtual environment..."
    . $venvPath
    Write-Host "Setting environment variables..."
    # Load .env file if it exists; otherwise set a dev secret
    if (Test-Path ".env") {
        Get-Content .env | ForEach-Object {
            if ($_ -match "^([^=]+)=(.*)$") {
                [Environment]::SetEnvironmentVariable($matches[1], $matches[2], "Process")
            }
        }
    } else {
        $env:DJANGO_SECRET_KEY = "dev-secret-key-for-dev-only"
        $env:DOSE_DB_PASSWORD = "dosedbpass"
    }
    Write-Host "Running TDD test..."
    python test_odoo_tdd.py
} else {
    Write-Host "Virtual environment not found at $venvPath. Please set up venv first."
}
