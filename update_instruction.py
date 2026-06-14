import os, django
os.environ['DJANGO_SETTINGS_MODULE'] = 'mysite.settings'
django.setup()
from django.db import connection

SCHEMA = 'polysaast4'  # PolySaaS T4 — active test tenant

with connection.cursor() as c:
    c.execute(f"SET search_path TO {SCHEMA}, public")

from dose.models import Instruction

existing = Instruction.objects.all()
print(f"Instructions in {SCHEMA}:", list(existing.values('id', 'direction', 'requestpath', 'match_type')))

def upsert(requestpath, match_type, direction, requestmethod, executescript, eventKey='', description=''):
    instr = Instruction.objects.filter(requestpath=requestpath, direction=direction).first()
    if instr:
        print(f"  Updating id={instr.id} path={requestpath!r}")
    else:
        print(f"  Creating path={requestpath!r}")
        instr = Instruction()
    instr.requestpath = requestpath
    instr.match_type = match_type
    instr.direction = direction
    instr.requestmethod = requestmethod
    instr.executescript = executescript
    instr.eventKey = eventKey
    instr.description = description
    instr.urllist = ''
    instr.match_extra = {}
    instr.save()
    print(f"  => id={instr.id} {instr.match_type}:{instr.requestpath} dir={instr.direction} script={instr.executescript}")

# 1. Display-shell navigation trigger (GET /odoo/customer-invoices fired by middleware hook)
upsert(
    requestpath='customer-invoices',
    match_type='contains',
    direction='REQ',
    requestmethod='GET',
    executescript='OdooInvoiceNotifier',
    eventKey='odoo_invoicing_viewed',
    description='Odoo Invoicing page navigation — display shell GET trigger',
)

# 2. API data-load trigger (POST /web/dataset/call_kw/account.move/web_search_read via forwarding.py)
upsert(
    requestpath='account.move/web_search_read',
    match_type='contains',
    direction='REQ',
    requestmethod='POST',
    executescript='OdooInvoiceNotifier',
    eventKey='odoo_invoicing_viewed',
    description='Odoo invoice data load — forwarding.py POST trigger',
)
