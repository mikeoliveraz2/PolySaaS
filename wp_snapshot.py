"""
WordPress Page Snapshot & Restore Utility
==========================================
Exports all WordPress page content (raw Gutenberg blocks) to timestamped JSON files.
Run before any bulk update script to create a rollback point.

Usage:
    python wp_snapshot.py export              # Create a snapshot
    python wp_snapshot.py export "description" # Create a snapshot with a label
    python wp_snapshot.py list                 # List available snapshots
    python wp_snapshot.py restore <filename>   # Restore all pages from a snapshot
    python wp_snapshot.py restore <filename> <slug>  # Restore a single page
    python wp_snapshot.py diff <filename>      # Show which pages changed since snapshot

As a library (call from other scripts):
    from wp_snapshot import take_snapshot
    take_snapshot("before fixing header logo")
"""
import requests, json, sys, os, re
from datetime import datetime
from pathlib import Path

sys.stdout.reconfigure(encoding='utf-8', errors='replace')

AZURE = "https://azure-nightingale-589250.hostingersite.com"
AUTH = ("mikeoliveraz@gmail.com", "vlop MpGU Os2V xDSI C6T7 2fAN")
SNAPSHOT_DIR = Path(__file__).parent / "wp_snapshots"


def get_session():
    s = requests.Session()
    s.auth = AUTH
    return s


def fetch_all_pages(session):
    """Fetch all pages with raw content (context=edit)."""
    r = session.get(f"{AZURE}/wp-json/wp/v2/pages", params={
        "per_page": 100, "context": "edit",
        "_fields": "id,slug,title,content,status,modified"
    })
    r.raise_for_status()
    pages = r.json()
    return [{
        "id": p["id"],
        "slug": p["slug"],
        "title": p["title"]["raw"] if isinstance(p["title"], dict) else p["title"],
        "content": p["content"]["raw"] if isinstance(p["content"], dict) else p["content"],
        "status": p["status"],
        "modified": p["modified"],
    } for p in pages]


def take_snapshot(description=""):
    """Export all pages to a timestamped JSON file. Returns the filepath."""
    SNAPSHOT_DIR.mkdir(exist_ok=True)
    s = get_session()
    pages = fetch_all_pages(s)

    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    safe_desc = re.sub(r'[^a-zA-Z0-9_-]', '_', description)[:40] if description else ""
    suffix = f"_{safe_desc}" if safe_desc else ""
    filename = f"snapshot_{ts}{suffix}.json"
    filepath = SNAPSHOT_DIR / filename

    data = {
        "timestamp": datetime.now().isoformat(),
        "description": description,
        "page_count": len(pages),
        "pages": pages,
    }

    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

    print(f"Snapshot saved: {filename} ({len(pages)} pages)")
    return str(filepath)


def list_snapshots():
    """List all available snapshots."""
    if not SNAPSHOT_DIR.exists():
        print("No snapshots directory found.")
        return

    files = sorted(SNAPSHOT_DIR.glob("snapshot_*.json"), reverse=True)
    if not files:
        print("No snapshots found.")
        return

    print(f"{'Filename':<55} {'Pages':>5}  {'Description'}")
    print("-" * 90)
    for f in files:
        try:
            with open(f, "r", encoding="utf-8") as fh:
                data = json.load(fh)
            desc = data.get("description", "")[:40]
            count = data.get("page_count", "?")
            print(f"{f.name:<55} {count:>5}  {desc}")
        except Exception as e:
            print(f"{f.name:<55}  (error reading: {e})")


def restore_snapshot(filename, slug_filter=None):
    """Restore pages from a snapshot file."""
    filepath = SNAPSHOT_DIR / filename if not os.path.isabs(filename) else Path(filename)
    if not filepath.exists():
        print(f"Snapshot not found: {filepath}")
        return False

    with open(filepath, "r", encoding="utf-8") as f:
        data = json.load(f)

    pages = data["pages"]
    if slug_filter:
        pages = [p for p in pages if p["slug"] == slug_filter]
        if not pages:
            print(f"No page with slug '{slug_filter}' in snapshot.")
            return False

    print(f"Restoring {len(pages)} page(s) from {filename}...")
    s = get_session()
    restored = 0

    for page in pages:
        pid = page["id"]
        slug = page["slug"]
        content = page["content"]

        r = s.post(f"{AZURE}/wp-json/wp/v2/pages/{pid}", json={"content": content})
        if r.status_code == 200:
            restored += 1
            print(f"  {slug}: restored")
        else:
            print(f"  {slug}: FAILED ({r.status_code})")

    print(f"\nRestored {restored}/{len(pages)} pages.")
    return restored == len(pages)


def diff_snapshot(filename):
    """Show which pages have changed since the snapshot."""
    filepath = SNAPSHOT_DIR / filename if not os.path.isabs(filename) else Path(filename)
    if not filepath.exists():
        print(f"Snapshot not found: {filepath}")
        return

    with open(filepath, "r", encoding="utf-8") as f:
        data = json.load(f)

    snap_pages = {p["slug"]: p["content"] for p in data["pages"]}
    s = get_session()
    current_pages = fetch_all_pages(s)

    changed = []
    for cp in current_pages:
        snap_content = snap_pages.get(cp["slug"])
        if snap_content is None:
            changed.append((cp["slug"], "NEW (not in snapshot)"))
        elif snap_content != cp["content"]:
            old_len = len(snap_content)
            new_len = len(cp["content"])
            delta = new_len - old_len
            sign = "+" if delta >= 0 else ""
            changed.append((cp["slug"], f"CHANGED ({sign}{delta} chars)"))

    if changed:
        print(f"Pages changed since {filename}:")
        for slug, status in sorted(changed):
            print(f"  {slug}: {status}")
    else:
        print("No changes since snapshot.")


if __name__ == "__main__":
    args = sys.argv[1:]
    if not args or args[0] == "export":
        desc = args[1] if len(args) > 1 else ""
        take_snapshot(desc)
    elif args[0] == "list":
        list_snapshots()
    elif args[0] == "restore":
        if len(args) < 2:
            print("Usage: wp_snapshot.py restore <filename> [slug]")
        else:
            slug = args[2] if len(args) > 2 else None
            restore_snapshot(args[1], slug)
    elif args[0] == "diff":
        if len(args) < 2:
            print("Usage: wp_snapshot.py diff <filename>")
        else:
            diff_snapshot(args[1])
    else:
        print(__doc__)
