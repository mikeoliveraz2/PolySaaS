@echo off
REM Start Services Batch Script - Launches both Django and Pass-Through Service
REM Date: August 16, 2025

REM Get the script directory (workspace root)
cd /d "%~dp0"

echo.
echo ========================================
echo   🚀 Starting Dose Services
echo ========================================
echo.

echo 📡 Starting Pass-Through Service (Port 5000)...
start "Pass-Through Service" /D "%~dp0pass_through_service" cmd /k "python app.py"

echo.
timeout /t 3 /nobreak >nul

echo 🌐 Starting Django Service (Port 8000)...
if exist "venv\Scripts\activate.bat" (
    start "Django Service" cmd /k "call venv\Scripts\activate.bat && python manage.py runserver"
) else (
    start "Django Service" cmd /k "python manage.py runserver"
)

echo.
timeout /t 2 /nobreak >nul

echo ✅ Both services are starting up!
echo.
echo 🌐 Service URLs:
echo   • Django Admin: http://localhost:8000/admin-panel/
echo   • Django API: http://localhost:8000/api/
echo   • Pass-Through Health: http://localhost:5000/health
echo   • Test Middleware: http://localhost:8000/test-pass-through
echo.
echo 🧪 Test Commands:
echo   Invoke-WebRequest -Uri "http://localhost:8000/test-pass-through"
echo   Invoke-WebRequest -Uri "http://localhost:5000/health"
echo.
echo Press any key to continue...
pause >nul
