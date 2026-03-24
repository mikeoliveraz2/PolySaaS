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

## Option B — Create the same draft via REST API (run once from laptop/CI)

Use when you prefer automation. Requires a **WordPress Application Password** (Users → Profile → Application Passwords).

1. In wp-admin, create an application password (e.g. label `polyml-draft-script`). Copy the generated password.
2. From the **PolySaaS repo root** (venv active), set env vars **only for this shell** (never commit real values):

```powershell
$env:WP_BASE_URL = "https://polysaas.online"
$env:WP_USER = "your-wp-username"
$env:WP_APP_PASSWORD = "xxxx xxxx xxxx xxxx xxxx xxxx"   # paste; script strips spaces
python scripts/wp_create_ml_draft_page.py
```

3. Open **wp-admin → Pages → Drafts** and edit **Machine Learning**.

Script path: **`scripts/wp_create_ml_draft_page.py`**.  
If a page with slug **`machine-learning`** already exists, the script exits with a message (no overwrite).

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
2. In wp-admin, edit your **Machine Learning** page.
3. In **wp-admin → Pages →** your Machine Learning page: open the **block editor**, add a **Custom HTML** block (or use **Code editor** / classic **Text** tab). Paste **the entire file contents** (including the `<div class="ps-ml-wrap">` … `</div>` block).
4. **Duplicate footer:** If this page already uses the **theme’s global footer template**, remove the `<footer class="ps-ml-footer">` … `</footer>` block from the paste so the site footer does not appear twice. If the page is a blank template with no footer, keep the footer block—it matches the link structure from **polysaas.online** (Applications, Features, Gallery, legal links).

---

## Standard pattern (inner / working pages — recreate anytime)

Use this for **Machine Learning** and any similar page: draft or published, in or out of menus.

1. **Source of truth in git:** one HTML file under **`documentation/website/`** per page (e.g. `machine-learning-page-content.html`). Scoped wrapper class (here: `ps-ml-wrap`) + embedded `<style>` keeps layout self-contained for a single **Custom HTML** block (or equivalent) in WordPress—**no Bricks or other page builder required.**
2. **Recreate in wp-admin:** replace the page body by pasting the latest file from `main` (pull first). Replace the whole HTML block content when you refresh from the repo.
3. **Footer:** Prefer the **theme’s global footer** when the page template includes it—then **delete** the `<footer class="ps-ml-footer">` block from the paste. If the template is blank (no footer), **keep** the pasted footer so the page still matches **polysaas.online** link columns and legal links.
4. **New pages:** copy `machine-learning-page-content.html`, rename (e.g. `feature-xyz-page-content.html`), replace the main content inside `.ps-ml-wrap`, **reuse the same footer block** unless the theme supplies the footer.

---

## Repo cross-reference

- Full technical draft (models, API paths): **`documentation/product/ML-PLATFORM-CONCEPT-AND-TABLES.md`**
- Marketing-ready layout + footer HTML: **`documentation/website/machine-learning-page-content.html`**
