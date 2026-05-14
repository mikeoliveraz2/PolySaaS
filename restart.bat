@echo off
echo Killing Django on port 8000...
for /f "tokens=5" %%a in ('netstat -ano ^| findstr :8000 ^| findstr LISTENING') do (
    echo Killing PID %%a
    taskkill /F /PID %%a 2>nul
)
timeout /t 2 /nobreak >nul
echo.
echo Starting Django...
cd /d "C:\Users\PC\.windsurf\worktrees\PolySaaS\PolySaaS-a136a386"
d:\PolySaaS\venv\Scripts\python.exe manage.py runserver 0.0.0.0:8000
