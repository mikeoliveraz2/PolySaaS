"""Verify the GCP section was added correctly."""
import sys
sys.stdout.reconfigure(encoding='utf-8', errors='replace')
from docx import Document

doc = Document(r'D:\PolySaaS\dose\website\staging\wp-content\uploads\PolySaaS Online Business PlanF1.md.docx')

# Find and print the GCP section
printing = False
for i, p in enumerate(doc.paragraphs):
    if 'GCP Deployment Plan' in p.text:
        printing = True
    if printing:
        style = p.style.name if p.style else ''
        prefix = f'[{style}] ' if 'Heading' in style else ''
        print(f"{i}: {prefix}{p.text}")
    if printing and 'Targets' in p.text and '18' in p.text:
        break
