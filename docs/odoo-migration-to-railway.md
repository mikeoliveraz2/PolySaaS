# Odoo on Railway: Working Deployment Runbook
_Date: 2026-04-13_

## Status
This document replaces the earlier migration-only notes with the deployment pattern that is now confirmed working on Railway for the `Odoo-mo` service.

Known-good outcomes:
- Odoo 18 starts cleanly on Railway
- the service initializes `base` when the target database exists but is still empty
- the app listens on Railway port `8069`
- the internal service is reachable on `odoo-mo.railway.internal`
- the public domain responds through Railway instead of returning `502`

---

## Canonical Deployment Layout
The Railway-managed Odoo deployment now lives under `docker/odoo/`:
- `docker/odoo/Dockerfile`
- `docker/odoo/odoo.conf`
- `docker/odoo/start-odoo.sh`

This is the canonical path for future bundled-app Odoo deployments. Do not rely on ad hoc Railway start commands or older `docker-compose.railway.yml` assumptions for Odoo.

---

## What Finally Worked

### 1. Use repo-controlled startup, not Railway command overrides
Railway was able to bypass earlier startup logic when the container relied on `CMD` or service-level command behavior.

The working fix was to force the startup wrapper through Docker `ENTRYPOINT`:

```dockerfile
ENTRYPOINT ["/start-odoo.sh"]
```

That guarantees the wrapper runs on every deploy and every restart.

### 2. Generate a runtime config from Railway environment variables
The wrapper copies the repo config to `/tmp/odoo-runtime.conf` and rewrites DB settings from the actual runtime environment.

This is important because earlier attempts left templated or stale values in the config, including bad host strings such as `${{Postgres.HOST}}`.

The working sources of truth are:
- `DB_*`
- `PG*`
- `POSTGRES_*`
- `ODOO_DATABASE_*`

The wrapper normalizes those into:
- `DB_NAME`
- `DB_HOST`
- `DB_PORT`
- `DB_USER`
- `DB_PASSWORD`

### 3. Treat “database exists” and “database initialized” as different states
A major failure mode was assuming that an existing database was ready for Odoo.

That was false.

The working logic is:
- if the target database does not exist: run one-time `-i base --stop-after-init`
- if the database exists but `public.ir_module_module` is missing: also run one-time `-i base --stop-after-init`
- otherwise: start Odoo normally

This avoids both failure modes:
- infinite re-initialization on every boot
- skipping initialization for an empty but already-created database

### 4. Pin Railway networking to the app port Odoo actually serves
The app is expected to serve HTTP on `8069`.

The confirmed working configuration is:
- Odoo config: `http_port = 8069`
- Railway service variable: `PORT=8069`
- Odoo config: `proxy_mode = True`
- Odoo config: `http_interface = 0.0.0.0`

### 5. Use Railway internal Postgres host directly
The final good DB target was the Railway internal hostname:

```text
postgres.railway.internal
```

The repo config now hardens around that value, and the startup wrapper rewrites runtime config from env vars before launch.

---

## Current Known-Good Files

### `docker/odoo/Dockerfile`
Purpose:
- builds from `odoo:18.0`
- installs repo-managed config
- forces the startup wrapper through `ENTRYPOINT`

Important behavior:
- replaces stale templated DB host values if they slip into the image
- copies `start-odoo.sh`
- leaves startup orchestration to the wrapper

### `docker/odoo/start-odoo.sh`
Purpose:
- normalizes Railway environment variables
- writes `/tmp/odoo-runtime.conf`
- checks whether the database exists
- checks whether the database is initialized
- runs one-time base initialization only when needed
- launches Odoo as the `odoo` user through the official entrypoint

Important checks:
- `db_exists()`
- `db_initialized()` via `to_regclass('public.ir_module_module')`

### `docker/odoo/odoo.conf`
Purpose:
- source-controlled base configuration

Important settings:
- `db_host = postgres.railway.internal`
- `db_port = 5432`
- `db_user = odoo`
- `db_name = odoo`
- `proxy_mode = True`
- `http_port = 8069`
- `http_interface = 0.0.0.0`
- `data_dir = /var/lib/odoo`

---

## Railway Service Variables
Set or confirm these on the Odoo Railway service:

| Variable | Expected value |
|---|---|
| `POSTGRES_HOST` | `postgres.railway.internal` |
| `ODOO_DATABASE_HOST` | `postgres.railway.internal` |
| `PORT` | `8069` |
| `DB_NAME` or equivalent | `odoo` |
| `DB_USER` or equivalent | `odoo` |
| `DB_PASSWORD` or equivalent | actual Railway Postgres password |

Notes:
- The wrapper accepts multiple variable families, but the service should still be kept explicit.
- Prefer concrete Railway values over template-like placeholders.
- Do not commit database passwords into the repo.

---

## Validation Signals
Healthy deployment signals looked like this:
- startup logs mention the wrapper path and runtime config file
- DB host resolves to `postgres.railway.internal`, not `${{Postgres.HOST}}`
- one-time base initialization completes successfully when needed
- Odoo restarts cleanly and stays up
- cron jobs begin running
- Railway public URL returns an HTTP response such as `303` instead of `502`

If those conditions are true, the service is usually healthy even if earlier deploys failed repeatedly.

---

## Failure Modes We Hit

| Failure mode | Root cause | Working fix |
|---|---|---|
| Odoo kept using `${{Postgres.HOST}}` | config interpolation was not happening in the deployed runtime | harden config and rewrite values in the startup wrapper |
| Odoo startup logic did not run | Railway command behavior bypassed `CMD`-based startup assumptions | force wrapper through Docker `ENTRYPOINT` |
| DB existed but Odoo still failed like it was empty | the database existed but base tables had not been created | detect initialization state using `ir_module_module` |
| Internal health looked good but public URL returned `502` | Railway proxying was not aligned to the app port | set `PORT=8069` and ensure Odoo listens on `8069` |
| Filestore writes failed or risked failing | Railway volume ownership can be root-owned | repair `/var/lib/odoo` ownership before launching Odoo |

---

## Lessons Learned For Future Bundled Apps
1. Make repo-controlled startup logic the default. Do not depend on platform command overrides for critical bootstrap behavior.
2. Generate runtime config from actual Railway variables instead of trusting build-time or templated config content.
3. Separate “service started” from “service publicly routable”. Internal logs and public ingress must be validated independently.
4. Separate “database exists” from “application schema initialized”. Those are different states and need different checks.
5. Prefer one canonical deployment folder per bundled app. Debugging gets much faster when Dockerfile, config, and startup script live together.
6. Normalize multiple env var families in wrappers when Railway, upstream images, and previous deploy attempts use different naming conventions.
7. Pin the serving port explicitly. If the app expects `8069`, configure both the app and Railway to use `8069`.

---

## Recommended Hardening Still Pending
These items are not blockers for boot, but they should be addressed before broader rollout:
- replace `admin_passwd = admin` with a strong production value sourced from Railway
- set `list_db = False`
- add an appropriate `dbfilter`
- confirm backup/restore handling for filestore content on attached volume

---

## Operator Checklist
Use this for the next Odoo-like Railway deployment:

1. Copy the deployment pattern under `docker/<app>/` and keep Dockerfile, config, and wrapper together.
2. Force startup through `ENTRYPOINT`, not `CMD` alone.
3. Normalize all likely DB env var names in the wrapper.
4. Generate a runtime config file and log which config file is actually used.
5. Add an application-level initialization check, not just a raw database existence check.
6. Pin the app port and the Railway `PORT` variable to the same value.
7. Validate both the internal host and the public Railway domain before declaring success.

---

## Related Files
- `docker/odoo/Dockerfile`
- `docker/odoo/start-odoo.sh`
- `docker/odoo/odoo.conf`
