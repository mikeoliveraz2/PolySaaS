# PolySaaS Developer Setup Guide

Welcome! This guide will walk you through setting up a local PolySaaS development environment on Windows, macOS, or Linux.

## Prerequisites

- **Python 3.10+** (verify with `python --version`)
- **PostgreSQL 12+** (running and accessible)
- **Git** (for cloning and version control)
- **Node.js 16+** (optional, for frontend tooling)

---

## 1. Clone the Repository

```bash
git clone https://github.com/mikeoliveraz2/PolySaaS.git
cd PolySaaS
```

---

## 2. Create and Activate a Virtual Environment

### Windows (PowerShell)
```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
```

### macOS / Linux (Bash/Zsh)
```bash
python3 -m venv venv
source venv/bin/activate
```

---

## 3. Install Python Dependencies

```bash
pip install --upgrade pip setuptools wheel
pip install -r requirements.txt
```

If you're developing and want linting/testing tools:
```bash
pip install -r requirements-dev.txt
```

---

## 4. Configure Environment Variables

Copy the example environment file and customize it:

```bash
cp .env.example .env
```

Edit `.env` and set these minimum required values:

```env
# Django security
DJANGO_SECRET_KEY=your-secret-key-here-min-50-chars
DEBUG=true
ALLOWED_HOSTS=localhost,127.0.0.1

# Database (adjust for your local PostgreSQL)
DB_NAME=polysaas_dev
DB_USER=postgres
DB_HOST=127.0.0.1
DB_PORT=5432
DOSE_DB_PASSWORD=your-postgres-password

# Mattermost (for AI peers bot — optional for local demo)
MATTERMOST_URL=http://localhost:8065
MATTERMOST_ADMIN_TOKEN=your-mattermost-token-or-leave-blank

# API Keys (optional — leave blank for local testing)
ANTHROPIC_API_KEY=
XAI_API_KEY=
GEMINI_API_KEY=
HUBSPOT_CLIENT_ID=
HUBSPOT_CLIENT_SECRET=
```

---

## 5. Create and Migrate the Database

```bash
# Create the PostgreSQL database
createdb polysaas_dev

# Run Django migrations
python manage.py migrate

# Create a superuser for /admin/
python manage.py createsuperuser
```

---

## 6. Collect Static Files (for Waitress)

```bash
python manage.py collectstatic --noinput
```

---

## 7. Start the Development Services

### Option A: Use the Orchestration Script (Recommended on Windows)

```powershell
.\runall.ps1
```

This will:
- Start Waitress on `http://localhost:8000`
- Sync AI peer bots to Mattermost (if configured)
- Display service status

### Option B: Manual Django Runserver (Simpler Alternative)

```bash
python manage.py runserver 0.0.0.0:8000
```

Then open: **http://localhost:8000**

---

## 8. Access the Application

| Component | URL | Purpose |
|-----------|-----|---------|
| **Main App** | http://localhost:8000 | Public-facing PolySaaS UI |
| **Admin Dashboard** | http://localhost:8000/admin/ | Django admin (use superuser creds) |
| **Dose Portal** | http://localhost:8000/dose/home/ | Tenant management |
| **PolySniffer** | http://localhost:8000/dose/sniff/ | Passthrough traffic capture tool |

---

## 9. Project Structure Overview

```
PolySaaS/
├── manage.py                    # Django CLI entry point
├── mysite/                      # Django project settings
│   ├── settings.py              # Main config (uses .env)
│   ├── urls.py                  # URL routing
│   └── wsgi.py                  # WSGI app (for Waitress)
├── dose/                        # Main app (authentication, endpoints, orchestration)
│   ├── models.py                # Database models
│   ├── admin.py                 # Django admin registration
│   ├── views/                   # Views and handlers
│   └── passthrough/             # Passthrough proxy logic
├── polysniffer/                 # Traffic capture and diagnostics
│   ├── models.py                # TrafficLog, CaptureSession
│   └── views/                   # Workspace shell, polling
├── requirements.txt             # Python package list
├── runall.ps1                   # Service orchestration (Windows)
├── .env.example                 # Environment template
└── README.md                    # User documentation

```

---

## 10. Common Development Tasks

### Run Database Migrations

```bash
python manage.py makemigrations
python manage.py migrate
```

### Check Django Shell

```bash
python manage.py shell
```

### Run Tests

```bash
python manage.py test
```

### View Logs (if using Waitress)

Check the terminal where `.\runall.ps1` or Django runserver is running.

### Reset Database (Careful!)

```bash
# Delete the DB
dropdb polysaas_dev

# Recreate and migrate
createdb polysaas_dev
python manage.py migrate
```

---

## 11. Troubleshooting

### `ImportError: No module named 'dose'`
- Ensure you're in the project root and virtual environment is activated.
- Run `pip install -r requirements.txt` again.

### `psycopg2` installation fails
- **Windows**: Install PostgreSQL dev headers; ensure `pg_config` is in PATH.
- **macOS**: `brew install postgresql`
- **Linux**: `sudo apt-get install postgresql-dev` (Debian/Ubuntu)

### Port 8000 already in use
- Change the port: `python manage.py runserver 0.0.0.0:8001`
- Or kill the process: 
  - **Windows (PowerShell)**: `Get-NetTCPConnection -LocalPort 8000 | Stop-Process -Force`
  - **macOS/Linux**: `lsof -i :8000 | grep LISTEN | awk '{print $2}' | xargs kill -9`

### Database connection refused
- Verify PostgreSQL is running
- Check `DB_HOST`, `DB_USER`, `DOSE_DB_PASSWORD` in `.env`
- Test: `psql -h 127.0.0.1 -U postgres -d polysaas_dev`

### `runall.ps1` execution policy error
```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy RemoteSigned
```

---

## 12. Next Steps

1. **Explore the Admin Panel**: Log in to http://localhost:8000/admin/ with your superuser account.
2. **Create a Tenant**: Use `/dose/home/` to set up your first organization.
3. **Add Passthrough Endpoints**: Configure integrations (HubSpot, Mattermost, Odoo, etc.).
4. **Test PolySniffer**: Use the workspace to capture and inspect upstream traffic.

---

## 13. Additional Resources

- **Django Docs**: https://docs.djangoproject.com/
- **PolySaaS Admin Docs**: http://localhost:8000/help/
- **Issue Tracker**: https://github.com/mikeoliveraz2/PolySaaS/issues
- **Main README**: [README.md](README.md) for architecture and deployment info

---

## 14. Getting Help

- Check existing GitHub issues
- Post a new issue with:
  - Your OS and Python version
  - Error messages and stack traces
  - Steps to reproduce
  - Expected vs. actual behavior

Happy developing! 🚀
