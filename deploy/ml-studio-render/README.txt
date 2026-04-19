Machine Learning Studio (standalone Docker)
===========================================

Purpose
-------
Separate web service from PolySaaS-Core for a future **builder UI** and **heavy ML
dependencies** (PyTorch, scikit-learn, notebooks, pipelines). Django already has
the data model and admin grouping (`ml_studio` app proxies to dose `MLEngine`,
`MLDataset`, `MLTaxonomy`, prompts, etc.); this container will eventually host
experiences and compute that should not ship inside the main API image.

Phase 1
-------
- `GET /` — simple scaffold page (links to Core admin when `POLYSAAS_CORE_BASE_URL` is set)
- `GET /health` — Render health check

Wire-up (later)
---------------
- In Render / Blueprint, set **PolySaaS-Core** env **`MLSTUDIO_BASE_URL`** to this
  service's public URL (what you already reserved in `polysaas-bundled-apps`).
- **`MLSTUDIO_API_KEY`** on Core and a matching bearer/shared secret on this
  service (e.g. `MLSTUDIO_SERVICE_TOKEN`) when you add authenticated APIs between them.
- Prefer **tenant-safe APIs on Core** over giving this container raw Postgres
  credentials, unless you deliberately add a read replica or job DB.

Dependencies
------------
Edit `requirements.txt` incrementally. CPU-only PyTorch and large CUDA images
will need a bigger Render plan and possibly a custom base image.

Local
-----
  docker build -t ml-studio-render .
  docker run -e POLYSAAS_CORE_BASE_URL=http://host.docker.internal:8000 -p 8010:8000 ml-studio-render

Blueprint
---------
Service **PolySaaS-ML-Studio** in `render.yaml` — `deploy/ml-studio-render/Dockerfile`,
context `deploy/ml-studio-render`.
