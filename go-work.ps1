# go-work.ps1 — Start Django from the correct PolySaaS worktree
Set-Location "C:\Users\PC\.windsurf\worktrees\PolySaaS\PolySaaS-a136a386"
Write-Host "Starting Django from worktree..." -ForegroundColor Cyan
python manage.py runserver
