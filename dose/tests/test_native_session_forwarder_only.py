"""Native session must start capture without launching Playwright Chromium."""
from unittest import mock

from django.contrib.auth.models import AnonymousUser
from django.test import RequestFactory, SimpleTestCase

from dose.polysniffer.sniff_session import session_start


class NativeSessionForwarderOnlyTests(SimpleTestCase):
    def setUp(self):
        self.factory = RequestFactory()
        self.user = mock.Mock()
        self.user.is_authenticated = True
        self.user.is_staff = True
        self.user.is_active = True

    @mock.patch("dose.polysniffer.sniff_session.TrafficCapture")
    @mock.patch("dose.polysniffer.sniff_session.ensure_trafficlog_capture_columns")
    @mock.patch("dose.polysniffer.sniff_session._ensure_tenant_schema")
    @mock.patch("dose.polysniffer.sniff_session.bind_request_tenant")
    def test_native_start_does_not_launch_playwright(
        self, mock_bind, mock_schema, mock_cols, mock_cap_model
    ):
        tenant = mock.Mock(schema_name="polysaas")
        mock_bind.return_value = tenant
        cap = mock.Mock(id=99, capture_name="app.slack.com-native-test")
        mock_cap_model.objects.filter.return_value.update.return_value = 0
        mock_cap_model.objects.create.return_value = cap

        request = self.factory.post(
            "/admin/polysniffer/sniff/app.slack.com/session/start/",
            {"mode": "native"},
        )
        request.user = self.user
        request.session = {}

        with mock.patch(
            "dose.polysniffer.native_browser_capture.start_native_browser",
            create=True,
        ) as start_browser:
            # Call the undecorated function if wrapped
            view = session_start
            while hasattr(view, "__wrapped__"):
                view = view.__wrapped__
            response = view(request, "app.slack.com")

        self.assertEqual(response.status_code, 200)
        import json
        data = json.loads(response.content.decode("utf-8"))
        self.assertTrue(data.get("ok"))
        self.assertEqual(data.get("browse_via"), "forwarder")
        self.assertEqual(data.get("mode"), "native")
        start_browser.assert_not_called()
