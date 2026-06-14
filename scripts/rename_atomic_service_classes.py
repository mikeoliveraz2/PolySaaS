"""One-shot: rename *Service atomic class names and fix stale module imports."""
from __future__ import annotations

import re
import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

# Longest names first to avoid partial replacements.
CLASS_RENAMES = [
    ("GenerateImageAndExport", "GenerateImageAndExport"),
    ("EndpointDataExtractor", "EndpointDataExtractor"),
    ("MattermostProvisioning", "MattermostProvisioning"),
    ("OdooInvoiceNotifier", "OdooInvoiceNotifier"),
    ("Calculus", "Calculus"),
    ("AddToMLDataset", "AddToMLDataset"),
    ("ExportToRESTAPI", "ExportToRESTAPI"),
    ("CreateGitHubIssue", "CreateGitHubIssue"),
    ("CreateCeleryTask", "CreateCeleryTask"),
    ("OdooCustomerSync", "OdooCustomerSync"),
    ("PublishToPubSub", "PublishToPubSub"),
    ("WriteToBigQuery", "WriteToBigQuery"),
    ("NotifyAIPeers", "NotifyAIPeers"),
    ("BigQueryLogging", "BigQueryLogging"),
    ("CopilotQuery", "CopilotQuery"),
    ("EmailToSelf", "EmailToSelf"),
    ("CustomOlient", "CustomOlient"),
    ("GmailEmail", "GmailEmail"),
    ("GmailProxy", "GmailProxy"),
]

MODULE_IMPORT_RENAMES = [
    ("dose.services.differential_equation", "dose.services.differential_equation"),
    ("dose.services.mattermost_provisioning", "dose.services.mattermost_provisioning"),
    ("dose.services.data_extractor", "dose.services.data_extractor"),
    ("dose.services.email_to", "dose.services.email_to"),
    ("dose.services.logging", "dose.services.logging"),
    ("dose.services.gmail_proxy", "dose.services.gmail_proxy"),
]

SKIP_PARTS = {".git", "venv", ".venv", "__pycache__", "var", "node_modules"}


def should_process(path: Path) -> bool:
    if path.suffix != ".py":
        return False
    if ".bak" in path.name:
        return False
    parts = set(path.parts)
    if parts & SKIP_PARTS:
        return False
    return True


def transform(text: str) -> str:
    for old, new in CLASS_RENAMES:
        text = text.replace(old, new)
    for old, new in MODULE_IMPORT_RENAMES:
        text = text.replace(old, new)
    return text


def main() -> None:
    changed_files: list[Path] = []
    for path in ROOT.rglob("*.py"):
        if not should_process(path):
            continue
        try:
            original = path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            continue
        updated = transform(original)
        if updated != original:
            bak = path.with_suffix(path.suffix + ".bak-rename-class")
            if not bak.exists():
                shutil.copy2(path, bak)
            path.write_text(updated, encoding="utf-8")
            changed_files.append(path)

    print(f"Updated {len(changed_files)} files")
    for p in sorted(changed_files)[:40]:
        print(f"  {p.relative_to(ROOT)}")
    if len(changed_files) > 40:
        print(f"  ... and {len(changed_files) - 40} more")


if __name__ == "__main__":
    main()
