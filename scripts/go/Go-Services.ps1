function Start-IfNotRunning {
    param([int]$Port, [string]$ScriptBlock, [string]$Name)
    $listener = Get-NetTCPConnection -State Listen -LocalPort $Port -ErrorAction SilentlyContinue
    if ($listener) {
        Write-Host "$Name already running on port $Port -> SKIPPING" -ForegroundColor Green
    } else {
        Write-Host "Starting $Name on port $Port..." -ForegroundColor Yellow
        Start-Process powershell -ArgumentList "-NoExit", "-Command", $ScriptBlock
    }
}

function Start-GoBackgroundServices {
    param(
        [Parameter(Mandatory)]
        [string]$ScriptRoot,
        [Parameter(Mandatory)]
        [string]$PythonExe
    )

    $monitorFolder = Join-Path $ScriptRoot "pass_through_service"
    Start-IfNotRunning -Port 5000 -Name "Monitor Logger" -ScriptBlock "cd '$monitorFolder'; & '$PythonExe' app.py"

    Start-IfNotRunning -Port 5002 -Name "PolySniffer" -ScriptBlock "cd '$ScriptRoot'; & '$PythonExe' polysniffer_simple.py"

    $polysysmonFolder = Join-Path $ScriptRoot "placeholders\polysysmon"
    if (-Not (Get-NetTCPConnection -State Listen -LocalPort 9001 -ErrorAction SilentlyContinue)) {
        Write-Host 'Starting PolySysMon (Tomcat Docker) on port 9001...' -ForegroundColor Yellow
        Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd '$polysysmonFolder'; docker build -t polysysmon-demo .; docker run -d -p 9001:8080 polysysmon-demo"
    } else {
        Write-Host "PolySysMon already running on port 9001 -> SKIPPING" -ForegroundColor Green
    }

    $liferayListening = Get-NetTCPConnection -State Listen -LocalPort 8181 -ErrorAction SilentlyContinue
    if (-Not $liferayListening) {
        $liferayCompose = Join-Path $ScriptRoot "docker-compose.liferay.yml"
        if (Test-Path $liferayCompose) {
            Write-Host "Starting Liferay CE on port 8181..." -ForegroundColor Yellow
            Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd '$ScriptRoot'; docker compose -f docker-compose.liferay.yml up"
        } else {
            Write-Host "Liferay compose file not found -> SKIPPING" -ForegroundColor DarkYellow
        }
    } else {
        Write-Host "Liferay CE already running on port 8181 -> SKIPPING" -ForegroundColor Green
    }
}
