# BINGO: Request Path Image Fix — Dynamic Orchestration Page

**Date:** 2026-03-16
**Status:** Complete
**Snapshot:** `snapshot_20260316_132856_bingo_request_path_image_fix.json`

## Summary

Replaced the "Request Path" / "PolySaaS Middleware" graph image on the Dynamic Orchestration page. The original PNG had multiple defects (RGBA transparency rendering as black, scrollbar artifact baked into bottom, content off-center within the image frame). After multiple CSS-based attempts that could not overcome the source file issues, the user provided a clean replacement image which was uploaded and placed successfully.

## What Changed

### Image Replacement
- **Old image:** `dynamic-orchestration-request-path.png` (1024x600, RGBA with transparency issues)
- **New image:** `polysaas-middleware-graph.png` (WordPress media ID: 2507)
  - Clean white background, no transparency
  - Graph content properly centered within the frame
  - All nodes (PolySaaS Middleware, Article, Chunk, Person, City, Country, Industry Category) fully visible with breathing room
  - Updated label: "PolySaaS Middleware" instead of "Request Path"

### Styling
- Matches the working agent-flow and event-bus images on the same page
- `width:100%; border-radius:10px; box-shadow:0 3px 12px rgba(0,0,0,0.1)`
- Centered in `max-width:700px` container
- Caption: "PolySaaS Middleware graph: event-driven relationships across entities, categories, and locations"

## Lessons Learned

- CSS cannot fix a fundamentally broken source image (transparency, baked-in artifacts, off-center content)
- Always check image `mode` (RGB vs RGBA) before assuming how it will render on dark backgrounds
- When an image has content extending to the pixel edge, `border-radius` will clip corner content

## Files Created During Troubleshooting

Scripts used during the fix process (can be cleaned up):
- `fix_request_path_img3.py` through `fix_request_path_final2.py` — iterative CSS fixes
- `fix_request_path_image.py`, `fix_request_path_image2.py` — PIL crop/pad attempts
- `fix_request_path_center.py` — content bounding box crop attempt
- `upload_request_path_new.py` — final successful upload of clean replacement

## Page

- **URL:** https://azure-nightingale-589250.hostingersite.com/dynamic-orchestration/
- **Section:** After "Event-Driven Triggers" capability block
