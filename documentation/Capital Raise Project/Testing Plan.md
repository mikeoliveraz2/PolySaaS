# 5. Testing Plan – PolySaaS MVP

## Version
1.0 – Locked for 8-week MVP (multi-tenant, self-service, Celery, Atomic Services, public API)

## Testing Pyramid & Coverage Goals
| Layer                  | Tooling                            | Minimum Coverage | Notes                                  |
|------------------------|------------------------------------|------------------|----------------------------------------|
| Unit Tests             | pytest + Jest                      | 92 %             | Pure functions, utils, models          |
| Integration Tests      | pytest + Testcontainers + Supertest| 85 %             | API ↔ DB, Celery workers, Atomic Services |
| Contract Tests         | Pact + OpenAPI spec validation     | 100 %            | Public API never breaks                |
| End-to-End             | Cypress 13 + Playwright            | Critical paths   | Real browser + real GCP staging        |
| Chaos / Multi-Tenant   | Custom Gremlin + tenant-isolation  | Zero leakage     | Mandatory before every release         |

## Critical Test Scenarios (Must Pass 100 %)

| ID  | Scenario                                      | Tools / Method                         | Success Criteria                              |
|-----|-----------------------------------------------|----------------------------------------|-----------------------------------------------|
| T01 | Brand-new tenant signup → login → full access | Cypress + Stripe test mode             | < 60 s from signup to seeing personal feed    |
| T02 | Two tenants active simultaneously             | Parallel Testcontainers + 2 schemas    | Zero data crossover under load                |
| T03 | Upload custom AtomicService → invoke via API | pytest + isolated Cloud Run            | Executes only for owning tenant               |
| T04 | Celery workflow across 3 apps (ticket → OCR → Nextcloud) | Real RabbitMQ + time travel            | File appears in correct tenant folder         |
| T05 | 1 000 concurrent WebSocket connections       | k6 + custom WS script                  | ≤ 100 ms latency 95th percentile              |
| T06 | Schema search_path attack attempts            | SQL injection suite                    | Middleware blocks or returns 403              |
| T07 | Stripe webhook replay + failed payment flow   | Stripe CLI + webhook replay            | Tenant correctly suspended/restored           |
| T08 | Public OpenAPI contract never breaks          | Spectral + Dredd                       | CI fails on any breaking change               |
| T09 | Zero downtime deployment                     | Cloud Run blue/green + smoke tests     | No 5xx during deploy                          |

## CI/CD Gates (GitHub Actions – All Must Pass)

1. Unit + Integration suite
2. Contract & OpenAPI validation
3. Multi-tenant isolation chaos suite
4. Cypress smoke on staging
5. Load test (k6) – 2 000 RPS baseline
6. Security scan (Bandit + npm audit + Trivy)
7. Manual QA sign-off (for first prod deploy only)

## Staging vs Production Parity
- Staging = exact replica of prod (same Terraform, same quotas)
- Every PR deploys its own isolated preview environment (tenant_preview_xyz)

## Sign-off Criteria for Go-Live
- All T01–T09 above: 100 % green for 48 hours
- Pen-test report: zero high/critical findings
- 99.9 % uptime in final 7-day load/soak test
- CTO + Michael final written approval

Approved by: _________________________        Date: ____________
(CTO / Tech Lead)