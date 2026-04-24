import json
import sys

# Usage: python fix_tenant_json.py local-backup.json fixed-backup.json
# This script will convert all "tenant_id": <int> to "tenant": "slug" in your backup JSON.
# You must provide a mapping from old tenant_id to new tenant_slug below.

# Example mapping (fill this in with your real data!):
id_to_slug = {
    1: "polysaas",
    2: "olient",
    # ... add all your tenant ids and their new slugs here ...
}

def fix_tenant_refs(obj):
    if isinstance(obj, dict):
        for k, v in list(obj.items()):
            if k == "tenant_id" and v in id_to_slug:
                obj["tenant"] = id_to_slug[v]
                del obj["tenant_id"]
            else:
                fix_tenant_refs(v)
    elif isinstance(obj, list):
        for item in obj:
            fix_tenant_refs(item)

if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: python fix_tenant_json.py local-backup.json fixed-backup.json")
        sys.exit(1)
    with open(sys.argv[1], "r", encoding="utf-8") as f:
        data = json.load(f)
    fix_tenant_refs(data)
    with open(sys.argv[2], "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)
    print("Done. Output written to", sys.argv[2])
