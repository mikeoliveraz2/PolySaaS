# Dot-source after $scriptDir is set (repo root). Defines venv paths.
$venvFolder = if (Test-Path (Join-Path $scriptDir ".venv")) { ".venv" } else { "venv" }
$venvActivate = Join-Path $scriptDir "$venvFolder\Scripts\Activate.ps1"
$venvPython = Join-Path $scriptDir "$venvFolder\Scripts\python.exe"
