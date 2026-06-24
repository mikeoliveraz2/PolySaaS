"""PolySniffer 2.0 unit tests."""
# THIS CODE IS FROZEN — NO CHANGES TO THIS CODE ARE ALLOWED WITHOUT THE OWNER'S PERMISSION
# BINGO: PolySniffer 2.0 — 2026-06-24
from django.test import SimpleTestCase

from dose.polysniffer.har_capture import body_hash, build_har_entry, truncate_text


class PolySnifferV2HarCaptureTests(SimpleTestCase):
    def test_truncate_text(self):
        self.assertEqual(truncate_text('abc', 10), 'abc')
        long = 'x' * 20
        out = truncate_text(long, 10)
        self.assertTrue(out.endswith('[TRUNCATED]'))
        self.assertEqual(len(out), 10 + len(' [TRUNCATED]'))

    def test_body_hash_stable(self):
        self.assertEqual(body_hash('hello'), body_hash('hello'))
        self.assertNotEqual(body_hash('a'), body_hash('b'))

    def test_build_har_entry_sniff_mode(self):
        entry = build_har_entry(
            method='GET',
            url='https://example.com/',
            path='/',
            headers={'Accept': 'text/html'},
            cookies={},
            query_params={},
            body='',
            status_code=200,
            response_headers={'Content-Type': 'text/html'},
            response_body='<html></html>',
            response_size=13,
            duration_ms=12.5,
            sniff_mode='native',
        )
        self.assertEqual(entry['_sniff_mode'], 'native')
        self.assertEqual(entry['request']['method'], 'GET')
