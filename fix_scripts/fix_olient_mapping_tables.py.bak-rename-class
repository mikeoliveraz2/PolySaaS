"""
Create the dose_mapping and dose_instructionmapping tables in the olient schema,
then seed the cross-app sync Instructions, Mappings, and InstructionMappings.
"""
import os, sys
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mysite.settings')
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

import django
django.setup()

from django.db import connection
from dose.models import Instruction, PassThroughEndpoint
from dose.models.mapping import Mapping, InstructionMapping, MappingDirection

SCHEMA = 'olient'

# --- Step 1: Check which tables are missing in olient ---
with connection.cursor() as cur:
    cur.execute(
        "SELECT tablename FROM pg_tables WHERE schemaname = %s AND tablename IN ('dose_mapping','dose_instructionmapping')",
        [SCHEMA]
    )
    existing = [r[0] for r in cur.fetchall()]

print(f"Tables in {SCHEMA}: {existing}")

if 'dose_mapping' not in existing:
    print("Creating dose_mapping in olient...")
    with connection.cursor() as cur:
        cur.execute(f"""
            CREATE TABLE {SCHEMA}.dose_mapping (
                id SERIAL PRIMARY KEY,
                name VARCHAR(200) NOT NULL,
                slug VARCHAR(120) NOT NULL,
                description TEXT NOT NULL DEFAULT '',
                source_endpoint_id INTEGER REFERENCES {SCHEMA}.dose_passthroughendpoint(id) ON DELETE SET NULL,
                target_endpoint_id INTEGER REFERENCES {SCHEMA}.dose_passthroughendpoint(id) ON DELETE SET NULL,
                direction VARCHAR(25) NOT NULL DEFAULT 'SOURCE_TO_NORMALIZED',
                field_mappings JSONB NOT NULL DEFAULT '{{}}'::jsonb,
                transformations JSONB NOT NULL DEFAULT '[]'::jsonb,
                version SMALLINT NOT NULL DEFAULT 1,
                is_active BOOLEAN NOT NULL DEFAULT TRUE,
                created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
                updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
                UNIQUE(slug, direction)
            );
        """)
    print("  OK: dose_mapping created")
else:
    print("  dose_mapping already exists")

if 'dose_instructionmapping' not in existing:
    print("Creating dose_instructionmapping in olient...")
    with connection.cursor() as cur:
        cur.execute(f"""
            CREATE TABLE {SCHEMA}.dose_instructionmapping (
                id SERIAL PRIMARY KEY,
                instruction_id INTEGER NOT NULL REFERENCES {SCHEMA}.dose_instruction(id) ON DELETE CASCADE,
                mapping_id INTEGER NOT NULL REFERENCES {SCHEMA}.dose_mapping(id) ON DELETE RESTRICT,
                "order" SMALLINT NOT NULL DEFAULT 1,
                enabled BOOLEAN NOT NULL DEFAULT TRUE,
                UNIQUE(instruction_id, mapping_id)
            );
        """)
    print("  OK: dose_instructionmapping created")
else:
    print("  dose_instructionmapping already exists")

# Mark migration as applied so future migrate_all_schemas doesn't try again
with connection.cursor() as cur:
    cur.execute(f"SET search_path TO {SCHEMA},public;")
    cur.execute(
        "SELECT 1 FROM django_migrations WHERE app='dose' AND name='0025_add_mapping_and_instruction_mapping'"
    )
    if not cur.fetchone():
        cur.execute(
            "INSERT INTO django_migrations (app, name, applied) VALUES ('dose', '0025_add_mapping_and_instruction_mapping', NOW())"
        )
        print("  Marked migration 0025 as applied in olient")

# --- Step 2: Set search_path and seed data ---
with connection.cursor() as cur:
    cur.execute(f"SET search_path TO {SCHEMA},public;")
print(f"\nsearch_path set to {SCHEMA},public")

dolibarr_ep = PassThroughEndpoint.objects.filter(trigger_path__icontains='dolibarr').first()
odoo_ep = PassThroughEndpoint.objects.filter(trigger_path__icontains='odoo').first()
print(f"Dolibarr endpoint: id={dolibarr_ep.id if dolibarr_ep else None}")
print(f"Odoo endpoint:     id={odoo_ep.id if odoo_ep else None}")

# Instruction A
instr_a, ca = Instruction.objects.get_or_create(
    requestpath='/societe/card.php', requestmethod='POST',
    defaults={
        'direction': 'REQ',
        'executescript': 'EndpointDataExtractorService',
        'eventKey': 'dolibarr.customer.created',
        'save_callbackdata': True,
        'description': 'Captures Dolibarr new third-party form POST, extracts fields via Mapping, publishes to RabbitMQ.',
    }
)
print(f"Instruction A: id={instr_a.id} {'CREATED' if ca else 'EXISTS'}")

# Instruction B
instr_b, cb = Instruction.objects.get_or_create(
    requestpath='/mq/polysaas.crossapp.customer.created', requestmethod='POST',
    defaults={
        'direction': 'REQ',
        'executescript': 'OdooCustomerSyncService',
        'eventKey': 'sync.customer.dolibarr.to.odoo',
        'save_callbackdata': True,
        'description': 'Triggered by MQQueueMonitor when a customer message arrives. Maps normalized data to Odoo partner fields and syncs via XML-RPC.',
    }
)
print(f"Instruction B: id={instr_b.id} {'CREATED' if cb else 'EXISTS'}")

# Mapping 1
map1, cm1 = Mapping.objects.get_or_create(
    slug='dolibarr-thirdparty-post-to-normalized',
    defaults={
        'name': 'Dolibarr Thirdparty POST -> Normalized Customer',
        'description': 'Extracts 21 fields from Dolibarr /societe/card.php POST and normalizes to cross-app customer event.',
        'source_endpoint': dolibarr_ep,
        'direction': MappingDirection.SOURCE_TO_NORMALIZED,
        'field_mappings': {
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
        },
        'transformations': [],
        'is_active': True,
    }
)
print(f"Mapping 1:     id={map1.id} {'CREATED' if cm1 else 'EXISTS'}")

# Mapping 2
map2, cm2 = Mapping.objects.get_or_create(
    slug='normalized-customer-to-odoo-partner',
    defaults={
        'name': 'Normalized Customer -> Odoo res.partner',
        'description': 'Transforms normalized customer event into 14 Odoo partner fields for XML-RPC sync.',
        'target_endpoint': odoo_ep,
        'direction': MappingDirection.NORMALIZED_TO_TARGET,
        'field_mappings': {
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
        },
        'transformations': [],
        'is_active': True,
    }
)
print(f"Mapping 2:     id={map2.id} {'CREATED' if cm2 else 'EXISTS'}")

# Link them
im1, ci1 = InstructionMapping.objects.get_or_create(
    instruction=instr_a, mapping=map1,
    defaults={'order': 1, 'enabled': True}
)
print(f"Link A->M1:    id={im1.id} {'CREATED' if ci1 else 'EXISTS'}")

im2, ci2 = InstructionMapping.objects.get_or_create(
    instruction=instr_b, mapping=map2,
    defaults={'order': 1, 'enabled': True}
)
print(f"Link B->M2:    id={im2.id} {'CREATED' if ci2 else 'EXISTS'}")

# Verify
print(f"\n=== Verification ({SCHEMA}) ===")
for i in Instruction.objects.all():
    print(f"  Instruction {i.id}: {i.requestmethod} {i.requestpath} -> {i.executescript}")
for m in Mapping.objects.all():
    print(f"  Mapping {m.id}: {m.slug} ({m.direction})")
for im in InstructionMapping.objects.select_related('instruction', 'mapping').all():
    print(f"  Link: Instruction {im.instruction.id} -> Mapping {im.mapping.id} (order={im.order})")

print("\nDone.")
