---
scope: ["dose/polysniffer/*", "dose/templates/polysniffer/*"]
---
# PolySniffer embedding rule

- NEVER use `<iframe>` in the PolySniffer workspace, passthrough pages, or any related template.
- The ONLY allowed embedding methods are:
  1. Server-side inline HTML scoping/rewriting (preferred for passthrough content).
  2. `<object type="text/html" ...>` only if the template already uses it and the user has not asked to change the approach.
- If an `<iframe>` seems unavoidable, stop and ask the user for explicit permission before writing code.
- Before editing `sniff_workspace.html`, `sniff_pt_embed.py`, `sniff_urls.py`, or `sniff_v2_workspace.py`, re-read this rule and confirm the chosen embedding approach in one sentence.
