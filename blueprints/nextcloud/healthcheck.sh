#!/usr/bin/env bash
set -euo pipefail

PORT="${NEXTCLOUD_PORT:-80}"

curl -fsS "http://127.0.0.1:${PORT}/status.php" >/dev/null
