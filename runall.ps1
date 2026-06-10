# PolySaaS Run All Services
# Activates venv, starts Waitress WSGI server (Windows), syncs AI peers, starts Mattermost bot

$ErrorActionPreference = "Stop"
$ProjectRoot = if ($PSScriptRoot) { $PSScriptRoot } else { "D:\PolySaaS" }
$WaitressListen = "0.0.0.0:8000"
$WaitressPort = 8000
$WaitressThreads = 16

function Get-PolySaaSVenvPython {
    param([string]$Root)
    foreach ($folder in @("venv", ".venv")) {
        $python = Join-Path $Root "$folder\Scripts\python.exe"
        if (Test-Path $python) { return $python }
    }
    throw "No venv found under $Root (expected venv\Scripts\python.exe or .venv\Scripts\python.exe)"
}

function Stop-ListenerOnPort {
    param(
        [int]$Port,
        [string]$Label = "port $Port"
    )
    $listeners = @(Get-NetTCPConnection -State Listen -LocalPort $Port -ErrorAction SilentlyContinue)
    foreach ($conn in $listeners) {
        $procId = $conn.OwningProcess
        if (-not $procId -or $procId -le 0) { continue }
        try {
            $proc = Get-Process -Id $procId -ErrorAction Stop
            Stop-Process -Id $procId -Force -ErrorAction Stop
            Write-Host "  Stopped $($proc.ProcessName) (PID $procId) on $Label" -ForegroundColor Yellow
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
            Stop-Process -Id $_.ProcessId -Force -ErrorAction SilentlyContinue
        }

        Start-Sleep -Seconds 2

        $onPort = @(Get-NetTCPConnection -State Listen -LocalPort $WaitressPort -ErrorAction SilentlyContinue)
        $left = @(Get-PolySaaSServiceProcesses -Root $Root)
        if ($onPort.Count -eq 0 -and $left.Count -eq 0) { break }
        if ($round -lt 3) {
            Write-Host "  Round $round — port/listeners still present, retrying..." -ForegroundColor DarkYellow
        }
    }

    $remainingPort = @(Get-NetTCPConnection -State Listen -LocalPort $WaitressPort -ErrorAction SilentlyContinue)
    if ($remainingPort.Count -gt 0) {
        Write-Host "WARNING: port $WaitressPort still has $($remainingPort.Count) listener(s)" -ForegroundColor Red
    }
}

function Wait-ForSinglePortListener {
    param(
        [int]$Port,
        [int]$TimeoutSec = 20
    )
    $deadline = (Get-Date).AddSeconds($TimeoutSec)
    while ((Get-Date) -lt $deadline) {
        $listeners = @(Get-NetTCPConnection -State Listen -LocalPort $Port -ErrorAction SilentlyContinue)
        if ($listeners.Count -eq 1) { return $listeners[0].OwningProcess }
        if ($listeners.Count -gt 1) { return -1 }
        Start-Sleep -Milliseconds 400
    }
    return $null
}

function Start-PolySaaSWaitress {
    param(
        [string]$WaitressExe,
        [string]$Root
    )

    Write-Host "Starting Waitress on http://$WaitressListen (threads=$WaitressThreads)..." -ForegroundColor Green
    Start-Process -FilePath $WaitressExe `
        -ArgumentList "--listen=$WaitressListen", "--threads=$WaitressThreads", "mysite.wsgi:application" `
        -WorkingDirectory $Root `
        -WindowStyle Hidden

    $ownerPid = Wait-ForSinglePortListener -Port $WaitressPort
    if ($ownerPid -eq -1) {
        Write-Host "Multiple listeners on port $WaitressPort — killing and restarting Waitress once..." -ForegroundColor Red
        Stop-ListenerOnPort -Port $WaitressPort
        Start-Sleep -Seconds 2
        Start-Process -FilePath $WaitressExe `
            -ArgumentList "--listen=$WaitressListen", "--threads=$WaitressThreads", "mysite.wsgi:application" `
            -WorkingDirectory $Root `
            -WindowStyle Hidden
        $ownerPid = Wait-ForSinglePortListener -Port $WaitressPort
    }

    if (-not $ownerPid -or $ownerPid -le 0) {
        throw "Waitress failed to bind port $WaitressPort within timeout"
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
        Stop-Process -Id $_.ProcessId -Force -ErrorAction SilentlyContinue
    }
    Start-Sleep -Seconds 1

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
    Start-Sleep -Seconds 3

    $bots = @(Get-AIPeersBotProcesses)
    if ($bots.Count -gt 1) {
        Write-Host "Found $($bots.Count) bot processes — keeping none, restarting one..." -ForegroundColor Red
        $bots | ForEach-Object { Stop-Process -Id $_.ProcessId -Force -ErrorAction SilentlyContinue }
        Start-Sleep -Seconds 1
        Start-Process -FilePath $PythonExe `
            -ArgumentList "manage.py", "run_mattermost_bot" `
            -WorkingDirectory $Root `
            -WindowStyle Hidden
        Start-Sleep -Seconds 2
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
$portListeners = @(Get-NetTCPConnection -State Listen -LocalPort $WaitressPort -ErrorAction SilentlyContinue)
Write-Host "  Port $WaitressPort listeners: $($portListeners.Count)" -ForegroundColor $(if ($portListeners.Count -eq 1) { 'Green' } else { 'Red' })

Get-CimInstance Win32_Process -Filter "Name='python.exe' OR Name='waitress-serve.exe'" -ErrorAction SilentlyContinue |
    Where-Object {
        $_.CommandLine -like '*waitress-serve*' -or $_.CommandLine -like '*run_mattermost_bot*' -or $_.CommandLine -like '*manage.py runserver*'
    } |
    Select-Object ProcessId, @{N='Service';E={
        if ($_.CommandLine -like '*waitress-serve*') { "Waitress ($WaitressListen)" }
        elseif ($_.CommandLine -like '*run_mattermost_bot*') { 'AI Peers bot' }
        elseif ($_.CommandLine -like '*runserver*') { 'Django runserver (legacy)' }
        else { 'Other' }
    }} | Format-Table -AutoSize

Write-Host "`nAll services started!" -ForegroundColor Green
Write-Host "Django (Waitress): http://localhost:$WaitressPort" -ForegroundColor White
Write-Host "AI Peers:          @copilot @grok @gemini in Town Square (single WebSocket bot process)" -ForegroundColor White
