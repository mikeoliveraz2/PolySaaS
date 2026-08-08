from django.test import SimpleTestCase

from dose.models import PassThroughEndpoint


class PassThroughEndpointUrlTests(SimpleTestCase):
    def test_proxy_url_uses_endpoint_host_and_starting_uri(self):
        endpoint = PassThroughEndpoint(
            endpoint_url="https://tenant-app.example.test:8443",
            starting_uri="/web",
            slug="legacy-label",
        )

        self.assertEqual(
            endpoint.get_menu_url(),
            "/pt/admin/tenant-app.example.test:8443/web",
        )
        self.assertEqual(endpoint.endpoint_url, "https://tenant-app.example.test:8443")

    def test_slug_and_record_id_do_not_affect_proxy_url(self):
        endpoint = PassThroughEndpoint(
            id=917,
            endpoint_url="http://localhost:8065",
            starting_uri="/",
            slug="mattermost",
        )

        expected = "/pt/admin/localhost:8065/"
        self.assertEqual(endpoint.get_menu_url(), expected)

        endpoint.id = 42
        endpoint.slug = "changed-label"
        self.assertEqual(endpoint.get_menu_url(), expected)