#!/usr/bin/env pwsh
# Start Services Script - Launches both Django and Pass-Through Service
# Date: August 16, 2025
#
# USE THIS FOR: Automated testing, CI/CD, background service monitoring, logging
# - Runs both Django (port 8000) and Pass-Through Service (port 5000) in background
# - Terminal remains interactive (use Get-Job, Receive-Job to check status)
# - Service health monitoring and port availability checks
# - Better for: Automated scripts, concurrent service testing, CI pipelines
#
# Example: .\start_services.ps1
# Then: Receive-Job -Name DjangoService -Keep  (to view logs)
#

Write-Host "🚀 Starting Dose Services..." -ForegroundColor Green
Write-Host "=====================================`n" -ForegroundColor Cyan

# Function to check if a process is running on a specific port
function Test-Port {
    param([int]$Port)
    $connection = Test-NetConnection -ComputerName "localhost" -Port $Port -InformationLevel Quiet -WarningAction SilentlyContinue
    return $connection
}

# Function to start Pass-Through Service
function Start-PassThroughService {
    Write-Host "📡 Starting Pass-Through Service (Port 5000)..." -ForegroundColor Yellow

    if (Test-Port -Port 5000) {
        Write-Host "⚠️  Port 5000 is already in use. Skipping pass-through service startup." -ForegroundColor Yellow
        return $false
    }

    # Change to pass-through service directory and start service
    $scriptPath = Split-Path -Parent $MyInvocation.MyCommand.Path
    $passThoughJob = Start-Job -ScriptBlock {
        param($basePath)
        Set-Location (Join-Path $basePath "pass_through_service")
        python app.py
    } -ArgumentList $scriptPath -Name "PassThroughService"

    Write-Host "✅ Pass-Through Service started (Job ID: $($passThoughJob.Id))" -ForegroundColor Green

    # Wait a moment for service to initialize
    Start-Sleep -Seconds 2
    return $true
}

# Function to start Django Service
function Start-DjangoService {
    Write-Host "🌐 Starting Django Service (Port 8000)..." -ForegroundColor Yellow

    if (Test-Port -Port 8000) {
        Write-Host "⚠️  Port 8000 is already in use. Skipping Django service startup." -ForegroundColor Yellow
        return $false
    }

    # Start Django development server
    $scriptPath = Split-Path -Parent $MyInvocation.MyCommand.Path
    $djangoJob = Start-Job -ScriptBlock {
        param($basePath)
        Set-Location $basePath
        python manage.py runserver
    } -ArgumentList $scriptPath -Name "DjangoService"

    Write-Host "✅ Django Service started (Job ID: $($djangoJob.Id))" -ForegroundColor Green

    # Wait a moment for service to initialize
    Start-Sleep -Seconds 3
    return $true
}

# Function to check service status
function Show-ServiceStatus {
    Write-Host "`n📊 Service Status Check..." -ForegroundColor Cyan
    Write-Host "=============================" -ForegroundColor Cyan

    # Check Pass-Through Service
    if (Test-Port -Port 5000) {
        Write-Host "🟢 Pass-Through Service: RUNNING (Port 5000)" -ForegroundColor Green
    } else {
        Write-Host "🔴 Pass-Through Service: NOT RUNNING" -ForegroundColor Red
    }

    # Check Django Service
    if (Test-Port -Port 8000) {
        Write-Host "🟢 Django Service: RUNNING (Port 8000)" -ForegroundColor Green
    } else {
        Write-Host "🔴 Django Service: NOT RUNNING" -ForegroundColor Red
    }

    Write-Host ""
}

# Function to show running background jobs
function Show-BackgroundJobs {
    Write-Host "💼 Background Jobs:" -ForegroundColor Cyan
    Write-Host "===================" -ForegroundColor Cyan

    $jobs = Get-Job | Where-Object { $_.Name -in @("PassThroughService", "DjangoService") }

    if ($jobs) {
        foreach ($job in $jobs) {
            $status = $job.State
            $statusColor = if ($status -eq "Running") { "Green" } else { "Red" }
            Write-Host "📋 $($job.Name): $status (ID: $($job.Id))" -ForegroundColor $statusColor
        }
    } else {
        Write-Host "No background service jobs found." -ForegroundColor Yellow
    }
    Write-Host ""
}

# Main execution
try {
    # Start services
    $passStarted = Start-PassThroughService
    $djangoStarted = Start-DjangoService

    # Show initial status
    Show-ServiceStatus
    Show-BackgroundJobs

    # Provide usage information
    Write-Host "🔧 Service Management Commands:" -ForegroundColor Cyan
    Write-Host "=================================" -ForegroundColor Cyan
    Write-Host "• Check Status: Get-Job" -ForegroundColor White
    Write-Host "• Stop Service: Stop-Job -Name 'ServiceName'" -ForegroundColor White
    Write-Host "• View Output: Receive-Job -Name 'ServiceName' -Keep" -ForegroundColor White
    Write-Host "• Stop All: Get-Job | Stop-Job; Get-Job | Remove-Job" -ForegroundColor White
    Write-Host ""

    Write-Host "🌐 Service URLs:" -ForegroundColor Cyan
    Write-Host "=================" -ForegroundColor Cyan
    Write-Host "• Django Admin: http://localhost:8000/admin-panel/" -ForegroundColor White
    Write-Host "• Django API: http://localhost:8000/api/" -ForegroundColor White
    Write-Host "• Pass-Through Health: http://localhost:5000/health" -ForegroundColor White
    Write-Host "• Test Middleware: http://localhost:8000/test-pass-through" -ForegroundColor White
    Write-Host ""

    # Test example
    Write-Host "🧪 Test Commands:" -ForegroundColor Cyan
    Write-Host "=================" -ForegroundColor Cyan
    Write-Host "# Test pass-through middleware:" -ForegroundColor Gray
    Write-Host 'Invoke-WebRequest -Uri "http://localhost:8000/test-pass-through"' -ForegroundColor Yellow
    Write-Host ""
    Write-Host "# Test direct pass-through service:" -ForegroundColor Gray
    Write-Host 'Invoke-WebRequest -Uri "http://localhost:5000/health"' -ForegroundColor Yellow
    Write-Host ""

    Write-Host "✨ Services are starting up! Check status above and test when ready." -ForegroundColor Green

} catch {
    Write-Host "❌ Error starting services: $($_.Exception.Message)" -ForegroundColor Red
    exit 1
}
