function Invoke-RailwayDockerStack {
    param([string]$RootDir)

    $composeFile = Join-Path $RootDir "docker-compose.railway-stack.yml"
    if (-Not (Test-Path $composeFile)) {
        Write-Host "  docker-compose.railway-stack.yml not found -> SKIPPING" -ForegroundColor DarkYellow
        return
    }

    Write-Host '  docker compose up -d (railway-stack)...' -ForegroundColor Cyan
    Push-Location $RootDir
    docker compose -f "docker-compose.railway-stack.yml" up -d 2>&1
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

    $testScript = Join-Path $RootDir "scripts\test-railway-stack.ps1"
    if (Test-Path $testScript) {
        Write-Host '--- Railway stack probe ---' -ForegroundColor Cyan
        & $testScript
        if ($LASTEXITCODE -ne 0) {
            Write-Host '  One or more probes failed - check containers: docker compose -f docker-compose.railway-stack.yml ps' -ForegroundColor Yellow
        } else {
            Write-Host '  Railway stack probes: all OK' -ForegroundColor Green
        }
    } else {
        if ($stackReady) {
            Write-Host '  Railway stack: core endpoints responded (no test-railway-stack.ps1)' -ForegroundColor Green
        } else {
            Write-Host '  Railway stack: timeout waiting for all services - run: docker compose -f docker-compose.railway-stack.yml ps' -ForegroundColor Yellow
        }
    }
    Write-Host ""
}
