Legacy Odoo pack (deploy/odoo-railpack)

This folder is an older Odoo-on-containers layout kept for reference.
For current Render deployments, prefer deploy/odoo-render/ and the root render.yaml blueprint.

If you still build from this folder:

- Set the Render service **root** to this folder and ensure the service **builds from Dockerfile**
- **`PORT`** — HTTP port (Render injects `PORT`; map Odoo to match, e.g. 8069)

Logs (example — adjust service name in the Render dashboard):

    # Use Render dashboard → Logs, or the Render CLI against your workspace.
