from PIL import Image
import os

src = r"C:\Users\PC\.cursor\projects\d-PolySaaS\assets\hero-bg-neural.png"
dst = r"C:\Users\PC\.cursor\projects\d-PolySaaS\assets\hero-bg-neural.jpg"

img = Image.open(src)
img = img.convert("RGB")
img.save(dst, "JPEG", quality=72, optimize=True)
print(f"Original: {os.path.getsize(src)} bytes")
print(f"Compressed: {os.path.getsize(dst)} bytes")
