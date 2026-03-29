# BINGO — 2026-03-24: WordPress Machine Learning page, home teaser, footer, REST sync scripts

**Status:** Complete and tested (live `polysaas.online` updated via scripts where noted).  
**Branch:** `main`

---

## Summary

Delivered repo-backed HTML and automation for the **Machine Learning** marketing page and **home** page: hero layout (icon banner + intro card), ML strip above the bottom CTA, inline footer fixes with **Machine Learning** in Features, and **stdlib-only** WordPress REST sync scripts using `.env.wordpress`.

---

## 1. Machine Learning inner page (`documentation/website/machine-learning-page-content.html`)

- **Hero:** Dark **banner band** (gradient, grid/decoration SVG, centered **ml-icon** at larger size) with short caption; **light intro card** below (slight overlap) for badge, `<h1>`, and lead paragraphs.
- **`body.dark-mode`:** Intro card and badge tuned for site dark-mode toggle.
- **Footer:** Unchanged standard `ps-ml-footer` block (parity with nav lists).
- **Published:** `python scripts/wp_sync_ml_page.py` → `https://polysaas.online/machine-learning/`

---

## 2. Home page ML teaser (`documentation/website/home-ml-teaser-block.html`)

- Two-column strip: icon + backdrop | copy + **Learn more** → `/machine-learning/`.
- **Live placement:** `scripts/wp_sync_home_ml_teaser.py` inserts above the **last** `ps-cta-banner` (bottom “Stop Managing Tools…” CTA), with fallback anchors documented in script.

---

## 3. Home inline footer (`scripts/wp_sync_home_inline_footer.py`)

- Patches the dark **in-page** footer HTML on the front page: logo `<p>` wrap, copyright stray `</p>`, closing `</p>` on Applications / Features / Gallery link blocks, **Machine Learning** link in Features (after Dynamic Orchestration).
- **Run:** `python scripts/wp_sync_home_inline_footer.py` (optional `--dry-run`).

---

## 4. REST sync scripts (Python stdlib only; no `requests`)

| Script | Role |
|--------|------|
| `scripts/wp_sync_ml_page.py` | Create/update **Machine Learning** page body from `machine-learning-page-content.html`. |
| `scripts/wp_sync_home_ml_teaser.py` | Insert/replace home ML teaser block; `--force` repositions from file. |
| `scripts/wp_sync_home_inline_footer.py` | Patch home inline footer Features + HTML fixes. |

**Credentials:** repo root `.env.wordpress` (gitignored); template `documentation/website/.env.wordpress.example`.

---

## 5. Docs and assets

- `documentation/website/WORDPRESS-ML-NAV-HOME.md` — Nav, footer template, home paste, script cross-references.
- `documentation/website/ML-DRAFT-PAGE-WP-ADMIN.md` — Draft/publish workflow.
- `documentation/website/assets/ml-icon.svg`, `ml-banner-pattern.svg` — Source assets (inline HTML stays canonical for paste).
- `documentation/README.md`, `documentation/WEBSITE_REDESIGN_PLAN.md`, `documentation/product/ML-PLATFORM-CONCEPT-AND-TABLES.md` — Index and product alignment updates in this commit where included.

---

## 6. Related script

- `scripts/wp_create_ml_draft_page.py` — Draft page creation helper (updated in this commit if present in diff).

---

## 7. Not covered by HTML/scripts (manual in wp-admin)

- **Header Features dropdown:** Site Editor → header pattern → add **Machine Learning** URL (see `WORDPRESS-ML-NAV-HOME.md`).
- **Theme global footer template part:** Still edited in Site Editor if separate from home inline footer.

---

## BINGO — certification

- [x] ML page hero + intro + dark-mode intro styles implemented in repo HTML and pushed to WordPress.
- [x] Home ML teaser and inline footer patched on live front page via scripts; Features list includes Machine Learning.
- [x] Sync scripts run on machine with `.env.wordpress` without requiring `pip install requests` for these tools.
- [x] This bingo document added; changes committed to `main` and **pushed to `origin/main`** when network allows.

**BINGO — this commit certifies the listed repository artifacts; live WordPress state matches as of the last successful script runs in this session.**
