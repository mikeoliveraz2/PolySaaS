from pathlib import Path
import argparse


APPS = [
    "odoo",
    "nextcloud",
    "mattermost",
    "dolibarr",
    "liferay",
    "wordpress",
    "ai-as-peers",
    "apps-as-peers",
    "polysysmon",
]


REQUIRED_FILES = [
    "Dockerfile",
    "docker-compose.yml",
    ".env.example",
    "README.md",
    "provision.sh",
]


PROVISION_CONTRACT_MARKER = "polysaas_provision_contract=v1"


def ensure_dirs(root: Path) -> None:
    for app in APPS:
        (root / app).mkdir(parents=True, exist_ok=True)


def check_blueprints(root: Path) -> list[str]:
    missing = []
    for app in APPS:
        app_dir = root / app
        for rel in REQUIRED_FILES:
            if not (app_dir / rel).exists():
                missing.append(f"{app}/{rel}")
        provision = app_dir / "provision.sh"
        if provision.exists():
            try:
                text = provision.read_text(encoding="utf-8")
            except Exception:
                text = ""
            if PROVISION_CONTRACT_MARKER not in text:
                missing.append(f"{app}/provision.sh missing {PROVISION_CONTRACT_MARKER}")
    return missing


def scaffold_missing(root: Path) -> None:
    for app in APPS:
        app_dir = root / app
        app_dir.mkdir(parents=True, exist_ok=True)
        readme = app_dir / "README.md"
        if not readme.exists():
            readme.write_text(f"# PolySaaS Blueprint: {app}\n", encoding="utf-8")
        provision = app_dir / "provision.sh"
        if not provision.exists():
            provision.write_text(
                "#!/usr/bin/env bash\nset -euo pipefail\n\n"
                "if [ -f .env ]; then\n  set -a\n  . ./.env\n  set +a\nfi\n\n"
                ": \"${TENANT_SLUG:?TENANT_SLUG is required}\"\n\n"
                f"echo \"[provision] app={app} tenant=${{TENANT_SLUG}}\"\n"
                "echo \"[provision] Hook: register_oauth2_app_for_tenant() (TODO)\"\n",
                encoding="utf-8",
            )


def main() -> None:
    repo_root = Path(__file__).resolve().parents[1]
    blueprints_root = repo_root / "blueprints"
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true")
    parser.add_argument("--scaffold", action="store_true")
    args = parser.parse_args()

    ensure_dirs(blueprints_root)

    if args.scaffold:
        scaffold_missing(blueprints_root)

    missing = check_blueprints(blueprints_root)
    if args.check and missing:
        raise SystemExit("Missing blueprint files:\n" + "\n".join(missing))

    if missing:
        print("Missing blueprint files:\n" + "\n".join(missing))
    else:
        print(f"Blueprints OK under: {blueprints_root}")


if __name__ == "__main__":
    main()
