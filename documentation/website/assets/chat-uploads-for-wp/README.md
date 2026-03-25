# Chat screenshots → WordPress Media Library

These PNGs were **saved from Cursor chat** (PolySaaS workspace) and copied here so you can **upload them in wp-admin → Media** and use them on the **Machine Learning** page (or elsewhere). They are **not** referenced by `machine-learning-page-content.html` until you add URLs after upload.

**Suggested filenames in WP:** use the descriptive alt text below when you upload (WordPress will still store under `uploads/YYYY/MM/`).

| File | Approx. subject (verify in preview) |
|------|-------------------------------------|
| `polysaas-chat-f43cf595-f88e-4f42-bea1-8d9b31bf2554.png` | Django admin dashboard (Jazzmin), Dose Tenant Management incl. ML prompts |
| `polysaas-chat-499f7f99-c140-464b-91e2-4ac741e65b7f.png` | Admin dashboard — sparse / layout whitespace |
| `polysaas-chat-b0c9b0d9-297f-434b-9c3e-0e030c594aec.png` | Jazzmin admin with theme / UI builder clutter |
| `polysaas-chat-6e8867dc-0741-4020-b5b6-bbbc8fe5a65a.png` | Tenant user home / dose landing (client view) |
| `polysaas-chat-3edf34ed-89c1-4365-a433-33221e3b8ee8.png` | Admin — ML dataset add/change form |
| `polysaas-chat-a39e8eb9-3f3d-4504-a944-2e6d74b879c9.png` | Admin — ML engine form |
| `polysaas-chat-e1694bf0-4d82-4db1-86b1-70432a867ab8.png` | Admin — ML taxonomy form |
| Other `polysaas-chat-*.png` | Additional chat captures — open file to identify |

**Workflow:** Upload to Media Library → copy **file URL** → paste into Custom HTML block or page content as needed. Repo sync script `scripts/wp_sync_ml_page.py` only pushes HTML; images stay in WordPress unless you host URLs elsewhere.
