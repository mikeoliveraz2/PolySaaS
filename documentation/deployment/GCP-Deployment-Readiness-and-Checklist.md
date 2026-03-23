# GCP Deployment Readiness Plan & Checklist

**Purpose:** Plan and track work for deploying PolySaaS to GCP. Shared by **Michael (you)**, **Laptop Cursor**, and **Desktop-CC**.

**Readiness gate:** Deploy to GCP **after** all bundled applications use OAuth2/SSO for users coming through PolySaaS (single sign-on: user logs in once at PolySaaS, then accesses all apps without logging in again).

**References:**
- [PolySaaS Architecture](../architecture/PolySaaS-Architecture.md)
- [GCP Deployment Plan](../GCP%20Deployment%20Plan.md)
- [Multi-App Deployment Architecture](../Doc-77-Doc-77-MULTI_APP_DEPLOYMENT_ARCHITECTURE.md)
- [GCP Deployment Q&A](../Doc-76-Doc-76-GCP_DEPLOYMENT_QA.md)
- Business plan: Google for Startups Cloud Program (apply post–production deploy)

**Railway (first deploy):** Primary hosting target is **Railway** with an internal container stack (Postgres, RabbitMQ, Elasticsearch, Grafana, **MonitorLogger**) before GCP. See **`documentation/deployment/railway/RAILWAY-DEPLOYMENT-PLAN.md`** and root **`docker-compose.railway-stack.yml`**.

---

## 1. Readiness Gate: OAuth2/SSO for All Bundled Apps

**Definition of done:** Every bundled app that a tenant uses is reachable via PolySaaS with **no second login**. Options:

- **Option A:** PolySaaS is the only OAuth2 IdP; users log in there; passthrough injects auth (e.g. headers/JWT) so each app trusts PolySaaS and auto-logs the user.
- **Option B:** Each app has its own OAuth2/OIDC config (e.g. Google) and accepts the same identity; PolySaaS still routes users into apps (e.g. passthrough or deep links) so UX is “login once, use all apps.”

**Bundled apps (from architecture):**

| App            | Port  | OAuth2/SSO status | Recommended approach (Shela) | Notes |
|----------------|-------|-------------------|-------------------------------|--------|
| Odoo           | 8069  | [~] Phase 2b      | **Native OAuth2/OIDC**        | auth_oauth module; DOT OIDC provider ready; provisioner enhancement in progress |
| Nextcloud      | 8888  | [~] Phase 2c      | **Native OIDC**              | user_oidc app; DOT OIDC provider ready; provisioner enhancement in progress |
| Mattermost     | 8065  | [~] Phase 2a      | **Native OAuth2/OIDC**        | Built-in OIDC; DOT OIDC provider ready; provisioner enhancement in progress |
| WordPress      | 8980  | [ ]               | **Passthrough (headers)**     | HTTP Header Auth / REMOTE_USER plugins; fastest with PolySaaS middleware |
| Liferay CE     | 8181  | [ ]               | **Native or passthrough**     | Strong OAuth2/OIDC; header auth also supported |
| Dolibarr       | 8889  | [ ]               | **Passthrough** (or native)   | Native OAuth modules exist but passthrough often easier |
| PolySysMon     | 9001  | [ ]               | **Header/session**            | Custom/demo; implement simplest (header → session) |
| Focalboard     | 8111  | [ ]               | **Via Mattermost**            | Inherits Mattermost auth; treat as part of Mattermost |
| AI As Peers    | 8990  | [ ]               | **TBD**                      | Placeholder; header or OIDC when implemented |

**Gate checklist (all must be done before “ready for GCP”):**

- [x] **POL-1** PolySaaS portal: users can sign in with OAuth2 (e.g. Google/GitHub via django-allauth). *Owner: Desktop* — allauth (Google/GitHub) + DOT OIDC provider live (commit `cadd450`, 2026-03-07).
- [ ] **POL-2** Passthrough auth: middleware injects identity (e.g. JWT or headers) into requests to bundled apps so they can auto-login. *Owner: __*
- [ ] **POL-3** Per-app SSO: each bundled app in the table above either (A) accepts PolySaaS-injected auth, or (B) is configured for OAuth2/OIDC with the same IdP. *Owner: Desktop (in progress)* — Phase 2a/2b/2c wiring Mattermost, Odoo, Nextcloud to DOT.
- [ ] **POL-4** Document which apps use “passthrough auth” vs “native OAuth2” and where config lives. *Owner: __*
- [ ] **POL-5** Manual test: one user logs in once at PolySaaS and opens each app without a second login. *Owner: Michael*

When **POL-1** through **POL-5** are done → **Ready for GCP deployment phase.**

**Recommended order to hit readiness gate (Shela):**  
1. **POL-1** — PolySaaS already on django-allauth + Google/GitHub.  
2. **R-2** — Build/test passthrough middleware on 1–2 easy apps (WordPress + one custom).  
3. **Native OIDC** — Configure Nextcloud, Mattermost, Odoo (and Liferay if desired) to use same upstream IdP as PolySaaS (e.g. Google) for Option B SSO.  
4. **R-4 / POL-4** — Document choice per app early.  
5. **POL-5 / R-5** — End-to-end manual test.

---

## 2. GCP Deployment Plan (High Level)

**Phases:**

1. **Pre-deploy (readiness)** — OAuth2/SSO for all bundled apps (Section 1).
2. **GCP prep** — Project, billing, APIs, secrets, DB, storage, optional CI/CD.
3. **Deploy Django (DOSE)** — Containerize, push to Artifact Registry, deploy to Cloud Run (or chosen compute).
4. **Deploy bundled apps** — Per-app decision: same project vs separate; Cloud Run vs GKE vs Compute; passthrough URLs and routing.
5. **Post-deploy** — Custom domain (if used), Google for Startups application, monitoring, backup.

---

## 3. Todo Checklist (You / Laptop Cursor / Desktop-CC)

Use **Owner** as: **Michael** (human), **Laptop** (Cursor on laptop), **Desktop** (desktop-cc). Tick `[x]` when done and note owner in *Owner*.

### 3.1 Readiness: OAuth2/SSO

| ID    | Task | Owner |
|-------|------|--------|
| R-1   | [ ] Confirm list of bundled apps that must have SSO (match table in Section 1 or adjust). | Michael |
| R-2   | [ ] Implement or extend passthrough auth middleware (inject JWT or headers for downstream apps). | Laptop or Desktop |
| R-3   | [~] For each app: either enable passthrough-based auto-login or configure native OAuth2/OIDC; document in POL-4. Desktop: DOT OIDC provider live (`cadd450`); Phase 2a/2b/2c provisioner enhancement in progress. | Desktop |
| R-4   | [ ] Add/update doc: “SSO and Passthrough Auth” (where config lives, which app uses which method). | Laptop or Desktop |
| R-5   | [ ] Michael: run through POL-5 (one user, one login, open each app). | Michael |

### 3.2 GCP Prep

| ID    | Task | Owner |
|-------|------|--------|
| G-1   | [ ] Create or select GCP project; enable billing; note project ID and region. | Michael |
| G-2   | [ ] Enable APIs: Cloud Run, Artifact Registry, Cloud SQL (if used), Secret Manager, Cloud Build (if used). | Michael or Desktop |
| G-3   | [ ] Create Cloud SQL (PostgreSQL) instance for DOSE + tenant schemas, or document reuse of existing. | Michael or Desktop |
| G-4   | [ ] Store Django `SECRET_KEY`, DB credentials, and other secrets in Secret Manager; document names. | Michael or Desktop |
| G-5   | [ ] Create GCS buckets (e.g. static, media, backups); document names and regions. | Michael or Desktop |
| G-6   | [ ] (Optional) Cloud Build trigger for main branch; document manual deploy steps if not using. | Laptop or Desktop |

### 3.3 Deploy Django (DOSE) to GCP

| ID    | Task | Owner |
|-------|------|--------|
| D-1   | [ ] Dockerfile for Django app (production-grade; use venv or multi-stage as needed). | Laptop or Desktop |
| D-2   | [ ] `cloudbuild.yaml` (or equivalent) to build image and push to Artifact Registry. | Laptop or Desktop |
| D-3   | [ ] Cloud Run service: deploy image; set env vars / Secret Manager refs; connect Cloud SQL if used. | Michael or Desktop |
| D-4   | [ ] Configure static/media: serve from GCS or via Cloud CDN; set `STATIC_URL` / `MEDIA_URL`. | Laptop or Desktop |
| D-5   | [ ] Run migrations on Cloud SQL (public + tenant schemas); document how (e.g. `migrate_all_schemas`). | Michael or Desktop |
| D-6   | [ ] Smoke test: open Cloud Run URL, log in, open admin and one passthrough app. | Michael |

### 3.4 Bundled Apps on GCP

| ID    | Task | Owner |
|-------|------|--------|
| B-1   | [ ] Decide topology: all apps in same project; one Cloud Run per app vs shared; subdomains vs path-based passthrough. | Michael |
| B-2   | [ ] Per bundled app: Dockerfile (if not using stock image), deploy to Cloud Run (or GKE/VM), set env/DB. | Laptop or Desktop |
| B-3   | [ ] Update PolySaaS `PassThroughEndpoint` (or config) with production URLs for each app. | Laptop or Desktop |
| B-4   | [ ] Verify SSO still works in production (passthrough auth or native OAuth2). | Michael or Desktop |

### 3.5 Post-Deploy

| ID    | Task | Owner |
|-------|------|--------|
| P-1   | [ ] (Optional) Map custom domain to Cloud Run; DNS and SSL. | Michael |
| P-2   | [ ] Apply for Google for Startups Cloud Program (AI Tier) per business plan; use production URL if required. | Michael |
| P-3   | [ ] Set up monitoring/logging (Cloud Logging, alerts on 5xx or downtime). | Michael or Desktop |
| P-4   | [ ] Document backup/restore for Cloud SQL and critical config. | Laptop or Desktop |
| P-5   | [ ] Update collaboration README or deployment doc with “Production URL” and “Last deploy” info. | Laptop or Desktop |

---

## 4. Who Does What (Guidance)

- **Michael:** Decisions (project, region, domain, which apps go first); credentials and billing; manual tests (POL-5, D-6, B-4); Google for Startups application; sign-off on readiness gate.
- **Laptop Cursor:** Tasks assigned “Laptop” or “Laptop or Desktop”; implement on laptop branch, commit, push; update this checklist when done.
- **Desktop-CC:** Tasks assigned “Desktop” or “Laptop or Desktop”; implement on desktop, commit, push; update this checklist when done.

**Rule 4:** Always pull before work, commit and push when done so the other machine has the latest.

---

## 5. Shela Feedback (March 2026)

Shela reviewed the plan and checklist; summary below (captured so we don’t lose it).

**Overall:** Plan and phased approach endorsed. Readiness gate (full SSO across bundled apps before GCP) makes sense as the main UX and security prerequisite. **Hybrid model** recommended: use **passthrough (headers/JWT)** where it’s simple and reliable (WordPress, Dolibarr, custom apps), and **native OIDC/OAuth** where support is mature (Nextcloud, Mattermost, Odoo, Liferay).

**Passthrough middleware (POL-2 / R-2):**  
In Django, middleware can: (1) rely on allauth/IdP for PolySaaS login; (2) on requests to app routes (e.g. `/app/<slug>/*`), inject headers such as `X-User-ID`, `X-User-Email`, `X-User-Name`, or preferably `Authorization: Bearer <short-lived-JWT>` signed by PolySaaS (downstream apps verify signature + claims); (3) use e.g. PyJWT to generate tokens. Works well behind Cloud Run (with IAP off or configured to trust these headers).

**Per-app feasibility (short):**  
- **Odoo** — Native OAuth2/OIDC preferred (auth_oauth; Google/custom OIDC).  
- **Nextcloud** — Native OIDC via `user_oidc` app (discovery + client ID/secret).  
- **Mattermost** — Native OAuth2/OIDC; no robust header-based auto-login.  
- **WordPress** — Passthrough via headers (e.g. HTTP Header Auth / REMOTE_USER) is often easiest.  
- **Liferay CE** — Native or header auth both viable.  
- **Dolibarr** — Passthrough often faster; native OAuth modules exist.  
- **Focalboard** — Tied to Mattermost; covered by Mattermost auth.  
- **PolySysMon / AI As Peers** — Custom; header check → session or full OIDC as needed.

**Optional deep dives Shela offered:**  
- Sample Django middleware for header/JWT injection  
- Nextcloud `user_oidc` config steps  
- Pros/cons of same-project vs multi-project topology (B-1)  
- Cloud Run + Cloud SQL multi-tenant schema tips  

---

## 6. Document History

| Date       | Change | By |
|------------|--------|-----|
| 2026-03-08 | Initial plan and checklist; readiness gate = OAuth2/SSO for all bundled apps. | Laptop Cursor |
| 2026-03-08 | Added Shela feedback: hybrid model, per-app recommended approach, prioritization order, middleware hint; new Section 5. | Laptop Cursor |
| 2026-03-08 | Marked POL-1 done (DOT OIDC provider live); updated R-3 and app table with Phase 2 progress; Desktop-CC picking up Phase 2a/2b/2c. | Desktop-CC |

---

*When a task is completed, mark it `[x]` and set the Owner column. Use this file as the single place to track deployment readiness and GCP todos for you and both agents.*
