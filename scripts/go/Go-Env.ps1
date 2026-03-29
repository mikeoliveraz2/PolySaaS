# Dot-source after $scriptDir is set (repo root). Defines venv paths.
$venvFolder = if (Test-Path (Join-Path $scriptDir ".venv")) { ".venv" } else { "venv" }
$venvActivate = Join-Path $scriptDir "$venvFolder\Scripts\Activate.ps1"
$venvPython = Join-Path $scriptDir "$venvFolder\Scripts\python.exe"

function Get-PolySaaSGitUnmergedPaths {
	param(
		[Parameter(Mandatory)]
		[string]$RepoRoot
	)

	Push-Location $RepoRoot
	try {
		$unmerged = git diff --name-only --diff-filter=U 2>$null
		if ($LASTEXITCODE -ne 0) {
			return @()
		}

		return @($unmerged | Where-Object { $_ -and $_.Trim() })
	} finally {
		Pop-Location
	}
}

function Test-PolySaaSGitHasUnmergedFiles {
	param(
		[Parameter(Mandatory)]
		[string]$RepoRoot
	)

	return (Get-PolySaaSGitUnmergedPaths -RepoRoot $RepoRoot).Count -gt 0
}
