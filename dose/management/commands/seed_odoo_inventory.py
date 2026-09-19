"""
Seed ~10 on-hand inventory rows in Odoo 18 (storable products + stock.quant).

Uses the same tenant / OdooRpcClient path as seed_odoo_sample_data.
Idempotent: re-run updates inventory quantities for PS-INV-* products.

Usage:
    python manage.py seed_odoo_inventory
    python manage.py seed_odoo_inventory polysaas
    python manage.py seed_odoo_inventory --schema polysaas
    python manage.py seed_odoo_inventory --dry-run
"""
from __future__ import annotations

from types import SimpleNamespace

from django.core.management.base import BaseCommand
from django.db import connection

SEED_TAG = "polysaas-inventory-seed"

# Ten storable SKUs with on-hand qty (Inventory → Products / Locations).
INVENTORY_ITEMS = (
    {"code": "PS-INV-01", "name": "Pine 2x4 stud (bundle)", "qty": 120.0, "list_price": 48.0},
    {"code": "PS-INV-02", "name": "Plywood 4x8 sheet", "qty": 85.0, "list_price": 32.5},
    {"code": "PS-INV-03", "name": "Deck screw box (500)", "qty": 200.0, "list_price": 14.9},
    {"code": "PS-INV-04", "name": "Safety cone (each)", "qty": 40.0, "list_price": 9.5},
    {"code": "PS-INV-05", "name": "Stretch wrap roll", "qty": 60.0, "list_price": 22.0},
    {"code": "PS-INV-06", "name": "Pallet jack", "qty": 6.0, "list_price": 420.0},
    {"code": "PS-INV-07", "name": "Hard hat (each)", "qty": 75.0, "list_price": 18.0},
    {"code": "PS-INV-08", "name": "Work glove pair", "qty": 150.0, "list_price": 6.5},
    {"code": "PS-INV-09", "name": "Cable tie pack", "qty": 90.0, "list_price": 5.25},
    {"code": "PS-INV-10", "name": "Warehouse bin (large)", "qty": 35.0, "list_price": 28.0},
)


class Command(BaseCommand):
    help = (
        "Seed Odoo Inventory with 10 storable products and on-hand quantities. "
        "Safe to re-run."
    )

    def add_arguments(self, parser):
        parser.add_argument(
            "tenant_slug",
            nargs="?",
            default="olient",
            help="Tenant slug (default: olient)",
        )
        parser.add_argument(
            "--schema",
            default="",
            help="Optional schema_name override (e.g. polysaas)",
        )
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Print planned writes without calling Odoo",
        )

    def handle(self, *args, **options):
        from dose.models import Tenant
        from dose.services.odoo_rpc import OdooRpcClient, load_odoo_rpc_config, public_config

        slug = (options["tenant_slug"] or "olient").strip()
        schema_override = (options["schema"] or "").strip()
        dry_run = bool(options["dry_run"])

        with connection.cursor() as cur:
            cur.execute("SET search_path TO public")

        tenant = None
        if schema_override:
            tenant = Tenant.objects.filter(schema_name=schema_override).first()
        if tenant is None:
            tenant = Tenant.objects.filter(slug=slug).first()
        if tenant is None:
            tenant = Tenant.objects.filter(schema_name=slug).first()
        if tenant is None:
            self.stderr.write(self.style.ERROR(f"Tenant not found: {slug}"))
            return

        with connection.cursor() as cur:
            cur.execute(f'SET search_path TO "{tenant.schema_name}", public')

        request = SimpleNamespace(tenant=tenant, atomic_parameters=[])
        config = load_odoo_rpc_config(request=request)
        pub = public_config(config)
        self.stdout.write(
            f"Tenant: {tenant.name} (schema={tenant.schema_name}) "
            f"Odoo db={pub.get('db')} url={pub.get('url')}"
        )
        if dry_run:
            self.stdout.write(self.style.WARNING("DRY RUN — no Odoo writes"))
            for item in INVENTORY_ITEMS:
                self.stdout.write(
                    f"  {item['code']}: {item['name']} qty={item['qty']}"
                )
            return

        client = OdooRpcClient.from_config(config)
        client.authenticate()

        location_id = self._stock_location_id(client)
        self.stdout.write(f"  stock location #{location_id}")

        applied = []
        for item in INVENTORY_ITEMS:
            product_id = self._ensure_storable_product(client, item)
            quant_id = self._apply_on_hand(client, product_id, location_id, item["qty"])
            applied.append(
                {
                    "code": item["code"],
                    "product_id": product_id,
                    "quant_id": quant_id,
                    "qty": item["qty"],
                }
            )
            self.stdout.write(
                f"  {item['code']} product=#{product_id} quant=#{quant_id} "
                f"on_hand={item['qty']}"
            )

        self.stdout.write(self.style.SUCCESS(
            f"Inventory sample ready ({len(applied)} products with stock)"
        ))
        self.stdout.write(
            "Re-check Odoo → Inventory → Products / Locations for PS-INV-01..10."
        )

    def _stock_location_id(self, client) -> int:
        # Prefer classic WH/Stock internal location.
        rows = client.execute_kw(
            "stock.location",
            "search_read",
            [[["usage", "=", "internal"], ["complete_name", "ilike", "WH/Stock"]]],
            {"fields": ["id", "complete_name"], "limit": 1},
        )
        if not rows:
            rows = client.execute_kw(
                "stock.location",
                "search_read",
                [[["usage", "=", "internal"]]],
                {"fields": ["id", "complete_name"], "limit": 1, "order": "id asc"},
            )
        if not rows:
            raise RuntimeError(
                "No internal stock.location found — is the Inventory (stock) app installed?"
            )
        return int(rows[0]["id"])

    def _product_field_names(self, client) -> set[str]:
        fields = client.execute_kw("product.product", "fields_get", [], {"attributes": ["type"]})
        return set(fields.keys()) if isinstance(fields, dict) else set()

    def _ensure_storable_product(self, client, item: dict) -> int:
        code = item["code"]
        existing = client.execute_kw(
            "product.product",
            "search",
            [[["default_code", "=", code]]],
            {"limit": 1},
        )
        field_names = self._product_field_names(client)
        # Odoo 18: type is consu/service; is_storable tracks Inventory qty.
        vals = {
            "name": item["name"],
            "default_code": code,
            "list_price": item["list_price"],
            "sale_ok": True,
            "purchase_ok": True,
            "description_sale": SEED_TAG,
        }
        if "is_storable" in field_names:
            vals["type"] = "consu"
            vals["is_storable"] = True
        elif "type" in field_names:
            vals["type"] = "product"  # Odoo ≤16 storable
        if "tracking" in field_names:
            vals["tracking"] = "none"

        if existing:
            pid = int(existing[0])
            client.execute_kw("product.product", "write", [[pid], vals])
            return pid

        return int(client.execute_kw("product.product", "create", [vals]))

    def _apply_on_hand(self, client, product_id: int, location_id: int, qty: float) -> int:
        existing = client.execute_kw(
            "stock.quant",
            "search",
            [[
                ["product_id", "=", product_id],
                ["location_id", "=", location_id],
            ]],
            {"limit": 1},
        )
        if existing:
            quant_id = int(existing[0])
            client.execute_kw(
                "stock.quant",
                "write",
                [[quant_id], {"inventory_quantity": qty}],
            )
        else:
            quant_id = int(
                client.execute_kw(
                    "stock.quant",
                    "create",
                    [{
                        "product_id": product_id,
                        "location_id": location_id,
                        "inventory_quantity": qty,
                    }],
                )
            )

        # Odoo 17/18 inventory adjustment apply
        try:
            client.execute_kw(
                "stock.quant",
                "action_apply_inventory",
                [[quant_id]],
            )
        except Exception as exc:
            # Some builds need inventory_quantity_set before apply
            try:
                client.execute_kw(
                    "stock.quant",
                    "write",
                    [[quant_id], {"inventory_quantity": qty, "inventory_quantity_set": True}],
                )
                client.execute_kw(
                    "stock.quant",
                    "action_apply_inventory",
                    [[quant_id]],
                )
            except Exception:
                raise RuntimeError(
                    f"Could not apply inventory for product #{product_id} "
                    f"quant #{quant_id}: {exc}"
                ) from exc
        return quant_id
