#!/usr/bin/env bash
set -euo pipefail

# We healthcheck php-fpm container by verifying PHP responds.
php -v >/dev/null
