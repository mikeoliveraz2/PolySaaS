# OpenClaw router service (Option 2)

Small **FastAPI** service with an **OpenAI-shaped** `POST /v1/chat/completions` endpoint. It classifies the prompt (same heuristics as the Django `llm_router` app), picks **Anthropic** `model` from `config.yaml`, and returns a minimal chat completion JSON.

This is intended as an **internal platform assistant** (private service, VPN, or authenticated mesh) — not a public anonymous API.

## Local run

```bash
cd openclaw_router
python -m venv .venv && .venv\Scripts\activate  # or source .venv/bin/activate
pip install -r requirements.txt
set ANTHROPIC_API_KEY=sk-ant-...   # Unix: export
uvicorn main:app --reload --port 8765
```

Health: `GET http://127.0.0.1:8765/healthz`

## Hosted deployment

1. Deploy as a private Docker service with build context `openclaw_router`.
2. Set **`ANTHROPIC_API_KEY`** (secret). Optional: **`OPENCLAW_ROUTER_CONFIG`** = path inside container if you mount a custom YAML; otherwise baked-in `config.yaml` is used.
3. Optional: **`OPENCLAW_ROUTER_TRUST_CLIENT_MODEL=1`** to honor the client `model` field (defeats cost routing — default off).
4. From Django or workers, call **`https://<private-host>/v1/chat/completions`** with a standard OpenAI JSON body.

## Django integration (PolySaaS-Core)

Use **`httpx`** or **`requests`** from Celery/management commands to POST to this service when you want **heavy or privileged** tasks off the Gunicorn workers. The in-app **`llm_router`** package (Option 1) remains the default for product features (orchestration, ML Studio, Peers).

## Files

| File | Role |
|------|------|
| `main.py` | FastAPI app, `/v1/chat/completions`, `/healthz` |
| `classifier.py` | Rule-based bucket selection |
| `config.yaml` | Thresholds + per-bucket provider/model |
| `Dockerfile` | Production image |
