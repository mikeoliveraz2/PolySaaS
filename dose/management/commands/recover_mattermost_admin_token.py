"""Recover Mattermost admin access without mmctl/UI (Hostinger).

Uses Mattermost Postgres to set a temporary password, then logs in via
http://mattermost:8065 and creates a Personal Access Token for Django provision.

Requires django env: MATTERMOST_DB_USER, MATTERMOST_DB_PASSWORD, MATTERMOST_DB_NAME
(and host mattermost-db on the compose network).
"""
from __future__ import annotations

import os
import secrets
from pathlib import Path

import requests
from django.core.management.base import BaseCommand


# bcrypt of TempMM-Reset-2026! (cost 10). Compatible with Mattermost password check.
_TEMP_PASSWORD = "TempMM-Reset-2026!"
_TEMP_BCRYPT = "$2b$10$.yPtp5.QBxwbpKUCBcHqpeIKrkvAz7ZpLiJC1Sk3YupnAq/CRCo9q"


class Command(BaseCommand):
    help = (
        "Reset Mattermost system-admin password via DB, create PAT via API, "
        "optionally write MATTERMOST_ADMIN_TOKEN to /app/.env"
    )

    def add_arguments(self, parser):
        parser.add_argument(
            "--username",
            default="",
            help="Mattermost username to reset (default: first system_admin)",
        )
        parser.add_argument(
            "--write-env",
            action="store_true",
            help="Append/replace MATTERMOST_ADMIN_TOKEN in /app/.env (or ./.env)",
        )
        parser.add_argument(
            "--mm-url",
            default="",
            help="Mattermost base URL (default: http://mattermost:8065)",
        )

    def handle(self, *args, **options):
        db_user = os.environ.get("MATTERMOST_DB_USER") or "mattermost"
        db_pass = os.environ.get("MATTERMOST_DB_PASSWORD") or ""
        db_name = os.environ.get("MATTERMOST_DB_NAME") or "mattermost"
        db_host = os.environ.get("MATTERMOST_DB_HOST") or "mattermost-db"
        if not db_pass:
            self.stderr.write(
                self.style.ERROR(
                    "MATTERMOST_DB_PASSWORD not set in this container. "
                    "Rebuild django after compose passes MATTERMOST_DB_*."
                )
            )
            return

        try:
            import psycopg2
        except ImportError:
            self.stderr.write(self.style.ERROR("psycopg2 not available"))
            return

        mm_url = (options["mm_url"] or "http://mattermost:8065").rstrip("/")
        want_user = (options["username"] or "").strip()

        self.stdout.write(f"Connecting to {db_host}/{db_name} as {db_user}…")
        conn = psycopg2.connect(
            host=db_host,
            dbname=db_name,
            user=db_user,
            password=db_pass,
            connect_timeout=10,
        )
        conn.autocommit = True
        cur = conn.cursor()

        cur.execute(
            """
            SELECT id, username, email, roles
            FROM users
            WHERE deleteat = 0
            ORDER BY createat ASC
            LIMIT 50
            """
        )
        rows = cur.fetchall()
        if not rows:
            self.stderr.write(self.style.ERROR("No Mattermost users found"))
            conn.close()
            return

        self.stdout.write("Users:")
        for uid, username, email, roles in rows:
            self.stdout.write(f"  {username!r} email={email!r} roles={roles!r}")

        target = None
        if want_user:
            for row in rows:
                if row[1] == want_user:
                    target = row
                    break
            if not target:
                self.stderr.write(self.style.ERROR(f"Username {want_user!r} not found"))
                conn.close()
                return
        else:
            for row in rows:
                if row[3] and "system_admin" in row[3]:
                    target = row
                    break
            if not target:
                target = rows[0]

        user_id, username, email, roles = target
        self.stdout.write(f"Resetting password for {username!r} ({email})…")
        cur.execute(
            "UPDATE users SET password = %s, updateat = (EXTRACT(EPOCH FROM NOW())*1000)::bigint WHERE id = %s",
            (_TEMP_BCRYPT, user_id),
        )
        try:
            cur.execute("DELETE FROM sessions WHERE userid = %s", (user_id,))
        except Exception as exc:
            self.stdout.write(self.style.WARNING(f"Session clear skipped: {exc}"))

        conn.close()

        login_id = email or username
        self.stdout.write(f"Logging in to {mm_url} as {login_id}…")
        session = requests.Session()
        login_resp = session.post(
            f"{mm_url}/api/v4/users/login",
            json={"login_id": login_id, "password": _TEMP_PASSWORD},
            timeout=30,
        )
        if login_resp.status_code != 200:
            self.stderr.write(
                self.style.ERROR(
                    f"Login failed HTTP {login_resp.status_code}: {login_resp.text[:300]}"
                )
            )
            self.stderr.write(
                f"You can still try UI login at MATTERMOST_URL with password: {_TEMP_PASSWORD}"
            )
            return

        bearer = login_resp.headers.get("Token") or ""
        if not bearer:
            self.stderr.write(self.style.ERROR("Login OK but no Token header"))
            return

        headers = {"Authorization": f"Bearer {bearer}"}
        tok_resp = session.post(
            f"{mm_url}/api/v4/users/me/tokens",
            headers=headers,
            json={"description": f"polysaas-django-{secrets.token_hex(4)}"},
            timeout=30,
        )
        if tok_resp.status_code not in (200, 201):
            self.stderr.write(
                self.style.ERROR(
                    f"Token create failed HTTP {tok_resp.status_code}: {tok_resp.text[:300]}"
                )
            )
            self.stderr.write(
                f"Login works with password {_TEMP_PASSWORD} — create a PAT in the UI."
            )
            return

        data = tok_resp.json()
        pat = data.get("token") or ""
        if not pat:
            self.stderr.write(self.style.ERROR(f"No token in response: {data}"))
            return

        self.stdout.write(self.style.SUCCESS(f"PAT created (len={len(pat)})"))
        self.stdout.write(
            self.style.WARNING(
                f"Temporary UI password for {username}: {_TEMP_PASSWORD} — change it after login."
            )
        )

        if options["write_env"]:
            env_path = Path("/app/.env")
            if not env_path.is_file():
                env_path = Path(".env")
            lines = []
            if env_path.is_file():
                lines = [
                    ln
                    for ln in env_path.read_text(encoding="utf-8", errors="replace").splitlines()
                    if not ln.startswith("MATTERMOST_ADMIN_TOKEN=")
                ]
            lines.append(f"MATTERMOST_ADMIN_TOKEN={pat}")
            env_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
            self.stdout.write(self.style.SUCCESS(f"Wrote MATTERMOST_ADMIN_TOKEN to {env_path}"))
        else:
            self.stdout.write(
                "Re-run with --write-env to save the token, or set Dokploy env manually."
            )
            self.stdout.write(f"Token prefix: {pat[:6]}… (use --write-env to persist)")
