function Invoke-GoSessionEnd {
    param(
        [Parameter(Mandatory)]
        [string]$ScriptRoot,
        [Parameter(Mandatory)]
        [string]$PythonExe
    )

    Write-Host ''
    Write-Host '── Freeze venv to requirements.txt ─────────────────' -ForegroundColor Cyan
    Push-Location $ScriptRoot

    $freezeOutput = & $PythonExe -m pip freeze 2>&1
    $freezeLines = ($freezeOutput | Where-Object { $_ -match '==' } | Measure-Object).Count

    if ($freezeLines -lt 20) {
        $failMsg = '  SAFETY CHECK FAILED: pip freeze returned only ' + $freezeLines + ' packages (expected 20+)'
        Write-Host $failMsg -ForegroundColor Red
        Write-Host '  Skipping requirements.txt update to avoid overwriting with empty/broken venv' -ForegroundColor Red
    } else {
        if ($LASTEXITCODE -eq 0) {
            $freezeOutput | Out-File -FilePath requirements.txt -Encoding utf8
            $okMsg = '  requirements.txt updated from venv (' + $freezeLines + ' packages)'
            Write-Host $okMsg -ForegroundColor Green
            $status = git status --porcelain requirements.txt 2>&1
            if ($status) {
                if (Test-PolySaaSGitHasUnmergedFiles -RepoRoot $ScriptRoot) {
                    Write-Host '  requirements.txt changed but auto-commit skipped because merge conflicts are unresolved' -ForegroundColor Yellow
                } else {
                    git add requirements.txt
                    $commitMsg = 'Update requirements.txt from pip freeze (post-runserver, ' + $freezeLines + ' packages)'
                    git commit -m $commitMsg
                    if ($LASTEXITCODE -eq 0) {
                        git push origin main 2>&1
                        Write-Host '  Committed and pushed requirements.txt' -ForegroundColor Green
                    }
                }
            } else {
                Write-Host '  No change to requirements.txt' -ForegroundColor DarkGray
            }
        }
    }

    Write-Host ''
    Write-Host '── Daily backup (end of session) ─────────────────────' -ForegroundColor Cyan
    Write-Host '  Running backup now - you will see output below.' -ForegroundColor Yellow
    Invoke-DailyBackup -ScriptRoot $ScriptRoot
    Write-Host '── Backup step complete ───────────────────────────────' -ForegroundColor Cyan
    Write-Host ''

    Pop-Location
}
