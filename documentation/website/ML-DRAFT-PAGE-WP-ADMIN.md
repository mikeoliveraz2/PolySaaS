# Machine Learning — WordPress draft page (not in menus, not meant for public)

**Goal:** A **Draft** page on **polysaas.online** you can open in **wp-admin → Pages** from any machine and flesh out with Shela—**without** adding it to the site menu or marketing navigation.

**Draft pages** are not shown to anonymous visitors (no direct public URL for normal users), are **not** in menus unless you add them, and should not appear in sitemaps while still **Draft** (verify with your SEO plugin).

---

## Option A — wp-admin only (~2 minutes)

1. Log in to **https://polysaas.online/wp-admin** (or your real admin URL).
2. **Pages → Add New**.
3. **Title:** `Machine Learning` (or your preferred title).
4. **Permalink / slug:** set to **`machine-learning`** (edit slug next to title) so it matches **`machine-learning-page-content.html`** and the REST script below.
5. Add a short stub in the body (or leave “Draft” placeholder).
6. **Document settings:** set status to **Draft** (not Publish).
7. **Save draft** — do **not** add this page to **Appearance → Menus** or your theme’s global header/footer template (if you use one).
8. Optional: when you later **Publish**, add **noindex** in Yoast/RankMath and still keep it **out of menus** if you want it URL-only for stakeholders.

You can paste content from the repo doc `documentation/product/ML-PLATFORM-CONCEPT-AND-TABLES.md` as you refine it.

---

## Option B — Push HTML from the repo (create or update) — preferred

**Source of truth:** `documentation/website/machine-learning-page-content.html`. After `git pull`, run one command so you are not pasting into wp-admin every time.

Requires a **WordPress Application Password** (Users → Profile → Application Passwords).

1. Copy **`documentation/website/.env.wordpress.example`** to **repo root** as **`.env.wordpress`** (gitignored). Fill `WP_BASE_URL`, `WP_USER`, `WP_APP_PASSWORD`. Never commit that file.
2. From **repo root** (venv with `requests` installed):

```powershell
python scripts/wp_sync_ml_page.py
```

- **No page yet:** creates slug **`machine-learning`** (default status **draft**; override with `WP_PAGE_STATUS` in `.env.wordpress`).
- **Page exists:** **updates title + body** from the HTML file. Existing **status** is kept unless you set **`WP_FORCE_STATUS`** (e.g. `publish`).

Optional: same env vars in the shell instead of `.env.wordpress`. Legacy alias: **`scripts/wp_create_ml_draft_page.py`** runs the same sync.

**Renaming from an old slug:** If you had **`ml-platform-internal`**, edit the page in wp-admin → **Permalink → Edit** → set slug to **`machine-learning`**, then **Update** (WordPress usually redirects the old URL; add a redirect plugin rule if you had shared the old link).

---

## Icon + banner (Machine Learning page)

- **Text under icon:** Editable in **`machine-learning-page-content.html`** inside `<p class="ps-ml-icon-caption">` (primary line + optional `.ps-ml-icon-caption-sub`). Swap in Shela’s final wording anytime.
- **Icon:** Inline **SVG** (neural-node motif) next to the headline—no upload required. Same artwork as **`documentation/website/assets/ml-icon.svg`** if you want to add it to **Media** for menus or other pages.
- **Banner:** **Dark gradient hero** behind the title (CSS only). Optional: upload a wide JPG/PNG to Media, then on the outer **`<div class="ps-ml-wrap">`** add  
  `style="--ps-ml-banner-image: url(YOUR_FULL_MEDIA_URL);"`  
  so it layers under the gradients.

## Styled page body + standard footer (paste-ready)

**File:** **`documentation/website/machine-learning-page-content.html`**

1. Open that file in the repo (or pull latest `main`).
2. Prefer **Option B** (`wp_sync_ml_page.py`) so the live page tracks the repo file.
3. **Manual paste (fallback):** In **wp-admin → Pages →** your Machine Learning page, open the **block editor**, add a **Custom HTML** block (or **Code editor** / classic **Text** tab). Paste **the entire file contents** (including the `<div class="ps-ml-wrap">` … `</div>` block).
4. **Duplicate footer:** If this page already uses the **theme’s global footer template**, remove the `<footer class="ps-ml-footer">` … `</footer>` block from the paste so the site footer does not appear twice. If the page is a blank template with no footer, keep the footer block—it matches the link structure from **polysaas.online** (Applications, Features, Gallery, legal links).

---

## Standard pattern (inner / working pages — recreate anytime)

Use this for **Machine Learning** and any similar page: draft or published, in or out of menus.

1. **Source of truth in git:** one HTML file under **`documentation/website/`** per page (e.g. `machine-learning-page-content.html`). Scoped wrapper class (here: `ps-ml-wrap`) + embedded `<style>` keeps layout self-contained for a single **Custom HTML** block (or equivalent) in WordPress—**no Bricks or other page builder required.**
2. **Deploy to WordPress:** run **`python scripts/wp_sync_ml_page.py`** after pull (see Option B), or manually paste the latest file from `main` into a **Custom HTML** block.
3. **Footer:** Prefer the **theme’s global footer** when the page template includes it—then **delete** the `<footer class="ps-ml-footer">` block from the paste. If the template is blank (no footer), **keep** the pasted footer so the page still matches **polysaas.online** link columns and legal links.
4. **New pages:** copy `machine-learning-page-content.html`, rename (e.g. `feature-xyz-page-content.html`), replace the main content inside `.ps-ml-wrap`, **reuse the same footer block** unless the theme supplies the footer.

---

## Repo cross-reference

- Full technical draft (models, API paths): **`documentation/product/ML-PLATFORM-CONCEPT-AND-TABLES.md`**
- Marketing-ready layout + footer HTML: **`documentation/website/machine-learning-page-content.html`**
- **Site-wide:** Add ML to top nav / footer / home: **`documentation/website/WORDPRESS-ML-NAV-HOME.md`** and home teaser HTML **`documentation/website/home-ml-teaser-block.html`**
