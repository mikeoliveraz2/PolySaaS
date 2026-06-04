# PolySaaS git worktree helpers (per-machine path via .worktree-path in repo root).
#
# Main checkout (F:\PolySaaS): pull, EOD encrypt, BINGO merge target.
# Worktree (wip branch): daily WIP edits; runserver runs here via go.ps1.

function Get-PolySaaSWorktreeRoot {
    param(
        [Parameter(Mandatory)]
        [string]$RepoRoot
    )

    $pathFile = Join-Path $RepoRoot ".worktree-path"
    if (Test-Path $pathFile) {
        $fromFile = (Get-Content $pathFile -Raw).Trim()
        if ($fromFile -and (Test-Path (Join-Path $fromFile "manage.py"))) {
            return $fromFile
        }
    }

    $laptopDefault = "F:\PolySaaS-worktrees\wip"
    if (Test-Path (Join-Path $laptopDefault "manage.py")) {
        return $laptopDefault
    }

    $officeDefault = "C:\Users\PC\.windsurf\worktrees\PolySaaS\PolySaaS-a136a386"
    if (Test-Path (Join-Path $officeDefault "manage.py")) {
        return $officeDefault
    }

    return $null
}

function Sync-PolySaaSWorktreeEnv {
    param(
        [Parameter(Mandatory)]
        [string]$RepoRoot,
        [Parameter(Mandatory)]
        [string]$WorktreeRoot
    )

    foreach ($name in @('.env', '.env.key')) {
        $src = Join-Path $RepoRoot $name
        $dst = Join-Path $WorktreeRoot $name
        if (Test-Path $src) {
            Copy-Item $src $dst -Force
            Write-Host "  Synced $name -> worktree" -ForegroundColor DarkGray
        }
    }
}

function Invoke-PolySaaSGitPullRepo {
    param(
        [Parameter(Mandatory)]
        [string]$RepoRoot,
        [Parameter(Mandatory)]
        [string]$Label
    )

    if (-not (Test-Path $RepoRoot)) {
        Write-Host "  $Label -> path not found: $RepoRoot" -ForegroundColor Red
        return $false
    }

    if (-not (Test-Path (Join-Path $RepoRoot ".git"))) {
        Write-Host "  $Label -> not a git checkout: $RepoRoot" -ForegroundColor Red
        return $false
    }

    $unmergedPaths = Get-PolySaaSGitUnmergedPaths -RepoRoot $RepoRoot
    if ($unmergedPaths.Count -gt 0) {
        Write-Host "  $Label -> SKIPPED - unresolved merge conflicts" -ForegroundColor Yellow
        $unmergedPaths | ForEach-Object { Write-Host ('    U ' + $_) -ForegroundColor Yellow }
        return $false
    }

    Push-Location $RepoRoot
    try {
        Write-Host "  Pulling $Label (origin/main)..." -ForegroundColor Cyan
        git pull origin main 2>&1 | ForEach-Object { Write-Host "    $_" }
        if ($LASTEXITCODE -ne 0) {
            Write-Host "  $Label pull failed - resolve conflicts before continuing" -ForegroundColor Red
            return $false
        }
        Write-Host "  $Label pull complete" -ForegroundColor Green
        return $true
    } finally {
        Pop-Location
    }
}

function Invoke-PolySaaSGitPullAll {
    param(
        [Parameter(Mandatory)]
        [string]$ScriptRoot
    )

    $allOk = Invoke-PolySaaSGitPullRepo -RepoRoot $ScriptRoot -Label "main checkout"

    $worktreeRoot = Get-PolySaaSWorktreeRoot -RepoRoot $ScriptRoot
    if (-not $worktreeRoot) {
        Write-Host "  worktree -> not configured (set .worktree-path or create worktree)" -ForegroundColor Red
        return $false
    }

    $worktreeOk = Invoke-PolySaaSGitPullRepo -RepoRoot $worktreeRoot -Label "worktree"
    return ($allOk -and $worktreeOk)
}
