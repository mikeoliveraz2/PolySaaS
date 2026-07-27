# Scripts

This folder contains operational helpers for local development and migration tasks.

## Current focus

1. Local stack workflows based on `docker-compose.local-stack.yml` and `docker-compose.full-stack.yml`.
2. Application maintenance scripts (WordPress sync, checks, audits, and fix helpers).
3. GCP migration and deployment support under `deploy/gcp/`.

## Environment keys

Use `.env.example` as the canonical key reference for local and hosted environments.

## Notes

1. Render-specific helper scripts and blueprint tooling were removed.
2. Keep script additions provider-neutral where possible.
3. Prefer small, single-purpose scripts with explicit inputs and outputs.
