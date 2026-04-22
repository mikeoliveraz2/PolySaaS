# OpenClaw router (Option 2) on Render

PolySaaS ships two layers:

1. **Option 1 — `llm_router` Django app** (in-process routing + `llm_router.providers.complete_chat`). Configure with `LLM_ROUTER_*` env vars (see `.env.example`).
2. **Option 2 — `openclaw_router/` FastAPI service** in this repo: OpenAI-compatible `POST /v1/chat/completions` for **internal** automation (ops, batch jobs, tedious tasks) without loading the full Django stack on each call.

## Deploy on Render

- Add a **private** or **internal** web service (same region as Core) using `openclaw_router/Dockerfile` with `dockerContext` set to `openclaw_router/`.
- Secrets: **`ANTHROPIC_API_KEY`** (required for the current skeleton; extend `main.py` for xAI/Gemini/OpenRouter as needed).
- **Do not** expose the service to the public internet without authentication.

## Calling from Django

Use server-side HTTP from a **Celery task** or **management command** to the service base URL (Render internal DNS or env `OPENCLAW_ROUTER_BASE_URL`). Request body matches OpenAI chat completions (see `openclaw_router/README.md`).

## Relation to Mattermost “#router” / “#openclaw”

Those triggers today map to **AI Peers** (`dose.services.ai_peer_service`). This Option 2 service is **separate**: you can later point internal jobs or a gateway at it without changing Peers until you explicitly wire them together.
