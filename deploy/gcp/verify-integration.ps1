#Requires -Version 5.1
# Phase 2 — Verify local PolySaaS against GCP-hosted bundled apps.
param(
    [string]$OdooUrl = $env:ODOO_SHARED_URL,
    [string]$MattermostUrl = $env:MATTERMOST_URL
)

$ErrorActionPreference = "Stop"

function Test-Endpoint {
    param([string]$Name, [string]$Url, [string]$Path = "/")
    if (-not $Url) {
        Write-Warning "[$Name] URL not set — skip"
        return $false
    }
    $target = "$($Url.TrimEnd('/'))$Path"
    try {
        $resp = Invoke-WebRequest -Uri $target -UseBasicParsing -TimeoutSec 15 -MaximumRedirection 0 -ErrorAction SilentlyContinue
        Write-Host "[$Name] $target => $($resp.StatusCode)" -ForegroundColor Green
        return $true
    } catch {
        $code = $_.Exception.Response.StatusCode.value__
        if ($code -in 301, 302, 401, 403) {
            Write-Host "[$Name] $target => HTTP $code (reachable)" -ForegroundColor Yellow
            return $true
        }
        Write-Host "[$Name] $target => FAIL: $_" -ForegroundColor Red
        return $false
    }
}

Write-Host "=== PolySaaS GCP integration smoke test ===" -ForegroundColor Cyan

$odooOk = Test-Endpoint -Name "Odoo" -Url $OdooUrl -Path "/web/health"
$mmOk = Test-Endpoint -Name "Mattermost" -Url $MattermostUrl -Path "/api/v4/system/ping"

if (-not $odooOk -or -not $mmOk) {
    Write-Host "`nFix URLs in .env (see deploy/gcp/.env.local-gcp.example) then re-run." -ForegroundColor Yellow
    exit 1
}

Write-Host "`nEndpoints reachable. Next: run .\runall.ps1 and test passthrough from admin UI." -ForegroundColor Green
