"""One-off: parse HubSpot HAR blobs from agent transcript."""
import json
from collections import Counter

TRANSCRIPT = (
    r"C:\Users\PC\.cursor\projects\d-PolySaaS\agent-transcripts"
    r"\cc6d90cd-95ad-4157-b6af-7cab8b21526f\cc6d90cd-95ad-4157-b6af-7cab8b21526f.jsonl"
)

found = []
with open(TRANSCRIPT, "r", encoding="utf-8") as f:
    for i, line in enumerate(f):
        if "hsappstatic" not in line or '"log":' not in line:
            continue
        try:
            obj = json.loads(line)
            text = obj["message"]["content"][0]["text"]
            idx = text.find("{")
            har, _ = json.JSONDecoder().raw_decode(text, idx)
            entries = har["log"]["entries"]
            native = sum(
                1 for e in entries if "/dose/sniff/" in e["request"]["url"]
            )
            cdn404 = sum(
                1
                for e in entries
                if "static.hsappstatic.net" in e["request"]["url"]
                and e["response"].get("status") == 404
            )
            title = har["log"]["pages"][0]["title"] if har["log"].get("pages") else "?"
            found.append((i, len(entries), native, cdn404, title[:80]))
        except Exception:
            pass

print("HAR blobs found:", len(found))
for row in found:
    print(row)
