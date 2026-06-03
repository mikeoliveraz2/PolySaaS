# go-work.ps1 — Start Django from the PolySaaS wip worktree (same path as go.ps1)
$repoRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
. (Join-Path $repoRoot "scripts\go\Go-Worktree.ps1")
$wt = Get-PolySaaSWorktreeRoot -RepoRoot $repoRoot
if (-not $wt) {
    Write-Host "No worktree found. Set .worktree-path or run: git worktree add F:\PolySaaS-worktrees\wip -b wip main" -ForegroundColor Red
    exit 1
}
Set-Location $wt
Write-Host "Starting Django from worktree: $wt" -ForegroundColor Cyan
& (Join-Path $repoRoot "venv\Scripts\python.exe") manage.py runserver
