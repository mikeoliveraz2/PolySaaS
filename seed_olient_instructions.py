"""
Seed the cross-app sync Instructions, Mappings, and InstructionMappings
in the 'olient' tenant schema (Oliver Enterprises).
"""
import os, sys, json
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mysite.settings')
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

import django
django.setup()

from django.db import connection
from dose.models import Instruction, PassThroughEndpoint
from dose.models.mapping import Mapping, InstructionMapping, MappingDirection

SCHEMA = 'olient'

with connection.cursor() as cur:
    cur.execute(f"SET search_path TO {SCHEMA},public;")
print(f"search_path set to {SCHEMA},public")

# --- Find PassThrough endpoints ---
all_eps = PassThroughEndpoint.objects.all()
print(f"Found {all_eps.count()} endpoints in {SCHEMA}:")
for ep in all_eps:
    print(f"  id={ep.id} provider={ep.provider} trigger={ep.trigger_path} url={ep.endpoint_url} menu={ep.menu_title}")

dolibarr_ep = PassThroughEndpoint.objects.filter(trigger_path__icontains='dolibarr').first()
if not dolibarr_ep:
    dolibarr_ep = PassThroughEndpoint.objects.filter(menu_title__icontains='dolibarr').first()
odoo_ep = PassThroughEndpoint.objects.filter(trigger_path__icontains='odoo').first()
if not odoo_ep:
    odoo_ep = PassThroughEndpoint.objects.filter(menu_title__icontains='odoo').first()
print(f"\nDolibarr endpoint: {dolibarr_ep} (id={dolibarr_ep.id if dolibarr_ep else None})")
print(f"Odoo endpoint:     {odoo_ep} (id={odoo_ep.id if odoo_ep else None})")

# --- Instruction A: Dolibarr Form POST Capture ---
instr_a, created_a = Instruction.objects.get_or_create(
    requestpath='/societe/card.php',
    requestmethod='POST',
    defaults={
        'direction': 'REQ',
        'executescript': 'EndpointDataExtractor',
        'eventKey': 'dolibarr.customer.created',
        'save_callbackdata': True,
        'description': 'Captures Dolibarr new third-party form POST, extracts fields via Mapping, publishes to RabbitMQ.',
    }
)
print(f"Instruction A (Dolibarr POST): id={instr_a.id} {'CREATED' if created_a else 'EXISTS'}")

# --- Instruction B: MQ Message -> Odoo Sync ---
instr_b, created_b = Instruction.objects.get_or_create(
    requestpath='/mq/polysaas.crossapp.customer.created',
    requestmethod='POST',
    defaults={
        'direction': 'REQ',
        'executescript': 'OdooCustomerSync',
        'eventKey': 'sync.customer.dolibarr.to.odoo',
        'save_callbackdata': True,
        'description': 'Triggered by MQQueueMonitor when a customer message arrives. Maps normalized data to Odoo partner fields and syncs via XML-RPC.',
    }
)
print(f"Instruction B (MQ->Odoo):      id={instr_b.id} {'CREATED' if created_b else 'EXISTS'}")

# --- Mapping 1: Dolibarr POST -> Normalized Customer Event ---
mapping1_fields = {
    "_topic": "'polysaas.crossapp.customer.created'",
    "_source_app": "'dolibarr'",
    "_entity": "'thirdparty'",
    "_action": "'created'",
    "name": "request.POST.name|strip",
    "name_alias": "request.POST.name_alias|strip|default:None",
    "email": "request.POST.email|strip|lower|email",
    "phone": "request.POST.phone|strip|default:None",
    "fax": "request.POST.fax|strip|default:None",
    "street": "request.POST.address|strip",
    "zip": "request.POST.zipcode|strip",
    "city": "request.POST.town|strip",
    "country_id": "request.POST.country_id|strip|default:None",
    "vat": "request.POST.tva_intra|strip|default:None",
    "customer_code": "request.POST.customer_code|strip|default:None",
    "is_customer": "request.POST.client|int:1:0",
    "is_vendor": "request.POST.fournisseur|int:1:0",
    "status": "request.POST.status|strip|default:1",
    "typent_id": "request.POST.typent_id|strip|default:None",
    "url": "request.POST.url|strip|default:None",
    "created_at": "now:iso",
}

map1, created_m1 = Mapping.objects.get_or_create(
    slug='dolibarr-thirdparty-post-to-normalized',
    defaults={
        'name': 'Dolibarr Thirdparty POST -> Normalized Customer',
        'description': 'Extracts 21 fields from Dolibarr /societe/card.php POST and normalizes to cross-app customer event.',
        'source_endpoint': dolibarr_ep,
        'direction': MappingDirection.SOURCE_TO_NORMALIZED,
        'field_mappings': mapping1_fields,
        'transformations': [],
        'is_active': True,
    }
)
print(f"Mapping 1 (Dolibarr->Norm):    id={map1.id} {'CREATED' if created_m1 else 'EXISTS'}")

# --- Mapping 2: Normalized Customer -> Odoo res.partner ---
mapping2_fields = {
    "name": "payload.name",
    "email": "payload.email",
    "phone": "payload.phone",
    "mobile": "payload.fax|default:None",
    "street": "payload.street",
    "zip": "payload.zip",
    "city": "payload.city",
    "vat": "payload.vat",
    "website": "payload.url",
    "customer_rank": "payload.is_customer|int:1:0",
    "supplier_rank": "payload.is_vendor|int:1:0",
    "ref": "payload.customer_code|default:None",
    "_country_code": "payload.country_id",
    "is_company": "'True'|bool",
}

map2, created_m2 = Mapping.objects.get_or_create(
    slug='normalized-customer-to-odoo-partner',
    defaults={
        'name': 'Normalized Customer -> Odoo res.partner',
        'description': 'Transforms normalized customer event into 14 Odoo partner fields for XML-RPC sync.',
        'target_endpoint': odoo_ep,
        'direction': MappingDirection.NORMALIZED_TO_TARGET,
        'field_mappings': mapping2_fields,
        'transformations': [],
        'is_active': True,
    }
)
print(f"Mapping 2 (Norm->Odoo):        id={map2.id} {'CREATED' if created_m2 else 'EXISTS'}")

# --- Link Mappings to Instructions ---
im1, created_im1 = InstructionMapping.objects.get_or_create(
    instruction=instr_a,
    mapping=map1,
    defaults={'order': 1, 'enabled': True}
)
print(f"InstructionMapping A->M1:      id={im1.id} {'CREATED' if created_im1 else 'EXISTS'}")

im2, created_im2 = InstructionMapping.objects.get_or_create(
    instruction=instr_b,
    mapping=map2,
    defaults={'order': 1, 'enabled': True}
)
print(f"InstructionMapping B->M2:      id={im2.id} {'CREATED' if created_im2 else 'EXISTS'}")

# --- Verify ---
print(f"\n=== Verification (schema={SCHEMA}) ===")
all_instrs = Instruction.objects.all().values_list('id', 'requestpath', 'requestmethod', 'executescript')
for i in all_instrs:
    print(f"  Instruction {i[0]}: {i[2]} {i[1]} -> {i[3]}")

all_maps = Mapping.objects.all().values_list('id', 'slug', 'direction')
for m in all_maps:
    print(f"  Mapping {m[0]}: {m[1]} ({m[2]})")

all_ims = InstructionMapping.objects.select_related('instruction', 'mapping').all()
for im in all_ims:
    print(f"  Link: Instruction {im.instruction.id} -> Mapping {im.mapping.id} (order={im.order})")

print("\nDone.")
