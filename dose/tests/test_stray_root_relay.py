"""Relay of upstream root-absolute navigations back onto the proxy prefix."""
from django.test import RequestFactory, SimpleTestCase

from dose.passthrough.stray_root_paths import resolve_stray_root_relay

PANE = "http://testserver/pt/polysniff/app.slack.com/"


class StrayRootRelayTests(SimpleTestCase):
    def setUp(self):
        self.factory = RequestFactory()

    def _resolve(self, path, query="", referer=PANE):
        extra = {"HTTP_REFERER": referer} if referer else {}
        request = self.factory.get(path + (f"?{query}" if query else ""), **extra)
        return resolve_stray_root_relay(request)

    def test_claimed_path_relays_onto_referer_prefix(self):
        query = "app=client&return_to=%2Fpt%2Fpolysniff%2Fapp.slack.com%2F&teams="
        self.assertEqual(
            self._resolve("/auth", query),
            f"/pt/polysniff/app.slack.com/auth?{query}",
        )

    def test_unclaimed_path_is_left_alone(self):
        self.assertIsNone(self._resolve("/accounts/login/"))

    def test_no_referer_is_left_alone(self):
        self.assertIsNone(self._resolve("/auth", referer=""))

    def test_foreign_referer_is_ignored(self):
        self.assertIsNone(self._resolve("/auth", referer="https://evil.example/x/y/z/"))

    def test_already_proxied_path_is_left_alone(self):
        self.assertIsNone(self._resolve("/pt/polysniff/app.slack.com/auth"))
