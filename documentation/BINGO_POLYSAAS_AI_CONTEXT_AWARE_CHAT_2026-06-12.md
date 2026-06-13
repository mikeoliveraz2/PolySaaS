# BINGO — PolySaaS AI Context-Aware Chat (Geronimo on Every Page)

**Date:** 2026-06-12  
**Declared by:** Michael  
**Commit:** `fd9febb8`  
**Baseline:** BINGO `7073725c` — Mattermost dual-team provisioning  
**Test tenant:** PolySaaS Test 154 (`polysaast154` / schema `polysaasst154`)  
**Test URL:** `http://localhost:8000/admin/dose/instruction/add/` (any admin page with inline dock)

---

## What Was Achieved

**Geronimo** — a context-aware PolySaaS AI co-pilot — is embedded on **every admin page** via the inline chat dock. Each page load starts fresh with a Geronimo intro tailored to the current screen; multi-turn chat works on the same page only. The backend receives rich page context (URL, tenant, passthrough service, orchestration bar, Mattermost team/channel) and answers with Gemini by default.

### Certified behaviors

| Feature | Status |
|---------|--------|
| Inline chat dock on all admin pages (`base_site.html` include) | ✓ |
| Geronimo intro on each new page (no cross-page history) | ✓ |
| Clear button resets to intro only | ✓ |
| Page context collector sends JSON on each message | ✓ |
| Context-aware answers (e.g. "Add Instruction" required fields) | ✓ |
| Admin chat API returns JSON (`/admin/llm-router/chat-api/`) | ✓ |
| Tenant chat API for passthrough embed (`/tenant/llm-router/chat-api/`) | ✓ |
| Routes registered **before** `admin.site.urls` (no HTML 404 on API) | ✓ |
| Default provider Gemini `gemini-2.5-flash` via settings | ✓ |
| Full-page chat at `/admin/polysaas-ai/` shares same backend | ✓ |
| Layout (inline/float) and Standard/ML Studio mode persist in sessionStorage | ✓ |

---

## How It Works

```
Admin page load (any /admin/… screen)
    → base_site.html includes polysaas_ai_chat_dock.html
    → initChatUi(): empty history, purge legacy sessionStorage, show Geronimo intro

User sends message
    → polysaas_ai_page_context.js collects URL, tenant, breadcrumbs, passthrough, MM context
    → POST /admin/llm-router/chat-api/ (or /tenant/… on /pt/admin/ embed)
    → admin_chat.py → build_staff_admin_system_prompt(page_context) → Gemini

Navigate to another admin page
    → fresh intro; prior Q&A not restored
```

---

## Files in This BINGO

| File | Change |
|------|--------|
| `dose/static/admin/js/polysaas_ai_page_context.js` | Browser page-context collector |
| `dose/templates/admin/includes/polysaas_ai_chat_dock.html` | Geronimo dock UI, clear-on-page, tenant API routing |
| `dose/templates/admin/polysaas_ai_chat.html` | Full-page chat, same Geronimo + clear-on-page |
| `llm_router/page_context.py` | Format JSON/URL context for system prompt |
| `llm_router/admin_prompts.py` | Geronimo persona + page context in system prompt |
| `llm_router/admin_chat.py` | Chat page + admin/tenant JSON APIs, Gemini default route |
| `mysite/urls.py` | Real chat routes before `admin.site.urls` |
| `mysite/settings.py` | `LLM_ROUTER_ADMIN_CHAT_PROVIDER` / `_MODEL` defaults |
| `*.bak-geronimo`, `*.bak-clear-page`, `mysite/urls.py.bak-geronimo-chat` | Backups before edit |

**Already wired (prior BINGO, unchanged in this commit):** `dose/templates/admin/base_site.html` includes the dock on every page except `/admin/polysaas-ai/`.

---

## Verification Steps

1. `.\runall` (or restart Django)
2. Log in as test tenant admin (e.g. `polysaast154`)
3. Open **Instructions → Add instruction** — dock shows Geronimo intro mentioning "Instructions"
4. Ask *"what is required on this page?"* — reply references Add Instruction / required fields
5. Navigate to another admin page — prior Q&A gone; new intro for that page
6. Click **Clear** — intro only returns
7. DevTools → Network → chat API POST returns JSON with `provider: gemini`, `model: gemini-2.5-flash`
8. Optional: `/admin/polysaas-ai/` full page — same behavior

---

## Out of Scope (by design)

- Mattermost `@gemini` bot (separate path)
- Legacy `contextual_ai.html` popup (`/dose/doseai/`)
- Cross-page chat history persistence
- In-chat tool-calling / slash commands (Phase 3 roadmap)
