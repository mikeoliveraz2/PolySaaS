# Quick probes for docker-compose.railway-stack.yml services (run after `docker compose ... up -d`).
# Usage: .\scripts\test-railway-stack.ps1
# Exit 0 if all pass, 1 if any fail.

$ErrorActionPreference = 'Stop'
$failed = $false

function Test-Tcp {
    param([int]$Port, [string]$Label)
    $ok = Test-NetConnection -ComputerName localhost -Port $Port -WarningAction SilentlyContinue |
        Select-Object -ExpandProperty TcpTestSucceeded
    if ($ok) { Write-Host "  [OK] $Label (port $Port)" -ForegroundColor Green }
    else { Write-Host "  [FAIL] $Label (port $Port)" -ForegroundColor Red; $script:failed = $true }
}

function Test-Http {
    param([string]$Url, [string]$Label)
    try {
        $r = Invoke-WebRequest -Uri $Url -UseBasicParsing -TimeoutSec 5
        if ($r.StatusCode -ge 200 -and $r.StatusCode -lt 500) {
            Write-Host "  [OK] $Label ($Url)" -ForegroundColor Green
        } else {
            Write-Host "  [FAIL] $Label HTTP $($r.StatusCode)" -ForegroundColor Red
            $script:failed = $true
        }
    } catch {
        Write-Host "  [FAIL] $Label — $($_.Exception.Message)" -ForegroundColor Red
        $script:failed = $true
    }
}

Write-Host "Railway stack probes:" -ForegroundColor Cyan
Test-Tcp -Port 5433 -Label 'PostgreSQL'
Test-Tcp -Port 5672 -Label 'RabbitMQ AMQP'
Test-Tcp -Port 15672 -Label 'RabbitMQ management UI'
Test-Http -Url 'http://127.0.0.1:9200/' -Label 'Elasticsearch'
Test-Http -Url 'http://127.0.0.1:3000/login' -Label 'Grafana'
Test-Http -Url 'http://127.0.0.1:5080/' -Label 'MonitorLogger'

if ($failed) { exit 1 }
exit 0
