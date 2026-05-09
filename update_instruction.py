import os, django
os.environ['DJANGO_SETTINGS_MODULE'] = 'mysite.settings'
django.setup()
from django.db import connection

SCHEMA = 'polysaasts'  # PolySaaS Test Sun — the active tenant

with connection.cursor() as c:
    c.execute(f"SET search_path TO {SCHEMA}, public")

from dose.models import Instruction

existing = Instruction.objects.all()
print(f"Instructions in {SCHEMA}:", list(existing.values('id', 'direction', 'requestpath')))

if existing.exists():
    instr = existing.first()
    print("Updating existing instruction id=", instr.id)
else:
    print("No instructions found — creating one")
    instr = Instruction()

instr.requestpath = 'account.move/web_search_read'
instr.direction = 'REQ'
instr.requestmethod = 'POST'
instr.executescript = 'OdooInvoiceNotifierService'
if hasattr(instr, 'urllist'):
    instr.urllist = ''
if hasattr(instr, 'match_type'):
    instr.match_type = 'contains'
if hasattr(instr, 'match_extra'):
    instr.match_extra = {}
instr.save()

instr.refresh_from_db()
print("After:", instr.id, instr.direction, instr.requestpath, instr.executescript)
