# PolySaaS Website Redesign Plan

**Date:** March 11, 2026
**Updated:** March 11, 2026 (Shela review incorporated)
**Status:** Approved — Ready to Build
**Stakeholder Feedback:** Simplify, standardize, less colorful, more subdued, less cluttered
**Platform:** Gutenberg (WordPress Block Editor) + Kadence Theme + Kadence Blocks Plugin
**Build Site:** Azure (azure-nightingale-589250.hostingersite.com)
**Production Site:** polysaas.online (untouched until migration)

---

## 1. Technology Stack

| Component | Choice | Reason |
|-----------|--------|--------|
| Theme | Kadence (free block theme) | Clean, fast, full Gutenberg support, built-in Style Guide |
| Plugin | Kadence Blocks (free) | Enhanced columns, icons, tabs, advanced layout blocks |
| Editor | WordPress Block Editor (Gutenberg) | AI-programmable via REST API + user visual editing |
| Builder | None (no Bricks/Elementor) | Simpler, standardized, less clutter |
| Styling | theme.json + Kadence Style Guide + minimal custom CSS | Brand consistency enforced globally |
| Content | Migrated from current Bricks site | Copy text/structure, rebuild as blocks |
| Migration Tool | All-in-One WP Migration (when ready) | Azure → polysaas.online push |

## 2. Brand Standards (Global via theme.json + Kadence Style Guide)

### Colors (subdued professional palette)
- **Primary:** #001F3F (deep navy — darker, more executive per Shela)
- **Secondary:** #003399 (current brand navy — for accents)
- **Accent:** #03a9f4 (light blue — used very sparingly)
- **Text:** #1a1a1a (near-black)
- **Muted Text:** #6C757D (Bootstrap gray-600 — standard muted)
- **Background:** #ffffff (white)
- **Surface/Cards:** #f5f5f5 (light gray)
- **Border/Dividers:** #e0e0e0

### Typography
- **Headings:** Inter (clean sans-serif), weight 600-700
- **Body:** Inter, weight 400, 16px base
- **Fallback:** system-ui (performance-first)
- **No decorative fonts** — clean and professional throughout

### Spacing
- Consistent section padding: 60px top/bottom desktop, 40px mobile
- Card gaps: 24-32px
- Max content width: 1200px
- Increased block gaps via theme.json presets for generous whitespace

## 3. Navigation (Top Nav — All Pages)

```
Home | About | Applications ▼ | Features ▼ | Blog | Gallery | Pricing | Sign Up
```

- **Applications dropdown:** Odoo, Nextcloud, Mattermost, WordPress, Liferay, SuiteCRM
- **Features dropdown:** Architecture, Portal, Dynamic Orchestration, Atomic Services, PolySniffer, AI Agents, OpenAPI
- **Gallery:** Images, Videos (combined into one page or tabbed)
- Sticky header, clean white background, navy text
- Mobile: hamburger menu

## 4. Homepage Layout (Top to Bottom)

### Section 1: Hero
- **Static logo** (no animation — per stakeholder feedback)
- **Heading:** "The Problem We Solve"
- **Body text:** Current "Problem" paragraph (keep existing copy)
- **Heading:** "Our Approach to Solving This Problem"
- **Body text:** Current "Approach" paragraph (keep existing copy)
- Clean white background, centered text, generous whitespace

### Section 2: Target Audience
- **Heading:** "Who Benefits Most"
- **Subheading:** "Liferay Partners & Resellers, Django System Integrators, and Large Enterprises"
- **Three icon boxes** in a row:
  1. **Liferay Partners & Resellers** — icon + brief description of why
  2. **Django System Integrators** — icon + brief description
  3. **Large Enterprises** — icon + brief description
- Light gray background to visually separate from hero

### Section 3: Bundled Applications
- **Heading:** "Six Enterprise-Grade Applications, One Platform"
- **Grid of 6 icon boxes** (2 rows × 3 columns):
  1. Odoo (ERP/CRM) — icon + short tagline + link to /odoo/
  2. Nextcloud (Files/Collaboration) — icon + tagline + link to /nextcloud/
  3. Mattermost (Team Chat) — icon + tagline + link to /mattermost/
  4. WordPress (Content/Blog) — icon + tagline + link to /wordpress/
  5. Liferay (Enterprise Portal) — icon + tagline + link to /liferay/
  6. SuiteCRM (Customer Relations) — icon + tagline + link to /suitecrm/
- White background, subtle card shadows, consistent sizing

### Section 4: Value Proposition
- **Heading:** "Simple, Transparent Pricing"
- **Three pricing boxes** side by side:
  1. **Starter — 1 App** — $29/mo/user — key bullet points
  2. **Team — 3 Apps** — $49/mo/user — key bullet points (highlight as "Most Popular")
  3. **Unlimited — All Apps** — $99/mo/user — key bullet points
- Brief text under each explaining the value
- Light gray background

### Section 5: Features Showcase (Alternating Layout)
- **Heading:** "Platform Features"
- Alternating rows, each feature gets one row:

| Row | Image | Text Side | Feature |
|-----|-------|-----------|---------|
| 1 | Right | Left | Architecture (GCP, Kubernetes, Microservices) |
| 2 | Left | Right | Portal (Liferay — unified dashboard) |
| 3 | Right | Left | Dynamic Orchestration (no-code workflows) |
| 4 | Left | Right | Atomic Services (building blocks) |
| 5 | Right | Left | PolySniffer (traffic intelligence) |
| 6 | Left | Right | AI Agents (AI as Peers) |
| 7 | Right | Left | OpenAPI (extensibility) |

- Each row: image/screenshot on one side, heading + 2-3 sentences + "Learn More →" link on the other
- White background, clean lines

### Section 6: Latest Blog Posts (Optional)
- **Heading:** "Latest from the Blog"
- 3 most recent posts in a row (cards)
- "View All Posts →" link to /blog/
- If kept, this section is dynamic (I'll build it properly this time)

### Footer (Same as Current)
- Logo, address, contact info
- Application links, Feature links, Gallery links
- Copyright, Privacy Policy, Terms of Service, Disclaimer

## 5. Inner Pages Plan

| Page | Structure |
|------|-----------|
| **About** | Company story, team, mission — clean single column |
| **Application pages** (×6) | Hero image + app name, description, key features list, screenshots, CTA |
| **Feature pages** (×7) | Similar to app pages — description, diagram/screenshot, how it works |
| **Blog** | Archive with dynamic post grid (Gutenberg Query Loop — truly dynamic) |
| **Blog Posts** | Clean single-column reading layout, compact header |
| **Gallery** | Images tab + Videos tab (or separate sections) |
| **Pricing** | Mirrors Section 4 of homepage, expanded with FAQ |
| **Sign Up** | Links to Django subscribe flow |

## 6. Build Process

### Phase 1: Foundation (Session 1)
1. Install Kadence theme + Kadence Blocks plugin on Azure
2. Configure theme.json (colors, fonts, spacing)
3. Configure Kadence Style Guide (global palette/font preview)
4. Set up navigation menus
5. Build header template
6. Build footer template
7. Set static homepage

### Phase 2: Homepage (Session 1-2)
1. Build all 6 homepage sections as Gutenberg blocks
2. Review with Michael — adjust spacing, copy, colors
3. Iterate until approved

### Phase 3: Inner Pages (Session 2-3)
1. Migrate content from current Bricks pages
2. Rebuild each page using standardized block patterns
3. Application pages (6)
4. Feature pages (7)
5. About, Gallery, Pricing, Sign Up

### Phase 4: Blog (Session 3)
1. Set up Gutenberg Query Loop for blog archive (truly dynamic)
2. Style single post template
3. Test with existing posts

### Phase 5: Review & Migration (Session 4)
1. Full review on Azure
2. Stakeholder preview (share Azure URL)
3. Backup polysaas.online
4. Migrate via All-in-One WP Migration (or API replication)
5. DNS/cache verification
6. Deactivate Bricks Builder + Bricks child theme
7. Final verification on production

## 7. What I (AI) Build vs. What Michael Does

| Task | Who |
|------|-----|
| theme.json configuration | AI |
| Page content/blocks via REST API | AI |
| CSS overrides | AI |
| Navigation menu setup | AI |
| Blog Query Loop | AI |
| Content migration from Bricks | AI extracts text → builds new blocks |
| Image selection/upload | Michael |
| Visual fine-tuning in block editor | Michael |
| Final approval per page | Michael |
| Stakeholder review coordination | Michael + Shela |

## 8. Timeline Estimate

| Phase | Effort | Sessions |
|-------|--------|----------|
| Foundation + Homepage | 3-4 hours | 1-2 |
| Inner Pages (13 pages) | 4-6 hours | 2-3 |
| Blog + Polish | 1-2 hours | 1 |
| Review + Migration | 1-2 hours | 1 |
| **Total** | **~10-14 hours** | **~5-7 sessions** |

## 9. Migration Checklist (When Ready)

- [ ] All pages reviewed on Azure
- [ ] Stakeholder sign-off
- [ ] Install Kadence on polysaas.online
- [ ] Sync theme.json settings
- [ ] Migrate page content via API
- [ ] Update navigation menus
- [ ] Verify blog works dynamically
- [ ] Test all links
- [ ] Verify mobile responsiveness
- [ ] Remove/deactivate Bricks Builder
- [ ] Clear caches
- [ ] Final verification

---

**Next Step:** Michael approves this plan → we start Phase 1 on Azure.
