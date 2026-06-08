## rungb.ps1 - Grok worktree launcher (run from C:\Users\PC\.grok\worktrees\polysaas\1\)

Write-Host "🚀 Starting PolySaaS from Grok Build worktree..." -ForegroundColor Green

# Activate venv from root (D:\PolySaaS)
$VENV_ACTIVATE = "D:\PolySaaS\venv\Scripts\Activate.ps1"
if (Test-Path $VENV_ACTIVATE) {
    & $VENV_ACTIVATE
    Write-Host "✓ Virtual environment activated" -ForegroundColor Green
} else {
    Write-Host "⚠️ Virtual environment not found; proceeding without activation" -ForegroundColor Yellow
}

# Fallback secret key
if (-not $env:DJANGO_SECRET_KEY) {
    $env:DJANGO_SECRET_KEY = "django-insecure-grokbuild-$(Get-Random -Maximum 999999999)"
}

Clear-Host
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "PolySaaS - Grok Build Worktree" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Location: $((Get-Location).Path)" -ForegroundColor Gray
Write-Host "Python: $(python --version)" -ForegroundColor Gray
Write-Host "========================================" -ForegroundColor Cyan

python manage.py runserver 0.0.0.0:8000
