# Local Standalone Stack

This stack is the laptop baseline for replacing Render and preparing the same service shape for GCP.

## Services

`docker-compose.local.yml` starts:

- Core Postgres: `localhost:15433`
- Redis: `localhost:6379`
- RabbitMQ: `localhost:5672`, management UI `localhost:15672`
- Mattermost: `http://localhost:8065`
- Nextcloud: `http://localhost:8888`
- Odoo: `http://localhost:8086`
- Dolibarr: `http://localhost:8083`

The Django core still runs on the host with `manage.py`; this keeps local debugging simple and matches the current repo workflow.

## First Run

1. Copy `.env.local.example` values into `.env`, or merge the local DB/app URL values into your existing `.env`.
2. Start the local containers:

   ```powershell
   docker compose --env-file .env -f docker-compose.local.yml up -d
   ```

3. Run Django migrations against the local Postgres:

   ```powershell
   venv\Scripts\python.exe manage.py migrate
   ```

4. Start Django:

   ```powershell
   venv\Scripts\python.exe manage.py runserver 127.0.0.1:8000
   ```

## Notes

- Odoo may still require first-time database initialization in its web UI before XML-RPC provisioning succeeds.
- Mattermost requires an admin account and personal access token before automated provisioning can create teams/users.
- Nextcloud and Dolibarr are configured with bootstrap admin credentials from `POLYSAAS_APP_ADMIN_PASSWORD`.
- Do not use the Render compose files as the local baseline; they are reference material and still contain Render-oriented assumptions.

## Useful Commands

```powershell
docker compose --env-file .env -f docker-compose.local.yml ps
docker compose --env-file .env -f docker-compose.local.yml logs -f core-postgres
docker compose --env-file .env -f docker-compose.local.yml down
```

To reset local data, stop the stack and remove the named volumes intentionally:

```powershell
docker compose --env-file .env -f docker-compose.local.yml down -v
```