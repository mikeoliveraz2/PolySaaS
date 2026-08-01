# THIS CODE IS FROZEN -- NO CHANGES TO THIS CODE ARE ALLOWED WITHOUT THE OWNER'S PERMISSION
# BINGO: Mattermost Composer via Roles Hydration -- 2026-06-11 -- commit 8293f54f
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
            Write-Host "  Round $round -- port/listeners still present, retrying..." -ForegroundColor DarkYellow
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
            Write-Host "  Port $Port still held by PID $procId -- killing..." -ForegroundColor DarkYellow
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
            Write-Host "  Multiple PIDs on port $Port ($($owners -join ', ')) -- cleaning..." -ForegroundColor DarkYellow
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
        throw "Port $WaitressPort is still in use -- close other Waitress/Django processes and retry"
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

function Get-AIPeersBotProcessRoots {
    # Windows Python often spawns a parent+child pair with the same command line.
    # Count/stop process trees by root PID, not every matching python.exe.
    $all = @(Get-AIPeersBotProcesses)
    if ($all.Count -eq 0) { return @() }

    $byPid = @{}
    foreach ($proc in $all) { $byPid[$proc.ProcessId] = $proc }

    @($all | Where-Object {
        $parent = $byPid[$_.ParentProcessId]
        -not ($parent -and $parent.CommandLine -like '*run_mattermost_bot*')
    })
}

function Start-PolySaaSAIPeersBot {
    param(
        [string]$PythonExe,
        [string]$Root
    )

    # Always start from zero bot process trees
    Get-AIPeersBotProcessRoots | ForEach-Object {
        Write-Host "  Stopping stray bot tree (root PID $($_.ProcessId))" -ForegroundColor Yellow
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

    Write-Host 'Starting AI Peers bot (@copilot @grok @gemini demo roster)...' -ForegroundColor Green
    Start-Process -FilePath $PythonExe `
        -ArgumentList "manage.py", "run_mattermost_bot" `
        -WorkingDirectory $Root `
        -WindowStyle Hidden
    Start-Sleep -Seconds 6

    $botRoots = @(Get-AIPeersBotProcessRoots)
    if ($botRoots.Count -gt 1) {
        Write-Host "Found $($botRoots.Count) bot trees -- keeping newest, stopping others..." -ForegroundColor Red
        $keep = $botRoots | Sort-Object CreationDate -Descending | Select-Object -First 1
        $botRoots | Where-Object { $_.ProcessId -ne $keep.ProcessId } | ForEach-Object {
            Stop-ProcessTree -ProcessId $_.ProcessId
        }
        Start-Sleep -Seconds 2
        $botRoots = @(Get-AIPeersBotProcessRoots)
    }

    if ($botRoots.Count -eq 0) {
        Write-Host "  Bot not running after start -- retrying once..." -ForegroundColor DarkYellow
        Start-Process -FilePath $PythonExe `
            -ArgumentList "manage.py", "run_mattermost_bot" `
            -WorkingDirectory $Root `
            -WindowStyle Hidden
        Start-Sleep -Seconds 6
        $botRoots = @(Get-AIPeersBotProcessRoots)
    }

    $botPids = @(Get-AIPeersBotProcesses | ForEach-Object { $_.ProcessId })
    if ($botRoots.Count -eq 0) {
        Write-Host "WARNING: AI Peers bot did not start -- check .env (MATTERMOST_ADMIN_TOKEN, API keys)" -ForegroundColor Red
    } elseif ($botRoots.Count -eq 1) {
        $rootPid = $botRoots[0].ProcessId
        $procNote = if ($botPids.Count -gt 1) { " ($($botPids.Count) PIDs -- normal on Windows)" } else { "" }
        Write-Host "AI Peers bot running (root PID $rootPid$procNote)" -ForegroundColor Green
    } else {
        Write-Host "WARNING: $($botRoots.Count) bot trees still running" -ForegroundColor Red
    }

    return @{
        Count = $botRoots.Count
        Pid   = if ($botRoots.Count -ge 1) { ($botRoots | Sort-Object CreationDate -Descending | Select-Object -First 1).ProcessId } else { 0 }
        Ok    = ($botRoots.Count -eq 1)
    }
}

$CursorWorkerName = "PolySaaS-office"

function Get-CursorWorkerProcesses {
    Get-CimInstance Win32_Process -Filter "Name='node.exe'" -ErrorAction SilentlyContinue | Where-Object {
        $_.CommandLine -match 'cursor-agent' -and $_.CommandLine -match 'worker'
    }
}

function Resolve-CursorAgentCommand {
    $cmd = Get-Command agent -ErrorAction SilentlyContinue
    if ($cmd) { return $cmd.Source }
    $default = Join-Path $env:LOCALAPPDATA "cursor-agent\agent.ps1"
    if (Test-Path $default) { return $default }
    return $null
}

function Start-PolySaaSCursorWorker {
    param(
        [string]$Root,
        [string]$Name = $CursorWorkerName
    )

    $existing = @(Get-CursorWorkerProcesses)
    if ($existing.Count -gt 0) {
        $workerPid = $existing[0].ProcessId
        Write-Host "Cursor worker already running (PID $workerPid, name $Name)" -ForegroundColor Green
        return @{
            Ok             = $true
            Pid            = $workerPid
            AlreadyRunning = $true
            Name           = $Name
        }
    }

    $agentCmd = Resolve-CursorAgentCommand
    if (-not $agentCmd) {
        Write-Host "WARNING: Cursor agent CLI not found -- tablet remote access unavailable" -ForegroundColor Red
        Write-Host "  Install: irm 'https://cursor.com/install?win32=true' | iex" -ForegroundColor DarkYellow
        return @{
            Ok             = $false
            Pid            = 0
            AlreadyRunning = $false
            Name           = $Name
        }
    }

    Write-Host "Starting Cursor worker ($Name) for tablet remote access..." -ForegroundColor Green
    Start-Process -FilePath "powershell.exe" `
        -ArgumentList "-NoProfile", "-ExecutionPolicy", "Bypass", "-File", $agentCmd, "worker", "start", "--name", $Name `
        -WorkingDirectory $Root `
        -WindowStyle Hidden

    Start-Sleep -Seconds 5
    $running = @(Get-CursorWorkerProcesses)
    if ($running.Count -ge 1) {
        $workerPid = $running[0].ProcessId
        Write-Host "Cursor worker running (PID $workerPid)" -ForegroundColor Green
        Write-Host "  Tablet: https://cursor.com/agents (choose $Name)" -ForegroundColor Gray
        return @{
            Ok             = $true
            Pid            = $workerPid
            AlreadyRunning = $false
            Name           = $Name
        }
    }

    Write-Host "WARNING: Cursor worker did not start -- run: agent worker start --name `"$Name`"" -ForegroundColor Red
    return @{
        Ok             = $false
        Pid            = 0
        AlreadyRunning = $false
        Name           = $Name
    }
}

function Show-PolySaaSRunAllSummary {
    param(
        [int]$WaitressPid,
        [bool]$WaitressOk,
        [hashtable]$BotStatus,
        [hashtable]$WorkerStatus,
        [int]$Port = 8000
    )

    $botOk = [bool]$BotStatus.Ok
    $workerOk = [bool]$WorkerStatus.Ok
    $allOk = $WaitressOk -and $botOk
    $line = ('=' * 62)

    Write-Host ""
    Write-Host $line -ForegroundColor Cyan
    Write-Host "  PolySaaS runall -- complete" -ForegroundColor Cyan
    Write-Host $line -ForegroundColor Cyan
    Write-Host ""
    Write-Host "  Deployment (current phase):" -ForegroundColor White
    Write-Host "    Django / PolySaaS admin  -> LOCAL ONLY  http://localhost:$Port" -ForegroundColor Gray
    Write-Host "    Mattermost + bundled apps -> Render (cloud); bot connects outbound" -ForegroundColor Gray
    Write-Host ""
    Write-Host "  Service status:" -ForegroundColor White

    if ($WaitressOk) {
        Write-Host "    [OK]   Django (Waitress)     PID $WaitressPid  port $Port" -ForegroundColor Green
    } else {
        Write-Host "    [FAIL] Django (Waitress)     not listening on port $Port" -ForegroundColor Red
    }

    if ($botOk) {
        Write-Host ('    [OK]   AI Peers bot          PID ' + $BotStatus.Pid + '  (@grok @gemini @copilot)') -ForegroundColor Green
    } elseif ($BotStatus.Count -gt 1) {
        Write-Host "    [WARN] AI Peers bot          $($BotStatus.Count) bot trees -- expect exactly 1" -ForegroundColor Red
    } else {
        Write-Host "    [FAIL] AI Peers bot          not running" -ForegroundColor Red
    }

    if ($workerOk) {
        Write-Host ('    [OK]   Cursor worker         PID ' + $WorkerStatus.Pid + '  (' + $WorkerStatus.Name + ' -- tablet @ cursor.com/agents)') -ForegroundColor Green
    } else {
        Write-Host "    [WARN] Cursor worker         not running (tablet remote access unavailable)" -ForegroundColor DarkYellow
    }

    Write-Host ""
    if ($allOk) {
        Write-Host "  READY FOR DEMO / VIDEO SESSION" -ForegroundColor Green
        Write-Host '  Pre-flight: open Mattermost Town Square and post  @grok ping' -ForegroundColor Green
    } else {
        Write-Host "  NOT READY -- fix the [FAIL]/[WARN] items above, then run .\runall again" -ForegroundColor Red
    }
    Write-Host ""
    Write-Host $line -ForegroundColor Cyan
    Write-Host ""
}

Stop-PolySaaSServiceProcesses -Root $ProjectRoot

Write-Host ""
Write-Host "PolySaaS runall -- starting local services (Django is local-only for now)..." -ForegroundColor Cyan
Write-Host ""

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

$waitressPid = Start-PolySaaSWaitress -WaitressExe $WaitressExe -Root $ProjectRoot
$botStatus = Start-PolySaaSAIPeersBot -PythonExe $VenvPython -Root $ProjectRoot
$workerStatus = Start-PolySaaSCursorWorker -Root $ProjectRoot -Name $CursorWorkerName

$portOwners = @(Get-WaitressPortOwnerPids -Port $WaitressPort)
$waitressOk = ($portOwners.Count -eq 1)

Show-PolySaaSRunAllSummary -WaitressPid $waitressPid -WaitressOk $waitressOk -BotStatus $botStatus -WorkerStatus $workerStatus -Port $WaitressPort
