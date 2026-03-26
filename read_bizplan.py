"""Read the business plan docx and output its full content."""
import sys
sys.stdout.reconfigure(encoding='utf-8', errors='replace')
from docx import Document

doc = Document(r'D:\PolySaaS\dose\website\staging\wp-content\uploads\PolySaaS Online Business PlanF1.md.docx')

for i, p in enumerate(doc.paragraphs):
    style = p.style.name if p.style else ''
    prefix = ''
    if 'Heading' in style:
        prefix = f'[{style}] '
    print(f"{i}: {prefix}{p.text}")
