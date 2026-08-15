"""Prove OdooCreatePartner: hard-coded payload → res.partner in tenant Odoo.

Does not print passwords. Not part of the product; run by hand.
  python tmp/_prove_odoo_create_partner.py
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "mysite.settings")

import django

django.setup()

from types import SimpleNamespace

from dose.services.odoo_create_partner import OdooCreatePartner
from dose.services.odoo_rpc import OdooRpcClient, load_odoo_rpc_config, public_config

SCHEMA = "pso17"
PAYLOAD = {
    "name": "PolySaaS Slack Demo Partner",
    "email": "polysaas.slack.demo.partner@example.com",
    "phone": "+1-555-0100",
}


def main():
    # Isolation prove uses Django settings (ODOO_SHARED_DB + XML-RPC admin).
    # pso17 TenantApp extra_config.odoo_db is odoo_pso17, which this local
    # Odoo instance does not have — do not overlay that here.
    request = SimpleNamespace(
        mq_message_data=PAYLOAD,
        body=b"",
        tenant=None,
        atomic_parameters=[],
        user=None,
        path="/prove/odoo-create-partner",
        method="POST",
    )

    result = OdooCreatePartner.execute_and_save(request, None)
    safe = {k: v for k, v in result.items() if k not in ("password", "odoo_password")}
    print("service_result", safe)

    if result.get("status") != "success":
        print("FAIL: service did not succeed")
        sys.exit(1)

    partner_id = result.get("partner_id")
    config = load_odoo_rpc_config(request=request)
    print("odoo_config", public_config(config))
    client = OdooRpcClient.from_config(config)
    client.authenticate()
    rows = client.execute_kw(
        "res.partner",
        "read",
        [[partner_id]],
        {"fields": ["id", "name", "email", "phone", "customer_rank", "is_company"]},
    )
    print("odoo_row", rows)
    print("transport", client.transport)
    if not rows or rows[0].get("email") != PAYLOAD["email"]:
        print("FAIL: partner row mismatch")
        sys.exit(1)
    print("OK partner_id=%s name=%s email=%s created=%s" % (
        partner_id,
        rows[0].get("name"),
        rows[0].get("email"),
        result.get("created"),
    ))


if __name__ == "__main__":
    main()
