# Grok Build Smart Helper - Auto-detects latest worktree + starts server

param([string]$Action = 'test')

function Start-GrokBuild {
    param([string]$WorktreePath)

    if (-not $WorktreePath) {
        Write-Host "Finding latest Grok worktree..." -ForegroundColor Cyan
        $worktrees = git worktree list --porcelain | Select-String -Pattern 'worktree ' | ForEach-Object { $_.ToString().Split(' ')[1] }
        $grokWorktree = $worktrees | Where-Object { $_ -like '*grok*' -or $_ -like '*grkbuild*' } | Select-Object -First 1
        if (-not $grokWorktree) { $grokWorktree = $worktrees[0] }
        $WorktreePath = $grokWorktree
    }

    if (Test-Path $WorktreePath) {
        Set-Location $WorktreePath
        Write-Host "✅ Switched to worktree: $WorktreePath" -ForegroundColor Green

        # Set required env vars for this project
        $env:DJANGO_SECRET_KEY = "temp-dev-key-grokbuild-20260609-1307"

        Write-Host "Starting Django runserver on port 8001..." -ForegroundColor Green
        python manage.py runserver 8001
    } else {
        Write-Host "Worktree not found!" -ForegroundColor Red
    }
}

if ($Action -eq 'test') {
    Start-GrokBuild
} 
elseif ($Action -eq 'list') {
    git worktree list
}
else {
    Write-Host "Usage: .\gb.ps1 test    # starts latest grok worktree"
    Write-Host "       .\gb.ps1 list"
}
