@echo off
REM DoseV3 Migration Script - All Tenants
cd /d "c:\DoseSaaS\October merge\DoseV3MasterSaaS-main-main"
call "venv\Scripts\activate.bat"
echo Running migrations for all tenant schemas...
python run_migrations.py
pause