#!/usr/bin/env bash
set -euo pipefail

# Delegate to the base image entrypoint/cmd.
exec "$@"
