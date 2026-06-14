import os, django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mysite.settings')
django.setup()
from django.db import connection
from dose.models import Tenant, Instruction, CallBackData

t = Tenant.objects.filter(slug__icontains='ppd').first()
if not t:
    t = Tenant.objects.filter(name__icontains='Pre Production').first()
if not t:
    print('Tenant not found')
    raise SystemExit(1)

# Check TenantApp and run provision if needed
from dose.models import TenantApp
ta = TenantApp.public_bundles.filter(tenant=t).first()
if ta:
    print(f'TenantApp odoo status={ta.status} extra={list((ta.extra_config or {}).keys())}')
else:
    print('No TenantApp row in public_bundles for this tenant')

with connection.cursor() as c:
    c.execute(f'SET search_path TO "{t.schema_name}", public')
    n = Instruction.objects.count()
    print(f'Instructions (tenant search_path): {n}')
    for i in Instruction.objects.filter(requestpath__icontains='account')[:10]:
        print(f'  id={i.id} path={i.requestpath!r} dir={i.direction} method={i.requestmethod} script={i.executescript} cb={i.save_callbackdata}')
    cb = CallBackData.objects.count()
    print(f'CallBackData rows: {cb}')

with connection.cursor() as c:
    c.execute('SET search_path TO public')
    all_pub = Instruction.objects.count()
    print(f'Public total Instructions: {all_pub}')
    for i in Instruction.objects.all()[:15]:
        print(f'  pub id={i.id} tenant_id={i.tenant_id} path={i.requestpath!r} dir={i.direction} script={i.executescript}')
    pub = list(Instruction.objects.filter(tenant__isnull=True, requestpath__icontains='account').values_list('id', 'requestpath', 'direction', 'requestmethod'))
    print(f'Public global account* instructions: {len(pub)}')

# Compare working tenant
for slug in ['polysaast121', 'olient']:
    tx = Tenant.objects.filter(slug=slug).first()
    if tx:
        with connection.cursor() as c:
            c.execute(f'SET search_path TO "{tx.schema_name}", public')
            print(f'{slug} Instructions: {Instruction.objects.count()} odoo/account: {Instruction.objects.filter(requestpath__icontains="account").count()}')
