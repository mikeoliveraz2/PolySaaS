# Render Blueprint — PolySaaS-Main (first-time connect)

**Goal:** Manage `render.yaml` from Git so pushes can update services, env groups, and new resources (e.g. Adminer) in one place.

**Rule (Render):** Each service / database / env group should be managed by **at most one** Blueprint. Do not attach the same resource to two Blueprints.

---

## Before you click “Deploy Blueprint”

1. **`render.yaml` on `main`** — Push the latest commit (service name for Django is **`PolySaaS-Core`** to match your existing web service).
2. **Regions** — Every service block has `region:`. It must match where you actually run that workload and (for internal Postgres hostnames) **the same region as `polysaas-postgres`**. If your live `PolySaaS-Core` is not in `singapore`, **edit `render.yaml` regions** to match before syncing, or Render may try to change region / create mismatched resources.
3. **Postgres** — If **`polysaas-postgres`** was created **outside** this Blueprint, it stays as-is. This file does **not** define a `databases:` block by default; Django uses `DATABASE_URL` / `DB_*` from **`polysaas-common`**. Do **not** add a second Postgres in YAML unless you intend a new database.

---

## Connect the Blueprint (Dashboard)

1. Open workspace **PolySaaS-Main** (or the workspace where your services live).
2. **New** → **Blueprint** (or **Blueprints** → create / connect — wording varies).
3. **Connect** repository **`mikeoliveraz2/PolySaaS`** (authorize GitHub if needed).
4. **Branch:** `main`  
5. **Blueprint path:** `render.yaml` (repo root — default).
6. **Name** the Blueprint (e.g. `PolySaaS-Main`).
7. Review the **plan**: Render lists creates/updates. When a service **`name` + `type` + key settings** match an existing resource, Render can **apply YAML to that resource** instead of creating a duplicate (see [Adding an existing resource](https://render.com/docs/infrastructure-as-code#managing-blueprint-resources)).
8. Fill **`sync: false`** secrets when prompted (`DJANGO_SECRET_KEY`, `DATABASE_URL`, Odoo `HOST` / `USER` / `PASSWORD`, `ADMINER_DEFAULT_SERVER`, etc.).
9. **Deploy Blueprint**.

After connect: optional **Auto Sync** off if you want manual **Sync** only ([Render docs](https://render.com/docs/infrastructure-as-code#disabling-automatic-sync)).

---

## If Render wants to create duplicates

- Use **Generate Blueprint** from selected existing services (Dashboard), compare names/plan/region with repo `render.yaml`, then align YAML and re-sync.
- Or rename the **existing** Render service to match `render.yaml` `name:` fields (only if safe for URLs and docs).

---

## Resources defined in `render.yaml` (current)

| Name | Type | Notes |
|------|------|--------|
| **PolySaaS-Core** | Web (Docker) | `Dockerfile.django`, `preDeployCommand`, env groups |
| **PolySaaS-Adminer** | Web (image) | Adminer; set **HTTP port 8080** if health checks fail |
| **PolySaaS-Celery-Worker** | Worker | Same image as Core |
| **PolySaaS-Odoo** | Web (Docker) | `deploy/odoo-render` + disk |

Env groups: **`polysaas-common`**, **`polysaas-bundled-apps`**, **`polysaas-odoo`**.

---

## References

- [Render Blueprints (IaC)](https://render.com/docs/infrastructure-as-code)  
- [Blueprint YAML reference](https://render.com/docs/blueprint-spec)
