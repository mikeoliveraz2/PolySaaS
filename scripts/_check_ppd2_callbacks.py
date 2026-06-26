import os
import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "mysite.settings")
django.setup()

from django.db import connection
from dose.models import Tenant, Instruction, CallBackData

with connection.cursor() as c:
    c.execute(
        "SELECT schema_name FROM information_schema.schemata "
        "WHERE schema_name LIKE '%ppd%' ORDER BY 1"
    )
    print("Schemas:", [r[0] for r in c.fetchall()])

for slug in ("polysaasppd2", "polysaasppd"):
    tenant = Tenant.objects.filter(slug=slug).first()
    if not tenant:
        print(f"\n=== {slug}: no Tenant row ===")
        continue
    schema = tenant.schema_name
    print(f"\n=== {slug} ({schema}) ===")
    with connection.cursor() as c:
        c.execute(f'SET search_path TO "{schema}", public;')
    for i in Instruction.objects.filter(eventKey="odoo_invoicing_viewed").order_by("id"):
        print(
            f"  instr id={i.id} path={i.requestpath!r} type={i.match_type} "
            f"method={i.requestmethod} script={i.executescript} save_cb={i.save_callbackdata}"
        )
        print(f"    desc={i.description!r}")
    count = CallBackData.objects.filter(matchingEventKey="odoo_invoicing_viewed").count()
    print(f"  CallBackData count (event): {count}")
    for cb in CallBackData.objects.filter(matchingEventKey="odoo_invoicing_viewed").order_by("-id")[:12]:
        print(f"    cb id={cb.id} desc={(cb.description or '')[:70]!r}")
