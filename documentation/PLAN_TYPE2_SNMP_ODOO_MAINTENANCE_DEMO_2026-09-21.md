# Plan: Type 2 Capture & Correlate + Type 1 Extract & Feed  
## Mock SNMP → WebhookMailbox → Odoo Maintenance

**Status:** Plan only (Shela + Michael — 2026-09-21)  
**Branch:** `main`  
**Audience:** investor / IT-ops buyer demo (PolySysMon narrative bridge)

---

## Why this is a killer

| Claim | Demo proof |
|--------|------------|
| **Type 2 — Capture & Correlate** | Every SNMP JSON lands in `WebhookMailbox` with TTL (raw telemetry history you can open in Admin) |
| **Type 1 — Extract & Feed** | Same pipe upserts `maintenance.equipment` and opens `maintenance.request` on anomaly |
| **PolySysMon future** | “Script today; PolySysMon drops thousands into this *same* webhook → mailbox → atomic pipe tomorrow” |

We already proved Type 2 browse on Inventory (`CapturePostResponse` → mailbox records table). This demo reuses that **mailbox history** story with an inbound webhook instead of passthrough SPA traffic.

---

## Architecture (fits locked orchestration model)

```
Generator script (Week 1 / Week 2)
    → POST /dose/webhook/snmp/<tenant_slug>/     (generic inbound)
    → enroll WebhookMailbox (processed, topic RES.snmp.…, payload = SNMP JSON)
    → Instruction match (source_app=snmp)
    → Atomic: SnmpToOdooMaintenance
         ├─ upsert maintenance.equipment (by device_mac)
         └─ if metrics.status=down OR temperature critical
              → create maintenance.request linked to equipment
    → DoseMessage / CallBackData optional (bar feedback)
```

**Hard rules (do not violate):**

1. Webhook **accepts + mailbox first**; heavy Odoo work in AtomicService (same pattern as HubSpot→Odoo contact).
2. Tenant from URL slug → `search_path` = tenant schema only for Instructions / mailbox / TenantApp. **No tenant rows in `public`.**
3. Odoo writes via existing `OdooRpcClient` + `TenantApp` credentials (schema `polysaas` / olient as seeded).
4. No iframe. No team logic. Passthrough Browse of Maintenance UI is optional for the “payoff” shot.

---

## Odoo targets

| Model | Role |
|--------|------|
| `maintenance.equipment` | Device inventory (name, serial/MAC, category “Network”) |
| `maintenance.request` | Ticket when status=down or temp critical |

**Prerequisite:** Maintenance app installed on shared Odoo (`polysaas-odoo2` / Hostinger Odoo). Verify once before seeding.

**Identity key:** `device_mac` → equipment `serial_no` (or `name` unique). Upsert, never duplicate on Week 2.

---

## Week-by-week narrative (film order)

### Week 1 — Baseline (clean)

- Push **one heartbeat per device** (start with **20 devices**, not 100×N — enough to look real, fast to film).
- Mailbox: 20 rows, `metrics.status=up`.
- Odoo Maintenance → Equipment: 20 assets appear.
- Voiceover: “Type 2 captured raw SNMP; Type 1 fed the CMDB.”

### Week 2 — Anomaly (~15% error)

- Push second batch; ~3 devices `status=down` / high temp.
- Mailbox: another 20 rows (history grows — correlate by MAC).
- Odoo: **Maintenance Requests** open for the 3 bad devices.
- Split screen: Admin mailbox (raw JSON) + Odoo tickets (business result).

### Optional Week 3 — Recover

- Push `status=up` for those MACs; show requests closable / equipment healthy again (nice-to-have, not required for v1 film).

---

## Payload contract (keep simple)

```json
{
  "event_id": "snmp-8492-abc",
  "timestamp": "2026-09-01T08:00:00Z",
  "device_mac": "00:1A:2B:3C:4D:5E",
  "device_name": "Core-Switch-01",
  "ip_address": "192.168.1.10",
  "metrics": {
    "status": "up",
    "cpu_utilization": 45,
    "temperature_c": 38
  }
}
```

**Anomaly rule (v1, data-driven via Instruction `parameters_json`):**

- `metrics.status == "down"` **or**
- `metrics.temperature_c >= 60` (configurable threshold)

---

## Build phases (proposal — wait for go)

### Phase A — Pipe + mailbox (Type 2 visible)

1. Webhook route already: `/dose/webhook/<source>/<tenant_slug>/` — use `source=snmp`.
2. Register atomic in generic inbound registry.
3. `SnmpMailboxEnroll` or enroll inside the atomic **before** Odoo RPC (same as capture enroll-first).
4. Seed Instruction in `polysaas` (and olient if needed).
5. Generator script under `scripts/snmp_week_feed.py` → Hostinger URL.
6. Verify Admin → Webhook mailboxes shows SNMP `records` / payload (theme-aware change form).

### Phase B — Odoo Maintenance feed (Type 1)

1. Confirm Maintenance module on Odoo; create category “Network / SNMP”.
2. Atomic upsert `maintenance.equipment`.
3. On anomaly → `maintenance.request` with name/description from SNMP.
4. Seed ~20 equipment via Week 1 run (idempotent).

### Phase C — Demo polish

1. Bookmark / Control Panel path to Odoo Maintenance Equipment + Requests.
2. One-pager talking points (PolySysMon bridge quote).
3. Optional: Mattermost notify on new request (reuse OdooInvoiceNotifier pattern — **later**).

### Defer (do not block this demo)

- Async **pull API** for mailbox subscribers (Sunday “#2”) — Admin browse is enough for the film.
- Real SNMP/MIB / PolySysMon agent.
- 100 heartbeats × many weeks (noise); scale volume only if the take needs it.

---

## Generator script (adapt Shela’s draft)

- `WEBHOOK_URL = https://app.prod-polysaas.cloud/dose/webhook/snmp/polysaas/`
- Week 1: `error_rate=0.0`, 20 devices.
- Week 2: uncomment, `error_rate=0.15`.
- Auth: if webhook requires token later, add header; v1 can match HubSpot-style CSRF-exempt inbound.

---

## Risks / speak-up

1. **Maintenance not installed** on shared Odoo → Phase B fails; check before promising film date.
2. **Generic inbound registry** is a small hardcoded map today — adding `SnmpToOdooMaintenance` is one line (same as HubSpot); longer term prefer full AtomicService registry discovery.
3. **Volume:** 20 devices × 2 weeks = 40 mailbox rows — clear story. Jumping to 100× without need slows the take.
4. **Correlate:** v1 correlates by MAC in Odoo + mailbox topic/filter; full “join UI” can be two browser windows (mailbox + Odoo).

---

## Success criteria (demo ready)

- [ ] Week 1 POST → mailbox rows + 20 equipment in Odoo  
- [ ] Week 2 POST → mailbox history + ≥1 maintenance.request for down/critical devices  
- [ ] Split-screen screenshot: mailbox payload + Odoo Maintenance UI  
- [ ] One sentence PolySysMon bridge delivered without new product code  

---

## Decision needed from Michael / Shela

**Go / no-go on Phase A+B implementation next?**  
If go: target tenant `polysaas` on Hostinger only first; olient second.  
If wait: this plan stays the source of truth until film date is set.
