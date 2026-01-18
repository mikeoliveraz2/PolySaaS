# DoseV3 Migration Script - All Tenants (PowerShell)
Set-Location "c:\DoseSaaS\October merge\DoseV3MasterSaaS-main-main"
& "venv\Scripts\Activate.ps1"
Write-Host "Running migrations for all tenant schemas..."
& python run_migrations.py
Read-Host "Press Enter to continue..."