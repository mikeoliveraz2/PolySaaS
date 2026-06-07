# PolySaaS — Official Demo Scenario

> **Purpose:** Canonical walkthrough for all pre-release testing and live demonstrations.
> Every feature change must be verified against this script before any BINGO commit.

---

## The Story

A new subscriber discovers PolySaaS online, signs up in minutes, and immediately has a
fully provisioned multi-app workspace — Odoo for accounting, Nextcloud for files, and
Mattermost for team communication — all behind a single login, with AI assistants already
waiting in the team chat.

---

## Act I — Discovery & Subscription

**Starting point:** Fresh browser window (incognito recommended)

| Step | Action | Expected Result |
|------|--------|-----------------|
| 1 | Open **polysaas.online** | Homepage loads cleanly |
| 2 | Click the **Subscribe** link | Subscription form displayed |
| 3 | Fill in: name, email, company name, password | All fields accept input |
| 4 | Enter the **demo Stripe card number** | Card accepted, no errors |
| 5 | Select **Odoo**, **Nextcloud**, **Mattermost** | All three apps checked |
| 6 | Submit the form | Subscription confirmed |

**Scene ends with:** Redirect to the PolySaaS login page, username and password
pre-filled, and a banner reminding the user to save their credentials.

---

## Act II — First Login

| Step | Action | Expected Result |
|------|--------|-----------------|
| 7 | Click **Log In** (credentials pre-filled) | Login succeeds instantly |
| 8 | Observe landing page | Admin dashboard — no extra prompts |

**Scene ends with:** User is on the admin dashboard, provisioned as tenant admin.

---

## Act III — Admin Dashboard Tour

| Step | Action | Expected Result |
|------|--------|-----------------|
| 9 | Review the dashboard widgets | Tenant info, subscription status, app tiles all visible |
| 10 | Note the sidebar navigation | Odoo, Nextcloud, Mattermost links present |

---

## Act IV — Odoo: Invoices & Event Capture

| Step | Action | Expected Result |
|------|--------|-----------------|
| 11 | Click **Odoo** in the sidebar | Odoo loads — **no login prompt**, silent SSO |
| 12 | Browse available Odoo apps | Apps render correctly within the PolySaaS frame |
| 13 | Navigate to **Invoices** | Invoice list loads |
| 14 | Observe the orchestration bar | Green bar visible, showing an event was captured |

**Scene ends with:** The user has seen Odoo working seamlessly inside PolySaaS,
with the orchestration layer quietly recording activity.

---

## Act V — Orchestration: Callback Data

| Step | Action | Expected Result |
|------|--------|-----------------|
| 15 | Return to the **admin dashboard** | Dashboard loads |
| 16 | Click **Callback Data** in the sidebar | List of captured events displayed |
| 17 | Find the invoice-view event | Event visible with timestamp, source app, and payload |

---

## Act VI — Mattermost: AI-Powered Team Chat

| Step | Action | Expected Result |
|------|--------|-----------------|
| 18 | Click **Mattermost** in the sidebar | Mattermost loads — **no login prompt**, no spinner hang |
| 19 | Observe landing channel | Lands directly on **Town Square** |
| 20 | Observe the orchestration bar | Green bar visible |
| 21 | Observe the channel | **3 AI Bots** are already present and chatting |
| 22 | Type and send: `Hello @everyone` | All 3 bots respond in kind |
| 23 | Send: `@Grok how is your research going?` | Grok replies with a relevant update |
| 24 | Send: `@[Copilot/Cursor] show me mattermost_handler` | Bot posts the handler source inline |
| 25 | Review the posted code in-channel | Code is readable and reviewable |

**Scene ends with:** A live demonstration of AI agents collaborating inside the team
chat, aware of the codebase, responding naturally.

---

## Pass / Fail Checklist

Run this before every demo or BINGO commit.

### Subscription & Onboarding

- [ ] Subscribe form completes without error
- [ ] Login page pre-filled with credentials after subscribe
- [ ] Warning banner present ("save your credentials")
- [ ] Post-login lands on admin dashboard (not homepage)

### Admin Dashboard

- [ ] Tenant info widget visible
- [ ] Subscription status correct
- [ ] App tiles for Odoo, Nextcloud, Mattermost present
- [ ] Sidebar navigation shows all three app links

### Odoo

- [ ] Loads with no login prompt (silent SSO)
- [ ] Odoo apps render within PolySaaS frame
- [ ] Invoices page loads
- [ ] Green orchestration bar visible on Invoices

### Orchestration

- [ ] Callback Data page accessible from sidebar
- [ ] Invoice-view event present in Callback Data list
- [ ] Event shows correct timestamp, source, and payload

### Mattermost

- [ ] Loads with no login prompt (silent SSO)
- [ ] Lands directly on Town Square (no click required)
- [ ] No "Team Not Found" error
- [ ] No infinite spinner
- [ ] Green orchestration bar visible
- [ ] 3 AI Bots present in Town Square
- [ ] `Hello @everyone` — all bots respond
- [ ] Grok responds to research question
- [ ] Copilot/Cursor posts `mattermost_handler.py` on request

---

## Open Items — Blocking Full Pass

| Priority | Item | Status |
|----------|------|--------|
| High | Mattermost: requires click to load Town Square (nav guard v17 partial) | Tomorrow |
| High | Mattermost: green orchestration bar missing | Tomorrow |
| High | Odoo: database recovery required (free Render DB expired) | Tomorrow |
| Medium | Mattermost: "Something went wrong while loading the component" at bottom | Tomorrow |
| Low | Nextcloud SSO — provisioning works, passthrough not implemented | Backlog |
| Low | AI Bots provisioned in Town Square | Backlog |
| Low | Copilot/Cursor bot posting code on request | Backlog |
| Low | Callback Data wired to Odoo invoice view event | Verify |

## Session Notes — 2026-06-07

**Fixes applied this session:**

- `dose/models/tenant.py`: Fixed `is_new` detection for slug-based PK
  (`self.pk is None` never fired; replaced with `Tenant.objects.filter(pk=self.pk).exists()`)
- `dose/utils.py`: Reverted to schema-only creation (no migrations in `save()`);
  Phase 4 migration in `subscription_views.py` is the correct place
- `dose/subscription_views.py` Phase 4: Fixed migrate `cmd.handle()` to pass all
  required kwargs and close/reopen connection properly
- Manually rebuilt `polysaast125` and `polysaast126` schemas (pre-existing empty schemas)
- `documentation/DEMO_SCENARIO.md`: Created this file

**Verified working (t129 test):**
- Subscription flow completes end-to-end: Stripe → Tenant → Migrate → Provision
- Nextcloud: provisioned and ready
- Mattermost: provisioned and ready; correct team name (PolySaaS Test 129); correct user
- Town Square loads (requires one click on sidebar link)
- No "Team Not Found" error
- No infinite spinner or crash

**Not yet working:**
- Town Square does not load automatically (nav guard v17 rewrites URLs but SPA
  still initialises on a loading screen requiring one click)
- "Something went wrong while loading the component" banner at bottom of Mattermost
  (plugin load error — Boards or Calls plugin failing)
- Orchestration bar not visible in Mattermost embed

---

*Maintained by: Michael & Shela*
*Last updated: 2026-06-07*
