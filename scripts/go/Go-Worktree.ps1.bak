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
