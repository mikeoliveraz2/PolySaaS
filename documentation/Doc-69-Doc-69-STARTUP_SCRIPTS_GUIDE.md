# Service Startup Scripts - Quick Reference

**Last Updated**: October 26, 2025

---

## Quick Decision Tree

```
Do you need to:
│
├─ Test features manually?
│  └─ Run interactive debugging?
│     └─ See logs in real-time?
│        └─ Want foreground blocking? → USE: .\go.ps1
│
└─ Run automated testing?
   └─ Monitor multiple services?
      └─ Keep terminal interactive?
         └─ Want background jobs? → USE: .\start_services.ps1
```

---

## .\go.ps1 - Single Service, Interactive

### When to Use
✅ **User testing** - testing features manually  
✅ **Development** - interactive debugging  
✅ **Learning** - understanding how things work  
✅ **Real-time logging** - watching output as it happens

### What It Does
- ✅ Activates virtual environment
- ✅ Loads `.env` variables
- ✅ Starts Django development server on port 8000
- ❌ Does NOT start pass-through service
- 📌 **Blocks terminal** (can't run other commands)

### How to Use
```powershell
# Start Django in foreground
.\go.ps1

# Logs appear directly in terminal
# Press Ctrl+C to stop
```

### Pros & Cons
| Pros | Cons |
|------|------|
| ✅ Full venv activation | ❌ Terminal blocked |
| ✅ .env variables loaded | ❌ No pass-through service |
| ✅ Real-time output | ❌ Can't run other commands |
| ✅ Easy debugging | ⚠️ Only Django |

---

## .\start_services.ps1 - Dual Service, Background

### When to Use
✅ **Automated testing** - CI/CD pipelines  
✅ **Service monitoring** - checking status  
✅ **Logging analysis** - examining historical output  
✅ **Concurrent testing** - testing multiple services

### What It Does
- ✅ Starts Django on port 8000 (background job)
- ✅ Starts Pass-Through Service on port 5000 (background job)
- ✅ Checks port availability
- ✅ Shows service status
- 📌 **Terminal remains interactive** (non-blocking)

### How to Use
```powershell
# Start both services in background
.\start_services.ps1

# Terminal is still usable - run other commands

# View Django logs
Receive-Job -Name DjangoService -Keep

# View Pass-Through logs
Receive-Job -Name PassThroughService -Keep

# Check status
Get-Job | Where-Object { $_.Name -like "*Service" }

# Stop all services
Get-Job | Stop-Job
Get-Job | Remove-Job
```

### Pros & Cons
| Pros | Cons |
|------|------|
| ✅ Background execution | ❌ Hard-coded user paths |
| ✅ Dual services | ⚠️ No venv activation |
| ✅ Terminal interactive | ⚠️ No .env loading |
| ✅ Health monitoring | ⚠️ More complex |

### ⚠️ Known Issues
- Hard-coded paths for `michael.oliver` user
- Does NOT activate venv
- Does NOT load .env variables
- May fail to start if paths are wrong

---

## Recommended Workflow

### For Testing OSTicket Integration

**Step 1: Start Services**
```powershell
# Terminal 1: Start Django
.\go.ps1

# Wait for "Starting development server" message
```

**Step 2: Test in Browser**
```
Open: http://localhost:8000/admin/osticket/
Expected: OSTicket login page with styling
```

**Step 3: Monitor Logs**
```
Watch Terminal 1 for:
- [DOSEIFY] >>>>>>>>>> SECTION markers
- HTTP requests from browser
- Any errors or warnings
```

**Step 4: Submit Test Forms**
```
In browser:
1. Enter OSTicket credentials
2. Click "Log In"
3. Watch terminal for:
   - POST to /admin/osticket/scp/login.php
   - Session cookie handling
   - Response HTML processing
```

**Step 5: Stop Services**
```powershell
# Press Ctrl+C in Terminal 1
# Django server stops
# venv deactivates
```

---

## Command Reference

### Using .\go.ps1
```powershell
# Start
.\go.ps1

# Monitor (no extra command needed - output in terminal)

# Stop
Ctrl+C

# Check venv
python --version  # After activation
```

### Using .\start_services.ps1
```powershell
# Start
.\start_services.ps1

# View Django logs (live)
Receive-Job -Name DjangoService -Keep

# View Pass-Through logs (live)
Receive-Job -Name PassThroughService -Keep

# Check which jobs running
Get-Job

# Get latest logs only
Receive-Job -Name DjangoService

# Stop specific service
Stop-Job -Name DjangoService

# Stop all services
Get-Job | Stop-Job
Get-Job | Remove-Job
```

---

## Troubleshooting

### Issue: "venv not found" with go.ps1
```
Solution: Run from project root directory
cd C:\Users\PC\OneDrive\Documents\GitHub\DoseV3MasterSaaS-main-main
.\go.ps1
```

### Issue: Port 8000 already in use
```powershell
# Kill existing Python processes
Get-Process python -ErrorAction SilentlyContinue | Stop-Process -Force

# Then start again
.\go.ps1
```

### Issue: start_services.ps1 fails with path error
```
Reason: Hard-coded user paths for michael.oliver
Status: Known limitation, paths need to be updated for your user
Workaround: Use .\go.ps1 instead
```

### Issue: No logs appearing with start_services.ps1
```powershell
# Check if jobs are running
Get-Job

# Retrieve logs
Receive-Job -Name DjangoService -Keep

# If job failed, check errors
Receive-Job -Name DjangoService -Error
```

---

## Summary

| Scenario | Use Script |
|----------|-----------|
| Manual feature testing | `.\go.ps1` ✅ |
| Development & debugging | `.\go.ps1` ✅ |
| Watching logs in real-time | `.\go.ps1` ✅ |
| Automated CI/CD testing | `.\start_services.ps1` ⚠️ |
| Monitoring multiple services | `.\start_services.ps1` ⚠️ |
| Background execution needed | `.\start_services.ps1` ⚠️ |

**For OSTicket Integration Testing**: Use `.\go.ps1` for interactive testing and real-time log monitoring.

---

