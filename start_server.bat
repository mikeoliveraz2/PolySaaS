@echo off
REM DoseV3 Server Start Script
REM Get the script directory (workspace root)
cd /d "%~dp0"

if exist "venv\Scripts\activate.bat" (
    call "venv\Scripts\activate.bat"
    echo Starting Django development server...
    python manage.py runserver 0.0.0.0:8000
) else (
    echo Error: Virtual environment not found at venv\Scripts\activate.bat
    echo Please ensure the virtual environment is set up.
    exit /b 1
)