#!/usr/bin/env python3
"""
SNMP week feed — push mock telemetry into PolySaaS generic inbound webhook.

Week 1 / Week 2 are *data scenarios*, not calendar waits. Run them back-to-back:

    python scripts/snmp_week_feed.py --week 1 --tenant polysaas
    python scripts/snmp_week_feed.py --week 2 --tenant polysaas

Defaults target Hostinger production. Override with --url for local/dev.
"""
from __future__ import annotations

import argparse
import json
import sys
import time
import urllib.error
import urllib.request
from datetime import datetime, timezone

DEFAULT_BASE = "https://app.prod-polysaas.cloud"
DEVICE_COUNT = 20
# Week 2: deterministic anomalies (~15%) — indices 2, 7, 14 → Core-Switch-03, Edge-AP-08, IoT-GW-15
WEEK2_ANOMALY_INDEXES = {2, 7, 14}


def _mac(i: int) -> str:
    # Stable demo MACs so Week 2 upserts the same equipment
    return f"00:1A:2B:3C:{i:02X}:{(i * 17) % 256:02X}"


def _name(i: int) -> str:
    families = ("Core-Switch", "Edge-AP", "IoT-GW", "Access-SW", "WLAN-Ctrl")
    return f"{families[i % len(families)]}-{i + 1:02d}"


def _ip(i: int) -> str:
    return f"192.168.{1 + (i // 20)}.{10 + i}"


def build_payload(i: int, week: int) -> dict:
    mac = _mac(i)
    name = _name(i)
    ts = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    if week == 1:
        metrics = {"status": "up", "cpu_utilization": 30 + (i % 40), "temperature_c": 32 + (i % 12)}
    elif i in WEEK2_ANOMALY_INDEXES:
        # Mix of down + critical temp for film variety
        if i == 7:
            metrics = {"status": "down", "cpu_utilization": 0, "temperature_c": 22}
        else:
            metrics = {"status": "up", "cpu_utilization": 88 + (i % 5), "temperature_c": 64 + (i % 8)}
    else:
        metrics = {"status": "up", "cpu_utilization": 28 + (i % 35), "temperature_c": 34 + (i % 10)}

    return {
        "event_id": f"snmp-w{week}-{i + 1:02d}-{mac.replace(':', '')[-6:]}",
        "timestamp": ts,
        "device_mac": mac,
        "device_name": name,
        "ip_address": _ip(i),
        "metrics": metrics,
        "week": week,
    }


def post_json(url: str, payload: dict, timeout: float = 30.0) -> tuple[int, str]:
    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        url,
        data=data,
        headers={"Content-Type": "application/json", "Accept": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            body = resp.read().decode("utf-8", errors="replace")
            return resp.status, body
    except urllib.error.HTTPError as exc:
        body = exc.read().decode("utf-8", errors="replace") if exc.fp else str(exc)
        return exc.code, body
    except Exception as exc:
        return 0, str(exc)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Push mock SNMP week feed to PolySaaS")
    parser.add_argument("--week", type=int, choices=(1, 2), required=True, help="1=baseline, 2=anomaly")
    parser.add_argument("--tenant", default="polysaas", help="Tenant slug in webhook URL")
    parser.add_argument(
        "--url",
        default="",
        help="Full webhook URL (default: {base}/dose/webhook/snmp/{tenant}/)",
    )
    parser.add_argument("--base", default=DEFAULT_BASE, help="Host base when --url omitted")
    parser.add_argument("--devices", type=int, default=DEVICE_COUNT, help="Device count (default 20)")
    parser.add_argument("--delay", type=float, default=0.15, help="Seconds between POSTs")
    parser.add_argument("--dry-run", action="store_true", help="Print payloads only")
    parser.add_argument("--limit", type=int, default=0, help="Only first N devices (0=all)")
    args = parser.parse_args(argv)

    url = (args.url or "").strip() or f"{args.base.rstrip('/')}/dose/webhook/snmp/{args.tenant}/"
    count = args.devices
    if args.limit and args.limit > 0:
        count = min(count, args.limit)

    print(f"Week {args.week} -> {url}")
    print(f"Devices: {count}" + (f" (anomalies at indexes {sorted(WEEK2_ANOMALY_INDEXES)})" if args.week == 2 else ""))

    ok = 0
    fail = 0
    anomalies = 0
    for i in range(count):
        payload = build_payload(i, args.week)
        if payload["metrics"].get("status") == "down" or float(payload["metrics"].get("temperature_c") or 0) >= 60:
            anomalies += 1
        if args.dry_run:
            print(json.dumps(payload))
            ok += 1
            continue
        status, body = post_json(url, payload)
        brief = body[:180].replace("\n", " ")
        flag = "OK" if 200 <= status < 300 else "FAIL"
        if flag == "OK":
            ok += 1
        else:
            fail += 1
        print(f"  [{flag}] {payload['device_name']} {payload['device_mac']} status={payload['metrics']['status']} http={status} {brief}")
        if args.delay:
            time.sleep(args.delay)

    print(f"\nDone: ok={ok} fail={fail} anomaly_payloads={anomalies}")
    if args.week == 1:
        print("Next: python scripts/snmp_week_feed.py --week 2 --tenant", args.tenant)
    return 0 if fail == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
