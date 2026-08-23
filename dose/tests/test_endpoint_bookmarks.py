from pathlib import Path

from django.conf import settings
from django.core.exceptions import ValidationError
from django.test import SimpleTestCase

from dose.models import EndpointBookmark, PassThroughEndpoint


class EndpointBookmarkTests(SimpleTestCase):
    def endpoint(self, url="https://app.slack.com/client/T/C"):
        return PassThroughEndpoint(
            endpoint_url=url,
            slug="slack",
            menu_title="Slack",
        )

    def test_registry_targets_are_declarative_keys(self):
        bookmark = EndpointBookmark(
            endpoint=self.endpoint(),
            destination_type=EndpointBookmark.POPUP_FORM,
            target="slack.contact",
        )
        bookmark.clean()
        bookmark.target = "javascript:alert(1)"
        with self.assertRaises(ValidationError):
            bookmark.clean()

    def test_passthrough_targets_are_relative(self):
        bookmark = EndpointBookmark(
            endpoint=self.endpoint(),
            destination_type=EndpointBookmark.PASSTHROUGH_PATH,
            target="/client/team/channel",
        )
        bookmark.clean()
        bookmark.target = "https://app.slack.com/client"
        with self.assertRaises(ValidationError):
            bookmark.clean()

    def test_absolute_application_url_must_match_endpoint_allowlist(self):
        bookmark = EndpointBookmark(
            endpoint=self.endpoint(),
            destination_type=EndpointBookmark.EXTERNAL_PATH,
            target="https://app.slack.com/client/T/C",
        )
        bookmark.clean()
        bookmark.target = "https://evil.example/client"
        with self.assertRaises(ValidationError):
            bookmark.clean()
        bookmark.target = "http://app.slack.com/client/T/C"
        with self.assertRaises(ValidationError):
            bookmark.clean()

    def test_local_http_endpoint_may_open_its_own_host(self):
        bookmark = EndpointBookmark(
            endpoint=self.endpoint("http://localhost:8069/web"),
            destination_type=EndpointBookmark.EXTERNAL_PATH,
            target="http://localhost:8069/web",
        )
        bookmark.clean()

    def test_model_is_endpoint_owned_not_public_or_user_owned(self):
        field_names = {field.name for field in EndpointBookmark._meta.fields}
        self.assertIn("endpoint", field_names)
        self.assertNotIn("tenant", field_names)
        self.assertNotIn("user", field_names)
        self.assertEqual(EndpointBookmark._meta.db_table, "endpoint_bookmark")

    def test_product_navigation_does_not_depend_on_slack_native_tests(self):
        endpoint_home = (
            Path(settings.BASE_DIR)
            / "dose"
            / "tests"
            / "test_endpoint_home.py"
        ).read_text(encoding="utf-8")
        self.assertNotIn("native_sniff", endpoint_home)
