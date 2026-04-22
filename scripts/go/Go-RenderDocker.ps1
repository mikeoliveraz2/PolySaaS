function Get-PolySaaSDockerDesktopExe {
    $desktopPaths = @(
        "$env:ProgramFiles\Docker\Docker\Docker Desktop.exe",
        "${env:ProgramFiles(x86)}\Docker\Docker\Docker Desktop.exe",
        "$env:LOCALAPPDATA\Docker\Docker Desktop.exe"
    )

    return $desktopPaths | Where-Object { $_ -and (Test-Path $_) } | Select-Object -First 1
}

function Get-PolySaaSDockerCli {
    $dockerCmd = Get-Command docker -ErrorAction SilentlyContinue
    if ($dockerCmd) {
        return $dockerCmd.Source
    }

    $dockerCliPaths = @(
        "$env:ProgramFiles\Docker\Docker\resources\bin\docker.exe",
        "${env:ProgramFiles(x86)}\Docker\Docker\resources\bin\docker.exe",
        "$env:LOCALAPPDATA\Docker\Docker\resources\bin\docker.exe"
    )

    return $dockerCliPaths | Where-Object { $_ -and (Test-Path $_) } | Select-Object -First 1
}

function Add-PolySaaSDockerBinToPath {
    param(
        [string]$DockerCli
    )

    if (-not $DockerCli) {
        return
    }

    $dockerBinDir = Split-Path -Parent $DockerCli
    if (-not $dockerBinDir) {
        return
    }

    $pathParts = @($env:PATH -split ';' | Where-Object { $_ })
    if ($pathParts -notcontains $dockerBinDir) {
        $env:PATH = $dockerBinDir + ';' + $env:PATH
    }
}

function Invoke-RenderDockerStack {
    param([string]$RootDir)

    $composeFile = Join-Path $RootDir "docker-compose.render-stack.yml"
    if (-Not (Test-Path $composeFile)) {
        Write-Host "  docker-compose.render-stack.yml not found -> SKIPPING" -ForegroundColor DarkYellow
        return
    }

    $dockerDesktopExe = Get-PolySaaSDockerDesktopExe
    $dockerCli = Get-PolySaaSDockerCli
    if (-not $dockerCli) {
        if (-not $dockerDesktopExe) {
            Write-Host '  Docker Desktop not found - install it from https://www.docker.com/products/docker-desktop/' -ForegroundColor Red
            return
        }
    }

    Add-PolySaaSDockerBinToPath -DockerCli $dockerCli

    # ── Ensure Docker Desktop is running ────────────────────────────────
    $dockerRunning = $false
    try {
        & $dockerCli info 2>&1 | Out-Null
        $dockerRunning = ($LASTEXITCODE -eq 0)
    } catch { $dockerRunning = $false }

    if (-not $dockerRunning) {
        Write-Host '  Docker Desktop not running - starting it...' -ForegroundColor DarkYellow
        if (-not $dockerDesktopExe) {
            Write-Host '  Docker Desktop executable not found - install it from https://www.docker.com/products/docker-desktop/' -ForegroundColor Red
            return
        }
        Start-Process $dockerDesktopExe
        Write-Host '  Waiting for Docker engine (up to 60s)...' -ForegroundColor DarkGray
        $ddDeadline = (Get-Date).AddSeconds(60)
        while ((Get-Date) -lt $ddDeadline) {
            Start-Sleep -Seconds 3
            if (-not $dockerCli) {
                $dockerCli = Get-PolySaaSDockerCli
                Add-PolySaaSDockerBinToPath -DockerCli $dockerCli
            }
            try {
                if (-not $dockerCli) {
                    continue
                }
                & $dockerCli info 2>&1 | Out-Null
                if ($LASTEXITCODE -eq 0) { $dockerRunning = $true; break }
            } catch {}
        }
        if (-not $dockerRunning) {
            Write-Host '  Docker engine did not start in time - skipping stack' -ForegroundColor Red
            return
        }
        Write-Host '  Docker Desktop ready' -ForegroundColor Green
    }

    Write-Host '  docker compose up -d (render-stack)...' -ForegroundColor Cyan
    Push-Location $RootDir
    & $dockerCli compose -f "docker-compose.render-stack.yml" up -d 2>&1
    $upOk = ($LASTEXITCODE -eq 0)
    Pop-Location

    if (-not $upOk) {
        Write-Host "  docker compose up failed - fix Docker / compose errors; Django may not reach DB on 5433" -ForegroundColor Red
        return
    }

    Write-Host '  Waiting for TCP/HTTP endpoints (Elasticsearch may need up to ~90s)...' -ForegroundColor DarkGray
    $deadline = (Get-Date).AddSeconds(95)
    $stackReady = $false
    while ((Get-Date) -lt $deadline) {
        $pg = Test-NetConnection -ComputerName localhost -Port 5433 -WarningAction SilentlyContinue | Select-Object -ExpandProperty TcpTestSucceeded
        $rmq = Test-NetConnection -ComputerName localhost -Port 5672 -WarningAction SilentlyContinue | Select-Object -ExpandProperty TcpTestSucceeded
        $esOk = $false
        try {
            $es = Invoke-WebRequest -Uri "http://127.0.0.1:9200/" -UseBasicParsing -TimeoutSec 3
            $esOk = ($es.StatusCode -eq 200)
        } catch {
            $esOk = $false
        }
        $gfOk = $false
        try {
            $gf = Invoke-WebRequest -Uri "http://127.0.0.1:3000/login" -UseBasicParsing -TimeoutSec 3
            $gfOk = ($gf.StatusCode -ge 200 -and $gf.StatusCode -lt 500)
        } catch {
            $gfOk = $false
        }
        $mlOk = $false
        try {
            $ml = Invoke-WebRequest -Uri "http://127.0.0.1:5080/" -UseBasicParsing -TimeoutSec 3
            $mlOk = ($ml.StatusCode -ge 200 -and $ml.StatusCode -lt 500)
        } catch {
            $mlOk = $false
        }

        if ($pg -and $rmq -and $esOk -and $gfOk -and $mlOk) {
            $stackReady = $true
            break
        }
        Start-Sleep -Seconds 3
    }

    $testScript = Join-Path $RootDir "scripts\test-render-stack.ps1"
    if (Test-Path $testScript) {
        Write-Host '--- Local stack probe (Render-style services) ---' -ForegroundColor Cyan
        & $testScript
        if ($LASTEXITCODE -ne 0) {
            Write-Host '  One or more probes failed - check containers: docker compose -f docker-compose.render-stack.yml ps' -ForegroundColor Yellow
        } else {
            Write-Host '  Stack probes: all OK' -ForegroundColor Green
        }
    } else {
        if ($stackReady) {
            Write-Host '  Stack: core endpoints responded (no test-render-stack.ps1)' -ForegroundColor Green
        } else {
            Write-Host '  Stack: timeout waiting for all services - run: docker compose -f docker-compose.render-stack.yml ps' -ForegroundColor Yellow
        }
    }
    Write-Host ""
}
