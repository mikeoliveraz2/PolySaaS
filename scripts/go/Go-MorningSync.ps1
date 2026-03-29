function Invoke-MorningSync {
    param(
        [Parameter(Mandatory)]
        [string]$ScriptRoot
    )

    Write-Host ""
    Write-Host "── Morning Sync ──────────────────────────────────" -ForegroundColor Cyan

    Push-Location $ScriptRoot

    Write-Host "  Pulling latest from origin/main..." -ForegroundColor Cyan
    git pull origin main 2>&1
    if ($LASTEXITCODE -ne 0) {
        Write-Host "  Pull failed - resolve conflicts before continuing" -ForegroundColor Red
        Write-Host "  Run 'git status' to see what needs attention" -ForegroundColor Red
        Pop-Location
        return
    }
    Write-Host "  Pull complete" -ForegroundColor Green

    $gitStatus = git status --porcelain 2>&1
    if (-Not $gitStatus) {
        Write-Host "  Working tree clean - nothing to commit" -ForegroundColor Green
        Pop-Location
        return
    }

    $changedCount = ($gitStatus | Measure-Object).Count
    Write-Host ('  Found ' + $changedCount + ' uncommitted change(s)') -ForegroundColor Yellow

    $docChanges = $gitStatus | Where-Object { $_ -match "documentation/" -or $_ -match "coordination/" -or $_ -match "\.cursor/rules/" -or $_ -match '\.md$' }
    $codeChanges = $gitStatus | Where-Object { $_ -notmatch "documentation/" -and $_ -notmatch "coordination/" -and $_ -notmatch "\.cursor/rules/" -and $_ -notmatch '\.md$' }

    if ($docChanges) {
        Write-Host "  Staging documentation/coordination files..." -ForegroundColor Cyan
        git add documentation/ 2>$null
        git add coordination/ 2>$null
        git add .cursor/rules/ 2>$null
        git add *.md 2>$null
    }

    if ($codeChanges) {
        Write-Host "  Code changes detected - staging all for morning commit" -ForegroundColor Yellow
        git add -A
    }

    $staged = git diff --cached --name-only 2>&1
    if (-Not $staged) {
        Write-Host "  Nothing staged - skipping commit" -ForegroundColor Green
        Pop-Location
        return
    }

    $today = Get-Date -Format "yyyy-MM-dd"
    $stagedCount = ($staged | Measure-Object).Count
    git commit -m ('Morning sync ' + $today + ' - ' + $stagedCount + ' file(s) from previous session')
    $commitOk = ($LASTEXITCODE -eq 0)

    if ($commitOk) {
        Write-Host "  Committed. Pushing to origin..." -ForegroundColor Cyan
        git push origin main
        if ($LASTEXITCODE -eq 0) {
            Write-Host "  Pushed to origin/main" -ForegroundColor Green
        } else {
            Write-Host "  Push failed - run 'git push origin main' manually" -ForegroundColor Red
        }
    }
    if (-not $commitOk) {
        Write-Host "  Commit failed - check git status manually" -ForegroundColor Red
    }

    Write-Host "──────────────────────────────────────────────────" -ForegroundColor Cyan
    Write-Host ""

    Pop-Location
}
