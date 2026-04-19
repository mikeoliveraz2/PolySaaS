PolySaaS Mattermost (Render Docker)
===================================

What this is
------------
A small **Alpine-based** image that installs the official **Mattermost Team Edition**
Linux bundle (same pattern as Render’s public example repo), plus an entrypoint that:

- Binds HTTP to **Render’s `PORT`** via `MM_SERVICESETTINGS_LISTENADDRESS`
- Normalizes Render Postgres **`postgresql://` → `postgres://`** for `MM_SQLSETTINGS_DATASOURCE`
- Stores config, uploads, and plugins under **`/var/lib/mattermost`** (mount a Render disk there)

Blueprint
---------
`render.yaml` defines:

- **Postgres** `polysaas-mattermost-db` (own instance; do not point Mattermost at the Django DB).
- **Web** `PolySaaS-Mattermost` using this Dockerfile.

Before first deploy
-------------------
1. **Service URL** — Render will give you `https://<service-name>.onrender.com`. Set
   **`MM_SERVICESETTINGS_SITEURL`** to that exact URL (https, no trailing slash).

2. **PolySaaS-Core** — In the bundled-apps env group / Core service, set:

   - **`MATTERMOST_URL`** = same public URL as above (Django `settings.MATTERMOST_URL`; used by provisioning).  
   - **`MATTERMOST_ADMIN_TOKEN`** = Personal Access Token from a Mattermost system admin
     (System Console → Integrations → Personal Access Tokens), for provisioning / API use.

3. **OIDC / Enterprise** — Local `docker-compose.mattermost.yml` uses Enterprise for some
   OpenID experiments. This image is **Team Edition**. If you need Enterprise-only settings,
   change the tarball URL in `Dockerfile` to the enterprise build for the same version.

4. **Provisioner URL** — `mattermost_tenant_provisioner` resolves the Mattermost origin from
   **`MATTERMOST_URL` env** then **`settings.MATTERMOST_URL`**, falling back to the legacy
   production host only if both are unset.

Health check
------------
Render uses **`/api/v4/system/ping`**.

Upgrades
--------
Bump **`ARG MM_VERSION`** in `Dockerfile` to a published release (see
https://github.com/mattermost/mattermost-server/releases), rebuild, and run Mattermost’s
upgrade guidance for that jump.

References
----------
- https://render.com/docs/deploy-mattermost  
- https://github.com/render-examples/mattermost  
