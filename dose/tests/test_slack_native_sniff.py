from types import SimpleNamespace

from django.test import SimpleTestCase

from dose.passthrough.registry import resolve_handler_for_endpoint


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
