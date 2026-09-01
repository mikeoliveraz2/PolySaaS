from pathlib import Path
import base64
from PIL import Image

src = Path(
    r"C:\Users\PC\.cursor\projects\d-PolySaaS\assets"
    r"\c__Users_PC_AppData_Roaming_Cursor_User_workspaceStorage_39549ed560cd5c4fa069ce83ddf22828_images_image-f12e0ad2-40d4-4459-9e73-cfebd9db9896.png"
)
dest_png = Path(r"D:\PolySaaS\static\img\apps\mattermost-sidebar-mark.png")
dest_svg = Path(r"D:\PolySaaS\static\img\apps\mattermost-sidebar-mark.svg")

im = Image.open(src).convert("RGBA")
pix = im.load()
w, h = im.size
for y in range(h):
    for x in range(w):
        r, g, b, _a = pix[x, y]
        lum = 0.299 * r + 0.587 * g + 0.114 * b
        if lum < 100:
            pix[x, y] = (255, 255, 255, 0)
        else:
            t = (lum - 100) / (255 - 100)
            pix[x, y] = (255, 255, 255, int(255 * min(1.0, t * 1.35)))

bbox = im.split()[-1].point(lambda p: 255 if p > 24 else 0).getbbox()
im = im.crop(bbox)
# Square crop with padding so the mark stays round, not stretched.
side = max(im.size) + 16
canvas = Image.new("RGBA", (side, side), (255, 255, 255, 0))
ox = (side - im.size[0]) // 2
oy = (side - im.size[1]) // 2
canvas.paste(im, (ox, oy), im)
canvas = canvas.resize((256, 256), Image.Resampling.LANCZOS)
canvas.save(dest_png, format="PNG", optimize=True)

raw = dest_png.read_bytes()
b64 = base64.b64encode(raw).decode("ascii")
svg = (
    '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100" '
    'preserveAspectRatio="xMidYMid meet">\n'
    f'  <image href="data:image/png;base64,{b64}" x="6" y="6" width="88" height="88"/>\n'
    "</svg>\n"
)
dest_svg.write_text(svg, encoding="utf-8")
print("png", dest_png.stat().st_size, "svg", dest_svg.stat().st_size, "src", src.name)
