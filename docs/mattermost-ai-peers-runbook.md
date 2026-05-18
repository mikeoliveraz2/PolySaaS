# Mattermost AI Peers Runbook
_Date: 2026-04-15_

## Status
The Mattermost AI peers layer now supports these peer identities through the existing Django webhook flow:
- `#copilot`
- `#cursor`
- `#grok`
- `#router`
- `#openclaw`

Legacy aliases remain supported for compatibility:
- `#cc` routes to `cursor`
- `#supergrok` routes to `grok`
- `#gem` remains available when `BOT_TOKEN_GEM` is configured

This is a working bot-based Mattermost integration. It is not a verified native Mattermost plugin deployment for OpenClaw.

---

## What Changed
The AI peers layer was expanded from the older three-bot demo (`cc`, `supergrok`, `gem`) to a configurable peer registry that supports named Mattermost identities for the current AI-as-Peers vision.

Current peer mapping:

| Peer | Default provider | Purpose |
|---|---|---|
| `copilot` | `anthropic` | engineering execution and implementation planning |
| `cursor` | `anthropic` | repo-aware coding and debugging |
| `grok` | `xai` | direct analysis and fast synthesis |
| `router` | `anthropic` | orchestration and task routing |
| `openclaw` | `anthropic` | open-systems and self-hosted workflow design |
| `gem` | `gemini` | synthesis-oriented Gemini peer |

Provider routing is configurable in Django settings, so the Mattermost bot identity and the backend model provider are decoupled.

---

## Files
- `dose/views/ai_peers_webhook.py`
- `dose/services/ai_peer_service.py`
- `dose/management/commands/setup_ai_peers.py`
- `mysite/settings.py`

---

## Environment Variables
Required base variables:
- `MATTERMOST_URL`
- `MATTERMOST_ADMIN_TOKEN`
- `AI_PEERS_WEBHOOK_TOKEN`

Provider keys as needed:
- `ANTHROPIC_API_KEY`
- `XAI_API_KEY`
- `GEMINI_API_KEY`

Bot tokens:
- `BOT_TOKEN_COPILOT`
- `BOT_TOKEN_CURSOR`
- `BOT_TOKEN_GROK`
- `BOT_TOKEN_ROUTER`
- `BOT_TOKEN_OPENCLAW`
- `BOT_TOKEN_GEM`
- `BOT_TOKEN_GEMINI`
- `BOT_TOKEN_WINDSURF`

Compatibility tokens still supported:
- `BOT_TOKEN_CC`
- `BOT_TOKEN_SUPERGROK`

Optional provider overrides:
- `AI_PEER_PROVIDER_COPILOT`
- `AI_PEER_PROVIDER_CURSOR`
- `AI_PEER_PROVIDER_GROK`
- `AI_PEER_PROVIDER_ROUTER`
- `AI_PEER_PROVIDER_OPENCLAW`
- `AI_PEER_PROVIDER_GEM`

Examples:
- `AI_PEER_PROVIDER_COPILOT=anthropic`
- `AI_PEER_PROVIDER_GROK=xai`
- `AI_PEER_PROVIDER_OPENCLAW=anthropic`

---

## Mattermost Setup
### 1. Create the channel
Create a dedicated Mattermost channel such as:
- `ai-peers`
- `deploy-team`
- `grok-copilot-cursor`

### 2. Create the bot accounts
Run:

```powershell
python manage.py setup_ai_peers
```

Dry-run validation:

```powershell
python manage.py setup_ai_peers --dry-run
```

The current command provisions these bot identities:
- `@copilot`
- `@cursor`
- `@grok`
- `@router`
- `@openclaw`

### 3. Configure the Mattermost outgoing webhook
Use the helper command:

```bash
python manage.py create_ai_peers_outgoing_webhook --team <your-team> --channel-name town-square
```

It will point the webhook to:

```text
/dose/webhook/ai-peers/
```

Trigger words to configure:
- `#copilot`
- `#cursor`
- `#grok`
- `#router`
- `#openclaw`

Optional compatibility triggers:
- `#cc`
- `#supergrok`
- `#gem`

### 4. Add the bots to the target team/channel
Ensure the created bot users are members of the team and the target channel.

---

## Operational Notes
- The current implementation posts responses back into Mattermost as the selected bot user.
- Peer recognition is registry-based and supports aliases.
- `router` is the orchestration identity, but it currently behaves as another configured AI peer. There is no verified separate OpenClaw routing service wired in this repo yet.
- `openclaw` is currently implemented as a named Mattermost peer identity, not a confirmed external OpenClaw deployment.

---

## Recommended Next Step
If the immediate goal is live collaboration in Mattermost, the fastest path is:
1. create the `ai-peers` channel
2. provision the bots with `setup_ai_peers`
3. configure the outgoing webhook triggers
4. test `#copilot`, `#cursor`, `#grok`, and `#router` in-channel

If the goal is a true external conductor service, the next work item is to define and deploy a separate OpenClaw-compatible router service and connect it to Mattermost explicitly instead of treating it as a peer alias.
