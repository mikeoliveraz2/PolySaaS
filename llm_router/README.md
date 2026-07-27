# LLM router (Django app)

**Staff UI help:** open **Admin → user menu → Help** or **Platform help** in the top bar — `/help/` and `/help/llm-router/`.

## Platform context (OpenAPI, Swagger, logs, passthrough)

The built-in router is expected to ground answers in **your** PolySaaS surface first:

| Module | Purpose |
|--------|--------|
| `llm_router.integrations.platform_link_map(request)` | Resolves URLs for site + Dose Swagger, OpenAPI JSON, DRF lists (`passthroughendpoints`, `requestlogs`, `errorlogs`), admin changelists, and passthrough HTML pattern. |
| `llm_router.integrations.platform_context_for_system_prompt(request)` | Short bullet block to append to a **system** prompt so the model knows where APIs and logs live (it does **not** embed the full OpenAPI document). |

Typical usage when calling `complete_chat`:

```python
from llm_router.integrations import platform_context_for_system_prompt
from llm_router.router import route
from llm_router.providers import complete_chat

base = platform_context_for_system_prompt(request)
plan = route(prompt=user_text, user_tier="staff")
text = complete_chat(
    plan,
    messages=[{"role": "user", "content": user_text}],
    system_prompt=base + "\n\nYou are assisting with PolySaaS operations.",
)
```

Repo docs: `openclaw_router/README.md`.
