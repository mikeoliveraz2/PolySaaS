"""Locked PolySniffer architecture contracts.

These tests intentionally report current production violations. They do not
select or enforce an isolation mechanism.
"""
from pathlib import Path
import re

from django.urls import Resolver404, resolve
from django.test import SimpleTestCase


REPO_ROOT = Path(__file__).resolve().parents[2]


def _source(path):
    return (REPO_ROOT / path).read_text(encoding="utf-8")


def _matches(path, patterns):
    findings = []
    for line_number, line in enumerate(_source(path).splitlines(), start=1):
        if any(re.search(pattern, line) for pattern in patterns):
            findings.append(f"{path}:{line_number}: {line.strip()}")
    return findings


class PolySnifferLockedArchitectureTests(SimpleTestCase):
    def test_polysniffer_is_not_mounted_on_the_dose_surface(self):
        findings = _matches(
            "dose/urls.py",
            [r"path\(['\"]sniff/['\"].*dose\.polysniffer\.sniff_urls"],
        )

        self.assertEqual(
            findings,
            [],
            "PolySniffer must exist only under Admin; remove the DOSE mount:\n"
            + "\n".join(findings),
        )

    def test_pt_dose_bare_id_is_not_a_polysniffer_entry(self):
        try:
            match = resolve("/pt/dose/17")
        except Resolver404:
            return
        route_name = match.url_name or ""
        namespace = match.namespace or ""

        self.assertFalse(
            route_name.startswith("polysniffer") or "polysniffer" in namespace,
            "/pt/dose/17 is production DOSE passthrough, never a PolySniffer entry",
        )

    def test_admin_polysniffer_routes_use_endpoint_strings_not_endpoint_ids(self):
        findings = _matches(
            "dose/polysniffer/urls.py",
            [r"<int:endpoint_id>", r"<int:.*endpoint.*id>"],
        )
        findings = [finding for finding in findings if "assertNotIn" not in finding]

        self.assertEqual(
            findings,
            [],
            "Admin PolySniffer routes must use the endpoint string, never a PK:\n"
            + "\n".join(findings),
        )

    def test_polysniffer_identity_artifacts_do_not_encode_endpoint_ids(self):
        checks = {
            "dose/polysniffer/structured_capture.py": [
                r"['\"]endpoint_id['\"]\s*:",
                r"endpoint\.id\b",
                r"endpoint\.pk\b",
            ],
            "dose/management/commands/capture_polysniffer_browser.py": [
                r"--endpoint-id\b",
                r"endpoint_id\b",
            ],
            "dose/polysniffer/browser_capture.py": [
                r"['\"]endpoint_id['\"]\s*:",
                r"endpoint\.id\b",
                r"endpoint\.pk\b",
            ],
            "dose/polysniffer/sniff_session.py": [
                r"polysniffer_ep",
                r"endpoint_id=",
                r"ep\{endpoint_id\}",
            ],
            "dose/polysniffer/sniff_session_utils.py": [
                r"polysniffer_ep",
                r"endpoint_id=",
                r"ep\{endpoint_id\}",
            ],
        }
        findings = []
        for path, patterns in checks.items():
            findings.extend(_matches(path, patterns))

        self.assertEqual(
            findings,
            [],
            "PolySniffer identity artifacts must encode endpoint strings only:\n"
            + "\n".join(findings),
        )

    def test_polysniffer_happy_path_tests_do_not_use_numeric_endpoint_urls(self):
        findings = _matches(
            "dose/tests/test_polysniffer_architecture.py",
            [
                r"/dose/sniff/",
                r"/admin/polysniffer/[^'\"]*/\d+(?:/|['\"])",
                r"/pt/dose/\d+(?:/|['\"])",
            ],
        )
        findings = [finding for finding in findings if "assertNotIn" not in finding]

        self.assertEqual(
            findings,
            [],
            "PolySniffer happy paths must use Admin endpoint-host URLs; /dose/ "
            "and numeric examples belong only in explicit rejection tests:\n"
            + "\n".join(findings),
        )

    def test_native_path_has_no_handler_processor_or_rewrite_dependency(self):
        findings = _matches(
            "dose/polysniffer/sniff_forward.py",
            [
                r"dose\.passthrough\.registry",
                r"resolve_handler",
                r"processor",
                r"sniff_native_rewrite",
                r"rewrite_(?:html|string|body|response)",
            ],
        )

        self.assertEqual(
            findings,
            [],
            "Native must not call handler registries, endpoint processors, or "
            "HTML/string rewrite helpers. Current call sites:\n"
            + "\n".join(findings),
        )

    def test_pt_admin_is_a_production_handler_route_not_polysniffer_identity(self):
        match = resolve("/pt/admin/example.test/web")
        route_name = match.url_name or ""
        namespace = match.namespace or ""

        self.assertNotIn(
            "polysniffer",
            f"{namespace}:{route_name}".lower(),
            "/pt/admin/<host> may exercise an installed production handler but "
            "must never resolve as PolySniffer identity",
        )
