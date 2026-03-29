# Laptop ↔ Desktop coordination

Notes between **Laptop Cursor** and **Desktop Claude** for PolySaaS (canonical repo: `mikeoliveraz2/PolySaaS`).

---

## Two-machine sync (storage & workflow)

**Storage (as of 2026-02):**

| Machine   | Drive / storage              | PolySaaS path   | Notes                                      |
|-----------|------------------------------|-----------------|--------------------------------------------|
| **Laptop**  | D: internal SSD (512 GB partition) | `D:\PolySaaS`   | Healthy; daily backups go to `D:\backups`  |
| **Desktop** | Imation 1TB HD               | (your path)     | Stable, in use >1 year; CrystalDiskInfo OK  |

**Sync workflow (Rule 4):**

- **Before starting work (either machine):** `git pull origin main`
- **When done or before switching machines:** commit changes, then `git push origin main`
- **Morning:** run `.\go.ps1` — it does pull, daily backup (skip if same day), then starts services.

Source of truth is **GitHub**; no external clone drive needed. Develop from either place as long as you pull first and push when done.

---

## How to use

- **Desktop:** Add or edit a note here (e.g. `notes-from-desktop.md`) when you leave work for the laptop.
- **Laptop:** Read the latest note, add a reply or `notes-from-laptop.md` when you hand back to desktop.

---

## Current status (laptop – 2026-02-28)

- Laptop: PolySaaS on **D:\PolySaaS** (internal SSD, healthy). Desktop machine **in shop for upgrade** — laptop-only for now; pull often; push when you commit.
- **Cross-app sync POC (Dolibarr → Odoo):** Public page [cross-app-sync](https://polysaas.online/cross-app-sync/). Repo copy of narrative → **`documentation/website/cross-app-sync-poc.md`**. Handoff for Desktop-CC → latest section in **`notes-from-laptop.md`**.
- **GCP deployment:** Shared plan and checklist → `documentation/deployment/GCP-Deployment-Readiness-and-Checklist.md`. Older notes → `notes-from-laptop.md` (this folder).

---

Input from Shela recarding ml engine selections...
Here's a clean, well-organized list of popular open-source ML platforms and frameworks suitable for the ML Engine selector in your Machine Learning Studio.
I’ve grouped them by primary strength so you (or CC) can easily decide which ones to include in the dropdown or multi-select.
Full MLOps / End-to-End Platforms (Great for "ML Engine" concept)

MLflow — Experiment tracking, model registry, deployment, and serving. Most popular open-source MLOps tool.
Kubeflow — Kubernetes-native full ML platform (pipelines, training, serving, notebooks).
ClearML — Experiment management, orchestration, model serving, and data versioning.
Polyaxon — Reproducible ML workflows, experiment tracking, and hyperparameter optimization.
ZenML — Extensible MLOps framework focused on production pipelines.
Metaflow — Netflix’s open-source framework for building and managing real-world ML workflows.

Model Serving / Inference Platforms

BentoML — Easy packaging and serving of models as production APIs (very developer-friendly).
Seldon Core — Kubernetes-native model deployment and monitoring.
KServe (formerly KFServing) — Standardized model serving on Kubernetes.
vLLM — High-performance serving for large language models.
TorchServe — Official PyTorch model serving.
Triton Inference Server (NVIDIA) — High-performance multi-framework inference server.

Training & Framework-Focused Platforms

TensorFlow + TensorFlow Extended (TFX) — End-to-end production ML on TensorFlow.
PyTorch + TorchServe — Flexible research-to-production framework.
Hugging Face Transformers + Inference Endpoints — Best for modern LLMs and NLP models.
Apache Spark MLlib — Scalable classical ML on big data.
H2O.ai (open-source version) — AutoML and scalable ML platform.

Specialized / Lightweight Options

Feast — Feature store for production ML (works great alongside others).
DVC (Data Version Control) — Git-like versioning for data and models.
Kedro — Pipeline framework for maintainable ML projects.

Recommended Shortlist for Your Selector (8–12 options)
If you want a concise dropdown, here’s a practical starter list:

MLflow
Kubeflow
BentoML
ClearML
Hugging Face (Transformers)
Seldon Core
KServe
PyTorch (TorchServe)
TensorFlow (TFX)
vLLM (for LLMs)
Polyaxon
H2O.ai

Would you like me to:

Format this as ready-to-paste HTML <select> options (with nice labels)?
Add short descriptions for each (e.g., “Best for experiment tracking” or “Optimized for LLMs”)?
Prioritize only self-hosted / on-prem friendly ones?
Include logos or icons suggestions?

Just tell me how you want it presented for the selector, and I’ll give you the exact code snippet.
Also, if you have any specific constraints (e.g., only Kubernetes-based, or focus on LLM serving), let me know and I’ll refine the list.1.9sFastcan we filter that lisk for those that have pyton libraries that can easily be integrated into the django venv. Not totally out of the quetion but something dockerized might work just fine.Here's a filtered and prioritized list of open-source ML platforms/tools that are easy to integrate via Python libraries into your Django virtual environment (or as separate Dockerized services).
I focused on tools with:

Strong, well-maintained Python SDK / client libraries (installable via pip)
Good support for remote API calls (so your Django app can talk to the ML engine without heavy local dependencies)
Reasonable Docker-friendly deployment (many run as separate services/containers)

Top Recommendations (Easiest Django Integration)





























































RankToolPython IntegrationBest ForDocker-Friendly?Notes for Django Use1MLflowExcellent (pip install mlflow, full client + tracking API)Experiment tracking, model registry, servingYes (official images)Best overall choice. Use MlflowClient to log/view models remotely.2ClearMLVery good (pip install clearml, rich SDK)Experiment management, data versioning, orchestrationYesGreat Python-first SDK. Easy to connect to a remote ClearML server.3ZenMLExcellent (pip install zenml, pipelines as Python code)Production ML pipelines & orchestrationYesVery clean Python API. Integrates well with many backends.4MetaflowExcellent (pip install metaflow)Workflow orchestration & scalingYesNetflix's tool — very Pythonic.5KedroExcellent (pip install kedro)Modular, maintainable data pipelinesYesGreat for structuring ML code.6BentoMLExcellent (pip install bentoml)Model serving as APIsYes (excellent Docker support)Perfect if you want to expose models as REST/gRPC endpoints.
Good Secondary Options

Hugging Face Transformers + Inference — pip install transformers + huggingface_hub. Extremely easy for LLM/NLP models. You can run inference locally or call Hugging Face Inference Endpoints.
DVC (pip install dvc) — Excellent for data + model versioning (pairs very well with MLflow).
Feast (pip install feast) — Feature store (if you need feature management).

Less Ideal for Direct Django venv (but still possible via Docker + API)

Kubeflow — Very powerful but Kubernetes-heavy. Better as a separate Docker/K8s service; interact via its Python SDK or REST API.
Seldon Core / KServe — Kubernetes-native serving. Use their Python clients or REST APIs from Django.
Polyaxon — Has Python SDK but more oriented toward full platform deployment.

Suggested Shortlist for Your ML Engine Selector
(These are the most practical ones you can start with)

MLflow
ClearML
ZenML
BentoML
Metaflow
Hugging Face (Transformers)
Kedro

Ready-to-use HTML Select Options
You can paste this directly into your template:
HTML<select id="ml-engine-select" class="regular-text" style="width:100%;">
    <option value="">— Select an ML Engine —</option>
    <option value="mlflow">MLflow (Experiment Tracking & Registry)</option>
    <option value="clearml">ClearML (Full Experiment & Data Management)</option>
    <option value="zenml">ZenML (Production Pipelines)</option>
    <option value="bentoml">BentoML (Model Serving)</option>
    <option value="metaflow">Metaflow (Workflow Orchestration)</option>
    <option value="huggingface">Hugging Face Transformers</option>
    <option value="kedro">Kedro (Modular Pipelines)</option>
</select>
Would you like me to expand this with short descriptions under each option, or add version numbers / installation commands for your docs?
Also, let me know if you want to focus more on LLM-focused tools or classical ML — I can refine the list further.

*Last updated: 2026-02-28 (laptop).*
