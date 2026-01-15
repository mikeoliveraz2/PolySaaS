```markdown
# 4. API Integration Guide (Public OpenAPI 3.1)

## Base URL
```
https://api.polysaas.com/v1
```

## Authentication
- **Bearer Token** in `Authorization` header (JWT issued at login)
- JWT contains custom claim `tenant_schema` → automatically applied to every request
- No tenant_id or subdomain ever required

## Global Headers
| Header                | Required | Description                                    |
|-----------------------|----------|------------------------------------------------|
| Authorization         | Yes      | `Bearer <jwt>`                                 |
| Content-Type          | Yes      | `application/json`                             |
| Accept                | Optional | `application/json`                             |

## Rate Limiting (per tenant, enforced by plan)
| Plan       | Requests / minute | Webhook deliveries / minute |
|------------|-------------------|-----------------------------|
| Trial      | 300               | 100                         |
| Starter    | 1 000             | 500                         |
| Growth     | 5 000             | 2 000                       |
| Enterprise | Custom            | Custom                      |

## OpenAPI & Docs
- Specification: `https://api.polysaas.com/openapi.json`
- Interactive Swagger UI: `https://api.polysaas.com/docs`
- ReDoc: `https://api.polysaas.com/redoc`

## Core Endpoints (MVP – auto-generated from FastAPI)

| Method | Endpoint                          | Description                                    | Scope          |
|--------|-----------------------------------|------------------------------------------------|----------------|
| POST   | /auth/login                       | Google OAuth callback → returns JWT            | Public         |
| POST   | /auth/refresh                     | Refresh JWT                                    | Authenticated  |
| GET    | /feed                             | Real-time activity feed (paginated)            | Authenticated  |
| POST   | /posts                            | Create rich-text post                          | Authenticated  |
| GET    | /posts/{id}                       | Retrieve single post                           | Authenticated  |
| POST   | /chat/messages                    | Send chat message (WebSocket fallback)         | Authenticated  |
| GET    | /files                            | List Nextcloud files                           | Authenticated  |
| POST   | /files                            | Upload file → tenant’s Nextcloud               | Authenticated  |
| POST   | /atomic-services                  | Upload new tenant-private AtomicService        | Automation Admin |
| GET    | /atomic-services                  | List tenant’s active services                  | Authenticated  |
| POST   | /atomic-services/{name}/invoke    | Trigger custom service (sync/async)            | Authenticated  |
| POST   | /webhooks                         | Register webhook URL + events                  | Tenant Owner   |
| GET    | /webhooks                         | List active webhooks                           | Tenant Owner   |

## Webhook Events (delivered as POST JSON)
```json
{
  "event": "post.created",
  "tenant_schema": "tenant_acme",
  "timestamp": "2025-12-05T10:00:00Z",
  "data": { ... }
}
```
Supported MVP events:
- post.created / post.commented
- ticket.created (osTicket)
- invoice.created (Odoo)
- lead.created (SuiteCRM)
- file.uploaded (Nextcloud)
- atomic.service.completed

## Example: Create a Post
```bash
curl -X POST https://api.polysaas.com/v1/posts \
  -H "Authorization: Bearer eyJ..." \
  -H "Content-Type: application/json" \
  -d '{
    "content": "New project launch! @summarize this thread",
    "attachments": ["file_id_123"]
  }'
```

## SDKs (auto-generated on every deploy)
- TypeScript: `npm install @polysaas/sdk`
- Python: `pip install polysaas-sdk`
- Go, Ruby, etc. available via OpenAPI generator
