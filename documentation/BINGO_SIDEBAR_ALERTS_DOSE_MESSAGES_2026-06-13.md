# BINGO — Sidebar Alerts Badge (Unread Dose Messages)

**Date:** 2026-06-13  
**Declared by:** Michael  
**Commit:** `d8a02538`  
**Baseline:** BINGO `c9339777` — Subscribe behavior enhanced  
**Test URL:** Any admin page with sidebar (e.g. `http://localhost:8000/admin/`)

---

## What Was Achieved

The **Alerts** control in the admin sidebar shows a red badge with the count of unread **Dose Messages**. Clicking **Alerts** opens the unread list and clears the badge (messages marked read server-side; list remains visible).

### Certified behaviors

| Feature | Status |
|---------|--------|
| Badge shows unread count from `/dose/api/unread-dosemessages/` | ✓ |
| Badge hidden when count is 0 | ✓ |
| Poll refreshes count every 30 seconds | ✓ |
| Click Alerts → dropdown with unread messages | ✓ |
| Open Alerts → mark all read → badge clears | ✓ |
| Per-message click marks single message read | ✓ |
| **Mark all read** button clears list + badge | ✓ |
| API returns `{ count, messages }` (not stub `unread_count: 0`) | ✓ |
| GET / POST / PATCH on `UnreadDoseMessagesView` | ✓ |

---

## Root Cause Fixed

`UnreadDoseMessagesView` in `dose/views/main.py` was a stub returning `{ unread_count: 0 }`. Sidebar JS expected `{ count, messages: [...] }` plus POST/PATCH for mark-read.

---

## How It Works

```
Page load / 30s poll
    → GET /dose/api/unread-dosemessages/
    → updateBadgeCount + renderUnreadMessagesList

User clicks Alerts
    → GET (populate list) → POST mark all read → badge = 0

Orchestration / atomic services
    → DoseMessage.objects.create(...) in tenant schema
    → badge increments on next poll or page load
```

---

## Files in This BINGO

| File | Change |
|------|--------|
| `dose/views/main.py` | Real `UnreadDoseMessagesView` GET/POST/PATCH |
| `dose/templates/admin/includes/custom_sidebar.html` | Badge + dropdown JS refactor |
| `*.bak-alerts-badge` | Backups before edit |

---

## Verification Steps

1. Log in as tenant admin with unread Dose Messages (or trigger orchestration to create one)
2. Confirm red badge on **Alerts** tile with correct count
3. Click **Alerts** — dropdown lists messages; badge clears
4. DevTools → GET returns JSON `{ "count": N, "messages": [...] }`
5. **Mark all read** — empty state; badge stays 0

---

## Out of Scope (by design)

- Email/push notifications for new Dose Messages
- Jazzmin top-navbar bell (`static/admin/js/notifications.js`) — separate legacy path
