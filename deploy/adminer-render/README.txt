PolySaaS — Adminer on Render (PolySaaS-Main workspace)
======================================================

Goal: a small web UI to run SQL against Render managed Postgres (same workspace as
polysaas-postgres so internal hostname resolves).

Option A — Render Dashboard (no Blueprint)
------------------------------------------
1. Dashboard → your workspace (e.g. PolySaaS-Main) → New → Web Service.
2. Choose "Deploy an existing image from a registry" (or equivalent).
   Image: docker.io/library/adminer:4.8.1  (or adminer:4)
3. Name: e.g. PolySaaS-Adminer.
4. Region: MUST match the Postgres instance region (internal networking).
5. After deploy opens Settings:
   - Set the HTTP / instance port to 8080 (official Adminer image listens there).
   - Health check path: /  (optional).
6. Environment variables:
   - ADMINER_DEFAULT_SERVER = internal hostname ONLY from Postgres → Connections
     (e.g. dpg-d7g2ombeo5us73aln4ug-a). Do NOT paste the full postgresql:// URL here.
7. Log in to Adminer:
   - System: PostgreSQL
   - Server: can be pre-filled from ADMINER_DEFAULT_SERVER
   - Username / Password / Database: from Connections (e.g. polysaas_postgres_user, DB name).

Option B — Blueprint (render.yaml)
-----------------------------------
Repo includes service PolySaaS-Adminer (runtime: image). Sync the Blueprint; when
prompted, set ADMINER_DEFAULT_SERVER to the internal hostname. Confirm port 8080
in the service settings if the deploy health check fails.

Security
--------
Adminer is powerful and public unless you restrict it. Prefer workspace controls,
strong DB passwords, and consider Adminer login plugins (see Render deploy-adminer doc).
