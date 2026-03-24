# Machine Learning — WordPress draft page (not in menus, not meant for public)

**Goal:** A **Draft** page on **polysaas.online** you can open in **wp-admin → Pages** from any machine and flesh out with Shela—**without** adding it to the site menu or marketing navigation.

**Draft pages** are not shown to anonymous visitors (no direct public URL for normal users), are **not** in menus unless you add them, and should not appear in sitemaps while still **Draft** (verify with your SEO plugin).

---

## Option A — wp-admin only (~2 minutes)

1. Log in to **https://polysaas.online/wp-admin** (or your real admin URL).
2. **Pages → Add New**.
3. **Title:** `Machine Learning (internal draft)` (or your preferred title).
4. **Permalink / slug:** set to **`ml-platform-internal`** (edit slug next to title) so it’s easy to find and consistent with the script below.
5. Add a short stub in the body (or leave “Draft” placeholder).
6. **Document settings:** set status to **Draft** (not Publish).
7. **Save draft** — do **not** add this page to **Appearance → Menus** or Bricks header/footer templates.
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

3. Open **wp-admin → Pages → Drafts** and edit **Machine Learning (internal draft)**.

Script path: **`scripts/wp_create_ml_draft_page.py`**.  
If a page with slug **`ml-platform-internal`** already exists, the script exits with a message (no overwrite).

---

## Styled page body + standard footer (paste-ready)

**File:** **`documentation/website/machine-learning-page-content.html`**

1. Open that file in the repo (or pull latest `main`).
2. In wp-admin, edit your **Machine Learning** page.
3. In **Bricks**: add an **HTML** (or **Code**) element; paste **the entire file contents** (including the `<div class="ps-ml-wrap">` … `</div>` block).
4. **Duplicate footer:** If this page already uses the **theme’s global footer template**, remove the `<footer class="ps-ml-footer">` … `</footer>` block from the paste so the site footer does not appear twice. If the page is a blank template with no footer, keep the footer block—it matches the link structure from **polysaas.online** (Applications, Features, Gallery, legal links).

---

## Repo cross-reference

- Full technical draft (models, API paths): **`documentation/product/ML-PLATFORM-CONCEPT-AND-TABLES.md`**
- Marketing-ready layout + footer HTML: **`documentation/website/machine-learning-page-content.html`**
