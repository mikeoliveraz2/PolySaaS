# PolySaaS — Laptop Dev Environment Setup Note

**For: Cursor/Claude on laptop**
**From: Office machine (E:\PolySaaS) — Feb 23, 2026**

## Source of Truth

- **Repo**: `https://github.com/mikeoliveraz2/PolySaaS.git`
- **Branch**: `main`
- **Clone command**: `git clone https://github.com/mikeoliveraz2/PolySaaS.git`

Other repos (`mikeoliveraz1/polysaas`, `michaeloliver-chief/PolySaaS`) are historical artifacts. All real work lives in `mikeoliveraz2/PolySaaS` on `main`.

## Current State (as of this commit)

### Stack
- **Django 5.x** with Jazzmin admin theme
- **PostgreSQL 16** on port 5433, database `dosedb`, user `dosedbadmin`, password `dosedbpass`
- **Multi-tenant** architecture: each tenant has its own PostgreSQL schema; no tenant data in `public`
- **DRF + drf_yasg** for REST API with Swagger UI at `/swagger/`
- **Docker containers**: Nextcloud (port 8888), Liferay CE (port 8181), PolySysMon (port 9001), WordPress (port 8080)

### Key Apps
- **dose** — Core multi-tenant SaaS app (models, views, admin, passthrough endpoints)
- **dose.polysniffer** — Chrome extension + Django backend for capturing raw HTTP traffic from external services
- **parameters** — System parameter management

### PolySniffer Architecture (Two-Tab, No Iframes)
1. Admin clicks "PolySniffer Analysis" on a PassThroughEndpoint
2. Tab 1: Live Capture page polls Django for captured traffic (`/admin/polysniffer/capture/{id}/`)
3. Tab 2: User browses the target service directly (e.g., Nextcloud at localhost:8888)
4. Chrome extension (`polysniffer-chrome-extension/`) auto-configures from the capture page, intercepts network traffic via `chrome.webRequest`, and POSTs it to Django's `silent_capture` endpoint
5. Live Capture page polls `get_captures` and displays traffic in real-time

### Swagger/API
- All models have DRF serializers, viewsets, and router registrations in `dose/serializers.py`, `dose/viewsets.py`, `dose/urls.py`
- PassThroughEndpoint API includes computed `proxy_url`, `admin_url`, and `polysniffer_url` fields
- Swagger UI linked in admin top menu via Jazzmin settings

### Process Rules (see `.cursor/rules/process-rules.mdc`)
1. **No unilateral changes** — propose, get approval, then implement
2. **Post-commit lock** — committed+documented files are read-only without permission
3. **Speak up** — raise concerns and suggestions proactively
4. **Commit implies push** — every commit is immediately pushed to origin

## Local Setup Steps

```bash
# 1. Clone
git clone https://github.com/mikeoliveraz2/PolySaaS.git
cd PolySaaS

# 2. Virtual environment
python -m venv venv
venv\Scripts\activate  # Windows
# source venv/bin/activate  # Linux/Mac

# 3. Install dependencies
pip install -r requirements.txt

# 4. Environment file
# Create .env in project root with:
#   DJANGO_SECRET_KEY=<your-key>
#   DOSE_DB_PASSWORD=dosedbpass

# 5. PostgreSQL
# Ensure PostgreSQL 16 is running on port 5433
# Database: dosedb, User: dosedbadmin, Password: dosedbpass

# 6. Migrate (all schemas)
python manage.py migrate

# 7. Docker services (optional, as needed)
docker run -d --name polysaas-nextcloud -p 8888:80 --restart unless-stopped nextcloud:latest
docker compose -f docker-compose.liferay.yml up -d

# 8. Run
python manage.py runserver
# Or use go.ps1 which starts everything including daily backup
```

## Files NOT to Touch Without Permission
All files from the last documented commit (`1d17fd3` — "PolySniffer: two-tab live capture with Chrome extension, add Swagger to admin menu") are considered tested and locked per Rule 2.
