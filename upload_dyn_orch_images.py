"""Upload Dynamic Orchestration replacement images to WordPress media library."""
import requests

AZURE = "https://azure-nightingale-589250.hostingersite.com"
s = requests.Session()
s.auth = ("mikeoliveraz@gmail.com", "vlop MpGU Os2V xDSI C6T7 2fAN")

images = [
    {
        "path": r"C:\Users\PC\.cursor\projects\d-PolySaaS\assets\c__Users_PC_AppData_Roaming_Cursor_User_workspaceStorage_77452477b6ce94d3acba53b24d1f01c9_images_dyn_orch2-f7c0e890-a427-49d1-b0f7-5e5285a3816f.png",
        "filename": "dynamic-orchestration-agent-flow.png",
        "title": "Dynamic Orchestration — Agent Task Execution Flow",
        "alt": "Dynamic Orchestration agent-based task execution flow with orchestrator, planner, and MCP server"
    },
    {
        "path": r"C:\Users\PC\.cursor\projects\d-PolySaaS\assets\c__Users_PC_AppData_Roaming_Cursor_User_workspaceStorage_77452477b6ce94d3acba53b24d1f01c9_images_dyna_orche3-0e9e86be-f574-434d-ab6e-ca18257d5658.png",
        "filename": "dynamic-orchestration-event-bus.png",
        "title": "Dynamic Orchestration — Event-Based Architecture",
        "alt": "Event-based orchestration architecture with central event bus and domain orchestration frameworks"
    }
]

uploaded = []
for img in images:
    with open(img["path"], "rb") as f:
        data = f.read()
    print(f"Uploading {img['filename']} ({len(data)} bytes)...")
    
    r = s.post(
        f"{AZURE}/wp-json/wp/v2/media",
        headers={
            "Content-Disposition": f'attachment; filename="{img["filename"]}"',
            "Content-Type": "image/png",
        },
        data=data
    )
    
    if r.status_code == 201:
        media = r.json()
        print(f"  Success! id={media['id']}, url={media['source_url']}")
        
        s.post(f"{AZURE}/wp-json/wp/v2/media/{media['id']}", json={
            "title": img["title"],
            "alt_text": img["alt"],
        })
        
        uploaded.append({"id": media["id"], "url": media["source_url"], "alt": img["alt"], "title": img["title"]})
    else:
        print(f"  Error: {r.status_code} {r.text[:200]}")

print(f"\nUploaded {len(uploaded)} images:")
for u in uploaded:
    print(f"  id={u['id']} {u['url']}")
