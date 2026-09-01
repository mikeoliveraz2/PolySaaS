# THIS CODE IS FROZEN — NO CHANGES TO THIS CODE ARE ALLOWED WITHOUT THE OWNER'S PERMISSION
# BINGO: Unified Endpoint Workspace — 2026-09-01

"""The one data envelope every endpoint panel renders from.

Odoo returned ``invoices``, HubSpot portlets returned ``rows``, and the browser
compensated with ``resolveListKind()`` plus a hand-written table builder per
shape. Normalizing here means a panel is described by its columns rather than
by which vendor produced it.

Built at the publisher layer, not inside the Atomic Services, so the services
stay the source of raw data and this stays the source of presentation.
"""
from __future__ import annotations

VALID_STATUSES = ("success", "error")
VALID_FORMATS = ("text", "money", "number", "date")

# Formats the browser right-aligns (the existing ``is-num`` cell class).
_NUMERIC_FORMATS = ("money", "number")


def _column(key, label, fmt="text", blank="—", fallback_key="", fallback_prefix="", note_key=""):
    column = {"key": key, "label": label, "format": fmt, "blank": blank}
    if fallback_key:
        column["fallback"] = {"key": fallback_key, "prefix": fallback_prefix}
    if note_key:
        column["note_key"] = note_key
    column["numeric"] = fmt in _NUMERIC_FORMATS
    return column


# Column sets transcribed from the three table builders they replace. Odoo and
# HubSpot already emit identical row keys for contacts and sales, so object_type
# is enough to describe a panel regardless of which vendor filled it.
COLUMN_CATALOG = {
    "invoice": (
        _column("name", "Invoice", fallback_key="id", fallback_prefix="#"),
        _column("partner_name", "Customer", blank=""),
        _column("invoice_date", "Date", fmt="date"),
        _column("amount_total", "Total", fmt="money"),
        _column("state", "State", blank=""),
        _column("payment_state", "Payment", blank=""),
    ),
    "contact": (
        _column("name", "Name", fallback_key="id", fallback_prefix="#"),
        _column("email", "Email"),
        _column("phone", "Phone"),
        _column("parent_name", "Company"),
        _column("id", "Id", fmt="number"),
    ),
    "sale": (
        _column("name", "Deal / Order", fallback_key="id", fallback_prefix="#", note_key="note"),
        _column("partner_name", "Customer", blank=""),
        _column("amount_total", "Amount", fmt="money"),
        _column("state", "Stage", blank=""),
        _column("date_order", "Created", fmt="date"),
    ),
}

_OBJECT_META = {
    "invoice": {
        "title": "Invoices",
        "noun": "invoice",
        "legacy_key": "invoices",
        "empty": "No customer invoices were returned. "
                 "The CallBackData row was still saved with count 0.",
    },
    "contact": {
        "title": "Contacts",
        "noun": "contact",
        "legacy_key": "contacts",
        "empty": "No customer contacts were returned. "
                 "The CallBackData row was still saved with count 0.",
    },
    "sale": {
        "title": "Sales",
        "noun": "sale",
        "legacy_key": "sales",
        "empty": "No sales orders were returned. "
                 "The CallBackData row was still saved with count 0.",
    },
}


def object_meta(object_type):
    """Title/noun/legacy-key metadata for a known object type."""
    return dict(_OBJECT_META.get(object_type) or {})


def columns_for(object_type):
    """Column definitions for an object type; empty tuple when unknown."""
    return tuple(dict(col) for col in COLUMN_CATALOG.get(object_type, ()))


def legacy_key_for(object_type):
    """Deprecated per-vendor rows key kept as an alias for one release."""
    return (_OBJECT_META.get(object_type) or {}).get("legacy_key", "rows")


def columns_from_rows(rows, exclude=("id",)):
    """Derive columns from row keys, for panels with no curated column set.

    Used by the HubSpot portlets, whose object types are open-ended. Labels
    stay as the raw key so the rendered table matches what it replaced.
    """
    first = None
    for row in rows or []:
        if isinstance(row, dict):
            first = row
            break
    if not first:
        return []
    skip = set(exclude or ())
    return [_column(key, key) for key in first.keys() if key not in skip]


def build_envelope(
    object_type,
    status="success",
    rows=None,
    title="",
    detail="",
    error=None,
    columns=None,
    empty_message="",
):
    """Assemble the standard envelope.

    ``rows`` is always a list and ``count`` always an int, so a consumer never
    has to guard the empty and error cases differently from the populated one.
    """
    meta = _OBJECT_META.get(object_type) or {}
    safe_rows = list(rows) if isinstance(rows, (list, tuple)) else []
    resolved_columns = (
        [dict(col) for col in columns] if columns else list(columns_for(object_type))
    )
    return {
        "status": status if status in VALID_STATUSES else "error",
        "title": title or meta.get("title") or (object_type or "Results").title(),
        "object_type": object_type or "",
        "count": len(safe_rows),
        "columns": resolved_columns,
        "rows": safe_rows,
        "empty_message": empty_message or meta.get("empty") or "Nothing was returned.",
        "detail": detail,
        "error": error,
    }


def error_envelope(object_type, detail, error="error", title=""):
    """Error envelope: same shape, zero rows, columns still present."""
    return build_envelope(
        object_type,
        status="error",
        rows=[],
        title=title,
        detail=detail,
        error=error or "error",
    )


def count_detail(object_type, count):
    """`3 invoices saved to CallBackData` with correct pluralization."""
    noun = (_OBJECT_META.get(object_type) or {}).get("noun") or "record"
    plural = "" if count == 1 else "s"
    return f"{count} {noun}{plural} saved to CallBackData"


def validate_envelope(envelope):
    """Return a list of contract violations; empty list means valid."""
    problems = []
    if not isinstance(envelope, dict):
        return ["envelope is not a dict"]

    status = envelope.get("status")
    if status not in VALID_STATUSES:
        problems.append(f"status must be one of {VALID_STATUSES}, got {status!r}")

    if not isinstance(envelope.get("title"), str) or not envelope.get("title"):
        problems.append("title must be a non-empty string")

    rows = envelope.get("rows")
    if not isinstance(rows, list):
        problems.append("rows must be a list")
        rows = []

    count = envelope.get("count")
    if not isinstance(count, int) or isinstance(count, bool):
        problems.append("count must be an int")
    elif count != len(rows):
        problems.append(f"count {count} does not match {len(rows)} rows")

    columns = envelope.get("columns")
    if not isinstance(columns, list):
        problems.append("columns must be a list")
    else:
        for index, column in enumerate(columns):
            if not isinstance(column, dict):
                problems.append(f"column {index} is not a dict")
                continue
            if not column.get("key"):
                problems.append(f"column {index} is missing key")
            if not column.get("label"):
                problems.append(f"column {index} is missing label")
            fmt = column.get("format")
            if fmt not in VALID_FORMATS:
                problems.append(f"column {index} format {fmt!r} not in {VALID_FORMATS}")

    if status == "error" and not envelope.get("error"):
        problems.append("error status requires a non-empty error code")
    if status == "error" and rows:
        problems.append("error status must not carry rows")

    return problems
