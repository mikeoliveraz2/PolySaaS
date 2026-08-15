from types import SimpleNamespace
from unittest.mock import patch

from django.http import HttpResponse
from django.test import RequestFactory
from django.test import SimpleTestCase

from dose.passthrough.registry import resolve_handler_for_endpoint
from dose.polysniffer.views.sniff_v2 import native_sniff_proxy_by_host


class SlackNativeSniffTests(SimpleTestCase):
    def test_slack_endpoint_resolves_to_handler(self):
        endpoint = SimpleNamespace(
            endpoint_url="https://polysaasworkspace.slack.com/sign_in",
            slug="slack",
            description="Slack workspace",
        )

        handler = resolve_handler_for_endpoint(endpoint)

        self.assertIsNotNone(handler)
        self.assertEqual(handler.__class__.__name__, "SlackPassthroughHandler")
        self.assertTrue(handler.matches_endpoint(endpoint))

    @patch("dose.polysniffer.views.sniff_v2.forward_sniff_native")
    @patch("dose.polysniffer.views.sniff_v2.get_endpoint_by_host")
    def test_native_proxy_resolves_slack_by_host(
        self, get_endpoint, forward_native
    ):
        endpoint = SimpleNamespace(pk=6, endpoint_url="https://polysaasworkspace.slack.com")
        get_endpoint.return_value = endpoint
        forward_native.return_value = HttpResponse("ok")
        request = RequestFactory().get(
            "/admin/polysniffer/sniff/polysaasworkspace.slack.com/native/sign_in",
            {"schema": "polysaasonline"},
        )
        request.user = SimpleNamespace(
            is_active=True,
            is_staff=True,
            is_authenticated=True,
        )

        response = native_sniff_proxy_by_host(
            request, "polysaasworkspace.slack.com", "sign_in"
        )

        self.assertEqual(response.status_code, 200)
        get_endpoint.assert_called_once_with("polysaasworkspace.slack.com", request)
        self.assertEqual(
            request._polysniffer_proxy_prefix,
            "/admin/polysniffer/sniff/polysaasworkspace.slack.com/native",
        )
        forward_native.assert_called_once_with(request, endpoint, "sign_in")
