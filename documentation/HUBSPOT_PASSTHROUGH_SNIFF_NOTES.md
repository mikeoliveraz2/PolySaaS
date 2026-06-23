# HubSpot Passthrough — PolySniffer / Traffic Notes

**Upstream base:** `https://app.hubspot.com`  
**API host (bypass passthrough HTML shell):** `https://api.hubapi.com` (UCM uses OAuth tokens directly, not proxied)

## Observed path families (HubSpot SPA)

| Prefix | Role | Passthrough |
|--------|------|-------------|
| `/contacts/` | CRM contacts UI | Proxy + HTML rewrite |
| `/companies/` | Companies UI | Proxy + HTML rewrite |
| `/deals/` | Deals pipeline | Proxy + HTML rewrite |
| `/service/` | Service hub / tickets | Proxy + HTML rewrite |
| `/reports/` | Reporting | Proxy + HTML rewrite |
| `/settings/` | Portal settings | Proxy + HTML rewrite |
| `/marketing/` | Marketing tools | Proxy + HTML rewrite |
| `/login/` | Auth | Proxy (OAuth connect separate for API) |
| `/oauth/` | OAuth inside HubSpot | Do not intercept PolySaaS OAuth callback |
| `/api/` | XHR to HubSpot APIs | Bypass admin HTML wrap |
| `/hs/` | Static bundles | Bypass shell |
| `/hublytics/` | Analytics beacons | Bypass or forward raw |
| `/notifications/` | Notification polling | Bypass shell |

## Auth

- **Track A (passthrough):** Browser session cookies on `app.hubspot.com` after user signs in through proxied `/login/`.
- **Track B (UCM + API):** Per-tenant OAuth tokens in `TenantApp.extra_config` (`hs_access_token`, `hs_refresh_token`, `hs_portal_id`).
- PolySaaS OAuth callback: `/dose/hubspot/oauth/callback/` — must not be proxied.

## OAuth scopes (v1 portlets)

```
crm.objects.contacts.read
crm.objects.companies.read
crm.objects.deals.read
tickets
crm.objects.owners.read
```

## Handler bypass prefixes (implemented)

See `HubspotPassthroughHandler._BYPASS_PREFIXES` in `dose/passthrough/handlers/hubspot_handler.py`.

## Risks

- CSP / `X-Frame-Options` on HubSpot may block admin embed — test in display shell early.
- Full SSO into HubSpot web UI via API token alone is **not** supported; users connect OAuth for API and may still use proxied web login for Track A.
