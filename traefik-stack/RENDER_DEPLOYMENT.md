# Render Deployment Guide - Traefik Path-Based Routing

## Overview

Deploy Traefik on Render to achieve single-domain path-based routing for all your services.

```
production.polysaas.online/
├── /                → PolySaaS Core (Render Web Service)
├── /mattermost      → Mattermost (Render Docker Service)
├── /odoo            → Odoo (Render Docker Service)
└── /nextcloud       → Nextcloud (Render Docker Service)
```

## Architecture

```
Internet
  ↓
production.polysaas.online (DNS)
  ↓
Render DNS
  ↓
Traefik (Render Docker Service) - Reverse Proxy
  ↓
Routes to Render service URLs:
  - polysaas-core.onrender.com
  - mattermost.onrender.com
  - odoo.onrender.com
  - nextcloud.onrender.com
```

## Prerequisites

- Render account with active workspace
- Domain `production.polysaas.online` already configured in Render
- Render CLI installed (optional, for easier deployment)

## Deployment Steps

### 1. Deploy Traefik Service

**Option A: Via Render Dashboard**

1. Go to Render Dashboard
2. Click "New +" → "Web Service"
3. Connect your GitHub repository
4. Select the `traefik-stack` directory
5. Configure:
   - **Name**: `traefik`
   - **Environment**: Docker
   - **Dockerfile Path**: `./traefik.Dockerfile`
   - **Branch**: `main`
6. Add Environment Variables:
   - `ACME_EMAIL`: `admin@polysaas.online`
   - `TRAEFIK_BASIC_AUTH`: Generate with `htpasswd -nb admin password`
7. Add Domain:
   - `production.polysaas.online`
8. Click "Deploy Web Service"

**Option B: Via Render Blueprint (render.yaml)**

```bash
render-blueprint apply render.yaml
```

### 2. Deploy Backend Services

Each service needs to be deployed as a separate Render service.

#### Mattermost

1. Create new Docker Service
2. Use Dockerfile from `blueprints/mattermost/Dockerfile`
3. Add Environment Variables:
   - `MM_SQLSETTINGS_DRIVERNAME`: `postgres`
   - `MM_SQLSETTINGS_DATASOURCE`: Use Render PostgreSQL connection string
   - `MM_SERVICESETTINGS_SITEURL`: `https://production.polysaas.online/mattermost`
4. Add Render PostgreSQL database
5. Deploy

#### Odoo

1. Create new Docker Service
2. Use Dockerfile from `blueprints/odoo/Dockerfile`
3. Add Environment Variables:
   - `HOST`: PostgreSQL host from Render
   - `USER`: PostgreSQL user
   - `PASSWORD`: PostgreSQL password
   - `PORT`: PostgreSQL port
4. Link to Render PostgreSQL
5. Deploy

#### Nextcloud

1. Create new Docker Service
2. Use Dockerfile from `blueprints/nextcloud/Dockerfile`
3. Add Environment Variables:
   - `POSTGRES_HOST`: PostgreSQL host
   - `POSTGRES_DB`: `nextcloud`
   - `POSTGRES_USER`: PostgreSQL user
   - `POSTGRES_PASSWORD`: PostgreSQL password
   - `NEXTCLOUD_TRUSTED_DOMAINS`: `production.polysaas.online`
   - `OVERWRITEPROTOCOL`: `https`
   - `OVERWRITECLIURL`: `https://production.polysaas.online/nextcloud`
4. Link to Render PostgreSQL
5. Deploy

### 3. Configure Traefik to Route to Services

After all services are deployed, get their Render URLs:

- PolySaaS Core: `https://polysaas-core.onrender.com`
- Mattermost: `https://mattermost.onrender.com`
- Odoo: `https://odoo.onrender.com`
- Nextcloud: `https://nextcloud.onrender.com`

Add these as environment variables to the Traefik service:

- `POLYSAAS_CORE_URL`: `https://polysaas-core.onrender.com`
- `MATTERMOST_URL`: `https://mattermost.onrender.com`
- `ODOO_URL`: `https://odoo.onrender.com`
- `NEXTCLOUD_URL`: `https://nextcloud.onrender.com`

Redeploy Traefik to pick up the new environment variables.

### 4. Update traefik.render.yml

Copy `traefik.render.yml` to `traefik.yml` in the traefik-stack directory:

```bash
cd traefik-stack
cp traefik.render.yml traefik.yml
```

Update the traefik.Dockerfile to copy the correct config:

```dockerfile
COPY traefik.yml /etc/traefik/traefik.yml
COPY dynamic.yml /etc/traefik/dynamic.yml
```

Redeploy Traefik.

### 5. Verify Routing

Test each path:

```bash
curl -I https://production.polysaas.online/
curl -I https://production.polysaas.online/mattermost
curl -I https://production.polysaas.online/odoo
curl -I https://production.polysaas.online/nextcloud
```

## Important Notes

### Render Service Discovery

Render services don't have Docker labels like local Docker Compose. Traefik must proxy to Render service URLs directly.

### WebSocket Support

The `dynamic.yml` file includes WebSocket support for Mattermost. Ensure the WebSocket path is configured correctly.

### SSL Certificates

Traefik will automatically provision Let's Encrypt certificates for `production.polysaas.online`.

### Database Configuration

All services can share the same Render PostgreSQL database by using different database names (e.g., `polysaas`, `mattermost`, `odoo`, `nextcloud`).

## Troubleshooting

### Service Not Accessible

1. Check Traefik logs in Render dashboard
2. Verify the service URL environment variable is set correctly
3. Test the backend service URL directly (e.g., `https://mattermost.onrender.com`)

### Certificate Not Issuing

1. Check Traefik logs for ACME errors
2. Verify port 80 is accessible
3. Ensure `ACME_EMAIL` is set to a valid email

### Strip Prefix Issues

If a service shows 404 or broken assets:

1. The service may not support running under a subpath
2. You may need to configure the app's internal URL
3. Check if `forceSlash: false` is set correctly

## Adding a New Service

1. Deploy the service on Render
2. Get the service URL
3. Add the URL as an environment variable to Traefik
4. Update `traefik.render.yml`:
   - Add strip prefix middleware
   - Add router rule
   - Add service with the URL
5. Copy to `traefik.yml` and redeploy Traefik

Example for a new service `/app`:

```yaml
http:
  middlewares:
    strip-app:
      stripprefix:
        prefixes:
          - /app
        forceSlash: false

  routers:
    app:
      rule: "Host(`production.polysaas.online`) && PathPrefix(`/app`)"
      service: app
      entryPoints:
        - websecure
      middlewares:
        - strip-app
      tls:
        certResolver: letsencrypt

  services:
    app:
      loadBalancer:
        servers:
          - url: ${APP_URL:-https://app.onrender.com}
```

## Cost Considerations

- Traefik: Starter plan ($7/month)
- Each service: Starter plan ($7/month each)
- PostgreSQL: Starter plan ($7/month)

Estimated monthly cost: ~$35-50 depending on number of services.

## Alternative: Render Native Routing

If you prefer not to use Traefik, you can use Render's native routing:

1. Deploy each service on Render
2. Each service gets its own subdomain (limited to 2 per workspace)
3. Use Render's URL forwarding for path-based routing (limited)

This approach is simpler but has the 2 custom domain limit you mentioned.
