function Invoke-EveningSync {
    param(
        [Parameter(Mandatory)]
        [string]$ScriptRoot
    )

    Write-Host ""
    Write-Host "── Evening Sync ──────────────────────────────────" -ForegroundColor Cyan

    $unmergedPaths = Get-PolySaaSGitUnmergedPaths -RepoRoot $ScriptRoot
    if ($unmergedPaths.Count -gt 0) {
        Write-Host "  SKIPPED - unresolved merge conflicts present" -ForegroundColor Yellow
        $unmergedPaths | ForEach-Object { Write-Host ('    U ' + $_) -ForegroundColor Yellow }
        Write-Host "  Resolve and stage those files before running sync again" -ForegroundColor Yellow
        Write-Host "──────────────────────────────────────────────────" -ForegroundColor Cyan
        Write-Host ""
        return
    }

    Push-Location $ScriptRoot

    $gitStatus = git status --porcelain 2>&1
    if (-Not $gitStatus) {
        Write-Host "  Working tree clean - nothing to commit" -ForegroundColor Green
        Pop-Location
        Write-Host "──────────────────────────────────────────────────" -ForegroundColor Cyan
        Write-Host ""
        return
    }

    $changedCount = ($gitStatus | Measure-Object).Count
    Write-Host ('  Found ' + $changedCount + ' uncommitted change(s)') -ForegroundColor Yellow

    # Encrypt .env -> .env.enc so the encrypted copy is committed (mirror of morning sync)
    Protect-PolySaaSEnv -RepoRoot $ScriptRoot

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
        Write-Host "  Code changes detected - staging all for end-of-day commit" -ForegroundColor Yellow
        git add -A
    }

    $staged = git diff --cached --name-only 2>&1
    if (-Not $staged) {
        Write-Host "  Nothing staged - skipping commit" -ForegroundColor Green
        Pop-Location
        Write-Host "──────────────────────────────────────────────────" -ForegroundColor Cyan
        Write-Host ""
        return
    }

    $today = Get-Date -Format "yyyy-MM-dd"
    $stagedCount = ($staged | Measure-Object).Count
    git commit -m ('End of day sync ' + $today + ' - ' + $stagedCount + ' file(s)')
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
