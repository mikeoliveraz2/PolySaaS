## rungb.ps1 - Grok Build worktree launcher

Write-Host "🚀 Starting PolySaaS from Grok Build worktree..." -ForegroundColor Green

# Activate venv
if (Test-Path "..\venv\Scripts\Activate.ps1") {
    ..\venv\Scripts\Activate.ps1
} elseif (Test-Path "D:\PolySaaS\venv\Scripts\Activate.ps1") {
    D:\PolySaaS\venv\Scripts\Activate.ps1
}

# Fallback secret key
if (-not $env:DJANGO_SECRET_KEY) {
    $env:DJANGO_SECRET_KEY = "django-insecure-grokbuild-$(Get-Random -Maximum 999999999)"
}

Clear-Host
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "PolySaaS - Grok Build Worktree" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Cyan

python manage.py runserver 0.0.0.0:8000