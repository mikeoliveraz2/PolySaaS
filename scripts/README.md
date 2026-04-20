# Scripts — Render env helper

## `render_env_sync.py`

Reduces manual copy-paste when filling **Render** environment groups and services to match `render.yaml`.

### What it does

1. Reads **`scripts/env-master.json`** (keys aligned with `polysaas-common`, `polysaas-bundled-apps`, `polysaas-odoo`, and each Blueprint service in `render.yaml`).
2. Optionally merges **`scripts/env-master.local.json`** if present (gitignored — put real secrets there locally).
3. Prints (or writes) **Markdown** with:
   - Per-**environment group** checklists + `.env`-style paste blocks.
   - Per-**service** effective variable list (groups merged + `overrides`) + paste block.

It does **not** call Render’s API; you still paste values in the dashboard. It keeps one editable JSON as the source of truth for *names* and *placeholders*.

### Usage

```bash
cd path/to/PolySaaS
python scripts/render_env_sync.py > render-env-checklist.md
```

Or write directly:

```bash
python scripts/render_env_sync.py -o render-env-checklist.md
```

Only certain services:

```bash
python scripts/render_env_sync.py --service PolySaaS-Core --service PolySaaS-Celery-Worker2
```

### Local secrets (recommended)

1. Copy the template keys you need into **`scripts/env-master.local.json`** (create this file; it is listed in `.gitignore`).
2. Use the same structure as the master file: top-level `envVarGroups` and/or `services` with nested objects — the script **deep-merges** local over master.
3. Run the script; generated markdown will show your local values (still avoid committing the generated file if it contains secrets).

### Maintenance

When `render.yaml` gains a new `sync: false` key or service, add the key under the right `envVarGroups` block and/or add a `services` entry so checklists stay accurate.

### Other scripts

See repo root and `documentation/` for Railway, WordPress, and other tooling; this README focuses on the Render env sync flow.
