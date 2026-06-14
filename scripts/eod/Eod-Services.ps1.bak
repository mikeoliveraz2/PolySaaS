function Stop-ListenerOnPort {
    param(
        [int]$Port,
        [string]$Name
    )

    $listeners = @(Get-NetTCPConnection -State Listen -LocalPort $Port -ErrorAction SilentlyContinue)
    if ($listeners.Count -eq 0) {
        Write-Host "  $Name (port $Port) -> not running" -ForegroundColor DarkGray
        return
    }

    $pids = $listeners | Select-Object -ExpandProperty OwningProcess -Unique
    foreach ($procId in $pids) {
        if (-not $procId -or $procId -eq 0) { continue }
        try {
            $proc = Get-Process -Id $procId -ErrorAction Stop
            Stop-Process -Id $procId -Force -ErrorAction Stop
            Write-Host "  Stopped $Name (PID $procId, $($proc.ProcessName))" -ForegroundColor Green
        } catch {
            Write-Host "  Could not stop PID $procId for $Name : $_" -ForegroundColor Yellow
        }
    }
}

function Stop-PolySaaSDockerPublish {
    param(
        [int]$Port,
        [string]$Name
    )

    $dockerCmd = Get-Command docker -ErrorAction SilentlyContinue
    if (-not $dockerCmd) {
        Write-Host "  $Name Docker (port $Port) -> docker not installed" -ForegroundColor DarkGray
        return
    }

    $ids = @(docker ps -q --filter "publish=$Port" 2>$null)
    if ($ids.Count -eq 0) {
        Write-Host "  $Name Docker (port $Port) -> not running" -ForegroundColor DarkGray
        return
    }

    foreach ($id in $ids) {
        docker stop $id 2>&1 | ForEach-Object { Write-Host "    $_" }
        if ($LASTEXITCODE -eq 0) {
            Write-Host "  Stopped $Name container $id" -ForegroundColor Green
        } else {
            Write-Host "  Failed to stop $Name container $id" -ForegroundColor Yellow
        }
    }
}

function Stop-GoBackgroundServices {
    param(
        [Parameter(Mandatory)]
        [string]$ScriptRoot
    )

    Write-Host "── Stop Services ─────────────────────────────────" -ForegroundColor Cyan

    Stop-ListenerOnPort -Port 8000 -Name "Django runserver"
    Stop-ListenerOnPort -Port 5000 -Name "Monitor Logger"
    Stop-ListenerOnPort -Port 5002 -Name "PolySniffer"
    Stop-PolySaaSDockerPublish -Port 9001 -Name "PolySysMon"

    $liferayCompose = Join-Path $ScriptRoot "docker-compose.liferay.yml"
    $liferayListening = Get-NetTCPConnection -State Listen -LocalPort 8181 -ErrorAction SilentlyContinue
    if ($liferayListening -and (Test-Path $liferayCompose)) {
        Write-Host "  Stopping Liferay CE (docker compose down)..." -ForegroundColor Yellow
        Push-Location $ScriptRoot
        try {
            docker compose -f docker-compose.liferay.yml down 2>&1 | ForEach-Object { Write-Host "    $_" }
            if ($LASTEXITCODE -eq 0) {
                Write-Host "  Liferay CE stopped" -ForegroundColor Green
            } else {
                Write-Host "  Liferay compose down had warnings (non-blocking)" -ForegroundColor DarkYellow
            }
        } finally {
            Pop-Location
        }
    } else {
        Write-Host "  Liferay CE (port 8181) -> not running" -ForegroundColor DarkGray
    }

    Write-Host ""
}
