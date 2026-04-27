# Traefik v3 Path-Based Routing Stack

Production-ready setup using Traefik v3 as reverse proxy for single-domain path-based routing.

## Folder Structure

```
PolySaaS/
├── traefik-stack/                    # Traefik v3 routing stack
│   ├── docker-compose.yml           # Main compose file
│   ├── traefik.yml                  # Traefik static configuration
│   ├── .env.example                 # Environment variables template
│   ├── .env                         # Your actual environment (create from .env.example)
│   ├── letsencrypt/                 # Let's Encrypt certificates (auto-created)
│   ├── services/                    # Individual service configurations (optional)
│   │   ├── mattermost.yml
│   │   ├── odoo.yml
│   │   └── nextcloud.yml
│   └── README.md                    # This file
├── blueprints/                      # Service blueprints
│   ├── mattermost/
│   ├── odoo/
│   ├── nextcloud/
│   └── ...
└── ... (rest of PolySaaS)
```

## Quick Start

### 1. Create the network

```bash
docker network create traefik-public
```

### 2. Configure environment

```bash
cd traefik-stack
cp .env.example .env
# Edit .env with your actual values
```

### 3. Generate Traefik dashboard password

```bash
# Install htpasswd tool if needed
# On Ubuntu/Debian: sudo apt-get install apache2-utils
# On macOS: brew install httpd

htpasswd -nb admin yourpassword
# Copy the output to TRAEFIK_BASIC_AUTH in .env
```

### 4. Start the stack

```bash
docker-compose up -d
```

### 5. Verify

- Traefik Dashboard: `https://traefik.production.polysaas.online`
- PolySaaS Core: `https://production.polysaas.online`
- Mattermost: `https://production.polysaas.online/mattermost`
- Odoo: `https://production.polysaas.online/odoo`
- Nextcloud: `https://production.polysaas.online/nextcloud`

## Adding a New Service

Use this template for any new service:

```yaml
your-service:
  image: your-image:tag
  container_name: your-service
  restart: unless-stopped
  networks:
    - traefik-public
  labels:
    # Enable Traefik
    - "traefik.enable=true"
    
    # Router configuration
    - "traefik.http.routers.your-service.rule=Host(`production.polysaas.online`) && PathPrefix(`/your-service`)"
    - "traefik.http.routers.your-service.tls=true"
    - "traefik.http.routers.your-service.tls.certresolver=letsencrypt"
    - "traefik.http.routers.your-service.entrypoints=websecure"
    
    # Service configuration
    - "traefik.http.services.your-service.loadbalancer.server.port=YOUR_PORT"
    
    # Strip prefix (so app sees root path)
    - "traefik.http.middlewares.your-service-stripprefix.stripprefix.prefixes=/your-service"
    - "traefik.http.middlewares.your-service-stripprefix.stripprefix.forceSlash=false"
    - "traefik.http.routers.your-service.middlewares=your-service-stripprefix"
    
    # Security headers (recommended)
    - "traefik.http.middlewares.your-service-headers.headers.customrequestheaders.X-Forwarded-Proto=https"
    - "traefik.http.routers.your-service.middlewares=your-service-stripprefix,your-service-headers"
```

## Example Labels by Service

### Mattermost (with WebSocket support)

```yaml
labels:
  - "traefik.enable=true"
  - "traefik.http.routers.mattermost.rule=Host(`production.polysaas.online`) && PathPrefix(`/mattermost`)"
  - "traefik.http.routers.mattermost.tls=true"
  - "traefik.http.routers.mattermost.tls.certresolver=letsencrypt"
  - "traefik.http.routers.mattermost.entrypoints=websecure"
  - "traefik.http.services.mattermost.loadbalancer.server.port=8065"
  - "traefik.http.middlewares.mattermost-stripprefix.stripprefix.prefixes=/mattermost"
  - "traefik.http.middlewares.mattermost-stripprefix.stripprefix.forceSlash=false"
  - "traefik.http.routers.mattermost.middlewares=mattermost-stripprefix"
  # WebSocket support
  - "traefik.http.routers.mattermost-websocket.rule=Host(`production.polysaas.online`) && PathPrefix(`/mattermost/api/v4/websocket`)"
  - "traefik.http.routers.mattermost-websocket.tls=true"
  - "traefik.http.routers.mattermost-websocket.tls.certresolver=letsencrypt"
  - "traefik.http.routers.mattermost-websocket.entrypoints=websecure"
  - "traefik.http.services.mattermost-websocket.loadbalancer.server.port=8065"
  - "traefik.http.routers.mattermost-websocket.middlewares=mattermost-stripprefix"
```

### Odoo

```yaml
labels:
  - "traefik.enable=true"
  - "traefik.http.routers.odoo.rule=Host(`production.polysaas.online`) && PathPrefix(`/odoo`)"
  - "traefik.http.routers.odoo.tls=true"
  - "traefik.http.routers.odoo.tls.certresolver=letsencrypt"
  - "traefik.http.routers.odoo.entrypoints=websecure"
  - "traefik.http.services.odoo.loadbalancer.server.port=8069"
  - "traefik.http.middlewares.odoo-stripprefix.stripprefix.prefixes=/odoo"
  - "traefik.http.middlewares.odoo-stripprefix.stripprefix.forceSlash=false"
  - "traefik.http.routers.odoo.middlewares=odoo-stripprefix"
  - "traefik.http.middlewares.odoo-headers.headers.customrequestheaders.X-Forwarded-Proto=https"
  - "traefik.http.middlewares.odoo-headers.headers.customrequestheaders.X-Forwarded-Host=production.polysaas.online"
  - "traefik.http.routers.odoo.middlewares=odoo-stripprefix,odoo-headers"
```

### Nextcloud

```yaml
labels:
  - "traefik.enable=true"
  - "traefik.http.routers.nextcloud.rule=Host(`production.polysaas.online`) && PathPrefix(`/nextcloud`)"
  - "traefik.http.routers.nextcloud.tls=true"
  - "traefik.http.routers.nextcloud.tls.certresolver=letsencrypt"
  - "traefik.http.routers.nextcloud.entrypoints=websecure"
  - "traefik.http.services.nextcloud.loadbalancer.server.port=80"
  - "traefik.http.middlewares.nextcloud-stripprefix.stripprefix.prefixes=/nextcloud"
  - "traefik.http.middlewares.nextcloud-stripprefix.stripprefix.forceSlash=false"
  - "traefik.http.routers.nextcloud.middlewares=nextcloud-stripprefix"
  - "traefik.http.middlewares.nextcloud-headers.headers.customrequestheaders.X-Forwarded-Proto=https"
  - "traefik.http.routers.nextcloud.middlewares=nextcloud-stripprefix,nextcloud-headers"
  - "traefik.http.middlewares.nextcloud-upload.headers.maxbodybytes=5368709120"
```

## WebSocket Support

For services that need WebSocket (like Mattermost), you need:

1. **Separate router for WebSocket paths**
2. **No strip prefix middleware on WebSocket router** (or careful configuration)
3. **Connection upgrade headers** (Traefik handles this automatically)

Example pattern:

```yaml
# Main router
- "traefik.http.routers.service.rule=Host(`domain.com`) && PathPrefix(`/service`)"
- "traefik.http.routers.service.middlewares=service-stripprefix"

# WebSocket router
- "traefik.http.routers.service-ws.rule=Host(`domain.com`) && PathPrefix(`/service/ws`)"
- "traefik.http.routers.service-ws.middlewares=service-stripprefix"
```

## Troubleshooting

### Certificates not issuing

Check Traefik logs:
```bash
docker-compose logs traefik
```

Common issues:
- Port 80 not reachable from internet
- DNS not propagated
- Email address invalid

### Service not accessible

1. Check if container is running:
```bash
docker-compose ps
```

2. Check container logs:
```bash
docker-compose logs your-service
```

3. Verify Traefik sees the service:
```bash
docker-compose exec traefik curl http://localhost:8080/api/http/routers
```

### Strip prefix issues

If the service shows 404 or broken assets:
- The service may not support running under a subpath
- You may need to configure the app's internal URL
- Check if `forceSlash=false` is set correctly

## Security Notes

- **Never expose Traefik dashboard publicly without authentication**
- **Use strong passwords in .env**
- **Keep .env out of version control**
- **Rotate Let's Encrypt email to a real address for production**
- **Consider DNS challenge for production (faster, no port 80 needed)**

## Production Checklist

- [ ] Change all passwords in .env
- [ ] Set ACME_EMAIL to real email
- [ ] Configure DNS challenge for Let's Encrypt (optional but recommended)
- [ ] Enable rate limiting in Traefik
- [ ] Set up monitoring/alerting
- [ ] Configure backups for volumes
- [ ] Test failover scenarios
- [ ] Review security headers
- [ ] Enable Traefik access logs for audit trail
