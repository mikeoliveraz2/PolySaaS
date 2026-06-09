# Grok Build Workflow Helpers for PolySaaS (PowerShell)

param(
    [string]$Command,
    [string]$FeatureBranch = $null
)

if (-not $FeatureBranch) {
    $FeatureBranch = git branch --show-current
}

switch ($Command) {
    "test" {
        Write-Host "🔧 Grok Build: Running tests in worktree..." -ForegroundColor Cyan
        git checkout $FeatureBranch 2>$null
        if ($LASTEXITCODE -ne 0) { Write-Host "Already on branch or checkout failed." -ForegroundColor Yellow }

        Get-Process -Name "python" -ErrorAction SilentlyContinue | Where-Object { $_.CommandLine -like "*runserver 8000*" } | Stop-Process -Force

        Write-Host "Starting Django runserver on http://127.0.0.1:8000 ..." -ForegroundColor Green
        Start-Process python -ArgumentList "manage.py", "runserver", "8000" -NoNewWindow

        Write-Host "
✅ Server started in background." -ForegroundColor Green
        Write-Host "Open http://127.0.0.1:8000 in browser" -ForegroundColor White
        Write-Host "Test the + Insert Orchestration Instruction button.
" -ForegroundColor White
        Write-Host "Close this window when done." -ForegroundColor Yellow
    }

    "merge-commit" {
        Write-Host "🚀 Grok Build: Merging to main..." -ForegroundColor Cyan
        git checkout main
        git pull origin main --rebase

        $CommitMsg = "GB-ORCH-EDIT-003: Orchestration button now detects existing instructions (update/create mode)"

        git merge --no-ff $FeatureBranch -m $CommitMsg

        Write-Host "
✅ Merge completed." -ForegroundColor Green
        $Push = Read-Host "Push to origin/main? (y/n)"
        if ($Push -match "^[Yy]") {
            git push origin main
            Write-Host "Pushed." -ForegroundColor Green
        }
    }

    default {
        Write-Host "Usage: .\scripts\grok-build.ps1 test" 
        Write-Host "       .\scripts\grok-build.ps1 merge-commit"
    }
}
