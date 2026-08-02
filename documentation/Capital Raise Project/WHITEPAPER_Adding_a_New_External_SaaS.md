# ADDING A NEW EXTERNAL SaaS

### How PolySniffer, Atomic Services, and the Connector Pipeline Turn Any SaaS Application Into a First-Class PolySaaS Integration

*A Technical & Strategic White Paper for Enterprise Architects, Investors, and Prospective Partners*

polysaas.online

---

## Executive Summary

Every integration platform eventually faces the same question from a prospect: *"We use [Tool X] — can you connect to it?"* Most platforms answer with a connector catalog and a shrug if the tool isn't already on the list. PolySaaS answers differently: **we don't wait for a vendor's official connector — we build one.**

This paper describes the repeatable, four-stage pipeline PolySaaS uses to bring a new external SaaS application under orchestration: **Discover → Capture → Normalize → Orchestrate**. It is the same pipeline already running today for Odoo, Mattermost, Nextcloud, Dolibarr, and HubSpot — proven infrastructure, not a roadmap slide. The purpose of this paper is to explain why each new connector gets cheaper to add than the last, why customer data stays isolated no matter how many external systems are connected, and what a customer or partner should realistically expect when they ask us to add a tool we don't support yet.

---

## 1. The Problem: Every New SaaS Is (Usually) a Custom Project

Traditional integration work treats every new SaaS application as a bespoke engineering effort: read the vendor's API docs, hand-write an auth flow, hand-write request/response handling, hand-write the business logic that reacts to what the API returns, and hope the vendor doesn't change their API before you ship. Multiply that by the number of tools a customer actually runs — often 15–25 for a modestly sized business — and integration becomes a standing engineering tax that never goes away.

PolySaaS treats a new SaaS connection as a **pipeline execution**, not a custom project. The pipeline has four fixed stages; only the first stage ("Discover") is genuinely bespoke per application, and even that stage is tool-assisted rather than hand-built from scratch.

---

## 2. The Connector Pipeline

### Stage 1 — Discover (PolySniffer)

Before anything can be connected, it has to be understood. **PolySniffer** captures a live session against the target SaaS application — its API calls, its authentication handshake, its page structure where relevant — and surfaces the concrete request/response patterns an engineer needs to wire up a connector, instead of requiring someone to reverse-engineer the application by hand from documentation (or lack of it).

### Stage 2 — Capture (the connector itself)

Depending on what the target SaaS actually offers, capture takes one of three forms — see Section 3 for the full comparison:

- A **passthrough handler** (for applications PolySaaS hosts or proxies)
- An **OAuth/API connector** (for applications the customer already owns and simply authorizes)
- **Inbound webhooks**, with scheduled polling only as a last resort when a vendor offers neither a proxy-friendly UI nor webhooks

### Stage 3 — Normalize (the Mapping layer)

This is the stage that keeps the pipeline from becoming N bespoke integrations. Every connector's raw output — regardless of whether it came from a scraped HTML page, a webhook payload, or a polled REST response — passes through a declarative **Mapping**: a source-to-normalized field transformation (already a first-class, reusable, chainable model in the platform, not a one-off script per connector). The result is a canonical event: `deal_created`, `invoice_paid`, `ticket_opened` — the same shape regardless of whether it came from HubSpot, Salesforce, or a tool we add next quarter.

### Stage 4 — Orchestrate (Atomic Services + Instructions)

Canonical events are matched against tenant-configured **Instructions** — simple rules ("when X happens, do Y") — which trigger **Atomic Services**: reusable, composable actions (notify a channel, sync a record, write to an analytics warehouse, call a custom workflow). Because Stage 3 already normalized the event, the same Instruction can react identically no matter which of a customer's tools actually produced the trigger.

```
Discover  →  Capture  →  Normalize  →  Orchestrate
(PolySniffer) (connector)  (Mapping)   (Instructions +
                                        Atomic Services)
```

---

## 3. Three Connection Models — Choosing the Right Capture Method

Not every SaaS application should be connected the same way. PolySaaS selects the lightest-weight, most durable option available for each target application:

| Model | When It's Used | How It Works | Durability |
|---|---|---|---|
| **Bundled / Proxied** | Applications PolySaaS hosts on the customer's behalf (Odoo, Mattermost, Nextcloud, Dolibarr) | PolySaaS provisions the instance and proxies its UI, injecting authentication automatically | High — PolySaaS controls both ends |
| **Pure API / BYO** *(preferred for customer-owned tools)* | Applications the customer already runs and simply authorizes (HubSpot today; the target model for most new connectors) | OAuth2 authorization code flow; official REST API calls; no UI scraping at all | Highest — no dependency on a vendor's frontend, only their published API contract |
| **Hybrid** | Applications with a usable API for some actions but no webhook support, or with UI elements not exposed via API | API/OAuth where possible, scheduled diff-polling only for the gaps | Medium — the polling piece is monitored and scoped tightly (see Section 4) |

**OAuth/API-first is policy, not preference.** Screen-scraping a UI PolySaaS doesn't control means every unannounced frontend change from the vendor is a silent breakage risk. An OAuth connection against a documented, versioned API doesn't have that failure mode — which is why HubSpot, PolySaaS's first customer-owned-SaaS connector, was built this way from day one, and why it's the template for everything added going forward.

---

## 4. Event Capture Without Polling — "Events Are Events"

Whatever produced a canonical event — a scraped proxy request, a vendor webhook, or (only when nothing better exists) a scheduled poller detecting a real state change — the orchestration layer downstream never knows or cares which one it was. That separation is deliberate:

- **Webhooks are preferred** wherever a vendor supports them — near real-time, no rate-limit burn, no engineering debt.
- **Polling is a last resort**, and even then it is scoped to do exactly one thing: detect that something genuinely changed and manufacture the same event envelope a webhook would have produced. It never fires on a blind interval, and it never bypasses normalization.
- **Every event carries a time-to-live.** If an event isn't actually acted on within a tunable window — for example, after a consumer outage produces a backlog — it expires and is logged rather than triggering a now-stale action days later. This keeps orchestration honest: it only ever acts on things that are still true.

---

## 5. Security, Isolation & Data Governance

- **Schema-per-tenant isolation.** Every customer's data — including every connector's captured events — lives in that customer's own database schema. There is no shared table of "everyone's Salesforce data" anywhere in the platform.
- **OAuth over stored credentials.** Wherever a target SaaS supports it, PolySaaS stores a scoped, revocable OAuth token — never the customer's actual login credentials — and the customer can revoke access from their own SaaS account at any time, no PolySaaS involvement required.
- **Tenant identity travels with the event**, not just the connection. Every event published to the orchestration layer carries its owning tenant; matching and execution are always scoped to that tenant's schema, the same discipline enforced everywhere else in the platform.

---

## 6. Why Each New Connector Gets Cheaper

The first SaaS PolySaaS connects to is the expensive one — it establishes the pattern. Every connector after that reuses the same Discover/Capture/Normalize/Orchestrate pipeline, the same Mapping model, and, increasingly, Mappings and Instructions from prior connectors in the same category (every CRM eventually needs a `deal_created` event; every accounting tool eventually needs `invoice_paid`). This is a deliberate compounding-library strategy: the cost of the *next* CRM connector should always be lower than the cost of the last one, because the normalization target it maps into already exists.

---

## 7. What To Expect — Realistic Timelines

Honesty here matters more than optimism. Approximate ranges, assuming PolySniffer has already captured a representative session against the target application:

| Connector Type | Typical Lead Time |
|---|---|
| Vendor offers OAuth2 + documented REST API + webhooks | Fast — days, not weeks |
| Vendor offers OAuth2 + REST API, no webhooks (polling required) | Slightly longer — the diff-poller needs scoping and testing |
| Vendor offers no usable API — UI-only, requires a scraped passthrough handler | Longest — proportional to how complex and how frequently-changing the target UI is |

New connectors are prioritized by customer demand and by how many customers would benefit from the same connector, not first-come-first-served — a connector requested by five customers is built before one requested by one, all else equal.

---

## 8. Conclusion

PolySaaS does not compete on having the largest static connector catalog on the day a prospect asks. It competes on the ability to say *"tell us what you use, and we'll add it"* — and mean it, because the pipeline that makes that true (PolySniffer discovery, a declarative normalization layer, and a tenant-isolated orchestration engine) is running in production today, not sketched on a roadmap. Every new SaaS added makes the next one faster to add, which is the compounding advantage this platform is built to capture.
