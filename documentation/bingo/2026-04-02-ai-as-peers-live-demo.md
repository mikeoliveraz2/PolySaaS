# Bingo: AI as Peers — Live Demo with Three AI Models

**Date:** April 2, 2026
**Status:** BINGO — Complete and Demonstrated
**Participants:** MO (Mike Oliver), Shela (co-developer), CC (Cursor Claude), SuperGrok (xAI Grok), Gem (Google Gemini)

---

## Summary

Successfully built, debugged, and demonstrated the **AI as Peers** feature — multiple AI models appearing as named, visible peers in a Mattermost channel, collaborating in real-time with human team members. Published a demo video, three blog posts, and updated the AI as Peers webpage.

## What Was Accomplished

### AI Peer Bots (All Three Live)

| Bot | Provider | Model | Mattermost Account | Trigger |
|-----|----------|-------|--------------------|---------|
| **CC** | Anthropic Claude | `claude-sonnet-4-6` | `@cc` (cc@polysaas.online) | `#cc` |
| **SuperGrok** | xAI Grok | `grok-3` | `@supergrok` | `#supergrok` |
| **Gem** | Google Gemini | `gemini-flash-latest` | `@gem` (gem@polysaas.online) | `#gem` |

### Architecture

```
User types "#cc hello" in Mattermost
    → Mattermost outgoing webhook fires (trigger word: #cc)
    → POST to Django: /dose/webhook/ai-peers/
    → ai_peers_webhook.py validates token, identifies mentioned peers
    → Dispatches to ai_peer_service.handle_mention() in background thread
    → handle_mention() fetches channel context (last 15 messages)
    → Routes to correct LLM provider (Anthropic / xAI / Gemini)
    → Posts AI response back to channel as the bot user identity
```

### Issues Resolved

1. **Mattermost `@` autocomplete interference** — Switched trigger words from `@cc` to `#cc` to avoid Mattermost's aggressive typeahead inserting file/user references instead of firing the webhook.

2. **Webhook connectivity blocked** — Mattermost's `AllowedUntrustedInternalConnections` setting was blocking outgoing webhooks to the host IP (`192.168.8.180`). Updated Mattermost server config to whitelist the host.

3. **Security token mismatch** — When trigger words were updated, the webhook token was accidentally cleared. Restored and synchronized the token between Mattermost and Django (`AI_PEERS_WEBHOOK_TOKEN`).

4. **Anthropic model name 404** — Claude 3.x models were retired. Updated to `claude-sonnet-4-6` (current API model name as of April 2026).

5. **Mattermost `root_id` error** — Bot replies using `root_id` for threading caused 400 errors. Added fallback to post without threading, then removed threading entirely for cleaner inline demo flow.

6. **Gem bot 403 Forbidden** — The `@gem` bot wasn't a member of the team or Town Square channel. Added via Mattermost API.

7. **Environment variable loading** — `django-environ` wasn't overwriting existing env vars on reload. Added `overwrite=True` to `env.read_env()`.

8. **Gemini quota exceeded** — Free tier limits hit. User linked billing account to enable paid tier.

9. **MATTERMOST_URL defaulting to production** — Was defaulting to `https://mm.polysaas.online` (not resolvable locally). Changed default to `http://localhost:8065` and added to `.env`.

### Rich AI Context

All three peers now receive a system prompt with full PolySaaS context:
- Team members (MO, Shela) and their roles
- Platform description and architecture (Django/DOSE, passthrough proxy, Pub/Sub, tenant isolation)
- Pricing tiers (PolySaaS-1 $29.99, PolySaaS-3 $79.99, Unlimited $199.99)
- Raise context ($15K SAFE, Wefunder community round)
- Instructions to keep responses concise (~150 words)

### UI/UX for Demo

- Mattermost dark mode (Onyx theme) enabled for admin and shela accounts
- Bot responses appear as inline channel messages (not hidden in threads)
- Post de-duplication prevents double-processing

## Files Changed

| File | Change |
|------|--------|
| `dose/services/ai_peer_service.py` | Added `_call_gemini()`, updated model names, added debug logging, removed threading from `_post_as_bot()` |
| `dose/views/ai_peers_webhook.py` | Added `#gem` registration, rich system prompts, `#` trigger pattern, post de-duplication |
| `mysite/settings.py` | Added `GEMINI_API_KEY`, `BOT_TOKEN_CC/SUPERGROK/GEM`, `MATTERMOST_URL` default fix, `overwrite=True` on env loading |
| `.env` | Added `MATTERMOST_URL`, `BOT_TOKEN_GEM` |
| `dose/urls.py` | AI peers webhook URL (added in prior session) |

## Demo Deliverables Published

- Demo video published via Loom
- Three blog posts published
- AI as Peers webpage updated on polysaas.online

## What's Next

- Record a polished Loom/OBS demo video with Shela's script (Shela asks #supergrok and #cc collaborative questions about PolySaaS workflows)
- Send angel update with AI as Peers video as traction evidence
- Prepare Wefunder community round launch (mid-April) with demo as centerpiece
- Consider adding persistent memory/context for AI peers (database-backed conversation history)

---

**Bingo!** Three AI models collaborating as visible peers in a Mattermost channel — a key differentiator for PolySaaS and the investor demo.
