# BINGO — 2026-03-05: Schedule a Demo Page + Dual CTA Blocks

## Session Summary

Desktop-CC session: Created a Schedule a Demo page with a branded date/time form, plus two reusable CTA blocks (Schedule a Demo and Join Waitlist) for flexible placement across the site.

## Completed Work

### 1. Schedule a Demo Page

- **URL:** `https://azure-nightingale-589250.hostingersite.com/schedule-demo/`
- **WordPress Page ID:** 1720
- **Status:** Published and live

**Form Fields:**
| Field | Type | Required |
|-------|------|----------|
| First Name | Text | Yes |
| Last Name | Text | Yes |
| Email Address | Email | Yes |
| Company | Text | No |
| Preferred Date | Date picker (weekdays, starts tomorrow) | Yes |
| Preferred Time (CST) | Dropdown (9:00 AM – 5:00 PM, 30-min slots) | Yes |
| What are you most interested in? | Textarea | No |

**Features:**
- Brand-consistent design (#003399 primary, #03a9f4 hover, #f5f5f5 form background)
- Date picker auto-skips weekends, minimum date = tomorrow
- Time dropdown: 17 slots from 9:00 AM to 5:00 PM CST
- Success message with checkmark on submit
- Fallback to mailto: if API endpoint unavailable
- Matches site gradient background via existing CSS

### 2. Reusable CTA Blocks

Two reusable blocks created for inserting on any page via Bricks editor:

| Block | WordPress ID | Heading | Button Text | Links To |
|-------|-------------|---------|-------------|----------|
| CTA — Schedule a Demo | 1721 | "See PolySaaS in Action" | "Schedule a Demo" | `/schedule-demo/` |
| CTA — Join Waitlist | 1722 | "Stop Managing Tools. Start Orchestrating Them." | "Get Early Access – No Risk" | `/sign-up/` |

Both blocks use brand blue buttons with hover-to-accent transition.

### 3. Existing Site Context

- Sign Up page (`/sign-up/`) uses WPForms (form ID 758) with Name, Email, Comment fields
- The new demo form uses custom HTML (no WPForms dependency) for the date/time picker capability
- Both CTA styles are now available as drag-and-drop blocks

## Form Submission Flow

```
User fills form → Click "Request Demo"
  → Try POST to /wp-json/contact/v1/demo-request (future API endpoint)
  → If API unavailable: fallback to mailto:mikeoliveraz@gmail.com
  → Show success message: "Demo Request Received!"
```

**Note:** The REST API endpoint (`/wp-json/contact/v1/demo-request`) is not yet implemented. Currently falls back to mailto. A server-side handler can be added later to store submissions and send email notifications.

## Files Created

| File | Purpose |
|------|---------|
| `wp_create_demo_form.py` | Script that created the page and reusable blocks via WordPress REST API |
| `wp_get_cta.py` | Audit script to examine existing CTA structure and WPForms setup |

## For Laptop-CC / Manual Steps

1. **Choose which pages get which CTA** — Michael will decide page-by-page
2. **Insert CTA blocks** — In Bricks editor, use the reusable blocks (IDs 1721 / 1722) or link directly to `/schedule-demo/`
3. **Optional: implement email handler** — Create a WordPress plugin or functions.php snippet to register `/wp-json/contact/v1/demo-request` endpoint that sends email on form submission

## Status

- **TESTED** — Page live, form renders correctly, date/time pickers functional
- **PENDING** — Server-side email handler (currently mailto fallback)
- **PENDING** — Michael to assign which pages get which CTA

---
*Session: Desktop-CC, 2026-03-05*
