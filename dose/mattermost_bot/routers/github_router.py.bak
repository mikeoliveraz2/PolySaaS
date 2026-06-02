"""GitHub router — PolySaaS repo-aware peer for Mattermost."""
import logging
import requests
from django.conf import settings

logger = logging.getLogger(__name__)

ANTHROPIC_API_URL = "https://api.anthropic.com/v1/messages"
CLAUDE_MODEL = "claude-sonnet-4-6"


def _github_repo_context() -> str:
    repo = getattr(settings, 'GITHUB_REPO', 'mikeoliveraz2/PolySaaS')
    token = getattr(settings, 'GITHUB_TOKEN', '') or getattr(settings, 'GITHUB_API_TOKEN', '')
    if not token:
        return f"Repository: https://github.com/{repo} (no GITHUB_TOKEN — using general knowledge only)."
    try:
        headers = {
            'Authorization': f'Bearer {token}',
            'Accept': 'application/vnd.github+json',
            'X-GitHub-Api-Version': '2022-11-28',
        }
        repo_resp = requests.get(f'https://api.github.com/repos/{repo}', headers=headers, timeout=15)
        repo_resp.raise_for_status()
        data = repo_resp.json()
        open_prs = requests.get(
            f'https://api.github.com/repos/{repo}/pulls',
            headers=headers,
            params={'state': 'open', 'per_page': 5},
            timeout=15,
        )
        pr_lines = []
        if open_prs.status_code == 200:
            for pr in open_prs.json()[:5]:
                pr_lines.append(f"  - #{pr.get('number')} {pr.get('title')}")
        return (
            f"Repository: {data.get('full_name', repo)}\n"
            f"Default branch: {data.get('default_branch', 'main')}\n"
            f"Open issues: {data.get('open_issues_count', '?')}\n"
            f"Recent open PRs:\n" + ('\n'.join(pr_lines) if pr_lines else '  (none fetched)')
        )
    except Exception as exc:
        logger.warning("[GitHub] API context fetch failed: %s", exc)
        return f"Repository: https://github.com/{repo} (live API fetch failed: {exc})"


def handle(message: str, user_id: str, channel_id: str) -> str:
    api_key = getattr(settings, 'ANTHROPIC_API_KEY', '')
    if not api_key:
        return "⚠️ GitHub peer is offline — ANTHROPIC_API_KEY not configured."

    clean = message
    for tag in ('@github', '@GitHub', '@anyone'):
        clean = clean.replace(tag, '')
    clean = clean.strip()
    if not clean:
        repo = getattr(settings, 'GITHUB_REPO', 'mikeoliveraz2/PolySaaS')
        return (
            f"Hi! I'm **GitHub**, your repo peer for **{repo}**. "
            "Ask about branches, PRs, architecture, or what changed recently — tag **@github**."
        )

    context = _github_repo_context()
    try:
        resp = requests.post(
            ANTHROPIC_API_URL,
            headers={
                "x-api-key": api_key,
                "anthropic-version": "2023-06-01",
                "Content-Type": "application/json",
            },
            json={
                "model": CLAUDE_MODEL,
                "max_tokens": 1500,
                "system": (
                    "You are GitHub, an AI peer representing the PolySaaS GitHub repository in Mattermost. "
                    "Use the live repo snapshot below when answering. Be concise and practical.\n\n"
                    f"{context}"
                ),
                "messages": [{"role": "user", "content": clean}],
            },
            timeout=45,
        )
        resp.raise_for_status()
        return resp.json()['content'][0]['text']
    except requests.exceptions.Timeout:
        logger.warning("[GitHub] API timeout")
        return "⚠️ GitHub peer is thinking… (timeout — try again)"
    except Exception as exc:
        logger.error("[GitHub] API error: %s", exc)
        return f"⚠️ GitHub peer hit an error: {str(exc)[:120]}"
