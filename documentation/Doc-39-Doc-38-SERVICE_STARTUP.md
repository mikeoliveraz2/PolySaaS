# Dose Services Startup Options

Multiple ways to start both Django and Pass-Through services together:

## Option 1: Django Management Command (Recommended)
```powershell
python manage.py runservices
```

**Features:**
- Integrated Django management command
- Port conflict detection
- Process monitoring
- Clean shutdown with Ctrl+C
- Service status reporting

**Options:**
```powershell
# Custom ports
python manage.py runservices --django-port 8080 --passthrough-port 5001

# Skip pass-through service
python manage.py runservices --no-passthrough

# Help
python manage.py runservices --help
```

## Option 2: Python Script
```powershell
python run_services.py
```

**Features:**
- Standalone Python script
- Process monitoring
- Automatic cleanup
- Status reporting

## Option 3: PowerShell Script  
```powershell
.\start_services.ps1
```

**Features:**
- Advanced PowerShell features
- Background job management
- Rich status display
- Port checking

## Option 4: Batch File
```cmd
start_services.bat
```

**Features:**
- Simple Windows batch script
- Opens separate command windows
- Quick startup

## Service URLs

Once started, services are available at:

- **Django Admin**: http://localhost:8000/admin-panel/
- **Django API**: http://localhost:8000/api/
- **Pass-Through Health**: http://localhost:5000/health
- **Test Middleware**: http://localhost:8000/test-pass-through

## Testing Commands

```powershell
# Test pass-through middleware
Invoke-WebRequest -Uri "http://localhost:8000/test-pass-through"

# Test pass-through service directly
Invoke-WebRequest -Uri "http://localhost:5000/health"

# Test with POST data
$body = '{"test": "data", "user": "testing"}'
Invoke-WebRequest -Uri "http://localhost:8000/api/test" -Method POST -Body $body -Headers @{"Content-Type"="application/json"}
```

## Stopping Services

- **Management Command**: Press `Ctrl+C`
- **Python Script**: Press `Ctrl+C`
- **PowerShell Jobs**: `Get-Job | Stop-Job; Get-Job | Remove-Job`
- **Batch Windows**: Close the command windows

---

**Recommended**: Use `python manage.py runservices` for the best integrated experience.
