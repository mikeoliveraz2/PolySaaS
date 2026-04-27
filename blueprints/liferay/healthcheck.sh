#!/usr/bin/env bash
set -euo pipefail

PORT="${LIFERAY_HTTP_PORT:-8080}"

curl -fsS "http://127.0.0.1:${PORT}/" >/dev/null
