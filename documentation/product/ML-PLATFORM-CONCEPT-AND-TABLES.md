# ML / AI platform concept & table reference (internal draft)

**Status:** Internal working document only. **Do not** link this from the public marketing site or the main Features list until the concept and claims are fully agreed and accurate.

**WordPress working copy:** To edit ML messaging in **wp-admin on polysaas.online** (draft page, not in menus), see **`documentation/website/ML-DRAFT-PAGE-WP-ADMIN.md`** and **`scripts/wp_sync_ml_page.py`** (pushes `machine-learning-page-content.html` from the repo).

**Audience:** Michael, Shela, builders. Expand this page gradually; when ready, derive customer-facing copy (website, deck) from here—not the other way around.

---

## 1. Product concept (original direction)

PolySaaS / DOSE was designed so a **tenant admin (or power user)** can define and operate their own ML-oriented workflows **inside the platform**, without being forced into a separate notebook product or a vendor-locked “AI add-on.”

**Illustrative arc (vision—not a guarantee of current UI):**

1. **Model the world** — e.g. PolySysMon builds a logical model of devices and relationships across a large organization.
2. **Scan & capture** — discovery and telemetry feed **structured records** into stores suited for search and analytics (e.g. **Elasticsearch**, **BigQuery**, or tenant-chosen sinks).
3. **Train / serve** — frameworks such as **TensorFlow** (or others) consume those records for training or inference, driven by configuration and orchestration defined in PolySaaS.
4. **Prompts & agents** — custom prompts (and chains) can be aimed at **tenant models** and/or **external LLMs** only where the tenant explicitly chooses—preserving ownership, compliance, and cost control.

The **potential use cases are open-ended** (predictive ops, recommendations, custom agents, etc.). This document stays grounded in **what exists in the repo today**; marketing language should lag until those bullets are validated.

---

## 2. Django models: `ML*` tables (implemented)

All three extend **`TenantAwareModel`** (`tenant` FK → `dose.Tenant`). Default database table names follow Django’s rule: **`dose_<lowercase_model_name>`** → `dose_mlengine`, `dose_mltaxonomy`, `dose_mldataset`.

### 2.1 `MLEngine` (`dose.models.ml_engine`)

| Field | Type | Notes |
|-------|------|--------|
| `id` | BigAutoField | PK |
| `engineName` | CharField(100) | Required |
| `engineEndPoint` | CharField(100) | Required — intended as hook to a service or runner |
| `matchingEventKey` | CharField(100) | Optional — **correlation key for dynamic orchestration / events** (detail TBD) |
| `description` | CharField(255) | Default `'Description'` |
| `parameters_json` | JSONField | Optional engine-level parameters |
| `pub_date` | DateTimeField | Default `now` |
| `tenant` | FK Tenant | From `TenantAwareModel` |

**Code:** `dose/models/ml_engine.py`

### 2.2 `MLTaxonomy` (`dose.models.ml_taxonomy`)

| Field | Type | Notes |
|-------|------|--------|
| `id` | BigAutoField | PK |
| `matchingEventKey` | CharField(100) | Optional — same integration idea as engine/dataset |
| `description` | CharField(255) | Default `'Description'` |
| `content_json` | JSONField | Optional taxonomy / labels / hierarchy payload |
| `pub_date` | DateTimeField | Default `now` |
| `tenant` | FK Tenant | |

**Code:** `dose/models/ml_taxonomy.py`

### 2.3 `MLDataset` (`dose.models.ml_dataset`)

| Field | Type | Notes |
|-------|------|--------|
| `id` | BigAutoField | PK |
| `matchingEventKey` | CharField(100) | Optional |
| `isTraining` | BooleanField | Default `True` — distinguishes training vs inference/other splits (usage TBD) |
| `description` | CharField(255) | Default `'Description'` |
| `content_json` | JSONField | Optional dataset metadata, pointers, or serialized refs |
| `pub_date` | DateTimeField | Default `now` |
| `tenant` | FK Tenant | |

**Code:** `dose/models/ml_dataset.py`

### 2.4 `matchingEventKey` (cross-cutting)

Repeated on all three models: intended as a **stable string key** so orchestration, MQ, atomic services, or scanners can **route events** to the right engine / taxonomy / dataset row without hard-coding IDs. **Exact contract** (who emits, who consumes, naming convention) — *to be documented by Michael*.

---

## 3. Related: parameters (not `ML*` prefix, same design family)

**`parameters.Parameter`** (`parameters.models`): `matchingKey`, `sequence`, `param_kwargs_json`, `param1`…`param10`, description, audit fields. Useful for **ordered, keyed configuration** that may align with ML pipelines or orchestration steps.

**Table:** `parameters_parameter` (typical Django default).

*Relationship to `MLEngine.parameters_json` / workflows — to be described when usage is finalized.*

---

## 4. Where this appears in the product today

| Surface | Location |
|---------|----------|
| **Django admin** | `MLEngine`, `MLTaxonomy`, `MLDataset` registered (see `dose/admin.py`) |
| **DRF API** (under site prefix `dose/`) | `GET/POST/... /dose/api/mlengines/`, `/dose/api/mltaxonomies/`, `/dose/api/mldatasets/` (router in `dose/urls.py`) |
| **Serializers** | `dose/serializers.py` — `MLEngineSerializer`, `MLTaxonomySerializer`, `MLDatasetSerializer` |
| **Swagger** | Staff-gated schema may list these resources when authenticated |

**Security note:** ViewSets use default DRF behavior; **tightening permissions / tenant scoping** for production is a separate hardening task—do not assume “safe by default” for multi-tenant exposure.

---

## 5. Adjacent orchestration (not `ML*` tables)

**`Instruction`**, **`Task`**, **`CallBackData`**, **`AtomicService`**, MQ configs, passthrough endpoints, etc. participate in **dynamic orchestration** and may eventually be documented as the **execution graph** around ML rows above. *Short pointer only for now—expand in a sibling doc if useful.*

---

## 6. Gaps to fill in (for Michael / Shela)

Use this list to evolve the doc before any public page:

- [ ] Canonical **meaning** of `matchingEventKey` (examples: PolySysMon event types, DOSE instruction IDs, etc.).
- [ ] **JSON shapes** intended for `content_json` / `parameters_json` (even one example JSON per model).
- [ ] **Elasticsearch / BigQuery / TensorFlow** — which are target integrations today vs roadmap; what code paths write/read them.
- [ ] **End-user vs admin** workflows: who creates rows, and through which UI (admin only vs future in-app wizard).
- [ ] **Privacy / data residency** claims for marketing (must match actual deployment modes: self-hosted, Railway, etc.).
- [ ] **Screenshots or diagrams** when a stable UI exists.

---

## 7. Shela’s marketing themes (hold until section 6 is done)

When ready to go public, themes like **“own the full loop,”** **framework-agnostic**, **optional external LLMs**, and **orchestrated training/inference** should be checked line-by-line against this file and the live product. Until then, keep that copy in email/docs only—not on the main marketing site.

---

## 8. Document history

| Date | Change |
|------|--------|
| 2026-02-28 | Initial internal draft: concept + table inventory from codebase. |
| 2026-02-28 | Pointer to WordPress draft page workflow (`documentation/website/ML-DRAFT-PAGE-WP-ADMIN.md`). |
