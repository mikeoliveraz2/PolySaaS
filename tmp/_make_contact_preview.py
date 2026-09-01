from pathlib import Path

src = Path(r"D:\PolySaaS\dose\templates\polysniffer\slack_wireframe.html").read_text(encoding="utf-8")
style = src.split("<style>", 1)[1].split("</style>", 1)[0]
marker = 'id="ps-slack-modal-contact"'
start = src.rfind("<div", 0, src.index(marker))
modal = src[start:].split('id="ps-slack-modal-sale"', 1)[0]
modal = modal.replace(" hidden", "")
modal = modal.replace('class="ps-slack-mock__modal"', 'class="ps-slack-mock__modal is-open"')
html = (
    "<!doctype html><html><head><meta charset='utf-8'><title>Contact style preview</title>"
    "<style>html,body{margin:0;height:100%;background:#1a1d21}"
    ".ps-slack-mock{position:relative;min-height:100vh}"
    + style
    + ".ps-slack-mock__modal{display:flex!important}</style></head><body>"
    '<div class="ps-slack-mock">'
    + modal
    + "</div></body></html>"
)
out = Path(r"D:\PolySaaS\tmp\_odoo_contact_preview.html")
out.write_text(html, encoding="utf-8")
print(out, out.stat().st_size)
