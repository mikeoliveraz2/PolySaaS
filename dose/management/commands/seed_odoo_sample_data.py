"""
Seed a small realistic Odoo demo dataset for a tenant (customers, products, invoices).

Idempotent: re-running finds existing partners/products/invoices by stable keys
and skips or updates instead of duplicating.

Usage (laptop or office — same command):
    python manage.py seed_odoo_sample_data
    python manage.py seed_odoo_sample_data olient
    python manage.py seed_odoo_sample_data --schema olient
    python manage.py seed_odoo_sample_data --dry-run
"""
from __future__ import annotations

from types import SimpleNamespace

from django.core.management.base import BaseCommand
from django.db import connection

COMPANY_NAME = "Big Guys Wharehouse"
SEED_TAG = "polysaas-sample-seed"

CUSTOMERS = (
    {
        "name": "Lumber Supply Co",
        "email": "billing@lumbersupply.example",
        "phone": "+1 503 555 0140",
        "is_company": True,
        "street": "1200 Mill Road",
        "city": "Portland",
        "zip": "97201",
    },
    {
        "name": "Pacific Packing LLC",
        "email": "ap@pacificpacking.example",
        "phone": "+1 206 555 0188",
        "is_company": True,
        "street": "88 Harbor Ave",
        "city": "Seattle",
        "zip": "98134",
    },
    {
        "name": "River City Distributors",
        "email": "orders@rivercitydist.example",
        "phone": "+1 916 555 0112",
        "is_company": True,
        "street": "450 Warehouse Blvd",
        "city": "Sacramento",
        "zip": "95814",
    },
    {
        "name": "Ana Reyes",
        "email": "ana.reyes@lumbersupply.example",
        "phone": "+1 503 555 0141",
        "is_company": False,
        "street": "1200 Mill Road",
        "city": "Portland",
        "zip": "97201",
    },
    {
        "name": "Tom Hall",
        "email": "tom.hall@pacificpacking.example",
        "phone": "+1 206 555 0189",
        "is_company": False,
        "street": "88 Harbor Ave",
        "city": "Seattle",
        "zip": "98134",
    },
)

PRODUCTS = (
    {
        "name": "Pallet racking bay",
        "default_code": "PS-SEED-RACK",
        "list_price": 450.0,
    },
    {
        "name": "Stretch wrap (case)",
        "default_code": "PS-SEED-WRAP",
        "list_price": 68.5,
    },
    {
        "name": "Forklift safety kit",
        "default_code": "PS-SEED-SAFE",
        "list_price": 215.0,
    },
    {
        "name": "Warehouse labor (hour)",
        "default_code": "PS-SEED-LABOR",
        "list_price": 85.0,
    },
)

# Invoices keyed by client ref so re-seed is safe.
INVOICES = (
    {
        "ref": "PS-SEED-INV-001",
        "partner_email": "billing@lumbersupply.example",
        "invoice_date": "2026-08-12",
        "post": True,
        "lines": (
            {"code": "PS-SEED-RACK", "qty": 4, "price": 450.0},
            {"code": "PS-SEED-WRAP", "qty": 6, "price": 68.5},
        ),
    },
    {
        "ref": "PS-SEED-INV-002",
        "partner_email": "ap@pacificpacking.example",
        "invoice_date": "2026-08-18",
        "post": True,
        "lines": (
            {"code": "PS-SEED-SAFE", "qty": 2, "price": 215.0},
            {"code": "PS-SEED-LABOR", "qty": 8, "price": 85.0},
        ),
    },
    {
        "ref": "PS-SEED-INV-003",
        "partner_email": "orders@rivercitydist.example",
        "invoice_date": "2026-08-22",
        "post": True,
        "lines": (
            {"code": "PS-SEED-RACK", "qty": 2, "price": 450.0},
            {"code": "PS-SEED-LABOR", "qty": 3, "price": 85.0},
        ),
    },
    {
        "ref": "PS-SEED-INV-DRAFT",
        "partner_email": "billing@lumbersupply.example",
        "invoice_date": "2026-08-26",
        "post": False,
        "lines": (
            {"code": "PS-SEED-WRAP", "qty": 10, "price": 68.5},
        ),
    },
)

QUOTATIONS = (
    {
        "ref": "PS-SEED-SO-001",
        "partner_email": "ap@pacificpacking.example",
        "note": f"{SEED_TAG} draft quotation",
        "lines": (
            {"code": "PS-SEED-RACK", "qty": 6, "price": 450.0},
            {"code": "PS-SEED-SAFE", "qty": 1, "price": 215.0},
        ),
    },
)


class Command(BaseCommand):
    help = (
        "Seed Odoo with sample customers, products, invoices, and a quotation "
        f"(company name -> {COMPANY_NAME}). Safe to re-run."
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
            help="Optional schema_name override (e.g. olient)",
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
            self.stdout.write(f"  company -> {COMPANY_NAME}")
            self.stdout.write(f"  customers: {len(CUSTOMERS)}")
            self.stdout.write(f"  products: {len(PRODUCTS)}")
            self.stdout.write(f"  invoices: {len(INVOICES)}")
            self.stdout.write(f"  quotations: {len(QUOTATIONS)}")
            return

        client = OdooRpcClient.from_config(config)
        client.authenticate()

        company_id = self._ensure_company_name(client)
        product_ids = self._ensure_products(client)
        partner_ids = self._ensure_customers(client)
        invoice_ids = self._ensure_invoices(client, partner_ids, product_ids)
        quotation_ids = self._ensure_quotations(client, partner_ids, product_ids)

        self.stdout.write(self.style.SUCCESS("Sample data ready"))
        self.stdout.write(f"  company_id={company_id} name={COMPANY_NAME}")
        self.stdout.write(f"  partners={partner_ids}")
        self.stdout.write(f"  products={product_ids}")
        self.stdout.write(f"  invoices={invoice_ids}")
        self.stdout.write(f"  quotations={quotation_ids}")
        self.stdout.write(
            "Re-check Odoo home -> Invoices bookmark for the seeded customer invoices."
        )

    def _ensure_company_name(self, client) -> int:
        rows = client.execute_kw(
            "res.company",
            "search_read",
            [[]],
            {"fields": ["id", "name", "partner_id"], "limit": 5},
        )
        if not rows:
            raise RuntimeError("No res.company rows in this Odoo database")
        row = rows[0]
        company_id = int(row["id"])
        if (row.get("name") or "").strip() != COMPANY_NAME:
            client.execute_kw(
                "res.company",
                "write",
                [[company_id], {"name": COMPANY_NAME}],
            )
            self.stdout.write(f"  renamed company #{company_id} -> {COMPANY_NAME}")
        partner = row.get("partner_id")
        partner_id = partner[0] if isinstance(partner, (list, tuple)) and partner else None
        if partner_id:
            client.execute_kw(
                "res.partner",
                "write",
                [[int(partner_id)], {"name": COMPANY_NAME}],
            )
        leftovers = client.execute_kw(
            "res.partner",
            "search",
            [[["name", "=", "My Company"]]],
            {"limit": 20},
        )
        if leftovers:
            client.execute_kw(
                "res.partner",
                "write",
                [leftovers, {"name": COMPANY_NAME}],
            )
            self.stdout.write(f"  renamed leftover My Company partners {leftovers}")
        return company_id

    def _ensure_products(self, client) -> dict[str, int]:
        ids: dict[str, int] = {}
        for spec in PRODUCTS:
            code = spec["default_code"]
            existing = client.execute_kw(
                "product.product",
                "search",
                [[["default_code", "=", code]]],
                {"limit": 1},
            )
            if existing:
                pid = int(existing[0])
                client.execute_kw(
                    "product.product",
                    "write",
                    [[pid], {"name": spec["name"], "list_price": spec["list_price"]}],
                )
                ids[code] = pid
                self.stdout.write(f"  product exists {code} -> #{pid}")
                continue
            pid = int(
                client.execute_kw(
                    "product.product",
                    "create",
                    [
                        {
                            "name": spec["name"],
                            "default_code": code,
                            "list_price": spec["list_price"],
                            "type": "consu",
                            "sale_ok": True,
                        }
                    ],
                )
            )
            ids[code] = pid
            self.stdout.write(f"  product created {code} -> #{pid}")
        return ids

    def _ensure_customers(self, client) -> dict[str, int]:
        ids: dict[str, int] = {}
        for spec in CUSTOMERS:
            email = spec["email"]
            existing = client.execute_kw(
                "res.partner",
                "search",
                [[["email", "=", email]]],
                {"limit": 1},
            )
            vals = {
                "name": spec["name"],
                "email": email,
                "phone": spec["phone"],
                "is_company": bool(spec["is_company"]),
                "street": spec.get("street") or "",
                "city": spec.get("city") or "",
                "zip": spec.get("zip") or "",
                "comment": SEED_TAG,
                "customer_rank": 1,
            }
            if existing:
                pid = int(existing[0])
                client.execute_kw("res.partner", "write", [[pid], vals])
                ids[email] = pid
                self.stdout.write(f"  customer updated {spec['name']} -> #{pid}")
            else:
                pid = int(client.execute_kw("res.partner", "create", [vals]))
                ids[email] = pid
                self.stdout.write(f"  customer created {spec['name']} -> #{pid}")
        return ids

    def _ensure_invoices(self, client, partners: dict[str, int], products: dict[str, int]):
        ids = []
        for spec in INVOICES:
            ref = spec["ref"]
            partner_id = partners.get(spec["partner_email"])
            if not partner_id:
                self.stderr.write(self.style.WARNING(f"  skip invoice {ref}: missing partner"))
                continue
            existing = client.execute_kw(
                "account.move",
                "search",
                [[
                    ["move_type", "=", "out_invoice"],
                    ["ref", "=", ref],
                ]],
                {"limit": 1},
            )
            if existing:
                ids.append(int(existing[0]))
                self.stdout.write(f"  invoice exists {ref} -> #{existing[0]}")
                continue
            line_cmds = []
            for line in spec["lines"]:
                product_id = products.get(line["code"])
                line_vals = {
                    "name": line["code"],
                    "quantity": line["qty"],
                    "price_unit": line["price"],
                }
                if product_id:
                    line_vals["product_id"] = product_id
                line_cmds.append((0, 0, line_vals))
            move_id = int(
                client.execute_kw(
                    "account.move",
                    "create",
                    [
                        {
                            "move_type": "out_invoice",
                            "partner_id": partner_id,
                            "invoice_date": spec["invoice_date"],
                            "ref": ref,
                            "narration": SEED_TAG,
                            "invoice_line_ids": line_cmds,
                        }
                    ],
                )
            )
            if spec.get("post"):
                try:
                    client.execute_kw("account.move", "action_post", [[move_id]])
                except Exception as exc:
                    self.stderr.write(
                        self.style.WARNING(f"  invoice {ref} created draft; post failed: {exc}")
                    )
            ids.append(move_id)
            self.stdout.write(f"  invoice created {ref} -> #{move_id}")
        return ids

    def _ensure_quotations(self, client, partners: dict[str, int], products: dict[str, int]):
        ids = []
        for spec in QUOTATIONS:
            ref = spec["ref"]
            partner_id = partners.get(spec["partner_email"])
            if not partner_id:
                self.stderr.write(self.style.WARNING(f"  skip quotation {ref}: missing partner"))
                continue
            existing = client.execute_kw(
                "sale.order",
                "search",
                [[["client_order_ref", "=", ref]]],
                {"limit": 1},
            )
            if existing:
                ids.append(int(existing[0]))
                self.stdout.write(f"  quotation exists {ref} -> #{existing[0]}")
                continue
            line_cmds = []
            for line in spec["lines"]:
                product_id = products.get(line["code"])
                line_vals = {
                    "name": line["code"],
                    "product_uom_qty": line["qty"],
                    "price_unit": line["price"],
                }
                if product_id:
                    line_vals["product_id"] = product_id
                line_cmds.append((0, 0, line_vals))
            order_id = int(
                client.execute_kw(
                    "sale.order",
                    "create",
                    [
                        {
                            "partner_id": partner_id,
                            "client_order_ref": ref,
                            "origin": SEED_TAG,
                            "note": spec.get("note") or SEED_TAG,
                            "order_line": line_cmds,
                        }
                    ],
                )
            )
            ids.append(order_id)
            self.stdout.write(f"  quotation created {ref} -> #{order_id}")
        return ids
