# WordPress — Add Machine Learning to nav, footer, and home

**Site:** polysaas.online  
**Page URL (default permalink):** `https://polysaas.online/machine-learning/`  
**Stack (per redesign plan):** Kadence + block editor — exact clicks may vary slightly by Kadence version.

This repo does **not** contain the WordPress theme; you (or Shela) apply these steps in **wp-admin** on the live site.

---

## 1. Top navigation — Features dropdown

### PolySaaS Online (Site Editor — Patterns → Headers)

The main header is often a **pattern**, not **Appearance → Menus**.

1. **Appearance → Editor** → **Patterns** → **Headers**.
2. Open **“Centered site header (Copy)”** (or whichever header pattern your site uses).
3. Click the **Navigation** block in the preview.
4. Under **Features**, add a submenu item (or use **+** in the submenu):
   - **URL:** `https://polysaas.online/machine-learning/`
   - **Label:** `Machine Learning`
5. **Save** (and confirm if WordPress offers to save the pattern / template).

If the live site doesn’t update, check **Templates** / **Template parts** for which **Header** is assigned and whether it uses a different pattern.

### Classic menus (if your theme still uses them)

1. **wp-admin → Appearance → Menus**.
2. Open the menu assigned to **Primary** / **Main** / **Header**.
3. **Custom Links** → URL `https://polysaas.online/machine-learning/`, link text **Machine Learning** → add under **Features** (indented) → **Save Menu**.

**Kadence:** **Appearance → Customize** or **Kadence** in the sidebar may also expose header / navigation on some installs.

---

## 2. Footer — Features column (and full footer reference)

The global footer is usually a **Template part** or **Footer pattern**, same idea as the header — **not** always **Appearance → Menus**.

### Site Editor (block theme)

1. **Appearance → Editor**
2. **Template parts → Footer** (try any footer part your theme lists), **or** **Patterns** → category **Footers**, **or** **Templates** → open **Index** / **Page** and scroll to the bottom and click the footer region.
3. **List view** → expand **Group** / **Columns** until you find the column titled **Features** (heading + list of links).
4. Add **Machine Learning** as another link (duplicate an existing link block and edit URL + text if easiest):
   - **URL:** `https://polysaas.online/machine-learning/`
   - **Label:** `Machine Learning`
5. **Save**.

### Classic footer menu / Kadence

- **Appearance → Menus** — if the footer uses a **Footer** menu, add **Machine Learning** next to other Features links.
- **Appearance → Customize → Footer** or **Kadence → Footer Builder** — edit the Features column there.

### Features column — full list (keep in sync with repo footer)

Use these URLs/labels so footer matches `machine-learning-page-content.html`:

| Label | URL |
|--------|-----|
| Bundled Applications | `https://polysaas.online/bundled-applications/` |
| External Applications | `https://polysaas.online/external-applications/` |
| AI As Peers | `https://polysaas.online/ai-as-peers/` |
| Apps As Peers | `https://polysaas.online/apps-as-peers/` |
| PolySniffer | `https://polysaas.online/polysniffer/` |
| Dynamic Orchestration | `https://polysaas.online/dynamic-orchestration/` |
| Machine Learning | `https://polysaas.online/machine-learning/` |
| Atomic Services | `https://polysaas.online/atomic-services/` |
| OpenAPI | `https://polysaas.online/openapi-2/` |
| Portal | `https://polysaas.online/portal/` |
| Architecture | `https://polysaas.online/architecture/` |

**Applications** and **Gallery** columns on the live footer should match the same file if you want parity with the ML page pasted footer.

---

## 3. Home page — Machine Learning strip (icon + background | text + link)

This repo file is the source of truth; WordPress is updated by **paste** (no sync script for the home page).

**Paste HTML (recommended)**  
1. **Pages →** open your **front page** (the page set under **Settings → Reading** as “Your homepage”).  
2. Add a **Custom HTML** block (or **Kadence HTML**).  
3. Open **`documentation/website/home-ml-teaser-block.html`** in the repo, copy **everything including** the `<div class="ps-home-ml-teaser">` … `</div>` (you may omit the `<!-- ... -->` comment at the top if the editor strips it).  
4. **Update** / **Publish** the page.

**Layout:** **Left** — dark ML-style gradient + subtle grid + neural **icon**. **Right** — heading, short description, **Learn more →** `https://polysaas.online/machine-learning/`.

**Option B — Native blocks**  
Two columns: left = cover background + image of `assets/ml-icon.svg`; right = heading + paragraph + button link to `/machine-learning/`.

**Placement:** e.g. after the hero or in the **Features** area—not only in the footer.

---

## 4. Publish the ML page (if still draft)

**Pages → Machine Learning →** set status to **Publish** when you are ready for the link to work for anonymous visitors. Until then, only logged-in users may see it depending on settings.

---

## 5. Repo sync after HTML changes

If you edit **`machine-learning-page-content.html`** (including footer links), push to WordPress:

```powershell
python scripts\wp_sync_ml_page.py
```

Nav, footer template, and home page are **not** updated by that script — only the **Machine Learning** page body.

---

## Cross-reference

- Full ML page HTML: `documentation/website/machine-learning-page-content.html`  
- IA / homepage spec: `documentation/WEBSITE_REDESIGN_PLAN.md`  
- ML page workflow: `documentation/website/ML-DRAFT-PAGE-WP-ADMIN.md`
