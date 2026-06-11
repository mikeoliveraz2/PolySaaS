# THIS CODE IS FROZEN — NO CHANGES TO THIS CODE ARE ALLOWED WITHOUT THE OWNER'S PERMISSION
# BINGO: Mattermost Composer via Roles Hydration — 2026-06-11
# Certification: documentation/BINGO_MATTERMOST_COMPOSER_ROLES_2026-06-11.md
# PolySaaS Run All Services
# Activates venv, starts Waitress WSGI server (Windows), syncs AI peers, starts Mattermost bot

$ErrorActionPreference = "Stop"
$ProjectRoot = if ($PSScriptRoot) { $PSScriptRoot } else { "D:\PolySaaS" }
$WaitressListen = "0.0.0.0:8000"
$WaitressPort = 8000
$WaitressThreads = 32

function Get-PolySaaSVenvPython {
    param([string]$Root)
    foreach ($folder in @("venv", ".venv")) {
        $python = Join-Path $Root "$folder\Scripts\python.exe"
        if (Test-Path $python) { return $python }
    }
    throw "No venv found under $Root (expected venv\Scripts\python.exe or .venv\Scripts\python.exe)"
}

function Stop-ProcessTree {
    param([int]$ProcessId)
    if ($ProcessId -le 0) { return }
    $ErrorActionPreference = 'SilentlyContinue'
    & taskkill.exe /T /F /PID $ProcessId 2>$null | Out-Null
    $ErrorActionPreference = 'Stop'
}

function Get-WaitressPortOwnerPids {
    param([int]$Port = 8000)
    @(Get-NetTCPConnection -State Listen -LocalPort $Port -ErrorAction SilentlyContinue |
        ForEach-Object { $_.OwningProcess } |
        Where-Object { $_ -gt 0 } |
        Sort-Object -Unique)
}

function Stop-ListenerOnPort {
    param(
        [int]$Port,
        [string]$Label = "port $Port"
    )
    $pids = @(Get-WaitressPortOwnerPids -Port $Port)
    foreach ($procId in $pids) {
        try {
            $proc = Get-Process -Id $procId -ErrorAction Stop
            Stop-ProcessTree -ProcessId $procId
            Write-Host "  Stopped $($proc.ProcessName) tree (PID $procId) on $Label" -ForegroundColor Yellow
        } catch {
            Write-Host "  Could not stop PID $procId on $Label : $_" -ForegroundColor DarkYellow
        }
    }
}

function Get-PolySaaSServiceProcesses {
    param([string]$Root)

    $patterns = @(
        '*manage.py runserver*',
        '*waitress-serve*',
        '*mysite.wsgi*',
        '*run_mattermost_bot*',
        '*mattermost_bot*'
    )

    $procs = @()
    foreach ($name in @('python', 'waitress-serve')) {
        $procs += @(Get-CimInstance Win32_Process -Filter "Name='$name.exe'" -ErrorAction SilentlyContinue | Where-Object {
            $cmd = $_.CommandLine
            if (-not $cmd) { return $false }
            foreach ($pat in $patterns) {
                if ($cmd -like $pat) { return $true }
            }
            if ($cmd -like "*$Root*" -and (
                $cmd -like '*runserver*' -or $cmd -like '*waitress*' -or $cmd -like '*run_mattermost_bot*'
            )) { return $true }
            return $false
        })
    }
    return $procs
}

function Stop-PolySaaSServiceProcesses {
    param([string]$Root)

    Write-Host "Cleaning up existing processes..." -ForegroundColor Yellow

    for ($round = 1; $round -le 3; $round++) {
        Stop-ListenerOnPort -Port $WaitressPort -Label "Waitress/Django"

        Get-PolySaaSServiceProcesses -Root $Root | ForEach-Object {
            Write-Host "  Stopping PID $($_.ProcessId): $($_.Name)" -ForegroundColor Yellow
            Stop-ProcessTree -ProcessId $_.ProcessId
        }

        Start-Sleep -Seconds 2

        $onPort = @(Get-WaitressPortOwnerPids -Port $WaitressPort)
        $left = @(Get-PolySaaSServiceProcesses -Root $Root)
        if ($onPort.Count -eq 0 -and $left.Count -eq 0) { break }
        if ($round -lt 3) {
            Write-Host "  Round $round — port/listeners still present, retrying..." -ForegroundColor DarkYellow
        }
    }

    if (-not (Wait-PortFree -Port $WaitressPort -TimeoutSec 15)) {
        Write-Host "WARNING: port $WaitressPort still in use after cleanup" -ForegroundColor Red
    }
}

function Wait-PortFree {
    param(
        [int]$Port = 8000,
        [int]$TimeoutSec = 30
    )
    $deadline = (Get-Date).AddSeconds($TimeoutSec)
    while ((Get-Date) -lt $deadline) {
        $owners = @(Get-WaitressPortOwnerPids -Port $Port)
        if ($owners.Count -eq 0) { return $true }
        foreach ($procId in $owners) {
            Write-Host "  Port $Port still held by PID $procId — killing..." -ForegroundColor DarkYellow
            Stop-ProcessTree -ProcessId $procId
        }
        Start-Sleep -Seconds 2
    }
    return (@(Get-WaitressPortOwnerPids -Port $Port).Count -eq 0)
}

function Wait-ForPortListener {
    param(
        [int]$Port,
        [int]$TimeoutSec = 45
    )
    $deadline = (Get-Date).AddSeconds($TimeoutSec)
    while ((Get-Date) -lt $deadline) {
        $owners = @(Get-WaitressPortOwnerPids -Port $Port)
        if ($owners.Count -eq 1) { return $owners[0] }
        if ($owners.Count -gt 1) {
            Write-Host "  Multiple PIDs on port $Port ($($owners -join ', ')) — cleaning..." -ForegroundColor DarkYellow
            foreach ($procId in $owners) { Stop-ProcessTree -ProcessId $procId }
            Start-Sleep -Seconds 2
        } else {
            Start-Sleep -Milliseconds 500
        }
    }
    return $null
}

function Start-PolySaaSWaitress {
    param(
        [string]$WaitressExe,
        [string]$Root
    )

    Write-Host "Starting Waitress on http://$WaitressListen (threads=$WaitressThreads)..." -ForegroundColor Green
    if (-not (Wait-PortFree -Port $WaitressPort -TimeoutSec 20)) {
        throw "Port $WaitressPort is still in use — close other Waitress/Django processes and retry"
    }

    Start-Process -FilePath $WaitressExe `
        -ArgumentList "--listen=$WaitressListen", "--threads=$WaitressThreads", "mysite.wsgi:application" `
        -WorkingDirectory $Root `
        -WindowStyle Hidden

    $ownerPid = Wait-ForPortListener -Port $WaitressPort -TimeoutSec 45
    if (-not $ownerPid -or $ownerPid -le 0) {
        throw "Waitress failed to bind port $WaitressPort within timeout (check venv and mysite.wsgi:application)"
    }

    Write-Host "Waitress listening on port $WaitressPort (PID $ownerPid)" -ForegroundColor Green
    return $ownerPid
}

function Get-AIPeersBotProcesses {
    Get-CimInstance Win32_Process -Filter "Name='python.exe'" -ErrorAction SilentlyContinue | Where-Object {
        $_.CommandLine -like '*run_mattermost_bot*'
    }
}

function Start-PolySaaSAIPeersBot {
    param(
        [string]$PythonExe,
        [string]$Root
    )

    # Always start from zero bot processes
    Get-AIPeersBotProcesses | ForEach-Object {
        Write-Host "  Stopping stray bot PID $($_.ProcessId)" -ForegroundColor Yellow
        Stop-ProcessTree -ProcessId $_.ProcessId
    }
    Start-Sleep -Seconds 2

    Write-Host "Syncing AI peer bots to tenant teams..." -ForegroundColor Cyan
    Push-Location $Root
    try {
        & $PythonExe manage.py add_bots_to_all_tenants 2>&1 | ForEach-Object { Write-Host "  $_" }
        if ($LASTEXITCODE -ne 0) {
            Write-Host "  Bot team sync had warnings (continuing anyway)" -ForegroundColor DarkYellow
        }
    } catch {
        Write-Host "  Bot team sync skipped: $($_.Exception.Message)" -ForegroundColor DarkYellow
    } finally {
        Pop-Location
    }

    Write-Host "Starting AI Peers bot (@copilot @grok @gemini demo roster)..." -ForegroundColor Green
    Start-Process -FilePath $PythonExe `
        -ArgumentList "manage.py", "run_mattermost_bot" `
        -WorkingDirectory $Root `
        -WindowStyle Hidden
    Start-Sleep -Seconds 4

    $bots = @(Get-AIPeersBotProcesses)
    if ($bots.Count -gt 1) {
        Write-Host "Found $($bots.Count) bot processes — keeping newest, stopping others..." -ForegroundColor Red
        $keep = $bots | Sort-Object CreationDate -Descending | Select-Object -First 1
        $bots | Where-Object { $_.ProcessId -ne $keep.ProcessId } | ForEach-Object {
            Stop-ProcessTree -ProcessId $_.ProcessId
        }
        Start-Sleep -Seconds 2
        $bots = @(Get-AIPeersBotProcesses)
    }

    if ($bots.Count -eq 0) {
        Write-Host "  Bot not running after start — retrying once..." -ForegroundColor DarkYellow
        Start-Process -FilePath $PythonExe `
            -ArgumentList "manage.py", "run_mattermost_bot" `
            -WorkingDirectory $Root `
            -WindowStyle Hidden
        Start-Sleep -Seconds 4
        $bots = @(Get-AIPeersBotProcesses)
    }

    if ($bots.Count -eq 0) {
        Write-Host "WARNING: AI Peers bot did not start — check .env (MATTERMOST_BOT_TOKEN, etc.)" -ForegroundColor Red
    } elseif ($bots.Count -eq 1) {
        Write-Host "AI Peers bot running (PID $($bots[0].ProcessId))" -ForegroundColor Green
    } else {
        Write-Host "WARNING: $($bots.Count) bot processes still running" -ForegroundColor Red
    }
}

Stop-PolySaaSServiceProcesses -Root $ProjectRoot

Write-Host "Activating virtual environment..." -ForegroundColor Cyan
$VenvPython = Get-PolySaaSVenvPython -Root $ProjectRoot
$VenvRoot = Split-Path (Split-Path $VenvPython -Parent) -Parent
$WaitressExe = Join-Path (Split-Path $VenvPython -Parent) "waitress-serve.exe"
$env:VIRTUAL_ENV = $VenvRoot
$env:PATH = "$(Split-Path $VenvPython -Parent);$env:PATH"

if (-not (Test-Path $WaitressExe)) {
    Write-Host "Installing waitress..." -ForegroundColor Yellow
    & $VenvPython -m pip install waitress
    if (-not (Test-Path $WaitressExe)) {
        throw "waitress-serve.exe not found after pip install. Check venv at $VenvRoot"
    }
}

$null = Start-PolySaaSWaitress -WaitressExe $WaitressExe -Root $ProjectRoot
Start-PolySaaSAIPeersBot -PythonExe $VenvPython -Root $ProjectRoot

Write-Host "`nRunning processes:" -ForegroundColor Cyan
$portOwners = @(Get-WaitressPortOwnerPids -Port $WaitressPort)
Write-Host "  Port $WaitressPort listeners: $($portOwners.Count)" -ForegroundColor $(if ($portOwners.Count -eq 1) { 'Green' } else { 'Red' })

$statusRows = @()
foreach ($ownerPid in $portOwners) {
    $statusRows += [PSCustomObject]@{
        ProcessId = $ownerPid
        Service   = "Waitress ($WaitressListen)"
    }
}
Get-AIPeersBotProcesses | ForEach-Object {
    $statusRows += [PSCustomObject]@{
        ProcessId = $_.ProcessId
        Service   = 'AI Peers bot'
    }
}
if ($statusRows.Count -gt 0) {
    $statusRows | Format-Table -AutoSize
} else {
    Write-Host "  (no service processes found)" -ForegroundColor DarkYellow
}

Write-Host "`nAll services started!" -ForegroundColor Green
Write-Host "Django (Waitress): http://localhost:$WaitressPort" -ForegroundColor White
Write-Host "AI Peers:          @copilot @grok @gemini in Town Square (single WebSocket bot process)" -ForegroundColor White
